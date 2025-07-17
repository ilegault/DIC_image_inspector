# app.py

import tkinter as tk
import logging

# Debug configuration
from utils.debug_config import DebugPresets
DebugPresets.apply_preset('zoom_pan')

# ===== DEBUG CONFIGURATION REFERENCE =====
"""
Debug Presets Quick Reference:

Usage: from utils.debug_config import DebugPresets
       DebugPresets.apply_preset('preset_name')

Available Presets:
┌────────────-─┬─────────────────────────────┬─────────────────────────────────────┐
│ Preset       │ What It Does                │ When To Use                         │
├────────────-─┼─────────────────────────────┼─────────────────────────────────────┤
│ 'off'        │ Only errors and warnings    │ When you want minimal output        │
│ 'normal'     │ Standard operation          │ **Recommended for daily use**       │
│ 'debug'      │ App debugging enabled       │ When troubleshooting app issues     │
│ 'verbose'    │ Everything at maximum       │ When you need to see everything     │
│ 'zoom_pan'   │ Debug zoom/pan operations   │ When zoom/pan is acting weird       │
│ 'images'     │ Debug image loading         │ When images won't load properly     │
│ 'performance'│ Debug performance issues    │ When the app is running slowly      │
└─────────────-┴─────────────────────────────┴─────────────────────────────────────┘

Quick Commands:
- DebugPresets.apply_preset('normal')    # Daily use
- DebugPresets.apply_preset('debug')     # Troubleshooting
- DebugControl.status()                  # Check current settings
- DebugControl.help()                    # Show all options

Individual Flags:
- DEBUG_MODE, VERBOSE_MODE, ZOOM_PAN_DEBUG, IMAGE_LOADING_DEBUG
- ROI_DEBUG, ANALYSIS_DEBUG, UI_DEBUG, PERFORMANCE_DEBUG
"""


try:
    # When run as a package
    from ui.main_window import DICQualityInspector
    from utils.debug_config import setup_logging
except ImportError:
    # For direct execution
    from ui.main_window import DICQualityInspector
    from utils.debug_config import setup_logging

def main():
    # Set up logging first using centralized configuration
    setup_logging()
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info("Starting DIC Image Quality Inspector")
    
    root = tk.Tk()
    app = DICQualityInspector(root)
    root.mainloop()

if __name__ == "__main__":
    main()