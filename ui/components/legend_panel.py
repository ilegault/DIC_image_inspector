# ui/components/legend_panel.py - Clean Legend Component

import tkinter as tk
from typing import Dict, List, Tuple
from utils.constants import APP_CONFIG


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

        # Legend definitions for different spectrums
        self.spectrum_definitions = {
            'optimized': {
                'name': 'Optimized (Rainbow: Red→Blue)',
                'colors': [
                    (0, 0, 0, "Critical (0-75%): Black - Not suitable for DIC"),
                    (255, 0, 0, "Minimum (75%): Red - Threshold for DIC"),
                    (255, 127, 0, "Good (80-85%): Orange - Acceptable for DIC"),
                    (255, 255, 0, "Very Good (85-90%): Yellow - Good for DIC"),
                    (0, 255, 0, "Excellent (90-95%): Green - Excellent for DIC"),
                    (0, 0, 255, "Perfect (95-100%): Blue - Ideal for DIC")
                ]
            },
            'controlled': {
                'name': 'Controlled Pattern Quality (Colorblind-Friendly)',
                'colors': [
                    (50, 0, 0, "Unusable (0-70%): No correlation possible"),
                    (255, 0, 0, "Poor (70-80%): Unreliable correlation"),
                    (255, 140, 0, "Acceptable (80-85%): Usable with uncertainty"),
                    (255, 255, 0, "Good (85-90%): Good correlation quality"),
                    (0, 255, 255, "Very Good (90-95%): Very reliable"),
                    (0, 100, 255, "Excellent (95-100%): Optimal pattern")
                ]
            }
        }

    def show_legend(self, spectrum_type: str):
        """
        Show legend for specified spectrum type.

        Args:
            spectrum_type: Type of spectrum to display legend for
        """
        try:
            # Hide existing legend
            self.hide_legend()

            # Validate spectrum type
            if spectrum_type not in self.spectrum_definitions:
                print(f"WARNING: Unknown spectrum type '{spectrum_type}', using 'custom_dic'")
                spectrum_type = 'custom_dic'

            # Create new legend
            self._create_legend(spectrum_type)
            self.current_spectrum = spectrum_type
            self.is_visible = True

            print(f"Legend shown for {spectrum_type}")

        except Exception as e:
            print(f"ERROR showing legend: {e}")
            import traceback
            traceback.print_exc()

    def hide_legend(self):
        """Hide the current legend."""
        try:
            if self.legend_frame:
                self.legend_frame.destroy()
                self.legend_frame = None
                self.is_visible = False
                print("Legend hidden")
        except Exception as e:
            print(f"ERROR hiding legend: {e}")

    def update_legend(self, spectrum_type: str):
        """
        Update legend to new spectrum type.

        Args:
            spectrum_type: New spectrum type to display
        """
        if spectrum_type != self.current_spectrum:
            self.show_legend(spectrum_type)

    def _create_legend(self, spectrum_type: str):
        """
        Create legend UI for specified spectrum.

        Args:
            spectrum_type: Spectrum type to create legend for
        """
        # Create legend container with larger fixed height for full display
        self.legend_frame = tk.Frame(
            self.parent,
            bg=APP_CONFIG['colors']['panel_bg'],
            relief='raised',
            bd=2,
            height=120
        )
        self.legend_frame.pack(fill='x', pady=10)
        self.legend_frame.pack_propagate(False)  # Maintain fixed height

        # Get spectrum definition
        spectrum_def = self.spectrum_definitions[spectrum_type]

        # Title
        title_text = f"Quality Legend - {spectrum_def['name']}"
        title_label = tk.Label(
            self.legend_frame,
            text=title_text,
            font=('Arial', 12, 'bold'),
            fg=APP_CONFIG['colors']['text_primary'],
            bg=APP_CONFIG['colors']['panel_bg']
        )
        title_label.pack(pady=(8, 5))

        # Color items container
        items_container = tk.Frame(self.legend_frame, bg=APP_CONFIG['colors']['panel_bg'])
        items_container.pack(fill='both', expand=True, pady=5)

        # Create color items
        self._create_color_items(items_container, spectrum_def['colors'])

    def _create_color_items(self, container: tk.Widget, colors: List[Tuple[int, int, int, str]]):
        """
        Create color legend items.

        Args:
            container: Container widget for color items
            colors: List of (r, g, b, label) tuples
        """
        try:
            for r, g, b, label in colors:
                # Convert RGB to hex
                bg_color = f"#{r:02x}{g:02x}{b:02x}"

                # Determine text color based on brightness
                brightness = (r * 0.299 + g * 0.587 + b * 0.114)
                text_color = "white" if brightness < 128 else "black"

                # Extract short label (before colon)
                short_label = label.split(':')[0] if ':' in label else label

                # Create legend item with larger, more prominent display
                item = tk.Label(
                    container,
                    text=f" {short_label} ",
                    bg=bg_color,
                    fg=text_color,
                    font=('Arial', 10, 'bold'),
                    relief='raised',
                    bd=2,
                    padx=4,
                    pady=3
                )
                item.pack(side='left', padx=2, expand=True, fill='both')

        except Exception as e:
            print(f"Error creating color items: {e}")

    def is_legend_visible(self) -> bool:
        """Check if legend is currently visible."""
        return self.is_visible and self.legend_frame is not None

    def get_current_spectrum(self) -> str:
        """Get currently displayed spectrum type."""
        return self.current_spectrum

    def get_available_spectrums(self) -> List[str]:
        """Get list of available spectrum types."""
        return list(self.spectrum_definitions.keys())

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

    def add_custom_spectrum(self, spectrum_name: str, spectrum_def: Dict):
        """
        Add a custom spectrum definition.

        Args:
            spectrum_name: Name of the custom spectrum
            spectrum_def: Spectrum definition dictionary
        """
        if 'name' in spectrum_def and 'colors' in spectrum_def:
            self.spectrum_definitions[spectrum_name] = spectrum_def
            print(f"Added custom spectrum: {spectrum_name}")
        else:
            print(f"Invalid spectrum definition for {spectrum_name}")

    def remove_custom_spectrum(self, spectrum_name: str):
        """
        Remove a custom spectrum definition.

        Args:
            spectrum_name: Name of spectrum to remove
        """
        if spectrum_name in self.spectrum_definitions:
            # Don't remove built-in spectrums
            built_in = ['optimized', 'controlled']
            if spectrum_name not in built_in:
                del self.spectrum_definitions[spectrum_name]
                print(f"Removed custom spectrum: {spectrum_name}")
            else:
                print(f"Cannot remove built-in spectrum: {spectrum_name}")
        else:
            print(f"Spectrum not found: {spectrum_name}")

    def create_legend_tooltip(self, spectrum_type: str) -> str:
        """
        Create detailed tooltip text for a spectrum.

        Args:
            spectrum_type: Spectrum type to create tooltip for

        Returns:
            Formatted tooltip text
        """
        if spectrum_type not in self.spectrum_definitions:
            return "Unknown spectrum type"

        spectrum_def = self.spectrum_definitions[spectrum_type]
        tooltip_lines = [f"Spectrum: {spectrum_def['name']}", ""]

        for r, g, b, label in spectrum_def['colors']:
            tooltip_lines.append(f"• {label}")

        return "\n".join(tooltip_lines)

    def export_legend_image(self, spectrum_type: str, filename: str):
        """
        Export legend as an image file.

        Args:
            spectrum_type: Spectrum type to export
            filename: Output filename
        """
        try:
            # This would require additional PIL/image generation code
            # For now, just provide a placeholder
            print(f"Legend export for {spectrum_type} to {filename} - Feature not implemented yet")

        except Exception as e:
            print(f"Error exporting legend: {e}")

    def get_legend_dimensions(self) -> Tuple[int, int]:
        """
        Get current legend dimensions.

        Returns:
            Tuple of (width, height) in pixels
        """
        if self.legend_frame:
            try:
                return self.legend_frame.winfo_width(), self.legend_frame.winfo_height()
            except:
                return (0, 0)
        return (0, 0)