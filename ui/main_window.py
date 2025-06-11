import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk, ImageGrab
import os
import threading
import time
from analysis.metrics import analyze_image
from utils.image_processing import get_analysis_region
from ui.image_display import ImageDisplay

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

        self.load_btn = tk.Button(btn_frame, text="📁 Load Image", command=self.load_image,
                                  bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                                  padx=20, pady=5)
        self.load_btn.pack(side='left', padx=5)

        self.screenshot_btn = tk.Button(btn_frame, text="📸 Screen Capture", command=self.start_screenshot,
                                        bg='#e67e22', fg='white', font=('Arial', 12, 'bold'),
                                        padx=20, pady=5)
        self.screenshot_btn.pack(side='left', padx=5)

        self.roi_btn = tk.Button(btn_frame, text="🎯 Select ROI", command=self.toggle_roi_selection,
                                 bg='#9b59b6', fg='white', font=('Arial', 12, 'bold'),
                                 padx=20, pady=5, state='disabled')
        self.roi_btn.pack(side='left', padx=5)

        self.analyze_btn = tk.Button(btn_frame, text="🔬 Analyze", command=self.analyze_image,
                                     bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                     padx=20, pady=5, state='disabled')
        self.analyze_btn.pack(side='left', padx=5)

        self.save_btn = tk.Button(btn_frame, text="💾 Save Report", command=self.save_report,
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

        self.image_canvas.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')

        # Create image display handler
        self.image_display = ImageDisplay(self.image_canvas)
        # Image processing buttons
        process_frame = tk.Frame(left_panel, bg='#34495e')
        process_frame.pack(pady=10)

        tk.Button(process_frame, text="Original", command=self.show_original,
                  bg='#95a5a6', fg='white', padx=10).pack(side='left', padx=2)
        tk.Button(process_frame, text="Edges", command=self.show_edges,
                  bg='#95a5a6', fg='white', padx=10).pack(side='left', padx=2)
        tk.Button(process_frame, text="Gradient", command=self.show_gradient,
                  bg='#95a5a6', fg='white', padx=10).pack(side='left', padx=2)
        tk.Button(process_frame, text="Clear ROI", command=self.clear_roi,
                  bg='#e74c3c', fg='white', padx=10).pack(side='left', padx=2)

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

    def load_image(self):
        """Load image from file"""
        file_types = [
            ('All Supported', '*.png *.jpg *.jpeg *.tiff *.tif *.bmp'),
            ('PNG files', '*.png'),
            ('JPEG files', '*.jpg *.jpeg'),
            ('TIFF files', '*.tiff *.tif'),
            ('All files', '*.*')
        ]

        filename = filedialog.askopenfilename(title="Select DIC Image", filetypes=file_types)
        if filename:
            try:
                self.load_image_from_path(filename)
                self.status_var.set(f"Loaded: {os.path.basename(filename)} - Select ROI for focused analysis")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def load_image_from_path(self, path):
        """Load and display image from file path"""
        # Load with PIL
        pil_image = Image.open(path)

        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Store original
        self.original_image = np.array(pil_image)
        self.current_image = self.original_image.copy()

        # Clear previous ROI
        self.roi_coords = None
        self.update_roi_info()

        # Display image - use the image_display instance
        self.image_display.display_image(pil_image)

        # Enable ROI selection and analysis
        self.roi_btn.config(state='normal')
        self.analyze_btn.config(state='normal')

    def start_screenshot(self):
        """Start screenshot capture process"""
        self.root.withdraw()  # Hide main window

        # Create screenshot window
        screenshot_window = tk.Toplevel()
        screenshot_window.attributes('-fullscreen', True)
        screenshot_window.attributes('-alpha', 0.3)
        screenshot_window.configure(bg='black')
        screenshot_window.attributes('-topmost', True)

        instructions = tk.Label(screenshot_window,
                                text="Click and drag to select area for DIC analysis\nPress ESC to cancel",
                                font=('Arial', 16, 'bold'), fg='white', bg='black')
        instructions.pack(expand=True)

        # Screenshot selection variables
        self.start_x = self.start_y = 0
        self.rect_id = None

        def start_selection(event):
            self.start_x, self.start_y = event.x, event.y
            if self.rect_id:
                screenshot_window.delete(self.rect_id)

        def update_selection(event):
            if self.rect_id:
                screenshot_window.delete(self.rect_id)
            canvas = tk.Canvas(screenshot_window, highlightthickness=0)
            canvas.place(x=0, y=0, relwidth=1, relheight=1)
            self.rect_id = canvas.create_rectangle(self.start_x, self.start_y,
                                                   event.x, event.y, outline='red', width=3)

        def end_selection(event):
            screenshot_window.destroy()
            self.root.deiconify()  # Show main window

            # Capture the selected area
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)

            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:  # Minimum size check
                try:
                    # Capture screenshot
                    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))

                    # Convert to numpy array
                    self.original_image = np.array(screenshot)
                    self.current_image = self.original_image.copy()

                    # Clear previous ROI
                    self.roi_coords = None
                    self.update_roi_info()

                    # Display image
                    self.display_image(screenshot)

                    # Enable ROI selection and analysis
                    self.roi_btn.config(state='normal')
                    self.analyze_btn.config(state='normal')
                    self.status_var.set(f"Screenshot captured: {x2 - x1}x{y2 - y1} pixels - Select ROI for analysis")

                except Exception as e:
                    messagebox.showerror("Error", f"Failed to capture screenshot: {str(e)}")
            else:
                self.status_var.set("Screenshot cancelled - area too small")

        def cancel_screenshot(event):
            screenshot_window.destroy()
            self.root.deiconify()
            self.status_var.set("Screenshot cancelled")

        # Bind events
        screenshot_window.bind('<Button-1>', start_selection)
        screenshot_window.bind('<B1-Motion>', update_selection)
        screenshot_window.bind('<ButtonRelease-1>', end_selection)
        screenshot_window.bind('<Escape>', cancel_screenshot)
        screenshot_window.focus_set()

    def toggle_roi_selection(self):
        """Toggle ROI selection mode"""
        self.roi_selection_mode = not self.roi_selection_mode
        if self.roi_selection_mode:
            self.roi_btn.config(text="🎯 ROI Mode ON", bg='#e74c3c')
            self.status_var.set("ROI Selection Mode: Click and drag on image to select analysis region")
        else:
            self.roi_btn.config(text="🎯 Select ROI", bg='#9b59b6')
            self.status_var.set("ROI Selection Mode OFF")

    def update_roi_info(self):
        """Update ROI information display"""
        if self.roi_coords:
            x1, y1, x2, y2 = self.roi_coords
            self.roi_info_label.config(text=f"ROI: {x2 - x1}x{y2 - y1} pixels at ({x1},{y1})")
        else:
            self.roi_info_label.config(text="ROI: Not Selected (analyzing full image)")

    def analyze_image(self):
        """Analyze image quality for DIC"""
        if self.original_image is None:
            return

        if self.roi_coords:
            self.status_var.set("Analyzing ROI for DIC quality...")
        else:
            self.status_var.set("Analyzing full image for DIC quality...")

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
            ("Gradient Strength", results['gradient_magnitude'], "", "Higher is better"),
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

    def _generate_recommendations(self, results):
        """Generate recommendations based on analysis results"""
        recommendations = []

        if results['contrast'] < 20:
            recommendations.append("Increase contrast - pattern is too uniform")
        elif results['contrast'] > 80:
            recommendations.append("Reduce contrast - pattern may be overexposed")

        if results['speckle_density'] < 50:
            recommendations.append("Increase speckle density - add more features")
        elif results['speckle_density'] > 200:
            recommendations.append("Reduce speckle density - pattern may be too busy")

        if results['feature_size'] < 3:
            recommendations.append("Increase feature size - speckles may be too small")
        elif results['feature_size'] > 15:
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

    def save_report(self):
        """Save analysis report to file"""
        if not self.analysis_results:
            messagebox.showwarning("No Data", "No analysis results to save")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Analysis Report"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("DIC Image Quality Analysis Report\n")
                    f.write("=" * 50 + "\n\n")

                    # ROI information
                    if self.roi_coords:
                        x1, y1, x2, y2 = self.roi_coords
                        f.write(f"Region of Interest: {x2 - x1}x{y2 - y1} pixels at ({x1},{y1})\n")
                    else:
                        f.write("Analysis Region: Full image\n")
                    f.write("\n")

                    # Results
                    results = self.analysis_results
                    f.write(f"Overall Score: {results['overall_score']}/100\n\n")

                    f.write("Detailed Metrics:\n")
                    f.write("-" * 20 + "\n")
                    f.write(f"Contrast: {results['contrast']}%\n")
                    f.write(f"Speckle Density: {results['speckle_density']} features/Mpx\n")
                    f.write(f"Gradient Strength: {results['gradient_magnitude']}\n")
                    f.write(f"Noise Level (SNR): {results['noise_level']} dB\n")
                    f.write(f"Pattern Uniformity: {results['pattern_uniformity']}%\n")
                    f.write(f"Feature Size: {results['feature_size']} pixels\n")
                    f.write(f"Intensity Distribution: {results['intensity_distribution']}%\n")
                    f.write(f"Edge Quality: {results['edge_quality']}%\n\n")

                    # Recommendations
                    recommendations = self._generate_recommendations(results)
                    if recommendations:
                        f.write("Recommendations:\n")
                        f.write("-" * 20 + "\n")
                        for rec in recommendations:
                            f.write(f"• {rec}\n")

                self.status_var.set(f"Report saved: {os.path.basename(filename)}")

            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save report: {str(e)}")

    def _analyze_worker(self):
        """Worker thread to perform image analysis"""
        try:
            # Get the image to analyze
            analysis_region = get_analysis_region(self.original_image, self.roi_coords)

            # Perform analysis
            results = analyze_image(analysis_region)

            # Store results
            self.analysis_results = results

            # Update GUI on main thread
            self.root.after(0, self._update_results_display)

        except Exception as e:
            # Show error in GUI thread
            self.root.after(0, lambda: messagebox.showerror("Analysis Error", f"Failed to analyze image: {str(e)}"))

        finally:
            # Re-enable analyze button in GUI thread
            self.root.after(0, lambda: self.analyze_btn.config(state='normal'))

    def show_original(self):
        """Show the original image."""
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            pil_image = Image.fromarray(self.current_image)
            self.image_display.display_image(pil_image)

    def show_edges(self):
        """Show edge-enhanced image."""
        if self.original_image is not None:
            # Get analysis region
            analysis_region = get_analysis_region(self.original_image, self.roi_coords)

            # Convert to grayscale
            if len(analysis_region.shape) == 3:
                gray = cv2.cvtColor(analysis_region, cv2.COLOR_RGB2GRAY)
            else:
                gray = analysis_region

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Convert back to RGB for display
            edge_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

            # If ROI is selected, create a composite image
            if self.roi_coords:
                composite = self.original_image.copy()
                x1, y1, x2, y2 = self.roi_coords
                composite[y1:y2, x1:x2] = edge_rgb
                self.current_image = composite
            else:
                self.current_image = edge_rgb

            # Display the processed image
            pil_image = Image.fromarray(self.current_image)
            self.image_display.display_image(pil_image)

    def show_gradient(self):
        """Show gradient magnitude image."""
        if self.original_image is not None:
            # Get analysis region
            analysis_region = get_analysis_region(self.original_image, self.roi_coords)

            # Convert to grayscale
            if len(analysis_region.shape) == 3:
                gray = cv2.cvtColor(analysis_region, cv2.COLOR_RGB2GRAY)
            else:
                gray = analysis_region

            # Calculate gradient
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

            # Normalize to 0-255
            gradient_normalized = cv2.normalize(gradient_magnitude, None, 0, 255, cv2.NORM_MINMAX)
            gradient_normalized = gradient_normalized.astype(np.uint8)

            # Convert to RGB
            gradient_rgb = cv2.cvtColor(gradient_normalized, cv2.COLOR_GRAY2RGB)

            # If we have ROI, create a composite image
            if self.roi_coords:
                composite = self.original_image.copy()
                x1, y1, x2, y2 = self.roi_coords
                composite[y1:y2, x1:x2] = gradient_rgb
                self.current_image = composite
            else:
                self.current_image = gradient_rgb

            pil_image = Image.fromarray(self.current_image)
            self.image_display.display_image(pil_image)

    def clear_roi(self):
        """Clear the current ROI selection"""
        self.roi_coords = None
        if self.roi_rect:
            self.image_canvas.delete(self.roi_rect)
            self.roi_rect = None
        self.update_roi_info()
        self.status_var.set("ROI cleared - will analyze full image")
