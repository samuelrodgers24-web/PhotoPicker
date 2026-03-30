#!/usr/bin/env python3
"""
diff_folders.py - Copy files that exist in one folder but not another.

Usage:
    python diff_folders.py <folder_a> <folder_b> <output_folder>

Copies every file from folder_a whose filename does NOT appear in folder_b
into output_folder. Comparison is by filename only, not content.

Example — collect the rejected photos after a PhotoPicker session:
    python diff_folders.py "D:\\Photos\\Shoot1" "D:\\Photos\\Shoot1\\selected" "D:\\Photos\\Shoot1\\rejected"
"""

import sys
import shutil
from pathlib import Path


def main():
    if len(sys.argv) != 4:
        print("Usage: python diff_folders.py <folder_a> <folder_b> <output_folder>")
        print("       Copies files in folder_a that are NOT in folder_b to output_folder.")
        sys.exit(1)

    folder_a = Path(sys.argv[1])
    folder_b = Path(sys.argv[2])
    out_dir   = Path(sys.argv[3])

    for folder, label in [(folder_a, 'folder_a'), (folder_b, 'folder_b')]:
        if not folder.is_dir():
            print(f"Error: '{folder}' is not a directory ({label})")
            sys.exit(1)

    names_in_b = {f.name for f in folder_b.iterdir() if f.is_file()}

    only_in_a = [f for f in folder_a.iterdir() if f.is_file() and f.name not in names_in_b]

    if not only_in_a:
        print("No difference found — every file in folder_a also exists in folder_b.")
        sys.exit(0)

    out_dir.mkdir(parents=True, exist_ok=True)

    for src in sorted(only_in_a):
        shutil.copy2(src, out_dir / src.name)
        print(f"  {src.name}")

    print(f"\nCopied {len(only_in_a)} file{'s' if len(only_in_a) != 1 else ''} to: {out_dir}")


if __name__ == '__main__':
    main()
