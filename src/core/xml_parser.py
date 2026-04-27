"""
XML Parser Module
Parses XML files from the DB directory structure
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _open_xml(path):
    """Open XML file using the standard OS path.

    Note (v1.5.1, 2026-04-27): Earlier versions auto-prepended Windows
    long-path prefix (``\\\\?\\``) to support deeply-nested or non-ASCII
    paths. In practice this broke SMB mapped-drive (e.g. ``Z:\\``) and
    UNC access on internal corporate networks — the prefix changed the
    SMB client's permission token validation path and produced spurious
    ``Errno 13: Permission denied`` even though Windows Explorer could
    read the same files. Python 3.6+ handles Unicode paths natively, so
    no prefix is needed under ``MAX_PATH``. This matches the SKILL 19
    pattern as used by sibling projects (see Sliding Stage OPM).
    """
    return open(str(path), 'rb')


class XMLParser:
    """
    Parses XML files from the Park Systems DB structure
    """
    
    def __init__(self):
        self.logger = logger
    
    def parse_db_root(self, db_path: str) -> Optional[str]:
        """
        Parse DB.xml to get the SelectedInstrument
        
        Args:
            db_path: Path to the DB directory
            
        Returns:
            Selected instrument name (e.g., 'nx') or None if not found
        """
        db_xml_path = Path(db_path) / "DB.xml"
        
        if not db_xml_path.exists():
            self.logger.error(f"DB.xml not found at {db_xml_path}")
            return None
        
        try:
            with _open_xml(db_xml_path) as f:
                tree = ET.parse(f)
            root = tree.getroot()

            # Find SelectedInstrument element
            selected_instrument = root.find('.//SelectedInstrument')
            if selected_instrument is not None and selected_instrument.text:
                self.logger.info(f"Selected Instrument: {selected_instrument.text}")
                return selected_instrument.text.strip()
            else:
                self.logger.warning("SelectedInstrument not found in DB.xml")
                return None

        except (PermissionError, OSError) as e:
            self.logger.error(f"Cannot read DB.xml (network/permission error): {db_xml_path} — {e}")
            return None
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse DB.xml: {e}")
            return None
    
    def parse_module_selection(self, module_path: str) -> Optional[str]:
        """
        Parse Module.xml to get the SelectedModule
        
        Args:
            module_path: Path to the Module directory (e.g., DB/Module/Dsp)
            
        Returns:
            Selected module name (e.g., 'General') or None if not found
        """
        module_xml_path = Path(module_path) / "Module.xml"
        
        if not module_xml_path.exists():
            self.logger.error(f"Module.xml not found at {module_xml_path}")
            return None
        
        try:
            with _open_xml(module_xml_path) as f:
                tree = ET.parse(f)
            root = tree.getroot()

            # Find SelectedModule element
            selected_module = root.find('.//SelectedModule')
            if selected_module is not None and selected_module.text:
                self.logger.info(f"Selected Module: {selected_module.text}")
                return selected_module.text.strip()
            else:
                self.logger.warning(f"SelectedModule not found in {module_xml_path}")
                return None

        except (PermissionError, OSError) as e:
            self.logger.error(f"Cannot read Module.xml (network/permission error): {module_xml_path} — {e}")
            return None
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse Module.xml: {e}")
            return None
    
    def parse_module_config(self, module_file: str) -> Optional[Dict]:
        """
        Parse Module configuration file to get PartList
        
        Args:
            module_file: Path to module config XML (e.g., DB/Module/Dsp/Module/General.xml)
            
        Returns:
            Dictionary with module config including PartList
            {
                'name': 'General',
                'description': '...',
                'parts': [
                    {'type': 'XScanner', 'name': '100um'},
                    {'type': 'YScanner', 'name': '100um'},
                    ...
                ]
            }
        """
        module_file_path = Path(module_file)
        
        if not module_file_path.exists():
            self.logger.error(f"Module config file not found: {module_file_path}")
            return None
        
        try:
            with _open_xml(module_file_path) as f:
                tree = ET.parse(f)
            root = tree.getroot()

            config = {
                'name': None,
                'description': None,
                'parts': []
            }

            # Get module name
            name_elem = root.find('.//Name')
            if name_elem is not None and name_elem.text:
                config['name'] = name_elem.text.strip()

            # Get description
            desc_elem = root.find('.//Description')
            if desc_elem is not None and desc_elem.text:
                config['description'] = desc_elem.text.strip()

            # Get PartList
            part_list = root.find('.//PartList')
            if part_list is not None:
                for part in part_list.findall('Part'):
                    part_type = part.find('Type')
                    part_name = part.find('Name')

                    if part_type is not None and part_name is not None:
                        config['parts'].append({
                            'type': part_type.text.strip() if part_type.text else '',
                            'name': part_name.text.strip() if part_name.text else ''
                        })

            self.logger.info(f"Parsed module config: {config['name']} with {len(config['parts'])} parts")
            return config

        except (PermissionError, OSError) as e:
            self.logger.error(f"Cannot read module config (network/permission error): {module_file_path} — {e}")
            return None
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse module config: {e}")
            return None
    
    def parse_part_items(self, part_file: str) -> Optional[List[Dict]]:
        """
        Parse Part XML file to get ItemList
        
        Args:
            part_file: Path to part XML file (e.g., DB/Module/Dsp/Part/XScanner/100um.xml)
            
        Returns:
            List of items:
            [
                {
                    'name': 'ServoCutoffFrequencyHz',
                    'description': '...',
                    'value_type': 'double',
                    'value': '80',
                    'access': '33'
                },
                ...
            ]
        """
        part_file_path = Path(part_file)
        
        if not part_file_path.exists():
            self.logger.error(f"Part file not found: {part_file_path}")
            return None
        
        try:
            with _open_xml(part_file_path) as f:
                tree = ET.parse(f)
            root = tree.getroot()

            items = []

            # Find ItemList
            item_list = root.find('.//ItemList')
            if item_list is not None:
                for item in item_list.findall('Item'):
                    item_data = {}

                    # Extract item fields
                    name_elem = item.find('Name')
                    if name_elem is not None and name_elem.text:
                        item_data['name'] = name_elem.text.strip()

                    desc_elem = item.find('Description')
                    if desc_elem is not None:
                        item_data['description'] = desc_elem.text.strip() if desc_elem.text else ''

                    value_type_elem = item.find('ValueType')
                    if value_type_elem is not None and value_type_elem.text:
                        item_data['value_type'] = value_type_elem.text.strip()

                    value_elem = item.find('Value')
                    if value_elem is not None:
                        item_data['value'] = value_elem.text.strip() if value_elem.text else ''

                    access_elem = item.find('Access')
                    if access_elem is not None and access_elem.text:
                        item_data['access'] = access_elem.text.strip()

                    # Only add if we have at least a name
                    if 'name' in item_data:
                        items.append(item_data)

            self.logger.info(f"Parsed {len(items)} items from {part_file_path.name}")
            return items

        except (PermissionError, OSError) as e:
            self.logger.error(f"Cannot read part file (network/permission error): {part_file_path} — {e}")
            return None
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse part file: {e}")
            return None
