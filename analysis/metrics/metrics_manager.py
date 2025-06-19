# analysis/metrics/metrics_manager.py

import cv2
import numpy as np
from analysis.metrics.subset_metrics import SubsetMetrics
from analysis.core.subset_analyzer import determine_optimal_subset_size


class MetricsManager:
    """Manager class to handle all DIC image quality metrics calculations"""

    def __init__(self, image=None, roi_coords=None, subset_size=None, overlap=0.5):
        """Initialize the metrics manager

        Args:
            image: Input image array (grayscale or color)
            roi_coords: Optional ROI coordinates (x1, y1, x2, y2)
            subset_size: Size of subsets for analysis (auto-determined if None)
            overlap: Overlap fraction between subsets (0-1)
        """
        self.image = image
        self.roi_coords = roi_coords
        self.overlap = overlap
        self.subset_metrics = SubsetMetrics()

        # Initialize subset size if provided
        self.subset_size = subset_size

        # Results storage
        self.quality_map = None
        self.metrics_results = {}

        # Calculate subset size immediately if image is provided
        if self.image is not None and self.subset_size is None:
            self.subset_size = self.determine_subset_size()

    def set_image(self, image):
        """Set or update the image to analyze"""
        self.image = image
        # Reset results when image changes
        self.quality_map = None
        self.metrics_results = {}
        # Recalculate subset size for new image
        if self.subset_size is None:
            self.subset_size = self.determine_subset_size()

    def set_roi(self, roi_coords):
        """Set or update ROI coordinates"""
        self.roi_coords = roi_coords
        # Reset results when ROI changes
        self.quality_map = None
        self.metrics_results = {}

    def get_analysis_region(self):
        """Extract the region to analyze (ROI or full image)"""
        if self.image is None:
            return None

        if self.roi_coords:
            x1, y1, x2, y2 = self.roi_coords
            return self.image[y1:y2, x1:x2]
        else:
            return self.image

    def determine_subset_size(self):
        """Determine optimal subset size for the current image"""
        analysis_region = self.get_analysis_region()
        if analysis_region is None:
            return 21  # Default size

        return determine_optimal_subset_size(analysis_region)

    def compute_all_metrics(self, image):
        """Compute all quality metrics for DIC analysis

        Args:
            image: Input image (grayscale or color)

        Returns:
            dict: Dictionary with all quality metrics
        """
        from analysis.metrics.noise_metrics import compute_noise_metrics
        from analysis.metrics.contrast_metrics import calculate_contrast
        from analysis.core.subset_analyzer import determine_optimal_subset_size, analyze_subset_grid



        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        print(f"Computing metrics for image of shape {gray.shape}")

        # Compute gradient-based metrics
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

        gradient_metrics = {
            'mean_gradient': np.mean(gradient_magnitude),
            'std_gradient': np.std(gradient_magnitude),
            'max_gradient': np.max(gradient_magnitude),
            'gradient_uniformity': 1.0 - (np.std(gradient_magnitude) / (np.mean(gradient_magnitude) + 1e-6))
        }

        # Compute noise metrics
        noise_metrics = compute_noise_metrics(gray)

        # Compute subset-based metrics
        subset_size = determine_optimal_subset_size(gray)
        quality_map, avg_quality = analyze_subset_grid(gray, subset_size=subset_size)

        # Store quality map for visualization
        self.quality_map = quality_map

        # Compute intensity distribution metrics
        hist, bins = np.histogram(gray.flatten(), bins=256, range=(0, 256))
        hist = hist / np.sum(hist)  # Normalize
        non_zero = hist[hist > 0]
        intensity_entropy = -np.sum(non_zero * np.log2(non_zero)) if len(non_zero) > 0 else 0

        intensity_metrics = {
            'contrast': calculate_contrast(gray),  # Already normalized to 0-100 range
            'entropy': intensity_entropy,
            'min_intensity': np.min(gray),
            'max_intensity': np.max(gray),
            'dynamic_range': np.max(gray) - np.min(gray),
            'distribution_score': min(100, max(0, intensity_entropy * 12))
        }

        # Compute speckle pattern metrics
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Calculate speckle features
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
        if num_labels > 1:
            # Skip background component
            areas = stats[1:, cv2.CC_STAT_AREA]
            valid_areas = areas[(areas > 4) & (areas < gray.size / 100)]

            if len(valid_areas) > 0:
                avg_feature_size = np.mean(np.sqrt(valid_areas))
                speckle_density = len(valid_areas) / (gray.shape[0] * gray.shape[1]) * 1e6  # per Mpx
                size_variation = np.std(valid_areas) / (np.mean(valid_areas) + 1e-6)
            else:
                avg_feature_size = 0
                speckle_density = 0
                size_variation = 1.0
        else:
            avg_feature_size = 0
            speckle_density = 0
            size_variation = 1.0

        speckle_metrics = {
            'density': speckle_density,
            'avg_size': avg_feature_size,
            'size_variation': size_variation,
            'uniformity': 1.0 - size_variation,
            'size_score': 100 * (1.0 - abs(avg_feature_size - 7) / 10) if avg_feature_size > 0 else 0
        }

        # Compile all metrics
        compiled_metrics = self.compile_metrics(
            noise=noise_metrics,
            gradient=gradient_metrics,
            subset={'quality': avg_quality * 100},  # Scale to 0-100
            intensity=intensity_metrics,
            speckle=speckle_metrics
        )

        return compiled_metrics

    def compile_metrics(self, **metric_categories):
        """Compile metrics from different categories and calculate overall score

        Args:
            **metric_categories: Category-based metric dictionaries

        Returns:
            dict: Compiled metrics with overall score
        """
        # Initialize compilation
        compiled = {}

        # Define key metrics to extract
        key_metrics = {
            'noise': {'noise_level': 'noise_level'},
            'gradient': {'gradient_magnitude': 'mean_gradient'},
            'subset': {'subset_quality': 'quality'},
            'intensity': {
                'contrast': 'contrast',
                'intensity_distribution': 'distribution_score'
            },
            'speckle': {
                'speckle_density': 'density',
                'pattern_uniformity': 'uniformity',
                'feature_size': 'size_score'
            }
        }

        # Extract metrics from each category
        for category, metrics in metric_categories.items():
            if category in key_metrics and metrics:
                for target_key, source_key in key_metrics[category].items():
                    if source_key in metrics:
                        compiled[target_key] = metrics[source_key]

        # Define weights for overall score calculation
        weights = {
            'noise_level': 15,
            'gradient_magnitude': 25,
            'subset_quality': 20,
            'contrast': 15,
            'intensity_distribution': 10,
            'speckle_density': 15,
            'pattern_uniformity': 15,
            'feature_size': 10
        }

        # Calculate weighted score
        total_weight = 0
        weighted_sum = 0

        for key, weight in weights.items():
            if key in compiled:
                value = compiled[key]

                # Normalize values to 0-100 range
                if key == 'gradient_magnitude':
                    # Higher gradient is better (typical range 0-50)
                    normalized = min(100, max(0, value * 2))
                elif key == 'speckle_density':
                    # Optimal density around 100 features/Mpx
                    normalized = min(100, max(0, 100 - abs(value - 100)))
                else:
                    # Use value as is (should already be normalized)
                    normalized = min(100, max(0, value))

                weighted_sum += normalized * weight
                total_weight += weight

        # Calculate overall score
        overall_score = round(weighted_sum / total_weight) if total_weight > 0 else 0

        # Add specific metrics needed for reporting
        compiled['overall_score'] = overall_score
        compiled['contrast'] = metric_categories.get('intensity', {}).get('contrast', 0)
        compiled['speckle_density'] = metric_categories.get('speckle', {}).get('density', 0)
        compiled['gradient_magnitude'] = metric_categories.get('gradient', {}).get('mean_gradient', 0)
        compiled['noise_level'] = metric_categories.get('noise', {}).get('snr_db', 0)
        compiled['pattern_uniformity'] = metric_categories.get('speckle', {}).get('uniformity', 0)
        compiled['feature_size'] = metric_categories.get('speckle', {}).get('avg_size', 0)
        compiled['intensity_distribution'] = metric_categories.get('intensity', {}).get('distribution_score', 0)
        compiled['edge_quality'] = metric_categories.get('gradient', {}).get('gradient_uniformity', 0)

        return compiled