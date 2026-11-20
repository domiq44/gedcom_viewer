# -*- mode: python ; coding: utf-8 -*-

import os

# --- Boilerplate de PyInstaller (Doit être au début) ---
from PyInstaller.utils.hooks import collect_all

block_cipher = None

pypdfium_datas, pypdfium_binaries, pypdfium_hiddenimports = collect_all(
    'pypdfium2'
)
pdfium_raw_datas, pdfium_raw_binaries, pdfium_raw_hiddenimports = collect_all(
    'pypdfium2_raw'
)

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=pypdfium_binaries + pdfium_raw_binaries,
    datas=list(dict.fromkeys([
        # INCLUSION DES RÉPERTOIRES CLÉS :
        ('ui', 'ui'),
        ('controllers', 'controllers'),
        ('gedcom', 'gedcom'),
    ] + pypdfium_datas + pdfium_raw_datas)),
    hiddenimports=list(dict.fromkeys([
        # Gardez les imports de haut niveau, mais retirez l'importation interne qui cause le conflit
        'ui.main_window',
        'controllers.app_controller',
        'controllers.entity_controller',
        'controllers.search_controller',
        'gedcom.parser',
        'ui.views',
        'PIL._tkinter_finder',
    ] + pypdfium_hiddenimports + pdfium_raw_hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='gedcom_viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=os.environ.get('GEDCOM_VIEWER_UPX', '0') == '1',
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
