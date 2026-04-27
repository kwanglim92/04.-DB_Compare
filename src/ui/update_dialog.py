"""Update available dialog — shown when a newer version is detected."""

import os
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)


class UpdateAvailableDialog(ctk.CTkToplevel):
    """Modal dialog shown when a newer app version is available."""

    def __init__(self, parent, current_version: str, release_info: dict):
        super().__init__(parent)
        self.result = None  # "download" | "later" | "skip"
        self._release = release_info
        self._current = current_version

        is_critical = release_info.get('is_critical', False)
        latest = release_info.get('version', '?')
        download_url = release_info.get('download_url', '')
        notes = release_info.get('release_notes', '')

        self.title("업데이트 알림")
        self.resizable(False, False)
        self.grab_set()

        # Header
        header = ctk.CTkFrame(self, fg_color="#1f6aa5", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="새 버전이 있습니다",
            font=("Segoe UI", 16, "bold"), text_color="white"
        ).pack(pady=12, padx=16)

        # Version row
        ver_frame = ctk.CTkFrame(self, fg_color="transparent")
        ver_frame.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(ver_frame, text=f"현재 버전:", font=("Segoe UI", 12)).pack(side="left")
        ctk.CTkLabel(ver_frame, text=f"  v{current_version}", font=("Segoe UI", 12),
                     text_color="gray60").pack(side="left")
        ctk.CTkLabel(ver_frame, text=f"   →   최신 버전:  v{latest}",
                     font=("Segoe UI", 12, "bold"), text_color="#0d7d3d").pack(side="left")

        if is_critical:
            ctk.CTkLabel(
                self, text="⚠  중요 업데이트입니다. 즉시 업데이트해주세요.",
                font=("Segoe UI", 11, "bold"), text_color="#d32f2f"
            ).pack(padx=20, pady=(0, 8))

        # Release notes
        if notes:
            ctk.CTkLabel(self, text="릴리즈 노트", font=("Segoe UI", 12, "bold"),
                         anchor="w").pack(fill="x", padx=20)
            notes_box = ctk.CTkTextbox(self, height=160, width=480,
                                       font=("Segoe UI", 11), state="normal")
            notes_box.pack(padx=20, pady=(4, 12), fill="x")
            notes_box.insert("end", notes)
            notes_box.configure(state="disabled")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 16))

        download_btn = ctk.CTkButton(
            btn_frame, text="다운로드 페이지 열기",
            font=("Segoe UI", 12, "bold"),
            fg_color="#1f6aa5", hover_color="#17538a",
            command=lambda: self._action("download", download_url)
        )
        download_btn.pack(side="left", padx=(0, 8))

        later_state = "disabled" if is_critical else "normal"
        ctk.CTkButton(
            btn_frame, text="나중에",
            font=("Segoe UI", 12),
            fg_color="#555555", hover_color="#333333",
            state=later_state,
            command=lambda: self._action("later", "")
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="이 버전 무시",
            font=("Segoe UI", 12),
            fg_color="#888888", hover_color="#666666",
            state=later_state,
            command=lambda: self._action("skip", "")
        ).pack(side="left")

        self._center(parent)
        self.wait_window()

    def _action(self, result: str, url: str):
        self.result = result
        if result == "download" and url:
            try:
                os.startfile(url)
            except Exception as e:
                logger.warning(f"Cannot open download URL: {e}")
                from tkinter import messagebox
                messagebox.showinfo(
                    "다운로드",
                    f"다운로드 경로를 직접 열어주세요:\n\n{url}"
                )
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        pw = parent.winfo_x() + parent.winfo_width() // 2
        ph = parent.winfo_y() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w // 2}+{ph - h // 2}")
