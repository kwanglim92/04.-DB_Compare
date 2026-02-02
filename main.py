#!/usr/bin/env python3
"""
DB_Compare QC Inspection Tool
Main entry point
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.main_window import main

if __name__ == "__main__":
    main()
