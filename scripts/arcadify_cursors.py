#!/usr/bin/env python3
"""Clone the vintage cursor theme and draw every pointer as an arcade sprite.

Each Xcursor frame is sampled on a grid of about 32 cells, snapped to at most
eight flat colors, and painted as hard blocks. That is small enough to read a
question mark, an I-beam, and a resize arrow. Hotspots, frame delays, and the
vintage symlink names stay. The click cell is kept even when the tip is too
thin for the coverage test.

    python3 scripts/arcadify_cursors.py [dest]
"""

from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flatten_icon import palette, sample

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/usr/share/icons/vintage/cursors")
IMAGE_TYPE = 0xFFFD0002
COVERAGE = 0.4
SNAP = 32
MAX_COLORS = 8


def cell_for(size: int) -> int:
    """Block size whose grid stays between 24 and 48, nearest 32.

    A 24px pointer is one pixel per cell. A 48px pointer is two. The old
    16-cell grid turned the help mark and the resize arrows into blobs.
    """
    best = 1
    best_distance = 999
    for cell in range(1, size):
        if size % cell:
            continue
        grid = size // cell
        if not 24 <= grid <= 48:
            continue
        distance = abs(grid - 32)
        if distance < best_distance or (distance == best_distance and cell < best):
            best = cell
            best_distance = distance
    return best


def read_frames(path: Path) -> list[dict]:
    data = path.read_bytes()
    magic, header, _version, count = struct.unpack_from("<4sIII", data, 0)
    if magic != b"Xcur":
        raise ValueError(f"{path} is not an Xcursor")
    frames = []
    for index in range(count):
        kind, subtype, position = struct.unpack_from("<III", data, header + index * 12)
        if kind != IMAGE_TYPE:
            raise ValueError(f"{path.name} has a non-image chunk {kind:#x}")
        (
            _chunk_header,
            _chunk_type,
            nominal,
            version,
            width,
            height,
            xhot,
            yhot,
            delay,
        ) = struct.unpack_from("<IIIIIIIII", data, position)
        raw = data[position + 36 : position + 36 + width * height * 4]
        image = Image.frombytes("RGBA", (width, height), raw, "raw", "BGRA")
        frames.append(
            {
                "nominal": nominal or width,
                "version": version,
                "image": image,
                "xhot": xhot,
                "yhot": yhot,
                "delay": delay,
            }
        )
    return frames


def pin_hotspot(cells: list[list], image: Image.Image, step: int, xhot: int, yhot: int) -> None:
    """Keep the click cell when the tip is only a sliver of that block.

    The vintage hotspot often sits on a faint edge pixel, one block short of
    the solid ink. Paint that cell from the nearest solid pixel within one
    block so the click lands on the sprite.
    """
    grid_x = len(cells[0])
    grid_y = len(cells)
    gx = min(grid_x - 1, max(0, xhot // step))
    gy = min(grid_y - 1, max(0, yhot // step))
    if cells[gy][gx] is not None:
        return
    pixels = image.load()
    best = None
    best_distance = step + 1
    x0 = max(0, xhot - step)
    y0 = max(0, yhot - step)
    x1 = min(image.width, xhot + step + 1)
    y1 = min(image.height, yhot + step + 1)
    for y in range(y0, y1):
        for x in range(x0, x1):
            red, green, blue, alpha = pixels[x, y]
            if alpha < 128:
                continue
            distance = max(abs(x - xhot), abs(y - yhot))
            if distance < best_distance or (distance == best_distance and alpha > (best[3] if best else 0)):
                best_distance = distance
                best = (red, green, blue, alpha)
    if best is not None:
        cells[gy][gx] = best[:3]


def paint(cells: list[list], mapping: dict, scale: int) -> Image.Image:
    grid = len(cells)
    image = Image.new("RGBA", (grid * scale, grid * scale), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(cells):
        for x, source in enumerate(row):
            if source is None:
                continue
            red, green, blue = mapping[source]
            for dy in range(scale):
                for dx in range(scale):
                    pixels[x * scale + dx, y * scale + dy] = (red, green, blue, 255)
    return image


def arcadify_size(frames: list[dict]) -> list[dict]:
    """Arcadify every frame, sharing one palette across the frames of a size."""
    by_size: dict[int, list[int]] = {}
    for index, frame in enumerate(frames):
        by_size.setdefault(frame["image"].width, []).append(index)
    sprites: dict[int, Image.Image] = {}
    for width, indexes in by_size.items():
        cell = cell_for(width)
        sample_frame = frames[indexes[0]]["image"]
        if width % cell or sample_frame.height != width:
            continue
        grid = width // cell
        prepared = []
        for index in indexes:
            frame = frames[index]
            cells = sample(frame["image"], grid, COVERAGE)
            pin_hotspot(cells, frame["image"], cell, frame["xhot"], frame["yhot"])
            prepared.append(cells)
        mapping = palette([row for cells in prepared for row in cells], SNAP, MAX_COLORS)
        for index, cells in zip(indexes, prepared):
            sprites[index] = paint(cells, mapping, cell)
    output = []
    for index, frame in enumerate(frames):
        image = sprites.get(index, frame["image"])
        output.append({**frame, "image": image})
    return output


def write_xcursor(path: Path, frames: list[dict]) -> None:
    chunks = []
    for frame in frames:
        image = frame["image"]
        width, height = image.size
        raw = image.tobytes("raw", "BGRA")
        header = struct.pack(
            "<IIIIIIIII",
            36,
            IMAGE_TYPE,
            frame["nominal"],
            frame["version"],
            width,
            height,
            frame["xhot"],
            frame["yhot"],
            frame["delay"],
        )
        chunks.append(header + raw)
    header_size = 16
    position = header_size + len(chunks) * 12
    contents = []
    body = b""
    for frame, chunk in zip(frames, chunks):
        contents.append(struct.pack("<III", IMAGE_TYPE, frame["nominal"], position))
        body += chunk
        position += len(chunk)
    blob = struct.pack("<4sIII", b"Xcur", header_size, 0x10000, len(chunks)) + b"".join(contents) + body
    path.write_bytes(blob)


def build_cursors(dest: Path, source: Path = SOURCE) -> None:
    cursor_dir = dest / "cursors"
    if cursor_dir.exists():
        for child in cursor_dir.iterdir():
            child.unlink()
    else:
        cursor_dir.mkdir(parents=True)
    files = 0
    frames = 0
    links: list[tuple[str, str]] = []
    for entry in sorted(source.iterdir(), key=lambda path: path.name):
        if entry.is_symlink():
            links.append((entry.name, os.readlink(entry)))
            continue
        if not entry.is_file():
            continue
        sprites = arcadify_size(read_frames(entry))
        write_xcursor(cursor_dir / entry.name, sprites)
        files += 1
        frames += len(sprites)
    for name, target in links:
        link = cursor_dir / name
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(target)
    (dest / "index.theme").write_text(
        "[Icon Theme]\n"
        "Name=1989 Cursors\n"
        "Comment=Vintage pointers drawn as arcade sprites\n"
        "Inherits=vintage\n"
    )
    (dest / ".1989").write_text("1989\n")
    print(f"cursors {files} files, {frames} frames, {len(links)} links -> {dest}")


def main() -> None:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "out" / "icons" / "1989-cursors"
    build_cursors(dest)


if __name__ == "__main__":
    main()
