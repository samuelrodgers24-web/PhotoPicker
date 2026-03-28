#!/usr/bin/env python3
"""
PhotoPicker - Fast photo sorter with keyboard navigation and preloading.

Usage:
    python photopicker.py [folder]                        # Copy kept photos to folder/selected/
    python photopicker.py [folder] --output <out_folder>  # Copy to a specific output folder
    python photopicker.py [folder] --move                 # Move kept photos instead of copying

Keys:
    Right / Left arrow  Navigate
    Space / F / K       Flag current image as "keep" and advance
    U                   Unflag current image
    Q / Escape          Finish and save flagged images
"""

import os
import sys
import shutil
import threading
from pathlib import Path
import tkinter as tk

# ---------------------------------------------------------------------------
# Auto-install Pillow if missing.  Shows a small status window so the user
# knows something is happening the first time they run on a new machine.
# ---------------------------------------------------------------------------
try:
    from PIL import Image, ImageOps, ImageTk
except ImportError:
    import subprocess as _sp

    _root = tk.Tk()
    _root.title('PhotoPicker – Setup')
    _root.resizable(False, False)
    _root.configure(bg='#18181b')
    _root.geometry('360x110')
    _lbl = tk.Label(
        _root,
        text='Installing image library (Pillow)…\nThis only happens once.',
        bg='#18181b', fg='#f4f4f5',
        font=('Segoe UI', 10), justify='center',
    )
    _lbl.pack(expand=True)
    _root.update()

    _result = _sp.run(
        [sys.executable, '-m', 'pip', 'install', '--quiet', 'Pillow'],
        capture_output=True,
    )

    if _result.returncode != 0:
        _lbl.config(
            text='Could not install Pillow.\n'
                 'Please run:  pip install Pillow\n'
                 'then try again.',
            fg='#ef4444',
        )
        _root.mainloop()
        sys.exit(1)

    _root.destroy()
    from PIL import Image, ImageOps, ImageTk

SUPPORTED = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
PRELOAD_AHEAD = 3   # images to preload forward
PRELOAD_BEHIND = 2  # images to keep loaded behind


class PhotoPicker:
    def __init__(self, root, folder, output=None, move=False):
        self.root = root
        self.folder = Path(folder)
        self.selected_folder = Path(output) if output else self.folder / 'selected'
        self.move = move

        self.images = sorted(
            f for f in self.folder.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED
        )

        if not self.images:
            print(f"No supported images found in: {folder}")
            sys.exit(1)

        self.index = 0
        self.flagged = set()         # paths of flagged images
        self.pil_cache = {}          # path -> PIL.Image (resized)
        self.loading = set()         # paths currently being loaded in bg
        self.cache_lock = threading.Lock()

        self.screen_w = None
        self.screen_h = None
        self._tk_img = None          # keep reference to prevent GC

        self._setup_ui()
        self.root.after(50, self._start)  # wait for window geometry

    def _setup_ui(self):
        self.root.title("PhotoPicker")
        self.root.configure(bg='black')
        self.root.attributes('-fullscreen', True)

        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.status = tk.Label(
            self.root, text='Loading...', bg='#111', fg='white',
            font=('Consolas', 11), anchor='w', padx=12, pady=5
        )
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

        bindings = {
            '<Right>':  lambda e: self.navigate(1),
            '<Left>':   lambda e: self.navigate(-1),
            '<space>':  lambda e: self.flag_and_advance(),
            '<Return>': lambda e: self.flag_and_advance(),
            'f':        lambda e: self.flag_and_advance(),
            'k':        lambda e: self.flag_and_advance(),
            'u':        lambda e: self.unflag_current(),
            'q':        lambda e: self.quit(),
            '<Escape>': lambda e: self.quit(),
        }
        for key, fn in bindings.items():
            self.root.bind(key, fn)

    def _start(self):
        self.screen_w = self.root.winfo_width()
        self.screen_h = self.root.winfo_height()
        self._preload_around(self.index)
        self._show_current()

    # ------------------------------------------------------------------ cache

    def _resize_for_screen(self, img):
        """Resize a PIL image to fit the screen without upscaling."""
        status_h = 35
        max_w = self.screen_w
        max_h = self.screen_h - status_h
        w, h = img.size
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        return img

    def _bg_load(self, path):
        """Load and resize an image in a background thread."""
        try:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            img.load()  # force full decode now, while in bg thread
            img = self._resize_for_screen(img)
            with self.cache_lock:
                self.pil_cache[path] = img
                self.loading.discard(path)
        except Exception as exc:
            print(f"Failed to load {path.name}: {exc}", file=sys.stderr)
            with self.cache_lock:
                self.loading.discard(path)

    def _preload_around(self, center):
        indices = range(
            max(0, center - PRELOAD_BEHIND),
            min(len(self.images), center + PRELOAD_AHEAD + 1)
        )
        keep = {self.images[i] for i in indices}

        with self.cache_lock:
            # Evict entries outside the window
            for path in list(self.pil_cache):
                if path not in keep:
                    del self.pil_cache[path]
            # Schedule background loads for uncached entries
            to_load = [p for p in keep if p not in self.pil_cache and p not in self.loading]
            self.loading.update(to_load)

        for path in to_load:
            threading.Thread(target=self._bg_load, args=(path,), daemon=True).start()

    def _get_pil(self, path):
        """Return the PIL image for path, loading synchronously if not cached."""
        with self.cache_lock:
            img = self.pil_cache.get(path)
        if img is None:
            # Synchronous fallback (only happens if bg load hasn't finished)
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            img.load()
            img = self._resize_for_screen(img)
            with self.cache_lock:
                self.pil_cache[path] = img
                self.loading.discard(path)
        return img

    # ---------------------------------------------------------------- display

    def _show_current(self):
        path = self.images[self.index]
        pil_img = self._get_pil(path)
        tk_img = ImageTk.PhotoImage(pil_img)

        self.canvas.delete('all')
        cx = self.screen_w // 2
        cy = (self.screen_h - 35) // 2
        self.canvas.create_image(cx, cy, image=tk_img, anchor='center')
        self._tk_img = tk_img  # must keep reference or GC will blank the image

        is_flagged = path in self.flagged
        flag_label = '  ★ KEEP' if is_flagged else ''
        action = 'MOVE' if self.move else 'COPY'
        status = (
            f'  {self.index + 1} / {len(self.images)}'
            f'   {path.name}{flag_label}'
            f'   |  Kept: {len(self.flagged)}'
            f'   |  [←/→] Navigate   [Space/F/K] Keep   [U] Undo   [Q] Done ({action})'
        )
        self.status.config(text=status, bg='#163016' if is_flagged else '#111')

    # --------------------------------------------------------------- actions

    def navigate(self, direction):
        new = self.index + direction
        if 0 <= new < len(self.images):
            self.index = new
            self._preload_around(self.index)
            self._show_current()

    def flag_and_advance(self):
        self.flagged.add(self.images[self.index])
        self._show_current()
        self.navigate(1)

    def unflag_current(self):
        self.flagged.discard(self.images[self.index])
        self._show_current()

    def quit(self):
        count = len(self.flagged)
        if count:
            self.selected_folder.mkdir(exist_ok=True)
            op = shutil.move if self.move else shutil.copy2
            verb = 'Moved' if self.move else 'Copied'
            for path in self.flagged:
                op(str(path), self.selected_folder / path.name)
            self.root.destroy()
            print(f"\n{verb} {count} image{'s' if count != 1 else ''} to: {self.selected_folder}")
        else:
            self.root.destroy()
            print("\nNo images flagged. Nothing saved.")


def main():
    folder = '.'
    output = None
    move = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--move':
            move = True
        elif args[i] in ('--output', '-o'):
            i += 1
            if i >= len(args):
                print("Error: --output requires a path argument")
                sys.exit(1)
            output = args[i]
        elif not args[i].startswith('-'):
            folder = args[i]
        else:
            print(f"Unknown option: {args[i]}")
            sys.exit(1)
        i += 1

    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a directory")
        sys.exit(1)

    root = tk.Tk()
    PhotoPicker(root, folder, output=output, move=move)
    root.mainloop()


if __name__ == '__main__':
    main()
