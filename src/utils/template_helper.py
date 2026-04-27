"""Report template load/save/validate and placeholder substitution."""

import copy
import json
import logging
import re
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

_DEFAULT_TEMPLATE: Dict = {
    "company": {
        "name": "Park Systems",
        "logo_path": "",
        "contact": "qc@parksystems.com",
    },
    "title_template": "QC Inspection Report — {profile} — {date}",
    "engineer_name": "",
    "header_color": "#1f6aa5",
    "footer_text": "Confidential — Internal Use Only",
    "sheets": {
        "summary": True,
        "all_items": True,
        "failed_items": True,
        "cover_page": False,
    },
    "columns": {
        "show_unit": True,
        "show_description": False,
    },
}

_HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


def get_default_template() -> Dict:
    return copy.deepcopy(_DEFAULT_TEMPLATE)


def load_template(template_path: Path) -> Dict:
    """Load template from JSON; falls back to default on any error."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return _merge_with_default(data)
    except Exception as e:
        logger.warning(f"Cannot load report template ({e}), using defaults")
        return get_default_template()


def save_template(template: Dict, template_path: Path) -> bool:
    """Save template dict to JSON. Returns True on success."""
    try:
        template_path.parent.mkdir(parents=True, exist_ok=True)
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save report template: {e}")
        return False


def validate_template(template: Dict) -> Dict:
    """Sanitize template fields in-place; return cleaned copy."""
    t = copy.deepcopy(template)

    # header_color — must be #RRGGBB
    color = t.get("header_color", "")
    if not _HEX_COLOR_RE.match(str(color)):
        logger.warning(f"Invalid header_color '{color}', using default")
        t["header_color"] = _DEFAULT_TEMPLATE["header_color"]

    # sheets — at least Summary must stay enabled
    sheets = t.setdefault("sheets", {})
    if not any(sheets.get(k, False) for k in ("summary", "all_items", "failed_items", "cover_page")):
        logger.warning("All sheets disabled — forcing summary=True")
        sheets["summary"] = True

    # logo_path — clear if file does not exist
    logo = t.get("company", {}).get("logo_path", "")
    if logo and not Path(logo).exists():
        logger.warning(f"Logo path not found: {logo}, ignoring")
        t.setdefault("company", {})["logo_path"] = ""

    return t


def apply_placeholders(template_str: str, ctx: Dict) -> str:
    """Substitute {key} placeholders; return original string on KeyError."""
    try:
        return template_str.format(**ctx)
    except (KeyError, ValueError) as e:
        logger.warning(f"Placeholder substitution failed ({e}), using raw string")
        return template_str


def _merge_with_default(data: Dict) -> Dict:
    """Deep-merge loaded data onto default template so missing keys are filled."""
    result = get_default_template()
    for key, value in data.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key].update(value)
        else:
            result[key] = value
    return result
