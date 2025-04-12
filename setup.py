"""
This is a setup.py script generated for packaging the rwb application
with py2app.
"""

from setuptools import setup

APP = ['main.py']
DATA_FILES = [('icons', ['rwb/icons/'])
             ]
OPTIONS = {
    'argv_emulation': True,
    'packages': ['rwb', 'agno', 'PySide6', 'numpy', 'librosa', 'ollama', 'fastrtc', 'pyaudio', 
                 'duckduckgo_search', 'kokoro', 'markdown', 'newspaper4k', 'pydub', 'pygame'],
    'includes': ['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets'],
    'excludes': ['tkinter', 'matplotlib', 'PyQt5'],
    'iconfile': 'rwb/icons/horstcartoon.png',
    'plist': {
        'CFBundleName': 'RWB',
        'CFBundleDisplayName': 'RWB',
        'CFBundleIdentifier': 'com.rwb.app',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSHumanReadableCopyright': 'Copyright © 2025, All Rights Reserved',
        'NSMicrophoneUsageDescription': 'The application needs access to the microphone for audio input.',
    }
}

setup(
    name='RWB',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
