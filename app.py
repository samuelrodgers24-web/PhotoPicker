#!/usr/bin/env python3
"""
app.py — PhotoPicker toolkit dashboard.

A GUI launcher for the full toolkit. Each card represents one script.
photopicker.py is always launched as a detached process to preserve performance.

Usage:
    python app.py
"""

import sys
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

SCRIPT_DIR = Path(__file__).parent

# ─────────────────────────── palette ─────────────────────────────────────────
BG         = '#18181b'
CARD_BG    = '#27272a'
TEXT       = '#f4f4f5'
MUTED      = '#a1a1aa'
ACCENT     = '#3b82f6'    # blue  — main workflow cards
UTIL_CLR   = '#8b5cf6'    # purple — utility cards
SUCCESS    = '#22c55e'
ERROR_CLR  = '#ef4444'
BTN_BG     = '#3f3f46'
BTN_ACTIVE = '#52525b'

TUT_HL     = '#f59e0b'    # amber — tutorial highlight / arrows
TUT_BG     = '#1c1917'    # dark  — caption background
TUT_FG     = '#fef3c7'    # cream — caption text

# Near-white used as the transparency key for the tutorial spotlight overlay.
# Must not appear as a natural color in any widget within the overlay window.
_TKEY = '#FEFEFE'

FN = 'Segoe UI'

# ─────────────────────────── tool definitions ─────────────────────────────────
#
# inputs : list of (key, label, browse_mode)
#            browse_mode 'file'   → user picks any photo; the parent folder is used.
#                                   Shows actual image files in the dialog — useful for
#                                   confirming you're in the right folder.
#            browse_mode 'folder' → standard folder picker with Make New Folder button.
#                                   Use for output/destination paths.
# flags  : list of (key, cli_flag, label) — one Checkbutton per entry
# build  : callable(values_dict, active_flags_list) -> extra CLI arg list
# detach : True = launch as independent process, do not capture output
#
TOOLS = [
    {
        'id': 'organize',
        'title': '1 · Organize  ·  optional',
        'desc': 'Split a folder into raw/, jpeg/, and video/ subfolders.\nSkip if your photos are already separated.',
        'script': 'separate_raws.py',
        'color': ACCENT,
        'inputs': [('folder', 'Folder to organize', 'file')],
        'flags':  [('copy', '--copy', 'Copy instead of move (keeps originals)')],
        'build':  lambda v, fl: [v['folder']] + fl,
        'detach': False,
    },
    {
        'id': 'pick',
        'title': '2 · Pick Photos',
        'desc': 'Browse JPEGs and flag keepers.  ← →  navigate  ·  Space  flag  ·  Q  done',
        'script': 'photopicker.py',
        'color': ACCENT,
        'inputs': [
            ('folder', 'Photo folder', 'file'),
            ('output', 'Output folder  (optional — leave blank for folder/selected/)', 'folder'),
        ],
        'flags':  [('move', '--move', 'Move flagged photos instead of copying')],
        'build':  lambda v, fl: (
            [v['folder']]
            + (['--output', v['output']] if v['output'].strip() else [])
            + fl
        ),
        'detach': True,
    },
    {
        'id': 'get_raws',
        'title': '3 · Get RAWs',
        'desc': 'Copy RAW files (+ XMP sidecars) matching your selected previews.',
        'script': 'get_raws.py',
        'color': ACCENT,
        'inputs': [
            ('jpeg',   'JPEG picks folder', 'file'),
            ('raws',   'RAW source folder',   'file'),
            ('output', 'Output folder',                                   'folder'),
        ],
        'flags':  [],
        'build':  lambda v, fl: [v['jpeg'], v['raws'], v['output']],
        'detach': False,
    },
    {
        'id': 'verify',
        'title': '4 · Verify Copy',
        'desc': 'Confirm files copied to a drive without corruption (MD5 checksum).',
        'script': 'verify_copy.py',
        'color': ACCENT,
        'inputs': [
            ('source', 'Source folder', 'file'),
            ('dest',   'Destination folder', 'file'),
        ],
        'flags':  [],
        'build':  lambda v, fl: [v['source'], v['dest']],
        'detach': False,
    },
    {
        'id': 'rename',
        'title': 'Rename by Date',
        'desc': 'Rename files to YYYY-MM-DD_HHMMSS using their EXIF shoot date.',
        'script': 'rename_by_date.py',
        'color': UTIL_CLR,
        'inputs': [('folder', 'Folder to rename', 'file')],
        'flags':  [('dry_run', '--dry-run', 'Dry run — preview only, no changes')],
        'build':  lambda v, fl: [v['folder']] + fl,
        'detach': False,
    },
    {
        'id': 'diff',
        'title': 'Find Rejected',
        'desc': "Copy photos not in your picks — the set difference of two folders.",
        'script': 'diff_folders.py',
        'color': UTIL_CLR,
        'inputs': [
            ('full',   'Full folder',  'file'),
            ('picks',  'Picks folder', 'file'),
            ('output', 'Output folder',                              'folder'),
        ],
        'flags':  [],
        'build':  lambda v, fl: [v['full'], v['picks'], v['output']],
        'detach': False,
    },
]

# ─────────────────────────── tutorial steps ───────────────────────────────────
TUTORIAL_STEPS = [
    {
        'card': None,
        'title': 'Welcome to PhotoPicker!',
        'text': (
            'This toolkit helps you sort and prepare\n'
            'photos for professional editing —\n'
            'no paid software needed.\n\n'
            'Cards 1–4 are the main workflow.\n'
            'The two purple cards are optional.'
        ),
    },
    {
        'card': 'organize',
        'title': '1 · Organize  (optional)',
        'text': (
            'If your photos are in one mixed folder,\n'
            'this sorts them into subfolders:\n\n'
            '  raw/   ·  RAW files for editing\n'
            '  jpeg/  ·  Preview images for picking\n'
            '  video/ ·  Video clips\n\n'
            'Skip this step if they are already\n'
            'separated.'
        ),
    },
    {
        'card': 'pick',
        'title': '2 · Pick your keepers',
        'text': (
            'Browse JPEGs at full speed and\n'
            'flag the ones you want to keep.\n\n'
            '  ← →   navigate photos\n'
            '  Space  flag as keep and advance\n'
            '  U      unflag current photo\n'
            '  Q      quit and save picks'
        ),
    },
    {
        'card': 'get_raws',
        'title': '3 · Collect the RAW files',
        'text': (
            'After picking your JPEGs, use this\n'
            'to grab the matching RAW files\n'
            'ready for editing software.\n\n'
            'XMP sidecar files are included\n'
            'automatically if they exist.'
        ),
    },
    {
        'card': 'verify',
        'title': '4 · Verify before deleting',
        'text': (
            'After copying RAW files to your\n'
            'drive, run this to confirm nothing\n'
            'was corrupted in transit.\n\n'
            'Only delete originals after\n'
            'this passes!'
        ),
    },
    {
        'card': 'rename',
        'title': 'Optional · Rename by date',
        'text': (
            'Renames files from camera names\n'
            'like IMG_1234 to readable dates\n'
            'like 2024-07-15_143022.\n\n'
            'Tick "Dry run" to preview first\n'
            'without renaming anything.'
        ),
    },
    {
        'card': 'diff',
        'title': 'Optional · Find rejected photos',
        'text': (
            'Creates a folder of everything\n'
            "you didn't pick — handy for a\n"
            'second look at the rejects\n'
            'before deleting them.'
        ),
    },
    {
        'card': None,
        'title': "You're all set!",
        'text': (
            'Standard workflow:\n\n'
            '  1 · Organize\n'
            '  2 · Pick Photos\n'
            '  3 · Get RAWs\n'
            '  4 · Verify Copy\n\n'
            'Click  ?  any time to replay\n'
            'this tutorial.'
        ),
    },
]


# ─────────────────────────── FolderInput ─────────────────────────────────────


class FolderInput(tk.Frame):
    """Label + text entry + Browse button for selecting a folder.

    browse_mode='file'   — Opens a file picker showing photos; the parent
                           folder of the selected file is used as the value.
                           Lets users see their photos to confirm the folder.
    browse_mode='folder' — Opens a folder picker (Make New Folder available).
                           Use for output/destination paths.
    """

    def __init__(self, parent, label, browse_mode='folder', **kw):
        super().__init__(parent, bg=CARD_BG, **kw)
        self._mode = browse_mode

        tk.Label(self, text=label, bg=CARD_BG, fg=MUTED,
                 font=(FN, 8), anchor='w').pack(anchor='w')

        row = tk.Frame(self, bg=CARD_BG)
        row.pack(fill='x')

        self._var = tk.StringVar()
        tk.Entry(row, textvariable=self._var, bg='#3f3f46', fg=TEXT,
                 insertbackground=TEXT, relief='flat',
                 font=(FN, 9), bd=5).pack(side='left', fill='x', expand=True)

        tk.Button(
            row, text='Browse', bg=BTN_BG, fg=TEXT, relief='flat',
            activebackground=BTN_ACTIVE, activeforeground=TEXT,
            font=(FN, 8), cursor='hand2', bd=0, padx=8,
            command=self._browse,
        ).pack(side='left', padx=(4, 0))

    def _browse(self):
        path = filedialog.askdirectory(title='Select folder')
        if path:
            self._var.set(path)

    def get(self):
        return self._var.get().strip()


# ─────────────────────────── ToolCard ────────────────────────────────────────

class ToolCard(tk.Frame):
    """Dashboard card for one toolkit script."""

    def __init__(self, parent, cfg, **kw):
        super().__init__(parent, bg=CARD_BG, **kw)
        self._cfg = cfg

        # Coloured top accent strip
        tk.Frame(self, bg=cfg['color'], height=3).pack(fill='x')

        body = tk.Frame(self, bg=CARD_BG)
        body.pack(fill='both', expand=True, padx=12, pady=(8, 10))

        # Pack the log and run button with side='bottom' first so they are
        # always anchored at the card bottom regardless of card height.
        self._log = tk.Text(
            body, height=5, bg='#18181b', fg='#71717a',
            font=('Consolas', 8), relief='flat', state='disabled',
            wrap='word', bd=6, cursor='arrow',
        )
        self._log.pack(side='bottom', fill='x', pady=(4, 0))

        bottom = tk.Frame(body, bg=CARD_BG)
        bottom.pack(side='bottom', fill='x', pady=(10, 4))

        self._run_btn = tk.Button(
            bottom, text='Run', bg=cfg['color'], fg='white', relief='flat',
            font=(FN, 9, 'bold'), cursor='hand2', bd=0, padx=18, pady=5,
            activebackground=cfg['color'], activeforeground='white',
            command=self._run,
        )
        self._run_btn.pack(side='left')

        self._status_var = tk.StringVar()
        self._status_lbl = tk.Label(
            bottom, textvariable=self._status_var,
            bg=CARD_BG, fg=MUTED, font=(FN, 8), anchor='w',
        )
        self._status_lbl.pack(side='left', padx=(10, 0))

        # Title, description, inputs, and flags fill from the top.
        tk.Label(body, text=cfg['title'], bg=CARD_BG, fg=TEXT,
                 font=(FN, 10, 'bold'), anchor='w').pack(anchor='w')
        tk.Label(body, text=cfg['desc'], bg=CARD_BG, fg=MUTED,
                 font=(FN, 8), anchor='w', justify='left').pack(anchor='w', pady=(2, 8))

        # Folder inputs
        self._inputs = {}
        for entry in cfg['inputs']:
            key, label = entry[0], entry[1]
            mode = entry[2] if len(entry) > 2 else 'folder'
            fi = FolderInput(body, label, browse_mode=mode)
            fi.pack(fill='x', pady=2)
            self._inputs[key] = fi

        # Flag checkboxes
        self._flag_vars = {}
        for key, flag, label in cfg.get('flags', []):
            var = tk.BooleanVar()
            tk.Checkbutton(
                body, text=label, variable=var,
                bg=CARD_BG, fg=MUTED, selectcolor=BTN_BG,
                activebackground=CARD_BG, activeforeground=TEXT,
                font=(FN, 8), cursor='hand2',
            ).pack(anchor='w', pady=(4, 0))
            self._flag_vars[key] = (var, flag)

    # ── run ───────────────────────────────────────────────────────────────────

    def _run(self):
        vals  = {key: fi.get() for key, fi in self._inputs.items()}
        flags = [flag for _, (var, flag) in self._flag_vars.items() if var.get()]

        # Validate: all inputs must be non-empty unless marked optional
        input_labels = {e[0]: e[1] for e in self._cfg['inputs']}
        for key, fi in self._inputs.items():
            if not fi.get() and 'optional' not in input_labels[key].lower():
                self._set_status('Fill in all required folders first.', ERROR_CLR)
                return

        args = self._cfg['build'](vals, flags)
        # -u forces unbuffered stdout so output streams in real time
        cmd  = [sys.executable, '-u', str(SCRIPT_DIR / self._cfg['script'])] + args

        if self._cfg.get('detach'):
            subprocess.Popen(cmd)
            self._set_status('Launched.', SUCCESS)
        else:
            self._run_btn.config(state='disabled', text='Running…')
            self._set_status('', MUTED)
            self._clear_log()
            threading.Thread(target=self._run_thread, args=(cmd,), daemon=True).start()

    def _run_thread(self, cmd):
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
            )
            for line in proc.stdout:
                self._append_log(line)
            proc.wait()
            ok  = proc.returncode == 0
            self._set_status('Done.' if ok else f'Error (exit {proc.returncode}).',
                             SUCCESS if ok else ERROR_CLR)
        except Exception as exc:
            self._set_status(str(exc), ERROR_CLR)
        finally:
            self._run_btn.after(0, lambda: self._run_btn.config(state='normal', text='Run'))

    # ── helpers ───────────────────────────────────────────────────────────────

    def _append_log(self, line):
        def _do():
            self._log.config(state='normal')
            self._log.insert('end', line)
            self._log.see('end')
            self._log.config(state='disabled')
        self._log.after(0, _do)

    def _clear_log(self):
        self._log.config(state='normal')
        self._log.delete('1.0', 'end')
        self._log.config(state='disabled')

    def _set_status(self, msg, color=MUTED):
        def _do():
            self._status_var.set(msg)
            self._status_lbl.config(fg=color)
        self._status_lbl.after(0, _do)


# ─────────────────────────── TutorialOverlay ─────────────────────────────────

class TutorialOverlay:
    """
    Game-style tutorial overlay.

    Two layered Toplevel windows sit above the dashboard:
      - _dim_win  : semi-transparent black window covering the whole screen (the fog)
      - _hl_win   : transparent window (color-keyed) used for the highlight border,
                    the arrow, and the caption box

    The highlighted card shows through _hl_win because its area is left as the
    transparent key color. Everything else is dimmed by _dim_win underneath.
    """

    _CAPTION_W   = 270   # caption box width in pixels
    _CARD_PAD    = 6     # extra padding around highlighted card
    _ARROW_PAD   = 20    # gap between caption edge and arrow start

    def __init__(self, root, dashboard, on_close):
        self.root      = root
        self.dashboard = dashboard
        self.on_close  = on_close
        self.step      = 0
        self._debounce = None

        # ── dim window ────────────────────────────────────────────────────────
        self._dim_win = tk.Toplevel(root)
        self._dim_win.overrideredirect(True)
        self._dim_win.attributes('-topmost', True)
        self._dim_win.attributes('-alpha', 0.55)
        self._dim_win.configure(bg='black')
        self._dim_win.bind('<Button-1>', lambda e: None)   # block clicks on fog

        # ── highlight + caption window ────────────────────────────────────────
        self._hl_win = tk.Toplevel(root)
        self._hl_win.overrideredirect(True)
        self._hl_win.attributes('-topmost', True)
        self._hl_win.configure(bg=_TKEY)
        try:
            self._hl_win.attributes('-transparentcolor', _TKEY)
        except tk.TclError:
            pass  # graceful degradation on non-Windows platforms

        self._canvas = tk.Canvas(self._hl_win, bg=_TKEY, highlightthickness=0)
        self._canvas.pack(fill='both', expand=True)

        # ── caption frame (embedded in canvas via create_window) ──────────────
        cap_outer = tk.Frame(self._canvas, bg=TUT_HL, padx=2, pady=2)  # amber border
        cap_inner = tk.Frame(cap_outer,   bg=TUT_BG, padx=14, pady=10)
        cap_inner.pack(fill='both', expand=True)

        self._cap_title = tk.Label(cap_inner, bg=TUT_BG, fg=TUT_HL,
                                    font=(FN, 11, 'bold'), justify='left', anchor='w')
        self._cap_title.pack(anchor='w')

        self._cap_text = tk.Label(cap_inner, bg=TUT_BG, fg=TUT_FG,
                                   font=(FN, 9), justify='left', anchor='w',
                                   wraplength=self._CAPTION_W - 32)
        self._cap_text.pack(anchor='w', pady=(6, 12))

        nav = tk.Frame(cap_inner, bg=TUT_BG)
        nav.pack(fill='x')

        self._prev_btn = tk.Button(
            nav, text='← Prev', bg=BTN_BG, fg=TEXT, relief='flat',
            font=(FN, 8), cursor='hand2', bd=0, padx=8, pady=3,
            activebackground=BTN_ACTIVE, activeforeground=TEXT,
            command=self._prev,
        )
        self._prev_btn.pack(side='left')

        self._next_btn = tk.Button(
            nav, text='Next →', bg=TUT_HL, fg='#1c1917', relief='flat',
            font=(FN, 8, 'bold'), cursor='hand2', bd=0, padx=10, pady=3,
            activebackground='#d97706', activeforeground='#1c1917',
            command=self._next,
        )
        self._next_btn.pack(side='left', padx=(6, 0))

        tk.Button(
            nav, text='Skip', bg=TUT_BG, fg=MUTED, relief='flat',
            font=(FN, 8), cursor='hand2', bd=0, padx=8, pady=3,
            activebackground=TUT_BG, activeforeground=TEXT,
            command=self._close,
        ).pack(side='right')

        self._cap_win = self._canvas.create_window(0, 0, window=cap_outer, anchor='nw')

        # Track parent window moves/resizes (debounced to avoid lag during drag)
        self._cfg_bind = root.bind('<Configure>', self._on_configure, add='+')

        self._update_geometry()
        self._draw()

        # grab_set() routes all tkinter events to _hl_win, ensuring the caption
        # buttons receive clicks even if _dim_win would otherwise intercept them.
        self._hl_win.focus_force()
        self._hl_win.grab_set()

    # ── geometry ──────────────────────────────────────────────────────────────

    def _window_rect(self):
        """Return (x, y, w, h) of the root window in screen coordinates."""
        self.root.update_idletasks()
        return (self.root.winfo_rootx(), self.root.winfo_rooty(),
                self.root.winfo_width(),  self.root.winfo_height())

    def _update_geometry(self):
        x, y, w, h = self._window_rect()
        geo = f'{w}x{h}+{x}+{y}'
        self._dim_win.geometry(geo)
        self._hl_win.geometry(geo)

    def _on_configure(self, event):
        if event.widget is not self.root:
            return
        if self._debounce:
            self.root.after_cancel(self._debounce)
        self._debounce = self.root.after(50, self._reposition)

    def _reposition(self):
        self._update_geometry()
        self._draw()

    # ── drawing ───────────────────────────────────────────────────────────────

    def _draw(self):
        c = self._canvas
        c.delete('hl')

        _, _, W, H = self._window_rect()
        if W <= 1 or H <= 1:
            c.after(60, self._draw)
            return

        step    = TUTORIAL_STEPS[self.step]
        card_id = step.get('card')
        card    = self.dashboard.cards.get(card_id) if card_id else None
        is_last = self.step == len(TUTORIAL_STEPS) - 1

        self._cap_title.config(text=step['title'])
        self._cap_text.config(text=step['text'])
        self._prev_btn.config(state='normal' if self.step > 0 else 'disabled')
        self._next_btn.config(
            text='Done ✓' if is_last else 'Next →',
            bg=SUCCESS if is_last else TUT_HL,
            activebackground='#16a34a' if is_last else '#d97706',
        )

        CW  = self._CAPTION_W
        PAD = self._ARROW_PAD

        if card:
            # Card bounding box in overlay-window coordinates
            ox = self._hl_win.winfo_rootx()
            oy = self._hl_win.winfo_rooty()
            m  = self._CARD_PAD
            cx1 = card.winfo_rootx() - ox - m
            cy1 = card.winfo_rooty() - oy - m
            cx2 = cx1 + card.winfo_width()  + 2 * m
            cy2 = cy1 + card.winfo_height() + 2 * m

            # Bright highlight border (drawn over the transparent key — visible)
            c.create_rectangle(cx1, cy1, cx2, cy2,
                               outline=TUT_HL, width=3, tags='hl')

            # The card area itself remains _TKEY so it shows through the overlay.
            # Draw _TKEY fill inside the border to keep it transparent.
            c.create_rectangle(cx1 + 3, cy1 + 3, cx2 - 3, cy2 - 3,
                               fill=_TKEY, outline='', tags='hl')

            # Caption placement: opposite horizontal side from the card centre
            card_cx = (cx1 + cx2) / 2
            if card_cx <= W / 2:
                cap_x = cx2 + PAD
                cap_y = max(8, min(cy1, H - 260))
                a_src = (cap_x,      cap_y + 80)
                a_dst = (cx2,        (cy1 + cy2) / 2)
            else:
                cap_x = cx1 - CW - PAD
                cap_y = max(8, min(cy1, H - 260))
                a_src = (cap_x + CW, cap_y + 80)
                a_dst = (cx1,        (cy1 + cy2) / 2)

            # Arrow from caption to card
            c.create_line(
                *a_src, *a_dst,
                fill=TUT_HL, width=2,
                arrow='last', arrowshape=(12, 14, 5),
                tags='hl',
            )
        else:
            # No card highlighted — caption centred over full-dim screen
            cap_x = (W - CW) // 2
            cap_y = (H - 250) // 2

        cap_x = max(8, min(cap_x, W - CW - 8))
        cap_y = max(8, cap_y)

        c.coords(self._cap_win, cap_x, cap_y)
        c.itemconfig(self._cap_win, width=CW)
        c.tag_raise(self._cap_win)

    # ── navigation ────────────────────────────────────────────────────────────

    def _next(self):
        if self.step < len(TUTORIAL_STEPS) - 1:
            self.step += 1
            self._draw()
        else:
            self._close()

    def _prev(self):
        if self.step > 0:
            self.step -= 1
            self._draw()

    def _close(self):
        self._hl_win.grab_release()
        self.root.unbind('<Configure>', self._cfg_bind)
        self._dim_win.destroy()
        self._hl_win.destroy()
        self.on_close()


# ─────────────────────────── Dashboard ───────────────────────────────────────

class Dashboard:
    def __init__(self, root):
        self.root      = root
        self._tutorial = None
        self.cards     = {}

        root.title('PhotoPicker')
        root.configure(bg=BG)
        root.minsize(780, 660)

        self._build_header()
        self._build_grid()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill='x', padx=20, pady=(16, 8))

        tk.Label(hdr, text='PhotoPicker', bg=BG, fg=TEXT,
                 font=(FN, 16, 'bold')).pack(side='left')
        tk.Label(hdr, text='Photo preparation toolkit', bg=BG, fg=MUTED,
                 font=(FN, 9)).pack(side='left', padx=(10, 0), pady=(5, 0))

        tk.Button(
            hdr, text='?  Tutorial', bg=BTN_BG, fg=TEXT, relief='flat',
            font=(FN, 9), cursor='hand2', bd=0, padx=12, pady=5,
            activebackground=BTN_ACTIVE, activeforeground=TEXT,
            command=self._start_tutorial,
        ).pack(side='right')

    def _build_grid(self):
        grid = tk.Frame(self.root, bg=BG)
        grid.pack(fill='both', expand=True, padx=14, pady=(0, 14))
        grid.columnconfigure(0, weight=1, uniform='col')
        grid.columnconfigure(1, weight=1, uniform='col')

        for i, cfg in enumerate(TOOLS):
            row, col = divmod(i, 2)
            card = ToolCard(grid, cfg)
            card.grid(row=row, column=col, padx=6, pady=6, sticky='nsew')
            grid.rowconfigure(row, weight=1)
            self.cards[cfg['id']] = card

    def _start_tutorial(self):
        if self._tutorial is None:
            self._tutorial = TutorialOverlay(self.root, self, self._end_tutorial)

    def _end_tutorial(self):
        self._tutorial = None


# ─────────────────────────── entry point ─────────────────────────────────────

def main():
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()


if __name__ == '__main__':
    main()
