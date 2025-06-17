

import cv2
import numpy as np
from PIL import Image
from tkinter import messagebox

def generate_subset_quality_map(image, subset_size=21):
    """Generates quality map based on subset analysis"""

def generate_multi_metric_map(image, metrics_list):
    """Creates multiple quality maps for different metrics"""

def _generate_quality_map(self, roi):
        """Generate a quality map for the ROI with pixel-by-pixel analysis"""
        # Convert to grayscale if needed
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        else:
            gray = roi.copy()

        # Create an empty quality map (normalized to 0-1)
        quality_map = np.zeros_like(gray, dtype=float)

        # Window size for local analysis
        window_size = 15
        half_window = window_size // 2

        # Pad the image to handle borders
        padded = cv2.copyMakeBorder(gray, half_window, half_window, half_window, half_window,
                                    cv2.BORDER_REFLECT)

        h, w = gray.shape

        # Calculate gradient magnitude for the entire image
        grad_x = cv2.Sobel(padded, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(padded, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)

        # Perform local analysis
        for y in range(h):
            for x in range(w):
                # Extract local window from padded image
                window = padded[y:y + window_size, x:x + window_size]
                grad_window = grad_mag[y:y + window_size, x:x + window_size]

                # Calculate local quality metrics
                local_contrast = np.std(window) / (np.mean(window) + 1e-5)
                local_gradient = np.mean(grad_window)

                # Simple quality score based on contrast and gradient
                quality = (local_contrast * 0.5 + local_gradient / 50 * 0.5)
                quality_map[y, x] = quality

        # Normalize quality map to 0-1 range
        if np.max(quality_map) > 0:
            quality_map = quality_map / np.max(quality_map)

        return quality_map

def show_quality_map(self, preserve_view=True):
    """Show quality map using the new subset-based approach"""
    if not self.main_window or self.main_window.original_image is None:
        return

    # Check if ROI exists
    if not hasattr(self.main_window, 'roi_handler') or not self.main_window.roi_handler.roi_coords:
        messagebox.showinfo("Information", "Please select a ROI first to generate a quality map")
        return

    # Get the ROI from the handler
    roi_coords = self.main_window.roi_handler.roi_coords

    # Extract the ROI from the original image
    analysis_region = get_analysis_region(self.main_window.original_image, roi_coords)

    # Use new modular approach for map generation
    from analysis.analyzer import DICAnalyzer
    analyzer = DICAnalyzer()

    # This will use subset-based analysis internally
    quality_map = analyzer.generate_quality_map(analysis_region)

    # Display the map
    self._display_quality_map(quality_map, roi_coords, preserve_view)