# ui/components/roi_selector.py - Clean ROI Selection Component

import tkinter as tk
from typing import List, Tuple, Callable, Dict, Optional
import logging
from utils.constants import APP_CONFIG

logger = logging.getLogger(__name__)


class ROISelector:
    """
    ROI (Region of Interest) selector component.

    Handles polygon ROI selection on the image canvas.
    Follows single responsibility principle - only ROI selection concerns.
    """

    def __init__(self, canvas: tk.Canvas, callbacks: Dict[str, Callable]):
        """
        Initialize ROI selector.

        Args:
            canvas: Canvas widget to draw ROI on
            callbacks: Dictionary of callback functions
        """
        self.canvas = canvas
        self.callbacks = callbacks

        # ROI state
        self.roi_coords = []  # List of (x, y) tuples in image coordinates
        self.roi_polygon = None
        self.preview_line = None
        self.selection_mode = False
        self.ctrl_selection_mode = False  # New: Ctrl+hold selection mode

        # Visual properties
        self.roi_color = APP_CONFIG['roi']['normal_color']
        self.selection_color = APP_CONFIG['roi']['selection_color']
        self.line_width = APP_CONFIG['roi']['line_width']

        # Bind events
        self._bind_events()

    def _bind_events(self):
        """Bind canvas events for ROI selection."""
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Motion>", self._on_mouse_motion)

    def start_roi_selection(self):
        """Start ROI selection mode."""
        # Clear any existing ROI
        self.clear()

        # Enter selection mode
        self.selection_mode = True
        self.canvas.config(cursor="crosshair")

        # Notify callbacks
        self._execute_callback('roi_changed', [])

    def start_ctrl_selection(self):
        """Start Ctrl+hold ROI selection mode."""
        if not self.ctrl_selection_mode and not self.selection_mode:
            logger.debug("Starting Ctrl ROI selection mode")
            self.ctrl_selection_mode = True
            
            # Clear any existing ROI
            self.clear()
            
            # Enter selection mode
            self.selection_mode = True
            self.canvas.config(cursor="crosshair")
            
            # Notify callbacks
            self._execute_callback('roi_changed', [])

    def end_ctrl_selection(self):
        """End Ctrl+hold ROI selection mode."""
        if self.ctrl_selection_mode:
            logger.debug("Ending Ctrl ROI selection mode")
            self.ctrl_selection_mode = False
            
            # Auto-complete ROI if we have enough points
            if len(self.roi_coords) >= 3:
                self._finish_selection()
            else:
                # Not enough points, cancel selection
                self.clear()

    def _on_ctrl_press(self, event):
        """Handle Ctrl key press - start Ctrl selection mode."""
        if not self.ctrl_selection_mode and not self.selection_mode:
            logger.debug("Starting Ctrl ROI selection mode")
            self.ctrl_selection_mode = True
            
            # Clear any existing ROI
            self.clear()
            
            # Enter selection mode
            self.selection_mode = True
            self.canvas.config(cursor="crosshair")
            
            # Notify callbacks
            self._execute_callback('roi_changed', [])

    def _on_ctrl_release(self, event):
        """Handle Ctrl key release - finish Ctrl selection mode."""
        if self.ctrl_selection_mode:
            logger.debug("Ending Ctrl ROI selection mode")
            self.ctrl_selection_mode = False
            
            # Auto-complete ROI if we have enough points
            if len(self.roi_coords) >= 3:
                self._finish_selection()
            else:
                # Not enough points, cancel selection
                self.clear()

    def _on_left_click(self, event):
        """Handle left mouse click - add ROI point."""
        # Check if Ctrl is held down for Ctrl selection mode
        ctrl_held = (event.state & 0x4) != 0  # Check Ctrl modifier
        
        if ctrl_held and not self.selection_mode:
            # Start Ctrl selection mode
            self.start_ctrl_selection()
        
        if not self.selection_mode:
            return

        # Get image coordinates
        try:
            # Check if canvas has image coordinate conversion method
            if hasattr(self.canvas.master, 'get_image_coordinates'):
                image_x, image_y = self.canvas.master.get_image_coordinates(event.x, event.y)
            else:
                # Fallback to manual calculation
                image_x, image_y = self._canvas_to_image_coords(event.x, event.y)

            # Add point if within image bounds
            if image_x >= 0 and image_y >= 0:
                self.roi_coords.append((image_x, image_y))
                logger.debug(f"Added ROI point {len(self.roi_coords)}: ({image_x:.1f}, {image_y:.1f})")

                # Redraw ROI
                self._redraw_roi(preview_point=None)

                # Notify callbacks
                self._execute_callback('roi_changed', self.roi_coords.copy())

        except Exception as e:
            logger.error(f"Error adding ROI point: {e}")



    def _on_mouse_motion(self, event):
        """Handle mouse motion - show preview line."""
        if not self.selection_mode or not self.roi_coords:
            return

        try:
            # Get image coordinates for preview
            if hasattr(self.canvas.master, 'get_image_coordinates'):
                image_x, image_y = self.canvas.master.get_image_coordinates(event.x, event.y)
            else:
                image_x, image_y = self._canvas_to_image_coords(event.x, event.y)

            # Redraw with preview
            self._redraw_roi(preview_point=(image_x, image_y))

        except Exception as e:
            print(f"Error in mouse motion: {e}")

    def _finish_selection(self):
        """Finish ROI selection."""
        logger.debug(f"Finishing ROI polygon with {len(self.roi_coords)} points")

        # Exit selection mode
        self.selection_mode = False
        self.canvas.config(cursor="")

        # Draw final polygon
        self._redraw_roi(preview_point=None, finalize=True)

        # Notify callbacks
        self._execute_callback('roi_completed', self.roi_coords.copy())

    def _redraw_roi(self, preview_point: Optional[Tuple[float, float]] = None, finalize: bool = False):
        """
        Redraw the ROI polygon and preview line.

        Args:
            preview_point: Current mouse position for preview line
            finalize: Whether this is the final polygon
        """
        # Remove previous drawings
        if self.roi_polygon:
            self.canvas.delete(self.roi_polygon)
            self.roi_polygon = None
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            self.preview_line = None

        if not self.roi_coords:
            return

        # Convert image coordinates to canvas coordinates
        canvas_coords = []
        for image_x, image_y in self.roi_coords:
            canvas_x, canvas_y = self._image_to_canvas_coords(image_x, image_y)
            canvas_coords.append((canvas_x, canvas_y))

        # Draw polygon or line
        if len(canvas_coords) >= 2:
            # Flatten coordinates for canvas methods
            flat_coords = [coord for point in canvas_coords for coord in point]

            if finalize and len(canvas_coords) >= 3:
                # Draw filled polygon
                self.roi_polygon = self.canvas.create_polygon(
                    *flat_coords,
                    outline=self.roi_color,
                    fill='',
                    width=self.line_width
                )
            else:
                # Draw line
                self.roi_polygon = self.canvas.create_line(
                    *flat_coords,
                    fill=self.selection_color,
                    width=self.line_width
                )

        # Draw preview line
        if preview_point and canvas_coords:
            last_canvas_x, last_canvas_y = canvas_coords[-1]
            preview_canvas_x, preview_canvas_y = self._image_to_canvas_coords(*preview_point)

            self.preview_line = self.canvas.create_line(
                last_canvas_x, last_canvas_y,
                preview_canvas_x, preview_canvas_y,
                fill=self.selection_color,
                dash=(5, 5),
                width=self.line_width
            )

    def _canvas_to_image_coords(self, canvas_x: int, canvas_y: int) -> Tuple[float, float]:
        """
        Convert canvas coordinates to original image coordinates.

        Args:
            canvas_x: Canvas X coordinate
            canvas_y: Canvas Y coordinate

        Returns:
            Tuple of (image_x, image_y) coordinates in original image space
        """
        # Get canvas-relative coordinates
        canvas_x = self.canvas.canvasx(canvas_x)
        canvas_y = self.canvas.canvasy(canvas_y)

        # Get display scale and offset from canvas
        display_scale = getattr(self.canvas, 'display_scale', 1.0)
        offset_x = getattr(self.canvas, 'image_offset_x', 0)
        offset_y = getattr(self.canvas, 'image_offset_y', 0)

        # Adjust for image offset
        canvas_x -= offset_x
        canvas_y -= offset_y

        # Convert to original image coordinates
        # The display_scale represents the total scaling from original to canvas
        if display_scale <= 0:
            display_scale = 1.0
            
        image_x = canvas_x / display_scale
        image_y = canvas_y / display_scale

        return image_x, image_y

    def _image_to_canvas_coords(self, image_x: float, image_y: float) -> Tuple[float, float]:
        """
        Convert original image coordinates to canvas coordinates.

        Args:
            image_x: Original image X coordinate
            image_y: Original image Y coordinate

        Returns:
            Tuple of (canvas_x, canvas_y) coordinates
        """
        # Get display scale and offset from canvas
        display_scale = getattr(self.canvas, 'display_scale', 1.0)
        offset_x = getattr(self.canvas, 'image_offset_x', 0)
        offset_y = getattr(self.canvas, 'image_offset_y', 0)

        # Convert from original image coordinates to canvas coordinates
        # Apply the total scaling and add offset
        if display_scale <= 0:
            display_scale = 1.0
            
        canvas_x = image_x * display_scale + offset_x
        canvas_y = image_y * display_scale + offset_y

        return canvas_x, canvas_y

    def update_roi_display(self, roi_data):
        """
        Update ROI display with new data.

        Args:
            roi_data: ROI data object with coordinates
        """
        if hasattr(roi_data, 'coordinates'):
            self.roi_coords = roi_data.coordinates.copy()
            self._redraw_roi(finalize=True)
        else:
            self.clear()

    def clear(self):
        """Clear the current ROI selection."""
        logger.debug("Clearing ROI selection")

        # Remove visual elements
        if self.roi_polygon:
            self.canvas.delete(self.roi_polygon)
            self.roi_polygon = None
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            self.preview_line = None

        # Reset state
        self.roi_coords = []
        self.selection_mode = False
        self.ctrl_selection_mode = False
        self.canvas.config(cursor="")

        # Notify callbacks
        self._execute_callback('roi_changed', [])

    def redraw_roi(self):
        """Redraw the ROI polygon after view changes (zoom, pan)."""
        if self.roi_coords and not self.selection_mode:
            self._redraw_roi(finalize=True)

    def get_roi_coordinates(self) -> List[Tuple[float, float]]:
        """Get current ROI coordinates in image space."""
        return self.roi_coords.copy()

    def has_roi(self) -> bool:
        """Check if ROI is currently defined."""
        return len(self.roi_coords) >= 3

    def get_roi_info_string(self) -> str:
        """Get ROI information as display string."""
        if self.has_roi():
            area = self._calculate_roi_area()
            return f"Polygon ROI: {len(self.roi_coords)} points, {area:.0f} px²"
        else:
            return "ROI: Not Selected (analyzing full image)"

    def _calculate_roi_area(self) -> float:
        """Calculate ROI area using shoelace formula."""
        if len(self.roi_coords) < 3:
            return 0.0

        # Shoelace formula
        area = 0.5 * abs(sum(
            x0 * y1 - x1 * y0
            for ((x0, y0), (x1, y1)) in zip(self.roi_coords, self.roi_coords[1:] + [self.roi_coords[0]])
        ))
        return area

    def handle_key_event(self, event_type: str, key: str):
        """
        Handle key events from parent window.
        
        Args:
            event_type: 'press' or 'release'
            key: Key name (e.g., 'Control_L', 'Control_R')
        """
        if key in ['Control_L', 'Control_R']:
            if event_type == 'press':
                self.start_ctrl_selection()
            elif event_type == 'release':
                self.end_ctrl_selection()

    def _execute_callback(self, callback_name: str, *args):
        """Execute callback if it exists."""
        if callback_name in self.callbacks:
            try:
                self.callbacks[callback_name](*args)
            except Exception as e:
                print(f"Error executing callback {callback_name}: {e}")