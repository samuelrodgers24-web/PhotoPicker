#!/usr/bin/env python3
"""
separate_raws.py - Split a mixed folder into raw/, jpeg/, and video/ subfolders.

Usage:
    python separate_raws.py <folder>
    python separate_raws.py <folder> --copy   # copy instead of move

Moves all recognized files into subfolders created inside <folder>:
    <folder>/raw/   — camera RAW files
    <folder>/jpeg/  — JPEG and other preview/export formats
    <folder>/video/ — video files

Files with unrecognized extensions are left in place and listed at the end.
"""

import sys
import shutil
from pathlib import Path

# Preview / export formats
JPEG_EXTENSIONS = {
    '.jpg', '.jpeg',    # JPEG
    '.png',             # PNG
    '.tiff', '.tif',    # TIFF
    '.webp',            # WebP
    '.bmp',             # Bitmap
    '.gif',             # GIF
    '.heic', '.heif',   # Apple HEIC (iPhone, newer cameras)
    '.avif',            # AVIF
    '.jxl',             # JPEG XL
}

VIDEO_EXTENSIONS = {
    '.mp4', '.mov',         # Most cameras and phones
    '.avi',                 # Older cameras
    '.mts', '.m2ts',        # AVCHD (Sony, Panasonic, Canon)
    '.mxf',                 # Professional cinema cameras
    '.mkv',                 # Container format
    '.wmv',                 # Windows
    '.m4v',                 # iTunes / Apple
    '.3gp',                 # Older mobile
    '.r3d',                 # RED cameras
    '.braw',                # Blackmagic RAW video
    '.ari',                 # ARRI
}

# RAW formats grouped by brand for reference
RAW_EXTENSIONS = {
    # Canon
    '.crw', '.cr2', '.cr3',
    # Nikon
    '.nef', '.nrw',
    # Sony
    '.arw', '.srf', '.sr2',
    # Fujifilm
    '.raf',
    # Olympus / OM System
    '.orf',
    # Panasonic / Leica (some)
    '.rw2',
    # Pentax / Ricoh
    '.pef', '.ptx',
    # Samsung
    '.srw',
    # Leica
    '.rwl', '.dng',     # DNG also used by many others (Adobe universal raw)
    # Hasselblad
    '.3fr', '.fff',
    # Phase One
    '.iiq',
    # Sigma
    '.x3f',
    # Kodak
    '.dcr', '.kdc',
    # Minolta / early Sony
    '.mrw',
    # GoPro
    '.gpr',
    # Casio
    '.bay',
    # Epson
    '.erf',
    # Mamiya
    '.mef',
    # Leaf
    '.mos',
}


def separate(folder: Path, copy: bool):
    files = [f for f in folder.iterdir() if f.is_file()]

    raws   = [f for f in files if f.suffix.lower() in RAW_EXTENSIONS]
    jpegs  = [f for f in files if f.suffix.lower() in JPEG_EXTENSIONS]
    videos = [f for f in files if f.suffix.lower() in VIDEO_EXTENSIONS]
    unknown = [
        f for f in files
        if f.suffix.lower() not in RAW_EXTENSIONS
        and f.suffix.lower() not in JPEG_EXTENSIONS
        and f.suffix.lower() not in VIDEO_EXTENSIONS
    ]

    if not raws and not jpegs and not videos:
        print("No recognized files found.")
        if unknown:
            print(f"\nUnrecognized files ({len(unknown)}):")
            for f in sorted(unknown):
                print(f"  {f.name}")
        sys.exit(0)

    op   = shutil.copy2 if copy else shutil.move
    verb = 'Copied' if copy else 'Moved'

    def transfer_group(file_list: list, dest_dir: Path, label: str):
        if not file_list:
            return
        dest_dir.mkdir(exist_ok=True)
        print(f"\n{label}  →  {dest_dir.name}/")
        for src in sorted(file_list):
            dest = dest_dir / src.name
            if dest.exists():
                print(f"  SKIP (already exists): {src.name}")
                continue
            op(str(src), dest)
            print(f"  {src.name}")
        print(f"  {verb} {len(file_list)} file{'s' if len(file_list) != 1 else ''}.")

    transfer_group(raws,   folder / 'raw',   'RAW files')
    transfer_group(jpegs,  folder / 'jpeg',  'Preview/JPEG files')
    transfer_group(videos, folder / 'video', 'Video files')

    if unknown:
        print(f"\nLeft in place — unrecognized extension ({len(unknown)}):")
        for f in sorted(unknown):
            print(f"  {f.name}")


def main():
    args = sys.argv[1:]
    copy = '--copy' in args
    paths = [a for a in args if not a.startswith('-')]

    if not paths:
        print("Usage: python separate_raws.py <folder> [--copy]")
        sys.exit(1)

    folder = Path(paths[0])
    if not folder.is_dir():
        print(f"Error: '{folder}' is not a directory")
        sys.exit(1)

    separate(folder, copy)


if __name__ == '__main__':
    main()
