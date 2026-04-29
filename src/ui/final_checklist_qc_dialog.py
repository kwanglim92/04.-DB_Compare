"""
Final Checklist QC dialog.
"""

import logging
import threading
from pathlib import Path
from tkinter import Menu, messagebox, simpledialog, ttk

import customtkinter as ctk

from src.core.checklist_final_qc import (
    ACTION_DO_NOT_WRITE,
    ACTION_FILL,
    ACTION_NONE,
    ACTION_REPLACE,
    ACTION_REVIEW,
    PREFLIGHT_ERROR,
    PREFLIGHT_INFO,
    PREFLIGHT_WARNING,
    RISK_BLOCKED,
    RISK_HIGH,
    RISK_OK,
    RISK_REVIEW,
    RISK_SAFE,
    STATUS_MISSING,
    STATUS_MISMATCH,
    STATUS_NON_COMPARABLE,
    STATUS_OK,
    STATUS_PROTECTED,
    STATUS_SKIPPED_GROUP,
    STATUS_UNMAPPED,
    ChecklistFinalQcEngine,
)
from src.core.checklist_validator import ChecklistValidator

logger = logging.getLogger(__name__)


_STATUS_TAGS = {
    STATUS_OK: "ok",
    STATUS_MISSING: "missing",
    STATUS_MISMATCH: "mismatch",
    STATUS_UNMAPPED: "unmapped",
    STATUS_PROTECTED: "protected",
    STATUS_SKIPPED_GROUP: "skipped",
    STATUS_NON_COMPARABLE: "non_comparable",
}

LANG_EN = "en"
LANG_KO = "ko"

FILTER_ALL = "all"
FILTER_ATTENTION = "attention"
FILTER_MISMATCH = "mismatch"
FILTER_PROFILE_MATCHED = "profile_matched"
FILTER_MISSING_CHECKLIST = "missing_checklist"

APPROVAL_UNCHECKED = "☐"
APPROVAL_CHECKED = "☑"
APPROVAL_EXCEPTION = "!"

_TRANSLATIONS = {
    "window_title": {LANG_EN: "Final Checklist QC", LANG_KO: "최종 체크리스트 QC"},
    "language_toggle": {LANG_EN: "한국어", LANG_KO: "English"},
    "maximize": {LANG_EN: "Maximize", LANG_KO: "최대화"},
    "restore": {LANG_EN: "Restore", LANG_KO: "복원"},
    "file_profile": {LANG_EN: "File: {file}  |  Profile: {profile}", LANG_KO: "파일: {file}  |  프로필: {profile}"},
    "stat_ok": {LANG_EN: "OK", LANG_KO: "정상"},
    "stat_missing": {LANG_EN: "Missing", LANG_KO: "누락"},
    "stat_mismatch": {LANG_EN: "Mismatch", LANG_KO: "불일치"},
    "stat_unmapped": {LANG_EN: "Unmapped", LANG_KO: "미매핑"},
    "stat_protected": {LANG_EN: "Protected", LANG_KO: "보호"},
    "stat_blocked": {LANG_EN: "Blocked", LANG_KO: "차단"},
    "preflight_pending": {LANG_EN: "Preflight: pending", LANG_KO: "사전 검사: 대기 중"},
    "preflight_unavailable": {LANG_EN: "Preflight: not available", LANG_KO: "사전 검사: 사용할 수 없음"},
    "preflight_status": {
        LANG_EN: "Preflight: {errors} errors, {warnings} warnings, {info} info | Sheet: {sheet} | QC keys: {keys}",
        LANG_KO: "사전 검사: 오류 {errors}개, 경고 {warnings}개, 정보 {info}개 | 시트: {sheet} | QC 키: {keys}개",
    },
    "preflight_failed": {
        LANG_EN: "Preflight failed. Fix these issues before Final Checklist QC:",
        LANG_KO: "사전 검사 실패. Final Checklist QC 전에 아래 항목을 수정하세요:",
    },
    "approve_selected": {LANG_EN: "Approve Selected", LANG_KO: "선택 승인"},
    "unapprove_selected": {LANG_EN: "Unapprove Selected", LANG_KO: "선택 해제"},
    "approve_safe": {LANG_EN: "Approve Safe Corrections", LANG_KO: "안전 보정 승인"},
    "filter_label": {LANG_EN: "Filter:", LANG_KO: "필터:"},
    "filter_all": {LANG_EN: "All Rows", LANG_KO: "전체 행"},
    "filter_attention": {LANG_EN: "Needs Attention", LANG_KO: "확인 필요"},
    "filter_mismatch": {LANG_EN: "Mismatch", LANG_KO: "불일치"},
    "filter_profile_matched": {LANG_EN: "Profile Matched", LANG_KO: "Profile 매칭"},
    "filter_missing_checklist": {LANG_EN: "Missing in Checklist", LANG_KO: "체크리스트 누락"},
    "coverage_pending": {LANG_EN: "Profile Coverage: pending", LANG_KO: "Profile 매칭: 대기 중"},
    "coverage_status": {
        LANG_EN: "Profile Coverage: checklist mapped {mapped} / profile items {profile} | Missing from checklist {missing} | Extra checklist keys {extra}",
        LANG_KO: "Profile 매칭: 체크리스트 매핑 {mapped} / 프로필 항목 {profile} | 체크리스트 누락 {missing} | 추가 체크리스트 키 {extra}",
    },
    "mark_exception": {LANG_EN: "Set Exception", LANG_KO: "예외 설정"},
    "clear_approval": {LANG_EN: "Reset All", LANG_KO: "전체 초기화"},
    "write_db_key": {LANG_EN: "Write DB_Key to M column (internal copy)", LANG_KO: "DB_Key를 M열에 기록 (내부 사본)"},
    "status_analyzing": {LANG_EN: "Analyzing...", LANG_KO: "분석 중..."},
    "status_running_preflight": {LANG_EN: "Running preflight...", LANG_KO: "사전 검사 실행 중..."},
    "status_rows_analyzed": {
        LANG_EN: "{rows} rows analyzed | Model: {model}",
        LANG_KO: "{rows}개 행 분석 완료 | 모델: {model}",
    },
    "status_error": {LANG_EN: "Error: {error}", LANG_KO: "오류: {error}"},
    "status_writing_copy": {LANG_EN: "Writing approved rows to internal copy...", LANG_KO: "승인된 행을 내부 사본에 기록 중..."},
    "status_saved_copy": {LANG_EN: "Saved internal copy: {file}", LANG_KO: "내부 사본 저장 완료: {file}"},
    "candidate_label": {LANG_EN: "Unmapped candidate:", LANG_KO: "미매핑 후보:"},
    "use_candidate": {LANG_EN: "Use Candidate + Approve", LANG_KO: "후보 사용 + 승인"},
    "apply_approved": {LANG_EN: "Apply Approved to Internal Copy", LANG_KO: "승인 항목 내부 사본에 적용"},
    "close": {LANG_EN: "Close", LANG_KO: "닫기"},
    "msg_select_mismatch": {LANG_EN: "Select one or more Mismatch rows first.", LANG_KO: "먼저 불일치 행을 하나 이상 선택하세요."},
    "msg_exception_reason_required": {LANG_EN: "Exception reason is required.", LANG_KO: "예외 사유를 입력해야 합니다."},
    "msg_invalid_candidate": {LANG_EN: "Select a valid DB key candidate.", LANG_KO: "유효한 DB key 후보를 선택하세요."},
    "msg_no_approved": {LANG_EN: "No approved rows or exceptions to apply.", LANG_KO: "적용할 승인 행 또는 예외가 없습니다."},
    "confirm_reset_all": {
        LANG_EN: "Clear all approvals and exceptions?",
        LANG_KO: "모든 승인과 예외 설정을 초기화할까요?",
    },
    "exception_title": {LANG_EN: "Mismatch Exception", LANG_KO: "불일치 예외"},
    "exception_prompt": {LANG_EN: "Reason to keep the checklist value:", LANG_KO: "체크리스트 값을 유지하는 사유:"},
    "unmapped_placeholder": {LANG_EN: "(unmapped)", LANG_KO: "(미매핑)"},
    "missing_checklist_status": {LANG_EN: "Missing in Checklist", LANG_KO: "체크리스트 누락"},
    "missing_checklist_action": {LANG_EN: "Add or Map Checklist Row", LANG_KO: "체크리스트 행 추가 또는 매핑"},
    "missing_checklist_reason": {LANG_EN: "Profile item has no checklist DB_Key mapping.", LANG_KO: "Profile 항목에 대응되는 체크리스트 DB_Key 매핑이 없습니다."},
    "source_profile": {LANG_EN: "profile", LANG_KO: "프로필"},
    "copy_cell": {LANG_EN: "Copy Cell", LANG_KO: "셀 복사"},
    "copy_db_key": {LANG_EN: "Copy DB Key", LANG_KO: "DB 키 복사"},
    "copy_row": {LANG_EN: "Copy Row", LANG_KO: "행 복사"},
    "help_approve_selected": {
        LANG_EN: "Approves selected writable rows only. It does not write to Excel until Apply is clicked.",
        LANG_KO: "선택한 기입 가능 행만 승인합니다. Apply를 누르기 전까지 Excel에는 기록되지 않습니다.",
    },
    "help_unapprove_selected": {
        LANG_EN: "Removes approval from selected rows only. Exception settings are not changed.",
        LANG_KO: "선택한 행의 승인만 해제합니다. 예외 설정은 변경하지 않습니다.",
    },
    "help_approve_safe": {
        LANG_EN: "Selects only Safe Missing/Mismatch rows from trusted explicit, learned, or exact QC mappings.",
        LANG_KO: "명시/학습/정확 매핑으로 신뢰 가능한 Safe 누락/불일치 행만 승인 후보로 선택합니다.",
    },
    "help_mark_exception": {LANG_EN: "Sets an exception reason to keep the current checklist value without changing G column.", LANG_KO: "G열을 바꾸지 않고 현재 체크리스트 값을 유지할 예외 사유를 설정합니다."},
    "help_clear_approval": {LANG_EN: "Clears every approval and exception setting in this dialog after confirmation.", LANG_KO: "확인 후 현재 창의 모든 승인 후보와 예외 설정을 초기화합니다."},
    "help_write_db_key": {LANG_EN: "Writes DB_Key into M column only in the internal output copy.", LANG_KO: "내부 결과 사본에만 DB_Key를 M열에 기록합니다."},
    "help_use_candidate": {LANG_EN: "Uses the selected DB key candidate for one unmapped row and approves it if writable.", LANG_KO: "미매핑 행 하나에 선택한 DB key 후보를 적용하고 기입 가능하면 승인합니다."},
    "help_apply_approved": {LANG_EN: "Creates a new internal copy and writes only approved corrections. The original file is untouched.", LANG_KO: "새 내부 사본을 만들고 승인된 보정만 기록합니다. 원본 파일은 수정하지 않습니다."},
    "apply_done": {
        LANG_EN: (
            "Approved rows were written to an internal copy.\n\n"
            "Applied: {applied}\n"
            "Skipped: {skipped}\n"
            "Exceptions logged: {exceptions}\n"
            "Learned mappings: {learned}\n\n"
            "Remaining Missing: {missing}\n"
            "Remaining Mismatch: {mismatch}\n"
            "Remaining Unmapped: {unmapped}\n"
            "Remaining Blocked: {blocked}\n\n"
            "Output:\n{output}"
        ),
        LANG_KO: (
            "승인된 행을 내부 사본에 기록했습니다.\n\n"
            "적용: {applied}\n"
            "건너뜀: {skipped}\n"
            "예외 로그: {exceptions}\n"
            "학습 매핑: {learned}\n\n"
            "남은 누락: {missing}\n"
            "남은 불일치: {mismatch}\n"
            "남은 미매핑: {unmapped}\n"
            "남은 차단: {blocked}\n\n"
            "출력:\n{output}"
        ),
    },
}

_STAT_DEFS = (
    (STATUS_OK, "stat_ok", "#2e7d32"),
    (STATUS_MISSING, "stat_missing", "#f39c12"),
    (STATUS_MISMATCH, "stat_mismatch", "#c62828"),
    (STATUS_UNMAPPED, "stat_unmapped", "#8e44ad"),
    (STATUS_PROTECTED, "stat_protected", "#777777"),
    ("Blocked", "stat_blocked", "#555555"),
)

_TREE_COLUMN_DEFS = (
    ("approved", "column_approved", 78, "center"),
    ("row", "column_row", 50, "center"),
    ("status", "column_status", 92, "center"),
    ("risk", "column_risk", 82, "center"),
    ("action", "column_action", 150, "center"),
    ("module", "column_module", 115, "w"),
    ("item", "column_item", 360, "w"),
    ("current", "column_current", 150, "center"),
    ("qc", "column_qc", 90, "center"),
    ("delta", "column_delta", 75, "center"),
    ("db_key", "column_db_key", 235, "w"),
    ("source", "column_source", 84, "center"),
    ("confidence", "column_confidence", 58, "center"),
    ("reason", "column_reason", 210, "w"),
)

_TRANSLATIONS.update({
    "column_approved": {LANG_EN: "Approved", LANG_KO: "승인"},
    "column_row": {LANG_EN: "Row", LANG_KO: "행"},
    "column_status": {LANG_EN: "Status", LANG_KO: "상태"},
    "column_risk": {LANG_EN: "Risk", LANG_KO: "위험도"},
    "column_action": {LANG_EN: "Recommended Action", LANG_KO: "추천 조치"},
    "column_module": {LANG_EN: "Module", LANG_KO: "모듈"},
    "column_item": {LANG_EN: "Check Item", LANG_KO: "검사항목"},
    "column_current": {LANG_EN: "Checklist Measurement (G)", LANG_KO: "체크리스트 측정값(G)"},
    "column_qc": {LANG_EN: "QC Value", LANG_KO: "QC 값"},
    "column_delta": {LANG_EN: "Delta", LANG_KO: "차이"},
    "column_db_key": {LANG_EN: "DB Key", LANG_KO: "DB 키"},
    "column_source": {LANG_EN: "Source", LANG_KO: "출처"},
    "column_confidence": {LANG_EN: "Conf.", LANG_KO: "신뢰도"},
    "column_reason": {LANG_EN: "Auto Reason", LANG_KO: "자동 판단 사유"},
})

_VALUE_TRANSLATIONS = {
    "status": {
        STATUS_OK: {LANG_EN: "OK", LANG_KO: "정상"},
        STATUS_MISSING: {LANG_EN: "Missing", LANG_KO: "누락"},
        STATUS_MISMATCH: {LANG_EN: "Mismatch", LANG_KO: "불일치"},
        STATUS_UNMAPPED: {LANG_EN: "Unmapped", LANG_KO: "미매핑"},
        STATUS_PROTECTED: {LANG_EN: "Protected", LANG_KO: "보호"},
        STATUS_SKIPPED_GROUP: {LANG_EN: "SkippedGroup", LANG_KO: "그룹 제외"},
        STATUS_NON_COMPARABLE: {LANG_EN: "NonComparable", LANG_KO: "비교 불가"},
    },
    "risk": {
        RISK_SAFE: {LANG_EN: "Safe", LANG_KO: "안전"},
        RISK_REVIEW: {LANG_EN: "Review", LANG_KO: "검토"},
        RISK_HIGH: {LANG_EN: "HighRisk", LANG_KO: "고위험"},
        RISK_BLOCKED: {LANG_EN: "Blocked", LANG_KO: "차단"},
        RISK_OK: {LANG_EN: "OK", LANG_KO: "정상"},
    },
    "action": {
        ACTION_FILL: {LANG_EN: "Fill QC Value", LANG_KO: "QC 값 기입"},
        ACTION_REPLACE: {LANG_EN: "Replace with QC Value", LANG_KO: "QC 값으로 교체"},
        ACTION_REVIEW: {LANG_EN: "Reviewer Confirm", LANG_KO: "검수자 확인"},
        ACTION_DO_NOT_WRITE: {LANG_EN: "Do Not Write", LANG_KO: "기입 금지"},
        ACTION_NONE: {LANG_EN: "No Action", LANG_KO: "조치 없음"},
    },
    "source": {
        "explicit": {LANG_EN: "explicit", LANG_KO: "명시 매핑"},
        "learned": {LANG_EN: "learned", LANG_KO: "학습 매핑"},
        "exact": {LANG_EN: "exact", LANG_KO: "정확 매칭"},
        "fuzzy": {LANG_EN: "fuzzy", LANG_KO: "유사 매칭"},
        "unit_hint": {LANG_EN: "unit_hint", LANG_KO: "단위 힌트"},
        "manual_candidate": {LANG_EN: "manual_candidate", LANG_KO: "수동 후보"},
        "manual": {LANG_EN: "manual", LANG_KO: "수동"},
        "unmapped": {LANG_EN: "unmapped", LANG_KO: "미매핑"},
        "skipped": {LANG_EN: "skipped", LANG_KO: "제외"},
    },
}

_REASON_KO = {
    "Not writable or not comparable": "기입 불가 또는 비교 불가",
    "Checklist value already matches QC": "체크리스트 값이 이미 QC와 일치",
    "No writable QC correction": "기입 가능한 QC 보정 없음",
    "Large delta, type mismatch, or ambiguous candidates": "큰 차이, 타입 불일치 또는 모호한 후보",
    "Reviewer confirmation required": "검수자 확인 필요",
    "Group header row": "그룹 헤더 행",
    "Measurement cell contains a formula": "Measurement 셀에 수식 포함",
}


class HelpTooltip:
    """Small hover tooltip for Final QC help buttons."""

    _active = None

    def __init__(self, widget, text_getter, delay_ms: int = 300):
        self.widget = widget
        self.text_getter = text_getter
        self.delay_ms = delay_ms
        self.tip = None
        self._after_id = None
        self._hovered = False
        widget.bind("<Enter>", self.schedule)
        widget.bind("<Leave>", self.hide)
        widget.bind("<ButtonPress>", self.hide)
        widget.bind("<FocusOut>", self.hide)
        widget.bind("<Destroy>", self.destroy)

    def schedule(self, _event=None):
        self._hovered = True
        self._cancel_pending()
        self._after_id = self.widget.after(self.delay_ms, self.show)

    def _cancel_pending(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def show(self, _event=None):
        self._after_id = None
        if not self._hovered:
            return
        if self.tip is not None:
            return
        if HelpTooltip._active is not None and HelpTooltip._active is not self:
            HelpTooltip._active.hide()
        text = self.text_getter()
        if not text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = ctk.CTkToplevel(self.widget)
        self.tip.withdraw()
        self.tip.overrideredirect(True)
        self.tip.geometry(f"+{x}+{y}")
        frame = ctk.CTkFrame(self.tip, fg_color="#333333", corner_radius=6)
        frame.pack()
        label = ctk.CTkLabel(
            frame,
            text=text,
            justify="left",
            wraplength=320,
        )
        label.pack(padx=10, pady=8)
        self.tip.deiconify()
        HelpTooltip._active = self

    def hide(self, _event=None):
        self._hovered = False
        self._cancel_pending()
        if self.tip is not None:
            try:
                self.tip.destroy()
            except Exception:
                pass
            self.tip = None
        if HelpTooltip._active is self:
            HelpTooltip._active = None

    def destroy(self, _event=None):
        self.hide()

    @classmethod
    def hide_active(cls):
        if cls._active is not None:
            cls._active.hide()


class FinalChecklistQcDialog(ctk.CTkToplevel):
    """Reviewer workflow: inspect checklist, approve rows, write to an internal copy."""

    def __init__(self, parent, excel_path: str, qc_report: dict, profile_name: str = "", sync_manager=None):
        super().__init__(parent)
        self.excel_path = excel_path
        self.qc_report = qc_report
        self.profile_name = profile_name
        self.engine = ChecklistFinalQcEngine(sync_manager=sync_manager)
        self.report = None
        self.approved_rows = set()
        self.exception_rows = {}
        self.show_mismatch_only = False
        self.current_filter = FILTER_ALL
        self.profile_coverage = self._build_profile_coverage(qc_report, [])
        self._help_tooltips = []
        self._last_tree_cell = (None, None)
        self._normal_geometry = "1420x820"
        self._is_maximized = False
        self._qc_lookup = ChecklistValidator()._build_qc_lookup(qc_report)

        self.language = LANG_EN
        self._status_message_key = "status_analyzing"
        self._status_message_kwargs = {}
        self.write_db_key_var = ctk.BooleanVar(value=True)
        self.candidate_var = ctk.StringVar(value="")

        self.title(self._t("window_title"))
        self.geometry(self._normal_geometry)
        self.resizable(True, True)

        self._build_ui()
        self._run_analysis_async()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        self.title_label = ctk.CTkLabel(
            title_row,
            text=self._t("window_title"),
            font=("Segoe UI", 18, "bold"),
        )
        self.title_label.pack(side="left", anchor="w")
        self.language_button = ctk.CTkButton(
            title_row,
            text=self._t("language_toggle"),
            command=self._toggle_language,
            width=92,
            height=28,
        )
        self.language_button.pack(side="right")
        self.maximize_button = ctk.CTkButton(
            title_row,
            text=self._t("maximize"),
            command=self._toggle_maximize,
            width=92,
            height=28,
        )
        self.maximize_button.pack(side="right", padx=(0, 8))
        self.file_label = ctk.CTkLabel(
            header,
            text=self._format_file_profile(),
            font=("Segoe UI", 11),
            text_color="#888888",
        )
        self.file_label.pack(anchor="w", pady=(2, 0))

        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.pack(fill="x", padx=20, pady=8)
        self.stat_labels = {}
        self.stat_name_labels = {}
        for idx, (key, label_key, color) in enumerate(_STAT_DEFS):
            frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
            frame.grid(row=0, column=idx, padx=22, pady=8)
            value = ctk.CTkLabel(frame, text="-", font=("Segoe UI", 22, "bold"), text_color=color)
            value.pack()
            name = ctk.CTkLabel(frame, text=self._t(label_key), font=("Segoe UI", 10), text_color="#aaaaaa")
            name.pack()
            self.stat_labels[key] = value
            self.stat_name_labels[key] = (name, label_key)

        self.preflight_label = ctk.CTkLabel(
            self,
            text=self._t("preflight_pending"),
            font=("Segoe UI", 11),
            text_color="#777777",
            anchor="w",
        )
        self.preflight_label.pack(fill="x", padx=20, pady=(0, 8))

        self.coverage_label = ctk.CTkLabel(
            self,
            text=self._format_coverage_status(),
            font=("Segoe UI", 11),
            text_color="#888888",
            anchor="w",
        )
        self.coverage_label.pack(fill="x", padx=20, pady=(0, 8))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(0, 8))

        self.btn_approve = ctk.CTkButton(actions, text=self._t("approve_selected"), command=self._approve_selected, width=135)
        self.btn_approve.pack(side="left", padx=(0, 2))
        self._add_help_button(actions, "help_approve_selected")
        self.btn_unapprove = ctk.CTkButton(
            actions,
            text=self._t("unapprove_selected"),
            command=self._unapprove_selected,
            width=135,
        )
        self.btn_unapprove.pack(side="left", padx=(0, 2))
        self._add_help_button(actions, "help_unapprove_selected")
        self.btn_safe = ctk.CTkButton(
            actions,
            text=self._t("approve_safe"),
            command=self._approve_safe_corrections,
            fg_color="#1976d2",
            hover_color="#0d47a1",
            width=190,
        )
        self.btn_safe.pack(side="left", padx=(0, 2))
        self._add_help_button(actions, "help_approve_safe")
        self.btn_exception = ctk.CTkButton(
            actions,
            text=self._t("mark_exception"),
            command=self._mark_exception,
            width=130,
        )
        self.btn_exception.pack(side="left", padx=(0, 2))
        self._add_help_button(actions, "help_mark_exception")
        self.btn_clear = ctk.CTkButton(actions, text=self._t("clear_approval"), command=self._clear_approval, width=125)
        self.btn_clear.pack(side="left", padx=(0, 2))
        self._add_help_button(actions, "help_clear_approval", padx=(0, 12))

        self.write_db_key_checkbox = ctk.CTkCheckBox(
            actions,
            text=self._t("write_db_key"),
            variable=self.write_db_key_var,
            font=("Segoe UI", 12),
        )
        self.write_db_key_checkbox.pack(side="left", padx=(0, 2))
        self._add_help_button(actions, "help_write_db_key", padx=(0, 16))

        self.status_label = ctk.CTkLabel(actions, text=self._t("status_analyzing"), font=("Segoe UI", 11), text_color="#888888")
        self.status_label.pack(side="left", padx=8)

        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 8))
        self.filter_label = ctk.CTkLabel(filter_frame, text=self._t("filter_label"), font=("Segoe UI", 12))
        self.filter_label.pack(side="left", padx=(0, 8))
        self.filter_segmented = ctk.CTkSegmentedButton(
            filter_frame,
            values=self._filter_labels(),
            command=self._on_filter_changed,
            font=("Segoe UI", 11),
        )
        self.filter_segmented.set(self._filter_label(self.current_filter))
        self.filter_segmented.pack(side="left")

        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        columns = (
            "approved",
            "row",
            "status",
            "risk",
            "action",
            "module",
            "item",
            "current",
            "qc",
            "delta",
            "db_key",
            "source",
            "confidence",
            "reason",
        )
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        for col, heading_key, width, anchor in _TREE_COLUMN_DEFS:
            self.tree.heading(col, text=self._t(heading_key))
            self.tree.column(col, width=width, anchor=anchor)

        self.tree.tag_configure("ok", background="#E8F5E9")
        self.tree.tag_configure("missing", background="#FFF8E1")
        self.tree.tag_configure("mismatch", background="#FFEBEE")
        self.tree.tag_configure("unmapped", background="#F3E5F5")
        self.tree.tag_configure("protected", background="#EEEEEE")
        self.tree.tag_configure("skipped", background="#EEEEEE")
        self.tree.tag_configure("non_comparable", background="#E3F2FD")

        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<Button-3>", self._show_tree_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._toggle_selected_approval)
        self.tree.bind("<space>", self._toggle_selected_approval)
        self.tree.bind("<Control-c>", self._copy_active_cell)
        self.tree.bind("<Control-C>", self._copy_active_cell)

        candidate_frame = ctk.CTkFrame(self, fg_color="transparent")
        candidate_frame.pack(fill="x", padx=20, pady=(0, 8))
        self.candidate_label = ctk.CTkLabel(candidate_frame, text=self._t("candidate_label"), font=("Segoe UI", 12))
        self.candidate_label.pack(side="left")
        self.candidate_combo = ctk.CTkComboBox(candidate_frame, values=[], variable=self.candidate_var, width=520)
        self.candidate_combo.pack(side="left", padx=8)
        self.btn_use_candidate = ctk.CTkButton(
            candidate_frame,
            text=self._t("use_candidate"),
            command=self._use_candidate,
            width=180,
            state="disabled",
        )
        self.btn_use_candidate.pack(side="left", padx=8)
        self._add_help_button(candidate_frame, "help_use_candidate")

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=(0, 14), side="bottom")
        self.btn_apply = ctk.CTkButton(
            bottom,
            text=self._t("apply_approved"),
            command=self._apply_approved_async,
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            width=230,
            height=38,
            state="disabled",
        )
        self.btn_apply.pack(side="left", padx=(0, 2))
        self._add_help_button(bottom, "help_apply_approved")
        self.btn_close = ctk.CTkButton(bottom, text=self._t("close"), command=self.destroy, width=90, height=38)
        self.btn_close.pack(side="right")

    def _t(self, key: str) -> str:
        entry = _TRANSLATIONS.get(key, {})
        if isinstance(entry, dict):
            return entry.get(self.language, entry.get(LANG_EN, key))
        return str(entry or key)

    def _tf(self, key: str, **kwargs) -> str:
        return self._t(key).format(**kwargs)

    def _format_file_profile(self) -> str:
        return self._tf(
            "file_profile",
            file=Path(self.excel_path).name,
            profile=self.profile_name,
        )

    def _add_help_button(self, parent, help_key: str, padx=(0, 8)):
        button = ctk.CTkButton(
            parent,
            text="?",
            width=24,
            height=24,
            fg_color="#455A64",
            hover_color="#37474F",
        )
        button.pack(side="left", padx=padx)
        self._help_tooltips.append(HelpTooltip(button, lambda key=help_key: self._t(key)))
        return button

    def _hide_help_tooltips(self):
        HelpTooltip.hide_active()
        for tooltip in getattr(self, "_help_tooltips", []):
            tooltip.hide()

    def _filter_options(self):
        return (
            (FILTER_ALL, "filter_all"),
            (FILTER_ATTENTION, "filter_attention"),
            (FILTER_MISMATCH, "filter_mismatch"),
            (FILTER_PROFILE_MATCHED, "filter_profile_matched"),
            (FILTER_MISSING_CHECKLIST, "filter_missing_checklist"),
        )

    def _filter_label(self, filter_key: str) -> str:
        for key, label_key in self._filter_options():
            if key == filter_key:
                return self._t(label_key)
        return self._t("filter_all")

    def _filter_labels(self):
        return [self._t(label_key) for _key, label_key in self._filter_options()]

    def _on_filter_changed(self, label: str):
        for key, label_key in self._filter_options():
            if label == self._t(label_key):
                self._set_filter(key, update_segmented=False)
                return

    def _set_filter(self, filter_key: str, update_segmented: bool = True):
        self._hide_help_tooltips()
        self.current_filter = filter_key
        self.show_mismatch_only = filter_key == FILTER_MISMATCH
        if update_segmented and hasattr(self, "filter_segmented"):
            self.filter_segmented.set(self._filter_label(filter_key))
        if hasattr(self, "tree"):
            self._populate_tree()

    def _toggle_language(self):
        self._hide_help_tooltips()
        self.language = LANG_KO if self.language == LANG_EN else LANG_EN
        self._apply_language()

    def _toggle_maximize(self):
        if self._is_maximized:
            try:
                self.state("normal")
            except Exception:
                pass
            self.geometry(self._normal_geometry)
            self._is_maximized = False
        else:
            self._normal_geometry = self.geometry()
            try:
                self.state("zoomed")
            except Exception:
                screen_w = self.winfo_screenwidth()
                screen_h = self.winfo_screenheight()
                self.geometry(f"{screen_w}x{screen_h}+0+0")
            self._is_maximized = True
        self.maximize_button.configure(text=self._t("restore" if self._is_maximized else "maximize"))

    def _apply_language(self):
        self.title(self._t("window_title"))
        self.title_label.configure(text=self._t("window_title"))
        self.language_button.configure(text=self._t("language_toggle"))
        self.maximize_button.configure(text=self._t("restore" if self._is_maximized else "maximize"))
        self.file_label.configure(text=self._format_file_profile())
        self.coverage_label.configure(text=self._format_coverage_status())
        self.filter_label.configure(text=self._t("filter_label"))
        self.filter_segmented.configure(values=self._filter_labels())
        self.filter_segmented.set(self._filter_label(self.current_filter))

        for _key, (label, label_key) in self.stat_name_labels.items():
            label.configure(text=self._t(label_key))

        self.btn_approve.configure(text=self._t("approve_selected"))
        self.btn_unapprove.configure(text=self._t("unapprove_selected"))
        self.btn_safe.configure(text=self._t("approve_safe"))
        self.btn_exception.configure(text=self._t("mark_exception"))
        self.btn_clear.configure(text=self._t("clear_approval"))
        self.write_db_key_checkbox.configure(text=self._t("write_db_key"))
        self.candidate_label.configure(text=self._t("candidate_label"))
        self.btn_use_candidate.configure(text=self._t("use_candidate"))
        self.btn_apply.configure(text=self._t("apply_approved"))
        self.btn_close.configure(text=self._t("close"))

        for col, heading_key, _width, _anchor in _TREE_COLUMN_DEFS:
            self.tree.heading(col, text=self._t(heading_key))

        self._refresh_preflight_label()
        self._set_status_message(self._status_message_key, **self._status_message_kwargs)
        if self.report:
            self._populate_tree()

    def _refresh_preflight_label(self):
        preflight = getattr(self.report, "preflight_result", None) if self.report else None
        if preflight:
            self.preflight_label.configure(text=self._format_preflight_status(preflight))
        else:
            self.preflight_label.configure(text=self._t("preflight_pending"))

    def _set_status_message(self, key: str, **kwargs):
        self._status_message_key = key
        self._status_message_kwargs = dict(kwargs)
        if hasattr(self, "status_label"):
            self.status_label.configure(text=self._tf(key, **kwargs))

    def _tree_columns(self) -> tuple:
        if not hasattr(self, "tree"):
            return ()
        return tuple(self.tree["columns"])

    def _tree_column_index(self, column) -> int | None:
        columns = self._tree_columns()
        if isinstance(column, str) and column.startswith("#"):
            try:
                index = int(column[1:]) - 1
            except ValueError:
                return None
            return index if 0 <= index < len(columns) else None
        try:
            return columns.index(column)
        except ValueError:
            return None

    def _tree_column_name(self, column) -> str:
        index = self._tree_column_index(column)
        columns = self._tree_columns()
        if index is None or index >= len(columns):
            return ""
        return columns[index]

    def _tree_item_values(self, item_id) -> tuple:
        if not item_id or not hasattr(self, "tree"):
            return ()
        return tuple(self.tree.item(item_id, "values") or ())

    def _set_active_tree_cell(self, item_id, column):
        if item_id and column:
            self._last_tree_cell = (item_id, column)
        else:
            self._last_tree_cell = (None, None)

    def _on_tree_click(self, event=None):
        if event is None:
            return
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        self._set_active_tree_cell(item_id, column)
        if item_id and self._tree_column_name(column) == "approved":
            self._toggle_approval_for_item(item_id)
            return "break"

    def _show_tree_context_menu(self, event=None):
        if event is None:
            return "break"
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item_id:
            self._set_active_tree_cell(None, None)
            return "break"

        self._hide_help_tooltips()
        self._set_active_tree_cell(item_id, column)
        if item_id not in self.tree.selection():
            self.tree.selection_set(item_id)

        menu = Menu(self, tearoff=0)
        menu.add_command(label=self._t("copy_cell"), command=self._copy_active_cell)
        menu.add_command(label=self._t("copy_db_key"), command=lambda item=item_id: self._copy_db_key(item))
        menu.add_command(label=self._t("copy_row"), command=lambda item=item_id: self._copy_row(item))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    def _active_tree_cell(self):
        item_id, column = getattr(self, "_last_tree_cell", (None, None))
        if item_id and column:
            return item_id, column
        if hasattr(self, "tree"):
            selection = self.tree.selection()
            if selection:
                return selection[0], "#1"
        return None, None

    def _tree_display_value(self, item_id, column) -> str:
        index = self._tree_column_index(column)
        values = self._tree_item_values(item_id)
        if index is None or index >= len(values):
            return ""
        return str(values[index])

    def _db_key_for_tree_item(self, item_id) -> str:
        if not item_id:
            return ""
        item_text = str(item_id)
        if item_text.startswith("missing:"):
            return item_text.split(":", 1)[1]

        try:
            row_number = int(item_text)
        except (TypeError, ValueError):
            row_number = None

        report = getattr(self, "report", None)
        if row_number is not None and report:
            row = report.get_row(row_number)
            if row and getattr(row, "db_key", None):
                return str(row.db_key)

        displayed = self._tree_display_value(item_id, "db_key")
        if displayed in {self._t("unmapped_placeholder"), "(unmapped)", "(미매핑)"}:
            return ""
        return displayed

    def _tree_cell_value(self, item_id, column) -> str:
        if self._tree_column_name(column) == "db_key":
            return self._db_key_for_tree_item(item_id)
        return self._tree_display_value(item_id, column)

    def _row_for_tree_item(self, item_id):
        try:
            row_number = int(item_id)
        except (TypeError, ValueError):
            return None
        report = getattr(self, "report", None)
        if not report:
            return None
        return report.get_row(row_number)

    def _toggle_approval_for_item(self, item_id) -> bool:
        row = self._row_for_tree_item(item_id)
        if not row:
            return False
        if row.row in self.approved_rows:
            self.approved_rows.discard(row.row)
        elif row.is_writable:
            self.approved_rows.add(row.row)
            self.exception_rows.pop(row.row, None)
        else:
            return False
        self._populate_tree()
        if (
            hasattr(self, "tree")
            and hasattr(self.tree, "get_children")
            and str(row.row) in self.tree.get_children("")
        ):
            self.tree.selection_set(str(row.row))
            self.tree.see(str(row.row))
        return True

    def _copy_to_clipboard(self, text: str):
        self.clipboard_clear()
        self.clipboard_append("" if text is None else str(text))
        self.update_idletasks()

    def _copy_active_cell(self, event=None):
        item_id, column = self._active_tree_cell()
        if item_id and column:
            self._copy_to_clipboard(self._tree_cell_value(item_id, column))
        return "break"

    def _copy_db_key(self, item_id=None):
        if item_id is None:
            item_id, _column = self._active_tree_cell()
        if item_id:
            self._copy_to_clipboard(self._db_key_for_tree_item(item_id))
        return "break"

    def _copy_row(self, item_id=None):
        if item_id is None:
            item_id, _column = self._active_tree_cell()
        if not item_id:
            return "break"

        values = list(self._tree_item_values(item_id))
        db_key_index = self._tree_column_index("db_key")
        if db_key_index is not None and db_key_index < len(values):
            values[db_key_index] = self._db_key_for_tree_item(item_id)
        self._copy_to_clipboard("\t".join(str(value) for value in values))
        return "break"

    def _display_term(self, category: str, value: str) -> str:
        entry = _VALUE_TRANSLATIONS.get(category, {}).get(value)
        if not entry:
            return value or ""
        return entry.get(self.language, entry.get(LANG_EN, value))

    def _display_reason(self, reason: str) -> str:
        if not reason or self.language == LANG_EN:
            return reason or ""
        if reason.startswith("Trusted ") and reason.endswith(" mapping"):
            source = reason[len("Trusted "):-len(" mapping")]
            return f"신뢰된 {self._display_term('source', source)}"
        return _REASON_KO.get(reason, reason)

    def _format_apply_done_message(self, result, remaining, blocked: int) -> str:
        return self._tf(
            "apply_done",
            applied=result.applied_count,
            skipped=result.skipped_count,
            exceptions=result.exception_count,
            learned=result.learned_count,
            missing=remaining.get(STATUS_MISSING, 0),
            mismatch=remaining.get(STATUS_MISMATCH, 0),
            unmapped=remaining.get(STATUS_UNMAPPED, 0),
            blocked=blocked,
            output=result.output_path,
        )

    @staticmethod
    def _profile_key_from_result(result: dict) -> str:
        parts = (
            result.get("module", ""),
            result.get("part_type", ""),
            result.get("part_name", ""),
            result.get("item_name", ""),
        )
        return ".".join(str(part).strip() for part in parts if str(part).strip())

    @classmethod
    def _build_profile_coverage(cls, qc_report: dict, rows) -> dict:
        profile_items = {}
        for result in (qc_report or {}).get("results", []):
            if result.get("spec") is None:
                continue
            key = cls._profile_key_from_result(result)
            if not key:
                continue
            profile_items[key] = {
                "db_key": key,
                "module": result.get("module", ""),
                "part_type": result.get("part_type", ""),
                "part_name": result.get("part_name", ""),
                "item_name": result.get("item_name", ""),
                "actual_value": result.get("actual_value", ""),
                "status": result.get("status", ""),
            }

        checklist_keys = {
            str(row.db_key).strip()
            for row in rows
            if getattr(row, "db_key", None) and str(row.db_key).strip()
        }
        profile_keys = set(profile_items)
        mapped_keys = profile_keys & checklist_keys
        missing_keys = profile_keys - checklist_keys
        extra_keys = checklist_keys - profile_keys
        missing_items = [profile_items[key] for key in sorted(missing_keys)]

        return {
            "profile_count": len(profile_keys),
            "mapped_count": len(mapped_keys),
            "missing_count": len(missing_keys),
            "extra_count": len(extra_keys),
            "profile_keys": profile_keys,
            "mapped_keys": mapped_keys,
            "missing_keys": missing_keys,
            "extra_keys": extra_keys,
            "missing_items": missing_items,
        }

    def _refresh_profile_coverage(self):
        rows = self.report.rows if self.report else []
        self.profile_coverage = self._build_profile_coverage(self.qc_report, rows)
        if hasattr(self, "coverage_label"):
            self.coverage_label.configure(text=self._format_coverage_status())

    def _format_coverage_status(self) -> str:
        coverage = getattr(self, "profile_coverage", None)
        if not coverage:
            return self._t("coverage_pending")
        return self._tf(
            "coverage_status",
            mapped=coverage.get("mapped_count", 0),
            profile=coverage.get("profile_count", 0),
            missing=coverage.get("missing_count", 0),
            extra=coverage.get("extra_count", 0),
        )

    def _is_profile_matched_row(self, row) -> bool:
        return bool(
            getattr(row, "db_key", None)
            and str(row.db_key).strip() in self.profile_coverage.get("profile_keys", set())
        )

    def _is_attention_row(self, row) -> bool:
        return (
            row.status in {STATUS_MISSING, STATUS_MISMATCH, STATUS_UNMAPPED}
            or row.risk_level in {RISK_HIGH, RISK_BLOCKED}
        )

    def _run_analysis_async(self):
        self._set_buttons("disabled")
        self._set_status_message("status_running_preflight")

        def worker():
            try:
                preflight = self.engine.preflight(self.excel_path, self.qc_report)
                if preflight.has_errors:
                    raise ValueError(self._format_preflight_errors(preflight))
                report = self.engine.analyze(self.excel_path, self.qc_report, self.profile_name)
                report.preflight_result = preflight
                self.after(0, lambda: self._on_analysis_done(report))
            except Exception as exc:
                logger.error(f"Final Checklist QC analysis failed: {exc}", exc_info=True)
                self.after(0, lambda exc=exc: messagebox.showerror(self._t("window_title"), str(exc), parent=self))
                self.after(0, lambda exc=exc: self._set_status_message("status_error", error=exc))
                self.after(0, lambda: self._set_buttons("disabled"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_analysis_done(self, report):
        self.report = report
        self.approved_rows.clear()
        self.exception_rows.clear()
        self._populate_tree()
        self._set_buttons("normal")
        self._refresh_preflight_label()
        self._set_status_message("status_rows_analyzed", rows=len(report.rows), model=report.model or "-")

    def _populate_tree(self):
        self._hide_help_tooltips()
        self.tree.delete(*self.tree.get_children())
        if not self.report:
            return

        self._refresh_profile_coverage()
        summary = self.report.summary
        for key, label in self.stat_labels.items():
            if key == "Blocked":
                label.configure(text=str(sum(1 for row in self.report.rows if row.risk_level == RISK_BLOCKED)))
            else:
                label.configure(text=str(summary.get(key, 0)))

        if self.current_filter == FILTER_MISSING_CHECKLIST:
            self._populate_missing_checklist_rows()
            self._update_apply_state()
            return

        for row in self._visible_rows():
            tag = _STATUS_TAGS.get(row.status, "unmapped")
            approved = self._approval_marker(row)
            confidence = f"{row.confidence:.2f}" if row.confidence else "-"
            reason = self.exception_rows.get(row.row, row.auto_approval_reason)
            self.tree.insert(
                "",
                "end",
                iid=str(row.row),
                values=(
                    approved,
                    row.row,
                    self._display_term("status", row.status),
                    self._display_term("risk", row.risk_level),
                    self._display_term("action", row.recommended_action),
                    row.module,
                    row.item,
                    self._display(row.current_value),
                    self._display(row.qc_value),
                    row.delta,
                    row.db_key or self._t("unmapped_placeholder"),
                    self._display_term("source", row.source),
                    confidence,
                    self._display_reason(reason),
                ),
                tags=(tag,),
            )
        self._update_apply_state()

    def _populate_missing_checklist_rows(self):
        for item in self.profile_coverage.get("missing_items", []):
            db_key = item["db_key"]
            values = (
                APPROVAL_UNCHECKED,
                "-",
                self._t("missing_checklist_status"),
                self._display_term("risk", RISK_REVIEW),
                self._t("missing_checklist_action"),
                item.get("module", ""),
                item.get("item_name", ""),
                "",
                self._display(item.get("actual_value", "")),
                "",
                db_key,
                self._t("source_profile"),
                "-",
                self._t("missing_checklist_reason"),
            )
            self.tree.insert(
                "",
                "end",
                iid=f"missing:{db_key}",
                values=values,
                tags=("unmapped",),
            )

    def _approval_marker(self, row) -> str:
        if row.row in self.exception_rows:
            return APPROVAL_EXCEPTION
        if row.row in self.approved_rows:
            return APPROVAL_CHECKED
        return APPROVAL_UNCHECKED

    def _approve_selected(self):
        for row in self._selected_rows():
            if row.is_writable:
                self.approved_rows.add(row.row)
                self.exception_rows.pop(row.row, None)
        self._populate_tree()

    def _unapprove_selected(self):
        for row in self._selected_rows():
            self.approved_rows.discard(row.row)
        self._populate_tree()

    def _approve_safe_corrections(self):
        if not self.report:
            return
        for row in self.report.rows:
            if row.is_safe_correction:
                self.approved_rows.add(row.row)
                self.exception_rows.pop(row.row, None)
        self._populate_tree()

    def _clear_approval(self):
        if not messagebox.askyesno(self._t("window_title"), self._t("confirm_reset_all"), parent=self):
            return
        self.approved_rows.clear()
        self.exception_rows.clear()
        self._populate_tree()

    def _mark_exception(self):
        mismatches = [row for row in self._selected_rows() if row.status == STATUS_MISMATCH]
        if not mismatches:
            messagebox.showinfo(self._t("window_title"), self._t("msg_select_mismatch"), parent=self)
            return
        reason = simpledialog.askstring(
            self._t("exception_title"),
            self._t("exception_prompt"),
            parent=self,
        )
        if reason is None:
            return
        reason = reason.strip()
        if not reason:
            messagebox.showwarning(self._t("window_title"), self._t("msg_exception_reason_required"), parent=self)
            return
        for row in mismatches:
            self.exception_rows[row.row] = reason
            self.approved_rows.discard(row.row)
        self._populate_tree()

    def _toggle_selected_approval(self, event=None):
        for row in self._selected_rows():
            if row.row in self.approved_rows:
                self.approved_rows.discard(row.row)
            elif row.is_writable:
                self.approved_rows.add(row.row)
                self.exception_rows.pop(row.row, None)
        self._populate_tree()
        return "break"

    def _on_tree_select(self, event=None):
        rows = self._selected_rows()
        if len(rows) != 1 or not rows[0].candidates:
            self.candidate_combo.configure(values=[])
            self.candidate_var.set("")
            self.btn_use_candidate.configure(state="disabled")
            return

        self.candidate_combo.configure(values=rows[0].candidates)
        self.candidate_var.set(rows[0].candidates[0])
        self.btn_use_candidate.configure(state="normal")

    def _use_candidate(self):
        rows = self._selected_rows()
        if len(rows) != 1:
            return
        row = rows[0]
        candidate = self.candidate_var.get().strip()
        if not candidate or candidate not in self._qc_lookup:
            messagebox.showwarning(self._t("window_title"), self._t("msg_invalid_candidate"), parent=self)
            return
        if row.status in (STATUS_PROTECTED, STATUS_SKIPPED_GROUP):
            return

        row.db_key = candidate
        row.qc_value = self._qc_lookup.get(candidate)
        row.source = "manual_candidate"
        row.confidence = 0.95
        row.status = self.engine.classify_value(row.current_value, row.qc_value)
        self.engine.apply_risk_metadata(row)
        if row.is_writable:
            self.approved_rows.add(row.row)
            self.exception_rows.pop(row.row, None)
        self._populate_tree()
        self.tree.selection_set(str(row.row))
        self.tree.see(str(row.row))

    def _apply_approved_async(self):
        if not self.report or (not self.approved_rows and not self.exception_rows):
            messagebox.showinfo(self._t("window_title"), self._t("msg_no_approved"), parent=self)
            return

        output_path = self.engine.default_output_path(self.excel_path)
        self._set_buttons("disabled")
        self._set_status_message("status_writing_copy")

        def worker():
            try:
                result = self.engine.apply_approved(
                    self.report,
                    self.approved_rows,
                    output_path,
                    write_db_key=self.write_db_key_var.get(),
                    exceptions=self.exception_rows,
                )
                self.after(0, lambda: self._on_apply_done(result))
            except Exception as exc:
                logger.error(f"Final Checklist QC apply failed: {exc}", exc_info=True)
                self.after(0, lambda exc=exc: messagebox.showerror(self._t("window_title"), str(exc), parent=self))
                self.after(0, lambda exc=exc: self._set_status_message("status_error", error=exc))
                self.after(0, lambda: self._set_buttons("normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_apply_done(self, result):
        remaining = result.post_report.summary
        blocked = sum(1 for row in result.post_report.rows if row.risk_level == RISK_BLOCKED)
        self.report = result.post_report
        self.approved_rows.clear()
        self.exception_rows.clear()
        self._populate_tree()
        self._set_buttons("normal")
        self._refresh_preflight_label()
        self._set_status_message("status_saved_copy", file=Path(result.output_path).name)
        messagebox.showinfo(
            self._t("window_title"),
            self._format_apply_done_message(result, remaining, blocked),
            parent=self,
        )

    def _visible_rows(self):
        if not self.report:
            return []
        if self.current_filter == FILTER_MISMATCH:
            return [row for row in self.report.rows if row.status == STATUS_MISMATCH]
        if self.current_filter == FILTER_ATTENTION:
            return [row for row in self.report.rows if self._is_attention_row(row)]
        if self.current_filter == FILTER_PROFILE_MATCHED:
            return [row for row in self.report.rows if self._is_profile_matched_row(row)]
        return self.report.rows

    def _selected_rows(self):
        if not self.report:
            return []
        rows = []
        for item_id in self.tree.selection():
            try:
                row_number = int(item_id)
            except (TypeError, ValueError):
                continue
            row = self.report.get_row(row_number)
            if row:
                rows.append(row)
        return rows

    def _update_apply_state(self):
        state = "normal" if self.approved_rows or self.exception_rows else "disabled"
        self.btn_apply.configure(state=state)

    def _set_buttons(self, state: str):
        for button in (
            self.btn_approve,
            self.btn_unapprove,
            self.btn_safe,
            self.btn_exception,
            self.btn_clear,
        ):
            button.configure(state=state)
        if state == "disabled":
            self.btn_apply.configure(state="disabled")
            self.btn_use_candidate.configure(state="disabled")
        else:
            self._update_apply_state()
            self._on_tree_select()

    def _format_preflight_status(self, preflight) -> str:
        if not preflight:
            return self._t("preflight_unavailable")
        summary = preflight.summary
        return self._tf(
            "preflight_status",
            errors=summary.get(PREFLIGHT_ERROR, 0),
            warnings=summary.get(PREFLIGHT_WARNING, 0),
            info=summary.get(PREFLIGHT_INFO, 0),
            sheet=preflight.main_sheet or "-",
            keys=preflight.qc_key_count,
        )

    def _format_preflight_errors(self, preflight) -> str:
        lines = [self._t("preflight_failed")]
        for issue in preflight.errors[:8]:
            lines.append(f"- {issue.code}: {issue.message}")
        return "\n".join(lines)

    def _display(self, value) -> str:
        if value is None:
            return ""
        return str(value)

    def destroy(self):
        self._hide_help_tooltips()
        super().destroy()
