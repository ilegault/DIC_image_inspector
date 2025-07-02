# ui/main_window.py - Clean Architecture Implementation

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, Dict, Any

# Import clean architecture components
from core.image_analyzer import ImageAnalyzer
from core.report_generator import ReportGenerator
from models.analysis_result import AnalysisResult
from models.application_state import ApplicationState
from ui.components.image_canvas import ImageCanvas
from ui.components.control_panel import ControlPanel
from ui.components.roi_selector import ROISelector
from ui.components.legend_panel import LegendPanel
from ui.components.results_popup import ResultsPopup
from ui.dialogs.help_dialog import HelpDialog
from ui.dialogs.screenshot_dialog import ScreenshotDialog
from utils.file_operations import FileOperationsManager
from utils.constants import APP_CONFIG


class DICQualityInspector:
    """
    Main application window - UI coordination only.

    This class handles UI coordination and delegates business logic to appropriate services.
    It follows clean architecture principles with clear separation of concerns.
    """

    def __init__(self, root: tk.Tk):
        """Initialize the main window with clean architecture."""
        self.root = root

        # Initialize services (business logic)
        self.analyzer = ImageAnalyzer()
        self.report_generator = ReportGenerator()
        self.file_operations = FileOperationsManager()

        # Initialize state management
        self.state = ApplicationState()

        # Initialize UI components
        self._setup_window()
        self._create_ui_components()
        self._connect_event_handlers()

        # Set initial state
        self._update_ui_state()
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_window(self):
        """Setup main window properties."""
        self.root.title("DIC Image Quality Inspector v2.0 - Clean Architecture")
        self.root.geometry("1200x800")
        self.root.configure(bg=APP_CONFIG['colors']['background'])
        self.root.minsize(800, 600)

    def _create_ui_components(self):
        """Create and arrange UI components."""
        # Main container
        main_container = tk.Frame(self.root, bg=APP_CONFIG['colors']['background'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Title
        self._create_title_section(main_container)

        # Control panel
        self.control_panel = ControlPanel(
            main_container,
            callbacks={
                'load_image': self.load_image,
                'take_screenshot': self.take_screenshot,
                'select_roi': self.select_roi,
                'analyze_image': self.analyze_image,
                'toggle_quality_map': self.toggle_quality_map,
                'show_results': self.show_results,
                'save_report': self.save_report,
                'show_help': self.show_help,
                'reset_application': self.reset_application,
                'reset_display_results': self.reset_display_results,
                'spectrum_changed': self.on_spectrum_changed
            }
        )

        # Main content area
        content_frame = tk.Frame(main_container, bg=APP_CONFIG['colors']['background'])
        content_frame.pack(fill='both', expand=True, pady=10)

        # Image canvas
        self.image_canvas = ImageCanvas(content_frame)

        # ROI selector
        self.roi_selector = ROISelector(
            self.image_canvas.canvas,
            callbacks={
                'roi_changed': self.on_roi_changed,
                'roi_completed': self.on_roi_completed
            }
        )

        # Legend panel
        self.legend_panel = LegendPanel(content_frame)

        # Status bar
        self._create_status_bar()

    def _create_title_section(self, parent):
        """Create application title section."""
        title_frame = tk.Frame(parent, bg=APP_CONFIG['colors']['background'])
        title_frame.pack(pady=10)

        title_label = tk.Label(
            title_frame,
            text="🔍 DIC Image Quality Inspector v2.0",
            font=('Arial', 24, 'bold'),
            fg=APP_CONFIG['colors']['text_primary'],
            bg=APP_CONFIG['colors']['background']
        )
        title_label.pack()

    def _create_status_bar(self):
        """Create status bar."""
        self.status_var = tk.StringVar(value="Ready - Load an image to begin analysis")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief='sunken',
            anchor='w',
            bg=APP_CONFIG['colors']['status_bar'],
            fg='white'
        )
        status_bar.pack(side='bottom', fill='x')

    def _connect_event_handlers(self):
        """Connect event handlers and observers."""
        # State change observers
        self.state.add_observer('analysis_result', self._on_analysis_result_changed)
        self.state.add_observer('image', self._on_image_changed)
        self.state.add_observer('roi', self._on_roi_changed_state)
        self.state.add_observer('application_state', self._on_app_state_changed)

    def _update_ui_state(self):
        """Update UI components based on current state."""
        app_state = self.state.get_application_state()

        # Update control panel state
        self.control_panel.update_state(app_state)

        # Update status message
        status_messages = {
            'no_image': "Ready - Load an image to begin analysis",
            'image_loaded': "Image loaded - Select ROI for targeted analysis or analyze full image",
            'roi_selected': "ROI selected - Ready for analysis",
            'analyzing': "Analysis in progress - Please wait...",
            'analysis_complete': "Analysis complete - Click 'Show Results' for details"
        }

        if app_state in status_messages:
            self.status_var.set(status_messages[app_state])

    # Event Handlers
    def load_image(self):
        """Handle load image request."""
        try:
            from tkinter import filedialog
            from PIL import Image
            import numpy as np

            filetypes = [
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("All files", "*.*")
            ]

            filepath = filedialog.askopenfilename(
                title="Select Image",
                filetypes=filetypes,
                initialdir=self.file_operations.get_last_directory()
            )

            if filepath:
                # Load image
                pil_image = Image.open(filepath)
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                image_array = np.array(pil_image)

                # Update state
                self.state.set_image(image_array, filepath, "file")
                self.file_operations.set_last_directory(filepath)

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load image: {str(e)}")

    def take_screenshot(self):
        """Handle screenshot request."""
        try:
            # Hide main window temporarily
            self.root.withdraw()

            # Show screenshot dialog
            screenshot_dialog = ScreenshotDialog(
                self.root,
                callback=self._on_screenshot_captured
            )
            screenshot_dialog.show()

        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Screenshot Error", f"Failed to capture screenshot: {str(e)}")

    def _on_screenshot_captured(self, image_data):
        """Handle screenshot capture completion."""
        self.root.deiconify()
        if image_data is not None:
            self.state.set_image(image_data, None, "screenshot")

    def select_roi(self):
        """Handle ROI selection request."""
        if not self.state.has_image():
            messagebox.showwarning("No Image", "Please load an image first")
            return

        self.roi_selector.start_roi_selection()

    def on_roi_changed(self, roi_coords):
        """Handle ROI coordinates change."""
        if roi_coords and len(roi_coords) >= 3:
            self.state.set_roi(roi_coords)

    def on_roi_completed(self, roi_coords):
        """Handle ROI selection completion."""
        if roi_coords and len(roi_coords) >= 3:
            self.state.set_roi(roi_coords)
            self.state.set_application_state('roi_selected')
            # Update ROI info display
            roi_info = f"ROI selected: {len(roi_coords)} points"
            self.control_panel.update_roi_info(roi_info)

    def analyze_image(self):
        """Handle image analysis request."""
        if not self.state.has_image():
            messagebox.showwarning("No Image", "Please load an image first")
            return

        # Update state to analyzing
        self.state.set_application_state('analyzing')

        # Run analysis in background thread
        threading.Thread(target=self._run_analysis, daemon=True).start()

    def _run_analysis(self):
        """Run analysis in background thread."""
        try:
            # Get analysis parameters
            image = self.state.get_image()
            roi = self.state.get_roi()
            spectrum = self.control_panel.get_selected_spectrum()

            # Run analysis using service
            result = self.analyzer.analyze_image(
                image=image,
                roi=roi,
                spectrum_type=spectrum
            )

            # Update state on UI thread
            self.root.after(0, lambda: self._on_analysis_complete(result))

        except Exception as e:
            error_message = str(e)
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self._on_analysis_error(error_message))

    def _on_analysis_complete(self, result: AnalysisResult):
        """Handle analysis completion."""
        self.state.set_analysis_result(result)
        self.state.set_application_state('analysis_complete')

        # Auto-show quality map
        self.root.after(500, self._auto_show_quality_map)

    def _on_analysis_error(self, error_message: str):
        """Handle analysis error."""
        messagebox.showerror("Analysis Error", f"Analysis failed: {error_message}")

        # Revert to previous state
        if self.state.has_roi():
            self.state.set_application_state('roi_selected')
        else:
            self.state.set_application_state('image_loaded')

    def _auto_show_quality_map(self):
        """Auto-show quality map after analysis."""
        if self.state.has_analysis_result():
            result = self.state.get_analysis_result()
            self.image_canvas.show_quality_map(
                result.quality_map,
                self.control_panel.get_selected_spectrum()
            )
            self.legend_panel.show_legend(self.control_panel.get_selected_spectrum())

    def toggle_quality_map(self):
        """Handle quality map toggle request."""
        if not self.state.has_analysis_result():
            messagebox.showwarning("No Analysis", "Please analyze an image first")
            return

        if self.image_canvas.is_showing_quality_map():
            self.image_canvas.show_original()
            self.legend_panel.hide_legend()
        else:
            result = self.state.get_analysis_result()
            self.image_canvas.show_quality_map(
                result.quality_map,
                self.control_panel.get_selected_spectrum()
            )
            self.legend_panel.show_legend(self.control_panel.get_selected_spectrum())

    def show_results(self):
        """Handle show results request."""
        if not self.state.has_analysis_result():
            messagebox.showwarning("No Results", "Please analyze an image first")
            return

        # Show results popup
        try:
            results_popup = ResultsPopup(
                self.root,
                self.state.get_analysis_result(),
                self.report_generator
            )
            results_popup.show()
        except Exception as e:
            messagebox.showerror("Results Error", f"Failed to show results: {str(e)}")

    def save_report(self):
        """Handle save report request."""
        if not self.state.has_analysis_result():
            messagebox.showwarning("No Results", "Please analyze an image first")
            return

        try:
            from tkinter import filedialog

            # Generate comprehensive report
            result = self.state.get_analysis_result()
            report_content = self.report_generator.generate_comprehensive_report(
                result.to_dict(),
                self._get_image_info(),
                self._get_roi_info()
            )

            # Save dialog
            filename = filedialog.asksaveasfilename(
                title="Save Report",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialdir=self.file_operations.get_last_directory()
            )

            if filename:
                success = self.file_operations.save_report_to_file(report_content, filename)
                if success:
                    self.status_var.set("Report saved successfully")
                    messagebox.showinfo("Success", "Report saved successfully!")
                else:
                    messagebox.showerror("Error", "Failed to save report")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save report: {str(e)}")

    def show_help(self):
        """Handle help request."""
        try:
            help_dialog = HelpDialog(self.root)
            help_dialog.show()
        except Exception as e:
            messagebox.showerror("Help Error", f"Failed to show help: {str(e)}")

    def reset_application(self):
        """Handle full application reset request."""
        self.state.reset()
        self.image_canvas.clear()
        self.roi_selector.clear()
        self.legend_panel.hide_legend()
        self.control_panel.update_roi_info("ROI: Not Selected (analyzing full image)")

    def reset_display_results(self):
        """Handle reset display/results request - keeps loaded image."""
        if not self.state.has_image():
            # No image loaded, perform full reset
            self.reset_application()
            return
        
        # Store current image for redisplay
        current_image = self.state.get_image()
        
        # Reset state (keeps image)
        self.state.reset_display_and_results()
        
        # Clear UI components but redisplay the image
        self.roi_selector.clear()
        self.legend_panel.hide_legend()
        self.control_panel.update_roi_info("ROI: Not Selected (analyzing full image)")
        
        # Redisplay the original image (without any overlays)
        if current_image is not None:
            self.image_canvas.display_image(current_image)

    def on_spectrum_changed(self):
        """Handle spectrum selection change."""
        spectrum_type = self.control_panel.get_selected_spectrum()

        if self.state.has_analysis_result() and self.image_canvas.is_showing_quality_map():
            # Update quality map with new spectrum
            result = self.state.get_analysis_result()
            self.image_canvas.show_quality_map(result.quality_map, spectrum_type)
            self.legend_panel.show_legend(spectrum_type)

    # State Change Observers
    def _on_analysis_result_changed(self, result: AnalysisResult):
        """Handle analysis result change."""
        self._update_ui_state()

    def _on_image_changed(self, image_data):
        """Handle image change."""
        if image_data:
            self.image_canvas.display_image(image_data.array)
            self.state.set_application_state('image_loaded')
        else:
            self.image_canvas.clear()
        self._update_ui_state()

    def _on_roi_changed_state(self, roi_data):
        """Handle ROI change."""
        if roi_data:
            self.roi_selector.update_roi_display(roi_data)
            roi_info = f"ROI: {len(roi_data.coordinates)} points, {roi_data.calculate_area():.0f} px²"
            self.control_panel.update_roi_info(roi_info)
        else:
            self.roi_selector.clear()
            self.control_panel.update_roi_info("ROI: Not Selected (analyzing full image)")
        self._update_ui_state()

    def _on_app_state_changed(self, state: str):
        """Handle application state change."""
        self._update_ui_state()

    # Helper Methods
    def _get_image_info(self) -> Optional[Dict[str, Any]]:
        """Get image information for report."""
        return self.state.get_image_info()

    def _get_roi_info(self) -> Optional[Dict[str, Any]]:
        """Get ROI information for report."""
        return self.state.get_roi_info()

    def _on_closing(self):
        """Handle application closing."""
        try:
            # Close main window
            self.root.destroy()
        except Exception as e:
            print(f"Error during application closing: {e}")
            self.root.destroy()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = DICQualityInspector(root)
    root.mainloop()


if __name__ == "__main__":
    main()