"""
PyInstaller spec file for the RWB application
"""

a = Analysis(['main.py'],
             pathex=[],
             binaries=[],
             datas=[('rwb/icons', 'icons')],
             hiddenimports=['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 
                           'rwb', 'agno', 'pyaudio', 'librosa', 'ollama', 'fastrtc',
                           'numpy', 'duckduckgo_search', 'kokoro', 'markdown', 'newspaper4k', 
                           'pydub', 'pygame'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['tkinter', 'matplotlib'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=None)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='RWB',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='rwb/icons/horstcartoon.png')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='RWB')

app = BUNDLE(coll,
             name='RWB.app',
             icon='rwb/icons/horstcartoon.png',
             bundle_identifier='com.rwb.app',
             info_plist={
                'NSMicrophoneUsageDescription': 'The application needs access to the microphone for audio input.',
                'CFBundleShortVersionString': '0.1.0',
                'CFBundleVersion': '0.1.0',
                'NSHumanReadableCopyright': 'Copyright © 2025, All Rights Reserved',
                'CFBundleName': 'RWB',
                'CFBundleDisplayName': 'RWB',
             })
