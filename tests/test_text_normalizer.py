"""
Tests for src/utils/text_normalizer.py
"""

import pytest
from src.utils.text_normalizer import normalize, extract_unit_tokens


class TestNormalize:
    def test_lowercases_input(self):
        assert normalize("AFM") == "atomic force microscope"

    def test_strips_parenthetical_conditions(self):
        result = normalize("AFM, Static Repeatability w/ 180nm Step Height Sample (15 repeats, 1σ)")
        assert "15 repeats" not in result
        assert "1σ" not in result

    def test_expands_repeat_abbreviation(self):
        result = normalize("XY Stage Repeat")
        assert "repeatability" in result

    def test_collapses_whitespace(self):
        result = normalize("  Laser   Power  ")
        assert "  " not in result
        assert result == result.strip()

    def test_empty_string_returns_empty(self):
        assert normalize("") == ""

    def test_none_handled(self):
        # normalize accepts str; callers should pass str(val or '')
        assert normalize("") == ""

    def test_brackets_stripped(self):
        result = normalize("Step Height [180nm]")
        assert "[" not in result
        assert "]" not in result

    def test_frequency_abbreviation(self):
        result = normalize("Servo Cutoff Freq")
        assert "frequency" in result

    def test_afm_head_abbreviation(self):
        result = normalize("AFM Head vibration")
        assert "atomic force microscope" in result

    def test_trailing_punctuation_removed(self):
        result = normalize("Laser Power,")
        assert not result.endswith(",")

    def test_calib_expands_to_calibration(self):
        result = normalize("XY Stage Calib")
        assert "calibration" in result


class TestExtractUnitTokens:
    def test_extracts_nm_unit(self):
        tokens = extract_unit_tokens("Step Height 180nm Sample")
        assert "180nm" in tokens

    def test_extracts_percent(self):
        tokens = extract_unit_tokens("Linearity 0.5%")
        assert "0.5%" in tokens

    def test_extracts_hz(self):
        tokens = extract_unit_tokens("Cutoff Frequency 1000Hz")
        assert "1000hz" in tokens

    def test_no_units_returns_empty(self):
        tokens = extract_unit_tokens("Static Repeatability")
        assert tokens == []

    def test_multiple_units(self):
        tokens = extract_unit_tokens("Range 100um noise 0.1nm")
        assert len(tokens) == 2
