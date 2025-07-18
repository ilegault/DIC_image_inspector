# ui/live_analyze/quality_overlay.py - TRULY STATIC Quality Overlay Display

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
    TRULY STATIC Quality Overlay - window created once, only canvas image updates.
    
    This implementation creates the window structure ONCE and then only updates
    StringVar content and canvas images. No window recreation or layout changes.
    """
    
    def __init__(self, parent_window, roi_bounds: Tuple[int, int, int, int], 
                 colormap_generator=None):
        """
        Create window ONCE - never recreate, only update content.
        
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
        
        # Create window ONCE and NEVER touch it again except content
        self._create_static_window()
        
        # Data that updates
        self.current_quality_map = None
        self.photo = None
        self.canvas_image_item = None  # Track the canvas image item
        self.update_counter = 0
        
        logger.info(f"TrulyStaticQualityOverlay window created ONCE at {roi_bounds}")
    
    def _create_static_window(self):
        """Create the window structure ONCE - never called again."""
        x1, y1, x2, y2 = self.roi_bounds
        
        # Create window ONCE
        self.overlay = tk.Toplevel(self.parent)
        self.overlay.title("🎨 Static Quality Map")
        
        # Set size and position ONCE
        window_width = min(450, max(300, self.roi_width))
        window_height = min(350, max(250, self.roi_height))
        self.overlay.geometry(f"{window_width}x{window_height}+{x1 + 50}+{y1 + 50}")
        self.overlay.attributes('-topmost', True)
        
        # Prevent window from being destroyed - CRITICAL for static behavior
        self.overlay.protocol("WM_DELETE_WINDOW", lambda: self.overlay.withdraw())
        
        # Create ALL UI elements ONCE
        # Header (NEVER changes)
        header_frame = tk.Frame(self.overlay, bg='darkblue', height=30)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🎨 Quality Map - Static Window",
            bg='darkblue',
            fg='white',
            font=('Arial', 11, 'bold')
        ).pack(side='left', padx=5, pady=5)
        
        # Quality info (ONLY text content changes via StringVar)
        self.quality_info_var = tk.StringVar(value="Initializing...")
        tk.Label(
            header_frame,
            textvariable=self.quality_info_var,  # ONLY this variable updates
            bg='darkblue',
            fg='yellow',
            font=('Arial', 9, 'bold')
        ).pack(side='right', padx=5, pady=5)
        
        # Canvas container (NEVER changes structure)
        canvas_frame = tk.Frame(self.overlay, bg='black', relief='sunken', bd=2)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Canvas (ONLY image content changes)
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Status bar (NEVER changes structure)
        status_frame = tk.Frame(self.overlay, bg='gray20', height=25)
        status_frame.pack(fill='x')
        status_frame.pack_propagate(False)
        
        # Status text (ONLY content changes via StringVar)
        self.status_var = tk.StringVar(value="Window created - waiting for quality data...")
        tk.Label(
            status_frame,
            textvariable=self.status_var,  # ONLY this variable updates
            bg='gray20',
            fg='lightgreen',
            font=('Arial', 8)
        ).pack(side='left', padx=5, pady=2)
        
        # Update counter (ONLY content changes via StringVar)
        self.update_count_var = tk.StringVar(value="Updates: 0")
        tk.Label(
            status_frame,
            textvariable=self.update_count_var,  # ONLY this variable updates
            bg='gray20',
            fg='lightblue',
            font=('Arial', 8)
        ).pack(side='right', padx=5, pady=2)
        
        logger.info("Static quality overlay window structure created ONCE")

    def update_quality_map(self, quality_map):
        """Update ONLY the canvas image and text variables - NO window changes."""
        try:
            self.current_quality_map = quality_map
            self.update_counter += 1

            # Get canvas size (should be stable after first time)
            self.canvas.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not ready yet
                self.status_var.set("Canvas initializing...")
                return

            # Convert quality map to image
            colorized = self._quality_map_to_image(quality_map)
            colorized_resized = colorized.resize((canvas_width, canvas_height), Image.Resampling.NEAREST)

            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(colorized_resized)

            # Update canvas image (EFFICIENT - only image data changes)
            if self.canvas_image_item is None:
                # First time - create the image item
                self.canvas_image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
                logger.info("Canvas image item created ONCE")
            else:
                # All subsequent times - just update the image data
                self.canvas.itemconfig(self.canvas_image_item, image=self.photo)

            # Update ONLY the text variables (EFFICIENT - no layout changes)
            avg_quality = np.mean(quality_map)
            min_quality = np.min(quality_map)
            max_quality = np.max(quality_map)

            self.quality_info_var.set(f"Avg: {avg_quality:.3f}")
            self.status_var.set(f"Min: {min_quality:.3f}, Max: {max_quality:.3f}, Shape: {quality_map.shape}")
            self.update_count_var.set(f"Updates: {self.update_counter}")

            logger.debug(f"Quality map updated #{self.update_counter} - ONLY content changed")

        except Exception as e:
            logger.error(f"Error updating quality map content: {e}")
            self.status_var.set(f"Error: {str(e)[:50]}...")

    def _quality_map_to_image(self, quality_map):
        """Convert quality map to colorized image."""
        try:
            normalized = (quality_map * 255).astype(np.uint8)
            height, width = normalized.shape
            colored = np.zeros((height, width, 3), dtype=np.uint8)

            # Rainbow color mapping for better visualization
            for i in range(height):
                for j in range(width):
                    value = normalized[i, j]
                    if value < 85:  # Blue to Cyan
                        colored[i, j] = [0, value * 3, 255]
                    elif value < 170:  # Cyan to Yellow
                        colored[i, j] = [(value - 85) * 3, 255, 255 - (value - 85) * 3]
                    else:  # Yellow to Red
                        colored[i, j] = [255, 255 - (value - 170) * 3, 0]

            return Image.fromarray(colored)
        except Exception as e:
            logger.error(f"Error creating quality image: {e}")
            # Simple fallback
            return Image.new('RGB', (100, 100), (64, 128, 64))

    def hide(self):
        """Hide window without destroying it."""
        if self.overlay:
            self.overlay.withdraw()

    def show(self):
        """Show window without recreating it."""
        if self.overlay:
            self.overlay.deiconify()
            self.overlay.lift()
            self.overlay.attributes('-topmost', True)

    def close(self):
        """Destroy window when truly done."""
        try:
            if self.overlay:
                self.overlay.destroy()
                self.overlay = None
            logger.info("Static quality overlay window destroyed")
        except Exception as e:
            logger.error(f"Error destroying quality overlay: {e}")