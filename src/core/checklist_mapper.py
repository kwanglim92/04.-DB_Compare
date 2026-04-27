"""
Checklist Mapper Module
Maps checklist Excel rows to DB keys via a 5-stage cascade pipeline.

Cascade order (first match wins):
  A) Explicit M-column DB key          → confidence 1.00
  B) Learned mapping dictionary hit    → confidence 0.95
  C) Normalized exact string match     → confidence 0.85
  D) Module-context + rapidfuzz        → confidence = fuzzy score (≥ threshold)
  E) Unit-hint + module match          → confidence 0.60
  -) Unmapped → top-5 candidate list
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.utils.text_normalizer import normalize, extract_unit_tokens

logger = logging.getLogger(__name__)

try:
    from rapidfuzz import process as rf_process, fuzz as rf_fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False
    logger.warning("rapidfuzz not installed — stage D fuzzy matching disabled")


@dataclass
class MapResult:
    """Outcome of mapping a single checklist row to a DB key"""
    row: int                         # Excel row number
    module: str                      # B-column (original)
    item: str                        # C-column (original)
    db_key: Optional[str]            # Matched DB key, or None if unmapped
    confidence: float                # 0.0–1.00
    source: str                      # 'explicit' | 'learned' | 'exact' | 'fuzzy' | 'unit_hint' | 'unmapped'
    candidates: List[str] = field(default_factory=list)  # top-5 when unmapped


class ChecklistMapper:
    """5-stage cascade mapper: checklist row → DB key"""

    DEFAULT_FUZZY_THRESHOLD = 0.80

    def __init__(self,
                 qc_lookup: Dict[str, any],
                 learned_mappings: List[Dict],
                 model: str = '',
                 fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD):
        """
        Args:
            qc_lookup: flat dict from ChecklistValidator._build_qc_lookup()
                       key format: 'Module.PartType.PartName.ItemName'
            learned_mappings: list of dicts from SyncManager._load_local_mappings()
                              each has: model, module, item_norm, db_key, confidence
            model: checklist model name (e.g. 'NX-Wafer 200mm') for filtering learned_mappings
            fuzzy_threshold: minimum score for stage D to accept a match (0–1)
        """
        self.qc_lookup = qc_lookup
        self.model = model
        self.fuzzy_threshold = fuzzy_threshold

        # All available DB keys (used for fuzzy search pool)
        self._all_keys: List[str] = list(qc_lookup.keys())

        # Normalized exact-match index: norm(item_name) → [db_key, ...]
        self._norm_index: Dict[str, List[str]] = self._build_norm_index()

        # Learned mapping: (norm_module, norm_item) → {db_key, confidence}
        self._learned: Dict[tuple, Dict] = self._build_learned_index(learned_mappings, model)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def map_rows(self, rows: List[Dict]) -> List[MapResult]:
        """Map a list of checklist rows.

        Each row dict must have: row (int), module (str), item (str),
        and optionally explicit_db_key (str from M-column).
        """
        return [self._map_single(r) for r in rows]

    def map_single(self, row: Dict) -> MapResult:
        return self._map_single(row)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _map_single(self, row: Dict) -> MapResult:
        row_num = row.get('row', 0)
        module = str(row.get('module', '')).strip()
        item = str(row.get('item', '')).strip()
        explicit_key = str(row.get('explicit_db_key') or '').strip()
        unit_hint = str(row.get('unit', '')).strip()

        norm_module = normalize(module)
        norm_item = normalize(item)

        # ---- Stage A: explicit M-column ----------------------------------
        if explicit_key and explicit_key in self.qc_lookup:
            return MapResult(row=row_num, module=module, item=item,
                             db_key=explicit_key, confidence=1.00, source='explicit')

        # ---- Stage B: learned dictionary ---------------------------------
        learned_hit = self._learned.get((norm_module, norm_item))
        if learned_hit:
            db_key = learned_hit['db_key']
            if db_key in self.qc_lookup:
                return MapResult(row=row_num, module=module, item=item,
                                 db_key=db_key, confidence=learned_hit.get('confidence', 0.95),
                                 source='learned')

        # ---- Stage C: normalized exact match -----------------------------
        exact_hits = self._norm_index.get(norm_item, [])
        if len(exact_hits) == 1:
            return MapResult(row=row_num, module=module, item=item,
                             db_key=exact_hits[0], confidence=0.85, source='exact')
        if len(exact_hits) > 1:
            # Disambiguate by module prefix
            module_filtered = [k for k in exact_hits
                               if k.lower().startswith(norm_module.split()[0])]
            if len(module_filtered) == 1:
                return MapResult(row=row_num, module=module, item=item,
                                 db_key=module_filtered[0], confidence=0.85, source='exact')

        # ---- Stage D: Module-context + rapidfuzz -------------------------
        if HAS_RAPIDFUZZ and self._all_keys:
            # Build module-filtered pool first
            pool = [k for k in self._all_keys
                    if norm_module and k.lower().split('.')[0].lower() == norm_module.split()[0].lower()]
            if not pool:
                pool = self._all_keys  # fall back to full pool

            results = rf_process.extractBests(
                norm_item,
                [normalize(k.split('.')[-1]) for k in pool],
                scorer=rf_fuzz.WRatio,
                score_cutoff=int(self.fuzzy_threshold * 100),
                limit=5,
            )
            if results:
                best_score = results[0][1] / 100.0
                best_idx = results[0][2]
                if best_score >= self.fuzzy_threshold:
                    return MapResult(row=row_num, module=module, item=item,
                                     db_key=pool[best_idx], confidence=round(best_score, 2),
                                     source='fuzzy',
                                     candidates=[pool[r[2]] for r in results[1:]])

        # ---- Stage E: unit-hint + module match ---------------------------
        unit_tokens = extract_unit_tokens(item)
        if unit_tokens and unit_hint:
            unit_norm = unit_hint.lower().strip()
            unit_matches = [
                k for k in self._all_keys
                if unit_norm in k.lower() or any(tok in k.lower() for tok in unit_tokens)
            ]
            if len(unit_matches) == 1:
                return MapResult(row=row_num, module=module, item=item,
                                 db_key=unit_matches[0], confidence=0.60, source='unit_hint')

        # ---- Unmapped — provide top-5 candidates -------------------------
        candidates: List[str] = []
        if HAS_RAPIDFUZZ and self._all_keys:
            top = rf_process.extractBests(
                norm_item,
                [normalize(k.split('.')[-1]) for k in self._all_keys],
                scorer=rf_fuzz.WRatio,
                limit=5,
            )
            candidates = [self._all_keys[r[2]] for r in top]

        return MapResult(row=row_num, module=module, item=item,
                         db_key=None, confidence=0.0, source='unmapped',
                         candidates=candidates)

    def _build_norm_index(self) -> Dict[str, List[str]]:
        """Build normalized item-name → [db_key] index from qc_lookup keys"""
        index: Dict[str, List[str]] = {}
        for key in self._all_keys:
            # The last segment of 'Module.PartType.PartName.ItemName' is the item name
            item_part = key.split('.')[-1] if '.' in key else key
            norm = normalize(item_part)
            index.setdefault(norm, []).append(key)
        return index

    def _build_learned_index(self, mappings: List[Dict], model: str) -> Dict[tuple, Dict]:
        """Build (norm_module, norm_item) → {db_key, confidence} from loaded cache"""
        index: Dict[tuple, Dict] = {}
        for m in mappings:
            if model and m.get('model', '') != model:
                continue
            key = (m.get('module', ''), m.get('item_norm', ''))
            index[key] = {'db_key': m['db_key'], 'confidence': float(m.get('confidence', 0.95))}
        return index
