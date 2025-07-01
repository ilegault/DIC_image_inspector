# core/image_analyzer.py - Main Analysis Orchestrator

import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any
import logging

from analysis.gradient_analysis import GradientAnalyzer
from analysis.speckle_analysis import SpeckleAnalyzer
from analysis.contrast_analysis import ContrastAnalyzer
from analysis.entropy_analysis import EntropyAnalyzer
from analysis.quality_map.generator import QualityMapGenerator
from core.quality_calculator import QualityCalculator
from core.dic_parameters import DICParameterCalculator
from models.analysis_result import AnalysisResult, QualityMapStats
from models.roi_data import ROIData

logger = logging.getLogger(__name__)


class ImageAnalyzer:
    """
    Main orchestrator for DIC image quality analysis.

    This class coordinates all analysis components and provides a clean
    interface for the UI layer. It handles the complete analysis workflow
    from image preprocessing to final results generation.
    """

    def __init__(self):
        self.gradient_analyzer = GradientAnalyzer()
        self.speckle_analyzer = SpeckleAnalyzer()
        self.contrast_analyzer = ContrastAnalyzer()
        self.entropy_analyzer = EntropyAnalyzer()
        self.quality_map_generator = QualityMapGenerator()
        self.quality_calculator = QualityCalculator()
        self.dic_calculator = DICParameterCalculator()

    def analyze_image(
            self,
            image: np.ndarray,
            roi: Optional[ROIData] = None,
            spectrum_type: str = 'custom_dic',
            subset_size: Optional[int] = None,
            step_size: Optional[int] = None
    ) -> AnalysisResult:
        """
        Perform complete DIC quality analysis on an image.

        Args:
            image: Input image as numpy array (RGB or grayscale)
            roi: Optional ROI data for focused analysis
            spectrum_type: Color spectrum for visualization
            subset_size: Optional custom subset size
            step_size: Optional custom step size

        Returns:
            AnalysisResult: Complete analysis results
        """
        logger.info("Starting image analysis")

        # Validate and preprocess image
        gray_image = self._preprocess_image(image)

        # Generate quality map
        quality_map, visualization = self._generate_quality_map(
            gray_image, roi, spectrum_type, subset_size, step_size
        )

        # Calculate overall quality score
        overall_score = self._calculate_overall_score(quality_map, roi)

        # Calculate detailed metrics
        detailed_metrics = self._calculate_detailed_metrics(gray_image, quality_map, roi)

        # Calculate DIC parameters
        dic_params = self.dic_calculator.calculate_parameters(
            gray_image, overall_score, subset_size
        )

        # Create result object
        
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
        
        result = AnalysisResult(
            overall_score=overall_score,
            quality_map=quality_map,
            quality_map_stats=quality_map_stats,
            analysis_method="ROI-based" if roi else "Full image",
            spectrum_used=spectrum_type,
            dic_parameters=dic_params,
            image_dimensions=image.shape[:2]
        )

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
            roi: Optional[ROIData]
    ) -> Dict[str, Any]:
        """Calculate detailed quality metrics."""
        # Use ROI region if available
        if roi:
            try:
                # Extract just the ROI region for analysis instead of using the full image
                analysis_region = self._extract_roi_region(gray_image, roi)
                roi_scores = self._extract_roi_scores(quality_map, roi)
                stats_data = roi_scores if roi_scores is not None else quality_map.flatten()
            except Exception as e:
                logger.warning(f"ROI region extraction failed: {e}")
                analysis_region = gray_image
                stats_data = quality_map.flatten()
        else:
            analysis_region = gray_image
            stats_data = quality_map.flatten()

        # Calculate individual metrics on the analysis region
        gradient_metrics = self.gradient_analyzer.analyze(analysis_region)
        speckle_metrics = self.speckle_analyzer.analyze(analysis_region)
        contrast_metrics = self.contrast_analyzer.analyze(analysis_region)
        entropy_metrics = self.entropy_analyzer.analyze(analysis_region)

        # Statistical metrics
        quality_stats = {
            'min_quality': float(np.min(stats_data) * 100),
            'max_quality': float(np.max(stats_data) * 100),
            'median_quality': float(np.median(stats_data) * 100),
            'std_quality': float(np.std(stats_data) * 100)
        }

        return {
            'gradient': gradient_metrics,
            'speckle': speckle_metrics,
            'contrast': contrast_metrics,
            'entropy': entropy_metrics,
            'quality_stats': quality_stats
        }

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