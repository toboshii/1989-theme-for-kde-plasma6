#!/usr/bin/env python3
"""Drop an icon or an app on this script to add it to the 1989 icon theme.

Each argument can be:

- an icon file: .svg, .svgz, .png, or .xpm
- a desktop entry: a .desktop file, as dropped from the app menu
- an AppImage file: its own icon is read from inside it, without running it
- an app name: a desktop entry is found by its id, Name, StartupWMClass,
  command, or icon name. This covers pacman and AUR packages, Flatpak apps, and
  AppImages that were added to the menu. A pacman package name also
  works, for a package whose desktop file has another name.

For an app, the icon is the one its desktop entry names, taken from the
icon themes it ships in (hicolor first), never from the 1989 theme.

The icon goes through the same steps as the rest of the set:

1. Color-scheme classes are baked, gloss and faint elements are dropped,
   and the drawing is flattened into an arcade sprite (flatten_icon.py).
2. Each size directory of the context that index.theme lists gets its
   own canvas and grid (size_geometry). Symbolic names go only to the
   symbolic directories.
3. Ink that disappears into the field is lifted, the same way
   readable_icons.py lifts system sprites.
4. The @2x twin is the 1x sprite doubled, as size_icons.py writes it.

An app icon is also saved in scripts/tuned/, so a full rebuild keeps it.

    python3 scripts/add_icon.py ~/Downloads/firefox.svg
    python3 scripts/add_icon.py firefox org.gimp.GIMP visual-studio-code-bin
    python3 scripts/add_icon.py ~/Applications/Obsidian.AppImage
    python3 scripts/add_icon.py --context places folder-games.svg
    python3 scripts/add_icon.py --make-launcher          # drop target on the desktop

An icon file's name is the icon name, unless --name is given.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import io
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
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
IMAGE_SUFFIXES = {".svg", ".svgz", ".png", ".xpm"}
ICON_SUFFIXES = (".svg", ".svgz", ".png", ".xpm")
# A flattened app sprite is a 32-cell grid. A smaller raster is blown up.
SMALL_RASTER = 32


class AppNotFound(ValueError):
    """An app or its icon could not be found."""


@dataclass
class Source:
    """One icon to add: the drawing, the theme name, and a label."""

    text: str
    stem: str
    context: str | None
    label: str | None
    origin: str
    notes: list[str]


# Icon files -----------------------------------------------------------------


def raster_svg(data: bytes) -> str:
    """Wrap a raster in an SVG so it renders through the same path."""
    from PIL import Image

    with Image.open(io.BytesIO(data)) as image:
        image = image.convert("RGBA")
        width, height = image.size
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
    side = max(width, height)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    x, y = (side - width) // 2, (side - height) // 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{side}" height="{side}" viewBox="0 0 {side} {side}">'
        f'<image x="{x}" y="{y}" width="{width}" height="{height}" '
        f'xlink:href="data:image/png;base64,{encoded}"/></svg>'
    )


def raster_size(data: bytes) -> int:
    from PIL import Image

    with Image.open(io.BytesIO(data)) as image:
        return max(image.size)


def read_icon(path: Path) -> tuple[str, list[str]]:
    """The icon as SVG text, and any warning about its quality."""
    data = path.read_bytes()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    head = data[:512].lstrip()
    if head.startswith(b"<?xml") or head.startswith(b"<svg") or b"<svg" in data[:2048]:
        return data.decode("utf-8", errors="replace"), []
    try:
        text = raster_svg(data)
    except Exception as exc:  # PIL raises many types for a bad image
        raise ValueError(f"{path.name}: not an SVG, PNG, or XPM image ({exc})") from exc
    notes = []
    size = raster_size(data)
    if size < SMALL_RASTER:
        notes.append(f"{path.name} is only {size}px; the sprite will be blocky")
    return text, notes


# Desktop entries -------------------------------------------------------------


def data_dirs() -> list[Path]:
    """XDG data directories in lookup order, plus the Flatpak exports."""
    home = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    found = [home, home / "flatpak" / "exports" / "share"]
    system = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    found += [Path(item) for item in system.split(":") if item]
    found += [Path("/var/lib/flatpak/exports/share"), Path("/usr/local/share"), Path("/usr/share")]
    unique: list[Path] = []
    for path in found:
        if path not in unique:
            unique.append(path)
    return unique


def read_entry(path: Path) -> dict[str, str]:
    entry: dict[str, str] = {}
    section = None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return entry
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            section = line
            continue
        if section != "[Desktop Entry]" or "=" not in line:
            continue
        key, value = line.split("=", 1)
        entry.setdefault(key.strip(), value.strip())
    return entry


def command_name(entry: dict[str, str]) -> str:
    """The program an Exec line runs: the Flatpak id, or the file name."""
    try:
        parts = shlex.split(entry.get("Exec", ""))
    except ValueError:
        parts = entry.get("Exec", "").split()
    parts = [part for part in parts if part != "env" and not re.match(r"^\w+=", part)]
    if not parts:
        return ""
    if Path(parts[0]).name == "flatpak" and "run" in parts:
        rest = [part for part in parts[parts.index("run") + 1 :] if not part.startswith("-")]
        return rest[0] if rest else ""
    name = Path(parts[0]).name
    return re.sub(r"\.appimage$", "", name, flags=re.I)


def all_entries() -> list[tuple[str, Path, dict[str, str]]]:
    """Every desktop entry, by id. The first directory wins, as in XDG."""
    seen: set[str] = set()
    entries = []
    for base in data_dirs():
        apps = base / "applications"
        if not apps.is_dir():
            continue
        for path in sorted(apps.rglob("*.desktop")):
            ident = str(path.relative_to(apps))[: -len(".desktop")].replace("/", "-")
            if ident in seen:
                continue
            seen.add(ident)
            entry = read_entry(path)
            if entry.get("Type", "Application") != "Application" or entry.get("Hidden") == "true":
                continue
            entries.append((ident, path, entry))
    return entries


def pacman_entries(package: str) -> list[Path]:
    """Desktop files a pacman or AUR package installed."""
    if not shutil.which("pacman"):
        return []
    listed = subprocess.run(["pacman", "-Qlq", package], capture_output=True, text=True, check=False)
    if listed.returncode != 0:
        return []
    return [
        Path(line)
        for line in listed.stdout.splitlines()
        if line.endswith(".desktop") and "/applications/" in line and Path(line).is_file()
    ]


def find_entry(query: str) -> tuple[str, Path, dict[str, str], list[str]]:
    """The desktop entry for an app name, and the other entries it matched."""
    wanted = re.sub(r"\.desktop$", "", query.strip(), flags=re.I).lower()
    entries = all_entries()
    ranked: list[tuple[int, str, Path, dict[str, str]]] = []
    for ident, path, entry in entries:
        lowered = ident.lower()
        keys = [
            (0, lowered),
            (1, entry.get("Name", "").lower()),
            (2, lowered.rsplit(".", 1)[-1]),
            (3, entry.get("StartupWMClass", "").lower()),
            (4, command_name(entry).lower()),
            (5, icon_name(entry.get("Icon", "")).lower()),
        ]
        rank = next((score for score, key in keys if key and key == wanted), None)
        if rank is not None:
            ranked.append((rank, ident, path, entry))
    if not ranked:
        by_path = {path.resolve(): (ident, entry) for ident, path, entry in entries}
        for desktop in pacman_entries(wanted):
            ident, entry = by_path.get(desktop.resolve(), (desktop.stem, read_entry(desktop)))
            ranked.append((6, ident, desktop, entry))
    if not ranked:
        loose = [
            (7, ident, path, entry)
            for ident, path, entry in entries
            if wanted in ident.lower() or wanted in entry.get("Name", "").lower()
        ]
        if len(loose) > 1:
            names = ", ".join(f"{ident} ({entry.get('Name', '?')})" for _, ident, _, entry in loose[:10])
            raise AppNotFound(f"{query} matches several apps: {names}. Pass one of those ids.")
        ranked = loose
    if not ranked:
        raise AppNotFound(f"no desktop entry matches {query}")
    ranked.sort(key=lambda item: item[0])
    _rank, ident, path, entry = ranked[0]
    others = [other for _, other, _, _ in ranked[1:] if other != ident]
    return ident, path, entry, others


# Icon lookup -----------------------------------------------------------------


def _size_of(path: Path) -> int:
    for part in reversed(path.parts):
        if part == "scalable":
            return 10_000
        match = re.match(r"^(\d+)(?:x\d+)?(?:@(\d+))?$", part)
        if match:
            return int(match.group(1)) * int(match.group(2) or 1)
    return 0


def _best(paths: list[Path]) -> Path | None:
    def score(path: Path) -> tuple[int, int, int]:
        vector = path.suffix in {".svg", ".svgz"}
        return (1 if vector else 0, _size_of(path), -len(path.parts))

    real = [path for path in paths if path.is_file()]
    return max(real, key=score) if real else None


def theme_icon(name: str, roots: list[Path]) -> Path | None:
    """The best file for an icon name: hicolor first, then any other theme, then pixmaps."""
    files = [f"{name}{suffix}" for suffix in ICON_SUFFIXES]
    others: list[Path] = []
    for base in roots:
        icons = base / "icons"
        hicolor = icons / "hicolor"
        if hicolor.is_dir():
            found = [path for file in files for path in hicolor.glob(f"*/*/{file}")]
            best = _best(found)
            if best:
                return best
        if icons.is_dir():
            for theme in sorted(icons.iterdir()):
                # The 1989 theme holds sprites already. Start from the original.
                if not theme.is_dir() or theme.name == "hicolor" or theme.name.startswith("1989"):
                    continue
                for file in files:
                    others += list(theme.glob(f"*/*/{file}"))
            others += [icons / file for file in files]
    best = _best(others)
    if best:
        return best
    return _best([base / "pixmaps" / file for base in roots for file in files])


def icon_name(value: str) -> str:
    """Icon= may carry an extension, which the theme lookup ignores."""
    name = Path(value).name
    for suffix in ICON_SUFFIXES:
        if name.lower().endswith(suffix):
            return name[: -len(suffix)]
    return name


def from_entry(ident: str, path: Path, entry: dict[str, str], *, notes: list[str] | None = None) -> Source:
    notes = list(notes or [])
    value = entry.get("Icon", "").strip()
    app = entry.get("Name") or ident
    if not value:
        raise AppNotFound(f"{path} has no Icon= line")
    if value.startswith("/"):
        icon = Path(value)
        if not icon.is_file():
            raise AppNotFound(f"{app}: its icon {value} does not exist")
        stem = icon_name(value)
        notes.append(
            f"{app} loads its icon from a file path ({value}), so no icon theme can replace it. "
            f"Set Icon={stem} in {path} to use the 1989 sprite."
        )
    else:
        stem = icon_name(value)
        icon = theme_icon(stem, data_dirs())
        if icon is None:
            raise AppNotFound(f"{app}: no icon file named {stem} in the icon themes or pixmaps")
    text, more = read_icon(icon)
    return Source(text, stem, "apps", app, f"{app} ({path.name}) -> {icon}", notes + more)


# AppImage --------------------------------------------------------------------


def is_appimage(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            head = handle.read(11)
    except OSError:
        return False
    # ELF with the AppImage magic "AI" and type 1 or 2 at byte 8.
    return head[:4] == b"\x7fELF" and head[8:10] == b"AI" and head[10] in (1, 2)


def squashfs_offset(path: Path) -> int:
    """Where the squashfs image starts: after the ELF runtime."""
    with path.open("rb") as handle:
        header = handle.read(64)
        is64 = header[4] == 2
        endian = "<" if header[5] == 1 else ">"
        if is64:
            shoff = struct.unpack_from(endian + "Q", header, 0x28)[0]
            entsize, count = struct.unpack_from(endian + "HH", header, 0x3A)
        else:
            shoff = struct.unpack_from(endian + "I", header, 0x20)[0]
            entsize, count = struct.unpack_from(endian + "HH", header, 0x2E)
        offset = shoff + entsize * count
        handle.seek(offset)
        if handle.read(4) == b"hsqs":
            return offset
        handle.seek(0)
        blob = handle.read(16 * 1024 * 1024)
    found = blob.find(b"hsqs", 4096)
    if found < 0:
        raise ValueError(f"{path.name}: no squashfs image found; only type 2 AppImages are supported")
    return found


def extract_appimage(path: Path, dest: Path) -> Path:
    """Unpack the desktop file and icons. The AppImage itself is not run."""
    patterns = ["*.desktop", ".DirIcon", "*.svg", "*.svgz", "*.png", "*.xpm", "usr/share/icons", "usr/share/pixmaps"]
    root = dest / "squashfs-root"
    if shutil.which("unsquashfs"):
        offset = squashfs_offset(path)
        subprocess.run(
            ["unsquashfs", "-q", "-n", "-f", "-o", str(offset), "-d", str(root), str(path), *patterns],
            capture_output=True,
            check=False,
        )
        if root.is_dir():
            return root
    raise ValueError(f"{path.name}: install squashfs-tools (unsquashfs) to read icons from AppImages")


def from_appimage(path: Path, notes: list[str] | None = None) -> Source:
    notes = list(notes or [])
    with tempfile.TemporaryDirectory(prefix="1989-appimage-") as tmp:
        root = extract_appimage(path, Path(tmp))
        desktops = sorted(root.glob("*.desktop"))
        entry = read_entry(desktops[0]) if desktops else {}
        app = entry.get("Name") or path.stem
        stem = icon_name(entry.get("Icon", "")) if entry.get("Icon") else ""
        icon = None
        if stem:
            icon = _best([root / f"{stem}{suffix}" for suffix in ICON_SUFFIXES])
            icon = icon or theme_icon(stem, [root / "usr" / "share"])
        dir_icon = root / ".DirIcon"
        if icon is None and dir_icon.is_file():
            icon = dir_icon
        if icon is None:
            raise AppNotFound(f"{path.name}: no icon inside the AppImage")
        stem = stem or re.sub(r"[-_ ]?(x86_64|aarch64|amd64|v?\d[\w.]*)$", "", path.stem, flags=re.I) or path.stem
        text, more = read_icon(icon)
    notes.append(
        f"wrote it as {stem}. If the menu entry for this AppImage uses another Icon= name "
        "(AppImageLauncher writes appimagekit_...), pass that app name instead."
    )
    return Source(text, stem, "apps", app, f"{app} ({path.name})", notes + more)


# Sources ---------------------------------------------------------------------


def resolve(arg: str, name: str | None, context: str | None) -> Source:
    path = Path(arg).expanduser()
    if path.is_file():
        suffix = path.suffix.lower()
        if suffix == ".desktop":
            entry = read_entry(path)
            source = from_entry(path.stem, path, entry)
        elif suffix == ".appimage" or is_appimage(path):
            source = from_appimage(path)
        elif suffix in IMAGE_SUFFIXES:
            text, notes = read_icon(path)
            stem = path.name[: -len(path.suffix)]
            source = Source(text, stem, context or guess_context(path), None, str(path), notes)
        else:
            raise ValueError(f"{path.name}: use an icon (.svg, .svgz, .png, .xpm), a .desktop file, or an AppImage")
    elif "/" in arg or Path(arg).suffix.lower() in IMAGE_SUFFIXES:
        raise ValueError(f"{arg}: no such file")
    else:
        ident, entry_path, entry, others = find_entry(arg)
        notes = [f"{arg} also matched {', '.join(others)}; used {ident}"] if others else []
        source = from_entry(ident, entry_path, entry, notes=notes)
    if name:
        source.stem = name[:-4] if name.endswith(".svg") else name
    if context:
        source.context = context
    return source


def guess_context(path: Path) -> str:
    """A file dropped from inside an icon theme keeps that theme's context."""
    for part in reversed(path.resolve().parent.parts):
        base = part.replace("@2x", "")
        if base in CONTEXTS:
            return base
    return "apps"


# Writing ---------------------------------------------------------------------


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


def write(source: Source, *, theme: Path, keep: bool) -> list[Path]:
    context = source.context or "apps"
    stem = source.stem
    label = source.label or label_for(source.text, Path(stem + ".svg"))
    written: list[Path] = []
    for size in target_dirs(theme, context, stem.endswith("-symbolic")):
        canvas, grid = size_geometry(size)
        dest = theme / context / size / f"{stem}.svg"
        sprite = readable(flatten_svg(source.text, label=label, canvas=canvas, grid=grid), dest, theme)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(sprite, encoding="utf-8")
        written.append(dest)

        double, double_grid = size_geometry(size, doubled=True)
        twin = theme / f"{context}@2x" / size / f"{stem}.svg"
        doubled = scale_sprite(sprite, double)
        if doubled is None:
            doubled = readable(flatten_svg(source.text, label=label, canvas=double, grid=double_grid), twin, theme)
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


# Desktop integration ----------------------------------------------------------


def notify(title: str, body: str, error: bool = False) -> None:
    """Report to the desktop when there is no terminal to read."""
    if shutil.which("kdialog"):
        kind = "--error" if error else "--passivepopup"
        args = ["kdialog", "--title", title, kind, body]
        if not error:
            args.append("10")
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
        "Comment=Drop icons, apps from the menu, or AppImages here to add their icons to the 1989 theme\n"
        f"Exec={command}\n"
        "Icon=cachyos\n"
        "Terminal=false\n"
        "MimeType=image/svg+xml;image/svg+xml-compressed;image/png;image/x-xpixmap;"
        "application/x-desktop;application/vnd.appimage;application/x-iso9660-appimage;\n"
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
    parser.add_argument(
        "items",
        nargs="*",
        help="icon files (.svg .svgz .png .xpm), .desktop files, AppImages, or app names",
    )
    parser.add_argument("--name", help="icon name to write (one item only)")
    parser.add_argument(
        "--context",
        choices=CONTEXTS,
        help="theme context (default: apps, or the icon file's folder)",
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
    if args.name and len(args.items) > 1:
        parser.error("--name works with one item only")
    if not args.items and not args.make_launcher:
        parser.error("pass one or more icon files, desktop files, AppImages, or app names")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.make_launcher:
        where = desktop_dir() if args.make_launcher is True else Path(args.make_launcher).expanduser()
        print(make_launcher(where))
        return 0
    if not shutil.which("rsvg-convert"):
        message = "rsvg-convert is missing. Install librsvg and try again."
        print(message, file=sys.stderr)
        if args.notify:
            notify("1989 icons", message, error=True)
        return 1

    added: list[str] = []
    failed: list[str] = []
    notes: list[str] = []
    for item in args.items:
        try:
            source = resolve(item, args.name, args.context)
            written = write(source, theme=args.theme, keep=not args.no_tuned)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            failed.append(str(exc))
            print(f"error: {exc}", file=sys.stderr)
            continue
        print(f"{source.origin}")
        for dest in written:
            print("  " + str(dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest))
        for note in source.notes:
            print(f"  note: {note}", file=sys.stderr)
        notes += source.notes
        added.append(source.stem)

    if args.notify:
        if failed:
            notify("1989 icons", "\n".join(failed), error=True)
        if added:
            body = "Added: " + ", ".join(added)
            if notes:
                body += "\n" + "\n".join(notes)
            notify("1989 icons", body)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
