"""
Credential Manager Module
Handles encryption/decryption of server connection credentials
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet

from src.utils.config_helper import get_credentials_file, get_encryption_key_file

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manages encrypted storage of server credentials"""

    def __init__(self):
        self._key_file = get_encryption_key_file()
        self._cred_file = get_credentials_file()

    def _get_or_create_key(self) -> bytes:
        """Get existing key or create a new one"""
        if self._key_file.exists():
            return self._key_file.read_bytes()

        key = Fernet.generate_key()
        self._key_file.write_bytes(key)
        # Restrict key file permissions on non-Windows platforms
        if sys.platform != 'win32':
            os.chmod(self._key_file, 0o600)
        logger.info("Generated new encryption key")
        return key

    def save_credentials(self, credentials: Dict[str, str]) -> bool:
        """Encrypt and save server credentials"""
        try:
            key = self._get_or_create_key()
            fernet = Fernet(key)
            data = json.dumps(credentials).encode('utf-8')
            encrypted = fernet.encrypt(data)
            self._cred_file.write_bytes(encrypted)
            logger.info("Credentials saved (encrypted)")
            return True
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False

    def load_credentials(self) -> Optional[Dict[str, str]]:
        """Load and decrypt server credentials"""
        if not self._cred_file.exists() or not self._key_file.exists():
            return None

        try:
            key = self._key_file.read_bytes()
            fernet = Fernet(key)
            encrypted = self._cred_file.read_bytes()
            decrypted = fernet.decrypt(encrypted)
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return None

    def has_credentials(self) -> bool:
        """Check if credentials exist"""
        return self._cred_file.exists() and self._key_file.exists()

    def delete_credentials(self) -> bool:
        """Delete stored credentials"""
        try:
            if self._cred_file.exists():
                self._cred_file.unlink()
            if self._key_file.exists():
                self._key_file.unlink()
            logger.info("Credentials deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False
