#!/usr/bin/env python3
"""
Window-specific capture solution.

Captures content of a specific window (camera UI) while ignoring all other windows.
Works on Windows using win32gui.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import cv2
import time
import threading
from PIL import Image, ImageTk
import logging
import platform

# Windows-specific imports
if platform.system() == 'Windows':
    import win32gui
    import win32ui
    import win32con
    import win32api
    from ctypes import windll

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WindowCapture:
    """Capture specific window content on Windows."""

    @staticmethod
    def list_windows():
        """List all visible windows."""
        windows = []

        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text:
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'class': win32gui.GetClassName(hwnd)
                    })

        win32gui.EnumWindows(enum_handler, None)
        return windows

    @staticmethod
    def capture_window(hwnd):
        """Capture content of specific window by handle."""
        try:
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # Get the window device context
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            # Create bitmap
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            # Copy window content
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)

            # Convert to numpy array
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            image = np.frombuffer(bmpstr, dtype='uint8')
            image.shape = (height, width, 4)

            # Clean up
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)

            # Convert BGRA to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)

            return image

        except Exception as e:
            logger.error(f"Error capturing window: {e}")
            return None

    @staticmethod
    def find_window_by_title(partial_title):
        """Find window handle by partial title match."""
        windows = WindowCapture.list_windows()
        for window in windows:
            if partial_title.lower() in window['title'].lower():
                return window['hwnd']
        return None


class SpecificWindowAnalyzer:
    """Analyzer that captures a specific window only."""

    def __init__(self):
        self.target_hwnd = None
        self.is_running = False
        self.thread = None

    def set_target_window(self, hwnd):
        """Set the window to capture."""
        self.target_hwnd = hwnd
        logger.info(f"Target window set: {hwnd}")

    def start(self, on_update=None):
        """Start capturing."""
        if not self.target_hwnd:
            raise ValueError("No target window set")

        self.is_running = True
        self.on_update = on_update

        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop capturing."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _capture_loop(self):
        """Main capture loop."""
        update_count = 0

        while self.is_running:
            try:
                # Capture specific window
                image = WindowCapture.capture_window(self.target_hwnd)

                if image is not None:
                    # Simple analysis
                    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                    score = np.std(gray) / 128.0

                    update_count += 1

                    if self.on_update:
                        self.on_update(image, score, update_count)
                else:
                    logger.warning("Failed to capture window")

                time.sleep(0.1)  # 10 FPS

            except Exception as e:
                logger.error(f"Capture error: {e}")
                time.sleep(0.5)


class WindowSpecificTestApp:
    """Test app for window-specific capture."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Window-Specific Capture (Camera UI Only)")
        self.root.geometry("900x700")

        self.analyzer = SpecificWindowAnalyzer()
        self.selected_hwnd = None

        self._create_ui()

    def _create_ui(self):
        """Create UI."""
        # Header
        header = tk.Frame(self.root, bg='#34495e', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🎯 Window-Specific Capture",
            font=('Arial', 20, 'bold'),
            bg='#34495e',
            fg='white'
        ).pack(expand=True)

        # Platform check
        if platform.system() != 'Windows':
            tk.Label(
                self.root,
                text="This solution requires Windows (uses win32gui)",
                font=('Arial', 14),
                fg='red'
            ).pack(pady=50)
            return

        # Window list
        list_frame = tk.LabelFrame(
            self.root,
            text="Available Windows",
            font=('Arial', 12, 'bold')
        )
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Refresh button
        tk.Button(
            list_frame,
            text="🔄 Refresh Window List",
            command=self._refresh_windows,
            bg='#3498db',
            fg='white'
        ).pack(pady=5)

        # Window listbox with scrollbar
        list_container = tk.Frame(list_frame)
        list_container.pack(fill='both', expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side='right', fill='y')

        self.window_listbox = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 10),
            height=10
        )
        self.window_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.window_listbox.yview)

        self.window_listbox.bind('<<ListboxSelect>>', self._on_window_select)

        # Info
        info_frame = tk.LabelFrame(
            self.root,
            text="How it works",
            font=('Arial', 12, 'bold')
        )
        info_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(
            info_frame,
            text="""This captures ONLY the content of your selected camera UI window.
All other windows (including analysis windows) are completely ignored!
You can see all your analysis windows while capturing clean content.""",
            justify='left',
            font=('Arial', 10)
        ).pack(padx=20, pady=10)

        # Controls
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        self.start_btn = tk.Button(
            control_frame,
            text="▶️ Start Capture",
            command=self._start_capture,
            bg='#27ae60',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10,
            state='disabled'
        )
        self.start_btn.pack(side='left', padx=10)

        self.stop_btn = tk.Button(
            control_frame,
            text="⏹️ Stop",
            command=self._stop_capture,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=10)

        # Preview
        preview_frame = tk.LabelFrame(
            self.root,
            text="Capture Preview",
            font=('Arial', 12, 'bold')
        )
        preview_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.preview_canvas = tk.Canvas(preview_frame, bg='black')
        self.preview_canvas.pack(fill='both', expand=True)
        self.preview_image_item = None

        # Status
        self.status_var = tk.StringVar(value="Select a window to capture")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=('Arial', 11),
            fg='#2c3e50'
        ).pack(pady=5)

        # Initial refresh
        self._refresh_windows()

    def _refresh_windows(self):
        """Refresh window list."""
        self.window_listbox.delete(0, tk.END)

        windows = WindowCapture.list_windows()
        self.window_data = {}

        for window in windows:
            # Filter out some system windows
            if window['title'] and 'Default IME' not in window['title']:
                display_text = f"{window['title']} [{window['class']}]"
                self.window_listbox.insert(tk.END, display_text)
                self.window_data[display_text] = window

        self.status_var.set(f"Found {len(self.window_data)} windows")

    def _on_window_select(self, event):
        """Handle window selection."""
        selection = self.window_listbox.curselection()
        if selection:
            index = selection[0]
            selected_text = self.window_listbox.get(index)

            if selected_text in self.window_data:
                window = self.window_data[selected_text]
                self.selected_hwnd = window['hwnd']
                self.analyzer.set_target_window(self.selected_hwnd)

                self.start_btn.config(state='normal')
                self.status_var.set(f"Selected: {window['title']}")

                # Try to preview
                self._preview_window()

    def _preview_window(self):
        """Preview the selected window."""
        if self.selected_hwnd:
            image = WindowCapture.capture_window(self.selected_hwnd)
            if image is not None:
                self._update_preview(image)

    def _start_capture(self):
        """Start capturing selected window."""
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        self.analyzer.start(on_update=self._on_update)

        self.status_var.set("Capturing window content - all other windows ignored!")

    def _on_update(self, image, score, count):
        """Handle capture update."""
        # Update preview
        self._update_preview(image)

        # Update status
        if count % 10 == 0:
            self.status_var.set(f"Capturing - Frame #{count} - Score: {score:.3f}")

    def _update_preview(self, image):
        """Update preview canvas."""
        try:
            # Get canvas size
            canvas_w = self.preview_canvas.winfo_width()
            canvas_h = self.preview_canvas.winfo_height()

            if canvas_w > 1 and canvas_h > 1:
                # Resize image to fit
                h, w = image.shape[:2]
                scale = min(canvas_w / w, canvas_h / h) * 0.9

                new_w = int(w * scale)
                new_h = int(h * scale)

                resized = cv2.resize(image, (new_w, new_h))

                # Convert to PhotoImage
                pil_image = Image.fromarray(resized)
                photo = ImageTk.PhotoImage(pil_image)

                # Update canvas
                if self.preview_image_item is None:
                    self.preview_image_item = self.preview_canvas.create_image(
                        canvas_w // 2, canvas_h // 2,
                        image=photo,
                        anchor='center'
                    )
                else:
                    self.preview_canvas.itemconfig(self.preview_image_item, image=photo)

                # Keep reference
                self.preview_canvas.image = photo

        except Exception as e:
            logger.error(f"Error updating preview: {e}")

    def _stop_capture(self):
        """Stop capture."""
        self.analyzer.stop()

        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

        self.status_var.set("Capture stopped")

    def run(self):
        """Run the app."""
        self.root.mainloop()


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("WINDOW-SPECIFIC CAPTURE SOLUTION")
    print("=" * 70)
    print("This captures ONLY the camera UI window content")
    print("All other windows are completely ignored!")
    print("=" * 70)

    if platform.system() != 'Windows':
        print("\nNOTE: This solution requires Windows (uses win32gui)")
        print("For cross-platform, use the multi-monitor solution instead")
    else:
        print("\nRequires: pip install pywin32 pillow opencv-python")

    print("=" * 70 + "\n")

    app = WindowSpecificTestApp()
    app.run()


if __name__ == "__main__":
    main()