"""Admin panel for customizing Excel report templates (F14)."""

import os
import tempfile
import logging
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk

from src.utils.template_helper import (
    load_template, save_template, validate_template, get_default_template
)
from src.utils.config_helper import get_config_dir

logger = logging.getLogger(__name__)

_TEMPLATE_PATH = get_config_dir() / "report_template.json"
_PLACEHOLDERS_HELP = "사용 가능: {profile}  {date}  {engineer}  {instrument}"


class ReportTemplatePanel(ctk.CTkFrame):
    """Editable panel for report_template.json — embedded in Admin tabview."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._template = load_template(_TEMPLATE_PATH)
        self._build_ui()
        self._load_to_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Section helper
        def section(label):
            ctk.CTkLabel(scroll, text=label, font=("Segoe UI", 13, "bold"),
                         anchor="w").pack(fill="x", padx=8, pady=(14, 2))

        def row(parent_frame, label, widget_factory):
            f = ctk.CTkFrame(parent_frame, fg_color="transparent")
            f.pack(fill="x", padx=8, pady=2)
            ctk.CTkLabel(f, text=label, width=130, anchor="w",
                         font=("Segoe UI", 12)).pack(side="left")
            widget = widget_factory(f)
            widget.pack(side="left", fill="x", expand=True)
            return widget

        # --- Company info ---
        section("회사 정보")
        self._company_name = row(scroll, "회사 이름",
            lambda p: ctk.CTkEntry(p, height=28, font=("Segoe UI", 12)))
        self._company_contact = row(scroll, "연락처 (이메일)",
            lambda p: ctk.CTkEntry(p, height=28, font=("Segoe UI", 12)))

        logo_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        logo_frame.pack(fill="x", padx=8, pady=2)
        ctk.CTkLabel(logo_frame, text="로고 파일", width=130, anchor="w",
                     font=("Segoe UI", 12)).pack(side="left")
        self._logo_path_entry = ctk.CTkEntry(logo_frame, height=28, font=("Segoe UI", 12))
        self._logo_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(logo_frame, text="찾아보기…", width=80, height=28,
                      font=("Segoe UI", 12), command=self._browse_logo).pack(side="left")

        # --- Report title ---
        section("리포트 제목")
        ctk.CTkLabel(scroll, text=_PLACEHOLDERS_HELP, font=("Segoe UI", 11),
                     text_color="gray60", anchor="w").pack(fill="x", padx=8)
        self._title_template = row(scroll, "제목 템플릿",
            lambda p: ctk.CTkEntry(p, height=28, font=("Segoe UI", 12)))
        self._engineer_name = row(scroll, "엔지니어 이름",
            lambda p: ctk.CTkEntry(p, height=28, font=("Segoe UI", 12)))

        # --- Style ---
        section("스타일")
        self._header_color = row(scroll, "헤더 색상 (#RRGGBB)",
            lambda p: ctk.CTkEntry(p, height=28, width=120, font=("Segoe UI", 12)))
        self._footer_text = row(scroll, "Footer 문구",
            lambda p: ctk.CTkEntry(p, height=28, font=("Segoe UI", 12)))

        # --- Sheets ---
        section("포함 시트")
        sheets_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        sheets_frame.pack(fill="x", padx=8, pady=2)
        self._sheet_vars = {}
        for key, label in [("summary", "Summary"), ("all_items", "All Items"),
                            ("failed_items", "Failed Items"), ("cover_page", "Cover Page")]:
            var = ctk.BooleanVar()
            ctk.CTkCheckBox(sheets_frame, text=label, variable=var,
                            font=("Segoe UI", 12)).pack(side="left", padx=(0, 16))
            self._sheet_vars[key] = var

        # --- Action buttons ---
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=(16, 8))
        ctk.CTkButton(btn_frame, text="기본값으로 초기화", width=140, height=32,
                      font=("Segoe UI", 12), fg_color="#888888", hover_color="#666666",
                      command=self._reset_defaults).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="미리보기 Excel", width=120, height=32,
                      font=("Segoe UI", 12), fg_color="#555555", hover_color="#333333",
                      command=self._preview).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="저장", width=80, height=32,
                      font=("Segoe UI", 12, "bold"), fg_color="#1f6aa5", hover_color="#17538a",
                      command=self._save).pack(side="left")

    # ------------------------------------------------------------------
    # Data ↔ UI sync
    # ------------------------------------------------------------------

    def _load_to_ui(self):
        t = self._template
        company = t.get("company", {})

        self._company_name.delete(0, "end")
        self._company_name.insert(0, company.get("name", ""))

        self._company_contact.delete(0, "end")
        self._company_contact.insert(0, company.get("contact", ""))

        self._logo_path_entry.delete(0, "end")
        self._logo_path_entry.insert(0, company.get("logo_path", ""))

        self._title_template.delete(0, "end")
        self._title_template.insert(0, t.get("title_template", ""))

        self._engineer_name.delete(0, "end")
        self._engineer_name.insert(0, t.get("engineer_name", ""))

        self._header_color.delete(0, "end")
        self._header_color.insert(0, t.get("header_color", "#1f6aa5"))

        self._footer_text.delete(0, "end")
        self._footer_text.insert(0, t.get("footer_text", ""))

        sheets = t.get("sheets", {})
        for key, var in self._sheet_vars.items():
            var.set(sheets.get(key, False))

    def _collect_from_ui(self) -> dict:
        sheets = {k: v.get() for k, v in self._sheet_vars.items()}
        # Enforce at least one sheet
        if not any(sheets.values()):
            sheets["summary"] = True
        return {
            "company": {
                "name": self._company_name.get().strip(),
                "logo_path": self._logo_path_entry.get().strip(),
                "contact": self._company_contact.get().strip(),
            },
            "title_template": self._title_template.get().strip(),
            "engineer_name": self._engineer_name.get().strip(),
            "header_color": self._header_color.get().strip(),
            "footer_text": self._footer_text.get().strip(),
            "sheets": sheets,
            "columns": self._template.get("columns", {}),
        }

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _browse_logo(self):
        path = filedialog.askopenfilename(
            title="로고 이미지 선택",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if path:
            self._logo_path_entry.delete(0, "end")
            self._logo_path_entry.insert(0, path)

    def _reset_defaults(self):
        if messagebox.askyesno("기본값 초기화", "모든 설정을 기본값으로 되돌리겠습니까?"):
            self._template = get_default_template()
            self._load_to_ui()

    def _save(self):
        raw = self._collect_from_ui()
        validated = validate_template(raw)
        if save_template(validated, _TEMPLATE_PATH):
            self._template = validated
            messagebox.showinfo("저장 완료", "리포트 템플릿이 저장되었습니다.")
        else:
            messagebox.showerror("저장 실패", "템플릿 저장 중 오류가 발생했습니다.")

    def _preview(self):
        """Generate a dummy Excel report with current settings and open it."""
        raw = self._collect_from_ui()
        validated = validate_template(raw)

        dummy_report = {
            "profile_name": "NX10-Preview",
            "timestamp": "2026-04-27 10:00:00",
            "db_root": "C:\\XEService\\DB",
            "instrument": "nx",
            "summary": {
                "total_items": 10, "validated": 8, "checked_only": 1,
                "passed": 6, "failed": 2, "no_spec": 2, "errors": 0,
                "pass_rate": 75.0,
            },
            "results": [
                {"module": "Dsp", "part_type": "XScanner", "part_name": "100um",
                 "item_name": "ServoCutoffFrequencyHz", "actual_value": "80",
                 "spec": {"type": "range", "min": 70, "max": 90}, "status": "PASS", "message": ""},
                {"module": "Dsp", "part_type": "XScanner", "part_name": "100um",
                 "item_name": "Gain", "actual_value": "1.5",
                 "spec": {"type": "exact", "value": "1.0"}, "status": "FAIL",
                 "message": "Expected 1.0, got 1.5"},
            ],
        }

        try:
            from src.utils.report_generator import ExcelReportGenerator
            gen = ExcelReportGenerator(template=validated)
            tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False,
                                             prefix="preview_report_")
            tmp.close()
            gen.generate_report(dummy_report, tmp.name)
            os.startfile(tmp.name)
        except Exception as e:
            logger.error(f"Preview generation failed: {e}", exc_info=True)
            messagebox.showerror("미리보기 실패", f"Excel 생성 중 오류:\n{e}")
