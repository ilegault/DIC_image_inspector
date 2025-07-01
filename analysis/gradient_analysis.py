# analysis/gradient_analysis.py - Gradient Analysis Module

import cv2
import numpy as np
from typing import Dict, Any, Tuple, List
import logging
from scipy import ndimage
from scipy.signal import convolve2d

logger = logging.getLogger(__name__)


class GradientAnalyzer:
    """
    Analyzes image gradients for DIC quality assessment.

    Gradient analysis is fundamental for DIC as correlation algorithms rely on
    local intensity variations. This module implements multiple gradient measures
    including magnitude, direction, coherence, and spatial distribution analysis.
    """

    def __init__(self):
        self.gradient_kernels = {
            'sobel': {'x': np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]),
                     'y': np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])},
            'prewitt': {'x': np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]]),
                       'y': np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])},
            'scharr': {'x': np.array([[-3, 0, 3], [-10, 0, 10], [-3, 0, 3]]),
                      'y': np.array([[-3, -10, -3], [0, 0, 0], [3, 10, 3]])}
        }
        self.local_window_sizes = [5, 9, 15, 21]  # For multi-scale analysis
        self.gradient_percentiles = [25, 50, 75, 90, 95, 99]

    def analyze(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Perform complete gradient analysis on an image.

        Args:
            image: Input image (grayscale or color)

        Returns:
            Dictionary containing gradient metrics
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        if gray.size == 0:
            return self._empty_result()

        try:
            # Basic gradient calculations
            gradient_maps = self._calculate_gradient_maps(gray)
            
            # Gradient magnitude and direction analysis
            magnitude_metrics = self._analyze_gradient_magnitude(gradient_maps)
            
            # Gradient direction analysis
            direction_metrics = self._analyze_gradient_direction(gradient_maps)
            
            # Multi-scale gradient analysis
            multiscale_metrics = self._analyze_multiscale_gradients(gray)
            
            # Local gradient coherence
            coherence_metrics = self._analyze_gradient_coherence(gradient_maps)
            
            # Gradient distribution analysis
            distribution_metrics = self._analyze_gradient_distribution(gradient_maps)
            
            # Edge-based gradient analysis
            edge_metrics = self._analyze_edge_gradients(gray, gradient_maps)
            
            # Spatial gradient uniformity
            spatial_metrics = self._analyze_spatial_uniformity(gradient_maps)
            
            # Gradient quality assessment
            quality_metrics = self._assess_gradient_quality(gradient_maps, gray)

            # Combine all results
            result = {
                **magnitude_metrics,
                **direction_metrics,
                **multiscale_metrics,
                **coherence_metrics,
                **distribution_metrics,
                **edge_metrics,
                **spatial_metrics,
                **quality_metrics
            }

            return result

        except Exception as e:
            logger.error(f"Error in gradient analysis: {e}")
            return self._empty_result()

    def _calculate_gradient_maps(self, gray: np.ndarray) -> Dict[str, np.ndarray]:
        """Calculate gradient maps using different operators."""
        gradient_maps = {}
        
        # Convert to float for better precision
        gray_float = gray.astype(np.float32)
        
        for kernel_name, kernels in self.gradient_kernels.items():
            # Calculate gradients
            grad_x = convolve2d(gray_float, kernels['x'], mode='same', boundary='symm')
            grad_y = convolve2d(gray_float, kernels['y'], mode='same', boundary='symm')
            
            # Calculate magnitude and direction
            magnitude = np.sqrt(grad_x**2 + grad_y**2)
            direction = np.arctan2(grad_y, grad_x)
            
            gradient_maps[kernel_name] = {
                'grad_x': grad_x,
                'grad_y': grad_y,
                'magnitude': magnitude,
                'direction': direction
            }
        
        # Also calculate using OpenCV for comparison
        grad_x_cv = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y_cv = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude_cv = np.sqrt(grad_x_cv**2 + grad_y_cv**2)
        direction_cv = np.arctan2(grad_y_cv, grad_x_cv)
        
        gradient_maps['opencv'] = {
            'grad_x': grad_x_cv,
            'grad_y': grad_y_cv,
            'magnitude': magnitude_cv,
            'direction': direction_cv
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
        
        # Use Sobel as primary gradient
        primary_grad = gradient_maps['sobel']
        direction = primary_grad['direction']
        magnitude = primary_grad['magnitude']
        
        # Only analyze directions where magnitude is significant
        threshold = np.percentile(magnitude, 25)  # Use 25th percentile as threshold
        significant_mask = magnitude > threshold
        
        if not np.any(significant_mask):
            return {
                'direction_entropy': 0.0,
                'direction_coherence': 0.0,
                'direction_uniformity': 0.0,
                'dominant_direction': 0.0,
                'direction_variance': 0.0
            }
        
        significant_directions = direction[significant_mask]
        
        # Direction histogram analysis
        hist, bin_edges = np.histogram(significant_directions, bins=36, range=(-np.pi, np.pi))
        hist_normalized = hist / np.sum(hist)
        
        # Direction entropy
        hist_nonzero = hist_normalized[hist_normalized > 0]
        direction_entropy = float(-np.sum(hist_nonzero * np.log2(hist_nonzero))) if len(hist_nonzero) > 0 else 0.0
        
        # Direction coherence (measure of how aligned gradients are)
        # Calculate mean direction vector
        mean_cos = np.mean(np.cos(significant_directions))
        mean_sin = np.mean(np.sin(significant_directions))
        direction_coherence = float(np.sqrt(mean_cos**2 + mean_sin**2))
        
        # Direction uniformity (inverse of entropy, normalized)
        max_entropy = np.log2(36)  # Maximum possible entropy for 36 bins
        direction_uniformity = float(1.0 - (direction_entropy / max_entropy)) if max_entropy > 0 else 0.0
        
        # Dominant direction
        dominant_bin = np.argmax(hist)
        dominant_direction = float(bin_edges[dominant_bin] + (bin_edges[1] - bin_edges[0]) / 2)
        
        # Direction variance
        direction_variance = float(np.var(significant_directions))
        
        results.update({
            'direction_entropy': direction_entropy,
            'direction_coherence': direction_coherence,
            'direction_uniformity': direction_uniformity,
            'dominant_direction': dominant_direction,
            'direction_variance': direction_variance
        })
        
        return results

    def _analyze_multiscale_gradients(self, gray: np.ndarray) -> Dict[str, Any]:
        """Analyze gradients at multiple scales."""
        results = {}
        scale_results = []
        
        for window_size in self.local_window_sizes:
            if gray.shape[0] < window_size or gray.shape[1] < window_size:
                continue
                
            # Create Gaussian kernel for smoothing
            sigma = window_size / 6.0  # Standard relationship
            kernel_size = int(2 * np.ceil(2 * sigma) + 1)
            
            # Smooth image at current scale
            smoothed = cv2.GaussianBlur(gray, (kernel_size, kernel_size), sigma)
            
            # Calculate gradients at this scale
            grad_x = cv2.Sobel(smoothed, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(smoothed, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Store scale-specific metrics
            scale_data = {
                'scale': window_size,
                'magnitude_mean': float(np.mean(magnitude)),
                'magnitude_std': float(np.std(magnitude)),
                'magnitude_max': float(np.max(magnitude))
            }
            scale_results.append(scale_data)
        
        if scale_results:
            # Multi-scale consistency analysis
            means = [s['magnitude_mean'] for s in scale_results]
            stds = [s['magnitude_std'] for s in scale_results]
            
            results.update({
                'multiscale_consistency': float(1.0 / (1.0 + np.std(means))),
                'multiscale_mean_variation': float(np.std(means)),
                'multiscale_std_variation': float(np.std(stds)),
                'scale_results': scale_results
            })
        else:
            results.update({
                'multiscale_consistency': 0.0,
                'multiscale_mean_variation': 0.0,
                'multiscale_std_variation': 0.0,
                'scale_results': []
            })
        
        return results

    def _analyze_gradient_coherence(self, gradient_maps: Dict) -> Dict[str, Any]:
        """Analyze local gradient coherence and structure."""
        results = {}
        
        primary_grad = gradient_maps['sobel']
        grad_x = primary_grad['grad_x']
        grad_y = primary_grad['grad_y']
        magnitude = primary_grad['magnitude']
        
        # Structure tensor analysis for coherence
        # Calculate structure tensor components
        Jxx = grad_x * grad_x
        Jxy = grad_x * grad_y
        Jyy = grad_y * grad_y
        
        # Apply Gaussian smoothing to structure tensor
        sigma = 2.0
        kernel_size = int(2 * np.ceil(2 * sigma) + 1)
        
        Jxx_smooth = cv2.GaussianBlur(Jxx.astype(np.float32), (kernel_size, kernel_size), sigma)
        Jxy_smooth = cv2.GaussianBlur(Jxy.astype(np.float32), (kernel_size, kernel_size), sigma)
        Jyy_smooth = cv2.GaussianBlur(Jyy.astype(np.float32), (kernel_size, kernel_size), sigma)
        
        # Calculate coherence measure
        trace = Jxx_smooth + Jyy_smooth
        determinant = Jxx_smooth * Jyy_smooth - Jxy_smooth * Jxy_smooth
        
        # Avoid division by zero
        coherence = np.zeros_like(trace)
        valid_mask = trace > 1e-6
        
        if np.any(valid_mask):
            lambda1 = 0.5 * (trace + np.sqrt(trace**2 - 4 * determinant))
            lambda2 = 0.5 * (trace - np.sqrt(trace**2 - 4 * determinant))
            
            # Coherence as (lambda1 - lambda2) / (lambda1 + lambda2)
            coherence[valid_mask] = (lambda1[valid_mask] - lambda2[valid_mask]) / (lambda1[valid_mask] + lambda2[valid_mask] + 1e-6)
        
        results.update({
            'coherence_mean': float(np.mean(coherence)),
            'coherence_std': float(np.std(coherence)),
            'coherence_max': float(np.max(coherence)),
            'high_coherence_ratio': float(np.sum(coherence > 0.5) / coherence.size)
        })
        
        return results

    def _analyze_gradient_distribution(self, gradient_maps: Dict) -> Dict[str, Any]:
        """Analyze spatial distribution of gradients."""
        results = {}
        
        primary_grad = gradient_maps['sobel']
        magnitude = primary_grad['magnitude']
        
        # Divide image into grid for spatial analysis
        h, w = magnitude.shape
        grid_size = 8
        cell_h = h // grid_size
        cell_w = w // grid_size
        
        if cell_h < 1 or cell_w < 1:
            return {
                'spatial_uniformity': 0.0,
                'gradient_concentration': 0.0,
                'spatial_entropy': 0.0
            }
        
        cell_means = []
        cell_stds = []
        
        for i in range(grid_size):
            for j in range(grid_size):
                y1 = i * cell_h
                y2 = min((i + 1) * cell_h, h)
                x1 = j * cell_w
                x2 = min((j + 1) * cell_w, w)
                
                cell = magnitude[y1:y2, x1:x2]
                if cell.size > 0:
                    cell_means.append(np.mean(cell))
                    cell_stds.append(np.std(cell))
        
        if cell_means:
            # Spatial uniformity (inverse of coefficient of variation)
            mean_of_means = np.mean(cell_means)
            std_of_means = np.std(cell_means)
            spatial_uniformity = float(1.0 / (1.0 + std_of_means / (mean_of_means + 1e-6)))
            
            # Gradient concentration (how concentrated gradients are)
            total_gradient = np.sum(magnitude)
            if total_gradient > 0:
                cell_weights = np.array(cell_means) / total_gradient
                gradient_concentration = float(-np.sum(cell_weights * np.log2(cell_weights + 1e-6)))
            else:
                gradient_concentration = 0.0
            
            # Spatial entropy
            hist, _ = np.histogram(cell_means, bins=16, density=True)
            hist = hist[hist > 0]
            spatial_entropy = float(-np.sum(hist * np.log2(hist))) if len(hist) > 0 else 0.0
            
            results.update({
                'spatial_uniformity': spatial_uniformity,
                'gradient_concentration': gradient_concentration,
                'spatial_entropy': spatial_entropy
            })
        else:
            results.update({
                'spatial_uniformity': 0.0,
                'gradient_concentration': 0.0,
                'spatial_entropy': 0.0
            })
        
        return results

    def _analyze_edge_gradients(self, gray: np.ndarray, gradient_maps: Dict) -> Dict[str, Any]:
        """Analyze gradients at edge locations."""
        results = {}
        
        magnitude = gradient_maps['sobel']['magnitude']
        
        # Edge detection using multiple methods
        edges_canny = cv2.Canny(gray, 50, 150)
        
        # Laplacian edge detection
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        edges_laplacian = np.abs(laplacian) > np.percentile(np.abs(laplacian), 90)
        
        # Combine edge maps
        edges_combined = (edges_canny > 0) | edges_laplacian
        
        if not np.any(edges_combined):
            return {
                'edge_gradient_mean': 0.0,
                'edge_gradient_max': 0.0,
                'edge_gradient_ratio': 0.0,
                'edge_strength_uniformity': 0.0
            }
        
        # Analyze gradients at edge locations
        edge_gradients = magnitude[edges_combined]
        
        results.update({
            'edge_gradient_mean': float(np.mean(edge_gradients)),
            'edge_gradient_max': float(np.max(edge_gradients)),
            'edge_gradient_ratio': float(np.sum(edges_combined) / magnitude.size),
            'edge_strength_uniformity': float(1.0 / (1.0 + np.std(edge_gradients) / (np.mean(edge_gradients) + 1e-6)))
        })
        
        return results

    def _analyze_spatial_uniformity(self, gradient_maps: Dict) -> Dict[str, Any]:
        """Analyze spatial uniformity of gradient distribution."""
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
        local_var = convolve2d((magnitude - local_mean)**2, kernel, mode='same', boundary='symm')
        local_std = np.sqrt(local_var)
        
        # Local uniformity measure
        local_cv = local_std / (local_mean + 1e-6)
        local_uniformity = 1.0 / (1.0 + local_cv)
        
        # Texture energy (second moment)
        normalized_magnitude = magnitude / (np.max(magnitude) + 1e-6)
        texture_energy = float(np.sum(normalized_magnitude**2))
        
        # Homogeneity measure
        # Calculate co-occurrence matrix for gradient magnitudes
        quantized_magnitude = (normalized_magnitude * 15).astype(np.int32)
        quantized_magnitude = np.clip(quantized_magnitude, 0, 15)
        
        # Simple homogeneity calculation
        homogeneity = 0.0
        count = 0
        for i in range(quantized_magnitude.shape[0] - 1):
            for j in range(quantized_magnitude.shape[1] - 1):
                diff = abs(quantized_magnitude[i, j] - quantized_magnitude[i, j+1])
                homogeneity += 1.0 / (1.0 + diff)
                diff = abs(quantized_magnitude[i, j] - quantized_magnitude[i+1, j])
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
        optimal_mean_range = (10, 50)  # Depends on image bit depth and contrast
        optimal_std_range = (5, 30)
        
        # Score gradient strength
        if optimal_mean_range[0] <= mean_magnitude <= optimal_mean_range[1]:
            strength_score = 1.0
        else:
            strength_score = max(0.0, 1.0 - abs(mean_magnitude - np.mean(optimal_mean_range)) / np.mean(optimal_mean_range))
        
        # Score gradient variation
        if optimal_std_range[0] <= std_magnitude <= optimal_std_range[1]:
            variation_score = 1.0
        else:
            variation_score = max(0.0, 1.0 - abs(std_magnitude - np.mean(optimal_std_range)) / np.mean(optimal_std_range))
        
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
            'overall_gradient_quality': 0.0
        }

    def calculate_gradient_quality_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate overall gradient quality score for DIC applications.

        Args:
            metrics: Gradient metrics from analyze()

        Returns:
            Quality score between 0.0 and 1.0
        """
        try:
            return metrics.get('overall_gradient_quality', 0.0)
        except Exception as e:
            logger.warning(f"Error calculating gradient quality score: {e}")
            return 0.0

    def analyze_local_gradient_quality(self, image: np.ndarray, window_size: int = 32) -> np.ndarray:
        """
        Analyze gradient quality in local windows across the image.

        Args:
            image: Input image
            window_size: Size of analysis windows

        Returns:
            2D array of local gradient quality scores
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

                # Analyze local gradients
                local_metrics = self.analyze(window)
                quality_score = self.calculate_gradient_quality_score(local_metrics)

                # Add to quality map
                quality_map[y:y + window_size, x:x + window_size] += quality_score
                count_map[y:y + window_size, x:x + window_size] += 1

        # Normalize by overlap count
        valid_mask = count_map > 0
        quality_map[valid_mask] /= count_map[valid_mask]

        return quality_map

    def get_gradient_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations for improving gradient quality.

        Args:
            metrics: Gradient metrics from analyze()

        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        try:
            # Check gradient strength
            strength_score = metrics.get('gradient_strength_score', 0.0)
            if strength_score < 0.6:
                recommendations.append("Consider improving image contrast to enhance gradient strength")
            
            # Check gradient coverage
            coverage_score = metrics.get('gradient_coverage_score', 0.0)
            if coverage_score < 0.5:
                recommendations.append("Increase speckle pattern density for better gradient coverage")
            
            # Check spatial uniformity
            spatial_uniformity = metrics.get('spatial_uniformity', 0.0)
            if spatial_uniformity < 0.6:
                recommendations.append("Improve speckle pattern uniformity across the image")
            
            # Check coherence
            coherence_mean = metrics.get('coherence_mean', 0.0)
            if coherence_mean > 0.8:
                recommendations.append("Pattern may be too regular - consider adding more randomness")
            elif coherence_mean < 0.2:
                recommendations.append("Pattern may be too noisy - consider smoothing or better focus")
            
            # Check multiscale consistency
            multiscale_consistency = metrics.get('multiscale_consistency', 0.0)
            if multiscale_consistency < 0.7:
                recommendations.append("Improve pattern consistency across different scales")
            
            if not recommendations:
                recommendations.append("Gradient quality is good for DIC applications")
                
        except Exception as e:
            logger.warning(f"Error generating gradient recommendations: {e}")
            recommendations.append("Unable to generate recommendations due to analysis error")
        
        return recommendations