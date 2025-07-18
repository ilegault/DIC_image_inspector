# ui/live_analyze/transparent_roi_selector.py - Transparent ROI Selector

import tkinter as tk
from PIL import Image, ImageTk
from typing import List, Tuple, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class TransparentROISelector:
    """
    FIXED Transparent overlay for ROI selection.

    CRITICAL: This overlay is shown AFTER capturing the original screen,
    ensuring the overlay never affects the analysis results.
    """

    def __init__(self, parent_window, original_screenshot: Image.Image,
                 on_roi_selected: Optional[Callable] = None,
                 on_cancelled: Optional[Callable] = None):
        """
        Initialize the transparent ROI selector.

        Args:
            parent_window: Parent tkinter window
            original_screenshot: The original screenshot taken BEFORE overlay
            on_roi_selected: Callback when ROI selection is complete
            on_cancelled: Callback when ROI selection is cancelled
        """
        self.parent = parent_window
        self.original_screenshot = original_screenshot
        self.on_roi_selected = on_roi_selected
        self.on_cancelled = on_cancelled

        # Create fullscreen window
        self.overlay = tk.Toplevel(parent_window)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-topmost', True)

        # Set transparency
        try:
            self.overlay.attributes('-alpha', 0.7)  # 70% opacity
        except:
            pass  # Transparency not supported on this platform

        self.overlay.configure(bg='black')

        # Canvas for drawing
        self.canvas = tk.Canvas(self.overlay, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)

        # ROI drawing state
        self.roi_points = []
        self.temp_lines = []
        self.preview_line = None

        # Visual elements
        self.point_radius = 5
        self.line_width = 3
        self.point_color = '#00FF00'  # Green
        self.line_color = '#00FF00'  # Green
        self.preview_color = '#FFFF00'  # Yellow

        # Initialize after a short delay to ensure window is ready
        self.overlay.after(100, self._initialize_overlay)

        logger.info("TransparentROISelector initialized")

    def _initialize_overlay(self):
        """Initialize the overlay after window is ready."""
        try:
            # Display the original screenshot as background
            self._display_screenshot_background()

            # Show instructions
            self._show_instructions()

            # Bind events
            self._bind_events()

            logger.info("ROI selector overlay ready")

        except Exception as e:
            logger.error(f"Error initializing overlay: {e}")
            self.close()

    def _display_screenshot_background(self):
        """Display the original screenshot on canvas."""
        try:
            # Get canvas dimensions
            self.overlay.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not ready yet, try again
                self.overlay.after(100, self._display_screenshot_background)
                return

            # Resize screenshot to fit canvas
            screenshot_resized = self.original_screenshot.resize(
                (canvas_width, canvas_height),
                Image.Resampling.LANCZOS
            )

            # Convert PIL image to PhotoImage
            self.photo = ImageTk.PhotoImage(screenshot_resized)
            self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

            # Store scaling factors for coordinate conversion
            self.scale_x = self.original_screenshot.width / canvas_width
            self.scale_y = self.original_screenshot.height / canvas_height

            logger.info(f"Screenshot background displayed: {canvas_width}x{canvas_height}")

        except Exception as e:
            logger.error(f"Failed to display screenshot background: {e}")

    def _show_instructions(self):
        """Show instruction text on the overlay."""
        instruction_text = (
            "ROI Selection Mode\n\n"
            "• Click to add points for ROI boundary\n"
            "• Right-click or press Enter to complete\n"
            "• Press Escape to cancel\n"
            "• Minimum 3 points required"
        )

        self.instruction_text = self.canvas.create_text(
            50, 50,
            text=instruction_text,
            fill='white',
            font=('Arial', 14, 'bold'),
            anchor='nw'
        )

    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Mouse events
        self.canvas.bind('<Button-1>', self._on_left_click)
        self.canvas.bind('<Button-3>', self._on_right_click)
        self.canvas.bind('<Motion>', self._on_mouse_move)

        # Keyboard events
        self.overlay.bind('<Return>', self._on_enter_key)
        self.overlay.bind('<Escape>', self._on_escape_key)
        self.overlay.focus_set()

        # Window events
        self.overlay.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_left_click(self, event):
        """Handle left mouse click - add ROI point."""
        x, y = event.x, event.y

        # Add point to ROI
        self.roi_points.append((x, y))

        # Draw point
        self._draw_point(x, y)

        # Draw line to previous point
        if len(self.roi_points) > 1:
            prev_x, prev_y = self.roi_points[-2]
            line_id = self.canvas.create_line(
                prev_x, prev_y, x, y,
                fill=self.line_color,
                width=self.line_width
            )
            self.temp_lines.append(line_id)

        # Update status
        self._update_status_text()

        logger.debug(f"ROI point added: ({x}, {y}), total points: {len(self.roi_points)}")

    def _on_right_click(self, event):
        """Handle right mouse click - complete ROI selection."""
        self._complete_roi_selection()

    def _on_mouse_move(self, event):
        """Handle mouse movement - show preview line."""
        if len(self.roi_points) == 0:
            return

        # Remove previous preview line
        if self.preview_line:
            self.canvas.delete(self.preview_line)

        # Draw preview line from last point to current mouse position
        last_x, last_y = self.roi_points[-1]
        self.preview_line = self.canvas.create_line(
            last_x, last_y, event.x, event.y,
            fill=self.preview_color,
            width=1,
            dash=(5, 5)
        )

    def _on_enter_key(self, event):
        """Handle Enter key - complete ROI selection."""
        self._complete_roi_selection()

    def _on_escape_key(self, event):
        """Handle Escape key - cancel ROI selection."""
        self._cancel_roi_selection()

    def _on_close(self):
        """Handle window close event."""
        self._cancel_roi_selection()

    def _draw_point(self, x, y):
        """Draw a point on the canvas."""
        self.canvas.create_oval(
            x - self.point_radius, y - self.point_radius,
            x + self.point_radius, y + self.point_radius,
            fill=self.point_color,
            outline='white',
            width=2
        )

    def _update_status_text(self):
        """Update the status/instruction text."""
        if hasattr(self, 'instruction_text'):
            status = f"ROI Points: {len(self.roi_points)} (minimum 3 required)"
            if len(self.roi_points) >= 3:
                status += "\nRight-click or press Enter to complete"

            self.canvas.itemconfig(self.instruction_text, text=
            f"ROI Selection Mode\n\n{status}\n\n"
            "• Click to add points\n"
            "• Right-click/Enter to complete\n"
            "• Escape to cancel"
                                   )

    def _complete_roi_selection(self):
        """Complete the ROI selection if enough points."""
        if len(self.roi_points) < 3:
            logger.warning("Not enough points for ROI selection")
            return

        # Convert canvas coordinates to screen coordinates
        screen_coords = self._canvas_to_screen_coords(self.roi_points)

        logger.info(f"ROI selection completed with {len(screen_coords)} points")

        # Call completion callback
        if self.on_roi_selected:
            self.on_roi_selected(screen_coords)

        # Don't close here - let the parent close us
        # self.close()

    def _cancel_roi_selection(self):
        """Cancel the ROI selection process."""
        logger.info("ROI selection cancelled")

        # Call cancellation callback
        if self.on_cancelled:
            self.on_cancelled()

        # Don't close here - let the parent close us
        # self.close()

    def _canvas_to_screen_coords(self, canvas_points):
        """Convert canvas coordinates to screen coordinates."""
        try:
            if not hasattr(self, 'scale_x') or not hasattr(self, 'scale_y'):
                logger.warning("Scale factors not available, returning canvas coordinates")
                return canvas_points

            screen_points = []
            for canvas_x, canvas_y in canvas_points:
                screen_x = int(canvas_x * self.scale_x)
                screen_y = int(canvas_y * self.scale_y)
                screen_points.append((screen_x, screen_y))

            logger.info(f"Converted {len(canvas_points)} points from canvas to screen coordinates")
            return screen_points

        except Exception as e:
            logger.error(f"Failed to convert coordinates: {e}")
            return canvas_points  # Return original points as fallback

    def close(self):
        """Close the ROI selector overlay."""
        try:
            if self.overlay:
                self.overlay.destroy()
                self.overlay = None
            logger.info("ROI selector closed")
        except Exception as e:
            logger.error(f"Error closing ROI selector: {e}")

    def hide(self):
        """Hide the overlay temporarily."""
        if self.overlay:
            self.overlay.withdraw()

    def show(self):
        """Show the overlay again."""
        if self.overlay:
            self.overlay.deiconify()
            self.overlay.lift()
            self.overlay.attributes('-topmost', True)
