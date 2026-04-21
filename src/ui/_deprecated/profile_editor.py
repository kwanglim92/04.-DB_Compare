"""
Profile Editor Window
Select items and configure specs for a profile
Supports two modes:
  - New: Load DB to select items
  - Edit: Show existing items directly, add from DB/Common Base on demand
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict
import logging

from src.core.db_extractor import DBExtractor
from src.ui.spec_dialog import SpecConfigDialog
from src.utils.format_helpers import center_window_on_parent

logger = logging.getLogger(__name__)


class ProfileEditorWindow(ctk.CTkToplevel):
    """
    Profile Editor - Select DB items and configure specs
    """
    
    def __init__(self, parent, profile_name: str, db_path: str, spec_manager, is_new: bool = True, is_common_base: bool = False):
        super().__init__(parent)
        
        self.profile_name = profile_name
        self.db_path = db_path
        self.spec_manager = spec_manager
        self.is_new = is_new
        self.is_common_base = is_common_base
        
        title_prefix = "★ Common Base Editor" if is_common_base else "Profile Editor"
        self.title(f"{title_prefix} - {profile_name}")
        self.geometry("1000x700")
        
        self.db_data = None
        self.checked_items = set()
        self.item_specs = {}  # item_id -> spec dict
        self.item_map = {}  # tree item_id -> item data
        self.all_tree_items = []  # Store all item IDs for filtering
        
        self.profile_saved = False
        
        # Load existing profile data if editing
        if is_common_base:
            self.existing_profile = None  # Common Base uses its own loader
        elif not is_new and profile_name in spec_manager.equipment_profiles:
            self.existing_profile = spec_manager.equipment_profiles[profile_name]
            logger.info(f"Loading existing profile '{profile_name}' for editing")
        else:
            self.existing_profile = None
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Create UI
        self.create_widgets()
        
        # Load data based on mode
        if is_common_base:
            self.load_common_base_items()
        elif is_new and db_path:
            self.load_db()
        elif not is_new and self.existing_profile:
            self.load_existing_profile_items()
        
        center_window_on_parent(self, parent, 1000, 700)
        
    def create_widgets(self):
        """Create UI widgets"""
        # Header
        if self.is_common_base:
            mode_text = "★ Common Base"
        elif not self.is_new:
            mode_text = "✏ Editing"
        else:
            mode_text = "➕ New Profile"
        header = ctk.CTkLabel(
            self,
            text=f"{mode_text}: {self.profile_name}",
            font=("Segoe UI", 16, "bold")
        )
        header.pack(pady=15)
        
        # Instructions
        if self.is_common_base:
            instr_text = "Double-click to edit spec values  |  Use [＋ Add from DB] to add items  |  Changes affect ALL profiles"
        elif self.is_new:
            instr_text = "1. Check ☑ items to include  |  2. Double-click to configure Range/Exact  |  3. Click Save"
        else:
            instr_text = "Double-click to edit spec values  |  Use buttons below to add items"
        
        ctk.CTkLabel(
            self, text=instr_text,
            font=("Segoe UI", 11), text_color="gray"
        ).pack(pady=(0, 10))
        
        # Search frame
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            search_frame, text="🔍 Search:",
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=(0, 10))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Type to filter items (Module, Part, Item name)...",
            font=("Segoe UI", 12), width=500
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        self.search_result_label = ctk.CTkLabel(
            search_frame, text="", font=("Segoe UI", 11), text_color="gray"
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
        
        # Add buttons frame (for Edit/Common Base mode — add items on demand)
        if not self.is_new or self.is_common_base:
            add_frame = ctk.CTkFrame(self, fg_color="transparent")
            add_frame.pack(fill="x", padx=20, pady=(0, 5))
            
            ctk.CTkButton(
                add_frame,
                text="＋ Add from DB",
                command=self.add_items_from_db,
                fg_color="#1f6aa5",
                hover_color="#144870",
                width=160, height=34,
                font=("Segoe UI", 12, "bold")
            ).pack(side="left", padx=5)
            
            # Don't show "Add Common Specs" when editing Common Base itself
            if not self.is_common_base:
                ctk.CTkButton(
                    add_frame,
                    text="＋ Add Common Specs",
                    command=self.add_common_specs,
                    fg_color="#7b1fa2",
                    hover_color="#6a1b9a",
                    width=180, height=34,
                    font=("Segoe UI", 12, "bold")
                ).pack(side="left", padx=5)
        
        # Bottom buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(
            btn_frame, text="Cancel", command=self.destroy,
            fg_color="gray", hover_color="#555555", width=120
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="💾 Save Profile", command=self.save_profile,
            fg_color="#2fa572", hover_color="#248f5f", width=150
        ).pack(side="right", padx=5)
        
        # Item count label
        self.count_label = ctk.CTkLabel(
            btn_frame, text="Selected: 0 items",
            font=("Segoe UI", 12, "bold")
        )
        self.count_label.pack(side="left", padx=20)
        
    def load_db(self):
        """Load DB data (New mode)"""
        try:
            extractor = DBExtractor(self.db_path)
            self.db_data = extractor.build_hierarchy()
            self.populate_tree_from_db()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load DB:\n{e}")
            logger.error(f"DB load failed: {e}", exc_info=True)
            self.destroy()
    
    def load_common_base_items(self):
        """Load Common_Base specs directly (Common Base edit mode)"""
        specs = self.spec_manager.get_common_base_specs()
        if not specs:
            logger.info("Common Base has no specs")
            return
        
        item_count = 0
        for module_name, module_data in specs.items():
            part_count = sum(len(type_data) for type_data in module_data.values())
            module_id = self.tree.insert('', 'end', text=f"▼ {module_name} ({part_count} parts)", open=True)
            
            for part_type, type_data in module_data.items():
                for part_name, items in type_data.items():
                    enabled_items = [s for s in items if s.get('enabled', True)]
                    part_id = self.tree.insert(
                        module_id, 'end',
                        text=f"  ▼ {part_type}/{part_name} ({len(enabled_items)} items)",
                        open=False
                    )
                    
                    for spec in items:
                        if not spec.get('enabled', True):
                            continue
                        
                        item_name = spec.get('item_name', '')
                        spec_str = self.format_spec_display(spec)
                        
                        item_id = self.tree.insert(
                            part_id, 'end',
                            text=f"    • {item_name}",
                            values=("☑", "", spec_str)
                        )
                        
                        self.item_map[item_id] = {
                            'module': module_name,
                            'part_type': part_type,
                            'part_name': part_name,
                            'item': {'name': item_name, 'value': ''}
                        }
                        
                        self.checked_items.add(item_id)
                        self.item_specs[item_id] = spec.copy()
                        
                        self.all_tree_items.append({
                            'id': item_id,
                            'module_id': module_id,
                            'part_id': part_id,
                            'module': module_name,
                            'part_type': part_type,
                            'part_name': part_name,
                            'item_name': item_name
                        })
                        
                        item_count += 1
        
        self.update_count()
        logger.info(f"Loaded {item_count} Common Base items")
    
    def load_existing_profile_items(self):
        """Load existing profile items directly (Edit mode — no DB needed)"""
        if not self.existing_profile:
            return
        
        # Load specs with inheritance to show the complete picture
        try:
            specs = self.spec_manager.load_profile_with_inheritance(self.profile_name)
            if not specs:
                return
            
            # Populate tree from loaded specs
            item_count = 0
            for module_name, module_data in specs.items():
                part_count = sum(len(type_data) for type_data in module_data.values())
                module_id = self.tree.insert('', 'end', text=f"▼ {module_name} ({part_count} parts)", open=True)
                
                for part_type, type_data in module_data.items():
                    for part_name, items in type_data.items():
                        enabled_items = [s for s in items if s.get('enabled', True)]
                        part_id = self.tree.insert(
                            module_id, 'end',
                            text=f"  ▼ {part_type}/{part_name} ({len(enabled_items)} items)",
                            open=False
                        )
                        
                        for spec in items:
                            if not spec.get('enabled', True):
                                continue
                            
                            item_name = spec.get('item_name', '')
                            spec_str = self.format_spec_display(spec)
                            
                            item_id = self.tree.insert(
                                part_id, 'end',
                                text=f"    • {item_name}",
                                values=("☑", "", spec_str)
                            )
                            
                            # Store item data
                            self.item_map[item_id] = {
                                'module': module_name,
                                'part_type': part_type,
                                'part_name': part_name,
                                'item': {'name': item_name, 'value': ''}
                            }
                            
                            # Auto-check and store spec
                            self.checked_items.add(item_id)
                            self.item_specs[item_id] = spec.copy()
                            
                            # Store for filtering
                            self.all_tree_items.append({
                                'id': item_id,
                                'module_id': module_id,
                                'part_id': part_id,
                                'module': module_name,
                                'part_type': part_type,
                                'part_name': part_name,
                                'item_name': item_name
                            })
                            
                            item_count += 1
            
            self.update_count()
            logger.info(f"Loaded {item_count} items from existing profile")
            
        except Exception as e:
            logger.error(f"Error loading profile items: {e}", exc_info=True)
    
    def add_items_from_db(self):
        """Open DB and add new items to the profile"""
        db_path = filedialog.askdirectory(title="Select DB to add items from")
        if not db_path:
            return
        
        try:
            extractor = DBExtractor(db_path)
            db_data = extractor.build_hierarchy()
            
            if not db_data:
                messagebox.showwarning("Warning", "No items found in selected DB")
                return
            
            # Collect existing item keys
            existing_keys = set()
            for item_data in self.item_map.values():
                key = f"{item_data['module']}.{item_data['part_type']}.{item_data['part_name']}.{item_data['item']['name']}"
                existing_keys.add(key)
            
            # Show selection dialog with only non-existing items
            self._show_add_items_dialog(db_data, existing_keys, source="DB")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load DB:\n{e}")
            logger.error(f"Add from DB failed: {e}", exc_info=True)
    
    def add_common_specs(self):
        """Add items from Common_Base specs"""
        common_specs = self.spec_manager.get_common_base_specs()
        
        if not common_specs:
            messagebox.showinfo("Info", "Common Base has no specs defined")
            return
        
        # Collect existing item keys
        existing_keys = set()
        for item_data in self.item_map.values():
            key = f"{item_data['module']}.{item_data['part_type']}.{item_data['part_name']}.{item_data['item']['name']}"
            existing_keys.add(key)
        
        # Build pseudo db_data structure from common specs
        pseudo_db = {'modules': []}
        for module, module_data in common_specs.items():
            mod = {'name': module, 'parts': []}
            for part_type, type_data in module_data.items():
                for part_name, items in type_data.items():
                    part = {'type': part_type, 'name': part_name, 'items': []}
                    for spec in items:
                        item_name = spec.get('item_name', '')
                        part['items'].append({
                            'name': item_name,
                            'value': spec.get('expected_value', ''),
                            '_spec': spec  # Attach spec for auto-config
                        })
                    mod['parts'].append(part)
            pseudo_db['modules'].append(mod)
        
        self._show_add_items_dialog(pseudo_db, existing_keys, source="Common Base")
    
    def _show_add_items_dialog(self, db_data, existing_keys, source="DB"):
        """Show dialog to select new items to add — matches Profile Editor UI"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Add Items from {source}")
        dialog.geometry("1000x700")
        dialog.transient(self)
        dialog.grab_set()
        center_window_on_parent(dialog, self, 1000, 700)
        
        # Header
        ctk.CTkLabel(
            dialog, text=f"Select items to add from {source}",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=15)
        
        ctk.CTkLabel(
            dialog, text="Items already in profile are excluded. Check ☑ items to add.",
            font=("Segoe UI", 11), text_color="gray"
        ).pack(pady=(0, 10))
        
        # Search frame
        search_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            search_frame, text="🔍 Search:",
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=(0, 10))
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Type to filter items (Module, Part, Item name)...",
            font=("Segoe UI", 12), width=500
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        search_result_label = ctk.CTkLabel(
            search_frame, text="", font=("Segoe UI", 11), text_color="gray"
        )
        search_result_label.pack(side="left", padx=(10, 0))
        
        # Tree
        tree_frame = ctk.CTkFrame(dialog)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        add_tree = ttk.Treeview(
            tree_frame,
            columns=('check', 'value'),
            show='tree headings',
            selectmode='browse'
        )
        add_tree.heading('#0', text='Item')
        add_tree.heading('check', text='☑')
        add_tree.heading('value', text='Value')
        add_tree.column('#0', width=500)
        add_tree.column('check', width=40, anchor='center')
        add_tree.column('value', width=200, anchor='center')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=add_tree.yview)
        add_tree.configure(yscrollcommand=scrollbar.set)
        add_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Tags for existing vs new items — amber/gold visible in dark mode
        add_tree.tag_configure('existing', foreground='#c9a33e', background='#2e2a1a')
        add_tree.tag_configure('new_item', foreground='')
        
        # Populate ALL items — existing as gold ☑, new as ☐
        check_items = set()
        item_data_map = {}       # toggleable new items
        existing_iids = set()    # non-toggleable existing items
        all_add_items = []       # For search filtering
        new_count = 0
        existing_count = 0
        
        # Part node tracking for (selected/total) counts
        part_info = {}  # part_id -> {'total': N, 'label': str, 'children': [iid,...]}
        
        for module in db_data.get('modules', []):
            module_parts = module.get('parts', [])
            part_count = len(module_parts)
            module_id = add_tree.insert('', 'end', text=f"▼ {module['name']} ({part_count} parts)", open=False)
            
            for part in module_parts:
                part_items = part.get('items', [])
                total_in_part = len(part_items)
                part_label = f"{part['type']}/{part['name']}"
                part_id = add_tree.insert(module_id, 'end', text=f"  ▼ {part_label} (0/{total_in_part} items)", open=False)
                part_info[part_id] = {'total': total_in_part, 'label': part_label, 'children': []}
                
                for item in part_items:
                    item_name = item.get('name', '')
                    key = f"{module['name']}.{part['type']}.{part['name']}.{item_name}"
                    
                    is_existing = key in existing_keys
                    
                    if is_existing:
                        # Existing item — amber/gold, pre-checked, non-toggleable
                        iid = add_tree.insert(
                            part_id, 'end',
                            text=f"    • {item_name}",
                            values=("☑", item.get('value', '')),
                            tags=('existing',)
                        )
                        existing_iids.add(iid)
                        existing_count += 1
                    else:
                        # New item — normal, toggleable
                        iid = add_tree.insert(
                            part_id, 'end',
                            text=f"    • {item_name}",
                            values=("☐", item.get('value', '')),
                            tags=('new_item',)
                        )
                        item_data_map[iid] = {
                            'module': module['name'],
                            'part_type': part['type'],
                            'part_name': part['name'],
                            'item': item
                        }
                        new_count += 1
                    
                    part_info[part_id]['children'].append(iid)
                    
                    all_add_items.append({
                        'id': iid,
                        'module_id': module_id,
                        'part_id': part_id,
                        'module': module['name'],
                        'part_type': part['type'],
                        'part_name': part['name'],
                        'item_name': item_name,
                        'is_existing': is_existing
                    })
        
        # Set initial part counts (existing items count as selected)
        for pid, info in part_info.items():
            selected_in_part = sum(1 for c in info['children'] if c in existing_iids)
            add_tree.item(pid, text=f"  ▼ {info['label']} ({selected_in_part}/{info['total']} items)")
        
        if new_count == 0:
            ctk.CTkLabel(
                dialog, text="No new items to add. All items already in profile.",
                font=("Segoe UI", 13), text_color="#ff9800"
            ).pack(pady=20)
        
        # Count label reference for updates
        count_label = [None]  # Use list for closure mutability
        
        def update_count_display():
            if count_label[0]:
                count_label[0].configure(
                    text=f"Selected: {len(check_items)} new  |  {existing_count} existing"
                )
        
        def update_part_count(part_id):
            """Update the part node text with (selected/total) count"""
            info = part_info.get(part_id)
            if not info:
                return
            selected = sum(1 for c in info['children'] if c in check_items or c in existing_iids)
            add_tree.item(part_id, text=f"  ▼ {info['label']} ({selected}/{info['total']} items)")
        
        # Toggle function — only allow new items
        def toggle_check(event):
            region = add_tree.identify("region", event.x, event.y)
            if region == "cell":
                col = add_tree.identify_column(event.x)
                if col == "#1":
                    iid = add_tree.identify_row(event.y)
                    if iid in existing_iids:
                        return  # Cannot toggle existing items
                    if iid in item_data_map:
                        if iid in check_items:
                            check_items.discard(iid)
                            add_tree.set(iid, 'check', "☐")
                        else:
                            check_items.add(iid)
                            add_tree.set(iid, 'check', "☑")
                        update_count_display()
                        # Update parent part node count
                        parent = add_tree.parent(iid)
                        if parent:
                            update_part_count(parent)
        
        add_tree.bind('<Button-1>', toggle_check)
        
        # Search function
        def on_search(event=None):
            query = search_entry.get().strip().lower()
            
            if not query:
                # Show all items
                for item_data in all_add_items:
                    try:
                        if not add_tree.parent(item_data['id']):
                            add_tree.move(item_data['id'], item_data['part_id'], 'end')
                    except:
                        pass
                    add_tree.item(item_data['module_id'], open=False)
                    add_tree.item(item_data['part_id'], open=False)
                search_result_label.configure(text="")
                return
            
            matched_count = 0
            matched_modules = set()
            matched_parts = set()
            
            for item_data in all_add_items:
                module_match = query in item_data['module'].lower()
                part_type_match = query in item_data['part_type'].lower()
                part_name_match = query in item_data['part_name'].lower()
                item_name_match = query in item_data['item_name'].lower()
                
                if module_match or part_type_match or part_name_match or item_name_match:
                    try:
                        if not add_tree.parent(item_data['id']):
                            add_tree.move(item_data['id'], item_data['part_id'], 'end')
                    except:
                        pass
                    matched_count += 1
                    matched_modules.add(item_data['module_id'])
                    matched_parts.add(item_data['part_id'])
                else:
                    try:
                        add_tree.detach(item_data['id'])
                    except:
                        pass
            
            for mid in matched_modules:
                add_tree.item(mid, open=True)
            for pid in matched_parts:
                add_tree.item(pid, open=True)
            
            if matched_count > 0:
                search_result_label.configure(text=f"Found {matched_count} item(s)", text_color="#2fa572")
            else:
                search_result_label.configure(text="No items found", text_color="#c62828")
        
        search_entry.bind('<KeyRelease>', on_search)
        
        # Bottom buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        # Selected count (left side)
        count_label[0] = ctk.CTkLabel(
            btn_frame, text="Selected: 0 items",
            font=("Segoe UI", 12, "bold")
        )
        count_label[0].pack(side="left", padx=20)
        
        def on_add():
            for iid in check_items:
                data = item_data_map[iid]
                item = data['item']
                item_name = item.get('name', '')
                
                # Get spec from _spec if available (Common Base), or create default
                spec = item.get('_spec', {
                    'item_name': item_name,
                    'validation_type': 'exact',
                    'expected_value': item.get('value', ''),
                    'enabled': True
                }).copy()
                spec['item_name'] = item_name
                spec['enabled'] = True
                
                # Find or create parent nodes in main tree
                main_module_id = self._find_or_create_module(data['module'])
                main_part_id = self._find_or_create_part(main_module_id, data['part_type'], data['part_name'])
                
                spec_str = self.format_spec_display(spec)
                new_item_id = self.tree.insert(
                    main_part_id, 'end',
                    text=f"    • {item_name}",
                    values=("☑", item.get('value', ''), spec_str)
                )
                
                self.item_map[new_item_id] = data
                self.checked_items.add(new_item_id)
                self.item_specs[new_item_id] = spec
                self.all_tree_items.append({
                    'id': new_item_id,
                    'module_id': main_module_id,
                    'part_id': main_part_id,
                    'module': data['module'],
                    'part_type': data['part_type'],
                    'part_name': data['part_name'],
                    'item_name': item_name
                })
            
            self.update_count()
            dialog.destroy()
            if check_items:
                messagebox.showinfo("Added", f"{len(check_items)} items added to profile")
        
        ctk.CTkButton(
            btn_frame, text="Cancel", command=dialog.destroy,
            fg_color="gray", hover_color="#555555", width=120
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="✓ Add Selected", command=on_add,
            fg_color="#2fa572", hover_color="#248f5f", width=150
        ).pack(side="right", padx=5)
    
    def _find_or_create_module(self, module_name):
        """Find existing module node or create new one"""
        for child in self.tree.get_children(''):
            if self.tree.item(child)['text'].endswith(module_name):
                return child
        return self.tree.insert('', 'end', text=f"▼ {module_name}", open=True)
    
    def _find_or_create_part(self, module_id, part_type, part_name):
        """Find existing part node or create new one"""
        label = f"  ▼ {part_type}/{part_name}"
        for child in self.tree.get_children(module_id):
            if self.tree.item(child)['text'] == label:
                return child
        return self.tree.insert(module_id, 'end', text=label, open=True)
    
    def populate_tree_from_db(self):
        """Populate tree with DB items (New mode)"""
        if not self.db_data:
            return
            
        for module in self.db_data.get('modules', []):
            part_count = len(module.get('parts', []))
            module_id = self.tree.insert('', 'end', text=f"▼ {module['name']} ({part_count} parts)", open=False)
            
            for part in module.get('parts', []):
                item_count = len(part.get('items', []))
                part_id = self.tree.insert(
                    module_id, 'end',
                    text=f"  ▼ {part['type']}/{part['name']} ({item_count} items)",
                    open=False
                )
                
                for item in part.get('items', []):
                    item_id = self.tree.insert(
                        part_id, 'end',
                        text=f"    • {item.get('name', '')}",
                        values=("☐", item.get('value', ''), "Not configured")
                    )
                    
                    self.item_map[item_id] = {
                        'module': module['name'],
                        'part_type': part['type'],
                        'part_name': part['name'],
                        'item': item
                    }
                    
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
        """Load and check items from existing profile (New mode with DB)"""
        if not self.existing_profile:
            return
            
        logger.info("Loading existing items from profile")
        additional_checks = self.existing_profile.get('additional_checks', {})
        loaded_count = 0
        
        for module, module_data in additional_checks.items():
            for part_type, type_data in module_data.items():
                for part_name, items in type_data.items():
                    for spec in items:
                        item_name = spec.get('item_name')
                        if not item_name or not spec.get('enabled', True):
                            continue
                        
                        for item_id, item_data in self.item_map.items():
                            if (item_data['module'] == module and
                                item_data['part_type'] == part_type and
                                item_data['part_name'] == part_name and
                                item_data['item']['name'] == item_name):
                                
                                self.checked_items.add(item_id)
                                self.tree.set(item_id, 'check', "☑")
                                self.item_specs[item_id] = spec.copy()
                                spec_str = self.format_spec_display(spec)
                                self.tree.set(item_id, 'spec', spec_str)
                                loaded_count += 1
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
        elif val_type == 'check':
            return "Check (record only)"
        else:
            return "Not configured"
    
    def on_click(self, event):
        """Handle click on checkbox"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":
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
        current_value = item_data['item'].get('value', '')
        
        current_spec = self.item_specs.get(item_id)
        
        dialog = SpecConfigDialog(self, item_name, current_value, current_spec)
        self.wait_window(dialog)
        
        if dialog.result:
            self.item_specs[item_id] = dialog.result
            
            if item_id not in self.checked_items:
                self.checked_items.add(item_id)
                self.tree.set(item_id, 'check', "☑")
            
            spec_str = self.format_spec_display(dialog.result)
            self.tree.set(item_id, 'spec', spec_str)
            self.update_count()
            
    def update_count(self):
        """Update selected items count"""
        self.count_label.configure(text=f"Selected: {len(self.checked_items)} items")
    
    def on_search(self, event=None):
        """Filter tree items based on search query"""
        query = self.search_entry.get().strip().lower()
        
        if not query:
            for item_data in self.all_tree_items:
                if not self.tree.exists(item_data['id']) or not self.tree.parent(item_data['id']):
                    try:
                        self.tree.move(item_data['id'], item_data['part_id'], 'end')
                    except:
                        pass
                self.tree.item(item_data['module_id'], open=False)
                self.tree.item(item_data['part_id'], open=False)
            self.search_result_label.configure(text="")
            return
        
        matched_count = 0
        matched_modules = set()
        matched_parts = set()
        
        for item_data in self.all_tree_items:
            module_match = query in item_data['module'].lower()
            part_type_match = query in item_data['part_type'].lower()
            part_name_match = query in item_data['part_name'].lower()
            item_name_match = query in item_data['item_name'].lower()
            
            if module_match or part_type_match or part_name_match or item_name_match:
                try:
                    if not self.tree.parent(item_data['id']):
                        self.tree.move(item_data['id'], item_data['part_id'], 'end')
                except:
                    pass
                matched_count += 1
                matched_modules.add(item_data['module_id'])
                matched_parts.add(item_data['part_id'])
            else:
                try:
                    self.tree.detach(item_data['id'])
                except:
                    pass
        
        for module_id in matched_modules:
            self.tree.item(module_id, open=True)
        for part_id in matched_parts:
            self.tree.item(part_id, open=True)
        
        if matched_count > 0:
            self.search_result_label.configure(text=f"Found {matched_count} item(s)", text_color="#2fa572")
        else:
            self.search_result_label.configure(text="No items found", text_color="#c62828")
        
    def save_profile(self):
        """Save profile to spec manager"""
        if not self.checked_items:
            messagebox.showwarning("Warning", "Please select at least one item")
            return
            
        try:
            # ===== Common Base save =====
            if self.is_common_base:
                new_specs = {}
                for item_id in self.checked_items:
                    if item_id not in self.item_map:
                        continue
                    data = self.item_map[item_id]
                    module = data['module']
                    part_type = data['part_type']
                    part_name = data['part_name']
                    item_name = data['item']['name']
                    
                    spec = self.item_specs.get(item_id)
                    if not spec:
                        spec = {
                            'item_name': item_name,
                            'validation_type': 'exact',
                            'expected_value': data['item'].get('value', ''),
                            'enabled': True
                        }
                    else:
                        spec = spec.copy()
                        spec['item_name'] = item_name
                        spec['enabled'] = True
                    
                    if module not in new_specs:
                        new_specs[module] = {}
                    if part_type not in new_specs[module]:
                        new_specs[module][part_type] = {}
                    if part_name not in new_specs[module][part_type]:
                        new_specs[module][part_type][part_name] = []
                    new_specs[module][part_type][part_name].append(spec)
                
                # Update base profile specs
                if 'Common_Base' not in self.spec_manager.base_profiles:
                    self.spec_manager.base_profiles['Common_Base'] = {
                        'description': 'Common Base Profile', 'specs': {}
                    }
                self.spec_manager.base_profiles['Common_Base']['specs'] = new_specs
                
                if self.spec_manager.save_base_profile():
                    messagebox.showinfo(
                        "Success",
                        f"Common Base saved with {len(self.checked_items)} items"
                    )
                    self.profile_saved = True
                    self.destroy()
                else:
                    messagebox.showerror("Error", "Failed to save Common Base")
                return
            
            # ===== Equipment Profile save =====
            # Get existing profile or create new one
            if self.existing_profile:
                profile_data = {
                    'description': self.existing_profile.get('description', f"Profile for {self.db_path or self.profile_name}"),
                    'inherits_from': self.existing_profile.get('inherits_from', 'Common_Base'),
                    'overrides': self.existing_profile.get('overrides', {}),
                    'additional_checks': self.existing_profile.get('additional_checks', {}),
                    'excluded_items': self.existing_profile.get('excluded_items', [])
                }
                logger.info(f"Merging with existing profile '{self.profile_name}'")
            else:
                profile_data = {
                    "description": f"Profile for {self.db_path or self.profile_name}",
                    "inherits_from": "Common_Base",
                    "overrides": {},
                    "additional_checks": {},
                    "excluded_items": []
                }
                logger.info(f"Creating new profile '{self.profile_name}'")
            
            # Build additional_checks from checked items
            new_additional_checks = {}
            
            for item_id in self.checked_items:
                if item_id not in self.item_map:
                    continue
                    
                data = self.item_map[item_id]
                module = data['module']
                part_type = data['part_type']
                part_name = data['part_name']
                item_name = data['item']['name']
                
                spec = self.item_specs.get(item_id)
                if not spec:
                    spec = {
                        'item_name': item_name,
                        'validation_type': 'exact',
                        'expected_value': data['item'].get('value', ''),
                        'enabled': True
                    }
                else:
                    spec = spec.copy()
                    spec['item_name'] = item_name
                    spec['enabled'] = True
                
                if module not in new_additional_checks:
                    new_additional_checks[module] = {}
                if part_type not in new_additional_checks[module]:
                    new_additional_checks[module][part_type] = {}
                if part_name not in new_additional_checks[module][part_type]:
                    new_additional_checks[module][part_type][part_name] = []
                    
                new_additional_checks[module][part_type][part_name].append(spec)
            
            profile_data['additional_checks'] = new_additional_checks
            
            # Save to spec manager
            self.spec_manager.equipment_profiles[self.profile_name] = profile_data
            
            # Save to file
            if self.spec_manager.save_equipment_profile(self.profile_name):
                messagebox.showinfo(
                    "Success",
                    f"Profile '{self.profile_name}' saved with {len(self.checked_items)} items"
                )
                self.profile_saved = True
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to save profile")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile:\n{e}")
            logger.error(f"Save profile failed: {e}", exc_info=True)
