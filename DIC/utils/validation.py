"""
Validation utilities for DIC image quality assessment.

This module provides centralized validation functions for images, ROI data,
and analysis parameters. It ensures consistent validation logic across the
application and provides clear error messages for invalid inputs.

Usage:
    from utils.validation import ValidationHelper

    validator = ValidationHelper()
    if validator.validate_image_for_analysis(image):
        # Proceed with analysis
        pass
"""

import numpy as np
from typing import Optional, Tuple
import logging

from DIC.models.roi_data import ROIData

logger = logging.getLogger(__name__)


class ValidationHelper:
    """
    Provides validation functions for the DIC Image Inspector.

    Centralizes all validation logic to ensure consistent checks
    across the application.
    """

    def __init__(self):
        self.min_image_size = 50  # Minimum dimension in pixels
        self.max_image_size = 20000  # Maximum dimension in pixels
        self.min_subset_size = 11  # Minimum DIC subset size
        self.max_subset_size = 101  # Maximum DIC subset size

    def validate_image_for_analysis(self, image: np.ndarray) -> bool:
        """
        Validate that an image is suitable for DIC analysis.

        Args:
            image: Image array to validate

        Returns:
            True if image is valid for analysis
        """
        try:
            # Check basic properties
            if not self._validate_image_basic(image):
                return False

            # Check dimensions
            if not self._validate_image_dimensions(image):
                return False

            # Check content
            if not self._validate_image_content(image):
                return False

            return True

        except Exception as e:
            logger.warning(f"Error validating image: {e}")
            return False

    def _validate_image_basic(self, image: np.ndarray) -> bool:
        """Validate basic image properties."""
        if image is None:
            return False

        if not isinstance(image, np.ndarray):
            return False

        if image.size == 0:
            return False

        if len(image.shape) not in [2, 3]:
            return False

        if len(image.shape) == 3 and image.shape[2] not in [1, 3, 4]:
            return False

        return True

    def _validate_image_dimensions(self, image: np.ndarray) -> bool:
        """Validate image dimensions are reasonable."""
        h, w = image.shape[:2]

        # Check minimum size
        if h < self.min_image_size or w < self.min_image_size:
            logger.warning(f"Image too small: {w}x{h} < {self.min_image_size}")
            return False

        # Check maximum size
        if h > self.max_image_size or w > self.max_image_size:
            logger.warning(f"Image too large: {w}x{h} > {self.max_image_size}")
            return False

        # Check aspect ratio (should be reasonable)
        aspect_ratio = max(w, h) / min(w, h)
        if aspect_ratio > 20:
            logger.warning(f"Extreme aspect ratio: {aspect_ratio}")
            return False

        return True

    def _validate_image_content(self, image: np.ndarray) -> bool:
        """Validate image content is suitable for analysis."""
        # Convert to grayscale for content checks
        if len(image.shape) == 3:
            import cv2
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Check for completely black or white images
        if np.all(gray == 0) or np.all(gray == 255):
            logger.warning("Image is completely uniform")
            return False

        # Check for sufficient contrast
        std_dev = np.std(gray)
        if std_dev < 5:  # Very low contrast
            logger.warning(f"Very low contrast: std={std_dev}")
            return False

        # Check for reasonable intensity distribution
        mean_intensity = np.mean(gray)
        if mean_intensity < 10 or mean_intensity > 245:
            logger.warning(f"Extreme mean intensity: {mean_intensity}")
            return False

        return True

    def validate_roi(self, roi: ROIData, image_shape: Tuple[int, int]) -> bool:
        """
        Validate ROI is suitable for analysis.

        Args:
            roi: ROI data to validate
            image_shape: (height, width) of the image

        Returns:
            True if ROI is valid
        """
        try:
            if not roi or not roi.coordinates:
                return False

            h, w = image_shape

            # Check coordinates are within image bounds
            for x, y in roi.coordinates:
                if x < 0 or x >= w or y < 0 or y >= h:
                    logger.warning(f"ROI coordinate out of bounds: ({x}, {y})")
                    return False

            # Check ROI area
            area = roi.calculate_area()
            min_area = self.min_subset_size ** 2  # Minimum useful area
            max_area = h * w * 0.95  # Maximum 95% of image

            if area < min_area:
                logger.warning(f"ROI too small: {area} < {min_area}")
                return False

            if area > max_area:
                logger.warning(f"ROI too large: {area} > {max_area}")
                return False

            # Check ROI geometry
            if roi.roi_type == 'polygon' and len(roi.coordinates) < 3:
                logger.warning("Polygon ROI needs at least 3 points")
                return False

            return True

        except Exception as e:
            logger.warning(f"Error validating ROI: {e}")
            return False

    def validate_subset_size(self, subset_size: int, image_shape: Tuple[int, int]) -> bool:
        """
        Validate subset size is appropriate for image.

        Args:
            subset_size: Proposed subset size
            image_shape: (height, width) of the image

        Returns:
            True if subset size is valid
        """
        h, w = image_shape
        min_dim = min(h, w)

        # Check basic range
        if subset_size < self.min_subset_size or subset_size > self.max_subset_size:
            logger.warning(f"Subset size out of range: {subset_size}")
            return False

        # Check relative to image size
        if subset_size >= min_dim / 3:
            logger.warning(f"Subset size too large for image: {subset_size} >= {min_dim / 3}")
            return False

        # Must be odd
        if subset_size % 2 == 0:
            logger.warning(f"Subset size must be odd: {subset_size}")
            return False

        return True

    def validate_analysis_parameters(self,
                                     subset_size: Optional[int],
                                     step_size: Optional[int],
                                     image_shape: Tuple[int, int]) -> bool:
        """
        Validate analysis parameters are compatible.

        Args:
            subset_size: DIC subset size
            step_size: Step size between subsets
            image_shape: (height, width) of the image

        Returns:
            True if parameters are valid
        """
        h, w = image_shape

        # Validate subset size if provided
        if subset_size is not None:
            if not self.validate_subset_size(subset_size, image_shape):
                return False

        # Validate step size if provided
        if step_size is not None:
            if subset_size is not None:
                # Step size should be reasonable relative to subset size
                min_step = 1
                max_step = subset_size

                if step_size < min_step or step_size > max_step:
                    logger.warning(f"Step size out of range: {step_size} not in [{min_step}, {max_step}]")
                    return False

                # Check if we'll have enough analysis points
                expected_points_x = (w - subset_size) // step_size + 1
                expected_points_y = (h - subset_size) // step_size + 1
                total_points = expected_points_x * expected_points_y

                if total_points < 10:
                    logger.warning(f"Too few analysis points: {total_points}")
                    return False

        return True

    def validate_spectrum_type(self, spectrum_type: str) -> bool:
        """
        Validate spectrum type is supported.

        Args:
            spectrum_type: Spectrum identifier

        Returns:
            True if spectrum is valid
        """
        valid_spectrums = [
            'optimized',
            'controlled'
        ]

        return spectrum_type in valid_spectrums

    def get_recommended_subset_size(self, image_shape: Tuple[int, int]) -> int:
        """
        Get recommended subset size for image.

        Args:
            image_shape: (height, width) of the image

        Returns:
            Recommended subset size
        """
        h, w = image_shape
        min_dim = min(h, w)

        # Size-based recommendations
        if min_dim < 200:
            return 15
        elif min_dim < 500:
            return 21
        elif min_dim < 1000:
            return 31
        else:
            return 41

    def get_recommended_step_size(self, subset_size: int) -> int:
        """
        Get recommended step size for given subset size.

        Args:
            subset_size: DIC subset size

        Returns:
            Recommended step size (75% overlap)
        """
        # Standard 75% overlap
        step_size = max(1, int(subset_size * 0.25))
        return step_size

    def validate_file_path(self, file_path: str, must_exist: bool = True) -> bool:
        """
        Validate file path.

        Args:
            file_path: Path to validate
            must_exist: Whether file must already exist

        Returns:
            True if path is valid
        """
        if not file_path or not isinstance(file_path, str):
            return False

        if must_exist:
            import os
            return os.path.exists(file_path)
        else:
            # Check if directory exists for new files
            import os
            directory = os.path.dirname(file_path)
            return os.path.exists(directory) if directory else True

    def get_validation_summary(self, image: np.ndarray,
                               roi: Optional[ROIData] = None,
                               subset_size: Optional[int] = None) -> dict:
        """
        Get comprehensive validation summary.

        Args:
            image: Image to validate
            roi: Optional ROI to validate
            subset_size: Optional subset size to validate

        Returns:
            Dictionary with validation results
        """
        summary = {
            'image_valid': False,
            'roi_valid': True,  # Valid if no ROI
            'subset_size_valid': True,  # Valid if not specified
            'overall_valid': False,
            'warnings': [],
            'recommendations': []
        }

        # Validate image
        summary['image_valid'] = self.validate_image_for_analysis(image)
        if not summary['image_valid']:
            summary['warnings'].append("Image is not suitable for DIC analysis")

        # Validate ROI if present
        if roi:
            summary['roi_valid'] = self.validate_roi(roi, image.shape[:2])
            if not summary['roi_valid']:
                summary['warnings'].append("ROI is not suitable for analysis")

        # Validate subset size if specified
        if subset_size:
            summary['subset_size_valid'] = self.validate_subset_size(subset_size, image.shape[:2])
            if not summary['subset_size_valid']:
                summary['warnings'].append("Subset size is not appropriate for this image")

        # Add recommendations
        if summary['image_valid']:
            recommended_subset = self.get_recommended_subset_size(image.shape[:2])
            summary['recommendations'].append(f"Recommended subset size: {recommended_subset}")

            recommended_step = self.get_recommended_step_size(recommended_subset)
            summary['recommendations'].append(f"Recommended step size: {recommended_step}")

        # Overall validation
        summary['overall_valid'] = (
                summary['image_valid'] and
                summary['roi_valid'] and
                summary['subset_size_valid']
        )

        return summary