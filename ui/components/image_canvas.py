# ui/components/image_canvas.py - Clean Image Display Component

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from typing import Optional, Tuple
from utils.constants import APP_CONFIG


class ImageCanvas:
    """
    Image canvas component for displaying images and quality maps.

    Handles image display, zooming, panning, and quality map overlays.
    Follows single responsibility principle - only image display concerns.
    """

    def __init__(self, parent: tk.Widget):
        """
        Initialize image canvas.

        Args:
            parent: Parent widget
        """
        self.parent = parent

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
        """Create the main canvas area with scrollbars."""
        # Main image panel
        self.image_panel = tk.Frame(
            self.parent,
            bg=APP_CONFIG['colors']['panel_bg'],
            relief='raised',
            bd=2
        )
        self.image_panel.pack(fill='both', expand=True, padx=5)

        # Title
        img_title = tk.Label(
            self.image_panel,
            text="📸 Image Preview",
            font=('Arial', 16, 'bold'),
            fg=APP_CONFIG['colors']['text_primary'],
            bg=APP_CONFIG['colors']['panel_bg']
        )
        img_title.pack(pady=10)

        # Canvas frame with scrollbars
        canvas_frame = tk.Frame(self.image_panel, bg=APP_CONFIG['colors']['panel_bg'])
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Canvas with scrollbars
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='white',
            width=800,
            height=500,
            highlightthickness=0
        )

        self.v_scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.canvas.xview)

        self.canvas.configure(
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )

        # Grid layout
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

    def _create_processing_controls(self):
        """Create image processing control buttons."""
        process_frame = tk.Frame(self.image_panel, bg=APP_CONFIG['colors']['panel_bg'])
        process_frame.pack(pady=10)

        # Processing buttons
        processing_buttons = [
            ("Original", self.show_original, '#95a5a6')
        ]

        for text, command, color in processing_buttons:
            btn = tk.Button(
                process_frame,
                text=text,
                bg=color,
                fg='white',
                padx=10,
                command=command
            )
            btn.pack(side='left', padx=2)

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

        # Determine positioning strategy
        if img_width <= canvas_width and img_height <= canvas_height:
            # Image fits - center it
            x_pos = (canvas_width - img_width) // 2
            y_pos = (canvas_height - img_height) // 2

            # Set scroll region to canvas size
            self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))

            # Place image at center
            self.image_item = self.canvas.create_image(x_pos, y_pos, anchor='nw', image=self.photo)

            # Store offset for coordinate calculations
            self.image_offset_x = x_pos
            self.image_offset_y = y_pos
            
            # Also store on canvas for ROI selector access
            self.canvas.image_offset_x = x_pos
            self.canvas.image_offset_y = y_pos
            
            # Debug for large original images
            if hasattr(self, 'original_image') and self.original_image is not None:
                orig_h, orig_w = self.original_image.shape[:2]
                if max(orig_w, orig_h) > 1000:
                    print(f"DEBUG: Image centered - Canvas: {canvas_width}x{canvas_height}, "
                          f"Display: {img_width}x{img_height}, Offset: ({x_pos}, {y_pos})")
        else:
            # Image is larger - enable scrolling
            self.canvas.configure(scrollregion=(0, 0, img_width, img_height))

            # Place image at origin
            self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

            # No offset when scrolling
            self.image_offset_x = 0
            self.image_offset_y = 0
            
            # Also store on canvas for ROI selector access
            self.canvas.image_offset_x = 0
            self.canvas.image_offset_y = 0
            
            # Debug for large original images
            if hasattr(self, 'original_image') and self.original_image is not None:
                orig_h, orig_w = self.original_image.shape[:2]
                if max(orig_w, orig_h) > 1000:
                    print(f"DEBUG: Image scrollable - Canvas: {canvas_width}x{canvas_height}, "
                          f"Display: {img_width}x{img_height}, Scroll region: {img_width}x{img_height}")

    def _on_mousewheel(self, event):
        """Handle mouse wheel zoom."""
        if not self.displayed_image:
            return "break"

        # Store old zoom level
        old_zoom = self.zoom_level

        # Calculate new zoom level
        if event.num == 5 or event.delta < 0:  # Zoom out
            self.zoom_level = max(0.1, self.zoom_level - 0.1)
        elif event.num == 4 or event.delta > 0:  # Zoom in
            self.zoom_level = min(5.0, self.zoom_level + 0.1)
        else:
            return "break"

        # Apply zoom
        self._apply_zoom(old_zoom)
        return "break"

    def _apply_zoom(self, old_zoom: float):
        """Apply zoom transformation."""
        if not self.displayed_image:
            return

        # Calculate new image size
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

        # Update canvas
        self.canvas.delete(self.image_item)
        self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

        # Update scroll region
        self.canvas.configure(scrollregion=(0, 0, new_width, new_height))

        # Update display scale
        self.canvas.display_scale = self.display_scale * self.zoom_level

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