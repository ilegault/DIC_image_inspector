# roi_handler.py

class ROIHandler:
    def __init__(self, main_window):
        """Initialize with a reference to the main window"""
        self.main_window = main_window
        self.roi_selection_mode = False
        self.roi_start = None
        self.roi_rect = None
        self.roi_coords = None
        self.main_window.image_canvas.bind("<ButtonPress-1>", self.start_roi_selection)
        self.main_window.image_canvas.bind("<B1-Motion>", self.update_roi_selection)
        self.main_window.image_canvas.bind("<ButtonRelease-1>", self.end_roi_selection)
        self.main_window.roi_btn.config(command=self.toggle_roi_selection)

    def toggle_roi_selection(self):
        """Toggle ROI selection mode"""
        self.roi_selection_mode = not self.roi_selection_mode
        if self.roi_selection_mode:
            self.main_window.roi_btn.config(text="🎯 ROI Mode ON", bg='#e74c3c')
            self.main_window.status_var.set(
                "ROI Selection Mode: Click and drag on the image to select the analysis region")
        else:
            self.main_window.roi_btn.config(text="🎯 Select ROI", bg='#9b59b6')
            self.main_window.status_var.set("ROI Selection Mode OFF")

    def start_roi_selection(self, event):
        """Start ROI selection on canvas"""
        if not self.roi_selection_mode or self.main_window.original_image is None:
            return

        # Get canvas coordinates
        canvas_x = self.main_window.image_canvas.canvasx(event.x)
        canvas_y = self.main_window.image_canvas.canvasy(event.y)

        self.roi_start = (canvas_x, canvas_y)

        # Clear previous ROI rectangle
        if self.roi_rect:
            self.main_window.image_canvas.delete(self.roi_rect)

    def update_roi_selection(self, event):
        """Update ROI selection rectangle"""
        if not self.roi_selection_mode or not self.roi_start:
            return

        # Get canvas coordinates
        canvas_x = self.main_window.image_canvas.canvasx(event.x)
        canvas_y = self.main_window.image_canvas.canvasy(event.y)

        # Clear previous rectangle
        if self.roi_rect:
            self.main_window.image_canvas.delete(self.roi_rect)

        # Draw new rectangle
        self.roi_rect = self.main_window.image_canvas.create_rectangle(
            self.roi_start[0], self.roi_start[1], canvas_x, canvas_y,
            outline='red', width=2, dash=(5, 5)
        )

    def end_roi_selection(self, event):
        """End ROI selection and store coordinates"""
        if not self.roi_selection_mode or not self.roi_start:
            return

        # Get canvas coordinates
        canvas_x = self.main_window.image_canvas.canvasx(event.x)
        canvas_y = self.main_window.image_canvas.canvasy(event.y)

        # Calculate scaling factor between displayed image and original
        scale = getattr(self.main_window.image_canvas, 'display_scale', 1.0)

        # Convert canvas coordinates to image coordinates
        x1 = int(min(self.roi_start[0], canvas_x) / scale)
        y1 = int(min(self.roi_start[1], canvas_y) / scale)
        x2 = int(max(self.roi_start[0], canvas_x) / scale)
        y2 = int(max(self.roi_start[1], canvas_y) / scale)

        # Ensure coordinates are within image bounds
        h, w = self.main_window.original_image.shape[:2]
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(0, min(x2, w - 1))
        y2 = max(0, min(y2, h - 1))

        # Store ROI if it's large enough
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            self.roi_coords = (x1, y1, x2, y2)
            self.update_roi_info()
            self.main_window.status_var.set(f"ROI Selected: {x2 - x1}x{y2 - y1} pixels - Ready for analysis")
        else:
            self.main_window.status_var.set("ROI too small - please select a larger area")

        # Turn off ROI selection mode
        self.main_window.roi_btn.config(text="🎯 Select ROI", bg='#9b59b6')
        self.roi_selection_mode = False

    def clear_roi(self):
        """Clear the current ROI selection"""
        self.roi_coords = None
        if self.roi_rect:
            self.main_window.image_canvas.delete(self.roi_rect)
            self.roi_rect = None
        self.update_roi_info()
        self.main_window.status_var.set("ROI cleared - will analyze full image")

    def update_roi_info(self):
        """Update ROI information display"""
        if self.roi_coords:
            x1, y1, x2, y2 = self.roi_coords
            self.main_window.roi_info_label.config(text=f"ROI: {x2 - x1}x{y2 - y1} pixels at ({x1},{y1})")
        else:
            self.main_window.roi_info_label.config(text="ROI: Not Selected (analyzing full image)")