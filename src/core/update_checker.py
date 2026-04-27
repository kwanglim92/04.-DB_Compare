"""Async update checker — queries app_releases table on the DB server."""

import logging
import threading
from typing import Callable, Optional, Dict

logger = logging.getLogger(__name__)

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

_QUERY = """
    SELECT version, download_url, release_notes, is_critical, min_compatible_version
    FROM app_releases
    ORDER BY release_date DESC
    LIMIT 1
"""


class UpdateChecker:
    """Checks for a newer app version against the server's app_releases table."""

    def __init__(self, server_config: Dict):
        """
        Args:
            server_config: dict with keys host, port, dbname, user, password
        """
        self._config = server_config

    def check_async(self, callback: Callable[[Optional[Dict]], None]):
        """Run the version check in a daemon thread; call callback with result dict or None."""
        t = threading.Thread(target=self._run, args=(callback,), daemon=True)
        t.start()

    def _run(self, callback: Callable[[Optional[Dict]], None]):
        result = self._fetch_latest()
        callback(result)

    def _fetch_latest(self) -> Optional[Dict]:
        if not HAS_PSYCOPG2:
            logger.debug("psycopg2 not available — skipping update check")
            return None
        if not self._config:
            return None

        conn = None
        try:
            conn = psycopg2.connect(
                host=self._config.get('host'),
                port=self._config.get('port'),
                dbname=self._config.get('dbname'),
                user=self._config.get('user'),
                password=self._config.get('password'),
                connect_timeout=5
            )
            with conn.cursor() as cur:
                cur.execute(_QUERY)
                row = cur.fetchone()
            if not row:
                return None
            return {
                'version': row[0],
                'download_url': row[1],
                'release_notes': row[2] or '',
                'is_critical': bool(row[3]),
                'min_compatible_version': row[4] or '',
            }
        except psycopg2.errors.UndefinedTable:
            logger.debug("app_releases table not found — skipping update check")
            return None
        except Exception as e:
            logger.debug(f"Update check failed (silent): {e}")
            return None
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
