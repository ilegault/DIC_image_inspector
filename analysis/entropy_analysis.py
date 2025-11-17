"""
Entropy analysis module for DIC image quality assessment.

This module evaluates information content and uniqueness of DIC images through
entropy measurements. It calculates Shannon entropy, local entropy variation,
and pattern uniqueness to assess the randomness and information density of
speckle patterns, which are crucial for reliable DIC correlation.

Usage:
    from analysis.entropy_analysis import EntropyAnalyzer

    analyzer = EntropyAnalyzer()
    results = analyzer.analyze(image_data)
"""

import cv2
import numpy as np
from typing import Dict, Any, Tuple
import logging
from scipy.stats import entropy as scipy_entropy
from analysis.gradient_analysis import GradientAnalyzer

logger = logging.getLogger(__name__)


class EntropyAnalyzer:
    """
    Analyzes information content and entropy for DIC quality assessment.

    Information content is crucial for correlation uniqueness in DIC.
    This module implements Shannon entropy, local entropy, and texture
    complexity measures to assess pattern information content.
    """

    def __init__(self):
        self.gradient_analyzer = GradientAnalyzer()
        self.histogram_bins = 64  # Bins for entropy calculation
        self.local_window_sizes = [5, 7, 9, 11]  # Multiple scales for local entropy
        self.texture_window_size = 7  # Window size for texture analysis

    def analyze(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Perform complete entropy and information content analysis.

        Args:
            image: Input image (grayscale)

        Returns:
            Dictionary containing entropy metrics
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        if gray.size == 0:
            return self._empty_result()

        try:
            # For large images, use optimized analysis
            if gray.size > 1000000:  # > 1 megapixel
                return self._analyze_optimized(gray)

            # Global Shannon entropy
            global_entropy = self._calculate_global_entropy(gray)

            # Local entropy analysis (simplified for performance)
            local_entropy = self._calculate_local_entropy_fast(gray)

            # Texture entropy (simplified)
            texture_entropy = self._calculate_texture_entropy_fast(gray)

            # Information measures (essential ones only)
            information_measures = self._calculate_information_measures_fast(gray)

            # Entropy distribution analysis
            entropy_distribution = self._calculate_entropy_distribution(gray)

            # Combine all results
            result = {
                **global_entropy,
                **local_entropy,
                **texture_entropy,
                **information_measures,
                **entropy_distribution,
                # Add default values for skipped calculations
                'conditional_entropy_h': 0.0,
                'conditional_entropy_v': 0.0,
                'mutual_information_h': 0.0,
                'mutual_information_v': 0.0,
                'joint_entropy_horizontal': 0.0,
                'joint_entropy_vertical': 0.0,
            }

            return result

        except Exception as e:
            logger.error(f"Error in entropy analysis: {e}")
            return self._empty_result()

    def _analyze_optimized(self, gray: np.ndarray) -> Dict[str, Any]:
        """Optimized analysis for large images."""
        # Downsample for analysis to improve performance
        h, w = gray.shape
        scale_factor = min(1.0, 800.0 / max(h, w))  # Max 800px on longest side

        if scale_factor < 1.0:
            new_h, new_w = int(h * scale_factor), int(w * scale_factor)
            gray_small = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            gray_small = gray

        # Calculate basic entropy metrics on downsampled image
        global_entropy = self._calculate_global_entropy(gray_small)
        local_entropy = self._calculate_local_entropy_fast(gray_small)
        texture_entropy = self._calculate_texture_entropy_fast(gray_small)
        information_measures = self._calculate_information_measures_fast(gray_small)
        entropy_distribution = self._calculate_entropy_distribution(gray_small)

        return {
            **global_entropy,
            **local_entropy,
            **texture_entropy,
            **information_measures,
            **entropy_distribution,
            # Default values for complex calculations
            'conditional_entropy_h': 0.0,
            'conditional_entropy_v': 0.0,
            'mutual_information_h': 0.0,
            'mutual_information_v': 0.0,
            'joint_entropy_horizontal': 0.0,
            'joint_entropy_vertical': 0.0,
        }

    def _calculate_local_entropy_fast(self, gray: np.ndarray) -> Dict[str, float]:
        """Fast local entropy calculation using sampling."""
        h, w = gray.shape

        # Use only one window size for speed
        window_size = 7
        if h < window_size or w < window_size:
            return {
                'local_entropy_mean': 0.0,
                'local_entropy_std': 0.0,
                'local_entropy_max': 0.0,
                'local_entropy_min': 0.0
            }

        # Sample fewer points for speed
        step = max(window_size, min(h, w) // 20)  # Sample ~400 points max
        window_entropies = []

        for y in range(0, h - window_size + 1, step):
            for x in range(0, w - window_size + 1, step):
                window = gray[y:y + window_size, x:x + window_size]

                # Calculate entropy for this window
                hist, _ = np.histogram(window, bins=16, range=(0, 256), density=True)
                hist = hist[hist > 0]

                if len(hist) > 0:
                    window_entropy = -np.sum(hist * np.log2(hist))
                    window_entropies.append(window_entropy)

        if not window_entropies:
            return {
                'local_entropy_mean': 0.0,
                'local_entropy_std': 0.0,
                'local_entropy_max': 0.0,
                'local_entropy_min': 0.0
            }

        window_entropies = np.array(window_entropies)

        return {
            'local_entropy_mean': float(np.mean(window_entropies)),
            'local_entropy_std': float(np.std(window_entropies)),
            'local_entropy_max': float(np.max(window_entropies)),
            'local_entropy_min': float(np.min(window_entropies))
        }

    def _calculate_texture_entropy_fast(self, gray: np.ndarray) -> Dict[str, float]:
        """Fast texture entropy using sampling."""
        h, w = gray.shape

        if h < 3 or w < 3:
            return {
                'texture_entropy': 0.0,
                'texture_uniformity': 0.0,
                'texture_complexity': 0.0
            }

        # Sample points instead of processing every pixel
        sample_step = max(1, min(h, w) // 100)  # Sample ~10000 points max
        lbp_patterns = []

        for y in range(1, h - 1, sample_step):
            for x in range(1, w - 1, sample_step):
                center = gray[y, x]

                # 8-neighborhood comparison
                pattern = 0
                neighbors = [
                    gray[y - 1, x - 1], gray[y - 1, x], gray[y - 1, x + 1],
                    gray[y, x + 1], gray[y + 1, x + 1], gray[y + 1, x],
                    gray[y + 1, x - 1], gray[y, x - 1]
                ]

                for i, neighbor in enumerate(neighbors):
                    if neighbor >= center:
                        pattern += 2 ** i

                lbp_patterns.append(pattern)

        if not lbp_patterns:
            return {
                'texture_entropy': 0.0,
                'texture_uniformity': 0.0,
                'texture_complexity': 0.0
            }

        # Calculate texture entropy
        lbp_hist, _ = np.histogram(lbp_patterns, bins=256, density=True)
        lbp_hist = lbp_hist[lbp_hist > 0]

        if len(lbp_hist) > 0:
            texture_entropy = float(-np.sum(lbp_hist * np.log2(lbp_hist)))
        else:
            texture_entropy = 0.0

        # Texture uniformity
        unique_patterns = len(np.unique(lbp_patterns))
        texture_uniformity = float(1.0 / unique_patterns) if unique_patterns > 0 else 0.0

        # Texture complexity
        max_texture_entropy = np.log2(256)
        texture_complexity = texture_entropy / max_texture_entropy if max_texture_entropy > 0 else 0.0

        return {
            'texture_entropy': texture_entropy,
            'texture_uniformity': texture_uniformity,
            'texture_complexity': float(texture_complexity)
        }

    def _calculate_information_measures_fast(self, gray: np.ndarray) -> Dict[str, float]:
        """Fast information measures calculation."""
        # Global entropy
        global_entropy = self._calculate_global_entropy(gray)['shannon_entropy']

        # Gradient entropy (simplified) using universal gradient analyzer
        grad_x, grad_y, gradient_mag = self.gradient_analyzer.calculate_gradients(gray, 'sobel', normalize=True)
        gradient_mag_int = np.clip(gradient_mag, 0, 255).astype(np.uint8)
        gradient_entropy = self._calculate_global_entropy(gradient_mag_int)['shannon_entropy']

        # Laplacian entropy
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_int = np.clip(np.abs(laplacian), 0, 255).astype(np.uint8)
        laplacian_entropy = self._calculate_global_entropy(laplacian_int)['shannon_entropy']

        # Information gain
        gradient_info_gain = gradient_entropy - global_entropy
        laplacian_info_gain = laplacian_entropy - global_entropy

        return {
            'gradient_entropy': float(gradient_entropy),
            'laplacian_entropy': float(laplacian_entropy),
            'gradient_info_gain': float(gradient_info_gain),
            'laplacian_info_gain': float(laplacian_info_gain)
        }

    def _calculate_global_entropy(self, gray: np.ndarray) -> Dict[str, float]:
        """Calculate global Shannon entropy."""
        # Histogram-based entropy
        hist, _ = np.histogram(gray, bins=self.histogram_bins, range=(0, 256), density=True)
        hist = hist[hist > 0]  # Remove zero entries

        if len(hist) == 0:
            shannon_entropy = 0.0
        else:
            shannon_entropy = float(-np.sum(hist * np.log2(hist)))

        # Normalized entropy (0-1 scale)
        max_entropy = np.log2(self.histogram_bins)
        normalized_entropy = shannon_entropy / max_entropy if max_entropy > 0 else 0.0

        # Effective number of intensity levels
        effective_levels = 2 ** shannon_entropy if shannon_entropy > 0 else 1.0

        return {
            'shannon_entropy': shannon_entropy,
            'normalized_entropy': float(normalized_entropy),
            'effective_levels': float(effective_levels)
        }

    def _calculate_local_entropy(self, gray: np.ndarray) -> Dict[str, float]:
        """Calculate local entropy at multiple scales."""
        h, w = gray.shape
        local_entropies = []

        for window_size in self.local_window_sizes:
            if h < window_size or w < window_size:
                continue

            # Calculate local entropy in sliding windows
            window_entropies = []
            step = max(1, window_size // 2)

            for y in range(0, h - window_size + 1, step):
                for x in range(0, w - window_size + 1, step):
                    window = gray[y:y + window_size, x:x + window_size]

                    # Calculate entropy for this window
                    hist, _ = np.histogram(window, bins=16, range=(0, 256), density=True)
                    hist = hist[hist > 0]

                    if len(hist) > 0:
                        window_entropy = -np.sum(hist * np.log2(hist))
                        window_entropies.append(window_entropy)

            if window_entropies:
                local_entropies.extend(window_entropies)

        if not local_entropies:
            return {
                'local_entropy_mean': 0.0,
                'local_entropy_std': 0.0,
                'local_entropy_max': 0.0,
                'local_entropy_min': 0.0
            }

        local_entropies = np.array(local_entropies)

        return {
            'local_entropy_mean': float(np.mean(local_entropies)),
            'local_entropy_std': float(np.std(local_entropies)),
            'local_entropy_max': float(np.max(local_entropies)),
            'local_entropy_min': float(np.min(local_entropies))
        }

    def _calculate_texture_entropy(self, gray: np.ndarray) -> Dict[str, float]:
        """Calculate texture-based entropy using local binary patterns."""
        h, w = gray.shape

        if h < self.texture_window_size or w < self.texture_window_size:
            return {
                'texture_entropy': 0.0,
                'texture_uniformity': 0.0,
                'texture_complexity': 0.0
            }

        # Simplified Local Binary Pattern (LBP) calculation
        lbp_patterns = []

        for y in range(1, h - 1):
            for x in range(1, w - 1):
                center = gray[y, x]

                # 8-neighborhood comparison
                pattern = 0
                neighbors = [
                    gray[y - 1, x - 1], gray[y - 1, x], gray[y - 1, x + 1],
                    gray[y, x + 1], gray[y + 1, x + 1], gray[y + 1, x],
                    gray[y + 1, x - 1], gray[y, x - 1]
                ]

                for i, neighbor in enumerate(neighbors):
                    if neighbor >= center:
                        pattern += 2 ** i

                lbp_patterns.append(pattern)

        if not lbp_patterns:
            return {
                'texture_entropy': 0.0,
                'texture_uniformity': 0.0,
                'texture_complexity': 0.0
            }

        # Calculate texture entropy
        lbp_hist, _ = np.histogram(lbp_patterns, bins=256, density=True)
        lbp_hist = lbp_hist[lbp_hist > 0]

        if len(lbp_hist) > 0:
            texture_entropy = float(-np.sum(lbp_hist * np.log2(lbp_hist)))
        else:
            texture_entropy = 0.0

        # Texture uniformity (inverse of number of distinct patterns)
        unique_patterns = len(np.unique(lbp_patterns))
        texture_uniformity = float(1.0 / unique_patterns) if unique_patterns > 0 else 0.0

        # Texture complexity (normalized entropy)
        max_texture_entropy = np.log2(256)
        texture_complexity = texture_entropy / max_texture_entropy if max_texture_entropy > 0 else 0.0

        return {
            'texture_entropy': texture_entropy,
            'texture_uniformity': texture_uniformity,
            'texture_complexity': float(texture_complexity)
        }

    def _calculate_conditional_entropy(self, gray: np.ndarray) -> Dict[str, float]:
        """Calculate conditional entropy H(Y|X) for spatial dependencies."""
        h, w = gray.shape

        if h < 2 or w < 2:
            return {
                'conditional_entropy_h': 0.0,
                'conditional_entropy_v': 0.0,
                'mutual_information_h': 0.0,
                'mutual_information_v': 0.0
            }

        # Horizontal conditional entropy H(X[i+1] | X[i])
        horizontal_pairs = []
        for y in range(h):
            for x in range(w - 1):
                horizontal_pairs.append((gray[y, x], gray[y, x + 1]))

        # Vertical conditional entropy H(X[j+1] | X[j])
        vertical_pairs = []
        for y in range(h - 1):
            for x in range(w):
                vertical_pairs.append((gray[y, x], gray[y + 1, x]))

        # Calculate conditional entropies
        cond_entropy_h = self._calculate_conditional_entropy_from_pairs(horizontal_pairs)
        cond_entropy_v = self._calculate_conditional_entropy_from_pairs(vertical_pairs)

        # Calculate mutual information
        # MI(X,Y) = H(X) + H(Y) - H(X,Y)
        global_entropy = self._calculate_global_entropy(gray)['shannon_entropy']

        # Joint entropy for horizontal pairs
        joint_hist_h = self._calculate_joint_histogram(horizontal_pairs)
        joint_entropy_h = self._entropy_from_histogram(joint_hist_h)

        # Joint entropy for vertical pairs
        joint_hist_v = self._calculate_joint_histogram(vertical_pairs)
        joint_entropy_v = self._entropy_from_histogram(joint_hist_v)

        # Mutual information = H(X) - H(X|Y)
        mutual_info_h = global_entropy - cond_entropy_h
        mutual_info_v = global_entropy - cond_entropy_v

        return {
            'conditional_entropy_h': float(cond_entropy_h),
            'conditional_entropy_v': float(cond_entropy_v),
            'mutual_information_h': float(mutual_info_h),
            'mutual_information_v': float(mutual_info_v)
        }

    def _calculate_conditional_entropy_from_pairs(self, pairs: list) -> float:
        """Calculate conditional entropy from list of (x, y) pairs."""
        if not pairs:
            return 0.0

        # Build conditional probability distributions
        xy_counts = {}
        x_counts = {}

        for x, y in pairs:
            # Quantize to reduce computation
            x_bin = x // 8  # Reduce to 32 bins
            y_bin = y // 8

            x_counts[x_bin] = x_counts.get(x_bin, 0) + 1
            xy_counts[(x_bin, y_bin)] = xy_counts.get((x_bin, y_bin), 0) + 1

        # Calculate H(Y|X) = -∑ p(x,y) log p(y|x)
        conditional_entropy = 0.0
        total_pairs = len(pairs)

        for (x_bin, y_bin), xy_count in xy_counts.items():
            p_xy = xy_count / total_pairs
            p_y_given_x = xy_count / x_counts[x_bin]

            if p_y_given_x > 0:
                conditional_entropy -= p_xy * np.log2(p_y_given_x)

        return conditional_entropy

    def _calculate_joint_entropy(self, gray: np.ndarray) -> Dict[str, float]:
        """Calculate joint entropy with spatially shifted versions."""
        h, w = gray.shape

        # Calculate joint entropy with horizontally shifted version
        if w > 1:
            img1 = gray[:, :-1]
            img2 = gray[:, 1:]
            joint_hist_h, _, _ = np.histogram2d(
                img1.flatten(), img2.flatten(),
                bins=32, range=[[0, 256], [0, 256]], density=True
            )
            joint_entropy_h = self._entropy_from_histogram(joint_hist_h.flatten())
        else:
            joint_entropy_h = 0.0

        # Calculate joint entropy with vertically shifted version
        if h > 1:
            img1 = gray[:-1, :]
            img2 = gray[1:, :]
            joint_hist_v, _, _ = np.histogram2d(
                img1.flatten(), img2.flatten(),
                bins=32, range=[[0, 256], [0, 256]], density=True
            )
            joint_entropy_v = self._entropy_from_histogram(joint_hist_v.flatten())
        else:
            joint_entropy_v = 0.0

        return {
            'joint_entropy_horizontal': float(joint_entropy_h),
            'joint_entropy_vertical': float(joint_entropy_v)
        }

    def _calculate_information_measures(self, gray: np.ndarray) -> Dict[str, float]:
        """Calculate various information-theoretic measures."""
        # Global entropy
        global_entropy = self._calculate_global_entropy(gray)['shannon_entropy']

        # Calculate entropy after different transformations
        # Gradient entropy
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)
        gradient_mag_int = np.clip(gradient_mag, 0, 255).astype(np.uint8)
        gradient_entropy = self._calculate_global_entropy(gradient_mag_int)['shannon_entropy']

        # Laplacian entropy (second derivative)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_int = np.clip(np.abs(laplacian), 0, 255).astype(np.uint8)
        laplacian_entropy = self._calculate_global_entropy(laplacian_int)['shannon_entropy']

        # Information gain from derivatives
        gradient_info_gain = gradient_entropy - global_entropy
        laplacian_info_gain = laplacian_entropy - global_entropy

        return {
            'gradient_entropy': float(gradient_entropy),
            'laplacian_entropy': float(laplacian_entropy),
            'gradient_info_gain': float(gradient_info_gain),
            'laplacian_info_gain': float(laplacian_info_gain)
        }

    def _calculate_entropy_distribution(self, gray: np.ndarray) -> Dict[str, float]:
        """Analyze entropy distribution across image regions."""
        h, w = gray.shape

        # Divide image into 4x4 grid
        grid_size = 4
        region_h, region_w = h // grid_size, w // grid_size

        region_entropies = []

        for i in range(grid_size):
            for j in range(grid_size):
                y1, y2 = i * region_h, min((i + 1) * region_h, h)
                x1, x2 = j * region_w, min((j + 1) * region_w, w)

                region = gray[y1:y2, x1:x2]
                if region.size > 0:
                    region_entropy = self._calculate_global_entropy(region)['shannon_entropy']
                    region_entropies.append(region_entropy)

        if not region_entropies:
            return {
                'entropy_uniformity': 0.0,
                'entropy_variation': 0.0,
                'min_region_entropy': 0.0,
                'max_region_entropy': 0.0
            }

        region_entropies = np.array(region_entropies)

        entropy_mean = np.mean(region_entropies)
        entropy_std = np.std(region_entropies)

        # Entropy uniformity (inverse of coefficient of variation)
        entropy_uniformity = float(1.0 / (1.0 + entropy_std / (entropy_mean + 1e-6)))

        return {
            'entropy_uniformity': entropy_uniformity,
            'entropy_variation': float(entropy_std),
            'min_region_entropy': float(np.min(region_entropies)),
            'max_region_entropy': float(np.max(region_entropies))
        }

    def _calculate_joint_histogram(self, pairs: list) -> np.ndarray:
        """Calculate joint histogram from pairs."""
        if not pairs:
            return np.array([])

        x_vals, y_vals = zip(*pairs)
        hist, _, _ = np.histogram2d(x_vals, y_vals, bins=32, range=[[0, 256], [0, 256]], density=True)
        return hist.flatten()

    def _entropy_from_histogram(self, hist: np.ndarray) -> float:
        """Calculate entropy from histogram."""
        hist = hist[hist > 0]
        if len(hist) == 0:
            return 0.0
        return float(-np.sum(hist * np.log2(hist)))

    def calculate_entropy_quality_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate overall entropy quality score.

        Args:
            metrics: Entropy metrics from analyze()

        Returns:
            Quality score between 0.0 and 1.0
        """
        try:
            # Extract key metrics
            shannon_entropy = metrics.get('shannon_entropy', 0.0)
            local_entropy_mean = metrics.get('local_entropy_mean', 0.0)
            texture_complexity = metrics.get('texture_complexity', 0.0)
            mutual_info_h = metrics.get('mutual_information_h', 0.0)
            entropy_uniformity = metrics.get('entropy_uniformity', 0.0)

            # Score main_components
            # Shannon entropy scoring (optimal: 3-6 bits)
            if 3.0 <= shannon_entropy <= 6.0:
                shannon_score = 1.0
            elif 2.0 <= shannon_entropy <= 7.0:
                shannon_score = 0.8
            elif 1.0 <= shannon_entropy <= 8.0:
                shannon_score = 0.6
            else:
                shannon_score = 0.3

            # Local entropy scoring
            local_score = min(1.0, local_entropy_mean / 4.0)

            # Texture complexity scoring
            texture_score = min(1.0, texture_complexity * 2.0)

            # Mutual information scoring (some correlation is good)
            if 0.1 <= mutual_info_h <= 1.0:
                mutual_score = 1.0
            elif mutual_info_h < 0.1:
                mutual_score = mutual_info_h * 10  # Linear increase
            else:
                mutual_score = max(0.3, 1.0 / mutual_info_h)  # Decrease for too much correlation

            # Uniformity scoring
            uniformity_score = entropy_uniformity

            # Weighted combination
            quality_score = (
                    shannon_score * 0.3 +
                    local_score * 0.25 +
                    texture_score * 0.2 +
                    mutual_score * 0.15 +
                    uniformity_score * 0.1
            )

            return max(0.0, min(1.0, quality_score))

        except Exception as e:
            logger.warning(f"Error calculating entropy quality score: {e}")
            return 0.0

    def get_entropy_recommendations(self, metrics: Dict[str, Any]) -> list:
        """Generate recommendations based on entropy analysis."""
        recommendations = []

        shannon_entropy = metrics.get('shannon_entropy', 0.0)
        texture_complexity = metrics.get('texture_complexity', 0.0)
        entropy_uniformity = metrics.get('entropy_uniformity', 0.0)

        # Shannon entropy recommendations
        if shannon_entropy < 2.0:
            recommendations.append(" Very low information content")
            recommendations.append("Pattern lacks sufficient detail for reliable correlation")
        elif shannon_entropy < 3.0:
            recommendations.append(" Low information content")
            recommendations.append("Consider more complex speckle pattern")
        elif shannon_entropy > 7.0:
            recommendations.append(" Very high information content")
            recommendations.append("May indicate noise or excessive detail")

        # Texture complexity recommendations
        if texture_complexity < 0.3:
            recommendations.append(" Low texture complexity")
            recommendations.append("Pattern may be too regular for optimal correlation")
        elif texture_complexity > 0.8:
            recommendations.append(" Very high texture complexity")
            recommendations.append("May indicate noise or overly random pattern")

        # Entropy uniformity recommendations
        if entropy_uniformity < 0.6:
            recommendations.append(" Uneven information distribution")
            recommendations.append("Some regions have much less detail than others")

        # Overall assessment
        quality_score = self.calculate_entropy_quality_score(metrics)
        if quality_score > 0.8:
            recommendations.append(" Excellent information content for DIC")
        elif quality_score > 0.6:
            recommendations.append(" Good information content for DIC")
        elif quality_score > 0.4:
            recommendations.append(" Acceptable information content")
        else:
            recommendations.append(" Poor information content for DIC")

        return recommendations

    def analyze_information_capacity(self, image: np.ndarray, subset_size: int = 21) -> Dict[str, float]:
        """
        Analyze information capacity for DIC correlation windows.

        Args:
            image: Input image
            subset_size: DIC subset size for analysis

        Returns:
            Dictionary with information capacity metrics
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape

        if h < subset_size or w < subset_size:
            return {
                'subset_entropy_mean': 0.0,
                'subset_entropy_std': 0.0,
                'subset_uniqueness': 0.0,
                'correlation_capacity': 0.0
            }

        # Analyze entropy in subset-sized windows
        subset_entropies = []
        step = max(1, subset_size // 2)

        for y in range(0, h - subset_size + 1, step):
            for x in range(0, w - subset_size + 1, step):
                subset = gray[y:y + subset_size, x:x + subset_size]
                subset_entropy = self._calculate_global_entropy(subset)['shannon_entropy']
                subset_entropies.append(subset_entropy)

        if not subset_entropies:
            return {
                'subset_entropy_mean': 0.0,
                'subset_entropy_std': 0.0,
                'subset_uniqueness': 0.0,
                'correlation_capacity': 0.0
            }

        subset_entropies = np.array(subset_entropies)

        # Calculate metrics
        entropy_mean = float(np.mean(subset_entropies))
        entropy_std = float(np.std(subset_entropies))

        # Subset uniqueness (how different subsets are from each other)
        entropy_range = np.max(subset_entropies) - np.min(subset_entropies)
        subset_uniqueness = float(entropy_range / (entropy_mean + 1e-6))

        # Correlation capacity (theoretical number of distinguishable subsets)
        # Based on information theory: 2^entropy possible states
        avg_states_per_subset = 2 ** entropy_mean
        correlation_capacity = float(np.log2(len(subset_entropies) * avg_states_per_subset + 1))

        return {
            'subset_entropy_mean': entropy_mean,
            'subset_entropy_std': entropy_std,
            'subset_uniqueness': subset_uniqueness,
            'correlation_capacity': correlation_capacity
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            'shannon_entropy': 0.0,
            'normalized_entropy': 0.0,
            'effective_levels': 0.0,
            'local_entropy_mean': 0.0,
            'local_entropy_std': 0.0,
            'local_entropy_max': 0.0,
            'local_entropy_min': 0.0,
            'texture_entropy': 0.0,
            'texture_uniformity': 0.0,
            'texture_complexity': 0.0,
            'conditional_entropy_h': 0.0,
            'conditional_entropy_v': 0.0,
            'mutual_information_h': 0.0,
            'mutual_information_v': 0.0,
            'joint_entropy_horizontal': 0.0,
            'joint_entropy_vertical': 0.0,
            'gradient_entropy': 0.0,
            'laplacian_entropy': 0.0,
            'gradient_info_gain': 0.0,
            'laplacian_info_gain': 0.0,
            'entropy_uniformity': 0.0,
            'entropy_variation': 0.0,
            'min_region_entropy': 0.0,
            'max_region_entropy': 0.0
        }