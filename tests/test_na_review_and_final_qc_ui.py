from pathlib import Path
from types import SimpleNamespace

import pytest

import src.ui.final_checklist_qc_dialog as final_qc_dialog
import src.ui.main_window as main_window_module
import src.ui.na_review_dialog as na_review_dialog
from src.ui.final_checklist_qc_dialog import (
    APPROVAL_CHECKED,
    APPROVAL_EXCEPTION,
    APPROVAL_UNCHECKED,
    FILTER_ALL,
    FILTER_ATTENTION,
    FILTER_MISMATCH,
    FILTER_MISSING_CHECKLIST,
    FILTER_PROFILE_MATCHED,
    LANG_EN,
    LANG_KO,
    FinalChecklistQcDialog,
    _TREE_COLUMN_DEFS,
)
from src.ui.main_window import MainWindow


def test_na_review_profile_save_ui_and_flow_removed():
    for path in (Path("src/ui/na_review_dialog.py"), Path("src/ui/main_window.py")):
        text = path.read_text(encoding="utf-8")
        assert "save_to_profile" not in text
        assert "_save_exclusions_to_profile" not in text
        assert "이 선택을 프로파일에 저장" not in text
        assert "Save this selection to profile" not in text


def test_na_review_confirm_reruns_qc_without_profile_save(monkeypatch):
    class FakeRoot:
        def wait_window(self, _dialog):
            return None

    class FakeDialog:
        def __init__(self, parent, missing_items, profile_name, spec_manager=None):
            self.parent = parent
            self.missing_items = missing_items
            self.profile_name = profile_name
            self.spec_manager = spec_manager
            self.confirmed = True
            self.excluded_patterns = {"Dsp.FocusStage.General.*"}

    monkeypatch.setattr(na_review_dialog, "NaReviewDialog", FakeDialog)

    window = MainWindow.__new__(MainWindow)
    window.root = FakeRoot()
    window.current_profile = "NX-Wafer"
    window.spec_manager = object()
    reruns = []
    window.run_qc_inspection = lambda **kwargs: reruns.append(kwargs)
    window._save_exclusions_to_profile = lambda _patterns: pytest.fail("profile save must not be called")

    window._show_na_review_dialog([{"module": "Dsp"}])

    assert reruns == [{"excluded_modules": {"Dsp.FocusStage.General.*"}}]


def make_final_qc_dialog():
    dialog = FinalChecklistQcDialog.__new__(FinalChecklistQcDialog)
    dialog.language = LANG_EN
    dialog.show_mismatch_only = False
    dialog.current_filter = FILTER_ALL
    return dialog


def test_final_qc_language_defaults_to_english_in_constructor_source():
    text = Path("src/ui/final_checklist_qc_dialog.py").read_text(encoding="utf-8")
    assert "self.language = LANG_EN" in text


def test_final_qc_translation_helpers_switch_to_korean():
    dialog = make_final_qc_dialog()

    assert dialog._t("approve_selected") == "Approve Selected"
    assert dialog._t("unapprove_selected") == "Unapprove Selected"
    assert dialog._t("mark_exception") == "Set Exception"
    assert dialog._t("clear_approval") == "Reset All"
    assert dialog._display_term("status", "Mismatch") == "Mismatch"
    assert dialog._display_term("risk", "HighRisk") == "HighRisk"
    assert dialog._display_term("action", "Replace with QC Value") == "Replace with QC Value"
    assert dialog._display_term("source", "manual_candidate") == "manual_candidate"

    dialog.language = LANG_KO

    assert dialog._t("approve_selected") == "선택 승인"
    assert dialog._t("unapprove_selected") == "선택 해제"
    assert dialog._t("mark_exception") == "예외 설정"
    assert dialog._t("clear_approval") == "전체 초기화"
    assert dialog._display_term("status", "Mismatch") == "불일치"
    assert dialog._display_term("risk", "HighRisk") == "고위험"
    assert dialog._display_term("action", "Replace with QC Value") == "QC 값으로 교체"
    assert dialog._display_term("source", "manual_candidate") == "수동 후보"


def test_final_qc_reason_translation_preserves_internal_values():
    dialog = make_final_qc_dialog()
    reason = "Trusted explicit mapping"

    assert dialog._display_reason(reason) == reason

    dialog.language = LANG_KO

    assert dialog._display_reason(reason) == "신뢰된 명시 매핑"
    assert dialog._display_reason("Reviewer confirmation required") == "검수자 확인 필요"


def test_final_qc_language_toggle_preserves_review_state():
    dialog = make_final_qc_dialog()
    dialog.approved_rows = {3, 9}
    dialog.exception_rows = {7: "Keep by reviewer"}
    dialog.show_mismatch_only = True
    dialog.current_filter = FILTER_MISMATCH
    applied_languages = []
    dialog._apply_language = lambda: applied_languages.append(dialog.language)

    dialog._toggle_language()

    assert dialog.language == LANG_KO
    assert dialog.approved_rows == {3, 9}
    assert dialog.exception_rows == {7: "Keep by reviewer"}
    assert dialog.show_mismatch_only is True
    assert dialog.current_filter == FILTER_MISMATCH
    assert applied_languages == [LANG_KO]


def test_final_qc_check_item_width_and_measurement_header():
    columns = {col: (heading_key, width) for col, heading_key, width, _anchor in _TREE_COLUMN_DEFS}
    dialog = make_final_qc_dialog()

    assert columns["item"][1] >= 360
    assert dialog._t(columns["current"][0]) == "Checklist Measurement (G)"

    dialog.language = LANG_KO

    assert dialog._t(columns["current"][0]) == "체크리스트 측정값(G)"


def test_profile_coverage_excludes_no_spec_and_counts_missing_extra_keys():
    qc_report = {
        "results": [
            {"module": "Dsp", "part_type": "Stage", "part_name": "A", "item_name": "One", "spec": {"x": 1}, "actual_value": 1, "status": "PASS"},
            {"module": "Dsp", "part_type": "Stage", "part_name": "A", "item_name": "Two", "spec": {"x": 2}, "actual_value": 2, "status": "PASS"},
            {"module": "Dsp", "part_type": "Stage", "part_name": "A", "item_name": "NoSpec", "spec": None, "actual_value": 3, "status": "NO_SPEC"},
        ]
    }
    rows = [
        SimpleNamespace(db_key="Dsp.Stage.A.One"),
        SimpleNamespace(db_key="Extra.Stage.A.Item"),
    ]

    coverage = FinalChecklistQcDialog._build_profile_coverage(qc_report, rows)

    assert coverage["profile_count"] == 2
    assert coverage["mapped_count"] == 1
    assert coverage["missing_count"] == 1
    assert coverage["extra_count"] == 1
    assert coverage["missing_items"][0]["db_key"] == "Dsp.Stage.A.Two"


def test_final_qc_filters_visible_rows_by_attention_mismatch_and_profile_match():
    dialog = make_final_qc_dialog()
    rows = [
        SimpleNamespace(row=1, status="OK", risk_level="OK", db_key="Dsp.Stage.A.One"),
        SimpleNamespace(row=2, status="Mismatch", risk_level="Safe", db_key="Dsp.Stage.A.Two"),
        SimpleNamespace(row=3, status="Unmapped", risk_level="Blocked", db_key=None),
        SimpleNamespace(row=4, status="OK", risk_level="OK", db_key="Extra.Stage.A.Item"),
    ]
    dialog.report = SimpleNamespace(rows=rows)
    dialog.profile_coverage = {"profile_keys": {"Dsp.Stage.A.One", "Dsp.Stage.A.Two"}}

    dialog.current_filter = FILTER_ATTENTION
    assert [row.row for row in dialog._visible_rows()] == [2, 3]

    dialog.current_filter = FILTER_MISMATCH
    assert [row.row for row in dialog._visible_rows()] == [2]

    dialog.current_filter = FILTER_PROFILE_MATCHED
    assert [row.row for row in dialog._visible_rows()] == [1, 2]


def test_missing_checklist_selection_is_read_only():
    class FakeTree:
        def selection(self):
            return ["missing:Dsp.Stage.A.Two", "2"]

    class FakeReport:
        def get_row(self, row_number):
            return SimpleNamespace(row=row_number)

    dialog = make_final_qc_dialog()
    dialog.report = FakeReport()
    dialog.tree = FakeTree()

    assert [row.row for row in dialog._selected_rows()] == [2]


def test_mismatch_review_button_removed_but_filter_remains():
    dialog = make_final_qc_dialog()
    text = Path("src/ui/final_checklist_qc_dialog.py").read_text(encoding="utf-8")

    assert "btn_mismatch" not in text
    assert "help_mismatch_review" not in text
    assert "_toggle_mismatch_review" not in text

    dialog._set_filter = lambda filter_key, update_segmented=True: setattr(dialog, "current_filter", filter_key)
    dialog._on_filter_changed("Mismatch")
    assert dialog.current_filter == FILTER_MISMATCH


def test_help_tooltip_text_is_bilingual():
    dialog = make_final_qc_dialog()

    assert "approved" in dialog._t("help_apply_approved").lower()

    dialog.language = LANG_KO

    assert "승인" in dialog._t("help_apply_approved")


def test_help_tooltip_lifecycle_source_hides_on_leave_and_destroy():
    text = Path("src/ui/final_checklist_qc_dialog.py").read_text(encoding="utf-8")

    assert 'widget.bind("<Leave>", self.hide)' in text
    assert 'widget.bind("<ButtonPress>", self.hide)' in text
    assert 'widget.bind("<FocusOut>", self.hide)' in text
    assert 'widget.bind("<Destroy>", self.destroy)' in text
    assert "after_cancel" in text
    assert "HelpTooltip.hide_active()" in text


class FakeFinalQcTree:
    def __init__(self, columns, values_by_id, selection=()):
        self._columns = tuple(columns)
        self._values_by_id = {str(key): tuple(value) for key, value in values_by_id.items()}
        self._selection = list(selection)
        self.selected_items = []
        self.seen_items = []

    def __getitem__(self, key):
        if key == "columns":
            return self._columns
        raise KeyError(key)

    def item(self, item_id, option=None):
        if option == "values":
            return self._values_by_id.get(str(item_id), ())
        return {"values": self._values_by_id.get(str(item_id), ())}

    def selection(self):
        return list(self._selection)

    def get_children(self, _item=""):
        return tuple(self._values_by_id)

    def selection_set(self, item_id):
        self.selected_items.append(str(item_id))
        self._selection = [str(item_id)]

    def see(self, item_id):
        self.seen_items.append(str(item_id))


class FakeFinalQcReport:
    def __init__(self, rows):
        self._rows = rows

    def get_row(self, row_number):
        return self._rows.get(row_number)


class FakeProfileViewerTree:
    def __init__(self):
        self.rows = {}
        self.deleted = []
        self.next_id = 1

    def selection(self):
        return []

    def get_children(self):
        return list(self.rows)

    def delete(self, item):
        self.deleted.append(item)
        self.rows.pop(item, None)

    def insert(self, _parent, _index, values=(), tags=()):
        item_id = f"item{self.next_id}"
        self.next_id += 1
        self.rows[item_id] = {"values": tuple(values), "tags": tuple(tags)}
        return item_id

    def selection_set(self, _item):
        return None

    def see(self, _item):
        return None


class FakeEntry:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def delete(self, _start, _end):
        self.value = ""


class FakeLabel:
    def __init__(self):
        self.kwargs = {}

    def configure(self, **kwargs):
        self.kwargs.update(kwargs)


def make_tree_values(**overrides):
    columns = tuple(col for col, _heading, _width, _anchor in _TREE_COLUMN_DEFS)
    values = {column: "" for column in columns}
    values.update(overrides)
    return tuple(values[column] for column in columns)


def attach_fake_clipboard(dialog):
    copied = []
    dialog.clipboard_clear = copied.clear
    dialog.clipboard_append = copied.append
    dialog.update_idletasks = lambda: None
    return copied


def test_approval_marker_uses_checkbox_display_values():
    dialog = make_final_qc_dialog()
    row = SimpleNamespace(row=5)

    dialog.approved_rows = set()
    dialog.exception_rows = {}
    assert dialog._approval_marker(row) == APPROVAL_UNCHECKED

    dialog.approved_rows = {5}
    assert dialog._approval_marker(row) == APPROVAL_CHECKED

    dialog.exception_rows = {5: "Keep current value"}
    assert dialog._approval_marker(row) == APPROVAL_EXCEPTION


def test_toggle_approval_for_item_approves_unapproves_and_clears_exception():
    columns = tuple(col for col, _heading, _width, _anchor in _TREE_COLUMN_DEFS)
    dialog = make_final_qc_dialog()
    dialog.approved_rows = set()
    dialog.exception_rows = {5: "Keep current value"}
    dialog.tree = FakeFinalQcTree(columns, {"5": make_tree_values(row="5")}, selection=("5",))
    dialog.report = FakeFinalQcReport({
        5: SimpleNamespace(row=5, is_writable=True),
    })
    populate_calls = []
    dialog._populate_tree = lambda: populate_calls.append(True)

    assert dialog._toggle_approval_for_item("5") is True
    assert dialog.approved_rows == {5}
    assert dialog.exception_rows == {}

    assert dialog._toggle_approval_for_item("5") is True
    assert dialog.approved_rows == set()
    assert populate_calls == [True, True]


def test_toggle_approval_for_item_ignores_blocked_and_diagnostic_rows():
    columns = tuple(col for col, _heading, _width, _anchor in _TREE_COLUMN_DEFS)
    dialog = make_final_qc_dialog()
    dialog.approved_rows = set()
    dialog.exception_rows = {}
    dialog.tree = FakeFinalQcTree(columns, {"8": make_tree_values(row="8")}, selection=("8",))
    dialog.report = FakeFinalQcReport({
        8: SimpleNamespace(row=8, is_writable=False),
    })
    dialog._populate_tree = lambda: pytest.fail("non-writable rows must not repopulate")

    assert dialog._toggle_approval_for_item("8") is False
    assert dialog._toggle_approval_for_item("missing:Dsp.Stage.A.Two") is False
    assert dialog.approved_rows == set()


def test_unapprove_selected_removes_only_selected_approvals():
    class FakeTree:
        def selection(self):
            return ["2", "3"]

    dialog = make_final_qc_dialog()
    dialog.tree = FakeTree()
    dialog.report = FakeFinalQcReport({
        2: SimpleNamespace(row=2),
        3: SimpleNamespace(row=3),
    })
    dialog.approved_rows = {1, 2, 3}
    dialog.exception_rows = {3: "Keep current value"}
    populate_calls = []
    dialog._populate_tree = lambda: populate_calls.append(True)

    dialog._unapprove_selected()

    assert dialog.approved_rows == {1}
    assert dialog.exception_rows == {3: "Keep current value"}
    assert populate_calls == [True]


def test_reset_all_requires_confirmation(monkeypatch):
    dialog = make_final_qc_dialog()
    dialog.approved_rows = {1, 2}
    dialog.exception_rows = {3: "Keep current value"}
    dialog._populate_tree = lambda: pytest.fail("reset must not run when cancelled")
    monkeypatch.setattr(final_qc_dialog.messagebox, "askyesno", lambda *args, **kwargs: False)

    dialog._clear_approval()

    assert dialog.approved_rows == {1, 2}
    assert dialog.exception_rows == {3: "Keep current value"}

    populate_calls = []
    dialog._populate_tree = lambda: populate_calls.append(True)
    monkeypatch.setattr(final_qc_dialog.messagebox, "askyesno", lambda *args, **kwargs: True)

    dialog._clear_approval()

    assert dialog.approved_rows == set()
    assert dialog.exception_rows == {}
    assert populate_calls == [True]


def test_copy_active_db_key_cell_uses_internal_raw_key():
    columns = tuple(col for col, _heading, _width, _anchor in _TREE_COLUMN_DEFS)
    dialog = make_final_qc_dialog()
    dialog.tree = FakeFinalQcTree(
        columns,
        {
            "7": make_tree_values(row="7", db_key="(unmapped)", item="MicronLowerLimit"),
        },
        selection=("7",),
    )
    dialog.report = FakeFinalQcReport({
        7: SimpleNamespace(row=7, db_key="Dsp.FocusStage.General.MicronLowerLimit")
    })
    dialog._last_tree_cell = ("7", f"#{columns.index('db_key') + 1}")
    copied = attach_fake_clipboard(dialog)

    assert dialog._copy_active_cell() == "break"
    assert copied == ["Dsp.FocusStage.General.MicronLowerLimit"]


def test_copy_db_key_supports_missing_checklist_diagnostic_rows():
    columns = tuple(col for col, _heading, _width, _anchor in _TREE_COLUMN_DEFS)
    dialog = make_final_qc_dialog()
    dialog.tree = FakeFinalQcTree(
        columns,
        {
            "missing:Dsp.Stage.A.Two": make_tree_values(
                row="-",
                status="Missing in Checklist",
                db_key="Dsp.Stage.A.Two",
            ),
        },
        selection=("missing:Dsp.Stage.A.Two",),
    )
    dialog.report = None
    copied = attach_fake_clipboard(dialog)

    assert dialog._copy_db_key("missing:Dsp.Stage.A.Two") == "break"
    assert copied == ["Dsp.Stage.A.Two"]


def test_copy_row_outputs_tab_separated_values_for_excel():
    columns = tuple(col for col, _heading, _width, _anchor in _TREE_COLUMN_DEFS)
    dialog = make_final_qc_dialog()
    dialog.tree = FakeFinalQcTree(
        columns,
        {
            "9": make_tree_values(
                approved=APPROVAL_CHECKED,
                row="9",
                status="Mismatch",
                item="UpperLimit",
                db_key="display-db-key",
                qc="100",
            ),
        },
        selection=("9",),
    )
    dialog.report = FakeFinalQcReport({
        9: SimpleNamespace(row=9, db_key="Dsp.FocusStage.General.UpperLimit")
    })
    copied = attach_fake_clipboard(dialog)

    assert dialog._copy_row("9") == "break"

    copied_values = copied[0].split("\t")
    assert len(copied_values) == len(columns)
    assert copied_values[columns.index("db_key")] == "Dsp.FocusStage.General.UpperLimit"
    assert copied_values[columns.index("item")] == "UpperLimit"


def test_profile_viewer_search_and_status_filter_are_combined():
    window = MainWindow.__new__(MainWindow)
    window.viewer_filter = "PASS"
    window.viewer_search_query = ""
    window._viewer_counts = {"ALL": 3, "PASS": 2, "CHECK": 1, "FAIL": 0, "PENDING": 0}
    window._all_viewer_rows = [
        (("Dsp", "Stage", "A", "UpperLimit", "EXACT", "= 1", "", "1"), "pass"),
        (("Dsp", "Stage", "A", "LowerLimit", "EXACT", "= 0", "", "0"), "pass"),
        (("Vision", "Camera", "A", "UpperLimit", "CHECK", "-", "", "CHECK"), "check"),
    ]
    window.profile_viewer_tree = FakeProfileViewerTree()
    window.profile_viewer_search = FakeEntry("upper")
    window.profile_viewer_count_label = FakeLabel()

    window._apply_viewer_filter()

    shown = [row["values"] for row in window.profile_viewer_tree.rows.values()]
    assert shown == [("Dsp", "Stage", "A", "UpperLimit", "EXACT", "= 1", "", "1")]
    assert window.profile_viewer_count_label.kwargs["text"] == "(1 of 3 items)"


def test_checklist_file_picker_uses_and_updates_separate_last_checklist_dir(monkeypatch):
    window = MainWindow.__new__(MainWindow)
    window.last_checklist_dir = "C:/ChecklistRoot"
    saved = []
    captured = {}

    def fake_askopenfilename(**kwargs):
        captured.update(kwargs)
        return "C:/ChecklistRoot/Job/A.xlsx"

    monkeypatch.setattr(main_window_module.filedialog, "askopenfilename", fake_askopenfilename)
    window._save_checklist_dir_path = lambda path: saved.append(path)

    selected = window._select_checklist_file("Select Checklist")

    assert selected == "C:/ChecklistRoot/Job/A.xlsx"
    assert captured["initialdir"] == "C:/ChecklistRoot"
    expected_dir = str(Path("C:/ChecklistRoot/Job/A.xlsx").parent)
    assert window.last_checklist_dir == expected_dir
    assert saved == [expected_dir]


def test_final_qc_dialog_source_is_modeless_and_has_maximize_controls():
    text = Path("src/ui/final_checklist_qc_dialog.py").read_text(encoding="utf-8")
    main_text = Path("src/ui/main_window.py").read_text(encoding="utf-8")

    assert "self.grab_set()" not in text
    assert "self.transient(parent)" not in text
    assert '"maximize"' in text
    assert '"restore"' in text
    assert "state(\"zoomed\")" in text
    final_qc_section = main_text.split("def final_checklist_qc", 1)[1].split("def autofill_checklist", 1)[0]
    assert "self.root.wait_window(dialog)" not in final_qc_section
    assert "Final Checklist QC opened" in main_text
