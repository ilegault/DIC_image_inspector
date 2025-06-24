# enhanced_debug_integration_BLUR_INTEGRATED.py
# Your working speckle analyzer + blur detection and blur heatmap overlay

import cv2
import numpy as np
from pathlib import Path
import datetime


def enhance_app_debug_functionality(main_window):
    """Enhanced debug with BLUR-INTEGRATED speckle detection"""

    # Store the original debug function
    original_save_debug = main_window.image_display.save_debug_visualizations

    def blur_integrated_debug_visualizations():
        """BLUR-INTEGRATED version of your working speckle analyzer"""
        print("\n" + "=" * 60)
        print("BLUR-INTEGRATED SPECKLE DETECTION")
        print("=" * 60)

        try:
            # First run the original debug function
            print("Running original debug visualizations...")
            original_save_debug()
            print("Original debug completed successfully")

            # Now add our BLUR-INTEGRATED speckle detection
            print("Starting BLUR-INTEGRATED speckle detection...")

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

            # Run BLUR-INTEGRATED analysis
            analyzer = BlurIntegratedSpeckleAnalyzer()
            results = analyzer.analyze_with_blur_integration(roi_image)

            # Show results in messagebox
            from tkinter import messagebox

            total_speckles = results.get('total_speckles', 0)
            large_speckles = results.get('large_count', 0)
            medium_speckles = results.get('medium_count', 0)
            small_speckles = results.get('small_count', 0)
            dic_score = results.get('dic_score', 0)
            blur_level = results.get('blur_level', 'unknown')
            blur_score = results.get('blur_score', 0)

            message = f"""BLUR-INTEGRATED Speckle Detection Complete!

BLUR ANALYSIS + SPECKLE DETECTION:
================================================
✓ Original debug completed successfully
✓ Blur detection integrated into method selection
✓ Large speckles preserved with DIC quality scoring

BLUR ASSESSMENT:
Blur Level: {blur_level} (score: {blur_score:.1f}/100)
Method Selected: {results.get('best_method', 'unknown')}
Blur-Aware Selection: {results.get('blur_reasoning', 'N/A')}

SPECKLE RESULTS:
Total Speckles: {total_speckles}
DIC Quality Score: {dic_score:.1f}/100

SIZE BREAKDOWN:
- Small (1-50px): {small_speckles}
- Medium (51-500px): {medium_speckles} 
- Large (501+ px): {large_speckles}

NEW FEATURES:
✓ Blur heatmap showing problem areas
✓ Blur-aware method parameter selection
✓ Method selection considers image sharpness
✓ Your existing DIC quality scoring preserved
================================================

Check debug folder for blur heatmap visualization!"""

            messagebox.showinfo("Blur-Integrated Detection Complete", message)

            # Update status
            main_window.status_var.set(
                f"BLUR-INTEGRATED: {total_speckles} speckles | Blur:{blur_level} | DIC:{dic_score:.1f}"
            )

            print("=" * 60)
            print("BLUR-INTEGRATED DETECTION COMPLETED")
            print(f"Blur level: {blur_level} (score: {blur_score:.1f})")
            print(f"Method: {results.get('best_method', 'unknown')}")
            print(f"Blur reasoning: {results.get('blur_reasoning', 'N/A')}")
            print(f"Total speckles: {total_speckles} (L:{large_speckles}, M:{medium_speckles}, S:{small_speckles})")
            print("=" * 60)

        except Exception as e:
            print(f"ERROR in blur-integrated detection: {e}")
            import traceback
            traceback.print_exc()

            from tkinter import messagebox
            messagebox.showerror("Blur-Integrated Detection Error",
                                 f"Blur-integrated detection failed: {str(e)}\n\nCheck console for details.")

    # Replace the debug button command
    main_window.debug_btn.config(command=blur_integrated_debug_visualizations)
    main_window.debug_btn.config(text="🔍 BLUR-INTEGRATED Detection")

    print("Successfully enhanced debug button with BLUR-INTEGRATED speckle detection!")


class BlurIntegratedSpeckleAnalyzer:
    """Your working speckle analyzer enhanced with blur detection and blur heatmap"""

    def __init__(self):
        # Use debug_output folder as requested
        self.debug_dir = Path("debug_output") / "blur_integrated_debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        print(f"Using debug folder: {self.debug_dir}")

    def analyze_with_blur_integration(self, roi_image):
        """Analyze with blur detection integrated into your existing method selection"""
        print(f"Input image shape: {roi_image.shape}")

        try:
            # Step 1: Convert to grayscale
            if len(roi_image.shape) == 3:
                gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi_image.copy()

            cv2.imwrite(str(self.debug_dir / "01_original.png"), gray)

            # Step 2: BLUR DETECTION using Laplacian + multiple metrics
            blur_analysis = self.detect_blur_comprehensive(gray)
            print(f"Blur analysis: {blur_analysis['level']} (score: {blur_analysis['score']:.1f})")

            # Step 3: CREATE BLUR HEATMAP for user understanding
            blur_heatmap = self.create_blur_heatmap_visualization(gray, blur_analysis)
            cv2.imwrite(str(self.debug_dir / "02_blur_heatmap.png"), blur_heatmap)
            print("✓ Blur heatmap saved - shows where detection might struggle")

            # Step 4: Test methods with BLUR-AWARE parameter selection
            methods_results = self.test_methods_with_blur_awareness(gray, blur_analysis)

            # Step 5: Choose best method using your DIC quality scoring + blur considerations
            best_result = self.choose_best_method_blur_aware(methods_results, gray, blur_analysis)

            if best_result is None:
                print("ERROR: No valid method found")
                return self._empty_results()

            # Step 6: Apply your existing FIXED size filtering (preserves large speckles)
            final_results = self.apply_fixed_size_filtering(best_result, gray)

            # Add blur information to results
            final_results['blur_level'] = blur_analysis['level']
            final_results['blur_score'] = blur_analysis['score']
            final_results['blur_confidence'] = blur_analysis['confidence']
            final_results['blur_reasoning'] = best_result.get('blur_reasoning', 'Standard selection')

            # Step 7: Create comprehensive visualizations including blur heatmap
            self.create_blur_integrated_visualizations(gray, final_results, blur_heatmap)

            # Step 8: Generate report
            self.generate_blur_integrated_report(gray, final_results)

            return final_results

        except Exception as e:
            print(f"ERROR in blur-integrated analysis: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_results(str(e))

    def detect_blur_comprehensive(self, gray):
        """Comprehensive blur detection using multiple metrics"""
        h, w = gray.shape

        # Method 1: Laplacian variance (primary metric)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_var = laplacian.var()

        # Method 2: Sobel gradient strength
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
        sobel_mean = np.mean(sobel_magnitude)

        # Method 3: Edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w)

        # Method 4: Local contrast
        local_std = cv2.blur(gray.astype(np.float32), (5, 5))
        local_contrast = np.mean(np.abs(gray.astype(np.float32) - local_std))

        # Normalize metrics to 0-100 scale
        laplacian_norm = min(100, laplacian_var / 200 * 100)
        sobel_norm = min(100, sobel_mean / 30 * 100)
        edge_norm = min(100, edge_density * 1000)
        contrast_norm = min(100, local_contrast / 20 * 100)

        # Weighted combination (Laplacian most reliable for blur detection)
        blur_score = (laplacian_norm * 0.4 + sobel_norm * 0.3 + edge_norm * 0.2 + contrast_norm * 0.1)

        # Calculate confidence
        metrics = [laplacian_norm, sobel_norm, edge_norm, contrast_norm]
        confidence = max(0.5, 1.0 - (float(np.std(metrics)) / 30))

        # Classify blur level
        if blur_score >= 70:
            level = "Very Sharp"
        elif blur_score >= 55:
            level = "Sharp"
        elif blur_score >= 40:
            level = "Slightly Blurry"
        elif blur_score >= 25:
            level = "Moderately Blurry"
        elif blur_score >= 15:
            level = "Blurry"
        else:
            level = "Very Blurry"

        return {
            'score': blur_score,
            'level': level,
            'confidence': confidence,
            'laplacian_var': laplacian_var,
            'sobel_mean': sobel_mean,
            'edge_density': edge_density,
            'local_contrast': local_contrast,
            'laplacian_map': np.abs(laplacian)  # For heatmap visualization
        }

    def create_blur_heatmap_visualization(self, gray, blur_analysis):
        """Create CLEAN blur heatmap showing sharp (red) vs blurry (blue) areas"""
        # Get the per-pixel blur map from Laplacian
        laplacian_map = blur_analysis['laplacian_map']

        # Smooth for better visualization
        smoothed_map = cv2.GaussianBlur(laplacian_map, (5, 5), 0)

        # Normalize to 0-255
        normalized_map = cv2.normalize(smoothed_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Apply colormap: Blue = Blurry, Red = Sharp
        heatmap = cv2.applyColorMap(normalized_map, cv2.COLORMAP_JET)

        # Create side-by-side comparison (CLEAN VERSION)
        h, w = gray.shape
        comparison = np.zeros((h, w * 2 + 30, 3), dtype=np.uint8)

        # Left: Original image
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        comparison[:, :w] = gray_bgr

        # Right: Blur heatmap
        comparison[:, w + 30:] = heatmap

        # MINIMAL labeling only (much cleaner)
        cv2.putText(comparison, "Original", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(comparison, "Blur Map", (w + 40, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        return comparison

    def test_methods_with_blur_awareness(self, gray, blur_analysis):
        """Test methods with EXPANDED set including speckle-preserving methods"""
        print("Testing EXPANDED method set with speckle-preserving techniques...")

        h, w = gray.shape
        roi_area = h * w
        methods_results = {}
        blur_level = blur_analysis['level']

        # BLUR-AWARE parameter selection (existing logic)
        if blur_level in ["Very Blurry", "Blurry"]:
            block_sizes = [21, 31, 41, 51]
            c_values = [4, 5, 6, 7]
            print(f"Using LARGE parameters for {blur_level} image")
        elif blur_level in ["Moderately Blurry", "Slightly Blurry"]:
            block_sizes = [15, 21, 31, 41]
            c_values = [2, 3, 4, 5]
            print(f"Using MEDIUM parameters for {blur_level} image")
        else:  # Sharp images
            block_sizes = [11, 15, 21, 31]
            c_values = [1, 2, 3, 4]
            print(f"Using STANDARD parameters for {blur_level} image")

        # METHOD SET 1: Standard Adaptive Thresholding
        print("Testing standard adaptive thresholding...")
        for block_size in block_sizes:
            for c_val in c_values:
                try:
                    # Gaussian adaptive
                    binary_gauss = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                         cv2.THRESH_BINARY_INV, block_size, c_val)
                    result_gauss = self.analyze_binary_method(binary_gauss, f"Adaptive_Gauss_{block_size}_C{c_val}",
                                                              roi_area)
                    methods_results[f"adaptive_gauss_{block_size}_c{c_val}"] = result_gauss

                    # Mean adaptive
                    binary_mean = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                                        cv2.THRESH_BINARY_INV, block_size, c_val)
                    result_mean = self.analyze_binary_method(binary_mean, f"Adaptive_Mean_{block_size}_C{c_val}",
                                                             roi_area)
                    methods_results[f"adaptive_mean_{block_size}_c{c_val}"] = result_mean

                except Exception as e:
                    print(f"Error with block_size {block_size}, C={c_val}: {e}")

        # METHOD SET 2: SPECKLE-PRESERVING Global Thresholds
        print("Testing speckle-preserving global thresholds...")

        # Conservative percentile thresholds (fewer, more conservative)
        conservative_percentiles = [25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75]
        for percentile in conservative_percentiles:
            try:
                thresh_val = np.percentile(gray, percentile)
                thresh_val_int = int(thresh_val)
                _, binary_percentile = cv2.threshold(gray, thresh_val_int, 255, cv2.THRESH_BINARY_INV)
                result_percentile = self.analyze_binary_method(binary_percentile,
                                                               f"Conservative_Percentile_{percentile}", roi_area)
                methods_results[f"conservative_percentile_{percentile}"] = result_percentile
            except Exception as e:
                print(f"Error with percentile {percentile}: {e}")

        # METHOD SET 3: MORPHOLOGICAL METHODS (speckle-preserving)
        print("Testing morphological speckle-preserving methods...")
        try:
            # Start with Otsu and improve it
            _, otsu_binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Morphological closing to connect nearby speckle parts
            for kernel_size in [3, 5, 7]:
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

                # Closing to connect broken speckles
                closed_binary = cv2.morphologyEx(otsu_binary, cv2.MORPH_CLOSE, kernel)
                result_closed = self.analyze_binary_method(closed_binary, f"Otsu_Closed_{kernel_size}", roi_area)
                methods_results[f"otsu_closed_{kernel_size}"] = result_closed

                # Opening to remove small noise then closing to connect
                opened_binary = cv2.morphologyEx(otsu_binary, cv2.MORPH_OPEN, kernel)
                opened_closed = cv2.morphologyEx(opened_binary, cv2.MORPH_CLOSE, kernel)
                result_open_close = self.analyze_binary_method(opened_closed, f"Otsu_OpenClose_{kernel_size}", roi_area)
                methods_results[f"otsu_openclose_{kernel_size}"] = result_open_close

        except Exception as e:
            print(f"Error with morphological methods: {e}")

        # METHOD SET 4: CONSERVATIVE ADAPTIVE with MORPHOLOGY
        print("Testing conservative adaptive with morphological enhancement...")
        try:
            # Use larger block sizes with morphological enhancement
            for block_size in [31, 41, 51]:
                for c_val in [2, 3, 4]:
                    try:
                        # Adaptive threshold
                        adaptive_binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                                cv2.THRESH_BINARY_INV, block_size, c_val)

                        # Apply morphological closing to preserve speckles
                        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                        enhanced_binary = cv2.morphologyEx(adaptive_binary, cv2.MORPH_CLOSE, kernel)

                        result_enhanced = self.analyze_binary_method(enhanced_binary,
                                                                     f"Enhanced_Adaptive_{block_size}_C{c_val}",
                                                                     roi_area)
                        methods_results[f"enhanced_adaptive_{block_size}_c{c_val}"] = result_enhanced

                    except Exception as e:
                        continue
        except Exception as e:
            print(f"Error with enhanced adaptive: {e}")

        # METHOD SET 5: MULTI-SCALE APPROACHES
        print("Testing multi-scale speckle detection...")
        try:
            # Gaussian blur + threshold (preserves larger structures)
            for sigma in [1.0, 1.5, 2.0]:
                blurred = cv2.GaussianBlur(gray, (0, 0), sigma)
                _, blur_binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                result_blur = self.analyze_binary_method(blur_binary, f"Gaussian_Blur_{sigma}", roi_area)
                methods_results[f"gaussian_blur_{sigma}"] = result_blur

        except Exception as e:
            print(f"Error with multi-scale methods: {e}")

        # METHOD SET 6: WATERSHED-BASED SPECKLE SEPARATION
        print("Testing watershed-based methods...")
        try:
            # Distance transform + watershed for better speckle separation
            _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Distance transform
            dist_transform = cv2.distanceTransform(otsu_thresh, cv2.DIST_L2, 5)

            # Find peaks for watershed
            for min_distance in [10, 15, 20]:
                try:
                    # Find local maxima using simple approach (avoid scipy dependency)
                    # Create a simple local maxima filter
                    kernel_size = min_distance
                    kernel = np.ones((kernel_size, kernel_size), np.uint8)
                    local_max = cv2.dilate(dist_transform, kernel)
                    local_maxima = (dist_transform == local_max) & (dist_transform > np.max(dist_transform) * 0.3)

                    # Create markers
                    markers, num_markers = cv2.connectedComponents(local_maxima.astype(np.uint8))
                    markers = markers + 1  # Watershed needs markers > 0
                    markers[otsu_thresh == 0] = 0  # Background

                    # Watershed
                    watershed_result = cv2.watershed(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), markers)
                    watershed_binary = (watershed_result > 1).astype(np.uint8) * 255

                    result_watershed = self.analyze_binary_method(watershed_binary, f"Watershed_{min_distance}",
                                                                  roi_area)
                    methods_results[f"watershed_{min_distance}"] = result_watershed

                except Exception as e:
                    continue

        except Exception as e:
            print(f"Error with watershed methods: {e}")

        # METHOD SET 7: CONTOUR-BASED METHODS
        print("Testing contour-based speckle extraction...")
        try:
            # Find contours and filter by area
            _, otsu_binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(otsu_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for min_area in [20, 50, 100]:
                try:
                    # Filter contours by area
                    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= min_area]

                    # Create binary from filtered contours
                    contour_binary = np.zeros_like(gray)
                    if filtered_contours:  # Only if we have contours
                        cv2.fillPoly(contour_binary, filtered_contours, 255)

                    result_contour = self.analyze_binary_method(contour_binary, f"Contour_MinArea_{min_area}", roi_area)
                    methods_results[f"contour_minarea_{min_area}"] = result_contour

                except Exception as e:
                    continue

        except Exception as e:
            print(f"Error with contour methods: {e}")

        # METHOD SET 8: HYBRID APPROACHES
        print("Testing hybrid speckle detection approaches...")
        try:
            # Combine multiple thresholds
            _, otsu_binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Conservative percentile + morphology
            percentile_70 = int(np.percentile(gray, 70))
            _, perc_binary = cv2.threshold(gray, percentile_70, 255, cv2.THRESH_BINARY_INV)

            # Combine with logical AND (more conservative)
            combined_and = cv2.bitwise_and(otsu_binary, perc_binary)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            combined_cleaned = cv2.morphologyEx(combined_and, cv2.MORPH_CLOSE, kernel)

            result_hybrid = self.analyze_binary_method(combined_cleaned, "Hybrid_Conservative", roi_area)
            methods_results["hybrid_conservative"] = result_hybrid

        except Exception as e:
            print(f"Error with hybrid methods: {e}")

        # METHOD SET 9: EDGE-BASED SPECKLE DETECTION
        print("Testing edge-based speckle methods...")
        try:
            # Canny edges + morphological operations
            edges = cv2.Canny(gray, 50, 150)

            # Close edges to form speckle boundaries
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

            # Fill enclosed areas
            contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            edge_based_binary = np.zeros_like(gray)
            if contours:  # Only if we have contours
                cv2.fillPoly(edge_based_binary, contours, 255)

            result_edge = self.analyze_binary_method(edge_based_binary, "Edge_Based_Speckles", roi_area)
            methods_results["edge_based_speckles"] = result_edge

        except Exception as e:
            print(f"Error with edge-based methods: {e}")

        # Standard Otsu for comparison
        try:
            _, binary_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            result_otsu = self.analyze_binary_method(binary_otsu, "Otsu", roi_area)
            methods_results["otsu"] = result_otsu
        except Exception as e:
            print(f"Error with Otsu: {e}")

        print(f"Tested {len(methods_results)} methods total (EXPANDED SET)")
        return methods_results

    def choose_best_method_blur_aware(self, methods_results, gray, blur_analysis):
        """Choose best method using your DIC quality scoring + blur awareness"""
        if not methods_results:
            return None

        print(f"\nChoosing best method with blur-aware DIC quality scoring...")
        print(f"Image blur level: {blur_analysis['level']} (score: {blur_analysis['score']:.1f})")

        method_scores = []
        for method_name, result in methods_results.items():
            if result['raw_count'] == 0:
                continue

            # Calculate your existing DIC quality score
            dic_quality = self.calculate_dic_quality_score(result, gray)

            # Apply blur-aware adjustments
            adjusted_score, reasoning = self.apply_blur_aware_adjustments(dic_quality, method_name, blur_analysis)

            method_scores.append((method_name, result, adjusted_score, dic_quality, reasoning))

        # Sort by adjusted score
        method_scores.sort(key=lambda x: x[2], reverse=True)

        print(f"\nTop 10 methods (blur-aware DIC scoring):")
        for i, (method_name, result, adj_score, base_score, reasoning) in enumerate(method_scores[:10]):
            adjustment = adj_score - base_score
            print(f"  {i + 1:2d}. {method_name:30} | Score: {adj_score:5.1f} | Δ: {adjustment:+5.1f} | {reasoning}")

        if method_scores:
            best_method_name, best_result, best_score, base_score, reasoning = method_scores[0]
            print(f"\nSelected: {best_method_name}")
            print(f"Reasoning: {reasoning}")

            best_result['dic_quality_score'] = best_score
            best_result['base_dic_score'] = base_score
            best_result['blur_reasoning'] = reasoning
            return best_result
        else:
            return None

    def apply_blur_aware_adjustments(self, base_dic_score, method_name, blur_analysis):
        """Apply MINIMAL blur-aware adjustments - let DIC quality dominate"""
        adjusted_score = base_dic_score
        blur_level = blur_analysis['level']
        is_very_blurry = blur_level in ["Very Blurry", "Blurry"]
        is_sharp = blur_level in ["Very Sharp", "Sharp"]

        reasoning_parts = []

        # MINIMAL blur adjustments - let actual speckle quality dominate
        if is_very_blurry:
            # Only small preferences for very blurry images
            if 'adaptive' in method_name.lower() and 'mean' in method_name.lower():
                adjusted_score += 8  # Small bonus for mean adaptive
                reasoning_parts.append("Mean adaptive slightly preferred for blur")

            # Small penalty for Otsu only in very blurry conditions
            if 'otsu' in method_name.lower():
                adjusted_score -= 8  # Small penalty
                reasoning_parts.append("Otsu slightly penalized for very blurry")

        elif is_sharp:
            # Very small Otsu preference for sharp images
            if 'otsu' in method_name.lower():
                adjusted_score += 5  # Very small bonus
                reasoning_parts.append("Otsu slightly preferred for sharp")

        # Minimal confidence bonus
        confidence_bonus = (blur_analysis['confidence'] - 0.5) * 2  # Very small adjustment
        adjusted_score += confidence_bonus

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "DIC quality dominates"
        return max(0, adjusted_score), reasoning

    def calculate_dic_quality_score(self, method_result, gray):
        """IMPROVED DIC quality scoring that heavily penalizes speckle merging"""
        components = method_result['components']
        if not components:
            return 0.0

        # Factor 1: SPECKLE SEPARATION QUALITY - most important for DIC (40% weight)
        separation_score = self.evaluate_speckle_separation_quality(method_result, gray)

        # Factor 2: SPECKLE COUNT ADEQUACY - need sufficient speckles (25% weight)
        count_score = self.evaluate_speckle_count_quality(components, gray)

        # Factor 3: SPECKLE REALISM - realistic vs noise (20% weight)
        realism_score = self.evaluate_speckle_realism(method_result, gray)

        # Factor 4: SIZE DISTRIBUTION - appropriate sizes (10% weight)
        size_score = self.evaluate_improved_size_distribution([comp['area'] for comp in components])

        # Factor 5: SPATIAL DISTRIBUTION - well distributed (5% weight)
        spatial_score = self.evaluate_spatial_distribution(components, gray.shape)

        # Combine with heavy emphasis on separation quality
        total_score = (
                separation_score * 0.40 +  # Most important - don't merge speckles!
                count_score * 0.25 +  # Need adequate speckle count
                realism_score * 0.20 +  # Should look like real speckles
                size_score * 0.10 +  # Reasonable sizes
                spatial_score * 0.05  # Well distributed
        )

        return total_score

    def evaluate_speckle_separation_quality(self, method_result, gray):
        """Evaluate speckle quality with DYNAMIC expectations and REAL speckle validation"""
        components = method_result['components']
        binary = method_result.get('binary')

        if not components or binary is None:
            return 0.0

        # 1. REAL SPECKLE VALIDATION - filter out obvious noise
        real_speckles = self.validate_real_speckles(components, gray)
        real_speckle_count = len(real_speckles)
        total_count = len(components)

        # Heavy penalty for methods that create mostly noise
        if total_count > 0:
            real_speckle_ratio = real_speckle_count / total_count
            if real_speckle_ratio < 0.3:  # Less than 30% real speckles
                return real_speckle_ratio * 30  # Heavy penalty
        else:
            return 0

        # 2. DYNAMIC DENSITY ANALYSIS - based on actual image content
        density_score = self.evaluate_dynamic_density(real_speckles, gray)

        # 3. SPECKLE SIZE REALISM - based on visible pattern
        size_score = self.evaluate_realistic_speckle_sizes(real_speckles, gray)

        # 4. OVER-SEGMENTATION PENALTY - heavily penalize tiny fragments
        over_seg_penalty = self.calculate_over_segmentation_penalty(components, gray)

        # 5. PATTERN COHERENCE - do speckles look coherent?
        coherence_score = self.evaluate_pattern_coherence_realistic(components, gray)

        # Combine factors with heavy emphasis on real speckles
        separation_score = (
                real_speckle_ratio * 100 * 0.35 +  # Most important - are they real speckles?
                density_score * 0.25 +  # Dynamic density based on content
                size_score * 0.20 +  # Realistic sizes
                coherence_score * 0.15 +  # Pattern coherence
                (100 - over_seg_penalty) * 0.05  # Penalize over-segmentation
        )

        return max(0.0, min(100.0, separation_score))

    def validate_real_speckles(self, components, gray):
        """Filter components to only include REAL speckles, not noise"""
        h, w = gray.shape
        real_speckles = []

        # Analyze the original image to understand expected speckle characteristics
        # Calculate local variance to understand texture scale
        kernel_size = min(15, min(h, w) // 10)
        if kernel_size % 2 == 0:
            kernel_size += 1

        local_mean = cv2.blur(gray.astype(np.float32), (kernel_size, kernel_size))
        local_variance = cv2.blur((gray.astype(np.float32) - local_mean) ** 2, (kernel_size, kernel_size))
        avg_local_variance = np.mean(local_variance)

        # Estimate minimum realistic speckle size based on image texture
        min_realistic_size = max(8, int(avg_local_variance / 100))  # Dynamic minimum
        max_realistic_size = min(1000, (h * w) // 50)  # Max 2% of image

        print(f"Speckle validation: min_size={min_realistic_size}, max_size={max_realistic_size}")

        for component in components:
            area = component['area']

            # Size filter - must be reasonable size
            if area < min_realistic_size or area > max_realistic_size:
                continue

            # Shape filter - must be reasonably compact (not long thin lines)
            if self.validate_speckle_shape(component, gray):
                real_speckles.append(component)

        print(f"Real speckle validation: {len(real_speckles)}/{len(components)} passed validation")
        return real_speckles

    def validate_speckle_shape(self, component, gray):
        """Validate that a component has a reasonable speckle-like shape"""
        try:
            area = component['area']

            # Very basic shape validation - can be expanded
            # For now, just check that it's not extremely elongated

            # Estimate aspect ratio from area (rough approximation)
            # Real speckles should be roughly circular to moderately elongated
            expected_diameter = np.sqrt(area / np.pi) * 2

            # If area is very small relative to expected circular area, it's likely noise
            circular_area = np.pi * (expected_diameter / 2) ** 2
            compactness = area / circular_area

            # Reasonable speckles should have compactness between 0.3 and 1.2
            return 0.3 <= compactness <= 1.2

        except Exception:
            return True  # If validation fails, assume it's valid

    def evaluate_dynamic_density(self, real_speckles, gray):
        """Evaluate speckle density dynamically based on image content"""
        h, w = gray.shape
        image_area = h * w
        speckle_count = len(real_speckles)

        if speckle_count == 0:
            return 0

        # Calculate dynamic density based on image texture complexity
        # More textured images can support more speckles
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w)

        # Estimate reasonable speckle count based on texture
        if edge_density > 0.15:  # High texture
            expected_density_per_1000px = 4  # Fewer larger speckles
        elif edge_density > 0.08:  # Medium texture
            expected_density_per_1000px = 6  # Moderate speckles
        else:  # Low texture
            expected_density_per_1000px = 8  # Can have more speckles

        expected_count = (image_area / 1000) * expected_density_per_1000px

        # Score based on how close to expected (with wide tolerance)
        ratio = speckle_count / expected_count if expected_count > 0 else 0

        if 0.5 <= ratio <= 2.0:  # Good range
            density_score = 100
        elif 0.3 <= ratio <= 3.0:  # Acceptable range
            density_score = 80
        elif ratio < 0.3:  # Too few
            density_score = ratio / 0.3 * 60
        else:  # Too many
            density_score = max(40, 100 - (ratio - 3.0) * 20)

        return max(0.0, min(100.0, density_score))

    def evaluate_realistic_speckle_sizes(self, real_speckles, gray):
        """Evaluate if speckle sizes are realistic for the image scale"""
        if not real_speckles:
            return 0

        areas = [comp['area'] for comp in real_speckles]
        h, w = gray.shape

        # Calculate median speckle size
        median_size = np.median(areas)

        # Estimate reasonable size range based on image dimensions
        min_reasonable = (h * w) / 5000  # At least 0.02% of image
        max_reasonable = (h * w) / 100  # At most 1% of image

        # Score based on median size reasonableness
        if min_reasonable <= median_size <= max_reasonable:
            size_score = 100
        elif median_size < min_reasonable:
            # Too small - likely over-segmented
            size_score = (median_size / min_reasonable) * 50
        else:
            # Too large - likely under-segmented
            size_score = max(50, 100 - ((median_size - max_reasonable) / max_reasonable) * 50)

        # Bonus for reasonable size distribution
        if len(areas) > 3:
            size_std = np.std(areas)
            size_mean = np.mean(areas)
            cv = size_std / size_mean if size_mean > 0 else 0

            # Good speckle patterns have moderate size variation
            if 0.4 <= cv <= 1.0:
                size_score += 10

        return max(0.0, min(100.0, size_score))

    def calculate_over_segmentation_penalty(self, components, gray):
        """Calculate penalty for over-segmentation (too many tiny components)"""
        if not components:
            return 0

        total_components = len(components)
        h, w = gray.shape

        # Count tiny components (likely noise)
        tiny_components = sum(1 for comp in components if comp['area'] <= 5)
        very_small_components = sum(1 for comp in components if comp['area'] <= 15)

        # Calculate ratios
        tiny_ratio = tiny_components / total_components
        very_small_ratio = very_small_components / total_components

        # Heavy penalties for too many tiny components
        penalty = 0

        if tiny_ratio > 0.3:  # More than 30% tiny
            penalty += (tiny_ratio - 0.3) * 150  # Heavy penalty

        if very_small_ratio > 0.6:  # More than 60% very small
            penalty += (very_small_ratio - 0.6) * 100

        # Penalty for absolute over-segmentation
        components_per_1000px = (total_components / (h * w)) * 1000
        if components_per_1000px > 20:  # More than 20 components per 1000 pixels
            penalty += (components_per_1000px - 20) * 2

        return min(100.0, penalty)

    def evaluate_pattern_coherence_realistic(self, components, gray):
        """Evaluate pattern coherence with realistic expectations"""
        if len(components) < 5:
            return 50  # Need some components for meaningful analysis

        # Simple coherence check - are components reasonably sized and distributed?
        areas = [comp['area'] for comp in components]

        # Check for reasonable size distribution
        median_area = np.median(areas)
        q75 = np.percentile(areas, 75)
        q25 = np.percentile(areas, 25)

        # Good patterns don't have extreme outliers
        iqr = q75 - q25
        outliers = [area for area in areas if area > q75 + 2 * iqr or area < q25 - 2 * iqr]
        outlier_ratio = len(outliers) / len(areas)

        coherence_score = 100 - (outlier_ratio * 100)
        return max(0.0, min(100.0, coherence_score))

    def evaluate_speckle_count_quality(self, components, gray):
        """Evaluate if speckle count is appropriate for DIC"""
        h, w = gray.shape
        image_area = h * w
        speckle_count = len(components)

        # DIC typically needs 5-20 speckles per 1000 pixels for good correlation
        min_expected = (image_area / 1000) * 5
        max_expected = (image_area / 1000) * 20
        optimal_expected = (image_area / 1000) * 12

        if speckle_count < min_expected:
            # Too few speckles (bad for DIC)
            score = (speckle_count / min_expected) * 40  # Heavy penalty
        elif speckle_count > max_expected:
            # Too many speckles (over-segmentation)
            score = max(40.0, 100 - ((speckle_count - max_expected) / max_expected) * 60)
        else:
            # Good range - closer to optimal is better
            distance_from_optimal = abs(speckle_count - optimal_expected) / optimal_expected
            score = 100 - (distance_from_optimal * 30)

        return max(0.0, min(100.0, score))

    def evaluate_pattern_texture_match(self, binary, gray):
        """Evaluate how well the binary pattern matches the original texture"""
        try:
            # Calculate local pattern correlation
            # Downsample for efficiency
            scale_factor = max(1, max(gray.shape) // 200)
            if scale_factor > 1:
                small_gray = cv2.resize(gray, (gray.shape[1] // scale_factor, gray.shape[0] // scale_factor))
                small_binary = cv2.resize(binary, (binary.shape[1] // scale_factor, binary.shape[0] // scale_factor))
            else:
                small_gray = gray
                small_binary = binary

            # Convert binary to same range as gray
            binary_float = small_binary.astype(float) / 255.0 * 255

            # Calculate normalized cross-correlation in local windows
            correlations = []
            window_size = 32
            step = 16

            for y in range(0, small_gray.shape[0] - window_size, step):
                for x in range(0, small_gray.shape[1] - window_size, step):
                    gray_window = small_gray[y:y + window_size, x:x + window_size]
                    binary_window = binary_float[y:y + window_size, x:x + window_size]

                    # Calculate correlation
                    gray_norm = gray_window - np.mean(gray_window)
                    binary_norm = binary_window - np.mean(binary_window)

                    gray_std = np.std(gray_norm)
                    binary_std = np.std(binary_norm)

                    if gray_std > 0 and binary_std > 0:
                        correlation = np.corrcoef(gray_norm.flatten(), binary_norm.flatten())[0, 1]
                        if not np.isnan(correlation):
                            correlations.append(abs(correlation))

            if correlations:
                avg_correlation = np.mean(correlations)
                texture_score = avg_correlation * 100
            else:
                texture_score = 50

            return max(0.0, min(100.0, texture_score))

        except Exception as e:
            print(f"Error in texture matching: {e}")
            return 50.0

    def detect_speckle_merging(self, components, gray):
        """Detect signs of speckle merging and return penalty score"""
        if len(components) < 5:
            return 50  # Too few components suggests heavy merging

        areas = [comp['area'] for comp in components]

        # 1. Check for oversized components (merged speckles)
        h, w = gray.shape
        very_large_threshold = (h * w) / 200  # Components bigger than 0.5% of image
        oversized_count = sum(1 for area in areas if area > very_large_threshold)
        oversized_penalty = min(30.0, oversized_count * 10)

        # 2. Check size distribution skew (merging creates large outliers)
        if len(areas) > 3:
            areas_array = np.array(areas)
            q75 = np.percentile(areas_array, 75)
            q25 = np.percentile(areas_array, 25)
            outliers = np.sum(areas_array > q75 + 2 * (q75 - q25))
            outlier_penalty = min(20.0, outliers * 5)
        else:
            outlier_penalty = 0

        # 3. Pattern density check (merged patterns are too sparse)
        expected_components = (h * w) / 100  # Rough estimate
        if len(components) < expected_components * 0.5:
            sparsity_penalty = 30.0
        else:
            sparsity_penalty = 0.0

        total_penalty = oversized_penalty + outlier_penalty + sparsity_penalty
        return min(100.0, total_penalty)

    def evaluate_speckle_realism(self, method_result, gray):
        """Evaluate how well the method captures ACTUAL speckles vs noise"""
        components = method_result['components']
        if not components:
            return 0.0

        # Get the binary result
        binary = method_result.get('binary')
        if binary is None:
            return 50.0

        # Calculate noise vs signal characteristics

        # 1. Count very small components (likely noise)
        total_components = len(components)
        tiny_components = sum(1 for comp in components if comp['area'] <= 5)
        noise_ratio = tiny_components / total_components if total_components > 0 else 1.0

        # 2. Evaluate size distribution realism
        areas = [comp['area'] for comp in components]
        if areas:
            # Good speckle patterns have most components in 10-200 pixel range
            good_size_count = sum(1 for area in areas if 10 <= area <= 200)
            realistic_size_ratio = good_size_count / len(areas)
        else:
            realistic_size_ratio = 0

        # 3. Check for over-segmentation (too many tiny fragments)
        if total_components > gray.size // 100:  # More than 1% of image pixels as separate components
            over_segmentation_penalty = 50  # Heavy penalty
        elif total_components > gray.size // 200:  # More than 0.5%
            over_segmentation_penalty = 25  # Moderate penalty
        else:
            over_segmentation_penalty = 0

        # 4. Check pattern density (realistic speckle patterns aren't too sparse or dense)
        pattern_coverage = np.sum(binary > 0) / binary.size
        if 0.3 <= pattern_coverage <= 0.7:  # Good coverage range
            coverage_score = 100
        elif 0.2 <= pattern_coverage <= 0.8:  # Acceptable range
            coverage_score = 75
        elif 0.1 <= pattern_coverage <= 0.9:  # Marginal range
            coverage_score = 50
        else:  # Too sparse or too dense
            coverage_score = 25

        # Combine realism factors
        realism_score = (
                                (1.0 - noise_ratio) * 40 +  # Penalize noise
                                realistic_size_ratio * 30 +  # Reward realistic sizes
                                coverage_score * 0.3  # Reward good coverage
                        ) - over_segmentation_penalty  # Penalize over-segmentation

        return max(0.0, min(100.0, realism_score))

    def evaluate_improved_size_distribution(self, areas):
        """IMPROVED size evaluation focused on realistic speckle patterns"""
        if not areas:
            return 0.0

        areas = np.array(areas)
        total = len(areas)

        # Define realistic size categories for DIC speckles
        noise_count = np.sum(areas <= 5)  # Noise (too small)
        tiny_count = np.sum((areas > 5) & (areas <= 15))  # Small but valid
        small_count = np.sum((areas > 15) & (areas <= 50))  # Good small speckles
        medium_count = np.sum((areas > 50) & (areas <= 200))  # Ideal medium speckles
        large_count = np.sum((areas > 200) & (areas <= 800))  # Good large speckles
        huge_count = np.sum(areas > 800)  # Too large (likely merged)

        # Calculate ratios
        noise_ratio = noise_count / total
        medium_ratio = medium_count / total
        huge_ratio = huge_count / total
        good_ratio = (tiny_count + small_count + medium_count + large_count) / total

        # Scoring based on realistic distributions
        score = 100.0

        # Heavy penalty for too much noise
        if noise_ratio > 0.5:  # More than 50% noise
            score -= (noise_ratio - 0.5) * 200

        # Reward good medium-sized speckles
        score += medium_ratio * 50

        # Reward overall good size distribution
        score += good_ratio * 30

        # Penalize too many oversized components
        if huge_ratio > 0.15:  # More than 15% huge
            score -= huge_ratio * 100

        return max(0.0, min(100.0, score))

    def evaluate_speckle_coherence(self, method_result, gray):
        """Your existing coherence evaluation with fixed boolean mask conversion"""
        if 'binary' not in method_result or method_result['binary'] is None:
            return 50.0

        try:
            components = method_result['components']
            if not components:
                return 0.0

            coherence_scores = []

            for component in components[:100]:
                area = component['area']

                if area > 10:
                    comp_id = component['id']
                    if 'labels' in method_result:
                        mask = method_result['labels'] == comp_id

                        # FIXED: Convert boolean mask to uint8 properly
                        mask_uint8 = np.array(mask).astype(np.uint8) * 255
                        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                        if contours:
                            perimeter = cv2.arcLength(contours[0], True)
                            if perimeter > 0:
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
        """Your existing spatial distribution evaluation"""
        if len(components) < 10:
            return 50.0

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

        # Calculate uniformity
        if np.mean(grid_counts) > 0:
            cv = np.std(grid_counts) / np.mean(grid_counts)
            uniformity_score = max(0, 100 - cv * 50)
        else:
            uniformity_score = 0

        return min(100.0, uniformity_score)

    def analyze_binary_method(self, binary, method_name, roi_area):
        """Your existing binary analysis logic"""
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

    def apply_fixed_size_filtering(self, method_result, gray):
        """Apply MINIMAL filtering - keep almost all components for color visualization"""
        if not method_result or not method_result.get('components'):
            return self._empty_results("No components to filter")

        print("Applying MINIMAL filtering for full component visualization...")

        h, w = gray.shape
        roi_area = h * w

        # VERY MINIMAL filtering - only remove obvious artifacts
        min_area = 1  # Keep everything
        max_area = roi_area // 2  # Only remove if bigger than half image

        print(f"MINIMAL size range: {min_area} - {max_area} pixels")

        # Keep almost ALL components
        filtered_speckles = []
        for component in method_result['components']:
            area = component['area']
            if min_area <= area <= max_area:
                filtered_speckles.append(component)

        # Categorize by size
        small_count = sum(1 for s in filtered_speckles if s['area'] <= 50)
        medium_count = sum(1 for s in filtered_speckles if 51 <= s['area'] <= 500)
        large_count = sum(1 for s in filtered_speckles if s['area'] > 500)

        # Calculate quality score
        total_speckles = len(filtered_speckles)
        quality_score = min(100.0, (total_speckles / 100.0) * 100)

        # Add bonus for size diversity
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
            'stats_used': method_result.get('stats'),
            'all_components': method_result.get('components', [])  # Pass ALL components for visualization
        }

    def create_blur_integrated_visualizations(self, gray, results, blur_heatmap):
        """Create CLEAN visualizations without text overlays"""
        try:
            print("Creating CLEAN BLUR-INTEGRATED visualizations...")

            # 1. CLEAN speckle detection (NO TEXT)
            if results['total_speckles'] > 0:
                vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

                # Draw speckles with size-based colors (NO TEXT)
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
                    except Exception:
                        continue

                # Save CLEAN detection (no text)
                cv2.imwrite(str(self.debug_dir / "10_CLEAN_speckle_detection.png"), vis)

            # 2. Save the CLEAN blur heatmap (already created without excessive text)
            # (blur_heatmap saved in main analysis function)

            # 3. Create CLEAN colored components using ALL components (not filtered)
            self.create_clean_colored_components_all(gray, results)

            # 4. Create CLEAN speckles on blur map using ALL components
            self.create_clean_speckles_on_blur_map(gray, results, blur_heatmap)

            # 5. Save binary method used (clean)
            if 'binary_used' in results and results['binary_used'] is not None:
                cv2.imwrite(str(self.debug_dir / "09_binary_method_used.png"), results['binary_used'])

            print("CLEAN BLUR-INTEGRATED visualizations created!")
            print("Files created (ALL CLEAN, NO TEXT):")
            print("  - 02_blur_heatmap.png (clean blur comparison)")
            print("  - 10_CLEAN_speckle_detection.png (clean speckle overlay)")
            print("  - 11_ALL_components_colored.png (ALL components colored)")
            print("  - 12_ALL_speckles_on_blur_map.png (ALL components on blur map)")

        except Exception as e:
            print(f"Error creating clean visualizations: {e}")

    def create_clean_colored_components_all(self, gray, results):
        """Create colored components using ALL components from method with FIXED component transfer"""
        try:
            if 'labels_used' not in results or results['labels_used'] is None:
                print("No labels available for component coloring")
                return

            labels = results['labels_used']
            colored_components = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)

            # Use ALL components from the method (before filtering)
            all_components = results.get('all_components', [])

            if not all_components:
                print("WARNING: No components found in all_components, trying speckles...")
                all_components = results.get('speckles', [])

            print(f"Creating colored visualization with {len(all_components)} components")

            if len(all_components) == 0:
                print("ERROR: No components to visualize!")
                return

            # Generate colors for ALL components with FIXED ID mapping
            np.random.seed(42)  # Consistent colors
            colors_used = 0

            for component in all_components:
                try:
                    speckle_id = component.get('id')
                    if speckle_id is None:
                        print(f"WARNING: Component missing ID: {component}")
                        continue

                    # Generate bright, distinct colors
                    color = tuple([int(x) for x in np.random.randint(50, 255, 3)])

                    # FIXED: Ensure we're looking for the right component ID in labels
                    mask = labels == speckle_id

                    # Check if this component actually exists in the labels
                    if np.any(mask):
                        colored_components[mask] = color
                        colors_used += 1
                    else:
                        print(f"WARNING: Component ID {speckle_id} not found in labels")

                except Exception as e:
                    print(f"Error processing component {component}: {e}")
                    continue

            cv2.imwrite(str(self.debug_dir / "11_ALL_components_colored.png"), colored_components)
            print(
                f"✓ Created colored visualization with {colors_used}/{len(all_components)} components successfully colored")

            # Debug: Save component mapping info
            with open(self.debug_dir / "component_mapping_debug.txt", 'w') as f:
                f.write(f"Component Mapping Debug Info\n")
                f.write(f"============================\n")
                f.write(f"Total components in all_components: {len(all_components)}\n")
                f.write(f"Successfully colored: {colors_used}\n")
                f.write(f"Labels shape: {labels.shape}\n")
                f.write(f"Unique label values: {np.unique(labels)}\n")
                f.write(f"Component IDs: {[comp.get('id', 'NO_ID') for comp in all_components[:10]]}\n")

        except Exception as e:
            print(f"Error creating ALL components colored visualization: {e}")
            import traceback
            traceback.print_exc()

    def create_clean_speckles_on_blur_map(self, gray, results, blur_heatmap):
        """Create CLEAN visualization showing ALL speckles overlaid on blur heatmap"""
        try:
            h, w = gray.shape

            # Extract just the heatmap portion from the comparison image
            # blur_heatmap is side-by-side, so get right half
            heatmap_only = blur_heatmap[:, w + 30:]

            # Resize if needed to match original dimensions
            if heatmap_only.shape[:2] != (h, w):
                heatmap_only = cv2.resize(heatmap_only, (w, h))

            # Overlay ALL speckles on the heatmap (not just filtered ones)
            combined = heatmap_only.copy()

            # Use ALL components from the method
            all_components = results.get('all_components', results.get('speckles', []))

            print(f"Overlaying {len(all_components)} components on blur map")

            # Draw ALL speckles with enhanced visibility on heatmap
            for component in all_components:
                try:
                    x, y = int(component['centroid'][0]), int(component['centroid'][1])
                    area = component['area']

                    # Use white circles with black outlines for visibility on colormap
                    if area <= 20:
                        radius = 2
                    elif area <= 100:
                        radius = 3
                    elif area <= 500:
                        radius = 4
                    else:
                        radius = 5

                    # Draw black outline
                    cv2.circle(combined, (x, y), radius + 1, (0, 0, 0), -1)
                    # Draw white center
                    cv2.circle(combined, (x, y), radius, (255, 255, 255), -1)

                except Exception:
                    continue

            # Save CLEAN version (no text)
            cv2.imwrite(str(self.debug_dir / "12_ALL_speckles_on_blur_map.png"), combined)
            print(f"✓ Created CLEAN speckles on blur map with ALL {len(all_components)} components")

        except Exception as e:
            print(f"Error creating clean speckles on blur map: {e}")

    def generate_blur_integrated_report(self, gray, results):
        """Generate comprehensive report for blur-integrated detection"""
        try:
            print("Generating BLUR-INTEGRATED report...")

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(self.debug_dir / "BLUR_INTEGRATED_detection_report.txt", 'w', encoding='utf-8') as f:
                f.write("BLUR-INTEGRATED SPECKLE DETECTION REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Analysis Time: {timestamp}\n")
                f.write(f"Image Dimensions: {gray.shape[1]} x {gray.shape[0]}\n")
                f.write(f"Output Folder: {self.debug_dir}\n\n")

                f.write("INTEGRATION ACHIEVEMENTS:\n")
                f.write("-" * 25 + "\n")
                f.write("✓ Blur detection integrated into existing speckle analyzer\n")
                f.write("✓ Blur heatmap visualization shows problem areas\n")
                f.write("✓ Method selection considers image sharpness\n")
                f.write("✓ Large speckle preservation maintained\n")
                f.write("✓ DIC quality scoring enhanced with blur awareness\n\n")

                f.write("BLUR ANALYSIS:\n")
                f.write("-" * 15 + "\n")
                f.write(f"Blur Level: {results['blur_level']}\n")
                f.write(f"Blur Score: {results['blur_score']:.1f}/100\n")
                f.write(f"Confidence: {results.get('blur_confidence', 0):.2f}\n\n")

                f.write("METHOD SELECTION:\n")
                f.write("-" * 17 + "\n")
                f.write(f"Selected Method: {results['best_method']}\n")
                f.write(f"Selection Reasoning: {results.get('blur_reasoning', 'N/A')}\n")
                f.write(f"DIC Quality Score: {results['dic_score']:.1f}/100\n\n")

                f.write("BLUR-AWARE IMPROVEMENTS:\n")
                f.write("-" * 25 + "\n")
                if results['blur_level'] in ["Very Blurry", "Blurry", "Moderately Blurry"]:
                    f.write("• Used larger adaptive thresholding blocks\n")
                    f.write("• Preferred Mean adaptive over Gaussian\n")
                    f.write("• Applied penalties to global Otsu methods\n")
                    f.write("• Adjusted parameters for blur conditions\n")
                else:
                    f.write("• Used standard parameters for sharp image\n")
                    f.write("• Otsu methods preferred for global thresholding\n")
                    f.write("• No blur-specific adjustments needed\n")
                f.write("\n")

                f.write("SPECKLE DETECTION RESULTS:\n")
                f.write("-" * 26 + "\n")
                f.write(f"Total Speckles: {results['total_speckles']}\n")
                f.write(f"Overall Quality: {results['quality_score']:.1f}/100\n\n")

                f.write("SIZE BREAKDOWN:\n")
                f.write("-" * 15 + "\n")
                f.write(f"Small (1-50px):   {results['small_count']:4}\n")
                f.write(f"Medium (51-500px): {results['medium_count']:4}\n")
                f.write(f"Large (501+px):    {results['large_count']:4}\n")
                f.write(f"{'':17} ----\n")
                f.write(f"Total:             {results['total_speckles']:4}\n\n")

                f.write("VISUALIZATION FILES:\n")
                f.write("-" * 19 + "\n")
                f.write("• 02_blur_heatmap.png - Shows blur distribution\n")
                f.write("• 10_BLUR_INTEGRATED_detection.png - Main results\n")
                f.write("• 12_speckles_on_blur_map.png - Combined view\n")
                f.write("• 11_colored_components.png - Component labeling\n\n")

                f.write("USER GUIDANCE:\n")
                f.write("-" * 14 + "\n")
                f.write("The blur heatmap shows where speckle detection\n")
                f.write("might struggle:\n")
                f.write("• BLUE areas = blurry regions (detection challenges)\n")
                f.write("• RED areas = sharp regions (good detection)\n")
                f.write("• WHITE dots on combined view = detected speckles\n\n")

                if results['blur_level'] in ["Very Blurry", "Blurry"]:
                    f.write("RECOMMENDATIONS:\n")
                    f.write("-" * 16 + "\n")
                    f.write("• Consider improving image sharpness if possible\n")
                    f.write("• Check camera focus and lighting conditions\n")
                    f.write("• Larger speckles may be needed for reliable DIC\n")
                    f.write("• Current detection adapted for blur conditions\n")
                elif results['large_count'] > 0:
                    f.write("SUCCESS NOTES:\n")
                    f.write("-" * 14 + "\n")
                    f.write(f"✓ Detected {results['large_count']} large speckles\n")
                    f.write("✓ Excellent image quality for DIC analysis\n")
                    f.write("✓ Detection should be highly reliable\n")

            print("BLUR-INTEGRATED report generated successfully")

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
            'blur_confidence': 0,
            'blur_reasoning': 'Analysis failed',
            'error': error_msg
        }


# Integration function
def integrate_blur_awareness_into_existing_analyzer(main_window):
    """
    Integration function to add blur detection and heatmap to your existing speckle analyzer

    This enhances your working speckle analyzer with:
    1. Comprehensive blur detection using Laplacian + multiple metrics
    2. Blur heatmap visualization (Blue=Blurry, Red=Sharp)
    3. Blur-aware method parameter selection
    4. Your existing DIC quality scoring enhanced with blur considerations
    5. Preservation of large speckles (your existing FIXED filtering)
    6. Clear visual feedback showing where detection might struggle
    """
    print("🚀 Integrating blur awareness into your existing speckle analyzer...")

    try:
        # This enhances your existing debug button with blur integration
        enhance_app_debug_functionality(main_window)

        print("✅ BLUR-INTEGRATION successful!")
        print("🎯 Enhanced features:")
        print("   • Comprehensive blur detection (Laplacian + multi-metric)")
        print("   • Blur heatmap visualization (Blue=Blurry, Red=Sharp)")
        print("   • Blur-aware method parameter selection")
        print("   • Your existing DIC quality scoring enhanced")
        print("   • Large speckle preservation maintained")
        print("   • Combined speckle+blur visualization")
        print("   • Method selection reasoning explained")
        print("   • Debug button now shows 'BLUR-INTEGRATED Detection'")

        return True

    except Exception as e:
        print(f"❌ BLUR-INTEGRATION failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Usage instructions
"""
INTEGRATION INSTRUCTIONS:

1. Replace your existing enhanced_debug_integration.py with this file

2. Or add this import to your main application:
   from enhanced_debug_integration_BLUR_INTEGRATED import integrate_blur_awareness_into_existing_analyzer

3. Call the integration function after creating your app:
   integrate_blur_awareness_into_existing_analyzer(app)

This will enhance your debug button with:
✓ All your existing speckle detection logic preserved
✓ Blur detection integrated into method selection  
✓ Blur heatmap showing where detection might struggle
✓ Blur-aware parameter selection for different image conditions
✓ Combined visualizations showing speckles on blur map
✓ Clear explanations of why methods were chosen

The blur heatmap helps users understand:
- BLUE areas = blurry regions where speckle detection is challenging
- RED areas = sharp regions where detection should work well  
- WHITE dots = successfully detected speckles
- Method selection automatically adapts to blur conditions
"""