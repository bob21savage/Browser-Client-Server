# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Get the absolute path to the project directory
project_dir = os.path.abspath(os.path.dirname('app.py'))

# Define data files to include
datas = []

# Add public directory and its contents
public_dir = os.path.join(project_dir, 'public')
if os.path.exists(public_dir):
    for root, dirs, files in os.walk(public_dir):
        for file in files:
            source_path = os.path.join(root, file)
            dest_path = os.path.relpath(os.path.join(root, file), project_dir)
            dest_dir = os.path.dirname(dest_path)
            datas.append((source_path, dest_dir))

# Add scrape directory and its contents
scrape_dir = os.path.join(project_dir, 'scrape')
if os.path.exists(scrape_dir):
    for root, dirs, files in os.walk(scrape_dir):
        for file in files:
            if file.endswith('.py'):  # Only include Python files
                source_path = os.path.join(root, file)
                dest_path = os.path.relpath(os.path.join(root, file), project_dir)
                dest_dir = os.path.dirname(dest_path)
                datas.append((source_path, dest_dir))

# Add templates directory if it exists
templates_dir = os.path.join(project_dir, 'templates')
if os.path.exists(templates_dir):
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            source_path = os.path.join(root, file)
            dest_path = os.path.relpath(os.path.join(root, file), project_dir)
            dest_dir = os.path.dirname(dest_path)
            datas.append((source_path, dest_dir))

# Add node_modules directory if it exists
node_modules_dir = os.path.join(project_dir, 'node_modules')
if os.path.exists(node_modules_dir):
    for root, dirs, files in os.walk(node_modules_dir):
        for file in files:
            source_path = os.path.join(root, file)
            dest_path = os.path.relpath(os.path.join(root, file), project_dir)
            dest_dir = os.path.dirname(dest_path)
            datas.append((source_path, dest_dir))

a = Analysis(
    ['app.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'engineio.async_drivers.threading',
        'flask_socketio',
        'eventlet',
        'bs4',
        'aiohttp',
        'html2text',
        'flask_cors',
        'scrape_upgrade',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='video-scraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
