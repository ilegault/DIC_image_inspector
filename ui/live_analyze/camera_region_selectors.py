#!/usr/bin/env python3
"""
Camera Region Selectors for SpinView Capture.

Extracted from test file for use in the main application.
"""

import tkinter as tk
import numpy as np
import cv2
from PIL import Image, ImageTk
import logging
from utils.window_utils import WindowManager

logger = logging.getLogger(__name__)


def position_window_on_parent_monitor(child_window, parent_window):
    """
    Position a child window on the same monitor as the parent window.
    
    Args:
        child_window: The window to position
        parent_window: The parent window to position relative to
    """
    try:
        # Get parent window position and size
        parent_x = parent_window.winfo_x()
        parent_y = parent_window.winfo_y()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        # Get child window size
        child_width = child_window.winfo_width()
        child_height = child_window.winfo_height()
        
        # Calculate center position relative to parent window
        # Center the child window over the parent window
        x = parent_x + (parent_width - child_width) // 2
        y = parent_y + (parent_height - child_height) // 2
        
        # For multi-monitor setups, we need to be more careful about screen bounds
        # Try to get the actual monitor bounds that contain the parent window
        try:
            import tkinter as tk
            # Create a temporary window to get screen info
            temp = tk.Toplevel()
            temp.withdraw()  # Hide it
            temp.geometry(f"1x1+{parent_x}+{parent_y}")  # Position at parent location
            temp.update_idletasks()
            
            # Get screen dimensions from the temporary window's perspective
            screen_width = temp.winfo_screenwidth()
            screen_height = temp.winfo_screenheight()
            temp.destroy()
            
        except Exception:
            # Fallback to parent's screen info
            screen_width = parent_window.winfo_screenwidth()
            screen_height = parent_window.winfo_screenheight()
        
        # Adjust if window would go off-screen, but be more lenient for multi-monitor
        # Allow negative coordinates for secondary monitors
        max_x = screen_width - child_width - 10
        max_y = screen_height - child_height - 10
        
        # Only adjust if the window would be completely off-screen
        if x + child_width < 0:  # Completely off left edge
            x = 10
        elif x > screen_width:  # Completely off right edge
            x = max_x
            
        if y + child_height < 0:  # Completely off top edge
            y = 10
        elif y > screen_height:  # Completely off bottom edge
            y = max_y
        
        # Set the window position
        child_window.geometry(f"+{x}+{y}")
        logger.debug(f"Positioned child window at: {x}, {y} (parent at {parent_x}, {parent_y})")
        
    except Exception as e:
        logger.warning(f"Could not position window on parent monitor: {e}")
        # Fallback: position relative to parent with simple offset
        try:
            parent_x = parent_window.winfo_x()
            parent_y = parent_window.winfo_y()
            x = parent_x + 100
            y = parent_y + 100
            child_window.geometry(f"+{x}+{y}")
        except Exception:
            # Final fallback to center of screen
            x = (child_window.winfo_screenwidth() - child_window.winfo_width()) // 2
            y = (child_window.winfo_screenheight() - child_window.winfo_height()) // 2
            child_window.geometry(f"+{x}+{y}")


class CameraRegionSelector:
    """Interactive selector for camera region within window."""

    def __init__(self, parent, window_image, on_selection):
        self.parent = parent
        self.window_image = window_image
        self.on_selection = on_selection

        self.selector_window = None
        self.canvas = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.image_scale = 1.0

    def show(self):
        """Show the region selector."""
        self.selector_window = WindowManager.create_child_window(
            parent=self.parent,
            title="Select Camera Feed Region",
            width=800,
            height=1000,
            resizable=True,
            topmost=True,
            center=True
        )
        self.selector_window.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Instructions
        inst_frame = tk.Frame(self.selector_window, bg='#2c3e50')
        inst_frame.pack(fill='x')

        tk.Label(
            inst_frame,
            text="📹 Draw a rectangle around the camera's live feed area (ignore UI elements)",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='white',
            pady=10
        ).pack()

        # Canvas for image and selection
        canvas_frame = tk.Frame(self.selector_window)
        canvas_frame.pack(fill='both', expand=True)

        # Calculate display size
        h, w = self.window_image.shape[:2]
        max_width = 1200
        max_height = 800

        self.image_scale = min(max_width / w, max_height / h, 1.0)
        display_w = int(w * self.image_scale)
        display_h = int(h * self.image_scale)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=display_w,
            height=display_h,
            cursor='crosshair',
            bg='black'
        )
        self.canvas.pack(padx=10, pady=10)

        # Display window image
        resized = cv2.resize(self.window_image, (display_w, display_h))
        pil_image = Image.fromarray(resized)
        self.photo = ImageTk.PhotoImage(pil_image)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

        # Bind mouse events
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)

        # Buttons
        btn_frame = tk.Frame(self.selector_window)
        btn_frame.pack(fill='x', pady=10)

        self.confirm_btn = tk.Button(
            btn_frame,
            text="✓ Confirm Selection",
            command=self._on_confirm,
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=5,
            state='disabled'
        )
        self.confirm_btn.pack(side='left', padx=10)

        tk.Button(
            btn_frame,
            text="✗ Cancel",
            command=self._on_cancel,
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=5
        ).pack(side='left', padx=10)

        tk.Label(
            self.selector_window,
            text="Tip: The camera feed is usually the largest rectangular area showing live video",
            font=('Arial', 10),
            fg='gray'
        ).pack(pady=5)

        # Window positioning is handled by WindowManager.create_child_window

    def _on_click(self, event):
        """Handle mouse click."""
        self.start_x = event.x
        self.start_y = event.y

        if self.rect_id:
            self.canvas.delete(self.rect_id)

        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='#00ff00', width=2
        )

    def _on_drag(self, event):
        """Handle mouse drag."""
        if self.rect_id:
            self.canvas.coords(
                self.rect_id,
                self.start_x, self.start_y, event.x, event.y
            )

    def _on_release(self, event):
        """Handle mouse release."""
        if self.start_x and self.start_y:
            # Calculate region
            x1 = min(self.start_x, event.x)
            y1 = min(self.start_y, event.y)
            x2 = max(self.start_x, event.x)
            y2 = max(self.start_y, event.y)

            # Ensure minimum size
            if abs(x2 - x1) > 20 and abs(y2 - y1) > 20:
                self.confirm_btn.config(state='normal')

                # Draw corner markers
                self._draw_corner_markers(x1, y1, x2, y2)

    def _draw_corner_markers(self, x1, y1, x2, y2):
        """Draw corner markers for clarity."""
        marker_size = 10
        marker_color = '#00ff00'

        # Top-left
        self.canvas.create_line(
            x1, y1, x1 + marker_size, y1,
            fill=marker_color, width=3
        )
        self.canvas.create_line(
            x1, y1, x1, y1 + marker_size,
            fill=marker_color, width=3
        )

        # Top-right
        self.canvas.create_line(
            x2 - marker_size, y1, x2, y1,
            fill=marker_color, width=3
        )
        self.canvas.create_line(
            x2, y1, x2, y1 + marker_size,
            fill=marker_color, width=3
        )

        # Bottom-left
        self.canvas.create_line(
            x1, y2, x1 + marker_size, y2,
            fill=marker_color, width=3
        )
        self.canvas.create_line(
            x1, y2 - marker_size, x1, y2,
            fill=marker_color, width=3
        )

        # Bottom-right
        self.canvas.create_line(
            x2 - marker_size, y2, x2, y2,
            fill=marker_color, width=3
        )
        self.canvas.create_line(
            x2, y2 - marker_size, x2, y2,
            fill=marker_color, width=3
        )

    def _on_confirm(self):
        """Confirm selection."""
        if self.rect_id:
            coords = self.canvas.coords(self.rect_id)
            if len(coords) == 4:
                # Convert back to original image coordinates
                x1 = int(coords[0] / self.image_scale)
                y1 = int(coords[1] / self.image_scale)
                x2 = int(coords[2] / self.image_scale)
                y2 = int(coords[3] / self.image_scale)

                # Return as (x, y, width, height)
                region = (x1, y1, x2 - x1, y2 - y1)

                self.selector_window.destroy()
                self.on_selection(region)

    def _on_cancel(self):
        """Cancel selection."""
        self.selector_window.destroy()
        self.on_selection(None)


class CameraPolygonSelector:
    """Interactive polygon selector for camera region within window."""

    def __init__(self, parent, window_image, on_selection):
        self.parent = parent
        self.window_image = window_image
        self.on_selection = on_selection

        self.selector_window = None
        self.canvas = None
        self.polygon_points = []
        self.polygon_id = None
        self.preview_line = None
        self.image_scale = 1.0

    def show(self):
        """Show the polygon selector."""
        self.selector_window = WindowManager.create_child_window(
            parent=self.parent,
            title="Select Camera Feed Region - Polygon",
            width=800,
            height=1000,
            resizable=True,
            topmost=True,
            center=True
        )
        self.selector_window.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Instructions
        inst_frame = tk.Frame(self.selector_window, bg='#2c3e50')
        inst_frame.pack(fill='x')

        tk.Label(
            inst_frame,
            text="🔺 Click to add polygon points around the camera feed area",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='white',
            pady=10
        ).pack()

        tk.Label(
            inst_frame,
            text="Left-click: Add point | Right-click: Finish polygon | ESC: Cancel",
            font=('Arial', 10),
            bg='#2c3e50',
            fg='#ecf0f1',
            pady=5
        ).pack()

        # Canvas for image and selection
        canvas_frame = tk.Frame(self.selector_window)
        canvas_frame.pack(fill='both', expand=True)

        # Calculate display size
        h, w = self.window_image.shape[:2]
        max_width = 1200
        max_height = 800

        self.image_scale = min(max_width / w, max_height / h, 1.0)
        display_w = int(w * self.image_scale)
        display_h = int(h * self.image_scale)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=display_w,
            height=display_h,
            cursor='crosshair',
            bg='black'
        )
        self.canvas.pack(padx=10, pady=10)

        # Display window image
        resized = cv2.resize(self.window_image, (display_w, display_h))
        pil_image = Image.fromarray(resized)
        self.photo = ImageTk.PhotoImage(pil_image)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

        # Bind mouse events
        self.canvas.bind('<Button-1>', self._on_left_click)
        self.canvas.bind('<Button-3>', self._on_right_click)
        self.canvas.bind('<Motion>', self._on_mouse_motion)
        self.selector_window.bind('<Escape>', lambda e: self._on_cancel())

        # Buttons
        btn_frame = tk.Frame(self.selector_window)
        btn_frame.pack(fill='x', pady=10)

        self.finish_btn = tk.Button(
            btn_frame,
            text="✓ Finish Polygon",
            command=self._on_finish,
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=5,
            state='disabled'
        )
        self.finish_btn.pack(side='left', padx=10)

        tk.Button(
            btn_frame,
            text="🗑️ Clear Points",
            command=self._clear_points,
            bg='#f39c12',
            fg='white',
            padx=20,
            pady=5
        ).pack(side='left', padx=10)

        tk.Button(
            btn_frame,
            text="✗ Cancel",
            command=self._on_cancel,
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=5
        ).pack(side='left', padx=10)

        # Status
        self.status_label = tk.Label(
            self.selector_window,
            text="Click to add points (minimum 3 points required)",
            font=('Arial', 10),
            fg='gray'
        )
        self.status_label.pack(pady=5)

        # Window positioning is handled by WindowManager.create_child_window

    def _on_left_click(self, event):
        """Handle left mouse click - add polygon point."""
        # Convert to original image coordinates
        orig_x = int(event.x / self.image_scale)
        orig_y = int(event.y / self.image_scale)
        
        self.polygon_points.append((orig_x, orig_y))
        
        # Update display
        self._redraw_polygon()
        
        # Update status
        point_count = len(self.polygon_points)
        if point_count < 3:
            self.status_label.config(text=f"Added point {point_count}. Need {3-point_count} more points minimum.")
        else:
            self.status_label.config(text=f"Added point {point_count}. Right-click or press Finish to complete.")
            self.finish_btn.config(state='normal')

    def _on_right_click(self, event):
        """Handle right mouse click - finish polygon."""
        if len(self.polygon_points) >= 3:
            self._on_finish()

    def _on_mouse_motion(self, event):
        """Handle mouse motion - show preview line."""
        if not self.polygon_points:
            return
            
        # Remove previous preview line
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            
        # Draw preview line from last point to current mouse position
        last_point = self.polygon_points[-1]
        last_x = int(last_point[0] * self.image_scale)
        last_y = int(last_point[1] * self.image_scale)
        
        self.preview_line = self.canvas.create_line(
            last_x, last_y, event.x, event.y,
            fill='#ffff00', width=2, dash=(5, 5)
        )

    def _redraw_polygon(self):
        """Redraw the polygon with all current points."""
        # Clear existing polygon
        if self.polygon_id:
            self.canvas.delete(self.polygon_id)
            
        if len(self.polygon_points) < 2:
            return
            
        # Convert points to display coordinates
        display_points = []
        for point in self.polygon_points:
            display_x = int(point[0] * self.image_scale)
            display_y = int(point[1] * self.image_scale)
            display_points.extend([display_x, display_y])
            
        # Draw polygon
        if len(display_points) >= 4:
            self.polygon_id = self.canvas.create_polygon(
                display_points,
                outline='#00ff00',
                fill='',
                width=2
            )
            
        # Draw points as circles
        for point in self.polygon_points:
            display_x = int(point[0] * self.image_scale)
            display_y = int(point[1] * self.image_scale)
            self.canvas.create_oval(
                display_x - 3, display_y - 3,
                display_x + 3, display_y + 3,
                fill='#00ff00', outline='#ffffff'
            )

    def _clear_points(self):
        """Clear all polygon points."""
        self.polygon_points = []
        if self.polygon_id:
            self.canvas.delete(self.polygon_id)
            self.polygon_id = None
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            self.preview_line = None
            
        self.finish_btn.config(state='disabled')
        self.status_label.config(text="Click to add points (minimum 3 points required)")
        
        # Redraw image to clear all drawings
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

    def _on_finish(self):
        """Finish polygon selection."""
        if len(self.polygon_points) >= 3:
            # Return polygon as tuple format
            region = ('polygon', self.polygon_points)
            self.selector_window.destroy()
            self.on_selection(region)

    def _on_cancel(self):
        """Cancel polygon selection."""
        self.selector_window.destroy()
        self.on_selection(None)