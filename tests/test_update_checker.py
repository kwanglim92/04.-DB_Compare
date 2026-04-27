"""Tests for src/core/update_checker.py (F13)."""
import threading
import pytest
from unittest.mock import MagicMock, patch
from src.core.update_checker import UpdateChecker


_CONFIG = {
    "host": "localhost", "port": 5434,
    "dbname": "dbmanager", "user": "dbmanager", "password": "test"
}


def _run_sync(checker) -> dict | None:
    """Helper: run check_async synchronously."""
    result = [None]
    event = threading.Event()
    def cb(info):
        result[0] = info
        event.set()
    checker.check_async(cb)
    event.wait(timeout=5)
    return result[0]


def test_returns_none_when_no_psycopg2():
    checker = UpdateChecker(_CONFIG)
    with patch("src.core.update_checker.HAS_PSYCOPG2", False):
        checker._config = _CONFIG
        result = checker._fetch_latest()
    assert result is None


def test_returns_none_when_no_config():
    checker = UpdateChecker({})
    result = checker._fetch_latest()
    assert result is None


def test_returns_release_info_on_success():
    checker = UpdateChecker(_CONFIG)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchone.return_value = (
        "1.5.1", "\\\\server\\share\\DB_Manager.exe",
        "## v1.5.1\n- Bug fix", False, "1.4.0"
    )
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("src.core.update_checker.HAS_PSYCOPG2", True):
        with patch("src.core.update_checker.psycopg2") as mock_psycopg2:
            mock_psycopg2.connect.return_value = mock_conn
            mock_psycopg2.errors = MagicMock()
            mock_psycopg2.errors.UndefinedTable = type("UndefinedTable", (Exception,), {})
            result = checker._fetch_latest()

    assert result is not None
    assert result["version"] == "1.5.1"
    assert result["is_critical"] is False
    assert result["min_compatible_version"] == "1.4.0"


def test_returns_none_on_connection_error():
    checker = UpdateChecker(_CONFIG)
    with patch("src.core.update_checker.HAS_PSYCOPG2", True):
        with patch("src.core.update_checker.psycopg2") as mock_psycopg2:
            mock_psycopg2.connect.side_effect = Exception("connection refused")
            mock_psycopg2.errors = MagicMock()
            mock_psycopg2.errors.UndefinedTable = type("UndefinedTable", (Exception,), {})
            result = checker._fetch_latest()
    assert result is None


def test_returns_none_on_missing_table():
    checker = UpdateChecker(_CONFIG)

    class FakeUndefinedTable(Exception):
        pass

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.execute.side_effect = FakeUndefinedTable("table not found")
    mock_conn.cursor.return_value = mock_cursor

    with patch("src.core.update_checker.HAS_PSYCOPG2", True):
        with patch("src.core.update_checker.psycopg2") as mock_psycopg2:
            mock_psycopg2.connect.return_value = mock_conn
            mock_psycopg2.errors.UndefinedTable = FakeUndefinedTable
            result = checker._fetch_latest()
    assert result is None
