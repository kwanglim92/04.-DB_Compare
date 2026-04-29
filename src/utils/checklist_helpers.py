"""
Checklist Helpers — shared utilities for Industrial Checklist Excel handling.

Extracted from `ChecklistValidator` private methods so that the same logic is
reachable from multiple call sites (validator / autofiller / final QC engine /
UI dialogs) without leaking through `_underscore_methods`.

`ChecklistValidator._build_qc_lookup` and `_find_db_key_column` are kept as
thin delegators to these functions for backward compatibility.
"""

import logging
from typing import Any, Dict, Optional

from src.constants import CHECKLIST_COLS

logger = logging.getLogger(__name__)


def build_qc_lookup(qc_report: Dict) -> Dict[str, Any]:
    """Build flat lookup table from a QC report.

    Key format: ``Module.PartType.PartName.ItemName`` → actual_value
    """
    lookup: Dict[str, Any] = {}
    for result in qc_report.get('results', []):
        key = (f"{result['module']}.{result['part_type']}."
               f"{result['part_name']}.{result['item_name']}")
        lookup[key] = result.get('actual_value', '')
    logger.info(f"Built QC lookup: {len(lookup)} items")
    return lookup


def find_db_key_column(ws) -> Optional[int]:
    """Auto-detect DB_Key column by scanning header rows + content fallback.

    Returns 1-based column index, or ``None`` if not found.
    """
    db_key_default = CHECKLIST_COLS['DB_KEY']

    # Scan header row 1 for "DB_Key" (case-insensitive)
    for col in range(1, ws.max_column + 1):
        header = ws.cell(1, col).value
        if header and _matches_db_key(str(header)):
            return col

    # Fallback: check row 2 (sometimes headers span 2 rows)
    for col in range(1, ws.max_column + 1):
        header = ws.cell(2, col).value
        if header and _matches_db_key(str(header)):
            return col

    # Final fallback: check if default M column has dot-key-like content
    sample = ws.cell(3, db_key_default).value
    if sample and '.' in str(sample):
        logger.info(f"DB_Key column auto-detected at index {db_key_default} by content pattern")
        return db_key_default

    return None


def _matches_db_key(header: str) -> bool:
    """Lower-case + normalize separators, then look for 'db_key'."""
    norm = header.lower().replace(' ', '_').replace('-', '_')
    return 'db_key' in norm
