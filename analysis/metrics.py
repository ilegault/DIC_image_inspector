# analysis.metrics.py

import cv2
import numpy as np
from tkinter import messagebox

def get_analysis_region(image, roi_coords):
    """Extract region of interest from image"""
    if roi_coords is None:
        return image

    x1, y1, x2, y2 = roi_coords
    return image[y1:y2, x1:x2]

def analyze_image(image, roi_coords=None):
    """Analyze the DIC pattern quality"""
    try:
        # Get analysis region
        if roi_coords:
            x1, y1, x2, y2 = roi_coords
            analysis_region = image[y1:y2, x1:x2]
        else:
            analysis_region = image

        # Convert to grayscale
        if len(analysis_region.shape) == 3:
            gray = cv2.cvtColor(analysis_region, cv2.COLOR_RGB2GRAY)
        else:
            gray = analysis_region

        results = {}

        # Enhanced analysis for DIC applications
        results['contrast'] = calculate_contrast(gray)
        results['speckle_density'] = calculate_speckle_density(gray)
        results['gradient_magnitude'] = calculate_gradient_magnitude(gray)
        results['noise_level'] = calculate_noise_level(gray)
        results['pattern_uniformity'] = calculate_uniformity(gray)
        results['feature_size'] = analyze_feature_size(gray)
        results['intensity_distribution'] = analyze_intensity_distribution(gray)
        results['edge_quality'] = analyze_edge_quality(gray)

        # Improved overall score calculation
        results['overall_score'] = calculate_overall_score(results)

        return results

    except Exception as e:
        raise Exception(f"Analysis error: {str(e)}")

def calculate_contrast(gray):
    """Improved contrast calculation using multiple methods"""
    # Method 1: RMS contrast (better for DIC)
    rms_contrast = np.sqrt(np.mean((gray - np.mean(gray))**2)) / np.mean(gray) * 100

    # Method 2: Michelson contrast for local features
    local_max = np.percentile(gray, 95)  # Avoid outliers
    local_min = np.percentile(gray, 5)
    if local_max + local_min > 0:
        michelson_contrast = (local_max - local_min) / (local_max + local_min) * 100
    else:
        michelson_contrast = 0

    # Combine both methods
    contrast = (rms_contrast + michelson_contrast) / 2
    return round(min(contrast, 100), 1)

def calculate_speckle_density(gray):
    """Improved speckle density calculation"""
    # Use multiple feature detection methods

    # Method 1: Good Features to Track
    corners = cv2.goodFeaturesToTrack(gray, maxCorners=2000, qualityLevel=0.01,
                                      minDistance=3, blockSize=3)

    # Method 2: FAST corner detection
    fast = cv2.FastFeatureDetector_create(threshold=20)
    fast_keypoints = fast.detect(gray, None)

    # Method 3: Binary pattern analysis
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Calculate densities
    area = gray.shape[0] * gray.shape[1]

    corner_density = len(corners) if corners is not None else 0
    fast_density = len(fast_keypoints)
    contour_density = len([c for c in contours if cv2.contourArea(c) > 3])

    # Combine and normalize
    total_features = (corner_density + fast_density + contour_density) / 3
    density = total_features / area * 1000000  # Features per million pixels

    return round(density, 1)

def calculate_noise_level(gray):
    """Improved noise level estimation"""
    # Use multiple noise estimation methods

    # Method 1: Laplacian variance
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    laplacian_var = laplacian.var()

    # Method 2: Local standard deviation
    kernel = np.ones((5, 5), np.float32) / 25
    local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
    local_var = cv2.filter2D((gray.astype(np.float32) - local_mean) ** 2, -1, kernel)
    noise_estimate = np.mean(np.sqrt(local_var))

    # Convert to SNR-like metric
    signal_strength = np.std(gray)
    if noise_estimate > 0:
        snr = 20 * np.log10(signal_strength / noise_estimate)
    else:
        # Avoid division by zero
        snr = 50  # Set a reasonable maximum SNR value

    return round(max(0, min(snr, 50)), 1)

def calculate_uniformity(gray):
    """Improved pattern uniformity calculation"""
    # Use overlapping windows for better uniformity assessment
    h, w = gray.shape
    window_size = min(h, w) // 6

    if window_size < 10:
        return 0

    step_size = window_size // 2
    window_stats = []

    for y in range(0, h - window_size, step_size):
        for x in range(0, w - window_size, step_size):
            window = gray[y:y + window_size, x:x + window_size]
            # Calculate multiple statistics
            mean_intensity = np.mean(window)
            std_intensity = np.std(window)
            gradient_strength = np.mean(cv2.Sobel(window, cv2.CV_64F, 1, 0) ** 2 +
                                        cv2.Sobel(window, cv2.CV_64F, 0, 1) ** 2)

            window_stats.append({
                'mean': mean_intensity,
                'std': std_intensity,
                'gradient': gradient_strength
            })

    if len(window_stats) < 2:
        return 0

    # Calculate uniformity based on variation in statistics
    means = [s['mean'] for s in window_stats]
    stds = [s['std'] for s in window_stats]
    gradients = [s['gradient'] for s in window_stats]

    mean_uniformity = 100 - (np.std(means) / np.mean(means) * 100) if np.mean(means) > 0 else 0
    std_uniformity = 100 - (np.std(stds) / np.mean(stds) * 100) if np.mean(stds) > 0 else 0
    grad_uniformity = 100 - (np.std(gradients) / np.mean(gradients) * 100) if np.mean(gradients) > 0 else 0

    overall_uniformity = (mean_uniformity + std_uniformity + grad_uniformity) / 3
    return round(max(0, min(overall_uniformity, 100)), 1)

def analyze_feature_size(gray):
    """Improved feature size analysis"""
    # Use watershed segmentation for better feature separation
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Distance transform
    dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)

    # Find local maxima
    local_maxima = cv2.dilate(dist_transform, np.ones((3, 3))) == dist_transform
    local_maxima = local_maxima & (dist_transform > 0.5 * dist_transform.max())

    # Get coordinates of maxima
    maxima_coords = np.where(local_maxima)

    if len(maxima_coords[0]) > 0:
        # Calculate average distance between features
        distances = []
        coords = list(zip(maxima_coords[0], maxima_coords[1]))

        for i, coord1 in enumerate(coords[:100]):  # Limit for performance
            for coord2 in coords[i + 1:i + 11]:  # Check nearest neighbors
                dist = np.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)
                distances.append(dist)

        if distances:
            avg_spacing = np.mean(distances)
            return round(avg_spacing, 1)

    # Fallback to connected components
    num_components, labels, stats, _ = cv2.connectedComponentsWithStats(binary)

    if num_components > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        areas = areas[(areas > 5) & (areas < 1000)]

        if len(areas) > 0:
            avg_area = np.mean(areas)
            # Convert area to approximate diameter
            avg_diameter = 2 * np.sqrt(avg_area / np.pi)
            return round(avg_diameter, 1)

    return 0

def calculate_gradient_magnitude(gray):
    """Calculate gradient magnitude for edge strength"""
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
    return round(np.mean(gradient_magnitude), 1)

def analyze_intensity_distribution(gray):
    """Analyze intensity distribution for DIC suitability"""
    hist, bins = np.histogram(gray, bins=256, range=(0, 256))

    # Calculate histogram statistics
    total_pixels = gray.shape[0] * gray.shape[1]
    hist_normalized = hist / total_pixels

    # Shannon entropy (higher is better for DIC)
    entropy = -np.sum(hist_normalized[hist_normalized > 0] *
                      np.log2(hist_normalized[hist_normalized > 0]))

    # Normalize entropy to 0-100 scale
    max_entropy = 8.0  # log2(256)
    entropy_score = (entropy / max_entropy) * 100

    return round(entropy_score, 1)

def analyze_edge_quality(gray):
    """Analyze edge quality and sharpness"""
    # Use Canny edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Calculate edge density
    edge_pixels = np.sum(edges > 0)
    total_pixels = gray.shape[0] * gray.shape[1]
    edge_density = (edge_pixels / total_pixels) * 100

    # Analyze edge strength
    if edge_pixels > 0:
        # Get gradient at edge locations
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

        edge_locations = edges > 0
        edge_strength = np.mean(gradient_magnitude[edge_locations])

        # Combine density and strength
        edge_quality = (edge_density * 0.3 + (edge_strength / 255 * 100) * 0.7)
    else:
        edge_quality = 0

    return round(min(edge_quality, 100), 1)

def calculate_overall_score(results):
    """Improved overall score calculation with DIC-specific weighting"""
    # DIC-specific weights
    weights = {
        'contrast': 0.20,  # Important but not everything
        'speckle_density': 0.25,  # Very important for DIC
        'gradient_magnitude': 0.15,  # Important for correlation
        'noise_level': 0.10,  # Less critical if other factors good
        'pattern_uniformity': 0.15,  # Important for consistent results
        'feature_size': 0.10,  # Important for subset size
        'intensity_distribution': 0.05  # Nice to have
    }

    # Normalize scores for combination
    normalized_scores = {}

    # Contrast: good range is 20-80
    contrast = results['contrast']
    if contrast < 20:
        normalized_scores['contrast'] = contrast / 20 * 50
    elif contrast > 80:
        normalized_scores['contrast'] = max(0, 100 - (contrast - 80) * 2)
    else:
        normalized_scores['contrast'] = 50 + (contrast - 20) / 60 * 50

    # Speckle density: optimal range varies, but generally 50-500 features per area
    density = results['speckle_density']
    if density < 10:
        normalized_scores['speckle_density'] = density * 5
    elif density > 200:
        normalized_scores['speckle_density'] = max(0, 100 - (density - 200) * 0.5)
    else:
        normalized_scores['speckle_density'] = min(100, density * 0.5 + 50)

    # Gradient magnitude: higher is generally better
    grad_mag = results['gradient_magnitude']
    normalized_scores['gradient_magnitude'] = min(100, grad_mag * 0.5)

    # Noise level: already normalized as SNR
    normalized_scores['noise_level'] = results['noise_level'] * 2

    # Pattern uniformity: already 0-100
    normalized_scores['pattern_uniformity'] = results['pattern_uniformity']

    # Feature size: optimal range is 3-15 pixels
    feature_size = results['feature_size']
    if feature_size == 0:
        normalized_scores['feature_size'] = 0
    elif feature_size < 3:
        normalized_scores['feature_size'] = feature_size / 3 * 50
    elif feature_size > 15:
        normalized_scores['feature_size'] = max(0, 100 - (feature_size - 15) * 5)
    else:
        normalized_scores['feature_size'] = 50 + (feature_size - 3) / 12 * 50

    # Intensity distribution: already 0-100
    normalized_scores['intensity_distribution'] = results['intensity_distribution']

    # Calculate weighted score
    overall_score = sum(normalized_scores.get(key, 0) * weight
                        for key, weight in weights.items())

    return round(overall_score, 1)