import cv2
import numpy as np
from scipy import ndimage


def estimate_image_noise(gray_image):
    """Estimates noise level in the image using multiple methods

    Args:
        gray_image: Grayscale image to analyze

    Returns:
        dict: Noise statistics
    """
    # Method 1: Laplacian variance method
    laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
    laplacian_var = laplacian.var()

    # Method 2: Median filter difference method
    median_filtered = cv2.medianBlur(gray_image, 3)
    noise_diff = gray_image.astype(np.float32) - median_filtered.astype(np.float32)
    noise_std = np.std(noise_diff)
    noise_rms = np.sqrt(np.mean(noise_diff ** 2))

    # Signal-to-noise ratio
    signal_mean = np.mean(gray_image)
    snr = 20 * np.log10(signal_mean / noise_std) if noise_std > 0 and signal_mean > 0 else 0

    # Normalized measures
    dynamic_range = np.max(gray_image) - np.min(gray_image)
    noise_ratio = noise_std / dynamic_range if dynamic_range > 0 else 1

    return {
        'noise_std': noise_std,
        'noise_rms': noise_rms,
        'laplacian_var': laplacian_var,
        'snr_db': snr,
        'noise_ratio': noise_ratio,
        'noise_level': min(100, max(0, 100 * (1 - noise_ratio ** 0.5)))
    }


def analyze_local_noise(gray_image, block_size=16):
    """Analyzes spatial variation in noise levels across the image

    Args:
        gray_image: Grayscale image to analyze
        block_size: Size of blocks for local noise analysis

    Returns:
        dict: Local noise statistics and noise map
    """
    h, w = gray_image.shape
    noise_map = np.zeros((h // block_size, w // block_size), dtype=np.float32)
    local_snr_values = []

    # Analyze local blocks
    for i in range(0, h - block_size, block_size):
        for j in range(0, w - block_size, block_size):
            block = gray_image[i:i + block_size, j:j + block_size]

            # Calculate local noise
            median_filtered = cv2.medianBlur(block, 3)
            noise_diff = block.astype(float) - median_filtered.astype(float)
            local_noise = np.std(noise_diff)

            # Local signal strength
            local_signal = np.mean(block)

            # Local SNR
            local_snr = 20 * np.log10(local_signal / local_noise) if local_noise > 0 and local_signal > 0 else 0
            local_snr_values.append(local_snr)

            # Store in map
            map_i, map_j = i // block_size, j // block_size
            noise_map[map_i, map_j] = local_noise

    # Calculate metrics for the noise map
    noise_uniformity = 100 * (1 - np.std(noise_map) / np.mean(noise_map)) if np.mean(noise_map) > 0 else 0
    noise_uniformity = max(0, min(100, noise_uniformity))

    # Average SNR and its consistency
    mean_snr = np.mean(local_snr_values) if local_snr_values else 0
    snr_std = np.std(local_snr_values) if local_snr_values else 0
    snr_consistency = 100 * (1 - snr_std / mean_snr) if mean_snr > 0 else 0
    snr_consistency = max(0, min(100, snr_consistency))

    return {
        'local_noise_map': noise_map,
        'noise_uniformity': noise_uniformity,
        'mean_snr': mean_snr,
        'snr_consistency': snr_consistency
    }


def estimate_noise_frequency(gray_image):
    """Analyzes noise frequency characteristics using FFT

    Args:
        gray_image: Grayscale image to analyze

    Returns:
        dict: Frequency-domain noise statistics
    """
    # Apply FFT
    f_transform = np.fft.fft2(gray_image.astype(float))
    f_shift = np.fft.fftshift(f_transform)
    magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1)

    # Get image dimensions
    h, w = gray_image.shape
    center_y, center_x = h // 2, w // 2

    # Analyze frequency bands (low, mid, high)
    radius_low = min(h, w) // 8
    radius_mid = min(h, w) // 4

    # Create masks for different frequency bands
    y_grid, x_grid = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x_grid - center_x) ** 2 + (y_grid - center_y) ** 2)

    low_mask = dist_from_center <= radius_low
    mid_mask = (dist_from_center > radius_low) & (dist_from_center <= radius_mid)
    high_mask = dist_from_center > radius_mid

    # Calculate energy in each band
    total_energy = np.sum(magnitude_spectrum)
    low_energy = np.sum(magnitude_spectrum * low_mask) / total_energy if total_energy > 0 else 0
    mid_energy = np.sum(magnitude_spectrum * mid_mask) / total_energy if total_energy > 0 else 0
    high_energy = np.sum(magnitude_spectrum * high_mask) / total_energy if total_energy > 0 else 0

    # High frequency ratio (indicator of noise)
    high_freq_ratio = high_energy / (low_energy + 1e-10)

    # Score based on desired frequency profile for DIC (balanced with some high frequency content)
    freq_balance_score = 100 * (0.6 * low_energy + 0.3 * mid_energy + 0.1 * high_energy)
    freq_balance_score = min(100, max(0, freq_balance_score))

    return {
        'low_freq_energy': low_energy * 100,  # as percentage
        'mid_freq_energy': mid_energy * 100,
        'high_freq_energy': high_energy * 100,
        'high_freq_ratio': high_freq_ratio,
        'frequency_balance': freq_balance_score
    }


def compute_noise_metrics(gray_image):
    """Comprehensive noise analysis for DIC quality assessment

    Args:
        gray_image: Grayscale image to analyze

    Returns:
        dict: Complete noise metrics
    """
    # Get basic noise estimates
    noise_stats = estimate_image_noise(gray_image)

    # Get local noise variation
    local_noise = analyze_local_noise(gray_image)

    # Get frequency characteristics
    freq_stats = estimate_noise_frequency(gray_image)

    # Combine results
    combined_metrics = {
        'noise_level': noise_stats['noise_level'],
        'snr_db': noise_stats['snr_db'],
        'noise_uniformity': local_noise['noise_uniformity'],
        'frequency_balance': freq_stats['frequency_balance'],
        'high_freq_noise': freq_stats['high_freq_energy'],
        'noise_map': local_noise['local_noise_map']
    }

    # Calculate overall noise quality score for DIC (higher is better)
    # SNR contribution (40%) - higher SNR is better
    snr_score = min(100, max(0, noise_stats['snr_db'] * 2.5)) if noise_stats['snr_db'] < 40 else 100

    # Noise uniformity contribution (30%) - more uniform noise is better
    uniformity_score = local_noise['noise_uniformity']

    # Frequency balance contribution (30%) - balanced frequency content is better
    freq_score = freq_stats['frequency_balance']

    # Weighted score
    noise_quality_score = (
            snr_score * 0.4 +
            uniformity_score * 0.3 +
            freq_score * 0.3
    )

    combined_metrics['noise_quality_score'] = min(100, noise_quality_score)

    return combined_metrics