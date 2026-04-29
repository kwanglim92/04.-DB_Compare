from src.ui.server_spec_manager import SpecItemDialog


BASE_VALUES = {
    "module": "Dsp",
    "part_type": "FocusStage",
    "part_name": "General",
    "item_name": "MicronLowerLimit",
    "unit": "um",
}


class FakeEntry:
    def __init__(self):
        self.configs = []

    def configure(self, **kwargs):
        self.configs.append(kwargs)


def build_spec(**overrides):
    values = {
        **BASE_VALUES,
        "validation_type": "range",
        "min_text": "0.1",
        "max_text": "0.3",
        "expected_text": "",
        **overrides,
    }
    return SpecItemDialog._build_spec_from_values(**values)


def test_range_rejects_non_numeric_min():
    spec, error = build_spec(min_text="abc")

    assert spec is None
    assert error == "Min must be a number."


def test_range_rejects_min_greater_than_max():
    spec, error = build_spec(min_text="10", max_text="5")

    assert spec is None
    assert error == "Min cannot be greater than Max."


def test_range_allows_only_one_bound():
    spec, error = build_spec(min_text="", max_text="5")

    assert error == ""
    assert spec["min_spec"] is None
    assert spec["max_spec"] == 5.0


def test_exact_requires_expected_value():
    spec, error = build_spec(
        validation_type="exact",
        min_text="",
        max_text="",
        expected_text="",
    )

    assert spec is None
    assert error == "Expected Value is required for Exact items."


def test_check_allows_no_spec_value():
    spec, error = build_spec(
        validation_type="check",
        min_text="",
        max_text="",
        expected_text="",
    )

    assert error == ""
    assert spec == {
        **BASE_VALUES,
        "validation_type": "check",
        "enabled": True,
        "description": "",
    }


def test_edit_mode_locks_key_fields():
    dialog = SpecItemDialog.__new__(SpecItemDialog)
    dialog.module_entry = FakeEntry()
    dialog.ptype_entry = FakeEntry()
    dialog.pname_entry = FakeEntry()
    dialog.iname_entry = FakeEntry()

    dialog._lock_key_fields()

    for attr in SpecItemDialog.KEY_ENTRY_ATTRS:
        entry = getattr(dialog, attr)
        assert entry.configs == [{"state": "disabled"}]


def test_add_mode_leaves_key_fields_editable():
    dialog = SpecItemDialog.__new__(SpecItemDialog)
    dialog._is_edit = False
    dialog.module_entry = FakeEntry()
    dialog.ptype_entry = FakeEntry()
    dialog.pname_entry = FakeEntry()
    dialog.iname_entry = FakeEntry()

    dialog._apply_key_field_state()

    for attr in SpecItemDialog.KEY_ENTRY_ATTRS:
        entry = getattr(dialog, attr)
        assert entry.configs == []
