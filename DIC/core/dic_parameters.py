"""
DIC parameter calculation and optimization.

Determines optimal DIC analysis parameters including subset size, step size, and
overlap based on image characteristics and quality scores. Provides recommendations
for facet size and correlation settings.

Usage:
    calculator = DICParameterCalculator()
    params = calculator.calculate_parameters(image, quality_score, subset_size)
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Any
import logging

from DIC.models.analysis_result import DICParameters
from DIC.analysis.gradient_analysis import GradientAnalyzer

logger = logging.getLogger(__name__)


class DICParameterCalculator:
    """
    Calculates optimal DIC analysis parameters.

    This class determines the best subset size, step size, and other
    parameters for DIC analysis based on image characteristics and
    quality requirements.
    """

    def __init__(self):
        self.gradient_analyzer = GradientAnalyzer()
        # Standard DIC subset sizes to consider
        self.possible_sizes = [11, 15, 21, 31, 41, 51]
        self.min_subset_size = 11
        self.max_subset_size = 51
        self.default_overlap = 0.75  # 75% overlap is standard

    def determine_optimal_subset_size(self, image: np.ndarray) -> int:
        """
        Determine optimal subset size for given image.

        Uses multiple criteria and picks the most stable result.

        Args:
            image: Input grayscale image

        Returns:
            Optimal subset size
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape
        min_dim = min(h, w)

        # Filter valid sizes based on image dimensions
        valid_sizes = [s for s in self.possible_sizes if s < min_dim / 3]

        if not valid_sizes:
            return self.min_subset_size

        # Use image-size based heuristic for consistency
        if min_dim < 200:
            return 15
        elif min_dim < 500:
            return 21
        elif min_dim < 1000:
            return 31
        else:
            return 41

    def calculate_parameters(self, image: np.ndarray, overall_score: float,
                             custom_subset_size: int = None) -> DICParameters:
        """
        Calculate complete DIC parameters based on image and quality.

        Args:
            image: Input image
            overall_score: Overall quality score (0-100)
            custom_subset_size: Optional custom subset size

        Returns:
            DICParameters object with all calculated parameters
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Determine subset size
        if custom_subset_size is not None:
            subset_size = custom_subset_size
        else:
            subset_size = self.determine_optimal_subset_size(gray)

        # Calculate step size for standard overlap
        step_size = max(1, int(subset_size * (1 - self.default_overlap)))

        # Calculate overlap percentage
        overlap_percent = int((1 - step_size / subset_size) * 100)

        # Determine expected accuracy based on quality score
        expected_accuracy = self._calculate_expected_accuracy(overall_score)

        return DICParameters(
            facet_size=subset_size,
            step_size=step_size,
            overlap_percent=overlap_percent,
            expected_accuracy=expected_accuracy,
            subset_size_used=subset_size
        )

    def _calculate_expected_accuracy(self, overall_score: float) -> str:
        """Calculate expected displacement accuracy based on quality score."""
        if overall_score >= 90:
            return "±0.01 pixels (excellent)"
        elif overall_score >= 75:
            return "±0.02 pixels (very good)"
        elif overall_score >= 60:
            return "±0.03 pixels (good)"
        elif overall_score >= 45:
            return "±0.05 pixels (acceptable)"
        elif overall_score >= 30:
            return "±0.1 pixels (challenging)"
        else:
            return "±0.2 pixels (poor)"

    def analyze_feature_characteristics(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Advanced feature characteristic analysis for subset size determination.

        Args:
            image: Input grayscale image

        Returns:
            Dictionary with feature analysis results
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape
        feature_estimates = []

        # Method 1: Multi-scale adaptive thresholding analysis
        feature_estimates.extend(self._adaptive_threshold_analysis(gray))

        # Method 2: Gradient-based analysis
        feature_estimates.extend(self._gradient_based_analysis(gray))

        # Method 3: Autocorrelation analysis
        try:
            autocorr_estimate = self._autocorrelation_analysis(gray)
            if autocorr_estimate > 0:
                feature_estimates.append(autocorr_estimate)
        except Exception as e:
            logger.warning(f"Autocorrelation analysis failed: {e}")

        # Method 4: Frequency domain analysis
        try:
            freq_estimate = self._frequency_domain_analysis(gray)
            if freq_estimate > 0:
                feature_estimates.append(freq_estimate)
        except Exception as e:
            logger.warning(f"Frequency domain analysis failed: {e}")

        # Calculate statistics
        if feature_estimates:
            feature_size_stats = {
                'mean_feature_size': float(np.mean(feature_estimates)),
                'median_feature_size': float(np.median(feature_estimates)),
                'std_feature_size': float(np.std(feature_estimates)),
                'min_feature_size': float(np.min(feature_estimates)),
                'max_feature_size': float(np.max(feature_estimates)),
                'num_estimates': len(feature_estimates)
            }
        else:
            feature_size_stats = {
                'mean_feature_size': 0.0,
                'median_feature_size': 0.0,
                'std_feature_size': 0.0,
                'min_feature_size': 0.0,
                'max_feature_size': 0.0,
                'num_estimates': 0
            }

        return feature_size_stats

    def _adaptive_threshold_analysis(self, gray: np.ndarray) -> list:
        """Multi-scale adaptive thresholding analysis."""
        feature_estimates = []
        h, w = gray.shape

        for block_size in [7, 11, 15, 21]:
            if block_size < min(h, w) // 4:
                try:
                    binary = cv2.adaptiveThreshold(
                        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                        cv2.THRESH_BINARY, block_size, 2
                    )
                    num_components, _, stats, _ = cv2.connectedComponentsWithStats(binary)

                    if num_components > 1:
                        areas = stats[1:, cv2.CC_STAT_AREA]
                        valid_areas = areas[(areas > 4) & (areas < (h * w) / 100)]
                        if len(valid_areas) > 0:
                            feature_diameter = np.median(np.sqrt(valid_areas))
                            feature_estimates.append(feature_diameter * 1.2)
                except Exception:
                    continue

        return feature_estimates

    def _gradient_based_analysis(self, gray: np.ndarray) -> list:
        """Advanced gradient-based analysis."""
        feature_estimates = []

        # Calculate gradients using universal gradient analyzer
        grad_x, grad_y, gradient_magnitude = self.gradient_analyzer.calculate_gradients(gray, 'sobel', normalize=True)

        # Multi-threshold gradient analysis
        for percentile in [75, 80, 85, 90]:
            threshold = np.percentile(gradient_magnitude, percentile)
            high_grad_mask = gradient_magnitude > threshold
            high_grad_count = np.sum(high_grad_mask)

            if high_grad_count > 10:
                h, w = gray.shape
                density = high_grad_count / (h * w)
                if density > 0:
                    spacing = 1.0 / np.sqrt(density)
                    feature_estimates.append(spacing * 0.8)

        return feature_estimates

    def _autocorrelation_analysis(self, gray: np.ndarray) -> float:
        """Autocorrelation-based feature size analysis."""
        # Downsample for efficiency
        scale = max(1, max(gray.shape) // 256)
        if scale > 1:
            small_gray = gray[::scale, ::scale]
        else:
            small_gray = gray

        # Calculate normalized autocorrelation
        normalized = small_gray.astype(float) - np.mean(small_gray)
        std_val = np.std(normalized)

        if std_val < 1e-6:
            return 0

        normalized /= std_val

        # Use FFT for efficient autocorrelation
        f_transform = np.fft.fft2(normalized)
        autocorr = np.real(np.fft.ifftshift(np.fft.ifft2(np.abs(f_transform) ** 2)))

        # Find characteristic length scale
        center_y, center_x = autocorr.shape[0] // 2, autocorr.shape[1] // 2
        center_val = autocorr[center_y, center_x]

        # Look for first significant drop (to 60% of peak)
        target_val = center_val * 0.6

        for radius in range(1, min(center_y, center_x) // 2):
            # Sample points at this radius
            circle_vals = []
            n_samples = max(8, int(2 * np.pi * radius))
            for i in range(n_samples):
                angle = 2 * np.pi * i / n_samples
                y = center_y + int(radius * np.sin(angle))
                x = center_x + int(radius * np.cos(angle))
                if 0 <= y < autocorr.shape[0] and 0 <= x < autocorr.shape[1]:
                    circle_vals.append(autocorr[y, x])

            if circle_vals and np.mean(circle_vals) < target_val:
                return radius * scale * 1.5

        return 0

    def _frequency_domain_analysis(self, gray: np.ndarray) -> float:
        """Frequency domain analysis for characteristic feature size."""
        # Apply FFT
        f_transform = np.fft.fft2(gray.astype(float))
        f_shift = np.fft.fftshift(f_transform)
        magnitude = np.abs(f_shift)

        # Calculate radial power spectrum
        h, w = gray.shape
        center_y, center_x = h // 2, w // 2

        # Create radial coordinate system
        y, x = np.ogrid[:h, :w]
        radius = np.sqrt((y - center_y) ** 2 + (x - center_x) ** 2)

        # Calculate average power at each radius
        max_radius = min(center_y, center_x) // 2
        radial_power = []

        for r in range(1, max_radius):
            mask = (radius >= r - 0.5) & (radius < r + 0.5)
            if np.any(mask):
                avg_power = np.mean(magnitude[mask])
                radial_power.append(avg_power)
            else:
                radial_power.append(0)

        if len(radial_power) > 10:
            # Smooth the spectrum
            radial_power = np.array(radial_power)
            if len(radial_power) > 5:
                kernel = np.ones(5) / 5
                if len(radial_power) >= len(kernel):
                    radial_power = np.convolve(radial_power, kernel, mode='same')

            # Find peak frequency
            peak_idx = np.argmax(radial_power)
            if peak_idx > 0:
                # Convert frequency to spatial scale
                spatial_wavelength = min(h, w) / peak_idx
                return spatial_wavelength / 3  # Feature size is typically 1/3 of wavelength

        return 0

    def get_size_recommendations(self, image: np.ndarray, quality_score: float) -> Dict[str, Any]:
        """
        Get subset size recommendations based on image analysis.

        Args:
            image: Input image
            quality_score: Overall quality score

        Returns:
            Dictionary with recommendations
        """
        feature_analysis = self.analyze_feature_characteristics(image)
        optimal_size = self.determine_optimal_subset_size(image)

        recommendations = {
            'optimal_subset_size': optimal_size,
            'alternative_sizes': [],
            'quality_based_adjustment': '',
            'feature_based_recommendation': '',
            'final_recommendation': optimal_size
        }

        # Quality-based adjustments
        if quality_score < 50:
            # Low quality - recommend larger subsets
            adjusted_size = min(51, optimal_size + 10)
            recommendations[
                'quality_based_adjustment'] = f"Low quality detected - consider larger subset ({adjusted_size}px) for better correlation"
            recommendations['final_recommendation'] = adjusted_size
        elif quality_score > 90:
            # High quality - can use smaller subsets
            adjusted_size = max(11, optimal_size - 4)
            recommendations[
                'quality_based_adjustment'] = f"High quality detected - smaller subset ({adjusted_size}px) may provide better spatial resolution"
            recommendations['final_recommendation'] = adjusted_size

        # Feature-based recommendations
        mean_feature_size = feature_analysis.get('mean_feature_size', 0)
        if mean_feature_size > 0:
            feature_based_size = int(mean_feature_size * 2.5)  # 2.5x feature size rule
            feature_based_size = max(11, min(51, feature_based_size))

            if abs(feature_based_size - optimal_size) > 4:
                recommendations[
                    'feature_based_recommendation'] = f"Feature analysis suggests {feature_based_size}px subset size"
                recommendations['final_recommendation'] = feature_based_size

        # Alternative sizes
        current_rec = recommendations['final_recommendation']
        alternatives = []
        for size in self.possible_sizes:
            if abs(size - current_rec) <= 10 and size != current_rec:
                alternatives.append(size)
        recommendations['alternative_sizes'] = sorted(alternatives)

        return recommendations

    def validate_parameters(self, subset_size: int, step_size: int, image_shape: Tuple[int, int]) -> Dict[str, Any]:
        """
        Validate DIC parameters for given image.

        Args:
            subset_size: Proposed subset size
            step_size: Proposed step size
            image_shape: (height, width) of image

        Returns:
            Validation results dictionary
        """
        h, w = image_shape

        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'expected_points': 0,
            'memory_estimate_mb': 0
        }

        # Validate subset size
        if subset_size < self.min_subset_size:
            validation['errors'].append(f"Subset size too small (min: {self.min_subset_size})")
            validation['valid'] = False

        if subset_size > self.max_subset_size:
            validation['errors'].append(f"Subset size too large (max: {self.max_subset_size})")
            validation['valid'] = False

        if subset_size >= min(h, w) / 3:
            validation['errors'].append("Subset size too large for image dimensions")
            validation['valid'] = False

        if subset_size % 2 == 0:
            validation['warnings'].append("Subset size should be odd for symmetric correlation")

        # Validate step size
        if step_size < 1:
            validation['errors'].append("Step size must be at least 1")
            validation['valid'] = False

        if step_size > subset_size:
            validation['warnings'].append("Step size larger than subset size (no overlap)")

        # Calculate expected analysis points
        if validation['valid']:
            points_x = (w - subset_size) // step_size + 1
            points_y = (h - subset_size) // step_size + 1
            total_points = points_x * points_y

            validation['expected_points'] = total_points

            if total_points < 25:
                validation['warnings'].append("Very few analysis points - results may be sparse")
            elif total_points > 100000:
                validation['warnings'].append("Very many analysis points - analysis will be slow")

            # Rough memory estimate (bytes per analysis point)
            validation['memory_estimate_mb'] = (total_points * subset_size * subset_size * 4) / (1024 * 1024)

        return validation