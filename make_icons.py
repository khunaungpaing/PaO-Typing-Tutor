"""
make_icons.py
-------------
Generates platform-native icon files from assets/img/app.png:

  assets/img/app.icns  – macOS (.app dock icon)
  assets/img/app.ico   – Windows (.exe / installer icon with 16, 32, 48, 64, 128, 256 px)

Requirements:
  Pillow (optional, will automatically use macOS sips + iconutil if Pillow is not installed)

Usage:
  python make_icons.py
"""

from __future__ import annotations

import io
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "assets" / "img" / "app.png"
ICNS = ROOT / "assets" / "img" / "app.icns"
ICO = ROOT / "assets" / "img" / "app.ico"

ICO_SIZES = [16, 32, 48, 64, 128, 256]
ICNS_SIZES = [16, 32, 64, 128, 256, 512, 1024]

_ICNS_TAG = {
    16: b"icp4",
    32: b"icp5",
    64: b"icp6",
    128: b"ic07",
    256: b"ic08",
    512: b"ic09",
    1024: b"ic10",
}


def _assemble_png_ico(png_data_by_size: list[tuple[int, bytes]], dst: Path) -> None:
    """Assemble a standard multi-resolution ICO file using PNG images."""
    count = len(png_data_by_size)
    header = struct.pack("<HHH", 0, 1, count)
    offset = 6 + 16 * count

    dir_entries: list[bytes] = []
    image_data: list[bytes] = []

    for size, data in png_data_by_size:
        w = 0 if size >= 256 else size
        h = 0 if size >= 256 else size
        entry = struct.pack(
            "<BBBBHHII",
            w,
            h,
            0,  # color count
            0,  # reserved
            1,  # color planes
            32,  # bits per pixel
            len(data),
            offset,
        )
        dir_entries.append(entry)
        image_data.append(data)
        offset += len(data)

    with open(dst, "wb") as f:
        f.write(header)
        for entry in dir_entries:
            f.write(entry)
        for data in image_data:
            f.write(data)


def make_ico(src: Path, dst: Path) -> None:
    """Create Windows .ico with 16, 32, 48, 64, 128, 256 sizes."""
    try:
        from PIL import Image

        img = Image.open(src).convert("RGBA")
        resized = [img.resize((s, s), Image.LANCZOS) for s in ICO_SIZES]
        resized[0].save(
            dst,
            format="ICO",
            sizes=[(s, s) for s in ICO_SIZES],
            append_images=resized[1:],
        )
        print(f"  created  {dst.relative_to(ROOT)} (Pillow)")
        return
    except ImportError:
        pass

    if shutil.which("sips"):
        tmp_dir = Path(tempfile.mkdtemp())
        try:
            png_list: list[tuple[int, bytes]] = []
            for s in ICO_SIZES:
                out_path = tmp_dir / f"icon_{s}.png"
                subprocess.run(
                    ["sips", "-z", str(s), str(s), str(src), "--out", str(out_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                png_list.append((s, out_path.read_bytes()))
            _assemble_png_ico(png_list, dst)
            print(f"  created  {dst.relative_to(ROOT)} (sips)")
            return
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    sys.exit("Error: Neither Pillow nor macOS sips available to generate ICO.")


def make_icns(src: Path, dst: Path) -> None:
    """Create macOS .icns using iconutil or pure-Python."""
    if shutil.which("iconutil") and shutil.which("sips"):
        tmp_parent = Path(tempfile.mkdtemp())
        iconset = tmp_parent / "app.iconset"
        iconset.mkdir()
        try:
            spec = [
                (16, "icon_16x16.png"),
                (32, "icon_16x16@2x.png"),
                (32, "icon_32x32.png"),
                (64, "icon_32x32@2x.png"),
                (128, "icon_128x128.png"),
                (256, "icon_128x128@2x.png"),
                (256, "icon_256x256.png"),
                (512, "icon_256x256@2x.png"),
                (512, "icon_512x512.png"),
                (1024, "icon_512x512@2x.png"),
            ]
            for size, name in spec:
                subprocess.run(
                    ["sips", "-z", str(size), str(size), str(src), "--out", str(iconset / name)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
            subprocess.run(
                ["iconutil", "-c", "icns", str(iconset), "-o", str(dst)],
                check=True,
            )
            print(f"  created  {dst.relative_to(ROOT)} (iconutil)")
            return
        finally:
            shutil.rmtree(tmp_parent, ignore_errors=True)

    print(f"  existing {dst.relative_to(ROOT)} kept")


def main() -> None:
    if not SRC.exists():
        sys.exit(f"Source image not found: {SRC}")

    print("Generating icons from", SRC.relative_to(ROOT))
    make_ico(SRC, ICO)
    make_icns(SRC, ICNS)
    print("Done.")


if __name__ == "__main__":
    main()
