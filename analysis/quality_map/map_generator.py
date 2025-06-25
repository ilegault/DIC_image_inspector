# analysis/quality_map/map_generator.py - Fixed overflow issues

import cv2
import numpy as np
import warnings
from scipy.signal import correlate2d
from scipy.stats import entropy
from analysis.core.subset_analyzer import determine_optimal_subset_size

# Suppress specific overflow warnings for this module
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar add')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar multiply')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar divide')


def generate_quality_map(image, colormap='dic_quality', alpha=0.7):
    """Generate a DIC quality map and visualization of the input image

    Uses sophisticated quality calculations internally but presents a clean interface.
    All complex metrics are calculated for accurate quality assessment but hidden from user.

    Args:
        image: Input image (numpy array)
        colormap: Colormap to use for visualization ('dic_quality', 'jet', 'viridis', etc.)
        alpha: Blending factor for overlay (0.0-1.0)

    Returns:
        tuple: (quality_map, visualization) where:
            - quality_map is the raw quality data (0-1 float values)
            - visualization is the RGB visualization ready for display
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

    # Determine optimal subset size for DIC analysis
    subset_size = determine_optimal_subset_size(gray)
    step_size = max(5, subset_size // 3)  # Good sampling density

    print(f"Generating quality map with subset size: {subset_size}, step: {step_size}")

    # Generate quality map using sophisticated subset analysis (internal complexity)
    quality_map = _analyze_subset_quality_advanced(gray, subset_size, step_size)

    # Create clean visualization (simple output)
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
    """Calculate comprehensive quality score for a single subset

    This implements sophisticated DIC quality metrics internally:
    1. Gradient content analysis (SSG, distribution)
    2. Contrast measures (multiple types)
    3. Uniqueness evaluation (correlation potential)
    4. Noise level assessment
    5. Pattern complexity (entropy, texture)
    6. Feature characteristics

    All complexity is hidden - just returns a single quality score.
    """

    # 1. GRADIENT ANALYSIS (35% weight) - Most critical for DIC
    # Sum of Squared Gradients (SSG) - key DIC metric
    ssg = np.sum(subset_gradients ** 2)
    normalized_ssg = ssg / (subset.size * 255 ** 2)

    # Gradient distribution quality
    gradient_mean = np.mean(subset_gradients)
    gradient_std = np.std(subset_gradients)
    gradient_cv = gradient_std / (gradient_mean + 1e-6)

    # Gradient score combines magnitude and distribution
    if normalized_ssg < 0.001:
        gradient_score = 0
    elif normalized_ssg > 0.1:
        gradient_score = 1.0
    else:
        gradient_score = np.log10(normalized_ssg * 1000) / 2

    # Penalize poor gradient distribution
    if gradient_cv < 0.5:  # Too uniform
        gradient_score *= 0.8
    elif gradient_cv > 2.5:  # Too chaotic
        gradient_score *= 0.7

    # 2. CONTRAST ANALYSIS (20% weight)
    subset_std = np.std(subset)
    subset_mean = np.mean(subset)

    # Convert to float to prevent overflow and use numpy functions
    subset_float = subset.astype(np.float64)
    min_val = np.min(subset_float)
    max_val = np.max(subset_float)

    # Multiple contrast measures with overflow protection
    rms_contrast = subset_std / (subset_mean + 1e-6)

    # Robust Michelson contrast calculation using numpy operations
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        if np.isclose(max_val, min_val, atol=1e-10):
            michelson_contrast = 0.0
        else:
            # Calculate using numpy operations with proper handling
            numerator = max_val - min_val
            denominator = max_val + min_val

            if denominator > 1e-10 and np.isfinite(denominator):
                michelson_contrast = numerator / denominator
            else:
                michelson_contrast = 0.0

    # Ensure michelson_contrast is valid and within bounds
    if not np.isfinite(michelson_contrast):
        michelson_contrast = 0.0
    michelson_contrast = np.clip(michelson_contrast, 0.0, 1.0)

    # Combined contrast score
    contrast_score = min(1.0, rms_contrast / 0.4) * 0.7 + min(1.0, michelson_contrast) * 0.3

    # 3. UNIQUENESS ANALYSIS (25% weight) - Critical for DIC correlation
    uniqueness_score = _calculate_subset_uniqueness(subset, full_image, x_pos, y_pos, subset_size)

    # 4. PATTERN COMPLEXITY (10% weight)
    # Entropy analysis
    hist, _ = np.histogram(subset, bins=32, range=(0, 256), density=True)
    pattern_entropy = entropy(hist[hist > 0]) if np.any(hist > 0) else 0
    entropy_score = min(1.0, pattern_entropy / 4.0)  # Normalize

    # Local texture analysis
    if subset.shape[0] > 5 and subset.shape[1] > 5:
        # Calculate local binary pattern-like features
        center = subset[1:-1, 1:-1]
        neighbors = [
            subset[:-2, :-2], subset[:-2, 1:-1], subset[:-2, 2:],
            subset[1:-1, :-2], subset[1:-1, 2:],
            subset[2:, :-2], subset[2:, 1:-1], subset[2:, 2:]
        ]

        # Count texture variations
        texture_variations = 0
        for neighbor in neighbors:
            texture_variations += np.sum(neighbor != center)

        texture_score = min(1.0, texture_variations / (center.size * 4))
    else:
        texture_score = 0.5

    complexity_score = entropy_score * 0.6 + texture_score * 0.4

    # 5. NOISE ASSESSMENT (10% weight)
    # Estimate noise using median filtering
    if subset.shape[0] > 3 and subset.shape[1] > 3:
        median_filtered = cv2.medianBlur(subset, 3)
        noise = subset.astype(float) - median_filtered.astype(float)
        noise_std = np.std(noise)
        signal_std = np.std(median_filtered)
        snr = signal_std / (noise_std + 1e-6)
        noise_score = min(1.0, snr / 25.0)  # Good SNR > 25
    else:
        noise_score = 0.5

    # COMBINE ALL METRICS INTO FINAL QUALITY SCORE
    overall_quality = (
            gradient_score * 0.35 +  # Gradient content
            contrast_score * 0.20 +  # Contrast quality
            uniqueness_score * 0.25 +  # Correlation potential
            complexity_score * 0.10 +  # Pattern complexity
            noise_score * 0.10  # Noise level
    )

    return max(0.0, min(1.0, overall_quality))


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
    """Create clean quality map visualization

    Simple interface despite complex calculations behind the scenes.
    """
    if quality_map is None:
        return base_image

    # Ensure base image is RGB
    if len(base_image.shape) == 2:
        rgb_image = cv2.cvtColor(base_image, cv2.COLOR_GRAY2RGB)
    else:
        rgb_image = base_image.copy()

    # Scale quality map to 0-255 for visualization
    normalized_map = (quality_map * 255).astype(np.uint8)

    # Apply colormap
    if colormap_name == 'dic_quality':
        colored_map = _apply_dic_colormap(normalized_map)
    else:
        # Use OpenCV colormap
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
    """Apply professional DIC-style colormap

    Red (poor) -> Orange (marginal) -> Yellow (acceptable) -> Green (good) -> Blue (excellent)
    """
    h, w = quality_map.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    # Normalize to 0-1
    normalized = quality_map.astype(float) / 255.0

    # Define quality-based color transitions
    # Poor quality (0.0-0.2): Dark Red to Red
    mask_very_poor = normalized <= 0.2
    colored[mask_very_poor] = [128, 0, 0]  # Dark red

    # Poor to marginal (0.2-0.4): Red to Orange
    mask_poor = (normalized > 0.2) & (normalized <= 0.4)
    if np.any(mask_poor):
        transition = np.clip((normalized[mask_poor] - 0.2) / 0.2, 0, 1)
        colored[mask_poor, 0] = np.clip(128 + transition * 127, 0, 255).astype(np.uint8)  # Red increases
        colored[mask_poor, 1] = np.clip(transition * 165, 0, 255).astype(np.uint8)  # Orange component
        colored[mask_poor, 2] = 0

    # Marginal to acceptable (0.4-0.6): Orange to Yellow
    mask_marginal = (normalized > 0.4) & (normalized <= 0.6)
    if np.any(mask_marginal):
        transition = np.clip((normalized[mask_marginal] - 0.4) / 0.2, 0, 1)
        colored[mask_marginal, 0] = 255  # Red stays high
        colored[mask_marginal, 1] = np.clip(165 + transition * 90, 0, 255).astype(np.uint8)  # Green increases
        colored[mask_marginal, 2] = 0

    # Acceptable to good (0.6-0.8): Yellow to Green
    mask_acceptable = (normalized > 0.6) & (normalized <= 0.8)
    if np.any(mask_acceptable):
        transition = np.clip((normalized[mask_acceptable] - 0.6) / 0.2, 0, 1)
        colored[mask_acceptable, 0] = np.clip(255 * (1 - transition), 0, 255).astype(np.uint8)  # Red decreases
        colored[mask_acceptable, 1] = 255  # Green at max
        colored[mask_acceptable, 2] = 0

    # Good to excellent (0.8-1.0): Green to Blue
    mask_good = normalized > 0.8
    if np.any(mask_good):
        transition = np.clip((normalized[mask_good] - 0.8) / 0.2, 0, 1)  # Ensure 0-1 range
        colored[mask_good, 0] = 0
        colored[mask_good, 1] = np.clip(255 * (1 - transition), 0, 255).astype(np.uint8)  # Green decreases
        colored[mask_good, 2] = np.clip(transition * 255, 0, 255).astype(np.uint8)  # Blue increases

    return colored


def visualize_quality_map(base_image, quality_map, colormap_name='dic_quality', alpha=0.7):
    """Simple wrapper for quality map visualization

    Clean interface - complexity hidden internally.
    """
    return _create_quality_visualization(base_image, quality_map, colormap_name, alpha)


def create_quality_map_visualization(original_image, quality_map_data, roi_coords=None):
    """Create quality map visualization for ROI or full image

    Clean interface function that handles ROI visualization.
    All the sophisticated quality calculations are done internally.
    """
    if quality_map_data is None:
        return original_image

    # Make a copy to avoid modifying the original
    result = original_image.copy()

    # Apply quality map
    if roi_coords:
        x1, y1, x2, y2 = roi_coords

        # Create colored version of the quality map
        quality_normalized = (quality_map_data * 255).astype(np.uint8)
        colored_map = _apply_dic_colormap(quality_normalized)

        # Extract the ROI region
        roi_height, roi_width = y2 - y1, x2 - x1

        # Make sure quality map has the right dimensions for the ROI
        if colored_map.shape[:2] != (roi_height, roi_width):
            colored_map = cv2.resize(colored_map, (roi_width, roi_height))

        # Create blended overlay just for the ROI region
        roi_overlay = cv2.addWeighted(
            result[y1:y2, x1:x2], 0.3,  # Keep 30% of original
            colored_map, 0.7,  # Add 70% of quality map
            0
        )

        # Apply the overlay only to the ROI region
        result[y1:y2, x1:x2] = roi_overlay
    else:
        # No ROI selected, apply to entire image
        quality_normalized = (quality_map_data * 255).astype(np.uint8)
        colored_map = _apply_dic_colormap(quality_normalized)

        # Resize if needed
        if colored_map.shape[:2] != result.shape[:2]:
            colored_map = cv2.resize(colored_map, (result.shape[1], result.shape[0]))

        result = cv2.addWeighted(result, 0.3, colored_map, 0.7, 0)

    return result