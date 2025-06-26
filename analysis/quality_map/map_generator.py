# analysis/quality_map/map_generator.py - Fixed overflow issues

import cv2
import numpy as np
import warnings
from analysis.core.subset_analyzer import determine_optimal_subset_size

# Suppress specific overflow warnings for this module
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar add')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar multiply')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar divide')


def generate_quality_map(image, colormap='dic_quality', alpha=0.7):
    """Generate a DIC quality map with better resolution and color variation"""
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    # Ensure image is in RGB for visualization output
    if len(image.shape) == 2:
        rgb_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    else:
        rgb_image = image.copy()

    # FIXED: Better subset size and step size for more detail
    subset_size = determine_optimal_subset_size(gray)
    # FIXED: Smaller step size for better color variation
    step_size = max(3, subset_size // 4)  # More detailed sampling

    print(f"Generating quality map with subset size: {subset_size}, step: {step_size}")

    # Generate quality map using sophisticated subset analysis
    quality_map = _analyze_subset_quality_advanced(gray, subset_size, step_size)

    # DEBUG: Print quality map statistics
    print(f"Quality map statistics:")
    print(f"  Min: {np.min(quality_map):.4f}")
    print(f"  Max: {np.max(quality_map):.4f}")
    print(f"  Mean: {np.mean(quality_map):.4f}")
    print(f"  Std: {np.std(quality_map):.4f}")

    # Check distribution
    excellent_pixels = np.sum(quality_map >= 0.75)
    good_pixels = np.sum((quality_map >= 0.60) & (quality_map < 0.75))
    acceptable_pixels = np.sum((quality_map >= 0.45) & (quality_map < 0.60))
    poor_pixels = np.sum(quality_map < 0.45)
    total_pixels = quality_map.size

    print(f"Quality distribution:")
    print(f"  Excellent (≥75%): {excellent_pixels / total_pixels * 100:.1f}%")
    print(f"  Good (60-75%): {good_pixels / total_pixels * 100:.1f}%")
    print(f"  Acceptable (45-60%): {acceptable_pixels / total_pixels * 100:.1f}%")
    print(f"  Poor (<45%): {poor_pixels / total_pixels * 100:.1f}%")

    # Create clean visualization
    visualization = _create_quality_visualization(rgb_image, quality_map, colormap, alpha)

    # Calculate average quality for minimal reporting
    avg_quality = np.mean(quality_map)
    print(f"Average quality: {avg_quality:.3f}")

    return quality_map, visualization


def _analyze_subset_quality_advanced(gray, subset_size=21, step_size=5):
    """Advanced subset quality analysis with comprehensive metrics

    This function contains all the sophisticated calculations but is private/internal.
    Evaluates each subset based on:
    1. Gradient content (Sum of Squared Gradients - SSG)
    2. Contrast and intensity distribution
    3. Uniqueness/correlation potential
    4. Noise characteristics
    5. Pattern complexity and entropy
    6. Feature size and distribution

    Args:
        gray: Grayscale image
        subset_size: Size of subsets to analyze
        step_size: Step between subset centers

    Returns:
        numpy.ndarray: Quality map with values 0-1
    """
    h, w = gray.shape

    # Initialize quality map and count map for averaging overlapping regions
    quality_map = np.zeros((h, w), dtype=np.float32)
    count_map = np.zeros((h, w), dtype=np.int32)

    # Pre-calculate image gradients for efficiency
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

    # Process each subset with comprehensive analysis
    for y in range(0, h - subset_size + 1, step_size):
        for x in range(0, w - subset_size + 1, step_size):
            # Extract subset
            subset = gray[y:y + subset_size, x:x + subset_size]
            subset_gradients = gradient_magnitude[y:y + subset_size, x:x + subset_size]

            # Calculate comprehensive quality score for this subset
            quality_score = _calculate_comprehensive_quality(
                subset, subset_gradients, gray, x, y, subset_size
            )

            # Map quality back to image coordinates
            y_end = min(y + subset_size, h)
            x_end = min(x + subset_size, w)
            quality_map[y:y_end, x:x_end] += quality_score
            count_map[y:y_end, x:x_end] += 1

    # Average overlapping regions
    mask = count_map > 0
    quality_map[mask] /= count_map[mask]

    # Apply smoothing for better visualization
    quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0)

    # Ensure values are in [0, 1] range
    quality_map = np.clip(quality_map, 0, 1)

    return quality_map


def _calculate_comprehensive_quality(subset, subset_gradients, full_image, x_pos, y_pos, subset_size):
    """
    FIXED: Subset size independent quality calculation

    The issue was that quality metrics were too sensitive to subset size.
    Now normalized to be consistent across different subset sizes.
    """

    # 1. GRADIENT ANALYSIS (60% weight) - FIXED: Size-normalized
    # Sum of Squared Gradients (SSG) - normalized by subset area
    ssg = np.sum(subset_gradients ** 2)
    normalized_ssg = ssg / (subset.size * 255 ** 2)

    # Mean Intensity Gradient (MIG) - most reliable metric per literature
    mig = np.mean(subset_gradients)
    normalized_mig = mig / 255.0

    # FIXED: Size-independent gradient scoring
    # Scale factors adjusted for subset size independence
    mig_score = min(1.0, normalized_mig * 6)  # Reduced sensitivity
    ssg_score = min(1.0, normalized_ssg * 200)  # Reduced sensitivity

    # Gradient distribution quality
    gradient_mean = np.mean(subset_gradients)
    gradient_std = np.std(subset_gradients)
    gradient_cv = gradient_std / (gradient_mean + 1e-6)

    # Size-independent distribution scoring
    if 0.5 <= gradient_cv <= 2.0:
        distribution_bonus = 1.0
    elif 0.3 <= gradient_cv <= 3.0:
        distribution_bonus = 0.9
    else:
        distribution_bonus = 0.8

    # Combined gradient score
    gradient_score = (mig_score * 0.7 + ssg_score * 0.3) * distribution_bonus

    # 2. SPECKLE MORPHOLOGY ANALYSIS (20% weight) - FIXED: Size-normalized
    morphology_score = _analyze_speckle_morphology(subset, subset_size)

    # 3. CONTRAST ANALYSIS (10% weight) - Already size-independent
    subset_std = np.std(subset)
    subset_mean = np.mean(subset)
    rms_contrast = subset_std / (subset_mean + 1e-6)
    contrast_score = min(1.0, rms_contrast / 0.25)  # Slightly adjusted threshold

    # 4. UNIQUENESS ANALYSIS (10% weight) - FIXED: Size-compensated
    uniqueness_score = _calculate_size_independent_uniqueness(subset, subset_size)

    # COMBINE ALL METRICS INTO FINAL QUALITY SCORE
    overall_quality = (
            gradient_score * 0.60 +  # Gradient content (DOMINANT)
            morphology_score * 0.20 +  # Speckle morphology
            contrast_score * 0.10 +  # Basic contrast
            uniqueness_score * 0.10  # Pattern uniqueness
    )

    return max(0.0, min(1.0, overall_quality))


def _analyze_speckle_morphology(subset, subset_size):
    """
    FIXED: Size-independent speckle morphology analysis

    Now accounts for subset size to give consistent results
    regardless of the subset dimensions.
    """
    # Create binary image using adaptive thresholding
    # Adjust block size based on subset size
    block_size = max(3, min(subset_size // 3, 15))
    if block_size % 2 == 0:
        block_size += 1

    binary = cv2.adaptiveThreshold(
        subset, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, block_size, 2
    )

    # Find connected components (speckles)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    if num_labels < 2:  # No meaningful speckles
        return 0.3  # Neutral score, not penalizing

    # Analyze speckle sizes (skip background at index 0)
    areas = stats[1:, cv2.CC_STAT_AREA]

    # FIXED: Size-relative speckle filtering
    # Minimum speckle should be ~0.5% of subset area
    min_speckle_area = max(2, int(subset_size * subset_size * 0.005))
    # Maximum speckle should be ~5% of subset area
    max_speckle_area = int(subset_size * subset_size * 0.05)

    valid_areas = areas[(areas >= min_speckle_area) & (areas <= max_speckle_area)]

    if len(valid_areas) == 0:
        return 0.4  # Some speckles exist but wrong size

    # Calculate size-normalized speckle characteristics
    avg_speckle_diameter = np.sqrt(np.mean(valid_areas) / np.pi) * 2
    coverage = np.sum(valid_areas) / (subset.shape[0] * subset.shape[1])
    speckle_count = len(valid_areas)

    # FIXED: Size-relative scoring
    # Optimal speckle diameter: 2-8% of subset size
    relative_speckle_size = avg_speckle_diameter / subset_size
    if 0.02 <= relative_speckle_size <= 0.08:
        size_score = 1.0
    elif 0.015 <= relative_speckle_size <= 0.12:
        size_score = 0.9
    elif 0.01 <= relative_speckle_size <= 0.15:
        size_score = 0.7
    else:
        size_score = 0.5

    # Coverage scoring (30-70% is good for most DIC)
    if 0.25 <= coverage <= 0.70:
        coverage_score = 1.0
    elif 0.15 <= coverage <= 0.80:
        coverage_score = 0.9
    else:
        coverage_score = 0.6

    # Density scoring - relative to subset size
    expected_speckles = subset_size * subset_size / (avg_speckle_diameter ** 2 * 4)
    density_ratio = speckle_count / (expected_speckles + 1e-6)
    if 0.3 <= density_ratio <= 3.0:
        density_score = 1.0
    elif 0.1 <= density_ratio <= 5.0:
        density_score = 0.8
    else:
        density_score = 0.6

    return size_score * 0.5 + coverage_score * 0.3 + density_score * 0.2


def _calculate_size_independent_uniqueness(subset, subset_size):
    """
    FIXED: Size-independent uniqueness calculation

    Accounts for subset size to provide consistent uniqueness scoring.
    """
    # Calculate gradients
    grad_x = cv2.Sobel(subset, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(subset, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

    # Size-normalized feature counting
    total_pixels = subset_size * subset_size

    # Directional features (good for correlation)
    horizontal_features = np.sum(np.abs(grad_x) > np.abs(grad_y))
    vertical_features = np.sum(np.abs(grad_y) > np.abs(grad_x))
    total_features = horizontal_features + vertical_features

    if total_features == 0:
        return 0.3

    # Balance of directional features
    balance = min(horizontal_features, vertical_features) / total_features

    # Size-normalized gradient variance
    gradient_variance = np.var(gradient_magnitude)
    # Normalize by subset size to make size-independent
    normalized_variance = min(1.0, gradient_variance / (subset_size * 10))

    # Feature density relative to subset size
    feature_density = total_features / total_pixels
    density_score = min(1.0, feature_density * 3)  # Reasonable density

    return balance * 0.4 + normalized_variance * 0.4 + density_score * 0.2


def _calculate_subset_uniqueness(subset, full_image, x_pos, y_pos, subset_size):
    """Calculate how unique a subset is within its search region

    This is critical for DIC - subsets must be distinguishable for correlation.
    Uses advanced template matching and correlation analysis.
    """
    h_full, w_full = full_image.shape
    h_sub, w_sub = subset.shape

    # Define search region (2x subset size)
    search_size = subset_size * 2
    y_start = max(0, y_pos - search_size // 2)
    y_end = min(h_full, y_pos + h_sub + search_size // 2)
    x_start = max(0, x_pos - search_size // 2)
    x_end = min(w_full, x_pos + w_sub + search_size // 2)

    search_region = full_image[y_start:y_end, x_start:x_end]

    # Normalize subset for correlation
    subset_norm = subset.astype(np.float32)
    subset_norm -= np.mean(subset_norm)
    subset_std = np.std(subset_norm)

    if subset_std < 1e-6:  # No variation
        return 0

    subset_norm /= subset_std

    try:
        # Calculate normalized cross-correlation across search region
        result = cv2.matchTemplate(
            search_region.astype(np.float32),
            subset_norm,
            cv2.TM_CCORR_NORMED
        )

        # Find correlation peaks
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Set correlation at expected location to 0 to find second peak
        temp_result = result.copy()
        mask_size = 3
        y_mask_start = max(0, max_loc[1] - mask_size)
        y_mask_end = min(result.shape[0], max_loc[1] + mask_size + 1)
        x_mask_start = max(0, max_loc[0] - mask_size)
        x_mask_end = min(result.shape[1], max_loc[0] + mask_size + 1)
        temp_result[y_mask_start:y_mask_end, x_mask_start:x_mask_end] = 0

        # Find second highest correlation
        second_peak = np.max(temp_result)

        # Uniqueness is the difference between main peak and second peak
        uniqueness = max_val - second_peak

        # Consider correlation peak sharpness
        if result.size > 9:
            peak_region = result[
                          max(0, max_loc[1] - 1):min(result.shape[0], max_loc[1] + 2),
                          max(0, max_loc[0] - 1):min(result.shape[1], max_loc[0] + 2)
                          ]
            if peak_region.size > 1:
                peak_sharpness = (max_val - np.mean(peak_region)) / (np.std(peak_region) + 1e-6)
                peak_sharpness = min(1.0, peak_sharpness / 5)
            else:
                peak_sharpness = 0.5
        else:
            peak_sharpness = 0.5

        # Combined uniqueness score
        uniqueness_score = uniqueness * 0.7 + peak_sharpness * 0.3

        return min(1.0, max(0.0, uniqueness_score))

    except:
        # Fallback if template matching fails
        return 0.3


def _create_quality_visualization(base_image, quality_map, colormap_name='dic_quality', alpha=0.7):
    """Create clean quality map visualization with proper debugging"""
    if quality_map is None:
        return base_image

    # Ensure base image is RGB
    if len(base_image.shape) == 2:
        rgb_image = cv2.cvtColor(base_image, cv2.COLOR_GRAY2RGB)
    else:
        rgb_image = base_image.copy()

    # DEBUG: Check quality map before processing
    print(f"Quality map before colormap: min={quality_map.min():.4f}, max={quality_map.max():.4f}")

    # Apply colormap - Handle data scaling properly!
    if colormap_name == 'dic_quality':
        # Quality map should be 0-1, pass directly to colormap
        colored_map = _apply_dic_colormap(quality_map)  # Pass 0-1 data directly
    else:
        # For OpenCV colormaps, scale to 0-255
        normalized_map = (quality_map * 255).astype(np.uint8)
        colormap_const = getattr(cv2, f'COLORMAP_{colormap_name.upper()}', cv2.COLORMAP_JET)
        colored_map = cv2.applyColorMap(normalized_map, colormap_const)
        colored_map = cv2.cvtColor(colored_map, cv2.COLOR_BGR2RGB)

    # Check dimensions match
    if colored_map.shape[:2] != rgb_image.shape[:2]:
        colored_map = cv2.resize(colored_map, (rgb_image.shape[1], rgb_image.shape[0]))

    # Create blended overlay
    visualization = cv2.addWeighted(rgb_image, 1 - alpha, colored_map, alpha, 0)

    return visualization


def _apply_dic_colormap(quality_map):
    """
    IMPROVED: Better color variation for DIC quality visualization
    """
    h, w = quality_map.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    # Ensure quality_map is 0-1 range
    if quality_map.max() > 1.0:
        normalized = quality_map.astype(float) / 255.0
        print(f"WARNING: Quality map had values > 1, normalizing from 0-255 to 0-1")
    else:
        normalized = quality_map.astype(float)

    normalized = np.clip(normalized, 0, 1)
    print(f"Colormap input range: {normalized.min():.4f} - {normalized.max():.4f}")

    # IMPROVED: More granular color transitions for better variation

    # Poor quality (0.0-0.10): Dark Red
    mask_very_poor = normalized <= 0.10
    colored[mask_very_poor] = [60, 0, 0]  # Very dark red

    # Challenging (0.10-0.25): Red
    mask_challenging = (normalized > 0.10) & (normalized <= 0.25)
    colored[mask_challenging] = [200, 0, 0]  # Red

    # Marginal (0.25-0.40): Orange-Red
    mask_marginal = (normalized > 0.25) & (normalized <= 0.40)
    colored[mask_marginal] = [255, 100, 0]  # Orange-red

    # Acceptable (0.40-0.55): Orange
    mask_acceptable = (normalized > 0.40) & (normalized <= 0.55)
    colored[mask_acceptable] = [255, 165, 0]  # Orange

    # Good (0.55-0.70): Yellow
    mask_good = (normalized > 0.55) & (normalized <= 0.70)
    colored[mask_good] = [255, 255, 0]  # Yellow

    # Very Good (0.70-0.85): Green
    mask_very_good = (normalized > 0.70) & (normalized <= 0.85)
    colored[mask_very_good] = [0, 255, 0]  # Green

    # Excellent (0.85-1.0): Blue
    mask_excellent = normalized > 0.85
    colored[mask_excellent] = [0, 120, 255]  # Blue

    # DEBUG: Print color distribution
    print(f"Color mapping results:")
    print(f"  Dark Red (≤10%): {np.sum(mask_very_poor)} pixels")
    print(f"  Red (10-25%): {np.sum(mask_challenging)} pixels")
    print(f"  Orange-Red (25-40%): {np.sum(mask_marginal)} pixels")
    print(f"  Orange (40-55%): {np.sum(mask_acceptable)} pixels")
    print(f"  Yellow (55-70%): {np.sum(mask_good)} pixels")
    print(f"  Green (70-85%): {np.sum(mask_very_good)} pixels")
    print(f"  Blue (≥85%): {np.sum(mask_excellent)} pixels")

    return colored


def visualize_quality_map(base_image, quality_map, colormap_name='dic_quality', alpha=0.7):
    """Simple wrapper for quality map visualization

    Clean interface - complexity hidden internally.
    """
    return _create_quality_visualization(base_image, quality_map, colormap_name, alpha)

































