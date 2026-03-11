"""
Format Helpers Module
Common formatting and UI utility functions
"""

from typing import Dict, Optional

def format_spec(spec: Optional[Dict]) -> str:
    """
    Format specification dictionary into a readable string
    
    Args:
        spec: Specification dictionary
        
    Returns:
        Formatted string (e.g., "[10, 20]", "= 5", "?")
    """
    if not spec:
        return ""
        
    val_type = spec.get('validation_type', '').lower()
    
    if val_type == 'range':
        min_val = spec.get('min_spec', '?')
        max_val = spec.get('max_spec', '?')
        
        # Format gracefully for single-sided limits (optional enhancement)
        if min_val == '?' and max_val != '?':
            return f"<= {max_val}"
        elif min_val != '?' and max_val == '?':
            return f">= {min_val}"
            
        return f"[{min_val}, {max_val}]"
        
    elif val_type == 'exact':
        expected = spec.get('expected_value', '?')
        return f"= {expected}"
        
    elif val_type == 'check':
        return "Record Only"
        
    else:
        return "?"

def center_window_on_parent(window, parent, width: int = None, height: int = None):
    """
    Center a Toplevel window on its parent window
    
    Args:
        window: The Toplevel window to center
        parent: The parent window to center relative to
        width: Optional forced width (uses current width if None)
        height: Optional forced height (uses current height if None)
    """
    window.update_idletasks()
    
    w = width if width is not None else window.winfo_width()
    h = height if height is not None else window.winfo_height()
    
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (h // 2)
    
    window.geometry(f"+{x}+{y}")
