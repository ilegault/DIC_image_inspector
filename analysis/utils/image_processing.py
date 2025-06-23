# analysis/utils/image_processing.py

import cv2
import numpy as np
import logging
from PIL import Image
from tkinter import messagebox

logger = logging.getLogger(__name__)


def get_analysis_region(image, roi_coords=None):
    """Extract region of interest from image

    Args:
        image: Input image as numpy array
        roi_coords: Optional ROI, can be (x1, y1, x2, y2) or list of (x, y) tuples

    Returns:
        numpy.ndarray: Cropped image region or original image if no ROI
    """
    if roi_coords is None or image is None:
        return image

    if isinstance(roi_coords, (list, tuple)) and len(roi_coords) >= 3 and isinstance(roi_coords[0], (list, tuple)):
        # Polygon ROI
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        pts = np.array(roi_coords, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        if len(image.shape) == 3:
            masked = cv2.bitwise_and(image, image, mask=mask)
        else:
            masked = cv2.bitwise_and(image, image, mask=mask)
        # Optionally crop to bounding box for efficiency
        x, y, w, h = cv2.boundingRect(pts)
        return masked[y:y+h, x:x+w]
    elif isinstance(roi_coords, (list, tuple)) and len(roi_coords) == 4:
        # Rectangle ROI
        x1, y1, x2, y2 = roi_coords
        h, w = image.shape[:2]
        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)
        logger.debug(f"Extracting ROI: ({x1},{y1}) to ({x2},{y2}) from image shape {image.shape}")
        return image[y1:y2, x1:x2]
    else:
        return image


def array_to_pil_image(array):
    """Convert a numpy array to PIL image

    Args:
        array: Numpy array (grayscale, RGB, or RGBA)

    Returns:
        PIL.Image: Converted PIL image
    """
    # Convert to uint8 if not already
    if array.dtype != np.uint8:
        array = np.clip(array, 0, 255).astype(np.uint8)

    # Convert to PIL Image based on shape
    if len(array.shape) == 2:  # Grayscale
        return Image.fromarray(array, 'L')
    elif array.shape[2] == 3:  # RGB
        return Image.fromarray(array, 'RGB')
    elif array.shape[2] == 4:  # RGBA
        return Image.fromarray(array, 'RGBA')
    else:
        raise ValueError(f"Unsupported array shape: {array.shape}")


def overlay_quality_map(base_image, quality_map_data, colormap_name='JET', alpha=0.7):
    """Overlay quality map on the base image

    Args:
        base_image: Base image as numpy array
        quality_map_data: Quality map data as numpy array
        colormap_name: OpenCV colormap name (default: JET)
        alpha: Alpha blending factor (0-1)

    Returns:
        numpy.ndarray: Image with quality map overlay
    """
    from analysis.quality_map.map_generator import visualize_quality_map

    if quality_map_data is None or base_image is None:
        return base_image

    # Generate visualization overlay using the existing function
    overlay = visualize_quality_map(base_image, quality_map_data,
                                    colormap_name=colormap_name, alpha=alpha)

    return overlay


def create_quality_map_visualization(original_image, quality_map_data, roi_coords=None):
    """Create quality map visualization for the image

    Args:
        original_image: Original image as numpy array
        quality_map_data: Quality map data as numpy array
        roi_coords: Optional ROI coordinates (rectangle or polygon)

    Returns:
        numpy.ndarray: Image with quality map visualization
    """
    if quality_map_data is None:
        return original_image

    result = original_image.copy()

    if roi_coords:
        if isinstance(roi_coords, (list, tuple)) and len(roi_coords) >= 3 and isinstance(roi_coords[0], (list, tuple)):
            # Polygon ROI
            mask = np.zeros(result.shape[:2], dtype=np.uint8)
            pts = np.array(roi_coords, dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)
            x, y, w, h = cv2.boundingRect(pts)
            # Prepare quality map for the bounding box
            normalized_map = (quality_map_data * 255).astype(np.uint8)
            colormap_const = getattr(cv2, f'COLORMAP_JET', cv2.COLORMAP_JET)
            colored_map = cv2.applyColorMap(normalized_map, colormap_const)
            colored_map = cv2.cvtColor(colored_map, cv2.COLOR_BGR2RGB)
            if colored_map.shape[:2] != (h, w):
                colored_map = cv2.resize(colored_map, (w, h))
            roi_overlay = cv2.addWeighted(
                result[y:y+h, x:x+w], 0.3,
                colored_map, 0.7,
                0
            )
            # Only blend inside the polygon
            roi_mask = mask[y:y+h, x:x+w]
            blended = result[y:y+h, x:x+w].copy()
            blended[roi_mask > 0] = roi_overlay[roi_mask > 0]
            result[y:y+h, x:x+w] = blended
        elif isinstance(roi_coords, (list, tuple)) and len(roi_coords) == 4:
            # Rectangle ROI
            x1, y1, x2, y2 = roi_coords
            normalized_map = (quality_map_data * 255).astype(np.uint8)
            colormap_const = getattr(cv2, f'COLORMAP_JET', cv2.COLORMAP_JET)
            colored_map = cv2.applyColorMap(normalized_map, colormap_const)
            colored_map = cv2.cvtColor(colored_map, cv2.COLOR_BGR2RGB)
            roi_height, roi_width = y2 - y1, x2 - x1
            if colored_map.shape[:2] != (roi_height, roi_width):
                colored_map = cv2.resize(colored_map, (roi_width, roi_height))
            roi_overlay = cv2.addWeighted(
                result[y1:y2, x1:x2], 0.3,
                colored_map, 0.7,
                0
            )
            result[y1:y2, x1:x2] = roi_overlay
        else:
            # Fallback: treat as no ROI
            from analysis.quality_map.map_generator import visualize_quality_map
            result = visualize_quality_map(result, quality_map_data)
    else:
        from analysis.quality_map.map_generator import visualize_quality_map
        result = visualize_quality_map(result, quality_map_data)

    return result


def create_edge_visualization(image, roi_coords=None):
    """Create edge detection visualization of an image

    Args:
        image: Input image as numpy array
        roi_coords: Optional ROI (rectangle or polygon)

    Returns:
        numpy.ndarray: Edge visualization image
    """
    image_region = get_analysis_region(image, roi_coords)
    if len(image_region.shape) == 3:
        gray = cv2.cvtColor(image_region, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_region.copy()
    edges = cv2.Canny(gray, 50, 150)
    edge_visualization = np.zeros_like(image_region if roi_coords else image)
    if len(edge_visualization.shape) == 3:
        edge_visualization[..., 2] = edges
    else:
        edge_visualization = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    return edge_visualization


def create_gradient_visualization(image, roi_coords=None):
    """Create gradient magnitude visualization of an image

    Args:
        image: Input image as numpy array
        roi_coords: Optional ROI (rectangle or polygon)

    Returns:
        numpy.ndarray: Gradient visualization image
    """
    image_region = get_analysis_region(image, roi_coords)
    if len(image_region.shape) == 3:
        gray = cv2.cvtColor(image_region, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_region.copy()
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(grad_x, grad_y)
    cv2.normalize(magnitude, magnitude, 0, 255, cv2.NORM_MINMAX)
    gradient_vis = magnitude.astype(np.uint8)
    gradient_vis_colored = cv2.applyColorMap(gradient_vis, cv2.COLORMAP_JET)
    if len(gradient_vis_colored.shape) == 2:
        gradient_vis_colored = cv2.cvtColor(gradient_vis_colored, cv2.COLOR_GRAY2RGB)
    elif gradient_vis_colored.shape[2] == 3:
        gradient_vis_colored = cv2.cvtColor(gradient_vis_colored, cv2.COLOR_BGR2RGB)
    return gradient_vis_colored

