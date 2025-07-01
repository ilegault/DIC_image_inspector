# ui/dialogs/screenshot_dialog.py - Screenshot Capture Dialog

import tkinter as tk
from PIL import ImageGrab
import numpy as np
from typing import Callable, Optional
from utils.constants import APP_CONFIG


class ScreenshotDialog:
    """
    Screenshot capture dialog for capturing screen regions.

    Provides fullscreen overlay for selecting screen regions to capture.
    Follows single responsibility principle - only screenshot capture.
    """

    def __init__(self, parent: tk.Widget, callback: Callable[[Optional[np.ndarray]], None]):
        """
        Initialize screenshot dialog.

        Args:
            parent: Parent widget
            callback: Function to call with captured image data
        """
        self.parent = parent
        self.callback = callback
        self.screenshot_window = None
        self.selection_canvas = None

        # Selection state
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.selecting = False

    def show(self):
        """Show the screenshot capture overlay."""
        try:
            self._setup_dpi_awareness()
            self._create_screenshot_overlay()
            self._bind_events()

        except Exception as e:
            print(f"Error showing screenshot dialog: {e}")
            self._cleanup_and_callback(None)

    def _setup_dpi_awareness(self):
        """Setup DPI awareness for consistent coordinates."""
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            # Not on Windows or ctypes not available
            pass

    def _create_screenshot_overlay(self):
        """Create fullscreen overlay for screenshot selection."""
        # Create fullscreen window
        self.screenshot_window = tk.Toplevel(self.parent)
        self.screenshot_window.attributes('-fullscreen', True)
        self.screenshot_window.attributes('-alpha', 0.3)
        self.screenshot_window.configure(bg='black')
        self.screenshot_window.attributes('-topmost', True)

        # Instructions label
        instructions = tk.Label(
            self.screenshot_window,
            text="Click and drag to select a screen region, or press ESC to cancel",
            font=('Arial', 16),
            fg="white",
            bg="black"
        )
        instructions.pack(expand=True)

        # Create canvas for drawing selection rectangle
        self.selection_canvas = tk.Canvas(
            self.screenshot_window,
            highlightthickness=0,
            bg='black'
        )
        self.selection_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Force focus
        self.screenshot_window.focus_force()
        self.screenshot_window.grab_set()
        self.screenshot_window.update()

    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Mouse events for selection
        self.selection_canvas.bind("<Button-1>", self._start_selection)
        self.selection_canvas.bind("<B1-Motion>", self._update_selection)
        self.selection_canvas.bind("<ButtonRelease-1>", self._end_selection)

        # Keyboard events for cancellation
        self.screenshot_window.bind('<Escape>', self._cancel_screenshot)
        self.selection_canvas.bind('<Escape>', self._cancel_screenshot)

        # Bind at application level to ensure ESC is captured
        self.screenshot_window.bind_all('<Escape>', self._cancel_screenshot)

    def _start_selection(self, event):
        """Start selection rectangle."""
        self.start_x = event.x
        self.start_y = event.y
        self.selecting = True

        # Clear any existing rectangle
        if self.rect_id:
            self.selection_canvas.delete(self.rect_id)
            self.rect_id = None

    def _update_selection(self, event):
        """Update selection rectangle during drag."""
        if not self.selecting:
            return

        # Clear previous rectangle
        if self.rect_id:
            self.selection_canvas.delete(self.rect_id)

        # Draw new rectangle
        self.rect_id = self.selection_canvas.create_rectangle(
            self.start_x, self.start_y,
            event.x, event.y,
            outline='red',
            width=3
        )

    def _end_selection(self, event):
        """End selection and capture screenshot."""
        if not self.selecting:
            return

        self.selecting = False

        # Calculate selection coordinates
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)

        # Check if selection is large enough
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            self._capture_screenshot(x1, y1, x2, y2)
        else:
            print("Screenshot area too small")
            self._cleanup_and_callback(None)

    def _capture_screenshot(self, x1: int, y1: int, x2: int, y2: int):
        """
        Capture screenshot of selected area.

        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
        """
        try:
            print(f"Capturing screenshot: ({x1},{y1}) to ({x2},{y2})")

            # Capture screenshot
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            if screenshot:
                # Convert to numpy array
                image_array = np.array(screenshot)
                print(f"Screenshot captured: {image_array.shape}")
                self._cleanup_and_callback(image_array)
            else:
                print("Failed to capture screenshot")
                self._cleanup_and_callback(None)

        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            self._cleanup_and_callback(None)

    def _cancel_screenshot(self, event=None):
        """Cancel screenshot capture."""
        print("Screenshot cancelled")
        self._cleanup_and_callback(None)
        return "break"

    def _cleanup_and_callback(self, image_data: Optional[np.ndarray]):
        """
        Clean up screenshot window and call callback.

        Args:
            image_data: Captured image data or None if cancelled/failed
        """
        try:
            # Destroy screenshot window
            if self.screenshot_window:
                self.screenshot_window.destroy()
                self.screenshot_window = None

            # Call callback with result
            if self.callback:
                self.callback(image_data)

        except Exception as e:
            print(f"Error in cleanup: {e}")

    def is_active(self) -> bool:
        """Check if screenshot dialog is currently active."""
        return (self.screenshot_window is not None and
                self.screenshot_window.winfo_exists())

    def force_close(self):
        """Force close the screenshot dialog."""
        if self.screenshot_window:
            try:
                self.screenshot_window.destroy()
            except:
                pass
            self.screenshot_window = None


class SimpleScreenshotCapture:
    """
    Simplified screenshot capture without overlay.

    Alternative implementation for systems where fullscreen overlay
    might not work properly.
    """

    @staticmethod
    def capture_full_screen() -> Optional[np.ndarray]:
        """
        Capture full screen without user selection.

        Returns:
            Full screen image as numpy array or None if failed
        """
        try:
            screenshot = ImageGrab.grab()
            if screenshot:
                return np.array(screenshot)
        except Exception as e:
            print(f"Error capturing full screen: {e}")
        return None

    @staticmethod
    def capture_with_delay(delay_seconds: int = 3) -> Optional[np.ndarray]:
        """
        Capture full screen after a delay.

        Args:
            delay_seconds: Delay before capture

        Returns:
            Screen image as numpy array or None if failed
        """
        import time
        try:
            time.sleep(delay_seconds)
            return SimpleScreenshotCapture.capture_full_screen()
        except Exception as e:
            print(f"Error in delayed capture: {e}")
        return None


class ScreenshotHelper:
    """
    Helper class for screenshot operations.

    Provides utility methods for screenshot handling.
    """

    @staticmethod
    def validate_screenshot_area(x1: int, y1: int, x2: int, y2: int) -> bool:
        """
        Validate screenshot area coordinates.

        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner

        Returns:
            True if area is valid
        """
        # Check minimum size
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        min_size = APP_CONFIG.get('screenshot', {}).get('min_size', 10)

        return width >= min_size and height >= min_size

    @staticmethod
    def get_screen_dimensions() -> tuple[int, int]:
        """
        Get screen dimensions.

        Returns:
            Tuple of (width, height)
        """
        try:
            # Try to get screen size using tkinter
            root = tk.Tk()
            root.withdraw()  # Hide the window

            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()

            root.destroy()

            return width, height

        except Exception:
            # Fallback to reasonable defaults
            return 1920, 1080

    @staticmethod
    def optimize_screenshot_quality(image_array: np.ndarray) -> np.ndarray:
        """
        Optimize screenshot for DIC analysis.

        Args:
            image_array: Input screenshot array

        Returns:
            Optimized image array
        """
        try:
            # Convert to grayscale if needed for DIC analysis
            if len(image_array.shape) == 3:
                # Keep as RGB for now, conversion will happen in analysis
                return image_array
            else:
                return image_array

        except Exception as e:
            print(f"Error optimizing screenshot: {e}")
            return image_array

    @staticmethod
    def save_screenshot_metadata(image_array: np.ndarray) -> dict:
        """
        Create metadata for screenshot.

        Args:
            image_array: Screenshot image array

        Returns:
            Metadata dictionary
        """
        from datetime import datetime

        return {
            'capture_time': datetime.now().isoformat(),
            'dimensions': image_array.shape,
            'source': 'screenshot',
            'capture_method': 'screen_selection'
        }