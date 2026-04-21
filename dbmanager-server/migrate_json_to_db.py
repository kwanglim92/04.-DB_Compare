#!/usr/bin/env python3
"""
JSON → PostgreSQL Migration Script
Migrates common_base.json and profiles/*.json into the dbmanager database.

Usage:
    python migrate_json_to_db.py --host localhost --port 5434 --db dbmanager --user dbmanager --password <pw> --config-dir ../config
"""

import json
import argparse
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary")
    exit(1)


def get_connection(args):
    """Create database connection"""
    return psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.db,
        user=args.user,
        password=args.password
    )


def migrate_common_base(cursor, config_dir: Path):
    """Migrate common_base.json → specs table"""
    base_file = config_dir / "common_base.json"
    if not base_file.exists():
        print(f"  [SKIP] {base_file} not found")
        return 0

    with open(base_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    specs = data.get('specs', {})
    count = 0

    for module, module_data in specs.items():
        for part_type, type_data in module_data.items():
            for part_name, items in type_data.items():
                for item in items:
                    cursor.execute("""
                        INSERT INTO specs (module, part_type, part_name, item_name,
                                          validation_type, min_spec, max_spec,
                                          expected_value, unit, enabled, description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (module, part_type, part_name, item_name)
                        DO UPDATE SET
                            validation_type = EXCLUDED.validation_type,
                            min_spec = EXCLUDED.min_spec,
                            max_spec = EXCLUDED.max_spec,
                            expected_value = EXCLUDED.expected_value,
                            unit = EXCLUDED.unit,
                            enabled = EXCLUDED.enabled,
                            description = EXCLUDED.description
                    """, (
                        module, part_type, part_name,
                        item.get('item_name', ''),
                        item.get('validation_type', 'range'),
                        item.get('min_spec'),
                        item.get('max_spec'),
                        item.get('expected_value'),
                        item.get('unit', ''),
                        item.get('enabled', True),
                        item.get('description', '')
                    ))
                    count += 1

    print(f"  [OK] Common Base: {count} spec items migrated")
    return count


def migrate_profile(cursor, profile_name: str, profile_data: dict):
    """Migrate a single equipment profile"""
    # Insert profile metadata
    cursor.execute("""
        INSERT INTO profiles (profile_name, description, inherits_from)
        VALUES (%s, %s, %s)
        ON CONFLICT (profile_name) DO UPDATE SET
            description = EXCLUDED.description,
            inherits_from = EXCLUDED.inherits_from
        RETURNING id
    """, (
        profile_name,
        profile_data.get('_description', profile_name),
        profile_data.get('inherits_from', 'Common_Base')
    ))
    profile_id = cursor.fetchone()[0]

    # Migrate excluded_items
    excluded_count = 0
    for pattern in profile_data.get('excluded_items', []):
        cursor.execute("""
            INSERT INTO profile_excluded_items (profile_id, pattern)
            VALUES (%s, %s)
            ON CONFLICT (profile_id, pattern) DO NOTHING
        """, (profile_id, pattern))
        excluded_count += 1

    # Migrate overrides
    override_count = _migrate_spec_items(
        cursor, profile_id, 'profile_overrides',
        profile_data.get('overrides', {})
    )

    # Migrate additional_checks
    additional_count = _migrate_spec_items(
        cursor, profile_id, 'profile_additional_checks',
        profile_data.get('additional_checks', {})
    )

    print(f"  [OK] {profile_name}: {excluded_count} excluded, "
          f"{override_count} overrides, {additional_count} additional checks")
    return profile_id


def _migrate_spec_items(cursor, profile_id: int, table_name: str, specs: dict):
    """Migrate spec items into overrides or additional_checks table"""
    count = 0
    for module, module_data in specs.items():
        for part_type, type_data in module_data.items():
            for part_name, items in type_data.items():
                for item in items:
                    cursor.execute(f"""
                        INSERT INTO {table_name}
                            (profile_id, module, part_type, part_name, item_name,
                             validation_type, min_spec, max_spec,
                             expected_value, unit, enabled, description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (profile_id, module, part_type, part_name, item_name)
                        DO UPDATE SET
                            validation_type = EXCLUDED.validation_type,
                            min_spec = EXCLUDED.min_spec,
                            max_spec = EXCLUDED.max_spec,
                            expected_value = EXCLUDED.expected_value,
                            unit = EXCLUDED.unit,
                            enabled = EXCLUDED.enabled,
                            description = EXCLUDED.description
                    """, (
                        profile_id, module, part_type, part_name,
                        item.get('item_name', ''),
                        item.get('validation_type', 'range'),
                        item.get('min_spec'),
                        item.get('max_spec'),
                        item.get('expected_value'),
                        item.get('unit', ''),
                        item.get('enabled', True),
                        item.get('description', '')
                    ))
                    count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description='Migrate JSON config to PostgreSQL')
    parser.add_argument('--host', default='localhost', help='DB host')
    parser.add_argument('--port', type=int, default=5434, help='DB port')
    parser.add_argument('--db', default='dbmanager', help='DB name')
    parser.add_argument('--user', default='dbmanager', help='DB user')
    parser.add_argument('--password', required=True, help='DB password')
    parser.add_argument('--config-dir', default='../config', help='Path to config directory')
    args = parser.parse_args()

    config_dir = Path(args.config_dir)
    if not config_dir.exists():
        print(f"Error: Config directory not found: {config_dir}")
        return

    print(f"Connecting to {args.host}:{args.port}/{args.db}...")
    conn = get_connection(args)

    try:
        cursor = conn.cursor()

        # 1. Migrate common_base
        print("\n[1/3] Migrating Common Base specs...")
        migrate_common_base(cursor, config_dir)

        # 2. Migrate equipment profiles
        print("\n[2/3] Migrating Equipment Profiles...")
        profiles_dir = config_dir / "profiles"
        if profiles_dir.exists():
            for profile_file in sorted(profiles_dir.glob("*.json")):
                profile_name = profile_file.stem
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                migrate_profile(cursor, profile_name, profile_data)
        else:
            print("  [SKIP] No profiles directory found")

        # 3. Reset version counters
        print("\n[3/3] Resetting sync versions...")
        cursor.execute("UPDATE sync_versions SET version = 1, updated_at = NOW()")
        print("  [OK] Versions reset to 1")

        conn.commit()
        print("\n=== Migration complete ===")

    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
