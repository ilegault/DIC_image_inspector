"""
Analysis result data model and operations.

Encapsulates complete DIC quality analysis results including overall scores,
quality maps, statistics, DIC parameters, and detailed metrics in a type-safe
data structure with validation and serialization support.

Usage:
    result = AnalysisResult(overall_score=85.5, quality_map=map_array,
                           quality_map_stats=stats, analysis_method='Full image')
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import numpy as np
from datetime import datetime


@dataclass
class QualityMapStats:
    """Statistics for quality map data."""
    min_quality: float
    max_quality: float
    mean_quality: float
    median_quality: float
    std_quality: float
    percentile_25: float
    percentile_75: float


@dataclass
class DICParameters:
    """Recommended DIC analysis parameters."""
    facet_size: int
    step_size: int
    overlap_percent: float
    expected_accuracy: str
    subset_size_used: int


@dataclass
class AnalysisMetrics:
    """Detailed analysis metrics."""
    contrast_score: float
    gradient_magnitude: float
    noise_level: float
    speckle_density: float
    feature_size: float
    pattern_uniformity: float
    intensity_distribution: float
    edge_quality: float


@dataclass
class AnalysisResult:
    """
    Complete analysis result data structure.

    This class encapsulates all results from DIC quality analysis
    in a clean, type-safe manner.
    """

    # Core results
    overall_score: float
    quality_map: np.ndarray
    quality_map_stats: QualityMapStats

    # Analysis metadata
    analysis_method: str
    spectrum_used: str
    timestamp: datetime = field(default_factory=datetime.now)

    # DIC parameters
    dic_parameters: Optional[DICParameters] = None

    # Detailed metrics
    metrics: Optional[AnalysisMetrics] = None

    # Processing info
    processing_time: Optional[float] = None
    image_dimensions: Optional[tuple] = None
    roi_area: Optional[float] = None

    # Per-metric breakdown (Task 1/2): normalized 0-100 scores + weights
    component_scores: Optional[dict] = None

    # Per-metric spatial maps (Task 4): large numpy data, not serialized
    metric_maps: Optional[dict] = None

    def __post_init__(self):
        """Post-initialization validation and processing."""
        # Validate overall score
        if not 0 <= self.overall_score <= 100:
            raise ValueError(f"Overall score must be 0-100, got {self.overall_score}")

        # Validate quality map
        if self.quality_map is not None:
            if not isinstance(self.quality_map, np.ndarray):
                raise TypeError("Quality map must be a numpy array")

            # Ensure quality map values are in [0, 1] range
            if self.quality_map.max() > 1.0 or self.quality_map.min() < 0.0:
                print(f"WARNING: Quality map values outside [0,1] range: "
                      f"min={self.quality_map.min():.3f}, max={self.quality_map.max():.3f}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """
        Create AnalysisResult from dictionary.

        Args:
            data: Dictionary containing analysis result data

        Returns:
            AnalysisResult instance
        """
        # Extract quality map stats
        stats_data = data.get('quality_map_stats', {})
        quality_stats = QualityMapStats(
            min_quality=stats_data.get('min_quality', 0.0),
            max_quality=stats_data.get('max_quality', 0.0),
            mean_quality=stats_data.get('mean_quality', 0.0),
            median_quality=stats_data.get('median_quality', 0.0),
            std_quality=stats_data.get('std_quality', 0.0),
            percentile_25=stats_data.get('percentile_25', 0.0),
            percentile_75=stats_data.get('percentile_75', 0.0)
        )

        # Extract DIC parameters
        dic_data = data.get('dic_parameters', {})
        dic_params = None
        if dic_data:
            dic_params = DICParameters(
                facet_size=dic_data.get('facet_size', 21),
                step_size=dic_data.get('step_size', 5),
                overlap_percent=dic_data.get('overlap_percent', 75.0),
                expected_accuracy=dic_data.get('expected_accuracy', '±0.05 pixels'),
                subset_size_used=dic_data.get('subset_size_used', 21)
            )

        # Extract metrics
        metrics_data = data.get('metrics', {})
        metrics = None
        if metrics_data:
            metrics = AnalysisMetrics(
                contrast_score=metrics_data.get('contrast', 0.0),
                gradient_magnitude=metrics_data.get('gradient_magnitude', 0.0),
                noise_level=metrics_data.get('noise_level', 0.0),
                speckle_density=metrics_data.get('speckle_density', 0.0),
                feature_size=metrics_data.get('feature_size', 0.0),
                pattern_uniformity=metrics_data.get('pattern_uniformity', 0.0),
                intensity_distribution=metrics_data.get('intensity_distribution', 0.0),
                edge_quality=metrics_data.get('edge_quality', 0.0)
            )

        # Create timestamp
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()

        return cls(
            overall_score=data.get('overall_score', 0.0),
            quality_map=data.get('quality_map'),
            quality_map_stats=quality_stats,
            analysis_method=data.get('analysis_method', 'Unknown'),
            spectrum_used=data.get('spectrum_used', 'custom_dic'),
            timestamp=timestamp,
            dic_parameters=dic_params,
            metrics=metrics,
            processing_time=data.get('processing_time'),
            image_dimensions=data.get('image_dimensions'),
            roi_area=data.get('roi_area')
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert AnalysisResult to dictionary.

        Returns:
            Dictionary representation of analysis result
        """
        result = {
            'overall_score': self.overall_score,
            'analysis_method': self.analysis_method,
            'spectrum_used': self.spectrum_used,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'image_dimensions': self.image_dimensions,
            'roi_area': self.roi_area
        }

        # Add quality map stats
        result['quality_map_stats'] = {
            'min_quality': self.quality_map_stats.min_quality,
            'max_quality': self.quality_map_stats.max_quality,
            'mean_quality': self.quality_map_stats.mean_quality,
            'median_quality': self.quality_map_stats.median_quality,
            'std_quality': self.quality_map_stats.std_quality,
            'percentile_25': self.quality_map_stats.percentile_25,
            'percentile_75': self.quality_map_stats.percentile_75
        }

        # Add DIC parameters
        if self.dic_parameters:
            result['dic_parameters'] = {
                'facet_size': self.dic_parameters.facet_size,
                'step_size': self.dic_parameters.step_size,
                'overlap_percent': self.dic_parameters.overlap_percent,
                'expected_accuracy': self.dic_parameters.expected_accuracy,
                'subset_size_used': self.dic_parameters.subset_size_used
            }

        # Add metrics
        if self.metrics:
            result['metrics'] = {
                'contrast': self.metrics.contrast_score,
                'gradient_magnitude': self.metrics.gradient_magnitude,
                'noise_level': self.metrics.noise_level,
                'speckle_density': self.metrics.speckle_density,
                'feature_size': self.metrics.feature_size,
                'pattern_uniformity': self.metrics.pattern_uniformity,
                'intensity_distribution': self.metrics.intensity_distribution,
                'edge_quality': self.metrics.edge_quality
            }

        # Note: quality_map and metric_maps are not included as they are large numpy arrays
        # component_scores is a plain dict and safe to serialize
        if self.component_scores is not None:
            result['component_scores'] = self.component_scores

        return result

    def get_quality_assessment(self) -> tuple[str, str]:
        """
        Get quality assessment text and color based on score and spectrum.

        Returns:
            Tuple of (assessment_text, color_hex)
        """
        score = self.overall_score
        spectrum = self.spectrum_used

        if spectrum == 'custom_dic':
            # Strict DIC-only assessment
            if score >= 95:
                return "Perfect for DIC", "#008cff"
            elif score >= 90:
                return "Excellent for DIC", "#78ffb4"
            elif score >= 85:
                return "Very Good for DIC", "#ffc800"
            elif score >= 80:
                return "Good for DIC", "#ff5000"
            elif score >= 75:
                return "Minimum for DIC", "#780000"
            else:
                return "CRITICAL - Not suitable for DIC", "#000000"
        else:
            # More realistic thresholds
            if score >= 75:
                return "Excellent for DIC", "#27ae60"
            elif score >= 60:
                return "Very Good for DIC", "#2ecc71"
            elif score >= 45:
                return "Good for DIC", "#f39c12"
            elif score >= 30:
                return "Acceptable for DIC", "#e67e22"
            elif score >= 15:
                return "Challenging for DIC", "#e74c3c"
            else:
                return "Poor for DIC", "#8e44ad"

    def get_recommendation_level(self) -> str:
        """
        Get recommendation level based on score.

        Returns:
            Recommendation level string
        """
        score = self.overall_score

        if score >= 90:
            return "PROCEED"
        elif score >= 75:
            return "PROCEED"
        elif score >= 60:
            return "PROCEED_WITH_CAUTION"
        elif score >= 45:
            return "MARGINAL"
        elif score >= 30:
            return "NOT_RECOMMENDED"
        else:
            return "DO_NOT_PROCEED"

    def calculate_quality_distribution(self) -> Dict[str, float]:
        """
        Calculate quality distribution percentages.

        Returns:
            Dictionary with quality level percentages
        """
        if self.quality_map is None:
            return {}

        # Convert quality map to percentages
        quality_percent = self.quality_map * 100

        # Define quality level ranges
        levels = {
            'poor': (0, 30),
            'acceptable': (30, 60),
            'good': (60, 75),
            'very_good': (75, 90),
            'excellent': (90, 100)
        }

        total_pixels = quality_percent.size
        distribution = {}

        for level, (min_val, max_val) in levels.items():
            mask = (quality_percent >= min_val) & (quality_percent < max_val)
            count = np.sum(mask)
            percentage = (count / total_pixels) * 100
            distribution[level] = percentage

        return distribution

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for the analysis result.

        Returns:
            Dictionary with summary statistics
        """
        stats = {
            'overall_score': self.overall_score,
            'analysis_method': self.analysis_method,
            'spectrum_used': self.spectrum_used,
            'processing_time': self.processing_time,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

        # Add quality assessment
        assessment_text, assessment_color = self.get_quality_assessment()
        stats['quality_assessment'] = assessment_text
        stats['recommendation_level'] = self.get_recommendation_level()

        # Add quality map statistics
        stats.update({
            'min_quality': self.quality_map_stats.min_quality,
            'max_quality': self.quality_map_stats.max_quality,
            'mean_quality': self.quality_map_stats.mean_quality,
            'median_quality': self.quality_map_stats.median_quality,
            'std_quality': self.quality_map_stats.std_quality
        })

        # Add DIC parameters if available
        if self.dic_parameters:
            stats['recommended_facet_size'] = self.dic_parameters.facet_size
            stats['recommended_step_size'] = self.dic_parameters.step_size
            stats['expected_accuracy'] = self.dic_parameters.expected_accuracy

        # Add quality distribution
        stats['quality_distribution'] = self.calculate_quality_distribution()

        return stats

    def validate(self) -> bool:
        """
        Validate the analysis result data.

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not isinstance(self.overall_score, (int, float)):
                return False

            if not 0 <= self.overall_score <= 100:
                return False

            if self.quality_map is not None:
                if not isinstance(self.quality_map, np.ndarray):
                    return False

                if len(self.quality_map.shape) != 2:
                    return False

            if not isinstance(self.analysis_method, str):
                return False

            if not isinstance(self.spectrum_used, str):
                return False

            # Check timestamp
            if not isinstance(self.timestamp, datetime):
                return False

            return True

        except Exception:
            return False

    def __str__(self) -> str:
        """String representation of analysis result."""
        return (f"AnalysisResult(score={self.overall_score:.1f}, "
                f"method={self.analysis_method}, "
                f"spectrum={self.spectrum_used}, "
                f"timestamp={self.timestamp.strftime('%Y-%m-%d %H:%M')})")

    def __repr__(self) -> str:
        """Detailed representation of analysis result."""
        return self.__str__()