#!/usr/bin/env python3
"""
move_files.py - Move all files from one folder into another.

Usage:
    python move_files.py <source_folder> <dest_folder>

Moves every file (not subdirectories) from source_folder into dest_folder.
Skips files that already exist at the destination.
"""

import sys
import shutil
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print("Usage: python move_files.py <source_folder> <dest_folder>")
        sys.exit(1)

    source = Path(sys.argv[1])
    dest   = Path(sys.argv[2])

    for folder, label in [(source, 'source'), (dest, 'destination')]:
        if folder != dest and not folder.is_dir():
            print(f"Error: '{folder}' is not a directory ({label})")
            sys.exit(1)

    files = sorted(f for f in source.iterdir() if f.is_file())

    if not files:
        print("No files found in source folder.")
        sys.exit(0)

    dest.mkdir(parents=True, exist_ok=True)

    moved = 0
    for f in files:
        dst = dest / f.name
        if dst.exists():
            print(f"  SKIP (already exists): {f.name}")
            continue
        shutil.move(str(f), dst)
        print(f"  {f.name}")
        moved += 1

    print(f"\nMoved {moved} file{'s' if moved != 1 else ''} to: {dest}")


if __name__ == '__main__':
    main()
