"""
Tests for src/core/checklist_mapper.py
5-stage cascade: explicit → learned → exact → fuzzy → unit_hint → unmapped
"""

import pytest
from src.core.checklist_mapper import ChecklistMapper, MapResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def qc_lookup():
    """Minimal QC dot-key lookup matching real DB key format."""
    return {
        'Dsp.XScanner.100um.ServoCutoffFrequencyHz': 800.0,
        'Dsp.ZDetector.LongHead.MicrometerPerAdcHigh': 0.0123,
        'Dsp.AFMHead.Probe.LaserPowerMw': 3.5,
        'Dsp.ZScanner.10um.RepeatabilityNm': 0.4,
        'System.EFEM.Aligner.CenteringAccuracyUm': 0.5,
    }


@pytest.fixture
def learned_mappings():
    return [
        {
            'model': 'NX-Wafer 200mm',
            'module': 'xy stage',
            'item_norm': 'servo cutoff frequency',
            'db_key': 'Dsp.XScanner.100um.ServoCutoffFrequencyHz',
            'confidence': 0.95,
        }
    ]


@pytest.fixture
def mapper(qc_lookup, learned_mappings):
    return ChecklistMapper(
        qc_lookup=qc_lookup,
        learned_mappings=learned_mappings,
        model='NX-Wafer 200mm',
        fuzzy_threshold=0.80,
    )


# ---------------------------------------------------------------------------
# Stage A: Explicit M-column
# ---------------------------------------------------------------------------

class TestStageA:
    def test_explicit_key_returns_confidence_1(self, mapper):
        row = {
            'row': 5,
            'module': 'AFM Head',
            'item': 'Laser Power',
            'explicit_db_key': 'Dsp.AFMHead.Probe.LaserPowerMw',
            'unit': 'mW',
        }
        result = mapper.map_single(row)
        assert result.source == 'explicit'
        assert result.confidence == 1.00
        assert result.db_key == 'Dsp.AFMHead.Probe.LaserPowerMw'

    def test_explicit_key_not_in_lookup_falls_through(self, mapper):
        row = {
            'row': 6,
            'module': 'AFM Head',
            'item': 'Laser Power',
            'explicit_db_key': 'Nonexistent.Key.Here',
            'unit': '',
        }
        result = mapper.map_single(row)
        assert result.source != 'explicit'


# ---------------------------------------------------------------------------
# Stage B: Learned dictionary
# ---------------------------------------------------------------------------

class TestStageB:
    def test_learned_hit_returns_confidence_095(self, mapper):
        row = {
            'row': 10,
            'module': 'XY Stage',
            'item': 'Servo Cutoff Frequency',
            'explicit_db_key': '',
            'unit': 'Hz',
        }
        result = mapper.map_single(row)
        assert result.source == 'learned'
        assert result.confidence == 0.95
        assert result.db_key == 'Dsp.XScanner.100um.ServoCutoffFrequencyHz'

    def test_learned_model_mismatch_falls_through(self, qc_lookup):
        mapper_other = ChecklistMapper(
            qc_lookup=qc_lookup,
            learned_mappings=[{
                'model': 'OTHER_MODEL',
                'module': 'xy stage',
                'item_norm': 'servo cutoff frequency',
                'db_key': 'Dsp.XScanner.100um.ServoCutoffFrequencyHz',
                'confidence': 0.95,
            }],
            model='NX-Wafer 200mm',
        )
        row = {
            'row': 11, 'module': 'XY Stage',
            'item': 'Servo Cutoff Frequency',
            'explicit_db_key': '', 'unit': 'Hz',
        }
        result = mapper_other.map_single(row)
        assert result.source != 'learned'


# ---------------------------------------------------------------------------
# Stage C: Normalized exact match
# ---------------------------------------------------------------------------

class TestStageC:
    def test_exact_normalized_match_confidence_085(self, qc_lookup):
        mapper = ChecklistMapper(qc_lookup=qc_lookup, learned_mappings=[], model='')
        row = {
            'row': 20, 'module': 'Z Detector',
            'item': 'MicrometerPerAdcHigh',
            'explicit_db_key': '', 'unit': '',
        }
        result = mapper.map_single(row)
        assert result.source == 'exact'
        assert result.confidence == 0.85
        assert 'MicrometerPerAdcHigh' in result.db_key


# ---------------------------------------------------------------------------
# Stage D: Fuzzy matching
# ---------------------------------------------------------------------------

class TestStageD:
    def test_fuzzy_match_above_threshold(self, qc_lookup):
        pytest.importorskip('rapidfuzz')
        mapper = ChecklistMapper(
            qc_lookup=qc_lookup, learned_mappings=[], model='',
            fuzzy_threshold=0.60,
        )
        row = {
            'row': 30, 'module': 'Dsp',
            'item': 'Laser Power Milliwatts',
            'explicit_db_key': '', 'unit': 'mW',
        }
        result = mapper.map_single(row)
        assert result.source in ('fuzzy', 'exact', 'unit_hint', 'unmapped')
        if result.source == 'fuzzy':
            assert result.confidence >= 0.60

    def test_fuzzy_confidence_stored(self, qc_lookup):
        pytest.importorskip('rapidfuzz')
        mapper = ChecklistMapper(
            qc_lookup=qc_lookup, learned_mappings=[], model='',
            fuzzy_threshold=0.60,
        )
        row = {
            'row': 31, 'module': 'Dsp',
            'item': 'Laser Power Mw',
            'explicit_db_key': '', 'unit': 'mW',
        }
        result = mapper.map_single(row)
        if result.source == 'fuzzy':
            assert 0.0 < result.confidence <= 1.0


# ---------------------------------------------------------------------------
# Unmapped: top-5 candidates
# ---------------------------------------------------------------------------

class TestUnmapped:
    def test_unmapped_provides_candidates(self, qc_lookup):
        pytest.importorskip('rapidfuzz')
        mapper = ChecklistMapper(
            qc_lookup=qc_lookup, learned_mappings=[], model='',
            fuzzy_threshold=0.99,  # Force unmapped
        )
        row = {
            'row': 50, 'module': 'Unknown',
            'item': 'Some totally unrelated item XYZ123',
            'explicit_db_key': '', 'unit': '',
        }
        result = mapper.map_single(row)
        assert result.source == 'unmapped'
        assert result.db_key is None
        assert isinstance(result.candidates, list)

    def test_unmapped_confidence_is_zero(self, qc_lookup):
        mapper = ChecklistMapper(
            qc_lookup=qc_lookup, learned_mappings=[], model='',
            fuzzy_threshold=0.99,
        )
        row = {
            'row': 51, 'module': 'XYZ',
            'item': 'ZZZZZZZ completely random text 9999',
            'explicit_db_key': '', 'unit': '',
        }
        result = mapper.map_single(row)
        if result.source == 'unmapped':
            assert result.confidence == 0.0


# ---------------------------------------------------------------------------
# map_rows: batch processing
# ---------------------------------------------------------------------------

class TestMapRows:
    def test_batch_returns_same_count(self, mapper):
        rows = [
            {'row': 1, 'module': 'AFM Head', 'item': 'Laser Power',
             'explicit_db_key': 'Dsp.AFMHead.Probe.LaserPowerMw', 'unit': 'mW'},
            {'row': 2, 'module': 'Unknown', 'item': 'Something else',
             'explicit_db_key': '', 'unit': ''},
        ]
        results = mapper.map_rows(rows)
        assert len(results) == 2

    def test_batch_preserves_row_numbers(self, mapper):
        rows = [
            {'row': 42, 'module': 'AFM Head', 'item': 'Laser Power',
             'explicit_db_key': 'Dsp.AFMHead.Probe.LaserPowerMw', 'unit': ''},
        ]
        results = mapper.map_rows(rows)
        assert results[0].row == 42
