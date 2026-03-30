#!/usr/bin/env python3
"""
rename_by_date.py - Rename image files using their EXIF shoot date.

Usage:
    python rename_by_date.py <folder>
    python rename_by_date.py <folder> --dry-run

Renames files to YYYY-MM-DD_HHMMSS.ext using the EXIF DateTimeOriginal tag.
If two files share the same timestamp, a counter suffix is added (_2, _3, ...).
Files with no EXIF date fall back to file modification time (flagged in output).
Use --dry-run to preview all renames without making any changes.

Requires: pip install exifread
"""

import sys
from pathlib import Path
from datetime import datetime

try:
    import exifread
except ImportError:
    print("Error: exifread is required.")
    print("       pip install exifread")
    sys.exit(1)

# ── Format ────────────────────────────────────────────────────────────────────
# Change this to adjust the output filename pattern.
# Tokens: %Y year, %m month, %d day, %H hour, %M minute, %S second
DATE_FORMAT = '%Y-%m-%d_%H%M%S'

# Extensions to process (others are skipped without being renamed)
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.heif',
    '.crw', '.cr2', '.cr3', '.nef', '.nrw', '.arw', '.srf', '.sr2',
    '.raf', '.orf', '.rw2', '.pef', '.ptx', '.srw', '.rwl', '.dng',
    '.3fr', '.fff', '.iiq', '.x3f', '.dcr', '.kdc', '.mrw', '.gpr',
    '.bay', '.erf', '.mef', '.mos',
}
# ─────────────────────────────────────────────────────────────────────────────


def get_exif_date(path):
    """Return the EXIF DateTimeOriginal for the file, or None if unavailable."""
    try:
        with open(path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal', details=False)
        tag = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
        if tag:
            return datetime.strptime(str(tag), '%Y:%m:%d %H:%M:%S')
    except Exception:
        pass
    return None


def unique_name(base, ext, used):
    """Return base+ext, or base_2+ext, base_3+ext ... until the name is unused."""
    candidate = base + ext
    if candidate not in used:
        return candidate
    n = 2
    while True:
        candidate = f"{base}_{n}{ext}"
        if candidate not in used:
            return candidate
        n += 1


def build_plan(files):
    """
    Given a sorted list of Paths, return:
        plan      — list of (src_path, new_name_str) for files that need renaming
        no_exif   — list of filenames where mtime fallback was used
    """
    used_names = set()
    plan = []
    no_exif = []

    for f in files:
        dt = get_exif_date(f)
        if dt is None:
            dt = datetime.fromtimestamp(f.stat().st_mtime)
            no_exif.append(f.name)

        base     = dt.strftime(DATE_FORMAT)
        new_name = unique_name(base, f.suffix.lower(), used_names)
        used_names.add(new_name)
        plan.append((f, new_name))

    return plan, no_exif


def main():
    args    = sys.argv[1:]
    dry_run = '--dry-run' in args
    paths   = [a for a in args if not a.startswith('-')]

    if not paths:
        print("Usage: python rename_by_date.py <folder> [--dry-run]")
        sys.exit(1)

    folder = Path(paths[0])
    if not folder.is_dir():
        print(f"Error: '{folder}' is not a directory")
        sys.exit(1)

    files = sorted(
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not files:
        print("No recognized image files found.")
        sys.exit(0)

    print(f"{'Dry run — previewing' if dry_run else 'Renaming'} {len(files)} files in: {folder}\n")

    plan, no_exif = build_plan(files)

    if no_exif:
        print(f"No EXIF date (using file modification time) for {len(no_exif)} file(s):")
        for name in no_exif:
            print(f"  {name}")
        print()

    changes   = [(src, name) for src, name in plan if src.name != name]
    unchanged = [(src, name) for src, name in plan if src.name == name]

    if not changes:
        print("All files already match the date format. Nothing to rename.")
        sys.exit(0)

    for src, new_name in changes:
        print(f"  {src.name:<40}  ->  {new_name}")

    print(f"\n{len(changes)} file{'s' if len(changes) != 1 else ''} to rename"
          + (f", {len(unchanged)} already correct." if unchanged else "."))

    if dry_run:
        print("\n(Dry run — no files were renamed.)")
        sys.exit(0)

    for src, new_name in changes:
        src.rename(src.parent / new_name)

    print("Done.")


if __name__ == '__main__':
    main()
