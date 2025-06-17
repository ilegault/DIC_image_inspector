# analysis/metrics/subset_metrics.py

import cv2
import numpy as np
from scipy.stats import entropy
from scipy.signal import correlate2d
import matplotlib.pyplot as plt


class SubsetMetrics:
    """Calculate and evaluate metrics for DIC image subsets"""

    def __init__(self):
        # Default parameters
        self.sobel_ksize = 3
        self.hist_bins = 256
        self.target_coverage = 0.5  # Ideal speckle coverage ratio (50%)

    def calculate_all_metrics(self, subset):
        """Calculate all subset metrics at once

        Args:
            subset: Numpy array of the subset (grayscale or RGB)

        Returns:
            dict: Dictionary of all metrics
        """
        # Convert to grayscale if needed
        if len(subset.shape) == 3:
            gray = cv2.cvtColor(subset, cv2.COLOR_RGB2GRAY)
        else:
            gray = subset.copy()

        # Calculate individual metrics
        gradient_metrics = self.calculate_gradient_metrics(gray)
        intensity_metrics = self.calculate_intensity_metrics(gray)
        texture_metrics = self.calculate_texture_metrics(gray)
        pattern_metrics = self.calculate_pattern_metrics(gray)
        noise_metrics = self.calculate_noise_metrics(gray)

        # Combine all metrics
        all_metrics = {
            **gradient_metrics,
            **intensity_metrics,
            **texture_metrics,
            **pattern_metrics,
            **noise_metrics,
            'quality_score': self.calculate_quality_score(gray)
        }

        return all_metrics

    def calculate_gradient_metrics(self, gray_subset):
        """Calculate gradient-based metrics

        Args:
            gray_subset: Grayscale subset image

        Returns:
            dict: Gradient metrics
        """
        # Calculate x and y gradients
        grad_x = cv2.Sobel(gray_subset, cv2.CV_64F, 1, 0, ksize=self.sobel_ksize)
        grad_y = cv2.Sobel(gray_subset, cv2.CV_64F, 0, 1, ksize=self.sobel_ksize)

        # Calculate gradient magnitude and direction
        magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
        direction = np.arctan2(grad_y, grad_x)

        # Calculate statistical measures
        mean_magnitude = np.mean(magnitude)
        std_magnitude = np.std(magnitude)
        max_magnitude = np.max(magnitude)

        # Calculate Sum of Square of Gradients (SSG) - important for DIC sensitivity
        ssg = np.sum(magnitude ** 2)

        # Calculate gradient isotropy (how evenly distributed are the gradients)
        hist, _ = np.histogram(direction, bins=8, range=(-np.pi, np.pi))
        hist = hist / np.sum(hist) if np.sum(hist) > 0 else hist
        gradient_isotropy = 1 - np.std(hist) / np.mean(hist) if np.mean(hist) > 0 else 0

        return {
            'mean_gradient': mean_magnitude,
            'std_gradient': std_magnitude,
            'max_gradient': max_magnitude,
            'sum_squared_gradient': ssg,
            'gradient_isotropy': gradient_isotropy
        }

    def calculate_intensity_metrics(self, gray_subset):
        """Calculate intensity-based metrics

        Args:
            gray_subset: Grayscale subset image

        Returns:
            dict: Intensity metrics
        """
        # Basic statistics
        mean_intensity = np.mean(gray_subset)
        std_intensity = np.std(gray_subset)
        min_intensity = np.min(gray_subset)
        max_intensity = np.max(gray_subset)

        # Calculate contrast
        contrast = std_intensity / mean_intensity if mean_intensity > 0 else 0

        # Calculate entropy (measures information content)
        hist, _ = np.histogram(gray_subset, bins=self.hist_bins, range=(0, 256), density=True)
        subset_entropy = entropy(hist[hist > 0]) if np.any(hist > 0) else 0

        # Calculate intensity distribution uniformity
        cumulative_hist = np.cumsum(hist)
        median_level = np.argmin(np.abs(cumulative_hist - 0.5)) / 255
        intensity_uniformity = 1 - 2 * abs(median_level - 0.5)

        return {
            'mean_intensity': mean_intensity,
            'std_intensity': std_intensity,
            'contrast': contrast,
            'entropy': subset_entropy,
            'intensity_range': max_intensity - min_intensity,
            'intensity_uniformity': intensity_uniformity
        }

    def calculate_texture_metrics(self, gray_subset):
        """Calculate texture-based metrics

        Args:
            gray_subset: Grayscale subset image

        Returns:
            dict: Texture metrics
        """
        # Create GLCM (Gray-Level Co-occurrence Matrix)
        # Using OpenCV or NumPy as scikit-image might not be available

        # Simple texture descriptors using auto-correlation
        kernel = np.ones((3, 3)) / 9  # Simple smoothing kernel
        smoothed = cv2.filter2D(gray_subset.astype(float), -1, kernel)
        texture_strength = np.mean(np.abs(gray_subset - smoothed))

        # Calculate local binary pattern-like feature for texture complexity
        h, w = gray_subset.shape
        if h < 3 or w < 3:  # Too small for meaningful texture analysis
            return {
                'texture_strength': 0,
                'texture_complexity': 0,
                'texture_scale': 0
            }

        # Simplified local binary pattern analysis
        center = gray_subset[1:-1, 1:-1]
        n0 = gray_subset[:-2, :-2] > center  # northwest
        n1 = gray_subset[:-2, 1:-1] > center  # north
        n2 = gray_subset[:-2, 2:] > center  # northeast
        n3 = gray_subset[1:-1, :-2] > center  # west
        n4 = gray_subset[1:-1, 2:] > center  # east
        n5 = gray_subset[2:, :-2] > center  # southwest
        n6 = gray_subset[2:, 1:-1] > center  # south
        n7 = gray_subset[2:, 2:] > center  # southeast

        # Count transitions (changes from 0 to 1 or 1 to 0) as measure of complexity
        binary_pattern = np.dstack([n0, n1, n2, n3, n4, n5, n6, n7]).astype(int)
        transitions = np.sum(np.abs(np.diff(np.append(binary_pattern, binary_pattern[:, :, :1], axis=2), axis=2)))
        texture_complexity = transitions / ((h - 2) * (w - 2) * 8) if (h - 2) * (w - 2) > 0 else 0

        # Estimate feature scale using autocorrelation
        if h > 5 and w > 5:  # Need sufficient size for autocorrelation
            # Subtract mean to reduce DC component
            normalized = gray_subset.astype(float) - np.mean(gray_subset)
            # Calculate autocorrelation
            autocorr = correlate2d(normalized, normalized, mode='same')
            # Find peak distance from center
            center_y, center_x = autocorr.shape[0] // 2, autocorr.shape[1] // 2
            autocorr[center_y - 1:center_y + 2, center_x - 1:center_x + 2] = 0  # Zero out center peak
            max_idx = np.argmax(autocorr)
            max_y, max_x = max_idx // autocorr.shape[1], max_idx % autocorr.shape[1]
            texture_scale = np.sqrt((max_y - center_y) ** 2 + (max_x - center_x) ** 2)
        else:
            texture_scale = 0

        return {
            'texture_strength': texture_strength,
            'texture_complexity': texture_complexity,
            'texture_scale': texture_scale
        }

    def calculate_pattern_metrics(self, gray_subset):
        """Calculate speckle pattern metrics

        Args:
            gray_subset: Grayscale subset image

        Returns:
            dict: Pattern metrics
        """
        # Apply adaptive thresholding for robust feature detection
        if gray_subset.shape[0] > 10 and gray_subset.shape[1] > 10:
            # For larger subsets, use adaptive thresholding
            binary = cv2.adaptiveThreshold(
                gray_subset, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
        else:
            # For small subsets, use Otsu thresholding
            _, binary = cv2.threshold(gray_subset, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Calculate speckle coverage
        coverage_ratio = np.sum(binary > 0) / binary.size
        coverage_score = 1.0 - 2.0 * abs(coverage_ratio - self.target_coverage)

        # Calculate feature count and average size
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary, connectivity=8
        )

        # Skip background
        if num_labels > 1:
            areas = stats[1:, cv2.CC_STAT_AREA]  # Skip background (index 0)
            valid_areas = areas[(areas > 1) & (areas < binary.size // 4)]

            if len(valid_areas) > 0:
                mean_feature_size = np.mean(valid_areas)
                median_feature_size = np.median(valid_areas)
                feature_density = len(valid_areas) / binary.size * 1000  # Features per 1000 pixels
            else:
                mean_feature_size = 0
                median_feature_size = 0
                feature_density = 0
        else:
            mean_feature_size = 0
            median_feature_size = 0
            feature_density = 0

        return {
            'speckle_coverage': coverage_ratio,
            'coverage_score': coverage_score,
            'feature_density': feature_density,
            'mean_feature_size': mean_feature_size,
            'median_feature_size': median_feature_size,
            'feature_count': num_labels - 1  # Subtract background
        }

    def calculate_noise_metrics(self, gray_subset):
        """Calculate noise-related metrics

        Args:
            gray_subset: Grayscale subset image

        Returns:
            dict: Noise metrics
        """
        # Estimate noise using median filtering
        if gray_subset.shape[0] > 3 and gray_subset.shape[1] > 3:
            median_filtered = cv2.medianBlur(gray_subset, 3)
            noise = gray_subset.astype(float) - median_filtered
            noise_std = np.std(noise)
            signal_std = np.std(median_filtered)
            snr = signal_std / noise_std if noise_std > 0 else float('inf')
        else:
            # Subset too small for noise estimation
            noise_std = 0
            snr = float('inf')

        return {
            'noise_std': noise_std,
            'snr': snr
        }

    def calculate_quality_score(self, gray_subset):
        """Calculate overall quality score for DIC subset

        Args:
            gray_subset: Grayscale subset image

        Returns:
            float: Quality score (0-1)
        """
        # Calculate key metrics
        gradient_metrics = self.calculate_gradient_metrics(gray_subset)
        intensity_metrics = self.calculate_intensity_metrics(gray_subset)
        pattern_metrics = self.calculate_pattern_metrics(gray_subset)
        texture_metrics = self.calculate_texture_metrics(gray_subset)
        noise_metrics = self.calculate_noise_metrics(gray_subset)

        # Normalize metrics to 0-1 range for scoring
        norm_gradient = min(1.0, gradient_metrics['mean_gradient'] / 30.0)
        norm_contrast = min(1.0, intensity_metrics['contrast'] / 0.5)
        norm_entropy = min(1.0, intensity_metrics['entropy'] / 5.0)
        norm_coverage = pattern_metrics['coverage_score']
        norm_snr = min(1.0, noise_metrics['snr'] / 20.0) if noise_metrics['snr'] != float('inf') else 1.0
        norm_texture = min(1.0, texture_metrics['texture_complexity'] * 5)

        # DIC Quality score with weighted components
        quality_score = (
                norm_gradient * 0.25 +  # Strong gradients are important for DIC
                norm_contrast * 0.20 +  # Good contrast is needed
                norm_entropy * 0.15 +  # Entropy ensures information richness
                norm_coverage * 0.15 +  # Proper coverage is key
                norm_snr * 0.15 +  # Low noise is preferable
                norm_texture * 0.10  # Complex texture helps matching
        )

        return max(0.0, min(1.0, quality_score))

    def map_subset_quality(self, image, subset_size=21, step=10):
        """Create a quality map by analyzing subsets across the image

        Args:
            image: Input image (grayscale or color)
            subset_size: Size of each subset
            step: Step size between subsets

        Returns:
            Tuple: (quality_map, quality_metrics)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.float32)

        # Store metrics for each subset position
        metrics_map = {}

        # Process each subset
        for y in range(0, h - subset_size + 1, step):
            for x in range(0, w - subset_size + 1, step):
                # Extract subset
                subset = gray[y:y + subset_size, x:x + subset_size]

                # Calculate quality score
                quality = self.calculate_quality_score(subset)

                # Optional: Get detailed metrics
                metrics = self.calculate_all_metrics(subset)
                metrics_map[(x, y)] = metrics

                # Map quality back to original image position
                quality_map[y:y + subset_size, x:x + subset_size] += quality
                count_map[y:y + subset_size, x:x + subset_size] += 1.0

        # Average overlapping regions
        mask = count_map > 0
        quality_map[mask] /= count_map[mask]

        return quality_map, metrics_map

    def compare_subsets(self, subset1, subset2):
        """Compare two subsets and calculate similarity metrics

        Args:
            subset1: First subset (numpy array)
            subset2: Second subset (numpy array)

        Returns:
            dict: Similarity metrics
        """
        # Ensure grayscale
        if len(subset1.shape) == 3:
            gray1 = cv2.cvtColor(subset1, cv2.COLOR_RGB2GRAY)
        else:
            gray1 = subset1.copy()

        if len(subset2.shape) == 3:
            gray2 = cv2.cvtColor(subset2, cv2.COLOR_RGB2GRAY)
        else:
            gray2 = subset2.copy()

        # Ensure same size for comparison
        min_h = min(gray1.shape[0], gray2.shape[0])
        min_w = min(gray1.shape[1], gray2.shape[1])
        gray1 = gray1[:min_h, :min_w]
        gray2 = gray2[:min_h, :min_w]

        # Calculate metrics
        mse = np.mean((gray1.astype(float) - gray2.astype(float)) ** 2)
        if mse == 0:
            psnr = float('inf')
        else:
            psnr = 10 * np.log10((255 ** 2) / mse)

        # Calculate structural similarity (simplified)
        mu1 = np.mean(gray1)
        mu2 = np.mean(gray2)
        sigma1 = np.std(gray1)
        sigma2 = np.std(gray2)
        sigma12 = np.mean((gray1 - mu1) * (gray2 - mu2))

        k1, k2, L = 0.01, 0.03, 255
        c1 = (k1 * L) ** 2
        c2 = (k2 * L) ** 2

        ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / \
               ((mu1 ** 2 + mu2 ** 2 + c1) * (sigma1 ** 2 + sigma2 ** 2 + c2))

        # Calculate normalized cross-correlation
        norm1 = gray1.astype(float) - np.mean(gray1)
        norm2 = gray2.astype(float) - np.mean(gray2)

        if np.sum(norm1 ** 2) == 0 or np.sum(norm2 ** 2) == 0:
            ncc = 0
        else:
            ncc = np.sum(norm1 * norm2) / np.sqrt(np.sum(norm1 ** 2) * np.sum(norm2 ** 2))

        return {
            'mse': mse,
            'psnr': psnr,
            'ssim': ssim,
            'ncc': ncc,
            'uniqueness': 1.0 - abs(ncc)  # Higher means more unique
        }


def visualize_subset_quality(image, quality_map, subset_size=21, colormap='jet'):
    """Visualize subset quality map with color overlay

    Args:
        image: Original image
        quality_map: Quality map from map_subset_quality
        subset_size: Size of subsets used (for visualization)
        colormap: Matplotlib colormap name

    Returns:
        numpy array: Visualization image
    """
    # Create colormap visualization
    cmap = plt.get_cmap(colormap)
    quality_map_normalized = (quality_map - np.min(quality_map)) / (np.max(quality_map) - np.min(quality_map) + 1e-8)
    colored_map = cmap(quality_map_normalized)
    colored_map = (colored_map[:, :, :3] * 255).astype(np.uint8)

    # Convert original image to RGB if grayscale
    if len(image.shape) == 2:
        vis_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    else:
        vis_image = image.copy()

    # Create alpha overlay
    alpha = 0.7
    overlay = cv2.addWeighted(vis_image, 1 - alpha, colored_map, alpha, 0)

    # Draw grid lines for subsets
    h, w = image.shape[:2]
    for y in range(0, h, subset_size):
        cv2.line(overlay, (0, y), (w, y), (0, 0, 0), 1)
    for x in range(0, w, subset_size):
        cv2.line(overlay, (x, 0), (x, h), (0, 0, 0), 1)

    return overlay


def get_best_subsets(image, subset_size=21, step=10, num_best=5):
    """Find the best subsets in an image for DIC analysis

    Args:
        image: Input image
        subset_size: Size of subsets to analyze
        step: Step size between subsets
        num_best: Number of best subsets to return

    Returns:
        list: List of (x, y, score) tuples for best subsets
    """
    metrics = SubsetMetrics()
    quality_map, metrics_map = metrics.map_subset_quality(image, subset_size, step)

    # Find best subset positions
    best_subsets = []
    for pos, data in metrics_map.items():
        x, y = pos
        score = data['quality_score']
        best_subsets.append((x, y, score))

    # Sort by score (descending)
    best_subsets.sort(key=lambda x: x[2], reverse=True)

    return best_subsets[:num_best]