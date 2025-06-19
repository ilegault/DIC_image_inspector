# analysis/utils/image_processing.py

import cv2
import numpy as np
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def get_analysis_region(image, roi_coords=None):
    """Extract region of interest from image

    Args:
        image: Input image as numpy array
        roi_coords: Optional tuple of (x1, y1, x2, y2) coordinates

    Returns:
        numpy.ndarray: Cropped image region or original image if no ROI
    """
    if roi_coords is None or image is None:
        return image

    x1, y1, x2, y2 = roi_coords

    # Ensure coordinates are within image bounds
    h, w = image.shape[:2]
    x1, x2 = max(0, x1), min(w, x2)
    y1, y2 = max(0, y1), min(h, y2)

    logger.debug(f"Extracting ROI: ({x1},{y1}) to ({x2},{y2}) from image shape {image.shape}")

    return image[y1:y2, x1:x2]


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
        roi_coords: Optional ROI coordinates (x1, y1, x2, y2)

    Returns:
        numpy.ndarray: Image with quality map visualization
    """
    if quality_map_data is None:
        return original_image

    # Make a copy to avoid modifying the original
    result = original_image.copy()

    # Apply quality map only to ROI if specified
    if roi_coords:
        x1, y1, x2, y2 = roi_coords

        # Create a colored version of the quality map
        normalized_map = (quality_map_data * 255).astype(np.uint8)
        colormap_const = getattr(cv2, f'COLORMAP_JET', cv2.COLORMAP_JET)
        colored_map = cv2.applyColorMap(normalized_map, colormap_const)
        colored_map = cv2.cvtColor(colored_map, cv2.COLOR_BGR2RGB)

        # Extract the ROI region
        roi_height, roi_width = y2 - y1, x2 - x1

        # Make sure quality map has the right dimensions for the ROI
        if colored_map.shape[:2] != (roi_height, roi_width):
            colored_map = cv2.resize(colored_map, (roi_width, roi_height))

        # Create blended overlay just for the ROI region
        roi_overlay = cv2.addWeighted(
            result[y1:y2, x1:x2], 0.3,  # Keep 30% of original
            colored_map, 0.7,  # Add 70% of quality map
            0
        )

        # Apply the overlay only to the ROI region
        result[y1:y2, x1:x2] = roi_overlay
    else:
        # No ROI selected, apply to entire image
        from analysis.quality_map.map_generator import visualize_quality_map
        result = visualize_quality_map(result, quality_map_data)

    return result


def create_edge_visualization(image, roi_coords=None):
    """Create edge detection visualization of an image

    Args:
        image: Input image as numpy array
        roi_coords: Optional tuple of (x1, y1, x2, y2) coordinates

    Returns:
        numpy.ndarray: Edge visualization image
    """
    # Get the appropriate image region based on ROI
    image_region = get_analysis_region(image, roi_coords)

    # Convert to grayscale if needed
    if len(image_region.shape) == 3:
        gray = cv2.cvtColor(image_region, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_region.copy()

    # Apply Canny edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Create a colored edge visualization
    edge_visualization = np.zeros_like(image)
    if len(image.shape) == 3:
        # For color images, create colored edge overlay
        edge_visualization[..., 2] = edges  # Set red channel to edges
    else:
        # For grayscale, create RGB visualization
        edge_visualization = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

    return edge_visualization


def create_gradient_visualization(image, roi_coords=None):
    """Create gradient magnitude visualization of an image

    Args:
        image: Input image as numpy array
        roi_coords: Optional tuple of (x1, y1, x2, y2) coordinates

    Returns:
        numpy.ndarray: Gradient visualization image
    """
    # Get the appropriate image region based on ROI
    image_region = get_analysis_region(image, roi_coords)

    # Convert to grayscale if needed
    if len(image_region.shape) == 3:
        gray = cv2.cvtColor(image_region, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_region.copy()

    # Calculate gradients
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    # Calculate gradient magnitude
    magnitude = cv2.magnitude(grad_x, grad_y)

    # Normalize for visualization
    cv2.normalize(magnitude, magnitude, 0, 255, cv2.NORM_MINMAX)
    gradient_vis = magnitude.astype(np.uint8)

    # Apply colormap for better visualization
    gradient_vis_colored = cv2.applyColorMap(gradient_vis, cv2.COLORMAP_JET)

    # Convert to RGB if needed
    if len(gradient_vis_colored.shape) == 2:
        gradient_vis_colored = cv2.cvtColor(gradient_vis_colored, cv2.COLOR_GRAY2RGB)
    elif gradient_vis_colored.shape[2] == 3:
        gradient_vis_colored = cv2.cvtColor(gradient_vis_colored, cv2.COLOR_BGR2RGB)

    return gradient_vis_colored


def save_debug_visualizations(original_image, roi_coords, output_dir="debug_output", prefix="debug",
                              save_intermediate_steps=True):
    """Save visual representations of ROI processing steps for debugging

    Args:
        original_image: Input image as numpy array
        roi_coords: Tuple of (x1, y1, x2, y2) coordinates
        output_dir: Directory to save debug images
        prefix: Prefix for saved image filenames
        save_intermediate_steps: If True, save preprocessing and thresholding steps

    Returns:
        dict: Paths to saved debug images
    """
    import os
    import datetime
    from pathlib import Path

    # Create unique timestamp for this debug session
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = f"{prefix}_{timestamp}"
    output_path = Path(output_dir) / session_dir

    # Create directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    # Extract ROI from original image
    roi_image = get_analysis_region(original_image, roi_coords)

    # Save original ROI
    original_path = output_path / "01_original_roi.png"
    cv2.imwrite(str(original_path), cv2.cvtColor(roi_image, cv2.COLOR_RGB2BGR))

    saved_paths = {"original": str(original_path)}

    if save_intermediate_steps:
        # Convert to grayscale for processing
        if len(roi_image.shape) == 3:
            gray = cv2.cvtColor(roi_image, cv2.COLOR_RGB2GRAY)
        else:
            gray = roi_image.copy()

        # Save grayscale
        gray_path = output_path / "02_grayscale.png"
        cv2.imwrite(str(gray_path), gray)
        saved_paths["grayscale"] = str(gray_path)

        # Save histogram equalized
        equalized = cv2.equalizeHist(gray)
        eq_path = output_path / "03_equalized.png"
        cv2.imwrite(str(eq_path), equalized)
        saved_paths["equalized"] = str(eq_path)

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        blur_path = output_path / "04_blurred.png"
        cv2.imwrite(str(blur_path), blurred)
        saved_paths["blurred"] = str(blur_path)

        # Generate thresholded images with different methods
        _, thresh_binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
        thresh_path = output_path / "05_threshold_binary.png"
        cv2.imwrite(str(thresh_path), thresh_binary)
        saved_paths["threshold_binary"] = str(thresh_path)

        # Adaptive threshold
        adaptive_thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                cv2.THRESH_BINARY, 11, 2)
        adaptive_path = output_path / "06_adaptive_threshold.png"
        cv2.imwrite(str(adaptive_path), adaptive_thresh)
        saved_paths["adaptive_threshold"] = str(adaptive_path)

        # Otsu's thresholding
        _, otsu_thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_path = output_path / "07_otsu_threshold.png"
        cv2.imwrite(str(otsu_path), otsu_thresh)
        saved_paths["otsu_threshold"] = str(otsu_path)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        edge_path = output_path / "08_edge_detection.png"
        cv2.imwrite(str(edge_path), edges)
        saved_paths["edges"] = str(edge_path)

        # Gradient visualization
        gradient_vis = create_gradient_visualization(roi_image)
        gradient_path = output_path / "09_gradient.png"
        cv2.imwrite(str(gradient_path), cv2.cvtColor(gradient_vis, cv2.COLOR_RGB2BGR))
        saved_paths["gradient"] = str(gradient_path)

    # Create composite visualization with all steps
    composite_path = output_path / "10_composite_visualization.png"

    # Create a simple composite image showing original and key processing steps
    try:
        # Combine some of the key visualizations into a composite image
        from analysis.utils.visualization import create_debug_composite
        composite = create_debug_composite(saved_paths)
        cv2.imwrite(str(composite_path), composite)
        saved_paths["composite"] = str(composite_path)
    except Exception as e:
        logger.error(f"Failed to create composite visualization: {str(e)}")

    logger.info(f"Saved {len(saved_paths)} debug visualizations to {output_path}")

    return {"output_directory": str(output_path), "saved_images": saved_paths}