# -*- mode: python ; coding: utf-8 -*-

# --- Boilerplate de PyInstaller (Doit être au début) ---
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # INCLUSION DES RÉPERTOIRES CLÉS :
        ('ui', 'ui'),
        ('controllers', 'controllers'),
        ('gedcom', 'gedcom'),
        ('gedcom/models', 'gedcom/models'),
        ('tests', 'tests'),
    ],
    hiddenimports=[
        # Gardez les imports de haut niveau, mais retirez l'importation interne qui cause le conflit
        'ui.main_window',
        'controllers.app_controller',
        'controllers.entity_controller',
        'controllers.search_controller',
        'gedcom.parser',
    ],
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
