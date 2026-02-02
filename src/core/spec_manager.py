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
    """
    
    def __init__(self):
        self.base_profiles = {}
        self.equipment_profiles = {}
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
        
        return final_specs
    
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
