import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import Delaunay


def calculate_pattern_uniformity(binary_image):
    """Calculates how uniform the pattern is distributed across the image

    Args:
        binary_image: Binary image with features

    Returns:
        float: Uniformity score (0-100)
    """
    # Find all feature centroids
    num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)

    if num_labels <= 2:  # Only background or one feature
        return 0

    # Skip background (label 0)
    centroids = centroids[1:]

    # Divide image into grid
    h, w = binary_image.shape
    grid_size = max(10, min(h, w) // 10)  # Adaptive grid size
    n_cells_x = w // grid_size
    n_cells_y = h // grid_size

    # Count features in each grid cell
    grid_counts = np.zeros((n_cells_y, n_cells_x), dtype=int)

    for x, y in centroids:
        cell_x = min(int(x) // grid_size, n_cells_x - 1)
        cell_y = min(int(y) // grid_size, n_cells_y - 1)
        grid_counts[cell_y, cell_x] += 1

    # Calculate coefficient of variation
    mean_count = np.mean(grid_counts)
    if mean_count == 0:
        return 0

    std_count = np.std(grid_counts)
    cv = std_count / mean_count

    # Convert to uniformity score (lower CV means higher uniformity)
    uniformity = 100 * (1 - min(cv, 1))

    return round(uniformity, 1)


def calculate_uniformity(gray_image):
    """Calculate pattern uniformity from grayscale image

    Args:
        gray_image: Grayscale image

    Returns:
        float: Uniformity score (0-100)
    """
    # Threshold to create binary image for analysis
    _, binary = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return calculate_pattern_uniformity(binary)


def analyze_edge_quality(gray_image):
    """Analyze the quality of edges in the image for DIC correlation

    Args:
        gray_image: Grayscale input image

    Returns:
        float: Edge quality score (0-100)
    """
    # Calculate gradients using Sobel operators
    grad_x = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=3)

    # Calculate gradient magnitude and direction
    magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

    # Normalize magnitude to 0-255 range
    magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)

    # Calculate edge density (percentage of pixels with significant gradients)
    threshold = np.mean(magnitude_norm) + np.std(magnitude_norm)
    edge_pixels = magnitude_norm > threshold
    edge_density = np.sum(edge_pixels) / magnitude_norm.size

    # Calculate edge strength (mean gradient magnitude)
    edge_strength = np.mean(magnitude_norm[edge_pixels]) if np.sum(edge_pixels) > 0 else 0

    # Calculate edge quality score
    # Good DIC patterns need sufficient edge density (5-20%) and strong edges
    optimal_density = 0.125  # 12.5% is often optimal
    density_score = 100 * (1 - abs(edge_density - optimal_density) / optimal_density)
    density_score = max(0, min(100, density_score))

    # Strength score (normalize to 0-100)
    strength_score = min(100, edge_strength * 100 / 128)

    # Combined edge quality score
    edge_quality = (density_score * 0.6 + strength_score * 0.4)

    return round(edge_quality, 1)


def calculate_gradient_magnitude(gray_image):
    """Calculate overall gradient magnitude for the image

    Args:
        gray_image: Grayscale input image

    Returns:
        float: Average gradient magnitude (0-100)
    """
    # Calculate gradients
    grad_x = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=3)

    # Calculate magnitude
    magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

    # Normalize to 0-100 scale
    avg_magnitude = np.mean(magnitude)
    max_possible = 255 * np.sqrt(2)  # Maximum possible gradient magnitude

    gradient_score = min(100, (avg_magnitude / max_possible) * 200)  # Scale for visibility

    return round(gradient_score, 1)


def analyze_nearest_neighbor_distribution(binary_image):
    """Analyzes distribution of nearest neighbor distances

    Args:
        binary_image: Binary image with features

    Returns:
        dict: Statistics about nearest neighbor distances
    """
    # Find all feature centroids
    num_labels, _, _, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)

    if num_labels <= 2:  # Background + maybe one feature
        return {
            'mean_distance': 0,
            'std_distance': 0,
            'cv_distance': 0,
            'regularity': 0
        }

    # Skip background (label 0)
    centroids = centroids[1:]

    # Calculate nearest neighbor distance for each centroid
    nearest_distances = []
    for i, point1 in enumerate(centroids):
        min_dist = float('inf')
        for j, point2 in enumerate(centroids):
            if i != j:
                dist = np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)
                min_dist = min(min_dist, dist)

        if min_dist < float('inf'):
            nearest_distances.append(min_dist)

    if not nearest_distances:
        return {
            'mean_distance': 0,
            'std_distance': 0,
            'cv_distance': 0,
            'regularity': 0
        }

    # Calculate statistics
    mean_dist = np.mean(nearest_distances)
    std_dist = np.std(nearest_distances)
    cv = std_dist / mean_dist if mean_dist > 0 else float('inf')

    # Regularity score (lower CV means more regular spacing)
    regularity = 100 * (1 - min(cv, 1))

    return {
        'mean_distance': round(mean_dist, 2),
        'std_distance': round(std_dist, 2),
        'cv_distance': round(cv, 3),
        'regularity': round(regularity, 1)
    }


def calculate_spatial_coverage(binary_image):
    """Evaluates how well the pattern covers the entire region

    Args:
        binary_image: Binary image with features

    Returns:
        dict: Coverage metrics
    """
    # Calculate distance transform (distance to nearest feature)
    dist_transform = distance_transform_edt(~binary_image)

    # Calculate coverage statistics
    mean_dist = np.mean(dist_transform)
    max_dist = np.max(dist_transform)

    # Calculate percentage of pixels within specific distance thresholds
    good_threshold = mean_dist * 1.5
    coverage_percentage = 100 * np.sum(dist_transform <= good_threshold) / dist_transform.size

    # Divide image into grid for uniformity analysis
    h, w = binary_image.shape
    grid_size = max(10, min(h, w) // 10)
    n_cells_x = w // grid_size
    n_cells_y = h // grid_size

    # Calculate coverage in each grid cell
    coverage_per_cell = []

    for y in range(n_cells_y):
        for x in range(n_cells_x):
            y1 = y * grid_size
            x1 = x * grid_size
            y2 = min((y + 1) * grid_size, h)
            x2 = min((x + 1) * grid_size, w)

            # Get cell from distance transform
            cell = dist_transform[y1:y2, x1:x2]
            coverage = 100 * np.sum(cell <= good_threshold) / cell.size
            coverage_per_cell.append(coverage)

    # Calculate coverage uniformity
    std_coverage = np.std(coverage_per_cell) if coverage_per_cell else 0
    mean_coverage = np.mean(coverage_per_cell) if coverage_per_cell else 0

    cv = std_coverage / mean_coverage if mean_coverage > 0 else 0
    uniformity = 100 * (1 - min(cv, 1))

    return {
        'coverage_percent': round(coverage_percentage, 1),
        'mean_distance': round(mean_dist, 2),
        'max_distance': round(max_dist, 2),
        'uniformity': round(uniformity, 1)
    }


def evaluate_spatial_quality(binary_image):
    """Evaluates overall spatial quality of pattern for DIC

    Args:
        binary_image: Binary image with pattern features

    Returns:
        dict: Comprehensive spatial quality metrics
    """
    # Calculate component metrics
    uniformity = calculate_pattern_uniformity(binary_image)
    neighbor_stats = analyze_nearest_neighbor_distribution(binary_image)
    coverage_stats = calculate_spatial_coverage(binary_image)

    # Calculate feature density
    num_labels, _, _, _ = cv2.connectedComponentsWithStats(binary_image, connectivity=8)
    feature_count = num_labels - 1  # Subtract background
    h, w = binary_image.shape
    density = feature_count / ((h * w) / 1000000)  # features per Mpx

    # Calculate edge quality (gradient at feature boundaries)
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.morphologyEx(binary_image, cv2.MORPH_GRADIENT, kernel)
    edge_quality = 100 * np.sum(edges) / max(1, np.sum(binary_image))

    # Calculate overall spatial score with weighted components
    overall_uniformity = (
            uniformity * 0.4 +
            neighbor_stats['regularity'] * 0.3 +
            coverage_stats['uniformity'] * 0.3
    )

    # Calculate combined quality score
    spatial_score = (
            uniformity * 0.25 +
            neighbor_stats['regularity'] * 0.25 +
            coverage_stats['coverage_percent'] * 0.2 +
            min(100, density) * 0.15 +
            min(100, edge_quality) * 0.15
    )

    return {
        'spatial_score': round(spatial_score, 1),
        'pattern_uniformity': round(uniformity, 1),
        'neighbor_regularity': round(neighbor_stats['regularity'], 1),
        'coverage_uniformity': round(coverage_stats['uniformity'], 1),
        'coverage_percent': round(coverage_stats['coverage_percent'], 1),
        'feature_density': round(density, 1),
        'edge_quality': round(min(100, edge_quality), 1),
        'mean_nn_distance': round(neighbor_stats['mean_distance'], 2),
        'overall_uniformity': round(max(0, min(overall_uniformity, 100)), 1)
    }