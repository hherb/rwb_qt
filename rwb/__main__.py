"""Main entry point for the voice assistant application.

This module initializes the Qt application and sets up the plugin manager
before starting the main window.
"""

import sys
from PySide6.QtWidgets import QApplication
from .qt.plugin_manager import QtPluginManager
from .audio.assistant import AudioAssistant
from .audio.ui.styles import TOOLTIP_STYLE

def main() -> None:
    """Main entry point for the application.
    
    Initializes the Qt application, sets up the plugin manager,
    and starts the main window.
    """
    # Create and setup plugin manager
    plugin_manager = QtPluginManager()
    if not plugin_manager.setup_plugins():
        print("Failed to setup Qt plugins. The application might not work correctly.")
        sys.exit(1)
    
    # Create and start the application
    app = QApplication(sys.argv)
    
    window = AudioAssistant()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()