"""
Colormap generation and application for quality visualization.

Provides color mapping functionality to visualize quality scores with different
color schemes optimized for DIC analysis. Supports multiple spectrum types and
overlay blending with original images.

Usage:
    colormap_gen = ColormapGenerator()
    colored_map = colormap_gen.apply_colormap(quality_map, 'optimized')
"""

import numpy as np
import cv2
from DIC.utils.constants import COLOR_SPECTRUMS


class ColormapGenerator:
    """
    Generates color-mapped visualizations for quality maps.

    Converts normalized quality values (0-1) to color visualizations
    using different spectrum types for various assessment criteria.
    """

    def __init__(self):
        self.spectrum_definitions = COLOR_SPECTRUMS

        # Define detailed color mappings for each spectrum
        # These include RGB tuples with descriptions for proper unpacking
        self.detailed_spectrums = {
            'optimized': {
                'name': 'Optimized DIC',
                'description': 'Optimized for DIC analysis visualization',
                'colors': [
                    (0, 0, 0, "Unusable: No correlation possible"),        # Black for worst
                    (139, 0, 0, "Poor: Unreliable correlation"),           # Dark red
                    (255, 140, 0, "Acceptable: Usable with uncertainty"),  # Orange
                    (255, 255, 0, "Good: Good correlation quality"),       # Yellow
                    (0, 255, 255, "Very Good: Very reliable"),             # Cyan
                    (0, 255, 0, "Excellent: Optimal pattern")              # Green for best
                ]
            },
            'controlled': {
                'name': 'Controlled Pattern Quality',
                'description': 'High-precision pattern quality assessment',
                'colors': [
                    (0, 0, 0, "Unusable: No correlation possible"),        # Black for worst
                    (139, 0, 0, "Poor: Unreliable correlation"),           # Dark red
                    (255, 140, 0, "Acceptable: Usable with uncertainty"),  # Orange
                    (255, 255, 0, "Good: Good correlation quality"),       # Yellow
                    (0, 255, 255, "Very Good: Very reliable"),             # Cyan
                    (0, 255, 0, "Excellent: Optimal pattern")              # Green for best
                ]
            },
            'custom_dic': {
                'name': 'Custom DIC Assessment',
                'description': 'Custom colormap for DIC quality visualization',
                'colors': [
                    (0, 0, 0, "Critical: Not suitable for DIC"),
                    (255, 0, 0, "Minimum: Threshold for DIC"),
                    (255, 127, 0, "Good: Acceptable for DIC"),
                    (255, 255, 0, "Very Good: Good for DIC"),
                    (0, 255, 0, "Excellent: Excellent for DIC"),
                    (0, 0, 255, "Perfect: Ideal for DIC")
                ]
            }
        }

        # Add hex to RGB conversions for other spectrums
        for spectrum_name, spectrum_data in self.spectrum_definitions.items():
            if spectrum_name not in self.detailed_spectrums and 'colors' in spectrum_data:
                # Convert hex colors to RGB tuples
                rgb_colors = []
                for i, hex_color in enumerate(spectrum_data['colors']):
                    if isinstance(hex_color, str) and hex_color.startswith('#'):
                        # Convert hex to RGB
                        r = int(hex_color[1:3], 16)
                        g = int(hex_color[3:5], 16)
                        b = int(hex_color[5:7], 16)
                        # Create generic description based on position
                        desc = f"Level {i + 1}"
                        rgb_colors.append((r, g, b, desc))

                if rgb_colors:
                    self.detailed_spectrums[spectrum_name] = {
                        'name': spectrum_data.get('name', spectrum_name),
                        'description': spectrum_data.get('description', ''),
                        'colors': rgb_colors
                    }

    def apply_colormap(self, quality_map: np.ndarray, spectrum_type: str = 'custom_dic',
                       interpolation: str = 'smooth') -> np.ndarray:
        """
        Apply colormap to quality map.

        Args:
            quality_map: Normalized quality values (0-1)
            spectrum_type: Type of color spectrum to use
            interpolation: 'smooth' for interpolated colors, 'discrete' for bands

        Returns:
            RGB colored image
        """
        if spectrum_type not in self.detailed_spectrums:
            spectrum_type = 'optimized'

        spectrum = self.detailed_spectrums[spectrum_type]
        colors = spectrum['colors']

        # Create RGB output image
        h, w = quality_map.shape
        colored_map = np.zeros((h, w, 3), dtype=np.uint8)

        if interpolation == 'smooth':
            colored_map = self._apply_smooth_colormap(quality_map, colors)
        else:
            colored_map = self._apply_discrete_colormap(quality_map, colors)

        return colored_map

    def _apply_smooth_colormap(self, quality_map: np.ndarray, colors: list) -> np.ndarray:
        """Apply smooth interpolated colormap using vectorized operations."""
        h, w = quality_map.shape

        # Extract RGB values from colors (now properly formatted as tuples)
        rgb_colors = np.array([[r, g, b] for r, g, b, _ in colors], dtype=np.float32)
        n_colors = len(rgb_colors)

        # Create interpolation points (0 to 1)
        color_positions = np.linspace(0, 1, n_colors)

        # Clamp quality values to [0, 1]
        quality_clamped = np.clip(quality_map, 0, 1)

        # Find which color segment each pixel belongs to
        segment_indices = np.searchsorted(color_positions, quality_clamped) - 1
        segment_indices = np.clip(segment_indices, 0, n_colors - 2)

        # Get the interpolation factor for each pixel
        pos1 = color_positions[segment_indices]
        pos2 = color_positions[segment_indices + 1]

        # Avoid division by zero
        denominator = pos2 - pos1
        denominator[denominator == 0] = 1
        t = (quality_clamped - pos1) / denominator
        t = np.clip(t, 0, 1)

        # Get colors for interpolation
        color1 = rgb_colors[segment_indices]  # Shape: (h, w, 3)
        color2 = rgb_colors[segment_indices + 1]  # Shape: (h, w, 3)

        # Expand t to match color dimensions
        t_expanded = np.expand_dims(t, axis=2)  # Shape: (h, w, 1)

        # Interpolate colors
        interpolated_colors = color1 * (1 - t_expanded) + color2 * t_expanded

        # Convert to uint8
        colored_map = np.clip(interpolated_colors, 0, 255).astype(np.uint8)

        return colored_map

    def _apply_discrete_colormap(self, quality_map: np.ndarray, colors: list) -> np.ndarray:
        """Apply discrete band colormap (original method)."""
        h, w = quality_map.shape
        colored_map = np.zeros((h, w, 3), dtype=np.uint8)

        # Apply color mapping with discrete bands
        for i, (r, g, b, description) in enumerate(colors):
            if i == 0:
                # First color (lowest quality)
                if i + 1 < len(colors):
                    next_threshold = (i + 1) / (len(colors) - 1)
                    mask = quality_map <= next_threshold
                else:
                    mask = quality_map <= 1.0
            elif i == len(colors) - 1:
                # Last color (highest quality)
                prev_threshold = i / (len(colors) - 1)
                mask = quality_map > prev_threshold
            else:
                # Middle colors
                prev_threshold = i / (len(colors) - 1)
                next_threshold = (i + 1) / (len(colors) - 1)
                mask = (quality_map > prev_threshold) & (quality_map <= next_threshold)

            colored_map[mask] = [r, g, b]

        return colored_map

    def apply_overlay_blend(self, base_image: np.ndarray, colored_map: np.ndarray,
                            alpha: float = 0.7) -> np.ndarray:
        """
        Blend colored quality map with base image.

        Args:
            base_image: Original image
            colored_map: Colored quality map
            alpha: Blending factor (0-1)

        Returns:
            Blended image
        """
        # Ensure images are same size
        if colored_map.shape[:2] != base_image.shape[:2]:
            colored_map = cv2.resize(colored_map, (base_image.shape[1], base_image.shape[0]))

        # Ensure both are RGB
        if len(base_image.shape) == 2:
            base_rgb = cv2.cvtColor(base_image, cv2.COLOR_GRAY2RGB)
        else:
            base_rgb = base_image.copy()

        # Blend
        blended = cv2.addWeighted(base_rgb, 1 - alpha, colored_map, alpha, 0)
        return blended


def apply_dic_colormap(quality_map: np.ndarray, spectrum_type: str = 'optimized') -> np.ndarray:
    """
    Convenience function to apply DIC colormap.

    Args:
        quality_map: Quality map data (0-1 normalized)
        spectrum_type: Color spectrum type

    Returns:
        RGB colored image
    """
    generator = ColormapGenerator()
    return generator.apply_colormap(quality_map, spectrum_type)