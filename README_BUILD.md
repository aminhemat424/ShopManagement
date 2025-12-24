# Building Shop Management Application

## Prerequisites

1. Python 3.8 or higher
2. All dependencies installed (from requirements.txt or your environment)

## Building the Executable

### Option 1: Using the Batch Script (Windows)

Simply run:
```bash
build.bat
```

This will:
- Check if PyInstaller is installed (install if needed)
- Build the executable using the spec file
- Create `ShopManagement.exe` in the `dist` folder

### Option 2: Manual Build

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build using the spec file:
```bash
pyinstaller --clean build_exe.spec
```

3. The executable will be in the `dist` folder: `dist\ShopManagement.exe`

## Creating an Installer (Optional)

For a professional installer, you can use:

### Inno Setup (Recommended for Windows)
1. Download Inno Setup: https://jrsoftware.org/isinfo.php
2. Create an installer script that:
   - Copies `ShopManagement.exe` to Program Files
   - Creates a desktop shortcut
   - Creates a Start Menu entry
   - Handles uninstallation

### NSIS (Nullsoft Scriptable Install System)
1. Download NSIS: https://nsis.sourceforge.io/
2. Create an installer script

### Advanced Installer
Commercial tool with GUI: https://www.advancedinstaller.com/

## Notes

- The executable is a single file (all dependencies bundled)
- First run may be slightly slower as files are extracted
- **Database Location**: The database file (`shop_data.db`) is stored in:
  - **Windows**: `C:\Users\[Username]\AppData\Local\ShopManagement\shop_data.db`
  - This ensures write permissions work even when installed in Program Files
  - See `DATABASE_FIX.md` for more details
- For distribution, you may want to:
  - Add an icon file (update `icon=None` in build_exe.spec)
  - Create a proper installer
  - Include a README for end users
  - Test on a clean Windows machine without Python installed

## Troubleshooting

If the executable doesn't run:
1. Check if all dependencies are included in `hiddenimports` in build_exe.spec
2. Run with console enabled (set `console=True` in build_exe.spec) to see errors
3. Check Windows Event Viewer for application errors
4. Test on a clean machine to ensure all dependencies are bundled

## File Size

The executable will be large (50-100MB) because it includes:
- Python runtime
- PyQt6 libraries
- All dependencies
- Your application code

This is normal for PyInstaller single-file executables.
