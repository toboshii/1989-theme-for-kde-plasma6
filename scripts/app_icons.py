#!/usr/bin/env python3
"""Keep each app icon's original drawing and its own colors.

Gloss is removed: shadow filters go away, and gradients become the flat
color already in that gradient. Nothing is redrawn and nothing is mapped
onto the theme scheme.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

SOURCE = Path("/home/daniel/.local/share/icons/ColorFlow.Agresive.Color")
KEEP_NAMES = {"cachyos.svg"}
TUNED = Path(__file__).resolve().parent / "tuned"


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def is_neutral(value: str) -> bool:
    red, green, blue = hex_rgb(value)
    return max(red, green, blue) - min(red, green, blue) < 18


def style_colors(text: str) -> dict[str, str]:
    found = re.findall(
        r"\.(ColorScheme-[\w-]+)\s*\{[^}]*?color:\s*(#[0-9A-Fa-f]{3,8})",
        text,
        flags=re.I | re.S,
    )
    return {name: color for name, color in found}


def gradient_colors(text: str) -> dict[str, list[str]]:
    colors: dict[str, list[str]] = {}
    for match in re.finditer(
        r"<(?:linear|radial)Gradient\b([^>]*)>(.*?)</(?:linear|radial)Gradient>",
        text,
        flags=re.I | re.S,
    ):
        attrs, body = match.group(1), match.group(2)
        ident = re.search(r'\bid="([^"]+)"', attrs)
        if not ident:
            continue
        stops = re.findall(
            r"stop-color:\s*(#[0-9A-Fa-f]{3,8})|stop-color=\"(#[0-9A-Fa-f]{3,8})\"",
            body,
            flags=re.I,
        )
        flat = [a or b for a, b in stops]
        colors[ident.group(1)] = flat
    return colors


def flat_color(stops: list[str]) -> str | None:
    if not stops:
        return None
    chromatic = [color for color in stops if not is_neutral(color)]
    pool = chromatic or stops
    return pool[len(pool) // 2]


def strip_gloss(text: str) -> str:
    text = re.sub(r"<filter\b[^>]*>.*?</filter>", "", text, flags=re.I | re.S)
    text = re.sub(r"\sfilter=\"url\(#[^)]+\)\"", "", text)
    # Soft shadow discs: a neutral fill, mostly transparent, that only existed to blur.
    text = re.sub(
        r"<circle\b[^>]*(?:opacity=\"0?\.[0-4][^\"]*\"[^>]*fill=\"#(?:000|111|222|333)\"|fill=\"#(?:000|111|222|333)\"[^>]*opacity=\"0?\.[0-4][^\"]*\")[^>]*/>",
        "",
        text,
        flags=re.I,
    )
    return text


def bake(text: str, *, flatten_gradients: bool = True) -> str:
    text = strip_gloss(text)
    classes = style_colors(text)
    gradients = gradient_colors(text)
    referenced = set(re.findall(r"url\(#([^)]+)\)", text))
    unused = [flat_color(gradients[name]) for name in gradients if name not in referenced]
    unused = [color for color in unused if color and not is_neutral(color)]
    spare = unused[0] if unused else None

    def paint(role: str | None) -> str | None:
        if role and role in classes:
            return classes[role]
        return spare

    def replace_tag(match: re.Match[str]) -> str:
        tag = match.group(0)
        if tag.startswith("</"):
            return tag
        role_match = re.search(r'class="(ColorScheme-[\w-]+)"', tag)
        role = role_match.group(1) if role_match else None
        has_current = "currentColor" in tag
        if has_current and re.search(r"fill:\s*#[0-9A-Fa-f]{3,8}", tag):
            tag = tag.replace(' fill="currentColor"', "").replace('fill="currentColor"', "")
            has_current = "currentColor" in tag
        if has_current and role:
            color = paint(role)
            if color:
                tag = re.sub(r'fill="currentColor"', f'fill="{color}"', tag)
                tag = re.sub(r"fill:\s*currentColor", f"fill:{color}", tag)
        if role:
            tag = re.sub(r'\sclass="ColorScheme-[\w-]+"', "", tag)
        return tag

    text = re.sub(r"<[^>]+>", replace_tag, text)

    if flatten_gradients:
        for name, stops in gradients.items():
            color = flat_color(stops)
            if not color:
                continue
            text = text.replace(f"url(#{name})", color)
            text = text.replace(f"fill:{color}", f"fill:{color}")
    # url(#id) became a bare hex. Repair the attributes that pointed at it.
    text = re.sub(r'fill="(#[0-9A-Fa-f]{3,8})"', r'fill="\1"', text)
    text = re.sub(r"fill:\s*(#[0-9A-Fa-f]{3,8})", r"fill:\1", text)
    text = re.sub(
        r"<style\b[^>]*id=\"current-color-scheme\".*?</style>",
        "",
        text,
        flags=re.I | re.S,
    )
    return text


def source_marks(source: Path) -> list[tuple[bytes, str]]:
    """Tuned drawings that replace every copy of one source icon."""
    found = []
    for name in ("utilities-terminal.svg", "google-chrome.svg"):
        mark = TUNED / name
        src = source / "apps" / "scalable" / name
        if not mark.is_file() or not src.is_file():
            continue
        found.append((src.read_bytes(), mark.read_text()))
    return found


def apply(root: Path, source: Path = SOURCE) -> tuple[int, int]:
    written = 0
    removed = 0
    marks = source_marks(source)
    for folder in ("apps", "apps@2x"):
        src_root = source / folder
        dst_root = root / folder
        if not src_root.is_dir():
            continue
        for src in src_root.rglob("*"):
            if not src.is_file() or src.suffix != ".svg":
                continue
            rel = src.relative_to(src_root)
            dst = dst_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                raw_bytes = src.read_bytes()
            except OSError:
                continue
            replacement = next((text for raw, text in marks if raw_bytes == raw), None)
            if replacement is not None:
                dst.write_text(replacement)
                written += 1
                continue
            dst.write_text(bake(raw_bytes.decode("utf-8", errors="ignore")))
            written += 1
        if not dst_root.is_dir():
            continue
        for dst in dst_root.rglob("*.svg"):
            rel = dst.relative_to(dst_root)
            if dst.name in KEEP_NAMES:
                continue
            if not (src_root / rel).is_file():
                dst.unlink()
                removed += 1
    if TUNED.is_dir():
        for src in TUNED.glob("*.svg"):
            dest = root / "apps" / "scalable" / src.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(src.read_text())
    return written, removed


def main() -> None:
    for arg in sys.argv[1:]:
        written, removed = apply(Path(arg))
        print(arg, "restored", written, "removed", removed)


if __name__ == "__main__":
    main()
