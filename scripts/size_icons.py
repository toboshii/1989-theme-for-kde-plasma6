#!/usr/bin/env python3
"""Arcadefy each ColorFlow size onto its own canvas, then write real @2x sprites.

The 1x file for a tuned name, or for a name ColorFlow does not have, is left
alone. Its @2x twin is still written when it is missing or still the 1x canvas.
"""

from __future__ import annotations

import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flatten_icon import flatten_svg, label_for, size_geometry

SOURCE = Path.home() / ".local/share/icons/ColorFlow.Agresive.Color"
TUNED = Path(__file__).resolve().parent / "tuned"

_NUM = re.compile(r"-?\d+(?:\.\d+)?")
_VIEW = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')


def viewbox_size(text: str) -> int | None:
    match = _VIEW.search(text)
    if not match:
        return None
    width, height = float(match.group(1)), float(match.group(2))
    if width != height or width != int(width):
        return None
    return int(width)


def scale_sprite(text: str, canvas: int) -> str | None:
    """Scale a flat sprite onto `canvas` when that is an integer multiple."""
    current = viewbox_size(text)
    if current is None or current == 0 or canvas % current:
        return None
    factor = canvas // current
    if factor == 1:
        return text

    def path(match: re.Match[str]) -> str:
        def number(piece: re.Match[str]) -> str:
            value = float(piece.group(0)) * factor
            rounded = round(value)
            if abs(value - rounded) < 1e-6:
                return str(int(rounded))
            return f"{value:.4f}".rstrip("0")

        return 'd="' + _NUM.sub(number, match.group(1)) + '"'

    text = re.sub(r'\bd="([^"]*)"', path, text)
    text = re.sub(r'\bwidth="[\d.]+(?:px)?"', f'width="{canvas}"', text, count=1)
    text = re.sub(r'\bheight="[\d.]+(?:px)?"', f'height="{canvas}"', text, count=1)
    text = re.sub(r'viewBox="[^"]+"', f'viewBox="0 0 {canvas} {canvas}"', text, count=1)
    return text


def source_index(source: Path) -> dict[tuple[str, str], dict[str, Path]]:
    found: dict[tuple[str, str], dict[str, Path]] = {}
    if not source.is_dir():
        return found
    for path in source.rglob("*.svg"):
        rel = path.relative_to(source)
        if len(rel.parts) < 3 or "@2x" in rel.parts[0]:
            continue
        # rglob yields a dangling symlink. is_file() follows it and rejects it.
        if not path.is_file():
            continue
        found.setdefault((rel.parts[0], path.stem), {})[rel.parts[1]] = path
    return found


def larger_source(
    index: dict[tuple[str, str], dict[str, Path]], ctx: str, stem: str, size: str
) -> Path | None:
    sizes = index.get((ctx, stem))
    if not sizes:
        return None
    nominal, _grid = size_geometry(size)
    best: Path | None = None
    best_px = nominal
    for candidate, path in sizes.items():
        px, _grid = size_geometry(candidate)
        if px > best_px:
            best_px = px
            best = path
    return best


def tuned_stems() -> set[str]:
    if not TUNED.is_dir():
        return set()
    return {path.stem for path in TUNED.glob("*.svg")}


def restore_tuned(theme: Path) -> int:
    if not TUNED.is_dir():
        return 0
    count = 0
    for src in TUNED.glob("*.svg"):
        dest = theme / "apps" / "scalable" / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"))
        count += 1
    return count


def ensure_index(theme: Path) -> None:
    index = theme / "index.theme"
    if not index.is_file():
        return
    text = index.read_text(encoding="utf-8")
    sections = {
        "actions/32": "[actions/32]\nSize=32\nContext=Actions\nType=Fixed\n",
        "actions@2x/32": "[actions@2x/32]\nSize=32\nScale=2\nContext=Actions\nType=Fixed\n",
        "status/symbolic5": (
            "[status/symbolic5]\nSize=16\nContext=Status\nMinSize=16\nMaxSize=512\nType=Scalable\n"
        ),
        "status@2x/symbolic5": (
            "[status@2x/symbolic5]\nSize=16\nScale=2\nContext=Status\n"
            "MinSize=16\nMaxSize=512\nType=Scalable\n"
        ),
        "status/weatheralt": (
            "[status/weatheralt]\nSize=16\nContext=Status\nMinSize=16\nMaxSize=512\nType=Scalable\n"
        ),
        "status@2x/weatheralt": (
            "[status@2x/weatheralt]\nSize=16\nScale=2\nContext=Status\n"
            "MinSize=16\nMaxSize=512\nType=Scalable\n"
        ),
    }
    directories = re.search(r"^Directories=(.*)$", text, flags=re.M)
    if directories:
        listed = [item for item in directories.group(1).split(",") if item]
        for name in sections:
            if name not in listed:
                listed.append(name)
        text = text[: directories.start(1)] + ",".join(listed) + text[directories.end(1) :]
    for name, body in sections.items():
        if f"[{name}]" not in text:
            if not text.endswith("\n"):
                text += "\n"
            text += "\n" + body
    parts = re.split(r"(?=^\[)", text, flags=re.M)
    rebuilt: list[str] = []
    for part in parts:
        header = part.split("]", 1)[0]
        if part.startswith("[") and "@2x" in header and "Scale=" not in part:
            part = re.sub(r"(Size=\d+\n)", r"\1Scale=2\n", part, count=1)
        rebuilt.append(part)
    index.write_text("".join(rebuilt), encoding="utf-8")


class Cache:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[tuple[bytes, int, int, str], str] = {}

    def flatten(self, text: str, label: str, canvas: int, grid: int) -> str:
        key = (text.encode("utf-8", errors="replace"), canvas, grid, label)
        with self._lock:
            cached = self._items.get(key)
        if cached is not None:
            return cached
        flat = flatten_svg(text, label=label, canvas=canvas, grid=grid)
        with self._lock:
            self._items.setdefault(key, flat)
            return self._items[key]


def run_tasks(tasks: list[tuple], jobs: int) -> tuple[int, int]:
    cache = Cache()
    failed = 0
    done = 0
    lock = threading.Lock()

    def work(task: tuple) -> None:
        kind, src, dest, canvas, grid = task
        dest.parent.mkdir(parents=True, exist_ok=True)
        if kind == "scale":
            scaled = scale_sprite(src, canvas)
            if scaled is None:
                raise RuntimeError(f"cannot scale onto {canvas}")
            dest.write_text(scaled, encoding="utf-8")
            return
        text = src.read_text(encoding="utf-8", errors="replace")
        label = label_for(text, src)
        dest.write_text(cache.flatten(text, label, canvas, grid), encoding="utf-8")

    def finish(exc: BaseException | None) -> None:
        nonlocal done, failed
        with lock:
            done += 1
            current = done
            if exc is not None:
                failed += 1
        if exc is not None:
            print(exc, file=sys.stderr)
        if current % 1000 == 0 or current == len(tasks):
            print(f"{current}/{len(tasks)}", file=sys.stderr, flush=True)

    if not tasks:
        return 0, 0
    workers = jobs or min(len(tasks), os.cpu_count() or 1)
    if workers == 1:
        for task in tasks:
            try:
                work(task)
                finish(None)
            except (OSError, RuntimeError) as exc:
                finish(exc)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(work, task): task for task in tasks}
            for future in as_completed(futures):
                try:
                    future.result()
                    finish(None)
                except (OSError, RuntimeError) as exc:
                    finish(exc)
    return len(tasks) - failed, failed


def one_x_tasks(theme: Path, index: dict, tuned: set[str]) -> list[tuple]:
    tasks = []
    for (ctx, stem), sizes in index.items():
        if stem in tuned:
            continue
        for size, src in sizes.items():
            canvas, grid = size_geometry(size)
            dest = theme / ctx / size / f"{stem}.svg"
            if dest.is_file():
                current = viewbox_size(dest.read_text(encoding="utf-8", errors="replace"))
                if current == canvas:
                    continue
            tasks.append(("flatten", src, dest, canvas, grid))
    return tasks


def two_x_tasks(theme: Path, index: dict, tuned: set[str]) -> list[tuple]:
    tasks = []
    for path in sorted(theme.rglob("*.svg")):
        rel = path.relative_to(theme)
        if len(rel.parts) < 3 or "@2x" in rel.parts[0]:
            continue
        ctx, size, name = rel.parts[0], rel.parts[1], rel.parts[2]
        if not name.endswith(".svg"):
            continue
        canvas, grid = size_geometry(size, doubled=True)
        dest = theme / f"{ctx}@2x" / size / name
        if dest.is_file():
            current = viewbox_size(dest.read_text(encoding="utf-8", errors="replace"))
            if current == canvas:
                continue
        stem = path.stem
        bigger = None if stem in tuned else larger_source(index, ctx, stem, size)
        if bigger is not None:
            tasks.append(("flatten", bigger, dest, canvas, grid))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        scaled = scale_sprite(text, canvas)
        if scaled is not None:
            tasks.append(("scale", text, dest, canvas, grid))
        else:
            tasks.append(("flatten", path, dest, canvas, grid))
    return tasks


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("pass the 1989 icon theme root", file=sys.stderr)
        return 1
    theme = Path(args[0])
    jobs = int(args[1]) if len(args) > 1 else 0
    if not theme.is_dir():
        print(f"missing {theme}", file=sys.stderr)
        return 1
    tuned = tuned_stems()
    index = source_index(SOURCE)
    print(f"sources {sum(len(sizes) for sizes in index.values())} tuned {len(tuned)}", file=sys.stderr)
    wrote, failed = run_tasks(one_x_tasks(theme, index, tuned), jobs)
    print(f"1x wrote {wrote} failed {failed}", file=sys.stderr)
    restored = restore_tuned(theme)
    print(f"tuned restored {restored}", file=sys.stderr)
    wrote2, failed2 = run_tasks(two_x_tasks(theme, index, tuned), jobs)
    print(f"2x wrote {wrote2} failed {failed2}", file=sys.stderr)
    ensure_index(theme)
    return 1 if failed or failed2 else 0


if __name__ == "__main__":
    raise SystemExit(main())
