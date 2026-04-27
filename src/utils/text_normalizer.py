"""
Text Normalizer for Checklist Item Matching
Normalizes checklist item names for comparison against DB keys.
"""

import re
from typing import List

# Abbreviation expansion table (lower-case key → expanded form)
_ABBREVIATIONS: dict[str, str] = {
    'afm': 'atomic force microscope',
    'afm head': 'atomic force microscope head',
    'stm': 'scanning tunneling microscope',
    'sem': 'scanning electron microscope',
    'xy stage': 'xy stage',
    'z stage': 'z stage',
    'efem': 'equipment front end module',
    'foup': 'front opening unified pod',
    'prealigner': 'prealigner',
    'atm': 'atmospheric',
    'vac': 'vacuum',
    'dsp': 'dsp',
    'qc': 'quality control',
    'pid': 'pid',
    'rms': 'root mean square',
    '1sigma': '1 sigma',
    '1σ': '1 sigma',
    '3sigma': '3 sigma',
    '3σ': '3 sigma',
    'hz': 'hz',
    'khz': 'khz',
    'mhz': 'mhz',
    'nm': 'nm',
    'um': 'um',
    'mm': 'mm',
    'mv': 'mv',
    'snr': 'signal noise ratio',
    'snr ': 'signal noise ratio ',
    'fwhm': 'full width half maximum',
    'psd': 'power spectral density',
    'adc': 'adc',
    'dac': 'dac',
    'encoder': 'encoder',
    'repeatability': 'repeatability',
    'repeat': 'repeatability',
    'repro': 'reproducibility',
    'reproducibility': 'reproducibility',
    'linearity': 'linearity',
    'orthogonality': 'orthogonality',
    'accuracy': 'accuracy',
    'resolution': 'resolution',
    'sensitivity': 'sensitivity',
    'bandwidth': 'bandwidth',
    'range': 'range',
    'gain': 'gain',
    'offset': 'offset',
    'threshold': 'threshold',
    'calibration': 'calibration',
    'calib': 'calibration',
    'noise': 'noise',
    'current': 'current',
    'voltage': 'voltage',
    'temperature': 'temperature',
    'temp': 'temperature',
    'frequency': 'frequency',
    'freq': 'frequency',
    'servo': 'servo',
    'cutoff': 'cutoff',
    'step height': 'step height',
    'roughness': 'roughness',
    'flatness': 'flatness',
    'wafer': 'wafer',
    'chuck': 'chuck',
    'leveling': 'leveling',
    'alignment': 'alignment',
    'centering': 'centering',
    'vibration': 'vibration',
    'thermal drift': 'thermal drift',
    'drift': 'drift',
    'scan': 'scan',
    'scanning': 'scanning',
    'tip': 'tip',
    'cantilever': 'cantilever',
    'laser': 'laser',
    'detector': 'detector',
    'photodetector': 'photodetector',
    'micrometer': 'micrometer',
    'setpoint': 'setpoint',
    'amplitude': 'amplitude',
    'phase': 'phase',
    'q factor': 'q factor',
    'version': 'version',
    'fw': 'firmware',
    'firmware': 'firmware',
    'sw': 'software',
    'software': 'software',
}

# Patterns to strip from item names before normalization
_STRIP_PATTERNS = [
    # parenthetical conditions: (15 repeats, 1σ), (3x3 um), etc.
    r'\([^)]*\)',
    # spec values in angle brackets or brackets: [0.5], <0.1>
    r'[\[<][^\]>]*[\]>]',
    # trailing punctuation
    r'[,;:]+$',
]
_STRIP_RE = re.compile('|'.join(_STRIP_PATTERNS), re.IGNORECASE)

# Unit tokens for extraction (\b after % doesn't work — use lookahead instead)
_UNIT_PATTERN = re.compile(
    r'\b(\d+(?:\.\d+)?)\s*(nm|um|mm|mv|v|hz|khz|mhz|ghz|db|%|deg)(?=\s|$|[,;)])',
    re.IGNORECASE
)


def normalize(text: str) -> str:
    """Normalize a checklist item name for fuzzy comparison.

    Steps:
    1. Lower-case
    2. Strip parenthetical conditions / spec ranges
    3. Expand known abbreviations
    4. Collapse whitespace
    """
    if not text:
        return ''
    t = text.lower().strip()
    # Remove parenthetical and bracket content
    t = _STRIP_RE.sub(' ', t)
    # Expand abbreviations (longest match wins via sorted order)
    for abbr, expanded in sorted(_ABBREVIATIONS.items(), key=lambda x: -len(x[0])):
        t = re.sub(r'\b' + re.escape(abbr) + r'\b', expanded, t)
    # Collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def extract_unit_tokens(text: str) -> List[str]:
    """Extract (value, unit) pairs from a checklist item name.

    Example: 'Step Height 180nm' → ['180nm']
    """
    matches = _UNIT_PATTERN.findall(text.lower())
    return [f"{val}{unit.lower()}" for val, unit in matches]
