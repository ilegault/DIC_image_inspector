# module: ui.main_window

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from PIL import ImageGrab
import threading
from ui.image_display import ImageDisplay
from ui.roi_handler import ROIHandler
from ui.file_operations import FileOperations
from analysis.analyzer import DICAnalyzer
from analysis.quality_map.map_generator import generate_quality_map
from ui.roi_handler import get_analysis_region
from ui.button_state_manager import ButtonStateManager


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

        self.image_canvas = tk.Canvas(canvas_frame, bg='white', width=600, height=500)
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
        """Worker thread for analysis with integrated quality map generation"""
        try:
            # Get analysis region (but always analyze full image for quality map alignment)
            if self.roi_handler.roi_coords and len(self.roi_handler.roi_coords) >= 3:
                # For polygon ROI, extract region for statistical analysis only
                analysis_region = get_analysis_region(self.original_image, self.roi_handler.roi_coords)
                print(f"Analyzing polygon ROI with {len(self.roi_handler.roi_coords)} points")
            else:
                # Full image analysis
                analysis_region = self.original_image.copy()
                print("Analyzing full image")

            # ALWAYS generate quality map from full image for proper overlay alignment
            print("Generating quality map from full image...")
            quality_map, visualization = generate_quality_map(self.original_image)

            # Store quality map data in image display for overlay
            self.image_display.quality_map_data = quality_map
            self.image_display.quality_visualization = visualization
            print(
                f"Quality map generated: shape {quality_map.shape}, range {quality_map.min():.3f}-{quality_map.max():.3f}")

            # Run main DIC analysis on the analysis region
            print("Running DIC analysis...")
            self.analyzer = DICAnalyzer()  # Store analyzer instance to access subset_size
            results = self.analyzer.analyze(analysis_region)

            # Add quality map data to results
            if quality_map is not None:
                results['quality_map'] = quality_map
                results['quality_visualization'] = visualization
                # Calculate overall quality statistics
                avg_quality = np.mean(quality_map)
                results['average_quality'] = avg_quality * 100  # Scale to 0-100
                print(f"Average quality: {avg_quality:.3f}")

            # Store results
            self.analysis_results = results

            print(f"Analysis complete. Overall score: {results.get('overall_score', 'N/A')}")

            # Update UI in main thread
            self.root.after(0, lambda: self._on_analysis_complete(results.get('overall_score', 0)))

        except Exception as e:
            import traceback
            error_message = str(e)
            traceback_info = traceback.format_exc()
            print(f"Analysis Error: {error_message}\n{traceback_info}")
            self.root.after(0, lambda: self._on_analysis_error(error_message))

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

    def _on_analysis_complete(self, score):
        """Handle analysis completion"""
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
        """Update the GUI with simplified DIC-focused results"""
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not self.analysis_results:
            return

        results = self.analysis_results

        # Overall Quality Score (prominent display similar to your reference image)
        score_frame = tk.Frame(self.results_frame, bg='#34495e', relief='raised', bd=2)
        score_frame.pack(fill='x', padx=10, pady=10)

        overall_score = results['overall_score']

        # Color code the score with more realistic DIC thresholds
        if overall_score >= 70:
            score_color = '#27ae60'  # Green
            score_text = "Excellent for DIC"
        elif overall_score >= 50:
            score_color = '#f39c12'  # Orange
            score_text = "Good for DIC"
        elif overall_score >= 30:
            score_color = '#e67e22'  # Dark Orange
            score_text = "Acceptable for DIC"
        elif overall_score >= 15:
            score_color = '#e74c3c'  # Red
            score_text = "Challenging for DIC"
        else:
            score_color = '#8e44ad'  # Purple
            score_text = "Very Difficult for DIC"

        tk.Label(score_frame, text="DIC Pattern Quality",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=5)

        # Large quality score display
        score_display_frame = tk.Frame(score_frame, bg='#34495e')
        score_display_frame.pack(pady=10)

        tk.Label(score_display_frame, text=f"{overall_score}",
                 font=('Arial', 48, 'bold'), fg=score_color, bg='#34495e').pack(side='left')
        tk.Label(score_display_frame, text="/100",
                 font=('Arial', 24), fg='#bdc3c7', bg='#34495e').pack(side='left', anchor='s', padx=(5, 0))

        tk.Label(score_frame, text=score_text,
                 font=('Arial', 14), fg=score_color, bg='#34495e').pack()

        # Average Quality from Quality Map (if available)
        if 'average_quality' in results:
            avg_quality = results['average_quality']
            tk.Label(score_frame, text=f"Average Pattern Quality: {avg_quality:.1f}%",
                     font=('Arial', 11), fg='#bdc3c7', bg='#34495e').pack(pady=(5, 0))

        # DIC Analysis Parameters Section
        params_frame = tk.Frame(self.results_frame, bg='#34495e', relief='raised', bd=2)
        params_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(params_frame, text="📐 Recommended DIC Parameters",
                 font=('Arial', 14, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=5)

        # Calculate recommended parameters based on analysis
        recommended_params = self._calculate_dic_parameters(results)

        # Facet Size
        param_frame = tk.Frame(params_frame, bg='#34495e')
        param_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(param_frame, text="Facet Size:",
                 font=('Arial', 12, 'bold'), fg='#bdc3c7', bg='#34495e', width=15, anchor='w').pack(side='left')
        tk.Label(param_frame, text=f"{recommended_params['facet_size']} pixels",
                 font=('Arial', 12), fg='#ecf0f1', bg='#34495e').pack(side='left')

        # Step Size
        param_frame = tk.Frame(params_frame, bg='#34495e')
        param_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(param_frame, text="Step Size:",
                 font=('Arial', 12, 'bold'), fg='#bdc3c7', bg='#34495e', width=15, anchor='w').pack(side='left')
        tk.Label(param_frame, text=f"{recommended_params['step_size']} pixels",
                 font=('Arial', 12), fg='#ecf0f1', bg='#34495e').pack(side='left')

        # Overlap Percentage
        param_frame = tk.Frame(params_frame, bg='#34495e')
        param_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(param_frame, text="Overlap:",
                 font=('Arial', 12, 'bold'), fg='#bdc3c7', bg='#34495e', width=15, anchor='w').pack(side='left')
        tk.Label(param_frame, text=f"{recommended_params['overlap']}%",
                 font=('Arial', 12), fg='#ecf0f1', bg='#34495e').pack(side='left')

        # Expected Accuracy
        param_frame = tk.Frame(params_frame, bg='#34495e')
        param_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(param_frame, text="Expected Accuracy:",
                 font=('Arial', 12, 'bold'), fg='#bdc3c7', bg='#34495e', width=15, anchor='w').pack(side='left')
        tk.Label(param_frame, text=recommended_params['accuracy'],
                 font=('Arial', 12), fg='#ecf0f1', bg='#34495e').pack(side='left')

        # DIC-Specific Recommendations
        recommendations = self._generate_dic_recommendations(results, recommended_params)
        if recommendations:
            rec_frame = tk.Frame(self.results_frame, bg='#34495e', relief='raised', bd=2)
            rec_frame.pack(fill='x', padx=10, pady=10)

            tk.Label(rec_frame, text="🎯 DIC Setup Recommendations",
                     font=('Arial', 14, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=5)

            for i, rec in enumerate(recommendations, 1):
                rec_item_frame = tk.Frame(rec_frame, bg='#34495e')
                rec_item_frame.pack(fill='x', padx=10, pady=3)

                tk.Label(rec_item_frame, text=f"{i}.",
                         font=('Arial', 10, 'bold'), fg='#3498db', bg='#34495e', width=3, anchor='w').pack(side='left')
                tk.Label(rec_item_frame, text=rec,
                         font=('Arial', 10), fg='#bdc3c7', bg='#34495e',
                         wraplength=320, justify='left', anchor='w').pack(side='left', fill='x', expand=True)

        # Update status
        roi_text = "ROI" if (self.roi_handler.roi_coords and len(self.roi_handler.roi_coords) >= 3) else "full image"
        self.status_var.set(f"Analysis complete - DIC quality: {overall_score}/100 ({roi_text})")

    def _calculate_dic_parameters(self, results):
        """Calculate recommended DIC parameters based on existing analysis results"""

        # Use the existing subset size that was already calculated by the analyzer
        if hasattr(self, 'analyzer') and hasattr(self.analyzer, 'subset_size'):
            facet_size = self.analyzer.subset_size
        else:
            # Fallback: use the optimal subset size determination from your existing code
            from analysis.core.subset_analyzer import determine_optimal_subset_size
            if hasattr(self, 'original_image') and self.original_image is not None:
                gray = self.original_image
                if len(gray.shape) == 3:
                    import cv2
                    gray = cv2.cvtColor(gray, cv2.COLOR_RGB2GRAY)
                facet_size = determine_optimal_subset_size(gray)
            else:
                facet_size = 21  # Fallback

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

    def _generate_dic_recommendations(self, results, params):
        """Generate DIC-specific recommendations"""
        recommendations = []
        score = results.get('overall_score', 0)

        # Pattern quality recommendations with more realistic thresholds
        if score >= 70:
            recommendations.append("Excellent pattern! Proceed with DIC analysis using recommended parameters.")
            recommendations.append("Consider using sub-pixel interpolation for maximum accuracy.")
        elif score >= 50:
            recommendations.append("Good pattern quality. DIC analysis should work well with standard settings.")
            recommendations.append("Monitor correlation quality during analysis - most subsets should correlate well.")
        elif score >= 30:
            recommendations.append("Acceptable pattern for DIC analysis with proper setup.")
            recommendations.append("Use recommended parameters and monitor correlation quality closely.")
            recommendations.append("Consider slightly larger facet sizes if correlation issues occur.")
        elif score >= 15:
            recommendations.append("Challenging but workable pattern for DIC analysis.")
            recommendations.append("Use larger facet sizes and careful correlation criteria.")
            recommendations.append("Expect some subsets to have poor correlation - use subset filtering.")
            recommendations.append("Consider improving lighting uniformity if possible.")
        else:
            recommendations.append("Very difficult pattern - DIC possible but with significant limitations.")
            recommendations.append("Use maximum feasible facet sizes and conservative correlation criteria.")
            recommendations.append("Expect substantial subset dropout and reduced spatial resolution.")
            recommendations.append("Consider pattern enhancement or re-application if critical results needed.")

        # Facet size specific recommendations
        facet_size = params['facet_size']
        if facet_size > 51:
            recommendations.append(f"Large facet size ({facet_size}px) recommended due to speckle characteristics.")
            recommendations.append("Larger facets provide better correlation but reduce spatial resolution.")
        elif facet_size < 21:
            recommendations.append(f"Small facet size ({facet_size}px) sufficient for this pattern.")
            recommendations.append("Smaller facets give better spatial resolution but may be less robust.")

        # Score-specific parameter adjustments
        if score < 40:
            recommendations.append("For low-quality patterns: Consider 80-85% overlap instead of 75%.")
            recommendations.append("Use stricter correlation coefficients (>0.8) to filter poor subsets.")

        # Contrast and feature recommendations
        contrast = results.get('contrast', 0)
        if contrast < 15:
            recommendations.append("Very low contrast - improve lighting or pattern application if possible.")
        elif contrast < 25:
            recommendations.append("Low contrast detected - monitor for correlation difficulties.")
        elif contrast > 80:
            recommendations.append("High contrast detected - watch for saturation in DIC images.")

        # Density recommendations adjusted for practical DIC
        density = results.get('speckle_density', 0)
        if density < 20:
            recommendations.append("Very low speckle density - expect reduced correlation reliability.")
        elif density < 40:
            recommendations.append("Low speckle density - consider adding pattern features if possible.")
        elif density > 300:
            recommendations.append("Very high speckle density - pattern may be too busy for optimal correlation.")

        # Software-specific recommendations based on score
        if score >= 30:
            recommendations.append("Pattern suitable for standard DIC analysis and strain mapping.")
        else:
            recommendations.append("Use post-processing filters to improve displacement field smoothness.")
            recommendations.append("Consider temporal or spatial filtering to reduce noise in results.")

        recommendations.append(
            "Save DIC parameters: Facet size, step size, and correlation criteria for repeatability.")

        return recommendations

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

    def _generate_recommendations(self, results):
        """Generate recommendations based on analysis results with adaptive thresholds for specimens of all sizes"""
        recommendations = []

        # Get image resolution to adjust thresholds
        image_size = self.original_image.shape[:2]
        image_mpx = (image_size[0] * image_size[1]) / 1_000_000

        # Get ROI size if available (for analyzing selected regions)
        if hasattr(self, 'roi_handler') and self.roi_handler.roi_coords and len(self.roi_handler.roi_coords) >= 3:
            # Estimate bounding box for polygon for adaptive thresholds
            xs = [pt[0] for pt in self.roi_handler.roi_coords]
            ys = [pt[1] for pt in self.roi_handler.roi_coords]
            roi_width, roi_height = max(xs) - min(xs), max(ys) - min(ys)
            roi_mpx = (roi_width * roi_height) / 1_000_000
        else:
            roi_mpx = image_mpx

        # More granular adaptive thresholds based on region size
        if roi_mpx < 0.1:  # Very small specimens (<0.1 MPx)
            min_density = 20
            max_density = 300
            min_feature_size = 2
            max_feature_size = 10
        elif roi_mpx < 1:  # Small specimens (<1 MPx)
            min_density = 30
            max_density = 200
            min_feature_size = 2
            max_feature_size = 12
        elif roi_mpx < 5:  # Medium specimens
            min_density = 40
            max_density = 150
            min_feature_size = 3
            max_feature_size = 15
        else:  # Large specimens
            min_density = 30
            max_density = 120
            min_feature_size = 3
            max_feature_size = 15

        if results['contrast'] < 20:
            recommendations.append("Increase contrast - pattern is too uniform")
        elif results['contrast'] > 80:
            recommendations.append("Reduce contrast - pattern may be overexposed")

        if results['speckle_density'] < min_density:
            recommendations.append("Increase speckle density - add more features")
        elif results['speckle_density'] > max_density:
            recommendations.append("Reduce speckle density - pattern may be too busy")

        if results['feature_size'] < min_feature_size:
            recommendations.append("Increase feature size - speckles may be too small")
        elif results['feature_size'] > max_feature_size:
            recommendations.append("Reduce feature size - speckles may be too large")

        if results['pattern_uniformity'] < 70:
            recommendations.append("Improve pattern uniformity across the surface")

        if results['noise_level'] < 20:
            recommendations.append("Reduce noise - improve lighting or camera settings")

        if results['overall_score'] >= 80:
            recommendations.append("Excellent pattern quality for DIC analysis!")
        elif results['overall_score'] < 40:
            recommendations.append("Consider recreating the speckle pattern")

        return recommendations