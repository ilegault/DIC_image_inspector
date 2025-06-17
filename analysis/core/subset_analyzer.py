# analysis/core/subset_analyzer.py

import cv2
import numpy as np
from scipy.signal import correlate2d
from scipy.stats import entropy


def determine_optimal_subset_size(image):
    """Determines optimal subset size for DIC analysis

    Args:
        image: Numpy array of grayscale image

    Returns:
        int: Recommended subset size in pixels
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    # Get image dimensions
    h, w = gray.shape
    min_dim = min(h, w)

    # Default sizes to consider
    possible_sizes = [11, 15, 21, 31, 41, 51]
    valid_sizes = [s for s in possible_sizes if s < min_dim / 3]

    if not valid_sizes:
        return min(possible_sizes)  # Return smallest size if image is very small

    # Analyze feature size using adaptive thresholding
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    num_components, _, stats, _ = cv2.connectedComponentsWithStats(binary)

    avg_feature_size = 0
    if num_components > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]  # Skip background (index 0)
        valid_areas = areas[(areas > 4) & (areas < 1000)]
        if len(valid_areas) > 0:
            avg_feature_size = np.median(np.sqrt(valid_areas))

    # Subset should be 3-5x the feature size
    if avg_feature_size > 0:
        ideal_size = int(avg_feature_size * 4)
        closest_size = min(valid_sizes, key=lambda x: abs(x - ideal_size))
        return closest_size

    return valid_sizes[min(1, len(valid_sizes) - 1)]  # Default to second option


def create_subset_grid(image, subset_size=21, overlap=0.5):
    """Creates a grid of overlapping subsets for analysis

    Args:
        image: Numpy array of image
        subset_size: Size of each subset (square)
        overlap: Overlap fraction between subsets (0-1)

    Returns:
        list: List of (x, y, subset) tuples where x,y are top-left coordinates
    """
    step_size = int(subset_size * (1 - overlap))
    if step_size < 1:
        step_size = 1

    h, w = image.shape[:2]
    subsets = []

    for y in range(0, h - subset_size + 1, step_size):
        for x in range(0, w - subset_size + 1, step_size):
            subset = image[y:y + subset_size, x:x + subset_size]
            subsets.append((x, y, subset))

    return subsets


def analyze_subset_uniqueness(subset, neighbor_subsets):
    """Measures how unique a subset is compared to its neighbors

    Args:
        subset: Numpy array of the subset
        neighbor_subsets: List of neighboring subsets

    Returns:
        float: Uniqueness score (0-1, higher is more unique)
    """
    if not neighbor_subsets:
        return 1.0

    # Ensure grayscale
    if len(subset.shape) == 3:
        subset_gray = cv2.cvtColor(subset, cv2.COLOR_RGB2GRAY)
    else:
        subset_gray = subset.copy()

    correlation_scores = []

    for neighbor in neighbor_subsets:
        if len(neighbor.shape) == 3:
            neighbor_gray = cv2.cvtColor(neighbor, cv2.COLOR_RGB2GRAY)
        else:
            neighbor_gray = neighbor.copy()

        # Calculate normalized cross-correlation
        result = cv2.matchTemplate(neighbor_gray, subset_gray, cv2.TM_CCORR_NORMED)
        correlation_scores.append(np.max(result))

    # Average correlation (higher means less unique)
    avg_correlation = np.mean(correlation_scores) if correlation_scores else 0

    # Convert to uniqueness score
    uniqueness = 1.0 - avg_correlation

    return uniqueness


def compute_subset_quality(subset):
    """Computes the quality of a subset for DIC analysis

    Args:
        subset: Numpy array of the subset

    Returns:
        float: Quality score (0-1)
        dict: Detailed metrics
    """
    # Convert to grayscale if needed
    if len(subset.shape) == 3:
        gray = cv2.cvtColor(subset, cv2.COLOR_RGB2GRAY)
    else:
        gray = subset.copy()

    # Calculate intensity gradient
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
    mean_gradient = np.mean(gradient_magnitude)

    # Calculate intensity contrast
    intensity_std = np.std(gray)
    mean_intensity = np.mean(gray)
    contrast = intensity_std / mean_intensity if mean_intensity > 0 else 0

    # Calculate entropy
    hist, _ = np.histogram(gray, bins=256, range=(0, 256), density=True)
    shannon_entropy = entropy(hist[hist > 0]) if np.any(hist > 0) else 0

    # Calculate pattern coverage
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    coverage_ratio = np.sum(binary > 0) / binary.size

    # Compute weighted quality score
    norm_gradient = min(1.0, mean_gradient / 30.0)
    norm_contrast = min(1.0, contrast / 0.3)
    norm_entropy = min(1.0, shannon_entropy / 5.0)
    coverage_score = 1.0 - 2.0 * abs(coverage_ratio - 0.5)

    quality_score = (
            norm_gradient * 0.3 +
            norm_contrast * 0.3 +
            norm_entropy * 0.2 +
            coverage_score * 0.2
    )

    # Ensure score is in [0, 1] range
    quality_score = max(0.0, min(1.0, quality_score))

    metrics = {
        'gradient': mean_gradient,
        'contrast': contrast,
        'entropy': shannon_entropy,
        'coverage': coverage_ratio
    }

    return quality_score, metrics


def analyze_subset_grid(image, subset_size=21, overlap=0.5):
    """Analyzes all subsets in an image and creates a quality map

    Args:
        image: Numpy array of image
        subset_size: Size of each subset
        overlap: Overlap fraction between subsets

    Returns:
        tuple: (quality_map, average_quality, quality_stats)
    """
    # Create subset grid
    subsets = create_subset_grid(image, subset_size, overlap)

    h, w = image.shape[:2]
    quality_map = np.zeros((h, w), dtype=np.float32)
    count_map = np.zeros((h, w), dtype=np.float32)

    quality_scores = []

    for x, y, subset in subsets:
        quality, _ = compute_subset_quality(subset)
        quality_scores.append(quality)

        # Map quality back to original image position
        quality_map[y:y + subset_size, x:x + subset_size] += quality
        count_map[y:y + subset_size, x:x + subset_size] += 1.0

    # Average overlapping regions
    mask = count_map > 0
    quality_map[mask] /= count_map[mask]

    avg_quality = np.mean(quality_scores) if quality_scores else 0

    return quality_map, avg_quality