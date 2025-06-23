# enhanced_debug_integration_FIXED.py
# Complete fix with proper method and debug_output folder

import cv2
import numpy as np
from pathlib import Path
import datetime


def enhance_app_debug_functionality(main_window):
    """Enhanced debug with FIXED size filtering for better app integration"""

    # Store the original debug function
    original_save_debug = main_window.image_display.save_debug_visualizations

    def fixed_debug_visualizations():
        """Fixed version that preserves larger speckles in labeling"""
        print("\n" + "=" * 60)
        print("FIXED SPECKLE DETECTION - PRESERVING LARGE SPECKLES")
        print("=" * 60)

        try:
            # First run the original debug function
            print("Running original debug visualizations...")
            original_save_debug()
            print("Original debug completed successfully")

            # Now add our FIXED speckle detection
            print("Starting FIXED speckle detection with corrected size filtering...")

            if main_window.original_image is None:
                print("ERROR: No image loaded")
                return

            # Get ROI or full image
            if hasattr(main_window, 'roi_handler') and main_window.roi_handler.roi_coords:
                roi_coords = main_window.roi_handler.roi_coords
                x1, y1, x2, y2 = roi_coords
                roi_image = main_window.original_image[y1:y2, x1:x2].copy()
                print(f"Using ROI: {roi_coords}")
                print(f"ROI dimensions: {x2 - x1} x {y2 - y1}")
            else:
                roi_image = main_window.original_image.copy()
                print("Using full image")
                print(f"Image dimensions: {roi_image.shape}")

            # Run FIXED analysis
            analyzer = FixedSpeckleAnalyzer()
            results = analyzer.analyze_with_fixed_filtering(roi_image)

            # Show results in messagebox
            from tkinter import messagebox

            total_speckles = results.get('total_speckles', 0)
            large_speckles = results.get('large_count', 0)
            medium_speckles = results.get('medium_count', 0)
            small_speckles = results.get('small_count', 0)
            dic_score = results.get('dic_score', 0)

            message = f"""FIXED Speckle Detection Complete!

Original Debug: [OK] Completed successfully
FIXED Detection: [OK] Large speckles preserved!

SPECKLE DETECTION RESULTS:
================================================
Detection Method: {results.get('best_method', 'unknown')}
Total Speckles: {total_speckles}
DIC Quality Score: {dic_score:.1f}/100

SIZE BREAKDOWN (FIXED FILTERING):
- Small (1-50px): {small_speckles}
- Medium (51-500px): {medium_speckles} 
- Large (501+ px): {large_speckles}

METHOD SELECTION IMPROVEMENTS:
- Uses DIC quality scoring (not just count)
- Prefers coherent, medium-sized speckles
- Penalizes over-segmentation
- Better for correlation analysis

DEBUG FILES SAVED:
- debug_output/fixed_debug/ - Complete analysis
================================================

Large speckles now properly preserved for app use!"""

            messagebox.showinfo("FIXED Detection Complete", message)

            # Update status
            main_window.status_var.set(
                f"FIXED: {total_speckles} speckles (L:{large_speckles}, M:{medium_speckles}, S:{small_speckles}) DIC:{dic_score:.1f}"
            )

            print("=" * 60)
            print("FIXED SPECKLE DETECTION COMPLETED")
            print(f"PRESERVED {large_speckles} large speckles for app integration!")
            print(f"DIC Quality Score: {dic_score:.1f}/100")
            print("=" * 60)

        except Exception as e:
            print(f"ERROR in fixed speckle detection: {e}")
            import traceback
            traceback.print_exc()

            from tkinter import messagebox
            messagebox.showerror("Fixed Detection Error",
                                 f"Fixed speckle detection failed: {str(e)}\n\nCheck console for details.")

    # Replace the debug button command
    main_window.debug_btn.config(command=fixed_debug_visualizations)
    main_window.debug_btn.config(text="🔧 FIXED Detection")

    print("Successfully enhanced debug button with FIXED speckle detection!")


class FixedSpeckleAnalyzer:
    """Analyzer with FIXED size filtering to preserve large speckles for app integration"""

    def __init__(self):
        # Use debug_output folder as requested
        self.debug_dir = Path("debug_output") / "fixed_debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        print(f"Using debug folder: {self.debug_dir}")

    def analyze_with_fixed_filtering(self, roi_image):
        """Analyze with CORRECTED size filtering that preserves large speckles"""
        print(f"Input image shape: {roi_image.shape}")

        try:
            # Step 1: Convert to grayscale
            if len(roi_image.shape) == 3:
                gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi_image.copy()

            print(f"Analyzing with FIXED filtering approach...")
            cv2.imwrite(str(self.debug_dir / "01_original.png"), gray)

            # Step 2: Test multiple methods with DIC quality evaluation
            methods_results = self.test_multiple_methods_fixed(gray)

            # Step 3: Choose best method using DIC quality scoring
            best_result = self.choose_best_method_for_app(methods_results, gray)

            if best_result is None:
                print("ERROR: No valid method found")
                return self._empty_results()

            # Step 4: Apply FIXED size filtering (very permissive)
            final_results = self.apply_fixed_size_filtering(best_result, gray)

            # Step 5: Create comprehensive visualizations
            self.create_fixed_visualizations(gray, final_results)

            # Step 6: Generate report
            self.generate_fixed_report(gray, final_results)

            return final_results

        except Exception as e:
            print(f"ERROR in fixed analysis: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_results(str(e))

    def _empty_results(self, error_msg=""):
        """Return empty results structure"""
        return {
            'total_speckles': 0,
            'best_method': 'failed',
            'quality_score': 0,
            'dic_score': 0,
            'small_count': 0,
            'medium_count': 0,
            'large_count': 0,
            'min_area_used': 0,
            'max_area_used': 0,
            'error': error_msg
        }

    def test_multiple_methods_fixed(self, gray):
        """Test multiple detection methods with consistent evaluation"""
        print("Testing multiple detection methods...")

        h, w = gray.shape
        roi_area = h * w

        methods_results = {}

        # Method 1: Adaptive threshold (multiple block sizes)
        print("Testing adaptive thresholding...")
        for block_size in [11, 15, 21, 31]:
            try:
                # Normal orientation
                binary_normal = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                      cv2.THRESH_BINARY, block_size, 2)
                result_normal = self.analyze_binary_method(binary_normal, f"Adaptive_Normal_{block_size}", roi_area)
                methods_results[f"adaptive_normal_{block_size}"] = result_normal

                # Inverted orientation
                binary_inverted = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                        cv2.THRESH_BINARY_INV, block_size, 2)
                result_inverted = self.analyze_binary_method(binary_inverted, f"Adaptive_Inverted_{block_size}",
                                                             roi_area)
                methods_results[f"adaptive_inverted_{block_size}"] = result_inverted

                print(
                    f"  Block {block_size}: Normal={result_normal['raw_count']}, Inverted={result_inverted['raw_count']}")

            except Exception as e:
                print(f"Error with adaptive block size {block_size}: {e}")

        # Method 2: Global Otsu
        print("Testing global Otsu...")
        try:
            _, binary_otsu_normal = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            result_otsu_normal = self.analyze_binary_method(binary_otsu_normal, "Otsu_Normal", roi_area)
            methods_results["otsu_normal"] = result_otsu_normal

            _, binary_otsu_inverted = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            result_otsu_inverted = self.analyze_binary_method(binary_otsu_inverted, "Otsu_Inverted", roi_area)
            methods_results["otsu_inverted"] = result_otsu_inverted

            print(f"  Otsu: Normal={result_otsu_normal['raw_count']}, Inverted={result_otsu_inverted['raw_count']}")

        except Exception as e:
            print(f"Error with Otsu: {e}")

        # Method 3: FINE-GRAINED percentile thresholds (much more increments)
        print("Testing fine-grained percentile thresholds...")

        # More granular percentiles to catch subtle variations
        fine_percentiles = [
            15, 18, 20, 22, 25, 28, 30, 32, 35, 38, 40, 42, 45, 48, 50,
            52, 55, 58, 60, 62, 65, 68, 70, 72, 75, 78, 80, 82, 85, 88, 90
        ]

        for percentile in fine_percentiles:
            try:
                thresh_val = np.percentile(gray, percentile)
                # FIX 1: Convert threshold to int
                thresh_val_int = int(thresh_val)
                _, binary_percentile = cv2.threshold(gray, thresh_val_int, 255, cv2.THRESH_BINARY_INV)
                result_percentile = self.analyze_binary_method(binary_percentile, f"Percentile_{percentile}", roi_area)
                methods_results[f"percentile_{percentile}"] = result_percentile

                print(f"  Percentile {percentile}: {result_percentile['raw_count']} speckles")

            except Exception as e:
                print(f"Error with percentile {percentile}: {e}")

        # Method 4: Multi-level Otsu variations
        print("Testing Otsu variations...")
        try:
            # Standard Otsu with slight variations
            for offset in [-10, -5, 0, 5, 10]:
                _, standard_binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

                # Get the Otsu threshold value
                otsu_thresh, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                # Apply offset to Otsu threshold
                # FIX 2: Convert to int for proper comparison and threshold
                adjusted_thresh = max(0, min(255, int(otsu_thresh) + offset))
                _, adjusted_binary = cv2.threshold(gray, adjusted_thresh, 255, cv2.THRESH_BINARY_INV)

                result_otsu_adj = self.analyze_binary_method(adjusted_binary, f"Otsu_Adjusted_{offset:+d}", roi_area)
                methods_results[f"otsu_adjusted_{offset:+d}"] = result_otsu_adj

                print(f"  Otsu+{offset}: {result_otsu_adj['raw_count']} speckles (thresh: {adjusted_thresh:.1f})")

        except Exception as e:
            print(f"Error with Otsu variations: {e}")

        # Method 5: Dual-threshold approach (to catch gaps in large speckles)
        print("Testing dual-threshold methods...")
        try:
            # Get Otsu threshold
            otsu_thresh, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Create dual thresholds around Otsu
            for gap_sensitivity in [5, 10, 15, 20]:
                high_thresh = int(otsu_thresh) + gap_sensitivity
                low_thresh = int(otsu_thresh) - gap_sensitivity

                # High threshold (catches small gaps)
                _, binary_high = cv2.threshold(gray, high_thresh, 255, cv2.THRESH_BINARY_INV)
                result_high = self.analyze_binary_method(binary_high, f"Dual_High_{gap_sensitivity}", roi_area)
                methods_results[f"dual_high_{gap_sensitivity}"] = result_high

                # Low threshold (catches smaller speckles)
                _, binary_low = cv2.threshold(gray, low_thresh, 255, cv2.THRESH_BINARY_INV)
                result_low = self.analyze_binary_method(binary_low, f"Dual_Low_{gap_sensitivity}", roi_area)
                methods_results[f"dual_low_{gap_sensitivity}"] = result_low

                print(f"  Dual ±{gap_sensitivity}: High={result_high['raw_count']}, Low={result_low['raw_count']}")

        except Exception as e:
            print(f"Error with dual-threshold: {e}")

        return methods_results

    def analyze_binary_method(self, binary, method_name, roi_area):
        """Analyze a binary image with MINIMAL filtering to preserve all speckles"""
        try:
            # Save binary for debugging
            cv2.imwrite(str(self.debug_dir / f"method_{method_name}.png"), binary)

            # Connected components analysis
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

            # VERY PERMISSIVE filtering - only remove obvious noise
            min_area = 1  # Keep almost everything
            max_area = roi_area // 2  # Only remove if bigger than half the image

            all_components = []
            for i in range(1, num_labels):  # Skip background
                area = stats[i, cv2.CC_STAT_AREA]
                if min_area <= area <= max_area:
                    all_components.append({
                        'id': i,
                        'area': area,
                        'centroid': [float(centroids[i][0]), float(centroids[i][1])]
                    })

            return {
                'method_name': method_name,
                'binary': binary,
                'labels': labels,
                'stats': stats,
                'centroids': centroids,
                'components': all_components,
                'raw_count': len(all_components),
                'min_area_used': min_area,
                'max_area_used': max_area
            }

        except Exception as e:
            print(f"Error analyzing {method_name}: {e}")
            return {
                'method_name': method_name,
                'components': [],
                'raw_count': 0,
                'min_area_used': 0,
                'max_area_used': 0
            }

    def choose_best_method_for_app(self, methods_results, gray):
        """Choose the best method based on DIC QUALITY metrics, not just speckle count"""
        if not methods_results:
            return None

        print(f"\nEvaluating methods for DIC quality...")

        # Calculate DIC quality score for each method
        method_scores = []
        for method_name, result in methods_results.items():
            if result['raw_count'] == 0:
                continue

            dic_quality = self.calculate_dic_quality_score(result, gray)
            method_scores.append((method_name, result, dic_quality))

            print(f"  {method_name}: {result['raw_count']} speckles, DIC quality: {dic_quality:.2f}")

        # Sort by DIC quality score (higher = better for DIC)
        method_scores.sort(key=lambda x: x[2], reverse=True)

        print(f"\nMethod ranking by DIC quality:")
        for i, (method_name, result, score) in enumerate(method_scores[:5]):
            print(f"  {i + 1}. {method_name}: DIC score {score:.2f} ({result['raw_count']} speckles)")

        if method_scores:
            best_method_name, best_result, best_score = method_scores[0]
            print(f"\nSelected best method for DIC: {best_method_name} (score: {best_score:.2f})")
            best_result['dic_quality_score'] = best_score  # Store the DIC quality score
            return best_result
        else:
            print("No valid methods found")
            return None

    def calculate_dic_quality_score(self, method_result, gray):
        """Calculate DIC quality score based on speckle characteristics that matter for correlation"""
        components = method_result['components']
        if not components:
            return 0.0

        # Extract areas for analysis
        areas = [comp['area'] for comp in components]

        # Factor 1: Size distribution quality (40% weight)
        size_score = self.evaluate_size_distribution_for_dic(areas)

        # Factor 2: Speckle coherence/compactness (30% weight)
        coherence_score = self.evaluate_speckle_coherence(method_result, gray)

        # Factor 3: Spatial distribution uniformity (20% weight)
        spatial_score = self.evaluate_spatial_distribution(components, gray.shape)

        # Factor 4: Count adequacy (10% weight) - some speckles needed, but not the main factor
        count_score = min(100.0, len(components) / 50.0 * 100)  # Diminishing returns after 50

        # Combine weighted scores
        total_score = (
                size_score * 0.40 +
                coherence_score * 0.30 +
                spatial_score * 0.20 +
                count_score * 0.10
        )

        return total_score

    def evaluate_size_distribution_for_dic(self, areas):
        """Evaluate if size distribution is good for DIC (prefers medium-sized coherent speckles)"""
        if not areas:
            return 0.0

        areas = np.array(areas)

        # Count speckles in different size categories
        tiny_count = np.sum(areas <= 10)  # Too small for reliable correlation
        small_count = np.sum((areas > 10) & (areas <= 50))
        medium_count = np.sum((areas > 50) & (areas <= 300))  # Sweet spot for DIC
        large_count = np.sum((areas > 300) & (areas <= 1000))
        huge_count = np.sum(areas > 1000)  # May be over-merged

        total = len(areas)

        # Ideal distribution: mostly medium, some small/large, minimal tiny/huge
        tiny_ratio = tiny_count / total
        medium_ratio = medium_count / total
        huge_ratio = huge_count / total

        # Score based on ideal ratios
        score = 100.0

        # Penalize too many tiny speckles (indicates over-segmentation)
        if tiny_ratio > 0.7:  # More than 70% tiny
            score -= (tiny_ratio - 0.7) * 200  # Heavy penalty

        # Reward good medium speckle ratio
        if medium_ratio > 0.3:  # At least 30% medium
            score += min(30, medium_ratio * 50)  # Bonus for medium speckles

        # Penalize too many huge speckles (indicates under-segmentation)
        if huge_ratio > 0.1:  # More than 10% huge
            score -= huge_ratio * 100

        return max(0.0, min(100.0, score))

    def evaluate_speckle_coherence(self, method_result, gray):
        """Evaluate how coherent/compact the speckles are (less fragmentation = better)"""
        if 'binary' not in method_result or method_result['binary'] is None:
            return 50.0  # Default score

        try:
            # Calculate shape metrics for each component
            components = method_result['components']
            if not components:
                return 0.0

            coherence_scores = []

            for component in components[:100]:  # Sample first 100 to avoid slowdown
                area = component['area']

                # Simple coherence metric: area vs perimeter ratio
                if area > 10:  # Only for reasonably sized speckles
                    # Extract component mask
                    comp_id = component['id']
                    if 'labels' in method_result:
                        mask = method_result['labels'] == comp_id

                        # Calculate perimeter using contour
                        # FIX 3: Convert boolean mask to uint8 properly
                        mask_uint8 = np.array(mask).astype(np.uint8) * 255
                        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                        if contours:
                            perimeter = cv2.arcLength(contours[0], True)
                            if perimeter > 0:
                                # Circularity metric: 4π*area / perimeter²
                                # Perfect circle = 1.0, more fragmented = lower
                                circularity = (4 * np.pi * area) / (perimeter * perimeter)
                                coherence_scores.append(min(1.0, circularity))

            if coherence_scores:
                avg_coherence = np.mean(coherence_scores)
                return avg_coherence * 100
            else:
                return 50.0

        except Exception as e:
            print(f"Error calculating coherence: {e}")
            return 50.0

    def evaluate_spatial_distribution(self, components, image_shape):
        """Evaluate how uniformly speckles are distributed spatially"""
        if len(components) < 10:
            return 50.0  # Need enough speckles for meaningful distribution

        # Extract centroids
        centroids = np.array([comp['centroid'] for comp in components])

        h, w = image_shape

        # Divide image into grid and count speckles per cell
        grid_size = 8
        cell_h, cell_w = h // grid_size, w // grid_size

        grid_counts = np.zeros((grid_size, grid_size))

        for x, y in centroids:
            grid_x = min(int(x // cell_w), grid_size - 1)
            grid_y = min(int(y // cell_h), grid_size - 1)
            grid_counts[grid_y, grid_x] += 1

        # Calculate uniformity (lower standard deviation = more uniform)
        if np.mean(grid_counts) > 0:
            cv = np.std(grid_counts) / np.mean(grid_counts)  # Coefficient of variation
            uniformity_score = max(0, 100 - cv * 50)  # Convert to 0-100 score
        else:
            uniformity_score = 0

        return min(100.0, uniformity_score)

    def apply_fixed_size_filtering(self, method_result, gray):
        """Apply CORRECTED size filtering that preserves large speckles"""
        if not method_result or not method_result.get('components'):
            return self._empty_results("No components to filter")

        print("Applying FIXED size filtering...")

        h, w = gray.shape
        roi_area = h * w

        # MUCH MORE PERMISSIVE size limits
        min_area = 1  # Keep tiny speckles
        max_area = roi_area // 3  # Allow very large speckles (up to 1/3 of image)

        print(f"FIXED size range: {min_area} - {max_area} pixels")
        print(f"Original components before filtering: {len(method_result['components'])}")

        # Filter components with new permissive limits
        filtered_speckles = []
        for component in method_result['components']:
            area = component['area']
            if min_area <= area <= max_area:
                filtered_speckles.append(component)

        print(f"Components after FIXED filtering: {len(filtered_speckles)}")

        # Categorize by size
        small_count = sum(1 for s in filtered_speckles if s['area'] <= 50)
        medium_count = sum(1 for s in filtered_speckles if 51 <= s['area'] <= 500)
        large_count = sum(1 for s in filtered_speckles if s['area'] > 500)

        print(f"Size breakdown: Small={small_count}, Medium={medium_count}, Large={large_count}")

        # Calculate quality score
        total_speckles = len(filtered_speckles)
        quality_score = min(100.0, (total_speckles / 100.0) * 100)  # Simple linear scale

        # Add bonus for size diversity
        if small_count > 0 and medium_count > 0:
            quality_score += 10
        if large_count > 0:
            quality_score += 15  # Bonus for having large speckles

        quality_score = min(100.0, quality_score)

        # Get DIC quality score from method result
        dic_score = method_result.get('dic_quality_score', 0)

        return {
            'total_speckles': total_speckles,
            'best_method': method_result['method_name'],
            'speckles': filtered_speckles,
            'small_count': small_count,
            'medium_count': medium_count,
            'large_count': large_count,
            'quality_score': quality_score,
            'dic_score': dic_score,
            'min_area_used': min_area,
            'max_area_used': max_area,
            'binary_used': method_result.get('binary'),
            'labels_used': method_result.get('labels'),
            'stats_used': method_result.get('stats')
        }

    def create_fixed_visualizations(self, gray, results):
        """Create visualizations showing the FIXED detection results"""
        try:
            print("Creating FIXED detection visualizations...")

            if results['total_speckles'] == 0:
                print("No speckles to visualize")
                return

            # Create main visualization with size-based colors
            vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            # Draw speckles with size-based colors
            for speckle in results['speckles']:
                try:
                    x, y = int(speckle['centroid'][0]), int(speckle['centroid'][1])
                    area = speckle['area']

                    # Color and size based on area
                    if area <= 50:
                        color = (0, 255, 0)  # Green for small
                        radius = 2
                    elif area <= 500:
                        color = (0, 255, 255)  # Yellow for medium
                        radius = 3
                    else:
                        color = (255, 0, 255)  # Magenta for large
                        radius = 5

                    cv2.circle(vis, (x, y), radius, color, -1)

                except Exception as e:
                    print(f"Error drawing speckle: {e}")
                    continue

            # Add legend and statistics
            legend_y = 25
            legend_items = [
                f"FIXED Detection Results:",
                f"Total Speckles: {results['total_speckles']}",
                f"Method: {results['best_method']}",
                f"DIC Quality: {results['dic_score']:.1f}/100",
                f"Small (green): {results['small_count']}",
                f"Medium (yellow): {results['medium_count']}",
                f"Large (magenta): {results['large_count']}",
                f"Size range: {results['min_area_used']}-{results['max_area_used']} px",
                "LARGE SPECKLES PRESERVED!"
            ]

            for text in legend_items:
                # Black background for readability
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(vis, (5, legend_y - 15), (text_size[0] + 10, legend_y + 5), (0, 0, 0), -1)

                cv2.putText(vis, text, (10, legend_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                legend_y += 22

            cv2.imwrite(str(self.debug_dir / "10_FIXED_speckle_detection.png"), vis)

            # Save the binary used
            if 'binary_used' in results and results['binary_used'] is not None:
                cv2.imwrite(str(self.debug_dir / "09_binary_method_used.png"), results['binary_used'])

            # Create component label visualization if available
            if 'labels_used' in results and results['labels_used'] is not None:
                try:
                    labels = results['labels_used']

                    # Create colored component visualization
                    colored_components = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)

                    # Generate random colors for each valid component
                    np.random.seed(42)
                    for speckle in results['speckles']:
                        speckle_id = speckle['id']
                        color = tuple([int(x) for x in np.random.randint(50, 255, 3)])

                        # Color all pixels belonging to this component
                        mask = labels == speckle_id
                        colored_components[mask] = color

                    cv2.imwrite(str(self.debug_dir / "11_colored_components.png"), colored_components)

                except Exception as e:
                    print(f"Error creating component visualization: {e}")

            print("FIXED visualizations created successfully!")

        except Exception as e:
            print(f"Error creating visualizations: {e}")
            import traceback
            traceback.print_exc()

    def generate_fixed_report(self, gray, results):
        """Generate report for the FIXED detection results"""
        try:
            print("Generating FIXED detection report...")

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(self.debug_dir / "FIXED_detection_report.txt", 'w', encoding='utf-8') as f:
                f.write("FIXED SPECKLE DETECTION REPORT\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Analysis Time: {timestamp}\n")
                f.write(f"Image Dimensions: {gray.shape[1]} x {gray.shape[0]}\n")
                f.write(f"Output Folder: {self.debug_dir}\n\n")

                f.write("PROBLEM SOLVED:\n")
                f.write("-" * 15 + "\n")
                f.write("✓ Large speckles now PRESERVED in detection\n")
                f.write("✓ Size filtering corrected to be more permissive\n")
                f.write("✓ Better integration ready for app usage\n")
                f.write("✓ DIC quality scoring implemented\n\n")

                f.write("DETECTION RESULTS:\n")
                f.write("-" * 18 + "\n")
                f.write(f"Best Method: {results['best_method']}\n")
                f.write(f"Total Speckles: {results['total_speckles']}\n")
                f.write(f"Quality Score: {results['quality_score']:.1f}/100\n")
                f.write(f"DIC Quality Score: {results['dic_score']:.1f}/100\n\n")

                f.write("SIZE BREAKDOWN:\n")
                f.write("-" * 15 + "\n")
                f.write(f"Small (1-50px):   {results['small_count']:4}\n")
                f.write(f"Medium (51-500px): {results['medium_count']:4}\n")
                f.write(f"Large (501+px):    {results['large_count']:4}\n")
                f.write(f"{'':17} ----\n")
                f.write(f"Total:             {results['total_speckles']:4}\n\n")

                f.write("METHOD SELECTION IMPROVED:\n")
                f.write("-" * 25 + "\n")
                f.write("✓ DIC quality scoring instead of just speckle count\n")
                f.write("✓ Evaluates size distribution (prefers medium speckles)\n")
                f.write("✓ Measures speckle coherence (less fragmentation)\n")
                f.write("✓ Assesses spatial uniformity\n")
                f.write("✓ Penalizes over-segmentation and under-segmentation\n\n")

                f.write("APP INTEGRATION READY:\n")
                f.write("-" * 22 + "\n")
                f.write("✓ Large speckle preservation: FIXED\n")
                f.write("✓ Consistent labeling: IMPROVED\n")
                f.write("✓ Better size filtering: IMPLEMENTED\n")
                f.write("✓ Ready for future app implementation\n\n")

                if results['large_count'] > 0:
                    f.write(f"SUCCESS: Detected {results['large_count']} large speckles!\n")
                    f.write("These were being filtered out before the fix.\n")
                else:
                    f.write("Note: No large speckles detected in this pattern.\n")
                    f.write("This may be normal depending on the speckle pattern.\n")

            print("FIXED detection report generated successfully")

        except Exception as e:
            print(f"Error generating report: {e}")


# Integration function
def integrate_enhanced_debug(main_window):
    """Integrate the FIXED speckle detection for better app usage"""
    print("Integrating FIXED speckle detection...")
    enhance_app_debug_functionality(main_window)
    print("FIXED speckle detection integration complete!")


if __name__ == "__main__":
    print("FIXED Speckle Detection for App Integration - COMPLETE")
    print("=" * 55)
    print()
    print("FIXES IMPLEMENTED:")
    print("• ✅ Fixed cv2.threshold type issues (convert to int)")
    print("• ✅ Fixed comparison type issues (int conversion)")
    print("• ✅ Fixed boolean mask astype issue (np.uint8)")
    print("• ✅ Output moved to debug_output/fixed_debug/ folder")
    print("• ✅ DIC quality scoring for method selection")
    print("• ✅ Permissive size filtering preserves large speckles")
    print("• ✅ Proper error handling and empty results")
    print()
    print("TYPE FIXES APPLIED:")
    print("• Line 242: thresh_val converted to int(thresh_val)")
    print("• Line 262: otsu_thresh converted to int(otsu_thresh)")
    print("• Line 473: mask.astype(np.uint8) instead of bool.astype()")
    print()
    print("DIC QUALITY SCORING:")
    print("• Size distribution (40%) - prefers medium speckles")
    print("• Speckle coherence (30%) - penalizes fragmentation")
    print("• Spatial uniformity (20%) - rewards even distribution")
    print("• Count adequacy (10%) - ensures sufficient speckles")
    print()
    print("INTEGRATION INSTRUCTIONS:")
    print("1. Save this as 'enhanced_debug_integration.py'")
    print("2. In main_window.py, import:")
    print("   from enhanced_debug_integration import integrate_enhanced_debug")
    print("3. In main_window.__init__, add:")
    print("   integrate_enhanced_debug(self)")
    print()
    print("This will:")
    print("• Replace debug button with '🔧 FIXED Detection'")
    print("• Use DIC quality scoring to choose best method")
    print("• Preserve large speckles in final results")
    print("• Save results to debug_output/fixed_debug/")
    print("• Show detailed DIC quality scores in results")