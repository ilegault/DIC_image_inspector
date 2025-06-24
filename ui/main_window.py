# module: ui.main_window

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from PIL import ImageGrab
import threading
from ui.image_display import ImageDisplay
from ui.roi_handler import ROIHandler
from ui.file_operations import FileOperations
from analysis.utils.image_processing import get_analysis_region
from analysis.quality_map.map_generator import generate_quality_map
from analysis.analyzer import DICAnalyzer
from debug_output.enhanced_debug_integration import integrate_blur_awareness_into_existing_analyzer


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

        # Connect UI elements to manager methods
        self.load_btn.config(command=self.file_operations.load_image)
        self.roi_btn.config(command=self.roi_handler.toggle_roi_selection)
        self.screenshot_btn.config(command=self.start_screenshot)
        self.analyze_btn.config(command=self.analyze_image)
        self.quality_map_btn.config(command=self.image_display.toggle_quality_map_overlay)
        self.quality_map_btn.config(state='disabled')

        integrate_blur_awareness_into_existing_analyzer(self)



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

        # Change the positioning of components
        self.image_canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid weights to make the canvas expand
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Image processing buttons
        process_frame = tk.Frame(left_panel, bg='#34495e')
        process_frame.pack(pady=10)

        # Add this to the btn_frame in create_gui method
        self.help_btn = tk.Button(btn_frame, text="❓ Help",
                                  bg="#7f8c8d", fg="white", font=("Arial", 12, "bold"),
                                  padx=10, pady=5, command=self.show_help)
        self.help_btn.pack(side="left", padx=5)

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

        self.quality_map_btn = tk.Button(process_frame, text="Quality Map",
                                         bg='#2ecc71', fg='white', padx=10)
        self.quality_map_btn.pack(side='left', padx=2)

        self.debug_btn = tk.Button(
            btn_frame,  # Using the correct variable name
            text="🐞 Debug ROI",
            command=lambda: self.image_display.save_debug_visualizations(),
            bg="#ffcc00",  # Yellow for debug
            fg="black",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=5,
            state='disabled'  # Initially disabled until ROI is selected
        )
        self.debug_btn.pack(side='left', padx=5)

        self.quality_map_btn.config(state='disabled')

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
                    self.roi_coords = None
                    self.roi_handler.update_roi_info()

                    # Use same approach as load_image_from_path
                    self.image_display.display_image(screenshot)

                    # Reset view position
                    self.image_canvas.xview_moveto(0)
                    self.image_canvas.yview_moveto(0)

                    # Enable buttons
                    self.roi_btn.config(state='normal')
                    self.analyze_btn.config(state='normal')
                    self.status_var.set(f"Screenshot captured: {screenshot.width}x{screenshot.height} pixels")
                    self.quality_map_btn.config(state='normal')


                except Exception as e:
                    self.root.deiconify()
                    messagebox.showerror("Error", f"Failed to capture screenshot: {str(e)}")
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

    def analyze_image(self):
        """Analyze image quality for DIC and show quality map"""
        if self.original_image is None:
            return

        if self.roi_coords:
            self.status_var.set("Analyzing ROI for DIC quality...")
            self.roi_btn.config(state='disabled')
        else:
            self.status_var.set("Analyzing full image for DIC quality...")
            self.roi_btn.config(state='disabled')
        self.analyze_btn.config(state='disabled')

        # Run analysis in separate thread to prevent GUI freezing
        threading.Thread(target=self._analyze_worker, daemon=True).start()

    def _update_results_display(self):
        """Update the GUI with analysis results"""
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not self.analysis_results:
            return

        results = self.analysis_results

        # Overall Score (prominent display)
        score_frame = tk.Frame(self.results_frame, bg='#34495e', relief='raised', bd=2)
        score_frame.pack(fill='x', padx=10, pady=10)

        overall_score = results['overall_score']

        # Color code the score
        if overall_score >= 80:
            score_color = '#27ae60'  # Green
            score_text = "Excellent"
        elif overall_score >= 60:
            score_color = '#f39c12'  # Orange
            score_text = "Good"
        elif overall_score >= 40:
            score_color = '#e67e22'  # Dark Orange
            score_text = "Fair"
        else:
            score_color = '#e74c3c'  # Red
            score_text = "Poor"

        tk.Label(score_frame, text="Overall DIC Quality Score",
                 font=('Arial', 14, 'bold'), fg='#ecf0f1', bg='#34495e').pack()
        tk.Label(score_frame, text=f"{overall_score}/100",
                 font=('Arial', 24, 'bold'), fg=score_color, bg='#34495e').pack()
        tk.Label(score_frame, text=score_text,
                 font=('Arial', 12), fg=score_color, bg='#34495e').pack()

        # Detailed metrics
        metrics_frame = tk.Frame(self.results_frame, bg='#34495e')
        metrics_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(metrics_frame, text="Detailed Analysis",
                 font=('Arial', 14, 'bold'), fg='#ecf0f1', bg='#34495e').pack()

        # Create metric displays
        metrics = [
            ("Contrast", results['contrast'], "%", "Optimal: 20-80%"),
            ("Speckle Density", results['speckle_density'], " features/Mpx", "Good: 50-200"),
            ("Gradient Strength", results['gradient_magnitude'], "", "Good: >30, Excellent: >50"),
            ("Noise Level (SNR)", results['noise_level'], " dB", "Good: >20 dB"),
            ("Pattern Uniformity", results['pattern_uniformity'], "%", "Good: >70%"),
            ("Feature Size", results['feature_size'], " pixels", "Optimal: 3-15 px"),
            ("Intensity Distribution", results['intensity_distribution'], "%", "Good: >60%"),
            ("Edge Quality", results['edge_quality'], "%", "Good: >50%")
        ]

        for name, value, unit, guidance in metrics:
            metric_frame = tk.Frame(metrics_frame, bg='#34495e')
            metric_frame.pack(fill='x', pady=2)

            tk.Label(metric_frame, text=f"{name}:",
                     font=('Arial', 10, 'bold'), fg='#bdc3c7', bg='#34495e', width=20, anchor='w').pack(side='left')
            tk.Label(metric_frame, text=f"{value}{unit}",
                     font=('Arial', 10), fg='#ecf0f1', bg='#34495e', width=15, anchor='w').pack(side='left')
            tk.Label(metric_frame, text=guidance,
                     font=('Arial', 8), fg='#95a5a6', bg='#34495e', anchor='w').pack(side='left')

        # Recommendations
        recommendations = self._generate_recommendations(results)
        if recommendations:
            rec_frame = tk.Frame(self.results_frame, bg='#34495e', relief='raised', bd=2)
            rec_frame.pack(fill='x', padx=10, pady=10)

            tk.Label(rec_frame, text="📋 Recommendations",
                     font=('Arial', 12, 'bold'), fg='#ecf0f1', bg='#34495e').pack()

            for rec in recommendations:
                tk.Label(rec_frame, text=f"• {rec}",
                         font=('Arial', 9), fg='#bdc3c7', bg='#34495e',
                         wraplength=350, justify='left').pack(anchor='w', padx=10)

        # Re-enable buttons
        self.analyze_btn.config(state='normal')
        self.save_btn.config(state='normal')

        # Update status
        roi_text = "ROI" if self.roi_coords else "full image"
        self.status_var.set(f"Analysis complete - Overall score: {overall_score}/100 ({roi_text})")

    def _update_results_display_and_show_map(self, results=None, preserve_view=False, zoom_level=None, x_view=None, y_view=None):
        """Update the results display and show quality map

        Args:
            results: The analysis results to display
            preserve_view: Whether to preserve current view position
            zoom_level: Current zoom level to restore
            x_view: X view position to restore
            y_view: Y view position to restore
        """
        # First update the results display with the provided results
        if results:
            self.analysis_results = results

        # Update the results panel
        self._update_results_display()

        # Get the image to analyze
        analysis_region = get_analysis_region(
            self.original_image,
            self.roi_handler.roi_coords if hasattr(self, 'roi_handler') else None
        )

        # Generate and show quality map
        quality_map, visualization = generate_quality_map(analysis_region)

        # Display the quality map
        self.image_display.show_quality_map()

    def _analyze_worker(self):
        """Worker thread to perform image analysis"""
        try:
            # Store current view state before analysis
            current_zoom = self.image_display.zoom_level
            visible_x = self.image_canvas.xview()
            visible_y = self.image_canvas.yview()

            # Get the analysis region (ROI or full image)
            analysis_region = get_analysis_region(self.original_image, self.roi_handler.roi_coords)

            # Print original and analysis region dimensions for debugging
            print(f"DEBUG: Original image shape: {self.original_image.shape}")
            print(f"DEBUG: Analysis region shape: {analysis_region.shape}")

            # Generate quality map based on analysis region
            quality_map, visualization = generate_quality_map(analysis_region)

            # Store quality map data for later use
            self.image_display.quality_map_data = quality_map
            self.image_display.quality_visualization = visualization

            # Use the DICAnalyzer class for analysis
            analyzer = DICAnalyzer()
            results = analyzer.analyze(analysis_region)

            # Store results
            self.analysis_results = results

            # Update GUI on the main thread
            self.root.after(0, lambda: self._update_results_display())

            # Enable the quality map button after successful analysis
            self.root.after(0, lambda: self.quality_map_btn.config(state='normal'))

            # Show quality map after updating results
            self.root.after(100, lambda: self.image_display.show_quality_map())

        except Exception as e:
            import traceback
            error_message = str(e)
            traceback_info = traceback.format_exc()
            print(f"Analysis Error: {error_message}\n{traceback_info}")  # Debug information
            self.root.after(0, lambda msg=error_message: messagebox.showerror(
                "Analysis Error", f"Failed to analyze image: {msg}"))

        finally:
            # Re-enable analyze button in GUI thread
            self.root.after(0, lambda: self.analyze_btn.config(state='normal'))

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
      - Clear the current ROI with the "Clear ROI" button

    • Image Navigation:
      - Zoom: Use the mouse wheel to zoom in/out
      - Pan: Hold Ctrl + click and drag to move around
      - Reset View: Click "Reset View" to return to original view

    • Image Processing:
      - Original: Return to the unprocessed image
      - Edges: Display edge detection visualization
      - Gradient: Display gradient magnitude visualization

    • Analysis:
      - Click "Analyze" to process the image quality metrics
      - Results are shown in the right panel
      - Higher overall scores indicate better DIC pattern quality
      - Recommendations provide guidance to improve your pattern

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
        if hasattr(self, 'roi_handler') and self.roi_handler.roi_coords:
            x1, y1, x2, y2 = self.roi_handler.roi_coords
            roi_width, roi_height = x2 - x1, y2 - y1
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