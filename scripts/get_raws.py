#!/usr/bin/env python3
"""
get_raws.py - Copy RAW files whose base names match a folder of preview images.
Also copies any XMP sidecar files found alongside the RAWs.

Usage:
    python get_raws.py <jpeg_folder> <raw_folder> <output_folder>

For each image file in jpeg_folder, finds a file with the same base name
(ignoring extension) in raw_folder and copies it to output_folder.
XMP sidecars (IMG_1234.xmp or IMG_1234.CR3.xmp) are copied automatically.

Example:
    python get_raws.py "D:\\Photos\\Shoot1\\selected" "D:\\Photos\\Shoot1\\RAW" "D:\\Photos\\Shoot1\\selected_raw"

    If selected/ contains IMG_1234.jpg, IMG_1589.jpg ...
    and RAW/        contains IMG_1234.CR3, IMG_1589.CR3, IMG_1234.xmp ...
    then selected_raw/ will contain IMG_1234.CR3, IMG_1589.CR3, IMG_1234.xmp ...
"""

import sys
import shutil
from pathlib import Path

PREVIEW_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}


def main():
    if len(sys.argv) != 4:
        print("Usage: python get_raws.py <jpeg_folder> <raw_folder> <output_folder>")
        print("       Copies RAW files from raw_folder that match image names in jpeg_folder.")
        sys.exit(1)

    jpeg_dir = Path(sys.argv[1])
    raw_dir  = Path(sys.argv[2])
    out_dir  = Path(sys.argv[3])

    for folder, label in [(jpeg_dir, 'jpeg_folder'), (raw_dir, 'raw_folder')]:
        if not folder.is_dir():
            print(f"Error: '{folder}' is not a directory ({label})")
            sys.exit(1)

    # Build a map of stem -> file path for RAW files and XMP sidecars.
    # XMP files can be named IMG_1234.xmp or IMG_1234.CR3.xmp — both are
    # indexed by the base stem (e.g. 'img_1234') so either style is found.
    raw_by_stem = {}
    xmp_by_stem = {}
    for f in raw_dir.iterdir():
        if not f.is_file():
            continue
        if f.suffix.lower() == '.xmp':
            # Path('IMG_1234.CR3.xmp').stem -> 'IMG_1234.CR3'
            # Path('IMG_1234.CR3').stem     -> 'IMG_1234'  (strips RAW ext too)
            key = Path(f.stem).stem.lower()
            xmp_by_stem[key] = f
        else:
            raw_by_stem[f.stem.lower()] = f

    # Find preview files in jpeg_folder and look up matching raws
    matched = []    # list of (raw_path, xmp_path_or_None)
    unmatched = []

    for f in sorted(jpeg_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in PREVIEW_EXTENSIONS:
            raw = raw_by_stem.get(f.stem.lower())
            if raw:
                xmp = xmp_by_stem.get(f.stem.lower())
                matched.append((raw, xmp))
            else:
                unmatched.append(f.name)

    if not matched:
        print("No matching RAW files found.")
        if unmatched:
            print(f"\nPreview files with no RAW match ({len(unmatched)}):")
            for name in unmatched:
                print(f"  {name}")
        sys.exit(0)

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Found {len(matched)} matching RAW file{'s' if len(matched) != 1 else ''}. Copying...")

    xmp_count = 0
    for raw, xmp in matched:
        shutil.copy2(raw, out_dir / raw.name)
        print(f"  {raw.name}")
        if xmp:
            shutil.copy2(xmp, out_dir / xmp.name)
            print(f"  {xmp.name}  (sidecar)")
            xmp_count += 1

    print(f"\nCopied {len(matched)} RAW file{'s' if len(matched) != 1 else ''}"
          + (f" + {xmp_count} XMP sidecar{'s' if xmp_count != 1 else ''}" if xmp_count else "")
          + f" to: {out_dir}")

    if unmatched:
        print(f"\nNo RAW found for ({len(unmatched)}):")
        for name in unmatched:
            print(f"  {name}")


if __name__ == '__main__':
    main()
