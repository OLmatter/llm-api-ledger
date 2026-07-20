# PyInstaller spec for llm-api-ledger probe.
# Build: pyinstaller src/probe/probe.spec  (run from repo root)
# Output: dist/ledger-probe (Linux/macOS) or dist/ledger-probe.exe (Windows)

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/probe/probe.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # keyring backends — bundled so users don't need to install anything
        'keyring.backends.SecretService',
        'keyring.backends.Windows',
        'keyring.backends.macOS',
        # uvicorn bits that PyInstaller misses
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # httpx extras
        'httpx._client',
        'h11',
        'anyio._backends._asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim unused modules to keep binary small
        'tkinter',
        'unittest',
        'pydoc',
        'doctest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ledger-probe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # Console window MUST stay visible (this is a server process)
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='docs/icon.ico',  # uncomment once an icon is added
)
