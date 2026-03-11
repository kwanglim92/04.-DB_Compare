"""
Constants Module
Global constants, themes, and colors for the application
"""

APP_VERSION = "1.0.0"
APP_TITLE = "DB_Compare - QC Inspection Tool"
DEVELOPER_INFO = "Version {version}  |  Developed by Levi.Beak  |  Contact: levi.beak@parksystems.com"

# Appearance settings
APPEARANCE_MODE = "dark"
COLOR_THEME = "blue"

# UI Colors (Hex format for CustomTkinter/Tkinter)
COLORS = {
    # Status colors
    'pass_bg': '#e8f5e9',         # Light green background
    'pass_fg': '#1b5e20',         # Dark green text
    'pass_main': '#0d7d3d',       # Main green for charts/bars
    
    'fail_bg': '#ffebee',         # Light red background
    'fail_fg': '#c62828',         # Dark red text
    'fail_main': '#c62828',       # Main red for charts/bars
    
    'check_bg': '#e3f2fd',        # Light blue background
    'check_fg': '#1976d2',        # Blue text
    'check_main': '#1f6aa5',      # Main blue for charts/bars
    
    'pending_fg': 'gray50',       # Pending/Empty text
    
    # Generic warnings/accents
    'warning': '#ff9800',
    'accent_orange': '#ed6c02',
    'accent_orange_hover': '#c75c02',
    'accent_gray': '#555555',
    
    # Tree item headers
    'tree_module': '#1f6aa5',
    'tree_part_type': '#424242',
    'tree_part': '#666666'
}

# Excel export colors (aRGB format: Alpha + RGB)
EXCEL_COLORS = {
    'pass_bg': 'FFE8F5E9',
    'pass_text': 'FF1B5E20',
    'fail_bg': 'FFFFEBEE',
    'fail_text': 'FFC62828',
    'check_bg': 'FFE3F2FD',
    'check_text': 'FF1976D2',
    'header_bg': 'FFF5F5F5',
    'border': 'FFD9D9D9',
    'chart_pass': '0D7D3D',
    'chart_fail': 'C62828',
    'chart_check': '1F6AA5'
}
