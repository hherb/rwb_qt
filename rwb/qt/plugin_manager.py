"""Qt plugin management module.

This module provides functionality to manage Qt platform plugins, including
finding, verifying, and caching plugin paths across different environments.
"""

import sys
import os
import json
import tempfile
from pathlib import Path
import subprocess
import site
from typing import List, Set, Optional

class QtPluginManager:
    """Manages Qt platform plugins with verification, caching, and fallback mechanisms.
    
    This class handles the discovery and verification of Qt platform plugins,
    particularly focusing on macOS where plugin management can be challenging.
    It implements caching to improve startup performance and provides fallback
    mechanisms for different installation scenarios.
    
    Attributes:
        cache_file (Path): Path to the cache file storing successful plugin paths
        cached_path (Optional[str]): Cached path to Qt plugins if available
        verified_paths (Set[str]): Set of paths that have been verified to work
    """
    
    def __init__(self) -> None:
        """Initialize the QtPluginManager.
        
        Sets up the cache file location and initializes instance variables.
        """
        self.cache_file = Path(tempfile.gettempdir()) / "qt_plugins_cache.json"
        self.cached_path: Optional[str] = None
        self.verified_paths: Set[str] = set()
        
    def load_cache(self) -> None:
        """Load cached plugin path from file.
        
        Attempts to load a previously successful plugin path from the cache file.
        If the cached path exists and is valid, it will be used as the primary
        plugin path.
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    if data.get('path') and os.path.exists(data['path']):
                        self.cached_path = data['path']
                        print(f"Loaded cached Qt plugin path: {self.cached_path}")
        except Exception as e:
            print(f"Error loading plugin cache: {e}")
    
    def save_cache(self, path: str) -> None:
        """Save successful plugin path to cache.
        
        Args:
            path: The path to the successfully verified Qt plugins
        """
        try:
            with open(self.cache_file, 'w') as f:
                json.dump({'path': path}, f)
            self.cached_path = path
        except Exception as e:
            print(f"Error saving plugin cache: {e}")
    
    def verify_plugins(self, path: str) -> bool:
        """Verify that Qt plugins at the given path are working.
        
        Args:
            path: The path to verify Qt plugins at
            
        Returns:
            bool: True if the plugins are verified to work, False otherwise
        """
        if path in self.verified_paths:
            return True
            
        try:
            # Simple verification: check if the cocoa plugin exists
            cocoa_plugin = os.path.join(path, "libqcocoa.dylib")
            if os.path.exists(cocoa_plugin):
                print(f"Found cocoa plugin at: {cocoa_plugin}")
                self.verified_paths.add(path)
                return True
            else:
                print(f"Cocoa plugin not found at: {cocoa_plugin}")
                return False
        except Exception as e:
            print(f"Plugin verification failed for {path}: {e}")
            return False
    
    def get_possible_plugin_paths(self) -> List[str]:
        """Get all possible plugin paths in order of priority.
        
        Searches for Qt plugin paths in various locations, ordered by priority:
        1. Cached path (if previously successful)
        2. Virtual environment paths
        3. PySide6 installation paths
        4. System-wide site-packages
        5. User's home directory
        
        Returns:
            List[str]: List of possible plugin paths in order of priority
        """
        paths: List[str] = []
        
        # 1. Check cached path first
        if self.cached_path and os.path.exists(self.cached_path):
            paths.append(self.cached_path)
            print(f"Added cached path: {self.cached_path}")
        
        # 2. Check virtual environment first (highest priority)
        if hasattr(sys, 'real_prefix') or hasattr(sys, 'base_prefix'):
            # We're in a virtual environment
            venv_path = sys.prefix
            possible_paths = [
                os.path.join(venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages", "PySide6", "Qt", "plugins", "platforms"),
                os.path.join(venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages", "PySide6", "plugins", "platforms"),
                os.path.join(venv_path, "lib", "site-packages", "PySide6", "Qt", "plugins", "platforms"),
                os.path.join(venv_path, "lib", "site-packages", "PySide6", "plugins", "platforms"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    paths.append(path)
                    print(f"Added virtual environment path: {path}")
        
        # 3. Check PySide6 installation
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "PySide6"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Location:'):
                        location = line.split(':', 1)[1].strip()
                        possible_paths = [
                            os.path.join(location, "PySide6", "Qt", "plugins", "platforms"),
                            os.path.join(location, "PySide6", "plugins", "platforms"),
                        ]
                        for path in possible_paths:
                            if os.path.exists(path):
                                paths.append(path)
                                print(f"Added PySide6 installation path: {path}")
        except Exception as e:
            print(f"Error finding PySide6 location: {e}")
        
        # 4. Check system-wide site-packages
        for site_dir in site.getsitepackages():
            possible_paths = [
                os.path.join(site_dir, "PySide6", "Qt", "plugins", "platforms"),
                os.path.join(site_dir, "PySide6", "plugins", "platforms"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    paths.append(path)
                    print(f"Added system site-packages path: {path}")
        
        # 5. Check user's home directory
        home_paths = [
            os.path.expanduser(f"~/.local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/PySide6/Qt/plugins/platforms"),
            os.path.expanduser(f"~/.local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/PySide6/plugins/platforms"),
        ]
        for path in home_paths:
            if os.path.exists(path):
                paths.append(path)
                print(f"Added home directory path: {path}")
        
        # Remove duplicates while preserving order
        seen: Set[str] = set()
        unique_paths: List[str] = []
        for path in paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        
        return unique_paths
    
    def setup_plugins(self) -> bool:
        """Setup Qt plugins with verification and fallback.
        
        Attempts to find and verify Qt plugins, setting up the necessary
        environment variables for Qt to function properly.
        
        Returns:
            bool: True if plugins were successfully set up, False otherwise
        """
        if sys.platform != "darwin":  # Only needed for macOS
            return True
        
        # Load cached path
        self.load_cache()
        
        # Try all possible paths
        paths = self.get_possible_plugin_paths()
        if not paths:
            print("No Qt plugin paths found!")
            return False
            
        print("\nTrying Qt plugin paths in order of priority:")
        for path in paths:
            print(f"\nAttempting path: {path}")
            
            # Set the plugin path
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = path
            
            # Set additional environment variables needed for Qt
            if hasattr(sys, 'real_prefix') or hasattr(sys, 'base_prefix'):
                # We're in a virtual environment
                venv_path = sys.prefix
                qt_lib_path = os.path.join(venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages", "PySide6", "Qt", "lib")
                if os.path.exists(qt_lib_path):
                    os.environ["DYLD_LIBRARY_PATH"] = qt_lib_path
                    os.environ["LD_LIBRARY_PATH"] = qt_lib_path
                    print(f"Set Qt library path: {qt_lib_path}")
            
            if self.verify_plugins(path):
                print(f"Successfully verified Qt plugins at: {path}")
                self.save_cache(path)
                return True
        
        # If we get here, no path worked
        print("\nWarning: Could not find working Qt platform plugins.")
        print("Try running: uv pip install --reinstall pyside6")
        return False 