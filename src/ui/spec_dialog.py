"""
Spec Configuration Dialog
Dialog for setting QC specifications for an item
"""

import customtkinter as ctk
from typing import Dict, Optional

from src.utils.format_helpers import center_window_on_parent


class SpecConfigDialog(ctk.CTkToplevel):
    """
    Dialog to configure QC spec for a single item
    """
    
    def __init__(self, parent, item_name: str, current_value: str, current_spec: Optional[Dict] = None):
        super().__init__(parent)
        
        self.title(f"Configure Spec: {item_name}")
        self.geometry("400x600")
        self.resizable(False, False)
        
        self.result = None
        self.item_name = item_name
        self.current_value = current_value
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets(current_spec)
        center_window_on_parent(self, parent, 400, 600)
        
    def create_widgets(self, current_spec):
        """Create dialog widgets"""
        # Item Info
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            info_frame, 
            text="Item Name:", 
            font=("Segoe UI", 12, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        ctk.CTkLabel(
            info_frame, 
            text=self.item_name,
            font=("Segoe UI", 12)
        ).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        ctk.CTkLabel(
            info_frame, 
            text="Current Value:", 
            font=("Segoe UI", 12, "bold")
        ).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        ctk.CTkLabel(
            info_frame, 
            text=str(self.current_value),
            font=("Segoe UI", 12)
        ).grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Validation Type
        type_frame = ctk.CTkFrame(self)
        type_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            type_frame,
            text="Validation Type",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        self.type_var = ctk.StringVar(value="range")
        if current_spec:
            val_type = current_spec.get('validation_type')
            if val_type in ['exact', 'check']:
                self.type_var.set(val_type)
            
        self.range_radio = ctk.CTkRadioButton(
            type_frame,
            text="Range (Min/Max)",
            variable=self.type_var,
            value="range",
            command=self.update_fields
        )
        self.range_radio.pack(anchor="w", padx=20, pady=5)
        
        self.exact_radio = ctk.CTkRadioButton(
            type_frame,
            text="Exact Match",
            variable=self.type_var,
            value="exact",
            command=self.update_fields
        )
        self.exact_radio.pack(anchor="w", padx=20, pady=5)
        
        self.check_radio = ctk.CTkRadioButton(
            type_frame,
            text="Check (Value Only)",
            variable=self.type_var,
            value="check",
            command=self.update_fields
        )
        self.check_radio.pack(anchor="w", padx=20, pady=5)
        
        # Value Fields
        self.fields_frame = ctk.CTkFrame(self)
        self.fields_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Range Fields
        self.range_container = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
        
        ctk.CTkLabel(self.range_container, text="Min Spec (optional):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.min_entry = ctk.CTkEntry(self.range_container, width=150, placeholder_text="Leave empty for no minimum")
        self.min_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(self.range_container, text="Max Spec (optional):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.max_entry = ctk.CTkEntry(self.range_container, width=150, placeholder_text="Leave empty for no maximum")
        self.max_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Exact Fields
        self.exact_container = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
        
        ctk.CTkLabel(self.exact_container, text="Expected Value:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.expected_entry = ctk.CTkEntry(self.exact_container, width=150)
        self.expected_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Check Fields
        self.check_container = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
        
        ctk.CTkLabel(
            self.check_container,
            text="This validation type will only record the value\nwithout PASS/FAIL judgment.",
            font=("Segoe UI", 11),
            text_color="gray"
        ).pack(padx=10, pady=20)
        
        # Unit Field
        unit_frame = ctk.CTkFrame(self)
        unit_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(unit_frame, text="Unit (Optional):").pack(side="left", padx=10, pady=10)
        self.unit_entry = ctk.CTkEntry(unit_frame, width=100)
        self.unit_entry.pack(side="left", padx=10, pady=10)
        
        # Populate fields if spec exists
        if current_spec:
            self.unit_entry.insert(0, current_spec.get('unit', ''))
            
            if current_spec.get('validation_type') == 'range':
                self.min_entry.insert(0, str(current_spec.get('min_spec', '')))
                self.max_entry.insert(0, str(current_spec.get('max_spec', '')))
            elif current_spec.get('validation_type') == 'exact':
                self.expected_entry.insert(0, str(current_spec.get('expected_value', '')))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="gray",
            hover_color="#555555",
            command=self.destroy
        ).pack(side="right", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self.save
        ).pack(side="right", padx=10)
        
        # Initial update
        self.update_fields()
        
    def update_fields(self):
        """Show/hide fields based on type"""
        if self.type_var.get() == "range":
            self.exact_container.pack_forget()
            self.check_container.pack_forget()
            self.range_container.pack(fill="x", padx=10, pady=10)
        elif self.type_var.get() == "exact":
            self.range_container.pack_forget()
            self.check_container.pack_forget()
            self.exact_container.pack(fill="x", padx=10, pady=10)
        else:  # check
            self.range_container.pack_forget()
            self.exact_container.pack_forget()
            self.check_container.pack(fill="x", padx=10, pady=10)
            
    def save(self):
        """Save configuration"""
        from tkinter import messagebox
        
        spec = {
            'item_name': self.item_name,
            'validation_type': self.type_var.get(),
            'unit': self.unit_entry.get().strip(),
            'enabled': True
        }
        
        if self.type_var.get() == "range":
            min_val = self.min_entry.get().strip()
            max_val = self.max_entry.get().strip()
            
            # Allow empty values for single-sided range
            if not min_val and not max_val:
                messagebox.showerror("Error", "Please enter at least Min or Max value")
                return
            
            try:
                if min_val:
                    spec['min_spec'] = float(min_val)
                if max_val:
                    spec['max_spec'] = float(max_val)
            except ValueError:
                messagebox.showerror("Error", "Min/Max must be numeric values")
                return
        elif self.type_var.get() == "exact":
            spec['expected_value'] = self.expected_entry.get().strip()
        # 'check' type doesn't need additional fields
            
        self.result = spec
        self.destroy()
