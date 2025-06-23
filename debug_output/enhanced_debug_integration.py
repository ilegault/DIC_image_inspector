# enhanced_debug_integration_BLUR_AWARE.py
# Fixed with blur detection and adaptive method selection

import cv2
import numpy as np
from pathlib import Path
import datetime


def enhance_app_debug_functionality(main_window):
    """Enhanced debug with BLUR-AWARE method selection for better results"""

    # Store the original debug function
    original_save_debug = main_window.image_display.save_debug_visualizations

    def blur_aware_debug_visualizations():
        """Blur-aware version that chooses methods based on image characteristics"""
        print("\n" + "=" * 60)
        print("BLUR-AWARE SPECKLE DETECTION - SMART METHOD SELECTION")
        print("=" * 60)

        try:
            # First run the original debug function
            print("Running original debug visualizations...")
            original_save_debug()
            print("Original debug completed successfully")

            # Now add our BLUR-AWARE speckle detection
            print("Starting BLUR-AWARE speckle detection...")

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

            # Run BLUR-AWARE analysis
            analyzer = BlurAwareSpeckleAnalyzer()
            results = analyzer.analyze_with_blur_detection(roi_image)

            # Show results in messagebox
            from tkinter import messagebox

            total_speckles = results.get('total_speckles', 0)
            large_speckles = results.get('large_count', 0)
            medium_speckles = results.get('medium_count', 0)
            small_speckles = results.get('small_count', 0)
            dic_score = results.get('dic_score', 0)
            blur_level = results.get('blur_level', 'unknown')
            blur_score = results.get('blur_score', 0)

            message = f"""BLUR-AWARE Speckle Detection Complete!

Original Debug: [OK] Completed successfully
BLUR-AWARE Detection: [OK] Smart method selection!

IMAGE ANALYSIS:
================================================
Blur Detection: {blur_level} (score: {blur_score:.1f})
Best Method: {results.get('best_method', 'unknown')}
Total Speckles: {total_speckles}
DIC Quality Score: {dic_score:.1f}/100

SIZE BREAKDOWN (BLUR-OPTIMIZED):
- Small (1-50px): {small_speckles}
- Medium (51-500px): {medium_speckles} 
- Large (501+ px): {large_speckles}

BLUR-AWARE IMPROVEMENTS:
- Detects image blur automatically
- Prefers adaptive methods for blurry images
- Adjusts quality scoring for blur conditions
- Better method ranking for image characteristics

DEBUG FILES SAVED:
- debug_output/blur_aware_debug/ - Complete analysis
================================================

Method selection now optimized for image blur level!"""

            messagebox.showinfo("BLUR-AWARE Detection Complete", message)

            # Update status
            main_window.status_var.set(
                f"BLUR-AWARE: {total_speckles} speckles (L:{large_speckles}, M:{medium_speckles}, S:{small_speckles}) DIC:{dic_score:.1f} Blur:{blur_level}"
            )

            print("=" * 60)
            print("BLUR-AWARE SPECKLE DETECTION COMPLETED")
            print(f"Image blur level: {blur_level} (score: {blur_score:.1f})")
            print(f"Selected method: {results.get('best_method', 'unknown')}")
            print(f"Total speckles: {total_speckles} (L:{large_speckles}, M:{medium_speckles}, S:{small_speckles})")
            print(f"DIC Quality Score: {dic_score:.1f}/100")
            print("=" * 60)

        except Exception as e:
            print(f"ERROR in blur-aware speckle detection: {e}")
            import traceback
            traceback.print_exc()

            from tkinter import messagebox
            messagebox.showerror("Blur-Aware Detection Error",
                                 f"Blur-aware speckle detection failed: {str(e)}\n\nCheck console for details.")

    # Replace the debug button command
    main_window.debug_btn.config(command=blur_aware_debug_visualizations)
    main_window.debug_btn.config(text="🔍 BLUR-AWARE Detection")

    print("Successfully enhanced debug button with BLUR-AWARE speckle detection!")


class BlurAwareSpeckleAnalyzer:
    """Analyzer with blur detection and adaptive method selection"""

    def __init__(self):
        # Use debug_output folder as requested
        self.debug_dir = Path("debug_output") / "blur_aware_debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        print(f"Using debug folder: {self.debug_dir}")

    def analyze_with_blur_detection(self, roi_image):
        """Analyze with blur detection and adaptive method selection"""
        print(f"Input image shape: {roi_image.shape}")

        try:
            # Step 1: Convert to grayscale
            if len(roi_image.shape) == 3:
                gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi_image.copy()

            cv2.imwrite(str(self.debug_dir / "01_original.png"), gray)

            # Step 2: Detect image blur level
            blur_analysis = self.detect_image_blur(gray)
            print(f"Blur analysis: {blur_analysis['level']} (score: {blur_analysis['score']:.1f})")

            # Step 3: Test methods with blur-aware evaluation
            methods_results = self.test_multiple_methods_blur_aware(gray)

            # Step 4: Choose best method using blur-aware scoring
            best_result = self.choose_best_method_blur_aware(methods_results, gray, blur_analysis)

            if best_result is None:
                print("ERROR: No valid method found")
                return self._empty_results()

            # Step 5: Apply size filtering
            final_results = self.apply_size_filtering(best_result, gray)

            # Add blur information to results
            final_results['blur_level'] = blur_analysis['level']
            final_results['blur_score'] = blur_analysis['score']
            final_results['blur_analysis'] = blur_analysis

            # Step 6: Create visualizations and report
            self.create_blur_aware_visualizations(gray, final_results)
            self.generate_blur_aware_report(gray, final_results)

            return final_results

        except Exception as e:
            print(f"ERROR in blur-aware analysis: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_results(str(e))

    def detect_image_blur(self, gray):
        """Detect if image is blurry using multiple methods"""
        h, w = gray.shape

        # Method 1: Laplacian variance (standard blur detection)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Method 2: Sobel gradient variance
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel_var = np.var(np.sqrt(grad_x ** 2 + grad_y ** 2))

        # Method 3: High frequency content in FFT
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)

        # Calculate high frequency ratio
        center_y, center_x = h // 2, w // 2
        high_freq_radius = min(h, w) // 4
        y, x = np.ogrid[:h, :w]
        high_freq_mask = (x - center_x) ** 2 + (y - center_y) ** 2 > high_freq_radius ** 2

        total_energy = np.sum(magnitude_spectrum)
        high_freq_energy = np.sum(magnitude_spectrum[high_freq_mask])
        high_freq_ratio = high_freq_energy / total_energy if total_energy > 0 else 0

        # Combine metrics for overall blur score
        # Normalize each metric
        laplacian_norm = min(100, laplacian_var / 100)  # Typical range 0-10000
        sobel_norm = min(100, sobel_var / 1000)  # Typical range 0-100000
        fft_norm = high_freq_ratio * 100  # Already 0-1

        # Weighted combination
        blur_score = (laplacian_norm * 0.4 + sobel_norm * 0.4 + fft_norm * 0.2)

        # Classify blur level
        if blur_score > 60:
            blur_level = "Sharp"
        elif blur_score > 30:
            blur_level = "Slightly Blurry"
        elif blur_score > 15:
            blur_level = "Moderately Blurry"
        else:
            blur_level = "Very Blurry"

        # Save blur analysis image
        blur_vis = self.create_blur_visualization(gray, laplacian_var, sobel_var, high_freq_ratio)
        cv2.imwrite(str(self.debug_dir / "02_blur_analysis.png"), blur_vis)

        return {
            'score': blur_score,
            'level': blur_level,
            'laplacian_var': laplacian_var,
            'sobel_var': sobel_var,
            'high_freq_ratio': high_freq_ratio,
            'is_blurry': blur_score < 30
        }

    def create_blur_visualization(self, gray, laplacian_var, sobel_var, high_freq_ratio):
        """Create clean visualization without text overlay"""
        # Just return the clean grayscale image converted to BGR
        vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return vis

    def test_multiple_methods_blur_aware(self, gray):
        """Test methods with expanded adaptive thresholding for blurry images"""
        print("Testing methods with blur-aware selection...")

        h, w = gray.shape
        roi_area = h * w
        methods_results = {}

        # Enhanced adaptive thresholding (especially important for blurry images)
        print("Testing enhanced adaptive thresholding...")
        adaptive_block_sizes = [7, 9, 11, 13, 15, 17, 19, 21, 25, 31, 35, 41]  # More options
        adaptive_c_values = [1, 2, 3, 4, 5]  # Different C values

        for block_size in adaptive_block_sizes:
            for c_val in adaptive_c_values:
                try:
                    # Normal orientation
                    binary_normal = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                          cv2.THRESH_BINARY, block_size, c_val)
                    result_normal = self.analyze_binary_method(binary_normal,
                                                               f"Adaptive_Normal_{block_size}_C{c_val}", roi_area)
                    methods_results[f"adaptive_normal_{block_size}_c{c_val}"] = result_normal

                    # Inverted orientation
                    binary_inverted = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                            cv2.THRESH_BINARY_INV, block_size, c_val)
                    result_inverted = self.analyze_binary_method(binary_inverted,
                                                                 f"Adaptive_Inverted_{block_size}_C{c_val}", roi_area)
                    methods_results[f"adaptive_inverted_{block_size}_c{c_val}"] = result_inverted

                except Exception as e:
                    print(f"Error with adaptive {block_size}, C={c_val}: {e}")

        # Mean adaptive thresholding (often better for blurry images)
        print("Testing mean adaptive thresholding...")
        for block_size in [11, 15, 21, 31]:
            for c_val in [1, 2, 3, 4]:
                try:
                    binary_mean_normal = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                                               cv2.THRESH_BINARY, block_size, c_val)
                    result_mean_normal = self.analyze_binary_method(binary_mean_normal,
                                                                    f"Mean_Normal_{block_size}_C{c_val}", roi_area)
                    methods_results[f"mean_normal_{block_size}_c{c_val}"] = result_mean_normal

                    binary_mean_inverted = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                                                 cv2.THRESH_BINARY_INV, block_size, c_val)
                    result_mean_inverted = self.analyze_binary_method(binary_mean_inverted,
                                                                      f"Mean_Inverted_{block_size}_C{c_val}", roi_area)
                    methods_results[f"mean_inverted_{block_size}_c{c_val}"] = result_mean_inverted

                except Exception as e:
                    print(f"Error with mean adaptive {block_size}, C={c_val}: {e}")

        # Standard Otsu (for comparison)
        print("Testing Otsu methods...")
        try:
            _, binary_otsu_normal = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            result_otsu_normal = self.analyze_binary_method(binary_otsu_normal, "Otsu_Normal", roi_area)
            methods_results["otsu_normal"] = result_otsu_normal

            _, binary_otsu_inverted = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            result_otsu_inverted = self.analyze_binary_method(binary_otsu_inverted, "Otsu_Inverted", roi_area)
            methods_results["otsu_inverted"] = result_otsu_inverted
        except Exception as e:
            print(f"Error with Otsu: {e}")

        # Preprocessed methods (blur reduction before thresholding)
        print("Testing preprocessed methods...")
        try:
            # Gaussian blur reduction
            deblurred = cv2.GaussianBlur(gray, (3, 3), 0)
            _, binary_deblur = cv2.threshold(deblurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            result_deblur = self.analyze_binary_method(binary_deblur, "Deblurred_Otsu", roi_area)
            methods_results["deblurred_otsu"] = result_deblur

            # Unsharp masking
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            unsharp = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
            _, binary_unsharp = cv2.threshold(unsharp, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            result_unsharp = self.analyze_binary_method(binary_unsharp, "Unsharp_Otsu", roi_area)
            methods_results["unsharp_otsu"] = result_unsharp

        except Exception as e:
            print(f"Error with preprocessed methods: {e}")

        print(f"Tested {len(methods_results)} methods total")
        return methods_results

    def choose_best_method_blur_aware(self, methods_results, gray, blur_analysis):
        """Choose best method considering blur characteristics"""
        if not methods_results:
            return None

        print(f"\nEvaluating methods with blur-aware scoring...")
        print(f"Image blur level: {blur_analysis['level']} (score: {blur_analysis['score']:.1f})")

        method_scores = []
        for method_name, result in methods_results.items():
            if result['raw_count'] == 0:
                continue

            # Calculate base DIC quality
            base_quality = self.calculate_dic_quality_score(result, gray)

            # Apply blur-aware adjustments
            blur_adjusted_quality = self.apply_blur_adjustments(base_quality, method_name, blur_analysis)

            method_scores.append((method_name, result, blur_adjusted_quality, base_quality))

        # Sort by blur-adjusted quality score
        method_scores.sort(key=lambda x: x[2], reverse=True)

        print(f"\nTop 10 methods (blur-adjusted scoring):")
        for i, (method_name, result, adj_score, base_score) in enumerate(method_scores[:10]):
            adjustment = adj_score - base_score
            print(
                f"  {i + 1:2d}. {method_name:30} | Adj: {adj_score:5.1f} | Base: {base_score:5.1f} | Δ: {adjustment:+5.1f} | Count: {result['raw_count']}")

        if method_scores:
            best_method_name, best_result, best_score, base_score = method_scores[0]
            print(f"\nSelected method: {best_method_name}")
            print(f"  Blur-adjusted score: {best_score:.2f}")
            print(f"  Base DIC score: {base_score:.2f}")
            print(f"  Blur adjustment: {best_score - base_score:+.2f}")

            best_result['dic_quality_score'] = best_score
            best_result['base_dic_score'] = base_score
            return best_result
        else:
            print("No valid methods found")
            return None

    def apply_blur_adjustments(self, base_score, method_name, blur_analysis):
        """Apply blur-specific adjustments to method scoring"""
        adjusted_score = base_score
        is_blurry = blur_analysis['is_blurry']
        blur_level = blur_analysis['level']

        # Boost adaptive methods for blurry images
        if is_blurry and 'adaptive' in method_name.lower():
            # Higher boost for mean adaptive on very blurry images
            if 'mean' in method_name.lower() and blur_level == "Very Blurry":
                adjusted_score += 25  # Strong boost
            elif 'adaptive' in method_name.lower():
                adjusted_score += 15  # Moderate boost

            # Prefer larger block sizes for blurry images
            if '_21_' in method_name or '_25_' in method_name or '_31_' in method_name:
                adjusted_score += 10
            elif '_35_' in method_name or '_41_' in method_name:
                adjusted_score += 15  # Even larger blocks for very blurry

        # Penalize Otsu methods for blurry images
        if is_blurry and 'otsu' in method_name.lower() and 'deblurred' not in method_name.lower():
            adjusted_score -= 20  # Significant penalty

        # Boost preprocessed methods for blurry images
        if is_blurry and ('deblurred' in method_name.lower() or 'unsharp' in method_name.lower()):
            adjusted_score += 20

        # For sharp images, prefer Otsu and penalize over-complex adaptive methods
        if not is_blurry:
            if 'otsu' in method_name.lower():
                adjusted_score += 10  # Boost Otsu for sharp images
            elif 'adaptive' in method_name.lower():
                # Penalize very large block sizes for sharp images
                if '_35_' in method_name or '_41_' in method_name:
                    adjusted_score -= 10

        return max(0, adjusted_score)  # Ensure non-negative

    def calculate_dic_quality_score(self, method_result, gray):
        """Calculate base DIC quality score (same as before but simplified)"""
        components = method_result['components']
        if not components:
            return 0.0

        areas = [comp['area'] for comp in components]

        # Simple scoring based on component count and size distribution
        count_score = min(100, int(len(components) / 20 * 100))  # Up to 100 for 20+ components

        # Size distribution score
        if areas:
            small_count = sum(1 for a in areas if a <= 50)
            medium_count = sum(1 for a in areas if 50 < a <= 500)
            large_count = sum(1 for a in areas if a > 500)
            total = len(areas)

            # Prefer balanced distribution
            medium_ratio = medium_count / total
            size_score = medium_ratio * 100
        else:
            size_score = 0

        return (count_score * 0.6 + size_score * 0.4)

    def analyze_binary_method(self, binary, method_name, roi_area):
        """Analyze binary image (same as before)"""
        try:
            cv2.imwrite(str(self.debug_dir / f"method_{method_name}.png"), binary)

            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

            min_area = 1
            max_area = roi_area // 2

            all_components = []
            for i in range(1, num_labels):
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

    def apply_size_filtering(self, method_result, gray):
        """Apply size filtering (same as before)"""
        if not method_result or not method_result.get('components'):
            return self._empty_results("No components to filter")

        h, w = gray.shape
        roi_area = h * w

        min_area = 1
        max_area = roi_area // 3

        filtered_speckles = []
        for component in method_result['components']:
            area = component['area']
            if min_area <= area <= max_area:
                filtered_speckles.append(component)

        small_count = sum(1 for s in filtered_speckles if s['area'] <= 50)
        medium_count = sum(1 for s in filtered_speckles if 51 <= s['area'] <= 500)
        large_count = sum(1 for s in filtered_speckles if s['area'] > 500)

        total_speckles = len(filtered_speckles)
        quality_score = min(100.0, (total_speckles / 100.0) * 100)

        if small_count > 0 and medium_count > 0:
            quality_score += 10
        if large_count > 0:
            quality_score += 15

        quality_score = min(100.0, quality_score)
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

    def create_blur_aware_visualizations(self, gray, results):
        """Create visualizations with blur information"""
        try:
            print("Creating blur-aware visualizations...")

            if results['total_speckles'] == 0:
                print("No speckles to visualize")
                return

            # Main visualization with size-based colors (clean, no text)
            vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            # Draw speckles with size-based colors
            for speckle in results['speckles']:
                try:
                    x, y = int(speckle['centroid'][0]), int(speckle['centroid'][1])
                    area = speckle['area']

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
                    continue

            # Save clean detection visualization
            cv2.imwrite(str(self.debug_dir / "10_BLUR_AWARE_detection.png"), vis)

            # Create separate visualization WITH text for reference
            vis_with_text = vis.copy()
            legend_y = 25
            legend_items = [
                f"BLUR-AWARE Detection Results:",
                f"Blur Level: {results['blur_level']} ({results['blur_score']:.1f})",
                f"Method: {results['best_method']}",
                f"Total Speckles: {results['total_speckles']}",
                f"DIC Quality: {results['dic_score']:.1f}/100",
                f"Small (green): {results['small_count']}",
                f"Medium (yellow): {results['medium_count']}",
                f"Large (magenta): {results['large_count']}",
                "METHOD OPTIMIZED FOR BLUR LEVEL!"
            ]

            for text in legend_items:
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(vis_with_text, (5, legend_y - 15), (text_size[0] + 10, legend_y + 5), (0, 0, 0), -1)
                cv2.putText(vis_with_text, text, (10, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                legend_y += 22

            # Save version with text overlay for reference
            cv2.imwrite(str(self.debug_dir / "10_BLUR_AWARE_detection_with_info.png"), vis_with_text)

            # Save the binary used (clean)
            if 'binary_used' in results and results['binary_used'] is not None:
                cv2.imwrite(str(self.debug_dir / "09_binary_method_used.png"), results['binary_used'])

            # Create COLORED COMPONENTS visualization (the one you liked!)
            if 'labels_used' in results and results['labels_used'] is not None:
                try:
                    labels = results['labels_used']

                    # Create colored component visualization
                    colored_components = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)

                    # Generate random colors for each valid component
                    np.random.seed(42)  # Consistent colors
                    for speckle in results['speckles']:
                        speckle_id = speckle['id']
                        color = tuple([int(x) for x in np.random.randint(50, 255, 3)])

                        # Color all pixels belonging to this component
                        mask = labels == speckle_id
                        colored_components[mask] = color

                    cv2.imwrite(str(self.debug_dir / "11_colored_components.png"), colored_components)
                    print("Created colored components visualization!")

                except Exception as e:
                    print(f"Error creating colored components visualization: {e}")

            print("Blur-aware visualizations created successfully!")
            print("Files created:")
            print("  - 10_BLUR_AWARE_detection.png (clean, no text)")
            print("  - 10_BLUR_AWARE_detection_with_info.png (with text overlay)")
            print("  - 11_colored_components.png (colorful components)")
            print("  - 09_binary_method_used.png (binary threshold)")

        except Exception as e:
            print(f"Error creating visualizations: {e}")
            import traceback
            traceback.print_exc()

    def generate_blur_aware_report(self, gray, results):
        """Generate comprehensive report including blur analysis"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(self.debug_dir / "BLUR_AWARE_detection_report.txt", 'w', encoding='utf-8') as f:
                f.write("BLUR-AWARE SPECKLE DETECTION REPORT\n")
                f.write("=" * 45 + "\n\n")
                f.write(f"Analysis Time: {timestamp}\n")
                f.write(f"Image Dimensions: {gray.shape[1]} x {gray.shape[0]}\n")
                f.write(f"Output Folder: {self.debug_dir}\n\n")

                f.write("BLUR ANALYSIS:\n")
                f.write("-" * 15 + "\n")
                blur_info = results.get('blur_analysis', {})
                f.write(f"Blur Level: {results['blur_level']}\n")
                f.write(f"Blur Score: {results['blur_score']:.1f}/100\n")
                if blur_info:
                    f.write(f"Laplacian Variance: {blur_info.get('laplacian_var', 0):.1f}\n")
                    f.write(f"Sobel Variance: {blur_info.get('sobel_var', 0):.1f}\n")
                    f.write(f"High Freq Ratio: {blur_info.get('high_freq_ratio', 0):.3f}\n")
                f.write("\n")

                f.write("METHOD SELECTION:\n")
                f.write("-" * 17 + "\n")
                f.write(f"Best Method: {results['best_method']}\n")
                f.write(f"DIC Quality Score: {results['dic_score']:.1f}/100\n")

                # Show why this method was chosen for this blur level
                if results['blur_level'] in ["Very Blurry", "Moderately Blurry"]:
                    f.write("✓ Adaptive thresholding preferred for blurry images\n")
                    f.write("✓ Larger block sizes better handle blur\n")
                    f.write("✓ Otsu methods penalized for blur conditions\n")
                elif results['blur_level'] == "Sharp":
                    f.write("✓ Otsu methods preferred for sharp images\n")
                    f.write("✓ Simple thresholding sufficient\n")
                f.write("\n")

                f.write("DETECTION RESULTS:\n")
                f.write("-" * 18 + "\n")
                f.write(f"Total Speckles: {results['total_speckles']}\n")
                f.write(f"Quality Score: {results['quality_score']:.1f}/100\n\n")

                f.write("SIZE BREAKDOWN:\n")
                f.write("-" * 15 + "\n")
                f.write(f"Small (1-50px):   {results['small_count']:4}\n")
                f.write(f"Medium (51-500px): {results['medium_count']:4}\n")
                f.write(f"Large (501+px):    {results['large_count']:4}\n")
                f.write(f"{'':17} ----\n")
                f.write(f"Total:             {results['total_speckles']:4}\n\n")

                f.write("BLUR-AWARE IMPROVEMENTS:\n")
                f.write("-" * 25 + "\n")
                f.write("✓ Automatic blur detection using multiple metrics\n")
                f.write("✓ Method selection adapted to image characteristics\n")
                f.write("✓ Enhanced adaptive thresholding for blurry images\n")
                f.write("✓ Preprocessing methods tested for severe blur\n")
                f.write("✓ Scoring adjustments based on blur level\n\n")

                f.write("BLUR-SPECIFIC OPTIMIZATIONS:\n")
                f.write("-" * 29 + "\n")
                if results['blur_level'] in ["Very Blurry", "Moderately Blurry"]:
                    f.write("• Tested multiple adaptive block sizes (7-41 pixels)\n")
                    f.write("• Tested both Gaussian and Mean adaptive methods\n")
                    f.write("• Applied blur reduction preprocessing\n")
                    f.write("• Boosted adaptive methods in scoring\n")
                    f.write("• Penalized global Otsu thresholding\n")
                else:
                    f.write("• Standard methods sufficient for sharp images\n")
                    f.write("• Otsu thresholding preferred\n")
                    f.write("• Avoided over-complex adaptive methods\n")
                f.write("\n")

                f.write("RECOMMENDATIONS:\n")
                f.write("-" * 16 + "\n")
                if results['blur_level'] == "Very Blurry":
                    f.write("• Consider improving image sharpness for better DIC results\n")
                    f.write("• Check camera focus and lighting conditions\n")
                    f.write("• Larger speckles may be needed for reliable correlation\n")
                elif results['blur_level'] in ["Moderately Blurry", "Slightly Blurry"]:
                    f.write("• Image quality acceptable for DIC with proper analysis\n")
                    f.write("• Consider slight focus adjustment if possible\n")
                else:
                    f.write("• Excellent image sharpness for DIC analysis\n")
                    f.write("• Pattern should provide reliable correlation\n")

                if results['large_count'] > 0:
                    f.write(f"• SUCCESS: Detected {results['large_count']} large speckles\n")
                    f.write("• Large speckles preserved despite blur challenges\n")

            print("Blur-aware detection report generated successfully")

        except Exception as e:
            print(f"Error generating report: {e}")

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
            'blur_level': 'unknown',
            'blur_score': 0,
            'error': error_msg
        }


# Integration function
def integrate_blur_aware_debug(main_window):
    """Integrate the BLUR-AWARE speckle detection"""
    print("Integrating BLUR-AWARE speckle detection...")
    enhance_app_debug_functionality(main_window)
    print("BLUR-AWARE speckle detection integration complete!")


if __name__ == "__main__":
    print("BLUR-AWARE Speckle Detection - COMPLETE")
    print("=" * 45)
    print()
    print("BLUR-AWARE FEATURES:")
    print("• ✅ Automatic image blur detection")
    print("• ✅ Multi-metric blur analysis (Laplacian, Sobel, FFT)")
    print("• ✅ Adaptive method selection based on blur level")
    print("• ✅ Enhanced adaptive thresholding options")
    print("• ✅ Blur-specific scoring adjustments")
    print("• ✅ Preprocessing methods for severe blur")
    print()
    print("BLUR DETECTION METRICS:")
    print("• Laplacian variance (40%) - edge sharpness")
    print("• Sobel gradient variance (40%) - directional edges")
    print("• FFT high frequency content (20%) - frequency analysis")
    print()
    print("METHOD SELECTION LOGIC:")
    print("• BLURRY IMAGES: Prefer adaptive thresholding")
    print("  - Boost Mean adaptive for very blurry images")
    print("  - Prefer larger block sizes (21-41 pixels)")
    print("  - Test preprocessing (deblur, unsharp mask)")
    print("  - Penalize global Otsu methods")
    print()
    print("• SHARP IMAGES: Prefer Otsu methods")
    print("  - Boost global Otsu thresholding")
    print("  - Penalize overly complex adaptive methods")
    print("  - Standard processing sufficient")
    print()
    print("INTEGRATION INSTRUCTIONS:")
    print("1. Save this as 'blur_aware_debug_integration.py'")
    print("2. In main_window.py, import:")
    print("   from blur_aware_debug_integration import integrate_blur_aware_debug")
    print("3. In main_window.__init__, add:")
    print("   integrate_blur_aware_debug(self)")
    print()
    print("This will:")
    print("• Replace debug button with '🔍 BLUR-AWARE Detection'")
    print("• Automatically detect image blur level")
    print("• Choose optimal method for image characteristics")
    print("• Save results to debug_output/blur_aware_debug/")
    print("• Show blur analysis in results")
    print()
    print("For your blurry speckle pattern, this should:")
    print("• Detect blur level automatically")
    print("• Prefer adaptive thresholding over Otsu")
    print("• Test multiple block sizes and C values")
    print("• Provide better speckle detection results")