
# analysis.file_operations.py
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk, ImageGrab
import os

class FileOperations:
    def __init__(self, main_window):
        """Initialize with a reference to the main window"""
        self.main_window = main_window

    def load_image(self):
        """Load an image from file"""
        filetypes = [
            ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff"),
            ("All files", "*.*")
        ]

        filename = filedialog.askopenfilename(title="Select Image File", filetypes=filetypes)

        if filename:
            try:
                # Reset analysis results and quality map data when loading a new image
                self.main_window.analysis_results = {}
                if hasattr(self.main_window.image_display, 'quality_map_data'):
                    self.main_window.image_display.quality_map_data = None
                    self.main_window.image_display.quality_visualization = None
                    self.main_window.image_display.showing_quality_overlay = False

                # Disable the quality map button until analysis is performed
                self.main_window.quality_map_btn.config(state='disabled')

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

        # Clear previous ROI
        self.main_window.roi_coords = None
        self.main_window.roi_handler.update_roi_info()  # Use the ROI handler's method

        # Display image
        self.main_window.image_display.display_image(pil_image)

        # Enable ROI selection and analysis
        self.main_window.roi_btn.config(state='normal')
        self.main_window.analyze_btn.config(state='normal')

    def save_report(self):
        """Save analysis report to file"""
        if not self.main_window.analysis_results:
            messagebox.showwarning("No Data", "No analysis results to save")
            return

        # Rest of the save_report method...
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
                    if self.main_window.roi_coords:
                        x1, y1, x2, y2 = self.main_window.roi_coords
                        f.write(f"Region of Interest: {x2 - x1}x{y2 - y1} pixels at ({x1},{y1})\n")
                    else:
                        f.write("Analysis Region: Full image\n")
                    f.write("\n")

                    # Results
                    results = self.main_window.analysis_results
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
                    recommendations = self.main_window._generate_recommendations(results)
                    if recommendations:
                        f.write("Recommendations:\n")
                        f.write("-" * 20 + "\n")
                        for rec in recommendations:
                            f.write(f"• {rec}\n")

                self.main_window.status_var.set(f"Report saved: {os.path.basename(filename)}")

            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save report: {str(e)}")
