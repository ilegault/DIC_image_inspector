# analysis/gradient_analysis.py - Gradient Analysis Module

import cv2
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
import logging
from scipy import ndimage
from scipy.signal import convolve2d
from functools import lru_cache
import hashlib


logger = logging.getLogger(__name__)


class GradientAnalyzer:
    """
    Analyzes image gradients for DIC quality assessment.

    This is the central source for all gradient calculations in the application.
    Other modules should use this class for gradient computation to ensure
    consistency and proper normalization.
    """

    def __init__(self):
        # Gradient operator kernels with their normalization factors
        self.gradient_kernels = {
            'sobel': {
                'x': np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64),
                'y': np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64),
                'norm_factor': 8.0
            },
            'prewitt': {
                'x': np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.float64),
                'y': np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]], dtype=np.float64),
                'norm_factor': 6.0
            },
            'scharr': {
                'x': np.array([[-3, 0, 3], [-10, 0, 10], [-3, 0, 3]], dtype=np.float64),
                'y': np.array([[-3, -10, -3], [0, 0, 0], [3, 10, 3]], dtype=np.float64),
                'norm_factor': 32.0
            }
        }

        self.local_window_sizes = [5, 9, 15, 21]  # For multi-scale analysis
        self.gradient_percentiles = [25, 50, 75, 90, 95, 99]

    # ========== Core Gradient Calculation Methods (Used by Other Modules) ==========

    def calculate_gradients(self, image: np.ndarray, method: str = 'sobel',
                            normalize: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate gradients using specified method. This is the PRIMARY method
        that should be used by other modules for gradient calculation.

        Args:
            image: Input grayscale image
            method: Gradient operator ('sobel', 'prewitt', 'scharr')
            normalize: Whether to apply proper normalization

        Returns:
            Tuple of (grad_x, grad_y, magnitude)
        """
        if len(image.shape) > 2:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        if method == 'sobel':
            grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
            norm_factor = 8.0
        elif method == 'scharr':
            grad_x = cv2.Scharr(image, cv2.CV_64F, 1, 0)
            grad_y = cv2.Scharr(image, cv2.CV_64F, 0, 1)
            norm_factor = 32.0
        elif method == 'prewitt':
            # Manual convolution for Prewitt
            kernel_x = self.gradient_kernels['prewitt']['x']
            kernel_y = self.gradient_kernels['prewitt']['y']
            grad_x = cv2.filter2D(image, cv2.CV_64F, kernel_x)
            grad_y = cv2.filter2D(image, cv2.CV_64F, kernel_y)
            norm_factor = 6.0
        else:
            raise ValueError(f"Unknown gradient method: {method}")

        # Apply normalization
        if normalize:
            grad_x = grad_x / norm_factor
            grad_y = grad_y / norm_factor

        # Calculate magnitude
        magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

        return grad_x, grad_y, magnitude

    def calculate_mig_ef_metrics(self, image: np.ndarray, normalize: bool = True) -> Dict[str, float]:
        """
        Calculate Mean Intensity Gradient (MIG) and Enhanced Feature (Ef) metrics.
        Used by QualityCalculator for DIC quality assessment.

        Based on:
        - Pan et al., 2009: Mean Intensity Gradient (MIG)
        - Hu et al., 2021: Enhanced feature (Ef)

        Args:
            image: Input grayscale image
            normalize: Whether to apply proper normalization

        Returns:
            Dictionary with MIG, Ef, and related metrics
        """
        # Get first-order gradients
        grad_x, grad_y, first_order_magnitude = self.calculate_gradients(image, 'sobel', normalize)

        # Calculate MIG
        mig = np.mean(first_order_magnitude)

        # Calculate second-order gradients (derivatives of already normalized gradients)
        grad_xx, _, _ = self.calculate_gradients(grad_x, 'sobel', normalize)
        _, grad_yy, _ = self.calculate_gradients(grad_y, 'sobel', normalize)
        _, grad_xy, _ = self.calculate_gradients(grad_x, 'sobel', normalize)

        # Second-order gradient magnitude
        second_order_magnitude = np.sqrt(grad_xx ** 2 + grad_yy ** 2 + 2 * grad_xy ** 2)

        # Enhanced feature (Ef) - Hu et al., 2021
        alpha = 0.7
        beta = 0.3
        ef = alpha * mig + beta * np.mean(second_order_magnitude)

        # Calculate gradient distribution statistics
        gradient_mean = np.mean(first_order_magnitude)
        gradient_std = np.std(first_order_magnitude)
        gradient_cv = gradient_std / (gradient_mean + 1e-6) if gradient_mean > 0 else 0.0

        return {
            'mig': float(mig),
            'ef': float(ef),
            'gradient_mean': float(gradient_mean),
            'gradient_std': float(gradient_std),
            'gradient_cv': float(gradient_cv),
            'first_order_magnitude_mean': float(np.mean(first_order_magnitude)),
            'second_order_magnitude_mean': float(np.mean(second_order_magnitude))
        }

    def calculate_gradient_quality_score(self, image: np.ndarray,
                                         mig_norm_factor: float = 50.0,
                                         ef_norm_factor: float = 100.0,
                                         mig_score_multiplier: float = 1.2,
                                         ef_score_multiplier: float = 1.0) -> Dict[str, float]:
        """
        Calculate gradient quality score for DIC assessment.
        This method can be used directly by QualityCalculator.

        Args:
            image: Input grayscale image
            mig_norm_factor: Normalization factor for MIG (default 50.0 per Pan et al.)
            ef_norm_factor: Normalization factor for Ef
            mig_score_multiplier: Multiplier for MIG score (default 1.2)
            ef_score_multiplier: Multiplier for Ef score (default 1.0)

        Returns:
            Dictionary with quality scores and metrics
        """
        # Get MIG/Ef metrics
        metrics = self.calculate_mig_ef_metrics(image, normalize=True)

        # Normalize scores
        normalized_mig = metrics['mig'] / mig_norm_factor
        normalized_ef = metrics['ef'] / ef_norm_factor

        # Calculate quality scores using the provided multipliers
        mig_score = min(1.0, normalized_mig * mig_score_multiplier)
        ef_score = min(1.0, normalized_ef * ef_score_multiplier)

        # Distribution quality assessment
        gradient_cv = metrics['gradient_cv']
        if 0.5 <= gradient_cv <= 2.0:
            distribution_bonus = 1.0
        elif 0.3 <= gradient_cv <= 3.0:
            distribution_bonus = 0.9
        else:
            distribution_bonus = 0.8

        # Combined gradient score
        gradient_score = (ef_score * 0.8 + mig_score * 0.2) * distribution_bonus

        return {
            'gradient_score': float(gradient_score),
            'mig_score': float(mig_score),
            'ef_score': float(ef_score),
            'distribution_bonus': float(distribution_bonus),
            'raw_mig': metrics['mig'],
            'raw_ef': metrics['ef'],
            'normalized_mig': float(normalized_mig),
            'normalized_ef': float(normalized_ef)
        }

    # ========== Original Analysis Methods (Enhanced) ==========

    def analyze(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Perform complete gradient analysis on an image.

        Args:
            image: Input image (grayscale or RGB)

        Returns:
            Comprehensive gradient analysis results
        """
        if image is None or image.size == 0:
            logger.warning("Empty image provided to gradient analyzer")
            return self._empty_result()

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        try:
            # Calculate gradients for all operators (with normalization)
            gradient_maps = self._calculate_gradient_maps(gray)

            # Get MIG/Ef metrics
            mig_ef_metrics = self.calculate_mig_ef_metrics(gray)

            # Get quality scores
            quality_scores = self.calculate_gradient_quality_score(gray)

            # Analyze gradient characteristics
            magnitude_stats = self._analyze_gradient_magnitude(gradient_maps)
            direction_stats = self._analyze_gradient_direction(gradient_maps)
            multiscale_stats = self._analyze_multiscale_gradients(gray)
            coherence_stats = self._analyze_gradient_coherence(gradient_maps)
            spatial_stats = self._analyze_spatial_distribution(gradient_maps)
            edge_stats = self._analyze_edge_gradients(gradient_maps, gray)
            local_stats = self._analyze_local_gradient_characteristics(gradient_maps)
            quality_assessment = self._assess_gradient_quality(gradient_maps, gray)

            # Combine all results
            results = {}
            results.update(magnitude_stats)
            results.update(direction_stats)
            results.update(multiscale_stats)
            results.update(coherence_stats)
            results.update(spatial_stats)
            results.update(edge_stats)
            results.update(local_stats)
            results.update(quality_assessment)
            results.update(mig_ef_metrics)
            results.update(quality_scores)

            return results

        except Exception as e:
            logger.error(f"Error in gradient analysis: {e}")
            return self._empty_result()

    def _calculate_gradient_maps(self, gray: np.ndarray) -> Dict[str, Dict[str, np.ndarray]]:
        """Calculate gradient maps for different operators with proper normalization."""
        gradient_maps = {}

        for operator in ['sobel', 'prewitt', 'scharr']:
            grad_x, grad_y, magnitude = self.calculate_gradients(gray, operator, normalize=True)

            # Calculate direction
            direction = np.arctan2(grad_y, grad_x)

            gradient_maps[operator] = {
                'x': grad_x,
                'y': grad_y,
                'magnitude': magnitude,
                'direction': direction
            }

        return gradient_maps

    def _analyze_gradient_magnitude(self, gradient_maps: Dict) -> Dict[str, Any]:
        """Analyze gradient magnitude characteristics."""
        results = {}

        # Use Sobel as primary gradient for analysis
        primary_grad = gradient_maps['sobel']
        magnitude = primary_grad['magnitude']

        # Basic magnitude statistics
        results.update({
            'magnitude_mean': float(np.mean(magnitude)),
            'magnitude_std': float(np.std(magnitude)),
            'magnitude_max': float(np.max(magnitude)),
            'magnitude_min': float(np.min(magnitude)),
            'magnitude_median': float(np.median(magnitude))
        })

        # Magnitude percentiles
        percentiles = [float(np.percentile(magnitude, p)) for p in self.gradient_percentiles]
        results['magnitude_percentiles'] = percentiles

        # Magnitude distribution characteristics
        non_zero_magnitude = magnitude[magnitude > 0]
        if len(non_zero_magnitude) > 0:
            results.update({
                'magnitude_nonzero_mean': float(np.mean(non_zero_magnitude)),
                'magnitude_nonzero_ratio': float(len(non_zero_magnitude) / magnitude.size),
                'magnitude_dynamic_range': float(np.max(non_zero_magnitude) - np.min(non_zero_magnitude))
            })
        else:
            results.update({
                'magnitude_nonzero_mean': 0.0,
                'magnitude_nonzero_ratio': 0.0,
                'magnitude_dynamic_range': 0.0
            })

        # Magnitude entropy
        hist, _ = np.histogram(magnitude, bins=64, density=True)
        hist = hist[hist > 0]
        magnitude_entropy = float(-np.sum(hist * np.log2(hist))) if len(hist) > 0 else 0.0
        results['magnitude_entropy'] = magnitude_entropy

        # Compare different gradient operators
        operator_comparison = {}
        for op_name, grad_data in gradient_maps.items():
            op_magnitude = grad_data['magnitude']
            operator_comparison[f'{op_name}_magnitude_mean'] = float(np.mean(op_magnitude))
            operator_comparison[f'{op_name}_magnitude_std'] = float(np.std(op_magnitude))

        results.update(operator_comparison)

        return results

    def _analyze_gradient_direction(self, gradient_maps: Dict) -> Dict[str, Any]:
        """Analyze gradient direction characteristics."""
        results = {}

        direction = gradient_maps['sobel']['direction']
        magnitude = gradient_maps['sobel']['magnitude']

        # Weight directions by magnitude
        significant_mask = magnitude > np.percentile(magnitude, 25)
        significant_directions = direction[significant_mask]

        if len(significant_directions) > 0:
            # Direction entropy (isotropy measure)
            hist, _ = np.histogram(significant_directions, bins=36, range=(-np.pi, np.pi), density=True)
            hist = hist[hist > 0]
            direction_entropy = float(-np.sum(hist * np.log2(hist))) if len(hist) > 0 else 0.0

            # Direction coherence (how aligned gradients are)
            cos_dir = np.cos(significant_directions)
            sin_dir = np.sin(significant_directions)
            mean_cos = np.mean(cos_dir)
            mean_sin = np.mean(sin_dir)
            coherence = np.sqrt(mean_cos ** 2 + mean_sin ** 2)

            # Dominant direction
            dominant_direction = np.arctan2(mean_sin, mean_cos)

            # Direction variance
            direction_variance = np.var(significant_directions)

            results.update({
                'direction_entropy': direction_entropy,
                'direction_coherence': float(coherence),
                'direction_uniformity': float(1.0 - coherence),
                'dominant_direction': float(dominant_direction),
                'direction_variance': float(direction_variance)
            })
        else:
            results.update({
                'direction_entropy': 0.0,
                'direction_coherence': 0.0,
                'direction_uniformity': 1.0,
                'dominant_direction': 0.0,
                'direction_variance': 0.0
            })

        return results

    def _analyze_multiscale_gradients(self, gray: np.ndarray) -> Dict[str, Any]:
        """Analyze gradients at multiple scales."""
        results = {}

        scale_means = []
        scale_stds = []

        for scale in [1.0, 2.0, 4.0]:
            # Apply Gaussian blur for scale
            if scale > 1.0:
                scaled = cv2.GaussianBlur(gray, (0, 0), scale)
            else:
                scaled = gray.copy()

            # Calculate gradients at this scale
            _, _, magnitude = self.calculate_gradients(scaled, 'sobel', normalize=True)

            scale_means.append(np.mean(magnitude))
            scale_stds.append(np.std(magnitude))

        # Analyze scale consistency
        if len(scale_means) > 1:
            consistency = 1.0 - np.std(scale_means) / (np.mean(scale_means) + 1e-6)
            mean_variation = np.std(scale_means)
            std_variation = np.std(scale_stds)
        else:
            consistency = 1.0
            mean_variation = 0.0
            std_variation = 0.0

        results.update({
            'multiscale_consistency': float(consistency),
            'multiscale_mean_variation': float(mean_variation),
            'multiscale_std_variation': float(std_variation)
        })

        return results

    def _analyze_gradient_coherence(self, gradient_maps: Dict) -> Dict[str, Any]:
        """Analyze gradient coherence using structure tensor."""
        results = {}

        grad_x = gradient_maps['sobel']['x']
        grad_y = gradient_maps['sobel']['y']

        # Calculate structure tensor main_components
        Ixx = grad_x * grad_x
        Iyy = grad_y * grad_y
        Ixy = grad_x * grad_y

        # Apply Gaussian smoothing
        kernel_size = 5
        Ixx = cv2.GaussianBlur(Ixx, (kernel_size, kernel_size), 1.5)
        Iyy = cv2.GaussianBlur(Iyy, (kernel_size, kernel_size), 1.5)
        Ixy = cv2.GaussianBlur(Ixy, (kernel_size, kernel_size), 1.5)

        # Calculate coherence
        trace = Ixx + Iyy
        det = Ixx * Iyy - Ixy * Ixy

        # Avoid division by zero
        coherence = np.zeros_like(trace)
        mask = trace > 1e-6
        coherence[mask] = np.sqrt(np.maximum(0, (trace[mask] ** 2 - 4 * det[mask]))) / trace[mask]

        results.update({
            'coherence_mean': float(np.mean(coherence)),
            'coherence_std': float(np.std(coherence)),
            'coherence_max': float(np.max(coherence)),
            'high_coherence_ratio': float(np.sum(coherence > 0.7) / coherence.size)
        })

        return results

    def _analyze_spatial_distribution(self, gradient_maps: Dict) -> Dict[str, Any]:
        """Analyze spatial distribution of gradients."""
        results = {}

        magnitude = gradient_maps['sobel']['magnitude']

        # Divide image into grid cells
        h, w = magnitude.shape
        grid_size = 16
        cell_h = h // grid_size
        cell_w = w // grid_size

        if cell_h > 0 and cell_w > 0:
            cell_means = []

            for i in range(grid_size):
                for j in range(grid_size):
                    cell = magnitude[i * cell_h:(i + 1) * cell_h, j * cell_w:(j + 1) * cell_w]
                    if cell.size > 0:
                        cell_means.append(np.mean(cell))

            if cell_means:
                # Spatial uniformity
                spatial_uniformity = 1.0 - np.std(cell_means) / (np.mean(cell_means) + 1e-6)

                # Gradient concentration (Gini coefficient)
                sorted_means = np.sort(cell_means)
                n = len(sorted_means)
                index = np.arange(1, n + 1)
                gini = (2 * np.sum(index * sorted_means)) / (n * np.sum(sorted_means)) - (n + 1) / n
                gradient_concentration = float(gini)

                # Spatial entropy
                hist, _ = np.histogram(cell_means, bins=16, density=True)
                hist = hist[hist > 0]
                spatial_entropy = float(-np.sum(hist * np.log2(hist))) if len(hist) > 0 else 0.0
            else:
                spatial_uniformity = 0.0
                gradient_concentration = 0.0
                spatial_entropy = 0.0
        else:
            spatial_uniformity = 0.0
            gradient_concentration = 0.0
            spatial_entropy = 0.0

        results.update({
            'spatial_uniformity': float(spatial_uniformity),
            'gradient_concentration': gradient_concentration,
            'spatial_entropy': spatial_entropy
        })

        return results

    def _analyze_edge_gradients(self, gradient_maps: Dict, gray: np.ndarray) -> Dict[str, Any]:
        """Analyze gradients specifically at edge locations."""
        results = {}

        magnitude = gradient_maps['sobel']['magnitude']

        # Detect edges using Canny
        edges = cv2.Canny(gray, 50, 150)
        edge_mask = edges > 0

        if np.any(edge_mask):
            edge_gradients = magnitude[edge_mask]
            non_edge_gradients = magnitude[~edge_mask]

            results.update({
                'edge_gradient_mean': float(np.mean(edge_gradients)),
                'edge_gradient_max': float(np.max(edge_gradients)),
                'edge_gradient_ratio': float(np.mean(edge_gradients) / (np.mean(non_edge_gradients) + 1e-6)),
                'edge_strength_uniformity': float(1.0 - np.std(edge_gradients) / (np.mean(edge_gradients) + 1e-6))
            })
        else:
            results.update({
                'edge_gradient_mean': 0.0,
                'edge_gradient_max': 0.0,
                'edge_gradient_ratio': 0.0,
                'edge_strength_uniformity': 0.0
            })

        return results

    def _analyze_local_gradient_characteristics(self, gradient_maps: Dict) -> Dict[str, Any]:
        """Analyze local gradient characteristics using sliding windows."""
        results = {}

        magnitude = gradient_maps['sobel']['magnitude']

        # Calculate local gradient statistics using sliding windows
        window_size = 15
        if magnitude.shape[0] < window_size or magnitude.shape[1] < window_size:
            return {
                'local_gradient_uniformity': 0.0,
                'gradient_texture_energy': 0.0,
                'gradient_homogeneity': 0.0
            }

        # Local mean and standard deviation
        kernel = np.ones((window_size, window_size)) / (window_size * window_size)
        local_mean = convolve2d(magnitude, kernel, mode='same', boundary='symm')
        local_var = convolve2d((magnitude - local_mean) ** 2, kernel, mode='same', boundary='symm')
        local_std = np.sqrt(local_var)

        # Local uniformity measure
        local_cv = local_std / (local_mean + 1e-6)
        local_uniformity = 1.0 / (1.0 + local_cv)

        # Texture energy (second moment)
        normalized_magnitude = magnitude / (np.max(magnitude) + 1e-6)
        texture_energy = float(np.sum(normalized_magnitude ** 2))

        # Homogeneity measure
        # Calculate co-occurrence matrix for gradient magnitudes
        quantized_magnitude = (normalized_magnitude * 15).astype(np.int32)
        quantized_magnitude = np.clip(quantized_magnitude, 0, 15)

        # Simple homogeneity calculation
        homogeneity = 0.0
        count = 0
        for i in range(quantized_magnitude.shape[0] - 1):
            for j in range(quantized_magnitude.shape[1] - 1):
                diff = abs(quantized_magnitude[i, j] - quantized_magnitude[i, j + 1])
                homogeneity += 1.0 / (1.0 + diff)
                diff = abs(quantized_magnitude[i, j] - quantized_magnitude[i + 1, j])
                homogeneity += 1.0 / (1.0 + diff)
                count += 2

        if count > 0:
            homogeneity /= count

        results.update({
            'local_gradient_uniformity': float(np.mean(local_uniformity)),
            'gradient_texture_energy': texture_energy,
            'gradient_homogeneity': float(homogeneity)
        })

        return results

    def _assess_gradient_quality(self, gradient_maps: Dict, gray: np.ndarray) -> Dict[str, Any]:
        """Assess overall gradient quality for DIC applications."""
        results = {}

        magnitude = gradient_maps['sobel']['magnitude']

        # Gradient strength assessment
        mean_magnitude = np.mean(magnitude)
        std_magnitude = np.std(magnitude)

        # Optimal gradient range for DIC (empirically determined)
        # Note: These ranges assume normalized gradients
        optimal_mean_range = (0.05, 0.3)  # Adjusted for normalized gradients
        optimal_std_range = (0.02, 0.2)  # Adjusted for normalized gradients

        # Score gradient strength
        if optimal_mean_range[0] <= mean_magnitude <= optimal_mean_range[1]:
            strength_score = 1.0
        else:
            strength_score = max(0.0,
                                 1.0 - abs(mean_magnitude - np.mean(optimal_mean_range)) / np.mean(optimal_mean_range))

        # Score gradient variation
        if optimal_std_range[0] <= std_magnitude <= optimal_std_range[1]:
            variation_score = 1.0
        else:
            variation_score = max(0.0,
                                  1.0 - abs(std_magnitude - np.mean(optimal_std_range)) / np.mean(optimal_std_range))

        # Gradient coverage (percentage of image with significant gradients)
        threshold = np.percentile(magnitude, 75)
        coverage = np.sum(magnitude > threshold) / magnitude.size
        coverage_score = min(1.0, coverage * 2.0)  # Optimal coverage around 50%

        # Gradient distribution quality
        hist, _ = np.histogram(magnitude, bins=64, density=True)
        hist = hist[hist > 0]
        entropy = -np.sum(hist * np.log2(hist)) if len(hist) > 0 else 0.0
        max_entropy = np.log2(64)
        distribution_score = entropy / max_entropy if max_entropy > 0 else 0.0

        # Overall gradient quality score
        quality_score = (
                strength_score * 0.3 +
                variation_score * 0.25 +
                coverage_score * 0.25 +
                distribution_score * 0.2
        )

        results.update({
            'gradient_strength_score': float(strength_score),
            'gradient_variation_score': float(variation_score),
            'gradient_coverage_score': float(coverage_score),
            'gradient_distribution_score': float(distribution_score),
            'overall_gradient_quality': float(quality_score)
        })

        return results

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            'magnitude_mean': 0.0,
            'magnitude_std': 0.0,
            'magnitude_max': 0.0,
            'magnitude_min': 0.0,
            'magnitude_median': 0.0,
            'magnitude_percentiles': [0.0] * len(self.gradient_percentiles),
            'magnitude_nonzero_mean': 0.0,
            'magnitude_nonzero_ratio': 0.0,
            'magnitude_dynamic_range': 0.0,
            'magnitude_entropy': 0.0,
            'direction_entropy': 0.0,
            'direction_coherence': 0.0,
            'direction_uniformity': 0.0,
            'dominant_direction': 0.0,
            'direction_variance': 0.0,
            'multiscale_consistency': 0.0,
            'multiscale_mean_variation': 0.0,
            'multiscale_std_variation': 0.0,
            'coherence_mean': 0.0,
            'coherence_std': 0.0,
            'coherence_max': 0.0,
            'high_coherence_ratio': 0.0,
            'spatial_uniformity': 0.0,
            'gradient_concentration': 0.0,
            'spatial_entropy': 0.0,
            'edge_gradient_mean': 0.0,
            'edge_gradient_max': 0.0,
            'edge_gradient_ratio': 0.0,
            'edge_strength_uniformity': 0.0,
            'local_gradient_uniformity': 0.0,
            'gradient_texture_energy': 0.0,
            'gradient_homogeneity': 0.0,
            'gradient_strength_score': 0.0,
            'gradient_variation_score': 0.0,
            'gradient_coverage_score': 0.0,
            'gradient_distribution_score': 0.0,
            'overall_gradient_quality': 0.0,
            'mig': 0.0,
            'ef': 0.0,
            'gradient_score': 0.0,
            'mig_score': 0.0,
            'ef_score': 0.0,
            'normalized_mig': 0.0,
            'normalized_ef': 0.0
        }

    def analyze_local_gradient_quality(self, image: np.ndarray, window_size: int = 32) -> np.ndarray:
        """
        Analyze gradient quality in local windows across the image.

        Args:
            image: Input image
            window_size: Size of analysis window

        Returns:
            2D array of local quality scores
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape
        quality_map = np.zeros((h // window_size, w // window_size))

        for i in range(0, h - window_size + 1, window_size):
            for j in range(0, w - window_size + 1, window_size):
                window = gray[i:i + window_size, j:j + window_size]
                quality_scores = self.calculate_gradient_quality_score(window)
                quality_map[i // window_size, j // window_size] = quality_scores['gradient_score']

        return quality_map

class GradientAnalyzerCache:
    """Cache wrapper for expensive gradient calculations."""

    def __init__(self, max_cache_size=10):
        self.cache = {}
        self.max_size = max_cache_size
        self.access_order = []

    def _get_image_hash(self, image: np.ndarray) -> str:
        """Generate hash for image array."""
        # Use a fast hash of image characteristics
        return hashlib.md5(
            f"{image.shape}_{image.mean():.2f}_{image.std():.2f}".encode()
        ).hexdigest()

    def get_gradients(self, image: np.ndarray) -> tuple:
        """Get cached gradients or compute new ones."""
        img_hash = self._get_image_hash(image)

        if img_hash in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(img_hash)
            self.access_order.append(img_hash)
            logger.debug(f"Using cached gradients for hash {img_hash[:8]}")
            return self.cache[img_hash]

        # Compute new gradients
        grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)

        # Add to cache
        self.cache[img_hash] = (grad_x, grad_y)
        self.access_order.append(img_hash)

        # Remove oldest if cache is full
        if len(self.cache) > self.max_size:
            oldest = self.access_order.pop(0)
            del self.cache[oldest]

        return grad_x, grad_y