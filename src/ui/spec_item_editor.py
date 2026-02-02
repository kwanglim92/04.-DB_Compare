"""
Spec Item Editor Dialog
Quick edit dialog for modifying spec values in Profile Manager
"""

import customtkinter as ctk
from tkinter import messagebox
import logging

logger = logging.getLogger(__name__)


class SpecItemEditorDialog(ctk.CTkToplevel):
    """Quick edit dialog for single spec item"""
    
    def __init__(self, parent, module, part_type, part, item_name, spec_data):
        super().__init__(parent)
        
        self.title("Edit Spec Item")
        self.geometry("450x500")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Store data
        self.module = module
        self.part_type = part_type
        self.part = part
        self.item_name = item_name
        self.spec_data = spec_data.copy()
        self.result = None
        
        # Create UI
        self.create_widgets()
        
        # Center on parent
        self.center_on_parent(parent)
        
    def center_on_parent(self, parent):
        """Center dialog on parent window"""
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (450 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.geometry(f"+{x}+{y}")
        
    def create_widgets(self):
        """Create dialog widgets"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="Edit Specification",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=15)
        
        # === Scrollable content area ===
        scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        scrollable_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        # === Item Information (Read-only) ===
        info_frame = ctk.CTkFrame(scrollable_frame)
        info_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="Item Information",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Item details
        items = [
            ("Module:", self.module),
            ("Part Type:", self.part_type),
            ("Part:", self.part),
            ("Item:", self.item_name)
        ]
        
        for label, value in items:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkLabel(
                row,
                text=label,
                font=("Segoe UI", 11, "bold"),
                width=100,
                anchor="w"
            ).pack(side="left")
            
            ctk.CTkLabel(
                row,
                text=value,
                font=("Segoe UI", 11),
                text_color="gray",
                anchor="w"
            ).pack(side="left", padx=5)
        
        # === Specification Editing ===
        spec_frame = ctk.CTkFrame(scrollable_frame)
        spec_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(
            spec_frame,
            text="Specification",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Validation type selection
        self.val_type_var = ctk.StringVar(
            value=self.spec_data.get('validation_type', 'range')
        )
        
        # Validation Type label
        ctk.CTkLabel(
            spec_frame,
            text="Validation Type",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Radio buttons - vertical layout
        ctk.CTkRadioButton(
            spec_frame,
            text="Range (Min/Max)",
            variable=self.val_type_var,
            value="range",
            command=self.on_type_change,
            font=("Segoe UI", 12)
        ).pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkRadioButton(
            spec_frame,
            text="Exact Match",
            variable=self.val_type_var,
            value="exact",
            command=self.on_type_change,
            font=("Segoe UI", 12)
        ).pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkRadioButton(
            spec_frame,
            text="Check (Value Only)",
            variable=self.val_type_var,
            value="check",
            command=self.on_type_change,
            font=("Segoe UI", 12)
        ).pack(anchor="w", padx=20, pady=5)
        
        # === Range inputs ===
        self.range_frame = ctk.CTkFrame(spec_frame, fg_color="transparent")
        self.range_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            self.range_frame,
            text="Min Spec (optional):",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=2)
        
        self.min_entry = ctk.CTkEntry(
            self.range_frame,
            width=300,
            font=("Segoe UI", 12),
            height=35,
            placeholder_text="Leave empty for no minimum"
        )
        self.min_entry.pack(anchor="w", pady=2)
        self.min_entry.insert(0, str(self.spec_data.get('min_spec', '')))
        
        ctk.CTkLabel(
            self.range_frame,
            text="Max Spec (optional):",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(15, 2))
        
        self.max_entry = ctk.CTkEntry(
            self.range_frame,
            width=300,
            font=("Segoe UI", 12),
            height=35,
            placeholder_text="Leave empty for no maximum"
        )
        self.max_entry.pack(anchor="w", pady=2)
        self.max_entry.insert(0, str(self.spec_data.get('max_spec', '')))
        
        # === Exact input ===
        self.exact_frame = ctk.CTkFrame(spec_frame, fg_color="transparent")
        self.exact_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            self.exact_frame,
            text="Expected Value:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=2)
        
        self.exact_entry = ctk.CTkEntry(
            self.exact_frame,
            width=300,
            font=("Segoe UI", 12),
            height=35
        )
        self.exact_entry.pack(anchor="w", pady=2)
        self.exact_entry.insert(0, str(self.spec_data.get('expected_value', '')))
        
        # === Check frame ===
        self.check_frame = ctk.CTkFrame(spec_frame, fg_color="transparent")
        self.check_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            self.check_frame,
            text="This validation type will only record the value\nwithout PASS/FAIL judgment.",
            font=("Segoe UI", 11),
            text_color="gray"
        ).pack(anchor="w", pady=20)
        
        # === Unit ===
        unit_container = ctk.CTkFrame(spec_frame, fg_color="transparent")
        unit_container.pack(fill="x", padx=10, pady=(15, 10))
        
        ctk.CTkLabel(
            unit_container,
            text="Unit:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=2)
        
        self.unit_entry = ctk.CTkEntry(
            unit_container,
            width=300,
            font=("Segoe UI", 12),
            height=35
        )
        self.unit_entry.pack(anchor="w", pady=2)
        self.unit_entry.insert(0, self.spec_data.get('unit', ''))
        
        # Add some padding at bottom of scrollable area
        ctk.CTkFrame(scrollable_frame, height=20, fg_color="transparent").pack()
        
        # === Buttons (Fixed at bottom, outside scroll) ===
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.on_cancel,
            fg_color="#d32f2f",
            hover_color="#b71c1c",
            width=120,
            height=40,
            font=("Segoe UI", 12, "bold")
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self.on_save,
            fg_color="#2fa572",
            hover_color="#248f5f",
            width=120,
            height=40,
            font=("Segoe UI", 12, "bold")
        ).pack(side="right", padx=5)
        
        # Initialize visibility
        self.on_type_change()
    
    def on_type_change(self):
        """Toggle between range, exact, and check inputs"""
        val_type = self.val_type_var.get()
        
        if val_type == "range":
            self.range_frame.pack(fill="x", padx=10, pady=5)
            self.exact_frame.pack_forget()
            self.check_frame.pack_forget()
        elif val_type == "exact":
            self.exact_frame.pack(fill="x", padx=10, pady=5)
            self.range_frame.pack_forget()
            self.check_frame.pack_forget()
        else:  # check
            self.check_frame.pack(fill="x", padx=10, pady=5)
            self.range_frame.pack_forget()
            self.exact_frame.pack_forget()
    
    def on_save(self):
        """Validate and save changes"""
        try:
            validation_type = self.val_type_var.get()
            
            result = {
                'item_name': self.item_name,
                'validation_type': validation_type,
                'unit': self.unit_entry.get().strip()
            }
            
            if validation_type == 'range':
                min_val = self.min_entry.get().strip()
                max_val = self.max_entry.get().strip()
                
                # Allow empty values for single-sided range
                if not min_val and not max_val:
                    messagebox.showerror(
                        "Validation Error",
                        "Please enter at least Min or Max value for Range validation."
                    )
                    return
                
                try:
                    if min_val:
                        result['min_spec'] = float(min_val)
                    if max_val:
                        result['max_spec'] = float(max_val)
                except ValueError:
                    messagebox.showerror(
                        "Validation Error",
                        "Min and Max values must be numeric."
                    )
                    return
                    
            elif validation_type == 'exact':
                expected = self.exact_entry.get().strip()
                
                if not expected:
                    messagebox.showerror(
                        "Validation Error",
                        "Please enter Expected Value for Exact validation."
                    )
                    return
                
                result['expected_value'] = expected
            # 'check' type doesn't need additional fields
            
            self.result = result
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{str(e)}")
            logger.error(f"Save error: {e}", exc_info=True)
    
    def on_cancel(self):
        """Cancel without saving"""
        self.result = None
        self.destroy()
