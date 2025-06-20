# analysis/core/pattern_analyzer.py

import cv2
import numpy as np


def analyze_speckle_histogram(binary_image):
    """Analyzes histogram of speckle sizes to assess pattern quality

    Args:
        binary_image: Binary image with speckles (white) on background (black)

    Returns:
        dict: Statistics about speckle size distribution
    """
    # Get connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)

    # Skip background (label 0)
    areas = stats[1:, cv2.CC_STAT_AREA]

    # Filter out noise (too small) and large blobs
    valid_areas = areas[(areas > 4) & (areas < 1000)]

    if len(valid_areas) == 0:
        return {
            'mean_area': 0,
            'std_area': 0,
            'median_area': 0,
            'min_area': 0,
            'max_area': 0,
            'count': 0,
            'uniformity': 0
        }

    # Calculate statistics
    mean_area = np.mean(valid_areas)
    std_area = np.std(valid_areas)
    median_area = np.median(valid_areas)
    min_area = np.min(valid_areas)
    max_area = np.max(valid_areas)

    # Calculate coefficient of variation as a uniformity measure (lower is better)
    cv = std_area / mean_area if mean_area > 0 else float('inf')
    uniformity = max(0, min(100, 100 * (1 - cv)))

    return {
        'mean_area': mean_area,
        'std_area': std_area,
        'median_area': median_area,
        'min_area': min_area,
        'max_area': max_area,
        'count': len(valid_areas),
        'uniformity': uniformity
    }


def evaluate_pattern_coverage(binary_image):
    """Evaluates coverage and distribution of speckles

    Args:
        binary_image: Binary image with speckles

    Returns:
        dict: Coverage statistics
    """
    height, width = binary_image.shape

    # Calculate overall coverage percentage
    speckle_count = np.sum(binary_image > 0)
    total_pixels = height * width
    coverage = (speckle_count / total_pixels) * 100

    # Analyze coverage uniformity using grid-based approach
    grid_size = min(height, width) // 8
    if grid_size < 4:  # Image too small for grid analysis
        grid_size = 4

    grid_h = height // grid_size
    grid_w = width // grid_size

    coverage_per_cell = []
    for y in range(grid_h):
        for x in range(grid_w):
            # Get cell region
            y_start = y * grid_size
            y_end = min((y + 1) * grid_size, height)
            x_start = x * grid_size
            x_end = min((x + 1) * grid_size, width)

            cell = binary_image[y_start:y_end, x_start:x_end]
            cell_coverage = np.sum(cell > 0) / (cell.shape[0] * cell.shape[1]) * 100
            coverage_per_cell.append(cell_coverage)

    # Calculate coverage uniformity (lower std = more uniform)
    coverage_std = np.std(coverage_per_cell)
    uniformity = max(0, min(100, 100 * (1 - coverage_std / 100)))

    return {
        'coverage_percent': coverage,
        'uniformity': uniformity,
        'grid_cells': len(coverage_per_cell),
        'min_cell_coverage': min(coverage_per_cell) if coverage_per_cell else 0,
        'max_cell_coverage': max(coverage_per_cell) if coverage_per_cell else 0
    }


def calculate_pattern_spacing(binary_image):
    """Calculates average spacing between speckles

    Args:
        binary_image: Binary image with speckles

    Returns:
        dict: Spacing statistics
    """
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

    # Calculate nearest neighbor for each centroid
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

    # Regularity - lower std deviation means more regular spacing
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


def analyze_pattern_quality(gray_image):
    """Comprehensive pattern analysis for DIC quality

    Args:
        gray_image: Grayscale image to analyze

    Returns:
        dict: Comprehensive pattern statistics
    """
    # Create binary image using adaptive thresholding
    binary = cv2.adaptiveThreshold(
        gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Analyze different pattern aspects
    size_stats = analyze_speckle_histogram(binary)
    coverage_stats = evaluate_pattern_coverage(binary)
    spacing_stats = calculate_pattern_spacing(binary)

    # Calculate pattern quality score based on DIC requirements
    quality_score = 0

    # Size uniformity (20%)
    quality_score += size_stats['uniformity'] * 0.2

    # Coverage & distribution (35%)
    quality_score += coverage_stats['uniformity'] * 0.15
    quality_score += min(100, coverage_stats['coverage_percent'] * 2) * 0.2

    # Spacing regularity (30%) 
    quality_score += spacing_stats['regularity'] * 0.3

    # Speckle count bonus (15%)
    ideal_count = gray_image.shape[0] * gray_image.shape[1] / 100  # ~1% of pixels
    count_ratio = min(1.0, size_stats['count'] / ideal_count)
    quality_score += count_ratio * 100 * 0.15

    return {
        'size_stats': size_stats,
        'coverage_stats': coverage_stats,
        'spacing_stats': spacing_stats,
        'quality_score': min(100, quality_score),
        'binary_result': binary
    }


def analyze_roi_speckles(roi_image, roi_coords=None):
    """Perform detailed analysis of speckle pattern in the selected ROI"""
    if roi_image is None:
        return {"error": "No image provided"}

    try:
        from analysis.metrics.pattern_metrics import evaluate_pattern_quality
        from debug_output.roi_speckle_fix import analyze_roi_speckles_improved

        # Convert to grayscale if needed
        if len(roi_image.shape) == 3:
            roi_gray = cv2.cvtColor(roi_image, cv2.COLOR_RGB2GRAY)
        else:
            roi_gray = roi_image.copy()

        # Run comprehensive analysis
        pattern_results = analyze_pattern_quality(roi_gray)
        segmentation_results = analyze_roi_speckles_improved(roi_gray)

        # Create the results dictionary
        results = {
            'speckle_count': segmentation_results['speckle_count'],
            'pattern_quality': pattern_results['quality_score'],
            'size_stats': pattern_results.get('size_stats', {}),
            'coverage': segmentation_results.get('confidence', 0) * 100
        }

        return results

    except Exception as e:
        import traceback
        print(f"Error in ROI speckle analysis: {str(e)}")
        print(traceback.format_exc())
        return {"error": str(e)}