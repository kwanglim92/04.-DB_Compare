"""
Config Helper Module
Provides utilities for path resolution depending on execution environment
"""

import sys
from pathlib import Path

def get_config_dir() -> Path:
    """
    Get the configuration directory path.
    Handles both standalone compiled EXE (PyInstaller) and script execution.
    
    Returns:
        Path object pointing to the config directory
    """
    if getattr(sys, 'frozen', False):
        # If running as compiled EXE, config is in the same directory as the executable
        return Path(sys.executable).parent / "config"
    else:
        # If running as script, config is in root/config
        return Path(__file__).parent.parent.parent / "config"

def get_settings_file() -> Path:
    """Get the path to settings.json"""
    return get_config_dir() / "settings.json"

def get_legacy_spec_file() -> Path:
    """Get the path to legacy qc_specs.json"""
    return get_config_dir() / "qc_specs.json"
