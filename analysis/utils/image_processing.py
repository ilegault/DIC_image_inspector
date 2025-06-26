# analysis/utils/image_processing.py

import cv2
import numpy as np
import logging
from PIL import Image
from tkinter import messagebox

logger = logging.getLogger(__name__)


def get_analysis_region(image, roi_coords=None):
    """Extract region of interest from image

    NOTE: Do NOT use this to crop/mask the image before passing to the analyzer or quality map generator.
    Always analyze the full image for correct overlay and alignment.
    Only use this for extracting statistics or for edge/gradient visualizations.
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
        return masked  # Only for visualization/statistics, not for analysis!
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


def convert_roi_coords_to_image_space(roi_coords, display_scale):
    """Convert ROI coordinates from canvas/display space to image (array) space."""
    # Fix: Default display_scale to 1.0 if None or zero
    if not roi_coords or not display_scale:
        display_scale = 1.0
    return [(int(round(x / display_scale)), int(round(y / display_scale))) for (x, y) in roi_coords]


def create_quality_map_visualization(original_image, quality_map_data, roi_coords=None, display_scale=1.0):
    """
    FIXED: Create quality map visualization for the image

    The issue was that ROI polygons were being handled incorrectly, causing the
    quality map to only show in a small region instead of the full ROI area.
    """
    if quality_map_data is None or original_image is None:
        return original_image

    # Ensure both images are valid numpy arrays
    if not isinstance(original_image, np.ndarray) or not isinstance(quality_map_data, np.ndarray):
        print(f"Invalid input types: original_image={type(original_image)}, quality_map_data={type(quality_map_data)}")
        return original_image

    result = original_image.copy()

    # DEBUG: Print dimensions for troubleshooting
    print(f"DEBUG: original_image shape: {original_image.shape}")
    print(f"DEBUG: quality_map_data shape: {quality_map_data.shape}")
    print(f"DEBUG: roi_coords type: {type(roi_coords)}")
    if roi_coords:
        print(f"DEBUG: roi_coords length: {len(roi_coords)}")

    # Handle ROI visualization
    if roi_coords and isinstance(roi_coords, (list, tuple)) and len(roi_coords) >= 3:
        print("DEBUG: Processing polygon ROI")

        # Ensure ROI coords are in image space (not canvas space)
        h, w = result.shape[:2]
        max_x = max(pt[0] for pt in roi_coords)
        max_y = max(pt[1] for pt in roi_coords)

        # If any point is outside image, convert from canvas to image space
        if max_x > w or max_y > h:
            if display_scale is None or display_scale == 0:
                display_scale = 1.0
            roi_coords_img = [(int(round(x / display_scale)), int(round(y / display_scale))) for (x, y) in roi_coords]
            print(f"DEBUG: Converted ROI coords from canvas to image space")
        else:
            roi_coords_img = [(int(round(x)), int(round(y))) for (x, y) in roi_coords]

        # Create mask for ROI - this is the key fix!
        mask = np.zeros(result.shape[:2], dtype=np.uint8)
        pts = np.array(roi_coords_img, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)

        print(f"DEBUG: ROI mask created, non-zero pixels: {np.sum(mask > 0)}")

        # FIXED: Apply quality map colors to the ENTIRE quality map, then mask the result
        # This ensures we get the correct colors throughout the ROI

        # Normalize quality map for coloring
        min_val, max_val = np.min(quality_map_data), np.max(quality_map_data)
        if max_val > min_val:
            normalized_map = ((quality_map_data - min_val) / (max_val - min_val)).astype(float)
        else:
            normalized_map = np.zeros_like(quality_map_data, dtype=float)

        print(f"DEBUG: Normalized quality map range: {normalized_map.min():.4f} - {normalized_map.max():.4f}")

        # Apply DIC colormap using the same function as the main visualization
        colored_map = _apply_dic_colormap_for_roi(normalized_map)

        print(f"DEBUG: Colored map shape: {colored_map.shape}")

        # Resize colored map to match original image dimensions if needed
        if colored_map.shape[:2] != result.shape[:2]:
            colored_map = cv2.resize(colored_map, (result.shape[1], result.shape[0]))
            print(f"DEBUG: Resized colored map to: {colored_map.shape}")

        # Create blended result - ONLY in the ROI area
        blended = result.copy()
        mask_bool = mask > 0

        if np.any(mask_bool):
            print(f"DEBUG: Applying quality colors to {np.sum(mask_bool)} pixels")
            # Blend colors only in ROI region
            blended[mask_bool] = cv2.addWeighted(
                result[mask_bool].astype(np.uint8), 0.3,
                colored_map[mask_bool].astype(np.uint8), 0.7, 0
            )
        else:
            print("DEBUG: WARNING - No pixels in ROI mask!")

        result = blended

    else:
        # No ROI selected, apply to entire image
        print("DEBUG: No ROI, applying to entire image")
        try:
            from analysis.quality_map.map_generator import visualize_quality_map
            result = visualize_quality_map(result, quality_map_data)
        except Exception as e:
            print(f"Error in full image visualization: {e}")
            result = original_image

    return result


def _apply_dic_colormap_for_roi(quality_map):
    """
    Apply DIC colormap for ROI visualization

    Same logic as main colormap but ensures we handle ROI properly
    """
    h, w = quality_map.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    # Ensure quality_map is 0-1 range
    normalized = np.clip(quality_map.astype(float), 0, 1)

    print(f"DEBUG: ROI colormap input range: {normalized.min():.4f} - {normalized.max():.4f}")

    # Apply same thresholds as main visualization
    # Poor quality (0.0-0.15): Dark Red
    mask_very_poor = normalized <= 0.15
    colored[mask_very_poor] = [80, 0, 0]

    # Challenging (0.15-0.30): Red
    mask_challenging = (normalized > 0.15) & (normalized <= 0.30)
    colored[mask_challenging] = [255, 0, 0]

    # Acceptable (0.30-0.45): Orange
    mask_acceptable = (normalized > 0.30) & (normalized <= 0.45)
    colored[mask_acceptable] = [255, 165, 0]

    # Good (0.45-0.60): Yellow
    mask_good = (normalized > 0.45) & (normalized <= 0.60)
    colored[mask_good] = [255, 255, 0]

    # Very Good (0.60-0.75): Green
    mask_very_good = (normalized > 0.60) & (normalized <= 0.75)
    colored[mask_very_good] = [0, 255, 0]

    # Excellent (0.75-1.0): Blue
    mask_excellent = normalized > 0.75
    colored[mask_excellent] = [0, 100, 255]

    print(f"DEBUG: ROI color distribution:")
    print(f"  Dark Red: {np.sum(mask_very_poor)} pixels")
    print(f"  Red: {np.sum(mask_challenging)} pixels")
    print(f"  Orange: {np.sum(mask_acceptable)} pixels")
    print(f"  Yellow: {np.sum(mask_good)} pixels")
    print(f"  Green: {np.sum(mask_very_good)} pixels")
    print(f"  Blue: {np.sum(mask_excellent)} pixels")

    return colored


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