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


