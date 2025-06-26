# analysis/analyzer.py

import cv2
import numpy as np
from analysis.core.subset_analyzer import determine_optimal_subset_size, analyze_subset_grid


def calculate_contrast(gray):
    """Calculate contrast score for DIC quality analysis"""
    # Method 1: Simple contrast ratio (max-min)/max
    min_val = np.min(gray)
    max_val = np.max(gray)
    if max_val == 0 or max_val == min_val:
        simple_contrast = 0
    else:
        simple_contrast = (max_val - min_val) / max_val * 100

    # Method 2: RMS contrast
    mean_intensity = np.mean(gray)
    epsilon = 1e-6  # Small value to avoid division instability
    rms_contrast = np.sqrt(np.mean((gray - mean_intensity) ** 2)) / (mean_intensity + epsilon) * 100

    # Method 3: Local contrast
    local_contrast = calculate_local_contrast(gray)

    # Combine metrics with weights
    contrast_score = (
            simple_contrast * 0.3 +
            rms_contrast * 0.4 +
            local_contrast * 0.3
    )

    # Normalize to 0-100 range
    contrast_score = min(100, max(0, contrast_score))

    return round(contrast_score, 1)


def calculate_local_contrast(gray):
    """Calculate contrast in local windows across the image"""
    h, w = gray.shape
    window_size = max(8, min(32, min(h, w) // 4))  # Ensure window size is reasonable
    step = window_size // 2
    local_contrasts = []

    for y in range(0, h - window_size, step):
        for x in range(0, w - window_size, step):
            window = gray[y:y + window_size, x:x + window_size]
            if window.size > 0:
                min_val = np.min(window)
                max_val = np.max(window)
                if max_val > min_val:
                    local_contrasts.append((max_val - min_val) / max_val * 100)

    return np.mean(local_contrasts) if local_contrasts else 0


def compute_noise_metrics(gray):
    """Compute noise metrics for an image"""
    # Calculate signal properties
    mean_signal = np.mean(gray)
    signal_std = np.std(gray)

    # Estimate noise using difference between image and smoothed version
    smoothed = cv2.GaussianBlur(gray, (5, 5), 0)
    noise = gray.astype(float) - smoothed.astype(float)
    noise_std = np.std(noise)

    # Calculate SNR (Signal-to-Noise Ratio)
    snr = signal_std / noise_std if noise_std > 0 else float('inf')

    # SNR in decibels (dB) = 20 * log10(signal / noise)
    snr_db = 20 * np.log10(snr) if snr > 0 else 0

    # Normalize SNR for quality score (0-100)
    # Good SNR is typically >20dB, excellent >30dB
    normalized_snr = min(100, max(0, snr_db * 2.5)) if snr_db > 0 else 0

    return {
        'noise_std': noise_std,
        'mean_signal': mean_signal,
        'signal_std': signal_std,
        'snr': snr,
        'snr_db': snr_db,
        'noise_level': normalized_snr  # This is used in the overall score
    }


class DICAnalyzer:
    """Main analyzer for DIC image quality assessment

    Coordinates all the different analysis components and provides a simplified
    interface for the main application.
    """

    def __init__(self):
        """Initialize the analyzer with default parameters"""
        self.subset_size = None
        self.overlap = 0.5

    def analyze(self, image):
        """Analyze an image for DIC quality metrics

        Args:
            image: Numpy array of the image to analyze (ROI or full image)

        Returns:
            dict: Complete analysis results with all metrics
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Determine optimal subset size using your existing sophisticated method
        self.subset_size = determine_optimal_subset_size(gray)
        print(f"Using optimal subset size: {self.subset_size}")

        # Use your existing subset grid analysis
        quality_map, avg_quality = analyze_subset_grid(gray, subset_size=self.subset_size)

        # Calculate basic metrics directly
        metrics = self._calculate_basic_metrics(gray)

        # Add quality data
        metrics['average_quality'] = avg_quality * 100
        metrics['subset_size_used'] = self.subset_size

    def _calculate_basic_metrics(self, gray):
        """Calculate basic metrics using the integrated functions"""

        # Contrast using integrated function
        contrast = calculate_contrast(gray)

        # Noise metrics using integrated function
        noise_metrics = compute_noise_metrics(gray)

        # Gradient analysis
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

        # Speckle analysis using adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)

        if num_labels > 1:
            areas = stats[1:, cv2.CC_STAT_AREA]  # Skip background
            valid_areas = areas[(areas > 4) & (areas < gray.size / 100)]

            if len(valid_areas) > 0:
                avg_feature_size = np.sqrt(np.mean(valid_areas))
                speckle_density = len(valid_areas) / (gray.shape[0] * gray.shape[1]) * 1e6
                # FIX: Convert numpy types to standard Python float before max()
                pattern_uniformity = max(0.0, float(100 * (1 - np.std(valid_areas) / (np.mean(valid_areas) + 1e-6))))
            else:
                avg_feature_size = 0
                speckle_density = 0
                pattern_uniformity = 0
        else:
            avg_feature_size = 0
            speckle_density = 0
            pattern_uniformity = 0

        # Intensity distribution
        hist, _ = np.histogram(gray, bins=256, range=(0, 256))
        hist = hist / np.sum(hist) if np.sum(hist) > 0 else hist
        non_zero = hist[hist > 0]
        intensity_entropy = -np.sum(non_zero * np.log2(non_zero)) if len(non_zero) > 0 else 0

        return {
            'contrast': contrast,
            'gradient_magnitude': np.mean(gradient_magnitude),
            'noise_level': noise_metrics.get('snr_db', 0),
            'speckle_density': speckle_density,
            'feature_size': avg_feature_size,
            'pattern_uniformity': pattern_uniformity,
            'intensity_distribution': min(100, intensity_entropy * 12),
            'edge_quality': min(100, np.mean(gradient_magnitude) / 2)
        }