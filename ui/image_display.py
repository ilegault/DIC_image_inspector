# image_display.py

import cv2
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk
from analysis.metrics import get_analysis_region

class ImageDisplay:
    def __init__(self, canvas, main_window=None):
        self.canvas = canvas
        self.main_window = main_window  # Reference to main window
        self.displayed_image = None
        self.photo = None
        self.display_scale = 1.0

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

        # Store the display scale on the canvas for ROI handler to use
        self.canvas.display_scale = self.display_scale

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

    def show_original(self):
        """Show the original image."""
        if self.main_window and self.main_window.original_image is not None:
            self.main_window.current_image = self.main_window.original_image.copy()
            pil_image = Image.fromarray(self.main_window.current_image)
            self.display_image(pil_image)

    def show_edges(self):
        """Show edge-enhanced image."""
        if self.main_window and self.main_window.original_image is not None:
            # Get analysis region
            analysis_region = get_analysis_region(
                self.main_window.original_image, self.main_window.roi_coords)

            # Convert to grayscale
            if len(analysis_region.shape) == 3:
                gray = cv2.cvtColor(analysis_region, cv2.COLOR_RGB2GRAY)
            else:
                gray = analysis_region

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Convert back to RGB for display
            edge_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

            # If ROI is selected, create a composite image
            if self.main_window.roi_coords:
                composite = self.main_window.original_image.copy()
                x1, y1, x2, y2 = self.main_window.roi_coords
                composite[y1:y2, x1:x2] = edge_rgb
                self.main_window.current_image = composite
            else:
                self.main_window.current_image = edge_rgb

            # Display the processed image
            pil_image = Image.fromarray(self.main_window.current_image)
            self.display_image(pil_image)

    def show_gradient(self):
        """Show gradient magnitude image."""
        if self.main_window and self.main_window.original_image is not None:
            # Get analysis region
            analysis_region = get_analysis_region(
                self.main_window.original_image, self.main_window.roi_coords)

            # Convert to grayscale
            if len(analysis_region.shape) == 3:
                gray = cv2.cvtColor(analysis_region, cv2.COLOR_RGB2GRAY)
            else:
                gray = analysis_region

            # Calculate gradient
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

            # Normalize to 0-255
            gradient_normalized = cv2.normalize(gradient_magnitude, None, 0, 255, cv2.NORM_MINMAX)
            gradient_normalized = gradient_normalized.astype(np.uint8)

            # Convert to RGB
            gradient_rgb = cv2.cvtColor(gradient_normalized, cv2.COLOR_GRAY2RGB)

            # If we have ROI, create a composite image
            if self.main_window.roi_coords:
                composite = self.main_window.original_image.copy()
                x1, y1, x2, y2 = self.main_window.roi_coords
                composite[y1:y2, x1:x2] = gradient_rgb
                self.main_window.current_image = composite
            else:
                self.main_window.current_image = gradient_rgb

            pil_image = Image.fromarray(self.main_window.current_image)
            self.display_image(pil_image)