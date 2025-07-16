# analysis/quality_map/debug_generator.py - Debug Quality Map Generator

import cv2
import numpy as np
from typing import Tuple, Optional, TYPE_CHECKING, Dict
import logging
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle

from core.quality_calculator import QualityCalculator
from core.dic_parameters import DICParameterCalculator
from analysis.quality_map.colormap import ColormapGenerator
from utils.constants import COLOR_SPECTRUMS, QUALITY_THRESHOLDS
from analysis.gradient_analysis import GradientAnalyzer

if TYPE_CHECKING:
    from models.roi_data import ROIData

logger = logging.getLogger(__name__)


class DebugQualityMapGenerator:
    """
    Debug version of Quality Map Generator with extensive logging and visualization.
    
    This class provides detailed debugging information about the quality map generation
    process, including intermediate results, statistics, and visualizations.
    """

    def __init__(self):
        self.gradient_analyzer = GradientAnalyzer()
        self.quality_calculator = QualityCalculator()
        self.dic_calculator = DICParameterCalculator()
        self.colormap_generator = ColormapGenerator()

        # Default parameters
        self.default_overlap = 0.5
        self.min_subset_size = 11
        self.max_subset_size = 51
        
        # Debug storage
        self.debug_info = {}
        self.subset_scores = []
        self.processing_stats = {}

    def generate_with_debug(self,
                           image: np.ndarray,
                           spectrum_type: str = 'custom_dic',
                           subset_size: Optional[int] = None,
                           step_size: Optional[int] = None,
                           roi: Optional['ROIData'] = None) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Generate quality map with comprehensive debugging information.

        Args:
            image: Input image (grayscale or RGB)
            spectrum_type: Color spectrum for visualization
            subset_size: Optional custom subset size
            step_size: Optional custom step size
            roi: Optional ROI data for focused analysis

        Returns:
            Tuple of (quality_map, visualization, debug_info)
        """
        print(f"\n=== DEBUG QUALITY MAP GENERATION ===")
        print(f"Input image shape: {image.shape}")
        print(f"Input image dtype: {image.dtype}")
        print(f"Input image range: {image.min()} - {image.max()}")
        print(f"Spectrum type: {spectrum_type}")
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            print(f"Converted RGB to grayscale")
        else:
            gray = image.copy()
        
        print(f"Grayscale image shape: {gray.shape}")
        print(f"Grayscale image range: {gray.min()} - {gray.max()}")

        # Handle ROI-based analysis
        if roi is not None:
            print(f"ROI-based analysis requested")
            return self._generate_roi_based_map_debug(gray, roi, spectrum_type, subset_size, step_size)
        
        # Determine optimal parameters
        if subset_size is None:
            subset_size = self.dic_calculator.determine_optimal_subset_size(gray)
        
        if step_size is None:
            step_size = max(1, int(subset_size * (1 - self.default_overlap)))
        
        print(f"Analysis parameters:")
        print(f"  - Subset size: {subset_size}")
        print(f"  - Step size: {step_size}")
        print(f"  - Overlap: {(1 - step_size/subset_size)*100:.1f}%")

        # Calculate expected number of analysis points
        h, w = gray.shape
        expected_points = ((h - subset_size) // step_size + 1) * ((w - subset_size) // step_size + 1)
        print(f"  - Expected analysis points: {expected_points}")

        # Generate quality map with debugging
        if spectrum_type == 'controlled':
            quality_map, debug_info = self._generate_controlled_method_map_debug(gray, subset_size, step_size)
        else:
            quality_map, debug_info = self._generate_standard_map_debug(gray, subset_size, step_size)

        print(f"\nQuality map statistics:")
        print(f"  - Shape: {quality_map.shape}")
        print(f"  - Range: {quality_map.min():.4f} - {quality_map.max():.4f}")
        print(f"  - Mean: {quality_map.mean():.4f}")
        print(f"  - Std: {quality_map.std():.4f}")
        print(f"  - Non-zero pixels: {np.count_nonzero(quality_map)}")

        # Generate visualization with debugging
        visualization = self._generate_visualization_debug(quality_map, spectrum_type)
        
        # Create comprehensive debug info
        debug_info.update({
            'input_image_shape': image.shape,
            'grayscale_shape': gray.shape,
            'subset_size': subset_size,
            'step_size': step_size,
            'spectrum_type': spectrum_type,
            'quality_map_stats': {
                'min': float(quality_map.min()),
                'max': float(quality_map.max()),
                'mean': float(quality_map.mean()),
                'std': float(quality_map.std()),
                'non_zero_count': int(np.count_nonzero(quality_map))
            }
        })

        return quality_map, visualization, debug_info

    def _generate_standard_map_debug(self, gray: np.ndarray, subset_size: int, step_size: int) -> Tuple[np.ndarray, Dict]:
        """Generate standard quality map with debugging."""
        h, w = gray.shape
        print(f"\n--- Standard Quality Map Generation ---")
        
        # Initialize maps
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)
        
        # Debug storage
        subset_scores = []
        processing_count = 0
        
        print(f"Processing subsets...")
        
        # Process overlapping subsets
        for y in range(0, h - subset_size + 1, step_size):
            for x in range(0, w - subset_size + 1, step_size):
                # Extract subset
                subset = gray[y:y + subset_size, x:x + subset_size]
                
                # Calculate quality score
                quality_score = self.quality_calculator.calculate_subset_quality(subset)
                subset_scores.append(quality_score)
                
                # Debug first few subsets
                if processing_count < 5:
                    print(f"  Subset {processing_count}: pos=({x},{y}), score={quality_score:.4f}")
                    print(f"    Subset range: {subset.min()} - {subset.max()}")
                    print(f"    Subset mean: {subset.mean():.2f}, std: {subset.std():.2f}")
                
                # Map back to image coordinates
                y_end = min(y + subset_size, h)
                x_end = min(x + subset_size, w)
                quality_map[y:y_end, x:x_end] += quality_score
                count_map[y:y_end, x:x_end] += 1
                
                processing_count += 1
        
        print(f"Processed {processing_count} subsets")
        print(f"Subset scores range: {min(subset_scores):.4f} - {max(subset_scores):.4f}")
        print(f"Subset scores mean: {np.mean(subset_scores):.4f}")
        
        # Average overlapping regions
        mask = count_map > 0
        print(f"Pixels with coverage: {np.sum(mask)} / {mask.size} ({np.sum(mask)/mask.size*100:.1f}%)")
        
        quality_map[mask] /= count_map[mask]
        
        print(f"After averaging - Quality map range: {quality_map.min():.4f} - {quality_map.max():.4f}")
        
        # Apply smoothing for better visualization
        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.5)
        
        print(f"After smoothing - Quality map range: {quality_map.min():.4f} - {quality_map.max():.4f}")
        
        # Clip to valid range
        quality_map = np.clip(quality_map, 0, 1)
        
        debug_info = {
            'processing_count': processing_count,
            'subset_scores': subset_scores,
            'coverage_percentage': float(np.sum(mask)/mask.size*100),
            'method': 'standard'
        }
        
        return quality_map, debug_info

    def _generate_controlled_method_map_debug(self, gray: np.ndarray, facet_size: int, point_distance: int) -> Tuple[np.ndarray, Dict]:
        """Generate controlled method quality map with debugging."""
        h, w = gray.shape
        print(f"\n--- Controlled Method Quality Map Generation ---")
        print(f"Facet size: {facet_size}, Point distance: {point_distance}")
        
        # Initialize maps
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)
        
        # Debug storage
        subset_scores = []
        processing_count = 0
        
        print(f"Processing ZEISS-style analysis...")
        
        # High-density sampling like ZEISS
        for y in range(0, h - facet_size + 1, point_distance):
            for x in range(0, w - facet_size + 1, point_distance):
                # Extract subset
                subset = gray[y:y + facet_size, x:x + facet_size]
                
                # Calculate ZEISS-style quality
                quality_score = self._calculate_zeiss_quality_debug(subset, processing_count < 5)
                subset_scores.append(quality_score)
                
                # Debug first few subsets
                if processing_count < 5:
                    print(f"  ZEISS Subset {processing_count}: pos=({x},{y}), score={quality_score:.4f}")
                
                # Map back to image coordinates
                y_end = min(y + facet_size, h)
                x_end = min(x + facet_size, w)
                quality_map[y:y_end, x:x_end] += quality_score
                count_map[y:y_end, x:x_end] += 1
                
                processing_count += 1
        
        print(f"Processed {processing_count} ZEISS-style analysis points")
        print(f"ZEISS scores range: {min(subset_scores):.4f} - {max(subset_scores):.4f}")
        print(f"ZEISS scores mean: {np.mean(subset_scores):.4f}")
        
        # Average overlapping regions
        mask = count_map > 0
        print(f"Pixels with coverage: {np.sum(mask)} / {mask.size} ({np.sum(mask)/mask.size*100:.1f}%)")
        
        quality_map[mask] /= count_map[mask]
        
        # Light smoothing for granular results
        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.3)
        
        # Clip to valid range
        quality_map = np.clip(quality_map, 0, 1)
        
        debug_info = {
            'processing_count': processing_count,
            'subset_scores': subset_scores,
            'coverage_percentage': float(np.sum(mask)/mask.size*100),
            'method': 'zeiss_style'
        }
        
        return quality_map, debug_info

    def _calculate_zeiss_quality_debug(self, subset: np.ndarray, debug_print: bool = False) -> float:
        """Calculate ZEISS-style quality with debugging."""
        if subset.size == 0:
            return 0.0

        try:
            # Calculate gradients using universal gradient analyzer
            grad_x, grad_y, gradient_magnitude = self.gradient_analyzer.calculate_gradients(subset, 'sobel', normalize=True)

            # 1. Gradient content analysis (50% weight)
            mean_gradient = np.mean(gradient_magnitude)
            gradient_std = np.std(gradient_magnitude)
            gradient_score = min(1.0, mean_gradient / 50.0)
            gradient_cv = gradient_std / (mean_gradient + 1e-6)
            
            if 0.5 <= gradient_cv <= 2.0:
                distribution_bonus = 1.0
            elif 0.3 <= gradient_cv <= 3.0:
                distribution_bonus = 0.8
            else:
                distribution_bonus = 0.6

            gradient_quality = gradient_score * distribution_bonus

            # 2. Pattern uniqueness (25% weight)
            mean_intensity = np.mean(subset)
            intensity_std = np.std(subset)
            contrast_ratio = intensity_std / (mean_intensity + 1e-6)
            complexity_score = self._calculate_pattern_complexity(subset)
            uniqueness_quality = min(1.0, contrast_ratio * 2.0) * 0.7 + complexity_score * 0.3

            # 3. Noise resistance (15% weight)
            if subset.shape[0] > 3 and subset.shape[1] > 3:
                smoothed = cv2.GaussianBlur(subset, (3, 3), 0.5)
                noise = subset.astype(float) - smoothed.astype(float)
                noise_std = np.std(noise)
                signal_std = np.std(smoothed)
                snr = signal_std / (noise_std + 1e-6)
                noise_quality = min(1.0, snr / 20.0)
            else:
                noise_quality = 0.5

            # 4. Focus quality (10% weight)
            laplacian = cv2.Laplacian(subset, cv2.CV_64F)
            focus_score = min(1.0, np.var(laplacian) / 1000.0)

            # Combine all factors
            overall_quality = (
                gradient_quality * 0.50 +
                uniqueness_quality * 0.25 +
                noise_quality * 0.15 +
                focus_score * 0.10
            )

            if debug_print:
                print(f"    ZEISS Quality Components:")
                print(f"      Gradient: {gradient_quality:.3f} (mean={mean_gradient:.1f}, cv={gradient_cv:.2f})")
                print(f"      Uniqueness: {uniqueness_quality:.3f} (contrast={contrast_ratio:.2f})")
                print(f"      Noise: {noise_quality:.3f} (snr={snr:.1f})")
                print(f"      Focus: {focus_score:.3f}")
                print(f"      Overall: {overall_quality:.3f}")

            return max(0.0, min(1.0, overall_quality))

        except Exception as e:
            if debug_print:
                print(f"    Error in ZEISS quality calculation: {e}")
            return 0.0

    def _calculate_pattern_complexity(self, subset: np.ndarray) -> float:
        """Calculate pattern complexity using simplified texture analysis."""
        if subset.shape[0] < 3 or subset.shape[1] < 3:
            return 0.5

        try:
            center = subset[1:-1, 1:-1]
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

    def _generate_visualization_debug(self, quality_map: np.ndarray, spectrum_type: str) -> np.ndarray:
        """Generate visualization with debugging information."""
        print(f"\n--- Visualization Generation ---")
        print(f"Quality map for visualization: {quality_map.shape}, range: {quality_map.min():.4f} - {quality_map.max():.4f}")
        
        # Check if we have valid data
        if quality_map.max() == 0:
            print("WARNING: Quality map is all zeros!")
            # Create a test pattern for debugging
            quality_map = np.random.rand(*quality_map.shape) * 0.5 + 0.25
            print(f"Created test pattern: range {quality_map.min():.4f} - {quality_map.max():.4f}")
        
        # Apply colormap
        visualization = self.colormap_generator.apply_colormap(quality_map, spectrum_type)
        
        print(f"Visualization shape: {visualization.shape}")
        print(f"Visualization range: {visualization.min()} - {visualization.max()}")
        
        # Check if colormap worked
        unique_colors = len(np.unique(visualization.reshape(-1, visualization.shape[-1]), axis=0))
        print(f"Unique colors in visualization: {unique_colors}")
        
        return visualization

    def create_legend(self, spectrum_type: str = 'custom_dic', save_path: Optional[str] = None) -> np.ndarray:
        """
        Create a legend for the quality map visualization.
        
        Args:
            spectrum_type: Type of color spectrum
            save_path: Optional path to save the legend image
            
        Returns:
            Legend image as numpy array
        """
        print(f"\n--- Creating Legend ---")
        
        if spectrum_type not in COLOR_SPECTRUMS:
            spectrum_type = 'custom_dic'
            
        spectrum = COLOR_SPECTRUMS[spectrum_type]
        colors = spectrum['colors']
        thresholds = QUALITY_THRESHOLDS.get(spectrum_type, QUALITY_THRESHOLDS['custom_dic'])
        
        print(f"Creating legend for {spectrum_type}")
        print(f"Colors: {len(colors)}")
        print(f"Thresholds: {thresholds}")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Create color bars
        bar_height = 0.8
        bar_width = 0.6
        
        # Sort thresholds by value
        sorted_thresholds = sorted(thresholds.items(), key=lambda x: x[1], reverse=True)
        
        y_positions = np.linspace(0.1, 0.9, len(colors))
        
        for i, (r, g, b, description) in enumerate(colors):
            # Convert RGB to 0-1 range
            color = (r/255, g/255, b/255)
            
            # Create rectangle
            rect = Rectangle((0.1, y_positions[-(i+1)] - bar_height/(2*len(colors))), 
                           bar_width, bar_height/len(colors), 
                           facecolor=color, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # Add text description
            ax.text(0.75, y_positions[-(i+1)], description, 
                   verticalalignment='center', fontsize=10, fontweight='bold')
        
        # Set title and labels
        ax.set_title(f'{spectrum["name"]}\n{spectrum["description"]}', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Remove axes
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Save if requested
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Legend saved to: {save_path}")
        
        # Convert to numpy array
        fig.canvas.draw()
        legend_array = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        legend_array = legend_array.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        
        plt.close(fig)
        
        print(f"Legend created: {legend_array.shape}")
        return legend_array

    def save_debug_report(self, debug_info: Dict, save_path: str):
        """Save comprehensive debug report."""
        print(f"\n--- Saving Debug Report ---")
        
        with open(save_path, 'w') as f:
            f.write("=== QUALITY MAP DEBUG REPORT ===\n\n")
            
            # Basic info
            f.write("BASIC INFORMATION:\n")
            f.write(f"Input image shape: {debug_info.get('input_image_shape', 'N/A')}\n")
            f.write(f"Grayscale shape: {debug_info.get('grayscale_shape', 'N/A')}\n")
            f.write(f"Subset size: {debug_info.get('subset_size', 'N/A')}\n")
            f.write(f"Step size: {debug_info.get('step_size', 'N/A')}\n")
            f.write(f"Spectrum type: {debug_info.get('spectrum_type', 'N/A')}\n")
            f.write(f"Method: {debug_info.get('method', 'N/A')}\n\n")
            
            # Processing stats
            f.write("PROCESSING STATISTICS:\n")
            f.write(f"Processing count: {debug_info.get('processing_count', 'N/A')}\n")
            f.write(f"Coverage percentage: {debug_info.get('coverage_percentage', 'N/A'):.1f}%\n\n")
            
            # Quality map stats
            if 'quality_map_stats' in debug_info:
                stats = debug_info['quality_map_stats']
                f.write("QUALITY MAP STATISTICS:\n")
                f.write(f"Min: {stats.get('min', 'N/A'):.6f}\n")
                f.write(f"Max: {stats.get('max', 'N/A'):.6f}\n")
                f.write(f"Mean: {stats.get('mean', 'N/A'):.6f}\n")
                f.write(f"Std: {stats.get('std', 'N/A'):.6f}\n")
                f.write(f"Non-zero count: {stats.get('non_zero_count', 'N/A')}\n\n")
            
            # Subset scores
            if 'subset_scores' in debug_info:
                scores = debug_info['subset_scores']
                f.write("SUBSET SCORES ANALYSIS:\n")
                f.write(f"Total subsets: {len(scores)}\n")
                if scores:
                    f.write(f"Score range: {min(scores):.6f} - {max(scores):.6f}\n")
                    f.write(f"Score mean: {np.mean(scores):.6f}\n")
                    f.write(f"Score std: {np.std(scores):.6f}\n")
                    
                    # Score distribution
                    bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
                    hist, _ = np.histogram(scores, bins=bins)
                    f.write("Score distribution:\n")
                    for i in range(len(bins)-1):
                        f.write(f"  {bins[i]:.1f}-{bins[i+1]:.1f}: {hist[i]} ({hist[i]/len(scores)*100:.1f}%)\n")
        
        print(f"Debug report saved to: {save_path}")

    def _generate_roi_based_map_debug(self, gray: np.ndarray, roi: 'ROIData', spectrum_type: str, 
                                     subset_size: Optional[int], step_size: Optional[int]) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Generate ROI-based quality map with debugging."""
        print(f"\n--- ROI-Based Analysis Debug ---")
        
        from models.roi_data import ROIData
        
        h, w = gray.shape
        
        # Get ROI bounding box
        x1, y1, x2, y2 = roi.get_bounding_box()
        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)
        
        print(f"ROI bounding box: ({x1}, {y1}) to ({x2}, {y2})")
        print(f"ROI size: {x2-x1} x {y2-y1}")
        
        # Extract ROI region
        roi_region = gray[y1:y2, x1:x2].copy()
        roi_h, roi_w = roi_region.shape
        
        print(f"ROI region shape: {roi_region.shape}")
        print(f"ROI region range: {roi_region.min()} - {roi_region.max()}")
        
        # Determine parameters
        if subset_size is None:
            subset_size = self.dic_calculator.determine_optimal_subset_size(roi_region)
        if step_size is None:
            step_size = max(1, int(subset_size * (1 - self.default_overlap)))
        
        print(f"ROI analysis parameters: subset={subset_size}, step={step_size}")
        
        # Create adjusted ROI coordinates
        adjusted_roi = ROIData(
            coordinates=[(x - x1, y - y1) for x, y in roi.coordinates],
            roi_type=roi.roi_type
        )
        
        # Create mask
        roi_mask = adjusted_roi.create_mask(roi_region.shape)
        print(f"ROI mask coverage: {np.sum(roi_mask > 0)} / {roi_mask.size} pixels ({np.sum(roi_mask > 0)/roi_mask.size*100:.1f}%)")
        
        # Generate quality map for ROI region
        if spectrum_type == 'controlled':
            roi_quality_map, debug_info = self._generate_controlled_method_map_with_mask_debug(roi_region, roi_mask, subset_size, step_size)
        else:
            roi_quality_map, debug_info = self._generate_standard_map_with_mask_debug(roi_region, roi_mask, subset_size, step_size)
        
        # Create full-size quality map
        full_quality_map = np.zeros((h, w), dtype=np.float32)
        full_quality_map[y1:y2, x1:x2] = roi_quality_map
        
        # Generate visualization
        visualization = self._generate_visualization_debug(full_quality_map, spectrum_type)
        
        debug_info.update({
            'roi_bounding_box': (x1, y1, x2, y2),
            'roi_region_shape': roi_region.shape,
            'roi_mask_coverage': float(np.sum(roi_mask > 0)/roi_mask.size*100),
            'analysis_type': 'roi_based'
        })
        
        return full_quality_map, visualization, debug_info

    def _generate_standard_map_with_mask_debug(self, gray: np.ndarray, roi_mask: np.ndarray, 
                                              subset_size: int, step_size: int) -> Tuple[np.ndarray, Dict]:
        """Generate standard quality map with ROI mask and debugging."""
        h, w = gray.shape
        print(f"Standard map with mask: {gray.shape}, subset={subset_size}, step={step_size}")
        
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)
        
        analysis_count = 0
        subset_scores = []
        
        for y in range(0, h - subset_size + 1, step_size):
            for x in range(0, w - subset_size + 1, step_size):
                # Check ROI intersection
                subset_mask = roi_mask[y:y + subset_size, x:x + subset_size]
                roi_coverage = np.sum(subset_mask > 0) / subset_mask.size
                
                if roi_coverage < 0.25:
                    continue
                
                subset = gray[y:y + subset_size, x:x + subset_size]
                quality_score = self.quality_calculator.calculate_subset_quality(subset)
                subset_scores.append(quality_score)
                
                if analysis_count < 3:
                    print(f"  ROI Subset {analysis_count}: pos=({x},{y}), coverage={roi_coverage:.2f}, score={quality_score:.4f}")
                
                y_end = min(y + subset_size, h)
                x_end = min(x + subset_size, w)
                quality_map[y:y_end, x:x_end] += quality_score
                count_map[y:y_end, x:x_end] += 1
                
                analysis_count += 1
        
        print(f"ROI analysis completed: {analysis_count} subsets processed")
        
        # Average overlapping regions
        mask = count_map > 0
        quality_map[mask] /= count_map[mask]
        
        # Apply smoothing
        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.5)
        quality_map = np.clip(quality_map, 0, 1)
        
        debug_info = {
            'processing_count': analysis_count,
            'subset_scores': subset_scores,
            'method': 'standard_with_mask'
        }
        
        return quality_map, debug_info

    def _generate_controlled_method_map_with_mask_debug(self, gray: np.ndarray, roi_mask: np.ndarray, 
                                                 facet_size: int, point_distance: int) -> Tuple[np.ndarray, Dict]:
        """Generate controlled method quality map with ROI mask and debugging."""
        h, w = gray.shape
        print(f"Controlled method map with mask: {gray.shape}, facet={facet_size}, distance={point_distance}")
        
        quality_map = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.int32)
        
        analysis_count = 0
        subset_scores = []
        
        for y in range(0, h - facet_size + 1, point_distance):
            for x in range(0, w - facet_size + 1, point_distance):
                # Check ROI intersection
                subset_mask = roi_mask[y:y + facet_size, x:x + facet_size]
                roi_coverage = np.sum(subset_mask > 0) / subset_mask.size
                
                if roi_coverage < 0.25:
                    continue
                
                subset = gray[y:y + facet_size, x:x + facet_size]
                quality_score = self._calculate_zeiss_quality_debug(subset, analysis_count < 3)
                subset_scores.append(quality_score)
                
                y_end = min(y + facet_size, h)
                x_end = min(x + facet_size, w)
                quality_map[y:y_end, x:x_end] += quality_score
                count_map[y:y_end, x:x_end] += 1
                
                analysis_count += 1
        
        print(f"ROI ZEISS analysis completed: {analysis_count} facets processed")
        
        # Average overlapping regions
        mask = count_map > 0
        quality_map[mask] /= count_map[mask]
        
        # Light smoothing
        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.3)
        quality_map = np.clip(quality_map, 0, 1)
        
        debug_info = {
            'processing_count': analysis_count,
            'subset_scores': subset_scores,
            'method': 'zeiss_with_mask'
        }
        
        return quality_map, debug_info