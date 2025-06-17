# analysis/metrics/correlation_metrics.py

import cv2
import numpy as np
from scipy.signal import correlate2d
from scipy.stats import entropy


def calculate_zncc(template, target):
    """Calculate Zero-Normalized Cross-Correlation between template and target

    Args:
        template: Template image patch
        target: Target image patch

    Returns:
        float: ZNCC score between -1 and 1 (1 is perfect correlation)
    """
    if template.shape != target.shape:
        raise ValueError("Template and target must have the same shape")

    # Normalize template and target
    template_norm = template - np.mean(template)
    target_norm = target - np.mean(target)

    # Calculate ZNCC
    numerator = np.sum(template_norm * target_norm)
    denominator = np.sqrt(np.sum(template_norm ** 2) * np.sum(target_norm ** 2))

    if denominator == 0:
        return 0

    return numerator / denominator


def calculate_subset_distinctiveness(subset, neighborhood_size=3):
    """Calculate how distinctive a subset is compared to its neighbors

    Args:
        subset: Numpy array of grayscale image subset
        neighborhood_size: Size of neighborhood to check for distinctiveness

    Returns:
        float: Distinctiveness score (0-1, higher means more distinctive)
    """
    # Get subset dimensions
    h, w = subset.shape
    padding = neighborhood_size

    # Create padded image to avoid edge effects
    padded = cv2.copyMakeBorder(subset, padding, padding, padding, padding,
                                cv2.BORDER_REFLECT_101)

    # Center coordinates in padded image
    center_y, center_x = padding + h // 2, padding + w // 2

    # Extract center subset (the reference)
    center_subset = padded[center_y - h // 2:center_y + h // 2 + h % 2,
                    center_x - w // 2:center_x + w // 2 + w % 2]

    # Calculate correlation with neighboring subsets
    correlation_scores = []

    # Check neighborhood
    for y_offset in range(-neighborhood_size, neighborhood_size + 1):
        for x_offset in range(-neighborhood_size, neighborhood_size + 1):
            # Skip the center
            if y_offset == 0 and x_offset == 0:
                continue

            # Extract neighbor subset
            y = center_y + y_offset
            x = center_x + x_offset

            neighbor = padded[y - h // 2:y + h // 2 + h % 2, x - w // 2:x + w // 2 + w % 2]

            # Calculate correlation
            correlation = calculate_zncc(center_subset, neighbor)
            correlation_scores.append(abs(correlation))

    # Calculate distinctiveness - lower correlation with neighbors means more distinctive
    avg_correlation = np.mean(correlation_scores) if correlation_scores else 0
    distinctiveness = 1.0 - avg_correlation

    return distinctiveness


def evaluate_correlation_potential(image, subset_size=21, step_size=10):
    """Evaluates the correlation potential of an image for DIC analysis

    Args:
        image: Grayscale image
        subset_size: Size of subsets to analyze
        step_size: Step size for subset grid

    Returns:
        dict: Correlation potential metrics
    """
    # Ensure grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    h, w = gray.shape

    # Create grid of subsets
    subsets = []
    distinctiveness_scores = []
    gradient_scores = []
    entropy_scores = []

    for y in range(0, h - subset_size + 1, step_size):
        for x in range(0, w - subset_size + 1, step_size):
            # Extract subset
            subset = gray[y:y + subset_size, x:x + subset_size]
            subsets.append(subset)

            # Calculate distinctiveness
            dist_score = calculate_subset_distinctiveness(subset)
            distinctiveness_scores.append(dist_score)

            # Calculate gradient
            grad_x = cv2.Sobel(subset, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(subset, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
            grad_score = np.mean(gradient_magnitude) / 255.0
            gradient_scores.append(grad_score)

            # Calculate entropy
            hist, _ = np.histogram(subset, bins=256, range=(0, 256), density=True)
            subset_entropy = entropy(hist[hist > 0]) if np.any(hist > 0) else 0
            entropy_scores.append(subset_entropy / 8.0)  # Normalize by max possible entropy

    # Calculate average metrics
    avg_distinctiveness = np.mean(distinctiveness_scores) if distinctiveness_scores else 0
    avg_gradient = np.mean(gradient_scores) if gradient_scores else 0
    avg_entropy = np.mean(entropy_scores) if entropy_scores else 0

    # Calculate standard deviations to measure uniformity
    std_distinctiveness = np.std(distinctiveness_scores) if distinctiveness_scores else 0
    std_gradient = np.std(gradient_scores) if gradient_scores else 0
    uniformity = 1.0 - (std_distinctiveness + std_gradient) / 2.0

    # Calculate overall correlation potential
    correlation_potential = (
                                    avg_distinctiveness * 0.4 +
                                    avg_gradient * 0.4 +
                                    avg_entropy * 0.1 +
                                    uniformity * 0.1
                            ) * 100

    return {
        'correlation_potential': min(100, correlation_potential),
        'distinctiveness': avg_distinctiveness * 100,
        'gradient_strength': avg_gradient * 100,
        'intensity_entropy': avg_entropy * 100,
        'pattern_uniformity': uniformity * 100,
        'subset_count': len(subsets)
    }


def generate_correlation_map(image, subset_size=21, step_size=10):
    """Generate a map showing correlation potential across the image

    Args:
        image: Grayscale image
        subset_size: Size of subsets to analyze
        step_size: Step size for subset grid

    Returns:
        numpy.ndarray: Heatmap of correlation potential
    """
    # Ensure grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    h, w = gray.shape

    # Create empty heatmap
    heatmap = np.zeros((h, w), dtype=np.float32)
    count_map = np.zeros((h, w), dtype=np.float32)

    for y in range(0, h - subset_size + 1, step_size):
        for x in range(0, w - subset_size + 1, step_size):
            # Extract subset
            subset = gray[y:y + subset_size, x:x + subset_size]

            # Calculate metrics for this subset
            distinctiveness = calculate_subset_distinctiveness(subset)

            # Calculate gradient
            grad_x = cv2.Sobel(subset, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(subset, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
            gradient_score = np.mean(gradient_magnitude) / 255.0

            # Combined score
            quality_score = (distinctiveness * 0.6 + gradient_score * 0.4) * 100

            # Add to heatmap
            heatmap[y:y + subset_size, x:x + subset_size] += quality_score
            count_map[y:y + subset_size, x:x + subset_size] += 1

    # Average the overlapping areas
    mask = count_map > 0
    heatmap[mask] /= count_map[mask]

    # Normalize to 0-255 for visualization
    heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    return heatmap