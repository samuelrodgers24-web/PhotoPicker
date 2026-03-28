#!/usr/bin/env python3
"""
verify_copy.py - Confirm that files were copied to a destination without corruption.

Usage:
    python verify_copy.py <source_folder> <dest_folder>

Computes an MD5 checksum for every file in source_folder and compares it to the
matching file in dest_folder. Reports missing files and checksum mismatches.
Run this after copying files to an external drive before deleting the originals.
"""

import sys
import hashlib
from pathlib import Path


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(source, dest):
    source_files = sorted(f for f in source.iterdir() if f.is_file())

    if not source_files:
        print("No files in source folder.")
        return True

    missing    = []
    mismatched = []
    ok_count   = 0
    total      = len(source_files)

    for i, src in enumerate(source_files, 1):
        print(f"\r  Checking {i}/{total}:  {src.name:<50}", end='', flush=True)
        dst = dest / src.name
        if not dst.exists():
            missing.append(src.name)
        elif md5(src) != md5(dst):
            mismatched.append(src.name)
        else:
            ok_count += 1

    print()  # end the progress line

    print(f"\n  Verified OK : {ok_count}")
    print(f"  Missing     : {len(missing)}")
    print(f"  Mismatched  : {len(mismatched)}")

    if missing:
        print(f"\nMissing in destination ({len(missing)}):")
        for name in missing:
            print(f"  {name}")

    if mismatched:
        print(f"\nChecksum mismatch — possible corruption ({len(mismatched)}):")
        for name in mismatched:
            print(f"  {name}")

    if not missing and not mismatched:
        print("\nAll files verified successfully.")
        return True

    return False


def main():
    if len(sys.argv) != 3:
        print("Usage: python verify_copy.py <source_folder> <dest_folder>")
        sys.exit(1)

    source = Path(sys.argv[1])
    dest   = Path(sys.argv[2])

    for folder, label in [(source, 'source_folder'), (dest, 'dest_folder')]:
        if not folder.is_dir():
            print(f"Error: '{folder}' is not a directory ({label})")
            sys.exit(1)

    print(f"Source : {source}")
    print(f"Dest   : {dest}")
    print(f"Comparing checksums...\n")

    ok = verify(source, dest)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
