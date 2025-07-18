# ui/live_analyze/quality_overlay.py - Quality Overlay Display

import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
from typing import Tuple, Optional
import logging
import cv2
import time

logger = logging.getLogger(__name__)


class QualityOverlay:
    """
    Overlay window to display quality map visualization over the ROI area.
    
    This overlay shows the real-time quality analysis results but can be
    hidden during screen captures to ensure clean analysis data.
    """
    
    def __init__(self, parent_window, roi_bounds: Tuple[int, int, int, int], 
                 colormap_generator=None):
        """
        Initialize the quality overlay.
        
        Args:
            parent_window: Parent tkinter window
            roi_bounds: (x1, y1, x2, y2) bounds of the ROI in screen coordinates
            colormap_generator: Colormap generator for quality visualization
        """
        self.parent = parent_window
        self.roi_bounds = roi_bounds
        self.colormap_generator = colormap_generator
        
        x1, y1, x2, y2 = roi_bounds
        self.roi_width = x2 - x1
        self.roi_height = y2 - y1
        
        # Create overlay window positioned over the ROI
        self.overlay = tk.Toplevel(parent_window)
        self.overlay.geometry(f"{self.roi_width}x{self.roi_height}+{x1}+{y1}")
        self.overlay.attributes('-topmost', True)
        self.overlay.attributes('-alpha', 0.7)  # Semi-transparent
        self.overlay.overrideredirect(True)  # Remove window decorations
        
        # Canvas for quality map display
        self.canvas = tk.Canvas(
            self.overlay, 
            width=self.roi_width, 
            height=self.roi_height,
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Current quality map data
        self.current_quality_map = None
        self.quality_image = None
        
        # Default colormap if none provided
        if not self.colormap_generator:
            self.use_default_colormap = True
        else:
            self.use_default_colormap = False
        
        logger.info(f"QualityOverlay initialized at {roi_bounds}")

        # Add caching for display
        self._last_quality_map_hash = None
        self._last_colorized_image = None
        self._last_photo_image = None

        # Display size limit for performance
        self.max_display_size = 400  # Max dimension for display

        # Update counter for performance monitoring
        self.update_count = 0
        self.last_update_time = 0

    def update_quality_map(self, quality_map: np.ndarray, resize_for_display: bool = True):
        """
        Optimized quality map display update with caching and resizing.

        Args:
            quality_map: Quality map array (0-1 range)
            resize_for_display: If True, resize large maps for performance
        """
        try:
            self.update_count += 1
            start_time = time.time()

            # Check if quality map has actually changed
            map_hash = self._get_map_hash(quality_map)
            if map_hash == self._last_quality_map_hash and self._last_photo_image:
                # No change, skip update
                logger.debug("Quality map unchanged, skipping update")
                return

            self._last_quality_map_hash = map_hash

            # Store original
            self.current_quality_map = quality_map

            # Resize for display if needed
            display_map = quality_map
            if resize_for_display and max(quality_map.shape) > self.max_display_size:
                scale = self.max_display_size / max(quality_map.shape)
                new_size = (int(quality_map.shape[1] * scale),
                            int(quality_map.shape[0] * scale))
                display_map = cv2.resize(quality_map, new_size, interpolation=cv2.INTER_AREA)
                logger.debug(f"Resized quality map from {quality_map.shape} to {display_map.shape}")

            # Check if we can reuse colorized image (if only size changed)
            if self._last_colorized_image is None or display_map.shape != self._last_colorized_image.shape[:2]:
                # Create colorized version
                if self.colormap_generator and hasattr(self.colormap_generator, 'generate_quality_colormap'):
                    self._last_colorized_image = self.colormap_generator.generate_quality_colormap(display_map)
                else:
                    self._last_colorized_image = self._create_rainbow_colormap_fast(display_map)

            # Create PIL Image
            pil_image = Image.fromarray(self._last_colorized_image)

            # Resize to overlay window size if needed
            if pil_image.size != (self.roi_width, self.roi_height):
                pil_image = pil_image.resize((self.roi_width, self.roi_height),
                                             Image.Resampling.BILINEAR)  # Faster than LANCZOS

            # Convert to PhotoImage and cache
            self._last_photo_image = ImageTk.PhotoImage(pil_image)

            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor='nw', image=self._last_photo_image)

            # Log performance occasionally
            update_time = (time.time() - start_time) * 1000  # ms
            if self.update_count % 10 == 0:
                logger.debug(f"Quality overlay update #{self.update_count}: {update_time:.1f}ms")

        except Exception as e:
            logger.error(f"Error updating quality map display: {e}")

    def _get_map_hash(self, quality_map: np.ndarray) -> int:
        """Generate fast hash of quality map for change detection."""
        # Use shape, mean, and a sample of values for fast hashing
        sample_indices = np.linspace(0, quality_map.size - 1, min(100, quality_map.size), dtype=int)
        sample_values = quality_map.flat[sample_indices]

        return hash((quality_map.shape,
                     round(quality_map.mean(), 3),
                     round(quality_map.std(), 3),
                     tuple(np.round(sample_values, 2))))

    def _create_rainbow_colormap_fast(self, quality_map: np.ndarray) -> np.ndarray:
        """
        Fast rainbow colormap generation using vectorized operations.

        Args:
            quality_map: Normalized quality map (0-1 range)

        Returns:
            RGB image array
        """
        try:
            # Ensure input is in 0-1 range
            normalized = np.clip(quality_map, 0, 1)

            # Convert to 0-255 range
            scaled = (normalized * 255).astype(np.uint8)

            # Create output array
            h, w = scaled.shape
            colored = np.zeros((h, w, 3), dtype=np.uint8)

            # Vectorized color mapping using masks
            # Blue to Cyan (0-85)
            mask1 = scaled < 85
            colored[mask1, 1] = scaled[mask1] * 3  # Green channel
            colored[mask1, 2] = 255  # Blue channel

            # Cyan to Yellow (85-170)
            mask2 = (scaled >= 85) & (scaled < 170)
            scaled_local = scaled[mask2] - 85
            colored[mask2, 0] = scaled_local * 3  # Red channel
            colored[mask2, 1] = 255  # Green channel
            colored[mask2, 2] = 255 - scaled_local * 3  # Blue channel

            # Yellow to Red (170-255)
            mask3 = scaled >= 170
            scaled_local = scaled[mask3] - 170
            colored[mask3, 0] = 255  # Red channel
            colored[mask3, 1] = 255 - scaled_local * 3  # Green channel
            colored[mask3, 2] = 0  # Blue channel

            return colored

        except Exception as e:
            logger.error(f"Error creating rainbow colormap: {e}")
            # Return simple grayscale as fallback
            gray_rgb = np.stack([scaled, scaled, scaled], axis=-1)
            return gray_rgb

    def hide_temporarily(self, duration_ms: int = 50):
        """
        Hide overlay temporarily for screen capture.

        Args:
            duration_ms: How long to hide in milliseconds
        """
        if self.overlay:
            self.overlay.withdraw()
            # Schedule reshow
            self.overlay.after(duration_ms, self.show)

    def set_transparency(self, alpha: float):
        """
        Adjust overlay transparency.

        Args:
            alpha: Transparency value (0.0 = invisible, 1.0 = opaque)
        """
        if self.overlay:
            self.overlay.attributes('-alpha', alpha)
    
    def _generate_colored_quality_map(self, quality_map: np.ndarray) -> np.ndarray:
        """
        Generate a colored quality map from quality values.
        
        Args:
            quality_map: 2D array with quality values (0-1)
            
        Returns:
            Colored image as numpy array
        """
        try:
            if self.use_default_colormap or not self.colormap_generator:
                return self._apply_default_colormap(quality_map)
            else:
                return self._apply_custom_colormap(quality_map)
                
        except Exception as e:
            logger.error(f"Error generating colored quality map: {e}")
            return self._apply_default_colormap(quality_map)
    
    def _apply_default_colormap(self, quality_map: np.ndarray) -> np.ndarray:
        """Apply default colormap using OpenCV."""
        try:
            # Normalize to 0-255 range
            normalized = (quality_map * 255).astype(np.uint8)
            
            # Apply colormap (JET colormap: blue=low, red=high)
            colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
            
            # Convert BGR to RGB
            colored_rgb = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
            
            return colored_rgb
            
        except Exception as e:
            logger.error(f"Error applying default colormap: {e}")
            # Fallback: return grayscale
            return (quality_map * 255).astype(np.uint8)
    
    def _apply_custom_colormap(self, quality_map: np.ndarray) -> np.ndarray:
        """Apply custom colormap using the colormap generator."""
        try:
            # Use the colormap generator to create colored image
            if hasattr(self.colormap_generator, 'apply_colormap'):
                colored_image = self.colormap_generator.apply_colormap(
                    quality_map, 
                    spectrum_type='optimized'
                )
                return colored_image
            else:
                # Fallback to default
                return self._apply_default_colormap(quality_map)
                
        except Exception as e:
            logger.error(f"Error applying custom colormap: {e}")
            return self._apply_default_colormap(quality_map)
    
    def hide(self):
        """Hide the quality overlay."""
        if self.overlay:
            self.overlay.withdraw()
    
    def show(self):
        """Show the quality overlay."""
        if self.overlay:
            self.overlay.deiconify()
            self.overlay.lift()
            self.overlay.attributes('-topmost', True)
    
    def move_to_roi(self, new_roi_bounds: Tuple[int, int, int, int]):
        """
        Move the overlay to a new ROI position.
        
        Args:
            new_roi_bounds: New (x1, y1, x2, y2) bounds
        """
        self.roi_bounds = new_roi_bounds
        x1, y1, x2, y2 = new_roi_bounds
        self.roi_width = x2 - x1
        self.roi_height = y2 - y1
        
        # Update window geometry
        if self.overlay:
            self.overlay.geometry(f"{self.roi_width}x{self.roi_height}+{x1}+{y1}")
            
        # Update canvas size
        self.canvas.configure(width=self.roi_width, height=self.roi_height)
        
        logger.info(f"Quality overlay moved to {new_roi_bounds}")
    
    def close(self):
        """Close the quality overlay."""
        try:
            if self.overlay:
                self.overlay.destroy()
                self.overlay = None
            logger.info("Quality overlay closed")
        except Exception as e:
            logger.error(f"Error closing quality overlay: {e}")
    
    def get_current_quality_stats(self) -> Optional[dict]:
        """
        Get statistics about the current quality map.
        
        Returns:
            Dictionary with quality statistics or None if no data
        """
        if self.current_quality_map is None:
            return None
        
        try:
            stats = {
                'mean': float(np.mean(self.current_quality_map)),
                'std': float(np.std(self.current_quality_map)),
                'min': float(np.min(self.current_quality_map)),
                'max': float(np.max(self.current_quality_map)),
                'shape': self.current_quality_map.shape
            }
            return stats
        except Exception as e:
            logger.error(f"Error calculating quality stats: {e}")
            return None
    
    def save_quality_map_image(self, filepath: str) -> bool:
        """
        Save the current quality map visualization to file.
        
        Args:
            filepath: Path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        if not self.quality_image:
            logger.warning("No quality image to save")
            return False
        
        try:
            # Convert PhotoImage back to PIL Image
            # This is a bit tricky, so we'll regenerate from the quality map
            if self.current_quality_map is not None:
                colored_image = self._generate_colored_quality_map(self.current_quality_map)
                pil_image = Image.fromarray(colored_image)
                pil_image.save(filepath)
                logger.info(f"Quality map image saved to {filepath}")
                return True
            else:
                logger.warning("No quality map data to save")
                return False
                
        except Exception as e:
            logger.error(f"Failed to save quality map image: {e}")
            return False