# ui/file_operations.py - UPDATED: Enhanced report system for popup-based results
from tkinter import filedialog, messagebox
import numpy as np
from PIL import Image
import os
import datetime


class FileOperations:
    def __init__(self, main_window):
        """Initialize with a reference to the main window"""
        self.main_window = main_window

    def load_image(self):
        """Load an image from file with full application reset"""
        filetypes = [
            ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff"),
            ("All files", "*.*")
        ]

        filename = filedialog.askopenfilename(title="Select Image File", filetypes=filetypes)

        if filename:
            try:
                # FIXED: Only reset if the method exists (avoid first-load crash)
                if hasattr(self.main_window, '_reset_application_data'):
                    print("Resetting application state before loading new image...")
                    self.main_window._reset_application_data()
                else:
                    print("First image load - skipping reset")

                # Load and process the image
                self.load_image_from_path(filename)

            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load image: {str(e)}")

    def load_image_from_path(self, path):
        """Load and display image from file path"""
        # Load with PIL
        pil_image = Image.open(path)

        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Store original
        self.main_window.original_image = np.array(pil_image)
        self.main_window.current_image = self.main_window.original_image.copy()

        # FIXED: Explicitly clear ROI coordinates and update display
        self.main_window.roi_coords = None
        if hasattr(self.main_window, 'roi_handler') and self.main_window.roi_handler:
            self.main_window.roi_handler.roi_coords = []
            self.main_window.roi_handler.roi_polygon = None
            self.main_window.roi_handler.preview_line = None
            self.main_window.roi_handler.roi_selection_mode = False
            self.main_window.roi_handler.update_roi_info()  # Force update of ROI info display
            print("ROI explicitly cleared after image load")

        # Display image (this will clear the canvas and redraw)
        self.main_window.image_display.display_image(pil_image)

        # Enable ROI selection and analysis for new image
        self.main_window.roi_btn.config(state='normal')
        self.main_window.analyze_btn.config(state='normal')

        # Update state to image_loaded
        if hasattr(self.main_window, 'state_manager'):
            self.main_window.state_manager.update_state("image_loaded")

        # Update status
        filename_only = os.path.basename(path)
        h, w = self.main_window.original_image.shape[:2]
        self.main_window.status_var.set(f"Image loaded: {filename_only} ({w}×{h} pixels)")

        print(f"Image loaded successfully: {filename_only}")
        print(
            f"ROI coordinates after load: {self.main_window.roi_handler.roi_coords if hasattr(self.main_window, 'roi_handler') else 'No ROI handler'}")

    def save_report(self):
        """ENHANCED: Save comprehensive analysis report to file"""
        if not self.main_window.analysis_results:
            messagebox.showwarning("No Data", "No analysis results to save")
            return

        # Get save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Analysis Report"
        )

        if filename:
            try:
                self._write_comprehensive_report(filename)
                self.main_window.status_var.set(f"Report saved: {os.path.basename(filename)}")
                messagebox.showinfo("Report Saved", f"Comprehensive analysis report saved to:\n{filename}")

            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save report: {str(e)}")

    def _write_comprehensive_report(self, filename):
        """Write a comprehensive analysis report to file"""
        results = self.main_window.analysis_results

        with open(filename, 'w', encoding='utf-8') as f:
            # HEADER
            f.write("=" * 80 + "\n")
            f.write("           DIC IMAGE QUALITY ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Software: DIC Image Quality Inspector\n")
            f.write("=" * 80 + "\n\n")

            # EXECUTIVE SUMMARY
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 40 + "\n")
            overall_score = results['overall_score']
            score_text, _ = self.main_window.get_quality_assessment_text(overall_score / 100.0)

            f.write(f"Overall Quality Score: {overall_score:.1f}/100\n")
            f.write(f"Assessment: {score_text}\n")
            f.write(f"Analysis Method: {results.get('analysis_method', 'Full image')}\n")
            f.write(f"Color Spectrum Used: {results.get('spectrum_used', 'custom_dic').replace('_', ' ').title()}\n\n")

            # IMAGE INFORMATION
            f.write("IMAGE INFORMATION\n")
            f.write("-" * 40 + "\n")
            if hasattr(self.main_window, 'original_image') and self.main_window.original_image is not None:
                h, w = self.main_window.original_image.shape[:2]
                f.write(f"Image Dimensions: {w} × {h} pixels\n")
                f.write(f"Total Image Area: {w * h:,} pixels\n")

            # ROI information
            if (hasattr(self.main_window, 'roi_handler') and
                    self.main_window.roi_handler.roi_coords and
                    len(self.main_window.roi_handler.roi_coords) >= 3):

                roi_area = self.main_window._calculate_roi_area()
                if hasattr(self.main_window, 'original_image') and self.main_window.original_image is not None:
                    total_area = w * h
                    percentage = (roi_area / total_area * 100) if total_area > 0 else 0
                    f.write(f"ROI Area: {roi_area:.0f} pixels² ({percentage:.1f}% of image)\n")
                    f.write(f"ROI Points: {len(self.main_window.roi_handler.roi_coords)} vertices\n")
            else:
                f.write("Analysis Region: Full image\n")
            f.write("\n")

            # TECHNICAL ANALYSIS
            f.write("TECHNICAL ANALYSIS\n")
            f.write("-" * 40 + "\n")
            stats = results.get('quality_map_stats', {})
            f.write("Quality Statistics:\n")
            f.write(f"  • Maximum Quality: {stats.get('max_quality', 0):.1f}%\n")
            f.write(f"  • Average Quality: {overall_score:.1f}%\n")
            f.write(f"  • Minimum Quality: {stats.get('min_quality', 0):.1f}%\n")
            f.write(f"  • Median Quality: {stats.get('median_quality', 0):.1f}%\n")
            f.write(f"  • Standard Deviation: {results.get('quality_std', 0):.1f}%\n\n")

            # DIC PARAMETERS
            f.write("RECOMMENDED DIC PARAMETERS\n")
            f.write("-" * 40 + "\n")
            dic_params = self.main_window._calculate_dic_parameters(results)
            f.write("Correlation Setup:\n")
            f.write(f"  • Subset Size (Facet): {dic_params['facet_size']} pixels\n")
            f.write(f"  • Step Size: {dic_params['step_size']} pixels\n")
            f.write(f"  • Overlap: {dic_params['overlap']}%\n")
            f.write(f"  • Expected Accuracy: {dic_params['accuracy']}\n\n")

            # NON-TECHNICAL EXPLANATION
            f.write("WHAT THIS MEANS (NON-TECHNICAL EXPLANATION)\n")
            f.write("-" * 60 + "\n")
            explanation = self.main_window._generate_non_technical_explanation(results)
            f.write(explanation)
            f.write("\n\n")

            # MATHEMATICAL BACKGROUND
            f.write("MATHEMATICAL BACKGROUND & EQUATIONS\n")
            f.write("-" * 60 + "\n")
            math_content = self.main_window._generate_mathematical_content(results)
            f.write(math_content)
            f.write("\n\n")

            # RECOMMENDATIONS
            f.write("DETAILED RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            recommendations = self.main_window._generate_recommendations(overall_score)
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i:2d}. {rec}\n")
            f.write("\n")

            # QUALITY ASSESSMENT CRITERIA
            f.write("QUALITY ASSESSMENT CRITERIA\n")
            f.write("-" * 40 + "\n")
            current_spectrum = self.main_window.selected_spectrum.get() if hasattr(self.main_window,
                                                                                   'selected_spectrum') else 'custom_dic'

            if current_spectrum == 'custom_dic':
                f.write("Using STRICT DIC-ONLY Assessment Criteria:\n")
                f.write("  • 95-100%: Perfect for DIC (Blue)\n")
                f.write("  • 90-95%:  Excellent for DIC (Cyan)\n")
                f.write("  • 85-90%:  Very Good for DIC (Yellow)\n")
                f.write("  • 80-85%:  Good for DIC (Orange)\n")
                f.write("  • 75-80%:  Minimum for DIC (Red)\n")
                f.write("  • 0-75%:   NOT suitable for DIC (Black)\n\n")
                f.write("NOTE: This strict assessment only considers patterns with 75%+ scores\n")
                f.write("      as suitable for DIC applications.\n")
            else:
                f.write(f"Using {current_spectrum.replace('_', ' ').title()} Assessment Criteria:\n")
                f.write("  • 75-100%: Excellent for DIC\n")
                f.write("  • 60-75%:  Very Good for DIC\n")
                f.write("  • 45-60%:  Good for DIC\n")
                f.write("  • 30-45%:  Acceptable for DIC\n")
                f.write("  • 15-30%:  Challenging for DIC\n")
                f.write("  • 0-15%:   Poor for DIC\n\n")
                f.write("NOTE: More lenient thresholds suitable for general pattern evaluation.\n")
            f.write("\n")

            # TECHNICAL DETAILS
            f.write("TECHNICAL DETAILS\n")
            f.write("-" * 40 + "\n")
            f.write("Analysis Algorithm:\n")
            f.write("  The analysis uses advanced subset-based quality assessment including:\n")
            f.write("  • Gradient content analysis (Sum of Squared Gradients)\n")
            f.write("  • Speckle morphology evaluation\n")
            f.write("  • Contrast distribution assessment\n")
            f.write("  • Pattern uniqueness calculation\n")
            f.write("  • Noise resistance evaluation\n\n")

            if results.get('spectrum_used') == 'zeiss_style_dic':
                if hasattr(self.main_window, 'facet_size_var') and hasattr(self.main_window, 'point_distance_var'):
                    f.write("ZEISS-Style Analysis Parameters:\n")
                    f.write(f"  • Facet Size: {self.main_window.facet_size_var.get()} pixels\n")
                    f.write(f"  • Point Distance: {self.main_window.point_distance_var.get()} pixels\n")
                    f.write("  • High-density point analysis for professional assessment\n\n")

            # FOOTER
            f.write("=" * 80 + "\n")
            f.write("End of Report\n")
            f.write("=" * 80 + "\n")

    def export_quality_map_image(self):
        """Export the current quality map visualization as an image"""
        if not hasattr(self.main_window.image_display, 'quality_map_data') or \
                self.main_window.image_display.quality_map_data is None:
            messagebox.showwarning("No Quality Map",
                                   "No quality map available to export. Please analyze an image first.")
            return

        # Get save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
            title="Export Quality Map Visualization"
        )

        if filename:
            try:
                # Get current spectrum type
                spectrum_type = self.main_window.selected_spectrum.get()

                # Generate visualization
                from analysis.utils.image_processing import create_quality_map_visualization
                roi_coords = self.main_window.roi_handler.roi_coords if hasattr(self.main_window,
                                                                                'roi_handler') else None

                visualization = create_quality_map_visualization(
                    self.main_window.original_image.copy(),
                    self.main_window.image_display.quality_map_data,
                    roi_coords,
                    display_scale=1.0,
                    spectrum_type=spectrum_type
                )

                # Save as image
                pil_image = Image.fromarray(visualization)
                pil_image.save(filename)

                self.main_window.status_var.set(f"Quality map exported: {os.path.basename(filename)}")
                messagebox.showinfo("Export Complete", f"Quality map visualization saved to:\n{filename}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export quality map: {str(e)}")

    def save_analysis_data_csv(self):
        """Save raw analysis data as CSV for further processing"""
        if not hasattr(self.main_window.image_display, 'quality_map_data') or \
                self.main_window.image_display.quality_map_data is None:
            messagebox.showwarning("No Analysis Data",
                                   "No analysis data available to export. Please analyze an image first.")
            return

        # Get save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Analysis Data as CSV"
        )

        if filename:
            try:
                import csv
                quality_map = self.main_window.image_display.quality_map_data

                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)

                    # Header
                    writer.writerow(['X_Pixel', 'Y_Pixel', 'Quality_Score_0_1', 'Quality_Percentage'])

                    # Data
                    h, w = quality_map.shape
                    for y in range(h):
                        for x in range(w):
                            quality_01 = quality_map[y, x]
                            quality_percent = quality_01 * 100
                            writer.writerow([x, y, f"{quality_01:.6f}", f"{quality_percent:.2f}"])

                self.main_window.status_var.set(f"Analysis data exported: {os.path.basename(filename)}")
                messagebox.showinfo("Export Complete", f"Analysis data saved to CSV:\n{filename}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export analysis data: {str(e)}")