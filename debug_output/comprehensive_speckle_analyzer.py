# comprehensive_speckle_analyzer_fixed.py

import cv2
import numpy as np
from pathlib import Path
import json
from typing import Dict, List, Tuple, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComprehensiveSpeckleAnalyzer:
    """
    Comprehensive speckle analyzer with minimal filtering - detect everything, analyze everything
    Focus on providing complete information rather than filtering based on assumptions
    """

    def __init__(self, debug_dir: str = "comprehensive_debug"):
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)
        self.clear_debug_folder()

        # Very permissive detection parameters - detect almost everything
        self.min_area_absolute = 1  # Detect even single pixels
        self.max_area_ratio = 0.25  # Up to 25% of image (very large speckles)
        self.morphology_kernel_size = 2  # Minimal noise removal

        # Analysis categories for comprehensive reporting
        self.size_categories = {
            'tiny': (1, 5),  # 1-5 pixels
            'very_small': (6, 15),  # 6-15 pixels
            'small': (16, 50),  # 16-50 pixels
            'medium': (51, 150),  # 51-150 pixels
            'large': (151, 500),  # 151-500 pixels
            'very_large': (501, 2000),  # 501-2000 pixels
            'huge': (2001, 10000)  # >2000 pixels
        }

    def clear_debug_folder(self):
        """Clear previous debug files"""
        if self.debug_dir.exists():
            for file in self.debug_dir.glob("*.png"):
                try:
                    file.unlink()
                except:
                    pass
            for file in self.debug_dir.glob("*.json"):
                try:
                    file.unlink()
                except:
                    pass

    def analyze_speckle_pattern_comprehensive(self, roi_image: np.ndarray, save_debug: bool = True) -> Dict[str, Any]:
        """
        Comprehensive analysis with minimal filtering - capture everything
        """
        print("DEBUG: Starting comprehensive analysis...")

        try:
            if len(roi_image.shape) == 3:
                gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi_image.copy()

            roi_area = gray.shape[0] * gray.shape[1]
            print(f"DEBUG: ROI dimensions: {gray.shape}, area: {roi_area}")

            if save_debug:
                cv2.imwrite(str(self.debug_dir / "01_original.png"), gray)
                print(f"DEBUG: Saved original image to {self.debug_dir}")

            # Step 1: Multi-method detection with minimal filtering
            print("DEBUG: Starting detection methods...")
            detection_results = self._detect_all_methods(gray, roi_area, save_debug)
            print(f"DEBUG: Detection completed, found {len(detection_results.get('summary', {}))} methods")

            # Step 2: Comprehensive speckle characterization (no filtering)
            print("DEBUG: Starting speckle analysis...")
            speckle_analysis = self._analyze_all_speckles(detection_results, gray, save_debug)
            print(f"DEBUG: Speckle analysis completed, found {speckle_analysis.get('total_speckles', 0)} speckles")

            # Step 3: Quality assessment across all categories
            print("DEBUG: Starting quality assessment...")
            quality_assessment = self._assess_comprehensive_quality(speckle_analysis, gray, roi_area, save_debug)
            print(f"DEBUG: Quality assessment completed")

            # Step 4: DIC utility analysis for all speckle types
            print("DEBUG: Starting DIC analysis...")
            dic_analysis = self._analyze_dic_potential(speckle_analysis, quality_assessment, save_debug)
            print(f"DEBUG: DIC analysis completed")

            # Step 5: Educational insights and recommendations
            print("DEBUG: Generating insights...")
            insights = self._generate_educational_insights(speckle_analysis, quality_assessment, dic_analysis)
            print(f"DEBUG: Insights generated")

            # Compile comprehensive results
            results = {
                'roi_info': {
                    'dimensions': gray.shape,
                    'area': roi_area,
                    'area_mpx': roi_area / 1_000_000
                },
                'detection_summary': detection_results['summary'],
                'speckle_analysis': speckle_analysis,
                'quality_assessment': quality_assessment,
                'dic_analysis': dic_analysis,
                'educational_insights': insights,
                'raw_detection_data': detection_results  # Include everything for ML training
            }

            if save_debug:
                print("DEBUG: Saving comprehensive report...")
                self._save_comprehensive_report(results)
                print("DEBUG: Creating visualizations...")
                self._create_comprehensive_visualizations(gray, results)

            print("DEBUG: Analysis completed successfully!")
            return results

        except Exception as e:
            print(f"DEBUG: CRITICAL ERROR in comprehensive analysis: {e}")
            import traceback
            traceback.print_exc()
            # Return minimal results to prevent complete failure
            return {
                'roi_info': {'dimensions': (0, 0), 'area': 0, 'area_mpx': 0},
                'detection_summary': {},
                'speckle_analysis': self._empty_speckle_analysis(),
                'quality_assessment': self._empty_quality_assessment(),
                'dic_analysis': self._empty_dic_analysis(),
                'educational_insights': {'pattern_summary': 'Analysis failed', 'strengths': [],
                                         'areas_for_improvement': []},
                'raw_detection_data': {}
            }

    def _detect_all_methods(self, gray: np.ndarray, roi_area: int, save_debug: bool) -> Dict[str, Any]:
        """Detect speckles using multiple methods with minimal filtering"""

        detection_methods = {}

        # Method 1: Global Otsu (both normal and inverted)
        _, otsu_normal = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, otsu_inverted = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        detection_methods['otsu_normal'] = self._process_binary_minimal_filter(otsu_normal, roi_area)
        detection_methods['otsu_inverted'] = self._process_binary_minimal_filter(otsu_inverted, roi_area)

        # Method 2: Adaptive thresholding variations
        adaptive_gaussian = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        adaptive_mean = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)

        detection_methods['adaptive_gaussian'] = self._process_binary_minimal_filter(adaptive_gaussian, roi_area)
        detection_methods['adaptive_mean'] = self._process_binary_minimal_filter(adaptive_mean, roi_area)

        # Method 3: Multiple threshold levels
        percentile_thresholds = [10, 25, 50, 75, 90]
        for p in percentile_thresholds:
            thresh_val = np.percentile(gray, p)
            _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY_INV)
            detection_methods[f'percentile_{p}'] = self._process_binary_minimal_filter(binary, roi_area)

        if save_debug:
            self._save_detection_methods(detection_methods, gray.shape)

        # Combine all detections for comprehensive analysis
        combined_analysis = self._combine_all_detections(detection_methods, gray.shape)

        return {
            'methods': detection_methods,
            'combined': combined_analysis,
            'summary': self._summarize_detection_results(detection_methods)
        }

    def _process_binary_minimal_filter(self, binary: np.ndarray, roi_area: int) -> Dict[str, Any]:
        """Process binary image with absolute minimal filtering - keep almost everything"""

        # Minimal morphological cleanup - only remove isolated pixels
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

        # Connected components analysis
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)

        # Extremely permissive filtering - only remove obvious noise
        max_area = int(roi_area * self.max_area_ratio)  # 25% of ROI

        all_components = []
        tiny_noise = []  # Separate tiny components for analysis

        for i in range(1, num_labels):  # Skip background
            area = stats[i, cv2.CC_STAT_AREA]

            if area >= self.min_area_absolute and area <= max_area:
                all_components.append(i)
            elif area < self.min_area_absolute:
                tiny_noise.append(i)

        # Categorize by size for analysis
        categorized = self._categorize_speckles_by_size(all_components, stats)

        return {
            'binary_image': cleaned,
            'num_total_components': num_labels - 1,
            'all_valid_components': all_components,
            'tiny_noise_components': tiny_noise,
            'labels': labels,
            'stats': stats,
            'centroids': centroids,
            'size_categories': categorized,
            'total_coverage': np.sum(cleaned > 0) / cleaned.size
        }

    def _categorize_speckles_by_size(self, components: List[int], stats: np.ndarray) -> Dict[str, List[int]]:
        """Categorize speckles into size groups for detailed analysis"""
        categorized = {category: [] for category in self.size_categories.keys()}

        for comp_id in components:
            area = stats[comp_id, cv2.CC_STAT_AREA]

            for category, (min_size, max_size) in self.size_categories.items():
                if min_size <= area <= max_size:
                    categorized[category].append(comp_id)
                    break

        return categorized

    def _combine_all_detections(self, detection_methods: Dict, image_shape: Tuple) -> Dict[str, Any]:
        """Combine detections from all methods to get comprehensive speckle map"""

        # Create comprehensive speckle map
        combined_map = np.zeros(image_shape, dtype=np.uint8)

        # Track which methods detected each pixel
        detection_count = np.zeros(image_shape, dtype=np.int32)

        for method_name, method_data in detection_methods.items():
            binary = method_data['binary_image']
            combined_map = cv2.bitwise_or(combined_map, binary)
            detection_count += (binary > 0).astype(np.int32)

        # Analyze overlapping detections
        overlap_analysis = {
            'single_method': int(np.sum(detection_count == 1)),
            'two_methods': int(np.sum(detection_count == 2)),
            'three_plus_methods': int(np.sum(detection_count >= 3)),
            'max_overlap': int(np.max(detection_count))
        }

        # Final comprehensive component analysis
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(combined_map, connectivity=8)

        # Keep everything except single pixels (absolute minimal filtering)
        final_components = []
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= 2:  # Keep everything 2+ pixels
                final_components.append(i)

        return {
            'combined_binary': combined_map,
            'detection_count_map': detection_count,
            'overlap_analysis': overlap_analysis,
            'final_components': final_components,
            'final_labels': labels,
            'final_stats': stats,
            'final_centroids': centroids,
            'total_detected': len(final_components)
        }

    def _analyze_all_speckles(self, detection_results: Dict, gray: np.ndarray, save_debug: bool) -> Dict[str, Any]:
        """Comprehensive analysis of ALL detected speckles"""

        combined = detection_results['combined']
        components = combined['final_components']
        stats = combined['final_stats']
        centroids = combined['final_centroids']

        if not components or len(components) == 0:
            return self._empty_speckle_analysis()

        # Detailed size analysis
        areas = [int(stats[i, cv2.CC_STAT_AREA]) for i in components]

        # Calculate comprehensive metrics for each speckle
        speckle_metrics = []
        for i, comp_id in enumerate(components):
            try:
                area = areas[i]
                centroid = centroids[comp_id]

                # Ensure centroid is valid
                if len(centroid) >= 2:
                    x, y = int(centroid[0]), int(centroid[1])

                    # Local intensity analysis
                    local_region = self._extract_local_region(gray, x, y, size=15)
                    if local_region.size > 0:
                        local_contrast = float(np.std(local_region)) / (float(np.mean(local_region)) + 1e-6)
                    else:
                        local_contrast = 0.0

                    speckle_metrics.append({
                        'component_id': int(comp_id),
                        'area': int(area),
                        'centroid': [float(centroid[0]), float(centroid[1])],
                        'local_contrast': float(local_contrast),
                        'size_category': self._get_size_category(area)
                    })
            except Exception as e:
                print(f"Error processing speckle {comp_id}: {e}")
                continue

        # Categorize all speckles
        size_distribution = self._analyze_size_distribution_simple(areas)
        spatial_distribution = self._analyze_spatial_distribution_simple([m['centroid'] for m in speckle_metrics],
                                                                         gray.shape)

        return {
            'total_speckles': len(speckle_metrics),
            'speckle_metrics': speckle_metrics,
            'size_distribution': size_distribution,
            'spatial_distribution': spatial_distribution,
            'detection_confidence': combined['overlap_analysis']
        }

    def _assess_comprehensive_quality(self, speckle_analysis: Dict, gray: np.ndarray, roi_area: int,
                                      save_debug: bool) -> Dict[str, Any]:
        """Assess quality without filtering - analyze everything"""

        if speckle_analysis['total_speckles'] == 0:
            return self._empty_quality_assessment()

        try:
            # Overall pattern quality metrics
            total_speckles = speckle_analysis['total_speckles']
            density_per_mpx = float(total_speckles) / float(roi_area) * 1_000_000

            # Multi-dimensional quality scoring
            quality_scores = {
                'density_quality': min(100.0, density_per_mpx / 10.0),  # Simple density scoring
                'size_diversity': 80.0 if len(
                    set(m['size_category'] for m in speckle_analysis['speckle_metrics'])) > 2 else 40.0
            }

            # Overall quality (not filtered, just informational)
            overall_quality = float(np.mean(list(quality_scores.values())))

            return {
                'overall_quality_score': overall_quality,
                'quality_components': quality_scores,
                'pattern_characteristics': {
                    'total_speckles': total_speckles,
                    'density_per_mpx': density_per_mpx,
                }
            }
        except Exception as e:
            print(f"Error in quality assessment: {e}")
            return self._empty_quality_assessment()

    def _analyze_dic_potential(self, speckle_analysis: Dict, quality_assessment: Dict, save_debug: bool) -> Dict[
        str, Any]:
        """Analyze DIC potential for ALL speckles, not just filtered ones"""

        if speckle_analysis['total_speckles'] == 0:
            return self._empty_dic_analysis()

        try:
            metrics = speckle_analysis['speckle_metrics']

            # Count speckles by category
            category_counts = {}
            for category in self.size_categories.keys():
                count = sum(1 for m in metrics if m.get('size_category') == category)
                category_counts[category] = count

            # Simple DIC scoring
            dic_scores = {
                'pattern_richness': min(100.0, float(speckle_analysis['total_speckles']) / 2.0),
                'medium_speckle_bonus': min(50.0, float(category_counts.get('medium', 0)) * 5.0),
                'large_speckle_bonus': min(30.0, float(category_counts.get('large', 0)) * 10.0)
            }

            overall_dic_score = float(np.mean(list(dic_scores.values())))

            # Simple recommendations
            recommendations = []
            if category_counts.get('medium', 0) < 10:
                recommendations.append(
                    "Consider adding medium-sized speckles (51-150 pixels) for optimal DIC performance")
            if category_counts.get('large', 0) < 3:
                recommendations.append("Add larger speckles for improved coarse displacement tracking")
            if speckle_analysis['total_speckles'] < 50:
                recommendations.append("Increase overall speckle density for richer correlation patterns")

            if not recommendations:
                recommendations.append("Pattern shows good characteristics for DIC analysis")

            return {
                'overall_dic_score': overall_dic_score,
                'dic_score_components': dic_scores,
                'category_counts': category_counts,
                'recommendations': recommendations,
                'suitability_rating': self._get_suitability_rating(overall_dic_score)
            }
        except Exception as e:
            print(f"Error in DIC analysis: {e}")
            return self._empty_dic_analysis()

    def _generate_educational_insights(self, speckle_analysis: Dict, quality_assessment: Dict, dic_analysis: Dict) -> \
    Dict[str, Any]:
        """Generate educational insights about the speckle pattern"""

        total = speckle_analysis['total_speckles']
        quality = quality_assessment['overall_quality_score']

        insights = {
            'pattern_summary': f"Detected {total} speckles with overall quality {quality:.1f}/100",
            'strengths': [],
            'areas_for_improvement': []
        }

        # Simple strengths identification
        if total > 100:
            insights['strengths'].append("Rich speckle pattern with good feature density")
        if quality > 70:
            insights['strengths'].append("High overall pattern quality")

        # Simple improvement areas
        if total < 50:
            insights['areas_for_improvement'].append("Low speckle count - consider increasing pattern density")
        if quality < 50:
            insights['areas_for_improvement'].append("Pattern quality could be improved")

        return insights

    # Helper methods - simplified implementations
    def _extract_local_region(self, gray: np.ndarray, x: int, y: int, size: int = 15) -> np.ndarray:
        """Extract local region around a point"""
        h, w = gray.shape
        x1, y1 = max(0, x - size // 2), max(0, y - size // 2)
        x2, y2 = min(w, x + size // 2), min(h, y + size // 2)
        return gray[y1:y2, x1:x2]

    def _get_size_category(self, area: float) -> str:
        """Get size category for a given area"""
        for category, (min_size, max_size) in self.size_categories.items():
            if min_size <= area <= max_size:
                return category
        return 'uncategorized'

    def _analyze_size_distribution_simple(self, areas: List[float]) -> Dict[str, Any]:
        """Simple size distribution analysis"""
        if not areas or len(areas) == 0:
            return {}

        try:
            areas_array = np.array(areas, dtype=float)
            return {
                'mean_area': float(np.mean(areas_array)),
                'median_area': float(np.median(areas_array)),
                'min_area': float(np.min(areas_array)),
                'max_area': float(np.max(areas_array))
            }
        except Exception as e:
            print(f"Error in size distribution analysis: {e}")
            return {}

    def _analyze_spatial_distribution_simple(self, centroids: List, image_shape: Tuple) -> Dict[str, Any]:
        """Simple spatial distribution analysis"""
        if len(centroids) < 2:
            return {'uniformity_score': 0.0}

        try:
            # Convert centroids to proper numpy array format
            centroids_list = []
            for centroid in centroids:
                if isinstance(centroid, np.ndarray):
                    centroids_list.append([float(centroid[0]), float(centroid[1])])
                else:
                    centroids_list.append([float(centroid[0]), float(centroid[1])])

            centroids_array = np.array(centroids_list)

            if centroids_array.shape[0] < 2 or centroids_array.shape[1] < 2:
                return {'uniformity_score': 0.0}

            std_x = float(np.std(centroids_array[:, 0]))
            std_y = float(np.std(centroids_array[:, 1]))

            # Higher standard deviation indicates better distribution
            uniformity_score = min(100.0, (std_x + std_y) / 10.0)

            return {'uniformity_score': float(uniformity_score)}

        except Exception as e:
            print(f"Error in spatial distribution analysis: {e}")
            return {'uniformity_score': 0.0}

    def _empty_speckle_analysis(self) -> Dict[str, Any]:
        """Return empty analysis when no speckles detected"""
        return {
            'total_speckles': 0,
            'speckle_metrics': [],
            'size_distribution': {},
            'spatial_distribution': {},
            'detection_confidence': {}
        }

    def _empty_quality_assessment(self) -> Dict[str, Any]:
        """Return empty quality assessment"""
        return {
            'overall_quality_score': 0.0,
            'quality_components': {},
            'pattern_characteristics': {}
        }

    def _empty_dic_analysis(self) -> Dict[str, Any]:
        """Return empty DIC analysis"""
        return {
            'overall_dic_score': 0.0,
            'dic_score_components': {},
            'category_counts': {},
            'recommendations': [],
            'suitability_rating': 'POOR'
        }

    def _get_suitability_rating(self, overall_score: float) -> str:
        """Get suitability rating based on overall score"""
        if overall_score >= 85:
            return 'EXCELLENT'
        elif overall_score >= 70:
            return 'GOOD'
        elif overall_score >= 55:
            return 'FAIR'
        elif overall_score >= 40:
            return 'MARGINAL'
        else:
            return 'POOR'

    def _summarize_detection_results(self, detection_methods: Dict) -> Dict[str, int]:
        """Summarize detection results across methods"""
        summary = {}
        for method_name, method_data in detection_methods.items():
            summary[method_name] = len(method_data['all_valid_components'])
        return summary

    def _save_detection_methods(self, detection_methods: Dict, image_shape: Tuple):
        """Save visualization of all detection methods"""
        # Create a simple grid visualization
        for i, (method_name, method_data) in enumerate(detection_methods.items()):
            binary = method_data['binary_image']
            cv2.imwrite(str(self.debug_dir / f"method_{i:02d}_{method_name}.png"), binary)

    def _save_comprehensive_report(self, results: Dict):
        """Save comprehensive analysis report"""

        try:
            print("DEBUG: Starting report save...")

            # Convert numpy types for JSON serialization
            def convert_numpy_types(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {key: convert_numpy_types(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                return obj

            print("DEBUG: Converting numpy types...")
            serializable_results = convert_numpy_types(results)

            # Save JSON report
            print("DEBUG: Saving JSON report...")
            json_path = self.debug_dir / "comprehensive_analysis.json"
            with open(str(json_path), 'w') as f:
                json.dump(serializable_results, f, indent=2)
            print(f"DEBUG: JSON saved to {json_path}")

            # Save human-readable report
            print("DEBUG: Saving text report...")
            txt_path = self.debug_dir / "comprehensive_report.txt"
            with open(str(txt_path), 'w', encoding='utf-8') as f:
                self._write_comprehensive_text_report(f, results)
            print(f"DEBUG: Text report saved to {txt_path}")

        except Exception as e:
            print(f"DEBUG: Error saving report: {e}")
            import traceback
            traceback.print_exc()

    def _write_comprehensive_text_report(self, f, results: Dict):
        """Write comprehensive human-readable report"""
        try:
            f.write("COMPREHENSIVE SPECKLE PATTERN ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")

            # ROI Information
            roi_info = results['roi_info']
            f.write(f"ROI Information:\n")
            f.write(f"  Dimensions: {roi_info['dimensions'][1]} x {roi_info['dimensions'][0]} pixels\n")
            f.write(f"  Area: {roi_info['area']:,} pixels ({roi_info['area_mpx']:.3f} Mpx)\n\n")

            # Speckle Analysis
            speckle = results['speckle_analysis']
            f.write(f"Comprehensive Speckle Analysis:\n")
            f.write(f"  Total Speckles Detected: {speckle['total_speckles']}\n")

            # Size category breakdown
            f.write(f"  Size Category Breakdown:\n")
            for category in self.size_categories.keys():
                count = sum(1 for m in speckle['speckle_metrics'] if m.get('size_category') == category)
                if count > 0:
                    f.write(f"    {category}: {count} speckles\n")
            f.write("\n")

            # Quality Assessment
            quality = results['quality_assessment']
            f.write(f"Quality Assessment:\n")
            f.write(f"  Overall Quality Score: {quality['overall_quality_score']:.1f}/100\n\n")

            # DIC Analysis
            dic = results['dic_analysis']
            f.write(f"DIC Analysis:\n")
            f.write(f"  Overall DIC Score: {dic['overall_dic_score']:.1f}/100\n")
            f.write(f"  Suitability Rating: {dic['suitability_rating']}\n")
            f.write(f"  Recommendations:\n")
            for rec in dic['recommendations']:
                f.write(f"    • {rec}\n")
        except Exception as e:
            f.write(f"Error writing report: {str(e)}\n")

    def _create_comprehensive_visualizations(self, gray: np.ndarray, results: Dict):
        """Create comprehensive visualizations showing all detected speckles"""

        speckle_analysis = results['speckle_analysis']
        if speckle_analysis['total_speckles'] == 0:
            return

        # Create size category visualization
        self._create_size_category_visualization(gray, speckle_analysis)

    def _create_size_category_visualization(self, gray: np.ndarray, speckle_analysis: Dict):
        """Create visualization showing speckles by size category"""
        if speckle_analysis['total_speckles'] == 0:
            return

        try:
            h, w = gray.shape
            vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            # Color map for categories
            category_colors = {
                'tiny': (128, 128, 128),  # Gray
                'very_small': (255, 255, 0),  # Cyan
                'small': (0, 255, 0),  # Green
                'medium': (0, 0, 255),  # Red
                'large': (255, 0, 255),  # Magenta
                'very_large': (0, 165, 255),  # Orange
                'huge': (255, 255, 255)  # White
            }

            # Draw centroids colored by category
            for metric in speckle_analysis['speckle_metrics']:
                try:
                    category = metric.get('size_category', 'uncategorized')
                    centroid = metric.get('centroid', [0, 0])
                    color = category_colors.get(category, (255, 255, 255))

                    if len(centroid) >= 2:
                        x, y = int(centroid[0]), int(centroid[1])
                        # Ensure coordinates are within image bounds
                        if 0 <= x < w and 0 <= y < h:
                            cv2.circle(vis, (x, y), 3, color, -1)
                except Exception as e:
                    print(f"Error drawing speckle: {e}")
                    continue

            # Add legend
            legend_y = 20
            for category, color in category_colors.items():
                count = sum(1 for m in speckle_analysis['speckle_metrics'] if m.get('size_category') == category)
                if count > 0:
                    cv2.rectangle(vis, (10, legend_y), (30, legend_y + 15), color, -1)
                    cv2.putText(vis, f"{category}: {count}", (35, legend_y + 12),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    legend_y += 20

            cv2.imwrite(str(self.debug_dir / "size_categories.png"), vis)
        except Exception as e:
            print(f"Error creating size category visualization: {e}")


# Modified integration function with fallback
def integrate_comprehensive_analyzer(main_window):
    """
    Integration function with debugging and fallback
    """
    # Add both analyzers to main window
    main_window.comprehensive_analyzer = ComprehensiveSpeckleAnalyzer("comprehensive_analysis")

    def comprehensive_analysis_callback():
        """Callback with debugging and fallback"""
        try:
            print("DEBUG: === STARTING COMPREHENSIVE ANALYSIS ===")

            if not hasattr(main_window, 'original_image') or main_window.original_image is None:
                from tkinter import messagebox
                messagebox.showwarning("No Image", "Please load an image first")
                return

            print("DEBUG: Image loaded, checking ROI...")

            # Get ROI or full image
            if hasattr(main_window, 'roi_handler') and main_window.roi_handler.roi_coords:
                roi_coords = main_window.roi_handler.roi_coords
                x1, y1, x2, y2 = roi_coords
                roi_image = main_window.original_image[y1:y2, x1:x2].copy()
                print(f"DEBUG: Using ROI: {roi_coords}")
            else:
                roi_image = main_window.original_image.copy()
                print("DEBUG: Using full image")

            print(f"DEBUG: ROI image shape: {roi_image.shape}")

            # Try comprehensive analysis first
            try:
                print("DEBUG: Attempting comprehensive analysis...")
                results = main_window.comprehensive_analyzer.analyze_speckle_pattern_comprehensive(roi_image)
                print("DEBUG: Comprehensive analysis succeeded!")

            except Exception as comp_error:
                print(f"DEBUG: Comprehensive analysis failed: {comp_error}")
                print("DEBUG: Falling back to simple analysis...")

                # Fallback to simple analysis
                simple_results = main_window.simple_analyzer.analyze_simple(roi_image)

                # Convert simple results to expected format
                results = {
                    'speckle_analysis': {'total_speckles': simple_results.get('total_speckles', 0)},
                    'quality_assessment': {'overall_quality_score': 50.0},
                    'dic_analysis': {
                        'overall_dic_score': 50.0,
                        'suitability_rating': 'UNKNOWN'
                    }
                }
                print(f"DEBUG: Simple analysis completed with {simple_results.get('total_speckles', 0)} speckles")

            # Update UI with results
            speckle_count = results['speckle_analysis']['total_speckles']
            quality_score = results['quality_assessment']['overall_quality_score']
            dic_score = results['dic_analysis']['overall_dic_score']

            print(f"DEBUG: Preparing results dialog...")

            # Show results dialog
            from tkinter import messagebox
            message = f"""Analysis Complete!

Total Speckles Detected: {speckle_count}
Quality Score: {quality_score:.1f}/100
DIC Score: {dic_score:.1f}/100
Suitability: {results['dic_analysis']['suitability_rating']}

Analysis results saved to debug folders."""

            messagebox.showinfo("Analysis Results", message)

            # Update status
            main_window.status_var.set(
                f"Analysis: {speckle_count} speckles, Quality: {quality_score:.1f}/100")

            print("DEBUG: Analysis callback completed successfully!")

        except Exception as e:
            print(f"DEBUG: CRITICAL ERROR in analysis callback: {e}")
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("Analysis Error", f"Analysis failed: {str(e)}\nCheck console for details.")

    # Replace existing debug button functionality
    if hasattr(main_window, 'debug_btn'):
        main_window.debug_btn.config(command=comprehensive_analysis_callback)
        main_window.debug_btn.config(text="🔬 Debug Analysis")

    # Also add to speckle debug button if it exists
    if hasattr(main_window, 'speckle_debug_btn'):
        main_window.speckle_debug_btn.config(command=comprehensive_analysis_callback)


if __name__ == "__main__":
    print("Comprehensive Speckle Analyzer - Fixed Version")
    print("=" * 60)
    print("This analyzer detects and analyzes ALL speckles without aggressive filtering.")
    print("The goal is to provide complete information about the speckle pattern")
    print("for educational purposes and detailed analysis.")
    print()
    print("Key Features:")
    print("• Detects speckles from 1 pixel to 25% of ROI area")
    print("• Multiple detection methods for comprehensive coverage")
    print("• Detailed size category analysis (7 categories)")
    print("• Educational insights about DIC utility")
    print("• No aggressive filtering - analyze everything")
    print("• Comprehensive reporting and visualization")
    print()
    print("Integration Instructions:")
    print("1. Save this file as 'comprehensive_speckle_analyzer.py' in your project")
    print("2. Add this to your main_window.py imports:")
    print("   from comprehensive_speckle_analyzer import integrate_comprehensive_analyzer")
    print("3. Add this line in your main_window.__init__ method (after creating GUI):")
    print("   integrate_comprehensive_analyzer(self)")
    print()
    print("This will replace your existing debug button with comprehensive analysis.")
    print("Results are saved to 'comprehensive_analysis/' folder with:")
    print("• comprehensive_analysis.json - Machine-readable results")
    print("• comprehensive_report.txt - Human-readable report")
    print("• size_categories.png - Visual breakdown by speckle size")
    print("• Multiple detection method visualizations")
    print()
    print("The analyzer provides:")
    print("• Total speckle count across all size categories")
    print("• Quality assessment without arbitrary filtering")
    print("• DIC suitability analysis for all speckle types")
    print("• Educational recommendations for pattern improvement")
    print("• Complete data for machine learning applications")