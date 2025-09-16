#!/usr/bin/env python3
"""
Build script for creating Windows executable from the WhatsApp Voice Processor GUI.

This script creates a PyInstaller spec file and builds the executable.
Run this on a Windows machine with Python and all dependencies installed.

Requirements:
- Python 3.8+
- All packages from requirements.txt
- PyInstaller

Usage:
    python build_exe.py
"""

import os
import subprocess
import sys

def create_spec_file():
    """Create PyInstaller spec file for Windows build"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pydub',
        'librosa',
        'soundfile',
        'numpy',
        'whisper',
        'speech_recognition',
        'sklearn',
        'scipy',
        'numba',
        'llvmlite',
        'joblib',
        'threadpoolctl',
        'lazy_loader',
        'pooch',
        'soxr',
        'audioread',
        'decorator',
        'msgpack',
        'platformdirs',
        'torch',
        'torchaudio',
        'transformers',
        'tokenizers',
        'regex',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'packaging',
        'filelock',
        'typing_extensions',
        'sympy',
        'networkx',
        'jinja2',
        'markupsafe',
        'fsspec',
        'huggingface_hub',
        'safetensors',
        'pyyaml',
        'tqdm',
        'more_itertools'
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
    name='WhatsAppVoiceProcessor',
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
    icon=None,
)
'''
    
    with open('whatsapp_voice_processor_windows.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created PyInstaller spec file: whatsapp_voice_processor_windows.spec")

def install_dependencies():
    """Install required dependencies"""
    print("Installing PyInstaller...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    print("Installing project dependencies...")
    if os.path.exists('requirements.txt'):
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    else:
        print("Warning: requirements.txt not found. Make sure all dependencies are installed.")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")
    try:
        subprocess.run(['pyinstaller', 'whatsapp_voice_processor_windows.spec'], check=True)
        print("Build completed successfully!")
        print("Executable can be found in the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        return False
    return True

def main():
    """Main build process"""
    print("WhatsApp Voice Processor - Windows Executable Builder")
    print("=" * 50)
    
    # Check if we're on Windows
    if os.name != 'nt':
        print("Warning: This script is designed for Windows. You may encounter issues on other platforms.")
    
    # Check required files
    required_files = ['gui_app.py', 'audio_processor.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"Error: Missing required files: {missing_files}")
        return
    
    try:
        # Install dependencies
        install_dependencies()
        
        # Create spec file
        create_spec_file()
        
        # Build executable
        if build_executable():
            print("\nBuild process completed successfully!")
            print("You can now distribute the executable from the 'dist' folder.")
        else:
            print("\nBuild process failed. Please check the error messages above.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

