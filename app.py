# app.py

import tkinter as tk
import logging

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