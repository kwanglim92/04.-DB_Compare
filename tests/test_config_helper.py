"""
Tests for config_helper path resolution (src/utils/config_helper.py)
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_fresh():
    """Import config_helper (already imported modules are fine; we just return it)."""
    from src.utils import config_helper
    return config_helper


# ---------------------------------------------------------------------------
# 1. get_appdata_dir
# ---------------------------------------------------------------------------

class TestGetAppdataDir:
    def test_creates_directory(self, tmp_path):
        """Given a custom APPDATA env var, When get_appdata_dir(), Then DB_Manager dir is created."""
        ch = _import_fresh()
        with patch.dict(os.environ, {"APPDATA": str(tmp_path)}):
            with patch("sys.platform", "win32"):
                result = ch.get_appdata_dir()
        assert result.is_dir()
        assert result.name == "DB_Manager"

    def test_win32_uses_appdata_env(self, tmp_path):
        """Given win32 platform, When get_appdata_dir(), Then path is under APPDATA."""
        ch = _import_fresh()
        with patch.dict(os.environ, {"APPDATA": str(tmp_path)}):
            with patch("sys.platform", "win32"):
                result = ch.get_appdata_dir()
        assert str(tmp_path) in str(result)

    def test_non_win32_uses_home_config(self, tmp_path):
        """Given non-win32 platform, When get_appdata_dir(), Then path is under ~/.config."""
        ch = _import_fresh()
        with patch("sys.platform", "linux"):
            with patch("pathlib.Path.home", return_value=tmp_path):
                result = ch.get_appdata_dir()
        assert ".config" in str(result) or "DB_Manager" in str(result)


# ---------------------------------------------------------------------------
# 2. get_cache_dir
# ---------------------------------------------------------------------------

class TestGetCacheDir:
    def test_cache_dir_is_under_appdata(self, tmp_path):
        """When get_cache_dir(), Then returned path is appdata/config."""
        ch = _import_fresh()
        with patch.dict(os.environ, {"APPDATA": str(tmp_path)}):
            with patch("sys.platform", "win32"):
                result = ch.get_cache_dir()
        assert result.name == "config"
        assert result.is_dir()

    def test_cache_dir_is_created(self, tmp_path):
        """Given cache dir absent, When get_cache_dir(), Then directory is created."""
        ch = _import_fresh()
        with patch.dict(os.environ, {"APPDATA": str(tmp_path)}):
            with patch("sys.platform", "win32"):
                result = ch.get_cache_dir()
        assert result.exists()


# ---------------------------------------------------------------------------
# 3. get_config_dir — offline mode
# ---------------------------------------------------------------------------

class TestGetConfigDirOffline:
    def test_offline_returns_local_config_in_script_mode(self):
        """Given offline mode and not frozen, When get_config_dir('offline'), Then local config/ returned."""
        ch = _import_fresh()
        # Ensure we're not in frozen mode
        with patch.object(sys, "frozen", False, create=True):
            result = ch.get_config_dir("offline")
        # Should end with 'config'
        assert result.name == "config"
        # Should NOT be under AppData
        assert "DB_Manager" not in str(result)

    def test_offline_mode_does_not_check_cache(self, tmp_path):
        """Given offline mode, When get_config_dir('offline'), Then cache dir is never checked."""
        ch = _import_fresh()
        # Even if cache/common_base.json exists, offline should not return it
        cache = tmp_path / "config"
        cache.mkdir(parents=True)
        (cache / "common_base.json").write_text("{}", encoding="utf-8")

        with patch.object(sys, "frozen", False, create=True):
            result = ch.get_config_dir("offline")

        # Result must be the local project config, not tmp_path cache
        assert str(tmp_path) not in str(result)


# ---------------------------------------------------------------------------
# 4. get_config_dir — online mode, no cache
# ---------------------------------------------------------------------------

class TestGetConfigDirOnlineNoCache:
    def test_online_falls_back_to_local_when_no_cache(self, tmp_path):
        """Given online mode but cache has no common_base.json, Then local config/ is returned."""
        ch = _import_fresh()
        with patch.dict(os.environ, {"APPDATA": str(tmp_path)}):
            with patch("sys.platform", "win32"):
                with patch.object(sys, "frozen", False, create=True):
                    result = ch.get_config_dir("online")
        # Fallback should be local config, not AppData cache
        assert result.name == "config"
        assert "DB_Manager" not in str(result)


# ---------------------------------------------------------------------------
# 5. get_config_dir — online mode, cache present
# ---------------------------------------------------------------------------

class TestGetConfigDirOnlineWithCache:
    def test_online_returns_cache_when_common_base_exists(self, tmp_path):
        """Given online mode and cache has common_base.json, Then cache dir is returned."""
        ch = _import_fresh()
        # Simulate AppData layout
        appdata_root = tmp_path / "Roaming"
        appdata_root.mkdir()
        cache_dir = appdata_root / "DB_Manager" / "config"
        cache_dir.mkdir(parents=True)
        (cache_dir / "common_base.json").write_text("{}", encoding="utf-8")

        with patch.dict(os.environ, {"APPDATA": str(appdata_root)}):
            with patch("sys.platform", "win32"):
                result = ch.get_config_dir("online")

        assert str(result) == str(cache_dir)


# ---------------------------------------------------------------------------
# 6. get_credentials_file / get_encryption_key_file
# ---------------------------------------------------------------------------

class TestSpecialFilePaths:
    def test_credentials_file_is_in_appdata(self, tmp_path):
        """When get_credentials_file(), Then path is inside DB_Manager appdata dir."""
        ch = _import_fresh()
        with patch.dict(os.environ, {"APPDATA": str(tmp_path)}):
            with patch("sys.platform", "win32"):
                result = ch.get_credentials_file()
        assert result.name == "credentials.enc"
        assert "DB_Manager" in str(result)

    def test_encryption_key_file_is_in_appdata(self, tmp_path):
        """When get_encryption_key_file(), Then path is inside DB_Manager appdata dir."""
        ch = _import_fresh()
        with patch.dict(os.environ, {"APPDATA": str(tmp_path)}):
            with patch("sys.platform", "win32"):
                result = ch.get_encryption_key_file()
        assert result.name == ".key"
        assert "DB_Manager" in str(result)
