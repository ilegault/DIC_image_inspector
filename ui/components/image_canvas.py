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

        # Pan state
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.panning = False

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

        # Pan events
        self.canvas.bind("<Control-Button-1>", self._start_pan)
        self.canvas.bind("<Control-B1-Motion>", self._pan_image)
        self.canvas.bind("<ButtonRelease-1>", self._end_pan)

        # Keyboard zoom shortcuts
        self.canvas.bind("<Control-plus>", self._zoom_in_keyboard)
        self.canvas.bind("<Control-equal>", self._zoom_in_keyboard)  # For keyboards without numpad
        self.canvas.bind("<Control-minus>", self._zoom_out_keyboard)
        self.canvas.bind("<Control-0>", self._zoom_fit)
        self.canvas.bind("<Control-1>", self._zoom_actual)

        # Key events
        self.canvas.bind("<KeyRelease-Control_L>", self._reset_cursor)
        self.canvas.bind("<KeyRelease-Control_R>", self._reset_cursor)
        self.canvas.bind("<Leave>", self._reset_cursor)
        self.canvas.bind("<KeyRelease>", self._check_ctrl_release)

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
            # Clear any existing image items
            self.canvas.delete("all")

            # Handle both numpy array and ImageData object
            if hasattr(image_data, 'array'):
                # It's an ImageData object, extract the array
                image_array = image_data.array
            else:
                # It's already a numpy array
                image_array = image_data

            # Validate image array
            if not isinstance(image_array, np.ndarray):
                raise ValueError("Image must be a numpy array")

            # Convert to uint8 if necessary
            if image_array.dtype != np.uint8:
                image_array = np.clip(image_array, 0, 255).astype(np.uint8)

            # Store current image
            self.current_image = image_array.copy()

            # Store as original image only if this is truly the original
            if is_original:
                self.original_image = image_array.copy()

            # Convert grayscale to RGB if needed
            if len(image_array.shape) == 2:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
            elif len(image_array.shape) == 3 and image_array.shape[2] == 4:
                # Convert RGBA to RGB
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)

            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(image_array)

            # Store as displayed image
            self.displayed_image = pil_image

            # Calculate initial display scale if not preserving view
            if not preserve_view:
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                # Use default size if canvas not yet rendered
                if canvas_width <= 1:
                    canvas_width = 800
                if canvas_height <= 1:
                    canvas_height = 500

                img_width, img_height = pil_image.size

                # Calculate scale to fit image in canvas
                scale_x = canvas_width / img_width
                scale_y = canvas_height / img_height
                self.display_scale = min(scale_x, scale_y) * 0.9  # 90% to leave margin

                # Reset zoom level
                self.zoom_level = 1.0

            # Create the photo image
            display_width = int(pil_image.width * self.display_scale * self.zoom_level)
            display_height = int(pil_image.height * self.display_scale * self.zoom_level)

            if display_width != pil_image.width or display_height != pil_image.height:
                resized_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            else:
                resized_image = pil_image

            self.photo = ImageTk.PhotoImage(resized_image)

            # Update canvas size and display image
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if display_width <= canvas_width and display_height <= canvas_height:
                # Center the image
                x = (canvas_width - display_width) // 2
                y = (canvas_height - display_height) // 2
                self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
                self.image_item = self.canvas.create_image(x, y, anchor='nw', image=self.photo)

                # Store offsets for coordinate conversion
                self.image_offset_x = x
                self.image_offset_y = y
                self.canvas.image_offset_x = x
                self.canvas.image_offset_y = y
            else:
                # Image larger than canvas - use scrolling
                self.canvas.configure(scrollregion=(0, 0, display_width, display_height))
                self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

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

        except Exception as e:
            print(f"Error displaying image: {e}")
            import traceback
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
        if not self.displayed_image:
            return "break"

        # Store old zoom level and mouse position
        old_zoom = self.zoom_level
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)

        # Calculate new zoom level with smaller, more precise increments
        if event.num == 5 or event.delta < 0:  # Zoom out
            self.zoom_level = max(0.1, self.zoom_level - 0.05)
        elif event.num == 4 or event.delta > 0:  # Zoom in
            self.zoom_level = min(2.0, self.zoom_level + 0.05)
        else:
            return "break"

        # Apply zoom centered on mouse position
        self._apply_zoom_at_point(old_zoom, mouse_x, mouse_y)

        # Notify zoom change
        self._notify_zoom_changed()
        return "break"

    def _apply_zoom_at_point(self, old_zoom: float, mouse_x: float, mouse_y: float):
        """Apply zoom transformation centered at a specific point."""
        if not self.displayed_image:
            return

        # Get current scroll position and canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Use reasonable defaults if canvas not rendered yet
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 500

        # Calculate old and new image dimensions using both display_scale and zoom_level
        old_width = int(self.displayed_image.width * self.display_scale * old_zoom)
        old_height = int(self.displayed_image.height * self.display_scale * old_zoom)

        base_width = self.displayed_image.width
        base_height = self.displayed_image.height
        new_width = max(1, int(base_width * self.display_scale * self.zoom_level))
        new_height = max(1, int(base_height * self.display_scale * self.zoom_level))

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
            self.canvas.configure(scrollregion=(0, 0, new_width, new_height))
            self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

            # No offset when using scroll regions
            self.image_offset_x = 0
            self.image_offset_y = 0
            self.canvas.image_offset_x = 0
            self.canvas.image_offset_y = 0

            # For large images, try to maintain the zoom center
            # Use a simpler approach to avoid coordinate system confusion
            try:
                if old_width > 0 and old_height > 0:
                    # Calculate the center point of the current view
                    if old_width <= canvas_width and old_height <= canvas_height:
                        # Old image was centered - use canvas center as zoom point
                        center_x_ratio = 0.5
                        center_y_ratio = 0.5
                    else:
                        # Old image was scrollable - get current view center
                        current_scroll_x = self.canvas.xview()[0]
                        current_scroll_y = self.canvas.yview()[0]
                        view_width = self.canvas.xview()[1] - self.canvas.xview()[0]
                        view_height = self.canvas.yview()[1] - self.canvas.yview()[0]
                        center_x_ratio = current_scroll_x + view_width / 2
                        center_y_ratio = current_scroll_y + view_height / 2

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

                    self.canvas.xview_moveto(new_scroll_x)
                    self.canvas.yview_moveto(new_scroll_y)
                else:
                    # No old dimensions - center the image
                    self.canvas.xview_moveto(0.5)
                    self.canvas.yview_moveto(0.5)
            except Exception as e:
                # Fallback to centering if anything goes wrong
                print(f"Zoom positioning error: {e}")
                self.canvas.xview_moveto(0.5)
                self.canvas.yview_moveto(0.5)

        # Update display scale
        self.canvas.display_scale = self.display_scale * self.zoom_level

    def _notify_zoom_changed(self):
        """Notify that zoom level has changed."""
        if 'zoom_changed' in self.callbacks:
            self.callbacks['zoom_changed'](self.zoom_level)

    def _start_pan(self, event):
        """Start panning operation."""
        self.canvas.config(cursor="fleur")
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.panning = True

    def _pan_image(self, event):
        """Pan the image."""
        if not self.panning:
            return

        # Calculate movement
        dx = (event.x - self.pan_start_x) / self.canvas.winfo_width()
        dy = (event.y - self.pan_start_y) / self.canvas.winfo_height()

        # Get current view position
        current_x = self.canvas.xview()[0]
        current_y = self.canvas.yview()[0]

        # Calculate new position
        new_x = max(0, min(1, current_x - dx))
        new_y = max(0, min(1, current_y - dy))

        # Apply movement
        self.canvas.xview_moveto(new_x)
        self.canvas.yview_moveto(new_y)

        # Update start position
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def _end_pan(self, event):
        """End panning operation."""
        self.panning = False
        self.canvas.config(cursor="")

    def _reset_cursor(self, event):
        """Reset cursor when Ctrl is released."""
        if not self.panning:
            self.canvas.config(cursor="")

    def _check_ctrl_release(self, event):
        """Check if Ctrl key is released and reset cursor."""
        if not (event.state & 0x0004):  # Ctrl not pressed
            self.panning = False
            self.canvas.config(cursor="")

    def _zoom_in_keyboard(self, event):
        """Zoom in using keyboard shortcut."""
        if not self.displayed_image:
            return "break"

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
        return "break"

    def _zoom_out_keyboard(self, event):
        """Zoom out using keyboard shortcut."""
        if not self.displayed_image:
            return "break"

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
        return "break"

    def _zoom_fit(self, event):
        """Fit image to canvas."""
        if not self.displayed_image:
            return "break"

        # Calculate fit zoom level
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return "break"

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
        return "break"

    def _zoom_actual(self, event):
        """Zoom to actual size (100%)."""
        if not self.displayed_image:
            return "break"

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
        return "break"

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