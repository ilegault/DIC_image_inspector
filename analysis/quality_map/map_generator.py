import cv2
import numpy as np
from PIL import Image
from tkinter import messagebox


def get_analysis_region(image, roi_coords):
    """Extract ROI from image based on coordinates"""
    x1, y1, x2, y2 = roi_coords
    return image[y1:y2, x1:x2]


def apply_colormap(quality_map, colormap=cv2.COLORMAP_JET):
    """Apply colormap to quality map for visualization"""
    # Ensure map is in 0-255 range for colormap
    if quality_map.dtype != np.uint8:
        quality_map = (quality_map * 255).astype(np.uint8)

    # Apply colormap
    colored_map = cv2.applyColorMap(quality_map, colormap)
    return colored_map


def generate_quality_map(image, window_size=15):
    """Generate a quality map for the provided image"""
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    # Create an empty quality map (normalized to 0-1)
    quality_map = np.zeros_like(gray, dtype=float)

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


def generate_subset_quality_map(image, subset_size=21):
    """Generates quality map based on subset analysis"""
    # Implementation using the window-based approach
    return generate_quality_map(image, window_size=subset_size)


def generate_multi_metric_map(image, metrics_list):
    """Creates multiple quality maps for different metrics"""
    maps = []
    for metric_name in metrics_list:
        if metric_name == "contrast":
            # Create contrast-focused map
            maps.append(generate_quality_map(image))
        # Add other metrics as needed

    return maps

# The following functions should be part of a class elsewhere
# They are included here for reference but commented out to avoid errors

# def show_quality_map(self, preserve_view=True):
#     """Show quality map using the new subset-based approach"""
#     if not self.main_window or self.main_window.original_image is None:
#         return
#
#     # Check if ROI exists
#     if not hasattr(self.main_window, 'roi_handler') or not self.main_window.roi_handler.roi_coords:
#         messagebox.showinfo("Information", "Please select a ROI first to generate a quality map")
#         return
#
#     # Get the ROI from the handler
#     roi_coords = self.main_window.roi_handler.roi_coords
#
#     # Extract the ROI from the original image
#     analysis_region = get_analysis_region(self.main_window.original_image, roi_coords)
#
#     # Use new modular approach for map generation
#     from analysis.analyzer import DICAnalyzer
#     analyzer = DICAnalyzer()
#
#     # This will use subset-based analysis internally
#     quality_map = analyzer.generate_quality_map(analysis_region)
#
#     # Display the map
#     self._display_quality_map(quality_map, roi_coords, preserve_view)