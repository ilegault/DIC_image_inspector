"""
Main image analysis orchestrator for DIC quality assessment.

This module provides the central coordination layer for DIC image quality analysis.
It orchestrates multiple analysis components (gradient, speckle, contrast, entropy)
and generates comprehensive quality assessments with DIC parameter recommendations.
The ImageAnalyzer class serves as the main entry point for all analysis operations.

Usage:
    from core.image_analyzer import ImageAnalyzer

    analyzer = ImageAnalyzer()
    results = analyzer.analyze_image(image, roi=roi_data, spectrum_type='optimized')
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any, Callable
import logging

from DIC.analysis.quality_map.generator import QualityMapGenerator
from DIC.core.quality_calculator import QualityCalculator
from DIC.core.dic_parameters import DICParameterCalculator
from DIC.models.analysis_result import AnalysisResult, QualityMapStats
from DIC.models.roi_data import ROIData

logger = logging.getLogger(__name__)


class ImageAnalyzer:
    """
    Main orchestrator for DIC image quality analysis.

    This class coordinates all analysis main_components and provides a clean
    interface for the UI layer. It handles the complete analysis workflow
    from image preprocessing to final results generation.
    """

    def __init__(self):
        self.quality_map_generator = QualityMapGenerator()
        self.quality_calculator = QualityCalculator()
        self.dic_calculator = DICParameterCalculator()

    def analyze_image(
            self,
            image: np.ndarray,
            roi: Optional[ROIData] = None,
            spectrum_type: str = 'optimized',
            subset_size: Optional[int] = None,
            step_size: Optional[int] = None,
            progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> AnalysisResult:
        """
        Perform complete DIC quality analysis on an image.

        Args:
            image: Input image as numpy array (RGB or grayscale)
            roi: Optional ROI data for focused analysis
            spectrum_type: Color spectrum for visualization
            subset_size: Optional custom subset size
            step_size: Optional custom step size
            progress_callback: Optional callable(fraction_0to1, label) for progress reporting.
                               Called from the analysis thread — use root.after() for Tk updates.

        Returns:
            AnalysisResult: Complete analysis results
        """
        logger.info("Starting image analysis")

        def _progress(frac: float, label: str = ""):
            if progress_callback:
                progress_callback(frac, label)

        # Validate and preprocess image
        _progress(0.02, "Preprocessing…")
        gray_image = self._preprocess_image(image)

        # Single-pass: generate overall quality map + component maps together
        _progress(0.05, "Starting map generation…")
        try:
            quality_map, visualization, metric_maps = self.quality_map_generator.generate_with_components(
                gray_image,
                roi=roi,
                spectrum_type=spectrum_type,
                subset_size=subset_size,
                step_size=step_size,
                progress_cb=lambda f, lbl: _progress(0.05 + f * 0.75, lbl),
            )
        except Exception as e:
            logger.warning(f"Combined map generation failed, falling back: {e}")
            quality_map, visualization = self._generate_quality_map(
                gray_image, roi, spectrum_type, subset_size, step_size
            )
            metric_maps = None

        # Calculate overall quality score
        _progress(0.82, "Calculating overall score…")
        overall_score = self._calculate_overall_score(quality_map, roi)

        # Calculate detailed metrics (normalized breakdown via QualityCalculator)
        _progress(0.84, "Computing metric breakdown…")
        detailed_metrics = self._calculate_detailed_metrics(
            gray_image, quality_map, roi,
            progress_callback=lambda f, lbl: _progress(0.84 + f * 0.09, lbl),
        )

        # Calculate DIC parameters
        _progress(0.94, "Estimating DIC parameters…")
        dic_params = self.dic_calculator.calculate_parameters(
            gray_image, overall_score, subset_size
        )

        # Create quality map stats
        quality_map_stats = QualityMapStats(
            min_quality=float(np.min(quality_map) * 100),
            max_quality=float(np.max(quality_map) * 100),
            mean_quality=float(np.mean(quality_map) * 100),
            median_quality=float(np.median(quality_map) * 100),
            std_quality=float(np.std(quality_map) * 100),
            percentile_25=float(np.percentile(quality_map * 100, 25)),
            percentile_75=float(np.percentile(quality_map * 100, 75))
        )

        _progress(0.98, "Finalising…")
        result = AnalysisResult(
            overall_score=overall_score,
            quality_map=quality_map,
            quality_map_stats=quality_map_stats,
            analysis_method="ROI-based" if roi else "Full image",
            spectrum_used=spectrum_type,
            dic_parameters=dic_params,
            image_dimensions=image.shape[:2],
            component_scores=detailed_metrics,
            metric_maps=metric_maps,
        )

        _progress(1.0, "Done")
        logger.info(f"Analysis complete. Overall score: {overall_score:.1f}")
        return result

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale if needed and validate."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        if gray.size == 0:
            raise ValueError("Empty image provided")

        return gray

    def _generate_quality_map(
            self,
            gray_image: np.ndarray,
            roi: Optional[ROIData],
            spectrum_type: str,
            subset_size: Optional[int],
            step_size: Optional[int]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate quality map and visualization."""
        return self.quality_map_generator.generate(
            gray_image,
            spectrum_type=spectrum_type,
            subset_size=subset_size,
            step_size=step_size,
            roi=roi
        )

    def _calculate_overall_score(
            self,
            quality_map: np.ndarray,
            roi: Optional[ROIData]
    ) -> float:
        """Calculate overall quality score from quality map."""
        if roi:
            roi_scores = self._extract_roi_scores(quality_map, roi)
            if roi_scores is not None and len(roi_scores) > 0:
                return float(np.mean(roi_scores) * 100)

        return float(np.mean(quality_map) * 100)

    def _extract_roi_scores(
            self,
            quality_map: np.ndarray,
            roi: ROIData
    ) -> Optional[np.ndarray]:
        """Extract quality scores from ROI region."""
        try:
            mask = roi.create_mask(quality_map.shape[:2])
            roi_pixels = mask > 0

            if np.sum(roi_pixels) == 0:
                return None

            return quality_map[roi_pixels]
        except Exception as e:
            logger.error(f"Error extracting ROI scores: {e}")
            return None

    def _extract_roi_region(
            self,
            image: np.ndarray,
            roi: ROIData
    ) -> np.ndarray:
        """
        Extract just the ROI region from the image for efficient analysis.
        
        This method extracts the bounding box region containing the ROI,
        then applies the ROI mask to focus analysis only on the relevant pixels.
        This significantly reduces computation time for large images with small ROIs.
        """
        try:
            # Get bounding box to minimize the region we work with
            x1, y1, x2, y2 = roi.get_bounding_box()
            
            # Clamp to image bounds
            h, w = image.shape[:2]
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)
            
            # Extract bounding box region
            roi_region = image[y1:y2, x1:x2].copy()
            
            # Create mask for the extracted region
            # Adjust ROI coordinates to the extracted region coordinate system
            adjusted_roi = ROIData(
                coordinates=[(x - x1, y - y1) for x, y in roi.coordinates],
                roi_type=roi.roi_type
            )
            
            # Create mask for the extracted region
            mask = adjusted_roi.create_mask(roi_region.shape[:2])
            
            # Apply mask to focus on ROI pixels only
            # Set non-ROI pixels to the mean value to avoid affecting analysis
            if np.any(mask > 0):
                roi_pixels = mask > 0
                mean_value = np.mean(roi_region[roi_pixels])
                roi_region[~roi_pixels] = mean_value
            
            return roi_region
            
        except Exception as e:
            logger.error(f"Error extracting ROI region: {e}")
            # Fallback to full image
            return image

    def _calculate_detailed_metrics(
            self,
            gray_image: np.ndarray,
            quality_map: np.ndarray,
            roi: Optional[ROIData],
            progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate normalized per-metric breakdown via QualityCalculator.

        Returns the canonical component_scores dict shape (see get_component_breakdown)
        which is attached to the result and shown in the results popup.
        """
        # Use ROI region if available for focused analysis
        if roi:
            try:
                analysis_region = self._extract_roi_region(gray_image, roi)
            except Exception as e:
                logger.warning(f"ROI region extraction failed: {e}")
                analysis_region = gray_image
        else:
            analysis_region = gray_image

        try:
            return self.quality_calculator.get_component_breakdown(
                analysis_region, progress_cb=progress_callback
            )
        except Exception as e:
            logger.warning(f"Component breakdown failed: {e}")
            return {}

    def get_optimal_subset_size(self, image: np.ndarray) -> int:
        """Get optimal subset size for given image."""
        gray = self._preprocess_image(image)
        return self.dic_calculator.determine_optimal_subset_size(gray)

    def validate_analysis_parameters(
            self,
            image: np.ndarray,
            subset_size: Optional[int] = None
    ) -> bool:
        """Validate that analysis parameters are suitable for the image."""
        h, w = image.shape[:2]
        min_dim = min(h, w)

        if subset_size and subset_size >= min_dim / 3:
            return False

        return min_dim >= 50  # Minimum reasonable image size

    def update_quality_scoring_parameters(self, **kwargs):
        """
        Update quality scoring parameters.
        
        Args:
            **kwargs: Parameters to update (mig_norm_factor, ef_norm_factor, 
                     mig_score_multiplier, ef_score_multiplier)
        """
        self.quality_calculator.update_scoring_parameters(**kwargs)
        logger.info("Quality scoring parameters updated")