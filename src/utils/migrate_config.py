"""
Config Migration Script
Migrates from legacy qc_specs.json to new multi-file structure

Run this script once to convert existing config.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_config(config_dir: Path) -> bool:
    """
    Migrate from legacy qc_specs.json to new structure:
    - config/common_base.json
    - config/profiles/*.json
    
    Args:
        config_dir: Path to config directory
        
    Returns:
        True if migration successful or not needed
    """
    old_file = config_dir / "qc_specs.json"
    profiles_dir = config_dir / "profiles"
    backup_dir = config_dir / "backup"
    
    # Check if migration needed
    if not old_file.exists():
        logger.info("No legacy qc_specs.json found, migration not needed")
        return True
    
    # Check if already migrated (profiles dir has files)
    if profiles_dir.exists() and list(profiles_dir.glob("*.json")):
        logger.info("Already migrated (profiles exist), skipping")
        return True
    
    logger.info("Starting migration from qc_specs.json...")
    
    try:
        # Create directories
        profiles_dir.mkdir(exist_ok=True)
        backup_dir.mkdir(exist_ok=True)
        
        # Load old file
        with open(old_file, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        
        # Extract base profiles
        base_profiles = old_data.get('base_profiles', {})
        
        if 'Common_Base' in base_profiles:
            base_profile = base_profiles['Common_Base']
            new_base = {
                '_version': '2.0',
                '_description': base_profile.get('description', 'Common Base Profile'),
                '_migrated_from': 'qc_specs.json',
                '_migrated_at': datetime.now().isoformat(),
                'specs': base_profile.get('specs', {})
            }
            
            base_file = config_dir / "common_base.json"
            with open(base_file, 'w', encoding='utf-8') as f:
                json.dump(new_base, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created common_base.json")
        
        # Extract equipment profiles
        equipment_profiles = old_data.get('equipment_profiles', {})
        
        for name, profile in equipment_profiles.items():
            new_profile = {
                '_version': '2.0',
                '_description': profile.get('description', name),
                '_migrated_from': 'qc_specs.json',
                '_migrated_at': datetime.now().isoformat(),
                'inherits_from': profile.get('inherits_from', 'Common_Base'),
                'overrides': profile.get('overrides', {}),
                'additional_checks': profile.get('additional_checks', {})
            }
            
            # Sanitize filename (replace spaces with underscores)
            safe_name = name.replace(' ', '_')
            profile_file = profiles_dir / f"{safe_name}.json"
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(new_profile, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created profile: {safe_name}.json")
        
        # Backup old file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"qc_specs_{timestamp}.json"
        shutil.copy(old_file, backup_file)
        logger.info(f"Backed up to {backup_file}")
        
        # Optionally remove old file (or rename)
        old_file.rename(config_dir / "qc_specs_legacy.json")
        logger.info("Renamed qc_specs.json to qc_specs_legacy.json")
        
        logger.info("=" * 50)
        logger.info("Migration complete!")
        logger.info(f"  Base profile: common_base.json")
        logger.info(f"  Equipment profiles: {len(equipment_profiles)} files in profiles/")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def main():
    """Run migration for the default config directory"""
    from src.utils.config_helper import get_config_dir
    
    config_dir = get_config_dir()
    print(f"Config directory: {config_dir}")
    
    if not config_dir.exists():
        print("Config directory not found!")
        return
    
    success = migrate_config(config_dir)
    
    if success:
        print("\n✅ Migration successful!")
    else:
        print("\n❌ Migration failed!")


if __name__ == "__main__":
    main()
