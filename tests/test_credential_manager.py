"""
Tests for CredentialManager (src/utils/credential_manager.py)
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_appdata(tmp_path):
    """Temporary directory that replaces AppData/DB_Manager during tests."""
    return tmp_path / "DB_Manager"


@pytest.fixture
def credential_manager(tmp_appdata):
    """Return a CredentialManager whose file paths point to tmp_appdata."""
    tmp_appdata.mkdir(parents=True, exist_ok=True)
    key_file = tmp_appdata / ".key"
    cred_file = tmp_appdata / "credentials.enc"

    from src.utils.credential_manager import CredentialManager
    mgr = CredentialManager()
    # Redirect internal paths to temp dir
    mgr._key_file = key_file
    mgr._cred_file = cred_file
    return mgr


# ---------------------------------------------------------------------------
# 1. Key file auto-creation
# ---------------------------------------------------------------------------

class TestKeyAutoCreation:
    def test_key_file_created_when_absent(self, credential_manager, tmp_appdata):
        """Given no key file, When _get_or_create_key(), Then key file is created."""
        key_file = credential_manager._key_file
        assert not key_file.exists()
        key = credential_manager._get_or_create_key()
        assert key_file.exists()
        assert len(key) == 44  # Fernet key is 32-byte base64url → 44 ASCII chars

    def test_same_key_returned_on_subsequent_calls(self, credential_manager):
        """Given key already exists, When called twice, Then both calls return the same key."""
        key1 = credential_manager._get_or_create_key()
        key2 = credential_manager._get_or_create_key()
        assert key1 == key2


# ---------------------------------------------------------------------------
# 2. save_credentials / load_credentials round-trip
# ---------------------------------------------------------------------------

class TestCredentialRoundTrip:
    def test_basic_roundtrip(self, credential_manager):
        """Given valid credentials, When save then load, Then data is identical."""
        creds = {"host": "192.168.1.10", "port": "5434", "dbname": "qc_db",
                 "user": "admin", "password": "secret123"}
        assert credential_manager.save_credentials(creds) is True
        loaded = credential_manager.load_credentials()
        assert loaded == creds

    def test_unicode_values_roundtrip(self, credential_manager):
        """Given credentials with Unicode values, When save then load, Then values are preserved."""
        creds = {"host": "서버-호스트", "password": "비밀번호123!"}
        credential_manager.save_credentials(creds)
        loaded = credential_manager.load_credentials()
        assert loaded == creds

    def test_empty_dict_roundtrip(self, credential_manager):
        """Given empty dict, When save then load, Then empty dict is returned."""
        credential_manager.save_credentials({})
        loaded = credential_manager.load_credentials()
        assert loaded == {}

    def test_load_returns_none_when_no_files(self, credential_manager):
        """Given no credential file, When load_credentials(), Then None is returned."""
        result = credential_manager.load_credentials()
        assert result is None

    def test_encrypted_bytes_differ_from_plain(self, credential_manager, tmp_appdata):
        """Given saved credentials, When reading raw file, Then content is not plain JSON."""
        creds = {"host": "localhost", "password": "pass"}
        credential_manager.save_credentials(creds)
        raw = credential_manager._cred_file.read_bytes()
        assert b'"host"' not in raw  # must not be stored as plain text


# ---------------------------------------------------------------------------
# 3. Wrong key decryption
# ---------------------------------------------------------------------------

class TestWrongKeyDecryption:
    def test_load_returns_none_with_wrong_key(self, credential_manager, tmp_appdata):
        """Given credentials encrypted with key A, When key replaced with key B, Then None returned."""
        from cryptography.fernet import Fernet
        creds = {"host": "srv", "password": "pwd"}
        credential_manager.save_credentials(creds)

        # Replace key file with a different key
        new_key = Fernet.generate_key()
        credential_manager._key_file.write_bytes(new_key)

        result = credential_manager.load_credentials()
        assert result is None

    def test_load_returns_none_with_corrupt_cred_file(self, credential_manager):
        """Given corrupt credential bytes, When load_credentials(), Then None returned."""
        # Create a valid key first
        credential_manager._get_or_create_key()
        # Write garbage as credential file
        credential_manager._cred_file.write_bytes(b"this_is_not_valid_fernet_data")
        result = credential_manager.load_credentials()
        assert result is None


# ---------------------------------------------------------------------------
# 4. has_credentials
# ---------------------------------------------------------------------------

class TestHasCredentials:
    def test_false_before_any_save(self, credential_manager):
        """Given nothing saved, When has_credentials(), Then False."""
        assert credential_manager.has_credentials() is False

    def test_true_after_save(self, credential_manager):
        """Given credentials saved, When has_credentials(), Then True."""
        credential_manager.save_credentials({"host": "x"})
        assert credential_manager.has_credentials() is True

    def test_false_after_delete(self, credential_manager):
        """Given credentials saved then deleted, When has_credentials(), Then False."""
        credential_manager.save_credentials({"host": "x"})
        credential_manager.delete_credentials()
        assert credential_manager.has_credentials() is False


# ---------------------------------------------------------------------------
# 5. delete_credentials
# ---------------------------------------------------------------------------

class TestDeleteCredentials:
    def test_delete_removes_both_files(self, credential_manager):
        """Given both files exist, When delete_credentials(), Then both files are gone."""
        credential_manager.save_credentials({"host": "x"})
        assert credential_manager._cred_file.exists()
        assert credential_manager._key_file.exists()
        result = credential_manager.delete_credentials()
        assert result is True
        assert not credential_manager._cred_file.exists()
        assert not credential_manager._key_file.exists()

    def test_delete_is_safe_when_files_absent(self, credential_manager):
        """Given no files, When delete_credentials(), Then True returned (idempotent)."""
        result = credential_manager.delete_credentials()
        assert result is True
