import numpy as np

def get_analysis_region(image, roi_coords):
    """Extract region of interest from image"""
    if roi_coords is None:
        return image

    x1, y1, x2, y2 = roi_coords
    return image[y1:y2, x1:x2]