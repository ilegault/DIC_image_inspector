# analysis/metrics/metrics_manager.py
import cv2
import numpy as np
from .subset_metrics import SubsetMetrics

from .contrast_metrics import (
    calculate_contrast,
    analyze_intensity_distribution
)
from .feature_metrics import (
    calculate_speckle_density,
)
from .spatial_metrics import (
    analyze_edge_quality,
    calculate_uniformity,
    calculate_gradient_magnitude,
)
from .noise_metrics import compute_noise_metrics
from .pattern_metrics import evaluate_pattern_quality
from .correlation_metrics import evaluate_correlation_potential


class MetricsManager:
    """Manager class to calculate and manage all image quality metrics"""

    def __init__(self, image, subset_size=None, overlap=0.5):
        """Initialize with an image"""
        self.original_image = image
        self.subset_metrics = SubsetMetrics()

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            self.gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            self.gray = image.copy()

        # Use optimal subset size if not provided
        if subset_size is None:
            from analysis.core.subset_analyzer import determine_optimal_subset_size
            self.subset_size = determine_optimal_subset_size(self.gray)
        else:
            self.subset_size = subset_size

        self.overlap = overlap
        self.step_size = int(self.subset_size * (1 - overlap))  # Calculate step size from overlap

    def calculate_all_metrics(self):
        """Calculate all DIC quality metrics"""
        metrics = {}

        # Calculate global metrics first
        metrics['contrast'] = calculate_contrast(self.gray)
        metrics['intensity_distribution'] = analyze_intensity_distribution(self.gray)
        metrics['speckle_density'] = calculate_speckle_density(self.gray)

        # Other global metrics
        metrics['edge_quality'] = analyze_edge_quality(self.gray)
        metrics['pattern_uniformity'] = calculate_uniformity(self.gray)
        metrics['gradient_magnitude'] = calculate_gradient_magnitude(self.gray)

        noise_results = compute_noise_metrics(self.gray)
        metrics['noise_level'] = noise_results['noise_quality_score']

        pattern_results = evaluate_pattern_quality(self.gray)
        metrics['pattern_quality'] = pattern_results['quality_score']

        correlation_results = evaluate_correlation_potential(self.gray)
        metrics['correlation_potential'] = correlation_results['correlation_potential']

        # Use the dedicated SubsetMetrics class for all subset-related calculations
        quality_map, metrics_map = self.subset_metrics.map_subset_quality(
            self.original_image, self.subset_size, self.step_size
        )

        # Extract feature size from subset metrics instead of recalculating
        subset_metrics_list = list(metrics_map.values())
        if subset_metrics_list:
            # Average feature size across all subsets
            feature_sizes = [m.get('median_feature_size', 0) for m in subset_metrics_list
                             if 'median_feature_size' in m]
            metrics['feature_size'] = np.mean(feature_sizes) if feature_sizes else 0

        # Add subset metrics to the results
        metrics['subset_quality_map'] = quality_map
        metrics['subset_metrics_map'] = metrics_map

        # Calculate average quality from the map
        metrics['avg_subset_quality'] = np.mean([m.get('quality_score', 0) for m in subset_metrics_list]) \
            if subset_metrics_list else 0

        # Calculate overall score
        metrics['overall_score'] = self.calculate_overall_score(metrics)

        return metrics

    def calculate_overall_score(self, metrics):
        """Calculate overall DIC quality score from individual metrics"""
        # Metric weights (sum to 1)
        weights = {
            'contrast': 0.15,
            'intensity_distribution': 0.10,
            'speckle_density': 0.10,
            'feature_size': 0.10,
            'edge_quality': 0.10,
            'pattern_uniformity': 0.10,
            'gradient_magnitude': 0.05,
            'noise_level': 0.10,
            'pattern_quality': 0.15,
            'correlation_potential': 0.05,
        }

        # Special handling for metrics with optimal ranges
        score = 0
        for metric, weight in weights.items():
            if metric not in metrics:
                continue

            # Custom normalization for metrics with optimal ranges
            if metric == 'feature_size':
                feature_size = metrics[metric]
                if 3 <= feature_size <= 15:
                    # Scale based on ideal range (7-10px)
                    normalized = 100 if 7 <= feature_size <= 10 else \
                        50 + ((feature_size - 3) * 50 / 4 if feature_size < 7 else
                                  50 - (feature_size - 10) * 50 / 5)
                else:
                    normalized = min(50, max(0, feature_size * 50 / 3 if feature_size < 3 else \
                        50 - (feature_size - 15) * 5))
            else:
                # Default normalization
                normalized = min(100, max(0, metrics[metric]))

            score += normalized * weight

        return round(score, 1)