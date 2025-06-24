# analysis/utils/visualization.py

import os
import cv2
import numpy as np
import datetime
import logging
from PIL import Image
import subprocess
import platform


logger = logging.getLogger(__name__)


def create_debug_composite(image_paths):
    """Create a composite visualization from multiple debug images

    Args:
        image_paths: Dictionary of {step_name: file_path} for debug images

    Returns:
        numpy.ndarray: Composite visualization image showing all steps
    """
    if not image_paths:
        logger.error("No images provided for composite visualization")
        return None

    # Collect images
    images = {}
    for name, path in image_paths.items():
        if name != "composite":  # Skip the composite itself
            try:
                img = cv2.imread(path)
                if img is not None:
                    images[name] = img
            except Exception as e:
                logger.error(f"Failed to read image {path}: {str(e)}")

    if not images:
        logger.error("No valid images loaded for composite")
        return None

    # Create a grid layout
    rows, cols = 3, 3  # Adjust as needed
    cell_height, cell_width = 300, 400

    # Create blank canvas
    composite = np.zeros((rows * cell_height, cols * cell_width, 3), dtype=np.uint8)

    # Add title labels and images
    i = 0
    for name, img in images.items():
        if i >= rows * cols:
            break

        row, col = i // cols, i % cols
        y, x = row * cell_height, col * cell_width

        # Resize image to fit cell (keeping aspect ratio)
        h, w = img.shape[:2]
        scale = min(cell_height / h * 0.8, cell_width / w * 0.8)
        new_h, new_w = int(h * scale), int(w * scale)
        resized = cv2.resize(img, (new_w, new_h))

        # Calculate position to center in cell
        offset_y = y + (cell_height - new_h) // 2
        offset_x = x + (cell_width - new_w) // 2

        # Place image on canvas
        composite[offset_y:offset_y + new_h, offset_x:offset_x + new_w] = resized

        # Add text label
        cv2.putText(composite, name, (x + 10, y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        i += 1

    return composite


def generate_visualization_grid(images_dict, labels=True):
    """Create a grid visualization from multiple images

    Args:
        images_dict: Dictionary of {name: image_array}
        labels: Whether to add text labels (default: True)

    Returns:
        numpy.ndarray: Grid visualization of all images
    """
    if not images_dict:
        logger.error("No images provided for grid visualization")
        return None

    # Create a grid layout
    rows, cols = 3, 3  # Adjust based on number of images
    cell_height, cell_width = 300, 400

    # Create blank canvas
    grid = np.zeros((rows * cell_height, cols * cell_width, 3), dtype=np.uint8)

    # Add images to grid
    i = 0
    for name, img in images_dict.items():
        if i >= rows * cols:
            break

        row, col = i // cols, i % cols
        y, x = row * cell_height, col * cell_width

        # Resize image to fit cell (keeping aspect ratio)
        h, w = img.shape[:2]
        scale = min(cell_height / h * 0.8, cell_width / w * 0.8)
        new_h, new_w = int(h * scale), int(w * scale)
        resized = cv2.resize(img, (new_w, new_h))

        # Calculate position to center in cell
        offset_y = y + (cell_height - new_h) // 2
        offset_x = x + (cell_width - new_w) // 2

        # Place image on canvas
        grid[offset_y:offset_y + new_h, offset_x:offset_x + new_w] = resized

        # Add text label if requested
        if labels:
            cv2.putText(grid, name, (x + 10, y + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        i += 1

    return grid


def save_debug_visualizations(image, roi_coords, output_dir="debug_output", prefix="debug",
                              save_intermediate_steps=True):
    """Save comprehensive debug visualizations of the image and ROI analysis

    Args:
        image: Original image as numpy array
        roi_coords: Either rectangle (x1,y1,x2,y2) or polygon [(x1,y1), (x2,y2), ...]
        output_dir: Base directory to save output
        prefix: Prefix for output directory name
        save_intermediate_steps: Whether to save intermediate processing steps

    Returns:
        dict: Information about saved files and output directory
    """
    logger = logging.getLogger(__name__)

    # Create output directory with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{prefix}_{timestamp}")
    os.makedirs(output_path, exist_ok=True)

    # Dictionary to store information about saved images
    saved_images = {}

    # Save original image
    original_path = os.path.join(output_path, "original.png")
    Image.fromarray(image).save(original_path)
    saved_images["original"] = original_path

    # Create visualizations only if ROI is provided
    if roi_coords is not None:
        # Determine if ROI is polygon or rectangle
        is_polygon = (
            isinstance(roi_coords, (list, tuple)) and
            len(roi_coords) >= 3 and
            isinstance(roi_coords[0], (list, tuple))
        )

        if is_polygon:
            # Create mask for polygon ROI
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            pts = np.array(roi_coords, dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)

            # Extract ROI using mask
            roi = cv2.bitwise_and(image, image, mask=mask)

            # Calculate bounding box for reference
            x_coords = [pt[0] for pt in roi_coords]
            y_coords = [pt[1] for pt in roi_coords]
            x1, y1 = min(x_coords), min(y_coords)
            x2, y2 = max(x_coords), max(y_coords)
        else:
            # Rectangle ROI
            x1, y1, x2, y2 = map(int, roi_coords)  # Ensure integer coordinates
            roi = image[y1:y2, x1:x2].copy()

        # Save ROI
        roi_path = os.path.join(output_path, "roi.png")
        Image.fromarray(roi).save(roi_path)
        saved_images["roi"] = roi_path

        # Create ROI outline visualization
        outline_image = image.copy()
        if is_polygon:
            # Draw polygon outline
            cv2.polylines(outline_image, [pts], True, (0, 255, 0), 2)
        else:
            # Draw rectangle outline
            cv2.rectangle(outline_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        outline_path = os.path.join(output_path, "roi_outline.png")
        Image.fromarray(outline_image).save(outline_path)
        saved_images["roi_outline"] = outline_path

        if save_intermediate_steps:
            # Create edge detection visualization
            if len(roi.shape) == 3:
                gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
            else:
                gray = roi.copy()

            edges = cv2.Canny(gray, 50, 150)
            edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
            edges_path = os.path.join(output_path, "edges.png")
            Image.fromarray(edges_colored).save(edges_path)
            saved_images["edges"] = edges_path

            # Create gradient magnitude visualization
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = cv2.magnitude(grad_x, grad_y)
            magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            gradient_colored = cv2.applyColorMap(magnitude_norm, cv2.COLORMAP_JET)
            gradient_colored_rgb = cv2.cvtColor(gradient_colored, cv2.COLOR_BGR2RGB)
            gradient_path = os.path.join(output_path, "gradient.png")
            Image.fromarray(gradient_colored_rgb).save(gradient_path)
            saved_images["gradient"] = gradient_path

        # Create composite visualization
        composite_image = outline_image.copy()

        # Add semi-transparent overlay
        overlay = composite_image.copy()
        if is_polygon:
            cv2.fillPoly(overlay, [pts], (0, 255, 0))
        else:
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), -1)

        cv2.addWeighted(overlay, 0.3, composite_image, 0.7, 0, composite_image)

        # Save composite
        composite_path = os.path.join(output_path, "composite.png")
        Image.fromarray(composite_image).save(composite_path)
        saved_images["composite"] = composite_path
    else:
        # No ROI selected, just save the original image as composite
        composite_path = os.path.join(output_path, "composite.png")
        Image.fromarray(image).save(composite_path)
        saved_images["composite"] = composite_path

    # Save debug info
    info = {
        "output_directory": output_path,
        "saved_images": saved_images,
        "timestamp": timestamp
    }

    logger.info(f"Saved debug visualizations to {output_path}")
    return info


def open_image_with_default_viewer(path):
    """Open an image file with the system's default viewer"""
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", path])
        else:  # Linux
            subprocess.call(["xdg-open", path])
        return True
    except Exception as e:
        print(f"Failed to open image: {e}")
        return False