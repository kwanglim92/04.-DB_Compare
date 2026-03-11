"""
N/A Items Review Dialog
Shows missing DB items grouped by module and allows user to exclude optional modules.
"""

import customtkinter as ctk
from tkinter import ttk
from typing import Dict, List, Set
import logging

from src.utils.format_helpers import center_window_on_parent

logger = logging.getLogger(__name__)


class NaReviewDialog(ctk.CTkToplevel):
    """
    Review dialog for N/A (missing in DB) items.
    Groups items by Module.PartType.PartName and provides ON/OFF toggles.
    OFF = EXCLUDED (option not installed), ON = FAIL (suspected missing).
    """
    
    def __init__(self, parent, missing_items: List[Dict], profile_name: str, spec_manager=None):
        super().__init__(parent)
        
        self.title("N/A Items Review")
        self.geometry("700x550")
        self.resizable(True, True)
        self.minsize(600, 400)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self.missing_items = missing_items
        self.profile_name = profile_name
        self.spec_manager = spec_manager
        
        # Result: set of exclusion patterns chosen by user
        self.excluded_patterns: Set[str] = set()
        self.save_to_profile = False
        self.confirmed = False
        
        # Group items by Module.PartType.PartName
        self.groups = self._group_items(missing_items)
        
        # Toggle state: group_key -> BooleanVar (True=ON/FAIL, False=OFF/EXCLUDED)
        self.toggle_vars: Dict[str, ctk.BooleanVar] = {}
        
        self.create_widgets()
        center_window_on_parent(self, parent, 700, 550)
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def _group_items(self, items: List[Dict]) -> Dict[str, List[Dict]]:
        """Group missing items by Module.PartType.PartName"""
        groups = {}
        for item in items:
            key = f"{item['module']}.{item['part_type']}.{item['part_name']}"
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups
    
    def create_widgets(self):
        """Build the dialog UI"""
        total_count = len(self.missing_items)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(
            header_frame,
            text="⚠ N/A Items Review",
            font=("Segoe UI", 18, "bold"),
            text_color="#ff9800"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_frame,
            text=f"프로파일 '{self.profile_name}'에 {total_count}개 항목이 DB에 없습니다.",
            font=("Segoe UI", 13),
            text_color="gray"
        ).pack(anchor="w", pady=(5, 0))
        
        ctk.CTkLabel(
            header_frame,
            text="옵션 미장착으로 인한 정상 부재 항목은 OFF로 전환하세요.",
            font=("Segoe UI", 12),
            text_color="gray"
        ).pack(anchor="w")
        
        # Legend
        legend_frame = ctk.CTkFrame(self, fg_color="transparent")
        legend_frame.pack(fill="x", padx=20, pady=(5, 10))
        
        ctk.CTkLabel(
            legend_frame,
            text="ON = FAIL 유지 (DB 누락 의심)  |  OFF = 제외 (옵션 미장착)",
            font=("Segoe UI", 11, "bold"),
            text_color="#aaaaaa"
        ).pack(anchor="w")
        
        # Scrollable group list
        scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=8)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Sort groups: larger groups first (likely modules)
        sorted_groups = sorted(self.groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        for group_key, items in sorted_groups:
            self._create_group_row(scroll_frame, group_key, items)
        
        # Save checkbox
        save_frame = ctk.CTkFrame(self, fg_color="transparent")
        save_frame.pack(fill="x", padx=20, pady=(0, 5))
        
        self.save_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            save_frame,
            text="이 선택을 프로파일에 저장",
            variable=self.save_var,
            font=("Segoe UI", 12),
            checkbox_width=20,
            checkbox_height=20
        ).pack(anchor="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 15))
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.on_cancel,
            fg_color="gray",
            hover_color="#555555",
            width=120,
            height=38,
            font=("Segoe UI", 13, "bold")
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="▶ Re-run QC",
            command=self.on_confirm,
            fg_color="#2fa572",
            hover_color="#248f5f",
            width=150,
            height=38,
            font=("Segoe UI", 13, "bold")
        ).pack(side="right", padx=5)
    
    def _create_group_row(self, parent, group_key: str, items: List[Dict]):
        """Create a single group row with toggle switch"""
        row = ctk.CTkFrame(parent, corner_radius=6)
        row.pack(fill="x", pady=3, padx=5)
        
        # Toggle (default ON = FAIL)
        var = ctk.BooleanVar(value=True)
        self.toggle_vars[group_key] = var
        
        switch = ctk.CTkSwitch(
            row,
            text="",
            variable=var,
            onvalue=True,
            offvalue=False,
            width=40,
            switch_width=40,
            switch_height=20
        )
        switch.pack(side="left", padx=(10, 5), pady=8)
        
        # Group label
        parts = group_key.split('.')
        module = parts[0]
        rest = '.'.join(parts[1:])
        
        label_frame = ctk.CTkFrame(row, fg_color="transparent")
        label_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkLabel(
            label_frame,
            text=module,
            font=("Segoe UI", 13, "bold"),
            anchor="w"
        ).pack(side="left")
        
        ctk.CTkLabel(
            label_frame,
            text=f"  ▸ {rest}",
            font=("Segoe UI", 12),
            text_color="gray",
            anchor="w"
        ).pack(side="left")
        
        # Item count badge
        count = len(items)
        count_color = "#c62828" if count >= 10 else "#ff9800" if count >= 3 else "gray"
        ctk.CTkLabel(
            row,
            text=f"({count} items)",
            font=("Segoe UI", 12, "bold"),
            text_color=count_color
        ).pack(side="right", padx=15, pady=8)
    
    def on_confirm(self):
        """User clicked Re-run QC"""
        self.excluded_patterns = set()
        
        for group_key, var in self.toggle_vars.items():
            if not var.get():  # OFF = exclude
                # Build wildcard pattern: Module.PartType.PartName.*
                self.excluded_patterns.add(f"{group_key}.*")
        
        self.save_to_profile = self.save_var.get()
        self.confirmed = True
        self.destroy()
    
    def on_cancel(self):
        """User cancelled — run QC without exclusions"""
        self.excluded_patterns = set()
        self.save_to_profile = False
        self.confirmed = False
        self.destroy()
