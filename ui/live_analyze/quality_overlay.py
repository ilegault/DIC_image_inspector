# ui/live_analyze/quality_overlay.py - Quality Overlay Display

import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
from typing import Tuple, Optional
import logging
import cv2

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
    
    def update_quality_map(self, quality_map: np.ndarray):
        """
        Update the quality map display.
        
        Args:
            quality_map: 2D numpy array with quality values (0-1)
        """
        try:
            self.current_quality_map = quality_map
            
            # Generate color-mapped image
            colored_image = self._generate_colored_quality_map(quality_map)
            
            # Resize to fit overlay
            if colored_image.shape[:2] != (self.roi_height, self.roi_width):
                colored_image = cv2.resize(
                    colored_image, 
                    (self.roi_width, self.roi_height),
                    interpolation=cv2.INTER_LINEAR
                )
            
            # Convert to PIL Image
            if len(colored_image.shape) == 3:
                pil_image = Image.fromarray(colored_image, 'RGB')
            else:
                pil_image = Image.fromarray(colored_image, 'L')
            
            # Convert to PhotoImage and display
            self.quality_image = ImageTk.PhotoImage(pil_image)
            
            # Clear canvas and draw new image
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor='nw', image=self.quality_image)
            
            logger.debug(f"Quality map updated: {quality_map.shape}")
            
        except Exception as e:
            logger.error(f"Failed to update quality map: {e}")
    
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
    
    def set_transparency(self, alpha: float):
        """
        Set the transparency of the overlay.
        
        Args:
            alpha: Transparency value (0.0 = fully transparent, 1.0 = opaque)
        """
        alpha = max(0.0, min(1.0, alpha))  # Clamp to valid range
        if self.overlay:
            self.overlay.attributes('-alpha', alpha)
    
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