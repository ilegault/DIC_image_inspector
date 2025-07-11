# ui/dialogs/screenshot_dialog.py - Screenshot Capture Dialog

import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab
import numpy as np
from typing import Callable, Optional
from utils.constants import APP_CONFIG
import time


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
        self.main_window_hidden = False
        self.screen_photo = None  # For storing screen capture PhotoImage

        # Selection state
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.selecting = False

    def show(self):
        """Show the screenshot capture options."""
        try:
            print("Screenshot dialog: Starting...")
            self._setup_dpi_awareness()
            self._show_screenshot_options()
            print("Screenshot dialog: Options dialog should be visible now")

        except Exception as e:
            print(f"Error showing screenshot dialog: {e}")
            import traceback
            traceback.print_exc()
            self._cleanup_and_callback(None)

    def _show_screenshot_options(self):
        """Show screenshot options dialog."""
        # Create options dialog
        options_window = tk.Toplevel(self.parent)
        options_window.title("Screenshot Options")
        options_window.geometry("450x280")
        options_window.resizable(False, False)
        options_window.transient(self.parent)
        options_window.grab_set()

        # Make sure it appears on top
        options_window.attributes('-topmost', True)
        options_window.lift()
        options_window.focus_force()

        # Center the window
        options_window.update_idletasks()
        x = (options_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (options_window.winfo_screenheight() // 2) - (280 // 2)
        options_window.geometry(f"450x280+{x}+{y}")

        # Set background color
        options_window.configure(bg='#f0f0f0')

        # Title
        title_label = tk.Label(
            options_window,
            text=" Choose Screenshot Method",
            font=('Arial', 16, 'bold'),
            bg='#f0f0f0',
            fg='#333333'
        )
        title_label.pack(pady=20)

        # Description
        desc_label = tk.Label(
            options_window,
            text="Select how you want to capture your screenshot:",
            font=('Arial', 11),
            bg='#f0f0f0',
            fg='#666666'
        )
        desc_label.pack(pady=(0, 15))

        # Buttons frame
        buttons_frame = tk.Frame(options_window, bg='#f0f0f0')
        buttons_frame.pack(expand=True, fill='both', padx=30, pady=10)

        # Full screen button with description
        full_screen_frame = tk.Frame(buttons_frame, bg='#f0f0f0')
        full_screen_frame.pack(fill='x', pady=8)

        full_screen_btn = tk.Button(
            full_screen_frame,
            text=" Capture Full Screen",
            font=('Arial', 12, 'bold'),
            bg='#10b981',
            fg='white',
            relief='flat',
            padx=20,
            pady=12,
            cursor='hand2',
            command=lambda: self._capture_full_screen_and_close(options_window)
        )
        full_screen_btn.pack(fill='x')

        full_desc = tk.Label(
            full_screen_frame,
            text="Captures entire screen, then use ROI selector in app",
            font=('Arial', 9),
            bg='#f0f0f0',
            fg='#888888'
        )
        full_desc.pack(pady=(2, 0))

        # Select region button with description
        region_frame = tk.Frame(buttons_frame, bg='#f0f0f0')
        region_frame.pack(fill='x', pady=8)

        select_region_btn = tk.Button(
            region_frame,
            text=" Select Screen Region",
            font=('Arial', 12, 'bold'),
            bg='#3b82f6',
            fg='white',
            relief='flat',
            padx=20,
            pady=12,
            cursor='hand2',
            command=lambda: self._start_region_selection(options_window)
        )
        select_region_btn.pack(fill='x')

        region_desc = tk.Label(
            region_frame,
            text="Click and drag to select specific area (Recommended)",
            font=('Arial', 9),
            bg='#f0f0f0',
            fg='#888888'
        )
        region_desc.pack(pady=(2, 0))

        # Cancel button
        cancel_btn = tk.Button(
            buttons_frame,
            text=" Cancel",
            font=('Arial', 11),
            bg='#6b7280',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=lambda: self._cancel_and_close(options_window)
        )
        cancel_btn.pack(fill='x', pady=(15, 5))

        # Focus on select region button by default (recommended option)
        select_region_btn.focus_set()

        # Keyboard shortcuts
        options_window.bind('<Escape>', lambda e: self._cancel_and_close(options_window))
        options_window.bind('<Return>', lambda e: self._start_region_selection(options_window))
        options_window.bind('<F>', lambda e: self._capture_full_screen_and_close(options_window))
        options_window.bind('<f>', lambda e: self._capture_full_screen_and_close(options_window))
        options_window.bind('<R>', lambda e: self._start_region_selection(options_window))
        options_window.bind('<r>', lambda e: self._start_region_selection(options_window))

        # Add keyboard shortcut hints
        shortcut_label = tk.Label(
            options_window,
            text="Shortcuts: Enter/R = Region, F = Full Screen, Esc = Cancel",
            font=('Arial', 8),
            bg='#f0f0f0',
            fg='#999999'
        )
        shortcut_label.pack(side='bottom', pady=5)

    def _capture_full_screen_and_close(self, options_window):
        """Capture full screen and close options window."""
        options_window.destroy()
        self._hide_main_window()
        # Longer delay to ensure window is fully hidden before capture
        self.parent.after(300, self._capture_full_screen)

    def _start_region_selection(self, options_window):
        """Start region selection and close options window."""
        options_window.destroy()
        self._hide_main_window()
        # Small delay to ensure window is hidden
        self.parent.after(100, self._start_region_selection_delayed)

    def _start_region_selection_delayed(self):
        """Start region selection after main window is hidden."""
        # Hide the main window completely during region selection
        self._hide_main_window()
        # Additional delay to ensure window is fully hidden before screen capture
        self.parent.after(400, self._create_screenshot_overlay_and_bind)

    def _create_screenshot_overlay_and_bind(self):
        """Create overlay and bind events after ensuring main window is hidden."""
        self._create_screenshot_overlay()
        self._bind_events()

    def _cancel_and_close(self, options_window):
        """Cancel screenshot and close options window."""
        options_window.destroy()
        self._cleanup_and_callback(None)

    def _hide_main_window(self):
        """Hide the main window completely for clean screenshot capture."""
        try:
            # Find the root window (main application window)
            root = self.parent
            while root.master:
                root = root.master

            # Hide the main window completely
            root.withdraw()

            # Also hide any other toplevel windows that might be visible
            for widget in root.winfo_children():
                if isinstance(widget, tk.Toplevel) and widget.winfo_viewable():
                    widget.withdraw()

            # Force update to ensure window is hidden
            root.update_idletasks()
            root.update()

            self.main_window_hidden = True
            print("Main window hidden for clean screenshot")

        except Exception as e:
            print(f"Warning: Could not hide main window: {e}")

    def _capture_full_screen(self):
        """Capture the entire screen without user selection."""
        try:
            print("Capturing full screen...")

            # Get all monitors and capture the entire virtual screen
            screenshot = ImageGrab.grab(all_screens=True)

            if screenshot:
                # Convert to numpy array
                image_array = np.array(screenshot)
                print(f"Full screen captured: {image_array.shape}")
                self._cleanup_and_callback(image_array)
            else:
                print("Failed to capture full screen")
                self._cleanup_and_callback(None)

        except Exception as e:
            print(f"Error capturing full screen: {e}")
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
        """Create fullscreen overlay showing actual screen content without app window."""
        print("Creating screenshot overlay with clean screen content...")

        # First, capture the current screen (now that main window is hidden)
        try:
            from PIL import ImageGrab, ImageTk
            import time

            # Small delay to ensure main window is fully hidden before capture
            time.sleep(0.1)

            # Capture the entire screen (should now be clean without app window)
            screen_image = ImageGrab.grab(all_screens=True)

            # Create fullscreen window
            self.screenshot_window = tk.Toplevel()  # Don't parent to main window
            self.screenshot_window.attributes('-fullscreen', True)
            self.screenshot_window.attributes('-topmost', True)
            self.screenshot_window.configure(bg='black')

            # Convert PIL image to PhotoImage for tkinter
            self.screen_photo = ImageTk.PhotoImage(screen_image)

            # Create canvas and display the screen capture as background
            self.selection_canvas = tk.Canvas(
                self.screenshot_window,
                highlightthickness=0,
                bg='black'
            )
            self.selection_canvas.place(x=0, y=0, relwidth=1, relheight=1)

            # Display the clean screen capture as background
            self.selection_canvas.create_image(
                0, 0,
                anchor='nw',
                image=self.screen_photo,
                tags="background"
            )

            # Create instructions overlay (keep this as requested)
            instructions_frame = tk.Frame(
                self.screenshot_window,
                bg='#1f2937',
                relief='solid',
                bd=1
            )
            instructions_frame.place(x=20, y=20)

            instructions = tk.Label(
                instructions_frame,
                text=" CLICK and DRAG to select region • ESC to cancel • Right-click to cancel",
                font=('Segoe UI', 12, 'bold'),
                fg="#ffffff",
                bg="#1f2937",
                padx=20,
                pady=10
            )
            instructions.pack()

            # Set crosshair cursor
            self.selection_canvas.config(cursor="crosshair")

            # Force focus and grab all input
            self.screenshot_window.focus_force()
            self.screenshot_window.grab_set()
            self.selection_canvas.focus_set()

            # Make sure window is fully rendered
            self.screenshot_window.update_idletasks()
            self.screenshot_window.update()

            print("Screenshot overlay created with clean screen content - app window hidden!")

        except Exception as e:
            print(f"Error creating screen overlay: {e}")
            # Fallback to simple overlay
            self._create_simple_overlay()

    def _create_simple_overlay(self):
        """Fallback: Create simple overlay without screen capture."""
        print("Creating simple overlay (fallback)...")

        # Create window without parent to avoid showing main window
        self.screenshot_window = tk.Toplevel()
        self.screenshot_window.attributes('-fullscreen', True)
        self.screenshot_window.attributes('-topmost', True)

        # Try to make it as transparent as possible
        try:
            self.screenshot_window.wm_attributes('-transparentcolor', 'grey')
            self.screenshot_window.configure(bg='grey')
        except:
            self.screenshot_window.configure(bg='black')
            self.screenshot_window.attributes('-alpha', 0.05)  # Very minimal tint

        # Create canvas
        self.selection_canvas = tk.Canvas(
            self.screenshot_window,
            highlightthickness=0,
            bg='grey'
        )
        self.selection_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Instructions (keep as requested)
        instructions_frame = tk.Frame(self.screenshot_window, bg='#1f2937', relief='solid', bd=1)
        instructions_frame.place(x=20, y=20)

        instructions = tk.Label(
            instructions_frame,
            text=" CLICK and DRAG to select region • ESC to cancel • Right-click to cancel",
            font=('Segoe UI', 12, 'bold'),
            fg="#ffffff",
            bg="#1f2937",
            padx=20,
            pady=10
        )
        instructions.pack()

        self.selection_canvas.config(cursor="crosshair")
        self.screenshot_window.focus_force()
        self.screenshot_window.grab_set()
        self.selection_canvas.focus_set()

        print("Simple overlay created (main window should be hidden)")

    def _bind_events(self):
        """Bind mouse and keyboard events - simplified and reliable."""
        print("Binding events...")

        # Mouse events for selection - bind to both window and canvas
        self.selection_canvas.bind("<Button-1>", self._start_selection)
        self.selection_canvas.bind("<B1-Motion>", self._update_selection)
        self.selection_canvas.bind("<ButtonRelease-1>", self._end_selection)

        # Also bind to window in case canvas doesn't get the events
        self.screenshot_window.bind("<Button-1>", self._start_selection)
        self.screenshot_window.bind("<B1-Motion>", self._update_selection)
        self.screenshot_window.bind("<ButtonRelease-1>", self._end_selection)

        # ESC key handling - multiple approaches
        self.screenshot_window.bind('<Escape>', self._cancel_screenshot)
        self.selection_canvas.bind('<Escape>', self._cancel_screenshot)
        self.screenshot_window.bind_all('<Escape>', self._cancel_screenshot)

        # Right-click to cancel
        self.selection_canvas.bind("<Button-3>", self._cancel_screenshot)
        self.screenshot_window.bind("<Button-3>", self._cancel_screenshot)

        # Any key press for ESC detection
        self.screenshot_window.bind('<KeyPress>', self._debug_key_press)
        self.selection_canvas.bind('<KeyPress>', self._debug_key_press)

        # Ensure focus
        self.screenshot_window.focus_force()
        self.selection_canvas.focus_set()

        print("Event bindings complete")

    def _debug_key_press(self, event):
        """Debug method to see what keys are being pressed."""
        print(f" Key pressed: {event.keysym} (keycode: {event.keycode})")
        if event.keysym == 'Escape':
            print("    ESC detected, calling cancel...")
            self._cancel_screenshot(event)

    def _start_selection(self, event):
        """Start selection rectangle."""
        print(f"Starting selection at ({event.x}, {event.y})")

        self.start_x = event.x
        self.start_y = event.y
        self.selecting = True

        # Clear any existing selection elements (but preserve background)
        self.selection_canvas.delete("selection")

        # Add starting point indicator with high visibility
        start_indicator_size = 10

        # White outer circle
        self.selection_canvas.create_oval(
            self.start_x - start_indicator_size, self.start_y - start_indicator_size,
            self.start_x + start_indicator_size, self.start_y + start_indicator_size,
            fill='white',
            outline='black',
            width=2,
            tags="selection"
        )

        # Red inner circle
        self.selection_canvas.create_oval(
            self.start_x - start_indicator_size//2, self.start_y - start_indicator_size//2,
            self.start_x + start_indicator_size//2, self.start_y + start_indicator_size//2,
            fill='#ff0000',
            outline='white',
            width=1,
            tags="selection"
        )

        print("Selection started, drag to create rectangle")

    def _update_selection(self, event):
        """Update selection rectangle during drag with high-contrast overlay."""
        if not self.selecting:
            return

        # Clear previous selection elements (but keep background)
        self.selection_canvas.delete("selection")

        # Calculate rectangle coordinates
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y

        # Ensure proper rectangle bounds
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)

        # Draw selection rectangle with high contrast
        # Outer border (white)
        self.selection_canvas.create_rectangle(
            left-2, top-2, right+2, bottom+2,
            outline='white',
            width=4,
            tags="selection"
        )

        # Inner border (red)
        self.selection_canvas.create_rectangle(
            left, top, right, bottom,
            outline='#ff0000',
            width=2,
            tags="selection"
        )

        # Semi-transparent fill to highlight selection
        self.selection_canvas.create_rectangle(
            left, top, right, bottom,
            fill='#ff0000',
            stipple='gray12',  # Very light fill
            outline='',
            tags="selection"
        )

        # Show dimensions with background
        width = abs(right - left)
        height = abs(bottom - top)

        if width > 50 and height > 30:  # Only show if there's space
            center_x = left + width // 2
            center_y = top + height // 2

            # Dimension background
            self.selection_canvas.create_rectangle(
                center_x - 50, center_y - 15,
                center_x + 50, center_y + 15,
                fill='#1f2937',
                outline='white',
                width=1,
                tags="selection"
            )

            # Dimension text
            self.selection_canvas.create_text(
                center_x, center_y,
                text=f"{width} × {height}",
                fill='white',
                font=('Segoe UI', 12, 'bold'),
                tags="selection"
            )

    def _end_selection(self, event):
        """End selection and capture screenshot with confirmation feedback."""
        if not self.selecting:
            return

        print(f"Ending selection at ({event.x}, {event.y})")
        self.selecting = False

        # Calculate selection coordinates
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)

        width = abs(x2 - x1)
        height = abs(y2 - y1)

        print(f"Final selection: {width}x{height} pixels from ({x1},{y1}) to ({x2},{y2})")

        # Check if selection is large enough
        if width > 20 and height > 20:
            print(f"Valid selection: {width}x{height} - preparing to capture")

            # Clear ALL visual elements before capture to avoid them appearing in screenshot
            self.selection_canvas.delete("selection")
            self.selection_canvas.delete("confirmation")
            self.selection_canvas.delete("error")

            # Hide the entire screenshot window before capture
            self.screenshot_window.withdraw()

            # Small delay to ensure window is fully hidden
            self.screenshot_window.after(100, lambda: self._capture_screenshot(x1, y1, x2, y2))
        else:
            print(f"Selection too small: {width}x{height} (need at least 20x20)")

            # Just show brief error message without visual elements that could be captured
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Brief error indication
            self.selection_canvas.create_text(
                center_x, center_y,
                text=" Area too small!",
                fill='red',
                font=('Segoe UI', 16, 'bold'),
                tags="error"
            )

            self.screenshot_window.update()
            self.screenshot_window.after(1000, lambda: self._cleanup_and_callback(None))

    def _capture_screenshot(self, x1: int, y1: int, x2: int, y2: int):
        """
        Capture screenshot of selected area with improved coordinate handling.

        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
        """
        try:
            print(f"Capturing screenshot: ({x1},{y1}) to ({x2},{y2})")

            # Get screen offset for multi-monitor setups
            screen_x = self.screenshot_window.winfo_rootx()
            screen_y = self.screenshot_window.winfo_rooty()

            # Adjust coordinates for screen position
            abs_x1 = x1 + screen_x
            abs_y1 = y1 + screen_y
            abs_x2 = x2 + screen_x
            abs_y2 = y2 + screen_y

            print(f"Adjusted coordinates: ({abs_x1},{abs_y1}) to ({abs_x2},{abs_y2})")

            # Capture screenshot with all_screens=True for multi-monitor support
            screenshot = ImageGrab.grab(bbox=(abs_x1, abs_y1, abs_x2, abs_y2), all_screens=True)

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
            # Fallback to original coordinates if adjustment fails
            try:
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                if screenshot:
                    image_array = np.array(screenshot)
                    print(f"Fallback screenshot captured: {image_array.shape}")
                    self._cleanup_and_callback(image_array)
                else:
                    self._cleanup_and_callback(None)
            except:
                self._cleanup_and_callback(None)

    def _refocus_window(self, event=None):
        """Refocus the screenshot window if focus is lost."""
        try:
            if (self.screenshot_window and
                hasattr(self.screenshot_window, 'winfo_exists') and
                self.screenshot_window.winfo_exists()):
                self.screenshot_window.focus_force()
                if self.selection_canvas:
                    self.selection_canvas.focus_set()
        except Exception as e:
            print(f"Focus error (can be ignored): {e}")
            pass

    def _cancel_screenshot(self, event=None):
        """Cancel screenshot capture - clean exit without visual feedback."""
        print(f" Screenshot cancelled by user (event: {event})")

        # Clean exit without visual feedback that could be captured
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

            # Clean up screen photo reference
            if self.screen_photo:
                self.screen_photo = None

            # Restore main window if it was hidden
            if self.main_window_hidden:
                try:
                    root = self.parent
                    while root.master:
                        root = root.master
                    root.deiconify()
                    self.main_window_hidden = False
                except Exception as e:
                    print(f"Warning: Could not restore main window: {e}")

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
    might not work properly. Enhanced for multi-monitor support.
    """

    @staticmethod
    def capture_full_screen() -> Optional[np.ndarray]:
        """
        Capture full screen without user selection.
        Supports multi-monitor setups.

        Returns:
            Full screen image as numpy array or None if failed
        """
        try:
            # Use all_screens=True to capture all monitors
            screenshot = ImageGrab.grab(all_screens=True)
            if screenshot:
                return np.array(screenshot)
        except Exception as e:
            print(f"Error capturing full screen: {e}")
            # Fallback to single screen capture
            try:
                screenshot = ImageGrab.grab()
                if screenshot:
                    return np.array(screenshot)
            except Exception as e2:
                print(f"Error in fallback capture: {e2}")
        return None

    @staticmethod
    def capture_primary_screen() -> Optional[np.ndarray]:
        """
        Capture only the primary screen.

        Returns:
            Primary screen image as numpy array or None if failed
        """
        try:
            screenshot = ImageGrab.grab()  # Default captures primary screen
            if screenshot:
                return np.array(screenshot)
        except Exception as e:
            print(f"Error capturing primary screen: {e}")
        return None

    @staticmethod
    def capture_with_delay(delay_seconds: int = 3, all_screens: bool = True) -> Optional[np.ndarray]:
        """
        Capture screen after a delay.

        Args:
            delay_seconds: Delay before capture
            all_screens: Whether to capture all screens or just primary

        Returns:
            Screen image as numpy array or None if failed
        """
        try:
            time.sleep(delay_seconds)
            if all_screens:
                return SimpleScreenshotCapture.capture_full_screen()
            else:
                return SimpleScreenshotCapture.capture_primary_screen()
        except Exception as e:
            print(f"Error in delayed capture: {e}")
        return None

    @staticmethod
    def get_screen_info() -> dict:
        """
        Get information about available screens.

        Returns:
            Dictionary with screen information
        """
        try:
            # Get primary screen dimensions
            root = tk.Tk()
            root.withdraw()

            primary_width = root.winfo_screenwidth()
            primary_height = root.winfo_screenheight()

            root.destroy()

            # Try to get virtual screen dimensions (all monitors)
            try:
                virtual_screenshot = ImageGrab.grab(all_screens=True)
                virtual_width, virtual_height = virtual_screenshot.size
            except:
                virtual_width, virtual_height = primary_width, primary_height

            return {
                'primary_screen': {
                    'width': primary_width,
                    'height': primary_height
                },
                'virtual_screen': {
                    'width': virtual_width,
                    'height': virtual_height
                },
                'multi_monitor': virtual_width > primary_width or virtual_height > primary_height
            }

        except Exception as e:
            print(f"Error getting screen info: {e}")
            return {
                'primary_screen': {'width': 1920, 'height': 1080},
                'virtual_screen': {'width': 1920, 'height': 1080},
                'multi_monitor': False
            }


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
        Get virtual screen dimensions (all monitors combined).

        Returns:
            Tuple of (width, height) for the entire virtual screen
        """
        try:
            # Get virtual screen dimensions using ImageGrab
            virtual_screenshot = ImageGrab.grab(all_screens=True)
            return virtual_screenshot.size
        except Exception:
            try:
                # Fallback to primary screen using tkinter
                root = tk.Tk()
                root.withdraw()
                width = root.winfo_screenwidth()
                height = root.winfo_screenheight()
                root.destroy()
                return width, height
            except Exception:
                # Final fallback to reasonable defaults
                return 1920, 1080

    @staticmethod
    def get_primary_screen_dimensions() -> tuple[int, int]:
        """
        Get primary screen dimensions only.

        Returns:
            Tuple of (width, height) for the primary screen
        """
        try:
            root = tk.Tk()
            root.withdraw()
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            return width, height
        except Exception:
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