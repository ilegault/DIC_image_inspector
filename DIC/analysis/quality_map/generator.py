"""
Quality map generation for DIC image analysis.

Generates spatial quality maps by analyzing image subsets across the entire image
or region of interest. Combines multiple quality metrics to produce a comprehensive
assessment of pattern suitability for DIC correlation.

Usage:
    generator = QualityMapGenerator()
    quality_map, visualization = generator.generate(image, spectrum_type='optimized')
"""

import cv2
import numpy as np
from typing import Tuple, Optional, TYPE_CHECKING, Callable
import logging

from DIC.core.quality_calculator import QualityCalculator
from DIC.core.dic_parameters import DICParameterCalculator
from DIC.analysis.quality_map.colormap import ColormapGenerator

if TYPE_CHECKING:
    from DIC.models.roi_data import ROIData

logger = logging.getLogger(__name__)

# Downscale images larger than this (longest side) before map generation.
# Maps are heavily smoothed, so sub-pixel accuracy is not needed.
# Tune this constant to balance speed vs. map resolution.
MAP_DOWNSCALE_THRESHOLD = 1500


class QualityMapGenerator:
    """
    Generates quality maps for DIC image analysis.

    This class orchestrates the generation of pixel-wise quality assessments
    and their visualization using various color schemes.
    """

    def __init__(self):
        self.quality_calculator = QualityCalculator()
        self.dic_calculator = DICParameterCalculator()
        self.colormap_generator = ColormapGenerator()
        
        # Log the scoring parameters being used
        logger.info(f"Quality map generator initialized with scoring parameters:")
        logger.debug(f"  MIG normalization: {self.quality_calculator.mig_normalization_factor}")
        logger.debug(f"  Ef normalization: {self.quality_calculator.ef_normalization_factor}")
        logger.debug(f"  MIG multiplier: {self.quality_calculator.mig_score_multiplier}")
        logger.debug(f"  Ef multiplier: {self.quality_calculator.ef_score_multiplier}")

        # Default parameters
        self.default_overlap = 0.5
        self.min_subset_size = 11
        self.max_subset_size = 51

    def generate(self,
                 image: np.ndarray,
                 spectrum_type: str = 'custom_dic',
                 subset_size: Optional[int] = None,
                 step_size: Optional[int] = None,
                 roi: Optional['ROIData'] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate quality map and visualization.

        Args:
            image: Input image (grayscale or RGB)
            spectrum_type: Color spectrum for visualization
            subset_size: Optional custom subset size
            step_size: Optional custom step size
            roi: Optional ROI data for focused analysis

        Returns:
            Tuple of (quality_map, visualization)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Handle ROI-based analysis
        if roi is not None:
            logger.info(f"Generating ROI-based quality map for {gray.shape} image with {spectrum_type} spectrum")
            return self._generate_roi_based_map(gray, roi, spectrum_type, subset_size, step_size)
        
        logger.info(f"Generating quality map for {gray.shape} image with {spectrum_type} spectrum")

        # Determine optimal parameters
        if subset_size is None:
            subset_size = self.dic_calculator.determine_optimal_subset_size(gray)

        if step_size is None:
            step_size = max(1, int(subset_size * (1 - self.default_overlap)))

        logger.info(f"Using subset_size={subset_size}, step_size={step_size}")

        # Choose analysis method based on spectrum type
        if spectrum_type == 'controlled':
            # Use controlled (high-precision) method
            quality_map = self._generate_controlled_method_map(gray, subset_size, step_size)
        elif spectrum_type == 'fast':
            # Use fast method for live analysis
            quality_map = self._generate_fast_map(gray, subset_size, step_size)
        else:
            # Use optimized method for 'optimized' and other types
            quality_map = self._generate_standard_map(gray, subset_size, step_size)

        # Generate visualization with smooth interpolation
        visualization = self.colormap_generator.apply_colormap(quality_map, spectrum_type, 'smooth')

        logger.info(f"Quality map generated: range {quality_map.min():.3f}-{quality_map.max():.3f}")

        return quality_map, visualization

    def _generate_standard_map(self, gray: np.ndarray, subset_size: int, step_size: int) -> np.ndarray:
        """Generate standard quality map using overlapping analysis."""
        h, w = gray.shape

        # Initialize maps
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)

        logger.info(
            f"Processing {((h - subset_size) // step_size + 1) * ((w - subset_size) // step_size + 1)} analysis points")

        # Process overlapping subsets
        for y in range(0, h - subset_size + 1, step_size):
            for x in range(0, w - subset_size + 1, step_size):
                # Extract subset
                subset = gray[y:y + subset_size, x:x + subset_size]

                # Calculate quality score
                quality_score = self.quality_calculator.calculate_subset_quality(subset)

                # Map back to image coordinates
                y_end = min(y + subset_size, h)
                x_end = min(x + subset_size, w)
                quality_map[y:y_end, x:x_end] += quality_score
                count_map[y:y_end, x:x_end] += 1

        # Average overlapping regions
        mask = count_map > 0
        quality_map[mask] /= count_map[mask]

        # Apply smoothing for better visualization
        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.5)

        return np.clip(quality_map, 0, 1)

    def _generate_fast_map(self, gray: np.ndarray, subset_size: int, step_size: int) -> np.ndarray:
        """Generate fast quality map with reduced computational overhead."""
        h, w = gray.shape
        
        # Use larger step size for faster processing
        fast_step = max(step_size * 2, subset_size // 2)
        
        # Calculate grid dimensions
        grid_h = (h - subset_size) // fast_step + 1
        grid_w = (w - subset_size) // fast_step + 1
        
        logger.info(f"Fast processing {grid_h * grid_w} analysis points (reduced from standard)")
        
        # Initialize sparse quality grid
        quality_grid = np.zeros((grid_h, grid_w), dtype=np.float32)
        
        # Process with larger steps (fewer analysis points)
        for i, y in enumerate(range(0, h - subset_size + 1, fast_step)):
            for j, x in enumerate(range(0, w - subset_size + 1, fast_step)):
                if i >= grid_h or j >= grid_w:
                    continue
                    
                # Extract subset
                subset = gray[y:y + subset_size, x:x + subset_size]
                
                # Calculate quality score with fast method
                quality_score = self.quality_calculator.calculate_fast_quality(subset)
                quality_grid[i, j] = quality_score
        
        # Interpolate sparse grid to full resolution using simple bilinear interpolation
        # This avoids scipy dependency and is faster
        quality_map = self._bilinear_interpolate_grid(quality_grid, (h, w), fast_step, subset_size)
        
        # Apply light smoothing
        quality_map = cv2.GaussianBlur(quality_map.astype(np.float32), (3, 3), 0.3)
        
        return np.clip(quality_map, 0, 1)

    def _bilinear_interpolate_grid(self, grid: np.ndarray, target_shape: tuple, step: int, subset_size: int) -> np.ndarray:
        """Fast bilinear interpolation of sparse grid to full resolution."""
        h, w = target_shape
        grid_h, grid_w = grid.shape
        
        # Create output array
        result = np.zeros((h, w), dtype=np.float32)
        
        # Fill in the known values first
        for i in range(grid_h):
            for j in range(grid_w):
                y = i * step
                x = j * step
                if y < h and x < w:
                    # Fill a small region around each grid point
                    y_end = min(y + subset_size, h)
                    x_end = min(x + subset_size, w)
                    result[y:y_end, x:x_end] = grid[i, j]
        
        # Simple interpolation for remaining areas using OpenCV
        mask = result == 0
        if np.any(mask):
            # Use OpenCV inpainting for fast interpolation
            mask_uint8 = mask.astype(np.uint8) * 255
            result = cv2.inpaint(result, mask_uint8, 3, cv2.INPAINT_TELEA)
        
        return result

    def _generate_controlled_method_map(self, gray: np.ndarray, facet_size: int, point_distance: int) -> np.ndarray:
        """Generate controlled method high-density quality map."""
        h, w = gray.shape

        # Initialize maps
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)

        logger.info(f"Controlled method analysis: facet={facet_size}, distance={point_distance}")

        # High-density sampling with controlled parameters
        analysis_count = 0
        for y in range(0, h - facet_size + 1, point_distance):
            for x in range(0, w - facet_size + 1, point_distance):
                # Extract subset
                subset = gray[y:y + facet_size, x:x + facet_size]

                # Calculate quality using unified method
                quality_score = self.quality_calculator.calculate_subset_quality(subset)

                # Map back to image coordinates
                y_end = min(y + facet_size, h)
                x_end = min(x + facet_size, w)
                quality_map[y:y_end, x:x_end] += quality_score
                count_map[y:y_end, x:x_end] += 1

                analysis_count += 1

        logger.info(f"Completed {analysis_count} controlled method analysis points")

        # Average overlapping regions
        mask = count_map > 0
        quality_map[mask] /= count_map[mask]

        # Light smoothing for granular results
        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.3)

        return np.clip(quality_map, 0, 1)

    def _generate_roi_based_map(self, gray: np.ndarray, roi: 'ROIData', spectrum_type: str, 
                               subset_size: Optional[int], step_size: Optional[int]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate quality map focused only on the ROI region for efficiency.
        
        This method extracts the ROI bounding box region, performs analysis only on that region,
        then maps the results back to the full image coordinates.
        """
        from DIC.models.roi_data import ROIData  # Import here to avoid circular imports
        
        h, w = gray.shape
        
        # Get ROI bounding box to minimize computation area
        x1, y1, x2, y2 = roi.get_bounding_box()
        
        # Debug output for large images
        if max(w, h) > 1000:
            logger.debug(f"Large image ROI processing - Image size: {w}x{h}")
            logger.debug(f"ROI bounding box: ({x1}, {y1}) to ({x2}, {y2})")
            logger.debug(f"ROI coordinates: {roi.coordinates[:3]}...")  # Show first 3 points
        
        # Clamp to image bounds
        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)
        
        # Extract ROI region
        roi_region = gray[y1:y2, x1:x2].copy()
        roi_h, roi_w = roi_region.shape
        
        logger.info(f"ROI analysis region: {roi_w}x{roi_h} (vs full image {w}x{h})")
        
        if max(w, h) > 1000:
            logger.debug(f"Clamped bounding box: ({x1}, {y1}) to ({x2}, {y2})")
        
        # Determine optimal parameters for ROI region
        if subset_size is None:
            subset_size = self.dic_calculator.determine_optimal_subset_size(roi_region)
        
        if step_size is None:
            step_size = max(1, int(subset_size * (1 - self.default_overlap)))
        
        logger.info(f"ROI analysis using subset_size={subset_size}, step_size={step_size}")
        
        # Create adjusted ROI coordinates for the extracted region
        adjusted_coords = [(x - x1, y - y1) for x, y in roi.coordinates]
        adjusted_roi = ROIData(
            coordinates=adjusted_coords,
            roi_type=roi.roi_type
        )
        
        if max(w, h) > 1000:
            logger.debug(f"Original ROI coords (first 3): {roi.coordinates[:3]}")
            logger.debug(f"Adjusted ROI coords (first 3): {adjusted_coords[:3]}")
            logger.debug(f"Offset applied: ({x1}, {y1})")
        
        # Create mask for the ROI within the extracted region
        roi_mask = adjusted_roi.create_mask(roi_region.shape)
        
        # Generate quality map for the ROI region only
        if spectrum_type == 'controlled':
            roi_quality_map = self._generate_controlled_method_map_with_mask(roi_region, roi_mask, subset_size, step_size)
        else:
            roi_quality_map = self._generate_standard_map_with_mask(roi_region, roi_mask, subset_size, step_size)
        
        # Create full-size quality map and place ROI results
        full_quality_map = np.zeros((h, w), dtype=np.float32)
        full_quality_map[y1:y2, x1:x2] = roi_quality_map
        
        # Generate visualization with smooth interpolation
        visualization = self.colormap_generator.apply_colormap(full_quality_map, spectrum_type, 'smooth')
        
        logger.info(f"ROI quality map generated: range {roi_quality_map.min():.3f}-{roi_quality_map.max():.3f}")
        
        return full_quality_map, visualization
    
    def _generate_standard_map_with_mask(self, gray: np.ndarray, roi_mask: np.ndarray, 
                                        subset_size: int, step_size: int) -> np.ndarray:
        """Generate standard quality map only for pixels within the ROI mask."""
        h, w = gray.shape
        
        # Initialize maps
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)
        
        analysis_count = 0
        
        # Process overlapping subsets, but only analyze those that intersect with ROI
        for y in range(0, h - subset_size + 1, step_size):
            for x in range(0, w - subset_size + 1, step_size):
                # Check if this subset intersects with ROI
                subset_mask = roi_mask[y:y + subset_size, x:x + subset_size]
                
                # Only analyze if at least 25% of the subset is within ROI
                roi_coverage = np.sum(subset_mask > 0) / subset_mask.size
                if roi_coverage < 0.25:
                    continue
                
                # Extract subset
                subset = gray[y:y + subset_size, x:x + subset_size]
                
                # Calculate quality score
                quality_score = self.quality_calculator.calculate_subset_quality(subset)
                
                # Map back to image coordinates, but only for ROI pixels
                y_end = min(y + subset_size, h)
                x_end = min(x + subset_size, w)
                
                # Only update pixels that are within the ROI
                region_mask = roi_mask[y:y_end, x:x_end] > 0
                quality_map[y:y_end, x:x_end][region_mask] += quality_score
                count_map[y:y_end, x:x_end][region_mask] += 1
                
                analysis_count += 1
        
        logger.info(f"Processed {analysis_count} ROI analysis points")
        
        # Average overlapping regions
        mask = count_map > 0
        quality_map[mask] /= count_map[mask]
        
        # Apply smoothing only to ROI region
        roi_pixels = roi_mask > 0
        if np.any(roi_pixels):
            # Create a temporary map for smoothing
            temp_map = quality_map.copy()
            temp_map = cv2.GaussianBlur(temp_map, (3, 3), 0.5)
            quality_map[roi_pixels] = temp_map[roi_pixels]
        
        return np.clip(quality_map, 0, 1)
    
    def _generate_controlled_method_map_with_mask(self, gray: np.ndarray, roi_mask: np.ndarray,
                                           facet_size: int, point_distance: int) -> np.ndarray:
        """Generate controlled method quality map only for pixels within the ROI mask."""
        h, w = gray.shape
        
        # Initialize maps
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)
        
        logger.info(f"Controlled method ROI analysis: facet={facet_size}, distance={point_distance}")
        
        analysis_count = 0
        
        # High-density sampling with controlled parameters, but only for ROI regions
        for y in range(0, h - facet_size + 1, point_distance):
            for x in range(0, w - facet_size + 1, point_distance):
                # Check if this facet intersects with ROI
                facet_mask = roi_mask[y:y + facet_size, x:x + facet_size]
                
                # Only analyze if at least 25% of the facet is within ROI
                roi_coverage = np.sum(facet_mask > 0) / facet_mask.size
                if roi_coverage < 0.25:
                    continue
                
                # Extract subset
                subset = gray[y:y + facet_size, x:x + facet_size]
                
                # Calculate quality using unified method
                quality_score = self.quality_calculator.calculate_subset_quality(subset)
                
                # Map back to image coordinates, but only for ROI pixels
                y_end = min(y + facet_size, h)
                x_end = min(x + facet_size, w)
                
                # Only update pixels that are within the ROI
                region_mask = roi_mask[y:y_end, x:x_end] > 0
                quality_map[y:y_end, x:x_end][region_mask] += quality_score
                count_map[y:y_end, x:x_end][region_mask] += 1
                
                analysis_count += 1
        
        logger.info(f"Completed {analysis_count} controlled method ROI analysis points")
        
        # Average overlapping regions
        mask = count_map > 0
        quality_map[mask] /= count_map[mask]
        
        # Light smoothing only for ROI region
        roi_pixels = roi_mask > 0
        if np.any(roi_pixels):
            temp_map = quality_map.copy()
            temp_map = cv2.GaussianBlur(temp_map, (3, 3), 0.3)
            quality_map[roi_pixels] = temp_map[roi_pixels]
        
        return np.clip(quality_map, 0, 1)

    def generate_component_maps(
            self,
            gray: np.ndarray,
            subset_size: Optional[int] = None,
            step_size: Optional[int] = None,
            roi: Optional['ROIData'] = None
    ) -> dict:
        """
        Generate per-component quality maps in a single subset pass.

        All five maps share a 0-1 domain identical to the overall quality map
        so they can be displayed with the same colormap and color scale.

        Returns:
            dict with keys 'gradient', 'contrast', 'entropy', 'pattern', 'noise',
            each a float32 ndarray in [0, 1] at the input image size.
        """
        # Convert to grayscale if needed
        if len(gray.shape) == 3:
            gray = cv2.cvtColor(gray, cv2.COLOR_RGB2GRAY)

        # Determine parameters (mirror the main generate() defaults)
        if subset_size is None:
            subset_size = self.dic_calculator.determine_optimal_subset_size(gray)
        if step_size is None:
            step_size = max(1, int(subset_size * (1 - self.default_overlap)))

        if roi is not None:
            return self._generate_component_maps_with_roi(gray, roi, subset_size, step_size)

        return self._generate_component_maps_standard(gray, subset_size, step_size)

    def _generate_component_maps_standard(
            self, gray: np.ndarray, subset_size: int, step_size: int
    ) -> dict:
        """Single-pass component map generation over the full image."""
        h, w = gray.shape
        component_names = ['gradient', 'contrast', 'entropy', 'pattern', 'noise']

        accum = {name: np.zeros((h, w), dtype=np.float32) for name in component_names}
        count_map = np.zeros((h, w), dtype=np.int32)

        for y in range(0, h - subset_size + 1, step_size):
            for x in range(0, w - subset_size + 1, step_size):
                subset = gray[y:y + subset_size, x:x + subset_size]
                scores = self.quality_calculator.calculate_subset_component_scores(subset)

                y_end = min(y + subset_size, h)
                x_end = min(x + subset_size, w)

                for name in component_names:
                    accum[name][y:y_end, x:x_end] += scores[name]
                count_map[y:y_end, x:x_end] += 1

        mask = count_map > 0
        result = {}
        for name in component_names:
            m = accum[name].copy()
            m[mask] /= count_map[mask]
            m = cv2.GaussianBlur(m, (3, 3), 0.5)
            result[name] = np.clip(m, 0, 1)

        return result

    def _generate_component_maps_with_roi(
            self, gray: np.ndarray, roi: 'ROIData', subset_size: int, step_size: int
    ) -> dict:
        """Single-pass component map generation restricted to the ROI bounding box."""
        from DIC.models.roi_data import ROIData

        h, w = gray.shape
        x1, y1, x2, y2 = roi.get_bounding_box()
        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)

        roi_region = gray[y1:y2, x1:x2].copy()
        roi_h, roi_w = roi_region.shape

        adjusted_coords = [(x - x1, y - y1) for x, y in roi.coordinates]
        adjusted_roi = ROIData(coordinates=adjusted_coords, roi_type=roi.roi_type)
        roi_mask = adjusted_roi.create_mask(roi_region.shape)

        component_names = ['gradient', 'contrast', 'entropy', 'pattern', 'noise']
        accum = {name: np.zeros((roi_h, roi_w), dtype=np.float32) for name in component_names}
        count_map = np.zeros((roi_h, roi_w), dtype=np.int32)

        for y in range(0, roi_h - subset_size + 1, step_size):
            for x in range(0, roi_w - subset_size + 1, step_size):
                subset_mask = roi_mask[y:y + subset_size, x:x + subset_size]
                if np.sum(subset_mask > 0) / subset_mask.size < 0.25:
                    continue

                subset = roi_region[y:y + subset_size, x:x + subset_size]
                scores = self.quality_calculator.calculate_subset_component_scores(subset)

                y_end = min(y + subset_size, roi_h)
                x_end = min(x + subset_size, roi_w)
                region_mask = roi_mask[y:y_end, x:x_end] > 0

                for name in component_names:
                    accum[name][y:y_end, x:x_end][region_mask] += scores[name]
                count_map[y:y_end, x:x_end][region_mask] += 1

        mask = count_map > 0
        roi_maps = {}
        for name in component_names:
            m = accum[name].copy()
            m[mask] /= count_map[mask]
            temp = cv2.GaussianBlur(m, (3, 3), 0.5)
            roi_pixels = roi_mask > 0
            if np.any(roi_pixels):
                m[roi_pixels] = temp[roi_pixels]
            roi_maps[name] = np.clip(m, 0, 1)

        # Place ROI maps back into full-image-sized arrays
        full_maps = {}
        for name in component_names:
            full_m = np.zeros((h, w), dtype=np.float32)
            full_m[y1:y2, x1:x2] = roi_maps[name]
            full_maps[name] = full_m

        return full_maps

    # ------------------------------------------------------------------
    # Combined single-pass generation (Task 5 performance)
    # ------------------------------------------------------------------

    def generate_with_components(
            self,
            image: np.ndarray,
            roi: Optional['ROIData'] = None,
            spectrum_type: str = 'custom_dic',
            subset_size: Optional[int] = None,
            step_size: Optional[int] = None,
            progress_cb: Optional[Callable[[float, str], None]] = None,
    ) -> Tuple[np.ndarray, np.ndarray, dict]:
        """
        Single-pass generation of the overall quality map AND all 5 component maps.

        Replaces calling generate() + generate_component_maps() separately (two passes).

        For large images (longest side > MAP_DOWNSCALE_THRESHOLD) the analysis is run
        on a downscaled copy; maps are upscaled back with bilinear interpolation.
        Scores computed by get_component_breakdown() (on the full region) are unaffected.

        Args:
            image: Grayscale (or RGB) image.
            roi: Optional ROI.
            spectrum_type: Colormap to apply.
            subset_size: Override subset size.
            step_size: Override step size.
            progress_cb: Optional callback(fraction_0to1, stage_label) called from the
                         analysis thread — schedule any Tk updates with root.after().

        Returns:
            (quality_map_0to1, visualization_rgb, component_maps_dict)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        orig_h, orig_w = gray.shape

        # Downscale guard — only for the map loop, not for the score breakdown
        longest = max(orig_h, orig_w)
        if longest > MAP_DOWNSCALE_THRESHOLD:
            scale = MAP_DOWNSCALE_THRESHOLD / longest
            new_w = max(1, int(orig_w * scale))
            new_h = max(1, int(orig_h * scale))
            work_gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.info(
                f"Downscaled image for map generation: {orig_w}x{orig_h} → {new_w}x{new_h} "
                f"(threshold={MAP_DOWNSCALE_THRESHOLD})"
            )
            # Scale ROI coordinates too if needed
            work_roi = None
            if roi is not None:
                try:
                    from DIC.models.roi_data import ROIData as _ROIData
                    scaled_coords = [(int(x * scale), int(y * scale)) for x, y in roi.coordinates]
                    work_roi = _ROIData(coordinates=scaled_coords, roi_type=roi.roi_type)
                except Exception as e:
                    logger.warning(f"Could not scale ROI for downscaled map: {e}")
                    work_roi = None
            upscale = True
        else:
            work_gray = gray
            work_roi = roi
            upscale = False

        # Determine subset / step for the (possibly downscaled) work image
        if subset_size is None:
            work_subset = self.dic_calculator.determine_optimal_subset_size(work_gray)
        else:
            work_subset = subset_size if not upscale else max(
                self.min_subset_size, int(subset_size * (work_gray.shape[0] / orig_h))
            )
        if step_size is None:
            work_step = max(1, int(work_subset * (1 - self.default_overlap)))
        else:
            work_step = step_size if not upscale else max(1, int(step_size * (work_gray.shape[0] / orig_h)))

        if progress_cb:
            progress_cb(0.0, "Generating quality maps…")

        # Single-pass combined computation
        if work_roi is not None:
            quality_map_work, comp_maps_work = self._combined_pass_with_roi(
                work_gray, work_roi, work_subset, work_step, progress_cb
            )
        else:
            quality_map_work, comp_maps_work = self._combined_pass_standard(
                work_gray, work_subset, work_step, progress_cb
            )

        # Upscale maps back to original image size if we downscaled
        if upscale:
            quality_map = cv2.resize(quality_map_work, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)
            quality_map = np.clip(quality_map, 0, 1)
            comp_maps = {}
            for name, m in comp_maps_work.items():
                comp_maps[name] = np.clip(
                    cv2.resize(m, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR), 0, 1
                )
        else:
            quality_map = quality_map_work
            comp_maps = comp_maps_work

        if progress_cb:
            progress_cb(0.95, "Generating visualization…")

        visualization = self.colormap_generator.apply_colormap(quality_map, spectrum_type, 'smooth')

        if progress_cb:
            progress_cb(1.0, "Done")

        logger.info(f"Combined map generated: range {quality_map.min():.3f}-{quality_map.max():.3f}")
        return quality_map, visualization, comp_maps

    def _combined_pass_standard(
            self, gray: np.ndarray, subset_size: int, step_size: int,
            progress_cb: Optional[Callable] = None
    ) -> Tuple[np.ndarray, dict]:
        """Single subset loop over the full image — returns quality_map + component maps."""
        h, w = gray.shape
        component_names = ['gradient', 'contrast', 'entropy', 'pattern', 'noise']

        quality_accum = np.zeros((h, w), dtype=np.float32)
        comp_accum = {n: np.zeros((h, w), dtype=np.float32) for n in component_names}
        count_map = np.zeros((h, w), dtype=np.int32)

        row_ys = list(range(0, h - subset_size + 1, step_size))
        xs = list(range(0, w - subset_size + 1, step_size))
        n_rows = len(row_ys)

        for i_y, y in enumerate(row_ys):
            for x in xs:
                subset = gray[y:y + subset_size, x:x + subset_size]
                q, comp = self.quality_calculator.calculate_subset_all(subset)

                y_end = min(y + subset_size, h)
                x_end = min(x + subset_size, w)
                quality_accum[y:y_end, x:x_end] += q
                for n in component_names:
                    comp_accum[n][y:y_end, x:x_end] += comp[n]
                count_map[y:y_end, x:x_end] += 1

            if progress_cb and n_rows > 0:
                pct = (i_y + 1) / n_rows
                progress_cb(pct * 0.88, f"Scanning subsets — row {i_y + 1} of {n_rows} ({pct * 100:.0f}%)")

        if progress_cb:
            progress_cb(0.90, "Averaging overlapping regions…")

        mask = count_map > 0
        quality_map = quality_accum.copy()
        quality_map[mask] /= count_map[mask]

        if progress_cb:
            progress_cb(0.93, "Smoothing maps…")

        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.5)
        quality_map = np.clip(quality_map, 0, 1)

        comp_maps = {}
        for n in component_names:
            m = comp_accum[n].copy()
            m[mask] /= count_map[mask]
            m = cv2.GaussianBlur(m, (3, 3), 0.5)
            comp_maps[n] = np.clip(m, 0, 1)

        return quality_map, comp_maps

    def _combined_pass_with_roi(
            self, gray: np.ndarray, roi: 'ROIData', subset_size: int, step_size: int,
            progress_cb: Optional[Callable] = None
    ) -> Tuple[np.ndarray, dict]:
        """Single pass restricted to ROI bounding box."""
        from DIC.models.roi_data import ROIData

        full_h, full_w = gray.shape
        x1, y1, x2, y2 = roi.get_bounding_box()
        x1, x2 = max(0, x1), min(full_w, x2)
        y1, y2 = max(0, y1), min(full_h, y2)

        roi_region = gray[y1:y2, x1:x2].copy()
        roi_h, roi_w = roi_region.shape

        adjusted_coords = [(x - x1, y - y1) for x, y in roi.coordinates]
        adjusted_roi = ROIData(coordinates=adjusted_coords, roi_type=roi.roi_type)
        roi_mask = adjusted_roi.create_mask(roi_region.shape)

        component_names = ['gradient', 'contrast', 'entropy', 'pattern', 'noise']
        quality_accum = np.zeros((roi_h, roi_w), dtype=np.float32)
        comp_accum = {n: np.zeros((roi_h, roi_w), dtype=np.float32) for n in component_names}
        count_map = np.zeros((roi_h, roi_w), dtype=np.int32)

        row_ys = list(range(0, roi_h - subset_size + 1, step_size))
        xs = list(range(0, roi_w - subset_size + 1, step_size))
        n_rows = len(row_ys)

        for i_y, y in enumerate(row_ys):
            for x in xs:
                subset_mask = roi_mask[y:y + subset_size, x:x + subset_size]
                if np.sum(subset_mask > 0) / subset_mask.size < 0.25:
                    continue

                subset = roi_region[y:y + subset_size, x:x + subset_size]
                q, comp = self.quality_calculator.calculate_subset_all(subset)

                y_end = min(y + subset_size, roi_h)
                x_end = min(x + subset_size, roi_w)
                region_mask = roi_mask[y:y_end, x:x_end] > 0

                quality_accum[y:y_end, x:x_end][region_mask] += q
                for n in component_names:
                    comp_accum[n][y:y_end, x:x_end][region_mask] += comp[n]
                count_map[y:y_end, x:x_end][region_mask] += 1

            if progress_cb and n_rows > 0:
                pct = (i_y + 1) / n_rows
                progress_cb(pct * 0.88, f"Scanning subsets — row {i_y + 1} of {n_rows} ({pct * 100:.0f}%)")

        if progress_cb:
            progress_cb(0.90, "Averaging overlapping regions…")

        mask = count_map > 0
        quality_roi = quality_accum.copy()
        quality_roi[mask] /= count_map[mask]

        if progress_cb:
            progress_cb(0.93, "Smoothing maps…")

        roi_pixels = roi_mask > 0
        if np.any(roi_pixels):
            tmp = cv2.GaussianBlur(quality_roi, (3, 3), 0.5)
            quality_roi[roi_pixels] = tmp[roi_pixels]

        comp_roi = {}
        for n in component_names:
            m = comp_accum[n].copy()
            m[mask] /= count_map[mask]
            if np.any(roi_pixels):
                tmp = cv2.GaussianBlur(m, (3, 3), 0.5)
                m[roi_pixels] = tmp[roi_pixels]
            comp_roi[n] = np.clip(m, 0, 1)

        # Embed into full-image arrays
        full_quality = np.zeros((full_h, full_w), dtype=np.float32)
        full_quality[y1:y2, x1:x2] = np.clip(quality_roi, 0, 1)
        full_comp = {}
        for n in component_names:
            fm = np.zeros((full_h, full_w), dtype=np.float32)
            fm[y1:y2, x1:x2] = comp_roi[n]
            full_comp[n] = fm

        return full_quality, full_comp

    def generate_quality_statistics(self, quality_map: np.ndarray) -> dict:
        """Generate statistical summary of quality map."""
        try:
            stats = {
                'min_quality': float(np.min(quality_map) * 100),
                'max_quality': float(np.max(quality_map) * 100),
                'mean_quality': float(np.mean(quality_map) * 100),
                'median_quality': float(np.median(quality_map) * 100),
                'std_quality': float(np.std(quality_map) * 100),
                'q25_quality': float(np.percentile(quality_map, 25) * 100),
                'q75_quality': float(np.percentile(quality_map, 75) * 100)
            }

            # Quality distribution
            excellent_pixels = np.sum(quality_map > 0.8)
            good_pixels = np.sum((quality_map > 0.6) & (quality_map <= 0.8))
            fair_pixels = np.sum((quality_map > 0.4) & (quality_map <= 0.6))
            poor_pixels = np.sum(quality_map <= 0.4)
            total_pixels = quality_map.size

            stats.update({
                'excellent_percentage': float(excellent_pixels / total_pixels * 100),
                'good_percentage': float(good_pixels / total_pixels * 100),
                'fair_percentage': float(fair_pixels / total_pixels * 100),
                'poor_percentage': float(poor_pixels / total_pixels * 100)
            })

            return stats

        except Exception as e:
            logger.error(f"Error generating quality statistics: {e}")
            return {}

    def extract_roi_quality_map(self, quality_map: np.ndarray, roi_mask: np.ndarray) -> np.ndarray:
        """Extract quality map for ROI region only."""
        try:
            if roi_mask.shape != quality_map.shape:
                roi_mask = cv2.resize(roi_mask, (quality_map.shape[1], quality_map.shape[0]))

            # Create ROI quality map
            roi_quality_map = quality_map.copy()
            roi_quality_map[roi_mask == 0] = 0  # Set non-ROI pixels to 0

            return roi_quality_map

        except Exception as e:
            logger.error(f"Error extracting ROI quality map: {e}")
            return quality_map

    def validate_parameters(self, image_shape: Tuple[int, int],
                            subset_size: int, step_size: int) -> bool:
        """Validate generation parameters."""
        h, w = image_shape

        # Check subset size
        if subset_size < self.min_subset_size or subset_size > self.max_subset_size:
            logger.warning(f"Subset size {subset_size} out of valid range")
            return False

        if subset_size >= min(h, w) / 3:
            logger.warning(f"Subset size {subset_size} too large for image {image_shape}")
            return False

        # Check step size
        if step_size < 1 or step_size > subset_size:
            logger.warning(f"Step size {step_size} invalid")
            return False

        # Check if we'll have enough analysis points
        points_x = (w - subset_size) // step_size + 1
        points_y = (h - subset_size) // step_size + 1
        total_points = points_x * points_y

        if total_points < 10:
            logger.warning(f"Too few analysis points: {total_points}")
            return False

        return True

    def get_optimal_parameters(self, image: np.ndarray) -> dict:
        """Get optimal analysis parameters for given image."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        optimal_subset = self.dic_calculator.determine_optimal_subset_size(gray)
        optimal_step = max(1, int(optimal_subset * (1 - self.default_overlap)))

        return {
            'subset_size': optimal_subset,
            'step_size': optimal_step,
            'overlap': self.default_overlap,
            'expected_points': ((gray.shape[0] - optimal_subset) // optimal_step + 1) *
                               ((gray.shape[1] - optimal_subset) // optimal_step + 1)
        }

    def create_legend(self, spectrum_type: str = 'custom_dic', 
                     size: Tuple[int, int] = (400, 100),
                     save_path: Optional[str] = None) -> np.ndarray:
        """
        Create a colorbar legend for the quality map.
        
        Args:
            spectrum_type: Type of color spectrum
            size: (width, height) of the legend
            save_path: Optional path to save the legend
            
        Returns:
            Legend image as numpy array
        """
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        
        if spectrum_type not in self.colormap_generator.spectrum_definitions:
            spectrum_type = 'custom_dic'
            
        spectrum = self.colormap_generator.spectrum_definitions[spectrum_type]
        colors = spectrum['colors']
        
        width, height = size
        
        # Create horizontal gradient
        gradient = np.linspace(0, 1, width).reshape(1, -1)
        gradient = np.repeat(gradient, height, axis=0)
        
        # Apply colormap to gradient
        legend_colored = self.colormap_generator.apply_colormap(gradient, spectrum_type, 'smooth')
        
        if save_path:
            # Create detailed legend with matplotlib
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), 
                                          gridspec_kw={'height_ratios': [1, 3]})
            
            # Show colorbar
            ax1.imshow(legend_colored, aspect='auto', extent=[0, 1, 0, 1])
            ax1.set_xlim(0, 1)
            ax1.set_ylim(0, 1)
            ax1.set_xlabel('Quality Score (0 = Poor, 1 = Excellent)', fontsize=12, fontweight='bold')
            ax1.set_title(f'{spectrum["name"]} - {spectrum["description"]}', fontsize=14, fontweight='bold')
            
            # Add tick marks
            n_colors = len(colors)
            tick_positions = np.linspace(0, 1, n_colors)
            ax1.set_xticks(tick_positions)
            ax1.set_xticklabels([f'{pos:.2f}' for pos in tick_positions])
            ax1.set_yticks([])
            
            # Create detailed description
            ax2.axis('off')
            
            # Color descriptions
            y_positions = np.linspace(0.9, 0.1, len(colors))
            
            for i, (r, g, b, description) in enumerate(colors):
                # Color patch
                color_norm = (r/255, g/255, b/255)
                rect = Rectangle((0.05, y_positions[i] - 0.05), 0.1, 0.08, 
                               facecolor=color_norm, edgecolor='black', linewidth=1)
                ax2.add_patch(rect)
                
                # Quality range
                if i == 0:
                    quality_range = "0.00 - 0.17"
                elif i == len(colors) - 1:
                    quality_range = "0.83 - 1.00"
                else:
                    start = i / (len(colors) - 1)
                    end = (i + 1) / (len(colors) - 1)
                    quality_range = f"{start:.2f} - {end:.2f}"
                
                # Description text
                ax2.text(0.2, y_positions[i], f'{quality_range}: {description}', 
                        va='center', fontsize=11, fontweight='bold')
            
            # Usage notes
            notes_text = ("Usage Notes:\n"
                         "• Higher values indicate better quality for DIC analysis\n"
                         "• Quality is based on gradient content, contrast, and pattern complexity\n"
                         "• Values below 0.2 are generally unsuitable for DIC correlation")
            
            ax2.text(0.05, 0.05, notes_text, va='bottom', fontsize=10, 
                    transform=ax2.transAxes, bbox=dict(boxstyle="round,pad=0.3", 
                    facecolor="lightgray", alpha=0.7))
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Legend saved to: {save_path}")
        
        return legend_colored