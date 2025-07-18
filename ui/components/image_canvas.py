# ui/components/image_canvas.py - Clean Image Display Component

import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import numpy as np
import logging
from typing import Optional, Tuple
from utils.constants import APP_CONFIG, get_theme_colors
from utils.modern_styling import ModernStyleManager

logger = logging.getLogger(__name__)


class ImageCanvas:
    """
    Image canvas component for displaying images and quality maps.

    Handles image display, zooming, panning, and quality map overlays.
    Follows single responsibility principle - only image display concerns.
    """

    def __init__(self, parent: tk.Widget, callbacks: dict = None):
        """
        Initialize image canvas.

        Args:
            parent: Parent widget
            callbacks: Dictionary of callback functions
        """
        self.parent = parent
        self.callbacks = callbacks or {}

        # Display state
        self.displayed_image = None
        self.original_image = None  # The true original image (never modified)
        self.current_image = None   # The currently displayed image (may be blended)
        self.quality_map_data = None
        self.quality_visualization = None
        self.showing_quality_map = False

        # Display properties
        self.zoom_level = 1.0
        self.display_scale = 1.0
        self.photo = None
        self.image_item = None
        
        # Image cache for performance (from canvas test.py)
        self.image_cache = {}
        self.max_cache_size = 10
        
        # Zoom limits (from canvas test.py)
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        # Pan state
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.panning = False

        # ROI selection state (integrated from canvas test.py style)
        self.roi_selection_active = False
        self.ctrl_selection_mode = False  # New: Ctrl+hold selection mode
        self.roi_coords = []  # List of (x, y) tuples in image coordinates
        self.roi_polygon = None
        self.preview_line = None
        
        # ROI visual properties
        self.roi_color = APP_CONFIG['roi']['normal_color']
        self.selection_color = APP_CONFIG['roi']['selection_color']
        self.line_width = APP_CONFIG['roi']['line_width']

        # Create UI
        self._create_canvas_area()
        self._create_processing_controls()
        self._bind_events()

    def _create_canvas_area(self):
        """Create the main canvas area with modern styling."""
        colors = get_theme_colors()

        # Main image panel with modern card-like appearance
        self.image_panel = tk.Frame(
            self.parent,
            bg=colors['panel_bg'],
            relief='flat',
            bd=0
        )
        self.image_panel.pack(fill='both', expand=True, padx=0)

        # Title section with modern styling
        title_frame = tk.Frame(self.image_panel, bg=colors['panel_bg'])
        title_frame.pack(fill='x', padx=APP_CONFIG['styling']['panel_padding'],
                        pady=(APP_CONFIG['styling']['panel_padding'], APP_CONFIG['styling']['small_spacing']))

        img_title = tk.Label(
            title_frame,
            text=" Image Preview",
            font=APP_CONFIG['fonts']['heading'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        img_title.pack(anchor='w')

        # Canvas frame with modern styling
        canvas_frame = tk.Frame(self.image_panel, bg=colors['panel_bg'])
        canvas_frame.pack(fill='both', expand=True,
                         padx=APP_CONFIG['styling']['panel_padding'],
                         pady=(0, APP_CONFIG['styling']['panel_padding']))

        # Canvas with modern styling and subtle border
        canvas_container = tk.Frame(
            canvas_frame,
            bg=colors['panel_border'],
            relief='flat',
            bd=1
        )
        canvas_container.pack(fill='both', expand=True)

        # Inner canvas frame
        inner_canvas_frame = tk.Frame(canvas_container, bg=colors['panel_bg'])
        inner_canvas_frame.pack(fill='both', expand=True, padx=1, pady=1)

        # Canvas with modern styling
        self.canvas = tk.Canvas(
            inner_canvas_frame,
            bg=colors['canvas_bg'],
            width=800,
            height=500,
            highlightthickness=0,
            relief='flat',
            bd=0
        )

        # Use modern styled scrollbars
        self.v_scrollbar, self.h_scrollbar = ModernStyleManager.apply_modern_scrollbars(
            self.canvas, inner_canvas_frame
        )

        self.canvas.configure(
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )

        # Grid layout
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        inner_canvas_frame.grid_rowconfigure(0, weight=1)
        inner_canvas_frame.grid_columnconfigure(0, weight=1)

    def _create_processing_controls(self):
        """Create image processing control buttons."""
        # Processing controls removed - functionality moved to main control panel
        pass

    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Zoom events
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down

        # Pan events - Right click for panning (like canvas test.py)
        self.canvas.bind("<Button-3>", self._start_pan)  # Right click
        self.canvas.bind("<B3-Motion>", self._pan_image)  # Right click motion
        self.canvas.bind("<ButtonRelease-3>", self._end_pan)  # Right click release

        # ROI selection events - Left click for ROI selection
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Motion>", self._on_mouse_motion)

        # Remove keyboard shortcuts to avoid conflicts with Ctrl ROI selection

        # Make canvas focusable for key events
        self.canvas.focus_set()

    def display_image(self, image_data: np.ndarray, preserve_view: bool = False, is_original: bool = True):
        """
        Display an image on the canvas.

        Args:
            image_data: Image as numpy array (NOT ImageData object)
            preserve_view: Whether to preserve current zoom/pan
            is_original: Whether this is the original image (not a processed/blended version)
        """
        try:
            logger.debug(f"Display image: preserve_view={preserve_view}, is_original={is_original}")
            
            # Clear any existing image items
            self.canvas.delete("all")
            
            # Clear cache when new image loaded
            self.image_cache.clear()

            # Handle both numpy array and ImageData object
            if hasattr(image_data, 'array'):
                # It's an ImageData object, extract the array
                image_array = image_data.array
                logger.debug("Display image: Extracted array from ImageData object")
            else:
                # It's already a numpy array
                image_array = image_data
                logger.debug("Display image: Using numpy array directly")

            # Validate image array
            if not isinstance(image_array, np.ndarray):
                raise ValueError("Image must be a numpy array")

            logger.debug(f"Display image: Original array shape: {image_array.shape}, dtype: {image_array.dtype}")

            # Convert to uint8 if necessary
            if image_array.dtype != np.uint8:
                image_array = np.clip(image_array, 0, 255).astype(np.uint8)
                logger.debug("Display image: Converted to uint8")

            # Store current image
            self.current_image = image_array.copy()

            # Store as original image only if this is truly the original
            if is_original:
                self.original_image = image_array.copy()
                logger.debug("Display image: Stored as original image")

            # Convert grayscale to RGB if needed
            if len(image_array.shape) == 2:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
                logger.debug("Display image: Converted grayscale to RGB")
            elif len(image_array.shape) == 3 and image_array.shape[2] == 4:
                # Convert RGBA to RGB
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
                logger.debug("Display image: Converted RGBA to RGB")

            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(image_array)
            logger.debug(f"Display image: PIL image size: {pil_image.size}")

            # Store as displayed image
            self.displayed_image = pil_image

            # Calculate initial display scale if not preserving view
            if not preserve_view:
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                logger.debug(f"Display image: Canvas size: {canvas_width}x{canvas_height}")

                # Use default size if canvas not yet rendered
                if canvas_width <= 1:
                    canvas_width = 800
                    logger.debug("Display image: Using default canvas width 800")
                if canvas_height <= 1:
                    canvas_height = 500
                    logger.debug("Display image: Using default canvas height 500")

                img_width, img_height = pil_image.size
                logger.debug(f"Display image: Image size: {img_width}x{img_height}")

                # Calculate scale to fit image in canvas
                scale_x = canvas_width / img_width
                scale_y = canvas_height / img_height
                self.display_scale = min(scale_x, scale_y) * 0.9  # 90% to leave margin
                logger.debug(f"Display image: Scale factors - x: {scale_x:.3f}, y: {scale_y:.3f}")
                logger.debug(f"Display image: Final display scale: {self.display_scale:.3f}")

                # Reset zoom level
                self.zoom_level = 1.0
                logger.debug("Display image: Reset zoom level to 1.0")
            else:
                logger.debug(f"Display image: Preserving view - current zoom: {self.zoom_level}, display_scale: {self.display_scale}")

            # Create the photo image
            display_width = int(pil_image.width * self.display_scale * self.zoom_level)
            display_height = int(pil_image.height * self.display_scale * self.zoom_level)
            
            logger.debug(f"Display image: Calculated display size: {display_width}x{display_height}")

            # Ensure minimum size
            display_width = max(1, display_width)
            display_height = max(1, display_height)

            if display_width != pil_image.width or display_height != pil_image.height:
                resized_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                logger.debug(f"Display image: Resized image to {display_width}x{display_height}")
            else:
                resized_image = pil_image
                logger.debug("Display image: Using original image size")

            self.photo = ImageTk.PhotoImage(resized_image)
            logger.debug(f"Display image: Created PhotoImage: {self.photo.width()}x{self.photo.height()}")
            
            # Keep a reference to prevent garbage collection
            self.canvas.image = self.photo

            # Update canvas size and display image
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            logger.debug(f"Display image: Canvas actual size: {canvas_width}x{canvas_height}")

            if display_width <= canvas_width and display_height <= canvas_height:
                # Center the image
                x = (canvas_width - display_width) // 2
                y = (canvas_height - display_height) // 2
                logger.debug(f"Display image: Centering image at ({x}, {y})")
                
                self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
                self.image_item = self.canvas.create_image(x, y, anchor='nw', image=self.photo)
                logger.debug(f"Display image: Created image item {self.image_item}")
                
                # Verify the image was created successfully
                try:
                    bbox = self.canvas.bbox(self.image_item)
                    logger.debug(f"Display image: Image item bbox: {bbox}")
                except Exception as e:
                    logger.error(f"Display image: Error getting bbox: {e}")

                # Store offsets for coordinate conversion
                self.image_offset_x = x
                self.image_offset_y = y
                self.canvas.image_offset_x = x
                self.canvas.image_offset_y = y
            else:
                # Image larger than canvas - use scrolling
                logger.debug(f"Display image: Image larger than canvas, using scrolling")
                self.canvas.configure(scrollregion=(0, 0, display_width, display_height))
                self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
                logger.debug(f"Display image: Created scrollable image item {self.image_item}")
                
                # Verify the image was created successfully
                try:
                    bbox = self.canvas.bbox(self.image_item)
                    logger.debug(f"Display image: Scrollable image item bbox: {bbox}")
                except Exception as e:
                    logger.error(f"Display image: Error getting scrollable bbox: {e}")

                # No offset when scrolling
                self.image_offset_x = 0
                self.image_offset_y = 0
                self.canvas.image_offset_x = 0
                self.canvas.image_offset_y = 0

            # Store display scale on canvas for ROI selector
            self.canvas.display_scale = self.display_scale * self.zoom_level

            # Notify zoom change
            self._notify_zoom_changed()

            # Clear quality map state
            self.quality_map_data = None
            self.quality_visualization = None
            self.showing_quality_map = False
            
            # Force canvas update
            self.canvas.update_idletasks()
            logger.debug("Display image: Canvas update completed")

        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"Error displaying image: {e}")
            traceback.print_exc()

    def refresh_theme(self):
        """Refresh canvas with new theme colors."""
        colors = get_theme_colors()

        # Update canvas background
        self.canvas.configure(bg=colors['canvas_bg'])

        # Update the image panel and its children
        self.image_panel.configure(bg=colors['panel_bg'])

        # Update all the frames in the hierarchy
        for widget in self.image_panel.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=colors['panel_bg'])
            elif isinstance(widget, tk.Label):
                widget.configure(
                    bg=colors['panel_bg'],
                    fg=colors['text_primary']
                )

        # Update scrollbar styling if they exist
        if hasattr(self, 'v_scrollbar') and hasattr(self, 'h_scrollbar'):
            # Re-apply modern scrollbar styling
            style = ttk.Style()
            style.configure(
                'Modern.Vertical.TScrollbar',
                background=colors['panel_bg'],
                troughcolor=colors['hover_bg'],
                borderwidth=0,
                arrowcolor=colors['text_secondary']
            )
            style.configure(
                'Modern.Horizontal.TScrollbar',
                background=colors['panel_bg'],
                troughcolor=colors['hover_bg'],
                borderwidth=0,
                arrowcolor=colors['text_secondary']
            )

        # Force canvas update
        self.canvas.update_idletasks()

    def show_quality_map(self, quality_map_data: np.ndarray, spectrum_type: str):
        """
        Show quality map overlay.

        Args:
            quality_map_data: Quality map data (0-1 normalized)
            spectrum_type: Color spectrum type to use
        """
        if quality_map_data is None or self.original_image is None:
            return

        # Store quality map data
        self.quality_map_data = quality_map_data

        # Generate quality visualization
        try:
            from analysis.quality_map.colormap import apply_dic_colormap

            # Apply colormap
            colored_map = apply_dic_colormap(quality_map_data, spectrum_type)

            # Always blend with original image to avoid multiple overlays
            alpha = 0.7  # Default alpha value for quality map overlay
            blended = self._blend_images(self.original_image, colored_map, alpha)

            # Display blended image (not original)
            self.display_image(blended, preserve_view=True, is_original=False)
            self.showing_quality_map = True
            logger.debug("Quality map displayed, showing_quality_map set to True")

        except Exception as e:
            print(f"Error showing quality map: {e}")
            import traceback
            traceback.print_exc()

    def _position_and_display_image(self):
        """Position and display the image on canvas."""
        # Force canvas update to get accurate dimensions
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Use reasonable defaults if canvas not rendered yet
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 500

        img_width = self.photo.width()
        img_height = self.photo.height()

        # Calculate positioning for proper centering
        if img_width <= canvas_width and img_height <= canvas_height:
            # Image fits entirely in canvas - center it directly
            center_x = (canvas_width - img_width) // 2
            center_y = (canvas_height - img_height) // 2

            # Set scroll region to canvas size for proper centering
            self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
            self.image_item = self.canvas.create_image(center_x, center_y, anchor='nw', image=self.photo)

            # Store offset for other components
            self.image_offset_x = center_x
            self.image_offset_y = center_y
            self.canvas.image_offset_x = center_x
            self.canvas.image_offset_y = center_y

            # No scrolling needed - image is centered
            self.canvas.xview_moveto(0.0)
            self.canvas.yview_moveto(0.0)

        else:
            # Image is larger than canvas - use scroll region approach
            self.canvas.configure(scrollregion=(0, 0, img_width, img_height))
            self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

            # No offset when using scroll regions
            self.image_offset_x = 0
            self.image_offset_y = 0
            self.canvas.image_offset_x = 0
            self.canvas.image_offset_y = 0

            # Center the view on the image
            if img_width > canvas_width:
                # Image is wider - center horizontally
                center_ratio_x = 0.5
            else:
                # Image fits horizontally - no horizontal scrolling needed
                center_ratio_x = 0.0

            if img_height > canvas_height:
                # Image is taller - center vertically
                center_ratio_y = 0.5
            else:
                # Image fits vertically - no vertical scrolling needed
                center_ratio_y = 0.0

            self.canvas.xview_moveto(center_ratio_x)
            self.canvas.yview_moveto(center_ratio_y)

        # Debug for large original images
        if hasattr(self, 'original_image') and self.original_image is not None:
            orig_h, orig_w = self.original_image.shape[:2]
            if max(orig_w, orig_h) > 1000:
                if img_width <= canvas_width and img_height <= canvas_height:
                    logger.debug(f"Image centered directly - Canvas: {canvas_width}x{canvas_height}, "
                          f"Display: {img_width}x{img_height}, Position: ({center_x}, {center_y})")
                else:
                    logger.debug(f"Image scrollable - Canvas: {canvas_width}x{canvas_height}, "
                          f"Display: {img_width}x{img_height}, Scroll region: {img_width}x{img_height}")

    def _on_mousewheel(self, event):
        """Handle mouse wheel zoom."""
        if self.displayed_image is None:
            return "break"

        # Store old zoom
        old_zoom = self.zoom_level

        # Calculate new zoom with multiplicative increments (smoother)
        # Handle different event types for cross-platform compatibility
        if hasattr(event, 'delta'):
            # Windows
            if event.delta < 0:  # Zoom out
                self.zoom_level = max(self.min_zoom, self.zoom_level * 0.9)
                direction = "out"
            else:  # Zoom in
                self.zoom_level = min(self.max_zoom, self.zoom_level * 1.1)
                direction = "in"
        else:
            # Linux - Button-4 is scroll up (zoom in), Button-5 is scroll down (zoom out)
            if event.num == 5:  # Zoom out
                self.zoom_level = max(self.min_zoom, self.zoom_level * 0.9)
                direction = "out"
            else:  # Zoom in
                self.zoom_level = min(self.max_zoom, self.zoom_level * 1.1)
                direction = "in"

        if abs(self.zoom_level - old_zoom) < 0.001:
            return "break"

        # Get mouse position and canvas dimensions
        mouse_x = event.x
        mouse_y = event.y
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Get current scroll positions
        xview = self.canvas.xview()
        yview = self.canvas.yview()

        # Calculate the point in the image that the mouse is over (in pixels of original image)
        # This is the point we want to keep fixed during zoom
        scroll_left = xview[0]
        scroll_top = yview[0]
        view_width = xview[1] - xview[0]
        view_height = yview[1] - yview[0]

        # Mouse position as fraction of visible area
        mouse_frac_x = mouse_x / canvas_width if canvas_width > 0 else 0.5
        mouse_frac_y = mouse_y / canvas_height if canvas_height > 0 else 0.5

        # Convert to fraction of total image
        image_frac_x = scroll_left + mouse_frac_x * view_width
        image_frac_y = scroll_top + mouse_frac_y * view_height

        # Update display with new zoom
        self._update_display_improved()

        # After zoom, calculate where to scroll to keep the same image point under mouse
        new_image_width = self.displayed_image.width * self.display_scale * self.zoom_level
        new_image_height = self.displayed_image.height * self.display_scale * self.zoom_level

        # Only adjust scroll if image is larger than canvas
        if new_image_width > canvas_width:
            # Calculate what fraction of the image should be visible
            new_view_width = canvas_width / new_image_width
            # Calculate scroll position to keep image point under mouse
            new_scroll_x = image_frac_x - mouse_frac_x * new_view_width
            new_scroll_x = max(0, min(new_scroll_x, 1 - new_view_width))
            self.canvas.xview_moveto(new_scroll_x)
        else:
            # Image fits in canvas - center it
            self.canvas.xview_moveto(0)

        if new_image_height > canvas_height:
            # Calculate what fraction of the image should be visible
            new_view_height = canvas_height / new_image_height
            # Calculate scroll position to keep image point under mouse
            new_scroll_y = image_frac_y - mouse_frac_y * new_view_height
            new_scroll_y = max(0, min(new_scroll_y, 1 - new_view_height))
            self.canvas.yview_moveto(new_scroll_y)
        else:
            # Image fits in canvas - center it
            self.canvas.yview_moveto(0)

        # Notify zoom change
        self._notify_zoom_changed()
        
        # Redraw ROI after zoom
        self.redraw_roi()
        
        logger.debug(f"Zoomed {direction} to {self.zoom_level:.2f}x at mouse position ({mouse_x}, {mouse_y})")
        
        return "break"

    def _update_display_improved(self):
        """Update the displayed image based on current zoom level (improved from canvas test.py)."""
        if self.displayed_image is None:
            return

        # Calculate new size
        orig_width, orig_height = self.displayed_image.size
        new_width = int(orig_width * self.display_scale * self.zoom_level)
        new_height = int(orig_height * self.display_scale * self.zoom_level)

        # Create cache key
        cache_key = (new_width, new_height)

        # Check cache first
        if cache_key in self.image_cache:
            self.photo = self.image_cache[cache_key]
            logger.debug(f"Using cached image for size {new_width}x{new_height}")
        else:
            # Resize image - use NEAREST for speed during interactive zoom
            if abs(self.zoom_level - 1.0) < 0.001:
                resized = self.displayed_image
            else:
                # Use NEAREST for speed, or BILINEAR for better quality but slower
                resample = Image.Resampling.BILINEAR if self.zoom_level < 1.0 else Image.Resampling.NEAREST
                resized = self.displayed_image.resize((new_width, new_height), resample)

            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(resized)

            # Add to cache
            self.image_cache[cache_key] = self.photo

            # Limit cache size
            if len(self.image_cache) > self.max_cache_size:
                # Remove oldest entries
                oldest_keys = list(self.image_cache.keys())[:-self.max_cache_size]
                for key in oldest_keys:
                    del self.image_cache[key]
                logger.debug(f"Cache cleaned, removed {len(oldest_keys)} entries")

        # Update canvas
        if self.image_item is None:
            self.image_item = self.canvas.create_image(0, 0, image=self.photo, anchor='nw')
        else:
            self.canvas.itemconfig(self.image_item, image=self.photo)

        # Update scroll region
        self.canvas.config(scrollregion=self.canvas.bbox('all'))

        # Update display scale for ROI selector
        self.canvas.display_scale = self.display_scale * self.zoom_level
        
        # Redraw ROI after display update
        self.redraw_roi()
        
        logger.debug(f"Display updated - Size: {new_width}x{new_height}, Zoom: {self.zoom_level:.2f}x")

    def _apply_zoom_at_point(self, old_zoom: float, mouse_x: float, mouse_y: float):
        """Apply zoom transformation centered at a specific point."""
        if not self.displayed_image:
            logger.debug("Apply zoom: No displayed image")
            return

        # Get current scroll position and canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        logger.debug(f"Apply zoom: Canvas dimensions: {canvas_width}x{canvas_height}")

        # Use reasonable defaults if canvas not rendered yet
        if canvas_width <= 1:
            canvas_width = 800
            logger.debug("Apply zoom: Using default canvas width 800")
        if canvas_height <= 1:
            canvas_height = 500
            logger.debug("Apply zoom: Using default canvas height 500")

        # Calculate old and new image dimensions using both display_scale and zoom_level
        old_width = int(self.displayed_image.width * self.display_scale * old_zoom)
        old_height = int(self.displayed_image.height * self.display_scale * old_zoom)

        base_width = self.displayed_image.width
        base_height = self.displayed_image.height
        new_width = max(1, int(base_width * self.display_scale * self.zoom_level))
        new_height = max(1, int(base_height * self.display_scale * self.zoom_level))
        
        logger.debug(f"Apply zoom: Image base size: {base_width}x{base_height}")
        logger.debug(f"Apply zoom: Display scale: {self.display_scale}")
        logger.debug(f"Apply zoom: Old zoom: {old_zoom}, New zoom: {self.zoom_level}")
        logger.debug(f"Apply zoom: Old dimensions: {old_width}x{old_height}")
        logger.debug(f"Apply zoom: New dimensions: {new_width}x{new_height}")
        logger.debug(f"Apply zoom: Mouse position: ({mouse_x}, {mouse_y})")

        # Resize image
        if new_width == self.displayed_image.width and new_height == self.displayed_image.height:
            resized_image = self.displayed_image
        else:
            resized_image = self.displayed_image.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS
            )

        # Update photo
        self.photo = ImageTk.PhotoImage(resized_image)

        # Update canvas and position image properly
        if self.image_item:
            self.canvas.delete(self.image_item)

        # Handle positioning based on image size relative to canvas
        if new_width <= canvas_width and new_height <= canvas_height:
            # Image fits entirely in canvas - center it directly
            center_x = (canvas_width - new_width) // 2
            center_y = (canvas_height - new_height) // 2
            
            logger.debug(f"Apply zoom: Image fits in canvas - centering at ({center_x}, {center_y})")

            # Set scroll region to canvas size for proper centering
            self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
            self.image_item = self.canvas.create_image(center_x, center_y, anchor='nw', image=self.photo)

            # Store offset for other components
            self.image_offset_x = center_x
            self.image_offset_y = center_y
            self.canvas.image_offset_x = center_x
            self.canvas.image_offset_y = center_y
            
            logger.debug(f"Apply zoom: Set image offsets to ({center_x}, {center_y})")

            # No scrolling needed - image is centered
            self.canvas.xview_moveto(0.0)
            self.canvas.yview_moveto(0.0)
            logger.debug("Apply zoom: Reset scroll position to (0.0, 0.0)")

        else:
            # Image is larger than canvas - use scroll region approach
            logger.debug(f"Apply zoom: Image larger than canvas - using scroll regions")
            self.canvas.configure(scrollregion=(0, 0, new_width, new_height))
            self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

            # No offset when using scroll regions
            self.image_offset_x = 0
            self.image_offset_y = 0
            self.canvas.image_offset_x = 0
            self.canvas.image_offset_y = 0
            logger.debug("Apply zoom: Set image offsets to (0, 0) for scrollable image")

            # For large images, try to maintain the zoom center
            # Use a simpler approach to avoid coordinate system confusion
            try:
                if old_width > 0 and old_height > 0:
                    # Calculate the center point of the current view
                    if old_width <= canvas_width and old_height <= canvas_height:
                        # Old image was centered - use canvas center as zoom point
                        center_x_ratio = 0.5
                        center_y_ratio = 0.5
                        logger.debug("Apply zoom: Old image was centered, using canvas center as zoom point")
                    else:
                        # Old image was scrollable - get current view center
                        current_scroll_x = self.canvas.xview()[0]
                        current_scroll_y = self.canvas.yview()[0]
                        view_width = self.canvas.xview()[1] - self.canvas.xview()[0]
                        view_height = self.canvas.yview()[1] - self.canvas.yview()[0]
                        center_x_ratio = current_scroll_x + view_width / 2
                        center_y_ratio = current_scroll_y + view_height / 2
                        logger.debug(f"Apply zoom: Old image scrollable - current scroll: ({current_scroll_x:.3f}, {current_scroll_y:.3f})")
                        logger.debug(f"Apply zoom: View size: {view_width:.3f}x{view_height:.3f}")
                        logger.debug(f"Apply zoom: Calculated center ratio: ({center_x_ratio:.3f}, {center_y_ratio:.3f})")

                    # Calculate new scroll position to keep the same center
                    # Only calculate scroll if the new image is larger than canvas
                    if new_width > canvas_width:
                        new_scroll_x = max(0, min(1, center_x_ratio - (canvas_width / new_width) / 2))
                    else:
                        new_scroll_x = 0

                    if new_height > canvas_height:
                        new_scroll_y = max(0, min(1, center_y_ratio - (canvas_height / new_height) / 2))
                    else:
                        new_scroll_y = 0
                    
                    logger.debug(f"Apply zoom: New scroll position: ({new_scroll_x:.3f}, {new_scroll_y:.3f})")

                    self.canvas.xview_moveto(new_scroll_x)
                    self.canvas.yview_moveto(new_scroll_y)
                else:
                    # No old dimensions - center the image
                    logger.debug("Apply zoom: No old dimensions, centering image")
                    self.canvas.xview_moveto(0.5)
                    self.canvas.yview_moveto(0.5)
            except Exception as e:
                # Fallback to centering if anything goes wrong
                logger.error(f"Apply zoom: Positioning error: {e}")
                import traceback
                logger.debug(f"Apply zoom: Traceback: {traceback.format_exc()}")
                self.canvas.xview_moveto(0.5)
                self.canvas.yview_moveto(0.5)

        # Update display scale
        self.canvas.display_scale = self.display_scale * self.zoom_level

    def _notify_zoom_changed(self):
        """Notify that zoom level has changed."""
        if 'zoom_changed' in self.callbacks:
            self.callbacks['zoom_changed'](self.zoom_level)

    def _start_pan(self, event):
        """Start panning operation (improved from canvas test.py)."""
        self.canvas.config(cursor="fleur")
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.panning = True
        logger.debug(f"Pan started at ({event.x}, {event.y})")

    def _pan_image(self, event):
        """Pan the image during mouse motion (improved from canvas test.py)."""
        if not self.panning:
            return

        # Calculate movement in screen pixels
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y

        # Update pan start position
        self.pan_start_x = event.x
        self.pan_start_y = event.y

        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Use reasonable defaults if canvas not rendered yet
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 500

        # Get current view bounds
        x_view = self.canvas.xview()
        y_view = self.canvas.yview()

        # Calculate the visible fraction of the image
        x_visible_fraction = x_view[1] - x_view[0]
        y_visible_fraction = y_view[1] - y_view[0]

        # Calculate movement as a fraction of the visible area
        if x_visible_fraction < 1.0:  # Only pan if image is larger than canvas
            x_delta = (dx / canvas_width) * x_visible_fraction
            new_x = x_view[0] - x_delta
            new_x = max(0, min(new_x, 1 - x_visible_fraction))
            self.canvas.xview_moveto(new_x)

        if y_visible_fraction < 1.0:  # Only pan if image is larger than canvas
            y_delta = (dy / canvas_height) * y_visible_fraction
            new_y = y_view[0] - y_delta
            new_y = max(0, min(new_y, 1 - y_visible_fraction))
            self.canvas.yview_moveto(new_y)

    def _end_pan(self, event):
        """End panning operation."""
        self.panning = False
        self.canvas.config(cursor="")
        logger.debug("Pan ended")
        
        # Redraw ROI after panning
        self.redraw_roi()







    def _add_roi_point(self, event):
        """Add a point to the ROI selection."""
        logger.debug(f"_add_roi_point called, roi_selection_active: {self.roi_selection_active}")
        if not self.roi_selection_active:
            return

        # Get image coordinates
        try:
            image_x, image_y = self._canvas_to_image_coords(event.x, event.y)
            logger.debug(f"Canvas coords: ({event.x}, {event.y}) -> Image coords: ({image_x:.1f}, {image_y:.1f})")
            
            # Add point if within image bounds
            if image_x >= 0 and image_y >= 0:
                self.roi_coords.append((image_x, image_y))
                logger.debug(f"Added ROI point {len(self.roi_coords)}: ({image_x:.1f}, {image_y:.1f})")
                
                # Redraw ROI
                self._redraw_roi()
                
                # Notify callbacks
                if 'roi_changed' in self.callbacks:
                    self.callbacks['roi_changed'](self.roi_coords.copy())
            else:
                logger.debug(f"Point outside image bounds: ({image_x:.1f}, {image_y:.1f})")

        except Exception as e:
            logger.error(f"Error adding ROI point: {e}")

    def _update_roi_preview(self, event):
        """Update ROI preview line during mouse motion."""
        if not self.roi_selection_active or not self.roi_coords:
            return

        try:
            # Get image coordinates for preview
            image_x, image_y = self._canvas_to_image_coords(event.x, event.y)
            
            # Redraw with preview
            self._redraw_roi(preview_point=(image_x, image_y))

        except Exception as e:
            logger.error(f"Error in ROI preview: {e}")

    def _finish_roi_selection(self):
        """Finish ROI selection."""
        logger.debug(f"Finishing ROI polygon with {len(self.roi_coords)} points")

        # Exit selection mode
        self.roi_selection_active = False
        self.ctrl_selection_mode = False
        self.canvas.config(cursor="")

        # Draw final polygon
        self._redraw_roi(finalize=True)

        # Notify callbacks
        if 'roi_completed' in self.callbacks:
            self.callbacks['roi_completed'](self.roi_coords.copy())

    def _redraw_roi(self, preview_point=None, finalize=False):
        """Redraw the ROI polygon and preview line."""
        # Remove previous drawings
        if self.roi_polygon:
            self.canvas.delete(self.roi_polygon)
            self.roi_polygon = None
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            self.preview_line = None

        if not self.roi_coords:
            return

        # Convert image coordinates to canvas coordinates
        canvas_coords = []
        for image_x, image_y in self.roi_coords:
            canvas_x, canvas_y = self._image_to_canvas_coords(image_x, image_y)
            canvas_coords.append((canvas_x, canvas_y))

        # Draw polygon or line
        if len(canvas_coords) >= 2:
            # Flatten coordinates for canvas methods
            flat_coords = [coord for point in canvas_coords for coord in point]

            if finalize and len(canvas_coords) >= 3:
                # Draw filled polygon
                self.roi_polygon = self.canvas.create_polygon(
                    *flat_coords,
                    outline=self.roi_color,
                    fill='',
                    width=self.line_width
                )
            else:
                # Draw line
                self.roi_polygon = self.canvas.create_line(
                    *flat_coords,
                    fill=self.selection_color,
                    width=self.line_width
                )

        # Draw preview line
        if preview_point and canvas_coords:
            last_canvas_x, last_canvas_y = canvas_coords[-1]
            preview_canvas_x, preview_canvas_y = self._image_to_canvas_coords(*preview_point)

            self.preview_line = self.canvas.create_line(
                last_canvas_x, last_canvas_y,
                preview_canvas_x, preview_canvas_y,
                fill=self.selection_color,
                dash=(5, 5),
                width=self.line_width
            )

    def _clear_roi(self):
        """Clear the current ROI selection."""
        # Remove visual elements
        if self.roi_polygon:
            self.canvas.delete(self.roi_polygon)
            self.roi_polygon = None
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            self.preview_line = None

        # Reset state
        self.roi_coords = []
        self.roi_selection_active = False
        self.ctrl_selection_mode = False
        self.canvas.config(cursor="")

    def _clear_roi_for_ctrl_selection(self):
        """Clear ROI for starting a new ctrl selection (preserves ctrl_selection_mode)."""
        # Remove visual elements
        if self.roi_polygon:
            self.canvas.delete(self.roi_polygon)
            self.roi_polygon = None
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            self.preview_line = None

        # Reset coordinates but preserve ctrl selection state
        self.roi_coords = []

        # Notify callbacks
        if 'roi_changed' in self.callbacks:
            self.callbacks['roi_changed']([])

    def _canvas_to_image_coords(self, canvas_x: int, canvas_y: int):
        """Convert canvas coordinates to original image coordinates."""
        # Get canvas-relative coordinates
        canvas_x = self.canvas.canvasx(canvas_x)
        canvas_y = self.canvas.canvasy(canvas_y)

        # Get display scale and offset from canvas
        display_scale = getattr(self.canvas, 'display_scale', self.display_scale * self.zoom_level)
        offset_x = getattr(self.canvas, 'image_offset_x', 0)
        offset_y = getattr(self.canvas, 'image_offset_y', 0)

        # Adjust for image offset
        canvas_x -= offset_x
        canvas_y -= offset_y

        # Convert to original image coordinates
        if display_scale <= 0:
            display_scale = 1.0
            
        image_x = canvas_x / display_scale
        image_y = canvas_y / display_scale

        return image_x, image_y

    def _image_to_canvas_coords(self, image_x: float, image_y: float):
        """Convert original image coordinates to canvas coordinates."""
        # Get display scale and offset from canvas
        display_scale = getattr(self.canvas, 'display_scale', self.display_scale * self.zoom_level)
        offset_x = getattr(self.canvas, 'image_offset_x', 0)
        offset_y = getattr(self.canvas, 'image_offset_y', 0)

        # Convert from original image coordinates to canvas coordinates
        if display_scale <= 0:
            display_scale = 1.0
            
        canvas_x = image_x * display_scale + offset_x
        canvas_y = image_y * display_scale + offset_y

        return canvas_x, canvas_y

    # Public ROI methods for integration with existing ROI selector
    def start_roi_selection(self):
        """Start ROI selection mode (for external calls)."""
        self._clear_roi()
        self.roi_selection_active = True
        self.canvas.config(cursor="crosshair")

    def clear_roi(self):
        """Clear ROI selection (for external calls)."""
        self._clear_roi()

    def get_roi_coordinates(self):
        """Get current ROI coordinates."""
        return self.roi_coords.copy()

    def has_roi(self):
        """Check if ROI is currently defined."""
        return len(self.roi_coords) >= 3

    def update_roi_display(self, roi_data):
        """Update ROI display with new data."""
        if hasattr(roi_data, 'coordinates'):
            self.roi_coords = roi_data.coordinates.copy()
            self._redraw_roi(finalize=True)
        else:
            self._clear_roi()

    def redraw_roi(self):
        """Redraw the ROI polygon after view changes (zoom, pan)."""
        if self.roi_coords and not self.roi_selection_active:
            self._redraw_roi(finalize=True)

    def _on_left_click(self, event):
        """Handle left mouse click - add ROI point or focus canvas."""
        # Check if Ctrl is held down for Ctrl selection mode
        ctrl_held = (event.state & 0x4) != 0  # Check Ctrl modifier
        logger.debug(f"Left click detected, ctrl_held: {ctrl_held}, roi_selection_active: {self.roi_selection_active}")
        
        if ctrl_held and not self.roi_selection_active:
            # Start Ctrl selection mode
            logger.debug("Starting Ctrl selection from left click")
            self.start_ctrl_selection()
        
        if self.roi_selection_active:
            # Add ROI point
            logger.debug("Adding ROI point from left click")
            self._add_roi_point(event)
        else:
            # Just focus the canvas for other interactions
            logger.debug("Focusing canvas")
            self.canvas.focus_set()

    def _on_mouse_motion(self, event):
        """Handle mouse motion - show preview line during ROI selection."""
        if self.roi_selection_active and self.roi_coords:
            self._update_roi_preview(event)

    def start_ctrl_selection(self):
        """Start Ctrl+hold ROI selection mode."""
        if not self.ctrl_selection_mode and not self.roi_selection_active:
            logger.debug("Starting Ctrl ROI selection mode")
            self.ctrl_selection_mode = True
            
            # Clear any existing ROI (but preserve ctrl_selection_mode)
            self._clear_roi_for_ctrl_selection()
            
            # Enter selection mode
            self.roi_selection_active = True
            self.canvas.config(cursor="crosshair")
            
            # Notify callbacks
            self._execute_callback('roi_changed', [])
        else:
            logger.debug(f"Ctrl selection already active (ctrl_mode: {self.ctrl_selection_mode}, roi_active: {self.roi_selection_active}), ignoring duplicate start call")

    def end_ctrl_selection(self):
        """End Ctrl+hold ROI selection mode."""
        logger.debug(f"end_ctrl_selection called: ctrl_mode={self.ctrl_selection_mode}, roi_active={self.roi_selection_active}, points={len(self.roi_coords)}")
        if self.ctrl_selection_mode:
            logger.debug(f"Ending Ctrl ROI selection mode with {len(self.roi_coords)} points")
            self.ctrl_selection_mode = False
            
            # Auto-complete ROI if we have enough points (minimum 3 for a polygon)
            if len(self.roi_coords) >= 3:
                logger.debug("Auto-completing ROI polygon by connecting last point to first")
                # The polygon will be automatically closed when we finish selection
                self._finish_roi_selection()
            else:
                # Not enough points, cancel selection
                logger.debug("Not enough points for ROI, canceling selection")
                self._clear_roi()
        else:
            logger.debug("end_ctrl_selection called but ctrl_selection_mode is False")

    def handle_key_event(self, event_type: str, key: str):
        """
        Handle key events from parent window.
        
        Args:
            event_type: 'press' or 'release'
            key: Key name (e.g., 'Control_L', 'Control_R')
        """
        logger.debug(f"ImageCanvas.handle_key_event: {event_type} {key}")
        if key in ['Control_L', 'Control_R']:
            if event_type == 'press':
                logger.debug("Starting Ctrl selection from handle_key_event")
                self.start_ctrl_selection()
            elif event_type == 'release':
                logger.debug("Ending Ctrl selection from handle_key_event")
                self.end_ctrl_selection()

    def _execute_callback(self, callback_name: str, *args):
        """Execute callback if it exists."""
        if callback_name in self.callbacks:
            try:
                self.callbacks[callback_name](*args)
            except Exception as e:
                logger.error(f"Error executing callback {callback_name}: {e}")





    # Public zoom control methods
    def zoom_in(self):
        """Zoom in programmatically."""
        if not self.displayed_image:
            return

        # Get canvas center for zoom point
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Convert to canvas coordinates
        mouse_x = self.canvas.canvasx(center_x)
        mouse_y = self.canvas.canvasy(center_y)

        old_zoom = self.zoom_level
        self.zoom_level = min(2.0, self.zoom_level + 0.1)
        self._apply_zoom_at_point(old_zoom, mouse_x, mouse_y)
        self._notify_zoom_changed()

    def zoom_out(self):
        """Zoom out programmatically."""
        if not self.displayed_image:
            return

        # Get canvas center for zoom point
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Convert to canvas coordinates
        mouse_x = self.canvas.canvasx(center_x)
        mouse_y = self.canvas.canvasy(center_y)

        old_zoom = self.zoom_level
        self.zoom_level = max(0.1, self.zoom_level - 0.1)
        self._apply_zoom_at_point(old_zoom, mouse_x, mouse_y)
        self._notify_zoom_changed()

    def zoom_fit(self):
        """Fit image to canvas programmatically."""
        if not self.displayed_image:
            return

        # Calculate fit zoom level
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        img_width = self.displayed_image.width
        img_height = self.displayed_image.height

        # Calculate zoom to fit
        zoom_x = canvas_width / img_width
        zoom_y = canvas_height / img_height
        fit_zoom = min(zoom_x, zoom_y) * 0.9  # 90% to leave some margin

        old_zoom = self.zoom_level
        self.zoom_level = max(0.1, min(2.0, fit_zoom))

        # Center the zoom
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        mouse_x = self.canvas.canvasx(center_x)
        mouse_y = self.canvas.canvasy(center_y)

        self._apply_zoom_at_point(old_zoom, mouse_x, mouse_y)
        self._notify_zoom_changed()

    def zoom_actual(self):
        """Zoom to actual size (100%) programmatically."""
        if not self.displayed_image:
            return

        # Get canvas center for zoom point
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Convert to canvas coordinates
        mouse_x = self.canvas.canvasx(center_x)
        mouse_y = self.canvas.canvasy(center_y)

        old_zoom = self.zoom_level
        self.zoom_level = 1.0
        self._apply_zoom_at_point(old_zoom, mouse_x, mouse_y)
        self._notify_zoom_changed()

    def get_zoom_level(self):
        """Get current zoom level."""
        return self.zoom_level

    def set_zoom_level(self, zoom_level: float):
        """Set zoom level programmatically."""
        if not self.displayed_image:
            return

        # Clamp zoom level
        zoom_level = max(0.1, min(2.0, zoom_level))

        # Get canvas center for zoom point
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Convert to canvas coordinates
        mouse_x = self.canvas.canvasx(center_x)
        mouse_y = self.canvas.canvasy(center_y)

        old_zoom = self.zoom_level
        self.zoom_level = zoom_level
        self._apply_zoom_at_point(old_zoom, mouse_x, mouse_y)
        self._notify_zoom_changed()

    def _blend_images(self, base_image: np.ndarray, overlay: np.ndarray, alpha: float) -> np.ndarray:
        """
        Blend base image with overlay.

        Args:
            base_image: Base image array
            overlay: Overlay image array
            alpha: Blending factor (0-1)

        Returns:
            Blended image array
        """
        # Ensure images are same size
        if overlay.shape[:2] != base_image.shape[:2]:
            from PIL import Image
            overlay_pil = Image.fromarray(overlay)
            overlay_pil = overlay_pil.resize((base_image.shape[1], base_image.shape[0]))
            overlay = np.array(overlay_pil)

        # Ensure both images are RGB
        if len(base_image.shape) == 2:
            base_image = np.stack([base_image] * 3, axis=-1)
        if len(overlay.shape) == 2:
            overlay = np.stack([overlay] * 3, axis=-1)

        # Blend images
        blended = (1 - alpha) * base_image.astype(float) + alpha * overlay.astype(float)
        return np.clip(blended, 0, 255).astype(np.uint8)

    def show_original(self):
        """Show original image without any processing."""
        logger.debug("show_original() called")
        if self.original_image is not None:
            logger.debug("Displaying original image")
            self.display_image(self.original_image, preserve_view=True, is_original=False)
            self.showing_quality_map = False
            logger.debug("Set showing_quality_map to False")
        else:
            logger.debug("No original image to show")

    def show_edges(self):
        """Show edge detection visualization."""
        if self.original_image is None:
            return

        try:
            import cv2

            # Convert to grayscale
            if len(self.original_image.shape) == 3:
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)
            else:
                gray = self.original_image.copy()

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Create colored edge visualization
            edge_visualization = np.zeros_like(self.original_image)
            if len(edge_visualization.shape) == 3:
                edge_visualization[..., 2] = edges  # Blue edges
            else:
                edge_visualization = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

            self.display_image(edge_visualization, preserve_view=True)
            self.showing_quality_map = False

        except Exception as e:
            print(f"Error showing edges: {e}")

    def show_gradient(self):
        """Show gradient magnitude visualization."""
        if self.original_image is None:
            return

        try:
            import cv2

            # Convert to grayscale
            if len(self.original_image.shape) == 3:
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)
            else:
                gray = self.original_image.copy()

            # Calculate gradients
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = cv2.magnitude(grad_x, grad_y)

            # Normalize and apply colormap
            cv2.normalize(magnitude, magnitude, 0, 255, cv2.NORM_MINMAX)
            gradient_vis = magnitude.astype(np.uint8)
            gradient_colored = cv2.applyColorMap(gradient_vis, cv2.COLORMAP_JET)
            gradient_colored_rgb = cv2.cvtColor(gradient_colored, cv2.COLOR_BGR2RGB)

            self.display_image(gradient_colored_rgb, preserve_view=True)
            self.showing_quality_map = False

        except Exception as e:
            print(f"Error showing gradient: {e}")

    def clear(self):
        """Clear the canvas."""
        logger.debug("Canvas clear() method called")
        import traceback
        logger.debug(f"Clear called from: {traceback.format_stack()[-2].strip()}")
        
        self.canvas.delete('all')
        self.displayed_image = None
        self.original_image = None
        self.current_image = None
        self.quality_map_data = None
        self.quality_visualization = None
        self.showing_quality_map = False
        self.zoom_level = 1.0
        self.display_scale = 1.0
        self.photo = None
        self.image_item = None
        logger.debug("Canvas cleared")

    def is_showing_quality_map(self) -> bool:
        """Check if quality map is currently being shown."""
        logger.debug(f"is_showing_quality_map() returning: {self.showing_quality_map}")
        return self.showing_quality_map

    def reset_view(self):
        """Reset view to default zoom and position."""
        logger.debug(f"reset_view() called, showing_quality_map={self.showing_quality_map}")
        if self.displayed_image:
            # Reset zoom level
            self.zoom_level = 1.0

            # Always show original image and reset quality map state
            logger.debug("reset_view() calling show_original()")
            self.show_original()

    def hide_quality_map(self):
        """Hide the quality map and show original image."""
        logger.debug(f"hide_quality_map() called, showing_quality_map={self.showing_quality_map}")
        if self.original_image is not None and self.showing_quality_map:
            logger.debug("Calling show_original() to hide quality map")
            self.show_original()
            # showing_quality_map is already set to False in show_original()
        else:
            logger.debug(f"Not hiding quality map - original_image={self.original_image is not None}, showing_quality_map={self.showing_quality_map}")

    def get_image_coordinates(self, canvas_x: int, canvas_y: int) -> Tuple[int, int]:
        """
        Convert canvas coordinates to original image coordinates.

        Args:
            canvas_x: Canvas X coordinate
            canvas_y: Canvas Y coordinate

        Returns:
            Tuple of (image_x, image_y) coordinates in original image space
        """
        # Convert canvas coordinates to scrollable canvas coordinates
        canvas_x = self.canvas.canvasx(canvas_x)
        canvas_y = self.canvas.canvasy(canvas_y)

        # Account for image offset (when image is centered on canvas)
        offset_x = getattr(self, 'image_offset_x', 0)
        offset_y = getattr(self, 'image_offset_y', 0)

        canvas_x -= offset_x
        canvas_y -= offset_y

        # Convert directly to original image coordinates
        # The canvas shows the image scaled by (display_scale * zoom_level)
        # So to get original coordinates, we divide by the total scaling
        total_scale = self.display_scale * self.zoom_level

        # Ensure we don't divide by zero
        if total_scale <= 0:
            total_scale = 1.0

        original_image_x = canvas_x / total_scale
        original_image_y = canvas_y / total_scale

        return int(round(original_image_x)), int(round(original_image_y))