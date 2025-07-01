# analysis/quality_map/generator.py - Quality Map Generator

import cv2
import numpy as np
from typing import Tuple, Optional, TYPE_CHECKING
import logging

from core.quality_calculator import QualityCalculator
from core.dic_parameters import DICParameterCalculator
from analysis.quality_map.colormap import ColormapGenerator

if TYPE_CHECKING:
    from models.roi_data import ROIData

logger = logging.getLogger(__name__)


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

        # Handle ZEISS-style analysis
        if spectrum_type == 'zeiss_style_dic':
            quality_map = self._generate_zeiss_style_map(gray, subset_size, step_size)
        else:
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

    def _generate_zeiss_style_map(self, gray: np.ndarray, facet_size: int, point_distance: int) -> np.ndarray:
        """Generate ZEISS-style high-density quality map."""
        h, w = gray.shape

        # Initialize maps
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)

        logger.info(f"ZEISS-style analysis: facet={facet_size}, distance={point_distance}")

        # High-density sampling like ZEISS
        analysis_count = 0
        for y in range(0, h - facet_size + 1, point_distance):
            for x in range(0, w - facet_size + 1, point_distance):
                # Extract subset
                subset = gray[y:y + facet_size, x:x + facet_size]

                # Calculate ZEISS-style quality
                quality_score = self._calculate_zeiss_quality(subset)

                # Map back to image coordinates
                y_end = min(y + facet_size, h)
                x_end = min(x + facet_size, w)
                quality_map[y:y_end, x:x_end] += quality_score
                count_map[y:y_end, x:x_end] += 1

                analysis_count += 1

        logger.info(f"Completed {analysis_count} ZEISS-style analysis points")

        # Average overlapping regions
        mask = count_map > 0
        quality_map[mask] /= count_map[mask]

        # Light smoothing for granular results
        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.3)

        return np.clip(quality_map, 0, 1)

    def _calculate_zeiss_quality(self, subset: np.ndarray) -> float:
        """Calculate ZEISS-style quality focusing on correlation reliability."""
        if subset.size == 0:
            return 0.0

        try:
            # Calculate gradients
            grad_x = cv2.Sobel(subset, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(subset, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

            # 1. Gradient content analysis (50% weight) - More strict
            mean_gradient = np.mean(gradient_magnitude)
            gradient_std = np.std(gradient_magnitude)

            # More strict gradient normalization for DIC
            gradient_score = min(1.0, mean_gradient / 40.0)  # Reduced threshold for stricter assessment
            
            # Heavy penalty for very low gradient regions
            if mean_gradient < 5.0:  # Very low gradient
                gradient_score *= 0.1  # Heavy penalty
            elif mean_gradient < 10.0:  # Low gradient
                gradient_score *= 0.3  # Moderate penalty

            # Gradient distribution quality - more strict requirements
            gradient_cv = gradient_std / (mean_gradient + 1e-6)
            if 0.8 <= gradient_cv <= 1.5:  # Narrower optimal range
                distribution_bonus = 1.0
            elif 0.5 <= gradient_cv <= 2.0:  # Acceptable range
                distribution_bonus = 0.7
            elif 0.3 <= gradient_cv <= 3.0:  # Poor range
                distribution_bonus = 0.4
            else:
                distribution_bonus = 0.2  # Very poor

            gradient_quality = gradient_score * distribution_bonus

            # 2. Pattern uniqueness (25% weight) - More strict
            mean_intensity = np.mean(subset)
            intensity_std = np.std(subset)
            contrast_ratio = intensity_std / (mean_intensity + 1e-6)

            # More strict contrast assessment
            contrast_score = min(1.0, contrast_ratio * 1.5)  # Reduced multiplier
            
            # Heavy penalty for very low contrast regions
            if contrast_ratio < 0.05:  # Very low contrast
                contrast_score *= 0.1
            elif contrast_ratio < 0.1:  # Low contrast
                contrast_score *= 0.3

            # Pattern complexity using simplified LBP
            complexity_score = self._calculate_pattern_complexity(subset)

            uniqueness_quality = contrast_score * 0.7 + complexity_score * 0.3

            # 3. Noise resistance (15% weight) - More strict
            if subset.shape[0] > 3 and subset.shape[1] > 3:
                smoothed = cv2.GaussianBlur(subset, (3, 3), 0.5)
                noise = subset.astype(float) - smoothed.astype(float)
                noise_std = np.std(noise)
                signal_std = np.std(smoothed)
                snr = signal_std / (noise_std + 1e-6)
                noise_quality = min(1.0, snr / 15.0)  # More strict SNR requirement
                
                # Heavy penalty for very noisy regions
                if snr < 5.0:  # Very low SNR
                    noise_quality *= 0.2
                elif snr < 10.0:  # Low SNR
                    noise_quality *= 0.5
            else:
                noise_quality = 0.3  # Lower default for small regions

            # 4. Focus quality (10% weight) - More strict
            laplacian = cv2.Laplacian(subset, cv2.CV_64F)
            laplacian_var = np.var(laplacian)
            focus_score = min(1.0, laplacian_var / 800.0)  # More strict threshold
            
            # Heavy penalty for very blurry regions
            if laplacian_var < 50.0:  # Very low focus
                focus_score *= 0.1
            elif laplacian_var < 100.0:  # Low focus
                focus_score *= 0.3

            # Combine all factors (ZEISS-style weighting)
            overall_quality = (
                    gradient_quality * 0.50 +
                    uniqueness_quality * 0.25 +
                    noise_quality * 0.15 +
                    focus_score * 0.10
            )
            
            # Apply critical quality checks - if any factor is extremely poor, heavily penalize
            critical_factors = []
            if gradient_quality < 0.1:
                critical_factors.append("gradient")
            if uniqueness_quality < 0.1:
                critical_factors.append("contrast")
            if noise_quality < 0.1:
                critical_factors.append("noise")
            if focus_score < 0.1:
                critical_factors.append("focus")
            
            # If multiple critical factors, apply severe penalty
            if len(critical_factors) >= 2:
                overall_quality *= 0.1  # Severe penalty for multiple critical issues
            elif len(critical_factors) == 1:
                overall_quality *= 0.3  # Moderate penalty for single critical issue

            return max(0.0, min(1.0, overall_quality))

        except Exception as e:
            logger.warning(f"Error in ZEISS quality calculation: {e}")
            return 0.0

    def _calculate_pattern_complexity(self, subset: np.ndarray) -> float:
        """Calculate pattern complexity using simplified texture analysis."""
        if subset.shape[0] < 3 or subset.shape[1] < 3:
            return 0.5

        try:
            center = subset[1:-1, 1:-1]

            # 8-neighborhood comparison
            neighbors = [
                subset[:-2, :-2], subset[:-2, 1:-1], subset[:-2, 2:],
                subset[1:-1, :-2], subset[1:-1, 2:],
                subset[2:, :-2], subset[2:, 1:-1], subset[2:, 2:]
            ]

            texture_variations = 0
            for neighbor in neighbors:
                texture_variations += np.sum(neighbor > center)

            if center.size > 0:
                texture_complexity = texture_variations / (center.size * len(neighbors))
                return min(1.0, texture_complexity * 4)
            else:
                return 0.5

        except Exception:
            return 0.5

    def _generate_roi_based_map(self, gray: np.ndarray, roi: 'ROIData', spectrum_type: str, 
                               subset_size: Optional[int], step_size: Optional[int]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate quality map focused only on the ROI region for efficiency.
        
        This method extracts the ROI bounding box region, performs analysis only on that region,
        then maps the results back to the full image coordinates.
        """
        from models.roi_data import ROIData  # Import here to avoid circular imports
        
        h, w = gray.shape
        
        # Get ROI bounding box to minimize computation area
        x1, y1, x2, y2 = roi.get_bounding_box()
        
        # Debug output for large images
        if max(w, h) > 1000:
            logger.info(f"DEBUG: Large image ROI processing - Image size: {w}x{h}")
            logger.info(f"DEBUG: ROI bounding box: ({x1}, {y1}) to ({x2}, {y2})")
            logger.info(f"DEBUG: ROI coordinates: {roi.coordinates[:3]}...")  # Show first 3 points
        
        # Clamp to image bounds
        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)
        
        # Extract ROI region
        roi_region = gray[y1:y2, x1:x2].copy()
        roi_h, roi_w = roi_region.shape
        
        logger.info(f"ROI analysis region: {roi_w}x{roi_h} (vs full image {w}x{h})")
        
        if max(w, h) > 1000:
            logger.info(f"DEBUG: Clamped bounding box: ({x1}, {y1}) to ({x2}, {y2})")
        
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
            logger.info(f"DEBUG: Original ROI coords (first 3): {roi.coordinates[:3]}")
            logger.info(f"DEBUG: Adjusted ROI coords (first 3): {adjusted_coords[:3]}")
            logger.info(f"DEBUG: Offset applied: ({x1}, {y1})")
        
        # Create mask for the ROI within the extracted region
        roi_mask = adjusted_roi.create_mask(roi_region.shape)
        
        # Generate quality map for the ROI region only
        if spectrum_type == 'zeiss_style_dic':
            roi_quality_map = self._generate_zeiss_style_map_with_mask(roi_region, roi_mask, subset_size, step_size)
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
    
    def _generate_zeiss_style_map_with_mask(self, gray: np.ndarray, roi_mask: np.ndarray,
                                           facet_size: int, point_distance: int) -> np.ndarray:
        """Generate ZEISS-style quality map only for pixels within the ROI mask."""
        h, w = gray.shape
        
        # Initialize maps
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)
        
        logger.info(f"ZEISS-style ROI analysis: facet={facet_size}, distance={point_distance}")
        
        analysis_count = 0
        
        # High-density sampling like ZEISS, but only for ROI regions
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
                
                # Calculate ZEISS-style quality
                quality_score = self._calculate_zeiss_quality(subset)
                
                # Map back to image coordinates, but only for ROI pixels
                y_end = min(y + facet_size, h)
                x_end = min(x + facet_size, w)
                
                # Only update pixels that are within the ROI
                region_mask = roi_mask[y:y_end, x:x_end] > 0
                quality_map[y:y_end, x:x_end][region_mask] += quality_score
                count_map[y:y_end, x:x_end][region_mask] += 1
                
                analysis_count += 1
        
        logger.info(f"Completed {analysis_count} ZEISS-style ROI analysis points")
        
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
        import matplotlib.colors as mcolors
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