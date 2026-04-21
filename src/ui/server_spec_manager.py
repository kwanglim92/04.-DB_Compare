"""
Server Spec Manager Window
Manage QC Spec data directly on the server PostgreSQL database
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import logging
import threading
from datetime import datetime

from src.core.server_db_manager import ServerDBManager
from src.utils.credential_manager import CredentialManager
from src.utils.format_helpers import format_spec, center_window_on_parent
from src.constants import COLORS

logger = logging.getLogger(__name__)

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


class ServerSpecManagerPanel(ctk.CTkFrame):
    """Embeddable panel for server QC Spec management.

    Designed to live inside a container (e.g., a tab in ``AdminWindow``).
    Parent owns lifecycle; call :meth:`cleanup` before destroying.

    Parameters
    ----------
    parent : widget
        Parent container.
    on_change_callback : callable, optional
        Invoked after successful CRUD operations (data changed on server).
    read_only : bool, default False
        When True, disables all editing controls (offline mode safeguard).
    """

    def __init__(self, parent, on_change_callback=None, read_only: bool = False):
        super().__init__(parent, fg_color="transparent")
        self.on_change_callback = on_change_callback
        self.read_only = read_only
        self.conn = None
        self.db_manager = None
        self.profiles = []  # [{id, profile_name, ...}]
        self._all_rows = {}  # tab_name -> [row dicts with 'id' key]
        self._view_mode = {}  # tab_name -> 'table' | 'tree'
        self._edit_buttons = []  # buttons to disable in read-only mode
        self._ui_ready = False

        # Connect to server
        if not self._connect():
            # Render a friendly fallback message instead of widgets
            self._render_connection_error()
            return

        self._create_ui()
        self._ui_ready = True

        if self.read_only:
            self._apply_read_only()

    # ========================================
    # Connection
    # ========================================

    def _connect(self) -> bool:
        """Establish server connection"""
        cm = CredentialManager()
        creds = cm.load_credentials()
        if not creds:
            return False

        try:
            self.conn = psycopg2.connect(
                host=creds['host'], port=creds['port'],
                dbname=creds['dbname'], user=creds['user'],
                password=creds['password'], connect_timeout=5
            )
            self.db_manager = ServerDBManager(self.conn)
            return True
        except Exception as e:
            logger.warning(f"Spec manager: server connection failed: {e}")
            return False

    def _render_connection_error(self):
        """Show a placeholder message when server is unreachable"""
        msg = ctk.CTkFrame(self, fg_color="transparent")
        msg.pack(fill="both", expand=True, padx=20, pady=40)
        ctk.CTkLabel(
            msg,
            text="서버에 연결할 수 없습니다.",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="gray70"
        ).pack(pady=(0, 8))
        ctk.CTkLabel(
            msg,
            text="'서버 설정' 탭에서 접속 정보를 확인해주세요.\n"
                 "오프라인 모드에서는 Spec 편집을 사용할 수 없습니다.",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            justify="center"
        ).pack()

    def _apply_read_only(self):
        """Disable all editing controls (offline mode)"""
        for btn in self._edit_buttons:
            try:
                btn.configure(state="disabled")
            except Exception:
                pass

        # Banner
        banner = ctk.CTkFrame(self, fg_color="#7c2d12", corner_radius=0, height=28)
        banner.pack(fill="x", side="top", before=self.tabview)
        ctk.CTkLabel(
            banner,
            text="⚠ 오프라인 모드 — 읽기 전용 (편집은 온라인 상태에서만 가능합니다)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white"
        ).pack(pady=4)

    def cleanup(self):
        """Close DB connection. Call from parent before destroying."""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    # ========================================
    # UI Creation
    # ========================================

    def _create_ui(self):
        """Build the main UI"""
        # Load profiles for tabs
        self.profiles = self.db_manager.get_all_profiles()

        # Tab view
        self.tabview = ctk.CTkTabview(self, anchor="nw")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        # Create Common Base tab
        self._create_tab("Common Base", is_common_base=True)

        # Create profile tabs
        for profile in self.profiles:
            self._create_tab(profile['profile_name'], profile_id=profile['id'])

        # Profile management toolbar (below tabview)
        profile_bar = ctk.CTkFrame(self, fg_color="transparent", height=35)
        profile_bar.pack(fill="x", padx=10, pady=(2, 0))

        btn_add_profile = ctk.CTkButton(
            profile_bar, text="+ 프로필 추가", width=110, height=28,
            fg_color="#1565c0", hover_color="#0d47a1",
            command=self._add_profile
        )
        btn_add_profile.pack(side="left", padx=(0, 5))
        self._edit_buttons.append(btn_add_profile)

        btn_rename_profile = ctk.CTkButton(
            profile_bar, text="프로필 이름변경", width=120, height=28,
            fg_color="#6a1b9a", hover_color="#4a148c",
            command=self._rename_profile
        )
        btn_rename_profile.pack(side="left", padx=(0, 5))
        self._edit_buttons.append(btn_rename_profile)

        btn_delete_profile = ctk.CTkButton(
            profile_bar, text="프로필 삭제", width=100, height=28,
            fg_color="#c62828", hover_color="#a01a1a",
            command=self._delete_profile
        )
        btn_delete_profile.pack(side="left")
        self._edit_buttons.append(btn_delete_profile)

        # Import/Export buttons (right side) — Import disabled in read-only, Export always allowed
        btn_import = ctk.CTkButton(
            profile_bar, text="Import", width=80, height=28,
            fg_color="#2e7d32", hover_color="#1b5e20",
            command=self._import_profile
        )
        btn_import.pack(side="right", padx=(5, 0))
        self._edit_buttons.append(btn_import)

        ctk.CTkButton(
            profile_bar, text="Export", width=80, height=28,
            fg_color="#00695c", hover_color="#004d40",
            command=self._export_profile
        ).pack(side="right")

        # Status bar
        self._create_status_bar()

        # Load initial data
        self.tabview.set("Common Base")
        self._load_tab_data("Common Base")

    def _create_tab(self, tab_name: str, is_common_base: bool = False,
                    profile_id: int = None):
        """Create a tab with toolbar + treeview"""
        tab = self.tabview.add(tab_name)

        # Store metadata
        if not hasattr(self, '_tab_meta'):
            self._tab_meta = {}
        self._tab_meta[tab_name] = {
            'is_common_base': is_common_base,
            'profile_id': profile_id,
            'loaded': False
        }

        # === Toolbar ===
        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.pack(fill="x", padx=5, pady=5)

        btn_add_item = ctk.CTkButton(
            toolbar, text="+ 추가", width=80, height=30,
            fg_color="#2fa572", hover_color="#248f5f",
            command=lambda tn=tab_name: self._add_item(tn)
        )
        btn_add_item.pack(side="left", padx=(0, 5))
        self._edit_buttons.append(btn_add_item)

        btn_delete_item = ctk.CTkButton(
            toolbar, text="삭제", width=70, height=30,
            fg_color="#c62828", hover_color="#a01a1a",
            command=lambda tn=tab_name: self._delete_selected(tn)
        )
        btn_delete_item.pack(side="left", padx=(0, 15))
        self._edit_buttons.append(btn_delete_item)

        # Search
        ctk.CTkLabel(toolbar, text="검색:").pack(side="left", padx=(0, 5))
        search_entry = ctk.CTkEntry(toolbar, width=200, placeholder_text="검색어 입력...")
        search_entry.pack(side="left", padx=(0, 10))
        search_entry.bind("<KeyRelease>", lambda e, tn=tab_name: self._on_search(tn))

        # Store search entry reference
        self._tab_meta[tab_name]['search_entry'] = search_entry

        # View mode toggle
        self._view_mode[tab_name] = 'table'
        view_toggle = ctk.CTkSwitch(
            toolbar, text="Group View", width=40,
            command=lambda tn=tab_name: self._toggle_view(tn)
        )
        view_toggle.pack(side="right", padx=(10, 5))
        self._tab_meta[tab_name]['view_toggle'] = view_toggle

        # Item count label
        count_label = ctk.CTkLabel(toolbar, text="0 items", text_color="gray")
        count_label.pack(side="right", padx=5)
        self._tab_meta[tab_name]['count_label'] = count_label

        # === Treeview ===
        tree_frame = ctk.CTkFrame(tab)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        columns = ('module', 'part_type', 'part_name', 'item_name',
                   'type', 'spec', 'unit', 'enabled')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                            selectmode='extended')

        # Column headings
        headings = {
            'module': ('Module', 100),
            'part_type': ('Part Type', 110),
            'part_name': ('Part Name', 100),
            'item_name': ('Item Name', 200),
            'type': ('Type', 70),
            'spec': ('Spec', 150),
            'unit': ('Unit', 60),
            'enabled': ('Enabled', 60),
        }
        for col, (text, width) in headings.items():
            tree.heading(col, text=text, anchor='w',
                         command=lambda c=col, tn=tab_name: self._sort_column(tn, c))
            tree.column(col, width=width, minwidth=50, anchor='w')

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Tree view tag styles
        tree.tag_configure('module', font=('Segoe UI', 11, 'bold'), foreground='#1f6aa5')
        tree.tag_configure('part_type', font=('Segoe UI', 10, 'bold'), foreground='#424242')
        tree.tag_configure('part', font=('Segoe UI', 10), foreground='#666666')
        tree.tag_configure('item', font=('Segoe UI', 10))
        tree.tag_configure('search_match', background='#fff3e0', foreground='#e65100')

        # Double-click to edit
        tree.bind("<Double-1>", lambda e, tn=tab_name: self._edit_selected(tn))

        # Right-click context menu
        tree.bind("<Button-3>", lambda e, tn=tab_name: self._show_context_menu(e, tn))

        # Store tree reference
        self._tab_meta[tab_name]['tree'] = tree

        # Bind tab change to lazy-load
        self.tabview.configure(command=self._on_tab_changed)

    def _create_status_bar(self):
        """Create bottom status bar"""
        status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_bar.pack(fill="x", side="bottom")

        creds = CredentialManager().load_credentials()
        host_info = f"{creds['host']}:{creds['port']}" if creds else "Unknown"

        self.status_label = ctk.CTkLabel(
            status_bar, text=f"Connected to {host_info}",
            font=("Segoe UI", 11), text_color="gray"
        )
        self.status_label.pack(side="left", padx=10, pady=2)

        versions = self.db_manager.get_sync_versions()
        ver_text = " | ".join(f"{k}: v{v}" for k, v in versions.items())
        ctk.CTkLabel(
            status_bar, text=ver_text,
            font=("Segoe UI", 10), text_color="gray"
        ).pack(side="right", padx=10, pady=2)

    # ========================================
    # Data Loading
    # ========================================

    def _on_tab_changed(self):
        """Lazy-load data when tab is selected"""
        tab_name = self.tabview.get()
        if tab_name and not self._tab_meta.get(tab_name, {}).get('loaded', False):
            self._load_tab_data(tab_name)

    def _load_tab_data(self, tab_name: str):
        """Load data for a tab from server"""
        meta = self._tab_meta.get(tab_name)
        if not meta:
            return

        try:
            if meta['is_common_base']:
                rows = self.db_manager.get_all_specs()
            else:
                rows = self.db_manager.get_profile_additional_checks(meta['profile_id'])

            self._all_rows[tab_name] = rows
            self._display_data(tab_name, rows)
            meta['loaded'] = True
        except Exception as e:
            logger.error(f"Failed to load tab data: {e}")
            messagebox.showerror("오류", f"데이터 로드 실패: {e}")

    def _display_data(self, tab_name: str, rows: list, search_query: str = ''):
        """Display data in current view mode"""
        if self._view_mode.get(tab_name) == 'tree':
            self._display_as_tree(tab_name, rows, search_query)
        else:
            self._display_as_table(tab_name, rows, search_query)

    def _display_as_table(self, tab_name: str, rows: list, search_query: str = ''):
        """Display rows in table view (flat list)"""
        tree = self._tab_meta[tab_name]['tree']
        tree.delete(*tree.get_children())

        for row in rows:
            spec_display = format_spec(row)
            enabled_display = "Y" if row.get('enabled', True) else "N"
            tags = ()
            if search_query and self._row_matches(row, search_query):
                tags = ('search_match',)
            tree.insert('', 'end', iid=str(row['id']), values=(
                row.get('module', ''),
                row.get('part_type', ''),
                row.get('part_name', ''),
                row.get('item_name', ''),
                row.get('validation_type', ''),
                spec_display,
                row.get('unit', ''),
                enabled_display
            ), tags=tags)

        count = len(rows)
        self._tab_meta[tab_name]['count_label'].configure(text=f"{count} items")

    def _display_as_tree(self, tab_name: str, rows: list, search_query: str = ''):
        """Display rows as grouped tree (Module > PartType > PartName > Item)"""
        tree = self._tab_meta[tab_name]['tree']
        tree.delete(*tree.get_children())

        # Build hierarchy: module -> part_type -> part_name -> [items]
        hierarchy = {}
        for row in rows:
            mod = row.get('module', '')
            pt = row.get('part_type', '')
            pn = row.get('part_name', '')
            hierarchy.setdefault(mod, {}).setdefault(pt, {}).setdefault(pn, []).append(row)

        item_count = 0
        for module, pt_data in sorted(hierarchy.items()):
            mod_count = sum(
                len(items) for td in pt_data.values() for items in td.values()
            )
            mod_id = tree.insert(
                '', 'end',
                text=f"\U0001F4C1 {module} ({mod_count})",
                values=('', '', ''),
                tags=('module',), open=True
            )

            for part_type, pn_data in sorted(pt_data.items()):
                type_count = sum(len(items) for items in pn_data.values())
                type_id = tree.insert(
                    mod_id, 'end',
                    text=f"  \U0001F4C2 {part_type} ({type_count})",
                    values=('', '', ''),
                    tags=('part_type',), open=True
                )

                for part_name, items in sorted(pn_data.items()):
                    part_id = tree.insert(
                        type_id, 'end',
                        text=f"    \U0001F4C4 {part_name}",
                        values=('', '', ''),
                        tags=('part',), open=True
                    )

                    for row in items:
                        item_tags = ('item',)
                        if search_query and self._row_matches(row, search_query):
                            item_tags = ('search_match',)
                        tree.insert(
                            part_id, 'end',
                            iid=str(row['id']),
                            text=f"      \u2022 {row.get('item_name', '')}",
                            values=(
                                row.get('validation_type', '').upper(),
                                format_spec(row),
                                row.get('unit', '')
                            ),
                            tags=item_tags
                        )
                        item_count += 1

        self._tab_meta[tab_name]['count_label'].configure(text=f"{item_count} items")

    # ========================================
    # View Mode Toggle
    # ========================================

    def _toggle_view(self, tab_name: str):
        """Toggle between table and tree view"""
        tree = self._tab_meta[tab_name]['tree']

        if self._view_mode.get(tab_name) == 'table':
            self._view_mode[tab_name] = 'tree'
            self._reconfigure_for_tree(tab_name, tree)
        else:
            self._view_mode[tab_name] = 'table'
            self._reconfigure_for_table(tab_name, tree)

        # Re-display current data
        rows = self._all_rows.get(tab_name, [])
        query = self._tab_meta[tab_name]['search_entry'].get().lower().strip()
        if query:
            rows = self._filter_rows(rows, query)
        self._display_data(tab_name, rows)

    def _reconfigure_for_table(self, tab_name: str, tree: ttk.Treeview):
        """Reconfigure treeview columns for table mode (8 columns)"""
        tree['columns'] = ('module', 'part_type', 'part_name', 'item_name',
                           'type', 'spec', 'unit', 'enabled')
        tree.configure(show='headings')

        headings = {
            'module': ('Module', 100),
            'part_type': ('Part Type', 110),
            'part_name': ('Part Name', 100),
            'item_name': ('Item Name', 200),
            'type': ('Type', 70),
            'spec': ('Spec', 150),
            'unit': ('Unit', 60),
            'enabled': ('Enabled', 60),
        }
        for col, (text, width) in headings.items():
            tree.heading(col, text=text, anchor='w',
                         command=lambda c=col, tn=tab_name: self._sort_column(tn, c))
            tree.column(col, width=width, minwidth=50, anchor='w')

    def _reconfigure_for_tree(self, tab_name: str, tree: ttk.Treeview):
        """Reconfigure treeview columns for tree mode (3 columns)"""
        tree['columns'] = ('type', 'spec', 'unit')
        tree.configure(show='tree headings')

        tree.heading('#0', text='Item Path')
        tree.column('#0', width=450, stretch=True)

        tree.heading('type', text='Type')
        tree.column('type', width=70, anchor='center', stretch=False)
        tree.heading('spec', text='Spec')
        tree.column('spec', width=150, anchor='center', stretch=False)
        tree.heading('unit', text='Unit')
        tree.column('unit', width=100, anchor='center', stretch=False)

    # ========================================
    # Search / Sort
    # ========================================

    def _filter_rows(self, rows: list, query: str) -> list:
        """Filter rows by search query string"""
        return [
            row for row in rows
            if (query in row.get('module', '').lower()
                or query in row.get('part_type', '').lower()
                or query in row.get('part_name', '').lower()
                or query in row.get('item_name', '').lower())
        ]

    def _row_matches(self, row: dict, query: str) -> bool:
        """Check if a row matches the search query"""
        return (query in row.get('module', '').lower()
                or query in row.get('part_type', '').lower()
                or query in row.get('part_name', '').lower()
                or query in row.get('item_name', '').lower())

    def _on_search(self, tab_name: str):
        """Filter rows by search query"""
        query = self._tab_meta[tab_name]['search_entry'].get().lower().strip()
        all_rows = self._all_rows.get(tab_name, [])

        if not query:
            self._display_data(tab_name, all_rows)
            return

        filtered = self._filter_rows(all_rows, query)
        self._display_data(tab_name, filtered, search_query=query)

    def _sort_column(self, tab_name: str, column: str):
        """Sort treeview by column"""
        rows = self._all_rows.get(tab_name, [])
        col_map = {
            'module': 'module', 'part_type': 'part_type',
            'part_name': 'part_name', 'item_name': 'item_name',
            'type': 'validation_type', 'unit': 'unit',
            'enabled': 'enabled'
        }
        key = col_map.get(column, column)

        # Toggle sort direction
        if not hasattr(self, '_sort_reverse'):
            self._sort_reverse = {}
        self._sort_reverse[column] = not self._sort_reverse.get(column, False)

        rows.sort(key=lambda r: str(r.get(key, '')).lower(),
                  reverse=self._sort_reverse[column])
        self._display_data(tab_name, rows)

    # ========================================
    # CRUD Operations
    # ========================================

    def _notify_change(self):
        """Notify parent that data has changed on the server"""
        if self.on_change_callback:
            try:
                self.on_change_callback()
            except Exception as e:
                logger.warning(f"on_change_callback failed: {e}")

    def _add_item(self, tab_name: str):
        """Open dialog to add a new spec item"""
        if self.read_only:
            return
        meta = self._tab_meta[tab_name]
        dialog = SpecItemDialog(self, tab_name)
        self.wait_window(dialog)

        if dialog.result:
            spec = dialog.result
            if meta['is_common_base']:
                new_id = self.db_manager.add_spec(spec)
            else:
                new_id = self.db_manager.add_additional_check(
                    meta['profile_id'], spec)

            if new_id:
                self._set_status(f"항목 추가됨: {spec['item_name']}")
                meta['loaded'] = False
                self._load_tab_data(tab_name)
                self._notify_change()
            else:
                messagebox.showerror("오류", "항목 추가에 실패했습니다.\n중복된 항목인지 확인해주세요.")

    def _edit_selected(self, tab_name: str):
        """Edit the selected row"""
        if self.read_only:
            return
        meta = self._tab_meta[tab_name]
        tree = meta['tree']
        selection = tree.selection()
        if not selection:
            return

        # In tree view, group nodes have non-numeric iids — skip them
        try:
            item_id = int(selection[0])
        except (ValueError, TypeError):
            return
        # Find row data
        rows = self._all_rows.get(tab_name, [])
        row_data = next((r for r in rows if r['id'] == item_id), None)
        if not row_data:
            return

        dialog = SpecItemDialog(self, tab_name, row_data)
        self.wait_window(dialog)

        if dialog.result:
            spec = dialog.result
            if meta['is_common_base']:
                ok = self.db_manager.update_spec(item_id, spec)
            else:
                ok = self.db_manager.update_additional_check(item_id, spec)

            if ok:
                self._set_status(f"항목 수정됨: {spec['item_name']}")
                meta['loaded'] = False
                self._load_tab_data(tab_name)
                self._notify_change()
            else:
                messagebox.showerror("오류", "항목 수정에 실패했습니다.")

    def _delete_selected(self, tab_name: str):
        """Delete selected rows"""
        if self.read_only:
            return
        meta = self._tab_meta[tab_name]
        tree = meta['tree']
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("알림", "삭제할 항목을 선택해주세요.")
            return

        # Filter out group nodes (non-numeric iids in tree view)
        numeric_sel = []
        for s in selection:
            try:
                numeric_sel.append(int(s))
            except (ValueError, TypeError):
                pass
        if not numeric_sel:
            messagebox.showinfo("알림", "삭제할 항목을 선택해주세요.\n(그룹 노드는 삭제할 수 없습니다)")
            return

        count = len(numeric_sel)
        if not messagebox.askyesno("삭제 확인",
                                    f"선택한 {count}개 항목을 삭제하시겠습니까?"):
            return

        ids = numeric_sel
        if meta['is_common_base']:
            ok = self.db_manager.delete_specs_batch(ids)
        else:
            ok = self.db_manager.delete_additional_checks_batch(ids)

        if ok:
            self._set_status(f"{count}개 항목 삭제됨")
            meta['loaded'] = False
            self._load_tab_data(tab_name)
            self._notify_change()
        else:
            messagebox.showerror("오류", "삭제에 실패했습니다.")

    def _set_status(self, text: str):
        """Update status bar"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=text)

    def _show_context_menu(self, event, tab_name: str):
        """Show right-click context menu on treeview item"""
        tree = self._tab_meta[tab_name]['tree']
        item_id = tree.identify_row(event.y)
        if not item_id:
            return

        tree.selection_set(item_id)
        tree.focus(item_id)

        # Only show menu for actual items (numeric iid)
        try:
            int(item_id)
        except (ValueError, TypeError):
            return

        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="편집", command=lambda: self._edit_selected(tab_name))
        menu.add_command(label="삭제", command=lambda: self._delete_selected(tab_name))
        menu.add_separator()
        menu.add_command(label="항목 경로 복사",
                         command=lambda: self._copy_item_path(tab_name, item_id))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_item_path(self, tab_name: str, item_id: str):
        """Copy item path (Module/PartType/PartName/ItemName) to clipboard"""
        rows = self._all_rows.get(tab_name, [])
        row = next((r for r in rows if r['id'] == int(item_id)), None)
        if not row:
            return
        path = f"{row.get('module', '')}/{row.get('part_type', '')}/{row.get('part_name', '')}/{row.get('item_name', '')}"
        self.clipboard_clear()
        self.clipboard_append(path)
        self._set_status(f"복사됨: {path}")

    # ========================================
    # Profile CRUD
    # ========================================

    def _get_current_profile_meta(self):
        """Get the profile meta for the currently selected tab (non-Common Base)"""
        tab_name = self.tabview.get()
        meta = self._tab_meta.get(tab_name)
        if not meta or meta['is_common_base']:
            return None, None
        return tab_name, meta

    def _add_profile(self):
        """Create a new profile via dialog"""
        if self.read_only:
            return
        name = simpledialog.askstring("프로필 추가", "새 프로필 이름:", parent=self)
        if not name or not name.strip():
            return
        name = name.strip()

        # Check for duplicate
        existing = [p['profile_name'] for p in self.profiles]
        if name in existing:
            messagebox.showwarning("중복", f"'{name}' 프로필이 이미 존재합니다.")
            return

        new_id = self.db_manager.create_profile(name)
        if new_id:
            self.profiles.append({'id': new_id, 'profile_name': name})
            self._create_tab(name, profile_id=new_id)
            self.tabview.set(name)
            self._load_tab_data(name)
            self._set_status(f"프로필 추가됨: {name}")
            self._notify_change()
        else:
            messagebox.showerror("오류", "프로필 추가에 실패했습니다.")

    def _rename_profile(self):
        """Rename the currently selected profile"""
        if self.read_only:
            return
        tab_name, meta = self._get_current_profile_meta()
        if not tab_name:
            messagebox.showinfo("알림", "이름을 변경할 프로필 탭을 선택해주세요.\n(Common Base는 변경할 수 없습니다)")
            return

        new_name = simpledialog.askstring(
            "프로필 이름변경", f"'{tab_name}'의 새 이름:", parent=self,
            initialvalue=tab_name)
        if not new_name or not new_name.strip() or new_name.strip() == tab_name:
            return
        new_name = new_name.strip()

        profile_id = meta['profile_id']
        if self.db_manager.rename_profile(profile_id, new_name):
            # Update internal state
            for p in self.profiles:
                if p['id'] == profile_id:
                    p['profile_name'] = new_name
                    break

            # Recreate tabs (CTkTabview doesn't support tab rename)
            self._rebuild_tabs()
            self.tabview.set(new_name)
            self._set_status(f"프로필 이름변경: {tab_name} → {new_name}")
            self._notify_change()
        else:
            messagebox.showerror("오류", "프로필 이름변경에 실패했습니다.")

    def _delete_profile(self):
        """Delete the currently selected profile"""
        if self.read_only:
            return
        tab_name, meta = self._get_current_profile_meta()
        if not tab_name:
            messagebox.showinfo("알림", "삭제할 프로필 탭을 선택해주세요.\n(Common Base는 삭제할 수 없습니다)")
            return

        if not messagebox.askyesno(
                "프로필 삭제",
                f"'{tab_name}' 프로필과 관련 데이터를 모두 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다."):
            return

        profile_id = meta['profile_id']
        if self.db_manager.delete_profile(profile_id):
            self.profiles = [p for p in self.profiles if p['id'] != profile_id]
            self._rebuild_tabs()
            self.tabview.set("Common Base")
            self._set_status(f"프로필 삭제됨: {tab_name}")
            self._notify_change()
        else:
            messagebox.showerror("오류", "프로필 삭제에 실패했습니다.")

    def _rebuild_tabs(self):
        """Rebuild all tabs from current profile list"""
        # Remove all existing tabs
        for name in list(self._tab_meta.keys()):
            self.tabview.delete(name)
        self._tab_meta.clear()
        self._all_rows.clear()
        self._view_mode.clear()

        # Recreate
        self._create_tab("Common Base", is_common_base=True)
        for profile in self.profiles:
            self._create_tab(profile['profile_name'], profile_id=profile['id'])

    # ========================================
    # Import / Export
    # ========================================

    def _export_profile(self):
        """Export current tab data to JSON file"""
        tab_name = self.tabview.get()
        meta = self._tab_meta.get(tab_name)
        if not meta:
            return

        if meta['is_common_base']:
            # Export Common Base as specs list
            rows = self._all_rows.get(tab_name, [])
            export_data = {
                'version': '1.0',
                'source': 'server_db',
                'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'profile_name': 'common_base',
                'specs': rows,
            }
        else:
            profile_id = meta['profile_id']
            export_data = self.db_manager.export_profile_data(profile_id, tab_name)
            export_data['export_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        default_name = f"{tab_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = filedialog.asksaveasfilename(
            title="Export", defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            messagebox.showinfo("Export 완료",
                                f"'{tab_name}' 데이터를 내보냈습니다.\n{filepath}")
            self._set_status(f"Export 완료: {filepath}")
        except Exception as e:
            messagebox.showerror("Export 실패", f"내보내기에 실패했습니다.\n{e}")

    def _import_profile(self):
        """Import profile data from JSON file into server DB"""
        if self.read_only:
            return
        filepath = filedialog.askopenfilename(
            title="Import Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            messagebox.showerror("Import 실패", f"파일을 읽을 수 없습니다.\n{e}")
            return

        # Validate format
        profile_name = import_data.get('profile_name')
        profile_data = import_data.get('profile_data')
        if not profile_name or not profile_data:
            messagebox.showerror("Import 실패", "유효하지 않은 프로필 파일입니다.")
            return

        # Find or create profile
        existing = next((p for p in self.profiles if p['profile_name'] == profile_name), None)
        if existing:
            if not messagebox.askyesno(
                    "프로필 존재",
                    f"'{profile_name}' 프로필이 이미 존재합니다.\n덮어쓰시겠습니까?"):
                return
            profile_id = existing['id']
        else:
            profile_id = self.db_manager.create_profile(profile_name)
            if not profile_id:
                messagebox.showerror("Import 실패", "프로필 생성에 실패했습니다.")
                return
            self.profiles.append({'id': profile_id, 'profile_name': profile_name})

        # Import data
        if self.db_manager.import_profile_data(profile_id, profile_data):
            self._rebuild_tabs()
            self.tabview.set(profile_name)
            self._load_tab_data(profile_name)
            messagebox.showinfo("Import 완료",
                                f"'{profile_name}' 프로필을 가져왔습니다.")
            self._set_status(f"Import 완료: {profile_name}")
            self._notify_change()
        else:
            messagebox.showerror("Import 실패", "데이터 가져오기에 실패했습니다.")

    def _refresh_all(self):
        """Reload all tabs"""
        for tab_name in self._tab_meta:
            self._tab_meta[tab_name]['loaded'] = False
        self._load_tab_data(self.tabview.get())


# ========================================
# Add / Edit Dialogs
# ========================================

class SpecItemDialog(ctk.CTkToplevel):
    """Unified dialog for adding / editing a spec item"""

    def __init__(self, parent, tab_name: str, row_data: dict = None):
        super().__init__(parent)
        self.result = None
        self.row_data = row_data  # None = add mode
        self._is_edit = row_data is not None

        title = f"항목 편집 — {tab_name}" if self._is_edit else f"항목 추가 — {tab_name}"
        self.title(title)
        self.geometry("420x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        center_window_on_parent(self, parent, 420, 400)
        self._create_widgets()

    def _create_widgets(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=15, pady=10)

        # --- Compact grid form ---
        form = ctk.CTkFrame(main)
        form.pack(fill="x", pady=(0, 8))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        r = self.row_data or {}

        # Row 0: Module / Part Type (2-column layout)
        ctk.CTkLabel(form, text="Module:").grid(row=0, column=0, padx=(10, 4), pady=4, sticky='w')
        self.module_entry = ctk.CTkEntry(form, placeholder_text="Dsp")
        self.module_entry.grid(row=0, column=1, padx=(0, 8), pady=4, sticky='ew')

        ctk.CTkLabel(form, text="Part Type:").grid(row=0, column=2, padx=(8, 4), pady=4, sticky='w')
        self.ptype_entry = ctk.CTkEntry(form, placeholder_text="XScanner")
        self.ptype_entry.grid(row=0, column=3, padx=(0, 10), pady=4, sticky='ew')

        # Row 1: Part Name / Unit (2-column layout)
        ctk.CTkLabel(form, text="Part Name:").grid(row=1, column=0, padx=(10, 4), pady=4, sticky='w')
        self.pname_entry = ctk.CTkEntry(form, placeholder_text="100um")
        self.pname_entry.grid(row=1, column=1, padx=(0, 8), pady=4, sticky='ew')

        ctk.CTkLabel(form, text="Unit:").grid(row=1, column=2, padx=(8, 4), pady=4, sticky='w')
        self.unit_entry = ctk.CTkEntry(form)
        self.unit_entry.grid(row=1, column=3, padx=(0, 10), pady=4, sticky='ew')

        # Row 2: Item Name (full width)
        ctk.CTkLabel(form, text="Item Name:").grid(row=2, column=0, padx=(10, 4), pady=4, sticky='w')
        self.iname_entry = ctk.CTkEntry(form)
        self.iname_entry.grid(row=2, column=1, columnspan=3, padx=(0, 10), pady=4, sticky='ew')

        # Fill values in edit mode
        if self._is_edit:
            self.module_entry.insert(0, r.get('module', ''))
            self.ptype_entry.insert(0, r.get('part_type', ''))
            self.pname_entry.insert(0, r.get('part_name', ''))
            self.iname_entry.insert(0, r.get('item_name', ''))
            self.unit_entry.insert(0, r.get('unit', ''))

        # --- Validation type radio ---
        type_frame = ctk.CTkFrame(main)
        type_frame.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(type_frame, text="검증 타입:",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=(10, 8), pady=6, sticky='w')

        self.type_var = ctk.StringVar(value=r.get('validation_type', 'range'))
        for col, (val, text) in enumerate([("range", "Range"), ("exact", "Exact"), ("check", "Check")]):
            ctk.CTkRadioButton(type_frame, text=text, variable=self.type_var,
                               value=val, command=self._on_type_change
                               ).grid(row=0, column=col + 1, padx=6, pady=6)

        # --- Spec fields (dynamic visibility) ---
        self._spec_frame = ctk.CTkFrame(main)
        self._spec_frame.pack(fill="x", pady=(0, 8))
        self._spec_frame.columnconfigure(1, weight=1)
        self._spec_frame.columnconfigure(3, weight=1)

        # Range fields: Min / Max on same row
        self._min_label = ctk.CTkLabel(self._spec_frame, text="Min:")
        self.min_entry = ctk.CTkEntry(self._spec_frame)
        self._max_label = ctk.CTkLabel(self._spec_frame, text="Max:")
        self.max_entry = ctk.CTkEntry(self._spec_frame)

        # Exact field
        self._expected_label = ctk.CTkLabel(self._spec_frame, text="Expected:")
        self.expected_entry = ctk.CTkEntry(self._spec_frame)

        # Fill spec values in edit mode
        if self._is_edit:
            min_val = r.get('min_spec', '')
            max_val = r.get('max_spec', '')
            expected = r.get('expected_value', '')
            if min_val is not None and min_val != '':
                self.min_entry.insert(0, str(min_val))
            if max_val is not None and max_val != '':
                self.max_entry.insert(0, str(max_val))
            if expected:
                self.expected_entry.insert(0, str(expected))

        self._on_type_change()

        # --- Buttons ---
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(btn_frame, text="취소", width=80,
                       fg_color="gray40", command=self.destroy).pack(side="right")
        save_text = "저장" if self._is_edit else "추가"
        ctk.CTkButton(btn_frame, text=save_text, width=80,
                       command=self._save).pack(side="right", padx=5)

    def _on_type_change(self):
        """Show/hide spec fields based on validation type"""
        vtype = self.type_var.get()

        # Clear all spec widgets from grid
        for widget in (self._min_label, self.min_entry,
                       self._max_label, self.max_entry,
                       self._expected_label, self.expected_entry):
            widget.grid_forget()

        if vtype == "range":
            self._min_label.grid(row=0, column=0, padx=(10, 4), pady=4, sticky='w')
            self.min_entry.grid(row=0, column=1, padx=(0, 8), pady=4, sticky='ew')
            self._max_label.grid(row=0, column=2, padx=(8, 4), pady=4, sticky='w')
            self.max_entry.grid(row=0, column=3, padx=(0, 10), pady=4, sticky='ew')
        elif vtype == "exact":
            self._expected_label.grid(row=0, column=0, padx=(10, 4), pady=4, sticky='w')
            self.expected_entry.grid(row=0, column=1, columnspan=3, padx=(0, 10), pady=4, sticky='ew')
        # check: no spec fields shown

    def _save(self):
        module = self.module_entry.get().strip()
        ptype = self.ptype_entry.get().strip()
        pname = self.pname_entry.get().strip()
        iname = self.iname_entry.get().strip()

        if not all([module, ptype, pname, iname]):
            messagebox.showwarning("입력 오류",
                                   "Module, Part Type, Part Name, Item Name은 필수입니다.")
            return

        vtype = self.type_var.get()
        spec = {
            'module': module, 'part_type': ptype,
            'part_name': pname, 'item_name': iname,
            'validation_type': vtype,
            'unit': self.unit_entry.get().strip(),
            'enabled': True, 'description': ''
        }

        if vtype == "range":
            min_val = self.min_entry.get().strip()
            max_val = self.max_entry.get().strip()
            spec['min_spec'] = float(min_val) if min_val else None
            spec['max_spec'] = float(max_val) if max_val else None
        elif vtype == "exact":
            spec['expected_value'] = self.expected_entry.get().strip() or None

        self.result = spec
        self.destroy()
