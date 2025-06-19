# analysis/metrics/feature_metrics.py

import cv2
import numpy as np
from scipy.stats import entropy
from scipy.spatial import distance
from scipy.ndimage import measurements


def calculate_speckle_density(binary_image):
    """Calculate the density of speckle features in the image with improved scaling

    Args:
        binary_image: Binary image with speckles (255) on background (0)

    Returns:
        float: Speckle density in features per megapixel, adjusted for scale
    """
    # Get connected components (exclude background at index 0)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)

    # Calculate image resolution (pixels per area)
    height, width = binary_image.shape
    image_area_mpx = (height * width) / 1_000_000

    # Calculate average feature size in this particular image to set better thresholds
    areas = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels)]
    if areas:
        median_area = np.median(areas)
        # More adaptive approach based on image content
        min_area = max(3, int(median_area * 0.2))  # Allow smaller features (20% of median)
        max_area = min(int(binary_image.size * 0.05), int(median_area * 5.0))  # Cap at 5x median
    else:
        min_area = 4
        max_area = int(binary_image.size * 0.05)

    # Count only valid speckles using adaptive thresholds
    valid_speckles = sum(1 for i in range(1, num_labels)
                         if min_area <= stats[i, cv2.CC_STAT_AREA] <= max_area)

    # Calculate density (features per megapixel)
    if image_area_mpx > 0:
        density = valid_speckles / image_area_mpx

        # Scale density for small windows to avoid artificially high values
        if image_area_mpx < 0.1:  # Very small regions (<0.1 MPx)
            density = density * (0.7 + 3.0 * image_area_mpx)  # More aggressive scaling

        # Apply normalization for very high resolution images
        if image_area_mpx > 5:  # Over 5 megapixels
            density = density * 0.85  # Reduce density slightly for high-res
    else:
        density = 0

    return density


def detect_speckles(gray_image):
    """
    Common speckle detection function that can be reused across the codebase

    Args:
        gray_image: Grayscale image to analyze

    Returns:
        tuple: (binary_image, stats, labels, centroids, avg_feature_size)
    """
    from analysis.core.subset_analyzer import determine_optimal_subset_size

    # Determine optimal subset size for adaptive parameters
    subset_size = determine_optimal_subset_size(gray_image)

    # Use adaptive thresholding with parameters based on subset size
    block_size = max(7, min(subset_size // 3, 15))
    if block_size % 2 == 0:  # Block size must be odd
        block_size += 1

    binary = cv2.adaptiveThreshold(
        gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, block_size, 2
    )

    # Get connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    # Calculate average feature size (excluding background)
    if num_labels > 1:
        areas = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels)]
        valid_areas = [a for a in areas if a > 3 and a < gray_image.size * 0.05]
        avg_feature_size = np.median(valid_areas) if valid_areas else 0
    else:
        avg_feature_size = 0

    return binary, stats, labels, centroids, avg_feature_size


def analyze_feature_size(gray):
    """
    Analyze the size distribution of speckles

    Args:
        gray: Grayscale image to analyze

    Returns:
        dict: Statistics about feature size distribution and quality score
    """
    # Use common detection function first
    binary, stats, labels, centroids, avg_feature_size = detect_speckles(gray)

    # Now focus on analyzing the feature sizes rather than detection
    num_labels = len(stats)

    if num_labels <= 1:  # No features detected
        return {
            'avg_size': 0,
            'median_size': 0,
            'std_size': 0,
            'min_size': 0,
            'max_size': 0,
            'size_variation': 1.0,
            'feature_count': 0,
            'density': 0,
            'quality_score': 0
        }

    # Extract areas (skip background at index 0)
    areas = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels)]

    # Filter for valid features
    valid_areas = [a for a in areas if a > 3 and a < gray.size * 0.05]

    if not valid_areas:
        return {
            'avg_size': 0,
            'median_size': 0,
            'std_size': 0,
            'min_size': 0,
            'max_size': 0,
            'size_variation': 1.0,
            'feature_count': 0,
            'density': 0,
            'quality_score': 0
        }

    # Calculate size statistics
    avg_size = np.mean(valid_areas)
    median_size = np.median(valid_areas)
    std_size = np.std(valid_areas)
    min_size = np.min(valid_areas)
    max_size = np.max(valid_areas)

    # Size variation (coefficient of variation)
    size_variation = std_size / avg_size if avg_size > 0 else 1.0

    # Calculate density
    height, width = gray.shape
    feature_count = len(valid_areas)
    image_area_mpx = (height * width) / 1_000_000
    density = feature_count / image_area_mpx if image_area_mpx > 0 else 0

    # Calculate quality score based on feature size distribution
    # Ideal size for DIC is typically 3-5 pixels radius (28-75 sq pixels area)
    ideal_size = 50
    size_score = 100 * (1.0 - min(1.0, abs(median_size - ideal_size) / ideal_size))

    # Penalize high variation
    uniformity_score = 100 * (1.0 - min(1.0, size_variation))

    # Overall quality score
    quality_score = 0.6 * size_score + 0.4 * uniformity_score

    return {
        'avg_size': avg_size,
        'median_size': median_size,
        'std_size': std_size,
        'min_size': min_size,
        'max_size': max_size,
        'size_variation': size_variation,
        'feature_count': feature_count,
        'density': density,
        'quality_score': quality_score
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