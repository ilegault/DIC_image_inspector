import tkinter as tk
from tkinter import Canvas
import numpy as np
from PIL import Image, ImageTk, ImageDraw
import logging

# Set up logging to console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImageCanvas:
    def __init__(self, parent):
        self.parent = parent
        self.canvas = Canvas(parent, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Image data
        self.original_image = None
        self.displayed_image = None
        self.photo_image = None

        # Image cache for performance
        self.image_cache = {}
        self.max_cache_size = 10

        # View state
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        # Pan state
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0

        # Image position
        self.image_id = None

        # Zoom debouncing
        self.pending_zoom = None
        self.zoom_timer = None

        # Bind events
        self._bind_events()

        # Status label for debugging
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(parent, textvariable=self.status_var, bg='white')
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status("Ready")

    def update_status(self, msg):
        """Update status bar for debugging."""
        self.status_var.set(f"Zoom: {self.zoom_level:.2f}x | {msg}")
        logger.info(msg)

    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Zoom events
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down

        # Pan events - only right click for panning
        self.canvas.bind("<Button-3>", self._start_pan)  # Right click
        self.canvas.bind("<B3-Motion>", self._pan_image)  # Right click motion
        self.canvas.bind("<ButtonRelease-3>", self._end_pan)  # Right click release

        # Control+Left click for future selection/move tool
        self.canvas.bind("<Control-Button-1>", self._start_selection)
        self.canvas.bind("<Control-B1-Motion>", self._move_selection)
        self.canvas.bind("<Control-ButtonRelease-1>", self._end_selection)

        # Double click to reset
        self.canvas.bind("<Double-Button-1>", self._reset_view)

        # Focus for keyboard events
        self.canvas.focus_set()

    def create_speckle_pattern(self, width=800, height=600):
        """Create a test image with large visible speckle pattern."""
        # Create image with gradient background
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        # Add gradient background
        for y in range(height):
            gray = int(255 * (1 - y / height * 0.3))
            draw.line([(0, y), (width, y)], fill=(gray, gray, gray))

        # Add large speckles
        np.random.seed(42)  # For consistent pattern
        num_speckles = 100

        for i in range(num_speckles):
            x = np.random.randint(20, width - 20)
            y = np.random.randint(20, height - 20)
            size = np.random.randint(10, 40)

            # Random color
            color = (
                np.random.randint(50, 200),
                np.random.randint(50, 200),
                np.random.randint(50, 200)
            )

            # Draw speckle
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

        # Add grid lines for reference
        for x in range(0, width, 100):
            draw.line([(x, 0), (x, height)], fill='red', width=2)
        for y in range(0, height, 100):
            draw.line([(0, y), (width, y)], fill='red', width=2)

        # Add text markers
        for x in range(100, width, 100):
            for y in range(100, height, 100):
                draw.text((x - 20, y - 10), f"{x},{y}", fill='blue')

        return np.array(img)

    def display_image(self, image_data: np.ndarray):
        """Display an image on the canvas."""
        # Convert numpy array to PIL Image
        if image_data.dtype != np.uint8:
            image_data = (image_data * 255).astype(np.uint8)

        if len(image_data.shape) == 2:
            self.original_image = Image.fromarray(image_data, mode='L')
        else:
            self.original_image = Image.fromarray(image_data, mode='RGB')

        # Clear cache when new image loaded
        self.image_cache.clear()

        # Reset zoom
        self.zoom_level = 1.0

        # Update display
        self._update_display()
        self.update_status("Image loaded")

    def _update_display(self):
        """Update the displayed image based on current zoom level."""
        if self.original_image is None:
            return

        # Calculate new size
        orig_width, orig_height = self.original_image.size
        new_width = int(orig_width * self.zoom_level)
        new_height = int(orig_height * self.zoom_level)

        # Create cache key
        cache_key = (new_width, new_height)

        # Check cache first
        if cache_key in self.image_cache:
            self.photo_image = self.image_cache[cache_key]
        else:
            # Resize image - use NEAREST for speed during interactive zoom
            if abs(self.zoom_level - 1.0) < 0.001:
                resized = self.original_image
            else:
                # Use NEAREST for speed, or BILINEAR for better quality but slower
                resample = Image.Resampling.BILINEAR if self.zoom_level < 1.0 else Image.Resampling.NEAREST
                resized = self.original_image.resize((new_width, new_height), resample)

            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(resized)

            # Add to cache
            self.image_cache[cache_key] = self.photo_image

            # Limit cache size
            if len(self.image_cache) > self.max_cache_size:
                # Remove oldest entries
                oldest_keys = list(self.image_cache.keys())[:-self.max_cache_size]
                for key in oldest_keys:
                    del self.image_cache[key]

        # Update canvas
        if self.image_id is None:
            self.image_id = self.canvas.create_image(0, 0, image=self.photo_image, anchor='nw')
        else:
            self.canvas.itemconfig(self.image_id, image=self.photo_image)

        # Update scroll region
        self.canvas.config(scrollregion=self.canvas.bbox('all'))

        self.update_status(f"Display updated - Size: {new_width}x{new_height}")

    def _on_mousewheel(self, event):
        """Handle mouse wheel zoom."""
        if self.original_image is None:
            return

        # Store old zoom
        old_zoom = self.zoom_level

        # Calculate new zoom with multiplicative increments
        if event.delta < 0:  # Zoom out
            self.zoom_level = max(self.min_zoom, self.zoom_level * 0.9)
            direction = "out"
        else:  # Zoom in
            self.zoom_level = min(self.max_zoom, self.zoom_level * 1.1)
            direction = "in"

        if abs(self.zoom_level - old_zoom) < 0.001:
            return

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
        mouse_frac_x = mouse_x / canvas_width
        mouse_frac_y = mouse_y / canvas_height

        # Convert to fraction of total image
        image_frac_x = scroll_left + mouse_frac_x * view_width
        image_frac_y = scroll_top + mouse_frac_y * view_height

        # Update display with new zoom
        self._update_display()

        # After zoom, calculate where to scroll to keep the same image point under mouse
        new_image_width = self.original_image.width * self.zoom_level
        new_image_height = self.original_image.height * self.zoom_level

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

        self.update_status(f"Zoomed {direction} at ({mouse_x}, {mouse_y})")

    def _start_pan(self, event):
        """Start panning operation."""
        self.canvas.config(cursor="fleur")
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.panning = True
        self.update_status(f"Pan started at ({event.x}, {event.y})")

    def _pan_image(self, event):
        """Pan the image during mouse motion."""
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
        self.update_status("Pan ended")

    def _start_selection(self, event):
        """Start selection/move operation with Ctrl+Left click."""
        self.canvas.config(cursor="crosshair")
        self.update_status(f"Selection mode at ({event.x}, {event.y})")

    def _move_selection(self, event):
        """Handle selection/move motion."""
        pass

    def _end_selection(self, event):
        """End selection/move operation."""
        self.canvas.config(cursor="")
        self.update_status("Selection ended")

    def _reset_view(self, event):
        """Reset zoom and center the image."""
        self.zoom_level = 1.0
        self._update_display()

        # Center the image
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        self.update_status("View reset")


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Image Canvas Test - Right Click to Pan, Scroll to Zoom")
    root.geometry("1000x700")

    # Create canvas
    canvas = ImageCanvas(root)

    # Create and display test speckle pattern
    test_image = canvas.create_speckle_pattern(1200, 800)
    canvas.display_image(test_image)

    # Instructions
    instructions = tk.Label(root,
                            text="Right-click & drag to pan | Scroll to zoom | Ctrl+Left for selection mode | Double-click to reset",
                            bg='yellow', font=('Arial', 12, 'bold'))
    instructions.pack(side=tk.TOP, fill=tk.X)

    root.mainloop()