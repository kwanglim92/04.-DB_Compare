"""
QC Comparator Module
Compares DB values against specifications and generates Pass/Fail results
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class QCComparator:
    """
    Compares actual DB values against QC specifications
    """
    
    def __init__(self):
        self.logger = logger
    
    def compare_item(self, item_data: Dict, spec: Dict) -> Dict:
        """
        Compare a single item against its specification
        
        Args:
            item_data: Item from DB with 'value', 'value_type', etc.
            spec: Specification dictionary with validation rules
            
        Returns:
            Comparison result:
            {
                'status': 'PASS' | 'FAIL' | 'ERROR',
                'actual_value': <value>,
                'spec': <spec dict>,
                'message': <optional message>
            }
        """
        result = {
            'status': 'ERROR',
            'actual_value': item_data.get('value', ''),
            'spec': spec,
            'message': ''
        }
        
        # Check if spec is enabled
        if not spec.get('enabled', True):
            result['status'] = 'SKIPPED'
            result['message'] = 'Spec disabled'
            return result
        
        # Get validation type
        validation_type = spec.get('validation_type', 'range')
        actual_value_str = item_data.get('value', '')
        
        # Handle empty value
        if not actual_value_str:
            result['status'] = 'ERROR'
            result['message'] = 'No value in DB'
            return result
        
        try:
            if validation_type == 'range':
                # Range validation
                return self.validate_range(actual_value_str, spec)
            elif validation_type == 'exact':
                # Exact value validation
                return self.validate_exact(actual_value_str, spec)
            elif validation_type == 'check':
                # Check type: just record value
                return self.validate_check(actual_value_str, spec)
            else:
                result['status'] = 'ERROR'
                result['message'] = f'Unknown validation type: {validation_type}'
                return result
                
        except Exception as e:
            result['status'] = 'ERROR'
            result['message'] = f'Comparison error: {str(e)}'
            self.logger.error(f"Error comparing item: {e}")
            return result
    
    def validate_range(self, value_str: str, spec: Dict) -> Dict:
        """
        Validate value is within min/max range
        Supports single-sided ranges:
        - Min only: value >= min_spec
        - Max only: value <= max_spec
        - Both: min_spec <= value <= max_spec
        
        Args:
            value_str: String value from DB
            spec: Spec with optional min_spec and/or max_spec
            
        Returns:
            Validation result
        """
        result = {
            'status': 'ERROR',
            'actual_value': value_str,
            'spec': spec,
            'message': ''
        }
        
        try:
            actual_value = float(value_str)
            result['actual_value'] = actual_value
            
            min_spec = spec.get('min_spec')
            max_spec = spec.get('max_spec')
            
            # Both min and max specified
            if min_spec is not None and max_spec is not None:
                min_spec = float(min_spec)
                max_spec = float(max_spec)
                
                if min_spec <= actual_value <= max_spec:
                    result['status'] = 'PASS'
                    result['message'] = f'{actual_value} within [{min_spec}, {max_spec}]'
                else:
                    result['status'] = 'FAIL'
                    result['message'] = f'{actual_value} outside [{min_spec}, {max_spec}]'
            
            # Only min specified (≥)
            elif min_spec is not None and max_spec is None:
                min_spec = float(min_spec)
                
                if actual_value >= min_spec:
                    result['status'] = 'PASS'
                    result['message'] = f'{actual_value} ≥ {min_spec}'
                else:
                    result['status'] = 'FAIL'
                    result['message'] = f'{actual_value} < {min_spec} (Required: ≥ {min_spec})'
            
            # Only max specified (≤)
            elif min_spec is None and max_spec is not None:
                max_spec = float(max_spec)
                
                if actual_value <= max_spec:
                    result['status'] = 'PASS'
                    result['message'] = f'{actual_value} ≤ {max_spec}'
                else:
                    result['status'] = 'FAIL'
                    result['message'] = f'{actual_value} > {max_spec} (Required: ≤ {max_spec})'
            
            # Neither specified (error)
            else:
                result['status'] = 'ERROR'
                result['message'] = 'Invalid spec: both min_spec and max_spec are missing'
            
        except ValueError:
            result['status'] = 'ERROR'
            result['message'] = f'Cannot convert value to number: {value_str}'
        
        return result
    
    def validate_check(self, value_str: str, spec: Dict) -> Dict:
        """
        Check type: simply record the value without validation
        
        Args:
            value_str: String value from DB
            spec: Spec dictionary (no validation fields needed)
            
        Returns:
            Result with CHECK status
        """
        result = {
            'status': 'CHECK',
            'actual_value': value_str,
            'spec': spec,
            'message': 'Value recorded'
        }
        
        return result
    
    def validate_exact(self, value_str: str, spec: Dict) -> Dict:
        """
        Validate value matches expected value exactly
        
        Args:
            value_str: String value from DB
            spec: Spec with expected_value
            
        Returns:
            Validation result
        """
        result = {
            'status': 'ERROR',
            'actual_value': value_str,
            'spec': spec,
            'message': ''
        }
        
        expected_value = spec.get('expected_value')
        
        if expected_value is None:
            result['status'] = 'ERROR'
            result['message'] = 'Invalid spec: expected_value missing'
            return result
        
        # Try numeric comparison first
        try:
            actual_num = float(value_str)
            expected_num = float(expected_value)
            
            if actual_num == expected_num:
                result['status'] = 'PASS'
                result['message'] = f'{actual_num} == {expected_num}'
            else:
                result['status'] = 'FAIL'
                result['message'] = f'{actual_num} != {expected_num}'
            
            result['actual_value'] = actual_num
            
        except ValueError:
            # String comparison
            if str(value_str) == str(expected_value):
                result['status'] = 'PASS'
                result['message'] = f'"{value_str}" == "{expected_value}"'
            else:
                result['status'] = 'FAIL'
                result['message'] = f'"{value_str}" != "{expected_value}"'
        
        return result
    
    def generate_report(self, db_data: Dict, specs: Dict, profile_name: str) -> Dict:
        """
        Generate complete QC comparison report
        
        Args:
            db_data: Complete DB hierarchy from DBExtractor
            specs: Loaded specs from SpecManager (with inheritance applied)
            profile_name: Name of the profile used
            
        Returns:
            Report dictionary:
            {
                'summary': {
                    'total_items': 150,
                    'checked': 145,
                    'passed': 142,
                    'failed': 3,
                    'skipped': 0,
                    'errors': 0,
                    'no_spec': 5,
                    'pass_rate': 97.93
                },
                'profile_name': 'NX10_Standard',
                'timestamp': '2025-12-23 00:00:00',
                'db_root': 'C:\\...',
                'instrument': 'nx',
                'results': [
                    {
                        'module': 'Dsp',
                        'part_type': 'XScanner',
                        'part_name': '100um',
                        'item_name': 'ServoCutoffFrequencyHz',
                        'actual_value': 80.0,
                        'spec': {...},
                        'status': 'PASS',
                        'message': '...'
                    },
                    ...
                ]
            }
        """
        self.logger.info("Generating QC comparison report...")
        
        report = {
            'summary': {
                'total_items': 0,
                'validated': 0,        # Items with PASS/FAIL validation
                'checked_only': 0,     # Items with CHECK status
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': 0,
                'no_spec': 0,
                'missing_in_db': 0,
                'pass_rate': 0.0
            },
            'profile_name': profile_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'db_root': db_data.get('db_root', ''),
            'instrument': db_data.get('instrument', ''),
            'results': []
        }
        
        # Process each module
        for module in db_data.get('modules', []):
            module_name = module['name']
            
            for part in module.get('parts', []):
                part_type = part['type']
                part_name = part['name']
                
                for item in part.get('items', []):
                    item_name = item.get('name', '')
                    report['summary']['total_items'] += 1
                    
                    # Check if spec exists
                    spec = self._get_spec(specs, module_name, part_type, part_name, item_name)
                    
                    if spec is None:
                        # No spec for this item
                        report['summary']['no_spec'] += 1
                        report['results'].append({
                            'module': module_name,
                            'part_type': part_type,
                            'part_name': part_name,
                            'item_name': item_name,
                            'actual_value': item.get('value', ''),
                            'spec': None,
                            'status': 'NO_SPEC',
                            'message': 'No specification defined'
                        })
                        continue
                    
                    # Compare item against spec
                    comparison_result = self.compare_item(item, spec)
                    
                    # Update counters
                    status = comparison_result['status']
                    if status == 'PASS':
                        report['summary']['passed'] += 1
                        report['summary']['validated'] += 1
                    elif status == 'FAIL':
                        report['summary']['failed'] += 1
                        report['summary']['validated'] += 1
                    elif status == 'CHECK':
                        report['summary']['checked_only'] += 1
                    elif status == 'SKIPPED':
                        report['summary']['skipped'] += 1
                    elif status == 'ERROR':
                        report['summary']['errors'] += 1
                    
                    # Add to results
                    report['results'].append({
                        'module': module_name,
                        'part_type': part_type,
                        'part_name': part_name,
                        'item_name': item_name,
                        'actual_value': comparison_result['actual_value'],
                        'spec': comparison_result['spec'],
                        'status': status,
                        'message': comparison_result.get('message', '')
                    })
        
        # Check for profile items missing in DB
        missing_items = self._find_missing_in_db(db_data, specs)
        for missing in missing_items:
            report['summary']['failed'] += 1
            report['summary']['validated'] += 1
            report['summary']['missing_in_db'] += 1
            report['results'].append({
                'module': missing['module'],
                'part_type': missing['part_type'],
                'part_name': missing['part_name'],
                'item_name': missing['item_name'],
                'actual_value': 'N/A',
                'spec': missing['spec'],
                'status': 'FAIL',
                'message': '⚠️ Item not found in DB'
            })
        
        # Calculate pass rate (exclude CHECK from denominator)
        validated_items = report['summary']['validated']
        if validated_items > 0:
            pass_rate = (report['summary']['passed'] / validated_items) * 100
            report['summary']['pass_rate'] = round(pass_rate, 2)
        
        # Log summary
        self.logger.info("=" * 60)
        self.logger.info("QC Inspection Summary:")
        self.logger.info(f"  Profile: {profile_name}")
        self.logger.info(f"  Total Items: {report['summary']['total_items']}")
        self.logger.info(f"  Validated: {report['summary']['validated']}")
        self.logger.info(f"  Checked Only: {report['summary']['checked_only']}")
        self.logger.info(f"  Passed: {report['summary']['passed']}")
        self.logger.info(f"  Failed: {report['summary']['failed']}")
        self.logger.info(f"  Skipped: {report['summary']['skipped']}")
        self.logger.info(f"  Errors: {report['summary']['errors']}")
        self.logger.info(f"  No Spec: {report['summary']['no_spec']}")
        self.logger.info(f"  Missing in DB: {report['summary']['missing_in_db']}")
        self.logger.info(f"  Pass Rate: {report['summary']['pass_rate']}%")
        self.logger.info("=" * 60)
        
        return report
    
    def _get_spec(self, specs: Dict, module: str, part_type: str, 
                  part_name: str, item_name: str) -> Optional[Dict]:
        """
        Get spec for a specific item from specs dictionary
        
        Args:
            specs: Complete specs dictionary
            module: Module name
            part_type: Part type
            part_name: Part name
            item_name: Item name
            
        Returns:
            Spec dictionary or None
        """
        try:
            items = specs[module][part_type][part_name]
            
            for item in items:
                if item.get('item_name') == item_name:
                    return item
            
            return None
            
        except KeyError:
            return None
    
    def _find_missing_in_db(self, db_data: Dict, specs: Dict) -> List[Dict]:
        """
        Find spec items that don't exist in DB
        
        Args:
            db_data: DB data from extractor
            specs: Loaded specs with inheritance
            
        Returns:
            List of missing items
        """
        missing = []
        
        # Build DB item set for fast lookup
        db_items = set()
        for module in db_data.get('modules', []):
            module_name = module['name']
            for part in module.get('parts', []):
                part_type = part['type']
                part_name = part['name']
                for item in part.get('items', []):
                    item_name = item.get('name', '')
                    key = (module_name, part_type, part_name, item_name)
                    db_items.add(key)
        
        # Check each spec item
        for module, module_data in specs.items():
            for part_type, type_data in module_data.items():
                for part_name, items in type_data.items():
                    for spec in items:
                        if not spec.get('enabled', True):
                            continue
                        item_name = spec.get('item_name', '')
                        key = (module, part_type, part_name, item_name)
                        
                        if key not in db_items:
                            missing.append({
                                'module': module,
                                'part_type': part_type,
                                'part_name': part_name,
                                'item_name': item_name,
                                'spec': spec
                            })
        
        if missing:
            self.logger.warning(f"Found {len(missing)} profile items missing in DB")
        
        return missing
