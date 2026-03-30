#!/usr/bin/env python3
"""
app.py — PhotoPicker toolkit dashboard.

Landing page shows nav buttons for every tool. Clicking one opens that tool's
page. photopicker.py is always launched as a detached process.

Usage:
    python app.py
"""

import sys

# ── Frozen-exe dispatch ───────────────────────────────────────────────────────
# When bundled by PyInstaller, sys.executable is the .exe itself (not python).
# Sub-scripts are imported as modules and their main() is called directly.
# The GUI launches them via:  [sys.executable, '--run-script', 'script_name', ...args]
_SCRIPTS = {
    'separate_raws': 'separate_raws',
    'get_raws':      'get_raws',
    'diff_folders':  'diff_folders',
    'verify_copy':   'verify_copy',
    'rename_by_date':'rename_by_date',
    'move_files':    'move_files',
    'delete_files':  'delete_files',
    'photopicker':   'photopicker',
}

if len(sys.argv) >= 3 and sys.argv[1] == '--run-script':
    _name = sys.argv[2]
    sys.argv = [sys.argv[0]] + sys.argv[3:]
    _mod = __import__(_SCRIPTS[_name])
    _mod.main()
    sys.exit(0)
# ─────────────────────────────────────────────────────────────────────────────

import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

if getattr(sys, 'frozen', False):
    # Running inside a PyInstaller bundle — scripts live in the extracted temp dir
    SCRIPT_DIR = Path(sys._MEIPASS)
else:
    SCRIPT_DIR = Path(__file__).parent

# ─────────────────────────── palette ─────────────────────────────────────────
BG         = '#18181b'
CARD_BG    = '#27272a'
HOVER_BG   = '#2f2f32'
TEXT       = '#f4f4f5'
MUTED      = '#a1a1aa'
ACCENT     = '#3b82f6'
UTIL_CLR   = '#8b5cf6'
DANGER_CLR = '#ef4444'
SUCCESS    = '#22c55e'
ERROR_CLR  = '#ef4444'
BTN_BG     = '#3f3f46'
BTN_ACTIVE = '#52525b'
DIVIDER    = '#3f3f46'

TUT_HL  = '#f59e0b'
TUT_BG  = '#1c1917'
TUT_FG  = '#fef3c7'
_TKEY   = '#FEFEFE'

FN = 'Segoe UI'

# ─────────────────────────── tool definitions ─────────────────────────────────
#
# Each tool has:
#   id, title, subtitle (home button), desc (tool page), script, color, group,
#   inputs, flags, build, detach
#   danger  : True adds a red warning + confirmation checkbox before Run
#   tutorial: steps shown when ? is pressed on that tool's page
#             each step: {target: input_key/'run'/None, title, text}
#
TOOLS = [
    # ── Workflow ──────────────────────────────────────────────────────────────
    {
        'id': 'organize',
        'title': '1 · Organize',
        'subtitle': 'Sort a mixed folder into raw/, jpeg/, video/',
        'desc': (
            'Splits a folder into subfolders by file type. '
            'Run this first if your RAW and JPEG files are mixed together.\n'
            'Skip if they are already separated.'
        ),
        'script': 'separate_raws.py',
        'color': ACCENT,
        'group': 'workflow',
        'inputs': [('folder', 'Folder to organize')],
        'flags':  [('copy', '--copy', 'Copy instead of move  (keeps originals in place)')],
        'build':  lambda v, fl: [v['folder']] + fl,
        'detach': False,
        'tutorial': [
            {
                'target': None,
                'title': '1 · Organize  (optional)',
                'text': (
                    'Use this if your photos and RAW files\n'
                    'are all mixed in one folder together.\n\n'
                    'It will create:\n'
                    '  raw/   · RAW files\n'
                    '  jpeg/  · JPEG previews\n'
                    '  video/ · Video clips'
                ),
            },
            {
                'target': 'folder',
                'title': 'Select the folder',
                'text': (
                    'Click Browse and navigate to the folder\n'
                    'that contains your mixed files.'
                ),
            },
            {
                'target': 'run',
                'title': 'Run it',
                'text': (
                    'Click Run to sort the files.\n\n'
                    'Tick "Copy instead of move" if you want\n'
                    'to keep the originals where they are.'
                ),
            },
        ],
    },
    {
        'id': 'pick',
        'title': '2 · Pick Photos',
        'subtitle': 'Browse JPEGs and flag the ones to keep',
        'desc': (
            'Opens a fullscreen photo browser. '
            'Use arrow keys to navigate and Space to flag keepers. '
            'Flagged photos are copied to the output folder when you press Q.'
        ),
        'script': 'photopicker.py',
        'color': ACCENT,
        'group': 'workflow',
        'inputs': [
            ('folder', 'Photo folder'),
            ('output', 'Output folder  (optional — defaults to folder/selected/)'),
        ],
        'flags':  [('move', '--move', 'Move flagged photos instead of copying')],
        'build':  lambda v, fl: (
            [v['folder']]
            + (['--output', v['output']] if v['output'].strip() else [])
            + fl
        ),
        'detach': True,
        'tutorial': [
            {
                'target': None,
                'title': '2 · Pick Photos',
                'text': (
                    'Opens a fast fullscreen photo browser.\n\n'
                    '  ← →   navigate photos\n'
                    '  Space  flag as "keep" and advance\n'
                    '  U      unflag current photo\n'
                    '  Q      quit and save picks'
                ),
            },
            {
                'target': 'folder',
                'title': 'Photo folder',
                'text': (
                    'Select the folder containing the JPEG\n'
                    'previews you want to browse through.'
                ),
            },
            {
                'target': 'output',
                'title': 'Output folder  (optional)',
                'text': (
                    'Leave blank to save picks into a\n'
                    'selected/ subfolder automatically.\n\n'
                    'Or choose a specific folder here.'
                ),
            },
        ],
    },
    {
        'id': 'get_raws',
        'title': '3 · Get RAWs',
        'subtitle': 'Copy RAW files matching your selected JPEGs',
        'desc': (
            'For each JPEG in your picks folder, finds the file with the same '
            'base name in your RAW folder and copies it to the output folder. '
            'XMP sidecar files are included automatically.'
        ),
        'script': 'get_raws.py',
        'color': ACCENT,
        'group': 'workflow',
        'inputs': [
            ('jpeg',   'JPEG picks folder'),
            ('raws',   'RAW source folder'),
            ('output', 'Output folder'),
        ],
        'flags':  [],
        'build':  lambda v, fl: [v['jpeg'], v['raws'], v['output']],
        'detach': False,
        'tutorial': [
            {
                'target': None,
                'title': '3 · Get RAWs',
                'text': (
                    'Matches your picked JPEGs to their\n'
                    'corresponding RAW files by filename.\n\n'
                    'XMP sidecar files (editing presets)\n'
                    'are copied along automatically.'
                ),
            },
            {
                'target': 'jpeg',
                'title': 'JPEG picks folder',
                'text': 'The folder containing the JPEGs\nyou flagged in step 2.',
            },
            {
                'target': 'raws',
                'title': 'RAW source folder',
                'text': (
                    'The folder containing your RAW files\n'
                    '(.CR3, .NEF, .ARW, etc.).'
                ),
            },
            {
                'target': 'output',
                'title': 'Output folder',
                'text': (
                    'Where the matched RAW files will be\n'
                    'copied. Create a new folder here\n'
                    'to keep things organised.'
                ),
            },
        ],
    },
    {
        'id': 'verify',
        'title': '4 · Verify Copy',
        'subtitle': 'Confirm files copied without corruption',
        'desc': (
            'Computes an MD5 checksum for every file in the source folder and '
            'compares it against the matching file in the destination. '
            'Run this after copying to an external drive, before deleting originals.'
        ),
        'script': 'verify_copy.py',
        'color': ACCENT,
        'group': 'workflow',
        'inputs': [
            ('source', 'Source folder'),
            ('dest',   'Destination folder'),
        ],
        'flags':  [],
        'build':  lambda v, fl: [v['source'], v['dest']],
        'detach': False,
        'tutorial': [
            {
                'target': None,
                'title': '4 · Verify Copy',
                'text': (
                    'Checksums every file in the source\n'
                    'and compares it to the destination.\n\n'
                    'Only delete originals after\n'
                    'this passes!'
                ),
            },
            {
                'target': 'source',
                'title': 'Source folder',
                'text': 'The original folder you copied from.',
            },
            {
                'target': 'dest',
                'title': 'Destination folder',
                'text': 'The folder you copied to\n(e.g. on your external drive).',
            },
        ],
    },
    # ── Utilities ─────────────────────────────────────────────────────────────
    {
        'id': 'rename',
        'title': 'Rename by Date',
        'subtitle': 'Rename files using EXIF shoot date',
        'desc': (
            'Renames image files from camera names like IMG_1234 to '
            'readable dates like 2024-07-15_143022, using the EXIF '
            'DateTimeOriginal tag. Use Dry run to preview before committing.'
        ),
        'script': 'rename_by_date.py',
        'color': UTIL_CLR,
        'group': 'utility',
        'inputs': [('folder', 'Folder to rename')],
        'flags':  [('dry_run', '--dry-run', 'Dry run — preview only, no changes made')],
        'build':  lambda v, fl: [v['folder']] + fl,
        'detach': False,
        'tutorial': [
            {
                'target': None,
                'title': 'Rename by Date',
                'text': (
                    'Renames files like IMG_1234.CR3\n'
                    'to 2024-07-15_143022.CR3 using\n'
                    'the EXIF shoot date.\n\n'
                    'Always tick Dry run first to\n'
                    'preview without making changes.'
                ),
            },
            {
                'target': 'folder',
                'title': 'Select folder',
                'text': 'Choose the folder of files to rename.',
            },
        ],
    },
    {
        'id': 'diff',
        'title': 'Find Rejected',
        'subtitle': 'Copy photos that were not selected',
        'desc': (
            'Copies every file from the full folder whose filename does not '
            'appear in the picks folder. Useful for collecting rejected photos '
            'before deleting them, or for a second-pass review.'
        ),
        'script': 'diff_folders.py',
        'color': UTIL_CLR,
        'group': 'utility',
        'inputs': [
            ('full',   'Full folder  (all photos)'),
            ('picks',  'Picks folder  (selected)'),
            ('output', 'Output folder'),
        ],
        'flags':  [],
        'build':  lambda v, fl: [v['full'], v['picks'], v['output']],
        'detach': False,
        'tutorial': [
            {
                'target': None,
                'title': 'Find Rejected',
                'text': (
                    'Finds every file that is in the\n'
                    'full folder but NOT in your picks,\n'
                    'and copies them to a new folder.\n\n'
                    'Handy for a second look before\n'
                    'deleting the rejects.'
                ),
            },
            {
                'target': 'full',
                'title': 'Full folder',
                'text': 'The folder with all your photos\nbefore culling.',
            },
            {
                'target': 'picks',
                'title': 'Picks folder',
                'text': 'The folder containing only\nthe photos you selected.',
            },
        ],
    },
    {
        'id': 'move',
        'title': 'Move Files',
        'subtitle': 'Bulk move all files to another folder',
        'desc': (
            'Moves every file from a source folder into a destination folder. '
            'Subdirectories are not moved. Skips files that already exist '
            'at the destination.'
        ),
        'script': 'move_files.py',
        'color': UTIL_CLR,
        'group': 'utility',
        'inputs': [
            ('source', 'Source folder'),
            ('dest',   'Destination folder'),
        ],
        'flags':  [],
        'build':  lambda v, fl: [v['source'], v['dest']],
        'detach': False,
        'tutorial': [
            {
                'target': None,
                'title': 'Move Files',
                'text': (
                    'Moves all files from one folder\n'
                    'into another.\n\n'
                    'Useful for consolidating photos\n'
                    'or reorganising after culling.'
                ),
            },
            {
                'target': 'source',
                'title': 'Source folder',
                'text': 'The folder whose files you want to move.',
            },
            {
                'target': 'dest',
                'title': 'Destination folder',
                'text': (
                    'Where the files will be moved to.\n'
                    'Will be created if it does not exist.'
                ),
            },
        ],
    },
    {
        'id': 'delete',
        'title': 'Delete Files',
        'subtitle': 'Permanently remove all files in a folder',
        'desc': (
            'Deletes every file directly inside the selected folder. '
            'Subdirectories are left untouched. '
            'This action cannot be undone — verify your copy first.'
        ),
        'script': 'delete_files.py',
        'color': DANGER_CLR,
        'group': 'utility',
        'inputs': [('folder', 'Folder to delete files from')],
        'flags':  [],
        'build':  lambda v, fl: [v['folder']],
        'detach': False,
        'danger': True,
        'tutorial': [
            {
                'target': None,
                'title': 'Delete Files',
                'text': (
                    'Permanently deletes all files in\n'
                    'the selected folder.\n\n'
                    'Use this to clean up originals\n'
                    'AFTER verifying your copy.\n\n'
                    'This cannot be undone.'
                ),
            },
            {
                'target': 'folder',
                'title': 'Select folder',
                'text': (
                    'Choose the folder whose files\n'
                    'you want to permanently delete.'
                ),
            },
            {
                'target': 'run',
                'title': 'Confirm before running',
                'text': (
                    'Tick the confirmation checkbox\n'
                    'to unlock the Delete button.\n\n'
                    'Make sure you have verified your\n'
                    'copy before doing this!'
                ),
            },
        ],
    },
]

# ─────────────────────────── home page tutorial ───────────────────────────────
HOME_TUTORIAL = [
    {
        'target': None,
        'title': 'Welcome to PhotoPicker!',
        'text': (
            'This toolkit prepares photos for\n'
            'professional editing — no paid\n'
            'software needed.\n\n'
            'Click any tool to open it.\n'
            'The top four are the main workflow.'
        ),
    },
    {
        'target': 'organize',
        'title': '1 · Organize  (optional)',
        'text': (
            'If your RAW and JPEG files are mixed\n'
            'in one folder, start here to sort them\n'
            'into raw/, jpeg/, and video/.'
        ),
    },
    {
        'target': 'pick',
        'title': '2 · Pick Photos',
        'text': (
            'Browse your JPEGs at full speed\n'
            'and flag the ones you want to keep.'
        ),
    },
    {
        'target': 'get_raws',
        'title': '3 · Get RAWs',
        'text': (
            'After picking, use this to collect\n'
            'the matching RAW files ready for\n'
            'your editing software.'
        ),
    },
    {
        'target': 'verify',
        'title': '4 · Verify Copy',
        'text': (
            'After copying files to a drive,\n'
            'run this to confirm nothing was\n'
            'corrupted. Do this before deleting\n'
            'the originals!'
        ),
    },
    {
        'target': 'rename',
        'title': 'Utilities',
        'text': (
            'These tools handle optional steps:\n\n'
            '  Rename by Date  — tidy filenames\n'
            '  Find Rejected   — review rejects\n'
            '  Move Files      — bulk move\n'
            '  Delete Files    — clean up originals'
        ),
    },
    {
        'target': None,
        'title': "You're all set!",
        'text': (
            'Click any tool to get started.\n\n'
            'Each tool page has its own\n'
            '?  button for a more detailed\n'
            'walkthrough of that specific tool.'
        ),
    },
]


# ─────────────────────────── FolderInput ─────────────────────────────────────

class FolderInput(tk.Frame):
    """Label + text entry + Browse button for selecting a folder."""

    def __init__(self, parent, label, **kw):
        super().__init__(parent, bg=CARD_BG, **kw)

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


# ─────────────────────────── NavButton ───────────────────────────────────────

class NavButton(tk.Frame):
    """Clickable home-page card for one tool."""

    def __init__(self, parent, cfg, on_click, **kw):
        super().__init__(parent, bg=CARD_BG, cursor='hand2', **kw)
        self._cfg = cfg

        # Left colour strip
        strip = tk.Frame(self, bg=cfg['color'], width=4)
        strip.pack(side='left', fill='y')

        body = tk.Frame(self, bg=CARD_BG, padx=14, pady=10)
        body.pack(side='left', fill='both', expand=True)

        title_lbl = tk.Label(body, text=cfg['title'], bg=CARD_BG, fg=TEXT,
                              font=(FN, 10, 'bold'), anchor='w')
        title_lbl.pack(anchor='w')

        sub_lbl = tk.Label(body, text=cfg['subtitle'], bg=CARD_BG, fg=MUTED,
                            font=(FN, 8), anchor='w')
        sub_lbl.pack(anchor='w')

        arrow = tk.Label(self, text='›', bg=CARD_BG, fg=MUTED,
                         font=(FN, 16), padx=14)
        arrow.pack(side='right')

        # Widgets that change colour on hover (strip excluded intentionally)
        self._hover_targets = [self, body, title_lbl, sub_lbl, arrow]

        for w in self._hover_targets:
            w.bind('<Button-1>', lambda e, c=cfg: on_click(c))
            w.bind('<Enter>',    lambda e: self._set_hover(True))
            w.bind('<Leave>',    lambda e: self._set_hover(False))

    def _set_hover(self, on):
        bg = HOVER_BG if on else CARD_BG
        for w in self._hover_targets:
            w.config(bg=bg)


# ─────────────────────────── HomePage ────────────────────────────────────────

class HomePage(tk.Frame):
    """Landing page with a nav button for each tool."""

    def __init__(self, parent, tools, on_select, **kw):
        super().__init__(parent, bg=BG, **kw)
        self.buttons = {}  # id -> NavButton (for tutorial targeting)

        # Scrollable canvas so the list works on small screens
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor='nw')

        def _on_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind('<Configure>', _on_resize)

        inner.bind('<Configure>',
                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        # Mouse-wheel scroll
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), 'units'))

        # Build sections
        workflow = [t for t in tools if t['group'] == 'workflow']
        utility  = [t for t in tools if t['group'] == 'utility']

        self._build_section(inner, 'Workflow', workflow, on_select)
        tk.Frame(inner, bg=DIVIDER, height=1).pack(fill='x', padx=20, pady=(4, 0))
        self._build_section(inner, 'Utilities', utility, on_select)

    def _build_section(self, parent, label, tools, on_select):
        tk.Label(parent, text=label.upper(), bg=BG, fg=MUTED,
                 font=(FN, 8, 'bold'), anchor='w').pack(
                     fill='x', padx=20, pady=(16, 6))

        grid = tk.Frame(parent, bg=BG)
        grid.pack(fill='x', padx=14, pady=(0, 4))
        grid.columnconfigure(0, weight=1, uniform='nav')
        grid.columnconfigure(1, weight=1, uniform='nav')

        for i, cfg in enumerate(tools):
            row, col = divmod(i, 2)
            btn = NavButton(grid, cfg, on_select)
            btn.grid(row=row, column=col, padx=5, pady=4, sticky='ew')
            self.buttons[cfg['id']] = btn

    def get_tutorial(self):
        """Return (steps, targets) for TutorialOverlay."""
        targets = {tid: btn for tid, btn in self.buttons.items()}
        return HOME_TUTORIAL, targets


# ─────────────────────────── ToolPage ────────────────────────────────────────

class ToolPage(tk.Frame):
    """Full-page view for a single tool."""

    def __init__(self, parent, cfg, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._cfg = cfg
        self._inputs = {}
        self._flag_vars = {}

        # Top colour strip
        tk.Frame(self, bg=cfg['color'], height=3).pack(fill='x')

        # Content area
        content = tk.Frame(self, bg=BG)
        content.pack(fill='both', expand=True, padx=28, pady=20)

        # Description
        tk.Label(content, text=cfg['desc'], bg=BG, fg=MUTED,
                 font=(FN, 9), anchor='w', justify='left',
                 wraplength=540).pack(anchor='w', pady=(0, 18))

        # Folder inputs
        for entry in cfg['inputs']:
            key, label = entry[0], entry[1]
            fi = FolderInput(content, label)
            fi.pack(fill='x', pady=4)
            self._inputs[key] = fi

        # Flag checkboxes
        for key, flag, label in cfg.get('flags', []):
            var = tk.BooleanVar()
            tk.Checkbutton(
                content, text=label, variable=var,
                bg=BG, fg=MUTED, selectcolor=BTN_BG,
                activebackground=BG, activeforeground=TEXT,
                font=(FN, 9), cursor='hand2',
            ).pack(anchor='w', pady=(8, 0))
            self._flag_vars[key] = (var, flag)

        # Danger confirmation checkbox
        self._confirmed = None
        if cfg.get('danger'):
            tk.Frame(content, bg=DANGER_CLR, height=1).pack(fill='x', pady=(16, 8))
            tk.Label(content,
                     text='⚠  This will permanently delete files. This cannot be undone.',
                     bg=BG, fg=DANGER_CLR, font=(FN, 9), anchor='w').pack(anchor='w')
            self._confirmed = tk.BooleanVar()
            tk.Checkbutton(
                content, text='I understand — proceed with deletion',
                variable=self._confirmed,
                bg=BG, fg=TEXT, selectcolor=BTN_BG,
                activebackground=BG, activeforeground=TEXT,
                font=(FN, 9, 'bold'), cursor='hand2',
                command=self._update_run_btn,
            ).pack(anchor='w', pady=(4, 0))

        # Run row
        run_row = tk.Frame(content, bg=BG)
        run_row.pack(fill='x', pady=(20, 8))

        btn_color = DANGER_CLR if cfg.get('danger') else cfg['color']
        self._run_btn = tk.Button(
            run_row, text='Run', bg=btn_color, fg='white', relief='flat',
            font=(FN, 10, 'bold'), cursor='hand2', bd=0, padx=24, pady=7,
            activebackground=btn_color, activeforeground='white',
            command=self._run,
        )
        self._run_btn.pack(side='left')
        if cfg.get('danger'):
            self._run_btn.config(state='disabled', text='Delete')

        self._status_var = tk.StringVar()
        self._status_lbl = tk.Label(run_row, textvariable=self._status_var,
                                     bg=BG, fg=MUTED, font=(FN, 9), anchor='w')
        self._status_lbl.pack(side='left', padx=(14, 0))

        # Output log
        log_frame = tk.Frame(content, bg=CARD_BG)
        log_frame.pack(fill='both', expand=True, pady=(4, 0))

        self._log = tk.Text(
            log_frame, bg='#18181b', fg='#71717a',
            font=('Consolas', 8), relief='flat', state='disabled',
            wrap='word', bd=8, cursor='arrow',
        )
        sb = tk.Scrollbar(log_frame, command=self._log.yview)
        self._log.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self._log.pack(side='left', fill='both', expand=True)

    def get_tutorial(self):
        """Return (steps, targets) for TutorialOverlay."""
        targets = {key: fi for key, fi in self._inputs.items()}
        targets['run'] = self._run_btn
        return self._cfg['tutorial'], targets

    def _update_run_btn(self):
        if self._confirmed and self._confirmed.get():
            self._run_btn.config(state='normal')
        else:
            self._run_btn.config(state='disabled')

    # ── run ───────────────────────────────────────────────────────────────────

    def _run(self):
        vals  = {key: fi.get() for key, fi in self._inputs.items()}
        flags = [flag for _, (var, flag) in self._flag_vars.items() if var.get()]

        input_labels = {e[0]: e[1] for e in self._cfg['inputs']}
        for key, fi in self._inputs.items():
            if not fi.get() and 'optional' not in input_labels[key].lower():
                self._set_status('Fill in all required folders first.', ERROR_CLR)
                return

        args = self._cfg['build'](vals, flags)
        script_stem = Path(self._cfg['script']).stem
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable, '--run-script', script_stem] + args
        else:
            cmd = [sys.executable, '-u', str(SCRIPT_DIR / self._cfg['script'])] + args

        if self._cfg.get('detach'):
            subprocess.Popen(cmd)
            self._set_status('Launched.', SUCCESS)
        else:
            self._run_btn.config(state='disabled',
                                  text='Running…' if not self._cfg.get('danger') else 'Deleting…')
            self._set_status('', MUTED)
            self._clear_log()
            threading.Thread(target=self._run_thread, args=(cmd,), daemon=True).start()

    def _run_thread(self, cmd):
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
            )
            for line in proc.stdout:
                self._append_log(line)
            proc.wait()
            ok = proc.returncode == 0
            self._set_status('Done.' if ok else f'Error (exit {proc.returncode}).',
                             SUCCESS if ok else ERROR_CLR)
        except Exception as exc:
            self._set_status(str(exc), ERROR_CLR)
        finally:
            def _reset():
                if self._cfg.get('danger'):
                    # Re-lock after a delete — require re-confirmation
                    if self._confirmed:
                        self._confirmed.set(False)
                    self._run_btn.config(state='disabled', text='Delete')
                else:
                    self._run_btn.config(state='normal', text='Run')
            self._run_btn.after(0, _reset)

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
    Game-style tutorial. Works on any page by accepting explicit steps + targets.

    steps   : list of {target: key_or_None, title: str, text: str}
    targets : dict of {key: widget}  — used to locate the highlight bounding box
    """

    _CAPTION_W = 270
    _CARD_PAD  = 6
    _ARROW_PAD = 20

    def __init__(self, root, steps, targets, on_close):
        self.root      = root
        self._steps    = steps
        self._targets  = targets
        self.on_close  = on_close
        self.step      = 0
        self._debounce = None

        # Dim window
        self._dim_win = tk.Toplevel(root)
        self._dim_win.overrideredirect(True)
        self._dim_win.attributes('-topmost', True)
        self._dim_win.attributes('-alpha', 0.55)
        self._dim_win.configure(bg='black')
        self._dim_win.bind('<Button-1>', lambda e: None)

        # Highlight + caption window
        self._hl_win = tk.Toplevel(root)
        self._hl_win.overrideredirect(True)
        self._hl_win.attributes('-topmost', True)
        self._hl_win.configure(bg=_TKEY)
        try:
            self._hl_win.attributes('-transparentcolor', _TKEY)
        except tk.TclError:
            pass

        self._canvas = tk.Canvas(self._hl_win, bg=_TKEY, highlightthickness=0)
        self._canvas.pack(fill='both', expand=True)

        # Caption frame
        cap_outer = tk.Frame(self._canvas, bg=TUT_HL, padx=2, pady=2)
        cap_inner = tk.Frame(cap_outer, bg=TUT_BG, padx=14, pady=10)
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

        self._cfg_bind = root.bind('<Configure>', self._on_configure, add='+')
        self._update_geometry()
        self._draw()
        self._hl_win.focus_force()
        self._hl_win.grab_set()

    # ── geometry ──────────────────────────────────────────────────────────────

    def _window_rect(self):
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

        step      = self._steps[self.step]
        target_id = step.get('target')
        widget    = self._targets.get(target_id) if target_id else None
        is_last   = self.step == len(self._steps) - 1

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

        if widget:
            ox = self._hl_win.winfo_rootx()
            oy = self._hl_win.winfo_rooty()
            m  = self._CARD_PAD
            cx1 = widget.winfo_rootx() - ox - m
            cy1 = widget.winfo_rooty() - oy - m
            cx2 = cx1 + widget.winfo_width()  + 2 * m
            cy2 = cy1 + widget.winfo_height() + 2 * m

            c.create_rectangle(cx1, cy1, cx2, cy2,
                               outline=TUT_HL, width=3, tags='hl')
            c.create_rectangle(cx1 + 3, cy1 + 3, cx2 - 3, cy2 - 3,
                               fill=_TKEY, outline='', tags='hl')

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

            c.create_line(*a_src, *a_dst, fill=TUT_HL, width=2,
                          arrow='last', arrowshape=(12, 14, 5), tags='hl')
        else:
            cap_x = (W - CW) // 2
            cap_y = (H - 250) // 2

        cap_x = max(8, min(cap_x, W - CW - 8))
        cap_y = max(8, cap_y)

        c.coords(self._cap_win, cap_x, cap_y)
        c.itemconfig(self._cap_win, width=CW)
        c.tag_raise(self._cap_win)

    # ── navigation ────────────────────────────────────────────────────────────

    def _next(self):
        if self.step < len(self._steps) - 1:
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


# ─────────────────────────── App ─────────────────────────────────────────────

class App:
    """Root application — manages the persistent chrome and page navigation."""

    def __init__(self, root):
        self.root          = root
        self._current_page = None
        self._tutorial     = None

        root.title('PhotoPicker')
        root.configure(bg=BG)
        root.minsize(640, 480)

        self._build_chrome()
        self.show_home()

    # ── chrome ────────────────────────────────────────────────────────────────

    def _build_chrome(self):
        # Persistent header
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill='x', padx=20, pady=(14, 0))

        self._back_btn = tk.Button(
            hdr, text='← Back', bg=BTN_BG, fg=TEXT, relief='flat',
            font=(FN, 9), cursor='hand2', bd=0, padx=10, pady=4,
            activebackground=BTN_ACTIVE, activeforeground=TEXT,
            command=self.show_home,
        )
        # Packed/forgotten dynamically in show_home / show_tool

        self._title_lbl = tk.Label(hdr, text='PhotoPicker', bg=BG, fg=TEXT,
                                    font=(FN, 15, 'bold'))
        self._title_lbl.pack(side='left')

        self._sub_lbl = tk.Label(hdr, text='Photo preparation toolkit',
                                  bg=BG, fg=MUTED, font=(FN, 9))
        self._sub_lbl.pack(side='left', padx=(10, 0), pady=(4, 0))

        self._tut_btn = tk.Button(
            hdr, text='?  Tutorial', bg=BTN_BG, fg=TEXT, relief='flat',
            font=(FN, 9), cursor='hand2', bd=0, padx=12, pady=4,
            activebackground=BTN_ACTIVE, activeforeground=TEXT,
            command=self._start_tutorial,
        )
        self._tut_btn.pack(side='right')

        # Thin divider under header
        tk.Frame(self.root, bg=DIVIDER, height=1).pack(fill='x', pady=(10, 0))

        # Page container — current page is packed/destroyed here
        self._page_area = tk.Frame(self.root, bg=BG)
        self._page_area.pack(fill='both', expand=True)

    # ── navigation ────────────────────────────────────────────────────────────

    def show_home(self):
        self._close_tutorial()
        self._swap_page(HomePage(self._page_area, TOOLS, on_select=self.show_tool))
        self._back_btn.pack_forget()
        self._title_lbl.config(text='PhotoPicker')
        self._sub_lbl.config(text='Photo preparation toolkit')
        self.root.title('PhotoPicker')

    def show_tool(self, cfg):
        self._close_tutorial()
        self._swap_page(ToolPage(self._page_area, cfg))
        self._back_btn.pack(side='left', before=self._title_lbl, padx=(0, 10))
        self._title_lbl.config(text=cfg['title'])
        self._sub_lbl.config(text=cfg['subtitle'])
        self.root.title(f"PhotoPicker — {cfg['title']}")

    def _swap_page(self, new_page):
        if self._current_page:
            self._current_page.destroy()
        new_page.pack(fill='both', expand=True)
        self._current_page = new_page

    # ── tutorial ──────────────────────────────────────────────────────────────

    def _start_tutorial(self):
        if self._tutorial is not None or self._current_page is None:
            return
        steps, targets = self._current_page.get_tutorial()
        self._tutorial = TutorialOverlay(self.root, steps, targets, self._end_tutorial)

    def _end_tutorial(self):
        self._tutorial = None

    def _close_tutorial(self):
        if self._tutorial:
            self._tutorial._close()


# ─────────────────────────── entry point ─────────────────────────────────────

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
