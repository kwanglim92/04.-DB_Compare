"""
Config Helper Module
Provides utilities for path resolution depending on execution environment and sync mode
"""

import sys
import os
from pathlib import Path

# Admin authentication password — gates access to server settings & spec editing.
# NOTE: stored as plain constant for sideloaded internal EXE distribution;
# consider env var / encrypted credential for production hardening (PRD §8.4).
ADMIN_PASSWORD = "pqc123"


def get_appdata_dir() -> Path:
    """Get the application data directory for local cache"""
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    else:
        base = Path.home() / '.config'
    app_dir = base / 'DB_Manager'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_cache_dir() -> Path:
    """Get the local cache directory for synced config"""
    cache_dir = get_appdata_dir() / "config"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_config_dir(mode: str = "offline") -> Path:
    """
    Get the configuration directory path.
    Handles three modes:
    - "online": Use local cache (synced from server)
    - "offline": Use bundled/local config
    - Auto-detection for frozen/script environments

    Args:
        mode: "online" or "offline"

    Returns:
        Path object pointing to the config directory
    """
    if mode == "online":
        cache_dir = get_cache_dir()
        # Only use cache if it has data
        if (cache_dir / "common_base.json").exists():
            return cache_dir

    # Fallback: bundled or local config
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE — config is embedded inside the executable
        base_path = Path(sys._MEIPASS)
        return base_path / "config"
    else:
        # Running as script — config is in project root/config
        return Path(__file__).parent.parent.parent / "config"


def get_settings_file() -> Path:
    """Get the path to settings.json (always in AppData for writability)"""
    appdata_settings = get_appdata_dir() / "settings.json"
    if appdata_settings.exists():
        return appdata_settings

    # Fallback to bundled settings
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / "config" / "settings.json"
    else:
        return Path(__file__).parent.parent.parent / "config" / "settings.json"


def get_credentials_file() -> Path:
    """Get the path to encrypted credentials file"""
    return get_appdata_dir() / "credentials.enc"


def get_encryption_key_file() -> Path:
    """Get the path to encryption key file"""
    return get_appdata_dir() / ".key"


def get_legacy_spec_file() -> Path:
    """Get the path to legacy qc_specs.json"""
    return get_config_dir() / "qc_specs.json"
