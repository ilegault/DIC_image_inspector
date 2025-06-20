import cv2
import numpy as np
from pathlib import Path


def analyze_roi_for_dic_quality(roi_image, debug=False):
    """
    Speckle detection specifically optimized for DIC quality assessment
    Focuses on capturing ALL meaningful speckles, including large ones
    """
    # Create a copy to avoid modifying original
    roi_gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY) if len(roi_image.shape) > 2 else roi_image.copy()
    roi_area = roi_gray.shape[0] * roi_gray.shape[1]

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
    normal_results = process_for_dic_quality(binary_normal, roi_area, debug, "normal")
    inverted_results = process_for_dic_quality(binary_inverted, roi_area, debug, "inverted")

    # Choose based on total speckle coverage (area), not just count
    # For DIC, we want good coverage including large speckles
    if normal_results['total_speckle_area'] >= inverted_results['total_speckle_area']:
        chosen_results = normal_results
        binary_chosen = binary_normal
        method = "normal"
    else:
        chosen_results = inverted_results
        binary_chosen = binary_inverted
        method = "inverted"

    chosen_results['method'] = method
    chosen_results['roi_area'] = roi_area

    # Calculate DIC quality metrics
    chosen_results.update(calculate_dic_quality_metrics(chosen_results, roi_area))

    if debug:
        cv2.imwrite("debug_roi/03_chosen_binary.png", binary_chosen)

        # Visualize speckles by size category
        size_vis = visualize_speckles_by_size(chosen_results['labels'],
                                              chosen_results['valid_components'],
                                              chosen_results['stats'],
                                              roi_gray.shape)
        cv2.imwrite("debug_roi/04_speckles_by_size.png", size_vis)

        # Create quality assessment visualization
        quality_vis = create_dic_quality_visualization(roi_gray, chosen_results)
        cv2.imwrite("debug_roi/05_dic_quality_assessment.png", quality_vis)

        print_dic_quality_report(chosen_results)

    return chosen_results


def process_for_dic_quality(binary, roi_area, debug=False, method_name=""):
    """
    Process binary image with DIC quality in mind - preserve large speckles
    """
    # Very minimal morphological cleanup - only remove single pixels
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    if debug:
        cv2.imwrite(f"debug_roi/morph_clean_{method_name}.png", cleaned)

    # Connected components analysis
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)

    # DIC-focused filtering: very permissive size limits
    min_area = 2  # Remove only tiny noise
    max_area = roi_area // 4  # Allow up to 25% of ROI area (very large speckles)

    valid_components = []
    for i in range(1, num_labels):  # Skip background (index 0)
        area = stats[i, cv2.CC_STAT_AREA]

        # For DIC, we want almost all speckles except obvious noise or full ROI
        if min_area <= area <= max_area:
            valid_components.append(i)

    # Calculate comprehensive statistics
    areas = [stats[i, cv2.CC_STAT_AREA] for i in valid_components]
    total_speckle_area = sum(areas) if areas else 0
    avg_size = np.mean(areas) if areas else 0
    speckle_ratio = total_speckle_area / roi_area if roi_area > 0 else 0

    return {
        'total_components': num_labels - 1,
        'valid_components': valid_components,
        'valid_count': len(valid_components),
        'labels': labels,
        'stats': stats,
        'centroids': centroids,
        'areas': areas,
        'total_speckle_area': total_speckle_area,
        'avg_speckle_size': avg_size,
        'speckle_ratio': speckle_ratio,
        'min_area_threshold': min_area,
        'max_area_threshold': max_area
    }


def calculate_dic_quality_metrics(results, roi_area):
    """
    Calculate DIC-specific quality metrics
    """
    areas = results['areas']

    if not areas:
        return {
            'dic_quality_score': 0.0,
            'size_diversity': 0.0,
            'coverage_quality': 0.0,
            'large_speckle_count': 0,
            'medium_speckle_count': 0,
            'small_speckle_count': 0,
            'speckle_density': 0.0
        }

    # Categorize speckles by size for DIC analysis
    small_threshold = 50
    large_threshold = 500

    small_speckles = [a for a in areas if a < small_threshold]
    medium_speckles = [a for a in areas if small_threshold <= a < large_threshold]
    large_speckles = [a for a in areas if a >= large_threshold]

    # Size diversity (good for DIC to have varied speckle sizes)
    size_std = np.std(areas) if len(areas) > 1 else 0
    size_mean = np.mean(areas)
    size_diversity = min(1.0, size_std / size_mean) if size_mean > 0 else 0

    # Coverage quality (total area covered)
    coverage_ratio = sum(areas) / roi_area
    coverage_quality = min(1.0, coverage_ratio / 0.3)  # Target ~30% coverage

    # Speckle density (speckles per unit area)
    speckle_density = len(areas) / roi_area * 10000  # Per 10k pixels

    # Overall DIC quality score
    density_score = min(1.0, speckle_density / 5.0)  # Target ~5 speckles per 10k pixels
    size_balance_score = min(1.0, len(large_speckles) / max(1, len(areas)))  # Want some large speckles

    dic_quality_score = (coverage_quality * 0.4 +
                         density_score * 0.3 +
                         size_diversity * 0.2 +
                         size_balance_score * 0.1)

    return {
        'dic_quality_score': dic_quality_score,
        'size_diversity': size_diversity,
        'coverage_quality': coverage_quality,
        'large_speckle_count': len(large_speckles),
        'medium_speckle_count': len(medium_speckles),
        'small_speckle_count': len(small_speckles),
        'speckle_density': speckle_density
    }


def visualize_speckles_by_size(labels, valid_components, stats, shape):
    """
    Create visualization showing speckles colored by size category
    """
    colored = np.zeros((shape[0], shape[1], 3), dtype=np.uint8)

    for i in valid_components:
        area = stats[i, cv2.CC_STAT_AREA]
        mask = labels == i

        if area < 50:
            colored[mask] = (255, 255, 0)  # Cyan for small
        elif area < 500:
            colored[mask] = (0, 255, 0)  # Green for medium
        else:
            colored[mask] = (0, 0, 255)  # Red for large

    return colored


def create_dic_quality_visualization(roi_gray, results):
    """
    Create a comprehensive DIC quality visualization
    """
    # Create RGB version
    vis = cv2.cvtColor(roi_gray, cv2.COLOR_GRAY2BGR)

    # Draw speckle centroids with size-based markers
    for i in results['valid_components']:
        area = results['stats'][i, cv2.CC_STAT_AREA]
        x = int(results['centroids'][i][0])
        y = int(results['centroids'][i][1])

        if area < 50:
            cv2.circle(vis, (x, y), 1, (255, 255, 0), -1)  # Small: cyan dot
        elif area < 500:
            cv2.circle(vis, (x, y), 2, (0, 255, 0), -1)  # Medium: green dot
        else:
            cv2.circle(vis, (x, y), 4, (0, 0, 255), -1)  # Large: red dot

    # Add quality score text
    quality_text = f"DIC Quality: {results['dic_quality_score']:.3f}"
    cv2.putText(vis, quality_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    coverage_text = f"Coverage: {results['speckle_ratio']:.3f}"
    cv2.putText(vis, coverage_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    return vis


def print_dic_quality_report(results):
    """
    Print detailed DIC quality assessment
    """
    print(f"\n=== DIC QUALITY ASSESSMENT ===")
    print(f"Detection method: {results['method']}")
    print(f"Total speckles detected: {results['valid_count']}")
    print(f"Area thresholds: {results['min_area_threshold']} - {results['max_area_threshold']} pixels")
    print(f"Total components before filtering: {results['total_components']}")

    print(f"\nSPECKLE SIZE DISTRIBUTION:")
    print(f"  Small speckles (<50px): {results['small_speckle_count']}")
    print(f"  Medium speckles (50-500px): {results['medium_speckle_count']}")
    print(f"  Large speckles (>500px): {results['large_speckle_count']}")

    print(f"\nDIC QUALITY METRICS:")
    print(f"  Overall DIC Quality Score: {results['dic_quality_score']:.3f} (0-1, higher is better)")
    print(f"  Speckle Coverage Ratio: {results['speckle_ratio']:.3f}")
    print(f"  Speckle Density: {results['speckle_density']:.2f} per 10k pixels")
    print(f"  Size Diversity: {results['size_diversity']:.3f}")
    print(f"  Coverage Quality: {results['coverage_quality']:.3f}")

    # Provide DIC quality interpretation
    if results['dic_quality_score'] > 0.7:
        quality_rating = "EXCELLENT"
    elif results['dic_quality_score'] > 0.5:
        quality_rating = "GOOD"
    elif results['dic_quality_score'] > 0.3:
        quality_rating = "FAIR"
    else:
        quality_rating = "POOR"

    print(f"\nDIC SUITABILITY: {quality_rating}")

    # Provide recommendations
    print(f"\nRECOMMENDATIONS:")
    if results['speckle_ratio'] < 0.2:
        print("  - Consider increasing speckle density for better DIC correlation")
    if results['large_speckle_count'] < 5:
        print("  - Consider adding larger speckles for coarse displacement tracking")
    if results['speckle_density'] < 3:
        print("  - Speckle density may be too low for robust DIC analysis")
    if results['dic_quality_score'] > 0.6:
        print("  - Speckle pattern appears suitable for DIC analysis")


def compare_dic_quality(roi_image_path):
    """
    Compare DIC quality assessment with different approaches
    """
    roi_image = cv2.imread(roi_image_path, cv2.IMREAD_GRAYSCALE)

    if roi_image is None:
        print(f"Could not load image: {roi_image_path}")
        return

    print("COMPARING DIC QUALITY ASSESSMENT METHODS")
    print("=" * 50)

    # Method 1: Original restrictive approach
    print("\n1. ORIGINAL RESTRICTIVE METHOD (max_area=500):")
    _, binary = cv2.threshold(roi_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    restrictive_results = process_for_dic_quality_restricted(binary, roi_image.shape[0] * roi_image.shape[1])

    # Method 2: DIC-optimized approach
    print("\n2. DIC-OPTIMIZED METHOD:")
    dic_results = analyze_roi_for_dic_quality(roi_image, debug=True)

    # Comparison
    print(f"\n=== COMPARISON ===")
    print(f"Restrictive method: {restrictive_results['valid_count']} speckles")
    print(f"DIC-optimized method: {dic_results['valid_count']} speckles")
    print(f"Improvement: +{dic_results['valid_count'] - restrictive_results['valid_count']} speckles")
    print(
        f"Large speckles captured: {dic_results['large_speckle_count']} (vs {restrictive_results.get('large_speckle_count', 0)})")

    return dic_results


def process_for_dic_quality_restricted(binary, roi_area):
    """
    Process with the original restrictive parameters for comparison
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)

    # Original restrictive filtering
    valid_components = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if 1 <= area <= 500:  # Your original limits
            valid_components.append(i)

    areas = [stats[i, cv2.CC_STAT_AREA] for i in valid_components]
    large_speckles = [a for a in areas if a >= 500]

    return {
        'valid_count': len(valid_components),
        'large_speckle_count': len(large_speckles),
        'total_area': sum(areas) if areas else 0
    }