import cv2
import numpy as np
from pathlib import Path


def analyze_roi_speckles_relaxed(roi_image, min_area=2, max_area=2000, debug=False):
    """
    More relaxed speckle detection that captures more speckles
    Reduced filtering to avoid missing valid speckles
    """
    # Create a copy to avoid modifying original
    roi_gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY) if len(roi_image.shape) > 2 else roi_image.copy()

    if debug:
        Path("debug_roi").mkdir(exist_ok=True)
        cv2.imwrite("debug_roi/01_original.png", roi_gray)

    # Try both normal and inverted thresholding
    _, binary_normal = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, binary_inverted = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    if debug:
        cv2.imwrite("debug_roi/02a_binary_normal.png", binary_normal)
        cv2.imwrite("debug_roi/02b_binary_inverted.png", binary_inverted)

    # Process both and choose the better one
    normal_results = process_binary_relaxed(binary_normal, min_area, max_area, debug, "normal")
    inverted_results = process_binary_relaxed(binary_inverted, min_area, max_area, debug, "inverted")

    # Choose based on speckle count (more speckles = better for DIC)
    if normal_results['valid_count'] >= inverted_results['valid_count']:
        chosen_results = normal_results
        binary_chosen = binary_normal
        method = "normal"
    else:
        chosen_results = inverted_results
        binary_chosen = binary_inverted
        method = "inverted"

    chosen_results['method'] = method

    if debug:
        cv2.imwrite("debug_roi/03_chosen_binary.png", binary_chosen)

        # Visualize all detected components (before size filtering)
        all_vis = visualize_all_components(chosen_results['labels'], roi_gray.shape)
        cv2.imwrite("debug_roi/04_all_components.png", all_vis)

        # Visualize only valid components
        valid_vis = visualize_valid_components(chosen_results['labels'],
                                               chosen_results['valid_components'],
                                               roi_gray.shape)
        cv2.imwrite("debug_roi/05_valid_components.png", valid_vis)

        print(f"Detection method: {method}")
        print(f"Total components found: {chosen_results['total_components']}")
        print(f"Valid components after filtering: {chosen_results['valid_count']}")
        print(f"Size range: {min_area}-{max_area} pixels")

    return chosen_results


def process_binary_relaxed(binary, min_area, max_area, debug=False, method_name=""):
    """
    Process binary image with minimal morphological operations to preserve speckles
    """
    # Minimal morphological cleanup - just remove single pixel noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    if debug:
        cv2.imwrite(f"debug_roi/morph_clean_{method_name}.png", cleaned)

    # Connected components analysis
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)

    # More relaxed size filtering
    valid_components = []
    for i in range(1, num_labels):  # Skip background (index 0)
        area = stats[i, cv2.CC_STAT_AREA]
        if min_area <= area <= max_area:
            valid_components.append(i)

    # Calculate statistics
    areas = [stats[i, cv2.CC_STAT_AREA] for i in valid_components]
    avg_size = np.mean(areas) if areas else 0
    total_area = sum(areas) if areas else 0
    roi_area = binary.shape[0] * binary.shape[1]
    speckle_ratio = total_area / roi_area if roi_area > 0 else 0

    return {
        'total_components': num_labels - 1,
        'valid_components': valid_components,
        'valid_count': len(valid_components),
        'labels': labels,
        'stats': stats,
        'centroids': centroids,
        'avg_speckle_size': avg_size,
        'speckle_ratio': speckle_ratio
    }


def analyze_with_multiple_thresholds(roi_image, debug=False):
    """
    Try multiple thresholding approaches and return the best results
    """
    roi_gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY) if len(roi_image.shape) > 2 else roi_image.copy()

    results = {}

    # Method 1: Otsu
    _, binary_otsu = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    results['otsu'] = count_speckles_simple(binary_otsu)

    # Method 2: Adaptive threshold
    binary_adaptive = cv2.adaptiveThreshold(roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY_INV, 11, 2)
    results['adaptive'] = count_speckles_simple(binary_adaptive)

    # Method 3: Multiple Otsu levels
    blurred = cv2.GaussianBlur(roi_gray, (3, 3), 0)
    _, binary_multi = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    results['multi_otsu'] = count_speckles_simple(binary_multi)

    # Method 4: Lower threshold (manual)
    mean_val = np.mean(roi_gray)
    std_val = np.std(roi_gray)
    low_thresh = max(0, mean_val - 0.5 * std_val)
    _, binary_low = cv2.threshold(roi_gray, low_thresh, 255, cv2.THRESH_BINARY_INV)
    results['low_threshold'] = count_speckles_simple(binary_low)

    if debug:
        Path("debug_roi").mkdir(exist_ok=True)
        cv2.imwrite("debug_roi/method_otsu.png", binary_otsu)
        cv2.imwrite("debug_roi/method_adaptive.png", binary_adaptive)
        cv2.imwrite("debug_roi/method_multi.png", binary_multi)
        cv2.imwrite("debug_roi/method_low.png", binary_low)

        print("Threshold method comparison:")
        for method, count in results.items():
            print(f"  {method}: {count} speckles")

    # Return the method that found the most speckles
    best_method = max(results.items(), key=lambda x: x[1])
    return best_method


def count_speckles_simple(binary_image, min_area=2, max_area=2000):
    """
    Simple speckle counting with minimal filtering
    """
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_image, connectivity=8)

    valid_count = 0
    for i in range(1, num_labels):  # Skip background
        area = stats[i, cv2.CC_STAT_AREA]
        if min_area <= area <= max_area:
            valid_count += 1

    return valid_count


def visualize_all_components(labels, shape):
    """Create colored visualization of all connected components"""
    colored = np.zeros((shape[0], shape[1], 3), dtype=np.uint8)
    num_labels = len(np.unique(labels))
    colors = np.random.randint(0, 255, size=(num_labels, 3))

    for i in range(1, num_labels):  # Skip background
        mask = labels == i
        colored[mask] = colors[i % len(colors)]

    return colored


def visualize_valid_components(labels, valid_components, shape):
    """Create visualization showing only valid components in green"""
    colored = np.zeros((shape[0], shape[1], 3), dtype=np.uint8)

    for i in valid_components:
        mask = labels == i
        colored[mask] = (0, 255, 0)  # Green for valid components

    return colored


def debug_size_distribution(roi_image, debug=True):
    """
    Analyze the size distribution of detected components to help tune parameters
    """
    roi_gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY) if len(roi_image.shape) > 2 else roi_image.copy()

    # Use inverted Otsu (assuming dark speckles on light background)
    _, binary = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Minimal morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # Get all components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)

    # Analyze size distribution
    areas = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels)]
    areas.sort()

    if debug and areas:
        print(f"Size distribution analysis:")
        print(f"  Total components: {len(areas)}")
        print(f"  Smallest: {min(areas)} pixels")
        print(f"  Largest: {max(areas)} pixels")
        print(f"  Mean: {np.mean(areas):.1f} pixels")
        print(f"  Median: {np.median(areas):.1f} pixels")
        print(f"  95th percentile: {np.percentile(areas, 95):.1f} pixels")

        # Show size ranges
        print(f"  Sizes 1-10: {sum(1 for a in areas if 1 <= a <= 10)} components")
        print(f"  Sizes 11-50: {sum(1 for a in areas if 11 <= a <= 50)} components")
        print(f"  Sizes 51-200: {sum(1 for a in areas if 51 <= a <= 200)} components")
        print(f"  Sizes 201-500: {sum(1 for a in areas if 201 <= a <= 500)} components")
        print(f"  Sizes 501+: {sum(1 for a in areas if a > 500)} components")

    return areas, stats, labels


def test_relaxed_detection(roi_image_path):
    """
    Test the relaxed detection parameters
    """
    roi_image = cv2.imread(roi_image_path, cv2.IMREAD_GRAYSCALE)

    if roi_image is None:
        print(f"Could not load image: {roi_image_path}")
        return

    print("Testing relaxed speckle detection...")

    # First, analyze size distribution
    print("\n=== Size Distribution Analysis ===")
    areas, stats, labels = debug_size_distribution(roi_image)

    # Test with different max_area values
    test_max_areas = [500, 1000, 2000, 5000]

    print(f"\n=== Testing Different Max Area Limits ===")
    for max_area in test_max_areas:
        results = analyze_roi_speckles_relaxed(roi_image, min_area=2, max_area=max_area, debug=False)
        print(f"Max area {max_area}: {results['valid_count']} speckles detected")

    # Run with debug enabled using a reasonable max_area
    suggested_max = int(np.percentile(areas, 95)) if areas else 2000
    print(f"\n=== Final Analysis (max_area={suggested_max}) ===")
    final_results = analyze_roi_speckles_relaxed(roi_image, min_area=2, max_area=suggested_max, debug=True)

    return final_results