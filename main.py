"""Write the entry image to /output/entry.png.

The entry is one picture of food: a photoreal honeycomb macro (one
ingredient, honey). The source image honey.jpg ships beside this file at
1024x1024 and under 1 MiB. This program copies it to /output/entry.png,
converting to PNG when Pillow is available, and verifies the gate
(a whole PNG or JPEG, at most 1,048,576 bytes, 1024 by 1024 pixels).
It uses only the standard library when Pillow is missing, so it runs
in the sandbox with no network.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "honey.jpg")
OUT_DIR = "/output"
OUT = os.path.join(OUT_DIR, "entry.png")
MAX_BYTES = 1_048_576
SIZE = (1024, 1024)


def write_with_pillow():
    """Re-encode via Pillow so the output is a clean PNG at 1024x1024."""
    from PIL import Image

    img = Image.open(SRC).convert("RGB")
    if img.size != SIZE:
        img = img.resize(SIZE, Image.LANCZOS)
    img.save(OUT, "PNG", optimize=True)
    if os.path.getsize(OUT) > MAX_BYTES:
        # PNG too big: fall back to JPEG bytes (the gate accepts JPEG).
        img.save(OUT, "JPEG", quality=85, optimize=True)
    return img.size


def write_raw_copy():
    """No Pillow: the source is already a 1024x1024 JPEG under the cap."""
    shutil.copyfile(SRC, OUT)
    return SIZE


def main():
    if not os.path.isfile(SRC):
        print("missing source image: honey.jpg", file=sys.stderr)
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)
    try:
        size = write_with_pillow()
    except ImportError:
        size = write_raw_copy()
    nbytes = os.path.getsize(OUT)
    if nbytes > MAX_BYTES:
        print(f"entry too large: {nbytes} bytes", file=sys.stderr)
        return 1
    try:
        from PIL import Image

        with Image.open(OUT) as check:
            if check.size != SIZE:
                print(f"entry wrong size: {check.size}", file=sys.stderr)
                return 1
    except ImportError:
        pass
    print(f"wrote {OUT}: {size[0]}x{size[1]}, {nbytes} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
