#!/usr/bin/env python3
"""Make system sprites readable on the dark 1989 field.

Menu drawings are flattened again from the original icon, so the symbol
survives. Anywhere else, ink that disappears into the field is lifted to
the theme text color, or lightened along its own hue.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flatten_icon import flatten_svg, label_for, size_geometry

FIELD = (0x18, 0x18, 0x21)
TEXT = (0xBD, 0xC5, 0xE3)
TITLE = (0xCD, 0xD6, 0xF4)
DIM = (0x8D, 0x93, 0x9F)
READABLE = 3.0
TARGET = 4.5
# A light plate, or a light glyph on a dark tile, is already readable.
LIGHT_SHARE = 0.62
BRIGHT_LUMA = 170
BRIGHT_SHARE = 0.12

SYSTEM = {
    "actions",
    "status",
    "categories",
    "places",
    "devices",
    "emblems",
    "animations",
    "mimes",
}
SKIP = {"cachyos.svg"}


def _channel(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def contrast(color: tuple[int, int, int], against: tuple[int, int, int] = FIELD) -> float:
    def lum(rgb: tuple[int, int, int]) -> float:
        red, green, blue = (_channel(c / 255) for c in rgb)
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    light, dark = lum(color), lum(against)
    if light < dark:
        light, dark = dark, light
    return (light + 0.05) / (dark + 0.05)


def chroma(color: tuple[int, int, int]) -> int:
    return max(color) - min(color)


def luma(color: tuple[int, int, int]) -> float:
    red, green, blue = color
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def parse_hex(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def hex_of(color: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color)


def lighten(color: tuple[int, int, int]) -> tuple[int, int, int]:
    """Raise a dark chromatic color until it clears the field."""
    import colorsys

    red, green, blue = (c / 255 for c in color)
    hue, light, sat = colorsys.rgb_to_hls(red, green, blue)
    sat = min(sat, 0.7)
    best = color
    step = light
    for _ in range(18):
        step = min(0.84, step + 0.06)
        out = colorsys.hls_to_rgb(hue, step, sat)
        best = tuple(max(0, min(255, round(c * 255))) for c in out)  # type: ignore[assignment]
        if contrast(best) >= TARGET:
            return best
    return best


def area_of(attrs: str) -> int:
    match = re.search(r'\bd="([^"]*)"', attrs)
    if not match:
        return 1
    total = 0
    for width, height in re.findall(r"h(-?\d+)v(\d+)", match.group(1)):
        total += abs(int(width)) * int(height)
    return total or 1


def fills(text: str) -> list[tuple[str, tuple[int, int, int], int]]:
    found = []
    for raw, attrs in re.findall(r'fill="#([0-9A-Fa-f]{3,8})"([^>]*)', text):
        found.append((raw, parse_hex(raw), area_of(attrs)))
    return found


def mapping_for(text: str, *, force_dark: bool = False) -> dict[str, str]:
    parts = fills(text)
    if not parts:
        return {}
    painted = sum(area for _, _, area in parts) or 1
    light = sum(area for _, color, area in parts if contrast(color) >= READABLE)
    bright = sum(area for _, color, area in parts if luma(color) >= BRIGHT_LUMA)
    # Tray sprites often pair a light glyph with a black stroke. The stroke
    # is most of the drawing and disappears on the field, so status icons
    # always lift that ink even when the rest of the sprite is already light.
    if not force_dark and (light / painted >= LIGHT_SHARE or bright / painted >= BRIGHT_SHARE):
        return {}
    neutrals = []
    mapped: dict[str, str] = {}
    for raw, color, _area in parts:
        if contrast(color) >= READABLE:
            continue
        key = raw.upper() if len(raw) > 3 else "".join(ch * 2 for ch in raw).upper()
        if chroma(color) < 32:
            neutrals.append((luma(color), key))
            continue
        mapped[key] = hex_of(lighten(color))
    ladder = (DIM, TEXT, TITLE)
    ordered = []
    for _, key in sorted(neutrals):
        if key not in ordered:
            ordered.append(key)
    if len(ordered) == 1:
        mapped[ordered[0]] = hex_of(TEXT)
    else:
        for index, key in enumerate(ordered):
            slot = min(index, len(ladder) - 1)
            mapped[key] = hex_of(ladder[slot])
    # Drop no-op replacements.
    return {key: value for key, value in mapped.items() if key != value.lstrip("#").upper()}


def apply_mapping(text: str, mapped: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        raw = match.group(1)
        key = raw.upper() if len(raw) > 3 else "".join(ch * 2 for ch in raw).upper()
        if key in mapped:
            return f'fill="{mapped[key]}"'
        return match.group(0)

    return re.sub(r'fill="#([0-9A-Fa-f]{3,8})"', repl, text)


def system_icon(path: Path, root: Path) -> bool:
    if path.name in SKIP:
        return False
    ctx = path.relative_to(root).parts[0].replace("@2x", "")
    if ctx in SYSTEM:
        return True
    if ctx != "apps":
        return False
    stem = path.stem
    return stem.startswith("applications-") or stem.startswith("preferences-") or "notification" in stem


def reflatten_sources(root: Path, source: Path) -> int:
    """Redraw menu and notification icons from the original file.

    The first flatten had already replaced those drawings with a flat
    scheme shape, so the hammer, paperclip, and mute stroke were gone.
    """
    count = 0
    for dest in root.rglob("*.svg"):
        rel = dest.relative_to(root)
        ctx = rel.parts[0].replace("@2x", "")
        stem = dest.stem
        menu = stem.startswith("applications-") and ctx in {"categories", "apps"}
        bell = "notification" in stem and ctx in {"actions", "status", "apps"}
        if not menu and not bell:
            continue
        if "symbolic" in dest.parts or stem.endswith("-symbolic"):
            continue
        # A 2x sprite is already the doubled grid. Reflattening it from the
        # 1x source would bake it back onto a 64 canvas.
        if "@2x" in rel.parts[0]:
            continue
        src = source / rel
        if not src.is_file():
            continue
        text = src.read_text(encoding="utf-8", errors="replace")
        size = rel.parts[1] if len(rel.parts) > 1 else "scalable"
        canvas, grid = size_geometry(size)
        dest.write_text(flatten_svg(text, label=label_for(text, dest), canvas=canvas, grid=grid))
        count += 1
    return count


def lift(root: Path) -> int:
    changed = 0
    for path in root.rglob("*.svg"):
        if not system_icon(path, root):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        ctx = path.relative_to(root).parts[0].replace("@2x", "")
        mapped = mapping_for(text, force_dark=ctx == "status")
        if not mapped:
            continue
        updated = apply_mapping(text, mapped)
        if updated != text:
            path.write_text(updated)
            changed += 1
    return changed


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    source = Path("/home/daniel/.local/share/icons/ColorFlow.Agresive.Color")
    roots: list[Path] = []
    i = 0
    while i < len(args):
        if args[i] == "--source":
            source = Path(args[i + 1])
            i += 2
            continue
        roots.append(Path(args[i]))
        i += 1
    if not roots:
        print("pass the icon theme root", file=sys.stderr)
        return 1
    for root in roots:
        menus = reflatten_sources(root, source) if source.is_dir() else 0
        changed = lift(root)
        print(root, "menus", menus, "lifted", changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
