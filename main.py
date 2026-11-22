#!/usr/bin/env python3
"""Entry builder: the-picture-that-tastes-of-one.

Reads honey.jpg (photoreal honeycomb macro, one ingredient: honey)
from the directory next to this script and produces the submission
image at /output/entry.png — exactly 1024x1024 pixels and at most
1 MiB. Exits non-zero if any check fails.
"""

import os
import shutil
import struct
import sys

MAX_BYTES = 1_048_576
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "honey.jpg")
OUTPUT_DIR = "/output"
OUTPUT = os.path.join(OUTPUT_DIR, "entry.png")


def jpeg_dimensions(path):
    """Return (width, height) parsed from a JPEG's SOF marker."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:2] != b"\xff\xd8":
        raise ValueError(f"not a JPEG file: {path}")
    pos = 2
    while pos + 9 < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if marker == 0xDA:  # start of scan: no more headers
            break
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        pos += 2 + length
    raise ValueError(f"could not find SOF marker in {path}")


def png_dimensions(path):
    """Return (width, height) from a PNG's IHDR chunk."""
    with open(path, "rb") as fh:
        header = fh.read(33)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG file: {path}")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def build_entry():
    if not os.path.isfile(SOURCE):
        raise FileNotFoundError(f"source image missing: {SOURCE}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        from PIL import Image

        with Image.open(SOURCE) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            if img.size != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
                raise ValueError(
                    f"source is {img.size[0]}x{img.size[1]}, "
                    f"expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"
                )
            img.save(OUTPUT, format="PNG", optimize=True)
            size = os.path.getsize(OUTPUT)
            if size > MAX_BYTES:
                rgb_size = size
                # A photoreal 1024x1024 RGB PNG runs over 1 MiB, so
                # fall back to an adaptive palette (fewer colours until
                # it fits). Honey is a narrow amber range, so 256
                # colours keeps the macro detail intact.
                for colours in (256, 128, 64):
                    pal = img.quantize(
                        colors=colours,
                        method=Image.Quantize.MEDIANCUT,
                        dither=Image.Dither.NONE,
                    )
                    pal.save(OUTPUT, format="PNG", optimize=True)
                    size = os.path.getsize(OUTPUT)
                    print(
                        f"RGB PNG was {rgb_size} bytes (over the limit); "
                        f"palette ({colours} colours): {size} bytes"
                    )
                    if size <= MAX_BYTES:
                        break
        print("re-encoded honey.jpg -> entry.png with Pillow")
    except ImportError:
        width, height = jpeg_dimensions(SOURCE)
        if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
            raise ValueError(
                f"source is {width}x{height}, "
                f"expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"
            )
        shutil.copyfile(SOURCE, OUTPUT)
        print("Pillow not available; copied honey.jpg bytes to entry.png")

    size = os.path.getsize(OUTPUT)
    if size > MAX_BYTES:
        raise ValueError(
            f"output is {size} bytes, over the {MAX_BYTES} byte limit"
        )

    if OUTPUT.endswith(".png"):
        width, height = png_dimensions(OUTPUT)
    else:  # pragma: no cover - only when Pillow is missing
        width, height = jpeg_dimensions(OUTPUT)
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise ValueError(
            f"output is {width}x{height}, "
            f"expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"
        )

    print(f"OK: {OUTPUT} is {width}x{height}, {size} bytes")
    return 0


def main():
    try:
        return build_entry()
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
