# ui/components/image_canvas.py - Clean Image Display Component

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from typing import Optional, Tuple
from utils.constants import APP_CONFIG, get_theme_colors
from utils.modern_styling import ModernStyleManager


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
        self.original_image = None
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
            text="📸 Image Preview",
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

    def display_image(self, image_data: np.ndarray, preserve_view: bool = False):
        """
        Display an image on the canvas.

        Args:
            image_data: Image data as numpy array
            preserve_view: Whether to preserve current zoom and scroll position
        """
        try:
            # Store current view state if preserving
            if preserve_view and self.displayed_image:
                current_zoom = self.zoom_level
                visible_x = self.canvas.xview()
                visible_y = self.canvas.yview()
            else:
                current_zoom = 1.0
                visible_x = None
                visible_y = None

            # Convert numpy array to PIL Image
            if len(image_data.shape) == 3:
                pil_image = Image.fromarray(image_data.astype(np.uint8))
            else:
                pil_image = Image.fromarray(image_data.astype(np.uint8), mode='L')
                pil_image = pil_image.convert('RGB')

            # Calculate display scale
            max_size = APP_CONFIG['display']['max_image_size']
            if max(pil_image.size) > max_size:
                ratio = max_size / max(pil_image.size)
                new_size = (int(pil_image.size[0] * ratio), int(pil_image.size[1] * ratio))
                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
                self.display_scale = ratio
            else:
                self.display_scale = 1.0

            # Store original and current images
            self.original_image = image_data
            self.displayed_image = pil_image

            # Apply zoom if not preserving view
            if not preserve_view:
                self.zoom_level = 1.0

            # Apply current zoom level
            if self.zoom_level != 1.0:
                zoomed_size = (
                    int(pil_image.width * self.zoom_level),
                    int(pil_image.height * self.zoom_level)
                )
                pil_image = pil_image.resize(zoomed_size, Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(pil_image)

            # Clear canvas and display image
            self.canvas.delete('all')
            self._position_and_display_image()

            # Restore view state if preserving
            if preserve_view and visible_x and visible_y:
                self.canvas.xview_moveto(visible_x[0])
                self.canvas.yview_moveto(visible_y[0])

            # Update canvas display scale for other components
            self.canvas.display_scale = self.display_scale * self.zoom_level

        except Exception as e:
            print(f"Error displaying image: {e}")

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
                    print(f"DEBUG: Image centered directly - Canvas: {canvas_width}x{canvas_height}, "
                          f"Display: {img_width}x{img_height}, Position: ({center_x}, {center_y})")
                else:
                    print(f"DEBUG: Image scrollable - Canvas: {canvas_width}x{canvas_height}, "
                          f"Display: {img_width}x{img_height}, Scroll region: {img_width}x{img_height}")

    def _on_mousewheel(self, event):
        """Handle mouse wheel zoom."""
        if not self.displayed_image:
            return "break"

        # Store old zoom level and mouse position
        old_zoom = self.zoom_level
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)

        # Calculate new zoom level
        if event.num == 5 or event.delta < 0:  # Zoom out
            self.zoom_level = max(0.1, self.zoom_level - 0.1)
        elif event.num == 4 or event.delta > 0:  # Zoom in
            self.zoom_level = min(5.0, self.zoom_level + 0.1)
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
        
        # Calculate old and new image dimensions
        old_width = int(self.displayed_image.width * old_zoom)
        old_height = int(self.displayed_image.height * old_zoom)
        
        base_width = self.displayed_image.width
        base_height = self.displayed_image.height
        new_width = int(base_width * self.zoom_level)
        new_height = int(base_height * self.zoom_level)

        # Resize image
        if self.zoom_level == 1.0:
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
            
            # Calculate zoom center adjustment for scrollable images
            if old_width > 0 and old_height > 0:
                # Adjust mouse coordinates if they were relative to a centered small image
                if hasattr(self, 'image_offset_x') and hasattr(self, 'image_offset_y'):
                    adjusted_mouse_x = mouse_x - getattr(self, 'image_offset_x', 0)
                    adjusted_mouse_y = mouse_y - getattr(self, 'image_offset_y', 0)
                else:
                    adjusted_mouse_x = mouse_x
                    adjusted_mouse_y = mouse_y
                
                # Calculate the relative position of the mouse in the old image
                rel_x = adjusted_mouse_x / old_width if old_width > 0 else 0.5
                rel_y = adjusted_mouse_y / old_height if old_height > 0 else 0.5
                
                # Clamp relative positions to valid range
                rel_x = max(0, min(1, rel_x))
                rel_y = max(0, min(1, rel_y))
                
                # Calculate where that same relative position should be in the new image
                new_mouse_x = rel_x * new_width
                new_mouse_y = rel_y * new_height
                
                # Calculate the desired scroll position to keep the zoom point centered
                if new_width > canvas_width:
                    # Image is wider than canvas - calculate scroll position
                    desired_x = (new_mouse_x - canvas_width / 2) / new_width
                    desired_x = max(0, min(1, desired_x))
                else:
                    # Image fits horizontally - center it
                    desired_x = 0.5
                
                if new_height > canvas_height:
                    # Image is taller than canvas - calculate scroll position  
                    desired_y = (new_mouse_y - canvas_height / 2) / new_height
                    desired_y = max(0, min(1, desired_y))
                else:
                    # Image fits vertically - center it
                    desired_y = 0.5
                
                # Apply the new scroll position
                self.canvas.xview_moveto(desired_x)
                self.canvas.yview_moveto(desired_y)
            else:
                # No old dimensions - center the image
                if new_width > canvas_width:
                    self.canvas.xview_moveto(0.5)
                else:
                    self.canvas.xview_moveto(0.0)
                    
                if new_height > canvas_height:
                    self.canvas.yview_moveto(0.5)
                else:
                    self.canvas.yview_moveto(0.0)

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
        self.zoom_level = min(5.0, self.zoom_level + 0.2)
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
        self.zoom_level = max(0.1, self.zoom_level - 0.2)
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
        self.zoom_level = max(0.1, min(5.0, fit_zoom))
        
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
        self.zoom_level = min(5.0, self.zoom_level + 0.2)
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
        self.zoom_level = max(0.1, self.zoom_level - 0.2)
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
        self.zoom_level = max(0.1, min(5.0, fit_zoom))
        
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
        zoom_level = max(0.1, min(5.0, zoom_level))
        
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

            # Blend with original image
            alpha = APP_CONFIG['display']['quality_map_alpha']
            blended = self._blend_images(self.original_image, colored_map, alpha)

            # Display blended image
            self.display_image(blended, preserve_view=True)
            self.showing_quality_map = True

        except Exception as e:
            print(f"Error showing quality map: {e}")

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
        if self.original_image is not None:
            self.display_image(self.original_image, preserve_view=True)
            self.showing_quality_map = False

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
        self.quality_map_data = None
        self.quality_visualization = None
        self.showing_quality_map = False
        self.zoom_level = 1.0
        self.display_scale = 1.0
        self.photo = None
        self.image_item = None

    def is_showing_quality_map(self) -> bool:
        """Check if quality map is currently being shown."""
        return self.showing_quality_map

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