import cv2
import numpy as np
from .metrics.metrics_manager import MetricsManager
from .quality_map.map_generator import generate_quality_map


class DICAnalyzer:
    """Main facade for Digital Image Correlation quality analysis"""

    def __init__(self, config=None):
        """Initialize analyzer with optional configuration

        Args:
            config (dict, optional): Configuration parameters
        """
        self.config = config or {}
        # Default parameters
        self.subset_size = self.config.get('subset_size', 21)
        self.overlap = self.config.get('overlap', 0.5)

    def analyze(self, image):
        """Analyze image quality for DIC applications

        Args:
            image: Input image (numpy array)

        Returns:
            dict: Analysis results with metrics and scores
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # Calculate metrics
        metrics_manager = MetricsManager(image)
        results = metrics_manager.calculate_all_metrics()
        results['contrast'] = self._calculate_contrast(gray)
        results['speckle_density'] = self._calculate_speckle_density(gray)
        results['gradient_magnitude'] = self._calculate_gradient_magnitude(gray)
        results['noise_level'] = self._calculate_noise_level(gray)
        results['pattern_uniformity'] = self._calculate_uniformity(gray)
        results['feature_size'] = self._analyze_feature_size(gray)
        results['intensity_distribution'] = self._analyze_intensity_distribution(gray)
        results['edge_quality'] = self._analyze_edge_quality(gray)

        # Calculate overall score
        results['overall_score'] = self._calculate_overall_score(results)

        return results

    def generate_quality_map(self, image):
        """Generate a quality heat map for the image"""
        return generate_quality_map(image)

    def _calculate_contrast(self, image):
        # Implementation
        return 65.0

    def _calculate_speckle_density(self, image):
        # Implementation
        return 120.0

    def _calculate_gradient_magnitude(self, image):
        # Implementation
        return 45.0

    def _calculate_noise_level(self, image):
        # Implementation
        return 25.0

    def _calculate_uniformity(self, image):
        # Implementation
        return 80.0

    def _analyze_feature_size(self, image):
        # Implementation
        return 7.5

    def _analyze_intensity_distribution(self, image):
        # Implementation
        return 75.0

    def _analyze_edge_quality(self, image):
        # Implementation
        return 60.0

    def _calculate_overall_score(self, results):
        """Calculate overall quality score from individual metrics"""
        # Simple weighted average for now
        weights = {
            'contrast': 0.15,
            'speckle_density': 0.15,
            'gradient_magnitude': 0.15,
            'noise_level': 0.1,
            'pattern_uniformity': 0.15,
            'feature_size': 0.1,
            'intensity_distribution': 0.1,
            'edge_quality': 0.1
        }

        # Normalize metrics to 0-100 scale
        # This is very simplified - you'd want to properly normalize each metric
        score = 0
        for key, weight in weights.items():
            score += results[key] * weight

        return min(max(int(score), 0), 100)