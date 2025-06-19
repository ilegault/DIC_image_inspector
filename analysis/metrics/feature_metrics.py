# analysis/metrics/feature_metrics.py

import cv2
import numpy as np
from scipy.stats import entropy
from scipy.spatial import distance
from scipy.ndimage import measurements


def calculate_speckle_density(binary_image):
    """Calculate the density of speckle features in the image with improved filtering

    Args:
        binary_image: Binary image with speckles (255) on background (0)

    Returns:
        float: Speckle density in features per megapixel, adjusted for resolution
    """
    # Get connected components (exclude background at index 0)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)

    # Calculate image resolution (pixels per area)
    height, width = binary_image.shape
    image_area_mpx = (height * width) / 1_000_000

    # Adaptive minimum area based on image resolution
    # For higher resolution images, use larger minimum area
    min_area = max(4, int(image_area_mpx * 2))

    # Maximum area to filter out large artifacts (relative to image size)
    max_area = int(binary_image.size * 0.05)  # 5% of image size

    # Count only valid speckles (exclude background, noise, and large artifacts)
    valid_speckles = sum(1 for i in range(1, num_labels)
                         if min_area <= stats[i, cv2.CC_STAT_AREA] <= max_area)

    # Calculate density (features per megapixel)
    if image_area_mpx > 0:
        density = valid_speckles / image_area_mpx

        # Apply normalization for very high resolution images
        if image_area_mpx > 10:  # Over 10 megapixels
            density = density * 0.85  # Reduce density slightly for high-res
    else:
        density = 0

    return density


def analyze_feature_size(gray):
    """Analyze the size distribution of speckles

    Args:
        gray: Grayscale image to analyze

    Returns:
        dict: Statistics about feature sizes
    """
    # Apply adaptive thresholding to identify speckles
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Find connected components
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)

    if num_labels <= 1:  # Only background
        return {
            'mean_size': 0,
            'median_size': 0,
            'std_size': 0,
            'min_size': 0,
            'max_size': 0,
            'size_uniformity': 0,
            'count': 0
        }

    # Get areas of all speckles (skip background at index 0)
    areas = stats[1:, cv2.CC_STAT_AREA]

    # Filter out noise (very small components)
    valid_areas = areas[areas >= 4]

    if len(valid_areas) == 0:
        return {
            'mean_size': 0,
            'median_size': 0,
            'std_size': 0,
            'min_size': 0,
            'max_size': 0,
            'size_uniformity': 0,
            'count': 0
        }

    # Calculate statistics
    mean_size = np.mean(valid_areas)
    median_size = np.median(valid_areas)
    std_size = np.std(valid_areas)
    min_size = np.min(valid_areas)
    max_size = np.max(valid_areas)

    # Calculate uniformity (coefficient of variation inverted and normalized)
    cv_value = std_size / mean_size if mean_size > 0 else float('inf')
    size_uniformity = max(0, min(100, 100 * (1 - cv_value)))

    return {
        'mean_size': mean_size,
        'median_size': median_size,
        'std_size': std_size,
        'min_size': min_size,
        'max_size': max_size,
        'size_uniformity': size_uniformity,
        'count': len(valid_areas)
    }


def evaluate_gradient_quality(gray):
    """Evaluate the quality of intensity gradients in the image

    Args:
        gray: Grayscale image to analyze

    Returns:
        dict: Gradient quality metrics
    """
    # Calculate gradients using Sobel operator
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    # Calculate gradient magnitude and direction
    magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
    direction = np.arctan2(grad_y, grad_x) * 180 / np.pi

    # Analyze gradient metrics
    mean_magnitude = np.mean(magnitude)
    median_magnitude = np.median(magnitude)
    std_magnitude = np.std(magnitude)

    # Calculate gradient directional diversity (entropy of directions)
    hist, _ = np.histogram(direction, bins=36, range=(-180, 180), density=True)
    direction_entropy = entropy(hist[hist > 0]) if np.any(hist > 0) else 0

    # Normalize direction entropy (max entropy for 36 bins is log(36))
    max_entropy = np.log(36)
    normalized_entropy = direction_entropy / max_entropy if max_entropy > 0 else 0

    # Calculate percentage of pixels with significant gradients
    significant_threshold = 10  # Threshold for significant gradient
    significant_pixels = np.sum(magnitude > significant_threshold) / magnitude.size

    return {
        'mean_magnitude': mean_magnitude,
        'median_magnitude': median_magnitude,
        'std_magnitude': std_magnitude,
        'direction_diversity': normalized_entropy * 100,  # As percentage
        'significant_gradient_ratio': significant_pixels * 100  # As percentage
    }


def measure_intensity_contrast(gray):
    """Measure the contrast of the image

    Args:
        gray: Grayscale image to analyze

    Returns:
        dict: Contrast metrics
    """
    # Basic statistics
    min_val = np.min(gray)
    max_val = np.max(gray)
    mean_val = np.mean(gray)
    std_val = np.std(gray)

    # Calculate various contrast measures
    if max_val > min_val:
        michelson_contrast = (max_val - min_val) / (max_val + min_val)
    else:
        michelson_contrast = 0

    weber_contrast = std_val / mean_val if mean_val > 0 else 0

    # Calculate histogram metrics
    hist, bins = np.histogram(gray, bins=256, range=(0, 256), density=True)
    hist_entropy = entropy(hist[hist > 0]) if np.any(hist > 0) else 0

    # Dynamic range utilization (percentage of all possible 256 gray levels used)
    used_bins = np.sum(hist > 0)
    dynamic_range = (used_bins / 256) * 100

    return {
        'michelson_contrast': michelson_contrast * 100,  # As percentage
        'weber_contrast': weber_contrast * 100,  # As percentage
        'std_deviation': std_val,
        'dynamic_range': dynamic_range,
        'histogram_entropy': hist_entropy
    }


def compute_feature_coverage(gray):
    """Compute the coverage of features across the image

    Args:
        gray: Grayscale image to analyze

    Returns:
        dict: Coverage metrics
    """
    # Create binary image using adaptive thresholding
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Calculate overall coverage ratio
    coverage_ratio = np.sum(binary > 0) / binary.size

    # Analyze coverage uniformity by splitting into grid cells
    rows, cols = 8, 8
    cell_height = gray.shape[0] // rows
    cell_width = gray.shape[1] // cols

    coverage_per_cell = []

    for i in range(rows):
        for j in range(cols):
            # Get cell coordinates
            y1 = i * cell_height
            y2 = min((i + 1) * cell_height, gray.shape[0])
            x1 = j * cell_width
            x2 = min((j + 1) * cell_width, gray.shape[1])

            # Extract cell and calculate coverage
            cell = binary[y1:y2, x1:x2]
            cell_coverage = np.sum(cell > 0) / cell.size
            coverage_per_cell.append(cell_coverage)

    # Calculate uniformity metrics
    std_coverage = np.std(coverage_per_cell)
    mean_coverage = np.mean(coverage_per_cell)

    # Calculate uniformity (coefficient of variation inverted and normalized)
    cv_value = std_coverage / mean_coverage if mean_coverage > 0 else float('inf')
    uniformity = max(0, min(100, 100 * (1 - cv_value)))

    # Calculate optimal coverage score (closer to 50% is better for DIC)
    optimal_coverage_score = 100 - abs(coverage_ratio - 0.5) * 200  # 0-100 scale

    return {
        'coverage_percent': coverage_ratio * 100,
        'uniformity': uniformity,
        'min_cell_coverage': min(coverage_per_cell) * 100 if coverage_per_cell else 0,
        'max_cell_coverage': max(coverage_per_cell) * 100 if coverage_per_cell else 0,
        'optimal_coverage_score': optimal_coverage_score
    }


def calculate_feature_spacing(gray_image, binary_image=None):
    """Calculates average spacing between features/speckles

    Args:
        gray_image: Grayscale image with speckles
        binary_image: Optional pre-computed binary image (if None, will generate from gray_image)

    Returns:
        dict: Spacing statistics
    """
    # Generate binary image if not provided
    if binary_image is None:
        binary_image = cv2.adaptiveThreshold(
            gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

    # Find centroids of all connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)

    # Skip background (index 0)
    if num_labels < 3:  # Need at least 2 speckles plus background
        return {
            'mean_spacing': 0,
            'median_spacing': 0,
            'min_spacing': 0,
            'nearest_neighbor': 0,
            'spacing_std': 0,
            'regularity': 0
        }

    # Use only centroids of valid speckles (skip background at index 0)
    valid_centroids = centroids[1:]

    # Calculate nearest neighbor distances
    distances = []
    nearest_neighbors = []

    for i, centroid1 in enumerate(valid_centroids):
        min_dist = float('inf')
        for j, centroid2 in enumerate(valid_centroids):
            if i != j:
                dist = np.sqrt((centroid1[0] - centroid2[0]) ** 2 + (centroid1[1] - centroid2[1]) ** 2)
                min_dist = min(min_dist, dist)
                distances.append(dist)

        if min_dist < float('inf'):
            nearest_neighbors.append(min_dist)

    if not nearest_neighbors:
        return {
            'mean_spacing': 0,
            'median_spacing': 0,
            'min_spacing': 0,
            'nearest_neighbor': 0,
            'spacing_std': 0,
            'regularity': 0
        }

    # Calculate statistics
    mean_spacing = np.mean(distances)
    median_spacing = np.median(distances)
    min_spacing = np.min(distances)
    mean_nearest = np.mean(nearest_neighbors)
    std_nearest = np.std(nearest_neighbors)

    # Regularity - lower coefficient of variation means more regular spacing
    cv = std_nearest / mean_nearest if mean_nearest > 0 else float('inf')
    regularity = max(0, min(100, 100 * (1 - cv)))

    return {
        'mean_spacing': mean_spacing,
        'median_spacing': median_spacing,
        'min_spacing': min_spacing,
        'nearest_neighbor': mean_nearest,
        'spacing_std': std_nearest,
        'regularity': regularity
    }


def assess_feature_quality(gray):
    """Assess overall feature quality for DIC by combining multiple metrics

    Args:
        gray: Grayscale image to analyze

    Returns:
        dict: Combined quality metrics
    """
    # Calculate individual metrics
    density_metrics = calculate_speckle_density(gray)
    size_metrics = analyze_feature_size(gray)
    gradient_metrics = evaluate_gradient_quality(gray)
    contrast_metrics = measure_intensity_contrast(gray)
    coverage_metrics = compute_feature_coverage(gray)
    spacing_metrics = calculate_feature_spacing(gray)

    # Calculate optimal feature size for DIC (3-5 pixels is often ideal)
    mean_size = size_metrics['mean_size'] if isinstance(size_metrics, dict) else 0
    feature_size = np.sqrt(mean_size)  # Approximate diameter from area

    # Calculate feature size score (highest at 3-7 pixels diameter)
    if feature_size < 3:
        size_score = feature_size / 3 * 100  # Linear ramp up to 3
    elif feature_size <= 7:
        size_score = 100  # Ideal range
    else:
        size_score = max(0, 100 - (feature_size - 7) * 10)  # Linear fall-off

    # Calculate overall quality score with weighted components
    quality_score = (
            size_metrics.get('size_uniformity', 0) * 0.15 +
            coverage_metrics.get('uniformity', 0) * 0.15 +
            spacing_metrics.get('regularity', 0) * 0.20 +
            contrast_metrics.get('dynamic_range', 0) * 0.10 +
            gradient_metrics.get('significant_gradient_ratio', 0) * 0.20 +
            size_score * 0.10 +
            coverage_metrics.get('optimal_coverage_score', 0) * 0.10
    )

    return {
        'feature_density': density_metrics if not isinstance(density_metrics, dict) else density_metrics,
        'feature_size': feature_size,
        'size_uniformity': size_metrics.get('size_uniformity', 0),
        'coverage': coverage_metrics.get('coverage_percent', 0),
        'coverage_uniformity': coverage_metrics.get('uniformity', 0),
        'spacing_regularity': spacing_metrics.get('regularity', 0),
        'contrast': contrast_metrics.get('michelson_contrast', 0),
        'gradient_strength': gradient_metrics.get('mean_magnitude', 0),
        'quality_score': quality_score
    }