import cv2
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk
from utils.image_processing import get_analysis_region


class ImageDisplay:
    def __init__(self, canvas):
        self.canvas = canvas
        self.displayed_image = None
        self.photo = None

    def display_image(self, pil_image):
        """Display image on canvas"""
        # Resize for display if too large
        display_image = pil_image.copy()
        max_size = 800

        if max(display_image.size) > max_size:
            ratio = max_size / max(display_image.size)
            new_size = (int(display_image.size[0] * ratio), int(display_image.size[1] * ratio))
            display_image = display_image.resize(new_size, Image.Resampling.LANCZOS)
            self.display_scale = ratio
        else:
            self.display_scale = 1.0

        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(display_image)

        # Clear canvas and display image
        self.canvas.delete('all')
        image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

        # Ensure scroll region is set to the image dimensions
        self.canvas.configure(scrollregion=(0, 0, self.photo.width(), self.photo.height()))

        # Force canvas to update
        self.canvas.update_idletasks()

        # Reset view to top-left
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # Ensure the image is visible
        self.displayed_image = display_image

    def start_roi_selection(self, event):
        """Start ROI selection on canvas"""
        if not self.roi_selection_mode or self.original_image is None:
            return

        # Get canvas coordinates
        canvas_x = self.image_canvas.canvasx(event.x)
        canvas_y = self.image_canvas.canvasy(event.y)

        self.roi_start = (canvas_x, canvas_y)

        # Clear previous ROI rectangle
        if self.roi_rect:
            self.image_canvas.delete(self.roi_rect)

    def update_roi_selection(self, event):
        """Update ROI selection rectangle"""
        if not self.roi_selection_mode or not self.roi_start:
            return

        # Get canvas coordinates
        canvas_x = self.image_canvas.canvasx(event.x)
        canvas_y = self.image_canvas.canvasy(event.y)

        # Clear previous rectangle
        if self.roi_rect:
            self.image_canvas.delete(self.roi_rect)

        # Draw new rectangle
        self.roi_rect = self.image_canvas.create_rectangle(
            self.roi_start[0], self.roi_start[1], canvas_x, canvas_y,
            outline='red', width=2, dash=(5, 5)
        )

    def end_roi_selection(self, event):
        """End ROI selection and store coordinates"""
        if not self.roi_selection_mode or not self.roi_start:
            return

        # Get canvas coordinates
        canvas_x = self.image_canvas.canvasx(event.x)
        canvas_y = self.image_canvas.canvasy(event.y)

        # Calculate scaling factor between displayed image and original
        if hasattr(self, 'display_scale'):
            scale = 1.0 / self.display_scale
        else:
            scale = 1.0

        # Convert canvas coordinates to image coordinates
        x1 = int(min(self.roi_start[0], canvas_x) * scale)
        y1 = int(min(self.roi_start[1], canvas_y) * scale)
        x2 = int(max(self.roi_start[0], canvas_x) * scale)
        y2 = int(max(self.roi_start[1], canvas_y) * scale)

        # Ensure coordinates are within image bounds
        h, w = self.original_image.shape[:2]
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(0, min(x2, w - 1))
        y2 = max(0, min(y2, h - 1))

        # Store ROI if it's large enough
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            self.roi_coords = (x1, y1, x2, y2)
            self.update_roi_info()
            self.status_var.set(f"ROI Selected: {x2 - x1}x{y2 - y1} pixels - Ready for analysis")
        else:
            self.status_var.set("ROI too small - please select a larger area")

        # Turn off ROI selection mode
        self.roi_btn.config(text="🎯 Select ROI", bg='#9b59b6')
        self.roi_selection_mode = False

    def get_analysis_region(self):
        """Get the region of the image to analyze"""
        if self.roi_coords:
            x1, y1, x2, y2 = self.roi_coords
            if len(self.original_image.shape) == 3:
                return self.original_image[y1:y2, x1:x2]
            else:
                return self.original_image[y1:y2, x1:x2]
        else:
            return self.original_image


