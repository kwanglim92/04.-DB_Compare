"""
Configuration Cleanup Script
Migrates 'enabled: false' items to 'excluded_items' list to keep config files clean.

Run this script to clean up existing profiles.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_profile(profile_path: Path):
    """
    Clean up a single profile:
    1. Find overrides where enabled: false
    2. Move them to excluded_items
    3. Remove from overrides
    """
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        overrides = data.get('overrides', {})
        excluded_items = data.get('excluded_items', [])
        
        # Track deletions
        items_to_remove = []
        
        # Scan overrides
        for module, module_data in overrides.items():
            for part_type, type_data in module_data.items():
                for part_name, items in type_data.items():
                    # We need to modify list, so iterate carefully
                    for item in items:
                        if not item.get('enabled', True):
                            item_name = item.get('item_name')
                            # Create exclusion path
                            item_path = f"{module}.{part_type}.{part_name}.{item_name}"
                            if item_path not in excluded_items:
                                excluded_items.append(item_path)
                                items_to_remove.append((module, part_type, part_name, item_name))
                                logger.info(f"Marked for exclusion: {item_path}")

        if not items_to_remove:
            logger.info(f"No items to clean up in {profile_path.name}")
            return False
            
        # Remove items from overrides
        for module, part_type, part_name, item_name in items_to_remove:
            items = overrides[module][part_type][part_name]
            # Filter out the item
            overrides[module][part_type][part_name] = [
                item for item in items 
                if item.get('item_name') != item_name
            ]
            
            # Clean up empty structures (optional, but good for cleanliness)
            if not overrides[module][part_type][part_name]:
                del overrides[module][part_type][part_name]
                if not overrides[module][part_type]:
                    del overrides[module][part_type]
                    if not overrides[module]:
                        del overrides[module]
        
        # Update data
        data['excluded_items'] = excluded_items
        data['overrides'] = overrides
        data['_cleaned_at'] = datetime.now().isoformat()
        
        # Save back
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Cleaned up {len(items_to_remove)} items in {profile_path.name}")
        return True

    except Exception as e:
        logger.error(f"Failed to cleanup {profile_path}: {e}")
        return False


def main():
    from src.utils.config_helper import get_config_dir
    config_dir = get_config_dir()
    profiles_dir = config_dir / "profiles"
    backup_dir = config_dir / "backup"
    
    if not profiles_dir.exists():
        print("Profiles directory not found!")
        return
        
    # Backup first
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"profiles_pre_cleanup_{timestamp}"
    shutil.copytree(profiles_dir, backup_path)
    print(f"Backed up profiles to {backup_path}")
    
    # Process all profiles
    count = 0
    for profile_file in profiles_dir.glob("*.json"):
        if cleanup_profile(profile_file):
            count += 1
            
    print(f"\n✅ Cleanup complete! {count} profiles updated.")

if __name__ == "__main__":
    main()
