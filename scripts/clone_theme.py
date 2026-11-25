#!/usr/bin/env python3
"""Copy the live Catppuccin Mocha and ColorFlow assets, then modify the copies.

Sources are read only. Output is the 1989 packages under ../out.
"""

from __future__ import annotations

import gzip
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
HOME = Path.home()
MOCHA_PLASMA = HOME / ".local/share/plasma/desktoptheme/Catppuccin.Mocha"
MOCHA_AURORAE = HOME / ".local/share/aurorae/themes/Catppuccin.Mocha"
MOCHA_COLORS = HOME / ".local/share/color-schemes/CatppuccinMocha.colors"
MOCHA_KONSOLE = HOME / ".local/share/konsole/CatppuccinMocha.colorscheme"
MOCHA_LNF = HOME / ".local/share/plasma/look-and-feel/Catppuccin.Mocha"
ICONS = HOME / ".local/share/icons/ColorFlow.Agresive.Color"

FIELD = "24,24,33"
TEXT = "189,197,227"
TITLE = "205,214,244"
DIM = "141,147,159"
GREEN = "166,227,161"
INK = "34,36,37"
FONT = "Hack,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"

# DecorationFocus in the Mocha file is this mauve. Selection uses it too.
MAUVE = "209,183,241"

VARIANTS = {
    "1989": {
        "name": "1989",
        "gtk": "1989",
        "accent": "221,157,137",
        "accent_hex": "#dd9d89",
        "selection": "209,183,241",
        "negative": "221,157,137",
        "link": "190,134,198",
        "positive": GREEN,
        "konsole": {"4": "137,180,250", "5": "209,183,241", "1": "243,139,168", "6": "148,226,213"},
    },
    "1989Mocha": {
        "name": "1989 Mocha",
        "gtk": "1989-Mocha",
        "accent": "203,166,247",
        "accent_hex": "#cba6f7",
        "selection": "203,166,247",
        "negative": "243,139,168",
        "link": "245,194,231",
        "positive": GREEN,
        "konsole": {"4": "137,180,250", "5": "203,166,247", "1": "243,139,168", "6": "148,226,213"},
    },
    "1989Blue": {
        "name": "1989 Blue",
        "gtk": "1989-Blue",
        "accent": "123,165,227",
        "accent_hex": "#7ba5e3",
        "selection": "123,165,227",
        "negative": "180,97,118",
        "link": "156,166,223",
        "positive": GREEN,
        "konsole": {"4": "123,165,227", "5": "156,166,223", "1": "180,97,118", "6": "116,184,198"},
    },
    "1989Green": {
        "name": "1989 Green",
        "gtk": "1989-Green",
        "accent": "111,154,114",
        "accent_hex": "#6f9a72",
        "selection": "111,154,114",
        "negative": "180,97,118",
        "link": "94,150,142",
        "positive": "94,150,142",
        "konsole": {"4": "94,150,142", "5": "111,154,114", "1": "180,97,118", "6": "94,150,142"},
    },
    "1989Red": {
        "name": "1989 Red",
        "gtk": "1989-Red",
        "accent": "180,97,118",
        "accent_hex": "#b46176",
        "selection": "180,97,118",
        "negative": "158,101,112",
        "link": "180,97,118",
        "positive": "111,154,114",
        "konsole": {"4": "158,101,112", "5": "180,97,118", "1": "180,97,118", "6": "158,101,112"},
    },
}

PLACE_ROLE = {
    "folder": "ColorScheme-Highlight",
    "folder-open": "ColorScheme-Highlight",
    "folder-documents": "ColorScheme-Highlight",
    "folder-text": "ColorScheme-Highlight",
    "folder-download": "ColorScheme-NegativeText",
    "folder-downloads": "ColorScheme-NegativeText",
    "folder-music": "ColorScheme-NeutralText",
    "folder-sound": "ColorScheme-NeutralText",
    "folder-pictures": "ColorScheme-PositiveText",
    "folder-picture": "ColorScheme-PositiveText",
    "folder-image": "ColorScheme-PositiveText",
    "folder-images": "ColorScheme-PositiveText",
    "folder-videos": "ColorScheme-NegativeText",
    "folder-video": "ColorScheme-NegativeText",
    "folder-movies": "ColorScheme-NegativeText",
    "user-home": "ColorScheme-Highlight",
    "user-desktop": "ColorScheme-Text",
    "user-documents": "ColorScheme-Highlight",
    "user-downloads": "ColorScheme-NegativeText",
    "user-music": "ColorScheme-NeutralText",
    "user-pictures": "ColorScheme-PositiveText",
    "user-videos": "ColorScheme-NegativeText",
}

SCHEME_STYLE = """<style id="current-color-scheme" type="text/css">
.ColorScheme-Text { color:#bdc5e3; }
.ColorScheme-Highlight { color:#dd9d89; }
.ColorScheme-PositiveText { color:#a6e3a1; }
.ColorScheme-NeutralText { color:#d1b7f1; }
.ColorScheme-NegativeText { color:#f38ba8; }
</style>
"""


def read_svg(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    if b"<svg" not in data[:500] and b"<svg" not in data[:2000]:
        return None
    return data.decode("utf-8", "ignore")


def square_svg(text: str, accent_hex: str) -> str:
    text = text.replace('rx="', 'data-rx="').replace("rx='", "data-rx='")
    for token in ("#d1b7f1", "#D1B7F1", "#e4d4f7", "#E4D4F7", "#cba6f7", "#CBA6F7"):
        text = text.replace(token, accent_hex)
    return text


SHADOW = 28
HAIR = 1
TITLE_BAR = 28
FRAME_CENTER = 40
FRAME_LEFT = SHADOW + HAIR
FRAME_TOP = SHADOW + TITLE_BAR
FRAME_RIGHT = FRAME_LEFT
FRAME_BOTTOM = FRAME_LEFT


def _shade(grad_id: str, x1: str, y1: str, x2: str, y2: str) -> str:
    return (
        f'<linearGradient id="{grad_id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#08080e" stop-opacity="0"/>'
        '<stop offset="0.45" stop-color="#08080e" stop-opacity="0.05"/>'
        '<stop offset="1" stop-color="#08080e" stop-opacity="0.42"/>'
        "</linearGradient>"
    )


def _corner_shade(grad_id: str, cx: str, cy: str) -> str:
    # Same curve as the edge shade, measured outward from the inner corner.
    # Offset 0.55 is the edge stop at 0.45, seen from the window.
    return (
        f'<radialGradient id="{grad_id}" cx="{cx}" cy="{cy}" r="{SHADOW}" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#08080e" stop-opacity="0.42"/>'
        '<stop offset="0.55" stop-color="#08080e" stop-opacity="0.05"/>'
        '<stop offset="1" stop-color="#08080e" stop-opacity="0"/>'
        "</radialGradient>"
    )


def _frame_parts(prefix: str, accent: str) -> str:
    s, h, t, c = SHADOW, HAIR, TITLE_BAR, FRAME_CENTER
    left, top = FRAME_LEFT, FRAME_TOP
    x1 = left + c
    y1 = top + c
    field = "#181821"
    return f'''
  <g id="{prefix}-topleft">
    <rect x="0" y="0" width="{s + h}" height="{s}" fill="url(#{prefix}-tl)"/>
    <rect x="0" y="{s}" width="{s}" height="{t}" fill="url(#{prefix}-tl-side)"/>
    <rect x="{s}" y="{s}" width="{h}" height="{t}" fill="{accent}"/>
  </g>
  <g id="{prefix}-top">
    <rect x="{left}" y="0" width="{c}" height="{s}" fill="url(#{prefix}-top-shade)"/>
    <rect x="{left}" y="{s}" width="{c}" height="{h}" fill="{accent}"/>
    <rect x="{left}" y="{s + h}" width="{c}" height="{t - h}" fill="{field}"/>
  </g>
  <g id="{prefix}-topright">
    <rect x="{x1}" y="0" width="{s + h}" height="{s}" fill="url(#{prefix}-tr)"/>
    <rect x="{x1 + h}" y="{s}" width="{s}" height="{t}" fill="url(#{prefix}-tr-side)"/>
    <rect x="{x1}" y="{s}" width="{h}" height="{t}" fill="{accent}"/>
  </g>
  <g id="{prefix}-left">
    <rect x="0" y="{top}" width="{s}" height="{c}" fill="url(#{prefix}-left-shade)"/>
    <rect x="{s}" y="{top}" width="{h}" height="{c}" fill="{accent}"/>
  </g>
  <rect id="{prefix}-center" x="{left}" y="{top}" width="{c}" height="{c}" fill="{field}"/>
  <g id="{prefix}-right">
    <rect x="{x1 + h}" y="{top}" width="{s}" height="{c}" fill="url(#{prefix}-right-shade)"/>
    <rect x="{x1}" y="{top}" width="{h}" height="{c}" fill="{accent}"/>
  </g>
  <g id="{prefix}-bottomleft">
    <rect x="0" y="{y1 + h}" width="{s + h}" height="{s}" fill="url(#{prefix}-bl)"/>
    <rect x="0" y="{y1}" width="{s}" height="{h}" fill="url(#{prefix}-left-shade)"/>
    <rect x="{s}" y="{y1}" width="{h}" height="{h}" fill="{accent}"/>
  </g>
  <g id="{prefix}-bottom">
    <rect x="{left}" y="{y1 + h}" width="{c}" height="{s}" fill="url(#{prefix}-bottom-shade)"/>
    <rect x="{left}" y="{y1}" width="{c}" height="{h}" fill="{accent}"/>
  </g>
  <g id="{prefix}-bottomright">
    <rect x="{x1}" y="{y1 + h}" width="{s + h}" height="{s}" fill="url(#{prefix}-br)"/>
    <rect x="{x1 + h}" y="{y1}" width="{s}" height="{h}" fill="url(#{prefix}-right-shade)"/>
    <rect x="{x1}" y="{y1}" width="{h}" height="{h}" fill="{accent}"/>
  </g>'''


def _frame_defs(prefix: str) -> str:
    s = str(SHADOW)
    left = FRAME_LEFT
    top = FRAME_TOP
    width = left + FRAME_CENTER + FRAME_RIGHT
    height = top + FRAME_CENTER + FRAME_BOTTOM
    x1 = left + FRAME_CENTER
    y1 = top + FRAME_CENTER
    return "\n".join(
        [
            _corner_shade(f"{prefix}-tl", s, s),
            _shade(f"{prefix}-tl-side", "0", s, s, s),
            _shade(f"{prefix}-top-shade", str(left), "0", str(left), s),
            _corner_shade(f"{prefix}-tr", str(x1 + HAIR), s),
            _shade(f"{prefix}-tr-side", str(width), s, str(x1 + HAIR), s),
            _shade(f"{prefix}-left-shade", "0", str(top), s, str(top)),
            _shade(f"{prefix}-right-shade", str(width), str(top), str(x1 + HAIR), str(top)),
            _corner_shade(f"{prefix}-bl", s, str(y1 + HAIR)),
            _shade(f"{prefix}-bottom-shade", str(left), str(height), str(left), str(y1 + HAIR)),
            _corner_shade(f"{prefix}-br", str(x1 + HAIR), str(y1 + HAIR)),
        ]
    )


def decoration_svg(accent: str) -> str:
    # Outer 28px is the shadow. The 1px accent is the first pixel inside that,
    # so the line sits on the window and the shadow hangs outside it.
    left, top = FRAME_LEFT, FRAME_TOP
    width = left + FRAME_CENTER + FRAME_RIGHT
    height = top + FRAME_CENTER + FRAME_BOTTOM
    hints = f"""
  <rect id="hint-left-margin" x="{width + 8}" y="0" width="{left}" height="4" fill="#ff00ff"/>
  <rect id="hint-right-margin" x="{width + 8}" y="8" width="{FRAME_RIGHT}" height="4" fill="#ff00ff"/>
  <rect id="hint-top-margin" x="{width + 8}" y="16" width="4" height="{top}" fill="#00ff00"/>
  <rect id="hint-bottom-margin" x="{width + 8}" y="{20 + top}" width="4" height="{FRAME_BOTTOM}" fill="#00ffff"/>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width + left + 16}" height="{height}" viewBox="0 0 {width + left + 16} {height}">
  <defs>
    {_frame_defs("decoration")}
    {_frame_defs("decoration-inactive")}
  </defs>
  {_frame_parts("decoration", accent)}
  {_frame_parts("decoration-inactive", "#6c7086")}
  <rect id="decoration-maximized-center" x="{left}" y="{top}" width="{FRAME_CENTER}" height="{FRAME_CENTER}" fill="#181821"/>
  <rect id="decoration-maximized-inactive-center" x="{left}" y="{top}" width="{FRAME_CENTER}" height="{FRAME_CENTER}" fill="#181821"/>
  {hints}
</svg>
"""


def button_svg(kind: str, accent: str) -> str:
    if kind == "close":
        mark = f'<path d="M4 4 L12 12 M12 4 L4 12" stroke="{accent}" stroke-width="1.4" fill="none"/>'
        idle = '<path d="M4 4 L12 12 M12 4 L4 12" stroke="#cdd6f4" stroke-width="1.4" fill="none"/>'
    elif kind == "minimize":
        mark = f'<path d="M3 8 H13" stroke="{accent}" stroke-width="1.4" fill="none"/>'
        idle = '<path d="M3 8 H13" stroke="#cdd6f4" stroke-width="1.4" fill="none"/>'
    else:
        mark = f'<rect x="4" y="4" width="8" height="8" fill="none" stroke="{accent}" stroke-width="1.2"/>'
        idle = '<rect x="4" y="4" width="8" height="8" fill="none" stroke="#cdd6f4" stroke-width="1.2"/>'
    dim = idle.replace("#cdd6f4", "#8d939f")
    parts = [
        f'<g id="active-center">{idle}</g>',
        f'<g id="hover-center">{mark}</g>',
        f'<g id="pressed-center">{mark}</g>',
        f'<g id="inactive-center">{dim}</g>',
        f'<g id="deactivated-center">{dim}</g>',
    ]
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">\n' + "\n".join(parts) + "\n</svg>\n"


def aurorae_rc(name: str) -> str:
    # Padding is the shadow. Border 1 survives BorderSize=Tiny (clamp 1..4).
    # Title bar is TitleHeight + TitleEdgeTop + TitleEdgeBottom = 28.
    return f"""[General]
ActiveTextColor={TITLE}
InactiveTextColor=166,173,200
LeftButtons=XIA
RightButtons=
Shadow=true
TextShadowOffsetX=1
TextShadowOffsetY=1
TitleAlignment=Center
TitleVerticalAlignment=Center
UseTextShadow=false
HaloActive=false
HaloInactive=false

[Layout]
ButtonHeight=14
ButtonWidth=14
ButtonMarginTop=1
ButtonSpacing=8
ExplicitButtonSpacer=8
BorderLeft=1
BorderRight=1
BorderBottom=1
BorderTop=0
PaddingBottom={SHADOW}
PaddingLeft={SHADOW}
PaddingRight={SHADOW}
PaddingTop={SHADOW}
TitleEdgeBottom=6
TitleEdgeBottomMaximized=4
TitleEdgeLeft=10
TitleEdgeLeftMaximized=8
TitleEdgeRight=10
TitleEdgeRightMaximized=8
TitleEdgeTop=6
TitleEdgeTopMaximized=4
TitleHeight=16
"""


def color_scheme(key: str, v: dict) -> str:
    text = MOCHA_COLORS.read_text()
    text = text.replace("Name=Catppuccin Mocha", f"Name={v['name']}")
    text = text.replace("ColorScheme=RichTealSea", f"ColorScheme={key}")
    # Focus ring and title accent follow the variation. Selection is its own color.
    lines = []
    section = ""
    for line in text.splitlines():
        if line.startswith("[") and line.endswith("]"):
            section = line
        elif line.startswith("DecorationFocus=") or line.startswith("DecorationHover="):
            line = line.split("=", 1)[0] + "=" + v["accent"]
        elif section == "[Colors:Selection]" and line.startswith("BackgroundNormal="):
            line = "BackgroundNormal=" + v["selection"]
        elif line.startswith("ForegroundLink="):
            line = "ForegroundLink=" + v["link"]
        elif line.startswith("ForegroundNegative="):
            line = "ForegroundNegative=" + v["negative"]
        elif line.startswith("ForegroundPositive=") and line.endswith(MAUVE):
            line = "ForegroundPositive=" + v["positive"]
        lines.append(line)
    return "\n".join(lines) + "\n"


def konsole_scheme(v: dict) -> str:
    text = MOCHA_KONSOLE.read_text().replace("Description=Catppuccin Mocha", f"Description={v['name']}")
    lines = []
    section = ""
    for line in text.splitlines():
        if line.startswith("[") and line.endswith("]"):
            section = line.strip("[]")
        elif line.startswith("Color=") and section.startswith("Color"):
            slot = section[5:].replace("Faint", "").replace("Intense", "")
            if slot in v["konsole"]:
                line = "Color=" + v["konsole"][slot]
        lines.append(line)
    return "\n".join(lines) + "\n"


def copy_plasma(key: str, v: dict) -> None:
    dest = OUT / "plasma/desktoptheme" / key
    if dest.exists():
        shutil.rmtree(dest)
    for src in MOCHA_PLASMA.rglob("*"):
        if not src.is_file():
            continue
        if ".bak" in src.name:
            continue
        rel = src.relative_to(MOCHA_PLASMA)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = src.read_bytes()
        if raw[:2] == b"\x1f\x8b" or src.suffix in {".svg", ".svgz"}:
            text = read_svg(src)
            if text:
                text = square_svg(text, v["accent_hex"])
                if src.suffix == ".svgz" or raw[:2] == b"\x1f\x8b":
                    target.write_bytes(gzip.compress(text.encode()))
                else:
                    target.write_text(text)
                continue
        shutil.copy2(src, target)
    meta = dest / "metadata.json"
    if meta.exists():
        meta.write_text(
            meta.read_text()
            .replace("Catppuccin.Mocha", key)
            .replace("Catppuccin Mocha", v["name"])
        )
    desktop = dest / "metadata.desktop"
    if desktop.exists():
        desktop.write_text(
            desktop.read_text()
            .replace("Catppuccin.Mocha", key)
            .replace("Catppuccin Mocha", v["name"])
        )
    (dest / ".1989").write_text("1989\n")


def copy_aurorae(key: str, v: dict) -> None:
    dest = OUT / "aurorae/themes" / key
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "decoration.svg").write_text(decoration_svg(v["accent_hex"]))
    for name, kind in (
        ("close", "close"),
        ("minimize", "minimize"),
        ("maximize", "max"),
        ("restore", "max"),
        ("alldesktops", "max"),
        ("keepabove", "max"),
        ("keepbelow", "minimize"),
        ("shade", "minimize"),
    ):
        (dest / f"{name}.svg").write_text(button_svg(kind, v["accent_hex"]))
    (dest / f"{key}rc").write_text(aurorae_rc(v["name"]))
    (dest / "metadata.desktop").write_text(
        f"""[Desktop Entry]
Name={v['name']}
Comment=Square hairline frame on the Mocha layout
X-KDE-PluginInfo-Author=1989
X-KDE-PluginInfo-EnabledByDefault=true
X-KDE-PluginInfo-License=GPL-3.0+
X-KDE-PluginInfo-Name={key}
X-KDE-PluginInfo-Version=1.0.0
"""
    )
    (dest / ".1989").write_text("1989\n")


def console_monochrome(text: str) -> str:
    import re

    text = re.sub(r"\sfill=\"[^\"]*\"", "", text)
    text = re.sub(r"\sstroke=\"[^\"]*\"", "", text)
    text = re.sub(r"fill:\s*#[0-9A-Fa-f]{3,8}", "fill:currentColor", text)
    text = re.sub(r"stroke:\s*#[0-9A-Fa-f]{3,8}", "stroke:currentColor", text)
    if "current-color-scheme" not in text:
        text = text.replace(">", ">\n" + SCHEME_STYLE, 1)
    text = text.replace("</svg>", '<g class="ColorScheme-Text" fill="currentColor" stroke="currentColor"/></svg>')
    # The empty group does nothing. Wrap the body instead.
    text = text.replace(
        '<g class="ColorScheme-Text" fill="currentColor" stroke="currentColor"/></svg>',
        "</svg>",
    )
    insert_at = text.find(">", text.find("<svg"))
    if insert_at != -1:
        text = (
            text[: insert_at + 1]
            + '\n<g class="ColorScheme-Text" fill="currentColor">'
            + text[insert_at + 1 :]
        )
        text = text.replace("</svg>", "</g>\n</svg>")
    return text


def is_clean_scheme(text: str) -> bool:
    import re

    body = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    return "ColorScheme-" in text and "fill:#" not in body.lower()


def reclass_place(text: str, stem: str) -> str:
    role = PLACE_ROLE.get(stem)
    if not role:
        return text
    return text.replace('class="ColorScheme-Text"', f'class="{role}"').replace(
        "class='ColorScheme-Text'", f"class='{role}'"
    )


def copy_icons() -> None:
    dest_root = OUT / "icons/1989"
    if dest_root.exists():
        shutil.rmtree(dest_root)
    prefer = {"symbolic": 0, "22": 1, "24": 2, "16": 3, "32": 4, "scalable": 5, "48": 6}
    scheme: dict[str, tuple[int, str]] = {}
    files: list[Path] = []
    for src in ICONS.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(ICONS)
        if ".bak" in src.name:
            continue
        files.append(src)
        if src.suffix != ".svg" or "@" in str(rel):
            continue
        text = read_svg(src)
        if not text or not is_clean_scheme(text):
            continue
        parts = rel.parts
        size = parts[1] if len(parts) > 2 else ""
        rank = prefer.get(size, 50)
        current = scheme.get(src.stem)
        if current is None or rank < current[0]:
            scheme[src.stem] = (rank, text)
    copied = 0
    for src in files:
        rel = src.relative_to(ICONS)
        target = dest_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix != ".svg":
            try:
                shutil.copy2(src, target)
            except OSError:
                continue
            copied += 1
            continue
        text = read_svg(src)
        if text is None:
            continue
        # App icons keep the original drawing and the colors in that file.
        if rel.parts and rel.parts[0].startswith("apps"):
            from app_icons import bake

            target.write_text(bake(text))
            copied += 1
            continue
        # Colored illustrations often mention a scheme class and also paint
        # with raw hex. Those get replaced by the plain scheme drawing of the
        # same name, which is the console version.
        clean = scheme.get(src.stem)
        if clean and not is_clean_scheme(text):
            text = clean[1]
        elif not is_clean_scheme(text):
            text = console_monochrome(text)
        text = reclass_place(text, src.stem)
        target.write_text(text)
        copied += 1
    cachy = dest_root / "apps/scalable/cachyos.svg"
    cachy.parent.mkdir(parents=True, exist_ok=True)
    cachy.write_text(CACHY)
    index = dest_root / "index.theme"
    if index.exists():
        body = index.read_text()
        body = body.replace("Name=ColorFlow.Agresive.Color", "Name=1989")
        if "FollowsColorScheme=" not in body:
            body = body.replace("Inherits=", "FollowsColorScheme=true\nInherits=")
        body = body.replace("Inherits=breeze,breeze-dark", "Inherits=breeze,breeze-dark")
        index.write_text(body)
    (dest_root / ".1989").write_text("1989\n")
    from app_icons import TUNED

    if TUNED.is_dir():
        for src in TUNED.glob("*.svg"):
            dest = dest_root / "apps" / "scalable" / src.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(src.read_text())
    print(f"icons {copied}")
    # Sprites come last. A rebuild recopies ColorFlow, so flattening earlier is lost.
    # The CachyOS mark stays a scheme drawing so each variant can recolor it.
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "flatten_icon.py"),
            "--in-place",
            "--exclude",
            "cachyos.svg",
            "-j",
            "16",
            str(dest_root),
        ],
        check=False,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "readable_icons.py"),
            "--source",
            str(ICONS),
            str(dest_root),
        ],
        check=False,
    )
    # The flatten above writes every sprite at 64. Size each ColorFlow
    # drawing onto its own canvas and build the @2x twins after that.
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "size_icons.py"), str(dest_root)],
        check=False,
    )


CACHY = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" shape-rendering="crispEdges" role="img" aria-label="CachyOS">
  <style id="current-color-scheme" type="text/css">
    .ColorScheme-Highlight { color:#dd9d89; }
    .ColorScheme-PositiveText { color:#a6e3a1; }
    .ColorScheme-NeutralText { color:#d1b7f1; }
    .ColorScheme-NegativeText { color:#f9e2af; }
  </style>
  <path class="ColorScheme-Highlight" fill="currentColor" d="M44 8h8v2h-8z M44 10h8v2h-8z M44 12h8v2h-8z M20 14h4v2h-4z M44 14h8v2h-8z M18 16h6v2h-6z M16 18h10v2h-10z M14 20h12v2h-12z M12 22h16v2h-16z M10 24h18v2h-18z M8 26h22v2h-22z M6 28h24v2h-24z M4 30h28v2h-28z M4 32h28v2h-28z M6 34h24v2h-24z M8 36h22v2h-22z M10 38h18v2h-18z M12 40h16v2h-16z M14 42h12v2h-12z M16 44h10v2h-10z M18 46h6v2h-6z M20 48h4v2h-4z M20 50h2v2h-2z"/>
  <path class="ColorScheme-PositiveText" fill="currentColor" d="M22 12h2v2h-2z M24 14h4v2h-4z M24 16h8v2h-8z M26 18h10v2h-10z M26 20h14v2h-14z M28 22h10v2h-10z M28 24h10v2h-10z M30 26h6v2h-6z M30 28h4v2h-4z M32 30h2v2h-2z M30 34h4v2h-4z M30 36h6v2h-6z M28 38h10v2h-10z M28 40h10v2h-10z M26 42h14v2h-14z M26 44h10v2h-10z M24 46h8v2h-8z M24 48h4v2h-4z M22 50h2v2h-2z"/>
  <path class="ColorScheme-NeutralText" fill="currentColor" d="M48 20h10v2h-10z M48 22h10v2h-10z M48 24h10v2h-10z M48 26h10v2h-10z"/>
  <path class="ColorScheme-NegativeText" fill="currentColor" d="M44 32h8v2h-8z M44 34h8v2h-8z M44 36h8v2h-8z M44 38h8v2h-8z"/>
</svg>
'''


def look_and_feel(key: str, v: dict) -> None:
    dest = OUT / "plasma/look-and-feel" / key
    dest.mkdir(parents=True, exist_ok=True)
    defaults = f"""[kcminputrc][Mouse]
cursorTheme=1989-cursors

[kdeglobals][General]
ColorScheme={key}
font={FONT}
menuFont={FONT}
toolBarFont={FONT}
fixed={FONT}
smallestReadableFont={FONT}
activeFont={FONT}

[kdeglobals][Icons]
Theme=1989

[kdeglobals][KDE]
frameContrast=0
widgetStyle=Breeze

[kdeglobals][WM]
activeFont={FONT}
inactiveFont={FONT}
font={FONT}
fixed={FONT}
menuFont={FONT}
toolBarFont={FONT}
smallestReadableFont={FONT}

[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae.v2
theme=__aurorae__svg__{key}
BorderSize=Tiny
BorderSizeAuto=false
NoPlugin=false

[kwinrc][Plugins]
blurEnabled=true

[plasmarc][Theme]
name={key}

[Wallpaper][org.kde.image][General]
Image=1989
"""
    (dest / "contents/defaults").parent.mkdir(parents=True, exist_ok=True)
    (dest / "contents/defaults").write_text(defaults)
    splash = dest / "contents/splash"
    if splash.exists():
        shutil.rmtree(splash)
    shutil.copytree(ROOT / "splash", splash)
    (dest / "metadata.json").write_text(
        f'''{{
  "KPackageStructure": "Plasma/LookAndFeel",
  "KPlugin": {{
    "Authors": [{{"Name": "1989"}}],
    "Id": "{key}",
    "License": "GPLv3",
    "Name": "{v["name"]}",
    "Description": "1989, from the Catppuccin Mocha assets"
  }}
}}
'''
    )
    layout = ROOT / "layouts" / "org.kde.plasma.desktop-layout.js"
    target = dest / "contents/layouts/org.kde.plasma.desktop-layout.js"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(layout, target)
    (dest / ".1989").write_text("1989\n")


def copy_wallpaper() -> None:
    src = ROOT / "wallpapers" / "1989"
    dest = OUT / "wallpapers" / "1989"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def main() -> None:
    for key, variant in VARIANTS.items():
        (OUT / "color-schemes").mkdir(parents=True, exist_ok=True)
        (OUT / "color-schemes" / f"{key}.colors").write_text(color_scheme(key, variant))
        (OUT / "konsole").mkdir(parents=True, exist_ok=True)
        (OUT / "konsole" / f"{key}.colorscheme").write_text(konsole_scheme(variant))
        copy_plasma(key, variant)
        copy_aurorae(key, variant)
        look_and_feel(key, variant)
        print("variant", key)
    copy_wallpaper()
    copy_icons()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
