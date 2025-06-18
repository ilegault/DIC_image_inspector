# analysis/quality_map/map_generator.py

import cv2
import numpy as np
from analysis.core.subset_analyzer import determine_optimal_subset_size, analyze_subset_grid


def generate_quality_map(image, colormap='dic_quality', alpha=0.7):
    """Generate a DIC quality map and visualization of the input image

    Args:
        image: Input image (numpy array)
        colormap: Colormap to use for visualization ('dic_quality', 'jet', 'viridis', etc.)
        alpha: Blending factor for overlay (0.0-1.0)

    Returns:
        tuple: (quality_map, visualization) where:
            - quality_map is the raw quality data (0-1 float values)
            - visualization is the RGB visualization ready for display
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    # Ensure image is in RGB for visualization output
    if len(image.shape) == 2:
        rgb_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    else:
        rgb_image = image.copy()

    # Determine optimal subset size for DIC analysis
    subset_size = determine_optimal_subset_size(gray)
    overlap = 0.5  # Standard 50% overlap

    # Generate quality map using subset analysis
    quality_map, avg_quality = analyze_subset_grid(gray, subset_size, overlap)

    # Scale quality map to 0-1 range if needed
    if np.max(quality_map) > 1.0:
        quality_map = quality_map / np.max(quality_map)

    # Create a color visualization
    # Normalize quality map to 0-255 for visualization
    normalized_map = (quality_map * 255).astype(np.uint8)

    # Apply colormap
    if colormap == 'dic_quality':
        # Custom colormap for DIC quality (red=bad, green=good)
        colored_map = cv2.applyColorMap(255 - normalized_map, cv2.COLORMAP_JET)
    else:
        # Use requested OpenCV colormap
        colormap_const = getattr(cv2, f'COLORMAP_{colormap.upper()}', cv2.COLORMAP_JET)
        colored_map = cv2.applyColorMap(normalized_map, colormap_const)

    # Convert BGR to RGB for PIL compatibility
    colored_map = cv2.cvtColor(colored_map, cv2.COLOR_BGR2RGB)

    # Create blended visualization
    visualization = cv2.addWeighted(rgb_image, 1 - alpha, colored_map, alpha, 0)

    return quality_map, visualization


def visualize_quality_map(base_image, quality_map, colormap_name='jet', alpha=0.7):
    """
    Create a visualization of the quality map overlaid on the base image

    Args:
        base_image: Original image (numpy array)
        quality_map: Generated quality map (2D array)
        colormap_name: Name of colormap to use ('jet', 'viridis', etc)
        alpha: Transparency of overlay (0.0-1.0)

    Returns:
        numpy array: Overlay visualization
    """
    print(f"DEBUG: visualize_quality_map called")
    print(f"DEBUG: base_image shape: {base_image.shape}")
    print(f"DEBUG: quality_map shape: {quality_map.shape if quality_map is not None else 'None'}")
    print(f"DEBUG: alpha: {alpha}, colormap: {colormap_name}")

    if quality_map is None:
        print("DEBUG: quality_map is None, returning original image")
        return base_image

    # Ensure base image is in RGB format
    if len(base_image.shape) == 2:
        print("DEBUG: Converting grayscale base image to RGB")
        rgb_image = cv2.cvtColor(base_image, cv2.COLOR_GRAY2RGB)
    else:
        rgb_image = base_image.copy()

    # Normalize quality map to 0-1 range if needed
    q_min, q_max = np.min(quality_map), np.max(quality_map)
    print(f"DEBUG: quality_map range: {q_min} to {q_max}")

    if q_max > 1.0:
        quality_map = quality_map / q_max
        print("DEBUG: Normalized quality map to 0-1 range")

    # Scale to 0-255 for visualization
    normalized_map = (quality_map * 255).astype(np.uint8)

    # Create colormap visualization
    try:
        colormap_const = getattr(cv2, f'COLORMAP_{colormap_name.upper()}', cv2.COLORMAP_JET)
        colored_map = cv2.applyColorMap(normalized_map, colormap_const)
        colored_map = cv2.cvtColor(colored_map, cv2.COLOR_BGR2RGB)
        print(f"DEBUG: Applied colormap, colored_map shape: {colored_map.shape}")
    except Exception as e:
        print(f"DEBUG: Error applying colormap: {str(e)}")
        return base_image

    # Check if dimensions match
    if colored_map.shape[:2] != rgb_image.shape[:2]:
        print(f"DEBUG: Dimension mismatch! colored_map: {colored_map.shape}, rgb_image: {rgb_image.shape}")
        # Resize quality map to match base image
        colored_map = cv2.resize(colored_map, (rgb_image.shape[1], rgb_image.shape[0]))
        print(f"DEBUG: Resized colored_map to {colored_map.shape}")

    # Create blended overlay
    try:
        overlay = cv2.addWeighted(rgb_image, 1 - alpha, colored_map, alpha, 0)
        print(f"DEBUG: Created overlay with shape: {overlay.shape}")
    except Exception as e:
        print(f"DEBUG: Error creating overlay: {str(e)}")
        return base_image

    # Return the visualization overlay
    return overlay