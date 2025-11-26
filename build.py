"""
Build script for BMSgo Smart Inventory System
This script builds a standalone executable using PyInstaller.
"""
import os
import subprocess
import shutil
import sys

def main():
    """Main build function."""
    print("Building BMSgo Smart Inventory System...")
    
    # Clean up previous builds
    if os.path.exists('dist'):
        print("Cleaning up previous builds...")
        shutil.rmtree('dist', ignore_errors=True)
    if os.path.exists('build'):
        shutil.rmtree('build', ignore_errors=True)
    
    # Create necessary directories
    os.makedirs('dist', exist_ok=True)
    
    # Run PyInstaller
    print("Running PyInstaller...")
    result = subprocess.run([
        'pyinstaller',
        '--clean',
        '--noconfirm',
        'bmsgo.spec'
    ], capture_output=True, text=True)
    
    # Check if PyInstaller was successful
    if result.returncode != 0:
        print("PyInstaller failed with the following error:")
        print(result.stderr)
        return 1
    
    print("Build completed successfully!")
    print(f"Executable can be found in: {os.path.abspath('dist/BMSgo')}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
