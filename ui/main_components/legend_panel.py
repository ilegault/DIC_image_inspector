"""
Legend panel component for quality map visualization.

This module provides a dynamic legend panel that displays color-coded quality
interpretations based on the selected spectrum type. It shows the mapping between
colors and DIC quality levels to help users interpret quality map visualizations.

Usage:
    from ui.main_components.legend_panel import LegendPanel

    legend = LegendPanel(parent_widget)
    legend.show_legend('optimized')  # Show legend for optimized spectrum
"""

import tkinter as tk
from typing import Dict, List, Tuple
from utils.constants import APP_CONFIG, get_theme_colors
from analysis.quality_map.colormap import ColormapGenerator


class LegendPanel:
    """
    Dynamic legend panel component for quality map visualization.

    Shows color-coded legend based on selected spectrum type.
    Follows single responsibility principle - only legend display concerns.
    """

    def __init__(self, parent: tk.Widget):
        """
        Initialize legend panel.

        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.legend_frame = None
        self.current_spectrum = None
        self.is_visible = False

        # Initialize colormap generator to get consistent spectrum definitions
        self.colormap_generator = ColormapGenerator()
        
        # Get spectrum definitions from the same source as the colormap visualization
        # This ensures the legend colors match exactly with the actual visualization
        self.spectrum_definitions = self.colormap_generator.detailed_spectrums

    def show_legend(self, spectrum_type: str):
        """
        Show legend for specified spectrum type.

        Args:
            spectrum_type: Type of spectrum ('optimized', 'controlled', etc.)
        """
        try:
            # Clear existing legend
            self.hide_legend()

            # Create new legend
            self._create_legend(spectrum_type)
            self.current_spectrum = spectrum_type
            self.is_visible = True

        except Exception as e:
            print(f"ERROR showing legend: {e}")
            import traceback
            traceback.print_exc()

    def hide_legend(self):
        """Hide the legend panel."""
        if self.legend_frame:
            self.legend_frame.destroy()
            self.legend_frame = None
        self.is_visible = False

    def update_spectrum(self, spectrum_type: str):
        """
        Update legend to show different spectrum.

        Args:
            spectrum_type: New spectrum type to display
        """
        if spectrum_type != self.current_spectrum:
            self.show_legend(spectrum_type)

    def _create_legend(self, spectrum_type: str):
        """
        Create legend UI with modern styling.

        Args:
            spectrum_type: Type of spectrum to display
        """
        if spectrum_type not in self.spectrum_definitions:
            print(f"Unknown spectrum type: {spectrum_type}")
            return

        colors = get_theme_colors()
        spectrum_def = self.spectrum_definitions[spectrum_type]

        # Create legend container with modern styling
        self.legend_frame = tk.Frame(
            self.parent,
            bg=colors['panel_bg'],
            relief='flat',
            bd=0,
            highlightbackground=colors['panel_border'],
            highlightthickness=1
        )
        self.legend_frame.place(x=10, y=10, width=320, height=240)

        # Skip shadow frame for now - it's causing the color issue
        # Tkinter doesn't support RGBA colors (colors with transparency)

        # Inner content frame
        content_frame = tk.Frame(
            self.legend_frame,
            bg=colors['panel_bg'],
            relief='flat',
            bd=0
        )
        content_frame.place(x=0, y=0, relwidth=1, relheight=1)

        # Legend header with theme-appropriate styling
        header_frame = tk.Frame(
            content_frame,
            bg=colors['hover_bg'],
            height=36
        )
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        # Title with proper contrast
        title_label = tk.Label(
            header_frame,
            text=f" {spectrum_def['name']}",
            font=('Segoe UI', 11, 'bold'),
            fg=colors['text_primary'],
            bg=colors['hover_bg']
        )
        title_label.pack(side='left', padx=12, pady=8)

        # Close button
        close_btn = tk.Label(
            header_frame,
            text="×",
            font=('Segoe UI', 12),
            fg=colors['text_secondary'],
            bg=colors['hover_bg'],
            cursor='hand2'
        )
        close_btn.pack(side='right', padx=12)
        close_btn.bind("<Button-1>", lambda e: self.hide_legend())

        # Add hover effect to close button
        def on_enter(e):
            close_btn.config(fg=colors['text_primary'])

        def on_leave(e):
            close_btn.config(fg=colors['text_secondary'])

        close_btn.bind("<Enter>", on_enter)
        close_btn.bind("<Leave>", on_leave)

        # Legend content
        legend_content = tk.Frame(
            content_frame,
            bg=colors['panel_bg']
        )
        legend_content.pack(fill='both', expand=True, padx=12, pady=8)

        # Create color entries
        for i, (r, g, b, description) in enumerate(spectrum_def['colors']):
            entry_frame = tk.Frame(
                legend_content,
                bg=colors['panel_bg']
            )
            entry_frame.pack(fill='x', pady=2)

            # Color box with border
            color_container = tk.Frame(
                entry_frame,
                bg=colors['panel_border'],
                relief='flat',
                bd=0
            )
            color_container.pack(side='left', padx=(0, 8))

            color_box = tk.Frame(
                color_container,
                bg=f'#{r:02x}{g:02x}{b:02x}',
                width=20,
                height=20,
                relief='flat',
                bd=0
            )
            color_box.pack(padx=1, pady=1)

            # Description with proper contrast
            desc_parts = description.split(': ', 1)
            if len(desc_parts) == 2:
                # Range label
                range_label = tk.Label(
                    entry_frame,
                    text=desc_parts[0] + ':',
                    font=('Segoe UI', 9, 'bold'),
                    fg=colors['text_primary'],
                    bg=colors['panel_bg']
                )
                range_label.pack(side='left', padx=(0, 4))

                # Description label
                desc_label = tk.Label(
                    entry_frame,
                    text=desc_parts[1],
                    font=('Segoe UI', 9),
                    fg=colors['text_secondary'],
                    bg=colors['panel_bg'],
                    wraplength=220,
                    justify='left'
                )
                desc_label.pack(side='left', fill='x', expand=True)
            else:
                # Single description
                desc_label = tk.Label(
                    entry_frame,
                    text=description,
                    font=('Segoe UI', 9),
                    fg=colors['text_secondary'],
                    bg=colors['panel_bg'],
                    wraplength=280,
                    justify='left'
                )
                desc_label.pack(side='left', fill='x', expand=True)

        # Make legend draggable
        self._make_draggable(self.legend_frame, header_frame)

    def _make_draggable(self, widget, handle):
        """
        Make a widget draggable by a handle.

        Args:
            widget: Widget to make draggable
            handle: Handle widget to drag by
        """

        def start_drag(event):
            widget.start_x = event.x
            widget.start_y = event.y

        def drag(event):
            x = widget.winfo_x() + event.x - widget.start_x
            y = widget.winfo_y() + event.y - widget.start_y

            # Keep within parent bounds
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            widget_width = widget.winfo_width()
            widget_height = widget.winfo_height()

            x = max(0, min(x, parent_width - widget_width))
            y = max(0, min(y, parent_height - widget_height))

            widget.place(x=x, y=y)

        handle.bind("<Button-1>", start_drag)
        handle.bind("<B1-Motion>", drag)

        # Change cursor on handle
        handle.configure(cursor='fleur')

    def get_spectrum_info(self, spectrum_type: str) -> Dict:
        """
        Get information about a spectrum type.

        Args:
            spectrum_type: Spectrum type to get info for

        Returns:
            Dictionary with spectrum information
        """
        if spectrum_type in self.spectrum_definitions:
            return self.spectrum_definitions[spectrum_type].copy()
        else:
            return {}

    def refresh_theme(self):
        """Refresh legend with new theme colors if visible."""
        if self.is_visible and self.current_spectrum:
            self.show_legend(self.current_spectrum)