# analysis/metrics/contract_metrics.py

import cv2
import numpy as np


def calculate_contrast(gray):
    """Calculate contrast score for DIC quality analysis"""
    # Calculate multiple contrast metrics and combine them

    # Method 1: Simple contrast ratio (max-min)/max
    min_val = np.min(gray)
    max_val = np.max(gray)
    if max_val == min_val:
        simple_contrast = 0
    else:
        simple_contrast = (max_val - min_val) / max_val * 100

    # Method 2: RMS contrast
    mean_intensity = np.mean(gray)
    rms_contrast = np.sqrt(np.mean((gray - mean_intensity) ** 2)) / mean_intensity * 100 if mean_intensity > 0 else 0

    # Method 3: Local contrast using standard deviation within windows
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
    window_size = min(32, min(h, w) // 4)
    if window_size < 8:
        window_size = 8

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

    if local_contrasts:
        return np.mean(local_contrasts)
    return 0


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
    entropy = -np.sum(hist[hist > 0] * np.log2(hist[hist > 0]))

    # Maximum entropy for 256 bins is 8 bits (uniform distribution)
    normalized_entropy = min(100, (entropy / 8) * 100)

    # Check for bimodal distribution which is often good for DIC
    bimodality = measure_bimodality(hist)

    # Check for coverage of intensity range
    coverage = measure_intensity_coverage(hist)

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


def measure_intensity_coverage(hist):
    """Measure how well the histogram covers the intensity range"""
    # Calculate percentiles
    cumsum = np.cumsum(hist)
    p1 = np.searchsorted(cumsum, 0.01)
    p99 = np.searchsorted(cumsum, 0.99)

    # Effective range coverage (as percentage of full range)
    coverage = (p99 - p1) / 255

    # Check for overexposure or underexposure
    over_exposed = np.sum(hist[-5:]) > 0.1  # More than 10% in top 5 bins
    under_exposed = np.sum(hist[:5]) > 0.1  # More than 10% in bottom 5 bins

    # Penalize if overexposed or underexposed
    if over_exposed or under_exposed:
        coverage *= 0.7

    return coverage * 100