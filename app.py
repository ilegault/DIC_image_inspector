# app.py

import tkinter as tk
import logging

# === CHANGE DEBUG PRESET HERE ===
# Available presets: 'off', 'normal', 'debug', 'zoom_pan', 'verbose'
DEBUG_PRESET = 'normal'  # <-- Change this line to change debug level

# ===== DEBUG PRESETS REFERENCE =====
"""
Available Debug Presets:

'off'      - Only errors, minimal output
'normal'   - Standard operation (recommended for daily use)  
'debug'    - App debugging enabled, detailed console output
'zoom_pan' - Debug zoom/pan operations specifically  
'verbose'  - Everything at maximum debug level

Just change DEBUG_PRESET above and restart the app.
"""

# Apply debug configuration FIRST, before any other imports
from utils.debug_config import DebugPresets

DebugPresets.apply_preset(DEBUG_PRESET)

# Now import the rest
try:
    from ui.main_window import DICQualityInspector
except ImportError:
    from ui.main_window import DICQualityInspector


def main():
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info("Starting DIC Image Quality Inspector")

    root = tk.Tk()
    app = DICQualityInspector(root)
    root.mainloop()


if __name__ == "__main__":
    main()