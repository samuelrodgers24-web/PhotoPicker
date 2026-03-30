# PhotoPicker.spec
#
# Build a standalone Windows executable with:
#
#   pyinstaller PhotoPicker.spec
#
# Output lands in dist/PhotoPicker/PhotoPicker.exe
# The whole dist/PhotoPicker/ folder can be zipped and shared.
# No Python installation required on the recipient's machine.
#
# One-dir mode is used instead of one-file because:
#   - Tkinter apps start noticeably faster (no temp-extraction step)
#   - Antivirus software is less likely to flag it

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['scripts/app.py'],
    pathex=['scripts'],
    binaries=[],
    datas=[],
    # All sub-scripts are imported dynamically via __import__() in the dispatch
    # block, so PyInstaller's static analyser won't find them automatically.
    hiddenimports=[
        'separate_raws',
        'get_raws',
        'diff_folders',
        'verify_copy',
        'rename_by_date',
        'move_files',
        'delete_files',
        'photopicker',
        'PIL',
        'PIL.Image',
        'PIL.ImageOps',
        'PIL.ImageTk',
        'exifread',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PhotoPicker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,      # No terminal window — pure GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',  # Uncomment and add an icon.ico to use a custom icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PhotoPicker',
)
