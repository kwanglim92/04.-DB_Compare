"""
Server DB Manager Module
Direct CRUD operations on the server PostgreSQL database
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

# Allowed table names for queries — prevents SQL injection
_ALLOWED_TABLES = frozenset({
    'specs', 'profiles', 'profile_overrides',
    'profile_additional_checks', 'profile_excluded_items',
})


class ServerDBManager:
    """Direct CRUD operations on server PostgreSQL"""

    def __init__(self, conn):
        self.conn = conn

    # ========================================
    # Transaction helper
    # ========================================

    def _execute_with_bump(self, version_target: str,
                           queries: List[Tuple[str, tuple]]) -> bool:
        """Execute queries + bump_version in a single transaction"""
        try:
            cursor = self.conn.cursor()
            for sql, params in queries:
                cursor.execute(sql, params)
            cursor.execute("SELECT bump_version(%s)", (version_target,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Transaction failed: {e}")
            return False

    # ========================================
    # Common Base (specs table)
    # ========================================

    def get_all_specs(self) -> List[Dict]:
        """Get all Common Base spec items"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, module, part_type, part_name, item_name,
                   validation_type, min_spec, max_spec,
                   expected_value, unit, enabled, description
            FROM specs
            ORDER BY module, part_type, part_name, item_name
        """)
        rows = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return rows

    def add_spec(self, spec: Dict) -> Optional[int]:
        """Add a spec item to Common Base. Returns new id or None."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO specs (module, part_type, part_name, item_name,
                                   validation_type, min_spec, max_spec,
                                   expected_value, unit, enabled, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                spec['module'], spec['part_type'], spec['part_name'],
                spec['item_name'], spec.get('validation_type', 'range'),
                spec.get('min_spec'), spec.get('max_spec'),
                spec.get('expected_value'), spec.get('unit', ''),
                spec.get('enabled', True), spec.get('description', '')
            ))
            new_id = cursor.fetchone()[0]
            cursor.execute("SELECT bump_version('specs')")
            self.conn.commit()
            cursor.close()
            logger.info(f"Added spec: {spec['module']}.{spec['part_type']}.{spec['part_name']}.{spec['item_name']}")
            return new_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to add spec: {e}")
            return None

    def update_spec(self, spec_id: int, spec: Dict) -> bool:
        """Update a Common Base spec item"""
        return self._execute_with_bump('specs', [(
            """UPDATE specs SET module=%s, part_type=%s, part_name=%s,
               item_name=%s, validation_type=%s, min_spec=%s, max_spec=%s,
               expected_value=%s, unit=%s, enabled=%s, description=%s
               WHERE id=%s""",
            (spec['module'], spec['part_type'], spec['part_name'],
             spec['item_name'], spec.get('validation_type', 'range'),
             spec.get('min_spec'), spec.get('max_spec'),
             spec.get('expected_value'), spec.get('unit', ''),
             spec.get('enabled', True), spec.get('description', ''),
             spec_id)
        )])

    def delete_spec(self, spec_id: int) -> bool:
        """Delete a Common Base spec item"""
        return self._execute_with_bump('specs', [(
            "DELETE FROM specs WHERE id=%s", (spec_id,)
        )])

    def delete_specs_batch(self, spec_ids: List[int]) -> bool:
        """Delete multiple spec items at once"""
        if not spec_ids:
            return True
        queries = [("DELETE FROM specs WHERE id=%s", (sid,)) for sid in spec_ids]
        return self._execute_with_bump('specs', queries)

    # ========================================
    # Profiles
    # ========================================

    def get_all_profiles(self) -> List[Dict]:
        """Get all equipment profiles"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, profile_name, description, inherits_from
            FROM profiles ORDER BY profile_name
        """)
        rows = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return rows

    def create_profile(self, profile_name: str, description: str = '',
                       inherits_from: str = 'common_base') -> Optional[int]:
        """Create a new profile. Returns new id or None."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO profiles (profile_name, description, inherits_from)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (profile_name, description, inherits_from))
            new_id = cursor.fetchone()[0]
            cursor.execute("SELECT bump_version('profiles')")
            self.conn.commit()
            cursor.close()
            logger.info(f"Created profile: {profile_name}")
            return new_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create profile: {e}")
            return None

    def rename_profile(self, profile_id: int, new_name: str) -> bool:
        """Rename an existing profile"""
        return self._execute_with_bump('profiles', [(
            "UPDATE profiles SET profile_name=%s WHERE id=%s",
            (new_name, profile_id)
        )])

    def delete_profile(self, profile_id: int) -> bool:
        """Delete a profile and all its related data (CASCADE)"""
        return self._execute_with_bump('profiles', [(
            "DELETE FROM profiles WHERE id=%s", (profile_id,)
        )])

    # ========================================
    # Profile Additional Checks
    # ========================================

    def get_profile_additional_checks(self, profile_id: int) -> List[Dict]:
        """Get additional check items for a profile"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, module, part_type, part_name, item_name,
                   validation_type, min_spec, max_spec,
                   expected_value, unit, enabled, description
            FROM profile_additional_checks
            WHERE profile_id = %s
            ORDER BY module, part_type, part_name, item_name
        """, (profile_id,))
        rows = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return rows

    def add_additional_check(self, profile_id: int, spec: Dict) -> Optional[int]:
        """Add an additional check item to a profile"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO profile_additional_checks
                    (profile_id, module, part_type, part_name, item_name,
                     validation_type, min_spec, max_spec,
                     expected_value, unit, enabled, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                profile_id,
                spec['module'], spec['part_type'], spec['part_name'],
                spec['item_name'], spec.get('validation_type', 'range'),
                spec.get('min_spec'), spec.get('max_spec'),
                spec.get('expected_value'), spec.get('unit', ''),
                spec.get('enabled', True), spec.get('description', '')
            ))
            new_id = cursor.fetchone()[0]
            cursor.execute("SELECT bump_version('profiles')")
            self.conn.commit()
            cursor.close()
            return new_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to add additional check: {e}")
            return None

    def update_additional_check(self, check_id: int, spec: Dict) -> bool:
        """Update an additional check item"""
        return self._execute_with_bump('profiles', [(
            """UPDATE profile_additional_checks
               SET module=%s, part_type=%s, part_name=%s,
                   item_name=%s, validation_type=%s, min_spec=%s, max_spec=%s,
                   expected_value=%s, unit=%s, enabled=%s, description=%s
               WHERE id=%s""",
            (spec['module'], spec['part_type'], spec['part_name'],
             spec['item_name'], spec.get('validation_type', 'range'),
             spec.get('min_spec'), spec.get('max_spec'),
             spec.get('expected_value'), spec.get('unit', ''),
             spec.get('enabled', True), spec.get('description', ''),
             check_id)
        )])

    def delete_additional_check(self, check_id: int) -> bool:
        """Delete an additional check item"""
        return self._execute_with_bump('profiles', [(
            "DELETE FROM profile_additional_checks WHERE id=%s", (check_id,)
        )])

    def delete_additional_checks_batch(self, check_ids: List[int]) -> bool:
        """Delete multiple additional check items"""
        if not check_ids:
            return True
        queries = [("DELETE FROM profile_additional_checks WHERE id=%s", (cid,))
                    for cid in check_ids]
        return self._execute_with_bump('profiles', queries)

    # ========================================
    # Bulk import (F2)
    # ========================================

    def bulk_add_specs(self, profile_id: Optional[int],
                       items: List[Dict],
                       conflict_strategy: str = 'skip') -> Dict:
        """Bulk add specs to Common Base or to a profile (additional checks).

        Single-transaction insert/update with conflict handling.

        Args:
            profile_id: None ⇒ Common Base; int ⇒ profile additional checks
            items: list of spec dicts (module, part_type, part_name, item_name +
                   optional validation_type, min_spec, max_spec, expected_value,
                   unit, enabled, description)
            conflict_strategy: 'skip' (keep existing) | 'update' (overwrite existing)
                               | 'abort' (rollback if any conflict)

        Returns:
            dict with keys: added, updated, skipped, errors
        """
        result = {'added': 0, 'updated': 0, 'skipped': 0, 'errors': []}

        if conflict_strategy not in ('skip', 'update', 'abort'):
            result['errors'].append(f"Invalid conflict_strategy: {conflict_strategy}")
            return result

        if not items:
            return result

        # Choose target table + version target
        is_common_base = (profile_id is None)
        version_target = 'specs' if is_common_base else 'profiles'

        # Fetch existing keys for conflict detection
        try:
            cursor = self.conn.cursor()
            if is_common_base:
                cursor.execute("""
                    SELECT id, module, part_type, part_name, item_name FROM specs
                """)
            else:
                cursor.execute("""
                    SELECT id, module, part_type, part_name, item_name
                    FROM profile_additional_checks WHERE profile_id=%s
                """, (profile_id,))
            existing = {(r[1], r[2], r[3], r[4]): r[0] for r in cursor.fetchall()}
            cursor.close()
        except Exception as e:
            self.conn.rollback()
            result['errors'].append(f"Failed to read existing keys: {e}")
            return result

        # Single transaction
        try:
            cursor = self.conn.cursor()
            for spec in items:
                key = (spec.get('module'), spec.get('part_type'),
                       spec.get('part_name'), spec.get('item_name'))
                if not all(key):
                    result['errors'].append(f"Skipping incomplete item: {spec}")
                    result['skipped'] += 1
                    continue

                params_common = (
                    spec.get('validation_type', 'range'),
                    spec.get('min_spec'), spec.get('max_spec'),
                    spec.get('expected_value'), spec.get('unit', ''),
                    spec.get('enabled', True), spec.get('description', '')
                )

                if key in existing:
                    if conflict_strategy == 'abort':
                        raise ValueError(
                            f"Conflict (abort policy): {'.'.join(key)}")
                    elif conflict_strategy == 'skip':
                        result['skipped'] += 1
                        continue
                    elif conflict_strategy == 'update':
                        existing_id = existing[key]
                        if is_common_base:
                            cursor.execute("""
                                UPDATE specs SET validation_type=%s, min_spec=%s,
                                    max_spec=%s, expected_value=%s, unit=%s,
                                    enabled=%s, description=%s WHERE id=%s
                            """, params_common + (existing_id,))
                        else:
                            cursor.execute("""
                                UPDATE profile_additional_checks
                                SET validation_type=%s, min_spec=%s, max_spec=%s,
                                    expected_value=%s, unit=%s, enabled=%s,
                                    description=%s WHERE id=%s
                            """, params_common + (existing_id,))
                        result['updated'] += 1
                else:
                    if is_common_base:
                        cursor.execute("""
                            INSERT INTO specs
                                (module, part_type, part_name, item_name,
                                 validation_type, min_spec, max_spec,
                                 expected_value, unit, enabled, description)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, key + params_common)
                    else:
                        cursor.execute("""
                            INSERT INTO profile_additional_checks
                                (profile_id, module, part_type, part_name,
                                 item_name, validation_type, min_spec, max_spec,
                                 expected_value, unit, enabled, description)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (profile_id,) + key + params_common)
                    result['added'] += 1

            # Bump version once for the whole batch
            cursor.execute("SELECT bump_version(%s)", (version_target,))
            self.conn.commit()
            cursor.close()
            logger.info(
                f"bulk_add_specs ({'common_base' if is_common_base else f'profile {profile_id}'}): "
                f"+{result['added']} ~{result['updated']} skip{result['skipped']}")
        except ValueError as e:
            # abort path
            self.conn.rollback()
            result['errors'].append(str(e))
            # On abort, zero out partial counters since transaction rolled back
            result['added'] = 0
            result['updated'] = 0
        except Exception as e:
            self.conn.rollback()
            logger.error(f"bulk_add_specs failed: {e}")
            result['errors'].append(str(e))
            result['added'] = 0
            result['updated'] = 0

        return result

    # ========================================
    # Profile Overrides
    # ========================================

    def get_profile_overrides(self, profile_id: int) -> List[Dict]:
        """Get override items for a profile"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, module, part_type, part_name, item_name,
                   validation_type, min_spec, max_spec,
                   expected_value, unit, enabled, description
            FROM profile_overrides
            WHERE profile_id = %s
            ORDER BY module, part_type, part_name, item_name
        """, (profile_id,))
        rows = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return rows

    # ========================================
    # Profile Excluded Items
    # ========================================

    def get_profile_excluded_items(self, profile_id: int) -> List[Dict]:
        """Get excluded item patterns for a profile"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, pattern
            FROM profile_excluded_items
            WHERE profile_id = %s
            ORDER BY pattern
        """, (profile_id,))
        rows = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return rows

    def add_excluded_item(self, profile_id: int, pattern: str) -> Optional[int]:
        """Add an exclusion pattern to a profile"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO profile_excluded_items (profile_id, pattern)
                VALUES (%s, %s)
                ON CONFLICT (profile_id, pattern) DO NOTHING
                RETURNING id
            """, (profile_id, pattern))
            result = cursor.fetchone()
            new_id = result[0] if result else None
            cursor.execute("SELECT bump_version('profiles')")
            self.conn.commit()
            cursor.close()
            return new_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to add excluded item: {e}")
            return None

    def delete_excluded_item(self, excluded_id: int) -> bool:
        """Delete an exclusion pattern"""
        return self._execute_with_bump('profiles', [(
            "DELETE FROM profile_excluded_items WHERE id=%s", (excluded_id,)
        )])

    # ========================================
    # Import / Export
    # ========================================

    def export_profile_data(self, profile_id: int, profile_name: str) -> Dict:
        """Export a profile's full data as a dict (compatible with PM format)"""
        additional = self.get_profile_additional_checks(profile_id)
        excluded = self.get_profile_excluded_items(profile_id)
        overrides = self.get_profile_overrides(profile_id)

        # Build profile_data in PM-compatible structure
        additional_checks = {}
        for row in additional:
            mod = row['module']
            pt = row['part_type']
            pn = row['part_name']
            item = {
                'item_name': row['item_name'],
                'validation_type': row['validation_type'],
                'unit': row.get('unit', ''),
                'enabled': row.get('enabled', True),
                'description': row.get('description', ''),
            }
            if row['validation_type'] == 'range':
                item['min_spec'] = row.get('min_spec')
                item['max_spec'] = row.get('max_spec')
            elif row['validation_type'] == 'exact':
                item['expected_value'] = row.get('expected_value')
            additional_checks.setdefault(mod, {}).setdefault(pt, {}).setdefault(pn, []).append(item)

        profile_data = {
            'inherits_from': 'common_base',
            'additional_checks': additional_checks,
            'excluded_items': [e['pattern'] for e in excluded],
        }

        if overrides:
            override_dict = {}
            for row in overrides:
                mod = row['module']
                pt = row['part_type']
                pn = row['part_name']
                item = {
                    'item_name': row['item_name'],
                    'validation_type': row['validation_type'],
                    'unit': row.get('unit', ''),
                    'enabled': row.get('enabled', True),
                }
                if row['validation_type'] == 'range':
                    item['min_spec'] = row.get('min_spec')
                    item['max_spec'] = row.get('max_spec')
                elif row['validation_type'] == 'exact':
                    item['expected_value'] = row.get('expected_value')
                override_dict.setdefault(mod, {}).setdefault(pt, {}).setdefault(pn, []).append(item)
            profile_data['overrides'] = override_dict

        return {
            'version': '1.0',
            'source': 'server_db',
            'profile_name': profile_name,
            'profile_data': profile_data,
        }

    def import_profile_data(self, profile_id: int, profile_data: Dict) -> bool:
        """Import profile data from PM-compatible dict. Replaces all additional_checks."""
        try:
            cursor = self.conn.cursor()
            # Clear existing additional checks
            cursor.execute(
                "DELETE FROM profile_additional_checks WHERE profile_id=%s",
                (profile_id,))

            # Insert new additional checks
            ac = profile_data.get('additional_checks', {})
            for mod, pt_data in ac.items():
                for pt, pn_data in pt_data.items():
                    for pn, items in pn_data.items():
                        for item in items:
                            cursor.execute("""
                                INSERT INTO profile_additional_checks
                                    (profile_id, module, part_type, part_name, item_name,
                                     validation_type, min_spec, max_spec,
                                     expected_value, unit, enabled, description)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """, (
                                profile_id, mod, pt, pn,
                                item.get('item_name', ''),
                                item.get('validation_type', 'range'),
                                item.get('min_spec'), item.get('max_spec'),
                                item.get('expected_value'), item.get('unit', ''),
                                item.get('enabled', True), item.get('description', '')
                            ))

            cursor.execute("SELECT bump_version('profiles')")
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to import profile data: {e}")
            return False

    # ========================================
    # Sync version info
    # ========================================

    def get_sync_versions(self) -> Dict[str, int]:
        """Get current sync version numbers"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT table_name, version FROM sync_versions")
        versions = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.close()
        return versions
