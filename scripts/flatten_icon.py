#!/usr/bin/env python3
"""Turn each icon into a flat arcade sprite.

Color-scheme classes become solid fills. The drawing is sampled on a
coarse grid and written as one filled path per color on a 64×64 canvas.
Filters, shadows, and soft edges become hard pixels in the icon's own
colors. A grid of 32 is the Chrome sprite: each cell is a 2px block.

    python3 scripts/flatten_icon.py icon.svg -o icon.flat.svg
    python3 scripts/flatten_icon.py out/icons/1989/apps/scalable -o /tmp/flat
    python3 scripts/flatten_icon.py --in-place out/icons/1989/apps/scalable

Symbolic icons use currentColor so the theme can recolor them. This bakes
the rendered colors, so leave those files out of a full-set run. Tuned
drawings in scripts/tuned/ are the ones the build copies back over the set.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
import subprocess
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app_icons import bake

CANVAS = 64


def _tag_end(text: str, start: int) -> int:
    quote = ""
    i = start
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == ">":
            return i + 1
        i += 1
    return len(text)


def _opacity(attrs: str) -> float | None:
    # The property is `opacity`. fill-opacity and stop-opacity are different.
    match = re.search(
        r"""(?:(?<![\w-])opacity\s*=\s*["']\s*([0-9.]+)\s*["']|(?<![\w-])opacity\s*:\s*([0-9.]+))""",
        attrs,
        flags=re.I,
    )
    if not match:
        return None
    try:
        return float(match.group(1) or match.group(2))
    except ValueError:
        return None


def drop_faint(text: str, limit: float = 0.5) -> str:
    """Remove whole elements painted below `limit` opacity. Those are gloss."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "<":
            nxt = text.find("<", i)
            if nxt == -1:
                out.append(text[i:])
                break
            out.append(text[i:nxt])
            i = nxt
            continue
        if text.startswith("<!--", i):
            nxt = text.find("-->", i + 4)
            nxt = n if nxt == -1 else nxt + 3
            out.append(text[i:nxt])
            i = nxt
            continue
        if text.startswith("</", i):
            nxt = _tag_end(text, i)
            out.append(text[i:nxt])
            i = nxt
            continue
        nxt = _tag_end(text, i)
        tag = text[i:nxt]
        name_match = re.match(r"<([A-Za-z][\w:.-]*)\b([^<>]*)>", tag, flags=re.S)
        if not name_match:
            out.append(tag)
            i = nxt
            continue
        name = name_match.group(1)
        local = name.split(":")[-1].lower()
        attrs = name_match.group(2)
        opacity = _opacity(attrs)
        faint = local != "svg" and opacity is not None and opacity < limit
        self_closing = attrs.rstrip().endswith("/")
        if not faint:
            out.append(tag)
            i = nxt
            continue
        if self_closing:
            i = nxt
            continue
        depth = 1
        i = nxt
        token = re.compile(rf"</?{re.escape(name)}\b", flags=re.I)
        while depth and i < n:
            found = token.search(text, i)
            if not found:
                i = n
                break
            end = _tag_end(text, found.start())
            piece = text[found.start() : end]
            if piece.startswith("</"):
                depth -= 1
            elif not piece.rstrip().endswith("/>"):
                depth += 1
            i = end
    return "".join(out)


def render(svg: str, size: int) -> Image.Image:
    proc = subprocess.run(
        [
            "rsvg-convert",
            "-w",
            str(size),
            "-h",
            str(size),
            "--page-width",
            str(size),
            "--page-height",
            str(size),
            "-a",
            "--unlimited",
            "-b",
            "none",
        ],
        input=svg.encode("utf-8"),
        capture_output=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0 or not proc.stdout:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or "rsvg-convert failed")
    image = Image.open(BytesIO(proc.stdout)).convert("RGBA")
    if image.size == (size, size):
        return image
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2), image)
    return canvas


def sample(image: Image.Image, grid: int, coverage: float) -> list[list[tuple[int, int, int] | None]]:
    pixels = image.load()
    step = image.width // grid
    cells: list[list[tuple[int, int, int] | None]] = []
    need = step * step * coverage
    for gy in range(grid):
        row: list[tuple[int, int, int] | None] = []
        y0 = gy * step
        for gx in range(grid):
            buckets: dict[tuple[int, int, int], list[int]] = {}
            opaque = 0
            x0 = gx * step
            for y in range(y0, y0 + step):
                for x in range(x0, x0 + step):
                    red, green, blue, alpha = pixels[x, y]
                    if alpha < 128:
                        continue
                    opaque += 1
                    key = (red >> 3, green >> 3, blue >> 3)
                    slot = buckets.get(key)
                    if slot is None:
                        buckets[key] = [red, green, blue, 1]
                    else:
                        slot[0] += red
                        slot[1] += green
                        slot[2] += blue
                        slot[3] += 1
            if opaque < need or not buckets:
                row.append(None)
                continue
            best = max(buckets.values(), key=lambda slot: slot[3])
            row.append((best[0] // best[3], best[1] // best[3], best[2] // best[3]))
        cells.append(row)
    return cells


def _dist2(a: list[float] | tuple[int, ...], b: list[float] | tuple[int, ...]) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def _chroma(color: tuple[int, int, int]) -> int:
    return max(color) - min(color)


def _luma(color: tuple[int, int, int]) -> float:
    red, green, blue = color
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _joins(color: tuple[int, int, int], anchor: tuple[int, int, int], snap2: float) -> bool:
    if _dist2(color, anchor) <= snap2:
        return True
    # A soft gray gradient is one flat color. A light mark on it stays.
    if _chroma(color) > 36 or _chroma(anchor) > 36:
        return False
    return abs(_luma(color) - _luma(anchor)) <= 58 and _dist2(color, anchor) <= 110 * 110


def _closest(entries: list[list[float]]) -> tuple[int, int, float] | None:
    found: tuple[int, int, float] | None = None
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            distance = _dist2(entries[i], entries[j])
            if found is None or distance < found[2]:
                found = (i, j, distance)
    return found


def palette(
    cells: list[list[tuple[int, int, int] | None]], snap: float, max_colors: int
) -> dict[tuple[int, int, int], tuple[int, int, int]]:
    counts: Counter[tuple[int, int, int]] = Counter(
        color for row in cells for color in row if color is not None
    )
    if not counts:
        return {}
    # Most common color wins a slot and keeps its value. Nearby shades join it.
    snap2 = snap * snap
    groups: list[dict] = []
    for color, count in counts.most_common():
        best_i = -1
        best_d = float("inf")
        for i, group in enumerate(groups):
            anchor = group["anchor"]
            if not _joins(color, anchor, snap2):
                continue
            distance = _dist2(color, anchor)
            if distance < best_d:
                best_d = distance
                best_i = i
        if best_i >= 0:
            groups[best_i]["n"] += count
            groups[best_i]["src"].append(color)
            continue
        groups.append({"color": [float(v) for v in color], "anchor": color, "n": count, "src": [color]})
    while max_colors and len(groups) > max_colors:
        entries = [group["color"] for group in groups]
        pair = _closest(entries)
        if pair is None:
            break
        i, j, _distance = pair
        left, right = groups[i], groups[j]
        total = left["n"] + right["n"]
        left["color"] = [
            (left["color"][channel] * left["n"] + right["color"][channel] * right["n"]) / total
            for channel in range(3)
        ]
        left["n"] = total
        left["src"].extend(right["src"])
        del groups[j]
    mapping: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    for group in groups:
        red, green, blue = (max(0, min(255, round(channel))) for channel in group["color"])
        if red >= 250 and green >= 250 and blue >= 250:
            red, green, blue = 255, 255, 255
        elif red <= 5 and green <= 5 and blue <= 5:
            red, green, blue = 0, 0, 0
        rgb = (red, green, blue)
        for source in group["src"]:
            mapping[source] = rgb
    return mapping


def size_geometry(size: str, doubled: bool = False) -> tuple[int, int]:
    """Canvas and grid for a theme size directory.

    16, 22, and 24 are 1px cells. 32 and 48 are 2px cells. Scalable stays
    the 64 canvas with a grid of 32. A doubled sprite keeps that grid and
    doubles the cell.
    """
    fixed = {
        "16": (16, 16),
        "22": (22, 22),
        "24": (24, 24),
        "32": (32, 16),
        "48": (48, 24),
        "64": (64, 32),
        "scalable": (64, 32),
    }
    if size in {"symbolic", "symbolic5", "weatheralt"}:
        return (32, 16) if doubled else (16, 16)
    canvas, grid = fixed.get(size, (16, 16))
    if not doubled:
        return canvas, grid
    return canvas * 2, grid


def sprite(
    cells: list[list[tuple[int, int, int] | None]],
    mapping: dict,
    label: str,
    canvas: int = CANVAS,
) -> str:
    scale = canvas // len(cells)
    paint: dict[tuple[int, int, int], list[str]] = {}
    order: list[tuple[int, int, int]] = []
    for y, row in enumerate(cells):
        x = 0
        width = len(row)
        while x < width:
            source = row[x]
            if source is None:
                x += 1
                continue
            color = mapping[source]
            start = x
            x += 1
            while x < width and row[x] is not None and mapping[row[x]] == color:
                x += 1
            if color not in paint:
                paint[color] = []
                order.append(color)
            px = start * scale
            py = y * scale
            run = (x - start) * scale
            paint[color].append(f"M{px} {py}h{run}v{scale}h-{run}z")
    ranked = sorted(order, key=lambda color: (-len(paint[color]), color))
    paths = []
    for color in ranked:
        hex_color = "#{:02X}{:02X}{:02X}".format(*color)
        paths.append(f'  <path fill="{hex_color}" d="{" ".join(paint[color])}"/>')
    body = "\n".join(paths)
    safe = html.escape(label, quote=True)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas}" height="{canvas}" '
        f'viewBox="0 0 {canvas} {canvas}" shape-rendering="crispEdges" role="img" '
        f'aria-label="{safe}">\n{body}\n</svg>\n'
    )


def label_for(text: str, path: Path) -> str:
    match = re.search(r'aria-label="([^"]+)"', text)
    if match:
        return match.group(1)
    words = re.split(r"[-_.]+", path.stem)
    return " ".join(word.capitalize() for word in words if word)


def flatten_svg(
    text: str,
    *,
    label: str,
    grid: int = 32,
    canvas: int = CANVAS,
    colors: int = 8,
    snap: float = 32,
    coverage: float = 0.4,
    sample_px: int = 8,
    keep_faint: bool = False,
) -> str:
    if canvas % grid:
        raise ValueError(f"grid {grid} does not divide the {canvas} canvas")
    # Scheme classes become flat fills. Gradients stay so the sample can posterize them.
    prepared = bake(text, flatten_gradients=False)
    if not keep_faint:
        prepared = drop_faint(prepared)
    image = render(prepared, grid * sample_px)
    cells = sample(image, grid, coverage)
    mapping = palette(cells, snap, colors)
    return sprite(cells, mapping, label, canvas)


def sources(paths: list[Path]) -> list[tuple[Path | None, Path]]:
    found: list[tuple[Path | None, Path]] = []
    for path in paths:
        if path.is_dir():
            found.extend((path, svg) for svg in sorted(path.rglob("*.svg")))
        elif path.is_file():
            found.append((None, path))
        else:
            raise FileNotFoundError(path)
    return found


def destination(root: Path | None, src: Path, out: Path | None, inplace: bool) -> Path | None:
    if inplace:
        return src
    if out is None:
        return None
    if root is None and out.suffix.lower() == ".svg":
        return out
    rel = src.relative_to(root) if root is not None else Path(src.name)
    return out / rel


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Flatten icons into arcade sprites.")
    parser.add_argument("paths", nargs="+", type=Path, help="SVG files or directories")
    parser.add_argument("-o", "--output", type=Path, help="SVG file, or a directory for many")
    parser.add_argument("--in-place", action="store_true", help="overwrite each source SVG")
    parser.add_argument("--grid", type=int, default=32, help="cells across the 64 canvas (default 32)")
    parser.add_argument("--colors", type=int, default=8, help="maximum flat colors (0 keeps every snapped color)")
    parser.add_argument("--snap", type=float, default=32, help="merge colors closer than this RGB distance")
    parser.add_argument("--coverage", type=float, default=0.4, help="opaque fraction a cell needs to be filled")
    parser.add_argument("--sample", type=int, default=8, help="render pixels per cell")
    parser.add_argument("--keep-faint", action="store_true", help="keep elements below half opacity")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="file name to leave unchanged (repeatable)",
    )
    parser.add_argument("-j", "--jobs", type=int, default=0, help="worker threads (0 uses one per core)")
    args = parser.parse_args(argv)
    if args.in_place and args.output:
        parser.error("pass --in-place or -o, not both")
    if args.grid < 1 or CANVAS % args.grid:
        parser.error(f"--grid must divide {CANVAS}")
    if args.colors < 0:
        parser.error("--colors must be 0 or more")
    if args.sample < 1:
        parser.error("--sample must be at least 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    items = sources(args.paths)
    if not items:
        print("no svg files", file=sys.stderr)
        return 1
    file_out = args.output is not None and args.output.suffix.lower() == ".svg"
    if file_out and (len(items) != 1 or items[0][0] is not None):
        print("-o file.svg accepts one SVG file", file=sys.stderr)
        return 1
    if args.output is None and not args.in_place and len(items) != 1:
        print("pass -o or --in-place for more than one icon", file=sys.stderr)
        return 1
    if file_out:
        out: Path | None = args.output
    elif args.output is not None:
        args.output.mkdir(parents=True, exist_ok=True)
        out = args.output
    else:
        out = None

    excluded = {name for name in args.exclude}
    skipped = [item for item in items if item[1].name in excluded]
    items = [item for item in items if item[1].name not in excluded]
    jobs = args.jobs or min(len(items), os.cpu_count() or 1)
    failed = 0
    done = 0
    quiet = len(items) > 40
    cache: dict[tuple[bytes, str], str] = {}
    cache_lock = threading.Lock()
    count_lock = threading.Lock()

    def run(item: tuple[Path | None, Path]) -> str:
        root, src = item
        text = src.read_text(encoding="utf-8", errors="replace")
        label = label_for(text, src)
        key = (hashlib.sha256(text.encode("utf-8", errors="replace")).digest(), label)
        with cache_lock:
            flat = cache.get(key)
        if flat is None:
            flat = flatten_svg(
                text,
                label=label,
                grid=args.grid,
                colors=args.colors,
                snap=args.snap,
                coverage=args.coverage,
                sample_px=args.sample,
                keep_faint=args.keep_faint,
            )
            with cache_lock:
                cache.setdefault(key, flat)
        dest = destination(root, src, out, args.in_place)
        if dest is None:
            sys.stdout.write(flat)
            return src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(flat)
        return f"{src} -> {dest}"

    def finish(item: tuple[Path | None, Path], result: str | None, exc: BaseException | None) -> None:
        nonlocal done, failed
        with count_lock:
            done += 1
            current = done
        if exc is not None:
            failed += 1
            print(f"{item[1]}: {exc}", file=sys.stderr)
        elif not quiet:
            print(result, file=sys.stderr)
        if quiet and (current % 1000 == 0 or current == len(items)):
            print(f"{current}/{len(items)}", file=sys.stderr, flush=True)

    if jobs == 1 or (out is None and not args.in_place):
        for item in items:
            try:
                finish(item, run(item), None)
            except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
                finish(item, None, exc)
    else:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {pool.submit(run, item): item for item in items}
            for future in as_completed(futures):
                item = futures[future]
                try:
                    finish(item, future.result(), None)
                except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
                    finish(item, None, exc)
    print(f"flattened {len(items) - failed} failed {failed} skipped {len(skipped)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
