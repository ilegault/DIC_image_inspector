# analysis/analyzer.py

import cv2
import numpy as np
from analysis.metrics.metrics_manager import MetricsManager
from analysis.quality_map.map_generator import generate_quality_map
from analysis.utils.image_processing import get_analysis_region


class DICAnalyzer:
    """Main analyzer for DIC image quality assessment

    Coordinates all the different analysis components and provides a simplified
    interface for the main application.
    """

    def __init__(self):
        """Initialize the analyzer with default parameters"""
        self.subset_size = None
        self.overlap = 0.5

    def analyze(self, image):
        """Analyze an image for DIC quality metrics

        Args:
            image: Numpy array of the image to analyze (ROI or full image)

        Returns:
            dict: Complete analysis results with all metrics
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Initialize metrics manager - automatically determines optimal subset size
        metrics_manager = MetricsManager(gray)

        # Store the subset size for reference
        self.subset_size = metrics_manager.subset_size

        # Run all metrics calculations
        metrics = metrics_manager.compute_all_metrics(image)

        # Generate the quality map visualization
        quality_map, visualization = generate_quality_map(image)

        # Store quality map in results
        metrics['quality_map'] = quality_map
        metrics['quality_visualization'] = visualization

        # Format results for display in the UI
        formatted_results = self._format_results(metrics)

        return formatted_results

    def _format_results(self, metrics):
        """Format raw metrics into a standardized structure for the UI

        Args:
            metrics: Raw metrics from the metrics manager

        Returns:
            dict: Formatted metrics ready for display
        """
        results = {
            # Overall score (0-100)
            'overall_score': metrics.get('overall_score', 0),

            # Main metrics with appropriate scaling and units
            'contrast': round(metrics.get('contrast', 0), 1),
            'speckle_density': round(metrics.get('speckle_density', 0), 1),
            'gradient_magnitude': round(metrics.get('gradient_magnitude', 0), 1),
            'noise_level': round(metrics.get('noise_level', 0), 1),
            'pattern_uniformity': round(metrics.get('pattern_uniformity', 0), 1),
            'feature_size': round(metrics.get('feature_size', 0), 1),
            'intensity_distribution': round(metrics.get('intensity_distribution', 0), 1),
            'edge_quality': round(metrics.get('edge_quality', 0), 1),

            # Additional metrics
            'avg_subset_quality': round(metrics.get('avg_subset_quality', 0) * 100, 1),

            # Store quality map and visualization
            'quality_map': metrics.get('quality_map'),
            'quality_visualization': metrics.get('quality_visualization'),

            # Store subset metrics for detailed analysis
            'subset_metrics': metrics.get('subset_metrics_map', {}),
        }

        return results