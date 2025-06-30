# analysis/utils/image_processing.py

import cv2
import numpy as np
import logging
from PIL import Image

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


def create_quality_map_visualization(original_image, quality_map_data, roi_coords=None, display_scale=1.0,
                                     spectrum_type='custom_dic'):
    """
    FIXED: Create quality map visualization with proper spectrum support

    Args:
        original_image: Original image array
        quality_map_data: Quality map data (0-1 normalized)
        roi_coords: ROI coordinates (optional polygon points)
        display_scale: Display scale factor (for coordinate conversion)
        spectrum_type: Color spectrum type to use

    Returns:
        numpy.ndarray: RGB image with quality overlay
    """
    if quality_map_data is None or original_image is None:
        print("No quality map data or original image provided")
        return original_image

    # Validate inputs
    if not isinstance(original_image, np.ndarray) or not isinstance(quality_map_data, np.ndarray):
        print(f"Invalid input types: original_image={type(original_image)}, quality_map_data={type(quality_map_data)}")
        return original_image

    result = original_image.copy()

    print(f"Creating quality map visualization:")
    print(f"  Spectrum type: {spectrum_type}")
    print(f"  Original image shape: {original_image.shape}")
    print(f"  Quality map shape: {quality_map_data.shape}")
    print(f"  Quality range: {quality_map_data.min():.4f} - {quality_map_data.max():.4f}")

    # Handle ROI-specific visualization
    if roi_coords and isinstance(roi_coords, (list, tuple)) and len(roi_coords) >= 3:
        print("Processing polygon ROI visualization")
        return _create_roi_quality_visualization(result, quality_map_data, roi_coords, display_scale, spectrum_type)
    else:
        # No ROI - apply to entire image
        print("Processing full image visualization")
        return _create_full_image_quality_visualization(result, quality_map_data, spectrum_type)

def _create_full_image_quality_visualization(original_image, quality_map_data, spectrum_type):
    """Create quality visualization for full image"""
    try:
        # Use the main visualization function from map_generator
        from analysis.quality_map.map_generator import _create_quality_visualization
        result = _create_quality_visualization(original_image, quality_map_data, spectrum_type, alpha=0.7)
        print(f"Created full image visualization with {spectrum_type}")
        return result
    except ImportError as e:
        print(f"Import error for full image visualization: {e}")
        # Fallback to basic visualization
        return _create_basic_full_image_visualization(original_image, quality_map_data)
    except Exception as e:
        print(f"Error in full image visualization: {e}")
        return original_image


def _apply_spectrum_for_roi(quality_map, spectrum_type):
    """Apply selected spectrum for ROI visualization"""

    # Import the spectrum functions from map_generator
    from analysis.quality_map.map_generator import (
        _create_smooth_rainbow_spectrum,
        _create_thermal_spectrum,
        _create_viridis_like_spectrum,
        _create_custom_dic_spectrum,
        _create_opencv_spectrum
    )

    if spectrum_type == 'smooth_rainbow':
        return _create_smooth_rainbow_spectrum(quality_map)
    elif spectrum_type == 'thermal':
        return _create_thermal_spectrum(quality_map)
    elif spectrum_type == 'viridis_like':
        return _create_viridis_like_spectrum(quality_map)
    elif spectrum_type == 'custom_dic':
        return _create_custom_dic_spectrum(quality_map)
    elif spectrum_type == 'opencv_jet':
        return _create_opencv_spectrum(quality_map, cv2.COLORMAP_JET)
    elif spectrum_type == 'opencv_viridis':
        return _create_opencv_spectrum(quality_map, cv2.COLORMAP_VIRIDIS)
    elif spectrum_type == 'opencv_plasma':
        return _create_opencv_spectrum(quality_map, cv2.COLORMAP_PLASMA)
    elif spectrum_type == 'opencv_inferno':
        return _create_opencv_spectrum(quality_map, cv2.COLORMAP_INFERNO)
    else:
        # Default to custom DIC spectrum
        return _create_custom_dic_spectrum(quality_map)


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


def _create_roi_quality_visualization(original_image, quality_map_data, roi_coords, display_scale, spectrum_type):
    """Create quality visualization for ROI region only"""
    h, w = original_image.shape[:2]

    print(f"Creating ROI visualization: image {h}x{w}, {len(roi_coords)} ROI points")

    # Convert ROI coordinates to image space if needed
    max_x = max(pt[0] for pt in roi_coords)
    max_y = max(pt[1] for pt in roi_coords)

    if max_x > w or max_y > h:
        # Convert from canvas space to image space
        if display_scale is None or display_scale == 0:
            display_scale = 1.0
        roi_coords_img = [(int(round(x / display_scale)), int(round(y / display_scale))) for (x, y) in roi_coords]
        print(f"Converted ROI coords from canvas to image space (scale: {display_scale})")
    else:
        roi_coords_img = [(int(round(x)), int(round(y))) for (x, y) in roi_coords]

    # Clamp coordinates to image bounds
    roi_coords_img = [(max(0, min(w - 1, x)), max(0, min(h - 1, y))) for (x, y) in roi_coords_img]

    print(f"ROI coords in image space: {roi_coords_img[:2]}...{roi_coords_img[-2:] if len(roi_coords_img) > 2 else []}")

    # Create mask for ROI
    mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array(roi_coords_img, dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)

    roi_pixel_count = np.sum(mask > 0)
    print(f"ROI mask created: {roi_pixel_count} pixels")

    if roi_pixel_count == 0:
        print("WARNING: ROI mask is empty!")
        return original_image

    # Normalize quality map data
    min_val, max_val = np.min(quality_map_data), np.max(quality_map_data)
    if max_val > min_val:
        normalized_map = ((quality_map_data - min_val) / (max_val - min_val)).astype(float)
    else:
        normalized_map = np.zeros_like(quality_map_data, dtype=float)

    print(f"Normalized quality map: {normalized_map.min():.4f} - {normalized_map.max():.4f}")

    # Apply spectrum colormap to the full quality map
    try:
        from analysis.quality_map.map_generator import _apply_dic_colormap
        colored_map = _apply_dic_colormap(normalized_map, spectrum_type)
        print(f"Applied {spectrum_type} colormap successfully")
    except ImportError as e:
        print(f"Import error for colormap: {e}")
        # Fallback to basic colormap
        colored_map = _apply_basic_colormap(normalized_map)

    # Resize colored map to match original image if needed
    if colored_map.shape[:2] != (h, w):
        colored_map = cv2.resize(colored_map, (w, h))
        print(f"Resized colored map to match image: {colored_map.shape}")

    # Apply colored overlay only to ROI region
    result = original_image.copy()
    mask_bool = mask > 0

    if np.any(mask_bool):
        # Blend colors only in ROI area with proper alpha blending
        alpha = 0.7  # Overlay strength
        result[mask_bool] = cv2.addWeighted(
            original_image[mask_bool].astype(np.uint8), 1 - alpha,
            colored_map[mask_bool].astype(np.uint8), alpha, 0
        )
        print(f"Applied {spectrum_type} overlay to {np.sum(mask_bool)} ROI pixels")

    return result


def _apply_basic_colormap(quality_map):
    """Basic fallback colormap if imports fail"""
    print("Using basic fallback colormap")
    h, w = quality_map.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    # Simple red to blue progression
    normalized = np.clip(quality_map, 0, 1)

    # Red component (high when quality is low)
    colored[:, :, 0] = ((1 - normalized) * 255).astype(np.uint8)

    # Green component (peak in middle)
    green_mask = (normalized > 0.3) & (normalized < 0.7)
    colored[green_mask, 1] = 255

    # Blue component (high when quality is high)
    colored[:, :, 2] = (normalized * 255).astype(np.uint8)

    return colored


def _create_basic_full_image_visualization(original_image, quality_map_data):
    """Basic fallback for full image visualization"""
    print("Using basic fallback full image visualization")

    # Apply basic colormap
    colored_map = _apply_basic_colormap(quality_map_data)

    # Resize if needed
    if colored_map.shape[:2] != original_image.shape[:2]:
        colored_map = cv2.resize(colored_map, (original_image.shape[1], original_image.shape[0]))

    # Blend with original
    result = cv2.addWeighted(original_image, 0.3, colored_map, 0.7, 0)

    return result


def create_quality_map_visualization_with_spectrum(original_image, quality_map_data, roi_coords=None,
                                                   display_scale=1.0, spectrum_type='custom_dic'):
    """
    Wrapper function for spectrum-aware quality map visualization
    """
    return create_quality_map_visualization(
        original_image, quality_map_data, roi_coords, display_scale, spectrum_type
    )

