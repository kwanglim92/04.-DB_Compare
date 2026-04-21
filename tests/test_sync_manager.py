"""
Tests for SyncManager (src/core/sync_manager.py)
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_cache(tmp_path):
    """Return a fresh temporary cache directory for each test."""
    return tmp_path / "cache"


@pytest.fixture
def manager(tmp_cache):
    from src.core.sync_manager import SyncManager
    return SyncManager(tmp_cache)


# ---------------------------------------------------------------------------
# 1. Cache directory creation
# ---------------------------------------------------------------------------

class TestCacheDirectoryCreation:
    def test_cache_dir_is_created_on_init(self, tmp_cache):
        """Given a non-existent path, When SyncManager is created, Then cache_dir exists."""
        from src.core.sync_manager import SyncManager
        assert not tmp_cache.exists()
        SyncManager(tmp_cache)
        assert tmp_cache.is_dir()

    def test_profiles_subdir_is_created_on_init(self, tmp_cache):
        """Given a non-existent path, When SyncManager is created, Then profiles/ subdir exists."""
        from src.core.sync_manager import SyncManager
        SyncManager(tmp_cache)
        assert (tmp_cache / "profiles").is_dir()

    def test_get_cache_dir_returns_configured_path(self, manager, tmp_cache):
        """When get_cache_dir() is called, Then it returns the path passed to __init__."""
        assert manager.get_cache_dir() == tmp_cache


# ---------------------------------------------------------------------------
# 2. has_local_cache
# ---------------------------------------------------------------------------

class TestHasLocalCache:
    def test_returns_false_when_cache_is_empty(self, manager):
        """Given no common_base.json, When has_local_cache(), Then False."""
        assert manager.has_local_cache() is False

    def test_returns_true_when_common_base_exists(self, manager, tmp_cache):
        """Given common_base.json exists, When has_local_cache(), Then True."""
        (tmp_cache / "common_base.json").write_text("{}", encoding="utf-8")
        assert manager.has_local_cache() is True

    def test_profiles_dir_alone_does_not_count_as_cache(self, manager, tmp_cache):
        """Given only profiles/ dir exists (no common_base), Then has_local_cache() is False."""
        # profiles dir is auto-created but common_base is absent
        assert (tmp_cache / "profiles").is_dir()
        assert manager.has_local_cache() is False


# ---------------------------------------------------------------------------
# 3. get_local_versions
# ---------------------------------------------------------------------------

class TestGetLocalVersions:
    def test_returns_zero_defaults_when_no_version_file(self, manager):
        """Given no sync_versions.json, When get_local_versions(), Then {'specs':0,'profiles':0}."""
        result = manager.get_local_versions()
        assert result == {"specs": 0, "profiles": 0}

    def test_returns_stored_versions(self, manager, tmp_cache):
        """Given sync_versions.json with data, When get_local_versions(), Then data is returned."""
        data = {"specs": 3, "profiles": 5}
        (tmp_cache / "sync_versions.json").write_text(json.dumps(data), encoding="utf-8")
        assert manager.get_local_versions() == data

    def test_returns_defaults_on_corrupt_version_file(self, manager, tmp_cache):
        """Given corrupt sync_versions.json, When get_local_versions(), Then default zeros returned."""
        (tmp_cache / "sync_versions.json").write_text("NOT_JSON", encoding="utf-8")
        result = manager.get_local_versions()
        assert result == {"specs": 0, "profiles": 0}


# ---------------------------------------------------------------------------
# 4. _save_local_versions (round-trip)
# ---------------------------------------------------------------------------

class TestSaveLocalVersions:
    def test_roundtrip_save_and_load(self, manager):
        """Given version dict, When _save_local_versions then get_local_versions, Then same data."""
        versions = {"specs": 7, "profiles": 2}
        manager._save_local_versions(versions)
        assert manager.get_local_versions() == versions


# ---------------------------------------------------------------------------
# 5. connect – offline / psycopg2 not available
# ---------------------------------------------------------------------------

class TestConnectOffline:
    def test_connect_returns_false_when_psycopg2_missing(self, manager):
        """Given psycopg2 not installed, When connect(), Then returns False."""
        import src.core.sync_manager as sm_module
        original = sm_module.HAS_PSYCOPG2
        sm_module.HAS_PSYCOPG2 = False
        try:
            result = manager.connect()
            assert result is False
        finally:
            sm_module.HAS_PSYCOPG2 = original

    def test_connect_returns_false_when_not_configured(self, manager):
        """Given psycopg2 available but no server config, When connect(), Then returns False."""
        import src.core.sync_manager as sm_module
        if not sm_module.HAS_PSYCOPG2:
            pytest.skip("psycopg2 not installed")
        result = manager.connect()
        assert result is False

    def test_connect_returns_false_on_connection_error(self, manager):
        """Given invalid host/port, When connect(), Then returns False and conn is None."""
        import src.core.sync_manager as sm_module
        if not sm_module.HAS_PSYCOPG2:
            pytest.skip("psycopg2 not installed")
        manager.configure_server("127.0.0.1", 9999, "testdb", "user", "pass")
        result = manager.connect()
        assert result is False
        assert manager.conn is None


# ---------------------------------------------------------------------------
# 6. is_connected property (offline)
# ---------------------------------------------------------------------------

class TestIsConnectedOffline:
    def test_is_connected_false_when_no_conn(self, manager):
        """Given conn is None, When is_connected, Then False."""
        assert manager.is_connected is False


# ---------------------------------------------------------------------------
# 7. needs_sync
# ---------------------------------------------------------------------------

class TestNeedsSync:
    def test_returns_false_when_not_connected(self, manager):
        """Given not connected (get_server_versions returns None), When needs_sync(), Then False."""
        result = manager.needs_sync()
        assert result is False


# ---------------------------------------------------------------------------
# 8. sync – not connected
# ---------------------------------------------------------------------------

class TestSyncNotConnected:
    def test_sync_fails_when_not_connected(self, manager):
        """Given not connected, When sync(), Then returns (False, error message)."""
        success, msg = manager.sync()
        assert success is False
        assert "연결" in msg


# ---------------------------------------------------------------------------
# 9. test_connection – psycopg2 missing
# ---------------------------------------------------------------------------

class TestTestConnectionOffline:
    def test_returns_false_with_message_when_psycopg2_missing(self, manager):
        """Given psycopg2 not installed, When test_connection(), Then (False, message)."""
        import src.core.sync_manager as sm_module
        original = sm_module.HAS_PSYCOPG2
        sm_module.HAS_PSYCOPG2 = False
        try:
            ok, msg = manager.test_connection("host", 5432, "db", "u", "p")
            assert ok is False
            assert len(msg) > 0
        finally:
            sm_module.HAS_PSYCOPG2 = original


# ---------------------------------------------------------------------------
# 10. disconnect (idempotent)
# ---------------------------------------------------------------------------

class TestDisconnect:
    def test_disconnect_is_safe_when_already_disconnected(self, manager):
        """Given conn is None, When disconnect(), Then no exception is raised."""
        manager.disconnect()  # should not raise

    def test_disconnect_clears_conn(self, manager):
        """Given a mock connection, When disconnect(), Then conn becomes None."""
        mock_conn = MagicMock()
        manager.conn = mock_conn
        manager.disconnect()
        assert manager.conn is None
        mock_conn.close.assert_called_once()
