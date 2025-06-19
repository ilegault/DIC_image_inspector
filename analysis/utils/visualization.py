# analysis/utils/visualization.py

import cv2
import numpy as np
import logging

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