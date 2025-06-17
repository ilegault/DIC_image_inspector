# roi_handler.py

from ui.image_display import ImageDisplay

class ROIHandler:
    def __init__(self, main_window):
        """Initialize with a reference to the main window"""
        self.main_window = main_window
        self.canvas = main_window.image_canvas  # Store the canvas reference
        self.roi_rect = None
        self.roi_coords = None
        self.roi_selection_mode = False
        self.roi_start = None

    def toggle_roi_selection(self):
        """Toggle ROI selection mode"""
        self.roi_selection_mode = not self.roi_selection_mode
        if self.roi_selection_mode:
            self.main_window.roi_btn.config(bg='#e74c3c')  # Red when active
            self.main_window.status_var.set("ROI selection mode: Click and drag to select analysis region")
            self.canvas.config(cursor="crosshair")
        else:
            self.main_window.roi_btn.config(bg='#9b59b6')  # Purple when inactive
            self.main_window.status_var.set("ROI selection mode disabled")
            self.canvas.config(cursor="")

    def start_roi_selection(self, event):
        """Start ROI selection"""
        if not self.roi_selection_mode:
            return

        # Convert window coordinates to canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.roi_start = (x, y)

        # Clear any existing ROI
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)
            self.roi_rect = None
            self.roi_coords = None

    def update_roi_selection(self, event):
        """Update ROI during selection"""
        if not self.roi_selection_mode or not self.roi_start:
            return

        # Convert window coordinates to canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Delete previous rectangle
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)

        # Draw new rectangle
        self.roi_rect = self.canvas.create_rectangle(
            self.roi_start[0], self.roi_start[1], x, y,
            outline='red', width=2, dash=(4, 4))

    def end_roi_selection(self, event):
        """Finish ROI selection"""
        if not self.roi_selection_mode or not self.roi_start:
            return

        # Convert window coordinates to canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Ensure x1 < x2 and y1 < y2
        x1 = min(self.roi_start[0], x)
        y1 = min(self.roi_start[1], y)
        x2 = max(self.roi_start[0], x)
        y2 = max(self.roi_start[1], y)

        # Minimum ROI size check
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            # ROI too small, clear it
            self.canvas.delete(self.roi_rect)
            self.roi_rect = None
            self.roi_coords = None
            self.update_roi_info()
            return

        # Get display scale from canvas
        display_scale = getattr(self.canvas, 'display_scale', 1.0)

        # Convert from displayed coordinates to original image coordinates
        orig_x1 = int(x1 / display_scale)
        orig_y1 = int(y1 / display_scale)
        orig_x2 = int(x2 / display_scale)
        orig_y2 = int(y2 / display_scale)

        # Store ROI in original image coordinates
        self.roi_coords = (orig_x1, orig_y1, orig_x2, orig_y2)

        # Update ROI info display
        self.update_roi_info()

        # Exit ROI selection mode
        self.roi_selection_mode = False
        self.main_window.roi_btn.config(bg='#9b59b6')  # Purple when inactive
        self.canvas.config(cursor="")

        # Update status
        width = orig_x2 - orig_x1
        height = orig_y2 - orig_y1
        self.main_window.status_var.set(f"ROI selected: {width}x{height} pixels at ({orig_x1},{orig_y1})")

    def update_roi_info(self):
        """Update ROI information label"""
        if self.roi_coords:
            x1, y1, x2, y2 = self.roi_coords
            width = x2 - x1
            height = y2 - y1
            self.main_window.roi_info_label.config(
                text=f"ROI: {width}x{height} pixels at ({x1},{y1})")
        else:
            self.main_window.roi_info_label.config(
                text="ROI: Not Selected (analyzing full image)")

    def clear_roi(self):
        """Clear the current ROI"""
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)
            self.roi_rect = None
            self.roi_coords = None
            self.update_roi_info()
            self.main_window.status_var.set("ROI cleared - full image will be analyzed")

    def redraw_roi(self):
        """Redraw ROI on the canvas after image changes/zoom"""
        if not self.roi_coords:
            return

        # Clear existing ROI rectangle
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)

        # Get current display scale from canvas
        display_scale = getattr(self.canvas, 'display_scale', 1.0)

        # Convert from original image coordinates to current display coordinates
        x1, y1, x2, y2 = self.roi_coords
        disp_x1 = int(x1 * display_scale)
        disp_y1 = int(y1 * display_scale)
        disp_x2 = int(x2 * display_scale)
        disp_y2 = int(y2 * display_scale)

        # Draw new rectangle
        self.roi_rect = self.canvas.create_rectangle(
            disp_x1, disp_y1, disp_x2, disp_y2,
            outline='red', width=2, dash=(4, 4))

        # Make sure ROI is visible
        self.canvas.tag_raise(self.roi_rect)

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

    def debug_roi_coords(self):
        """Print current ROI coordinates and scales for debugging"""
        if self.roi_coords:
            display_scale = getattr(self.canvas, 'display_scale', 1.0)
            zoom_level = getattr(self.main_window.image_display, 'zoom_level', 1.0)
            roi = self.roi_coords
            print(f"ROI: {roi} | Display scale: {display_scale} | Zoom: {zoom_level}")

    def get_subset_grid(self):
        """Return a grid of subset coordinates based on the ROI"""
        if not self.roi_coords:
            return None

        from analysis.core.subset_analyzer import determine_optimal_subset_size

        x1, y1, x2, y2 = self.roi_coords
        roi_width = x2 - x1
        roi_height = y2 - y1

        # Get ROI from the main image
        roi_image = self.main_window.original_image[y1:y2, x1:x2]

        # Find optimal subset size for this ROI
        subset_size = determine_optimal_subset_size(roi_image)

        # Create grid with 50% overlap
        step_size = subset_size // 2

        subsets = []
        for y in range(0, roi_height - subset_size + 1, step_size):
            for x in range(0, roi_width - subset_size + 1, step_size):
                # Global coordinates (within the original image)
                global_x1 = x1 + x
                global_y1 = y1 + y
                global_x2 = global_x1 + subset_size
                global_y2 = global_y1 + subset_size

                subsets.append((global_x1, global_y1, global_x2, global_y2))

        return subsets, subset_size

    def show_subset_grid(self):
        """Visualize the subset grid on the canvas"""
        if not self.roi_coords:
            return

        # Clear previous subset visualization
        for item in getattr(self, 'subset_rects', []):
            self.canvas.delete(item)

        # Get subset grid
        subsets, _ = self.get_subset_grid()
        if not subsets:
            return

        # Display scale for converting image coordinates to canvas coordinates
        display_scale = getattr(self.canvas, 'display_scale', 1.0)

        # Draw each subset as a rectangle
        self.subset_rects = []
        for x1, y1, x2, y2 in subsets:
            # Convert to canvas coordinates
            canvas_x1 = int(x1 * display_scale)
            canvas_y1 = int(y1 * display_scale)
            canvas_x2 = int(x2 * display_scale)
            canvas_y2 = int(y2 * display_scale)

            # Draw rectangle (dotted line, lighter than ROI)
            rect = self.canvas.create_rectangle(
                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                outline='yellow', width=1, dash=(2, 4))
            self.subset_rects.append(rect)