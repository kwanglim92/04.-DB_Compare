"""App version — single source of truth."""

from typing import Tuple

APP_VERSION = "1.5.0"


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse a semver string into (major, minor, patch). Ignores pre-release suffixes."""
    try:
        parts = version_str.strip().split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2].split("-")[0].split("+")[0]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except (ValueError, IndexError, AttributeError):
        return (0, 0, 0)


def is_newer(candidate: str, current: str) -> bool:
    """Return True if candidate version is strictly newer than current."""
    return parse_version(candidate) > parse_version(current)
