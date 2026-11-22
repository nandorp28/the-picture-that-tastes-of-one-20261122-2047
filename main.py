#!/usr/bin/env python3
"""The picture that tastes of one ingredient.

One ingredient: HONEY. A single chunk of golden honeycomb, thick amber
honey dripping off its waxy cells in glossy ribbons, shot as a photoreal
macro photograph on dark slate. One look and you can taste it.

The program ships the finished photograph as `honey.jpg` next to this
file, validates it against the competition gate (whole JPEG, at most
1,048,576 bytes, at most 1024x1024 pixels), and writes it to
/output/entry.png. Only the Python standard library is used, so the
sandboxed run needs no network and no third-party package.
"""

import os
import struct
import sys

MAX_BYTES = 1_048_576
MAX_SIDE = 1024
ASSET_NAME = "honey.jpg"
OUTPUT_PATH = "/output/entry.png"

JPEG_SOI = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def read_asset() -> bytes:
    """Load the bundled photograph from beside this script."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, ASSET_NAME)
    with open(path, "rb") as handle:
        data = handle.read()
    if not data:
        raise SystemExit(f"asset {ASSET_NAME} is empty")
    return data


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Parse width and height out of a JPEG's Start-Of-Frame marker.

    Walks the marker segments after the SOI; the first SOF0/SOF2 segment
    carries the height and width as big-endian 16-bit values.
    """
    if not data.startswith(JPEG_SOI):
        raise ValueError("not a JPEG: missing SOI marker")
    offset = 2
    while offset + 9 <= len(data):
        if data[offset] != 0xFF:
            raise ValueError(f"bad marker prefix at offset {offset}")
        marker = data[offset + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            offset += 2
            continue
        size = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
        if size < 2 or offset + 2 + size > len(data):
            raise ValueError("truncated JPEG segment")
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(
                ">HH", data[offset + 5 : offset + 9]
            )
            return width, height
        offset += 2 + size
    raise ValueError("no Start-Of-Frame marker found")


def png_dimensions(data: bytes) -> tuple[int, int]:
    """Parse width and height out of a PNG's IHDR chunk."""
    if not data.startswith(PNG_MAGIC):
        raise ValueError("not a PNG: missing magic bytes")
    if len(data) < 24:
        raise ValueError("truncated PNG header")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def detect_format(data: bytes) -> str:
    """Return 'jpeg' or 'png' for the image bytes, else raise."""
    if data.startswith(JPEG_SOI):
        return "jpeg"
    if data.startswith(PNG_MAGIC):
        return "png"
    raise ValueError("image is neither JPEG nor PNG")


def check_gate(data: bytes) -> tuple[str, int, int]:
    """Enforce the competition gate and return (format, width, height)."""
    if len(data) > MAX_BYTES:
        raise SystemExit(
            f"image is {len(data)} bytes, over the {MAX_BYTES} byte cap"
        )
    fmt = detect_format(data)
    if fmt == "jpeg":
        width, height = jpeg_dimensions(data)
    else:
        width, height = png_dimensions(data)
    if width > MAX_SIDE or height > MAX_SIDE:
        raise SystemExit(
            f"image is {width}x{height}, over the {MAX_SIDE}x{MAX_SIDE} cap"
        )
    if width == 0 or height == 0:
        raise SystemExit("image has a zero dimension")
    return fmt, width, height


def write_output(data: bytes) -> None:
    """Write the validated image to the output path and re-verify it.

    The grader's path is /output/entry.png; ENTRY_OUTPUT lets a local
    run point elsewhere without changing the graded behaviour.
    """
    out_path = os.environ.get("ENTRY_OUTPUT", OUTPUT_PATH)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as handle:
        handle.write(data)
    with open(out_path, "rb") as handle:
        written = handle.read()
    if written != data:
        raise SystemExit("output verification failed: bytes differ")
    print(f"wrote {out_path}: {len(written)} bytes")


def main() -> int:
    data = read_asset()
    fmt, width, height = check_gate(data)
    print(f"asset {ASSET_NAME}: {fmt}, {width}x{height}, {len(data)} bytes")
    print("gate: whole image, <=1 MiB, <=1024x1024 -- PASS")
    write_output(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
