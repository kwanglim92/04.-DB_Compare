"""
Spec Manager Module
Manages QC specification profiles with inheritance support
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


class SpecManager:
    """
    Manages QC specification profiles with Base + Equipment profile inheritance
    
    Supports two modes:
    1. Legacy: Single qc_specs.json file
    2. New: common_base.json + profiles/ directory
    """
    
    def __init__(self):
        self.base_profiles = {}
        self.equipment_profiles = {}
        self.config_dir = None
        self.use_multi_file = False
        self.logger = logger
    
    def load_spec_file(self, json_path: str) -> bool:
        """
        Load spec profiles from JSON file
        
        Args:
            json_path: Path to JSON spec file
            
        Returns:
            True if successful, False otherwise
        """
        spec_file = Path(json_path)
        
        if not spec_file.exists():
            self.logger.error(f"Spec file not found: {json_path}")
            return False
        
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.base_profiles = data.get('base_profiles', {})
            self.equipment_profiles = data.get('equipment_profiles', {})
            
            self.logger.info(f"Loaded {len(self.base_profiles)} base profiles")
            self.logger.info(f"Loaded {len(self.equipment_profiles)} equipment profiles")
            
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error loading spec file: {e}")
            return False
    
    def save_spec_file(self, json_path: str) -> bool:
        """
        Save spec profiles to JSON file
        
        Args:
            json_path: Path to JSON spec file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                'base_profiles': self.base_profiles,
                'equipment_profiles': self.equipment_profiles
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved spec file to {json_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving spec file: {e}")
            return False
    
    # ========================================
    # Multi-file Config Methods (New v2.0)
    # ========================================
    
    def load_multi_file_config(self, config_dir: Path) -> bool:
        """
        Load config from multi-file structure:
        - config/common_base.json
        - config/profiles/*.json
        
        Args:
            config_dir: Path to config directory
            
        Returns:
            True if successful
        """
        self.config_dir = Path(config_dir)
        self.use_multi_file = True
        
        try:
            # 1. Load common base
            base_file = self.config_dir / "common_base.json"
            if base_file.exists():
                with open(base_file, 'r', encoding='utf-8') as f:
                    base_data = json.load(f)
                # Store as "Common_Base" for compatibility
                self.base_profiles['Common_Base'] = {
                    'description': base_data.get('_description', 'Common Base Profile'),
                    'specs': base_data.get('specs', {})
                }
                self.logger.info("Loaded common_base.json")
            
            # 2. Load all equipment profiles from profiles/
            profiles_dir = self.config_dir / "profiles"
            if profiles_dir.exists():
                for profile_file in profiles_dir.glob("*.json"):
                    profile_name = profile_file.stem
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                    
                    # Convert to internal format
                    self.equipment_profiles[profile_name] = {
                        'description': profile_data.get('_description', profile_name),
                        'inherits_from': profile_data.get('inherits_from', 'Common_Base'),
                        'excluded_items': profile_data.get('excluded_items', []),
                        'overrides': profile_data.get('overrides', {}),
                        'additional_checks': profile_data.get('additional_checks', {})
                    }
                    self.logger.info(f"Loaded profile: {profile_name}")
            
            self.logger.info(f"Loaded {len(self.base_profiles)} base, {len(self.equipment_profiles)} equipment profiles")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading multi-file config: {e}")
            return False
    
    def save_base_profile(self) -> bool:
        """Save common_base.json"""
        if not self.config_dir or 'Common_Base' not in self.base_profiles:
            return False
        
        try:
            base_file = self.config_dir / "common_base.json"
            base_profile = self.base_profiles['Common_Base']
            
            data = {
                '_version': '2.0',
                '_description': base_profile.get('description', 'Common Base Profile'),
                'specs': base_profile.get('specs', {})
            }
            
            with open(base_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved common_base.json")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving base profile: {e}")
            return False
    
    def get_common_base_specs(self) -> Dict:
        """Get Common_Base specs dictionary directly"""
        if 'Common_Base' in self.base_profiles:
            return deepcopy(self.base_profiles['Common_Base'].get('specs', {}))
        return {}
    
    def add_item_to_common_base(self, module: str, part_type: str,
                                 part_name: str, spec: Dict) -> bool:
        """Add a spec item to Common_Base"""
        try:
            if 'Common_Base' not in self.base_profiles:
                self.base_profiles['Common_Base'] = {'description': 'Common Base Profile', 'specs': {}}
            
            specs = self.base_profiles['Common_Base']['specs']
            
            if module not in specs:
                specs[module] = {}
            if part_type not in specs[module]:
                specs[module][part_type] = {}
            if part_name not in specs[module][part_type]:
                specs[module][part_type][part_name] = []
            
            # Check for duplicate
            items = specs[module][part_type][part_name]
            item_name = spec.get('item_name', '')
            for existing in items:
                if existing.get('item_name') == item_name:
                    # Update existing
                    existing.update(spec)
                    self.logger.info(f"Updated Common_Base item: {module}.{part_type}.{part_name}.{item_name}")
                    return self.save_base_profile()
            
            # Add new
            items.append(spec)
            self.logger.info(f"Added to Common_Base: {module}.{part_type}.{part_name}.{item_name}")
            return self.save_base_profile()
            
        except Exception as e:
            self.logger.error(f"Error adding to Common_Base: {e}")
            return False
    
    def remove_item_from_common_base(self, module: str, part_type: str,
                                      part_name: str, item_name: str) -> bool:
        """Remove a spec item from Common_Base"""
        try:
            if 'Common_Base' not in self.base_profiles:
                return False
            
            specs = self.base_profiles['Common_Base']['specs']
            
            if (module not in specs or part_type not in specs[module] or
                part_name not in specs[module][part_type]):
                return False
            
            items = specs[module][part_type][part_name]
            specs[module][part_type][part_name] = [
                item for item in items if item.get('item_name') != item_name
            ]
            
            # Cleanup empty structures
            if not specs[module][part_type][part_name]:
                del specs[module][part_type][part_name]
            if not specs[module][part_type]:
                del specs[module][part_type]
            if not specs[module]:
                del specs[module]
            
            self.logger.info(f"Removed from Common_Base: {module}.{part_type}.{part_name}.{item_name}")
            return self.save_base_profile()
            
        except Exception as e:
            self.logger.error(f"Error removing from Common_Base: {e}")
            return False
    
    def update_common_base_item(self, module: str, part_type: str,
                                 part_name: str, item_name: str, new_spec: Dict) -> bool:
        """Update an existing spec item in Common_Base"""
        new_spec['item_name'] = item_name
        return self.add_item_to_common_base(module, part_type, part_name, new_spec)
    
    def save_equipment_profile(self, profile_name: str) -> bool:
        """
        Save single equipment profile to profiles/ directory
        
        Args:
            profile_name: Name of the profile to save
        """
        if not self.config_dir or profile_name not in self.equipment_profiles:
            return False
        
        try:
            profiles_dir = self.config_dir / "profiles"
            profiles_dir.mkdir(exist_ok=True)
            
            profile_file = profiles_dir / f"{profile_name}.json"
            profile = self.equipment_profiles[profile_name]
            
            # Auto-cleanup: Move enabled:false items to excluded_items
            self._cleanup_profile_data(profile)
            
            data = {
                '_version': '2.0',
                '_description': profile.get('description', profile_name),
                'inherits_from': profile.get('inherits_from', 'Common_Base'),
                'excluded_items': profile.get('excluded_items', []),
                'overrides': profile.get('overrides', {}),
                'additional_checks': profile.get('additional_checks', {})
            }
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved profile: {profile_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving profile {profile_name}: {e}")
            return False
    
    def save_all_profiles(self) -> bool:
        """Save all profiles (base + equipment)"""
        success = True
        
        # Save base
        if not self.save_base_profile():
            success = False
        
        # Save all equipment profiles
        for profile_name in self.equipment_profiles.keys():
            if not self.save_equipment_profile(profile_name):
                success = False
        
        return success
    
    def get_all_profile_names(self) -> List[str]:
        """
        Get list of all equipment profile names
        
        Returns:
            List of profile names
        """
        return list(self.equipment_profiles.keys())
    
    def load_profile_with_inheritance(self, profile_name: str) -> Optional[Dict]:
        """
        Load equipment profile with inheritance from base profile applied
        
        Process:
        1. Load base profile
        2. Apply overrides
        3. Add additional checks
        
        Args:
            profile_name: Name of equipment profile
            
        Returns:
            Final merged spec dictionary or None if profile not found
        """
        if profile_name not in self.equipment_profiles:
            self.logger.error(f"Equipment profile not found: {profile_name}")
            return None
        
        eq_profile = self.equipment_profiles[profile_name]
        base_name = eq_profile.get('inherits_from')
        
        if not base_name or base_name not in self.base_profiles:
            self.logger.warning(f"Base profile '{base_name}' not found, using equipment profile only")
            return eq_profile.get('additional_checks', {})
        
        # Start with deep copy of base specs
        base_profile = self.base_profiles[base_name]
        final_specs = deepcopy(base_profile.get('specs', {}))
        
        self.logger.info(f"Loading profile '{profile_name}' inheriting from '{base_name}'")
        
        # Apply overrides
        overrides = eq_profile.get('overrides', {})
        if overrides:
            self.logger.info(f"Applying overrides...")
            final_specs = self._merge_specs(final_specs, overrides, override_mode=True)
        
        # Add additional checks
        additional = eq_profile.get('additional_checks', {})
        if additional:
            self.logger.info(f"Adding additional checks...")
            final_specs = self._merge_specs(final_specs, additional, override_mode=False)
            
        # Apply exclusions (Clean-up: Remove deleted items)
        excluded_items = eq_profile.get('excluded_items', [])
        if excluded_items:
            self.logger.info(f"Removing {len(excluded_items)} excluded items...")
            self._apply_exclusions(final_specs, excluded_items)
        
        return final_specs
    
    def _match_exclusion(self, item_path: str, pattern: str) -> bool:
        """
        Check if item_path matches exclusion pattern (supports * wildcard)
        
        Supported patterns:
          Module.*.*.*              → exclude entire module
          Module.PartType.*.*      → exclude all under part type
          Module.PartType.Part.*   → exclude all under part
          Module.PartType.Part.Item → exclude single item (exact)
        """
        item_parts = item_path.split('.')
        pattern_parts = pattern.split('.')
        
        for item_seg, pat_seg in zip(item_parts, pattern_parts):
            if pat_seg == '*':
                return True  # wildcard matches all remaining segments
            if item_seg != pat_seg:
                return False
        return len(item_parts) == len(pattern_parts)
    
    def _apply_exclusions(self, specs: Dict, excluded_items: List[str]):
        """
        Remove validation items specified in excluded_items list.
        Supports wildcard (*) patterns and individual item paths.
        
        Examples:
          "Profiler.*.*.*"  → remove all Profiler items
          "Dsp.XScanner.5um.ServoCutoffFrequencyHz" → remove single item
        """
        for module in list(specs.keys()):
            for part_type in list(specs[module].keys()):
                for part_name in list(specs[module][part_type].keys()):
                    items = specs[module][part_type][part_name]
                    filtered = []
                    for item in items:
                        item_name = item.get('item_name', '')
                        full_path = f"{module}.{part_type}.{part_name}.{item_name}"
                        
                        excluded = any(
                            self._match_exclusion(full_path, pattern)
                            for pattern in excluded_items
                        )
                        if excluded:
                            self.logger.debug(f"Excluded: {full_path}")
                        else:
                            filtered.append(item)
                    
                    specs[module][part_type][part_name] = filtered
                    
                    # Clean up empty part
                    if not specs[module][part_type][part_name]:
                        del specs[module][part_type][part_name]
                
                # Clean up empty part_type
                if part_type in specs[module] and not specs[module][part_type]:
                    del specs[module][part_type]
            
            # Clean up empty module
            if module in specs and not specs[module]:
                del specs[module]
    
    def _cleanup_profile_data(self, profile: Dict):
        """
        Auto-cleanup: Move enabled:false items to excluded_items list
        """
        overrides = profile.get('overrides', {})
        excluded_items = profile.get('excluded_items', [])
        
        items_to_remove = []
        
        # Scan overrides
        for module, module_data in overrides.items():
            for part_type, type_data in module_data.items():
                for part_name, items in type_data.items():
                    for item in items:
                        if not item.get('enabled', True):
                            item_name = item.get('item_name')
                            # Create exclusion path
                            item_path = f"{module}.{part_type}.{part_name}.{item_name}"
                            if item_path not in excluded_items:
                                excluded_items.append(item_path)
                                items_to_remove.append((module, part_type, part_name, item_name))
                                self.logger.debug(f"Auto-excluded: {item_path}")
        
        if items_to_remove:
            # Remove items from overrides
            for module, part_type, part_name, item_name in items_to_remove:
                items = overrides[module][part_type][part_name]
                # Filter out the item
                overrides[module][part_type][part_name] = [
                    item for item in items 
                    if item.get('item_name') != item_name
                ]
                
                # Clean up empty structures
                if not overrides[module][part_type][part_name]:
                    del overrides[module][part_type][part_name]
                    if not overrides[module][part_type]:
                        del overrides[module][part_type]
                        if not overrides[module]:
                            del overrides[module]
            
            profile['excluded_items'] = excluded_items
            self.logger.info(f"Cleaned up {len(items_to_remove)} deleted items")
    
    def _merge_specs(self, base: Dict, updates: Dict, override_mode: bool = False) -> Dict:
        """
        Merge spec dictionaries recursively
        
        Args:
            base: Base spec dictionary
            updates: Updates to apply
            override_mode: If True, override matching items. If False, add new items
            
        Returns:
            Merged dictionary
        """
        result = deepcopy(base)
        
        for module, module_data in updates.items():
            if module not in result:
                # New module, add completely
                result[module] = deepcopy(module_data)
                continue
            
            for part_type, part_type_data in module_data.items():
                if part_type not in result[module]:
                    # New part type, add completely
                    result[module][part_type] = deepcopy(part_type_data)
                    continue
                
                for part_name, items in part_type_data.items():
                    if part_name not in result[module][part_type]:
                        # New part name, add completely
                        result[module][part_type][part_name] = deepcopy(items)
                        continue
                    
                    # Merge items
                    if override_mode:
                        # Override mode: replace matching item names
                        existing_items = result[module][part_type][part_name]
                        
                        for new_item in items:
                            new_item_name = new_item.get('item_name')
                            
                            # Find and replace existing item with same name
                            replaced = False
                            for i, existing_item in enumerate(existing_items):
                                if existing_item.get('item_name') == new_item_name:
                                    # Merge: keep fields from base, update with new fields
                                    merged_item = deepcopy(existing_item)
                                    merged_item.update(new_item)
                                    existing_items[i] = merged_item
                                    replaced = True
                                    self.logger.debug(f"Overriding {module}.{part_type}.{part_name}.{new_item_name}")
                                    break
                            
                            # If not found, add as new
                            if not replaced:
                                existing_items.append(deepcopy(new_item))
                    else:
                        # Addition mode: just append new items
                        result[module][part_type][part_name].extend(deepcopy(items))
        
        return result
    
    def get_item_spec(self, profile_name: str, module: str, part_type: str, 
                      part_name: str, item_name: str) -> Optional[Dict]:
        """
        Get specification for a specific item
        
        Args:
            profile_name: Equipment profile name
            module: Module name (e.g., 'Dsp')
            part_type: Part type (e.g., 'XScanner')
            part_name: Part name (e.g., '100um')
            item_name: Item name (e.g., 'ServoCutoffFrequencyHz')
            
        Returns:
            Spec dictionary or None if not found
        """
        # Load full profile with inheritance
        specs = self.load_profile_with_inheritance(profile_name)
        
        if not specs:
            return None
        
        # Navigate to item
        try:
            items = specs[module][part_type][part_name]
            
            for item in items:
                if item.get('item_name') == item_name:
                    return item
            
            return None
            
        except KeyError:
            return None
    
    def get_profile_description(self, profile_name: str) -> str:
        """
        Get description of an equipment profile
        
        Args:
            profile_name: Equipment profile name
            
        Returns:
            Description string
        """
        if profile_name in self.equipment_profiles:
            return self.equipment_profiles[profile_name].get('description', '')
        return ''
