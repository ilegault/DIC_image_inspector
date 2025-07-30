# ui/dialogs/results_popup.py - Results Display Dialog

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from models.analysis_result import AnalysisResult
from core.report_generator import ReportGenerator
from utils.constants import APP_CONFIG, get_theme_colors
from utils.window_utils import WindowManager


class ResultsPopup:
    """
    Results popup dialog for displaying comprehensive analysis results.

    Shows detailed analysis information in a scrollable popup window.
    Follows single responsibility principle - only results display.
    """

    def __init__(self, parent: tk.Widget, analysis_result: AnalysisResult,
                 report_generator: ReportGenerator):
        """
        Initialize results popup.

        Args:
            parent: Parent widget
            analysis_result: Analysis result to display
            report_generator: Report generator for creating content
        """
        self.parent = parent
        self.analysis_result = analysis_result
        self.report_generator = report_generator
        self.popup_window = None

    def show(self):
        """Show the results popup dialog."""
        try:
            self._create_popup_window()
            self._create_popup_content()
            self._center_window()

        except Exception as e:
            print(f"Error showing results popup: {e}")
            messagebox.showerror("Display Error", f"Failed to show results: {str(e)}")

    def _create_popup_window(self):
        """Create the main popup window."""
        colors = get_theme_colors()

        self.popup_window = WindowManager.create_child_window(
            parent=self.parent,
            title="DIC Quality Analysis Results",
            width=1000,
            height=800,
            resizable=True,
            topmost=False,
            center=True
        )
        self.popup_window.configure(bg=colors['background'])
        self.popup_window.grab_set()
        self.popup_window.minsize(800, 600)

    def _create_popup_content(self):
        """Create the scrollable content area."""
        colors = get_theme_colors()

        # Main container
        main_frame = tk.Frame(self.popup_window, bg=colors['background'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Create scrollable area
        self._create_scrollable_content(main_frame)

        # Close button
        self._create_close_button(main_frame)

    def _create_scrollable_content(self, parent):
        """Create scrollable content area with results."""
        colors = get_theme_colors()

        # Canvas and scrollbar for scrolling
        canvas = tk.Canvas(parent, bg=colors['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=colors['background'])

        # Configure scrolling
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.scrollable_frame.bind('<Configure>', configure_scroll_region)

        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Configure canvas window width
        def configure_canvas_window(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)

        canvas.bind('<Configure>', configure_canvas_window)

        # Mousewheel scrolling
        def on_mousewheel(event):
            try:
                if event.delta:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
            except:
                pass

        # Bind mousewheel to popup window
        self.popup_window.bind("<MouseWheel>", on_mousewheel)
        self.popup_window.bind("<Button-4>", on_mousewheel)
        self.popup_window.bind("<Button-5>", on_mousewheel)

        # Populate content
        self._populate_results_content()

    def _populate_results_content(self):
        """Populate the results content."""
        # Title
        self._add_title_section()

        # Executive Summary
        self._add_executive_summary()

        # Technical Analysis
        self._add_technical_analysis()

        # DIC Parameters
        self._add_dic_parameters()

        # Recommendations
        self._add_recommendations()

        # Image Information
        self._add_image_information()

    def _add_title_section(self):
        """Add title section."""
        colors = get_theme_colors()

        title_label = tk.Label(
            self.scrollable_frame,
            text=" DIC Image Quality Analysis Results",
            font=APP_CONFIG['fonts']['title'],
            fg=colors['text_primary'],
            bg=colors['background']
        )
        title_label.pack(pady=(0, 20))

    def _add_executive_summary(self):
        """Add executive summary section."""
        colors = get_theme_colors()
        section_frame = self._create_section_frame(" Executive Summary")

        # Overall score display
        score_frame = tk.Frame(section_frame, bg=colors['panel_bg'])
        score_frame.pack(pady=10)

        overall_score = self.analysis_result.overall_score
        quality_text, score_color = self.analysis_result.get_quality_assessment()

        # Large score display
        score_display = tk.Frame(score_frame, bg=colors['panel_bg'])
        score_display.pack()

        tk.Label(
            score_display,
            text=f"{overall_score:.1f}",
            font=('Arial', 48, 'bold'),
            fg=score_color,
            bg=colors['panel_bg']
        ).pack(side='left')

        tk.Label(
            score_display,
            text="/100",
            font=('Arial', 24),
            fg=colors['text_secondary'],
            bg=colors['panel_bg']
        ).pack(side='left', anchor='s', padx=(5, 0))

        tk.Label(
            score_frame,
            text=quality_text,
            font=('Arial', 14, 'bold'),
            fg=score_color,
            bg=colors['panel_bg']
        ).pack(pady=5)

        # Analysis method
        method_text = f"Analysis Method: {self.analysis_result.analysis_method}"
        tk.Label(
            section_frame,
            text=method_text,
            font=APP_CONFIG['fonts']['body'],
            fg=colors['text_secondary'],
            bg=colors['panel_bg']
        ).pack(pady=(0, 10))

    def _add_technical_analysis(self):
        """Add technical analysis section."""
        colors = get_theme_colors()
        section_frame = self._create_section_frame(" Technical Analysis")

        stats = self.analysis_result.quality_map_stats

        # Create grid for statistics
        stats_grid = tk.Frame(section_frame, bg=colors['panel_bg'])
        stats_grid.pack(pady=10)

        # Left column
        left_col = tk.Frame(stats_grid, bg=colors['panel_bg'])
        left_col.pack(side='left', padx=20)

        tk.Label(
            left_col,
            text="Quality Statistics:",
            font=('Arial', 12, 'bold'),
            fg=colors['primary'],
            bg=colors['panel_bg']
        ).pack(anchor='w')

        self._add_stat_label(left_col, f"• Maximum: {stats.max_quality:.1f}%", colors['success'])
        self._add_stat_label(left_col, f"• Average: {self.analysis_result.overall_score:.1f}%", colors['primary'])
        self._add_stat_label(left_col, f"• Minimum: {stats.min_quality:.1f}%", colors['danger'])

        # Right column
        right_col = tk.Frame(stats_grid, bg=colors['panel_bg'])
        right_col.pack(side='right', padx=20)

        tk.Label(
            right_col,
            text="Distribution:",
            font=('Arial', 12, 'bold'),
            fg=colors['primary'],
            bg=colors['panel_bg']
        ).pack(anchor='w')

        self._add_stat_label(right_col, f"• Median: {stats.median_quality:.1f}%", colors['warning'])
        self._add_stat_label(right_col, f"• Std Deviation: {stats.std_quality:.1f}%", colors['purple'])
        self._add_stat_label(right_col, f"• Spectrum: {self.analysis_result.spectrum_used}", colors['secondary'])

    def _add_dic_parameters(self):
        """Add DIC parameters section."""
        colors = get_theme_colors()
        section_frame = self._create_section_frame(" Recommended DIC Parameters")

        if self.analysis_result.dic_parameters:
            params = self.analysis_result.dic_parameters

            # Parameters grid
            params_grid = tk.Frame(section_frame, bg=colors['panel_bg'])
            params_grid.pack(pady=10)

            # Left column
            left_params = tk.Frame(params_grid, bg=colors['panel_bg'])
            left_params.pack(side='left', padx=30)

            tk.Label(
                left_params,
                text="Correlation Setup:",
                font=('Arial', 12, 'bold'),
                fg=colors['primary'],
                bg=colors['panel_bg']
            ).pack(anchor='w')

            self._add_param_label(left_params, f"• Subset Size: {params.subset_size_used} pixels")
            self._add_param_label(left_params, f"• Step Size: {params.step_size} pixels")

            # Right column
            right_params = tk.Frame(params_grid, bg=colors['panel_bg'])
            right_params.pack(side='right', padx=30)

            tk.Label(
                right_params,
                text="Expected Performance:",
                font=('Arial', 12, 'bold'),
                fg=colors['primary'],
                bg=colors['panel_bg']
            ).pack(anchor='w')

            self._add_param_label(right_params, f"• Overlap: {params.overlap_percent:.0f}%")
            self._add_param_label(right_params, f"• Accuracy: {params.expected_accuracy}")

    def _add_recommendations(self):
        """Add recommendations section."""
        colors = get_theme_colors()
        section_frame = self._create_section_frame(" Recommendations")

        # Generate recommendations using report generator
        recommendations_text = self.report_generator.generate_section(
            'recommendations',
            self.analysis_result.to_dict()
        )

        # Extract just the recommendations list
        lines = recommendations_text.split('\n')
        recommendation_lines = [line for line in lines if
                                line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.'))]

        # Display first 8 recommendations
        for rec_line in recommendation_lines[:8]:
            label = tk.Label(
                section_frame,
                text=rec_line.strip(),
                font=APP_CONFIG['fonts']['body'],
                fg=colors['text_primary'],
                bg=colors['panel_bg'],
                wraplength=800,
                justify='left'
            )
            label.pack(anchor='w', padx=15, pady=2)

    def _add_image_information(self):
        """Add image information section."""
        colors = get_theme_colors()
        section_frame = self._create_section_frame("ℹ️ Image Information")

        info_frame = tk.Frame(section_frame, bg=colors['panel_bg'])
        info_frame.pack(pady=10)

        # Add image dimensions if available
        if self.analysis_result.image_dimensions:
            h, w = self.analysis_result.image_dimensions
            tk.Label(
                info_frame,
                text=f"Image Size: {w} × {h} pixels",
                font=APP_CONFIG['fonts']['body'],
                fg=colors['text_secondary'],
                bg=colors['panel_bg']
            ).pack()

        # Add ROI information if available
        if self.analysis_result.roi_area:
            tk.Label(
                info_frame,
                text=f"ROI Area: {self.analysis_result.roi_area:.0f} pixels²",
                font=APP_CONFIG['fonts']['body'],
                fg=colors['text_secondary'],
                bg=colors['panel_bg']
            ).pack()
        else:
            tk.Label(
                info_frame,
                text="ROI: Full image analyzed",
                font=APP_CONFIG['fonts']['body'],
                fg=colors['text_secondary'],
                bg=colors['panel_bg']
            ).pack()

    def _create_section_frame(self, title: str) -> tk.Frame:
        """Create a section frame with title."""
        colors = get_theme_colors()

        section_frame = tk.Frame(
            self.scrollable_frame,
            bg=colors['panel_bg'],
            relief='raised',
            bd=2
        )
        section_frame.pack(fill='x', padx=10, pady=10)

        # Section title
        tk.Label(
            section_frame,
            text=title,
            font=APP_CONFIG['fonts']['heading'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        ).pack(pady=10)

        return section_frame

    def _add_stat_label(self, parent, text: str, color: str):
        """Add a colored statistic label."""
        colors = get_theme_colors()
        tk.Label(
            parent,
            text=text,
            font=APP_CONFIG['fonts']['body'],
            fg=color,
            bg=colors['panel_bg']
        ).pack(anchor='w')

    def _add_param_label(self, parent, text: str):
        """Add a parameter label."""
        colors = get_theme_colors()
        tk.Label(
            parent,
            text=text,
            font=APP_CONFIG['fonts']['body'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        ).pack(anchor='w')

    def _create_close_button(self, parent):
        """Create close button."""
        colors = get_theme_colors()
        close_btn = tk.Button(
            parent,
            text="Close Results",
            bg=colors['btn_primary'],
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=30,
            pady=10,
            relief='flat',
            bd=0,
            cursor='hand2',
            command=self._close_popup,
            activebackground=colors['btn_primary_hover'],
            activeforeground='white'
        )
        close_btn.pack(pady=20)

    def _close_popup(self):
        """Close the popup window."""
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_window = None

    def _center_window(self):
        """Center the popup window on the parent."""
        if not self.popup_window:
            return

        # Update window to get accurate dimensions
        self.popup_window.update_idletasks()

        # Get window dimensions
        window_width = self.popup_window.winfo_width()
        window_height = self.popup_window.winfo_height()

        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Calculate center position
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        # Ensure window is not off-screen
        x = max(0, x)
        y = max(0, y)

        # Set window position
        self.popup_window.geometry(f"+{x}+{y}")

    def is_open(self) -> bool:
        """Check if popup is currently open."""
        return self.popup_window is not None and self.popup_window.winfo_exists()

    def bring_to_front(self):
        """Bring popup to front if it's open."""
        if self.is_open():
            self.popup_window.lift()
            self.popup_window.focus_set()