# analysis/quality_map/map_generator.py - CLEANED: Only essential DIC spectrums

import cv2
import numpy as np
import warnings
from analysis.core.subset_analyzer import determine_optimal_subset_size

# Suppress specific overflow warnings for this module
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar add')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar multiply')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in scalar divide')


def generate_quality_map(image, colormap='custom_dic', alpha=0.7):
    """
    Generate a DIC quality map with essential spectrum options only

    Args:
        image: Input image
        colormap: Spectrum type ('custom_dic', 'zeiss_style_dic', 'ultra_strict_dic', 'focus_aware_dic')
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


def generate_zeiss_style_quality_map(image, subset_size=19, step_size=4):
    """
    Main function to generate ZEISS-style quality map

    Args:
        image: Input image
        subset_size: Subset size (ZEISS typically uses 15-25)
        step_size: Step between analysis points (ZEISS uses 3-5)

    Returns:
        tuple: (quality_map, visualization)
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    # Ensure image is RGB for visualization
    if len(image.shape) == 2:
        rgb_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    else:
        rgb_image = image.copy()

    print(f"Generating ZEISS-style quality map...")
    print(f"Parameters: subset_size={subset_size}, step_size={step_size}")

    # Generate high-density quality map
    quality_map = _create_zeiss_high_density_analysis(gray, subset_size, step_size)

    print(f"Quality map statistics:")
    print(f"  Min: {np.min(quality_map):.4f}, Max: {np.max(quality_map):.4f}")
    print(f"  Mean: {np.mean(quality_map):.4f}, Std: {np.std(quality_map):.4f}")

    # Create ZEISS-style visualization
    colored_map = _create_zeiss_style_dic_spectrum(quality_map)

    # Resize colored map to match original image if needed
    if colored_map.shape[:2] != rgb_image.shape[:2]:
        colored_map = cv2.resize(colored_map, (rgb_image.shape[1], rgb_image.shape[0]))

    # Blend with original image (ZEISS-style overlay)
    alpha = 0.75  # Slightly more opaque overlay like ZEISS
    visualization = cv2.addWeighted(rgb_image, 1 - alpha, colored_map, alpha, 0)

    return quality_map, visualization


def _apply_dic_colormap(quality_map, spectrum_type='custom_dic'):
    """
    CLEANED: Essential spectrum colormap for DIC quality visualization

    Args:
        quality_map: Normalized quality data (0-1)
        spectrum_type: Type of spectrum to use (only 4 essential types)
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

    # CLEANED: Only essential DIC spectrums
    if spectrum_type == 'custom_dic':
        colored = _create_custom_dic_spectrum(normalized)
    elif spectrum_type == 'zeiss_style_dic':
        colored = _create_zeiss_style_dic_spectrum(normalized)
    elif spectrum_type == 'ultra_strict_dic':
        colored = _create_ultra_strict_dic_spectrum(normalized)
    elif spectrum_type == 'focus_aware_dic':
        colored = _create_focus_aware_dic_spectrum(normalized)
    else:
        # Fallback to custom DIC
        print(f"WARNING: Unknown spectrum '{spectrum_type}', using custom_dic")
        colored = _create_custom_dic_spectrum(normalized)

    print(f"Applied {spectrum_type} spectrum colormap")
    return colored


def _create_custom_dic_spectrum(normalized):
    """
    Custom DIC spectrum - Black to Red to Blue

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


def _create_zeiss_style_dic_spectrum(normalized):
    """
    ZEISS-Style Pattern Quality Spectrum (Colorblind-Friendly Red-to-Blue)
    """
    h, w = normalized.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    normalized = np.clip(normalized, 0, 1)

    # Professional DIC quality thresholds with colorblind-friendly colors
    # Red-to-Blue progression for maximum accessibility

    # Unusable (0-70%): Black to Dark Red - No reliable correlation possible
    mask_unusable = normalized < 0.70
    if np.any(mask_unusable):
        intensity = normalized[mask_unusable] / 0.70  # 0-1 range within this band
        colored[mask_unusable, 0] = (intensity * 100).astype(np.uint8)  # R: 0-100
        colored[mask_unusable, 1] = 0  # G: 0
        colored[mask_unusable, 2] = 0  # B: 0

    # Poor (70-80%): Bright Red - Unreliable correlation, high uncertainty
    mask_poor = (normalized >= 0.70) & (normalized < 0.80)
    colored[mask_poor, 0] = 255  # R: 255 (bright red)
    colored[mask_poor, 1] = 0  # G: 0
    colored[mask_poor, 2] = 0  # B: 0

    # Acceptable (80-85%): Orange - Usable but with increased uncertainty
    mask_acceptable = (normalized >= 0.80) & (normalized < 0.85)
    colored[mask_acceptable, 0] = 255  # R: 255
    colored[mask_acceptable, 1] = 140  # G: 140 (orange)
    colored[mask_acceptable, 2] = 0  # B: 0

    # Good (85-90%): Yellow - Good correlation quality
    mask_good = (normalized >= 0.85) & (normalized < 0.90)
    colored[mask_good, 0] = 255  # R: 255
    colored[mask_good, 1] = 255  # G: 255 (yellow)
    colored[mask_good, 2] = 0  # B: 0

    # Very Good (90-95%): Cyan - Very reliable correlation
    mask_very_good = (normalized >= 0.90) & (normalized < 0.95)
    colored[mask_very_good, 0] = 0  # R: 0
    colored[mask_very_good, 1] = 255  # G: 255 (cyan)
    colored[mask_very_good, 2] = 255  # B: 255

    # Excellent (95-100%): Blue - Optimal pattern quality
    mask_excellent = normalized >= 0.95
    colored[mask_excellent, 0] = 0  # R: 0
    colored[mask_excellent, 1] = 100  # G: 100 (dark blue)
    colored[mask_excellent, 2] = 255  # B: 255

    return colored


def _create_ultra_strict_dic_spectrum(normalized):
    """
    ULTRA-STRICT DIC spectrum - Only top 10% of quality range is considered good
    """
    h, w = normalized.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    normalized = np.clip(normalized, 0, 1)
    score_percent = normalized * 100

    # ULTRA-STRICT THRESHOLDS - focus on top 10% of quality range

    # Critical range (0-90%): Pure black - completely unsuitable
    mask_critical = score_percent < 90
    colored[mask_critical, 0] = 0  # R
    colored[mask_critical, 1] = 0  # G
    colored[mask_critical, 2] = 0  # B

    # Poor range (90-93%): Dark red - major focus/pattern issues
    mask_poor = (score_percent >= 90) & (score_percent < 93)
    colored[mask_poor, 0] = 80  # R
    colored[mask_poor, 1] = 0  # G
    colored[mask_poor, 2] = 0  # B

    # Marginal range (93-95%): Red - barely acceptable
    mask_marginal = (score_percent >= 93) & (score_percent < 95)
    colored[mask_marginal, 0] = 180  # R
    colored[mask_marginal, 1] = 0  # G
    colored[mask_marginal, 2] = 0  # B

    # Acceptable range (95-97%): Orange - acceptable for DIC
    mask_acceptable = (score_percent >= 95) & (score_percent < 97)
    colored[mask_acceptable, 0] = 255  # R
    colored[mask_acceptable, 1] = 140  # G
    colored[mask_acceptable, 2] = 0  # B

    # Good range (97-98%): Yellow - good for DIC
    mask_good = (score_percent >= 97) & (score_percent < 98)
    colored[mask_good, 0] = 255  # R
    colored[mask_good, 1] = 255  # G
    colored[mask_good, 2] = 0  # B

    # Very Good range (98-99%): Cyan - very good for DIC
    mask_very_good = (score_percent >= 98) & (score_percent < 99)
    colored[mask_very_good, 0] = 0  # R
    colored[mask_very_good, 1] = 255  # G
    colored[mask_very_good, 2] = 255  # B

    # Perfect range (99-100%): Blue - perfect for DIC
    mask_perfect = score_percent >= 99
    colored[mask_perfect, 0] = 0  # R
    colored[mask_perfect, 1] = 100  # G
    colored[mask_perfect, 2] = 255  # B

    return colored


def _create_focus_aware_dic_spectrum(normalized):
    """
    FOCUS-AWARE DIC spectrum - Emphasizes gradient quality and sharpness
    """
    h, w = normalized.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)

    normalized = np.clip(normalized, 0, 1)
    score_percent = normalized * 100

    # Focus-quality thresholds

    # Severely out of focus (0-85%): Black to dark red gradient
    mask_oof = score_percent < 85
    if np.any(mask_oof):
        oof_intensity = np.clip(score_percent[mask_oof] / 85, 0, 1)
        colored[mask_oof, 0] = (oof_intensity * 60).astype(np.uint8)  # R: 0-60
        colored[mask_oof, 1] = 0  # G: 0
        colored[mask_oof, 2] = 0  # B: 0

    # Soft focus - problematic (85-92%): Red to orange transition
    mask_soft = (score_percent >= 85) & (score_percent < 92)
    if np.any(mask_soft):
        soft_progress = (score_percent[mask_soft] - 85) / 7  # 0-1 within range
        colored[mask_soft, 0] = (180 + soft_progress * 75).astype(np.uint8)  # R: 180-255
        colored[mask_soft, 1] = (soft_progress * 100).astype(np.uint8)  # G: 0-100
        colored[mask_soft, 2] = 0  # B: 0

    # Acceptable focus (92-96%): Orange to yellow
    mask_acceptable = (score_percent >= 92) & (score_percent < 96)
    if np.any(mask_acceptable):
        acc_progress = (score_percent[mask_acceptable] - 92) / 4
        colored[mask_acceptable, 0] = 255  # R: 255
        colored[mask_acceptable, 1] = (100 + acc_progress * 155).astype(np.uint8)  # G: 100-255
        colored[mask_acceptable, 2] = 0  # B: 0

    # Good focus (96-98%): Yellow to cyan
    mask_good = (score_percent >= 96) & (score_percent < 98)
    if np.any(mask_good):
        good_progress = (score_percent[mask_good] - 96) / 2
        colored[mask_good, 0] = (255 * (1 - good_progress)).astype(np.uint8)  # R: 255-0
        colored[mask_good, 1] = 255  # G: 255
        colored[mask_good, 2] = (good_progress * 255).astype(np.uint8)  # B: 0-255

    # Excellent focus (98-100%): Cyan to blue
    mask_excellent = score_percent >= 98
    if np.any(mask_excellent):
        exc_progress = np.clip((score_percent[mask_excellent] - 98) / 2, 0, 1)
        colored[mask_excellent, 0] = 0  # R: 0
        colored[mask_excellent, 1] = (255 * (1 - exc_progress * 0.6)).astype(np.uint8)  # G: 255-102
        colored[mask_excellent, 2] = 255  # B: 255

    return colored


def _analyze_subset_quality_advanced(gray, subset_size=21, step_size=5):
    """Advanced subset quality analysis with comprehensive metrics"""
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
    Subset size independent quality calculation
    """

    # 1. GRADIENT ANALYSIS (60% weight) - Size-normalized
    # Sum of Squared Gradients (SSG) - normalized by subset area
    ssg = np.sum(subset_gradients ** 2)
    normalized_ssg = ssg / (subset.size * 255 ** 2)

    # Mean Intensity Gradient (MIG) - most reliable metric per literature
    mig = np.mean(subset_gradients)
    normalized_mig = mig / 255.0

    # Size-independent gradient scoring
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

    # 2. SPECKLE MORPHOLOGY ANALYSIS (20% weight) - Size-normalized
    morphology_score = _analyze_speckle_morphology(subset, subset_size)

    # 3. CONTRAST ANALYSIS (10% weight) - Already size-independent
    subset_std = np.std(subset)
    subset_mean = np.mean(subset)
    rms_contrast = subset_std / (subset_mean + 1e-6)
    contrast_score = min(1.0, rms_contrast / 0.25)

    # 4. UNIQUENESS ANALYSIS (10% weight) - Size-compensated
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
    """Size-independent speckle morphology analysis"""
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

    # Size-relative speckle filtering
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

    # Size-relative scoring
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
    """Size-independent uniqueness calculation"""
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


def _create_zeiss_high_density_analysis(gray, subset_size=15, step_size=3):
    """ZEISS-Style High-Density Pattern Quality Analysis"""
    h, w = gray.shape

    # Initialize high-density quality map
    quality_map = np.zeros((h, w), dtype=np.float32)
    count_map = np.zeros((h, w), dtype=np.int32)

    print(f"ZEISS-style analysis: subset={subset_size}, step={step_size}")
    print(f"Expected analysis points: {((h - subset_size) // step_size) * ((w - subset_size) // step_size)}")

    # Pre-calculate gradients for efficiency
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

    analysis_count = 0

    # High-density sampling (like ZEISS)
    for y in range(0, h - subset_size + 1, step_size):
        for x in range(0, w - subset_size + 1, step_size):
            # Extract subset
            subset = gray[y:y + subset_size, x:x + subset_size]
            subset_gradients = gradient_magnitude[y:y + subset_size, x:x + subset_size]

            # ZEISS-style quality calculation
            quality_score = _calculate_zeiss_style_quality(subset, subset_gradients)

            # Map quality back to image coordinates
            y_end = min(y + subset_size, h)
            x_end = min(x + subset_size, w)
            quality_map[y:y_end, x:x_end] += quality_score
            count_map[y:y_end, x:x_end] += 1

            analysis_count += 1

    print(f"Completed {analysis_count} analysis points")

    # Average overlapping regions
    mask = count_map > 0
    quality_map[mask] /= count_map[mask]

    # Apply light smoothing (less than before for more granular results)
    quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.5)

    return np.clip(quality_map, 0, 1)


def _calculate_zeiss_style_quality(subset, subset_gradients):
    """ZEISS-style quality calculation focusing on correlation reliability"""

    # 1. GRADIENT CONTENT ANALYSIS (50% weight) - Primary DIC requirement
    mean_gradient = np.mean(subset_gradients)
    gradient_std = np.std(subset_gradients)

    # Normalize gradient metrics
    gradient_score = min(1.0, mean_gradient / 50.0)  # Adjust threshold based on typical values

    # Gradient distribution quality (avoid too uniform or too chaotic)
    gradient_cv = gradient_std / (mean_gradient + 1e-6)
    if 0.5 <= gradient_cv <= 2.0:
        distribution_bonus = 1.0
    elif 0.3 <= gradient_cv <= 3.0:
        distribution_bonus = 0.8
    else:
        distribution_bonus = 0.6

    gradient_quality = gradient_score * distribution_bonus

    # 2. PATTERN UNIQUENESS (25% weight) - Critical for correlation
    # Calculate local contrast variations
    mean_intensity = np.mean(subset)
    intensity_std = np.std(subset)
    contrast_ratio = intensity_std / (mean_intensity + 1e-6)

    # Pattern complexity using local binary pattern concept
    center = subset[1:-1, 1:-1]
    complexity_score = 0

    if center.size > 0:
        # Check 8-neighborhood variations
        neighbors = [
            subset[:-2, :-2], subset[:-2, 1:-1], subset[:-2, 2:],
            subset[1:-1, :-2], subset[1:-1, 2:],
            subset[2:, :-2], subset[2:, 1:-1], subset[2:, 2:]
        ]

        variations = sum(np.mean(neighbor != center) for neighbor in neighbors)
        complexity_score = min(1.0, variations / 4.0)  # Normalize

    uniqueness_quality = min(1.0, contrast_ratio * 2.0) * 0.7 + complexity_score * 0.3

    # 3. NOISE RESISTANCE (15% weight) - For stable correlation
    # Estimate signal-to-noise ratio
    if subset.shape[0] > 3 and subset.shape[1] > 3:
        smoothed = cv2.GaussianBlur(subset, (3, 3), 0.5)
        noise = subset.astype(float) - smoothed.astype(float)
        noise_std = np.std(noise)
        signal_std = np.std(smoothed)
        snr = signal_std / (noise_std + 1e-6)
        noise_quality = min(1.0, snr / 20.0)
    else:
        noise_quality = 0.5

    # 4. FOCUS QUALITY (10% weight) - For sharp correlation
    # High-frequency content indicates good focus
    laplacian = cv2.Laplacian(subset, cv2.CV_64F)
    focus_score = min(1.0, np.var(laplacian) / 1000.0)  # Adjust threshold as needed

    # COMBINE ALL FACTORS (similar to ZEISS weighting)
    overall_quality = (
            gradient_quality * 0.50 +  # Gradient content (most important)
            uniqueness_quality * 0.25 +  # Pattern uniqueness
            noise_quality * 0.15 +  # Noise resistance
            focus_score * 0.10  # Focus quality
    )

    return max(0.0, min(1.0, overall_quality))


def _create_quality_visualization(base_image, quality_map, colormap_name='custom_dic', alpha=0.7):
    """Create quality map visualization with essential spectrum options"""
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


def visualize_quality_map(base_image, quality_map, colormap_name='custom_dic', alpha=0.7):
    """Simple wrapper for quality map visualization"""
    return _create_quality_visualization(base_image, quality_map, colormap_name, alpha)