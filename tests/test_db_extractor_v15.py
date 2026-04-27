"""Tests for v1.5.0 additions to DBExtractor (F5)."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.core.db_extractor import DBExtractor


# ---------------------------------------------------------------------------
# validate_db_root
# ---------------------------------------------------------------------------

def test_validate_valid(tmp_path):
    module_dir = tmp_path / "Module" / "Dsp"
    module_dir.mkdir(parents=True)
    status, _ = DBExtractor.validate_db_root(str(tmp_path))
    assert status == "valid"


def test_validate_no_module_dir(tmp_path):
    status, path = DBExtractor.validate_db_root(str(tmp_path))
    assert status == "no_module_dir"
    assert path == str(tmp_path)


def test_validate_empty_module(tmp_path):
    (tmp_path / "Module").mkdir()
    status, _ = DBExtractor.validate_db_root(str(tmp_path))
    assert status == "empty"


def test_validate_nonexistent_path():
    status, _ = DBExtractor.validate_db_root("/nonexistent/path/xyz")
    assert status == "no_module_dir"


# ---------------------------------------------------------------------------
# find_db_root_in_subtree
# ---------------------------------------------------------------------------

def test_find_root_direct(tmp_path):
    (tmp_path / "Module").mkdir()
    result = DBExtractor.find_db_root_in_subtree(str(tmp_path))
    assert result == tmp_path


def test_find_root_one_level_deep(tmp_path):
    db_dir = tmp_path / "DB"
    (db_dir / "Module").mkdir(parents=True)
    result = DBExtractor.find_db_root_in_subtree(str(tmp_path))
    assert result == db_dir


def test_find_root_too_deep(tmp_path):
    deep = tmp_path / "a" / "b" / "c" / "d"
    (deep / "Module").mkdir(parents=True)
    result = DBExtractor.find_db_root_in_subtree(str(tmp_path), max_depth=2)
    assert result is None


def test_find_root_not_found(tmp_path):
    (tmp_path / "SomeOtherFolder").mkdir()
    result = DBExtractor.find_db_root_in_subtree(str(tmp_path))
    assert result is None


# ---------------------------------------------------------------------------
# extract_all_modules — PermissionError graceful skip
# ---------------------------------------------------------------------------

def test_extract_all_modules_permission_error(tmp_path):
    (tmp_path / "Module").mkdir()
    with patch("src.core.db_extractor.DBExtractor.__init__", return_value=None):
        extractor = DBExtractor.__new__(DBExtractor)
        extractor.db_root = tmp_path
        extractor.logger = MagicMock()
        extractor.parser = MagicMock()

        with patch.object(Path, "iterdir", side_effect=PermissionError("denied")):
            result = extractor.extract_all_modules()
        assert result == []
        extractor.logger.warning.assert_called()
