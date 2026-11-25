#!/usr/bin/env python3
"""Replace copied ColorFlow icons with the console drawings from the 1989 study.

Filenames stay the same. Places become the flat folder. The tray marks
(volume, network, battery, bell) become the hairline drawings in the study.
"""

from __future__ import annotations

import sys
from pathlib import Path

STYLE = """<style id="current-color-scheme" type="text/css">
.ColorScheme-Text { color:#bdc5e3; }
.ColorScheme-Background { color:#181821; }
.ColorScheme-Highlight { color:#7ba5e3; }
.ColorScheme-PositiveText { color:#a6e3a1; }
.ColorScheme-NeutralText { color:#d1b7f1; }
.ColorScheme-NegativeText { color:#f38ba8; }
.ColorScheme-ButtonText { color:#bdc5e3; }
</style>"""

HIGHLIGHT = "ColorScheme-Highlight"
TEXT = "ColorScheme-Text"
POSITIVE = "ColorScheme-PositiveText"
NEUTRAL = "ColorScheme-NeutralText"
NEGATIVE = "ColorScheme-NegativeText"

FOLDER_ROLE = {
    "folder-download": NEGATIVE,
    "folder-downloads": NEGATIVE,
    "folder-videos": NEGATIVE,
    "folder-video": NEGATIVE,
    "folder-movies": NEGATIVE,
    "folder-red": NEGATIVE,
    "folder-important": NEGATIVE,
    "folder-music": NEUTRAL,
    "folder-sound": NEUTRAL,
    "folder-yellow": NEUTRAL,
    "folder-orange": NEUTRAL,
    "folder-brown": NEUTRAL,
    "folder-pink": NEUTRAL,
    "folder-purple": NEUTRAL,
    "folder-pictures": POSITIVE,
    "folder-picture": POSITIVE,
    "folder-images": POSITIVE,
    "folder-image": POSITIVE,
    "folder-photos": POSITIVE,
    "folder-green": POSITIVE,
    "folder-lime": POSITIVE,
    "folder-teal": POSITIVE,
    "user-trash-full": NEGATIVE,
}


def wrap(body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">\n'
        + STYLE
        + "\n"
        + body
        + "\n</svg>\n"
    )


def folder(role: str, open_folder: bool = False) -> str:
    back = ""
    if open_folder:
        back = f'<path class="{role}" fill="currentColor" opacity="0.45" d="M1 4h6l1.6-2H15v3H1z"/>'
    face = f'<path class="{role}" fill="currentColor" d="M1 5.2H6.2L8 3h7v10H1z"/>'
    return wrap(back + face)


def monitor() -> str:
    return wrap(
        f'<rect class="{TEXT}" x="2" y="2.5" width="12" height="8" fill="none" stroke="currentColor" stroke-width="1.2"/>'
        f'<path class="{TEXT}" d="M6 13.2h4M8 10.5v2.7" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    )


def trash(full: bool) -> str:
    lid = f'<path class="{TEXT}" d="M3 4.2h10M6.2 4.2V3h3.6v1.2" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    can = f'<path class="{NEGATIVE if full else TEXT}" d="M4.2 5.2h7.6l-.6 8H4.8z" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    return wrap(lid + can)


def volume(level: str) -> str:
    speaker = f'<path class="{TEXT}" fill="currentColor" d="M2.2 6.2h2.1L8 3.4v9.2L4.3 9.8H2.2z"/>'
    one = f'<path class="{TEXT}" d="M10 6.5a2.4 2.4 0 0 1 0 3" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    two = f'<path class="{TEXT}" d="M11.5 4.7a4.6 4.6 0 0 1 0 6.6" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    mute = f'<path class="{NEGATIVE}" d="M10.2 6.2l3.6 3.6M13.8 6.2l-3.6 3.6" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    if "muted" in level or level.endswith("off"):
        return wrap(speaker + mute)
    arcs = speaker
    if "low" not in level and "zero" not in level:
        arcs += one
    if "high" in level or "medium" not in level and "low" not in level:
        arcs += two
    return wrap(arcs)


def wired(name: str) -> str:
    line = f'<path class="{TEXT}" d="M1.6 8h8.2" fill="none" stroke="currentColor" stroke-width="1.3"/>'
    node = f'<rect class="{TEXT}" x="10" y="5.6" width="4.2" height="4.8" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    if any(word in name for word in ("offline", "disconnected", "none")):
        cross = f'<path class="{NEGATIVE}" d="M3 5.2l2.2 2.2M5.2 5.2L3 7.4" fill="none" stroke="currentColor" stroke-width="1.2"/>'
        return wrap(line + node + cross)
    return wrap(line + node)


def network(name: str) -> str:
    if name.startswith("network-wired"):
        return wired(name)
    dot = f'<circle class="{TEXT}" cx="8" cy="12.2" r="1.05" fill="currentColor"/>'
    near = f'<path class="{TEXT}" d="M5.3 9.5a3.8 3.8 0 0 1 5.4 0" fill="none" stroke="currentColor" stroke-width="1.3"/>'
    far = f'<path class="{TEXT}" d="M3.1 7.2a7 7 0 0 1 9.8 0" fill="none" stroke="currentColor" stroke-width="1.3"/>'
    cross = f'<path class="{NEGATIVE}" d="M3 3.2l2.2 2.2M5.2 3.2L3 5.4" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    if "none" in name or "offline" in name or "disconnected" in name:
        return wrap(dot + cross)
    body = dot
    if any(word in name for word in ("weak", "low")):
        return wrap(body)
    body += near
    if any(word in name for word in ("excellent", "good", "connected", "secure", "hotspot", "wired")):
        body += far
    elif "ok" in name or "acquiring" in name:
        pass
    else:
        body += far
    return wrap(body)


def battery(name: str) -> str:
    level = {
        "000": 0,
        "empty": 0,
        "missing": 0,
        "020": 2,
        "caution": 2,
        "low": 3,
        "040": 4,
        "060": 6,
        "medium": 6,
        "080": 8,
        "good": 8,
        "100": 10,
        "full": 10,
        "charged": 10,
    }
    width = 6
    for key, value in level.items():
        if key in name:
            width = value
            break
    shell = f'<rect class="{TEXT}" x="1" y="4" width="12" height="8" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    nub = f'<rect class="{TEXT}" x="13.4" y="6.4" width="1.3" height="3.2" fill="currentColor"/>'
    fill = ""
    if width:
        fill = f'<rect class="{POSITIVE}" x="2.2" y="5.3" width="{width}" height="5.4" fill="currentColor"/>'
    bolt = ""
    if "charging" in name or "plugged" in name or "ac-adapter" in name:
        bolt = f'<path class="{HIGHLIGHT}" d="M8.4 5.6L6.4 8.4h2.2L7.2 11" fill="none" stroke="currentColor" stroke-width="1"/>'
    return wrap(shell + nub + fill + bolt)


def bell(unread: bool) -> str:
    body = (
        f'<path class="{TEXT}" d="M8 2.4a3.6 3.6 0 0 0-3.6 3.6v2l-1.1 1.6h9.4L11.6 8V6a3.6 3.6 0 0 0-3.6-3.6z" '
        f'fill="none" stroke="currentColor" stroke-width="1.2"/>'
        f'<path class="{TEXT}" d="M6.7 11.2a1.3 1.3 0 0 0 2.6 0" fill="none" stroke="currentColor" stroke-width="1.1"/>'
    )
    if unread:
        body += f'<circle class="{HIGHLIGHT}" cx="11.7" cy="3.3" r="1.45" fill="currentColor"/>'
    return wrap(body)


def drawing_for(stem: str) -> str | None:
    name = stem.removesuffix("-symbolic").removesuffix("-panel")
    if name in {"user-desktop", "folder-desktop"}:
        return monitor()
    if name in {"user-trash", "user-trash-full"} or name.startswith("user-trash"):
        return trash("full" in name)
    if name.startswith("folder") or name in {"user-home", "folder-home", "folder_home"}:
        role = FOLDER_ROLE.get(name, HIGHLIGHT)
        return folder(role, open_folder=name == "folder-open")
    if name.startswith("audio-volume") or name.startswith("audio-volume".replace("audio-", "")):
        return volume(name)
    if name.startswith("network-wireless") or name.startswith("network-wired"):
        return network(name)
    if name.startswith("battery"):
        return battery(name)
    if "notification" in name:
        return bell("new" in name or "unread" in name)
    return None


def apply(root: Path) -> int:
    count = 0
    for path in root.rglob("*.svg"):
        drawing = drawing_for(path.stem)
        # @2x lives in the directory name, not the stem.
        if drawing is None:
            continue
        path.write_text(drawing)
        count += 1
    return count


def main() -> None:
    roots = [Path(arg) for arg in sys.argv[1:]]
    for root in roots:
        print(root, apply(root))


if __name__ == "__main__":
    main()
