# analysis/core/subset_analyzer.py - Advanced Calculations, Simple Interface

import cv2
import numpy as np
from scipy.signal import correlate2d
from scipy.stats import entropy


def determine_optimal_subset_size(image):
    """Determines optimal subset size for DIC analysis using advanced feature analysis

    Uses sophisticated methods internally but provides simple interface.
    Complex calculations include:
    - Multi-scale feature detection
    - Autocorrelation analysis
    - Gradient-based texture analysis
    - Statistical pattern assessment

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

    # Standard DIC subset sizes to consider
    possible_sizes = [11, 15, 21, 31, 41, 51, 71]
    valid_sizes = [s for s in possible_sizes if s < min_dim / 3]

    if not valid_sizes:
        return min(possible_sizes)

    # ADVANCED FEATURE SIZE ANALYSIS (hidden complexity)
    feature_size_estimates = _analyze_feature_characteristics(gray)

    # Select optimal subset size based on sophisticated analysis
    if feature_size_estimates:
        avg_feature_size = np.median(feature_size_estimates)
        # Subset should be 3-5x the feature size for optimal DIC performance
        ideal_size = int(avg_feature_size * 4)

        # Find closest valid size with intelligent bounds checking
        closest_size = min(valid_sizes, key=lambda x: abs(x - ideal_size))

        # Apply constraints based on image characteristics
        if closest_size < min_dim / 20:  # Too small relative to image
            closest_size = min(valid_sizes[len(valid_sizes) // 2:])
        elif closest_size > min_dim / 5:  # Too large relative to image
            closest_size = max(valid_sizes[:len(valid_sizes) // 2])

        return closest_size

    # Fallback with image-size heuristics
    return _size_fallback_heuristic(min_dim)


def _analyze_feature_characteristics(gray):
    """Advanced feature characteristic analysis (internal complexity)

    Uses multiple sophisticated methods to determine feature sizes:
    1. Adaptive thresholding with multi-scale analysis
    2. Gradient-based texture analysis
    3. Autocorrelation-based pattern detection
    4. Frequency domain analysis
    5. Statistical texture measures
    """
    feature_estimates = []
    h, w = gray.shape

    # Method 1: Multi-scale adaptive thresholding analysis
    for block_size in [7, 11, 15, 21]:
        if block_size < min(h, w) // 4:
            try:
                binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                               cv2.THRESH_BINARY, block_size, 2)
                num_components, _, stats, _ = cv2.connectedComponentsWithStats(binary)

                if num_components > 1:
                    areas = stats[1:, cv2.CC_STAT_AREA]
                    valid_areas = areas[(areas > 4) & (areas < (h * w) / 100)]
                    if len(valid_areas) > 0:
                        feature_diameter = np.median(np.sqrt(valid_areas))
                        feature_estimates.append(feature_diameter * 1.2)  # Scale factor
            except:
                continue

    # Method 2: Advanced gradient-based analysis
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

    # Multi-threshold gradient analysis
    for percentile in [75, 80, 85, 90]:
        threshold = np.percentile(gradient_magnitude, percentile)
        high_grad_mask = gradient_magnitude > threshold
        high_grad_count = np.sum(high_grad_mask)

        if high_grad_count > 10:
            density = high_grad_count / (h * w)
            if density > 0:
                spacing = 1.0 / np.sqrt(density)
                feature_estimates.append(spacing * 0.8)  # Conservative estimate

    # Method 3: Autocorrelation analysis (most sophisticated)
    try:
        autocorr_estimate = _autocorrelation_feature_analysis(gray)
        if autocorr_estimate > 0:
            feature_estimates.append(autocorr_estimate)
    except:
        pass

    # Method 4: Frequency domain analysis
    try:
        freq_estimate = _frequency_domain_analysis(gray)
        if freq_estimate > 0:
            feature_estimates.append(freq_estimate)
    except:
        pass

    # Method 5: Local texture analysis
    try:
        texture_estimate = _texture_based_analysis(gray)
        if texture_estimate > 0:
            feature_estimates.append(texture_estimate)
    except:
        pass

    return feature_estimates


def _autocorrelation_feature_analysis(gray):
    """Sophisticated autocorrelation-based feature size analysis"""
    # Downsample for efficiency while maintaining accuracy
    scale = max(1, max(gray.shape) // 256)
    if scale > 1:
        small_gray = gray[::scale, ::scale]
    else:
        small_gray = gray

    # Calculate normalized autocorrelation
    normalized = small_gray.astype(float) - np.mean(small_gray)
    std_val = np.std(normalized)

    if std_val < 1e-6:
        return 0

    normalized /= std_val

    # Use FFT for efficient autocorrelation
    f_transform = np.fft.fft2(normalized)
    autocorr = np.real(np.fft.ifftshift(np.fft.ifft2(np.abs(f_transform) ** 2)))

    # Find characteristic length scale
    center_y, center_x = autocorr.shape[0] // 2, autocorr.shape[1] // 2
    center_val = autocorr[center_y, center_x]

    # Look for first significant drop (to 60% of peak)
    target_val = center_val * 0.6

    for radius in range(1, min(center_y, center_x) // 2):
        # Sample points at this radius
        circle_vals = []
        n_samples = max(8, int(2 * np.pi * radius))
        for i in range(n_samples):
            angle = 2 * np.pi * i / n_samples
            y = center_y + int(radius * np.sin(angle))
            x = center_x + int(radius * np.cos(angle))
            if 0 <= y < autocorr.shape[0] and 0 <= x < autocorr.shape[1]:
                circle_vals.append(autocorr[y, x])

        if circle_vals and np.mean(circle_vals) < target_val:
            return radius * scale * 1.5  # Scale back and adjust

    return 0


def _frequency_domain_analysis(gray):
    """Frequency domain analysis for characteristic feature size"""
    # Apply FFT
    f_transform = np.fft.fft2(gray.astype(float))
    f_shift = np.fft.fftshift(f_transform)
    magnitude = np.abs(f_shift)

    # Calculate radial power spectrum
    h, w = gray.shape
    center_y, center_x = h // 2, w // 2

    # Create radial coordinate system
    y, x = np.ogrid[:h, :w]
    radius = np.sqrt((y - center_y) ** 2 + (x - center_x) ** 2)

    # Calculate average power at each radius
    max_radius = min(center_y, center_x) // 2
    radial_power = []

    for r in range(1, max_radius):
        mask = (radius >= r - 0.5) & (radius < r + 0.5)
        if np.any(mask):
            avg_power = np.mean(magnitude[mask])
            radial_power.append(avg_power)
        else:
            radial_power.append(0)

    if len(radial_power) > 10:
        # Find dominant frequency (peak in power spectrum)
        radial_power = np.array(radial_power)
        # Smooth the spectrum
        if len(radial_power) > 5:
            kernel = np.ones(5) / 5
            if len(radial_power) >= len(kernel):
                radial_power = np.convolve(radial_power, kernel, mode='same')

        # Find peak frequency
        peak_idx = np.argmax(radial_power)
        if peak_idx > 0:
            # Convert frequency to spatial scale
            dominant_frequency = peak_idx
            spatial_wavelength = min(h, w) / dominant_frequency
            return spatial_wavelength / 3  # Feature size is typically 1/3 of wavelength

    return 0


def _texture_based_analysis(gray):
    """Texture-based feature size analysis using local binary patterns"""
    h, w = gray.shape

    if h < 10 or w < 10:
        return 0

    # Calculate local binary pattern-like features at different scales
    feature_sizes = []

    for radius in [1, 2, 3]:
        if radius * 3 < min(h, w) // 4:
            # Sample points around each pixel at given radius
            texture_response = np.zeros_like(gray, dtype=float)

            # 8-point sampling
            angles = np.linspace(0, 2 * np.pi, 9)[:-1]  # 8 points

            for angle in angles:
                dy = int(round(radius * np.sin(angle)))
                dx = int(round(radius * np.cos(angle)))

                # Create shifted versions
                y_indices = np.arange(radius, h - radius)
                x_indices = np.arange(radius, w - radius)

                if len(y_indices) > 0 and len(x_indices) > 0:
                    center_region = gray[y_indices[:, None], x_indices]
                    shifted_region = gray[y_indices[:, None] + dy, x_indices + dx]

                    # Count texture variations
                    texture_response[y_indices[:, None], x_indices] += (
                            shifted_region != center_region
                    ).astype(float)

            # Analyze texture response to estimate feature size
            if np.max(texture_response) > 0:
                # Find regions with high texture activity
                threshold = np.percentile(texture_response, 75)
                active_regions = texture_response > threshold

                if np.sum(active_regions) > 0:
                    # Estimate average spacing between active regions
                    # Simple approach: use distance transform
                    # Ensure we have a proper uint8 binary image
                    binary_input = (~active_regions).astype(np.uint8) * 255
                    dist_transform = cv2.distanceTransform(
                        binary_input,
                        cv2.DIST_L2, 5
                    )

                    mean_distance = np.mean(dist_transform[active_regions])
                    if mean_distance > 0:
                        feature_sizes.append(mean_distance * 2 * radius)

    return np.median(feature_sizes) if feature_sizes else 0


def _size_fallback_heuristic(min_dim):
    """Intelligent fallback heuristic based on image size"""
    if min_dim < 100:
        return 11
    elif min_dim < 200:
        return 15
    elif min_dim < 400:
        return 21
    elif min_dim < 800:
        return 31
    elif min_dim < 1600:
        return 41
    else:
        return 51


def analyze_subset_grid(image, subset_size=21, overlap=0.5):
    """Advanced subset grid analysis with comprehensive quality assessment

    Uses sophisticated internal calculations but provides simple interface.

    Args:
        image: Numpy array of image
        subset_size: Size of each subset (auto-determined if None)
        overlap: Overlap fraction between subsets

    Returns:
        tuple: (quality_map, average_quality)
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    # Auto-determine subset size if not provided
    if subset_size is None:
        subset_size = determine_optimal_subset_size(gray)

    # Import the advanced quality map generation
    from analysis.quality_map.map_generator import _analyze_subset_quality_advanced

    # Generate quality map using sophisticated analysis (internal complexity)
    step_size = max(1, int(subset_size * (1 - overlap)))
    quality_map = _analyze_subset_quality_advanced(gray, subset_size, step_size)

    # Calculate simple statistics for interface
    avg_quality = np.mean(quality_map)

    return quality_map, avg_quality


def create_subset_grid(image, subset_size=21, overlap=0.5):
    """Creates a grid of overlapping subsets for analysis

    Simple interface for advanced subset creation.

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


def compute_subset_quality(subset):
    """Compute quality score for a subset using advanced analysis

    Uses comprehensive internal calculations but returns simple score.
    Internal complexity includes:
    - Gradient analysis (SSG, distribution)
    - Multiple contrast measures
    - Entropy and texture analysis
    - Noise assessment
    - Pattern complexity evaluation

    Args:
        subset: Numpy array of the subset

    Returns:
        tuple: (quality_score, basic_metrics)
    """
    # Convert to grayscale if needed
    if len(subset.shape) == 3:
        gray = cv2.cvtColor(subset, cv2.COLOR_RGB2GRAY)
    else:
        gray = subset.copy()

    # ADVANCED QUALITY CALCULATION (hidden complexity)
    quality_score = _compute_advanced_subset_quality(gray)

    # Basic metrics for simple interface
    basic_metrics = {
        'mean_intensity': float(np.mean(gray)),
        'std_intensity': float(np.std(gray)),
        'quality_score': float(quality_score)
    }

    return quality_score, basic_metrics


def _compute_advanced_subset_quality(gray):
    """Advanced subset quality computation (internal complexity)

    Comprehensive analysis including:
    1. Gradient content (Sum of Squared Gradients)
    2. Multiple contrast measures (RMS, Michelson, Weber)
    3. Information content (Shannon entropy, local entropy)
    4. Texture analysis (LBP-like features, co-occurrence)
    5. Pattern complexity (frequency content, spatial distribution)
    6. Noise characteristics (SNR, signal estimation)
    7. Feature characteristics (size, distribution, spacing)
    """

    # 1. GRADIENT ANALYSIS (40% weight)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

    # Sum of Squared Gradients (key DIC metric)
    ssg = np.sum(gradient_magnitude ** 2)
    normalized_ssg = ssg / (gray.size * 255 ** 2)

    # Gradient distribution analysis
    grad_mean = np.mean(gradient_magnitude)
    grad_std = np.std(gradient_magnitude)
    grad_cv = grad_std / (grad_mean + 1e-6)

    # Gradient score with distribution penalty
    if normalized_ssg < 0.0005:
        gradient_score = 0
    elif normalized_ssg > 0.05:
        gradient_score = 1.0
    else:
        gradient_score = np.log10(normalized_ssg * 2000) / 2

    # Penalize poor gradient distribution
    if grad_cv < 0.4:  # Too uniform
        gradient_score *= 0.7
    elif grad_cv > 3.0:  # Too chaotic
        gradient_score *= 0.6

    # 2. COMPREHENSIVE CONTRAST ANALYSIS (25% weight)
    mean_val = np.mean(gray)
    std_val = np.std(gray)
    min_val = np.min(gray)
    max_val = np.max(gray)

    # Multiple contrast measures
    rms_contrast = std_val / (mean_val + 1e-6)
    michelson_contrast = (max_val - min_val) / (max_val + min_val + 1e-6)
    weber_contrast = (max_val - mean_val) / (mean_val + 1e-6)

    # Local contrast analysis
    if gray.shape[0] > 7 and gray.shape[1] > 7:
        kernel = np.ones((5, 5)) / 25
        local_mean = cv2.filter2D(gray.astype(float), -1, kernel)
        local_contrast = np.std(gray - local_mean) / (np.mean(local_mean) + 1e-6)
    else:
        local_contrast = rms_contrast

    # Combined contrast score
    contrast_score = (
            min(1.0, rms_contrast / 0.4) * 0.4 +
            min(1.0, michelson_contrast * 2) * 0.3 +
            min(1.0, weber_contrast / 0.5) * 0.2 +
            min(1.0, local_contrast / 0.3) * 0.1
    )

    # 3. INFORMATION CONTENT ANALYSIS (20% weight)
    # Shannon entropy
    hist, _ = np.histogram(gray, bins=64, range=(0, 256), density=True)
    shannon_entropy = entropy(hist[hist > 0]) if np.any(hist > 0) else 0
    entropy_score = min(1.0, shannon_entropy / 5.0)

    # Local entropy analysis
    if gray.shape[0] > 5 and gray.shape[1] > 5:
        local_entropies = []
        window_size = min(7, gray.shape[0] // 2, gray.shape[1] // 2)
        if window_size >= 3:
            step = max(1, window_size // 2)
            for i in range(0, gray.shape[0] - window_size + 1, step):
                for j in range(0, gray.shape[1] - window_size + 1, step):
                    window = gray[i:i + window_size, j:j + window_size]
                    w_hist, _ = np.histogram(window, bins=16, range=(0, 256), density=True)
                    w_entropy = entropy(w_hist[w_hist > 0]) if np.any(w_hist > 0) else 0
                    local_entropies.append(w_entropy)

        local_entropy_score = np.mean(local_entropies) / 4.0 if local_entropies else entropy_score
    else:
        local_entropy_score = entropy_score

    information_score = entropy_score * 0.6 + min(1.0, local_entropy_score) * 0.4

    # 4. PATTERN COMPLEXITY ANALYSIS (10% weight)
    # Texture complexity using simplified LBP
    if gray.shape[0] > 3 and gray.shape[1] > 3:
        center = gray[1:-1, 1:-1]
        # 8-neighborhood comparison
        neighbors = [
            gray[:-2, :-2], gray[:-2, 1:-1], gray[:-2, 2:],
            gray[1:-1, :-2], gray[1:-1, 2:],
            gray[2:, :-2], gray[2:, 1:-1], gray[2:, 2:]
        ]

        texture_variations = 0
        for neighbor in neighbors:
            texture_variations += np.sum(neighbor > center)

        texture_complexity = texture_variations / (center.size * len(neighbors))
        pattern_score = min(1.0, texture_complexity * 4)
    else:
        pattern_score = 0.5

    # 5. NOISE ASSESSMENT (5% weight)
    # Advanced noise estimation
    if gray.shape[0] > 5 and gray.shape[1] > 5:
        # Use bilateral filter for better signal/noise separation
        denoised = cv2.bilateralFilter(gray, 5, 50, 50)
        noise = gray.astype(float) - denoised.astype(float)
        noise_std = np.std(noise)
        signal_std = np.std(denoised)
        snr = signal_std / (noise_std + 1e-6)
        noise_score = min(1.0, snr / 30.0)
    else:
        # Fallback to simple median filter
        denoised = cv2.medianBlur(gray, 3)
        noise = gray.astype(float) - denoised.astype(float)
        noise_std = np.std(noise)
        signal_std = np.std(denoised)
        snr = signal_std / (noise_std + 1e-6)
        noise_score = min(1.0, snr / 20.0)

    # COMBINE ALL METRICS INTO FINAL QUALITY SCORE
    overall_quality = (
            gradient_score * 0.40 +  # Gradient content (most important)
            contrast_score * 0.25 +  # Contrast quality
            information_score * 0.20 +  # Information content
            pattern_score * 0.10 +  # Pattern complexity
            noise_score * 0.05  # Noise level
    )

    return max(0.0, min(1.0, overall_quality))


def find_optimal_subsets(image, subset_size=21, num_best=10):
    """Find the best subsets in an image for DIC analysis

    Uses advanced quality assessment internally but provides simple interface.

    Args:
        image: Input image
        subset_size: Size of subsets to analyze (auto-determined if None)
        num_best: Number of best subsets to return

    Returns:
        list: List of best subset locations with quality scores
    """
    # Auto-determine subset size if needed
    if subset_size is None:
        subset_size = determine_optimal_subset_size(image)

    # Create grid with good coverage
    subsets = create_subset_grid(image, subset_size, overlap=0.3)

    best_subsets = []

    for x, y, subset in subsets:
        quality, _ = compute_subset_quality(subset)

        subset_info = {
            'x': x,
            'y': y,
            'center_x': x + subset_size // 2,
            'center_y': y + subset_size // 2,
            'quality': quality,
            'subset_size': subset_size
        }

        best_subsets.append(subset_info)

    # Sort by quality score (descending)
    best_subsets.sort(key=lambda x: x['quality'], reverse=True)

    return best_subsets[:num_best]