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
        self.roi_coords = []  # List of (x, y) tuples for polygon points
        self.roi_polygon = None
        self.preview_line = None
        self.roi_selection_mode = False
        self.roi_overlay_color = "#3498db"  # Blue
        self.selection_active_color = "#e74c3c"  # Red for active selection
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_left_click)
        self.canvas.bind("<ButtonPress-3>", self.on_canvas_right_click)
        self.canvas.bind("<Motion>", self.on_canvas_motion)

    def toggle_roi_selection(self):
        """Toggle ROI selection mode on/off"""
        self.roi_selection_mode = not self.roi_selection_mode

        # Check if ROI selection is allowed
        if hasattr(self.main_window, 'state_manager'):
            if not self.main_window.state_manager.can_select_roi():
                self.main_window.status_var.set("Cannot select ROI during analysis")
                return

            if self.main_window.state_manager.is_analysis_in_progress():
                self.main_window.status_var.set("Cannot modify ROI during analysis")
                return

        if self.roi_selection_mode:
            self.main_window.roi_btn.config(bg=self.selection_active_color)
            self.canvas.config(cursor="crosshair")
            self.main_window.status_var.set("Click to add points, right-click to finish the polygon ROI")
        else:
            self.main_window.roi_btn.config(bg="#9b59b6")  # Default purple
            self.canvas.config(cursor="")
            self.main_window.status_var.set("ROI selection mode disabled")
            self.roi_coords = []
            if self.roi_polygon:
                self.canvas.delete(self.roi_polygon)
                self.roi_polygon = None
            if self.preview_line:
                self.canvas.delete(self.preview_line)
                self.preview_line = None

    def on_canvas_left_click(self, event):
        """Add a point to the polygon ROI on left click"""
        if not self.roi_selection_mode:
            return
        display_scale = getattr(self.canvas, 'display_scale', 1.0)
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        # Store ROI points in image coordinates (always!)
        image_x = canvas_x / display_scale
        image_y = canvas_y / display_scale
        self.roi_coords.append((image_x, image_y))
        self.redraw_polygon_roi(preview_point=None)

    def on_canvas_right_click(self, event):
        """Finish the polygon ROI on right click"""
        if not self.roi_selection_mode or len(self.roi_coords) < 3:
            return
        # Close the polygon by connecting last to first
        self.redraw_polygon_roi(preview_point=None, finalize=True)
        self.roi_selection_mode = False
        self.main_window.roi_btn.config(bg="#9b59b6")
        self.canvas.config(cursor="")
        if hasattr(self.main_window, 'debug_btn'):
            self.main_window.debug_btn.config(state='normal')
        # Enable the analyze button after ROI is finished
        if hasattr(self.main_window, 'analyze_btn'):
            self.main_window.analyze_btn.config(state='normal')
        self.update_roi_info()
        self.main_window.status_var.set("Polygon ROI selected")
        self.main_window.quality_map_btn.config(state='normal')

        if hasattr(self.main_window, 'state_manager'):
            self.main_window.state_manager.update_state("roi_selected")

    def on_canvas_motion(self, event):
        """Show preview line from last point to mouse"""
        if not self.roi_selection_mode or not self.roi_coords:
            return
        display_scale = getattr(self.canvas, 'display_scale', 1.0)
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        # Convert preview point to image coordinates for consistency
        image_x = canvas_x / display_scale
        image_y = canvas_y / display_scale
        self.redraw_polygon_roi(preview_point=(image_x, image_y))

    def redraw_polygon_roi(self, preview_point=None, finalize=False):
        """Draw the polygon ROI and preview line"""
        # Remove previous drawings
        if self.roi_polygon:
            self.canvas.delete(self.roi_polygon)
            self.roi_polygon = None
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            self.preview_line = None

        # Prevent ROI perimeter from being redrawn after analyze/overlay
        if hasattr(self.main_window, 'image_display') and getattr(self.main_window.image_display, 'showing_quality_overlay', False):
            return  # Do not redraw ROI perimeter when quality map is shown

        display_scale = getattr(self.canvas, 'display_scale', 1.0)
        # Convert stored image coordinates to canvas coordinates for drawing
        scaled_coords = [(x * display_scale, y * display_scale) for (x, y) in self.roi_coords]

        if len(scaled_coords) >= 2:
            points = [coord for pt in scaled_coords for coord in pt]
            if finalize:
                self.roi_polygon = self.canvas.create_polygon(
                    *points,
                    outline=self.roi_overlay_color,
                    fill='',
                    width=2
                )
            else:
                self.roi_polygon = self.canvas.create_line(
                    *points,
                    fill=self.selection_active_color,
                    width=2
                )
                if preview_point:
                    last_x, last_y = scaled_coords[-1]
                    px, py = preview_point
                    # Convert preview_point from image to canvas coordinates
                    px_canvas, py_canvas = px * display_scale, py * display_scale
                    self.preview_line = self.canvas.create_line(
                        last_x, last_y, px_canvas, py_canvas,
                        fill=self.selection_active_color,
                        dash=(5, 5),
                        width=2
                    )
        elif len(scaled_coords) == 1 and preview_point:
            x0, y0 = scaled_coords[0]
            px, py = preview_point
            px_canvas, py_canvas = px * display_scale, py * display_scale
            self.preview_line = self.canvas.create_line(
                x0, y0, px_canvas, py_canvas,
                fill=self.selection_active_color,
                dash=(5, 5),
                width=2
            )

    def clear_roi(self):
        """Remove the current ROI selection"""
        if self.roi_polygon:
            self.canvas.delete(self.roi_polygon)
            self.roi_polygon = None
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            self.preview_line = None
        self.roi_coords = []
        self.roi_selection_mode = False

        if hasattr(self.main_window, 'roi_btn'):
            self.main_window.roi_btn.config(bg="#9b59b6")  # Reset button color

        # Disable the debug button when ROI is cleared
        if hasattr(self.main_window, 'debug_btn'):
            self.main_window.debug_btn.config(state='disabled')

        self.update_roi_info()
        self.main_window.status_var.set("ROI cleared - analyzing full image")

        if hasattr(self.main_window, 'state_manager'):
            self.main_window.state_manager.update_state("image_loaded")

    def update_roi_info(self):
        """Update the ROI information display"""
        if self.roi_coords and len(self.roi_coords) >= 3:
            # Calculate area using Shoelace formula
            xys = self.roi_coords
            area = 0.5 * abs(sum(x0*y1 - x1*y0
                                 for ((x0, y0), (x1, y1)) in zip(xys, xys[1:] + [xys[0]])))
            total_area = 0
            if hasattr(self.main_window, 'original_image') and self.main_window.original_image is not None:
                h, w = self.main_window.original_image.shape[:2]
                total_area = w * h
            percentage = (area / total_area * 100) if total_area > 0 else 0
            if hasattr(self.main_window, 'roi_info_label'):
                self.main_window.roi_info_label.config(
                    text=f"Polygon ROI: {len(self.roi_coords)} points, {area:.0f} px² ({percentage:.1f}% of image)"
                )
        else:
            # No ROI selected
            if hasattr(self.main_window, 'roi_info_label'):
                self.main_window.roi_info_label.config(
                    text="ROI: Not Selected (analyzing full image)"
                )

    def redraw_roi(self):
        """Redraw the ROI polygon after zoom or pan operations"""
        if not self.roi_coords or not hasattr(self.main_window, 'image_display'):
            return
        # Prevent ROI perimeter from being redrawn after analyze/overlay
        if getattr(self.main_window.image_display, 'showing_quality_overlay', False):
            return
        display_scale = getattr(self.canvas, 'display_scale', 1.0)
        scaled_coords = [(x * display_scale, y * display_scale) for (x, y) in self.roi_coords]
        if self.roi_polygon:
            self.canvas.delete(self.roi_polygon)
            self.roi_polygon = None
        if len(scaled_coords) >= 3:
            points = [coord for pt in scaled_coords for coord in pt]
            self.roi_polygon = self.canvas.create_polygon(
                *points,
                outline=self.roi_overlay_color,
                fill='',
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
