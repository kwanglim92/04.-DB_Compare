"""
Admin Window (v1.3.0)

Password-protected unified window that consolidates all administrator
functions previously spread across:
  - Server Settings dialog
  - Server DB (Spec) Manager window
  - Profile Manager (deprecated)

Entry is gated by ``ADMIN_PASSWORD`` (see config_helper). The window hosts
two tabs:
  1. 서버 설정   — connection host/port/credentials + online toggle
  2. Spec 관리  — per-profile CRUD, Import/Export (read-only when offline)
"""

import customtkinter as ctk
import logging
from typing import Callable, Optional

from src.core.sync_manager import SyncManager
from src.ui.server_settings_dialog import ServerSettingsPanel
from src.ui.server_spec_manager import ServerSpecManagerPanel
from src.ui.report_template_panel import ReportTemplatePanel

logger = logging.getLogger(__name__)


class AdminWindow(ctk.CTkToplevel):
    """Unified admin window with tabbed server settings + spec manager."""

    def __init__(
        self,
        parent,
        sync_manager: SyncManager,
        sync_mode: str = "offline",
        on_settings_saved: Optional[Callable[[str], None]] = None,
        on_spec_changed: Optional[Callable[[], None]] = None,
        on_check_update: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.sync_manager = sync_manager
        self._sync_mode = sync_mode
        self._on_settings_saved = on_settings_saved
        self._on_spec_changed = on_spec_changed
        self._on_check_update = on_check_update

        self.title("관리자 모드 — DB_Manager")
        self.geometry("1320x760")
        self.minsize(1000, 600)
        self.transient(parent)

        # Center on parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() - 1320) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 760) // 2
            self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        except Exception:
            pass

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Grab focus after construction
        self.after(100, self._grab_focus)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Construct the tabbed layout."""
        # Header
        header = ctk.CTkFrame(self, height=38, corner_radius=0, fg_color="#1f2a3a")
        header.pack(fill="x", side="top")
        ctk.CTkLabel(
            header,
            text="🔒 관리자 모드 — 서버 접속 및 Spec 편집은 여기에서만 수행됩니다.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=12, pady=6)

        mode_label = "● Online" if self._sync_mode == "online" else "● Offline (읽기 전용)"
        mode_color = "#4ade80" if self._sync_mode == "online" else "#fbbf24"
        ctk.CTkLabel(
            header, text=mode_label,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=mode_color
        ).pack(side="right", padx=12)

        # Tabview
        self.tabview = ctk.CTkTabview(self, anchor="nw")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        tab_settings = self.tabview.add("서버 설정")
        tab_specs = self.tabview.add("Spec 관리")
        tab_template = self.tabview.add("리포트 템플릿")

        # --- Tab 1: Server Settings ---
        self.settings_panel = ServerSettingsPanel(
            tab_settings,
            sync_manager=self.sync_manager,
            on_save_callback=self._handle_settings_saved,
        )
        self.settings_panel.pack(fill="both", expand=True, padx=5, pady=5)

        # Update check button (F13)
        update_row = ctk.CTkFrame(tab_settings, fg_color="transparent")
        update_row.pack(fill="x", padx=5, pady=(0, 8))
        ctk.CTkLabel(update_row, text="앱 업데이트:", font=("Segoe UI", 12)).pack(side="left", padx=(4, 8))
        ctk.CTkButton(
            update_row, text="지금 확인", width=100, height=28,
            font=("Segoe UI", 12),
            fg_color="#1f6aa5", hover_color="#17538a",
            command=self._handle_check_update
        ).pack(side="left")

        # --- Tab 2: Spec Manager ---
        # In offline mode the panel renders a graceful fallback + read-only guard
        self.specs_panel = ServerSpecManagerPanel(
            tab_specs,
            on_change_callback=self._handle_spec_changed,
            read_only=(self._sync_mode != "online"),
        )
        self.specs_panel.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Tab 3: Report Template ---
        self.template_panel = ReportTemplatePanel(tab_template)
        self.template_panel.pack(fill="both", expand=True, padx=5, pady=5)

        # Start on settings tab when offline (prompt user to go online first)
        if self._sync_mode != "online":
            self.tabview.set("서버 설정")
        else:
            self.tabview.set("Spec 관리")

    def _grab_focus(self):
        """Acquire modal-like focus without a hard grab (tabview needs flexibility)."""
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _handle_settings_saved(self, new_mode: str):
        """Propagate to parent and, if mode changed, note it for UX."""
        self._sync_mode = new_mode
        logger.info(f"Admin: server settings saved (mode={new_mode})")
        if self._on_settings_saved:
            try:
                self._on_settings_saved(new_mode)
            except Exception as e:
                logger.warning(f"on_settings_saved callback failed: {e}")

    def _handle_check_update(self):
        """Trigger manual update check via MainWindow callback."""
        if self._on_check_update:
            try:
                self._on_check_update()
            except Exception as e:
                logger.warning(f"on_check_update callback failed: {e}")

    def _handle_spec_changed(self):
        """Propagate spec-change notification to parent (MainWindow)."""
        if self._on_spec_changed:
            try:
                self._on_spec_changed()
            except Exception as e:
                logger.warning(f"on_spec_changed callback failed: {e}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_close(self):
        """Clean up DB connection and destroy."""
        try:
            if hasattr(self, "specs_panel"):
                self.specs_panel.cleanup()
        except Exception as e:
            logger.debug(f"specs_panel cleanup: {e}")
        self.destroy()


def prompt_admin_password(parent) -> bool:
    """Modal password prompt. Returns True on correct password, False otherwise."""
    from tkinter import simpledialog, messagebox
    from src.utils.config_helper import ADMIN_PASSWORD

    password = simpledialog.askstring(
        "관리자 인증",
        "관리자 비밀번호를 입력하세요:",
        show="*",
        parent=parent,
    )
    if password is None:
        return False
    if password == ADMIN_PASSWORD:
        return True
    messagebox.showerror("인증 실패", "비밀번호가 올바르지 않습니다.", parent=parent)
    return False
