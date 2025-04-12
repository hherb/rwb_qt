#!/bin/bash
# Packaging script for RWB macOS application using PyInstaller

# Exit on error
set -e

echo "===== Starting RWB macOS packaging process with PyInstaller ====="

# Install PyInstaller if not already installed
pip install pyinstaller

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Create the application bundle with PyInstaller
echo "Creating application bundle with PyInstaller..."
pyinstaller --clean --noconfirm rwb.spec

# Verify the app was created
if [ ! -d "dist/RWB.app" ]; then
    echo "Error: Application bundle was not created successfully."
    exit 1
fi

echo "Application bundle created successfully at dist/RWB.app"

# Create a temporary directory for DMG contents
echo "Creating DMG image..."
DMG_TMP="dist/dmg_tmp"
mkdir -p "$DMG_TMP"

# Copy the app bundle to the temporary directory
cp -R "dist/RWB.app" "$DMG_TMP/"

# Create a symbolic link to the Applications folder
ln -s /Applications "$DMG_TMP/Applications"

# Create the DMG file
hdiutil create -volname "RWB Installer" -srcfolder "$DMG_TMP" -ov -format UDZO "dist/RWB-0.1.0.dmg"

# Clean up the temporary directory
rm -rf "$DMG_TMP"

echo "===== Packaging complete! ====="
echo "DMG installer created at: dist/RWB-0.1.0.dmg"
echo "You can distribute this file to Mac users for easy installation."
