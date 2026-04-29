from pathlib import Path

import pytest

import src.ui.server_spec_manager as server_spec_manager
from src.ui.server_spec_manager import SPEC_FILTER_NEEDS_SETUP, ServerSpecManagerPanel


TARGET_ADMIN_UI_FILES = [
    Path("src/ui/admin_window.py"),
    Path("src/ui/server_settings_dialog.py"),
    Path("src/ui/server_spec_manager.py"),
    Path("src/ui/report_template_panel.py"),
]


class FakeDbManager:
    def __init__(self, delete_result=True):
        self.delete_result = delete_result
        self.deleted_profile_ids = []

    def delete_profile(self, profile_id):
        self.deleted_profile_ids.append(profile_id)
        return self.delete_result


class FakeTabView:
    def __init__(self):
        self.selected = []

    def set(self, name):
        self.selected.append(name)


def make_profile_panel():
    panel = ServerSpecManagerPanel.__new__(ServerSpecManagerPanel)
    panel.read_only = False
    panel.profiles = [
        {"id": 101, "profile_name": "Profile A"},
        {"id": 202, "profile_name": "Profile B"},
    ]
    panel.db_manager = FakeDbManager()
    panel.tabview = FakeTabView()
    panel.status_messages = []
    panel.rebuild_count = 0
    panel.change_count = 0
    panel._get_current_profile_meta = lambda: ("Profile A", {"profile_id": 101})
    panel._rebuild_tabs = lambda: setattr(panel, "rebuild_count", panel.rebuild_count + 1)
    panel._set_status = lambda text: panel.status_messages.append(text)
    panel._notify_change = lambda: setattr(panel, "change_count", panel.change_count + 1)
    return panel


def patch_delete_prompts(monkeypatch, *, confirm=True, password="admin-secret"):
    errors = []
    password_prompts = []
    monkeypatch.setattr(server_spec_manager, "ADMIN_PASSWORD", "admin-secret")
    monkeypatch.setattr(server_spec_manager.messagebox, "askyesno", lambda *args, **kwargs: confirm)

    def fake_askstring(*args, **kwargs):
        password_prompts.append((args, kwargs))
        return password

    monkeypatch.setattr(server_spec_manager.simpledialog, "askstring", fake_askstring)
    monkeypatch.setattr(
        server_spec_manager.messagebox,
        "showerror",
        lambda *args, **kwargs: errors.append((args, kwargs)),
    )
    return errors, password_prompts


def test_admin_ui_target_files_have_no_korean_text():
    for path in TARGET_ADMIN_UI_FILES:
        text = path.read_text(encoding="utf-8")
        assert not any("\uac00" <= char <= "\ud7a3" for char in text), path


def test_profile_delete_cancelled_at_warning_does_not_delete(monkeypatch):
    panel = make_profile_panel()
    _, password_prompts = patch_delete_prompts(monkeypatch, confirm=False)

    panel._delete_profile()

    assert panel.db_manager.deleted_profile_ids == []
    assert password_prompts == []
    assert panel.profiles == [
        {"id": 101, "profile_name": "Profile A"},
        {"id": 202, "profile_name": "Profile B"},
    ]


def test_profile_delete_cancelled_at_password_prompt_does_not_delete(monkeypatch):
    panel = make_profile_panel()
    patch_delete_prompts(monkeypatch, confirm=True, password=None)

    panel._delete_profile()

    assert panel.db_manager.deleted_profile_ids == []
    assert panel.rebuild_count == 0
    assert panel.change_count == 0


def test_profile_delete_wrong_password_does_not_delete(monkeypatch):
    panel = make_profile_panel()
    errors, _ = patch_delete_prompts(monkeypatch, confirm=True, password="wrong")

    panel._delete_profile()

    assert panel.db_manager.deleted_profile_ids == []
    assert panel.rebuild_count == 0
    assert panel.change_count == 0
    assert errors


def test_profile_delete_correct_password_deletes_and_refreshes(monkeypatch):
    panel = make_profile_panel()
    patch_delete_prompts(monkeypatch, confirm=True, password="admin-secret")

    panel._delete_profile()

    assert panel.db_manager.deleted_profile_ids == [101]
    assert panel.profiles == [{"id": 202, "profile_name": "Profile B"}]
    assert panel.rebuild_count == 1
    assert panel.tabview.selected == ["Common Base"]
    assert panel.status_messages == ["Profile deleted: Profile A"]
    assert panel.change_count == 1


def test_spec_setup_filter_classifies_unconfigured_type_and_spec_values():
    assert ServerSpecManagerPanel._needs_spec_setup({"validation_type": ""}) is True
    assert ServerSpecManagerPanel._needs_spec_setup({"validation_type": "range", "min_spec": None, "max_spec": ""}) is True
    assert ServerSpecManagerPanel._needs_spec_setup({"validation_type": "range", "min_spec": 0, "max_spec": ""}) is False
    assert ServerSpecManagerPanel._needs_spec_setup({"validation_type": "exact", "expected_value": ""}) is True
    assert ServerSpecManagerPanel._needs_spec_setup({"validation_type": "exact", "expected_value": "1"}) is False
    assert ServerSpecManagerPanel._needs_spec_setup({"validation_type": "check"}) is False


def test_spec_setup_filter_combines_with_search_query():
    panel = ServerSpecManagerPanel.__new__(ServerSpecManagerPanel)
    rows = [
        {"module": "Dsp", "part_type": "Stage", "part_name": "General", "item_name": "NeedsRange", "validation_type": "range", "min_spec": None, "max_spec": None},
        {"module": "Dsp", "part_type": "Stage", "part_name": "General", "item_name": "Configured", "validation_type": "exact", "expected_value": "1"},
        {"module": "Vision", "part_type": "Camera", "part_name": "A", "item_name": "NeedsExact", "validation_type": "exact", "expected_value": ""},
    ]

    searched = panel._filter_rows(rows, "needs")
    filtered = panel._filter_rows_for_setup_state(searched, SPEC_FILTER_NEEDS_SETUP)

    assert [row["item_name"] for row in filtered] == ["NeedsRange", "NeedsExact"]
