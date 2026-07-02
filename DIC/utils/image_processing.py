"""
Image processing utilities for DIC quality assessment.

This module provides standardized image processing functions used throughout
the DIC Image Quality Inspector application. It includes utilities for color
conversion, normalization, ROI extraction, and quality visualization operations.

Usage:
    from utils.image_processing import ImageProcessor

    processor = ImageProcessor()
    gray_image = processor.convert_to_grayscale(image)
    roi_image = processor.extract_roi(image, roi_coordinates)
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict
from PIL import Image
import logging

from DIC.utils.constants import VALIDATION
from DIC.analysis.gradient_analysis import GradientAnalyzer

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Utility class for common image processing operations.

    This class provides standardized image processing functions used
    throughout the DIC Image Quality Inspector application.
    """

    def __init__(self):
        """Initialize the image processor."""
        self.gradient_analyzer = GradientAnalyzer()

    @staticmethod
    def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
        """
        Convert image to grayscale if needed.

        Args:
            image: Input image array

        Returns:
            Grayscale image array
        """
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return image.copy()

    @staticmethod
    def convert_to_rgb(image: np.ndarray) -> np.ndarray:
        """
        Convert image to RGB if needed.

        Args:
            image: Input image array

        Returns:
            RGB image array
        """
        if len(image.shape) == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        return image.copy()

    @staticmethod
    def resize_image_for_display(image: np.ndarray, max_size: int = 800) -> Tuple[np.ndarray, float]:
        """
        Resize image for display while maintaining aspect ratio.

        Args:
            image: Input image array
            max_size: Maximum dimension size

        Returns:
            Tuple of (resized_image, scale_factor)
        """
        height, width = image.shape[:2]

        if max(height, width) <= max_size:
            return image.copy(), 1.0

        # Calculate scale factor
        scale = max_size / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Resize image
        if len(image.shape) == 3:
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        else:
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

        return resized, scale

    @staticmethod
    def apply_roi_mask(image: np.ndarray, roi_coords: Optional[List[Tuple[int, int]]]) -> np.ndarray:
        """
        Apply ROI mask to image.

        Args:
            image: Input image array
            roi_coords: List of (x, y) coordinates defining polygon ROI

        Returns:
            Masked image array
        """
        if not roi_coords or len(roi_coords) < 3:
            return image.copy()

        try:
            # Create mask
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            pts = np.array(roi_coords, dtype=np.int32)

            # Validate and clamp coordinates
            h, w = image.shape[:2]
            pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)
            pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)

            cv2.fillPoly(mask, [pts], 255)

            # Apply mask
            if len(image.shape) == 3:
                masked = cv2.bitwise_and(image, image, mask=mask)
            else:
                masked = cv2.bitwise_and(image, image, mask=mask)

            return masked

        except Exception as e:
            logger.error(f"Failed to apply ROI mask: {e}")
            return image.copy()

    @staticmethod
    def extract_roi_region(image: np.ndarray, roi_coords: Optional[List[Tuple[int, int]]]) -> np.ndarray:
        """
        Extract ROI region from image (cropped to bounding box).

        Args:
            image: Input image array
            roi_coords: List of (x, y) coordinates defining polygon ROI

        Returns:
            Cropped image array containing ROI
        """
        if not roi_coords or len(roi_coords) < 3:
            return image.copy()

        try:
            # Get bounding box
            x_coords = [pt[0] for pt in roi_coords]
            y_coords = [pt[1] for pt in roi_coords]

            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)

            # Clamp to image bounds
            h, w = image.shape[:2]
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)

            # Extract region
            roi_image = image[y1:y2, x1:x2].copy()

            return roi_image

        except Exception as e:
            logger.error(f"Failed to extract ROI region: {e}")
            return image.copy()

    @staticmethod
    def calculate_roi_area(roi_coords: List[Tuple[int, int]]) -> float:
        """
        Calculate area of polygon ROI using shoelace formula.

        Args:
            roi_coords: List of (x, y) coordinates

        Returns:
            Area in pixels
        """
        if len(roi_coords) < 3:
            return 0.0

        try:
            # Shoelace formula
            area = 0.5 * abs(
                sum(x0 * y1 - x1 * y0
                    for ((x0, y0), (x1, y1)) in zip(roi_coords, roi_coords[1:] + [roi_coords[0]]))
            )
            return area

        except Exception as e:
            logger.error(f"Failed to calculate ROI area: {e}")
            return 0.0

    @staticmethod
    def create_edge_visualization(image: np.ndarray, roi_coords: Optional[List] = None) -> np.ndarray:
        """
        Create edge detection visualization.

        Args:
            image: Input image array
            roi_coords: Optional ROI coordinates

        Returns:
            Edge visualization as RGB image
        """
        try:
            # Apply ROI mask if provided
            if roi_coords:
                image_region = ImageProcessor.apply_roi_mask(image, roi_coords)
            else:
                image_region = image.copy()

            # Convert to grayscale
            gray = ImageProcessor.convert_to_grayscale(image_region)

            # Apply Canny edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Create colored visualization
            edge_visualization = np.zeros_like(image if roi_coords is None else image_region)

            if len(edge_visualization.shape) == 3:
                edge_visualization[:, :, 2] = edges  # Red channel
            else:
                edge_visualization = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

            return edge_visualization

        except Exception as e:
            logger.error(f"Failed to create edge visualization: {e}")
            return ImageProcessor.convert_to_rgb(image)

    @staticmethod
    def create_gradient_visualization(image: np.ndarray, roi_coords: Optional[List] = None) -> np.ndarray:
        """
        Create gradient magnitude visualization.

        Args:
            image: Input image array
            roi_coords: Optional ROI coordinates

        Returns:
            Gradient visualization as RGB image
        """
        try:
            # Apply ROI mask if provided
            if roi_coords:
                image_region = ImageProcessor.apply_roi_mask(image, roi_coords)
            else:
                image_region = image.copy()

            # Convert to grayscale
            gray = ImageProcessor.convert_to_grayscale(image_region)

            # Calculate gradients using universal gradient analyzer
            gradient_analyzer = GradientAnalyzer()
            grad_x, grad_y, magnitude = gradient_analyzer.calculate_gradients(gray, 'sobel', normalize=True)

            # Normalize to 0-255 range
            cv2.normalize(magnitude, magnitude, 0, 255, cv2.NORM_MINMAX)
            gradient_vis = magnitude.astype(np.uint8)

            # Apply colormap
            gradient_colored = cv2.applyColorMap(gradient_vis, cv2.COLORMAP_JET)

            # Convert BGR to RGB
            if len(gradient_colored.shape) == 3:
                gradient_colored = cv2.cvtColor(gradient_colored, cv2.COLOR_BGR2RGB)

            return gradient_colored

        except Exception as e:
            logger.error(f"Failed to create gradient visualization: {e}")
            return ImageProcessor.convert_to_rgb(image)

    @staticmethod
    def create_quality_map_overlay(base_image: np.ndarray, quality_map: np.ndarray,
                                   spectrum_type: str = 'custom_dic', alpha: float = 0.7) -> np.ndarray:
        """
        Create quality map overlay on base image.

        Args:
            base_image: Base image array
            quality_map: Quality map data (0-1 range)
            spectrum_type: Color spectrum type
            alpha: Overlay transparency

        Returns:
            Overlaid visualization
        """
        try:
            from DIC.analysis.quality_map.colormap import ColormapGenerator

            # Ensure base image is RGB
            rgb_base = ImageProcessor.convert_to_rgb(base_image)

            # Generate colored quality map
            colormap_gen = ColormapGenerator()
            colored_map = colormap_gen.apply_colormap(quality_map, spectrum_type)

            # Resize colored map to match base image if needed
            if colored_map.shape[:2] != rgb_base.shape[:2]:
                colored_map = cv2.resize(colored_map, (rgb_base.shape[1], rgb_base.shape[0]))

            # Blend images
            overlay = cv2.addWeighted(rgb_base, 1 - alpha, colored_map, alpha, 0)

            return overlay

        except Exception as e:
            logger.error(f"Failed to create quality map overlay: {e}")
            return ImageProcessor.convert_to_rgb(base_image)

    @staticmethod
    def normalize_image(image: np.ndarray, target_range: Tuple[int, int] = (0, 255)) -> np.ndarray:
        """
        Normalize image to target range.

        Args:
            image: Input image array
            target_range: Target (min, max) range

        Returns:
            Normalized image array
        """
        try:
            min_val, max_val = target_range

            # Get current range
            img_min = np.min(image)
            img_max = np.max(image)

            if img_max == img_min:
                # Uniform image
                return np.full_like(image, min_val, dtype=np.uint8)

            # Normalize
            normalized = (image - img_min) / (img_max - img_min)
            normalized = normalized * (max_val - min_val) + min_val

            return normalized.astype(np.uint8)

        except Exception as e:
            logger.error(f"Failed to normalize image: {e}")
            return image.astype(np.uint8)

    @staticmethod
    def enhance_contrast(image: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
        """
        Enhance image contrast using CLAHE.

        Args:
            image: Input image array
            clip_limit: Clipping limit for CLAHE

        Returns:
            Contrast-enhanced image
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                is_color = True
            else:
                gray = image.copy()
                is_color = False

            # Apply CLAHE
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Convert back to color if needed
            if is_color:
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)

            return enhanced

        except Exception as e:
            logger.error(f"Failed to enhance contrast: {e}")
            return image.copy()

    @staticmethod
    def apply_gaussian_blur(image: np.ndarray, kernel_size: int = 5, sigma: float = 1.0) -> np.ndarray:
        """
        Apply Gaussian blur to image.

        Args:
            image: Input image array
            kernel_size: Blur kernel size (must be odd)
            sigma: Gaussian sigma value

        Returns:
            Blurred image
        """
        try:
            # Ensure kernel size is odd
            if kernel_size % 2 == 0:
                kernel_size += 1

            blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
            return blurred

        except Exception as e:
            logger.error(f"Failed to apply Gaussian blur: {e}")
            return image.copy()

    @staticmethod
    def validate_image_array(image: np.ndarray) -> bool:
        """
        Validate image array properties.

        Args:
            image: Image array to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if it's a numpy array
            if not isinstance(image, np.ndarray):
                return False

            # Check dimensions
            if len(image.shape) not in [2, 3]:
                return False

            # Check size constraints
            if len(image.shape) >= 2:
                height, width = image.shape[:2]
                min_w, min_h = VALIDATION['min_image_size']
                max_w, max_h = VALIDATION['max_image_size']

                if not (min_w <= width <= max_w and min_h <= height <= max_h):
                    return False

            # Check data type
            if image.dtype not in [np.uint8, np.uint16, np.float32, np.float64]:
                return False

            # Check for valid color channels
            if len(image.shape) == 3:
                channels = image.shape[2]
                if channels not in [1, 3, 4]:  # Grayscale, RGB, or RGBA
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating image array: {e}")
            return False

    @staticmethod
    def array_to_pil_image(array: np.ndarray) -> Image.Image:
        """
        Convert numpy array to PIL Image.

        Args:
            array: Numpy array

        Returns:
            PIL Image object
        """
        try:
            # Convert to uint8 if not already
            if array.dtype != np.uint8:
                array = np.clip(array, 0, 255).astype(np.uint8)

            # Convert based on shape
            if len(array.shape) == 2:  # Grayscale
                return Image.fromarray(array, 'L')
            elif array.shape[2] == 3:  # RGB
                return Image.fromarray(array, 'RGB')
            elif array.shape[2] == 4:  # RGBA
                return Image.fromarray(array, 'RGBA')
            else:
                raise ValueError(f"Unsupported array shape: {array.shape}")

        except Exception as e:
            logger.error(f"Failed to convert array to PIL image: {e}")
            # Return a simple fallback image
            return Image.new('RGB', (100, 100), (128, 128, 128))

    @staticmethod
    def pil_image_to_array(pil_image: Image.Image) -> np.ndarray:
        """
        Convert PIL Image to numpy array.

        Args:
            pil_image: PIL Image object

        Returns:
            Numpy array
        """
        try:
            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Convert to numpy array
            return np.array(pil_image)

        except Exception as e:
            logger.error(f"Failed to convert PIL image to array: {e}")
            # Return fallback array
            return np.zeros((100, 100, 3), dtype=np.uint8)


class ROIProcessor:
    """
    Specialized processor for ROI-related operations.
    """

    def __init__(self):
        """Initialize ROI processor."""
        pass

    @staticmethod
    def validate_roi_coordinates(roi_coords: List[Tuple[int, int]],
                                 image_shape: Tuple[int, int]) -> bool:
        """
        Validate ROI coordinates against image dimensions.

        Args:
            roi_coords: List of (x, y) coordinates
            image_shape: (height, width) of image

        Returns:
            True if valid, False otherwise
        """
        try:
            if not roi_coords or len(roi_coords) < 3:
                return False

            height, width = image_shape[:2]

            for x, y in roi_coords:
                if not (0 <= x < width and 0 <= y < height):
                    return False

            # Check area
            area = ImageProcessor.calculate_roi_area(roi_coords)
            if area < VALIDATION['min_roi_area']:
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating ROI coordinates: {e}")
            return False

    @staticmethod
    def clamp_roi_to_image(roi_coords: List[Tuple[int, int]],
                           image_shape: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Clamp ROI coordinates to image boundaries.

        Args:
            roi_coords: List of (x, y) coordinates
            image_shape: (height, width) of image

        Returns:
            Clamped coordinates
        """
        try:
            if not roi_coords:
                return []

            height, width = image_shape[:2]
            clamped_coords = []

            for x, y in roi_coords:
                clamped_x = max(0, min(width - 1, int(x)))
                clamped_y = max(0, min(height - 1, int(y)))
                clamped_coords.append((clamped_x, clamped_y))

            return clamped_coords

        except Exception as e:
            logger.error(f"Error clamping ROI coordinates: {e}")
            return roi_coords

    @staticmethod
    def get_roi_bounding_box(roi_coords: List[Tuple[int, int]]) -> Tuple[int, int, int, int]:
        """
        Get bounding box of ROI.

        Args:
            roi_coords: List of (x, y) coordinates

        Returns:
            (x1, y1, x2, y2) bounding box coordinates
        """
        try:
            if not roi_coords:
                return (0, 0, 0, 0)

            x_coords = [pt[0] for pt in roi_coords]
            y_coords = [pt[1] for pt in roi_coords]

            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)

            return (x1, y1, x2, y2)

        except Exception as e:
            logger.error(f"Error getting ROI bounding box: {e}")
            return (0, 0, 0, 0)

    @staticmethod
    def convert_display_to_image_coords(display_coords: List[Tuple[float, float]],
                                        display_scale: float,
                                        image_offset: Tuple[int, int] = (0, 0)) -> List[Tuple[int, int]]:
        """
        Convert display coordinates to image coordinates.

        Args:
            display_coords: Coordinates in display space
            display_scale: Scale factor from image to display
            image_offset: (x, y) offset of image in display

        Returns:
            Coordinates in image space
        """
        try:
            offset_x, offset_y = image_offset
            image_coords = []

            for x, y in display_coords:
                # Remove offset
                x_adj = x - offset_x
                y_adj = y - offset_y

                # Scale to image coordinates
                img_x = int(round(x_adj / display_scale))
                img_y = int(round(y_adj / display_scale))

                image_coords.append((img_x, img_y))

            return image_coords

        except Exception as e:
            logger.error(f"Error converting display to image coordinates: {e}")
            return [(int(x), int(y)) for x, y in display_coords]

    @staticmethod
    def convert_image_to_display_coords(image_coords: List[Tuple[int, int]],
                                        display_scale: float,
                                        image_offset: Tuple[int, int] = (0, 0)) -> List[Tuple[float, float]]:
        """
        Convert image coordinates to display coordinates.

        Args:
            image_coords: Coordinates in image space
            display_scale: Scale factor from image to display
            image_offset: (x, y) offset of image in display

        Returns:
            Coordinates in display space
        """
        try:
            offset_x, offset_y = image_offset
            display_coords = []

            for x, y in image_coords:
                # Scale to display coordinates
                disp_x = x * display_scale + offset_x
                disp_y = y * display_scale + offset_y

                display_coords.append((disp_x, disp_y))

            return display_coords

        except Exception as e:
            logger.error(f"Error converting image to display coordinates: {e}")
            return [(float(x), float(y)) for x, y in image_coords]


class VisualizationProcessor:
    """
    Specialized processor for creating visualizations.
    """

    def __init__(self):
        """Initialize visualization processor."""
        pass

    @staticmethod
    def create_colorbar(width: int = 300, height: int = 50,
                        spectrum_type: str = 'custom_dic') -> np.ndarray:
        """
        Create a colorbar for quality visualization.

        Args:
            width: Colorbar width in pixels
            height: Colorbar height in pixels
            spectrum_type: Color spectrum type

        Returns:
            Colorbar image as RGB array
        """
        try:
            from DIC.analysis.quality_map.colormap import ColormapGenerator

            # Create gradient from 0 to 1
            gradient = np.linspace(0, 1, width).reshape(1, -1)
            gradient_2d = np.repeat(gradient, height, axis=0)

            # Apply colormap
            colormap_gen = ColormapGenerator()
            colorbar = colormap_gen.apply_colormap(gradient_2d, spectrum_type)

            return colorbar

        except Exception as e:
            logger.error(f"Failed to create colorbar: {e}")
            # Return simple gradient fallback
            gradient = np.linspace(0, 255, width, dtype=np.uint8)
            colorbar = np.repeat(gradient.reshape(1, -1), height, axis=0)
            return cv2.cvtColor(colorbar, cv2.COLOR_GRAY2RGB)

    @staticmethod
    def add_text_overlay(image: np.ndarray, text: str,
                         position: Tuple[int, int] = (10, 30),
                         font_scale: float = 1.0,
                         color: Tuple[int, int, int] = (255, 255, 255),
                         thickness: int = 2) -> np.ndarray:
        """
        Add text overlay to image.

        Args:
            image: Input image array
            text: Text to add
            position: (x, y) position for text
            font_scale: Font scale factor
            color: RGB color tuple
            thickness: Text thickness

        Returns:
            Image with text overlay
        """
        try:
            result = image.copy()

            # Convert RGB to BGR for OpenCV
            bgr_color = (color[2], color[1], color[0])

            cv2.putText(result, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                        font_scale, bgr_color, thickness, cv2.LINE_AA)

            return result

        except Exception as e:
            logger.error(f"Failed to add text overlay: {e}")
            return image.copy()

    @staticmethod
    def create_side_by_side_comparison(image1: np.ndarray, image2: np.ndarray,
                                       labels: Optional[Tuple[str, str]] = None) -> np.ndarray:
        """
        Create side-by-side comparison of two images.

        Args:
            image1: First image
            image2: Second image
            labels: Optional labels for images

        Returns:
            Combined comparison image
        """
        try:
            # Ensure both images are RGB
            img1_rgb = ImageProcessor.convert_to_rgb(image1)
            img2_rgb = ImageProcessor.convert_to_rgb(image2)

            # Resize to same height
            h1, w1 = img1_rgb.shape[:2]
            h2, w2 = img2_rgb.shape[:2]

            target_height = min(h1, h2)

            if h1 != target_height:
                scale = target_height / h1
                new_w1 = int(w1 * scale)
                img1_rgb = cv2.resize(img1_rgb, (new_w1, target_height))

            if h2 != target_height:
                scale = target_height / h2
                new_w2 = int(w2 * scale)
                img2_rgb = cv2.resize(img2_rgb, (new_w2, target_height))

            # Combine horizontally
            combined = np.hstack([img1_rgb, img2_rgb])

            # Add labels if provided
            if labels:
                label1, label2 = labels
                combined = VisualizationProcessor.add_text_overlay(
                    combined, label1, (10, 30), font_scale=0.8)
                combined = VisualizationProcessor.add_text_overlay(
                    combined, label2, (img1_rgb.shape[1] + 10, 30), font_scale=0.8)

            return combined

        except Exception as e:
            logger.error(f"Failed to create side-by-side comparison: {e}")
            return ImageProcessor.convert_to_rgb(image1)

    @staticmethod
    def create_grid_layout(images: List[np.ndarray],
                           grid_size: Optional[Tuple[int, int]] = None,
                           labels: Optional[List[str]] = None) -> np.ndarray:
        """
        Create grid layout of multiple images.

        Args:
            images: List of images to arrange
            grid_size: (rows, cols) for grid. If None, automatically determined
            labels: Optional labels for each image

        Returns:
            Grid layout image
        """
        try:
            if not images:
                return np.zeros((100, 100, 3), dtype=np.uint8)

            # Determine grid size
            if grid_size is None:
                n_images = len(images)
                cols = int(np.ceil(np.sqrt(n_images)))
                rows = int(np.ceil(n_images / cols))
            else:
                rows, cols = grid_size

            # Convert all images to RGB and get maximum dimensions
            rgb_images = [ImageProcessor.convert_to_rgb(img) for img in images]
            max_height = max(img.shape[0] for img in rgb_images)
            max_width = max(img.shape[1] for img in rgb_images)

            # Resize all images to same size
            target_size = (max_width, max_height)
            resized_images = []

            for img in rgb_images:
                if img.shape[:2] != (max_height, max_width):
                    resized = cv2.resize(img, target_size)
                else:
                    resized = img.copy()
                resized_images.append(resized)

            # Create grid
            grid_rows = []
            for r in range(rows):
                row_images = []
                for c in range(cols):
                    idx = r * cols + c
                    if idx < len(resized_images):
                        img = resized_images[idx].copy()

                        # Add label if provided
                        if labels and idx < len(labels):
                            img = VisualizationProcessor.add_text_overlay(
                                img, labels[idx], (10, 30), font_scale=0.6)

                        row_images.append(img)
                    else:
                        # Fill with black image
                        row_images.append(np.zeros((max_height, max_width, 3), dtype=np.uint8))

                if row_images:
                    grid_rows.append(np.hstack(row_images))

            # Combine rows
            if grid_rows:
                grid = np.vstack(grid_rows)
                return grid
            else:
                return np.zeros((100, 100, 3), dtype=np.uint8)

        except Exception as e:
            logger.error(f"Failed to create grid layout: {e}")
            return ImageProcessor.convert_to_rgb(images[0]) if images else np.zeros((100, 100, 3), dtype=np.uint8)


# Utility functions
def calculate_image_statistics(image: np.ndarray) -> Dict[str, float]:
    """
    Calculate basic image statistics.

    Args:
        image: Input image array

    Returns:
        Dictionary of statistics
    """
    try:
        # Convert to grayscale for statistics
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        stats = {
            'mean': float(np.mean(gray)),
            'std': float(np.std(gray)),
            'min': float(np.min(gray)),
            'max': float(np.max(gray)),
            'median': float(np.median(gray)),
            'range': float(np.max(gray) - np.min(gray))
        }

        # Calculate additional metrics
        if stats['mean'] > 0:
            stats['coefficient_of_variation'] = stats['std'] / stats['mean']
        else:
            stats['coefficient_of_variation'] = 0.0

        return stats

    except Exception as e:
        logger.error(f"Failed to calculate image statistics: {e}")
        return {
            'mean': 0.0, 'std': 0.0, 'min': 0.0,
            'max': 0.0, 'median': 0.0, 'range': 0.0,
            'coefficient_of_variation': 0.0
        }


def get_optimal_display_size(image_shape: Tuple[int, int],
                             max_size: int = 800) -> Tuple[int, int, float]:
    """
    Get optimal display size for image.

    Args:
        image_shape: (height, width) of image
        max_size: Maximum dimension size

    Returns:
        Tuple of (display_width, display_height, scale_factor)
    """
    height, width = image_shape[:2]

    if max(height, width) <= max_size:
        return width, height, 1.0

    scale = max_size / max(height, width)
    new_width = int(width * scale)
    new_height = int(height * scale)

    return new_width, new_height, scale