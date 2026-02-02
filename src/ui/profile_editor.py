"""
Profile Editor Window
Select items and configure specs for a profile
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Dict
import logging

from src.core.db_extractor import DBExtractor
from src.ui.spec_dialog import SpecConfigDialog

logger = logging.getLogger(__name__)


class ProfileEditorWindow(ctk.CTkToplevel):
    """
    Profile Editor - Select DB items and configure specs
    """
    
    def __init__(self, parent, profile_name: str, db_path: str, spec_manager, is_new: bool = True):
        super().__init__(parent)
        
        self.title(f"Profile Editor - {profile_name}")
        self.geometry("1000x700")
        
        self.profile_name = profile_name
        self.db_path = db_path
        self.spec_manager = spec_manager
        self.is_new = is_new
        
        self.db_data = None
        self.checked_items = set()
        self.item_specs = {}  # item_id -> spec dict
        self.item_map = {}  # tree item_id -> item data
        self.all_tree_items = []  # Store all item IDs for filtering
        
        self.profile_saved = False
        
        # Load existing profile data if editing
        if not is_new and profile_name in spec_manager.equipment_profiles:
            self.existing_profile = spec_manager.equipment_profiles[profile_name]
            logger.info(f"Loading existing profile '{profile_name}' for editing")
        else:
            self.existing_profile = None
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Create UI
        self.create_widgets()
        
        # Load DB
        self.load_db()
        
        # Center on parent
        self.center_on_parent(parent)
        
    def center_on_parent(self, parent):
        """Center window on parent"""
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (1000 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (700 // 2)
        self.geometry(f"+{x}+{y}")
        
    def create_widgets(self):
        """Create UI widgets"""
        # Header
        header = ctk.CTkLabel(
            self,
            text=f"✏ Editing: {self.profile_name}",
            font=("Segoe UI", 16, "bold")
        )
        header.pack(pady=15)
        
        # Instructions
        instructions = ctk.CTkLabel(
            self,
            text="1. Check ☑ items to include  |  2. Double-click to configure Range/Exact  |  3. Click Save",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        instructions.pack(pady=(0, 10))
        
        # Search frame
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            search_frame,
            text="🔍 Search:",
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=(0, 10))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Type to filter items (Module, Part, Item name)...",
            font=("Segoe UI", 12),
            width=500
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        self.search_result_label = ctk.CTkLabel(
            search_frame,
            text="",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        self.search_result_label.pack(side="left", padx=(10, 0))
        
        # Tree frame
        tree_container = ctk.CTkFrame(self)
        tree_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Create treeview
        self.tree = ttk.Treeview(
            tree_container,
            columns=('check', 'value', 'spec'),
            show='tree headings',
            selectmode='browse'
        )
        
        self.tree.heading('#0', text='Item')
        self.tree.heading('check', text='☑')
        self.tree.heading('value', text='Current Value')
        self.tree.heading('spec', text='Spec (Range/Exact)')
        
        self.tree.column('#0', width=350)
        self.tree.column('check', width=40, anchor='center')
        self.tree.column('value', width=150, anchor='center')
        self.tree.column('spec', width=400, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind events
        self.tree.bind('<Button-1>', self.on_click)
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # Bottom buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray",
            hover_color="#555555",
            width=120
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save Profile",
            command=self.save_profile,
            fg_color="#2fa572",
            hover_color="#248f5f",
            width=150
        ).pack(side="right", padx=5)
        
        # Item count label
        self.count_label = ctk.CTkLabel(
            btn_frame,
            text="Selected: 0 items",
            font=("Segoe UI", 12, "bold")
        )
        self.count_label.pack(side="left", padx=20)
        
    def load_db(self):
        """Load DB data"""
        try:
            extractor = DBExtractor(self.db_path)
            self.db_data = extractor.build_hierarchy()
            
            # Populate tree
            self.populate_tree()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load DB:\n{e}")
            logger.error(f"DB load failed: {e}", exc_info=True)
            self.destroy()
            
    def populate_tree(self):
        """Populate tree with DB items"""
        if not self.db_data:
            return
            
        # Add modules
        for module in self.db_data.get('modules', []):
            module_id = self.tree.insert('', 'end', text=f"▼ {module['name']}", open=False)
            
            for part in module.get('parts', []):
                part_id = self.tree.insert(
                    module_id,
                    'end',
                    text=f"  ▼ {part['type']}/{part['name']}",
                    open=False
                )
                
                for item in part.get('items', []):
                    item_id = self.tree.insert(
                        part_id,
                        'end',
                        text=f"    • {item.get('name', '')}",
                        values=("☐", item.get('value', ''), "Not configured")
                    )
                    
                    # Store item data
                    self.item_map[item_id] = {
                        'module': module['name'],
                        'part_type': part['type'],
                        'part_name': part['name'],
                        'item': item
                    }
                    
                    # Store for filtering
                    self.all_tree_items.append({
                        'id': item_id,
                        'module_id': module_id,
                        'part_id': part_id,
                        'module': module['name'],
                        'part_type': part['type'],
                        'part_name': part['name'],
                        'item_name': item.get('name', '')
                    })
        
        # Load existing items if editing
        if self.existing_profile:
            self.load_existing_items()
    
    def load_existing_items(self):
        """Load and check items from existing profile"""
        if not self.existing_profile:
            return
            
        logger.info("Loading existing items from profile")
        additional_checks = self.existing_profile.get('additional_checks', {})
        
        # Track loaded items for summary
        loaded_count = 0
        
        # Iterate through additional_checks
        for module, module_data in additional_checks.items():
            for part_type, type_data in module_data.items():
                for part_name, items in type_data.items():
                    for spec in items:
                        item_name = spec.get('item_name')
                        if not item_name:
                            continue
                            
                        # Skip if disabled (was deleted)
                        if not spec.get('enabled', True):
                            continue
                        
                        # Find matching item in tree
                        for item_id, item_data in self.item_map.items():
                            if (item_data['module'] == module and
                                item_data['part_type'] == part_type and
                                item_data['part_name'] == part_name and
                                item_data['item']['name'] == item_name):
                                
                                # Check this item
                                self.checked_items.add(item_id)
                                self.tree.set(item_id, 'check', "☑")
                                
                                # Load spec
                                self.item_specs[item_id] = spec.copy()
                                
                                # Update spec display
                                spec_str = self.format_spec_display(spec)
                                self.tree.set(item_id, 'spec', spec_str)
                                
                                loaded_count += 1
                                logger.debug(f"Loaded: {module}.{part_type}.{part_name}.{item_name}")
                                break
        
        self.update_count()
        logger.info(f"Loaded {loaded_count} existing items")
    
    def format_spec_display(self, spec):
        """Format spec for display in tree"""
        val_type = spec.get('validation_type', '').lower()
        
        if val_type == 'range':
            min_val = spec.get('min_spec', '?')
            max_val = spec.get('max_spec', '?')
            unit = spec.get('unit', '')
            return f"Range: [{min_val}, {max_val}] {unit}".strip()
        elif val_type == 'exact':
            expected = spec.get('expected_value', '?')
            return f"Exact: {expected}"
        else:
            return "Not configured"
    
    def on_click(self, event):
        """Handle click on checkbox"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":  # Check column
                item_id = self.tree.identify_row(event.y)
                if item_id in self.item_map:
                    self.toggle_check(item_id)
                    
    def toggle_check(self, item_id):
        """Toggle checked state"""
        if item_id in self.checked_items:
            self.checked_items.remove(item_id)
            self.tree.set(item_id, 'check', "☐")
        else:
            self.checked_items.add(item_id)
            self.tree.set(item_id, 'check', "☑")
            
        self.update_count()
        
    def on_double_click(self, event):
        """Handle double-click to configure spec"""
        item_id = self.tree.identify_row(event.y)
        if item_id not in self.item_map:
            return
            
        item_data = self.item_map[item_id]
        item_name = item_data['item']['name']
        current_value = item_data['item']['value']
        
        # Get existing spec if any
        current_spec = self.item_specs.get(item_id)
        
        # Open config dialog
        dialog = SpecConfigDialog(self, item_name, current_value, current_spec)
        self.wait_window(dialog)
        
        if dialog.result:
            self.item_specs[item_id] = dialog.result
            
            # Auto-check the item
            if item_id not in self.checked_items:
                self.checked_items.add(item_id)
                self.tree.set(item_id, 'check', "☑")
            
            # Update spec display
            val_type = dialog.result.get('validation_type')
            if val_type == 'range':
                spec_str = f"Range: [{dialog.result.get('min_spec')}, {dialog.result.get('max_spec')}] {dialog.result.get('unit', '')}"
            else:
                spec_str = f"Exact: {dialog.result.get('expected_value')} {dialog.result.get('unit', '')}"
                
            self.tree.set(item_id, 'spec', spec_str.strip())
            self.update_count()
            
    def update_count(self):
        """Update selected items count"""
        self.count_label.configure(text=f"Selected: {len(self.checked_items)} items")
    
    def on_search(self, event=None):
        """Filter tree items based on search query"""
        query = self.search_entry.get().strip().lower()
        
        if not query:
            # Restore all detached items
            for item_data in self.all_tree_items:
                # Reattach if detached
                if not self.tree.exists(item_data['id']) or not self.tree.parent(item_data['id']):
                    try:
                        self.tree.move(item_data['id'], item_data['part_id'], 'end')
                    except:
                        pass
                # Collapse all parents
                self.tree.item(item_data['module_id'], open=False)
                self.tree.item(item_data['part_id'], open=False)
            self.search_result_label.configure(text="")
            return
        
        # Filter items
        matched_count = 0
        matched_modules = set()
        matched_parts = set()
        
        for item_data in self.all_tree_items:
            # Check if query matches
            module_match = query in item_data['module'].lower()
            part_type_match = query in item_data['part_type'].lower()
            part_name_match = query in item_data['part_name'].lower()
            item_name_match = query in item_data['item_name'].lower()
            
            if module_match or part_type_match or part_name_match or item_name_match:
                # Show item (reattach if detached)
                try:
                    if not self.tree.parent(item_data['id']):
                        self.tree.move(item_data['id'], item_data['part_id'], 'end')
                except:
                    pass
                matched_count += 1
                matched_modules.add(item_data['module_id'])
                matched_parts.add(item_data['part_id'])
            else:
                # Hide item (detach from tree)
                try:
                    self.tree.detach(item_data['id'])
                except:
                    pass
        
        # Expand matched modules and parts
        for module_id in matched_modules:
            self.tree.item(module_id, open=True)
        for part_id in matched_parts:
            self.tree.item(part_id, open=True)
        
        # Update result label
        if matched_count > 0:
            self.search_result_label.configure(
                text=f"Found {matched_count} item(s)",
                text_color="#2fa572"
            )
        else:
            self.search_result_label.configure(
                text="No items found",
                text_color="#c62828"
            )
        
    def save_profile(self):
        """Save profile to spec manager"""
        if not self.checked_items:
            messagebox.showwarning("Warning", "Please select at least one item")
            return
            
        try:
            # Get existing profile or create new one
            if self.existing_profile:
                profile_data = {
                    'description': self.existing_profile.get('description', f"Profile for {self.db_path}"),
                    'inherits_from': self.existing_profile.get('inherits_from', 'Common_Base'),
                    'overrides': self.existing_profile.get('overrides', {}),
                    'additional_checks': self.existing_profile.get('additional_checks', {})
                }
                logger.info(f"Merging with existing profile '{self.profile_name}'")
            else:
                profile_data = {
                    "description": f"Profile for {self.db_path}",
                    "inherits_from": "Common_Base",
                    "overrides": {},
                    "additional_checks": {}
                }
                logger.info(f"Creating new profile '{self.profile_name}'")
            
            # Build new additional_checks from checked items
            new_additional_checks = {}
            
            for item_id in self.checked_items:
                if item_id not in self.item_map:
                    continue
                    
                data = self.item_map[item_id]
                module = data['module']
                part_type = data['part_type']
                part_name = data['part_name']
                item_name = data['item']['name']
                
                # Get spec
                spec = self.item_specs.get(item_id)
                if not spec:
                    # Create default exact match
                    spec = {
                        'item_name': item_name,
                        'validation_type': 'exact',
                        'expected_value': data['item']['value'],
                        'enabled': True
                    }
                else:
                    spec = spec.copy()
                    spec['item_name'] = item_name
                    spec['enabled'] = True
                
                # Add to new_additional_checks
                if module not in new_additional_checks:
                    new_additional_checks[module] = {}
                if part_type not in new_additional_checks[module]:
                    new_additional_checks[module][part_type] = {}
                if part_name not in new_additional_checks[module][part_type]:
                    new_additional_checks[module][part_type][part_name] = []
                    
                new_additional_checks[module][part_type][part_name].append(spec)
            
            # Merge: Keep items from DB tree, preserve items not in DB tree
            if self.existing_profile:
                # Start with existing additional_checks
                merged_checks = {}
                
                # First, add items from DB that were checked
                for module, module_data in new_additional_checks.items():
                    if module not in merged_checks:
                        merged_checks[module] = {}
                    for part_type, type_data in module_data.items():
                        if part_type not in merged_checks[module]:
                            merged_checks[module][part_type] = {}
                        for part_name, items in type_data.items():
                            merged_checks[module][part_type][part_name] = items
                
                # Then, preserve items that were in profile but not in current DB
                existing_checks = profile_data.get('additional_checks', {})
                for module, module_data in existing_checks.items():
                    for part_type, type_data in module_data.items():
                        for part_name, items in type_data.items():
                            for spec in items:
                                item_name = spec.get('item_name')
                                
                                # Check if this item exists in current DB
                                found_in_db = False
                                for item_data in self.item_map.values():
                                    if (item_data['module'] == module and
                                        item_data['part_type'] == part_type and
                                        item_data['part_name'] == part_name and
                                        item_data['item']['name'] == item_name):
                                        found_in_db = True
                                        break
                                
                                # If not in DB, preserve it (user can't see it to uncheck)
                                if not found_in_db:
                                    if module not in merged_checks:
                                        merged_checks[module] = {}
                                    if part_type not in merged_checks[module]:
                                        merged_checks[module][part_type] = {}
                                    if part_name not in merged_checks[module][part_type]:
                                        merged_checks[module][part_type][part_name] = []
                                    merged_checks[module][part_type][part_name].append(spec)
                                    logger.debug(f"Preserving item not in DB: {module}.{part_type}.{part_name}.{item_name}")
                
                profile_data['additional_checks'] = merged_checks
            else:
                profile_data['additional_checks'] = new_additional_checks
            
            # Save to spec manager
            self.spec_manager.equipment_profiles[self.profile_name] = profile_data
            
            # Save to file
            spec_file = Path(__file__).parent.parent.parent / "config" / "qc_specs.json"
            if self.spec_manager.save_spec_file(str(spec_file)):
                messagebox.showinfo(
                    "Success",
                    f"Profile '{self.profile_name}' saved with {len(self.checked_items)} items"
                )
                self.profile_saved = True
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to save spec file")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile:\n{e}")
            logger.error(f"Save profile failed: {e}", exc_info=True)
