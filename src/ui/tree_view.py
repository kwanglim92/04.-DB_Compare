"""
DB Tree View Component
Displays DB hierarchy with QC results using ttk.Treeview
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional


class DBTreeView:
    """
    Tree view component to display DB structure with QC results
    """
    
    def __init__(self, parent):
        """
        Initialize tree view
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        
        # Create tree frame
        self.tree_frame = ttk.Frame(parent)
        self.tree_frame.pack(fill="both", expand=True)
        
        # Create treeview (no checkbox column for main view)
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=('value', 'spec', 'status'),
            show='tree headings',
            selectmode='browse'
        )
        
        # Configure columns
        self.tree.heading('#0', text='Item')
        self.tree.heading('value', text='Actual Value')
        self.tree.heading('spec', text='Spec')
        self.tree.heading('status', text='Status')
        
        self.tree.column('#0', width=300, minwidth=200)
        self.tree.column('value', width=120, minwidth=80, anchor='center')
        self.tree.column('spec', width=90, minwidth=80, anchor='center')
        self.tree.column('status', width=100, minwidth=80, anchor='center')
        
        # Add scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        
        # Configure tags for colors
        self.tree.tag_configure('pass', foreground='#2fa572', font=('Segoe UI', 10))
        self.tree.tag_configure('fail', foreground='#d32f2f', font=('Segoe UI', 10, 'bold'))
        self.tree.tag_configure('no_spec', foreground='#757575', font=('Segoe UI', 10))
        self.tree.tag_configure('error', foreground='#ed6c02', font=('Segoe UI', 10))
        self.tree.tag_configure('skipped', foreground='#9e9e9e', font=('Segoe UI', 10))
        self.tree.tag_configure('module', foreground='#1f6aa5', font=('Segoe UI', 11, 'bold'))
        self.tree.tag_configure('part', foreground='#424242', font=('Segoe UI', 10, 'bold'))
        # Search highlight (F1) — yellow background, dark foreground
        self.tree.tag_configure('search_hit', background='#fff59d', foreground='#5d4d00',
                                font=('Segoe UI', 10, 'bold'))
        # Active match highlight (F4) — orange background
        self.tree.tag_configure('search_active', background='#ff9800', foreground='#000000',
                                font=('Segoe UI', 10, 'bold'))

        # Store data
        self.db_data = None
        self.qc_report = None

        # Search state (F1)
        self._search_index = []          # list[(iid, casefold_text)]
        self._original_tags = {}         # iid -> original tags tuple
        self._saved_open_state = None    # dict[iid] -> bool, set during active search
        self._highlighted_iids = set()   # iids currently carrying 'search_hit'

        # Navigation state (F4)
        self._search_matches = []        # ordered list of matching iids
        self._current_match_idx = -1     # index of active match (-1 = none)

        # Bind events
        self.tree.bind('<Double-1>', self.on_double_click)
    
    def clear(self):
        """Clear all items from tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def populate(self, db_data: Dict, qc_report: Optional[Dict] = None):
        """
        Populate tree with DB data and QC results
        
        Args:
            db_data: DB hierarchy from DBExtractor
            qc_report: QC report from Comparator (optional)
        """
        self.clear()
        self.db_data = db_data
        self.qc_report = qc_report
        
        if not db_data:
            return
        
        # Add instrument info as root
        instrument = db_data.get('instrument', 'Unknown')
        root_id = self.tree.insert('', 'end', 
            text=f"🔧 Instrument: {instrument}",
            open=True,
            tags=('module',))
        
        # Add modules
        for module in db_data.get('modules', []):
            self.add_module(root_id, module)

        # Build search index (F1)
        self._build_search_index()
    
    def add_module(self, parent_id: str, module: Dict):
        """Add module to tree"""
        module_name = module['name']
        part_count = len(module.get('parts', []))
        
        # Calculate module stats if QC report exists
        stats_str = ""
        if self.qc_report:
            stats = self.get_module_stats(module_name)
            if stats['total'] > 0:
                stats_str = f" [{stats['passed']}/{stats['total']} passed]"
        
        module_id = self.tree.insert(parent_id, 'end',
            text=f"▼ {module_name} ({part_count} parts){stats_str}",
            open=False,
            tags=('module',))
        
        # Add parts
        for part in module.get('parts', []):
            self.add_part(module_id, module_name, part)
    
    def add_part(self, parent_id: str, module_name: str, part: Dict):
        """Add part to tree"""
        part_type = part['type']
        part_name = part['name']
        item_count = len(part.get('items', []))
        
        # Calculate part stats
        stats_str = ""
        if self.qc_report:
            stats = self.get_part_stats(module_name, part_type, part_name)
            if stats['total'] > 0:
                stats_str = f" [{stats['passed']}/{stats['total']}]"
        
        part_id = self.tree.insert(parent_id, 'end',
            text=f"  ▼ {part_type}/{part_name} ({item_count} items){stats_str}",
            open=False,
            tags=('part',))
        
        # Add items
        for item in part.get('items', []):
            self.add_item(part_id, module_name, part_type, part_name, item)
    
    def add_item(self, parent_id: str, module_name: str, part_type: str, 
                 part_name: str, item: Dict):
        """Add item to tree with QC result"""
        item_name = item.get('name', '')
        item_value = item.get('value', '')
        item_type = item.get('value_type', '')
        
        # Find QC result
        result = None
        if self.qc_report:
            result = self.find_qc_result(module_name, part_type, part_name, item_name)
        
        # Determine display values
        status_icon = self.get_status_icon(result)
        status_text = result.get('status', 'NO_SPEC') if result else 'NO_SPEC'
        spec_text = self.format_spec(result.get('spec')) if result else '-'
        tag = self.get_status_tag(result)
        
        # Format value with type
        value_display = f"{item_value}"
        if item_type and item_value:
            if item_type in ['double', 'float', 'int']:
                value_display = f"{item_value}"
        
        # Insert item
        self.tree.insert(parent_id, 'end',
            text=f"    {status_icon} {item_name}",
            values=(value_display, spec_text, status_text),
            tags=(tag,))
    
    def find_qc_result(self, module: str, part_type: str, part_name: str, 
                       item_name: str) -> Optional[Dict]:
        """Find QC result for specific item"""
        if not self.qc_report:
            return None
        
        for result in self.qc_report.get('results', []):
            if (result['module'] == module and
                result['part_type'] == part_type and
                result['part_name'] == part_name and
                result['item_name'] == item_name):
                return result
        
        return None
    
    def get_status_icon(self, result: Optional[Dict]) -> str:
        """Get icon for status"""
        if not result:
            return '○'
        
        status = result.get('status', 'NO_SPEC')
        icon_map = {
            'PASS': '✓',
            'FAIL': '✗',
            'NO_SPEC': '○',
            'ERROR': '⚠',
            'SKIPPED': '⊘'
        }
        return icon_map.get(status, '?')
    
    def get_status_tag(self, result: Optional[Dict]) -> str:
        """Get tag name for status"""
        if not result:
            return 'no_spec'
        
        status = result.get('status', 'NO_SPEC')
        tag_map = {
            'PASS': 'pass',
            'FAIL': 'fail',
            'NO_SPEC': 'no_spec',
            'ERROR': 'error',
            'SKIPPED': 'skipped'
        }
        return tag_map.get(status, 'no_spec')
    
    def format_spec(self, spec: Optional[Dict]) -> str:
        """Format spec for display"""
        if not spec:
            return '-'
        
        validation_type = spec.get('validation_type', 'range')
        
        if validation_type == 'range':
            min_spec = spec.get('min_spec', '?')
            max_spec = spec.get('max_spec', '?')
            unit = spec.get('unit', '')
            return f"[{min_spec}, {max_spec}] {unit}".strip()
        elif validation_type == 'exact':
            expected = spec.get('expected_value', '?')
            unit = spec.get('unit', '')
            return f"= {expected} {unit}".strip()
        else:
            return '?'
    
    def get_module_stats(self, module_name: str) -> Dict:
        """Get statistics for a module"""
        stats = {'total': 0, 'passed': 0, 'failed': 0}
        
        if not self.qc_report:
            return stats
        
        for result in self.qc_report.get('results', []):
            if result['module'] == module_name:
                stats['total'] += 1
                if result['status'] == 'PASS':
                    stats['passed'] += 1
                elif result['status'] == 'FAIL':
                    stats['failed'] += 1
        
        return stats
    
    def get_part_stats(self, module_name: str, part_type: str, part_name: str) -> Dict:
        """Get statistics for a part"""
        stats = {'total': 0, 'passed': 0, 'failed': 0}
        
        if not self.qc_report:
            return stats
        
        for result in self.qc_report.get('results', []):
            if (result['module'] == module_name and
                result['part_type'] == part_type and
                result['part_name'] == part_name):
                stats['total'] += 1
                if result['status'] == 'PASS':
                    stats['passed'] += 1
                elif result['status'] == 'FAIL':
                    stats['failed'] += 1
        
        return stats
    
    def on_double_click(self, event):
        """Handle double-click on item"""
        # Disabled for simple view - use Profile Manager instead
        pass

    # ------------------------------------------------------------------
    # Search (F1)
    # ------------------------------------------------------------------

    def _build_search_index(self):
        """Build a flat search index over all visible nodes."""
        self._search_index = []
        self._original_tags = {}
        self._highlighted_iids = set()
        self._search_matches = []
        self._current_match_idx = -1
        # Reset open-state snapshot — fresh tree, fresh state
        self._saved_open_state = None

        def visit(parent_iid):
            for iid in self.tree.get_children(parent_iid):
                text = self.tree.item(iid, 'text') or ''
                self._search_index.append((iid, text.casefold()))
                self._original_tags[iid] = self.tree.item(iid, 'tags')
                visit(iid)
        visit('')

    def has_data(self) -> bool:
        """True if tree is populated and searchable."""
        return bool(self._search_index)

    def search(self, query: str) -> int:
        """Search nodes by substring; expand parents, highlight, scroll to first.

        Returns the number of matches. Empty query clears search and restores state.
        """
        query = (query or '').strip()

        if not query:
            self.clear_search()
            return 0

        # Snapshot open state on first search (so we can restore later)
        if self._saved_open_state is None:
            self._saved_open_state = {}
            def snapshot(parent_iid):
                for iid in self.tree.get_children(parent_iid):
                    self._saved_open_state[iid] = self.tree.item(iid, 'open')
                    snapshot(iid)
            snapshot('')

        # Clear previous highlights (without restoring open-state)
        self._clear_highlights_only()

        q = query.casefold()
        matches = [iid for iid, text in self._search_index if q in text]

        if not matches:
            return 0

        # Expand all ancestors of every match
        parents_to_open = set()
        for iid in matches:
            p = self.tree.parent(iid)
            while p:
                parents_to_open.add(p)
                p = self.tree.parent(p)
        for p in parents_to_open:
            try:
                self.tree.item(p, open=True)
            except Exception:
                pass

        # Apply 'search_hit' tag to all matches
        for iid in matches:
            try:
                self.tree.item(iid, tags=('search_hit',))
                self._highlighted_iids.add(iid)
            except Exception:
                pass

        # Store match list and activate first match
        self._search_matches = matches
        self._current_match_idx = 0
        self._goto_match(0)

        return len(matches)

    def _goto_match(self, idx: int):
        """Scroll to and highlight the match at idx as the active match."""
        if not self._search_matches:
            return
        idx = idx % len(self._search_matches)
        self._current_match_idx = idx

        # Remove search_active from previously active match
        for iid in list(self._highlighted_iids):
            try:
                current_tags = self.tree.item(iid, 'tags')
                if 'search_active' in current_tags:
                    self.tree.item(iid, tags=('search_hit',))
            except Exception:
                pass

        # Apply search_active to current match
        active_iid = self._search_matches[idx]
        try:
            self.tree.item(active_iid, tags=('search_active',))
            self.tree.see(active_iid)
            self.tree.selection_set(active_iid)
        except Exception:
            pass

    def next_match(self) -> tuple:
        """Move to next match (wraparound). Returns (current_1based, total)."""
        if not self._search_matches:
            return (0, 0)
        new_idx = (self._current_match_idx + 1) % len(self._search_matches)
        self._goto_match(new_idx)
        return (new_idx + 1, len(self._search_matches))

    def prev_match(self) -> tuple:
        """Move to previous match (wraparound). Returns (current_1based, total)."""
        if not self._search_matches:
            return (0, 0)
        new_idx = (self._current_match_idx - 1) % len(self._search_matches)
        self._goto_match(new_idx)
        return (new_idx + 1, len(self._search_matches))

    def _clear_highlights_only(self):
        """Remove search_hit tag from highlighted nodes, restore original tags."""
        for iid in list(self._highlighted_iids):
            try:
                original = self._original_tags.get(iid, ())
                self.tree.item(iid, tags=original)
            except Exception:
                pass
        self._highlighted_iids.clear()

    def clear_search(self):
        """Clear search highlights AND restore tree open-state to pre-search snapshot."""
        self._clear_highlights_only()
        self._search_matches = []
        self._current_match_idx = -1

        if self._saved_open_state is not None:
            for iid, was_open in self._saved_open_state.items():
                try:
                    self.tree.item(iid, open=was_open)
                except Exception:
                    pass
            self._saved_open_state = None

    def expand_all(self):
        """Expand all items in the tree"""
        def expand_recursive(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand_recursive(child)
        
        for item in self.tree.get_children():
            expand_recursive(item)

    def collapse_all(self):
        """Collapse all items in the tree"""
        def collapse_recursive(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                collapse_recursive(child)
        
        for item in self.tree.get_children():
            collapse_recursive(item)
