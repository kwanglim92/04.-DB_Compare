"""Tests for src/utils/version.py"""
import pytest
from src.utils.version import parse_version, is_newer, APP_VERSION


def test_parse_version_basic():
    assert parse_version("1.5.0") == (1, 5, 0)


def test_parse_version_patch():
    assert parse_version("2.10.3") == (2, 10, 3)


def test_parse_version_prerelease_ignored():
    assert parse_version("1.5.0-rc1") == (1, 5, 0)
    assert parse_version("1.5.0+build42") == (1, 5, 0)


def test_parse_version_invalid_returns_zero():
    assert parse_version("not-a-version") == (0, 0, 0)
    assert parse_version("") == (0, 0, 0)


def test_is_newer_true():
    assert is_newer("1.5.1", "1.5.0") is True
    assert is_newer("2.0.0", "1.9.9") is True


def test_is_newer_false_when_same():
    assert is_newer("1.5.0", "1.5.0") is False


def test_is_newer_false_when_older():
    assert is_newer("1.4.0", "1.5.0") is False


def test_app_version_is_string():
    assert isinstance(APP_VERSION, str)
    assert len(APP_VERSION) > 0


def test_app_version_parseable():
    major, minor, patch = parse_version(APP_VERSION)
    assert (major, minor, patch) >= (1, 5, 0)
