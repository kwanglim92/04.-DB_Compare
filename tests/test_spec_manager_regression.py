"""
Regression tests for SpecManager (src/core/spec_manager.py)
Ensures existing functionality remains intact after server-sync additions.
"""

import json
import pytest
from pathlib import Path
from copy import deepcopy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

COMMON_BASE_DATA = {
    "_version": "2.0",
    "_description": "Test common base",
    "specs": {
        "Dsp": {
            "XScanner": {
                "100um": [
                    {
                        "item_name": "ServoCutoffFrequencyHz",
                        "validation_type": "range",
                        "min_spec": 70.0,
                        "max_spec": 90.0,
                        "unit": "Hz",
                        "enabled": True
                    },
                    {
                        "item_name": "ScanningRangeDefaultLow",
                        "validation_type": "range",
                        "min_spec": 0.1,
                        "max_spec": 0.3,
                        "unit": "um",
                        "enabled": True
                    }
                ]
            }
        }
    }
}

PROFILE_DATA = {
    "_version": "2.0",
    "_description": "Test Equipment A",
    "inherits_from": "Common_Base",
    "excluded_items": [],
    "overrides": {
        "Dsp": {
            "XScanner": {
                "100um": [
                    {
                        "item_name": "ServoCutoffFrequencyHz",
                        "min_spec": 75.0,
                        "max_spec": 85.0
                    }
                ]
            }
        }
    },
    "additional_checks": {
        "Profiler": {
            "ZScanner": {
                "Standard": [
                    {
                        "item_name": "FocusOffset",
                        "validation_type": "range",
                        "min_spec": -5.0,
                        "max_spec": 5.0,
                        "unit": "um",
                        "enabled": True
                    }
                ]
            }
        }
    }
}


@pytest.fixture
def config_dir(tmp_path):
    """Create a temp config directory with common_base.json and one profile."""
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "profiles").mkdir()

    with open(cfg / "common_base.json", "w", encoding="utf-8") as f:
        json.dump(COMMON_BASE_DATA, f, indent=2, ensure_ascii=False)

    with open(cfg / "profiles" / "EquipA.json", "w", encoding="utf-8") as f:
        json.dump(PROFILE_DATA, f, indent=2, ensure_ascii=False)

    return cfg


@pytest.fixture
def spec_manager(config_dir):
    from src.core.spec_manager import SpecManager
    sm = SpecManager()
    sm.load_multi_file_config(config_dir)
    return sm, config_dir


# ---------------------------------------------------------------------------
# 1. Multi-file config loading
# ---------------------------------------------------------------------------

class TestMultiFileConfigLoading:
    def test_common_base_loaded(self, spec_manager):
        """Given valid config_dir, When load_multi_file_config(), Then Common_Base is present."""
        sm, _ = spec_manager
        assert "Common_Base" in sm.base_profiles

    def test_equipment_profile_loaded(self, spec_manager):
        """Given profiles/ with EquipA.json, When loaded, Then EquipA is in equipment_profiles."""
        sm, _ = spec_manager
        assert "EquipA" in sm.equipment_profiles

    def test_returns_true_on_valid_dir(self, config_dir):
        """When load_multi_file_config() with valid dir, Then returns True."""
        from src.core.spec_manager import SpecManager
        sm = SpecManager()
        result = sm.load_multi_file_config(config_dir)
        assert result is True

    def test_returns_false_on_invalid_dir(self, tmp_path):
        """When load_multi_file_config() called on dir with corrupt JSON, Then returns False."""
        cfg = tmp_path / "bad_config"
        cfg.mkdir()
        (cfg / "common_base.json").write_text("NOT_JSON", encoding="utf-8")
        from src.core.spec_manager import SpecManager
        sm = SpecManager()
        result = sm.load_multi_file_config(cfg)
        assert result is False


# ---------------------------------------------------------------------------
# 2. Profile name listing
# ---------------------------------------------------------------------------

class TestGetAllProfileNames:
    def test_returns_equipment_profile_names(self, spec_manager):
        """When get_all_profile_names(), Then ['EquipA'] is returned."""
        sm, _ = spec_manager
        names = sm.get_all_profile_names()
        assert "EquipA" in names

    def test_returns_empty_when_no_profiles(self, tmp_path):
        """Given config with no profiles, When get_all_profile_names(), Then empty list."""
        cfg = tmp_path / "config"
        cfg.mkdir()
        with open(cfg / "common_base.json", "w") as f:
            json.dump(COMMON_BASE_DATA, f)
        from src.core.spec_manager import SpecManager
        sm = SpecManager()
        sm.load_multi_file_config(cfg)
        assert sm.get_all_profile_names() == []


# ---------------------------------------------------------------------------
# 3. load_profile_with_inheritance
# ---------------------------------------------------------------------------

class TestLoadProfileWithInheritance:
    def test_base_specs_included_in_result(self, spec_manager):
        """When loading EquipA, Then Dsp.XScanner.100um items from Common_Base are present."""
        sm, _ = spec_manager
        result = sm.load_profile_with_inheritance("EquipA")
        assert "Dsp" in result
        assert "XScanner" in result["Dsp"]
        assert "100um" in result["Dsp"]["XScanner"]

    def test_override_is_applied(self, spec_manager):
        """When loading EquipA, Then ServoCutoffFrequencyHz override values are applied."""
        sm, _ = spec_manager
        result = sm.load_profile_with_inheritance("EquipA")
        items = result["Dsp"]["XScanner"]["100um"]
        servo_item = next((i for i in items if i["item_name"] == "ServoCutoffFrequencyHz"), None)
        assert servo_item is not None
        assert servo_item["min_spec"] == 75.0
        assert servo_item["max_spec"] == 85.0

    def test_additional_checks_appended(self, spec_manager):
        """When loading EquipA, Then Profiler.ZScanner.Standard items are present."""
        sm, _ = spec_manager
        result = sm.load_profile_with_inheritance("EquipA")
        assert "Profiler" in result
        assert "ZScanner" in result["Profiler"]

    def test_returns_none_for_unknown_profile(self, spec_manager):
        """Given unknown profile name, When load_profile_with_inheritance(), Then None returned."""
        sm, _ = spec_manager
        result = sm.load_profile_with_inheritance("NonExistentProfile")
        assert result is None

    def test_does_not_mutate_base_profile(self, spec_manager):
        """When loading a profile twice, Then the base profile data is not mutated."""
        sm, _ = spec_manager
        before = deepcopy(sm.base_profiles["Common_Base"]["specs"])
        sm.load_profile_with_inheritance("EquipA")
        sm.load_profile_with_inheritance("EquipA")
        after = sm.base_profiles["Common_Base"]["specs"]
        assert before == after


# ---------------------------------------------------------------------------
# 4. exclusions
# ---------------------------------------------------------------------------

class TestExclusions:
    def test_excluded_item_removed_from_result(self, config_dir):
        """Given excluded_items pattern, When profile loaded, Then item is absent."""
        # Add exclusion to EquipA profile
        profile_file = config_dir / "profiles" / "EquipA.json"
        data = json.loads(profile_file.read_text(encoding="utf-8"))
        data["excluded_items"] = ["Dsp.XScanner.100um.ScanningRangeDefaultLow"]
        profile_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        from src.core.spec_manager import SpecManager
        sm = SpecManager()
        sm.load_multi_file_config(config_dir)
        result = sm.load_profile_with_inheritance("EquipA")

        items_100um = result.get("Dsp", {}).get("XScanner", {}).get("100um", [])
        item_names = [i["item_name"] for i in items_100um]
        assert "ScanningRangeDefaultLow" not in item_names

    def test_wildcard_exclusion_removes_all_module_items(self, config_dir):
        """Given wildcard exclusion 'Dsp.*.*.*', When profile loaded, Then Dsp is absent."""
        profile_file = config_dir / "profiles" / "EquipA.json"
        data = json.loads(profile_file.read_text(encoding="utf-8"))
        data["excluded_items"] = ["Dsp.*.*.*"]
        profile_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        from src.core.spec_manager import SpecManager
        sm = SpecManager()
        sm.load_multi_file_config(config_dir)
        result = sm.load_profile_with_inheritance("EquipA")
        assert "Dsp" not in result


# ---------------------------------------------------------------------------
# 5. add / remove / update Common_Base items
# ---------------------------------------------------------------------------

class TestCommonBaseEditing:
    def test_add_new_item_to_common_base(self, spec_manager):
        """When add_item_to_common_base(), Then new item appears in Common_Base specs."""
        sm, _ = spec_manager
        new_spec = {
            "item_name": "NewItem",
            "validation_type": "range",
            "min_spec": 1.0,
            "max_spec": 2.0,
            "enabled": True
        }
        result = sm.add_item_to_common_base("Dsp", "XScanner", "100um", new_spec)
        assert result is True
        items = sm.base_profiles["Common_Base"]["specs"]["Dsp"]["XScanner"]["100um"]
        names = [i["item_name"] for i in items]
        assert "NewItem" in names

    def test_update_existing_item_in_common_base(self, spec_manager):
        """When updating existing item, Then updated fields are stored."""
        sm, _ = spec_manager
        updated = {
            "item_name": "ServoCutoffFrequencyHz",
            "min_spec": 65.0,
            "max_spec": 95.0,
            "validation_type": "range",
            "enabled": True
        }
        sm.add_item_to_common_base("Dsp", "XScanner", "100um", updated)
        items = sm.base_profiles["Common_Base"]["specs"]["Dsp"]["XScanner"]["100um"]
        servo = next((i for i in items if i["item_name"] == "ServoCutoffFrequencyHz"), None)
        assert servo["min_spec"] == 65.0
        assert servo["max_spec"] == 95.0

    def test_remove_item_from_common_base(self, spec_manager):
        """When remove_item_from_common_base(), Then item is gone from specs."""
        sm, _ = spec_manager
        result = sm.remove_item_from_common_base("Dsp", "XScanner", "100um", "ServoCutoffFrequencyHz")
        assert result is True
        items = sm.base_profiles["Common_Base"]["specs"].get("Dsp", {}).get("XScanner", {}).get("100um", [])
        names = [i["item_name"] for i in items]
        assert "ServoCutoffFrequencyHz" not in names

    def test_remove_nonexistent_item_still_saves(self, spec_manager):
        """When removing item that does not exist, save still succeeds (no-op removal)."""
        sm, _ = spec_manager
        result = sm.remove_item_from_common_base("Dsp", "XScanner", "100um", "GhostItem")
        # Existing behavior: save_base_profile is called regardless, returns True
        assert result is True


# ---------------------------------------------------------------------------
# 6. get_common_base_specs (deep-copy safety)
# ---------------------------------------------------------------------------

class TestGetCommonBaseSpecs:
    def test_returns_copy_not_reference(self, spec_manager):
        """When get_common_base_specs() called, Then returned dict is independent of internal state."""
        sm, _ = spec_manager
        specs = sm.get_common_base_specs()
        specs["Dsp"]["XScanner"]["100um"] = []  # mutate the returned copy
        # Internal state should be unchanged
        internal = sm.base_profiles["Common_Base"]["specs"]["Dsp"]["XScanner"]["100um"]
        assert len(internal) > 0


# ---------------------------------------------------------------------------
# 7. save_equipment_profile (auto-cleanup of enabled:false items)
# ---------------------------------------------------------------------------

class TestSaveEquipmentProfileCleanup:
    def test_disabled_override_moved_to_excluded_items(self, spec_manager):
        """Given override with enabled:false, When save_equipment_profile(), Then item moved to excluded_items."""
        sm, config_dir = spec_manager
        # Add an override with enabled:false
        sm.equipment_profiles["EquipA"]["overrides"].setdefault("Dsp", {}).setdefault(
            "XScanner", {}).setdefault("100um", []).append({
                "item_name": "DisabledItem",
                "validation_type": "range",
                "min_spec": 0,
                "max_spec": 1,
                "enabled": False
            })
        sm.save_equipment_profile("EquipA")
        # After save, excluded_items should contain the disabled item path
        excluded = sm.equipment_profiles["EquipA"]["excluded_items"]
        assert any("DisabledItem" in e for e in excluded)


# ---------------------------------------------------------------------------
# 8. Legacy single-file load (backward compatibility)
# ---------------------------------------------------------------------------

class TestLegacySingleFileLoad:
    def test_load_spec_file_returns_true_on_valid_json(self, tmp_path):
        """Given legacy qc_specs.json, When load_spec_file(), Then True returned."""
        legacy = {
            "base_profiles": {"Base": {"description": "B", "specs": {}}},
            "equipment_profiles": {"EQ1": {"description": "E1", "inherits_from": "Base"}}
        }
        spec_file = tmp_path / "qc_specs.json"
        spec_file.write_text(json.dumps(legacy), encoding="utf-8")

        from src.core.spec_manager import SpecManager
        sm = SpecManager()
        result = sm.load_spec_file(str(spec_file))
        assert result is True
        assert "Base" in sm.base_profiles
        assert "EQ1" in sm.equipment_profiles

    def test_load_spec_file_returns_false_on_missing_file(self, tmp_path):
        """Given non-existent path, When load_spec_file(), Then False returned."""
        from src.core.spec_manager import SpecManager
        sm = SpecManager()
        result = sm.load_spec_file(str(tmp_path / "missing.json"))
        assert result is False

    def test_load_spec_file_returns_false_on_invalid_json(self, tmp_path):
        """Given invalid JSON, When load_spec_file(), Then False returned."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("NOT_JSON")
        from src.core.spec_manager import SpecManager
        sm = SpecManager()
        result = sm.load_spec_file(str(bad_file))
        assert result is False
