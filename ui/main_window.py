# module: ui.main_window

import tkinter as tk
import cv2
from tkinter import ttk, messagebox
import numpy as np
from PIL import ImageGrab
import threading
from ui.image_display import ImageDisplay
from ui.roi_handler import ROIHandler
from ui.file_operations import FileOperations
from analysis.quality_map.map_generator import generate_quality_map
from ui.button_state_manager import ButtonStateManager
from analysis.core.subset_analyzer import determine_optimal_subset_size

class DICQualityInspector:
    def __init__(self, root):
        self.root = root
        self.root.title("DIC Image Quality Inspector - ROI Enhanced")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')

        # Variables
        self.current_image = None
        self.original_image = None
        self.analysis_results = {}
        self.roi_coords = None  # (x1, y1, x2, y2)
        self.roi_selection_mode = False
        self.roi_start = None
        self.roi_rect = None

        # Create GUI
        self.create_gui()

        # Create managers
        self.image_display = ImageDisplay(self.image_canvas, self)
        self.file_operations = FileOperations(self)
        self.roi_handler = ROIHandler(self)
        self.state_manager = ButtonStateManager(self)

        # Connect UI elements to manager methods
        self.load_btn.config(command=self.file_operations.load_image)
        self.roi_btn.config(command=self.roi_handler.toggle_roi_selection)
        self.screenshot_btn.config(command=self.start_screenshot)
        self.analyze_btn.config(command=self.analyze_image)
        self.quality_map_btn.config(command=self.image_display.toggle_quality_map_overlay)
        self.save_btn.config(command=self.file_operations.save_report)
        self.quality_map_btn.config(state='disabled')

    def create_gui(self):
        # Main title
        title_frame = tk.Frame(self.root, bg='#2c3e50')
        title_frame.pack(pady=10)

        title_label = tk.Label(title_frame, text="🔍 DIC Image Quality Inspector - ROI Enhanced",
                               font=('Arial', 24, 'bold'), fg='#ecf0f1', bg='#2c3e50')
        title_label.pack()

        # Control frame
        control_frame = tk.Frame(self.root, bg='#34495e', relief='raised', bd=2)
        control_frame.pack(fill='x', padx=10, pady=5)

        # Buttons
        btn_frame = tk.Frame(control_frame, bg='#34495e')
        btn_frame.pack(pady=10)

        self.load_btn = tk.Button(btn_frame, text="📁 Load Image",
                                  bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                                  padx=20, pady=5)
        self.load_btn.pack(side='left', padx=5)

        self.screenshot_btn = tk.Button(btn_frame, text="📸 Screen Capture",
                                        bg='#e67e22', fg='white', font=('Arial', 12, 'bold'),
                                        padx=20, pady=5)
        self.screenshot_btn.pack(side='left', padx=5)

        self.roi_btn = tk.Button(btn_frame, text="🎯 Select ROI",
                                 bg='#9b59b6', fg='white', font=('Arial', 12, 'bold'),
                                 padx=20, pady=5, state='disabled')
        self.roi_btn.pack(side='left', padx=5)

        self.analyze_btn = tk.Button(btn_frame, text="🔬 Analyze",
                                     bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                     padx=20, pady=5, state='disabled')
        self.analyze_btn.pack(side='left', padx=5)

        self.save_btn = tk.Button(btn_frame, text="💾 Save Report",
                                  bg='#8e44ad', fg='white', font=('Arial', 12, 'bold'),
                                  padx=20, pady=5, state='disabled')
        self.save_btn.pack(side='left', padx=5)

        # Help button
        self.help_btn = tk.Button(btn_frame, text="❓ Help",
                                  bg="#7f8c8d", fg="white", font=("Arial", 12, "bold"),
                                  padx=10, pady=5, command=self.show_help)
        self.help_btn.pack(side="left", padx=5)

        # ROI Info
        roi_info_frame = tk.Frame(control_frame, bg='#34495e')
        roi_info_frame.pack(pady=5)

        self.roi_info_label = tk.Label(roi_info_frame, text="ROI: Not Selected (analyzing full image)",
                                       font=('Arial', 10), fg='#bdc3c7', bg='#34495e')
        self.roi_info_label.pack()

        # Main content frame
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Left panel - Image display
        left_panel = tk.Frame(main_frame, bg='#34495e', relief='raised', bd=2)
        left_panel.pack(side='left', fill='both', expand=True, padx=5)

        img_title = tk.Label(left_panel, text="📸 Image Preview", font=('Arial', 16, 'bold'),
                             fg='#ecf0f1', bg='#34495e')
        img_title.pack(pady=10)

        # Image canvas with scrollbars
        canvas_frame = tk.Frame(left_panel, bg='#34495e')
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.image_canvas = tk.Canvas(canvas_frame, bg='white', width=600, height=400)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.image_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.image_canvas.xview)

        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Position components
        self.image_canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Image processing buttons
        process_frame = tk.Frame(left_panel, bg='#34495e')
        process_frame.pack(pady=10)

        original_btn = tk.Button(process_frame, text="Original",
                                 bg='#95a5a6', fg='white', padx=10,
                                 command=lambda: self.image_display.show_original())
        original_btn.pack(side='left', padx=2)

        edges_btn = tk.Button(process_frame, text="Edges",
                              bg='#95a5a6', fg='white', padx=10,
                              command=lambda: self.image_display.show_edges())
        edges_btn.pack(side='left', padx=2)

        gradient_btn = tk.Button(process_frame, text="Gradient",
                                 bg='#95a5a6', fg='white', padx=10,
                                 command=lambda: self.image_display.show_gradient())
        gradient_btn.pack(side='left', padx=2)

        reset_display_btn = tk.Button(process_frame, text="Reset Display",
                                      bg='#e74c3c', fg='white', padx=10,
                                      command=lambda: self.image_display.reset_display())
        reset_display_btn.pack(side='left', padx=2)

        # Quality map button
        self.quality_map_btn = tk.Button(process_frame, text="Quality Map",
                                         bg='#2ecc71', fg='white', padx=10)
        self.quality_map_btn.pack(side='left', padx=2)

        # QUALITY MAP LEGEND - Inline as small buttons/labels
        legend_items = [
            ("Excellent", "#0066FF"),  # Blue
            ("Good", "#00FF00"),  # Green
            ("Acceptable", "#FFFF00"),  # Yellow
            ("Marginal", "#FF8800"),  # Orange
            ("Poor", "#FF0000")  # Red
        ]

        for text, color in legend_items:
            legend_btn = tk.Label(process_frame, text=f"■ {text}",
                                  bg='#34495e', fg=color, font=('Arial', 9),
                                  padx=5, pady=2)
            legend_btn.pack(side='left', padx=1)

        # Right panel - Analysis results
        right_panel = tk.Frame(main_frame, bg='#34495e', relief='raised', bd=2)
        right_panel.pack(side='right', fill='y', padx=5)
        right_panel.config(width=400)

        results_title = tk.Label(right_panel, text="📊 Quality Analysis", font=('Arial', 16, 'bold'),
                                 fg='#ecf0f1', bg='#34495e')
        results_title.pack(pady=10)

        # Scrollable results frame
        canvas_results = tk.Canvas(right_panel, bg='#34495e', highlightthickness=0)
        scrollbar_results = ttk.Scrollbar(right_panel, orient='vertical', command=canvas_results.yview)
        self.results_frame = tk.Frame(canvas_results, bg='#34495e')

        canvas_results.configure(yscrollcommand=scrollbar_results.set)
        canvas_results.pack(side='left', fill='both', expand=True, padx=10)
        scrollbar_results.pack(side='right', fill='y')

        canvas_results.create_window((0, 0), window=self.results_frame, anchor='nw')

        def configure_scroll_region(event):
            canvas_results.configure(scrollregion=canvas_results.bbox('all'))

        self.results_frame.bind('<Configure>', configure_scroll_region)

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Load an image and select ROI for accurate analysis")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief='sunken',
                              anchor='w', bg='#95a5a6', fg='white')
        status_bar.pack(side='bottom', fill='x')

    def start_screenshot(self):
        """Start screenshot capture process"""
        from ctypes import windll

        # Set DPI awareness for consistent coordinates
        windll.shcore.SetProcessDpiAwareness(1)

        # Reset analysis results and quality map data when taking a new screenshot
        self.analysis_results = {}
        if hasattr(self.image_display, 'quality_map_data'):
            self.image_display.quality_map_data = None
            self.image_display.quality_visualization = None
            self.image_display.showing_quality_overlay = False

        # Disable the quality map button until analysis is performed
        self.quality_map_btn.config(state='disabled')

        self.root.withdraw()  # Hide main window

        # Create screenshot window
        screenshot_window = tk.Toplevel()
        screenshot_window.attributes('-fullscreen', True)
        screenshot_window.attributes('-alpha', 0.3)
        screenshot_window.configure(bg='black')
        screenshot_window.attributes('-topmost', True)

        instructions = tk.Label(screenshot_window,
                                text="Click and drag to select a screen region, or press ESC to cancel",
                                font=('Arial', 16), fg="white", bg="black")
        instructions.pack(expand=True)

        # Create canvas for drawing selection rectangle
        selection_canvas = tk.Canvas(screenshot_window, highlightthickness=0)
        selection_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Screenshot selection variables
        self.start_x = self.start_y = 0
        self.rect_id = None

        def start_selection(event):
            self.start_x, self.start_y = event.x, event.y
            if self.rect_id:
                selection_canvas.delete(self.rect_id)

        def update_selection(event):
            if self.rect_id:
                selection_canvas.delete(self.rect_id)
            self.rect_id = selection_canvas.create_rectangle(self.start_x, self.start_y,
                                                             event.x, event.y, outline='red', width=3)

        def end_selection(event):
            # Store selection coordinates
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)

            # Close screenshot window
            screenshot_window.destroy()

            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                try:
                    # Take screenshot
                    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))

                    # Show main window after capture is ready
                    self.root.deiconify()
                    self.root.update()

                    # Store image data
                    self.original_image = np.array(screenshot)
                    self.current_image = self.original_image.copy()

                    # Clear previous ROI
                    self.roi_handler.update_roi_info()

                    # Use same approach as load_image_from_path
                    self.image_display.display_image(screenshot)

                    # Reset view position
                    self.image_canvas.xview_moveto(0)
                    self.image_canvas.yview_moveto(0)

                    # Update state to image_loaded
                    if hasattr(self, 'state_manager'):
                        self.state_manager.update_state("image_loaded")

                    self.status_var.set(f"Screenshot captured: {screenshot.width}x{screenshot.height} pixels")

                except Exception as e:
                    self.root.deiconify()
                    messagebox.showerror("Error", f"Failed to capture screenshot: {str(e)}")

                    # Reset to no_image state on error
                    if hasattr(self, 'state_manager'):
                        self.state_manager.update_state("no_image")
            else:
                self.root.deiconify()
                self.status_var.set("Screenshot cancelled - area too small")

        def cancel_screenshot(event=None):
            screenshot_window.destroy()
            self.root.deiconify()
            return "break"

        # Bind events
        screenshot_window.bind('<Button-1>', start_selection)
        screenshot_window.bind('<B1-Motion>', update_selection)
        screenshot_window.bind('<ButtonRelease-1>', end_selection)

        # Add multiple bindings to ensure ESC key is captured
        screenshot_window.bind('<Escape>', cancel_screenshot)
        selection_canvas.bind('<Escape>', cancel_screenshot)
        instructions.bind('<Escape>', cancel_screenshot)

        # Bind key press at the application level
        screenshot_window.bind_all('<Escape>', cancel_screenshot)

        # Force focus and grab all events
        screenshot_window.focus_force()
        screenshot_window.grab_set()
        screenshot_window.update()

    def _analyze_worker(self):
        """Worker thread for analysis - FIXED with proper variable scoping"""
        try:
            # Always analyze full image for proper quality map alignment
            print("Generating quality map from full image...")
            quality_map, visualization = generate_quality_map(self.original_image)

            # Store quality map data in image display for overlay
            self.image_display.quality_map_data = quality_map
            self.image_display.quality_visualization = visualization
            print(
                f"Quality map generated: shape {quality_map.shape}, range {quality_map.min():.3f}-{quality_map.max():.3f}")

            # FIXED: Initialize variables before conditional blocks
            roi_quality_scores = None
            use_roi_calculation = False

            # Calculate overall score from ROI region only (to match what user sees)
            if hasattr(self, 'roi_handler') and self.roi_handler.roi_coords and len(self.roi_handler.roi_coords) >= 3:
                try:
                    # Extract quality scores from ROI region only
                    roi_quality_scores = self._extract_roi_quality_scores(quality_map, self.roi_handler.roi_coords)
                    if roi_quality_scores is not None and len(roi_quality_scores) > 0:
                        average_quality = float(np.mean(roi_quality_scores) * 100)
                        use_roi_calculation = True
                        print(
                            f"ROI-based quality calculation: {average_quality:.1f}% (from {len(roi_quality_scores)} ROI pixels)")
                    else:
                        # ROI extraction failed, fall back to full image
                        average_quality = float(np.mean(quality_map) * 100)
                        print(f"ROI extraction failed, using full image quality: {average_quality:.1f}%")
                except Exception as e:
                    print(f"Error in ROI quality extraction: {e}")
                    # Fall back to full image calculation
                    average_quality = float(np.mean(quality_map) * 100)
                    print(f"Fallback to full image quality calculation: {average_quality:.1f}%")
            else:
                # No ROI - use full image average
                average_quality = float(np.mean(quality_map) * 100)
                print(f"Full image quality calculation: {average_quality:.1f}%")

            # Determine optimal subset size for DIC parameters
            from analysis.core.subset_analyzer import determine_optimal_subset_size
            if len(self.original_image.shape) == 3:
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)
            else:
                gray = self.original_image.copy()
            self.optimal_subset_size = determine_optimal_subset_size(gray)

            # FIXED: Use appropriate data source for statistics
            if use_roi_calculation and roi_quality_scores is not None:
                # Use ROI-based statistics
                quality_data_for_stats = roi_quality_scores
                print("Using ROI-based statistics")
            else:
                # Use full quality map statistics
                quality_data_for_stats = quality_map.flatten()
                print("Using full image statistics")

            # Create results with consistent data source
            analysis_results = {
                'overall_score': round(average_quality, 1),
                'average_quality': average_quality,
                'quality_std': float(np.std(quality_data_for_stats) * 100),
                'optimal_subset_size': self.optimal_subset_size,
                'quality_map_stats': {
                    'min_quality': float(np.min(quality_data_for_stats) * 100),
                    'max_quality': float(np.max(quality_data_for_stats) * 100),
                    'median_quality': float(np.median(quality_data_for_stats) * 100)
                },
                'analysis_method': 'ROI-based' if use_roi_calculation else 'Full image'
            }

            print(f"Analysis complete. Overall score: {average_quality:.1f} ({analysis_results['analysis_method']})")

            # Call completion handler on UI thread
            self.root.after(0, lambda: self._on_analysis_complete(analysis_results))

        except Exception as e:
            import traceback
            error_message = str(e)
            traceback_info = traceback.format_exc()
            print(f"Analysis Error: {error_message}\n{traceback_info}")
            self.root.after(0, lambda: self._on_analysis_error(error_message))

    def _extract_roi_quality_scores(self, quality_map, roi_coords):
        """Extract quality scores from ROI region only"""
        try:
            import cv2
            import numpy as np

            # Validate inputs
            if quality_map is None or roi_coords is None:
                print("Invalid inputs to _extract_roi_quality_scores")
                return None

            if len(roi_coords) < 3:
                print("ROI coords too short for polygon")
                return None

            # Create mask for ROI
            mask = np.zeros(quality_map.shape[:2], dtype=np.uint8)
            pts = np.array(roi_coords, dtype=np.int32)

            # Validate ROI coordinates are within image bounds
            h, w = quality_map.shape[:2]
            pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)  # Clamp x coordinates
            pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)  # Clamp y coordinates

            cv2.fillPoly(mask, [pts], 255)

            # Extract quality scores from ROI pixels only
            roi_mask_bool = mask > 0
            roi_pixel_count = np.sum(roi_mask_bool)

            if roi_pixel_count == 0:
                print("ROI mask is empty - no pixels selected")
                return None

            roi_quality_scores = quality_map[roi_mask_bool]

            print(f"Extracted {len(roi_quality_scores)} quality scores from ROI ({roi_pixel_count} pixels)")
            return roi_quality_scores

        except Exception as e:
            print(f"Error in _extract_roi_quality_scores: {e}")
            return None

    def analyze_image(self):
        """Enhanced analyze with state management"""
        if self.original_image is None:
            return

        # Check if analysis is allowed
        if not self.state_manager.can_analyze():
            self.status_var.set("Analysis not available in current state")
            return

        if self.state_manager.is_analysis_in_progress():
            self.status_var.set("Analysis already in progress")
            return

        # Update state to analyzing
        self.state_manager.update_state("analyzing")

        # Run analysis in separate thread
        threading.Thread(target=self._analyze_worker, daemon=True).start()

    def _on_analysis_complete(self, analysis_results):
        """Handle analysis completion - simplified version"""
        # Store results
        self.analysis_results = analysis_results

        # Get overall score (same as average quality)
        score = analysis_results.get('overall_score', 0)

        # Update results display
        self._update_results_display()

        # Update state to analysis_complete
        self.state_manager.update_state("analysis_complete", score=score)

        # Enable quality map button
        self.quality_map_btn.config(state='normal')

        # Auto-show quality map after a brief delay
        self.root.after(500, self._auto_show_quality_map)

    def _auto_show_quality_map(self):
        """Automatically show quality map after analysis"""
        if hasattr(self.image_display, 'quality_map_data') and self.image_display.quality_map_data is not None:
            # Only auto-show if not already showing
            if not getattr(self.image_display, 'showing_quality_overlay', False):
                self.image_display.toggle_quality_map_overlay()

    def _on_analysis_error(self, error_msg):
        """Handle analysis error"""
        messagebox.showerror("Analysis Error", f"Failed to analyze image: {error_msg}")

        # Reset to appropriate state
        if (hasattr(self, 'roi_handler') and
                self.roi_handler.roi_coords and
                len(self.roi_handler.roi_coords) >= 3):
            self.state_manager.update_state("roi_selected")
        else:
            self.state_manager.update_state("image_loaded")

    def _update_results_display(self):
        """Update the GUI with quality map based results"""
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not self.analysis_results:
            return

        results = self.analysis_results

        # Overall Quality Score (prominent display)
        score_frame = tk.Frame(self.results_frame, bg='#34495e', relief='raised', bd=2)
        score_frame.pack(fill='x', padx=10, pady=10)

        overall_score = results['overall_score']

        # FIXED: Use the new quality assessment function
        score_text, score_color = self.get_quality_assessment_text(overall_score / 100.0)

        tk.Label(score_frame, text="DIC Pattern Quality",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=5)

        # Large quality score display
        score_display_frame = tk.Frame(score_frame, bg='#34495e')
        score_display_frame.pack(pady=10)

        tk.Label(score_display_frame, text=f"{overall_score:.1f}",
                 font=('Arial', 48, 'bold'), fg=score_color, bg='#34495e').pack(side='left')
        tk.Label(score_display_frame, text="/100",
                 font=('Arial', 24), fg='#bdc3c7', bg='#34495e').pack(side='left', anchor='s', padx=(5, 0))

        tk.Label(score_frame, text=score_text,
                 font=('Arial', 14), fg=score_color, bg='#34495e').pack()

        # ... rest of the existing _update_results_display method stays the same ...

    def _calculate_dic_parameters(self, results):
        """Calculate recommended DIC parameters based on existing analysis results"""

        # Use the optimal subset size that was calculated during analysis
        if hasattr(self, 'optimal_subset_size'):
            facet_size = self.optimal_subset_size
        else:
            # Fallback: calculate it now if somehow missing
            if hasattr(self, 'original_image') and self.original_image is not None:
                gray = self.original_image
                if len(gray.shape) == 3:
                    import cv2
                    gray = cv2.cvtColor(gray, cv2.COLOR_RGB2GRAY)
                facet_size = determine_optimal_subset_size(gray)
            else:
                facet_size = 21  # Final fallback

        # Calculate step size for standard DIC overlap (75%)
        overlap_percent = 75
        step_size = max(1, int(facet_size * (1 - overlap_percent / 100)))

        # Determine expected accuracy based on pattern quality (more realistic thresholds)
        score = results.get('overall_score', 0)
        if score >= 70:
            accuracy = "±0.01 pixels"
        elif score >= 50:
            accuracy = "±0.02 pixels"
        elif score >= 30:
            accuracy = "±0.05 pixels"
        elif score >= 15:
            accuracy = "±0.1 pixels"
        else:
            accuracy = "±0.2 pixels"

        return {
            'facet_size': facet_size,
            'step_size': step_size,
            'overlap': overlap_percent,
            'accuracy': accuracy
        }

    def _generate_recommendations(self, score):
        """
        UPDATED: Generate recommendations based on the new realistic scoring

        Args:
            score: Overall quality score (0-100)
        """
        recommendations = []

        if score >= 75:
            recommendations.append("Excellent pattern! Proceed with DIC analysis using recommended parameters.")
            recommendations.append("Consider using sub-pixel interpolation for maximum accuracy.")
            recommendations.append("Pattern has optimal gradient content and speckle morphology.")
        elif score >= 60:
            recommendations.append("Very good pattern quality. DIC analysis should work excellently.")
            recommendations.append("Use standard DIC parameters with confidence.")
            recommendations.append("Monitor correlation quality during analysis for best results.")
        elif score >= 45:
            recommendations.append("Good pattern for DIC analysis with proper setup.")
            recommendations.append("Use recommended subset sizes and overlap settings.")
            recommendations.append("Consider slightly larger subset sizes if correlation issues occur.")
        elif score >= 30:
            recommendations.append("Acceptable pattern for DIC analysis with careful setup.")
            recommendations.append("Use larger subset sizes (increase by 20-30%) for better correlation.")
            recommendations.append("Monitor correlation quality closely during analysis.")
            recommendations.append("Consider post-processing filtering if needed.")
        elif score >= 15:
            recommendations.append("Challenging but workable pattern for DIC analysis.")
            recommendations.append("Use larger subset sizes and stricter correlation criteria.")
            recommendations.append("Expect some areas to have poor correlation - filter results carefully.")
            recommendations.append("Consider pattern enhancement if critical accuracy is needed.")
        else:
            recommendations.append("Poor pattern quality - DIC will have significant limitations.")
            recommendations.append("Strong recommendation to improve or reapply speckle pattern.")
            recommendations.append("If proceeding: use maximum subset sizes and very strict filtering.")
            recommendations.append("Consider alternative measurement techniques if high accuracy needed.")

        # Add general recommendations
        recommendations.append("Save quality map and parameters for repeatability.")
        if score < 60:
            recommendations.append("Document pattern limitations in analysis report.")

        return recommendations

    def get_quality_assessment_text(self, score):
        """
        FIXED: Realistic quality thresholds based on DIC research

        Args:
            score: Quality score from 0.0 to 1.0

        Returns:
            tuple: (description_text, color_hex)
        """
        # Convert 0-1 score to percentage for thresholds
        score_percent = score * 100

        if score_percent >= 75:
            return "Excellent for DIC", "#27ae60"  # Green
        elif score_percent >= 60:
            return "Very Good for DIC", "#2ecc71"  # Light Green
        elif score_percent >= 45:
            return "Good for DIC", "#f39c12"  # Orange
        elif score_percent >= 30:
            return "Acceptable for DIC", "#e67e22"  # Dark Orange
        elif score_percent >= 15:
            return "Challenging for DIC", "#e74c3c"  # Red
        else:
            return "Poor for DIC", "#8e44ad"  # Purple

    def show_help(self):
        """Show comprehensive help for the application"""
        help_text = """
    DIC Image Quality Inspector - Help Guide

    • Getting Started:
      - Load an image using "Load Image" or capture with "Screen Capture"
      - Images can be in PNG, JPEG, TIFF, or BMP formats

    • Region of Interest (ROI):
      - Click "Select ROI" to enable ROI selection mode
      - Click and drag on the image to select your analysis region
      - Right-click to complete the polygon selection

    • Image Navigation:
      - Zoom: Use the mouse wheel to zoom in/out
      - Pan: Hold Ctrl + click and drag to move around
      - Reset View: Click "Reset Display" to return to original view

    • Image Processing:
      - Original: Return to the unprocessed image
      - Edges: Display edge detection visualization
      - Gradient: Display gradient magnitude visualization
      - Quality Map: Toggle overlay showing DIC quality analysis

    • Analysis:
      - Click "Analyze" to process the image quality metrics
      - Results are shown in the right panel
      - Higher overall scores indicate better DIC pattern quality
      - Quality map shows color-coded analysis across the image

    • Report:
      - Save a detailed analysis report using "Save Report"

    • Troubleshooting:
      - If ROI selection appears off, try resetting the view first
      - For best results, ensure proper lighting in original images
      - Large images may take longer to process
        """

        # Create a custom dialog with scrollable text
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("DIC Image Quality Inspector - Help")
        help_dialog.geometry("600x500")
        help_dialog.transient(self.root)
        help_dialog.grab_set()

        # Add scrollable text area
        text_frame = tk.Frame(help_dialog)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(text_frame, wrap="word", bg="#f0f0f0",
                              font=("Arial", 11), padx=10, pady=10)
        text_widget.pack(side="left", fill="both", expand=True)

        # Connect scrollbar to text widget
        scrollbar.config(command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)

        # Insert help text
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")  # Make read-only

        # Close button
        close_button = tk.Button(help_dialog, text="Close",
                                 bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                                 command=help_dialog.destroy, padx=20, pady=5)
        close_button.pack(pady=10)

