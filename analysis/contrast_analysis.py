# analysis/contrast_analysis.py - Contrast Analysis Module

import cv2
import numpy as np
from typing import Dict, Any, Tuple
import logging
from analysis.gradient_analysis import GradientAnalyzer

logger = logging.getLogger(__name__)


class ContrastAnalyzer:
    """
    Analyzes image contrast for DIC quality assessment.

    Contrast is essential for reliable correlation in DIC. This module implements
    multiple contrast measures including RMS, Michelson, Weber contrasts, and
    local contrast variations.
    """

    def __init__(self):
        self.gradient_analyzer = GradientAnalyzer()
        self.local_window_size = 5  # Size for local contrast analysis
        self.contrast_percentiles = [25, 50, 75, 90, 95]  # For distribution analysis

    def analyze(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Perform complete contrast analysis on an image.

        Args:
            image: Input image (grayscale)

        Returns:
            Dictionary containing contrast metrics
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        if gray.size == 0:
            return self._empty_result()

        try:
            # Basic intensity statistics
            basic_stats = self._calculate_basic_statistics(gray)

            # Global contrast measures
            global_contrast = self._calculate_global_contrast(gray, basic_stats)

            # Local contrast analysis
            local_contrast = self._calculate_local_contrast(gray)

            # Contrast distribution analysis
            distribution_metrics = self._calculate_contrast_distribution(gray)

            # Edge-based contrast
            edge_contrast = self._calculate_edge_contrast(gray)

            # Dynamic range analysis
            dynamic_range = self._calculate_dynamic_range(gray)

            # Combine all results
            result = {
                **basic_stats,
                **global_contrast,
                **local_contrast,
                **distribution_metrics,
                **edge_contrast,
                **dynamic_range
            }

            return result

        except Exception as e:
            logger.error(f"Error in contrast analysis: {e}")
            return self._empty_result()

    def _calculate_basic_statistics(self, gray: np.ndarray) -> Dict[str, float]:
        """Calculate basic intensity statistics."""
        mean_intensity = float(np.mean(gray))
        std_intensity = float(np.std(gray))
        min_intensity = float(np.min(gray))
        max_intensity = float(np.max(gray))
        median_intensity = float(np.median(gray))

        return {
            'mean_intensity': mean_intensity,
            'std_intensity': std_intensity,
            'min_intensity': min_intensity,
            'max_intensity': max_intensity,
            'median_intensity': median_intensity
        }

    def _calculate_global_contrast(self, gray: np.ndarray, basic_stats: Dict) -> Dict[str, float]:
        """Calculate global contrast measures."""
        mean_val = basic_stats['mean_intensity']
        std_val = basic_stats['std_intensity']
        min_val = basic_stats['min_intensity']
        max_val = basic_stats['max_intensity']

        # RMS Contrast (most common for DIC)
        rms_contrast = float(std_val / (mean_val + 1e-6))

        # Michelson Contrast
        if (max_val + min_val) > 0:
            michelson_contrast = float((max_val - min_val) / (max_val + min_val))
        else:
            michelson_contrast = 0.0

        # Weber Contrast
        weber_contrast = float((max_val - mean_val) / (mean_val + 1e-6))

        # Coefficient of Variation
        cv_contrast = float(std_val / (mean_val + 1e-6))

        # Simple contrast ratio
        if max_val > 0:
            simple_contrast = float((max_val - min_val) / max_val)
        else:
            simple_contrast = 0.0

        return {
            'rms_contrast': rms_contrast,
            'michelson_contrast': michelson_contrast,
            'weber_contrast': weber_contrast,
            'cv_contrast': cv_contrast,
            'simple_contrast': simple_contrast
        }

    def _calculate_local_contrast(self, gray: np.ndarray) -> Dict[str, float]:
        """Calculate local contrast variations."""
        h, w = gray.shape

        if h < self.local_window_size or w < self.local_window_size:
            return {
                'local_contrast_mean': 0.0,
                'local_contrast_std': 0.0,
                'local_contrast_max': 0.0,
                'local_contrast_min': 0.0
            }

        # Create local mean filter
        kernel = np.ones((self.local_window_size, self.local_window_size)) / (self.local_window_size ** 2)
        local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)

        # Calculate local contrast using different methods
        local_contrasts = []

        # Method 1: Local RMS contrast
        local_diff = gray.astype(np.float32) - local_mean
        local_rms = np.sqrt(cv2.filter2D(local_diff ** 2, -1, kernel))
        local_rms_contrast = local_rms / (local_mean + 1e-6)
        local_contrasts.append(local_rms_contrast)

        # Method 2: Local standard deviation
        local_std = cv2.filter2D((gray.astype(np.float32) - local_mean) ** 2, -1, kernel)
        local_std = np.sqrt(local_std)
        local_std_contrast = local_std / (local_mean + 1e-6)
        local_contrasts.append(local_std_contrast)

        # Combine local contrast measures
        combined_local = (local_rms_contrast + local_std_contrast) / 2

        return {
            'local_contrast_mean': float(np.mean(combined_local)),
            'local_contrast_std': float(np.std(combined_local)),
            'local_contrast_max': float(np.max(combined_local)),
            'local_contrast_min': float(np.min(combined_local))
        }

    def _calculate_contrast_distribution(self, gray: np.ndarray) -> Dict[str, Any]:
        """Analyze contrast distribution across the image."""
        # Calculate local contrast at multiple scales
        contrasts_multiscale = []

        for window_size in [3, 5, 7, 9]:
            if gray.shape[0] > window_size and gray.shape[1] > window_size:
                kernel = np.ones((window_size, window_size)) / (window_size ** 2)
                local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
                local_std = cv2.filter2D(
                    (gray.astype(np.float32) - local_mean) ** 2, -1, kernel
                )
                local_std = np.sqrt(local_std)
                local_contrast = local_std / (local_mean + 1e-6)
                contrasts_multiscale.append(local_contrast)

        if not contrasts_multiscale:
            return {
                'contrast_percentiles': [0.0] * len(self.contrast_percentiles),
                'contrast_entropy': 0.0,
                'contrast_uniformity': 0.0
            }

        # Average across scales
        avg_contrast = np.mean(contrasts_multiscale, axis=0)

        # Calculate percentiles
        percentiles = [float(np.percentile(avg_contrast, p)) for p in self.contrast_percentiles]

        # Calculate entropy of contrast distribution
        hist, _ = np.histogram(avg_contrast, bins=64, density=True)
        hist = hist[hist > 0]
        contrast_entropy = float(-np.sum(hist * np.log2(hist))) if len(hist) > 0 else 0.0

        # Contrast uniformity (inverse of standard deviation)
        contrast_uniformity = float(1.0 / (1.0 + np.std(avg_contrast)))

        return {
            'contrast_percentiles': percentiles,
            'contrast_entropy': contrast_entropy,
            'contrast_uniformity': contrast_uniformity
        }

    def _calculate_edge_contrast(self, gray: np.ndarray) -> Dict[str, float]:
        """Calculate contrast at edges and boundaries."""
        # Calculate gradients using the universal gradient analyzer
        grad_x, grad_y, gradient_magnitude = self.gradient_analyzer.calculate_gradients(gray, 'sobel', normalize=True)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        edge_pixels = edges > 0

        if not np.any(edge_pixels):
            return {
                'edge_contrast_mean': 0.0,
                'edge_contrast_max': 0.0,
                'edge_density': 0.0,
                'edge_strength': 0.0
            }

        # Calculate contrast at edge locations
        edge_gradients = gradient_magnitude[edge_pixels]

        edge_contrast_mean = float(np.mean(edge_gradients))
        edge_contrast_max = float(np.max(edge_gradients))
        edge_density = float(np.sum(edge_pixels) / gray.size)
        edge_strength = float(np.mean(gradient_magnitude))

        return {
            'edge_contrast_mean': edge_contrast_mean,
            'edge_contrast_max': edge_contrast_max,
            'edge_density': edge_density,
            'edge_strength': edge_strength
        }

    def _calculate_dynamic_range(self, gray: np.ndarray) -> Dict[str, float]:
        """Calculate dynamic range characteristics."""
        min_val = float(np.min(gray))
        max_val = float(np.max(gray))

        # Full dynamic range
        dynamic_range = max_val - min_val

        # Effective dynamic range (5th to 95th percentile)
        p5 = float(np.percentile(gray, 5))
        p95 = float(np.percentile(gray, 95))
        effective_range = p95 - p5

        # Dynamic range utilization
        theoretical_max = 255.0
        range_utilization = dynamic_range / theoretical_max

        # Histogram analysis for dynamic range
        hist, bin_edges = np.histogram(gray, bins=256, range=(0, 256))

        # Find first and last non-zero bins
        non_zero_bins = np.where(hist > 0)[0]
        if len(non_zero_bins) > 0:
            used_range = non_zero_bins[-1] - non_zero_bins[0]
            histogram_utilization = used_range / 255.0
        else:
            histogram_utilization = 0.0

        # Bit depth estimation
        unique_values = len(np.unique(gray))
        effective_bit_depth = float(np.log2(unique_values)) if unique_values > 1 else 0.0

        return {
            'dynamic_range': dynamic_range,
            'effective_range': effective_range,
            'range_utilization': range_utilization,
            'histogram_utilization': float(histogram_utilization),
            'effective_bit_depth': effective_bit_depth,
            'unique_intensities': float(unique_values)
        }

    def calculate_contrast_quality_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate overall contrast quality score.

        Args:
            metrics: Contrast metrics from analyze()

        Returns:
            Quality score between 0.0 and 1.0
        """
        try:
            # Extract key metrics
            rms_contrast = metrics.get('rms_contrast', 0.0)
            michelson_contrast = metrics.get('michelson_contrast', 0.0)
            local_contrast_mean = metrics.get('local_contrast_mean', 0.0)
            range_utilization = metrics.get('range_utilization', 0.0)
            edge_strength = metrics.get('edge_strength', 0.0)

            # Score individual main_components
            # RMS contrast scoring (optimal: 0.2-0.6)
            if 0.2 <= rms_contrast <= 0.6:
                rms_score = 1.0
            elif 0.1 <= rms_contrast <= 0.8:
                rms_score = 0.8
            elif 0.05 <= rms_contrast <= 1.0:
                rms_score = 0.6
            else:
                rms_score = 0.3

            # Michelson contrast scoring
            michelson_score = min(1.0, michelson_contrast * 2.0)

            # Local contrast scoring
            local_score = min(1.0, local_contrast_mean / 0.3)

            # Dynamic range scoring
            range_score = min(1.0, range_utilization * 2.0)

            # Edge strength scoring
            edge_score = min(1.0, edge_strength / 50.0)

            # Weighted combination
            quality_score = (
                    rms_score * 0.3 +
                    michelson_score * 0.2 +
                    local_score * 0.2 +
                    range_score * 0.15 +
                    edge_score * 0.15
            )

            return max(0.0, min(1.0, quality_score))

        except Exception as e:
            logger.warning(f"Error calculating contrast quality score: {e}")
            return 0.0

    def analyze_local_contrast_quality(self, image: np.ndarray, window_size: int = 32) -> np.ndarray:
        """
        Analyze contrast quality in local windows across the image.

        Args:
            image: Input image
            window_size: Size of analysis windows

        Returns:
            2D array of local contrast quality scores
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)

        step = max(1, window_size // 4)

        for y in range(0, h - window_size + 1, step):
            for x in range(0, w - window_size + 1, step):
                # Extract local window
                window = gray[y:y + window_size, x:x + window_size]

                # Analyze local contrast
                local_metrics = self.analyze(window)
                local_quality = self.calculate_contrast_quality_score(local_metrics)

                # Map back to image coordinates
                y_end = min(y + window_size, h)
                x_end = min(x + window_size, w)
                quality_map[y:y_end, x:x_end] += local_quality
                count_map[y:y_end, x:x_end] += 1

        # Average overlapping regions
        mask = count_map > 0
        quality_map[mask] /= count_map[mask]

        return quality_map

    def get_contrast_recommendations(self, metrics: Dict[str, Any]) -> list:
        """Generate recommendations based on contrast analysis."""
        recommendations = []

        rms_contrast = metrics.get('rms_contrast', 0.0)
        dynamic_range = metrics.get('dynamic_range', 0.0)
        range_utilization = metrics.get('range_utilization', 0.0)
        edge_strength = metrics.get('edge_strength', 0.0)

        # RMS contrast recommendations
        if rms_contrast < 0.1:
            recommendations.append(" Very low contrast - improve lighting or pattern")
            recommendations.append("Consider adjusting camera exposure or gain settings")
        elif rms_contrast < 0.2:
            recommendations.append(" Low contrast - may affect correlation accuracy")
            recommendations.append("Try increasing lighting contrast or adjusting camera settings")
        elif rms_contrast > 0.8:
            recommendations.append(" Very high contrast - may cause saturation")
            recommendations.append("Consider reducing lighting contrast or exposure")

        # Dynamic range recommendations
        if range_utilization < 0.3:
            recommendations.append(" Poor dynamic range utilization")
            recommendations.append("Adjust camera exposure to use full intensity range")
        elif dynamic_range < 50:
            recommendations.append(" Limited dynamic range")
            recommendations.append("Improve lighting setup or check camera bit depth")

        # Edge strength recommendations
        if edge_strength < 10:
            recommendations.append(" Weak edge content")
            recommendations.append("Ensure sharp focus and adequate speckle pattern")

        # Overall assessment
        quality_score = self.calculate_contrast_quality_score(metrics)
        if quality_score > 0.8:
            recommendations.append(" Excellent contrast for DIC analysis")
        elif quality_score > 0.6:
            recommendations.append(" Good contrast for DIC analysis")
        elif quality_score > 0.4:
            recommendations.append(" Acceptable contrast - minor improvements recommended")
        else:
            recommendations.append(" Poor contrast - significant improvements needed")

        return recommendations

    def compare_regions(self, image: np.ndarray, regions: list) -> Dict[str, Any]:
        """
        Compare contrast characteristics across different image regions.

        Args:
            image: Input image
            regions: List of region coordinates [(x1,y1,x2,y2), ...]

        Returns:
            Dictionary with comparison results
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        region_results = []

        for i, (x1, y1, x2, y2) in enumerate(regions):
            # Extract region
            region = gray[y1:y2, x1:x2]

            if region.size > 0:
                # Analyze region
                metrics = self.analyze(region)
                quality = self.calculate_contrast_quality_score(metrics)

                region_results.append({
                    'region_id': i,
                    'bounds': (x1, y1, x2, y2),
                    'metrics': metrics,
                    'quality_score': quality
                })

        if not region_results:
            return {'regions': [], 'comparison': {}}

        # Compare regions
        quality_scores = [r['quality_score'] for r in region_results]
        rms_contrasts = [r['metrics']['rms_contrast'] for r in region_results]

        comparison = {
            'best_region': int(np.argmax(quality_scores)),
            'worst_region': int(np.argmin(quality_scores)),
            'quality_range': float(np.max(quality_scores) - np.min(quality_scores)),
            'quality_std': float(np.std(quality_scores)),
            'contrast_consistency': float(1.0 / (1.0 + np.std(rms_contrasts))),
            'mean_quality': float(np.mean(quality_scores))
        }

        return {
            'regions': region_results,
            'comparison': comparison
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            'mean_intensity': 0.0,
            'std_intensity': 0.0,
            'min_intensity': 0.0,
            'max_intensity': 0.0,
            'median_intensity': 0.0,
            'rms_contrast': 0.0,
            'michelson_contrast': 0.0,
            'weber_contrast': 0.0,
            'cv_contrast': 0.0,
            'simple_contrast': 0.0,
            'local_contrast_mean': 0.0,
            'local_contrast_std': 0.0,
            'local_contrast_max': 0.0,
            'local_contrast_min': 0.0,
            'contrast_percentiles': [0.0] * len(self.contrast_percentiles),
            'contrast_entropy': 0.0,
            'contrast_uniformity': 0.0,
            'edge_contrast_mean': 0.0,
            'edge_contrast_max': 0.0,
            'edge_density': 0.0,
            'edge_strength': 0.0,
            'dynamic_range': 0.0,
            'effective_range': 0.0,
            'range_utilization': 0.0,
            'histogram_utilization': 0.0,
            'effective_bit_depth': 0.0,
            'unique_intensities': 0.0
        }