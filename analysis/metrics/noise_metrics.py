# analysis/metrics/noise_metrics.py

import cv2
import numpy as np
from scipy import ndimage
from skimage.restoration import estimate_sigma


def estimate_image_noise(image):
    """Estimate overall noise level in the image

    Args:
        image: Grayscale image array

    Returns:
        float: Estimated noise standard deviation
    """
    # Wavelet-based noise estimation
    noise_sigma = estimate_sigma(image, average_sigmas=True)

    # Alternative method using difference between image and smoothed version
    smoothed = cv2.GaussianBlur(image, (5, 5), 0)
    noise_diff = image.astype(float) - smoothed.astype(float)
    noise_std = np.std(noise_diff)

    # Combine estimates (weighted)
    combined_noise = (0.7 * noise_sigma + 0.3 * noise_std)

    return combined_noise


def analyze_local_noise(image, block_size=32):
    """Analyze noise characteristics in local image regions

    Args:
        image: Grayscale image array
        block_size: Size of local blocks to analyze

    Returns:
        dict: Local noise characteristics
    """
    h, w = image.shape
    noise_map = np.zeros((h // block_size, w // block_size), dtype=float)
    local_snr_map = np.zeros_like(noise_map)

    for i in range(0, h - block_size, block_size):
        for j in range(0, w - block_size, block_size):
            block = image[i:i + block_size, j:j + block_size]

            # Local noise measurement
            smoothed = cv2.GaussianBlur(block.astype(float), (5, 5), 0)
            noise = block.astype(float) - smoothed
            noise_level = np.std(noise)

            # Local SNR calculation
            signal_level = np.std(smoothed)
            snr = signal_level / (noise_level + 1e-6)  # Avoid division by zero

            # Store measurements
            map_i, map_j = i // block_size, j // block_size
            if map_i < noise_map.shape[0] and map_j < noise_map.shape[1]:
                noise_map[map_i, map_j] = noise_level
                local_snr_map[map_i, map_j] = snr

    # Calculate statistical metrics
    avg_noise = np.mean(noise_map)
    max_noise = np.max(noise_map)
    avg_snr = np.mean(local_snr_map)
    snr_uniformity = 1.0 - np.std(local_snr_map) / (np.mean(local_snr_map) + 1e-6)

    return {
        'avg_noise': avg_noise,
        'max_noise': max_noise,
        'noise_map': noise_map,
        'avg_snr': avg_snr,
        'snr_map': local_snr_map,
        'snr_uniformity': snr_uniformity
    }


def estimate_noise_frequency(image):
    """Estimate noise frequency characteristics using FFT

    Args:
        image: Grayscale image array

    Returns:
        dict: Frequency domain noise characteristics
    """
    # Apply FFT to get frequency domain representation
    f_transform = np.fft.fft2(image.astype(float))
    f_shift = np.fft.fftshift(f_transform)
    magnitude = np.log(np.abs(f_shift) + 1)

    # Get dimensions
    h, w = image.shape
    cy, cx = h // 2, w // 2

    # Create masks for different frequency bands
    y, x = np.ogrid[-cy:h - cy, -cx:w - cx]
    low_radius = min(h, w) // 8
    mid_radius = min(h, w) // 4

    # Define frequency regions
    low_freq_mask = x ** 2 + y ** 2 <= low_radius ** 2
    mid_freq_mask = (x ** 2 + y ** 2 > low_radius ** 2) & (x ** 2 + y ** 2 <= mid_radius ** 2)
    high_freq_mask = x ** 2 + y ** 2 > mid_radius ** 2

    # Calculate energy in each frequency band
    low_freq_energy = np.sum(magnitude[low_freq_mask])
    mid_freq_energy = np.sum(magnitude[mid_freq_mask])
    high_freq_energy = np.sum(magnitude[high_freq_mask])
    total_energy = low_freq_energy + mid_freq_energy + high_freq_energy

    # Calculate percentage of energy in each band
    if total_energy > 0:
        low_freq_percent = (low_freq_energy / total_energy) * 100
        mid_freq_percent = (mid_freq_energy / total_energy) * 100
        high_freq_percent = (high_freq_energy / total_energy) * 100
    else:
        low_freq_percent = mid_freq_percent = high_freq_percent = 0

    # Higher high-frequency content typically indicates more noise
    noise_frequency_score = high_freq_percent

    return {
        'low_freq_percent': low_freq_percent,
        'mid_freq_percent': mid_freq_percent,
        'high_freq_percent': high_freq_percent,
        'noise_frequency_score': noise_frequency_score
    }


def compute_signal_to_noise_ratio(image):
    """Compute signal-to-noise ratio using different methods

    Args:
        image: Grayscale image array

    Returns:
        float: Signal-to-noise ratio in dB
    """
    # Method 1: Using global statistics
    smoothed = cv2.GaussianBlur(image.astype(float), (5, 5), 0)
    noise = image.astype(float) - smoothed

    signal_power = np.var(smoothed)
    noise_power = np.var(noise)

    if noise_power == 0:
        snr_global = 100.0  # High value for very low noise
    else:
        snr_global = 10 * np.log10(signal_power / noise_power)

    # Method 2: Using gradient-based approach
    grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

    threshold = np.mean(gradient_magnitude) + 0.5 * np.std(gradient_magnitude)
    edge_mask = gradient_magnitude > threshold
    non_edge_mask = ~edge_mask

    if np.sum(edge_mask) > 0 and np.sum(non_edge_mask) > 0:
        edge_std = np.std(image[edge_mask])
        non_edge_std = np.std(image[non_edge_mask])

        if non_edge_std == 0:
            snr_edge = 100.0
        else:
            snr_edge = 20 * np.log10(edge_std / non_edge_std)
    else:
        snr_edge = 0

    # Combine SNR estimates
    snr_combined = 0.5 * snr_global + 0.5 * snr_edge

    return max(0, snr_combined)  # Ensure non-negative


def compute_noise_metrics(image):
    """Compute comprehensive noise metrics for an image

    Args:
        image: Grayscale image to analyze

    Returns:
        dict: Dictionary of noise metrics including SNR
    """
    # Make sure image is grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    # Get noise estimate
    noise_std = estimate_image_noise(gray)

    # Calculate signal properties
    mean_signal = np.mean(gray)
    signal_std = np.std(gray)

    # Calculate SNR (Signal-to-Noise Ratio)
    snr = signal_std / noise_std if noise_std > 0 else float('inf')

    # SNR in decibels (dB) = 20 * log10(signal / noise)
    snr_db = 20 * np.log10(snr) if snr > 0 else float('-inf')

    # Normalize SNR for quality score (0-100)
    # Good SNR is typically >20dB, excellent >30dB
    normalized_snr = min(100, max(0, snr_db * 2.5)) if snr_db > 0 else 0

    # Get local noise variation
    local_noise = analyze_local_noise(gray)

    # Get frequency-based noise metrics
    freq_metrics = estimate_noise_frequency(gray)

    return {
        'noise_std': noise_std,
        'mean_signal': mean_signal,
        'signal_std': signal_std,
        'snr': snr,
        'snr_db': snr_db,
        'local_variation': local_noise,
        'frequency_metrics': freq_metrics,
        # Use normalized SNR as the final noise quality metric
        'noise_level': normalized_snr  # This is used in the overall score
    }