#!/usr/bin/env python3
"""Generate the 1989 Plasma theme into ../out. Does not touch installed themes."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
SRC_ICON_THEME = Path("/home/daniel/.local/share/icons/ColorFlow.Agresive.Color")

FIELD = (24, 24, 33)
SURFACE = (30, 30, 42)
BUTTON = (35, 35, 50)
TEXT = (189, 197, 227)
DIM = (141, 147, 159)
TITLE = (205, 214, 244)
INK = (34, 36, 37)
NEUTRAL = (166, 173, 200)
GREEN = (166, 227, 161)
PEACH = (221, 157, 137)
MAUVE = (209, 183, 241)
PINK = (190, 134, 198)
SAND = (249, 226, 175)
TEAL = (148, 226, 213)
BLUE = (137, 180, 250)
MOCHA_RED = (243, 139, 168)
MOCHA_PEACH = (250, 179, 135)
MOCHA_PINK = (245, 194, 231)
MOCHA_MAUVE = (203, 166, 247)

FONT = "Hack,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"


def hx(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def csv(rgb: tuple[int, int, int]) -> str:
    return f"{rgb[0]},{rgb[1]},{rgb[2]}"


VARIANTS = {
    "1989": {
        "name": "1989",
        "gtk": "1989",
        "accent": PEACH,
        "selection": MAUVE,
        "positive": GREEN,
        "negative": PEACH,
        "link": PINK,
        "circle": MAUVE,
        "wedges": (PEACH, SAND, TEAL),
        "ansi": {
            1: MOCHA_RED,
            2: GREEN,
            3: SAND,
            4: BLUE,
            5: MAUVE,
            6: TEAL,
        },
    },
    "1989Mocha": {
        "name": "1989 Mocha",
        "gtk": "1989-Mocha",
        "accent": MOCHA_MAUVE,
        "selection": MOCHA_MAUVE,
        "positive": GREEN,
        "negative": MOCHA_RED,
        "link": MOCHA_PINK,
        "circle": MOCHA_MAUVE,
        "wedges": (MOCHA_MAUVE, MOCHA_RED, BLUE),
        "ansi": {
            1: MOCHA_RED,
            2: GREEN,
            3: SAND,
            4: BLUE,
            5: MOCHA_MAUVE,
            6: TEAL,
        },
    },
    "1989Blue": {
        "name": "1989 Blue",
        "gtk": "1989-Blue",
        "accent": (123, 165, 227),
        "selection": (123, 165, 227),
        "positive": GREEN,
        "negative": (180, 97, 118),
        "link": (156, 166, 223),
        "circle": (116, 184, 198),
        "wedges": ((123, 165, 227), (116, 184, 198), (156, 166, 223)),
        "ansi": {
            1: (180, 97, 118),
            2: GREEN,
            3: SAND,
            4: (123, 165, 227),
            5: (156, 166, 223),
            6: (116, 184, 198),
        },
    },
    "1989Green": {
        "name": "1989 Green",
        "gtk": "1989-Green",
        "accent": (111, 154, 114),
        "selection": (111, 154, 114),
        "positive": (94, 150, 142),
        "negative": (180, 97, 118),
        "link": (94, 150, 142),
        "circle": (94, 150, 142),
        "wedges": ((111, 154, 114), (94, 150, 142), (122, 108, 72)),
        "ansi": {
            1: (180, 97, 118),
            2: (111, 154, 114),
            3: SAND,
            4: BLUE,
            5: MAUVE,
            6: (94, 150, 142),
        },
    },
    "1989Red": {
        "name": "1989 Red",
        "gtk": "1989-Red",
        "accent": (180, 97, 118),
        "selection": (180, 97, 118),
        "positive": GREEN,
        "negative": (180, 97, 118),
        "link": (158, 101, 112),
        "circle": (158, 101, 112),
        "wedges": ((180, 97, 118), (158, 101, 112), (171, 118, 98)),
        "ansi": {
            1: (180, 97, 118),
            2: GREEN,
            3: SAND,
            4: BLUE,
            5: (158, 101, 112),
            6: TEAL,
        },
    },
}


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def marker(path: Path) -> None:
    write(path / ".1989", "1989\n")


def color_scheme(key: str, v: dict) -> str:
    accent, selection = v["accent"], v["selection"]
    positive, negative, link = v["positive"], v["negative"], v["link"]

    def block(bg, fg, sel_bg, sel_fg) -> str:
        return "\n".join(
            [
                f"BackgroundAlternate={csv(SURFACE)}",
                f"BackgroundNormal={csv(bg)}",
                f"DecorationFocus={csv(accent)}",
                f"DecorationHover={csv(accent)}",
                f"ForegroundActive={csv(accent)}",
                f"ForegroundInactive={csv(DIM)}",
                f"ForegroundLink={csv(link)}",
                f"ForegroundNegative={csv(negative)}",
                f"ForegroundNeutral={csv(NEUTRAL)}",
                f"ForegroundNormal={csv(fg)}",
                f"ForegroundPositive={csv(positive)}",
                f"ForegroundVisited={csv(link)}",
            ]
        )

    sections = {
        "Colors:Button": block(BUTTON, TEXT, selection, INK),
        "Colors:Complementary": block(FIELD, TEXT, selection, INK),
        "Colors:Header": block(FIELD, TITLE, selection, INK),
        "Colors:Selection": block(selection, INK, selection, INK),
        "Colors:Tooltip": block(SURFACE, TEXT, selection, INK),
        "Colors:View": block(SURFACE, TEXT, selection, INK),
        "Colors:Window": block(FIELD, TEXT, selection, INK),
    }
    parts = [
        "[ColorEffects:Disabled]",
        "Color=56,56,56",
        "ColorAmount=0",
        "ColorEffect=0",
        "ContrastAmount=0.45",
        "ContrastEffect=1",
        "IntensityAmount=0.1",
        "IntensityEffect=2",
        "",
        "[ColorEffects:Inactive]",
        "ChangeSelectionColor=true",
        "Color=112,111,110",
        "ColorAmount=0.025",
        "ColorEffect=2",
        "ContrastAmount=0.1",
        "ContrastEffect=2",
        "Enable=true",
        "IntensityAmount=0",
        "IntensityEffect=0",
        "",
    ]
    for name, body in sections.items():
        parts.append(f"[{name}]")
        parts.append(body)
        parts.append("")
    parts += [
        "[General]",
        f"ColorScheme={key}",
        f"Name={v['name']}",
        "shadeSortColumn=true",
        "TitlebarIsAccentColored=false",
        "",
        "[KDE]",
        "contrast=4",
        "frameContrast=0",
        "",
        "[WM]",
        f"activeBackground={csv(FIELD)}",
        f"activeBlend={csv(FIELD)}",
        f"activeForeground={csv(TITLE)}",
        f"inactiveBackground={csv(FIELD)}",
        f"inactiveBlend={csv(FIELD)}",
        f"inactiveForeground={csv(DIM)}",
        "",
    ]
    return "\n".join(parts)


def konsole_scheme(v: dict) -> str:
    lines = [
        "[Background]",
        f"Color={csv(FIELD)}",
        "",
        "[BackgroundFaint]",
        f"Color={csv(FIELD)}",
        "",
        "[BackgroundIntense]",
        f"Color={csv(SURFACE)}",
        "",
        "[Color0]",
        "Color=69,71,90",
        "",
        "[Color0Intense]",
        "Color=108,112,134",
        "",
    ]
    bright = {
        1: (255, 170, 180),
        2: (190, 235, 185),
        3: (255, 230, 180),
        4: (170, 200, 245),
        5: (220, 200, 245),
        6: (170, 230, 220),
    }
    for i in range(1, 7):
        lines += [f"[Color{i}]", f"Color={csv(v['ansi'][i])}", ""]
        lines += [f"[Color{i}Intense]", f"Color={csv(bright[i])}", ""]
    lines += [
        "[Color7]",
        f"Color={csv(TEXT)}",
        "",
        "[Color7Intense]",
        f"Color={csv(TITLE)}",
        "",
        "[Foreground]",
        f"Color={csv(TEXT)}",
        "",
        "[ForegroundIntense]",
        f"Color={csv(TITLE)}",
        "",
        "[General]",
        "Blur=false",
        f"Description={v['name']}",
        "Opacity=1",
        "",
    ]
    return "\n".join(lines)


def svg_frame(prefix: str, fill: str, edge: str, opacity: float) -> str:
    p = f"{prefix}-" if prefix else ""
    op = f"{opacity:.2f}"
    return f"""
  <rect id="{p}center" x="1" y="1" width="30" height="30" fill="{fill}" fill-opacity="{op}"/>
  <rect id="{p}top" x="1" y="0" width="30" height="1" fill="{edge}"/>
  <rect id="{p}bottom" x="1" y="31" width="30" height="1" fill="{edge}"/>
  <rect id="{p}left" x="0" y="1" width="1" height="30" fill="{edge}"/>
  <rect id="{p}right" x="31" y="1" width="1" height="30" fill="{edge}"/>
  <rect id="{p}topleft" x="0" y="0" width="1" height="1" fill="{edge}"/>
  <rect id="{p}topright" x="31" y="0" width="1" height="1" fill="{edge}"/>
  <rect id="{p}bottomleft" x="0" y="31" width="1" height="1" fill="{edge}"/>
  <rect id="{p}bottomright" x="31" y="31" width="1" height="1" fill="{edge}"/>
  <rect id="{p}hint-left-margin" width="1" height="1" fill="none"/>
  <rect id="{p}hint-right-margin" width="1" height="1" fill="none"/>
  <rect id="{p}hint-top-margin" width="1" height="1" fill="none"/>
  <rect id="{p}hint-bottom-margin" width="1" height="1" fill="none"/>
"""


def svg_doc(body: str, size: int = 32) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">\n'
        f"{body}\n</svg>\n"
    )


def plasma_theme(key: str, v: dict) -> None:
    base = OUT / "plasma/desktoptheme" / key
    fill = hx(FIELD)
    accent = hx(v["accent"])
    dim = hx(DIM)
    surface = hx(SURFACE)
    positive = hx(v["positive"])
    panel = svg_doc(svg_frame("", fill, accent, 0.78))
    dialog = svg_doc(svg_frame("", fill, accent, 0.88))
    tooltip = svg_doc(svg_frame("", surface, accent, 0.92))
    button = svg_doc(
        svg_frame("normal", hx(BUTTON), dim, 0.9)
        + svg_frame("hover", hx(BUTTON), accent, 0.95)
        + svg_frame("focus", hx(BUTTON), accent, 1)
        + svg_frame("pressed", hx(BUTTON), accent, 1)
    )
    tasks = svg_doc(
        svg_frame("normal", fill, dim, 0.0)
        + svg_frame("hover", fill, accent, 0.35)
        + svg_frame("focus", fill, accent, 0.55)
        + svg_frame("attention", fill, positive, 0.55)
        + svg_frame("minimized", fill, dim, 0.2)
    )
    lineedit = svg_doc(
        svg_frame("base", surface, dim, 1)
        + svg_frame("hover", surface, accent, 1)
        + svg_frame("focus", surface, accent, 1)
    )
    meter = svg_doc(
        f'<rect id="background-center" width="32" height="32" fill="{hx(BUTTON)}"/>'
        f'<rect id="bar-center" x="0" y="0" width="32" height="32" fill="{positive}"/>'
    )
    write(base / "widgets/panel-background.svg", panel)
    write(base / "widgets/tooltip.svg", tooltip)
    write(base / "widgets/background.svg", dialog)
    write(base / "widgets/button.svg", button)
    write(base / "widgets/tasks.svg", tasks)
    write(base / "widgets/lineedit.svg", lineedit)
    write(base / "widgets/bar_meter_horizontal.svg", meter)
    write(base / "dialogs/background.svg", dialog)
    write(
        base / "plasmarc",
        "[AdaptiveTransparency]\nenabled=true\n\n[BlurBehindEffect]\nenabled=true\n\n[ContrastEffect]\nenabled=true\n",
    )
    write(
        base / "metadata.json",
        """{
  "KPlugin": {
    "Authors": [{"Name": "1989"}],
    "Category": "Plasma Theme",
    "Description": "Square glass chrome for the 1989 desktop",
    "EnabledByDefault": true,
    "Id": "%s",
    "License": "GPLv3",
    "Name": "%s",
    "Version": "1.0.0"
  },
  "X-Plasma-API": "5.0"
}
"""
        % (key, v["name"]),
    )
    marker(base)


def aurorae(key: str, v: dict) -> None:
    base = OUT / "aurorae/themes" / key
    accent = hx(v["accent"])
    fill = hx(FIELD)
    dim = hx(DIM)
    title = hx(TITLE)
    # Shadow lives in the shadow-* elements. Padding stays 0 so the hairline
    # sits on the window. BorderTop is the titlebar, and it matches the SVG hint.
    shadow, top, side, bottom, center = 28, 28, 1, 1, 48
    width = shadow + side + center + side + shadow
    height = shadow + top + center + bottom + shadow
    x0, y0 = shadow, shadow
    inner_w = side + center + side
    inner_h = top + center + bottom
    deco = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect id="shadow-center" x="{x0}" y="{y0}" width="{inner_w}" height="{inner_h}" fill="none"/>
  <rect id="shadow-top" x="{x0}" y="0" width="{inner_w}" height="{shadow}" fill="#000000" fill-opacity="0.16"/>
  <rect id="shadow-bottom" x="{x0}" y="{y0 + inner_h}" width="{inner_w}" height="{shadow}" fill="#000000" fill-opacity="0.28"/>
  <rect id="shadow-left" x="0" y="{y0}" width="{shadow}" height="{inner_h}" fill="#000000" fill-opacity="0.16"/>
  <rect id="shadow-right" x="{x0 + inner_w}" y="{y0}" width="{shadow}" height="{inner_h}" fill="#000000" fill-opacity="0.16"/>
  <rect id="shadow-topleft" x="0" y="0" width="{shadow}" height="{shadow}" fill="#000000" fill-opacity="0.10"/>
  <rect id="shadow-topright" x="{x0 + inner_w}" y="0" width="{shadow}" height="{shadow}" fill="#000000" fill-opacity="0.10"/>
  <rect id="shadow-bottomleft" x="0" y="{y0 + inner_h}" width="{shadow}" height="{shadow}" fill="#000000" fill-opacity="0.22"/>
  <rect id="shadow-bottomright" x="{x0 + inner_w}" y="{y0 + inner_h}" width="{shadow}" height="{shadow}" fill="#000000" fill-opacity="0.22"/>
  <rect id="shadow-hint-left-margin" width="{shadow}" height="{shadow}" fill="none"/>
  <rect id="shadow-hint-right-margin" width="{shadow}" height="{shadow}" fill="none"/>
  <rect id="shadow-hint-top-margin" width="{shadow}" height="{shadow}" fill="none"/>
  <rect id="shadow-hint-bottom-margin" width="{shadow}" height="{shadow}" fill="none"/>
  <rect id="decoration-topleft" x="{x0}" y="{y0}" width="{side}" height="{top}" fill="{accent}"/>
  <g id="decoration-top">
    <rect x="{x0 + side}" y="{y0}" width="{center}" height="{top}" fill="{fill}" fill-opacity="0.94"/>
    <rect x="{x0 + side}" y="{y0}" width="{center}" height="1" fill="{accent}"/>
  </g>
  <rect id="decoration-topright" x="{x0 + side + center}" y="{y0}" width="{side}" height="{top}" fill="{accent}"/>
  <rect id="decoration-left" x="{x0}" y="{y0 + top}" width="{side}" height="{center}" fill="{accent}"/>
  <rect id="decoration-center" x="{x0 + side}" y="{y0 + top}" width="{center}" height="{center}" fill="{fill}" fill-opacity="0.94"/>
  <rect id="decoration-right" x="{x0 + side + center}" y="{y0 + top}" width="{side}" height="{center}" fill="{accent}"/>
  <rect id="decoration-bottomleft" x="{x0}" y="{y0 + top + center}" width="{side}" height="{bottom}" fill="{accent}"/>
  <rect id="decoration-bottom" x="{x0 + side}" y="{y0 + top + center}" width="{center}" height="{bottom}" fill="{accent}"/>
  <rect id="decoration-bottomright" x="{x0 + side + center}" y="{y0 + top + center}" width="{side}" height="{bottom}" fill="{accent}"/>
  <rect id="decoration-hint-left-margin" width="{side}" height="{side}" fill="none"/>
  <rect id="decoration-hint-right-margin" width="{side}" height="{side}" fill="none"/>
  <rect id="decoration-hint-top-margin" width="{top}" height="{top}" fill="none"/>
  <rect id="decoration-hint-bottom-margin" width="{bottom}" height="{bottom}" fill="none"/>
</svg>
'''
    write(base / "decoration.svg", deco)

    def glyph(kind: str, stroke: str) -> str:
        if kind == "close":
            mark = f'<path d="M4 4 L12 12 M12 4 L4 12" stroke="{stroke}" stroke-width="1.4"/>'
        elif kind == "minimize":
            mark = f'<path d="M3 8 H13" stroke="{stroke}" stroke-width="1.4"/>'
        else:
            mark = f'<rect x="4" y="4" width="8" height="8" fill="none" stroke="{stroke}" stroke-width="1.2"/>'
        parts = []
        for state, color in (
            ("active", stroke),
            ("hover", accent),
            ("pressed", accent),
            ("inactive", dim),
        ):
            local = mark.replace(stroke, color) if state != "active" else mark
            parts.append(f'<g id="{state}-center">{local}</g>')
        return svg_doc("\n".join(parts), 16)

    for name, kind in (
        ("close", "close"),
        ("minimize", "minimize"),
        ("maximize", "maximize"),
        ("restore", "maximize"),
        ("alldesktops", "maximize"),
        ("keepabove", "maximize"),
        ("keepbelow", "minimize"),
        ("shade", "minimize"),
    ):
        write(base / f"{name}.svg", glyph(kind, title))

    write(
        base / f"{key}rc",
        f"""[General]
ActiveTextColor={csv(TITLE)}
InactiveTextColor={csv(DIM)}
LeftButtons=XIA
RightButtons=
Shadow=true
TitleAlignment=Center
TitleVerticalAlignment=Center
UseTextShadow=false

[Layout]
ButtonHeight=16
ButtonWidth=16
ButtonMarginTop=2
ButtonSpacing=6
BorderLeft=1
BorderRight=1
BorderBottom=1
BorderTop=28
PaddingLeft=0
PaddingRight=0
PaddingTop=0
PaddingBottom=0
TitleEdgeTop=5
TitleEdgeBottom=4
TitleEdgeLeft=6
TitleEdgeRight=6
TitleHeight=18
""",
    )
    write(
        base / "metadata.desktop",
        f"""[Desktop Entry]
Name={v['name']}
Comment=Square glass window frame
X-KDE-PluginInfo-Name={key}
X-KDE-PluginInfo-Author=1989
X-KDE-PluginInfo-Version=1.0.0
X-KDE-PluginInfo-License=GPL-3.0+
X-KDE-PluginInfo-EnabledByDefault=true
""",
    )
    write(
        base / "metadata.json",
        """{
  "KPackageStructure": "aurorae",
  "KPlugin": {
    "Authors": [{"Name": "1989"}],
    "Category": "Plasma 6 Window Decorations",
    "ServiceTypes": ["aurorae"],
    "EnabledByDefault": true,
    "Id": "%s",
    "License": "GPL-3.0+",
    "Name": "%s",
    "Description": "Square glass window frame",
    "Version": "1.0.0"
  }
}
"""
        % (key, v["name"]),
    )
    marker(base)


def copy_splash(base: Path) -> None:
    dest = base / "contents/splash"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / "splash", dest)


def look_and_feel(key: str, v: dict) -> None:
    base = OUT / "plasma/look-and-feel" / key
    # Plasma 6.8.3 detects fonts in the swapped groups, then applies the real
    # ones. Both groups carry the same Hack string so either build applies it.
    defaults = f"""[kdeglobals][General]
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

[kcminputrc][Mouse]
cursorTheme=1989-cursors

[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae.v2
theme=__aurorae__svg__{key}
BorderSize=Tiny
BorderSizeAuto=false
ButtonsOnLeft=XIA
ButtonsOnRight=

[kwinrc][Plugins]
blurEnabled=true

[plasmarc][Theme]
name={key}

[Wallpaper][org.kde.image][General]
Image=1989

[gtk-3.0/settings.ini][Settings]
gtk-theme-name={v['gtk']}
gtk-font-name=Hack, 10
gtk-icon-theme-name=1989
gtk-cursor-theme-name=1989-cursors
gtk-application-prefer-dark-theme=true

[gtk-4.0/settings.ini][Settings]
gtk-theme-name={v['gtk']}
gtk-font-name=Hack, 10
gtk-icon-theme-name=1989
gtk-cursor-theme-name=1989-cursors
gtk-application-prefer-dark-theme=true
"""
    write(base / "contents/defaults", defaults)
    copy_splash(base)
    write(
        base / "metadata.json",
        """{
  "KPackageStructure": "Plasma/LookAndFeel",
  "KPlugin": {
    "Authors": [{"Name": "1989"}],
    "Id": "%s",
    "License": "GPLv3",
    "Name": "%s",
    "Description": "1989 desktop, %s"
  }
}
"""
        % (key, v["name"], v["name"]),
    )
    write_previews(base, key, v)
    copy_layout(base)
    marker(base)


def copy_layout(base: Path) -> None:
    src = ROOT / "layouts" / "org.kde.plasma.desktop-layout.js"
    dest = base / "contents/layouts/org.kde.plasma.desktop-layout.js"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)


def copy_wallpaper() -> None:
    src = ROOT / "wallpapers" / "1989"
    dest = OUT / "wallpapers" / "1989"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def write_previews(base: Path, key: str, v: dict) -> None:
    from PIL import Image, ImageDraw, ImageFont

    dest = base / "contents/previews"
    dest.mkdir(parents=True, exist_ok=True)
    source = ROOT / "previews" / f"{key}.png"
    if source.is_file():
        full = Image.open(source).convert("RGB")
        if full.size != (1920, 1080):
            full = full.resize((1920, 1080), Image.Resampling.LANCZOS)
        preview = full.resize((600, 337), Image.Resampling.LANCZOS)
        preview.save(dest / "preview.png")
        full.save(dest / "fullscreenpreview.jpg", quality=90)
        return

    poster = Image.new("RGB", (1920, 1080), FIELD)
    font = ImageFont.truetype("/usr/share/fonts/TTF/Hack-Regular.ttf", 22)
    small = ImageFont.truetype("/usr/share/fonts/TTF/Hack-Regular.ttf", 16)

    def chrome(image: Image.Image) -> None:
        draw = ImageDraw.Draw(image)
        w, h = image.size
        scale = w / 1920
        bar = max(18, round(28 * scale))
        draw.rectangle((0, 0, w, bar), fill=FIELD)
        draw.line((0, bar, w, bar), fill=v["accent"], width=max(1, round(scale)))
        draw.text((round(14 * scale), bar // 2 - 8), "1989", font=small, fill=TITLE)
        win_w, win_h = round(w * 0.46), round(h * 0.62)
        x, y = round(w * 0.08), round(h * 0.16)
        title_h = max(16, round(28 * scale))
        draw.rectangle((x, y, x + win_w, y + win_h), outline=v["accent"], width=max(1, round(scale)))
        draw.rectangle((x, y, x + win_w, y + title_h), fill=FIELD)
        draw.text((x + 12, y + 4), "dolphin", font=font if scale > 0.6 else small, fill=TITLE)
        folders = [v["accent"], v["positive"], v["circle"], v["selection"]]
        gap = round(18 * scale)
        size = round(36 * scale)
        fx = x + round(24 * scale)
        fy = y + title_h + round(28 * scale)
        for color in folders:
            draw.rectangle((fx, fy, fx + size, fy + round(size * 0.72)), fill=color)
            fx += size + gap

    full = poster.copy()
    chrome(full)
    preview = full.resize((600, 337), Image.Resampling.LANCZOS)
    preview.save(dest / "preview.png")
    full.save(dest / "fullscreenpreview.jpg", quality=86)


def gtk_css(v: dict) -> str:
    accent, selection = hx(v["accent"]), hx(v["selection"])
    return f'''* {{
  border-radius: 0;
  font-family: Hack, monospace;
}}
window, .background {{
  background-color: {hx(FIELD)};
  color: {hx(TEXT)};
}}
headerbar, .titlebar {{
  background-color: rgba(24, 24, 33, 0.86);
  color: {hx(TITLE)};
  border-bottom: 1px solid {accent};
  box-shadow: none;
}}
button, entry, combobox, notebook tab {{
  border-radius: 0;
  border: 1px solid {hx(DIM)};
  background-color: {hx(BUTTON)};
  color: {hx(TEXT)};
  box-shadow: none;
}}
button:hover, button:focus, entry:focus {{
  border-color: {accent};
}}
selection, *:selected, treeview:selected {{
  background-color: {selection};
  color: {hx(INK)};
}}
scrollbar slider {{
  border-radius: 0;
  background-color: {accent};
  min-width: 8px;
  min-height: 8px;
}}
'''


def gtk_theme(v: dict) -> None:
    name = v["gtk"]
    base = OUT / "themes" / name
    css = gtk_css(v)
    write(base / "gtk-3.0/gtk.css", css)
    write(base / "gtk-4.0/gtk.css", css)
    write(
        base / "index.theme",
        f"[Desktop Entry]\nType=X-GNOME-Metatheme\nName={v['name']}\nComment=1989\nEncoding=UTF-8\n\n[X-GNOME-Metatheme]\nGtkTheme={name}\n",
    )
    marker(base)


def cachy_svg() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" shape-rendering="crispEdges" role="img" aria-label="CachyOS">
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


# Same ColorFlow drawing, painted with a scheme role so Dolphin's places pick up the variant.
PLACE_ROLE = {
    "folder": "ColorScheme-Highlight",
    "folder-open": "ColorScheme-Highlight",
    "folder-documents": "ColorScheme-Highlight",
    "folder-text": "ColorScheme-Highlight",
    "folder-txt": "ColorScheme-Highlight",
    "folder-download": "ColorScheme-NegativeText",
    "folder-downloads": "ColorScheme-NegativeText",
    "folder-music": "ColorScheme-NeutralText",
    "folder-sound": "ColorScheme-NeutralText",
    "folder-pictures": "ColorScheme-PositiveText",
    "folder-picture": "ColorScheme-PositiveText",
    "folder-image": "ColorScheme-PositiveText",
    "folder-images": "ColorScheme-PositiveText",
    "folder-photos": "ColorScheme-PositiveText",
    "folder-videos": "ColorScheme-NegativeText",
    "folder-video": "ColorScheme-NegativeText",
    "folder-movies": "ColorScheme-NegativeText",
    "folder-development": "ColorScheme-NeutralText",
    "folder-script": "ColorScheme-NeutralText",
    "user-home": "ColorScheme-Highlight",
    "user-desktop": "ColorScheme-Text",
    "user-downloads": "ColorScheme-NegativeText",
    "user-documents": "ColorScheme-Highlight",
    "user-music": "ColorScheme-NeutralText",
    "user-pictures": "ColorScheme-PositiveText",
    "user-videos": "ColorScheme-NegativeText",
}


def icons() -> None:
    base = OUT / "icons/1989"
    contexts = ("actions", "status", "apps", "places", "devices", "mimes", "categories", "emblems")
    prefer = ("symbolic", "22", "24", "16", "32", "scalable", "48")
    chosen: dict[tuple[str, str], tuple[int, Path]] = {}
    if SRC_ICON_THEME.is_dir():
        for src in SRC_ICON_THEME.rglob("*.svg"):
            rel = src.relative_to(SRC_ICON_THEME)
            if "@" in str(rel) or len(rel.parts) < 3:
                continue
            ctx, size = rel.parts[0], rel.parts[1]
            if ctx not in contexts:
                continue
            try:
                head = src.read_bytes()[:6000]
            except OSError:
                continue
            if b"ColorScheme-" not in head:
                continue
            rank = prefer.index(size) if size in prefer else 50
            key = (ctx, src.stem)
            current = chosen.get(key)
            if current is None or rank < current[0]:
                chosen[key] = (rank, src)
        for (ctx, stem), (_, src) in chosen.items():
            dest = base / ctx / "scalable" / f"{stem}.svg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            text = src.read_text(errors="ignore")
            role = PLACE_ROLE.get(stem)
            if role and ctx == "places":
                text = text.replace('class="ColorScheme-Text"', f'class="{role}"')
                text = text.replace("class='ColorScheme-Text'", f"class='{role}'")
            dest.write_text(text)
    write(base / "apps/scalable/cachyos.svg", cachy_svg())
    directories = ",".join(f"{ctx}/scalable" for ctx in contexts)
    sections = []
    context_name = {
        "actions": "Actions",
        "status": "Status",
        "apps": "Applications",
        "places": "Places",
        "devices": "Devices",
        "mimes": "MimeTypes",
        "categories": "Categories",
        "emblems": "Emblems",
    }
    for ctx in contexts:
        sections.append(
            f"[{ctx}/scalable]\nSize=22\nContext={context_name[ctx]}\nType=Scalable\nMinSize=8\nMaxSize=512\n"
        )
    write(
        base / "index.theme",
        f"""[Icon Theme]
Name=1989
Comment=ColorFlow drawings, recolored by the 1989 scheme
Inherits=ColorFlow.Agresive.Color,breeze
FollowsColorScheme=true
DisplayDepth=32
Example=cachyos
DesktopDefault=48
DesktopSizes=16,22,32,48,64,128,256
ToolbarDefault=22
ToolbarSizes=16,22,32,48
SmallDefault=16
SmallSizes=16,22,32
PanelDefault=22
PanelSizes=16,22,32,48
DialogDefault=32
DialogSizes=16,22,32,48
KDE-Extensions=.svg
Directories={directories}

{chr(10).join(sections)}
""",
    )
    marker(base)


def cursors() -> None:
    import importlib.util

    script = ROOT / "scripts" / "arcadify_cursors.py"
    spec = importlib.util.spec_from_file_location("arcadify_cursors", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.build_cursors(OUT / "icons" / "1989-cursors")


def sddm() -> None:
    base = ROOT / "sddm/1989"
    write(
        base / "theme.conf",
        "[General]\nbackground=#181821\ntype=color\nfont=Hack\n",
    )
    write(
        base / "Main.qml",
        '''import QtQuick 2.15
import QtQuick.Controls 2.15
import SddmComponents 2.0

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#181821"
    Text {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -80
        text: "1989"
        color: "#cdd6f4"
        font.family: "Hack"
        font.pixelSize: 72
    }
    Column {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 40
        spacing: 12
        width: 280
        TextField {
            id: name
            width: parent.width
            text: userModel.lastUser
            color: "#bdc5e3"
            font.family: "Hack"
        }
        TextField {
            id: pw
            width: parent.width
            echoMode: TextInput.Password
            color: "#bdc5e3"
            font.family: "Hack"
            onAccepted: sddm.login(name.text, pw.text, session.index)
        }
        Button {
            text: "Log in"
            font.family: "Hack"
            onClicked: sddm.login(name.text, pw.text, session.index)
        }
    }
    ComboBox {
        id: session
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 24
        model: sessionModel
        textRole: "name"
        font.family: "Hack"
    }
}
''',
    )
    write(
        base / "metadata.desktop",
        "[SddmGreeterTheme]\nName=1989\nDescription=1989 login\nLicense=GPLv3\nType=sddm-theme\nTheme-Id=1989\nTheme-API=2.0\nMainScript=Main.qml\n",
    )


def konsole_profile() -> None:
    write(
        OUT / "konsole/1989.profile",
        """[Appearance]
ColorScheme=1989
Font=Hack,10,-1,5,50,0,0,0,0,0

[General]
Name=1989
Parent=FALLBACK/
""",
    )


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    for key, variant in VARIANTS.items():
        write(OUT / "color-schemes" / f"{key}.colors", color_scheme(key, variant))
        write(OUT / "konsole" / f"{key}.colorscheme", konsole_scheme(variant))
        plasma_theme(key, variant)
        aurorae(key, variant)
        look_and_feel(key, variant)
        gtk_theme(variant)
    copy_wallpaper()
    konsole_profile()
    icons()
    cursors()
    sddm()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
