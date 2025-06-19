# ui/roi_handler.py

class ROIHandler:
    """Handles Region of Interest selection and management"""

    def __init__(self, main_window):
        """Initialize the ROI handler

        Args:
            main_window: Reference to the main application window
        """
        self.main_window = main_window
        self.canvas = main_window.image_canvas
        self.roi_selection_mode = False
        self.roi_coords = None  # (x1, y1, x2, y2) in image coordinates
        self.roi_rect = None  # Canvas rectangle object ID
        self.roi_start = None  # Starting point for ROI selection
        self.roi_overlay_color = "#3498db"  # Blue
        self.selection_active_color = "#e74c3c"  # Red for active selection


    def toggle_roi_selection(self):
        """Toggle ROI selection mode on/off"""
        self.roi_selection_mode = not self.roi_selection_mode

        if self.roi_selection_mode:
            self.main_window.roi_btn.config(bg=self.selection_active_color)
            self.canvas.config(cursor="crosshair")
            self.main_window.status_var.set("Click and drag to select a Region of Interest (ROI)")
        else:
            self.main_window.roi_btn.config(bg="#9b59b6")  # Default purple
            self.canvas.config(cursor="")
            self.main_window.status_var.set("ROI selection mode disabled")


    def start_roi_selection(self, event):
        """Start ROI selection with mouse click

        Args:
            event: Mouse event with x, y coordinates
        """
        if not self.roi_selection_mode:
            return

        # Convert to canvas coordinates accounting for scroll
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Store start position in canvas coordinates
        self.roi_start = (canvas_x, canvas_y)

        # Clear any existing ROI rectangle
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)
            self.roi_rect = None


    def update_roi_selection(self, event):
        """Update ROI selection while dragging

        Args:
            event: Mouse motion event with x, y coordinates
        """
        if not self.roi_selection_mode or not self.roi_start:
            return

        # Convert to canvas coordinates accounting for scroll
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Delete previous rectangle and draw a new one
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)

        self.roi_rect = self.canvas.create_rectangle(
            self.roi_start[0], self.roi_start[1],
            canvas_x, canvas_y,
            outline=self.selection_active_color,
            width=2,
            dash=(5, 5)  # Dashed line for selection in progress
        )


    def end_roi_selection(self, event):
        """Finalize ROI selection on mouse release

        Args:
            event: Mouse release event with x, y coordinates
        """
        if not self.roi_selection_mode or not self.roi_start:
            return

        # Convert to canvas coordinates accounting for scroll
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Calculate ROI coordinates in canvas space
        x1, y1 = self.roi_start
        x2, y2 = canvas_x, canvas_y

        # Ensure x1,y1 is top-left and x2,y2 is bottom-right
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        # Minimum ROI size check
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            if self.roi_rect:
                self.canvas.delete(self.roi_rect)
                self.roi_rect = None
            self.main_window.status_var.set("ROI too small - please select a larger area")
            return

        # Convert to image coordinates (accounting for zoom and scaling)
        display_scale = self.canvas.display_scale if hasattr(self.canvas, 'display_scale') else 1.0

        # Convert canvas coordinates to original image coordinates
        image_x1 = int(x1 / display_scale)
        image_y1 = int(y1 / display_scale)
        image_x2 = int(x2 / display_scale)
        image_y2 = int(y2 / display_scale)

        # Store ROI coordinates in image space
        self.roi_coords = (image_x1, image_y1, image_x2, image_y2)

        # Update the ROI rectangle with final styling
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)

        self.roi_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=self.roi_overlay_color,
            width=2
        )

        # Exit selection mode
        self.roi_selection_mode = False
        self.main_window.roi_btn.config(bg="#9b59b6")  # Reset button color
        self.canvas.config(cursor="")

        # Enable the debug button when ROI is selected
        if hasattr(self.main_window, 'debug_btn'):
            self.main_window.debug_btn.config(state='normal')

        # Update ROI info
        self.update_roi_info()

        # Update status
        roi_width = image_x2 - image_x1
        roi_height = image_y2 - image_y1
        self.main_window.status_var.set(f"ROI selected: {roi_width}x{roi_height} pixels")


    def clear_roi(self):
        """Remove the current ROI selection"""
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)
            self.roi_rect = None

        self.roi_coords = None
        self.roi_selection_mode = False

        if hasattr(self.main_window, 'roi_btn'):
            self.main_window.roi_btn.config(bg="#9b59b6")  # Reset button color

        # Disable the debug button when ROI is cleared
        if hasattr(self.main_window, 'debug_btn'):
            self.main_window.debug_btn.config(state='disabled')

        self.update_roi_info()
        self.main_window.status_var.set("ROI cleared - analyzing full image")


    def update_roi_info(self):
        """Update the ROI information display"""
        if self.roi_coords:
            x1, y1, x2, y2 = self.roi_coords
            width = x2 - x1
            height = y2 - y1

            # Calculate area in pixels and percentage
            total_area = 0
            if hasattr(self.main_window, 'original_image') and self.main_window.original_image is not None:
                h, w = self.main_window.original_image.shape[:2]
                total_area = w * h

            roi_area = width * height
            percentage = (roi_area / total_area * 100) if total_area > 0 else 0

            # Update ROI info label
            if hasattr(self.main_window, 'roi_info_label'):
                self.main_window.roi_info_label.config(
                    text=f"ROI: {width}x{height} pixels ({percentage:.1f}% of image)"
                )
        else:
            # No ROI selected
            if hasattr(self.main_window, 'roi_info_label'):
                self.main_window.roi_info_label.config(
                    text="ROI: Not Selected (analyzing full image)"
                )


    def redraw_roi(self):
        """Redraw the ROI rectangle after zoom or pan operations"""
        if not self.roi_coords or not hasattr(self.main_window, 'image_display'):
            return

        # Get current display scale
        display_scale = self.canvas.display_scale if hasattr(self.canvas, 'display_scale') else 1.0

        # Convert image coordinates to current canvas coordinates
        x1, y1, x2, y2 = self.roi_coords
        canvas_x1 = x1 * display_scale
        canvas_y1 = y1 * display_scale
        canvas_x2 = x2 * display_scale
        canvas_y2 = y2 * display_scale

        # Update or recreate ROI rectangle
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)

        self.roi_rect = self.canvas.create_rectangle(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            outline=self.roi_overlay_color,
            width=2
        )


    def sync_roi_with_view(self, zoom_level=None, visible_x=None, visible_y=None):
        """Synchronize ROI with current view after analysis"""
        if not self.roi_coords:
            return

        # If parameters are provided, use them
        if zoom_level is not None and visible_x is not None and visible_y is not None:
            # Store them for debugging if needed
            self._last_sync = {
                'zoom': zoom_level,
                'x_view': visible_x,
                'y_view': visible_y
            }

        # Redraw the ROI to match current view scale
        self.redraw_roi()


    def display_image(self, pil_image):
        """Display the given PIL image in the image display area"""
        self.main_window.image_display.display_image(pil_image)
        self.redraw_roi()

        # If the image is replaced or cropped, recalculate ROI:
        image_shape_changed = False
        if image_shape_changed:
            self.clear_roi()

