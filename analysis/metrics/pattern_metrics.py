import cv2
import numpy as np
from scipy import ndimage
from scipy.fftpack import fft2, fftshift
from scipy.stats import entropy


def analyze_pattern_isotropy(binary_image):
    """Calculates pattern isotropy (directional bias)

    Args:
        binary_image: Binary image with speckles

    Returns:
        dict: Isotropy metrics
    """
    # Get morphological gradient
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.morphologyEx(binary_image, cv2.MORPH_GRADIENT, kernel)

    # Calculate Hough transform to detect lines
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=15,
                            minLineLength=10, maxLineGap=5)

    # Count lines in different orientations
    angles = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:  # Avoid division by zero
                angle = np.degrees(np.arctan((y2 - y1) / (x2 - x1))) % 180
                angles.append(angle)

    # Calculate angle distribution statistics
    angle_std = np.std(angles) if angles else 0
    angle_hist = np.histogram(angles, bins=18, range=(0, 180))[0] if angles else np.zeros(18)

    # Calculate entropy of angle distribution (higher is more isotropic)
    angle_entropy = entropy(angle_hist + 1e-10)  # Add small value to avoid log(0)

    # Normalize metrics
    max_possible_entropy = np.log2(18)  # Maximum entropy for 18 bins
    isotropy_score = min(100, 100 * angle_entropy / max_possible_entropy) if max_possible_entropy > 0 else 0

    return {
        'isotropy_score': isotropy_score,
        'angle_std': angle_std,
        'directional_bias': max(0, 100 - isotropy_score)
    }


def analyze_pattern_frequency(gray_image):
    """Analyzes pattern frequency distribution and characteristics

    Args:
        gray_image: Grayscale image containing pattern

    Returns:
        dict: Frequency domain characteristics
    """
    # Apply FFT
    f_transform = fft2(gray_image.astype(float))
    f_shift = fftshift(f_transform)
    magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1)

    # Normalize to 0-255
    magnitude_norm = cv2.normalize(magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Create circular masks for different frequency bands
    rows, cols = gray_image.shape
    center_row, center_col = rows // 2, cols // 2

    radius_low = min(rows, cols) // 16  # Low frequencies
    radius_mid = min(rows, cols) // 8  # Mid frequencies
    radius_high = min(rows, cols) // 4  # High frequencies

    y_grid, x_grid = np.ogrid[:rows, :cols]
    dist_from_center = np.sqrt((y_grid - center_row) ** 2 + (x_grid - center_col) ** 2)

    # Create masks for each frequency band
    low_mask = dist_from_center <= radius_low
    mid_mask = (dist_from_center > radius_low) & (dist_from_center <= radius_mid)
    high_mask = (dist_from_center > radius_mid) & (dist_from_center <= radius_high)

    # Calculate energy in each frequency band
    low_energy = np.sum(magnitude_norm * low_mask) / (np.sum(low_mask) + 1e-10)
    mid_energy = np.sum(magnitude_norm * mid_mask) / (np.sum(mid_mask) + 1e-10)
    high_energy = np.sum(magnitude_norm * high_mask) / (np.sum(high_mask) + 1e-10)

    total_energy = low_energy + mid_energy + high_energy

    # Calculate frequency distribution percentages
    low_percent = 100 * low_energy / total_energy if total_energy > 0 else 0
    mid_percent = 100 * mid_energy / total_energy if total_energy > 0 else 0
    high_percent = 100 * high_energy / total_energy if total_energy > 0 else 0

    # Frequency balance score - ideal pattern has good mid-frequency content
    freq_balance = min(100, 100 * mid_percent / 50) if mid_percent < 50 else min(100, 100 * (100 - mid_percent) / 50)

    return {
        'frequency_balance': freq_balance,
        'low_frequency_percent': low_percent,
        'mid_frequency_percent': mid_percent,
        'high_frequency_percent': high_percent,
        'frequency_spectrum': magnitude_norm
    }


def analyze_pattern_randomness(binary_image):
    """Analyzes the randomness/repeatability of the pattern

    Args:
        binary_image: Binary image with speckles

    Returns:
        dict: Pattern randomness metrics
    """
    # Calculate auto-correlation
    autocorr = ndimage.correlate(binary_image.astype(float), binary_image.astype(float), mode='constant')

    # Normalize autocorrelation
    autocorr = autocorr / np.max(autocorr)

    # Get the center value and remove it (it's always 1.0)
    center_y, center_x = binary_image.shape[0] // 2, binary_image.shape[1] // 2
    center_val = autocorr[center_y, center_x]
    autocorr[center_y, center_x] = 0

    # Find the maximum correlation peak (excluding center)
    max_corr = np.max(autocorr)

    # Calculate randomness score (lower correlation = more random)
    randomness_score = 100 * (1 - max_corr)

    # Calculate pattern periodicity
    y_indices, x_indices = np.nonzero(autocorr > 0.5)  # Points with high correlation

    # If we have correlation peaks, find the minimum distance to center
    if len(y_indices) > 0:
        distances = np.sqrt((y_indices - center_y) ** 2 + (x_indices - center_x) ** 2)
        min_period = np.min(distances) if distances.size > 0 else 0
    else:
        min_period = 0

    return {
        'randomness_score': randomness_score,
        'max_correlation': max_corr * 100,  # As percentage
        'min_pattern_period': min_period,
        'autocorrelation': autocorr
    }


def evaluate_pattern_quality(gray_image):
    """Comprehensive evaluation of pattern quality for DIC

    Args:
        gray_image: Grayscale image to analyze

    Returns:
        dict: Pattern quality metrics
    """
    # Create binary image using adaptive thresholding
    binary = cv2.adaptiveThreshold(
        gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Analyze different pattern aspects
    isotropy = analyze_pattern_isotropy(binary)
    frequency = analyze_pattern_frequency(gray_image)
    randomness = analyze_pattern_randomness(binary)

    # Calculate overall pattern quality score
    # Weightings based on importance for DIC analysis
    quality_score = (
            isotropy['isotropy_score'] * 0.3 +
            frequency['frequency_balance'] * 0.4 +
            randomness['randomness_score'] * 0.3
    )

    return {
        'quality_score': quality_score,
        'isotropy_metrics': isotropy,
        'frequency_metrics': frequency,
        'randomness_metrics': randomness,
        'binary_image': binary
    }