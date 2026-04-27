"""Tests for src/utils/template_helper.py (F14)."""
import json
import pytest
from pathlib import Path
from src.utils.template_helper import (
    get_default_template, load_template, save_template,
    validate_template, apply_placeholders
)


def test_get_default_template_structure():
    t = get_default_template()
    assert "company" in t
    assert "sheets" in t
    assert t["sheets"]["summary"] is True
    assert t["sheets"]["cover_page"] is False


def test_load_template_from_file(tmp_path):
    data = {"title_template": "Test — {profile}", "header_color": "#ff0000"}
    p = tmp_path / "tmpl.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    t = load_template(p)
    assert t["title_template"] == "Test — {profile}"
    assert t["header_color"] == "#ff0000"
    # Default keys should still be present
    assert "company" in t


def test_load_template_fallback_on_invalid(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    t = load_template(p)
    assert t == get_default_template()


def test_save_and_reload(tmp_path):
    t = get_default_template()
    t["engineer_name"] = "Levi"
    p = tmp_path / "out.json"
    assert save_template(t, p) is True
    loaded = load_template(p)
    assert loaded["engineer_name"] == "Levi"


def test_validate_template_bad_color():
    t = get_default_template()
    t["header_color"] = "notacolor"
    result = validate_template(t)
    assert result["header_color"] == "#1f6aa5"


def test_validate_template_all_sheets_off():
    t = get_default_template()
    for k in t["sheets"]:
        t["sheets"][k] = False
    result = validate_template(t)
    assert result["sheets"]["summary"] is True


def test_validate_template_logo_missing(tmp_path):
    t = get_default_template()
    t["company"]["logo_path"] = str(tmp_path / "nonexistent.png")
    result = validate_template(t)
    assert result["company"]["logo_path"] == ""


def test_apply_placeholders_basic():
    result = apply_placeholders("Report — {profile} — {date}", {"profile": "NX10", "date": "2026-04-27"})
    assert result == "Report — NX10 — 2026-04-27"


def test_apply_placeholders_missing_key():
    result = apply_placeholders("Hello {missing}", {})
    assert result == "Hello {missing}"


def test_apply_placeholders_extra_keys_ok():
    result = apply_placeholders("Hi {name}", {"name": "Levi", "extra": "ignored"})
    assert result == "Hi Levi"
