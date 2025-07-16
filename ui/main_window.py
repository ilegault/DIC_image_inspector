# main_window.py - Updated Main Window with Theme Support

import tkinter as tk
from tkinter import messagebox, filedialog, ttk

from typing import Optional, Dict, Any

import threading
import numpy as np
from PIL import Image
import logging

from ui.components.control_panel import ControlPanel
from ui.components.image_canvas import ImageCanvas
from ui.components.roi_selector import ROISelector
from ui.components.legend_panel import LegendPanel
from ui.components.results_popup import ResultsPopup
from ui.dialogs.help_dialog import HelpDialog
from ui.dialogs.screenshot_dialog import ScreenshotDialog

from models.application_state import ApplicationState
from models.analysis_result import AnalysisResult
from core.image_analyzer import ImageAnalyzer
from core.report_generator import ReportGenerator
from utils.file_operations import FileOperationsManager

from utils.constants import APP_CONFIG, get_theme_colors
from utils.modern_styling import ModernStyleManager

logger = logging.getLogger(__name__)


class DICQualityInspector:
    """
    Main application window for DIC Image Quality Inspector.

    Orchestrates all UI components and manages application flow.
    """

    def __init__(self, root: tk.Tk):
        """Initialize the main application window."""
        self.root = root
        self.root.title("DIC Image Quality Inspector")

        # Set initial window size and position
        self._setup_window()

        # Initialize state management
        self.state = ApplicationState()

        # Initialize components
        self.control_panel = None
        self.image_canvas = None
        self.roi_selector = None
        self.legend_panel = None
        self.results_popup = None

        # Initialize services
        logger.info("Initializing application services...")
        self.file_operations = FileOperationsManager()
        self.analyzer = ImageAnalyzer()
        self.report_generator = ReportGenerator()
        logger.info("Application services initialized successfully")

        # Style manager
        self.style_manager = ModernStyleManager()

        # Create UI
        self._create_ui()

        # Connect event handlers
        self._connect_event_handlers()

        # Set initial state
        self.state.set_application_state('no_image')
        self._update_ui_state()

        # Status variable
        self.status_var = tk.StringVar(value="Ready - Load an image to begin analysis")

    def _setup_window(self):
        """Configure main window properties."""
        # Get screen dimensions for 1/4 size calculation
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate 1/4 screen size (approximately)
        window_width = int(screen_width * 0.5)  # Half width for better usability
        window_height = int(screen_height * 0.6)  # 60% height for better aspect ratio

        # Set window size
        self.root.geometry(f"{window_width}x{window_height}")

        # Center window on screen
        self.root.update_idletasks()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Set minimum size (much smaller for compact app)
        self.root.minsize(800, 500)

        # Configure grid weights for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Apply theme colors
        self._apply_theme()

    def _apply_theme(self):
        """Apply current theme to window."""
        colors = get_theme_colors()
        self.root.configure(bg=colors['background'])

        # Configure ttk style for the entire application
        style = ttk.Style()

        # Set the theme based on current mode
        if APP_CONFIG['theme'] == 'dark':
            # Try to use a dark theme if available
            try:
                available_themes = style.theme_names()
                if 'equilux' in available_themes:
                    style.theme_use('equilux')
                elif 'alt' in available_themes:
                    style.theme_use('alt')
                else:
                    style.theme_use('default')
            except:
                style.theme_use('default')
        else:
            # Use default theme for light mode
            try:
                style.theme_use('vista' if 'vista' in style.theme_names() else 'default')
            except:
                style.theme_use('default')

        # Apply comprehensive styling
        self._apply_comprehensive_styling(style, colors)

        # Update window styling for Windows
        try:
            if tk.sys.platform == 'win32':
                import ctypes
                # Enable dark title bar on Windows
                if APP_CONFIG['theme'] == 'dark':
                    self.root.update()
                    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
                    hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                    value = ctypes.c_int(1)
                    set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                                         ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass  # Ignore if dark mode setting fails

    def _apply_comprehensive_styling(self, style, colors):
        """Apply comprehensive styling to all ttk widgets."""
        try:
            # Configure all ttk widgets with theme colors

            # Combobox styling with proper text color handling
            style.configure('TCombobox',
                fieldbackground=colors['canvas_bg'],
                background=colors['panel_bg'],
                foreground=colors['text_primary'],
                borderwidth=1,
                relief='flat',
                arrowcolor=colors['text_primary'],
                insertcolor=colors['text_primary']
            )

            style.map('TCombobox',
                fieldbackground=[
                    ('readonly', colors['canvas_bg']),
                    ('focus', colors['canvas_bg']),
                    ('active', colors['canvas_bg'])
                ],
                foreground=[
                    ('readonly', colors['text_primary']),
                    ('focus', colors['text_primary']),
                    ('active', colors['text_primary'])
                ],
                selectbackground=[('readonly', colors['selected_bg'])],
                selectforeground=[('readonly', colors['text_primary'])],
                background=[('active', colors['hover_bg'])],
                arrowcolor=[
                    ('active', colors['text_primary']),
                    ('focus', colors['text_primary']),
                    ('readonly', colors['text_primary'])
                ]
            )

            # Scrollbar styling
            style.configure('Vertical.TScrollbar',
                background=colors['panel_bg'],
                troughcolor=colors['hover_bg'],
                borderwidth=0,
                arrowcolor=colors['text_secondary'],
                darkcolor=colors['panel_bg'],
                lightcolor=colors['panel_bg']
            )

            style.map('Vertical.TScrollbar',
                background=[('active', colors['selected_bg']), ('pressed', colors['primary'])],
                arrowcolor=[('active', colors['text_primary'])]
            )

            style.configure('Horizontal.TScrollbar',
                background=colors['panel_bg'],
                troughcolor=colors['hover_bg'],
                borderwidth=0,
                arrowcolor=colors['text_secondary'],
                darkcolor=colors['panel_bg'],
                lightcolor=colors['panel_bg']
            )

            style.map('Horizontal.TScrollbar',
                background=[('active', colors['selected_bg']), ('pressed', colors['primary'])],
                arrowcolor=[('active', colors['text_primary'])]
            )

            # Frame styling
            style.configure('TFrame',
                background=colors['panel_bg'],
                borderwidth=0,
                relief='flat'
            )

            # Label styling
            style.configure('TLabel',
                background=colors['panel_bg'],
                foreground=colors['text_primary']
            )

            # Button styling
            style.configure('TButton',
                background=colors['btn_primary'],
                foreground='white',
                borderwidth=0,
                relief='flat'
            )

            style.map('TButton',
                background=[('active', colors['btn_primary_hover']), ('pressed', colors['btn_primary_hover'])],
                foreground=[('active', 'white'), ('pressed', 'white')]
            )

            # Entry styling
            style.configure('TEntry',
                fieldbackground=colors['canvas_bg'],
                background=colors['panel_bg'],
                foreground=colors['text_primary'],
                borderwidth=1,
                relief='flat'
            )

            # Spinbox styling
            style.configure('TSpinbox',
                fieldbackground=colors['canvas_bg'],
                background=colors['panel_bg'],
                foreground=colors['text_primary'],
                borderwidth=1,
                relief='flat',
                arrowcolor=colors['text_primary']
            )

        except Exception as e:
            print(f"Warning: Could not apply comprehensive styling: {e}")

    def _create_ui(self):
        """Create the main UI layout."""
        colors = get_theme_colors()

        # Main container
        main_container = tk.Frame(self.root, bg=colors['background'])
        main_container.pack(fill='both', expand=True)

        # Create header
        self._create_header(main_container)

        # Create content area (reduced padding for compact design)
        content_frame = tk.Frame(main_container, bg=colors['background'])
        content_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        # Left panel - Control Panel (reduced width with better spacing)
        left_panel = tk.Frame(content_frame, bg=colors['background'], width=310)
        left_panel.pack(side='left', fill='y', padx=(0, 20))
        left_panel.pack_propagate(False)

        # Create control panel with callbacks
        control_callbacks = {
            'load_image': self.load_image,
            'take_screenshot': self.take_screenshot,
            'select_roi': self.select_roi,
            'analyze_image': self.analyze_image,
            'toggle_quality_map': self.toggle_quality_map,
            'show_results': self.show_results,
            'save_report': self.save_report,
            'show_help': self.show_help,
            'reset_application': self.reset_application,
            'reset_display_results': self.reset_display,
            'toggle_theme': self.toggle_theme,
            'spectrum_changed': self.on_spectrum_changed,
            'zoom_in': self.zoom_in,
            'zoom_out': self.zoom_out,
            'zoom_actual': self.zoom_actual
        }

        self.control_panel = ControlPanel(left_panel, control_callbacks)

        # Right panel - Image Display
        right_panel = tk.Frame(content_frame, bg=colors['panel_bg'], relief='flat', bd=0)
        right_panel.pack(side='left', fill='both', expand=True)

        # Create image canvas with zoom callback
        canvas_callbacks = {
            'zoom_changed': self._on_zoom_changed
        }
        self.image_canvas = ImageCanvas(right_panel, canvas_callbacks)

        # Create ROI selector
        roi_callbacks = {
            'roi_changed': self.on_roi_changed,
            'roi_completed': self.on_roi_completed
        }
        self.roi_selector = ROISelector(self.image_canvas.canvas, roi_callbacks)

        # Create legend panel (initially on image canvas parent)
        self.legend_panel = LegendPanel(right_panel)

        # Create status bar
        self._create_status_bar()

    def _create_header(self, parent):
        """Create application header with title."""
        colors = get_theme_colors()

        # Compact title container
        title_container = tk.Frame(
            parent,
            bg=colors['panel_bg'],
            relief='flat',
            bd=0
        )
        title_container.pack(fill='x', pady=(0, 8))

        # Add subtle border
        border = tk.Frame(title_container, bg=colors['panel_border'], height=1)
        border.pack(side='bottom', fill='x')

        # Horizontal layout for compact title (reduced padding)
        title_frame = tk.Frame(title_container, bg=colors['panel_bg'])
        title_frame.pack(fill='x', padx=15, pady=10)

        # Application title (compact version)
        title_label = tk.Label(
            title_frame,
            text=" DIC Quality Inspector v2.0",
            font=APP_CONFIG['fonts']['subheading'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        title_label.pack(side='left')

        # Subtitle (shorter for compact design)
        subtitle_label = tk.Label(
            title_frame,
            text="• Digital Image Correlation Analysis",
            font=APP_CONFIG['fonts']['small'],
            fg=colors['text_secondary'],
            bg=colors['panel_bg']
        )
        subtitle_label.pack(side='left', padx=(8, 0))

    def _create_status_bar(self):
        """Create modern status bar."""
        colors = get_theme_colors()

        # Status bar container,
        status_container = tk.Frame(
            self.root,
            bg=colors['panel_bg'],
            relief='flat',
            bd=0
        )
        status_container.pack(side='bottom', fill='x')

        # Add top border
        border_frame = tk.Frame(
            status_container,
            bg=colors['panel_border'],
            height=1
        )
        border_frame.pack(fill='x', side='top')

        # Status bar with modern styling
        self.status_var = tk.StringVar(value="Ready - Load an image to begin analysis")
        status_bar = tk.Label(
            status_container,
            textvariable=self.status_var,
            relief='flat',
            anchor='w',
            bg=colors['panel_bg'],
            fg=colors['text_secondary'],
            font=APP_CONFIG['fonts']['status'],
            padx=20,
            pady=8
        )
        status_bar.pack(fill='x')

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        # Theme toggling is handled in control panel
        # Refresh entire UI
        self._refresh_ui_theme()

    def _refresh_ui_theme(self):
        """Refresh UI with new theme colors."""
        # Apply new theme to window
        self._apply_theme()

        # Get new colors
        colors = get_theme_colors()

        # Update all frames recursively
        self._update_widget_theme(self.root, colors)

        # Update specific components
        if self.control_panel:
            self.control_panel.refresh_theme()

        if self.image_canvas:
            self.image_canvas.refresh_theme()

        if self.legend_panel:
            self.legend_panel.refresh_theme()

        # Refresh style manager to update ttk styles
        self.style_manager = ModernStyleManager()

        # Re-show quality map if active
        if self.state.has_analysis_result() and self.image_canvas.is_showing_quality_map():
            result = self.state.get_analysis_result()
            spectrum = self.control_panel.get_selected_spectrum()
            self.image_canvas.show_quality_map(result.quality_map, spectrum)
            self.legend_panel.show_legend(spectrum)

    def _update_widget_theme(self, widget, colors):
        """Recursively update widget colors for theme."""
        try:
            # Skip ttk widgets as they're handled by ttk styling
            if isinstance(widget, (ttk.Widget,)):
                return

            # Update widget background and foreground
            if hasattr(widget, 'configure') and hasattr(widget, 'cget'):
                widget_type = type(widget).__name__

                # Get current background to determine what type of widget this is
                try:
                    current_bg = widget.cget('bg')
                except:
                    current_bg = None

                # Handle different widget types based on their current background
                if isinstance(widget, tk.Frame):
                    # Determine frame type by current background
                    if current_bg in [colors.get('background'), '#f8fafc', '#0f172a']:
                        widget.configure(bg=colors['background'])
                    elif current_bg in [colors.get('hover_bg'), '#f3f4f6', '#374151']:
                        widget.configure(bg=colors['hover_bg'])
                    else:
                        widget.configure(bg=colors['panel_bg'])

                elif isinstance(widget, tk.Label):
                    # Get parent background to match
                    try:
                        parent_bg = widget.master.cget('bg')
                        widget.configure(bg=parent_bg, fg=colors['text_primary'])
                    except:
                        widget.configure(bg=colors['panel_bg'], fg=colors['text_primary'])

                elif isinstance(widget, tk.Button):
                    # Only update if it's not a custom styled button
                    if not hasattr(widget, '_custom_styled'):
                        # Check if it's a primary button by color
                        if current_bg in ['#3b82f6', '#2563eb']:
                            widget.configure(
                                bg=colors['btn_primary'],
                                fg='white',
                                activebackground=colors['btn_primary_hover'],
                                activeforeground='white'
                            )
                        else:
                            # Keep the button's original styling but update text
                            try:
                                widget.configure(fg=colors['text_primary'])
                            except:
                                pass

                elif isinstance(widget, (tk.Entry, tk.Text)):
                    widget.configure(
                        bg=colors['canvas_bg'],
                        fg=colors['text_primary'],
                        insertbackground=colors['text_primary']
                    )

                elif isinstance(widget, tk.Listbox):
                    widget.configure(
                        bg=colors['canvas_bg'],
                        fg=colors['text_primary'],
                        selectbackground=colors['selected_bg'],
                        selectforeground=colors['text_primary']
                    )

                elif isinstance(widget, tk.Canvas):
                    widget.configure(bg=colors['canvas_bg'])

                elif isinstance(widget, tk.Spinbox):
                    widget.configure(
                        bg=colors['canvas_bg'],
                        fg=colors['text_primary'],
                        buttonbackground=colors['panel_bg'],
                        insertbackground=colors['text_primary']
                    )

            # Recursively update children
            for child in widget.winfo_children():
                self._update_widget_theme(child, colors)

        except Exception as e:
            pass  # Skip widgets that can't be updated

    def _connect_event_handlers(self):
        """Connect event handlers and observers."""
        # State observers
        self.state.add_observer('image', self._on_image_changed)
        self.state.add_observer('roi', self._on_roi_changed_state)
        self.state.add_observer('analysis_result', self._on_analysis_result_changed)
        self.state.add_observer('application_state', self._on_app_state_changed)

        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _update_ui_state(self):
        """Update UI components based on current state."""
        state = self.state.get_application_state()
        self.control_panel.update_state(state)

        # Update status bar
        status_messages = {
            'no_image': "Ready - Load an image to begin analysis",
            'image_loaded': "Image loaded - Select ROI or analyze full image",
            'roi_selected': "ROI selected - Ready for analysis",
            'analyzing': "Analyzing image quality...",
            'analysis_complete': "Analysis complete - View results or adjust settings"
        }

        self.status_var.set(status_messages.get(state, "Ready"))

    # Rest of the methods remain the same...
    def load_image(self):
        """Handle load image request."""
        try:
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
                # Load image using file operations
                image_array = self.file_operations.load_image_from_file(filepath)

                if image_array is not None:
                    self.state.set_image(image_array, filepath, "file")
                    self.state.clear_roi()
                    self.state.clear_analysis_result()
                else:
                    messagebox.showerror("Load Error", "Failed to load image file")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load image: {str(e)}")

    def take_screenshot(self):
        """Handle screenshot request."""
        try:
            # Show screenshot dialog first (don't hide main window yet)
            screenshot_dialog = ScreenshotDialog(
                self.root,
                callback=self._on_screenshot_captured
            )
            screenshot_dialog.show()

        except Exception as e:
            messagebox.showerror("Screenshot Error", f"Failed to capture screenshot: {str(e)}")

    def _start_screenshot_dialog(self):
        """Start the screenshot dialog after window is hidden."""
        try:
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
        # Window restoration is handled by the dialog itself
        if image_data is not None:
            self.state.set_image(image_data, None, "screenshot")
            self.state.clear_roi()
            self.state.clear_analysis_result()
            self._update_ui_state()
            self.status_var.set("Screenshot captured - Ready for analysis")

    def select_roi(self):
        """Handle ROI selection request."""
        if self.state.has_image():
            self.roi_selector.start_roi_selection()

    def on_roi_changed(self, roi_coords):
        """Handle ROI coordinates change during selection."""
        # Update display during selection if needed
        pass

    def on_roi_completed(self, roi_coords):
        """Handle ROI selection completion."""
        if roi_coords and len(roi_coords) >= 3:
            self.state.set_roi(roi_coords)
            self.state.set_application_state('roi_selected')

    def analyze_image(self):
        """Handle analyze image request."""
        if not self.state.can_analyze():
            return

        # Get analysis parameters
        spectrum_type = self.control_panel.get_selected_spectrum()

        # Set analysis in progress
        self.state.set_analysis_in_progress(True)

        # Run analysis in background thread
        threading.Thread(
            target=self._run_analysis,
            args=(spectrum_type,),
            daemon=True
        ).start()

    def _run_analysis(self, spectrum_type: str):
        """Run analysis in background thread."""
        try:
            # Get image and ROI
            image = self.state.get_image()
            roi = self.state.get_roi()

            # Get parameters for controlled method
            analysis_kwargs = {
                'spectrum_type': spectrum_type
            }

            if spectrum_type == 'controlled':
                params = self.control_panel.get_control_parameters()
                analysis_kwargs['subset_size'] = params['subset_size']
                analysis_kwargs['step_size'] = params['step_size']

            # Perform analysis
            result = self.analyzer.analyze_image(
                image=image,
                roi=roi,
                **analysis_kwargs
            )

            # Update UI on main thread
            self.root.after(0, lambda: self._on_analysis_complete(result))

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self._on_analysis_error(str(e)))

    def _on_analysis_complete(self, result: AnalysisResult):
        """Handle analysis completion."""
        self.state.set_analysis_result(result)
        self.state.set_analysis_in_progress(False)

        # Auto-show quality map after short delay
        self.root.after(500, self._auto_show_quality_map)

    def _on_analysis_error(self, error_message: str):
        """Handle analysis error."""
        self.state.set_analysis_in_progress(False)
        messagebox.showerror("Analysis Error", f"Analysis failed: {error_message}")

    def _auto_show_quality_map(self):
        """Automatically show quality map after analysis."""
        if self.state.has_analysis_result() and not self.image_canvas.is_showing_quality_map():
            self.toggle_quality_map()

    def toggle_quality_map(self):
        """Toggle quality map display."""
        logger.debug("toggle_quality_map() called")
        if not self.state.has_analysis_result():
            logger.debug("No analysis result available")
            return

        is_showing = self.image_canvas.is_showing_quality_map()
        logger.debug(f"Currently showing quality map: {is_showing}")

        if is_showing:
            # Hide quality map
            logger.debug("Hiding quality map")
            self.image_canvas.hide_quality_map()
            self.legend_panel.hide_legend()
            self.control_panel.set_quality_map_active(False)
        else:
            # Show quality map
            logger.debug("Showing quality map")
            result = self.state.get_analysis_result()
            spectrum_type = self.control_panel.get_selected_spectrum()
            self.image_canvas.show_quality_map(result.quality_map, spectrum_type)
            self.legend_panel.show_legend(spectrum_type)
            self.control_panel.set_quality_map_active(True)

    def show_results(self):
        """Show analysis results dialog."""
        if not self.state.has_analysis_result():
            return

        try:
            self.results_popup = ResultsPopup(
                self.root,
                self.state.get_analysis_result(),
                self.report_generator
            )
            self.results_popup.show()
        except Exception as e:
            messagebox.showerror("Results Error", f"Failed to show results: {str(e)}")

    def save_report(self):
        """Save analysis report."""
        if not self.state.can_save_report():
            return

        try:
            # Generate report content
            result = self.state.get_analysis_result()
            image_info = self.state.get_image_info()
            roi_info = self.state.get_roi_info()

            report_content = self.report_generator.generate_comprehensive_report(
                result.to_dict(),
                image_info,
                roi_info
            )

            # Get save location
            filename = filedialog.asksaveasfilename(
                title="Save Report",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialdir=self.file_operations.get_last_directory()
            )

            if filename:
                success = self.file_operations.save_report_to_file(report_content, filename)
                if success:
                    messagebox.showinfo("Success", "Report saved successfully!")
                else:
                    messagebox.showerror("Error", "Failed to save report")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save report: {str(e)}")

    def show_help(self):
        """Show help dialog."""
        try:
            help_dialog = HelpDialog(self.root)
            help_dialog.show()
        except Exception as e:
            messagebox.showerror("Help Error", f"Failed to show help: {str(e)}")

    def reset_application(self):
        """Reset entire application."""
        if messagebox.askyesno("Confirm Reset",
                               "This will clear all data and reset the application. Continue?"):
            self.state.reset()
            self.image_canvas.clear()
            self.roi_selector.clear()
            self.legend_panel.hide_legend()
            self._update_ui_state()

    def reset_display(self):
        """Reset display and view options."""
        logger.debug("reset_display() called")

        # Hide quality map first, then reset view
        logger.debug("Hiding quality map")
        self.image_canvas.hide_quality_map()
        logger.debug("Resetting canvas view")
        self.image_canvas.reset_view()

        # Clear ROI display and data
        logger.debug("Clearing ROI")
        self.roi_selector.clear()
        self.state.clear_roi()
        self.state.clear_analysis_result()

        # Reset UI panels
        logger.debug("Hiding legend and resetting controls")
        self.legend_panel.hide_legend()
        self.control_panel.set_quality_map_active(False)

        # Clear any displayed results/statistics
        if hasattr(self, 'results_popup') and self.results_popup:
            self.results_popup.destroy()
            self.results_popup = None

        # Update UI state to reflect changes
        logger.debug("Updating UI state")
        self._update_ui_state()
        logger.debug("reset_display() completed")

    def on_spectrum_changed(self):
        """Handle spectrum type change."""
        spectrum_type = self.control_panel.get_selected_spectrum()

        if self.state.has_analysis_result() and self.image_canvas.is_showing_quality_map():
            # Update quality map with new spectrum
            result = self.state.get_analysis_result()
            self.image_canvas.show_quality_map(result.quality_map, spectrum_type)
            self.legend_panel.show_legend(spectrum_type)

    # Zoom control methods
    def zoom_in(self):
        """Handle zoom in request."""
        self.image_canvas.zoom_in()
        self._update_zoom_display()

    def zoom_out(self):
        """Handle zoom out request."""
        self.image_canvas.zoom_out()
        self._update_zoom_display()

    def zoom_actual(self):
        """Handle zoom to actual size request."""
        self.image_canvas.zoom_actual()
        self._update_zoom_display()

    def _update_zoom_display(self):
        """Update zoom level display in control panel."""
        zoom_level = self.image_canvas.get_zoom_level()
        self.control_panel.update_zoom_level(zoom_level)

    def _on_zoom_changed(self, zoom_level: float):
        """Handle zoom level change from image canvas."""
        self.control_panel.update_zoom_level(zoom_level)

    def _get_image_info(self) -> Optional[Dict[str, Any]]:
        """Get image information for report."""
        return self.state.get_image_info()

    def _get_roi_info(self) -> Optional[Dict[str, Any]]:
        """Get ROI information for report."""
        return self.state.get_roi_info()

    # State change observers
    def _on_analysis_result_changed(self, result: AnalysisResult):
        """Handle analysis result change."""
        self._update_ui_state()

    def _on_image_changed(self, image_data):
        """Handle image change."""
        if image_data:
            # Extract the numpy array from ImageData object
            if hasattr(image_data, 'array'):
                image_array = image_data.array
            else:
                # Fallback if it's already an array
                image_array = image_data

            self.image_canvas.display_image(image_array)
            self.state.set_application_state('image_loaded')
            # Update zoom display
            self._update_zoom_display()
        else:
            self.image_canvas.clear()
        self._update_ui_state()

    def _on_roi_changed_state(self, roi_data):
        """Handle ROI change."""
        if roi_data:
            self.roi_selector.update_roi_display(roi_data)
            roi_info = f"ROI: {len(roi_data) if isinstance(roi_data, list) else len(roi_data.coordinates)} points"
            if hasattr(roi_data, 'calculate_area'):
                roi_info += f", {roi_data.calculate_area():.0f} px²"
            self.control_panel.update_roi_info(roi_info)
        else:
            self.roi_selector.clear()
            self.control_panel.update_roi_info("ROI: Not Selected (analyzing full image)")
        self._update_ui_state()

    def _on_app_state_changed(self, state: str):
        """Handle application state change."""
        self._update_ui_state()

    def on_closing(self):
        """Handle window closing event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()

    def run(self):
        """Start the application."""
        self.root.mainloop()


# Application entry point
def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = DICQualityInspector(root)

    # Set window close protocol
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    app.run()


if __name__ == "__main__":
    main()