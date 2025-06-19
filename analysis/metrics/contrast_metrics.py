# analysis/metrics/contrast_metrics.py

import cv2
import numpy as np
from scipy.stats import entropy

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

    # Method 4: Histogram spread analysis
    hist_contrast = analyze_histogram_contrast(gray)

    # Combine metrics with weights
    contrast_score = (
        simple_contrast * 0.2 +
        rms_contrast * 0.3 +
        local_contrast * 0.3 +
        hist_contrast * 0.2
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


def analyze_histogram_contrast(gray):
    """Analyze image contrast based on histogram distribution"""
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.flatten() / hist.sum()  # Normalize

    # Calculate histogram spread (percentile difference)
    cumsum = np.cumsum(hist)
    p5 = np.searchsorted(cumsum, 0.05)
    p95 = np.searchsorted(cumsum, 0.95)

    # Spread as percentage of full range
    hist_spread = (p95 - p5) / 255 * 100

    return hist_spread


def analyze_intensity_distribution(gray):
    """Analyze the quality of intensity distribution for DIC"""
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    hist = hist / np.sum(hist)  # Normalize

    # Calculate entropy of distribution
    raw_entropy = -np.sum(hist[hist > 0] * np.log2(hist[hist > 0]))

    # Maximum entropy for 256 bins is 8 bits (uniform distribution)
    normalized_entropy = min(100, (raw_entropy / 8) * 100)

    # Check for bimodal distribution which is often good for DIC
    bimodality = measure_bimodality(hist)

    # Check for coverage of intensity range - extract the appropriate value from the dictionary
    contrast_metrics = measure_intensity_contrast(gray)
    coverage = contrast_metrics['dynamic_range']  # Use dynamic_range as the coverage metric

    # Combined score
    distribution_score = (
            normalized_entropy * 0.4 +
            bimodality * 0.3 +
            coverage * 0.3
    )

    return round(distribution_score, 1)


def measure_bimodality(hist):
    """Measure bimodality of histogram (higher is better for DIC)"""
    # Smoothed histogram
    kernel_size = 5
    kernel = np.ones(kernel_size) / kernel_size
    smoothed_hist = np.convolve(hist, kernel, mode='same')

    # Find peaks
    peaks = []
    for i in range(1, len(smoothed_hist) - 1):
        if smoothed_hist[i - 1] < smoothed_hist[i] > smoothed_hist[i + 1]:
            peaks.append((i, smoothed_hist[i]))

    # Sort peaks by height
    peaks.sort(key=lambda x: x[1], reverse=True)

    if len(peaks) >= 2:
        # Get and validate top two peaks
        idx1, val1 = peaks[0]
        idx2, val2 = peaks[1]

        # Check if values are valid
        if val1 <= 0 or val2 <= 0:
            return 0

        # Calculate separation and prominence
        separation = abs(idx2 - idx1) / 255
        prominence = np.min([val1, val2]) / np.max(smoothed_hist)

        # Both separation and prominence matter
        bimodality = separation * 0.5 + prominence * 0.5
        return bimodality * 100

    return 0


def measure_intensity_contrast(gray):
    """Measure contrast metrics for the grayscale image

    Args:
        gray: Grayscale image to analyze

    Returns:
        dict: Contrast metrics
    """
    # Calculate basic statistics
    mean_val = np.mean(gray)
    std_val = np.std(gray)
    min_val = np.min(gray)
    max_val = np.max(gray)

    # Calculate Michelson contrast (enhanced for more meaningful values)
    if max_val != min_val:
        michelson_contrast = (max_val - min_val) / (max_val + min_val)
        # Scale to better utilize the range for typical images
        enhanced_michelson = min(1.0, michelson_contrast * 3)
    else:
        michelson_contrast = 0
        enhanced_michelson = 0

    # Calculate RMS contrast (more consistent for natural images)
    rms_contrast = std_val / 128  # Normalized to typical 8-bit image midpoint

    # True Weber contrast (using brightest vs. average as background)
    weber_contrast = (max_val - mean_val) / mean_val if mean_val > 0 else 0

    # Calculate histogram metrics
    hist, bins = np.histogram(gray, bins=256, range=(0, 256), density=True)
    hist_entropy = entropy(hist[hist > 0]) if np.any(hist > 0) else 0

    # Dynamic range utilization (percentage of all possible 256 gray levels used)
    used_bins = np.sum(hist > 0)
    dynamic_range = (used_bins / 256) * 100

    # Perceptual contrast (combining metrics for better human-aligned score)
    perceptual_contrast = (
        enhanced_michelson * 0.4 +
        min(1.0, rms_contrast * 2) * 0.4 +
        min(1.0, weber_contrast * 0.5) * 0.2
    ) * 100

    return {
        'michelson_contrast': michelson_contrast * 100,  # Original as percentage
        'enhanced_contrast': perceptual_contrast,  # Better scaled for typical images
        'rms_contrast': rms_contrast * 100,  # As percentage
        'weber_contrast': weber_contrast * 100,  # As percentage
        'std_deviation': std_val,
        'dynamic_range': dynamic_range,
        'histogram_entropy': hist_entropy
    }