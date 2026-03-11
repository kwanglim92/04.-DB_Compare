"""
Profile Manager Window
GUI for managing QC profiles - create, edit, delete, view
Dual-view mode: Flat Table ↔️ Grouped Tree
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
from typing import Dict, Optional
import logging

from src.core.db_extractor import DBExtractor
from src.ui.spec_dialog import SpecConfigDialog
from src.utils.format_helpers import format_spec, center_window_on_parent
from src.constants import COLORS

logger = logging.getLogger(__name__)


class ProfileManagerWindow(ctk.CTkToplevel):
    """
    Profile Manager - Create, Edit, Delete QC Profiles
    Features dual-view mode with table/tree toggle
    """
    
    def __init__(self, parent, spec_manager):
        super().__init__(parent)
        
        self.title("Profile Manager")
        self.geometry("1000x650")
        self.spec_manager = spec_manager
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Data
        self.current_profile = None
        self.profiles_modified = False
        self.view_mode = 'table'  # 'table' or 'tree'
        self.all_specs_data = []  # For search filtering
        
        # Create UI
        self.create_widgets()
        self.load_profiles()
        
        # Center on parent
        self.center_on_parent(parent)
        
    def center_on_parent(self, parent):
        """Center window on parent"""
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (1000 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (650 // 2)
        self.geometry(f"+{x}+{y}")
        
    def create_widgets(self):
        """Create UI widgets"""
        # Header
        header = ctk.CTkLabel(
            self,
            text="📋 QC Profile Manager",
            font=("Segoe UI", 18, "bold")
        )
        header.pack(pady=15)
        
        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Left panel - Profile list (reduced width for more space on right)
        left_panel = ctk.CTkFrame(main_container, width=180)
        left_panel.pack(side="left", fill="both", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        ctk.CTkLabel(
            left_panel,
            text="Profiles",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)
        
        # Profile listbox
        import tkinter as tk
        self.profile_listbox = tk.Listbox(
            left_panel,
            font=("Segoe UI", 11),
            selectmode="single",
            bg="#2b2b2b",
            fg="white",
            selectbackground="#1f6aa5",
            selectforeground="white",
            borderwidth=0,
            highlightthickness=0
        )
        self.profile_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.profile_listbox.bind('<<ListboxSelect>>', self.on_profile_select)
        self.profile_listbox.bind('<Button-3>', self.show_profile_context_menu)
        
        # Profile Context Menu
        self.profile_context_menu = tk.Menu(self, tearoff=0)
        self.profile_context_menu.add_command(label="Rename Profile", command=self.rename_profile)
        self.profile_context_menu.add_command(label="Delete Profile", command=self.delete_profile)
        
        # Buttons
        btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="New",
            command=self.new_profile,
            fg_color="#2fa572",
            hover_color="#248f5f",
            height=32
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            btn_frame,
            text="Edit",
            command=self.edit_profile,
            fg_color="#ed6c02",
            hover_color="#c75c02",
            height=32
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            btn_frame,
            text="Delete",
            command=self.delete_profile,
            fg_color="#d32f2f",
            hover_color="#b71c1c",
            height=32
        ).pack(fill="x", pady=2)
        
        # Separator
        sep_frame = ctk.CTkFrame(btn_frame, height=2, fg_color="gray30")
        sep_frame.pack(fill="x", pady=10)
        
        # Export/Import buttons
        ctk.CTkButton(
            btn_frame,
            text="📤 Export",
            command=self.export_profile,
            fg_color="#2196f3",
            hover_color="#1976d2",
            height=32
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            btn_frame,
            text="📥 Import",
            command=self.import_profile,
            fg_color="#4caf50",
            hover_color="#388e3c",
            height=32
        ).pack(fill="x", pady=2)
        
        # Right panel - Spec items
        right_panel = ctk.CTkFrame(main_container)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Header with controls
        header_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Title with item count
        self.spec_title_label = ctk.CTkLabel(
            header_frame,
            text="Spec Items",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        self.spec_title_label.pack(side="left")
        
        # View mode toggle
        self.view_toggle = ctk.CTkSwitch(
            header_frame,
            text="🌲 Group View",
            command=self.toggle_view_mode,
            font=("Segoe UI", 11)
        )
        self.view_toggle.pack(side="right", padx=10)
        
        # Search box
        self.search_entry = ctk.CTkEntry(
            header_frame,
            placeholder_text="🔍 Search items...",
            width=200,
            font=("Segoe UI", 11)
        )
        self.search_entry.pack(side="right", padx=5)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        # Create treeview for specs
        tree_frame = ctk.CTkFrame(right_panel)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Configure treeview columns based on initial mode
        self.spec_tree = ttk.Treeview(
            tree_frame,
            columns=('module', 'part_type', 'part', 'item', 'type', 'spec', 'unit'),
            show='headings',  # Start with table mode
            selectmode='browse'
        )
        
        # Table mode headers
        self.spec_tree.heading('module', text='Module')
        self.spec_tree.heading('part_type', text='Part Type')
        self.spec_tree.heading('part', text='Part')
        self.spec_tree.heading('item', text='Item')
        self.spec_tree.heading('type', text='Type')
        self.spec_tree.heading('spec', text='Specification')
        self.spec_tree.heading('unit', text='Unit')
        
        # Table mode columns
        self.spec_tree.column('module', width=80, anchor='w')
        self.spec_tree.column('part_type', width=90, anchor='w')
        self.spec_tree.column('part', width=80, anchor='w')
        self.spec_tree.column('item', width=180, anchor='w')
        self.spec_tree.column('type', width=60, anchor='center')
        self.spec_tree.column('spec', width=150, anchor='center')
        self.spec_tree.column('unit', width=60, anchor='center')
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.spec_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.spec_tree.xview)
        self.spec_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.spec_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Tags for tree mode
        self.spec_tree.tag_configure('module', font=('Segoe UI', 11, 'bold'), foreground='#1f6aa5')
        self.spec_tree.tag_configure('part_type', font=('Segoe UI', 10, 'bold'), foreground='#424242')
        self.spec_tree.tag_configure('part', font=('Segoe UI', 10), foreground='#666666')
        self.spec_tree.tag_configure('item', font=('Segoe UI', 10))
        
        # Tag for search highlighting
        self.spec_tree.tag_configure('search_match', font=('Segoe UI', 10, 'bold'), foreground='#ff9800')
        
        # Bind double-click for quick edit
        self.spec_tree.bind('<Double-Button-1>', self.on_item_double_click)
        self.spec_tree.bind('<Button-3>', self.show_spec_context_menu)
        
        # Spec Context Menu
        self.spec_context_menu = tk.Menu(self, tearoff=0)
        self.spec_context_menu.add_command(label="Delete Item", command=self.delete_spec_item)
        
        # Bottom buttons
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            bottom_frame,
            text="Close",
            command=self.on_close,
            width=100
        ).pack(side="right")
        
    def load_profiles(self):
        """Load all profiles into listbox"""
        self.profile_listbox.delete(0, "end")
        
        # Add Common Base as special entry
        self.profile_listbox.insert("end", "★ Common Base")
        
        profiles = self.spec_manager.get_all_profile_names()
        for profile in profiles:
            self.profile_listbox.insert("end", profile)
            
    def on_profile_select(self, event):
        """Handle profile selection"""
        selection = self.profile_listbox.curselection()
        if not selection:
            return
            
        profile_name = self.profile_listbox.get(selection[0])
        self.search_entry.delete(0, 'end')  # Clear search
        
        if profile_name == "★ Common Base":
            self.current_profile = "__COMMON_BASE__"
            self.display_common_base_specs()
        else:
            self.current_profile = profile_name
            self.display_profile_specs(profile_name)
    
    def toggle_view_mode(self):
        """Toggle between table and tree view"""
        if self.view_mode == 'table':
            self.view_mode = 'tree'
            self.view_toggle.configure(text="📋 Table View")
            self.reconfigure_treeview_for_tree()
        else:
            self.view_mode = 'table'
            self.view_toggle.configure(text="🌲 Group View")
            self.reconfigure_treeview_for_table()
        
        # Refresh display
        if self.current_profile == '__COMMON_BASE__':
            self.display_common_base_specs()
        elif self.current_profile:
            self.display_profile_specs(self.current_profile)
    
    def reconfigure_treeview_for_table(self):
        """Reconfigure treeview for table mode (7 columns)"""
        # Set columns
        self.spec_tree['columns'] = ('module', 'part_type', 'part', 'item', 'type', 'spec', 'unit')
        
        # Configure headings
        self.spec_tree.heading('module', text='Module')
        self.spec_tree.heading('part_type', text='Part Type')
        self.spec_tree.heading('part', text='Part')
        self.spec_tree.heading('item', text='Item')
        self.spec_tree.heading('type', text='Type')
        self.spec_tree.heading('spec', text='Specification')
        self.spec_tree.heading('unit', text='Unit')
        
        # Configure columns
        self.spec_tree.column('module', width=70, anchor='w')
        self.spec_tree.column('part_type', width=80, anchor='w')
        self.spec_tree.column('part', width=70, anchor='w')
        self.spec_tree.column('item', width=180, anchor='w')
        self.spec_tree.column('type', width=60, anchor='center')
        self.spec_tree.column('spec', width=120, anchor='center')
        self.spec_tree.column('unit', width=80, anchor='center')  # Increased from 60
        
        # Hide tree column
        self.spec_tree.configure(show='headings')
    
    def reconfigure_treeview_for_tree(self):
        """Reconfigure treeview for tree mode (3 columns only)"""
        # Set columns (only 3 for tree mode)
        self.spec_tree['columns'] = ('type', 'spec', 'unit')
        
        # Configure tree column (#0)
        self.spec_tree.heading('#0', text='Item Path')
        self.spec_tree.column('#0', width=400, stretch=True)  # Auto-expand
        
        # Configure value columns
        self.spec_tree.heading('type', text='Type')
        self.spec_tree.heading('spec', text='Specification')
        self.spec_tree.heading('unit', text='Unit')
        
        self.spec_tree.column('type', width=70, anchor='center', stretch=False)
        self.spec_tree.column('spec', width=150, anchor='center', stretch=False)
        self.spec_tree.column('unit', width=100, anchor='center', stretch=False)  # Increased from 80
        
        # Show tree column
        self.spec_tree.configure(show='tree headings')
    
    def display_common_base_specs(self):
        """Display Common_Base specs"""
        # Clear tree
        for item in self.spec_tree.get_children():
            self.spec_tree.delete(item)
        
        specs = self.spec_manager.get_common_base_specs()
        
        if not specs:
            self.spec_title_label.configure(text="★ Common Base (0 items)")
            return
        
        # Build all_specs_data for reuse with table/tree views
        self.all_specs_data = []
        for module, module_data in specs.items():
            for part_type, type_data in module_data.items():
                for part_name, items in type_data.items():
                    for spec in items:
                        if not spec.get('enabled', True):
                            continue
                        self.all_specs_data.append({
                            'module': module,
                            'part_type': part_type,
                            'part': part_name,
                            'item': spec.get('item_name', ''),
                            'type': spec.get('validation_type', '').upper(),
                            'spec': self.format_spec(spec),
                            'unit': spec.get('unit', ''),
                            'raw_spec': spec
                        })
        
        total_items = len(self.all_specs_data)
        self.spec_title_label.configure(text=f"★ Common Base ({total_items} items)")
        
        # Display based on view mode
        if self.view_mode == 'table':
            self.display_as_table(specs)
        else:
            self.display_as_tree(specs)
    
    def display_profile_specs(self, profile_name: str):
        """Display specs for selected profile"""
        # Clear tree
        for item in self.spec_tree.get_children():
            self.spec_tree.delete(item)
            
        # Load profile with inheritance
        specs = self.spec_manager.load_profile_with_inheritance(profile_name)
        
        if not specs:
            self.spec_title_label.configure(text="Spec Items (0 items)")
            return
        
        # Store all specs for searching
        self.all_specs_data = []
        for module, module_data in specs.items():
            for part_type, type_data in module_data.items():
                for part_name, items in type_data.items():
                    for spec in items:
                        self.all_specs_data.append({
                            'module': module,
                            'part_type': part_type,
                            'part': part_name,
                            'item': spec.get('item_name', ''),
                            'type': spec.get('validation_type', '').upper(),
                            'spec': self.format_spec(spec),
                            'unit': spec.get('unit', ''),
                            'raw_spec': spec
                        })
                        
        # Filter out disabled items
        self.all_specs_data = [
            item for item in self.all_specs_data 
            if item['raw_spec'].get('enabled', True)
        ]
        
        # Update title with count
        total_items = len(self.all_specs_data)
        self.spec_title_label.configure(text=f"Spec Items ({total_items} items)")
        
        # Display based on view mode
        if self.view_mode == 'table':
            self.display_as_table(specs)
        else:
            self.display_as_tree(specs)
    
    def display_as_table(self, specs: Dict):
        """Display specs as flat table"""
        # Configure treeview for table mode
        self.spec_tree.configure(show='headings')
        
        # Insert all items at root level
        for spec_data in self.all_specs_data:
            self.spec_tree.insert(
                '',
                'end',
                values=(
                    spec_data['module'],
                    spec_data['part_type'],
                    spec_data['part'],
                    spec_data['item'],
                    spec_data['type'],
                    spec_data['spec'],
                    spec_data['unit']
                )
            )
    
    def display_as_tree(self, specs: Dict, search_text: str = ''):
        """Display specs as grouped tree (3 columns only)"""
        # Build hierarchical structure
        for module, module_data in specs.items():
            # Count total items in module (excluding disabled)
            module_count = sum(
                len([item for item in items if item.get('enabled', True)])
                for type_data in module_data.values() 
                for items in type_data.values()
            )
            
            module_id = self.spec_tree.insert(
                '',
                'end',
                text=f"📁 {module} ({module_count} items)",
                values=('', '', ''),  # Only 3 values for tree mode
                tags=('module',),
                open=True
            )
            
            for part_type, type_data in module_data.items():
                # Count items in part type (excluding disabled)
                type_count = sum(
                    len([item for item in items if item.get('enabled', True)])
                    for items in type_data.values()
                )
                
                type_id = self.spec_tree.insert(
                    module_id,
                    'end',
                    text=f"  📂 {part_type} ({type_count} items)",
                    values=('', '', ''),  # Only 3 values
                    tags=('part_type',),
                    open=True
                )
                
                for part_name, items in type_data.items():
                    part_id = self.spec_tree.insert(
                        type_id,
                        'end',
                        text=f"    📄 {part_name}",
                        values=('', '', ''),  # Only 3 values
                        tags=('part',),
                        open=True
                    )
                    
                    for spec in items:
                        # Skip disabled items
                        if not spec.get('enabled', True):
                            continue
                        item_name = spec.get('item_name', '')
                        val_type = spec.get('validation_type', '').upper()
                        spec_str = self.format_spec(spec)
                        unit = spec.get('unit', '')
                        
                        # Check if this item matches search
                        is_match = (search_text and 
                                   (search_text in item_name.lower() or
                                    search_text in module.lower() or
                                    search_text in part_type.lower() or
                                    search_text in part_name.lower()))
                        
                        tags = ('search_match',) if is_match else ('item',)
                        
                        self.spec_tree.insert(
                            part_id,
                            'end',
                            text=f"      • {item_name}",
                            values=(val_type, spec_str, unit),  # Only 3 values!
                            tags=tags
                        )
    
    def format_spec(self, spec: Dict) -> str:
        """Format specification for display"""
        val_type = spec.get('validation_type', '').lower()
        
        if val_type == 'range':
            min_val = spec.get('min_spec', '?')
            max_val = spec.get('max_spec', '?')
            return f"[{min_val}, {max_val}]"
        elif val_type == 'exact':
            expected = spec.get('expected_value', '?')
            return f"= {expected}"
        else:
            return "?"
    
    def on_search(self, event=None):
        """Handle search input"""
        search_text = self.search_entry.get().lower()
        
        # Clear current display
        for item in self.spec_tree.get_children():
            self.spec_tree.delete(item)
        
        if not self.current_profile:
            return
        
        # Filter specs
        if search_text:
            filtered_specs = [
                spec for spec in self.all_specs_data
                if (search_text in spec['module'].lower() or
                    search_text in spec['part_type'].lower() or
                    search_text in spec['part'].lower() or
                    search_text in spec['item'].lower())
            ]
        else:
            filtered_specs = self.all_specs_data
        
        # Update count
        self.spec_title_label.configure(
            text=f"Spec Items ({len(filtered_specs)} of {len(self.all_specs_data)} items)"
        )
        
        # Display filtered results
        if self.view_mode == 'table':
            # Flat table display
            for spec_data in filtered_specs:
                # Highlight matched items
                tags = ('search_match',) if search_text else ()
                
                self.spec_tree.insert(
                    '',
                    'end',
                    values=(
                        spec_data['module'],
                        spec_data['part_type'],
                        spec_data['part'],
                        spec_data['item'],
                        spec_data['type'],
                        spec_data['spec'],
                        spec_data['unit']
                    ),
                    tags=tags
                )
        else:
            # Tree display - rebuild hierarchy with filtered items
            filtered_hierarchy = {}
            for spec_data in filtered_specs:
                module = spec_data['module']
                part_type = spec_data['part_type']
                part = spec_data['part']
                
                if module not in filtered_hierarchy:
                    filtered_hierarchy[module] = {}
                if part_type not in filtered_hierarchy[module]:
                    filtered_hierarchy[module][part_type] = {}
                if part not in filtered_hierarchy[module][part_type]:
                    filtered_hierarchy[module][part_type][part] = []
                
                filtered_hierarchy[module][part_type][part].append(spec_data['raw_spec'])
            
            # Display filtered hierarchy with search highlighting
            self.display_as_tree(filtered_hierarchy, search_text)
    
    def new_profile(self):
        """Create new profile"""
        # Ask for DB path
        db_path = filedialog.askdirectory(title="Select DB for New Profile")
        if not db_path:
            return
            
        # Ask for profile name
        from tkinter import simpledialog
        profile_name = simpledialog.askstring("New Profile", "Enter new profile name:")
        if not profile_name or not profile_name.strip():
            return
            
        profile_name = profile_name.strip()
        
        # Check if already exists
        if profile_name in self.spec_manager.equipment_profiles:
            messagebox.showerror("Error", f"Profile '{profile_name}' already exists")
            return
            
        # Open profile editor
        self.open_profile_editor(profile_name, db_path, is_new=True)
        
    def edit_profile(self):
        """Edit selected profile — open directly without DB selection"""
        if not self.current_profile:
            messagebox.showwarning("Warning", "Please select a profile to edit")
            return
        
        if self.current_profile == '__COMMON_BASE__':
            # Common Base requires additional password
            password = simpledialog.askstring(
                "Security",
                "Common Base 편집은 관리자 비밀번호가 필요합니다.\nEnter administrator password:",
                show='*',
                parent=self
            )
            if password is None:
                return
            if password != "pqclevi":
                messagebox.showerror("Access Denied", "Incorrect password.")
                return
            
            # Open profile editor for Common Base
            self.open_profile_editor("Common_Base", db_path=None, is_new=False, is_common_base=True)
            return
        
        # Open profile editor directly (no DB required for editing existing items)
        self.open_profile_editor(self.current_profile, db_path=None, is_new=False)
        
    def open_profile_editor(self, profile_name: str, db_path: str, is_new: bool, is_common_base: bool = False):
        """Open profile editor window"""
        from src.ui.profile_editor import ProfileEditorWindow
        
        editor = ProfileEditorWindow(self, profile_name, db_path, self.spec_manager, is_new, is_common_base=is_common_base)
        self.wait_window(editor)
        
        # Reload if modified
        if editor.profile_saved:
            self.profiles_modified = True
            self.load_profiles()
            
            if is_common_base:
                # Re-select Common Base
                self.profile_listbox.selection_clear(0, "end")
                self.profile_listbox.selection_set(0)
                self.current_profile = "__COMMON_BASE__"
                self.display_common_base_specs()
                return
            
            # Select the new/edited profile
            for i in range(self.profile_listbox.size()):
                if self.profile_listbox.get(i) == profile_name:
                    self.profile_listbox.selection_clear(0, "end")
                    self.profile_listbox.selection_set(i)
                    self.profile_listbox.see(i)
                    self.display_profile_specs(profile_name)
                    break
    
    def delete_profile(self):
        """Delete selected profile"""
        if not self.current_profile:
            messagebox.showwarning("Warning", "Please select a profile to delete")
            return
            
        # Confirm
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete profile '{self.current_profile}'?"
        )
        
        if not confirm:
            return
            
        try:
            # Delete from spec manager
            del self.spec_manager.equipment_profiles[self.current_profile]
            # Delete profile JSON file
            if self.spec_manager.config_dir:
                profile_file = self.spec_manager.config_dir / "profiles" / f"{self.current_profile}.json"
                if profile_file.exists():
                    profile_file.unlink()
            
            messagebox.showinfo("Success", f"Profile '{self.current_profile}' deleted")
            self.profiles_modified = True
            self.current_profile = None
            
            # Clear spec tree
            for item in self.spec_tree.get_children():
                self.spec_tree.delete(item)
                
            # Reload profiles
            self.load_profiles()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete profile:\n{e}")
            logger.error(f"Delete profile failed: {e}", exc_info=True)
            
    def show_profile_context_menu(self, event):
        """Show context menu for profile list"""
        try:
            # Select item under cursor
            index = self.profile_listbox.nearest(event.y)
            self.profile_listbox.selection_clear(0, "end")
            self.profile_listbox.selection_set(index)
            self.profile_listbox.activate(index)
            
            # Trigger selection event manually
            self.on_profile_select(None)
            
            # Show menu
            self.profile_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.profile_context_menu.grab_release()
            
    def rename_profile(self):
        """Rename selected profile"""
        if not self.current_profile:
            return
            
        from tkinter import simpledialog
        new_name = simpledialog.askstring(
            "Rename Profile",
            f"Enter new name for '{self.current_profile}':",
            initialvalue=self.current_profile
        )
        
        if not new_name or not new_name.strip() or new_name == self.current_profile:
            return
            
        new_name = new_name.strip()
        
        # Check if exists
        if new_name in self.spec_manager.equipment_profiles:
            messagebox.showerror("Error", f"Profile '{new_name}' already exists")
            return
            
        try:
            # Rename in spec manager
            profile_data = self.spec_manager.equipment_profiles.pop(self.current_profile)
            self.spec_manager.equipment_profiles[new_name] = profile_data
            
            # Delete old profile file and save with new name
            if self.spec_manager.config_dir:
                old_file = self.spec_manager.config_dir / "profiles" / f"{self.current_profile}.json"
                if old_file.exists():
                    old_file.unlink()
            
            if self.spec_manager.save_equipment_profile(new_name):
                messagebox.showinfo("Success", f"Renamed '{self.current_profile}' to '{new_name}'")
                self.profiles_modified = True
                self.current_profile = new_name
                
                # Reload list
                self.load_profiles()
                
                # Select new name
                for i in range(self.profile_listbox.size()):
                    if self.profile_listbox.get(i) == new_name:
                        self.profile_listbox.selection_clear(0, "end")
                        self.profile_listbox.selection_set(i)
                        self.profile_listbox.see(i)
                        break
            else:
                messagebox.showerror("Error", "Failed to save changes")
                # Revert
                self.spec_manager.equipment_profiles[self.current_profile] = profile_data
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename profile:\n{e}")
            logger.error(f"Rename profile failed: {e}", exc_info=True)
            
    def show_spec_context_menu(self, event):
        """Show context menu for spec tree"""
        try:
            # Select item under cursor
            item_id = self.spec_tree.identify_row(event.y)
            if not item_id:
                return
                
            self.spec_tree.selection_set(item_id)
            self.spec_tree.focus(item_id)
            
            # Show menu only if it's a leaf item (has values)
            if self.view_mode == 'table':
                self.spec_context_menu.tk_popup(event.x_root, event.y_root)
            else:
                # In tree mode, check if it's a leaf node (has 'item' tag)
                tags = self.spec_tree.item(item_id)['tags']
                if 'item' in tags or 'search_match' in tags:
                    self.spec_context_menu.tk_popup(event.x_root, event.y_root)
                    
        finally:
            self.spec_context_menu.grab_release()
            
    def delete_spec_item(self):
        """Delete selected spec item"""
        item_id = self.spec_tree.focus()
        if not item_id:
            return
            
        try:
            values = self.spec_tree.item(item_id)['values']
            
            # Get item details based on view mode
            if self.view_mode == 'table':
                module, part_type, part, item_name, _, _, _ = values
            else:
                # Tree mode logic is complex, simpler to rely on table mode or stored data
                # For now, let's support table mode primarily, or find data from all_specs_data
                # But wait, we can find the item in all_specs_data using the tree structure
                # Actually, tree mode values are (type, spec, unit), so we need to traverse up
                
                # Let's simplify: Only support delete in Table Mode for now?
                # Or traverse up:
                parent_part = self.spec_tree.parent(item_id)
                parent_type = self.spec_tree.parent(parent_part)
                parent_module = self.spec_tree.parent(parent_type)
                
                if not parent_module: # Should not happen for leaf
                    return
                    
                module = self.spec_tree.item(parent_module)['text'].split(' ')[1] # "📁 Dsp (..)" -> Dsp
                part_type = self.spec_tree.item(parent_type)['text'].split(' ')[1] # "📂 XScanner (..)" -> XScanner
                part = self.spec_tree.item(parent_part)['text'].split(' ')[1] # "📄 100um" -> 100um
                item_name = self.spec_tree.item(item_id)['text'].split('• ')[1] # "      • ItemName" -> ItemName
            
            # Confirm delete
            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete item:\n'{item_name}'?"
            )
            if not confirm:
                return
                
            # Handle Common_Base delete
            if self.current_profile == '__COMMON_BASE__':
                self.spec_manager.remove_item_from_common_base(module, part_type, part, item_name)
                messagebox.showinfo("Success", "Item deleted from Common Base")
                self.display_common_base_specs()
                return
            
            # Remove from profile
            profile_data = self.spec_manager.equipment_profiles[self.current_profile]
            
            # Check additional_checks
            deleted = False
            if 'additional_checks' in profile_data:
                checks = profile_data['additional_checks']
                if module in checks and part_type in checks[module] and part in checks[module][part_type]:
                    items = checks[module][part_type][part]
                    # Filter out the item
                    new_items = [i for i in items if i.get('item_name') != item_name]
                    
                    if len(new_items) < len(items):
                        checks[module][part_type][part] = new_items
                        # Cleanup empty structures
                        if not new_items:
                            del checks[module][part_type][part]
                        if not checks[module][part_type]:
                            del checks[module][part_type]
                        if not checks[module]:
                            del checks[module]
                        deleted = True
            
            if not deleted:
                # It might be inherited. Instead of deleting, we override it to be disabled.
                
                # Check if overrides exists
                if 'overrides' not in profile_data:
                    profile_data['overrides'] = {}
                
                overrides = profile_data['overrides']
                
                # Create structure if needed
                if module not in overrides:
                    overrides[module] = {}
                if part_type not in overrides[module]:
                    overrides[module][part_type] = {}
                if part not in overrides[module][part_type]:
                    overrides[module][part_type][part] = []
                
                # Check if override already exists
                existing_overrides = overrides[module][part_type][part]
                found = False
                for i, ov in enumerate(existing_overrides):
                    if ov.get('item_name') == item_name:
                        # Update existing override
                        existing_overrides[i]['enabled'] = False
                        found = True
                        break
                
                if not found:
                    # Add new override to disable
                    # We need to find the original spec to keep other fields valid if needed,
                    # but for disabling, just item_name and enabled=False is enough for our logic,
                    # provided spec_manager merges correctly.
                    # Let's look at spec_manager._merge_specs. It updates fields.
                    # So we just need to push the update.
                    overrides[module][part_type][part].append({
                        'item_name': item_name,
                        'enabled': False
                    })
                
                deleted = True

            # Save changes to individual profile file
            if self.spec_manager.save_equipment_profile(self.current_profile):
                messagebox.showinfo("Success", "Item deleted successfully")
                self.display_profile_specs(self.current_profile)
            else:
                messagebox.showerror("Error", "Failed to save changes")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete item:\n{e}")
            logger.error(f"Delete item failed: {e}", exc_info=True)
    
    
    def export_profile(self):
        """Export selected profile to JSON file"""
        if not self.current_profile:
            messagebox.showwarning("Warning", "Please select a profile to export")
            return
        
        # Ask for save location
        from datetime import datetime
        default_filename = f"{self.current_profile}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = filedialog.asksaveasfilename(
            title="Export Profile",
            defaultextension=".json",
            initialfile=default_filename,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            # Prepare export data
            export_data = {
                "version": "1.0",
                "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "exported_by": "QC Inspection Tool",
                "profile_name": self.current_profile,
                "profile_data": self.spec_manager.equipment_profiles[self.current_profile]
            }
            
            # Save to JSON file
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo(
                "Export Success",
                f"Profile '{self.current_profile}' exported to:\n{filepath}\n\n"
                f"This file can be used to update the program with your changes."
            )
            logger.info(f"Profile exported: {self.current_profile} -> {filepath}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export profile:\n{e}")
            logger.error(f"Export failed: {e}", exc_info=True)
    
    def import_profile(self):
        """Import profile from JSON file"""
        # Ask for file
        filepath = filedialog.askopenfilename(
            title="Import Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            # Load JSON file
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate format
            if "profile_name" not in import_data or "profile_data" not in import_data:
                raise ValueError("Invalid profile file format")
            
            profile_name = import_data["profile_name"]
            profile_data = import_data["profile_data"]
            
            # Check if profile already exists
            if profile_name in self.spec_manager.equipment_profiles:
                confirm = messagebox.askyesno(
                    "Profile Exists",
                    f"Profile '{profile_name}' already exists.\n\n"
                    f"Do you want to overwrite it?"
                )
                if not confirm:
                    return
            
            # Import profile (in-memory only)
            self.spec_manager.equipment_profiles[profile_name] = profile_data
            
            # Reload profile list
            self.load_profiles()
            
            # Select imported profile
            for i in range(self.profile_listbox.size()):
                if self.profile_listbox.get(i) == profile_name:
                    self.profile_listbox.selection_clear(0, "end")
                    self.profile_listbox.selection_set(i)
                    self.profile_listbox.see(i)
                    self.current_profile = profile_name
                    self.display_profile_specs(profile_name)
                    break
            
            messagebox.showinfo(
                "Import Success",
                f"Profile '{profile_name}' imported successfully!\n\n"
                f"⚠️ Note: This change is temporary.\n"
                f"To make it permanent, export this profile and\n"
                f"send it to the administrator for rebuilding."
            )
            logger.info(f"Profile imported: {profile_name} from {filepath}")
            
        except json.JSONDecodeError:
            messagebox.showerror("Import Error", "Invalid JSON file format")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import profile:\n{e}")
            logger.error(f"Import failed: {e}", exc_info=True)
    
    def on_item_double_click(self, event):
        """Handle double-click on spec item - open quick edit dialog"""
        item_id = self.spec_tree.focus()
        if not item_id:
            return
        
        try:
            values = self.spec_tree.item(item_id)['values']
            
            if self.view_mode == 'table' and len(values) == 7:
                module, part_type, part, item_name, val_type, spec_str, unit = values
                spec_data = self.find_spec_data(module, part_type, part, item_name)
                
                if spec_data:
                    self.edit_spec_item(module, part_type, part, item_name, spec_data)
        
        except Exception as e:
            logger.error(f"Double-click error: {e}", exc_info=True)
    
    def find_spec_data(self, module, part_type, part, item_name):
        """Find spec data for given item"""
        try:
            if self.current_profile == '__COMMON_BASE__':
                specs = self.spec_manager.get_common_base_specs()
            else:
                specs = self.spec_manager.load_profile_with_inheritance(self.current_profile)
            
            if module in specs:
                if part_type in specs[module]:
                    if part in specs[module][part_type]:
                        for spec in specs[module][part_type][part]:
                            if spec.get('item_name') == item_name:
                                return spec
        except Exception as e:
            logger.error(f"Find spec error: {e}", exc_info=True)
        
        return None
    
    def edit_spec_item(self, module, part_type, part, item_name, spec_data):
        """Open edit dialog for spec item"""
        from src.ui.spec_item_editor import SpecItemEditorDialog
        
        dialog = SpecItemEditorDialog(self, module, part_type, part, item_name, spec_data)
        self.wait_window(dialog)
        
        if dialog.result:
            if self.current_profile == '__COMMON_BASE__':
                # Save to Common_Base
                self.spec_manager.update_common_base_item(
                    module, part_type, part, item_name, dialog.result
                )
                self.display_common_base_specs()
            else:
                self.update_spec_in_profile(module, part_type, part, item_name, dialog.result)
                self.display_profile_specs(self.current_profile)
            
            messagebox.showinfo(
                "Saved",
                f"Spec for '{item_name}' has been updated and saved."
            )
    
    def update_spec_in_profile(self, module, part_type, part, item_name, new_spec):
        """Update spec in current profile and save to file"""
        try:
            if self.current_profile not in self.spec_manager.equipment_profiles:
                return
            
            profile = self.spec_manager.equipment_profiles[self.current_profile]
            
            if 'additional_checks' not in profile:
                profile['additional_checks'] = {}
            
            checks = profile['additional_checks']
            
            if module not in checks:
                checks[module] = {}
            if part_type not in checks[module]:
                checks[module][part_type] = {}
            if part not in checks[module][part_type]:
                checks[module][part_type][part] = []
            
            items = checks[module][part_type][part]
            
            # Find and update existing item, or add new
            found = False
            for i, spec in enumerate(items):
                if spec.get('item_name') == item_name:
                    items[i] = new_spec
                    found = True
                    break
            
            if not found:
                # Add new item (override inherited item)
                items.append(new_spec)
            
            logger.info(f"Updated spec: {module}/{part_type}/{part}/{item_name}")
            
            # Save to individual profile file
            if self.spec_manager.save_equipment_profile(self.current_profile):
                logger.info("Profile saved successfully")
            else:
                logger.error("Failed to save profile")
            
        except Exception as e:
            logger.error(f"Update spec error: {e}", exc_info=True)
            raise
    
    def on_close(self):
        """Handle window close"""
        self.destroy()
