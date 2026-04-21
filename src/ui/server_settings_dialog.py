"""
Server Settings Panel
Embeddable frame for configuring server connection and sync mode.

Historically this module provided a standalone CTkToplevel dialog.
From v1.3.0, it exposes an embeddable ``ServerSettingsPanel`` used inside
the unified ``AdminWindow``.
"""

import customtkinter as ctk
import logging
import threading

from src.utils.credential_manager import CredentialManager
from src.core.sync_manager import SyncManager

logger = logging.getLogger(__name__)

# Default connection values
DEFAULTS = {
    'host': '10.4.1.141',
    'port': '5434',
    'dbname': 'dbmanager',
    'user': 'dbmanager',
}


class ServerSettingsPanel(ctk.CTkFrame):
    """Embeddable panel for server connection settings.

    Designed to be placed inside a parent container (e.g., a tab view).
    Lifecycle is owned by the parent container.
    """

    def __init__(self, parent, sync_manager: SyncManager, on_save_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.sync_manager = sync_manager
        self.credential_manager = CredentialManager()
        self.on_save_callback = on_save_callback

        self._create_widgets()
        self._load_existing_credentials()

    def _create_widgets(self):
        """Build the panel UI — compact grid layout"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # Title
        ctk.CTkLabel(
            main_frame, text="서버 연결 설정",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10))

        # Connection fields — grid layout for compactness
        fields_frame = ctk.CTkFrame(main_frame)
        fields_frame.pack(fill="x", pady=(0, 8))
        fields_frame.columnconfigure(1, weight=1)

        row = 0
        pad = {'padx': (12, 12), 'pady': (6, 0), 'sticky': 'w'}
        entry_pad = {'padx': (12, 12), 'pady': (6, 0), 'sticky': 'ew'}

        ctk.CTkLabel(fields_frame, text="Host:").grid(row=row, column=0, **pad)
        self.host_entry = ctk.CTkEntry(fields_frame)
        self.host_entry.grid(row=row, column=1, **entry_pad)

        row += 1
        ctk.CTkLabel(fields_frame, text="Port:").grid(row=row, column=0, **pad)
        self.port_entry = ctk.CTkEntry(fields_frame, width=100)
        self.port_entry.grid(row=row, column=1, **entry_pad)

        row += 1
        ctk.CTkLabel(fields_frame, text="Database:").grid(row=row, column=0, **pad)
        self.db_entry = ctk.CTkEntry(fields_frame)
        self.db_entry.grid(row=row, column=1, **entry_pad)

        row += 1
        ctk.CTkLabel(fields_frame, text="User:").grid(row=row, column=0, **pad)
        self.user_entry = ctk.CTkEntry(fields_frame)
        self.user_entry.grid(row=row, column=1, **entry_pad)

        row += 1
        ctk.CTkLabel(fields_frame, text="Password:").grid(row=row, column=0, **pad)
        self.password_entry = ctk.CTkEntry(fields_frame, show="*",
                                            placeholder_text="비밀번호 입력")
        self.password_entry.grid(row=row, column=1, padx=(12, 12), pady=(6, 12), sticky='ew')

        # Mode switch
        self.mode_var = ctk.StringVar(value="offline")
        self.mode_switch = ctk.CTkSwitch(
            main_frame,
            text="온라인 모드 (서버 동기화 사용)",
            variable=self.mode_var,
            onvalue="online",
            offvalue="offline"
        )
        self.mode_switch.pack(fill="x", pady=(0, 8))

        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame, text="", text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=(0, 8))

        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.test_btn = ctk.CTkButton(
            btn_frame, text="연결 테스트",
            command=self._test_connection, width=110
        )
        self.test_btn.pack(side="left")

        self.save_btn = ctk.CTkButton(
            btn_frame, text="저장",
            command=self._save, width=80
        )
        self.save_btn.pack(side="right")

    def _load_existing_credentials(self):
        """Load saved credentials or fill defaults"""
        creds = self.credential_manager.load_credentials()
        if creds:
            self.host_entry.insert(0, creds.get('host', DEFAULTS['host']))
            self.port_entry.insert(0, str(creds.get('port', DEFAULTS['port'])))
            self.db_entry.insert(0, creds.get('dbname', DEFAULTS['dbname']))
            self.user_entry.insert(0, creds.get('user', DEFAULTS['user']))
            self.password_entry.insert(0, creds.get('password', ''))
            self.mode_var.set(creds.get('mode', 'offline'))
        else:
            # Fill defaults — password left empty for user to enter
            self.host_entry.insert(0, DEFAULTS['host'])
            self.port_entry.insert(0, DEFAULTS['port'])
            self.db_entry.insert(0, DEFAULTS['dbname'])
            self.user_entry.insert(0, DEFAULTS['user'])

    def _get_form_values(self) -> dict:
        """Get current form values"""
        port_str = self.port_entry.get().strip()
        return {
            'host': self.host_entry.get().strip(),
            'port': int(port_str) if port_str.isdigit() else 5434,
            'dbname': self.db_entry.get().strip() or 'dbmanager',
            'user': self.user_entry.get().strip() or 'dbmanager',
            'password': self.password_entry.get(),
            'mode': self.mode_var.get()
        }

    def _validate_form(self) -> bool:
        """Validate required fields"""
        values = self._get_form_values()
        if not values['host']:
            self._set_status("Host를 입력해주세요", "red")
            return False
        if not values['password']:
            self._set_status("Password를 입력해주세요", "red")
            return False
        return True

    def _set_status(self, text: str, color: str = "gray"):
        """Update status label"""
        self.status_label.configure(text=text, text_color=color)

    def _test_connection(self):
        """Test server connection in background thread"""
        if not self._validate_form():
            return

        values = self._get_form_values()
        self.test_btn.configure(state="disabled", text="연결 중...")
        self._set_status("연결 테스트 중...", "gray")

        def _test():
            success, message = self.sync_manager.test_connection(
                host=values['host'],
                port=values['port'],
                dbname=values['dbname'],
                user=values['user'],
                password=values['password']
            )
            self.after(0, lambda: self._on_test_result(success, message))

        threading.Thread(target=_test, daemon=True).start()

    def _on_test_result(self, success: bool, message: str):
        """Handle test connection result"""
        self.test_btn.configure(state="normal", text="연결 테스트")
        color = "#0d7d3d" if success else "red"
        self._set_status(message, color)

    def _save(self):
        """Save credentials and mode"""
        if not self._validate_form():
            return

        values = self._get_form_values()

        # Save encrypted credentials
        if self.credential_manager.save_credentials(values):
            self._set_status("저장 완료", "#0d7d3d")
            logger.info(f"Server settings saved (mode: {values['mode']})")

            # Configure sync manager
            if values['mode'] == 'online':
                self.sync_manager.configure_server(
                    host=values['host'],
                    port=values['port'],
                    dbname=values['dbname'],
                    user=values['user'],
                    password=values['password']
                )

            if self.on_save_callback:
                self.on_save_callback(values['mode'])
        else:
            self._set_status("저장 실패", "red")
