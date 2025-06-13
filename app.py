# app.py

import tkinter as tk

try:
    # When run as a package
    from ui.main_window import DICQualityInspector
except ImportError:
    # For direct execution
    from ui.main_window import DICQualityInspector

def main():
    root = tk.Tk()
    app = DICQualityInspector(root)
    root.mainloop()

if __name__ == "__main__":
    main()