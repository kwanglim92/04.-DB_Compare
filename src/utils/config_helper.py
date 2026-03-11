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
        # Running as compiled EXE — config is embedded inside the executable
        base_path = Path(sys._MEIPASS)
        return base_path / "config"
    else:
        # Running as script — config is in project root/config
        return Path(__file__).parent.parent.parent / "config"

def get_settings_file() -> Path:
    """Get the path to settings.json"""
    return get_config_dir() / "settings.json"

def get_legacy_spec_file() -> Path:
    """Get the path to legacy qc_specs.json"""
    return get_config_dir() / "qc_specs.json"
