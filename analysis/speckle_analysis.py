# analysis/speckle_analysis.py - Speckle Pattern Analysis

import cv2
import numpy as np
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class SpeckleAnalyzer:
    """
    Analyzes speckle pattern characteristics for DIC quality assessment.

    Speckle morphology is critical for DIC correlation. This module analyzes
    speckle size distribution, density, and uniformity to determine pattern
    suitability for DIC measurements.
    """

    def __init__(self):
        self.min_speckle_area = 4  # Minimum pixels for valid speckle
        self.max_speckle_ratio = 0.05  # Maximum speckle size as fraction of image

    def analyze(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Perform complete speckle pattern analysis.

        Args:
            image: Input image (grayscale)

        Returns:
            Dictionary containing speckle metrics
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        if gray.size == 0:
            return self._empty_result()

        try:
            # Binary segmentation for speckle identification
            binary_image = self._create_binary_segmentation(gray)

            # Connected component analysis
            speckle_data = self._analyze_connected_components(binary_image, gray.shape)

            # Size distribution analysis
            size_metrics = self._analyze_size_distribution(speckle_data, gray.shape)

            # Density analysis
            density_metrics = self._analyze_speckle_density(speckle_data, gray.shape)

            # Uniformity analysis
            uniformity_metrics = self._analyze_spatial_uniformity(speckle_data, gray.shape)

            # Quality scoring
            quality_scores = self._calculate_quality_scores(
                size_metrics, density_metrics, uniformity_metrics, gray.shape
            )

            # Combine all results
            result = {
                **speckle_data,
                **size_metrics,
                **density_metrics,
                **uniformity_metrics,
                **quality_scores
            }

            return result

        except Exception as e:
            logger.error(f"Error in speckle analysis: {e}")
            return self._empty_result()

    def _create_binary_segmentation(self, gray: np.ndarray) -> np.ndarray:
        """Create binary segmentation for speckle identification."""
        # Use adaptive thresholding for robust segmentation
        h, w = gray.shape
        block_size = max(3, min(15, min(h, w) // 10))
        if block_size % 2 == 0:
            block_size += 1

        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, block_size, 2
        )

        # Clean up binary image with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return binary

    def _analyze_connected_components(self, binary: np.ndarray, image_shape: Tuple[int, int]) -> Dict[str, Any]:
        """Analyze connected components to identify speckles."""
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary, connectivity=8
        )

        if num_labels < 2:  # Only background
            return {
                'total_speckles': 0,
                'speckle_areas': np.array([]),
                'speckle_centroids': np.array([]),
                'speckle_bboxes': np.array([])
            }

        # Extract speckle properties (skip background at index 0)
        areas = stats[1:, cv2.CC_STAT_AREA]
        centroids_data = centroids[1:]
        bboxes = stats[1:, :4]  # x, y, width, height

        # Filter speckles by size
        h, w = image_shape
        max_area = int(h * w * self.max_speckle_ratio)

        valid_mask = (areas >= self.min_speckle_area) & (areas <= max_area)

        valid_areas = areas[valid_mask]
        valid_centroids = centroids_data[valid_mask]
        valid_bboxes = bboxes[valid_mask]

        return {
            'total_speckles': len(valid_areas),
            'speckle_areas': valid_areas,
            'speckle_centroids': valid_centroids,
            'speckle_bboxes': valid_bboxes
        }

    def _analyze_size_distribution(self, speckle_data: Dict, image_shape: Tuple[int, int]) -> Dict[str, float]:
        """Analyze speckle size distribution."""
        areas = speckle_data['speckle_areas']

        if len(areas) == 0:
            return {
                'mean_area': 0.0,
                'std_area': 0.0,
                'median_area': 0.0,
                'mean_diameter': 0.0,
                'diameter_cv': 0.0,
                'size_uniformity': 0.0
            }

        # Calculate size statistics
        mean_area = float(np.mean(areas))
        std_area = float(np.std(areas))
        median_area = float(np.median(areas))

        # Convert to equivalent diameters
        diameters = 2 * np.sqrt(areas / np.pi)
        mean_diameter = float(np.mean(diameters))
        diameter_cv = float(np.std(diameters) / (np.mean(diameters) + 1e-6))

        # Size uniformity (lower CV = more uniform)
        size_uniformity = float(1.0 / (1.0 + diameter_cv))

        return {
            'mean_area': mean_area,
            'std_area': std_area,
            'median_area': median_area,
            'mean_diameter': mean_diameter,
            'diameter_cv': diameter_cv,
            'size_uniformity': size_uniformity
        }

    def _analyze_speckle_density(self, speckle_data: Dict, image_shape: Tuple[int, int]) -> Dict[str, float]:
        """Analyze speckle density characteristics."""
        h, w = image_shape
        total_area = h * w
        areas = speckle_data['speckle_areas']

        if len(areas) == 0:
            return {
                'speckle_density': 0.0,
                'coverage_ratio': 0.0,
                'density_score': 0.0
            }

        # Speckle density (speckles per unit area)
        speckle_density = float(len(areas) / total_area * 1e6)  # per million pixels

        # Coverage ratio (fraction of image covered by speckles)
        coverage_ratio = float(np.sum(areas) / total_area)

        # Density score (optimal range: 50-200 speckles per million pixels)
        if 50 <= speckle_density <= 200:
            density_score = 1.0
        elif 20 <= speckle_density <= 400:
            density_score = 0.8
        elif 10 <= speckle_density <= 600:
            density_score = 0.6
        else:
            density_score = 0.3

        return {
            'speckle_density': speckle_density,
            'coverage_ratio': coverage_ratio,
            'density_score': float(density_score)
        }

    def _analyze_spatial_uniformity(self, speckle_data: Dict, image_shape: Tuple[int, int]) -> Dict[str, float]:
        """Analyze spatial distribution uniformity of speckles."""
        centroids = speckle_data['speckle_centroids']

        if len(centroids) < 4:
            return {
                'spatial_uniformity': 0.0,
                'clustering_coefficient': 1.0,
                'distribution_entropy': 0.0
            }

        h, w = image_shape

        # Grid-based uniformity analysis
        grid_size = 4  # 4x4 grid
        grid_h, grid_w = h // grid_size, w // grid_size

        grid_counts = np.zeros((grid_size, grid_size))

        for x, y in centroids:
            grid_x = min(int(x // grid_w), grid_size - 1)
            grid_y = min(int(y // grid_h), grid_size - 1)
            grid_counts[grid_y, grid_x] += 1

        # Calculate distribution entropy
        total_speckles = len(centroids)
        if total_speckles > 0:
            probabilities = grid_counts.flatten() / total_speckles
            probabilities = probabilities[probabilities > 0]
            distribution_entropy = float(-np.sum(probabilities * np.log2(probabilities)))
        else:
            distribution_entropy = 0.0

        # Spatial uniformity (normalized entropy)
        max_entropy = np.log2(grid_size * grid_size)
        spatial_uniformity = float(distribution_entropy / max_entropy) if max_entropy > 0 else 0.0

        # Clustering coefficient (measure of local clustering)
        clustering_coefficient = self._calculate_clustering_coefficient(centroids)

        return {
            'spatial_uniformity': spatial_uniformity,
            'clustering_coefficient': float(clustering_coefficient),
            'distribution_entropy': distribution_entropy
        }

    def _calculate_clustering_coefficient(self, centroids: np.ndarray) -> float:
        """Calculate clustering coefficient for speckle distribution."""
        if len(centroids) < 3:
            return 0.0

        # Calculate average nearest neighbor distance
        distances = []
        for i, point in enumerate(centroids):
            other_points = np.delete(centroids, i, axis=0)
            dists = np.sqrt(np.sum((other_points - point) ** 2, axis=1))
            distances.append(np.min(dists))

        avg_nn_distance = np.mean(distances)

        # Compare to expected distance for random distribution
        area_per_point = (centroids[:, 0].max() - centroids[:, 0].min()) * \
                         (centroids[:, 1].max() - centroids[:, 1].min()) / len(centroids)
        expected_distance = 0.5 * np.sqrt(area_per_point)

        # Clustering coefficient (1 = random, >1 = clustered, <1 = regular)
        clustering_coeff = avg_nn_distance / (expected_distance + 1e-6)

        return min(2.0, max(0.0, clustering_coeff))

    def _calculate_quality_scores(self, size_metrics: Dict, density_metrics: Dict,
                                  uniformity_metrics: Dict, image_shape: Tuple[int, int]) -> Dict[str, float]:
        """Calculate overall quality scores for speckle characteristics."""

        # Size quality (optimal diameter: 3-8 pixels)
        mean_diameter = size_metrics['mean_diameter']
        if 3 <= mean_diameter <= 8:
            size_quality = 1.0
        elif 2 <= mean_diameter <= 12:
            size_quality = 0.8
        elif 1 <= mean_diameter <= 15:
            size_quality = 0.6
        else:
            size_quality = 0.3

        # Size uniformity quality (lower CV is better)
        diameter_cv = size_metrics['diameter_cv']
        if diameter_cv < 0.5:
            uniformity_quality = 1.0
        elif diameter_cv < 0.8:
            uniformity_quality = 0.8
        elif diameter_cv < 1.2:
            uniformity_quality = 0.6
        else:
            uniformity_quality = 0.4

        # Density quality (from density analysis)
        density_quality = density_metrics['density_score']

        # Spatial distribution quality
        spatial_uniformity = uniformity_metrics['spatial_uniformity']
        clustering_coeff = uniformity_metrics['clustering_coefficient']

        # Optimal clustering coefficient: 0.8-1.2 (slightly irregular but not too clustered)
        if 0.8 <= clustering_coeff <= 1.2:
            spatial_quality = spatial_uniformity
        else:
            spatial_quality = spatial_uniformity * 0.7

        # Overall speckle quality (weighted combination)
        overall_quality = (
                size_quality * 0.3 +
                uniformity_quality * 0.25 +
                density_quality * 0.25 +
                spatial_quality * 0.2
        )

        return {
            'size_quality': float(size_quality),
            'uniformity_quality': float(uniformity_quality),
            'density_quality': float(density_quality),
            'spatial_quality': float(spatial_quality),
            'overall_speckle_quality': float(overall_quality)
        }

    def analyze_local_speckle_quality(self, image: np.ndarray, window_size: int = 64) -> np.ndarray:
        """
        Analyze speckle quality in local windows across the image.

        Args:
            image: Input image
            window_size: Size of analysis windows

        Returns:
            2D array of local speckle quality scores
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)

        step = max(1, window_size // 4)

        for y in range(0, h - window_size + 1, step):
            for x in range(0, w - window_size + 1, step):
                # Extract local window
                window = gray[y:y + window_size, x:x + window_size]

                # Analyze local speckle characteristics
                local_metrics = self.analyze(window)
                local_quality = local_metrics.get('overall_speckle_quality', 0.0)

                # Map back to image coordinates
                y_end = min(y + window_size, h)
                x_end = min(x + window_size, w)
                quality_map[y:y_end, x:x_end] += local_quality
                count_map[y:y_end, x:x_end] += 1

        # Average overlapping regions
        mask = count_map > 0
        quality_map[mask] /= count_map[mask]

        return quality_map

    def get_speckle_recommendations(self, metrics: Dict[str, Any]) -> list:
        """Generate recommendations based on speckle analysis."""
        recommendations = []

        total_speckles = metrics.get('total_speckles', 0)
        mean_diameter = metrics.get('mean_diameter', 0)
        density_score = metrics.get('density_score', 0)
        spatial_uniformity = metrics.get('spatial_uniformity', 0)

        if total_speckles == 0:
            recommendations.append(" No speckles detected - apply speckle pattern")
            recommendations.append("Use spray paint or toner powder to create random pattern")
        elif total_speckles < 20:
            recommendations.append(" Very few speckles - increase speckle density")

        if mean_diameter < 2:
            recommendations.append(" Speckles too small - may cause noise issues")
            recommendations.append("Use larger speckle pattern or reduce image resolution")
        elif mean_diameter > 12:
            recommendations.append(" Speckles too large - may reduce correlation accuracy")
            recommendations.append("Use finer speckle pattern or increase image resolution")

        if density_score < 0.6:
            recommendations.append(" Suboptimal speckle density")
            if metrics.get('speckle_density', 0) < 50:
                recommendations.append("Increase speckle density")
            else:
                recommendations.append("Reduce speckle density")

        if spatial_uniformity < 0.6:
            recommendations.append(" Uneven speckle distribution")
            recommendations.append("Ensure more uniform speckle application")

        if len(recommendations) == 0:
            recommendations.append(" Good speckle pattern for DIC analysis")

        return recommendations

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            'total_speckles': 0,
            'speckle_areas': np.array([]),
            'speckle_centroids': np.array([]),
            'speckle_bboxes': np.array([]),
            'mean_area': 0.0,
            'std_area': 0.0,
            'median_area': 0.0,
            'mean_diameter': 0.0,
            'diameter_cv': 0.0,
            'size_uniformity': 0.0,
            'speckle_density': 0.0,
            'coverage_ratio': 0.0,
            'density_score': 0.0,
            'spatial_uniformity': 0.0,
            'clustering_coefficient': 1.0,
            'distribution_entropy': 0.0,
            'size_quality': 0.0,
            'uniformity_quality': 0.0,
            'density_quality': 0.0,
            'spatial_quality': 0.0,
            'overall_speckle_quality': 0.0
        }