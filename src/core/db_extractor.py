"""
DB Extractor Module
Traverses the DB directory structure and extracts all data
"""

from pathlib import Path
from typing import Dict, List, Optional
import logging
from .xml_parser import XMLParser

logger = logging.getLogger(__name__)


class DBExtractor:
    """
    Extracts complete DB hierarchy from Park Systems DB directory
    """
    
    def __init__(self, db_root: str):
        """
        Initialize DB Extractor
        
        Args:
            db_root: Root path to DB directory (e.g., C:\\Park Systems\\XEService\\DB)
        """
        self.db_root = Path(db_root)
        self.parser = XMLParser()
        self.logger = logger
        
        if not self.db_root.exists():
            raise FileNotFoundError(f"DB root not found: {db_root}")
    
    def extract_all_modules(self) -> List[str]:
        """
        Get list of all module directories
        
        Returns:
            List of module names (e.g., ['Dsp', 'Profiler', 'XYStage', ...])
        """
        module_dir = self.db_root / "Module"
        
        if not module_dir.exists():
            self.logger.warning(f"Module directory not found: {module_dir}")
            return []
        
        modules = []
        for item in module_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                modules.append(item.name)
        
        self.logger.info(f"Found {len(modules)} modules: {modules}")
        return sorted(modules)
    
    def extract_module_parts(self, module_name: str) -> Dict:
        """
        Extract all parts for a specific module
        
        Args:
            module_name: Name of the module (e.g., 'Dsp')
            
        Returns:
            Dictionary with module info and parts:
            {
                'module_name': 'Dsp',
                'selected_module': 'General',
                'module_config': {...},
                'parts': [...]
            }
        """
        module_path = self.db_root / "Module" / module_name
        
        if not module_path.exists():
            self.logger.error(f"Module path not found: {module_path}")
            return None
        
        result = {
            'module_name': module_name,
            'selected_module': None,
            'module_config': None,
            'parts': []
        }
        
        # Get selected module
        selected_module = self.parser.parse_module_selection(str(module_path))
        result['selected_module'] = selected_module
        
        # Get module config
        if selected_module:
            config_file = module_path / "Module" / f"{selected_module}.xml"
            if config_file.exists():
                result['module_config'] = self.parser.parse_module_config(str(config_file))
        
        return result
    
    def extract_part_items(self, module_name: str, part_type: str, part_name: str) -> Optional[List[Dict]]:
        """
        Extract all items for a specific part
        
        Args:
            module_name: Module name (e.g., 'Dsp')
            part_type: Part type (e.g., 'XScanner')
            part_name: Part name (e.g., '100um')
            
        Returns:
            List of items with their properties
        """
        part_file = self.db_root / "Module" / module_name / "Part" / part_type / f"{part_name}.xml"
        
        if not part_file.exists():
            self.logger.warning(f"Part file not found: {part_file}")
            return None
        
        return self.parser.parse_part_items(str(part_file))
    
    def build_hierarchy(self) -> Dict:
        """
        Build complete DB hierarchy with all modules, parts, and items
        
        Returns:
            Complete DB structure:
            {
                'instrument': 'nx',
                'db_root': 'C:\\...',
                'modules': [
                    {
                        'name': 'Dsp',
                        'selected_module': 'General',
                        'description': '...',
                        'parts': [
                            {
                                'type': 'XScanner',
                                'name': '100um',
                                'items': [
                                    {
                                        'name': 'ServoCutoffFrequencyHz',
                                        'value': '80',
                                        'value_type': 'double',
                                        ...
                                    },
                                    ...
                                ]
                            },
                            ...
                        ]
                    },
                    ...
                ]
            }
        """
        self.logger.info("Building complete DB hierarchy...")
        
        hierarchy = {
            'instrument': None,
            'db_root': str(self.db_root),
            'modules': []
        }
        
        # Get instrument name
        instrument = self.parser.parse_db_root(str(self.db_root))
        hierarchy['instrument'] = instrument
        
        # Get all modules
        module_names = self.extract_all_modules()
        
        for module_name in module_names:
            self.logger.info(f"Processing module: {module_name}")
            
            module_data = self.extract_module_parts(module_name)
            if not module_data or not module_data.get('module_config'):
                self.logger.warning(f"Skipping module {module_name} - no config found")
                continue
            
            module_config = module_data['module_config']
            
            module_info = {
                'name': module_name,
                'selected_module': module_data['selected_module'],
                'description': module_config.get('description', ''),
                'parts': []
            }
            
            # Process each part in the module config
            for part_ref in module_config.get('parts', []):
                part_type = part_ref['type']
                part_name = part_ref['name']
                
                self.logger.debug(f"  Processing part: {part_type}/{part_name}")
                
                # Extract items for this part
                items = self.extract_part_items(module_name, part_type, part_name)
                
                if items is not None:
                    part_info = {
                        'type': part_type,
                        'name': part_name,
                        'items': items
                    }
                    module_info['parts'].append(part_info)
                    self.logger.debug(f"    Found {len(items)} items")
                else:
                    self.logger.debug(f"    No items found for {part_type}/{part_name}")
            
            hierarchy['modules'].append(module_info)
        
        # Summary
        total_parts = sum(len(m['parts']) for m in hierarchy['modules'])
        total_items = sum(
            sum(len(p['items']) for p in m['parts']) 
            for m in hierarchy['modules']
        )
        
        self.logger.info("=" * 60)
        self.logger.info(f"Extraction complete:")
        self.logger.info(f"  Instrument: {hierarchy['instrument']}")
        self.logger.info(f"  Modules: {len(hierarchy['modules'])}")
        self.logger.info(f"  Parts: {total_parts}")
        self.logger.info(f"  Items: {total_items}")
        self.logger.info("=" * 60)
        
        return hierarchy
