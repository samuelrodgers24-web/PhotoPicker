#!/usr/bin/env python3
"""
delete_files.py - Permanently delete all files in a folder.

Usage:
    python delete_files.py <folder>

Deletes every file directly inside <folder>. Subdirectories are left untouched.
This action cannot be undone.
"""

import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("Usage: python delete_files.py <folder>")
        sys.exit(1)

    folder = Path(sys.argv[1])

    if not folder.is_dir():
        print(f"Error: '{folder}' is not a directory")
        sys.exit(1)

    files = sorted(f for f in folder.iterdir() if f.is_file())

    if not files:
        print("No files found.")
        sys.exit(0)

    deleted = 0
    for f in files:
        f.unlink()
        print(f"  Deleted: {f.name}")
        deleted += 1

    print(f"\nDeleted {deleted} file{'s' if deleted != 1 else ''} from: {folder}")


if __name__ == '__main__':
    main()
