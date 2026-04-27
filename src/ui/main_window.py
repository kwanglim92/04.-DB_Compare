import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import logging
from pathlib import Path
import threading
import json
import os
import sys

from src.core.spec_manager import SpecManager
from src.core.comparator import QCComparator
from src.core.sync_manager import SyncManager
from src.ui.tree_view import DBTreeView
from src.utils.config_helper import get_config_dir, get_cache_dir, get_appdata_dir
from src.utils.credential_manager import CredentialManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MainWindow:
    """Main Application Window"""
    
    def __init__(self):
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("DB_Manager - QC Inspection Tool v1.4.0")
        self.root.geometry("1600x800")
        
        # Initialize variables
        self.db_root = None
        self.db_data = None
        self.spec_manager = SpecManager()
        self.comparator = QCComparator()
        self.current_profile = None
        self.qc_report = None
        self.spec_edit_mode = False
        self.temp_specs = {}  # Temporary specs being edited
        self.review_checklist_enabled = False  # Toggled via Profile Manager
        self.sync_mode = "offline"  # "online" or "offline"

        # Profile Viewer filter state (F3)
        self.viewer_filter = "ALL"
        self._all_viewer_rows = []  # list of (values_tuple, tag_str)
        self._viewer_counts = {"ALL": 0, "PASS": 0, "CHECK": 0, "FAIL": 0, "PENDING": 0}

        # Initialize sync manager
        self.sync_manager = SyncManager(get_cache_dir())
        self.credential_manager = CredentialManager()

        # Load settings
        self.load_settings()

        # Attempt server sync if online mode
        self._initial_sync()

        # Load spec config — try new multi-file structure first, fallback to legacy
        config_dir = get_config_dir(mode=self.sync_mode)
        common_base = config_dir / "common_base.json"
        profiles_dir = config_dir / "profiles"

        if common_base.exists() and profiles_dir.exists():
            logger.info("Loading config from multi-file structure")
            self.spec_manager.load_multi_file_config(config_dir)
        else:
            # Legacy single-file fallback
            spec_file = config_dir / "qc_specs.json"
            if spec_file.exists():
                logger.info("Loading config from legacy qc_specs.json")
                self.spec_manager.load_spec_file(str(spec_file))

        # Create UI
        self.create_menu()
        self.create_toolbar()
        self.create_main_content()
        self.create_status_bar()

        # Update status with sync info
        self._update_sync_status()
    
    def load_settings(self):
        """Load settings from config file"""
        settings_file = get_config_dir() / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                self.db_root = settings.get('db_root_path', '')
                default_profile = settings.get('default_equipment_profile', '')
                if default_profile:
                    self.current_profile = default_profile
                self.review_checklist_enabled = settings.get('review_checklist_enabled', False)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load settings, using defaults: {e}")

        # Load sync mode from credentials
        creds = self.credential_manager.load_credentials()
        if creds:
            self.sync_mode = creds.get('mode', 'offline')

    def _initial_sync(self):
        """Attempt server sync on startup if online mode (non-blocking)"""
        if self.sync_mode != "online":
            return

        creds = self.credential_manager.load_credentials()
        if not creds:
            return

        self.sync_manager.configure_server(
            host=creds['host'],
            port=creds['port'],
            dbname=creds['dbname'],
            user=creds['user'],
            password=creds['password']
        )

        def _do_sync():
            if self.sync_manager.connect():
                success, msg = self.sync_manager.sync()
                self.sync_manager.disconnect()
                self.root.after(0, lambda: self._on_initial_sync_done(success, msg))
            else:
                self.root.after(0, lambda: self._on_initial_sync_done(
                    False, "서버에 연결할 수 없습니다"))

        threading.Thread(target=_do_sync, daemon=True).start()

    def _on_initial_sync_done(self, success: bool, msg: str):
        """Handle initial sync result on main thread"""
        if success:
            logger.info(f"Startup sync: {msg}")
            self._reload_specs()
            self.update_status(f"Ready (Online - {msg})")
        else:
            logger.warning(f"Startup sync failed: {msg}")
            self.update_status("Ready (Online - 로컬 캐시 사용)")

    def _update_sync_status(self):
        """Update status bar with sync mode info"""
        if self.sync_mode == "online":
            if self.sync_manager.has_local_cache():
                self.update_status("Ready (Online Mode)")
            else:
                self.update_status("Ready (Online - No cache yet)")
        else:
            self.update_status("Ready")
    
    def create_menu(self):
        """Create menu bar"""
        # Note: Keep minimal, most actions via toolbar buttons
        pass
    
    def create_toolbar(self):
        """Create toolbar with action buttons"""
        toolbar = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        toolbar.pack(fill="x", padx=0, pady=0)
        
        # Open DB button
        self.open_db_btn = ctk.CTkButton(
            toolbar,
            text="Open DB",
            font=("Segoe UI", 14, "bold"),
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self.open_db,
            width=120,
            height=35
        )
        self.open_db_btn.pack(side="left", padx=10, pady=10)
        
        # Profile Selection
        ctk.CTkLabel(toolbar, text="Profile:", font=("Segoe UI", 14)).pack(side="left", padx=(10, 5))
        
        self.profile_combo = ctk.CTkComboBox(
            toolbar,
            values=self.get_profile_list(),
            command=self.on_profile_changed,
            width=200
        )
        self.profile_combo.pack(side="left", padx=5)
        
        if self.current_profile:
            self.profile_combo.set(self.current_profile)
        
        # Run QC button
        self.run_qc_btn = ctk.CTkButton(
            toolbar,
            text="Run QC",
            font=("Segoe UI", 14, "bold"),
            fg_color="#2fa572",
            hover_color="#248f5f",
            command=self.run_qc_inspection,
            width=120,
            height=35,
            state="disabled"  # Disabled until DB loaded
        )
        self.run_qc_btn.pack(side="left", padx=20)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            toolbar,
            text="Export",
            font=("Segoe UI", 14, "bold"),
            fg_color="#ed6c02",
            hover_color="#c75c02",
            command=self.export_report,
            width=100,
            height=35,
            state="disabled"
        )
        self.export_btn.pack(side="left", padx=5)
        
        # Review Checklist button
        self.review_cl_btn = ctk.CTkButton(
            toolbar,
            text="Review Checklist",
            font=("Segoe UI", 14, "bold"),
            fg_color="#7b1fa2",
            hover_color="#5c1680",
            command=self.review_checklist,
            width=160,
            height=35,
            state="disabled"
        )
        self.review_cl_btn.pack(side="left", padx=5)
        if not self.review_checklist_enabled:
            self.review_cl_btn.pack_forget()
        
        # Dark mode toggle
        self.dark_mode_switch = ctk.CTkSwitch(
            toolbar,
            text="Dark Mode",
            font=("Segoe UI", 11),
            command=self.toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.dark_mode_switch.select()  # Start in dark mode
        self.dark_mode_switch.pack(side="right", padx=10)

        # Admin button (gated entry for server settings + spec management)
        self.admin_btn = ctk.CTkButton(
            toolbar,
            text="🔒 Admin",
            font=("Segoe UI", 12, "bold"),
            fg_color="#37474f",
            hover_color="#263238",
            command=self.open_admin_window,
            width=90,
            height=30
        )
        self.admin_btn.pack(side="right", padx=5)

        # Sync indicator (display-only)
        sync_text = "● Online" if self.sync_mode == "online" else "● Offline"
        sync_color = "#0d7d3d" if self.sync_mode == "online" else "gray50"
        self.sync_indicator = ctk.CTkLabel(
            toolbar,
            text=sync_text,
            font=("Segoe UI", 11, "bold"),
            text_color=sync_color
        )
        self.sync_indicator.pack(side="right", padx=(5, 5))
    
    def create_main_content(self):
        """Create main content area: DB Tree + 2-Panel Right (Results + Profile Viewer)"""
        # Main container
        main_container = ctk.CTkFrame(self.root, corner_radius=0)
        main_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # === Left panel - DB Tree ===
        left_panel = ctk.CTkFrame(main_container, corner_radius=8)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        tree_header_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        tree_header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            tree_header_frame,
            text="DB STRUCTURE",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        ).pack(side="left")

        # DB tree search (F1) — input + match count
        self._db_search_after_id = None
        self.db_search_entry = ctk.CTkEntry(
            tree_header_frame,
            placeholder_text="검색: 모듈 / Part / Item…",
            width=260,
            height=28,
            state="disabled"  # enabled when DB is populated
        )
        self.db_search_entry.pack(side="left", padx=(12, 6))
        self.db_search_entry.bind("<KeyRelease>", self._on_db_search_key)
        self.db_search_entry.bind("<Return>", lambda e: self._do_db_search(immediate=True))
        self.db_search_entry.bind("<Escape>", lambda e: self._clear_db_search())

        self.db_search_count_label = ctk.CTkLabel(
            tree_header_frame, text="", font=("Segoe UI", 11),
            text_color="gray60", width=80
        )
        self.db_search_count_label.pack(side="left", padx=(0, 8))

        # Expand/Collapse buttons
        btn_frame = ctk.CTkFrame(tree_header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(
            btn_frame,
            text="Expand All",
            font=("Segoe UI", 12),
            width=80,
            height=25,
            command=self.expand_all_tree,
            fg_color="#555555",
            hover_color="#333333"
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            btn_frame,
            text="Collapse All",
            font=("Segoe UI", 12),
            width=80,
            height=25,
            command=self.collapse_all_tree,
            fg_color="#555555",
            hover_color="#333333"
        ).pack(side="left", padx=2)
        
        tree_container = ctk.CTkFrame(left_panel, corner_radius=8)
        tree_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.db_tree = DBTreeView(tree_container)
        
        # === Right panel - 2 sections ===
        right_panel = ctk.CTkFrame(main_container, corner_radius=8, width=1060)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # --- Top: QC Results (35%) ---
        results_container = ctk.CTkFrame(right_panel, corner_radius=8)
        results_container.pack(fill="both", expand=False, side="top", padx=5, pady=5)
        results_container.configure(height=280)
        
        results_header = ctk.CTkLabel(
            results_container,
            text="QC INSPECTION RESULTS",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        results_header.pack(fill="x", padx=10, pady=(10, 5))
        
        self.results_frame = ctk.CTkScrollableFrame(results_container, corner_radius=8)
        self.results_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        self.results_placeholder = ctk.CTkLabel(
            self.results_frame,
            text="Run QC to see results",
            font=("Segoe UI", 12),
            text_color="gray"
        )
        self.results_placeholder.pack(pady=30)
        
        # --- Bottom: Profile Viewer (65%) ---
        viewer_container = ctk.CTkFrame(right_panel, corner_radius=8)
        viewer_container.pack(fill="both", expand=True, side="bottom", padx=5, pady=(0, 5))
        
        viewer_header = ctk.CTkFrame(viewer_container, fg_color="transparent")
        viewer_header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            viewer_header,
            text="PROFILE VIEWER",
            font=("Segoe UI", 14, "bold")
        ).pack(side="left")
        
        self.profile_viewer_count_label = ctk.CTkLabel(
            viewer_header,
            text="(0 items)",
            font=("Segoe UI", 12),
            text_color="gray"
        )
        self.profile_viewer_count_label.pack(side="left", padx=10)

        # Result filter (F3) — All / Pass / Check / Fail
        self.viewer_filter_segmented = ctk.CTkSegmentedButton(
            viewer_header,
            values=["All", "Pass", "Check", "Fail"],
            command=self.set_viewer_filter,
            font=("Segoe UI", 11)
        )
        self.viewer_filter_segmented.set("All")
        self.viewer_filter_segmented.pack(side="left", padx=15)

        self.profile_viewer_label = ctk.CTkLabel(
            viewer_header,
            text="No profile selected",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        self.profile_viewer_label.pack(side="right")
        
        self.create_profile_viewer(viewer_container)
    
    def create_profile_viewer(self, parent):
        """Create profile viewer table with QC results"""
        from tkinter import ttk
        
        table_frame = ctk.CTkFrame(parent)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Treeview
        columns = ('module', 'part_type', 'part', 'item', 'type', 'spec', 'unit', 'result')
        
        self.profile_viewer_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            selectmode='browse',
            height=15
        )
        
        # Headers
        headers = {
            'module': 'Module', 'part_type': 'Part Type', 'part': 'Part',
            'item': 'Item', 'type': 'Type', 'spec': 'Specification',
            'unit': 'Unit', 'result': 'Result'
        }
        
        for col, header in headers.items():
            self.profile_viewer_tree.heading(col, text=header)
        
        # Column widths
        widths = {
            'module': 70, 'part_type': 80, 'part': 70, 'item': 180,
            'type': 60, 'spec': 120, 'unit': 60, 'result': 100
        }
        
        for col, width in widths.items():
            self.profile_viewer_tree.column(col, width=width, 
                                           anchor='center' if col != 'item' else 'w')
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.profile_viewer_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.profile_viewer_tree.xview)
        self.profile_viewer_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.profile_viewer_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Tags - LIGHT MODE OPTIMIZED
        self.profile_viewer_tree.tag_configure('pass', background='#e8f5e9', foreground='#1b5e20')  # Light green bg, dark green text
        self.profile_viewer_tree.tag_configure('fail', background='#ffebee', foreground='#c62828')  # Light red bg, dark red text
        self.profile_viewer_tree.tag_configure('check', background='#e3f2fd', foreground='#1976d2')  # Light blue bg, blue text
        self.profile_viewer_tree.tag_configure('pending', foreground='gray50')
        
        # Right-click context menu for DB_Key copy
        self.profile_viewer_menu = tk.Menu(self.root, tearoff=0)
        self.profile_viewer_menu.add_command(
            label="📋 Copy DB_Key",
            command=self._copy_db_key
        )
        self.profile_viewer_menu.add_command(
            label="📎 Append DB_Key (;)",
            command=self._append_db_key
        )
        self.profile_viewer_tree.bind("<Button-3>", self._show_profile_viewer_menu)
    
    def create_status_bar(self):
        """Create status bar at bottom with version and developer info"""
        status_bar = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        status_bar.pack(fill="x", side="bottom")
        
        # Left: Status message
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Ready",
            font=("Segoe UI", 11),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, pady=2)
        
        # Right: Developer info
        dev_info = ctk.CTkLabel(
            status_bar,
            text="Version 1.0  |  Developed by Levi.Beak  |  Contact: levi.beak@parksystems.com",
            font=("Segoe UI", 10),
            text_color="gray"
        )
        dev_info.pack(side="right", padx=10, pady=2)
        
        # Bind click to email (simple implementation)
        dev_info.bind("<Button-1>", lambda e: self.copy_email())
    
    def _get_db_key_from_selection(self):
        """Get DB_Key string from selected Profile Viewer row"""
        selection = self.profile_viewer_tree.selection()
        if not selection:
            return None
        
        item = self.profile_viewer_tree.item(selection[0])
        values = item['values']
        if len(values) >= 4:
            # Module.PartType.Part.Item
            return f"{values[0]}.{values[1]}.{values[2]}.{values[3]}"
        return None
    
    def _show_profile_viewer_menu(self, event):
        """Show right-click context menu on Profile Viewer"""
        item = self.profile_viewer_tree.identify_row(event.y)
        if item:
            self.profile_viewer_tree.selection_set(item)
            self.profile_viewer_menu.post(event.x_root, event.y_root)
    
    def _copy_db_key(self):
        """Copy DB_Key of selected row to clipboard"""
        db_key = self._get_db_key_from_selection()
        if db_key:
            self.root.clipboard_clear()
            self.root.clipboard_append(db_key)
            self.update_status(f"Copied: {db_key}")
    
    def _append_db_key(self):
        """Append DB_Key to clipboard with ; separator"""
        db_key = self._get_db_key_from_selection()
        if db_key:
            try:
                existing = self.root.clipboard_get()
                if existing and not existing.endswith(';'):
                    new_value = f"{existing};{db_key}"
                else:
                    new_value = db_key
            except tk.TclError:
                new_value = db_key
            
            self.root.clipboard_clear()
            self.root.clipboard_append(new_value)
            self.update_status(f"Appended: {db_key}")
    
    def copy_email(self):
        self.root.clipboard_clear()
        self.root.clipboard_append("levi.beak@parksystems.com")
        self.update_status("Email copied to clipboard!")
    
    def update_status(self, message):
        """Update status bar message"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
    
    def get_profile_list(self):
        """Get list of available profiles"""
        return list(self.spec_manager.equipment_profiles.keys())
    
    def open_db(self):
        """Open DB directory"""
        try:
            path = filedialog.askdirectory(title="Select DB Directory")
            if path:
                self.db_root = path
                self.update_status(f"Loading DB from: {path}")
                
                # Run in thread
                threading.Thread(target=self._load_db_thread, args=(path,), daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file dialog:\n{str(e)}")
            logger.error(f"Error in open_db: {e}", exc_info=True)
    
    def _load_db_thread(self, path):
        """Thread for loading DB"""
        try:
            from src.core.db_extractor import DBExtractor
            extractor = DBExtractor(path)
            self.db_data = extractor.build_hierarchy()
            
            # Update UI in main thread
            self.root.after(0, self._on_db_loaded)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load DB:\n{str(e)}"))
            self.root.after(0, lambda: self.update_status("Error loading DB"))
            logger.error(f"Error loading DB: {e}", exc_info=True)
    
    def _on_db_loaded(self):
        """Called when DB load finishes"""
        self.update_status("DB Loaded. Ready for QC.")
        self.run_qc_btn.configure(state="normal")
        self.display_db_tree()
        
        # Show confirmation
        messagebox.showinfo(
            "DB Loaded",
            "Database loaded successfully.\n\n"
            "The DB structure is shown on the left.\n"
            "Click 'Run QC' to perform inspection."
        )
    
    def display_db_tree(self):
        """Display DB structure in tree view"""
        if not self.db_data:
            return

        # Populate tree with DB data and QC report (if available)
        self.db_tree.populate(self.db_data, self.qc_report)

        # Enable search input now that tree has data (F1)
        if hasattr(self, "db_search_entry"):
            self.db_search_entry.configure(state="normal")
            # Re-apply existing search if any (e.g., after re-load)
            current_query = self.db_search_entry.get().strip()
            if current_query:
                self._do_db_search(immediate=True)
    
    def on_profile_changed(self, selected_profile):
        """Handle profile selection change"""
        self.current_profile = selected_profile
        self.update_status(f"Selected profile: {selected_profile}")
        
        # Load profile to viewer
        if selected_profile:
            self.load_profile_to_viewer(selected_profile)
    
    def run_qc_inspection(self, excluded_modules=None):
        """Run QC inspection with optional module exclusions"""
        if not self.db_data or not self.current_profile:
            return
        
        self.update_status("Running QC inspection...")
        
        try:
            # Load specs with inheritance
            specs = self.spec_manager.load_profile_with_inheritance(self.current_profile)
            
            if not specs:
                messagebox.showerror("Error", "Failed to load spec profile")
                return
            
            # Generate report (with exclusions if provided)
            self.qc_report = self.comparator.generate_report(
                self.db_data,
                specs,
                self.current_profile,
                excluded_modules=list(excluded_modules) if excluded_modules else None
            )
            
            # Check for N/A items — show review dialog on first run (no exclusions yet)
            if excluded_modules is None:
                missing_items = [
                    r for r in self.qc_report['results']
                    if r['status'] == 'FAIL' and r['actual_value'] == 'N/A'
                ]
                
                if missing_items:
                    self._show_na_review_dialog(missing_items)
                    return  # Wait for dialog result
            
            # Display results
            self.display_results()
            
            # Update profile viewer with results
            self.update_profile_viewer_with_results(self.qc_report)
            
            self.display_db_tree()  # Refresh tree with QC results
            self.export_btn.configure(state="normal")
            self.review_cl_btn.configure(state="normal")
            
            # Update status with pass rate
            pass_rate = self.qc_report['summary']['pass_rate']
            excluded_count = self.qc_report['summary'].get('excluded', 0)
            status_text = f"QC Complete - Pass Rate: {pass_rate}%"
            if excluded_count > 0:
                status_text += f" ({excluded_count} excluded)"
            self.update_status(status_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run QC:\n{str(e)}")
            self.update_status("Error running QC")
            logger.error(f"Error running QC: {e}", exc_info=True)
    
    def _show_na_review_dialog(self, missing_items):
        """Show N/A review dialog and handle result"""
        from src.ui.na_review_dialog import NaReviewDialog
        
        dialog = NaReviewDialog(
            self.root,
            missing_items,
            self.current_profile,
            self.spec_manager
        )
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        
        if dialog.confirmed:
            excluded = dialog.excluded_patterns
            
            # Save to profile if requested
            if dialog.save_to_profile and excluded:
                self._save_exclusions_to_profile(excluded)
            
            # Re-run QC with exclusions
            self.run_qc_inspection(excluded_modules=excluded)
        else:
            # User cancelled — show results without exclusion (all N/A as FAIL)
            self.display_results()
            self.update_profile_viewer_with_results(self.qc_report)
            self.display_db_tree()
            self.export_btn.configure(state="normal")
            
            pass_rate = self.qc_report['summary']['pass_rate']
            self.update_status(f"QC Complete - Pass Rate: {pass_rate}%")
    
    def _save_exclusions_to_profile(self, excluded_patterns):
        """Save exclusion patterns to profile JSON"""
        try:
            profile_name = self.current_profile
            if profile_name not in self.spec_manager.equipment_profiles:
                return
            
            profile = self.spec_manager.equipment_profiles[profile_name]
            existing = set(profile.get('excluded_items', []))
            
            # Add new patterns
            existing.update(excluded_patterns)
            profile['excluded_items'] = sorted(list(existing))
            
            # Save to file
            self.spec_manager.save_equipment_profile(profile_name)
            logger.info(f"Saved {len(excluded_patterns)} exclusion patterns to {profile_name}")
            
        except Exception as e:
            logger.error(f"Error saving exclusions: {e}", exc_info=True)
    
    def display_results(self):
        """Display QC results - COMPACT VERSION"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not self.qc_report:
            return
        
        summary = self.qc_report['summary']
        
        # Main Container - Use grid for better layout control
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)
        
        # === Left Column: Statistics ===
        stats_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        stats_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        # Total / Validated / Checked Only
        ctk.CTkLabel(stats_frame, text=f"Total Items: {summary['total_items']}", 
                    font=("Segoe UI", 14)).pack(anchor="w")
        ctk.CTkLabel(stats_frame, text=f"Validated: {summary.get('validated', summary.get('checked', 0))}", 
                    font=("Segoe UI", 14)).pack(anchor="w")
        checked_only = summary.get('checked_only', 0)
        if checked_only > 0:
            ctk.CTkLabel(stats_frame, text=f"Checked Only: {checked_only}", 
                        font=("Segoe UI", 14), text_color="#1f6aa5").pack(anchor="w")
        
        # Pass Rate Bar
        pass_rate = summary['pass_rate']
        rate_color = "#0d7d3d" if pass_rate == 100 else ("#ff9800" if pass_rate >= 80 else "#c62828")
        
        ctk.CTkLabel(stats_frame, text=f"Pass Rate: {pass_rate:.1f}%", 
                    font=("Segoe UI", 18, "bold"), text_color=rate_color).pack(anchor="w", pady=(10, 2))
        
        progress = ctk.CTkProgressBar(stats_frame, width=200, height=10, progress_color=rate_color)
        progress.pack(anchor="w")
        progress.set(pass_rate / 100.0)
        
        # === Right Column: Detailed Counts ===
        counts_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        counts_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)
        
        # Passed
        passed = summary['passed']
        ctk.CTkLabel(counts_frame, text=f"PASSED: {passed}", 
                    font=("Segoe UI", 16, "bold"), text_color="#0d7d3d").pack(anchor="e")
        
        # Failed
        failed = summary['failed']
        failed_color = "#c62828" if failed > 0 else "gray50"
        ctk.CTkLabel(counts_frame, text=f"FAILED: {failed}", 
                    font=("Segoe UI", 16, "bold"), text_color=failed_color).pack(anchor="e")
        
        # Checked (if any)
        if checked_only > 0:
            ctk.CTkLabel(counts_frame, text=f"CHECKED: {checked_only}", 
                        font=("Segoe UI", 14), text_color="#1f6aa5").pack(anchor="e")
        
        # Others
        excluded_count = summary.get('excluded', 0)
        if excluded_count > 0:
            ctk.CTkLabel(counts_frame, text=f"EXCLUDED: {excluded_count}", 
                        font=("Segoe UI", 14), text_color="#888888").pack(anchor="e")
        ctk.CTkLabel(counts_frame, text=f"No Spec: {summary['no_spec']}", 
                    font=("Segoe UI", 13), text_color="gray").pack(anchor="e")
        ctk.CTkLabel(counts_frame, text=f"Errors: {summary['errors']}", 
                    font=("Segoe UI", 13), text_color="gray").pack(anchor="e")
        
        # === Bottom: Failed Items List (Compact) ===
        if failed > 0:
            ctk.CTkFrame(self.results_frame, height=1, fg_color="gray40").grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
            
            failed_container = ctk.CTkFrame(self.results_frame, fg_color="transparent")
            failed_container.grid(row=2, column=0, columnspan=2, sticky="nsew")
            
            ctk.CTkLabel(failed_container, text="Failed Items:", 
                        font=("Segoe UI", 14, "bold"), text_color="#c62828").pack(anchor="w")
            
            failed_items = [r for r in self.qc_report['results'] if r['status'] == 'FAIL']
            for i, item in enumerate(failed_items[:8]):  # Show max 8 items
                item_text = f"• {item['module']}.{item['part_name']}.{item['item_name']}"
                ctk.CTkLabel(failed_container, text=item_text, font=("Segoe UI", 13),
                            text_color="#ff6b6b", anchor="w").pack(anchor="w", padx=10)
            
            if len(failed_items) > 8:
                ctk.CTkLabel(failed_container, text=f"... +{len(failed_items) - 8} more",
                            font=("Segoe UI", 12, "italic"), text_color="gray").pack(anchor="w", padx=10)
    
    def export_report(self):
        """Export QC report to Excel file"""
        if not self.qc_report:
            return
        
        try:
            from src.utils.report_generator import ExcelReportGenerator
            from datetime import datetime
            
            # Generate timestamp safely
            timestamp = self.qc_report.get('summary', {}).get('timestamp', datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
            # Replace invalid filename characters
            timestamp_clean = timestamp.replace(':', '-').replace(' ', '_')
            
            # Default filename
            default_name = f"QC_Report_{self.current_profile}_{timestamp_clean}.xlsx"
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=default_name,
                title="Export QC Report"
            )
            
            if filepath:
                generator = ExcelReportGenerator()
                success = generator.generate_report(self.qc_report, filepath)
                
                if success:
                    messagebox.showinfo("Export Success", f"Report exported to:\n{filepath}")
                    self.update_status(f"Report exported: {Path(filepath).name}")
                else:
                    messagebox.showerror("Export Error", f"Failed to save report.\nPlease check if the file is already open in Excel.\n\nPath: {filepath}")
                    self.update_status("Export failed")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")
            logger.error(f"Export error: {e}", exc_info=True)
    
    def review_checklist(self):
        """Review Checklist Excel against QC results"""
        if not self.qc_report:
            messagebox.showwarning("Warning", "Please run QC inspection first.")
            return
        
        # Select checklist Excel file
        excel_path = filedialog.askopenfilename(
            title="Select Checklist Excel File",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if not excel_path:
            return
        
        try:
            from src.core.checklist_validator import ChecklistValidator
            from src.ui.checklist_report_dialog import ChecklistReportDialog
            
            # Run validation (reads DB_Key column from Excel directly)
            validator = ChecklistValidator()
            results = validator.validate(excel_path, self.qc_report)
            
            if not results:
                messagebox.showinfo(
                    "No Results",
                    "No DB_Key mappings found in the Checklist Excel.\n\n"
                    "Add a 'DB_Key' column header and paste DB keys for items to validate.\n"
                    "Use 'Export DB Keys' in the report dialog to get available keys."
                )
                return
            
            # Show report dialog (pass qc_report for Export DB Keys)
            profile_name = self.current_profile or ''
            dialog = ChecklistReportDialog(
                self.root, results, excel_path, profile_name, self.qc_report
            )
            self.root.wait_window(dialog)
            
            self.update_status(f"Checklist review complete: {Path(excel_path).name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Checklist review failed:\n{str(e)}")
            logger.error(f"Checklist review error: {e}", exc_info=True)
    
    def open_admin_window(self):
        """Open the unified Admin Window (password-protected)."""
        from src.ui.admin_window import AdminWindow, prompt_admin_password

        if not prompt_admin_password(self.root):
            return

        admin = AdminWindow(
            self.root,
            sync_manager=self.sync_manager,
            sync_mode=self.sync_mode,
            on_settings_saved=self._on_server_settings_saved,
            on_spec_changed=self._on_admin_spec_changed,
        )
        self.root.wait_window(admin)

        # Refresh after admin window closes
        if self.current_profile:
            self.load_profile_to_viewer(self.current_profile)
        self.update_profile_list()
    
    def update_profile_list(self):
        """Update profile combo box"""
        if hasattr(self, 'profile_combo'):
            profiles = self.get_profile_list()
            self.profile_combo.configure(values=profiles)
            
            # Keep current selection if still exists
            if self.current_profile and self.current_profile in profiles:
                self.profile_combo.set(self.current_profile)
            elif profiles:
                self.profile_combo.set(profiles[0])
                self.current_profile = profiles[0]
                
            self.update_status("Profiles updated")

    def load_profile_to_viewer(self, profile_name):
        """Load profile to viewer (resets viewer filter to All)."""
        for item in self.profile_viewer_tree.get_children():
            self.profile_viewer_tree.delete(item)

        # Reset filter state on profile change (F3)
        self.viewer_filter = "ALL"
        if hasattr(self, "viewer_filter_segmented"):
            self.viewer_filter_segmented.set("All")
        self._all_viewer_rows = []
        self._viewer_counts = {"ALL": 0, "PASS": 0, "CHECK": 0, "FAIL": 0, "PENDING": 0}

        self.profile_viewer_label.configure(text=f"Profile: {profile_name}")
        specs = self.spec_manager.load_profile_with_inheritance(profile_name)

        if not specs:
            self.profile_viewer_count_label.configure(text="(0 items)")
            return

        for module, module_data in specs.items():
            for part_type, type_data in module_data.items():
                for part_name, items in type_data.items():
                    for spec in items:
                        # Skip disabled items
                        if not spec.get('enabled', True):
                            continue

                        item_name = spec.get('item_name', '')
                        val_type = spec.get('validation_type', '').upper()

                        if val_type == 'RANGE':
                            spec_str = f"[{spec.get('min_spec', '')}, {spec.get('max_spec', '')}]"
                        else:
                            spec_str = f"= {spec.get('expected_value', '')}"

                        unit = spec.get('unit', '')

                        values = (module, part_type, part_name, item_name,
                                  val_type, spec_str, unit, '-')
                        tag = 'pending'
                        self.profile_viewer_tree.insert('', 'end',
                                                        values=values, tags=(tag,))
                        self._all_viewer_rows.append((values, tag))

        self._recount_viewer()
        self._update_viewer_count_label()

    def update_profile_viewer_with_results(self, qc_report):
        """Update viewer with QC results, then refresh cache + apply current filter (F3)."""
        results_map = {}
        for result in qc_report.get('results', []):
            key = (result['module'], result['part_type'], result['part_name'], result['item_name'])
            results_map[key] = result

        # Update each row in-place AND rebuild cache for filter
        new_rows = []
        for item_id in self.profile_viewer_tree.get_children():
            values = list(self.profile_viewer_tree.item(item_id)['values'])
            key = (values[0], values[1], values[2], values[3])
            tag = 'pending'

            if key in results_map:
                result = results_map[key]
                status, actual = result['status'], result.get('actual_value', '-')

                if status == 'PASS':
                    result_text, tag = f"{actual}", 'pass'
                elif status == 'FAIL':
                    result_text, tag = f"{actual} FAIL", 'fail'
                elif status == 'CHECK':
                    result_text, tag = f"{actual} ✓", 'check'
                else:
                    result_text, tag = actual, 'pending'

                values[7] = result_text
                self.profile_viewer_tree.item(item_id, values=values, tags=(tag,))

            new_rows.append((tuple(values), tag))

        self._all_viewer_rows = new_rows
        self._recount_viewer()
        self._apply_viewer_filter()

    # ------------------------------------------------------------------
    # Viewer filter (F3) helpers
    # ------------------------------------------------------------------

    def _recount_viewer(self):
        """Recompute per-status counts from cached rows."""
        counts = {"ALL": len(self._all_viewer_rows),
                  "PASS": 0, "CHECK": 0, "FAIL": 0, "PENDING": 0}
        for _, tag in self._all_viewer_rows:
            key = tag.upper() if tag else "PENDING"
            if key in counts:
                counts[key] += 1
        self._viewer_counts = counts

    def _update_viewer_count_label(self):
        """Update count label according to active filter."""
        total = self._viewer_counts.get("ALL", 0)
        if self.viewer_filter == "ALL":
            self.profile_viewer_count_label.configure(
                text=f"({total} items)", text_color="gray")
        else:
            shown = self._viewer_counts.get(self.viewer_filter, 0)
            color = {
                "PASS": "#2e7d32",
                "CHECK": "#1976d2",
                "FAIL": "#c62828",
            }.get(self.viewer_filter, "gray")
            self.profile_viewer_count_label.configure(
                text=f"({shown} of {total} items, {self.viewer_filter})",
                text_color=color)

    def set_viewer_filter(self, value: str):
        """Callback for SegmentedButton — apply filter."""
        self.viewer_filter = value.upper()
        # Guidance for QC-not-yet-run case
        if (self.viewer_filter != "ALL"
                and self._viewer_counts.get("PENDING", 0) == self._viewer_counts.get("ALL", 0)
                and self._viewer_counts.get("ALL", 0) > 0):
            self.update_status("QC를 먼저 실행하세요.")
        self._apply_viewer_filter()

    def _apply_viewer_filter(self):
        """Re-render profile viewer rows according to active filter."""
        # Save current selection (DB_Key) to attempt to preserve
        sel_key = None
        sel = self.profile_viewer_tree.selection()
        if sel:
            try:
                v = self.profile_viewer_tree.item(sel[0])['values']
                sel_key = (v[0], v[1], v[2], v[3])
            except Exception:
                sel_key = None

        # Clear & re-insert
        for item in self.profile_viewer_tree.get_children():
            self.profile_viewer_tree.delete(item)

        target_tag = self.viewer_filter.lower() if self.viewer_filter != "ALL" else None
        new_sel_iid = None
        for values, tag in self._all_viewer_rows:
            if target_tag is not None and tag != target_tag:
                continue
            iid = self.profile_viewer_tree.insert('', 'end', values=values, tags=(tag,))
            if sel_key and (values[0], values[1], values[2], values[3]) == sel_key:
                new_sel_iid = iid

        if new_sel_iid:
            self.profile_viewer_tree.selection_set(new_sel_iid)
            self.profile_viewer_tree.see(new_sel_iid)

        self._update_viewer_count_label()
    
    def expand_all_tree(self):
        """Expand all tree items"""
        if hasattr(self.db_tree, 'expand_all'):
            self.db_tree.expand_all()

    def collapse_all_tree(self):
        """Collapse all tree items"""
        if hasattr(self.db_tree, 'collapse_all'):
            self.db_tree.collapse_all()

    # ------------------------------------------------------------------
    # DB Tree search (F1)
    # ------------------------------------------------------------------

    def _on_db_search_key(self, event):
        """Debounced search on KeyRelease (250ms)."""
        # Cancel pending callback
        if self._db_search_after_id is not None:
            try:
                self.root.after_cancel(self._db_search_after_id)
            except Exception:
                pass
        self._db_search_after_id = self.root.after(250, self._do_db_search)

    def _do_db_search(self, immediate: bool = False):
        """Run search against DBTreeView and update count label."""
        self._db_search_after_id = None
        if not hasattr(self, "db_tree") or not self.db_tree.has_data():
            return

        query = self.db_search_entry.get().strip()
        match_count = self.db_tree.search(query)

        if not query:
            self.db_search_count_label.configure(text="", text_color="gray60")
        elif match_count == 0:
            self.db_search_count_label.configure(text="0 matches", text_color="#ed6c02")
        else:
            self.db_search_count_label.configure(
                text=f"{match_count} matches", text_color="#0d7d3d")

    def _clear_db_search(self):
        """Clear the search box and restore tree state."""
        self.db_search_entry.delete(0, "end")
        self._do_db_search(immediate=True)

    def toggle_theme(self):
        """Toggle between dark and light mode"""
        current_mode = ctk.get_appearance_mode()
        new_mode = "light" if current_mode == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
    
    def _on_admin_spec_changed(self):
        """Called when server-side specs are mutated via Admin window."""
        # Trigger re-sync so local cache stays fresh
        if self.sync_mode == "online":
            self._initial_sync()

    def _on_server_settings_saved(self, new_mode: str):
        """Handle server settings saved"""
        self.sync_mode = new_mode

        # Update sync indicator
        if hasattr(self, 'sync_indicator'):
            sync_text = "● Online" if new_mode == "online" else "● Offline"
            sync_color = "#0d7d3d" if new_mode == "online" else "gray50"
            self.sync_indicator.configure(text=sync_text, text_color=sync_color)

        # If switched to online, attempt sync and reload
        if new_mode == "online":
            self._initial_sync()
            self._reload_specs()
            self._update_sync_status()

    def _reload_specs(self):
        """Reload spec config from current mode's config dir"""
        config_dir = get_config_dir(mode=self.sync_mode)
        common_base = config_dir / "common_base.json"
        profiles_dir = config_dir / "profiles"

        if common_base.exists() and profiles_dir.exists():
            self.spec_manager = SpecManager()
            self.spec_manager.load_multi_file_config(config_dir)
            logger.info(f"Reloaded specs from {config_dir}")

            # Refresh profile combo
            if hasattr(self, 'profile_combo'):
                self.profile_combo.configure(values=self.get_profile_list())

    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Entry point"""
    app = MainWindow()
    app.run()
