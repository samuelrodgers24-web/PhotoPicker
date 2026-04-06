#!/usr/bin/env python3
"""
rename_by_date.py - Flexible batch rename for image files.

Builds new filenames from composable parts:
  primary     first name component
  secondary   second name component (optional)
  separator   character placed between components
  counter     zero-padded sequential number (files are processed in sorted order)

Primary / secondary field choices:
  "Date (YYYY-MM-DD)"   EXIF shoot date
  "Date + Time"         EXIF date and time
  "Time (HHMMSS)"       EXIF time only
  "Camera model"        EXIF camera make/model
  "Original name"       original filename stem
  "Custom text"         literal text you provide

Falls back to file modification time if EXIF date is unavailable.

Requires: pip install exifread
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

try:
    import exifread
except ImportError:
    print("Error: exifread is required.  pip install exifread")
    sys.exit(1)

IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.heif',
    '.crw', '.cr2', '.cr3', '.nef', '.nrw', '.arw', '.srf', '.sr2',
    '.raf', '.orf', '.rw2', '.pef', '.ptx', '.srw', '.rwl', '.dng',
    '.3fr', '.fff', '.iiq', '.x3f', '.dcr', '.kdc', '.mrw', '.gpr',
    '.bay', '.erf', '.mef', '.mos',
}

# ─────────────────────────── EXIF helpers ─────────────────────────────────────

def _read_exif(path):
    """Return the raw exifread tag dict for a file."""
    try:
        with open(path, 'rb') as f:
            return exifread.process_file(f, details=False)
    except Exception:
        return {}


def get_exif_date(tags):
    """Parse DateTimeOriginal (or Image DateTime) from an exifread tag dict."""
    raw = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
    if raw:
        try:
            return datetime.strptime(str(raw), '%Y:%m:%d %H:%M:%S')
        except ValueError:
            pass
    return None


def get_camera_model(tags):
    """Return a filesystem-safe camera model string, e.g. 'Canon_EOS_R5'."""
    make  = str(tags.get('Image Make',  '') or '').strip()
    model = str(tags.get('Image Model', '') or '').strip()

    # Avoid redundancy when make is already in model (e.g. "Canon Canon EOS R5")
    if make and model.lower().startswith(make.lower()):
        label = model
    elif make and model:
        label = f"{make} {model}"
    else:
        label = model or make or 'unknown-camera'

    # Replace characters that are unsafe in filenames
    for ch in r'/\:*?"<>|':
        label = label.replace(ch, '')
    return label.strip().replace(' ', '_')


# ─────────────────────────── field resolver ───────────────────────────────────

def resolve_field(field, custom_text, dt, camera, original_stem):
    """
    Return the string component for one field choice.
    Returns None when field is 'None' (used for secondary).
    """
    if field == 'Date (YYYY-MM-DD)':
        return dt.strftime('%Y-%m-%d') if dt else 'no-date'
    if field == 'Date + Time':
        return dt.strftime('%Y-%m-%d_%H%M%S') if dt else 'no-datetime'
    if field == 'Time (HHMMSS)':
        return dt.strftime('%H%M%S') if dt else 'no-time'
    if field == 'Camera model':
        return camera
    if field == 'Original name':
        return original_stem
    if field == 'Custom text':
        return custom_text.strip() if custom_text.strip() else 'custom'
    return None   # 'None' choice


# ─────────────────────────── rename plan ──────────────────────────────────────

def build_plan(files, primary, secondary, separator, custom_primary,
               custom_secondary, counter_digits, counter_start):
    """
    Return:
        plan    — list of (src_path, new_name_str) for every processed file
        no_exif — list of filenames where mtime fallback was used for the date
    """
    used_names = set()
    plan       = []
    no_exif    = []

    for idx, f in enumerate(files):
        tags   = _read_exif(f)
        dt     = get_exif_date(tags)
        camera = get_camera_model(tags)

        if dt is None and primary in ('Date (YYYY-MM-DD)', 'Date + Time', 'Time (HHMMSS)'):
            dt = datetime.fromtimestamp(f.stat().st_mtime)
            no_exif.append(f.name)

        original_stem = f.stem

        primary_part   = resolve_field(primary,   custom_primary,   dt, camera, original_stem)
        secondary_part = resolve_field(secondary, custom_secondary, dt, camera, original_stem)

        parts = [primary_part]
        if secondary_part is not None:
            parts.append(secondary_part)

        if counter_digits > 0:
            n = counter_start + idx
            parts.append(str(n).zfill(counter_digits))

        base = separator.join(p for p in parts if p)
        ext  = f.suffix.lower()

        # Collision handling (only needed when counter is off)
        if counter_digits > 0:
            new_name = base + ext
        else:
            new_name = _unique_name(base, ext, used_names)

        used_names.add(new_name)
        plan.append((f, new_name))

    return plan, no_exif


def _unique_name(base, ext, used):
    candidate = base + ext
    if candidate not in used:
        return candidate
    n = 2
    while True:
        candidate = f"{base}_{n}{ext}"
        if candidate not in used:
            return candidate
        n += 1


# ─────────────────────────── main ─────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description='Flexible image batch rename.')
    p.add_argument('folder')
    p.add_argument('--primary',          default='Date (YYYY-MM-DD)')
    p.add_argument('--secondary',        default='None')
    p.add_argument('--separator',        default='_')
    p.add_argument('--custom-primary',   default='')
    p.add_argument('--custom-secondary', default='')
    p.add_argument('--counter-digits',   type=int, default=0)
    p.add_argument('--counter-start',    type=int, default=1)
    p.add_argument('--dry-run',          action='store_true')
    args = p.parse_args()

    folder = Path(args.folder)
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

    print(f"{'Dry run — previewing' if args.dry_run else 'Renaming'} "
          f"{len(files)} files in: {folder}\n")

    plan, no_exif = build_plan(
        files,
        primary          = args.primary,
        secondary        = args.secondary,
        separator        = args.separator,
        custom_primary   = args.custom_primary,
        custom_secondary = args.custom_secondary,
        counter_digits   = args.counter_digits,
        counter_start    = args.counter_start,
    )

    if no_exif:
        print(f"No EXIF date (using file modification time) for {len(no_exif)} file(s):")
        for name in no_exif:
            print(f"  {name}")
        print()

    changes   = [(s, n) for s, n in plan if s.name != n]
    unchanged = [(s, n) for s, n in plan if s.name == n]

    if not changes:
        print("All files already match the target pattern. Nothing to rename.")
        sys.exit(0)

    col = max(len(s.name) for s, _ in changes)
    for src, new_name in changes:
        print(f"  {src.name:<{col}}  →  {new_name}")

    summary = f"\n{len(changes)} file{'s' if len(changes) != 1 else ''} to rename"
    if unchanged:
        summary += f", {len(unchanged)} already correct."
    print(summary)

    if args.dry_run:
        print("\n(Dry run — no files were renamed.)")
        sys.exit(0)

    for src, new_name in changes:
        src.rename(src.parent / new_name)

    print("\nDone.")


if __name__ == '__main__':
    main()
