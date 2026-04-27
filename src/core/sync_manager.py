"""
Sync Manager Module
Manages synchronization between server PostgreSQL and local JSON cache
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from copy import deepcopy

logger = logging.getLogger(__name__)

# psycopg2 is optional — only needed in online mode
try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


class SyncManager:
    """Manages server DB sync and local JSON cache"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.conn = None
        self._server_config = None
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Create cache directory structure if needed"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "profiles").mkdir(exist_ok=True)

    # ========================================
    # Connection Management
    # ========================================

    def configure_server(self, host: str, port: int, dbname: str,
                         user: str, password: str):
        """Set server connection parameters"""
        self._server_config = {
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        }

    def connect(self) -> bool:
        """Establish connection to server DB"""
        if not HAS_PSYCOPG2:
            logger.warning("psycopg2 not installed, cannot connect to server")
            return False

        if not self._server_config:
            logger.warning("Server not configured")
            return False

        try:
            self.conn = psycopg2.connect(
                host=self._server_config['host'],
                port=self._server_config['port'],
                dbname=self._server_config['dbname'],
                user=self._server_config['user'],
                password=self._server_config['password'],
                connect_timeout=5
            )
            logger.info(f"Connected to server: {self._server_config['host']}:{self._server_config['port']}")
            return True
        except Exception as e:
            logger.error(f"Server connection failed: {e}")
            self.conn = None
            return False

    def disconnect(self):
        """Close server connection"""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
            logger.info("Disconnected from server")

    def test_connection(self, host: str, port: int, dbname: str,
                        user: str, password: str) -> Tuple[bool, str]:
        """Test server connection with given parameters"""
        if not HAS_PSYCOPG2:
            return False, "psycopg2 라이브러리가 설치되지 않았습니다"

        try:
            test_conn = psycopg2.connect(
                host=host, port=port, dbname=dbname,
                user=user, password=password,
                connect_timeout=5
            )
            # Verify schema exists
            cursor = test_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sync_versions")
            cursor.close()
            test_conn.close()
            return True, "연결 성공"
        except psycopg2.OperationalError as e:
            return False, f"연결 실패: {e}"
        except psycopg2.ProgrammingError:
            return False, "DB 스키마가 초기화되지 않았습니다"
        except Exception as e:
            return False, f"오류: {e}"

    @property
    def is_connected(self) -> bool:
        """Check if currently connected"""
        if not self.conn:
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            self.conn = None
            return False

    # ========================================
    # Version Check
    # ========================================

    def get_server_versions(self) -> Optional[Dict[str, int]]:
        """Get version numbers from server"""
        if not self.is_connected:
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT table_name, version FROM sync_versions")
            versions = {row[0]: row[1] for row in cursor.fetchall()}
            cursor.close()
            return versions
        except Exception as e:
            logger.error(f"Failed to get server versions: {e}")
            return None

    def get_local_versions(self) -> Dict[str, int]:
        """Get version numbers from local cache"""
        version_file = self.cache_dir / "sync_versions.json"
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"specs": 0, "profiles": 0}

    def _save_local_versions(self, versions: Dict[str, int]):
        """Save version numbers to local cache"""
        version_file = self.cache_dir / "sync_versions.json"
        try:
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(versions, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save local versions: {e}")

    def needs_sync(self) -> bool:
        """Check if local cache is outdated"""
        server_versions = self.get_server_versions()
        if not server_versions:
            return False

        local_versions = self.get_local_versions()
        return server_versions != local_versions

    # ========================================
    # Sync: Server → Local JSON Cache
    # ========================================

    def sync(self) -> Tuple[bool, str]:
        """
        Full sync: download server data → save as local JSON cache.
        Returns (success, message).
        """
        if not self.is_connected:
            return False, "서버에 연결되지 않았습니다"

        try:
            server_versions = self.get_server_versions()
            if not server_versions:
                return False, "서버 버전 정보를 가져올 수 없습니다"

            local_versions = self.get_local_versions()

            synced_items = []

            # Sync specs (common_base)
            if server_versions.get('specs', 0) != local_versions.get('specs', 0):
                count = self._sync_common_base()
                synced_items.append(f"Common Base ({count} items)")

            # Sync profiles
            if server_versions.get('profiles', 0) != local_versions.get('profiles', 0):
                count = self._sync_profiles()
                synced_items.append(f"Profiles ({count}개)")

            # Save versions
            self._save_local_versions(server_versions)

            if synced_items:
                msg = "동기화 완료: " + ", ".join(synced_items)
            else:
                msg = "이미 최신 상태입니다"

            logger.info(msg)
            return True, msg

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return False, f"동기화 실패: {e}"

    def _sync_common_base(self) -> int:
        """Download specs from server → save as common_base.json"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT module, part_type, part_name, item_name,
                   validation_type, min_spec, max_spec,
                   expected_value, unit, enabled, description
            FROM specs
            ORDER BY module, part_type, part_name, item_name
        """)

        specs = {}
        count = 0
        for row in cursor.fetchall():
            module, part_type, part_name, item_name = row[0], row[1], row[2], row[3]
            validation_type = row[4]
            min_spec, max_spec = row[5], row[6]
            expected_value = row[7]
            unit, enabled, description = row[8], row[9], row[10]

            if module not in specs:
                specs[module] = {}
            if part_type not in specs[module]:
                specs[module][part_type] = {}
            if part_name not in specs[module][part_type]:
                specs[module][part_type][part_name] = []

            item = {
                'item_name': item_name,
                'validation_type': validation_type,
                'enabled': enabled
            }
            if min_spec is not None:
                item['min_spec'] = min_spec
            if max_spec is not None:
                item['max_spec'] = max_spec
            if expected_value:
                item['expected_value'] = expected_value
            if unit:
                item['unit'] = unit
            if description:
                item['description'] = description

            specs[module][part_type][part_name].append(item)
            count += 1

        cursor.close()

        # Save as common_base.json
        data = {
            '_version': '2.0',
            '_description': '모든 장비 공통 QC 항목 (서버 동기화)',
            'specs': specs
        }
        base_file = self.cache_dir / "common_base.json"
        with open(base_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Synced common_base: {count} items")
        return count

    def _sync_profiles(self) -> int:
        """Download profiles from server → save as profiles/*.json"""
        cursor = self.conn.cursor()

        # Get all profiles
        cursor.execute("SELECT id, profile_name, description, inherits_from FROM profiles")
        profiles = cursor.fetchall()

        profiles_dir = self.cache_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

        # Remove old profile files that no longer exist on server
        server_names = {row[1] for row in profiles}
        for existing_file in profiles_dir.glob("*.json"):
            if existing_file.stem not in server_names:
                existing_file.unlink()
                logger.info(f"Removed obsolete profile: {existing_file.stem}")

        for profile_id, profile_name, description, inherits_from in profiles:
            profile_data = {
                '_version': '2.0',
                '_description': description or profile_name,
                'inherits_from': inherits_from or 'Common_Base',
                'excluded_items': [],
                'overrides': {},
                'additional_checks': {}
            }

            # Excluded items
            cursor.execute(
                "SELECT pattern FROM profile_excluded_items WHERE profile_id = %s",
                (profile_id,)
            )
            profile_data['excluded_items'] = [row[0] for row in cursor.fetchall()]

            # Overrides
            profile_data['overrides'] = self._fetch_spec_items(
                cursor, 'profile_overrides', profile_id
            )

            # Additional checks
            profile_data['additional_checks'] = self._fetch_spec_items(
                cursor, 'profile_additional_checks', profile_id
            )

            # Save profile file
            profile_file = profiles_dir / f"{profile_name}.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)

        cursor.close()
        logger.info(f"Synced {len(profiles)} profiles")
        return len(profiles)

    # Allowed table names for _fetch_spec_items — prevents SQL injection via
    # table_name interpolation (psycopg2 cannot parameterize identifiers).
    _ALLOWED_SPEC_TABLES = frozenset({
        'profile_overrides',
        'profile_additional_checks',
    })

    def _fetch_spec_items(self, cursor, table_name: str, profile_id: int) -> Dict:
        """Fetch spec items from a profile table and structure as nested dict"""
        if table_name not in self._ALLOWED_SPEC_TABLES:
            raise ValueError(f"Invalid table name: {table_name!r}")

        cursor.execute(f"""
            SELECT module, part_type, part_name, item_name,
                   validation_type, min_spec, max_spec,
                   expected_value, unit, enabled, description
            FROM {table_name}
            WHERE profile_id = %s
            ORDER BY module, part_type, part_name, item_name
        """, (profile_id,))

        result = {}
        for row in cursor.fetchall():
            module, part_type, part_name, item_name = row[0], row[1], row[2], row[3]
            validation_type = row[4]
            min_spec, max_spec = row[5], row[6]
            expected_value = row[7]
            unit, enabled, description = row[8], row[9], row[10]

            if module not in result:
                result[module] = {}
            if part_type not in result[module]:
                result[module][part_type] = {}
            if part_name not in result[module][part_type]:
                result[module][part_type][part_name] = []

            item = {
                'item_name': item_name,
                'validation_type': validation_type,
                'enabled': enabled
            }
            if min_spec is not None:
                item['min_spec'] = min_spec
            if max_spec is not None:
                item['max_spec'] = max_spec
            if expected_value:
                item['expected_value'] = expected_value
            if unit:
                item['unit'] = unit
            if description:
                item['description'] = description

            result[module][part_type][part_name].append(item)

        return result

    # ========================================
    # Cache Management
    # ========================================

    def has_local_cache(self) -> bool:
        """Check if local cache has data"""
        base_file = self.cache_dir / "common_base.json"
        return base_file.exists()

    def get_cache_dir(self) -> Path:
        """Get the cache directory path"""
        return self.cache_dir

    # ========================================
    # Checklist Mappings Sync
    # ========================================

    def sync_checklist_mappings(self, model: str) -> Tuple[bool, str]:
        """Download checklist mappings for model from server → local JSON cache.
        Falls back to existing local cache if server is unreachable.
        """
        if not self.is_connected:
            cached = self._load_local_mappings(model)
            if cached:
                return True, f"오프라인 캐시 사용 ({len(cached)}개)"
            return False, "서버 미연결, 로컬 캐시 없음"

        try:
            from .server_db_manager import ServerDBManager
            db = ServerDBManager(self.conn)
            rows = db.fetch_checklist_mappings(model)
            # Convert Decimal confidence to float for JSON serialization
            for row in rows:
                if 'confidence' in row and row['confidence'] is not None:
                    row['confidence'] = float(row['confidence'])
                if 'verified_at' in row and row['verified_at'] is not None:
                    row['verified_at'] = row['verified_at'].isoformat()
            self._save_local_mappings(model, rows)
            logger.info(f"Synced checklist_mappings for '{model}': {len(rows)} rows")
            return True, f"동기화 완료 ({len(rows)}개)"
        except Exception as e:
            logger.error(f"sync_checklist_mappings failed: {e}")
            cached = self._load_local_mappings(model)
            if cached:
                return True, f"오류로 캐시 폴백 ({len(cached)}개)"
            return False, f"동기화 실패: {e}"

    def _load_local_mappings(self, model: str) -> list:
        """Load cached checklist mappings for model from local JSON"""
        cache_file = self._mapping_cache_path(model)
        if not cache_file.exists():
            return []
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load local mappings for '{model}': {e}")
            return []

    def _save_local_mappings(self, model: str, data: list):
        """Save checklist mappings for model to local JSON cache"""
        cache_file = self._mapping_cache_path(model)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error(f"Failed to save local mappings for '{model}': {e}")

    def _mapping_cache_path(self, model: str) -> Path:
        """Return local cache path for a model's checklist mappings"""
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in model)
        return self.cache_dir / f"checklist_mappings_{safe_name}.json"
