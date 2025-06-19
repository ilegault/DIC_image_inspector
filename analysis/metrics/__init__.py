# analysis/metrics/__init__.py

# Import contrast measurement metrics
from .contrast_metrics import (
    calculate_contrast,
    calculate_local_contrast,
    analyze_histogram_contrast,
    analyze_intensity_distribution,
    measure_bimodality,
    measure_intensity_contrast
)

# Import feature/speckle metrics
from .feature_metrics import (
    calculate_speckle_density,
    analyze_feature_size,
    evaluate_gradient_quality,
    measure_intensity_contrast,
    calculate_feature_spacing,
    compute_feature_coverage,
    assess_feature_quality
)

# Import spatial metrics
from .spatial_metrics import (
    calculate_pattern_uniformity,
    calculate_uniformity,
    analyze_edge_quality,
    calculate_gradient_magnitude,
    analyze_nearest_neighbor_distribution,
    calculate_spatial_coverage,
    evaluate_spatial_quality,
)

# Import correlation metrics
from .correlation_metrics import (
    calculate_zncc,
    calculate_subset_distinctiveness,
    evaluate_correlation_potential,
    generate_correlation_map
)

# Import pattern metrics
from .pattern_metrics import (
    analyze_pattern_isotropy,
    analyze_pattern_frequency,
    analyze_pattern_randomness,
    evaluate_pattern_quality
)

# Import noise metrics
from .noise_metrics import (
    estimate_image_noise,
    analyze_local_noise,
    estimate_noise_frequency,
    compute_noise_metrics
)

# Import the metrics manager
from .metrics_manager import MetricsManager

# Define what gets exported with "from analysis.metrics import *"
__all__ = [
    # Contrast metrics
    'calculate_contrast',
    'calculate_local_contrast',
    'analyze_histogram_contrast',
    'analyze_intensity_distribution',
    'measure_bimodality',
    'measure_intensity_contrast',

    # Feature metrics
    'calculate_speckle_density',
    'analyze_feature_size',
    'evaluate_gradient_quality',
    'measure_intensity_contrast',
    'compute_feature_coverage',
    'calculate_feature_spacing',
    'assess_feature_quality',

    # Spatial metrics
    'calculate_pattern_uniformity',
    'calculate_uniformity',
    'analyze_edge_quality',
    'calculate_gradient_magnitude',
    'analyze_nearest_neighbor_distribution',
    'calculate_spatial_coverage',
    'evaluate_spatial_quality',

    # Correlation metrics
    'calculate_zncc',
    'calculate_subset_distinctiveness',
    'evaluate_correlation_potential',
    'generate_correlation_map',

    # Pattern metrics
    'analyze_pattern_isotropy',
    'analyze_pattern_frequency',
    'analyze_pattern_randomness',
    'evaluate_pattern_quality',

    # Noise metrics
    'estimate_image_noise',
    'analyze_local_noise',
    'estimate_noise_frequency',
    'compute_noise_metrics',

    # Metrics manager
    'MetricsManager'
]