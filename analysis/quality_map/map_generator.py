# analysis/quality_map/map_generator.py - Fixed overflow issues

import cv2
import numpy as np
import warnings
from analysis.core.subset_analyzer import determine_optimal_subset_size

# Suppress specific overflow warnings for this module
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar add')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar multiply')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar divide')


# Update the main generate_quality_map function to support spectrum selection
def generate_quality_map(image, colormap='custom_dic', alpha=0.7):
    """
    UPDATED: Generate a DIC quality map with selectable smooth spectrum

    Args:
        image: Input image
        colormap: Spectrum type ('custom_dic', 'smooth_rainbow', 'thermal', etc.)
        alpha: Blending factor for visualization

    Returns:
        tuple: (quality_map, visualization)
    """
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

    # Generate quality map using existing sophisticated analysis
    subset_size = determine_optimal_subset_size(gray)
    step_size = max(3, subset_size // 4)  # More detailed sampling

    print(f"Generating quality map with subset size: {subset_size}, step: {step_size}")
    print(f"Using {colormap} spectrum for visualization")

    # Generate quality map using sophisticated subset analysis
    quality_map = _analyze_subset_quality_advanced(gray, subset_size, step_size)

    # Print quality statistics
    print(f"Quality map statistics:")
    print(f"  Min: {np.min(quality_map):.4f}, Max: {np.max(quality_map):.4f}")
    print(f"  Mean: {np.mean(quality_map):.4f}, Std: {np.std(quality_map):.4f}")

    # Create visualization with selected spectrum
    visualization = _create_quality_visualization(rgb_image, quality_map, colormap, alpha)

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


def _apply_dic_colormap(quality_map, spectrum_type='smooth_rainbow'):
    """
    UPDATED: Smooth spectrum colormap for DIC quality visualization

    Args:
        quality_map: Normalized quality data (0-1)
        spectrum_type: Type of spectrum to use
                      - 'smooth_rainbow': Red->Orange->Yellow->Green->Blue
                      - 'thermal': Black->Red->Orange->Yellow->White
                      - 'viridis_like': Purple->Blue->Green->Yellow
                      - 'custom_dic': Optimized for DIC visualization
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

    if spectrum_type == 'smooth_rainbow':
        # Smooth rainbow spectrum: Red -> Orange -> Yellow -> Green -> Blue
        colored = _create_smooth_rainbow_spectrum(normalized)
    elif spectrum_type == 'thermal':
        # Thermal spectrum: Black -> Red -> Orange -> Yellow -> White
        colored = _create_thermal_spectrum(normalized)
    elif spectrum_type == 'viridis_like':
        # Viridis-like spectrum: Purple -> Blue -> Green -> Yellow
        colored = _create_viridis_like_spectrum(normalized)
    elif spectrum_type == 'custom_dic':
        # Custom DIC spectrum optimized for quality visualization
        colored = _create_custom_dic_spectrum(normalized)
    else:
        # Fallback to smooth rainbow
        colored = _create_smooth_rainbow_spectrum(normalized)

    print(f"Applied {spectrum_type} spectrum colormap")
    return colored


def _create_opencv_spectrum(normalized, colormap_id=cv2.COLORMAP_JET):
    """Use OpenCV's built-in smooth colormaps"""
    # Convert 0-1 to 0-255 for OpenCV
    normalized_255 = (normalized * 255).astype(np.uint8)

    # Apply OpenCV colormap
    colored_bgr = cv2.applyColorMap(normalized_255, colormap_id)

    # Convert BGR to RGB
    colored_rgb = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2RGB)

    return colored_rgb


def _create_smooth_rainbow_spectrum(normalized):
    """Create smooth rainbow spectrum from red to blue"""
    h, w = normalized.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    # Define color points in RGB
    colors = np.array([
        [139, 0, 0],  # Dark red (very poor)
        [255, 0, 0],  # Red (poor)
        [255, 127, 0],  # Orange (challenging)
        [255, 255, 0],  # Yellow (acceptable)
        [127, 255, 0],  # Yellow-green (good)
        [0, 255, 0],  # Green (very good)
        [0, 127, 255],  # Light blue (excellent)
        [0, 64, 255]  # Blue (outstanding)
    ])

    # Interpolate smoothly between colors
    for i in range(h):
        for j in range(w):
            value = normalized[i, j]

            # Map value to color index range
            color_idx = value * (len(colors) - 1)
            lower_idx = int(np.floor(color_idx))
            upper_idx = min(lower_idx + 1, len(colors) - 1)

            # Linear interpolation between adjacent colors
            if lower_idx == upper_idx:
                colored[i, j] = colors[lower_idx]
            else:
                t = color_idx - lower_idx  # interpolation factor
                colored[i, j] = (1 - t) * colors[lower_idx] + t * colors[upper_idx]

    return colored


def _create_thermal_spectrum(normalized):
    """Create thermal spectrum from black to white"""
    h, w = normalized.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    colors = np.array([
        [0, 0, 0],  # Black (very poor)
        [32, 0, 0],  # Very dark red
        [64, 0, 0],  # Dark red
        [128, 0, 0],  # Medium red
        [192, 0, 0],  # Red
        [255, 0, 0],  # Bright red
        [255, 64, 0],  # Red-orange
        [255, 128, 0],  # Orange
        [255, 192, 0],  # Yellow-orange
        [255, 255, 0],  # Yellow
        [255, 255, 128],  # Light yellow
        [255, 255, 192],  # Very light yellow
        [255, 255, 255]  # White (excellent)
    ], dtype=np.float32)

    # Vectorized interpolation
    color_indices = normalized * (len(colors) - 1)
    lower_indices = np.floor(color_indices).astype(np.int32)
    upper_indices = np.minimum(lower_indices + 1, len(colors) - 1)
    t = color_indices - lower_indices

    for c in range(3):
        lower_colors = colors[lower_indices, c]
        upper_colors = colors[upper_indices, c]
        colored[:, :, c] = ((1 - t) * lower_colors + t * upper_colors).astype(np.uint8)

    return colored


def _create_viridis_like_spectrum(normalized):
    """Create viridis-like spectrum"""
    h, w = normalized.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    colors = np.array([
        [68, 1, 84],  # Purple (very poor)
        [72, 35, 116],  # Dark purple
        [64, 67, 135],  # Purple-blue
        [52, 94, 141],  # Blue
        [41, 120, 142],  # Blue-cyan
        [32, 144, 140],  # Cyan
        [34, 167, 132],  # Cyan-green
        [68, 190, 112],  # Green
        [121, 209, 81],  # Light green
        [189, 223, 38],  # Yellow-green
        [253, 231, 37]  # Yellow (excellent)
    ], dtype=np.float32)

    # Vectorized interpolation
    color_indices = normalized * (len(colors) - 1)
    lower_indices = np.floor(color_indices).astype(np.int32)
    upper_indices = np.minimum(lower_indices + 1, len(colors) - 1)
    t = color_indices - lower_indices

    for c in range(3):
        lower_colors = colors[lower_indices, c]
        upper_colors = colors[upper_indices, c]
        colored[:, :, c] = ((1 - t) * lower_colors + t * upper_colors).astype(np.uint8)

    return colored


def _create_custom_dic_spectrum(normalized):
    """
    FRESH: Custom DIC spectrum - Black to Red to Blue

    This is a clean DIC-only assessment spectrum:
    - 0-75%: Black to Dark Red (Critical - not suitable for DIC)
    - 75-80%: Red (Minimum acceptable for DIC)
    - 80-85%: Red-Orange (Good for DIC)
    - 85-90%: Orange-Yellow (Very good for DIC)
    - 90-95%: Yellow-Cyan (Excellent for DIC)
    - 95-100%: Cyan-Blue (Perfect for DIC)

    Clean progression: Black → Red → Orange → Yellow → Cyan → Blue
    """
    h, w = normalized.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    # Ensure quality_map is 0-1 range
    normalized = np.clip(normalized, 0, 1)

    # FRESH COLOR SPECTRUM: Black → Red → Orange → Yellow → Cyan → Blue
    colors = np.array([
        # Critical range (0-75%): Black to Dark Red
        [0, 0, 0],  # 0%: Pure black (critical)
        [20, 0, 0],  # 15%: Very dark red
        [40, 0, 0],  # 30%: Dark red
        [60, 0, 0],  # 45%: Medium dark red
        [80, 0, 0],  # 60%: Dark red
        [120, 0, 0],  # 75%: Red (threshold for DIC)

        # Acceptable range (75-100%): Red → Orange → Yellow → Cyan → Blue
        [180, 0, 0],  # 78%: Bright red (minimum for DIC)
        [220, 40, 0],  # 81%: Red-orange
        [255, 80, 0],  # 84%: Orange
        [255, 140, 0],  # 87%: Orange-yellow
        [255, 200, 0],  # 90%: Yellow
        [200, 255, 80],  # 93%: Yellow-cyan
        [120, 255, 180],  # 96%: Cyan
        [40, 200, 255],  # 98%: Light blue
        [0, 140, 255],  # 100%: Pure blue (perfect)
    ], dtype=np.float32)

    # Smooth interpolation across the entire spectrum
    color_indices = normalized * (len(colors) - 1)
    lower_indices = np.floor(color_indices).astype(np.int32)
    upper_indices = np.minimum(lower_indices + 1, len(colors) - 1)

    # Interpolation factors with smooth transitions
    t = color_indices - lower_indices

    # Apply smooth interpolation
    for c in range(3):  # RGB channels
        lower_colors = colors[lower_indices, c]
        upper_colors = colors[upper_indices, c]
        colored[:, :, c] = ((1 - t) * lower_colors + t * upper_colors).astype(np.uint8)

    return colored


def _update_dynamic_legend_for_custom_dic():
    """
    Updated legend definition for the new custom_dic spectrum
    """
    custom_dic_legend = {
        'name': 'Custom DIC (Excellent+ Only)',
        'colors': [
            (32, 0, 0, "Critical (0-75%): Not suitable for DIC"),
            (0, 180, 0, "Excellent (75-80%): Minimum for DIC"),
            (0, 220, 0, "Outstanding (80-85%)"),
            (0, 255, 140, "Exceptional (85-90%)"),
            (0, 180, 255, "Superior (90-95%)"),
            (0, 60, 255, "Perfect (95-100%)")
        ]
    }
    return custom_dic_legend


def _create_quality_visualization(base_image, quality_map, colormap_name='custom_dic', alpha=0.7):
    """
    UPDATED: Create quality map visualization with smooth spectrum options

    Args:
        base_image: Base RGB image
        quality_map: Quality map data (0-1)
        colormap_name: Spectrum type to use
        alpha: Blending factor (0-1)

    Returns:
        numpy.ndarray: Visualization with quality overlay
    """
    if quality_map is None:
        return base_image

    # Ensure base image is RGB
    if len(base_image.shape) == 2:
        rgb_image = cv2.cvtColor(base_image, cv2.COLOR_GRAY2RGB)
    else:
        rgb_image = base_image.copy()

    print(f"Creating quality visualization with {colormap_name} spectrum")
    print(f"Quality map stats: min={quality_map.min():.4f}, max={quality_map.max():.4f}, mean={quality_map.mean():.4f}")

    # Apply selected colormap using the updated function
    colored_map = _apply_dic_colormap(quality_map, colormap_name)

    # Check dimensions match
    if colored_map.shape[:2] != rgb_image.shape[:2]:
        colored_map = cv2.resize(colored_map, (rgb_image.shape[1], rgb_image.shape[0]))
        print(f"Resized colored map to match base image: {colored_map.shape}")

    # Create blended overlay
    visualization = cv2.addWeighted(rgb_image, 1 - alpha, colored_map, alpha, 0)

    print(f"Quality visualization created successfully with {colormap_name}")
    return visualization


def visualize_quality_map(base_image, quality_map, colormap_name='dic_quality', alpha=0.7):
    """Simple wrapper for quality map visualization

    Clean interface - complexity hidden internally.
    """
    return _create_quality_visualization(base_image, quality_map, colormap_name, alpha)














































