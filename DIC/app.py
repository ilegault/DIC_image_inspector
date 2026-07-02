"""
Main application entry point for DIC Image Quality Inspector.

This module initializes and launches the DIC Image Quality Inspector application,
a comprehensive tool for analyzing Digital Image Correlation (DIC) image quality.
It provides various quality metrics including contrast, gradient, entropy, and
speckle pattern analysis to assess the suitability of images for DIC measurements.

Usage:
    python app.py

Configuration:
    Adjust DEBUG_PRESET below to control logging verbosity:
    - 'off': Only errors
    - 'normal': Standard operation (recommended)
    - 'debug': Detailed console output
    - 'zoom_pan': Debug zoom/pan operations
    - 'verbose': Maximum debug level
"""

import tkinter as tk
import logging

# === CHANGE DEBUG PRESET HERE ===
# Available presets: 'off', 'normal', 'debug', 'zoom_pan', 'verbose'
DEBUG_PRESET = 'normal'  # <-- Change this line to change debug level

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