#!/usr/bin/env python3
"""Drop an icon on this script to add it to the 1989 icon theme.

The icon goes through the same steps as the rest of the set:

1. Color-scheme classes are baked, gloss and faint elements are dropped,
   and the drawing is flattened into an arcade sprite (flatten_icon.py).
2. Each size directory of the context gets its own canvas and grid
   (size_geometry). Symbolic names go only to the symbolic directories.
3. Ink that disappears into the field is lifted, the same way
   readable_icons.py lifts system sprites.
4. The @2x twin is the 1x sprite doubled, as size_icons.py writes it.

An app icon is also saved in scripts/tuned/, so a full rebuild keeps it.

    python3 scripts/add_icon.py ~/Downloads/firefox.svg
    python3 scripts/add_icon.py --context places folder-games.svg
    python3 scripts/add_icon.py --name org.mozilla.firefox logo.png
    python3 scripts/add_icon.py --make-launcher          # drop target on the desktop

The file name is the icon name, unless --name is given. SVG and PNG work.
"""

from __future__ import annotations

import argparse
import base64
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flatten_icon import flatten_svg, label_for, size_geometry  # noqa: E402
from readable_icons import apply_mapping, mapping_for, system_icon  # noqa: E402
from size_icons import scale_sprite  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "out" / "icons" / "1989"
TUNED = Path(__file__).resolve().parent / "tuned"
CONTEXTS = ("apps", "actions", "status", "places", "devices", "mimes", "categories", "emblems", "animations")
SYMBOLIC_DIRS = {"symbolic", "symbolic5"}
# weatheralt is a special set of status drawings. Nothing is added there.
SKIP_DIRS = {"weatheralt"}


def guess_context(path: Path) -> str:
    """A file dropped from inside an icon theme keeps that theme's context."""
    for part in reversed(path.resolve().parent.parts):
        base = part.replace("@2x", "")
        if base in CONTEXTS:
            return base
    return "apps"


def source_svg(path: Path) -> str:
    if path.suffix.lower() == ".svg":
        return path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".svgz":
        import gzip

        return gzip.decompress(path.read_bytes()).decode("utf-8", errors="replace")
    if path.suffix.lower() == ".png":
        from PIL import Image

        with Image.open(path) as image:
            width, height = image.size
        side = max(width, height)
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        x, y = (side - width) // 2, (side - height) // 2
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{side}" height="{side}" viewBox="0 0 {side} {side}">'
            f'<image x="{x}" y="{y}" width="{width}" height="{height}" '
            f'xlink:href="data:image/png;base64,{data}"/></svg>'
        )
    raise ValueError(f"{path.name}: use an .svg, .svgz, or .png file")


def listed_dirs(theme: Path) -> set[str] | None:
    """Directories named in index.theme. Plasma reads no others."""
    index = theme / "index.theme"
    if not index.is_file():
        return None
    for line in index.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Directories="):
            return {item.strip() for item in line.split("=", 1)[1].split(",") if item.strip()}
    return None


def target_dirs(theme: Path, context: str, symbolic: bool) -> list[str]:
    root = theme / context
    if not root.is_dir():
        raise ValueError(f"{context} is not a directory in {theme}")
    listed = listed_dirs(theme)
    sizes = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name in SKIP_DIRS:
            continue
        if listed is not None and f"{context}/{entry.name}" not in listed:
            continue
        if (entry.name in SYMBOLIC_DIRS) == symbolic:
            sizes.append(entry.name)
    if not sizes:
        kind = "symbolic" if symbolic else "sized or scalable"
        raise ValueError(f"{context} has no {kind} directory for this icon")
    return sizes


def readable(sprite: str, dest: Path, theme: Path) -> str:
    if not system_icon(dest, theme):
        return sprite
    context = dest.relative_to(theme).parts[0].replace("@2x", "")
    mapped = mapping_for(sprite, force_dark=context == "status")
    return apply_mapping(sprite, mapped) if mapped else sprite


def add(path: Path, *, name: str | None, context: str | None, theme: Path, keep: bool) -> list[Path]:
    text = source_svg(path)
    stem = name or path.stem
    if stem.endswith(".svg"):
        stem = stem[:-4]
    context = context or guess_context(path)
    symbolic = stem.endswith("-symbolic")
    label = label_for(text, Path(stem + ".svg"))
    written: list[Path] = []
    for size in target_dirs(theme, context, symbolic):
        canvas, grid = size_geometry(size)
        dest = theme / context / size / f"{stem}.svg"
        sprite = readable(flatten_svg(text, label=label, canvas=canvas, grid=grid), dest, theme)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(sprite, encoding="utf-8")
        written.append(dest)

        double, double_grid = size_geometry(size, doubled=True)
        twin = theme / f"{context}@2x" / size / f"{stem}.svg"
        doubled = scale_sprite(sprite, double)
        if doubled is None:
            doubled = readable(flatten_svg(text, label=label, canvas=double, grid=double_grid), twin, theme)
        twin.parent.mkdir(parents=True, exist_ok=True)
        twin.write_text(doubled, encoding="utf-8")
        written.append(twin)

        # The build restores scripts/tuned/ over apps/scalable after it
        # recopies the source theme. Saving the sprite there keeps it.
        if keep and context == "apps" and size == "scalable":
            TUNED.mkdir(parents=True, exist_ok=True)
            tuned = TUNED / f"{stem}.svg"
            tuned.write_text(sprite, encoding="utf-8")
            written.append(tuned)
    return written


def notify(title: str, body: str, error: bool = False) -> None:
    """Report to the desktop when there is no terminal to read."""
    if shutil.which("kdialog"):
        kind = "--error" if error else "--passivepopup"
        args = ["kdialog", "--title", title, kind, body]
        if not error:
            args.append("8")
        subprocess.run(args, check=False)
    elif shutil.which("notify-send"):
        subprocess.run(["notify-send", "-i", "dialog-error" if error else "image-x-generic", title, body], check=False)


def desktop_dir() -> Path:
    if shutil.which("xdg-user-dir"):
        found = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, check=False)
        if found.returncode == 0 and found.stdout.strip():
            return Path(found.stdout.strip())
    return Path.home() / "Desktop"


def make_launcher(where: Path) -> Path:
    """Write a .desktop file that runs this script on whatever is dropped on it."""
    script = Path(__file__).resolve()
    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(script))} --notify %F"
    where.mkdir(parents=True, exist_ok=True)
    launcher = where / "1989-add-icon.desktop"
    launcher.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Add icon to 1989\n"
        "Comment=Drop SVG or PNG icons here to add them to the 1989 icon theme\n"
        f"Exec={command}\n"
        "Icon=cachyos\n"
        "Terminal=false\n"
        "MimeType=image/svg+xml;image/svg+xml-compressed;image/png;\n"
        "NoDisplay=true\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    # Plasma asks before it runs an untrusted launcher. Mark this one trusted.
    if shutil.which("gio"):
        subprocess.run(["gio", "set", str(launcher), "metadata::trusted", "true"], check=False, capture_output=True)
    return launcher


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add icons to the 1989 icon theme in out/.")
    parser.add_argument("files", nargs="*", type=Path, help="SVG, SVGZ, or PNG icons")
    parser.add_argument("--name", help="icon name to write (one file only; default: the file name)")
    parser.add_argument(
        "--context",
        choices=CONTEXTS,
        help="theme context (default: from the file's folder, else apps)",
    )
    parser.add_argument("--theme", type=Path, default=THEME, help=f"icon theme root (default: {THEME})")
    parser.add_argument("--no-tuned", action="store_true", help="do not save app icons in scripts/tuned/")
    parser.add_argument("--notify", action="store_true", help="report on the desktop instead of the terminal")
    parser.add_argument(
        "--make-launcher",
        nargs="?",
        const=True,
        metavar="DIR",
        help="write a drop-target launcher to DIR (default: the desktop folder) and exit",
    )
    args = parser.parse_args(argv)
    if args.name and len(args.files) > 1:
        parser.error("--name works with one file only")
    if not args.files and not args.make_launcher:
        parser.error("pass one or more icon files")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.make_launcher:
        where = desktop_dir() if args.make_launcher is True else Path(args.make_launcher).expanduser()
        print(make_launcher(where))
        return 0
    if not shutil.which("rsvg-convert"):
        message = "rsvg-convert is missing. Install librsvg (the rsvg-convert tool) and try again."
        print(message, file=sys.stderr)
        if args.notify:
            notify("1989 icons", message, error=True)
        return 1

    added: list[str] = []
    failed: list[str] = []
    for path in args.files:
        try:
            written = add(path, name=args.name, context=args.context, theme=args.theme, keep=not args.no_tuned)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            failed.append(f"{path.name}: {exc}")
            print(f"{path}: {exc}", file=sys.stderr)
            continue
        for dest in written:
            print(dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest)
        added.append(written[0].stem)

    if args.notify:
        if failed:
            notify("1989 icons", "\n".join(failed), error=True)
        if added:
            notify("1989 icons", "Added: " + ", ".join(added))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
