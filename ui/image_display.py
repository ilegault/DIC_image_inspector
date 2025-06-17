# ui.image_display.py

import cv2
import numpy as np
from PIL import Image, ImageTk
from tkinter import messagebox
from analysis.metrics import get_analysis_region

class ImageDisplay:
    def __init__(self, canvas, main_window=None):
        self.canvas = canvas
        self.main_window = main_window
        self.displayed_image = None
        self.photo = None
        self.display_scale = 1.0
        self.zoom_level = 1.0
        self.image_item = None
        self.zoom_overlay_item = None  # Overlay for zoomed view

        # Setup mouse bindings for panning and zooming
        self.canvas.bind("<MouseWheel>", self.zoom)  # Windows mousewheel
        self.canvas.bind("<Button-4>", self.zoom)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom)  # Linux scroll down
        self.canvas.bind("<Control-Button-1>", self.start_pan)
        self.canvas.bind("<Control-B1-Motion>", self.pan)
        self.canvas.bind("<ButtonRelease-1>", self.end_pan)  # Add this line
        self.canvas.bind("<KeyRelease-Control_L>", self.reset_cursor)
        self.canvas.bind("<KeyRelease-Control_R>", self.reset_cursor)

        # Add these new bindings
        self.canvas.bind("<Leave>", self.reset_cursor)  # Reset when mouse leaves canvas
        self.canvas.bind("<KeyRelease>", self.check_ctrl_release)  # Check any key release

        # For panning
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.panning = False  # Add this flag to track panning state

    def display_image(self, pil_image, preserve_view=False):
        """Display image with option to preserve current view

        Args:
            pil_image: PIL Image to display
            preserve_view: If True, maintain current zoom level and scroll position
        """
        # Store current view state if needed
        if preserve_view and self.displayed_image:
            current_zoom = self.zoom_level
            visible_x = self.canvas.xview()
            visible_y = self.canvas.yview()
        else:
            # Default to reset view
            current_zoom = 1.0
            visible_x = (0, 1)
            visible_y = (0, 1)

        # Calculate scale
        display_image = pil_image.copy()
        max_size = 800

        if max(display_image.size) > max_size:
            ratio = max_size / max(display_image.size)
            new_size = (int(display_image.size[0] * ratio), int(display_image.size[1] * ratio))
            display_image = display_image.resize(new_size, Image.Resampling.LANCZOS)
            self.display_scale = ratio
        else:
            self.display_scale = 1.0

        # Set zoom level (either preserve or reset)
        if not preserve_view:
            self.zoom_level = 1.0

        # Process image with current zoom
        if self.zoom_level != 1.0:
            new_width = int(display_image.width * self.zoom_level)
            new_height = int(display_image.height * self.zoom_level)
            display_image = display_image.resize((new_width, new_height), resample = Image.Resampling.NEAREST)

        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(display_image)

        # Clear canvas and display image
        self.canvas.delete('all')
        self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

        # Update scroll region to match the image dimensions
        self.canvas.configure(scrollregion=(0, 0, self.photo.width(), self.photo.height()))

        # Update canvas.display_scale for ROI handler
        self.canvas.display_scale = self.display_scale * self.zoom_level

        # Store the displayed image
        self.displayed_image = display_image

        # Force canvas to update
        self.canvas.update_idletasks()

        # Restore previous view position if preserving view
        if preserve_view:
            self.canvas.xview_moveto(visible_x[0])
            self.canvas.yview_moveto(visible_y[0])

        # Redraw ROI with updated scale and view
        if hasattr(self.main_window, 'roi_handler') and self.main_window.roi_handler.roi_coords:
            self.main_window.roi_handler.redraw_roi()

    def zoom(self, event):
        """Handle zoom with mouse wheel"""
        if not self.displayed_image:
            return

        # Store original zoom level
        old_zoom = self.zoom_level

        # Determine zoom direction and new zoom level
        if event.num == 5 or event.delta < 0:  # Zoom out
            self.zoom_level = max(0.1, self.zoom_level - 0.1)
        elif event.num == 4 or event.delta > 0:  # Zoom in
            self.zoom_level = min(5.0, self.zoom_level + 0.1)
        else:
            return "break"

        # Get mouse position in both window and canvas coordinates
        window_x, window_y = event.x, event.y
        canvas_x = self.canvas.canvasx(window_x)
        canvas_y = self.canvas.canvasy(window_y)

        # Get current view bounds before zoom
        old_scroll_region = self.canvas.cget("scrollregion").split()
        old_width = int(old_scroll_region[2])
        old_height = int(old_scroll_region[3])

        # Calculate new size
        new_width = int(self.displayed_image.width * self.zoom_level)
        new_height = int(self.displayed_image.height * self.zoom_level)

        # Calculate zoom ratio
        zoom_ratio = self.zoom_level / old_zoom

        # Resize image
        if self.zoom_level == 1.0:
            resized_image = self.displayed_image
        else:
            resized_image = self.displayed_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Update photo image
        self.photo = ImageTk.PhotoImage(resized_image)

        # Update canvas
        self.canvas.delete(self.image_item)
        self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

        # Update scroll region
        self.canvas.configure(scrollregion=(0, 0, new_width, new_height))

        # Update the display_scale for ROI handler to use
        self.canvas.display_scale = self.display_scale * self.zoom_level

        # Redraw ROI if it exists
        if hasattr(self.main_window, 'roi_handler') and self.main_window.roi_handler.roi_coords:
            self.main_window.roi_handler.redraw_roi()

        # Calculate new view center to maintain zoom point
        # Mouse position relative to visible canvas area
        visible_width = self.canvas.winfo_width()
        visible_height = self.canvas.winfo_height()

        # Current scroll position in fractions
        old_x_view = self.canvas.xview()
        old_y_view = self.canvas.yview()

        # Calculate scroll offset to keep mouse point fixed
        x_offset = canvas_x / old_width
        y_offset = canvas_y / old_height

        # Adjust for visible area
        new_x = x_offset - (window_x / visible_width) * (visible_width / new_width)
        new_y = y_offset - (window_y / visible_height) * (visible_height / new_height)

        # Clamp values to valid range
        new_x = max(0, min(1.0 - visible_width / new_width, new_x))
        new_y = max(0, min(1.0 - visible_height / new_height, new_y))

        # Apply new view position
        self.canvas.xview_moveto(new_x)
        self.canvas.yview_moveto(new_y)

        return "break"  # Prevent default behavior

    def apply_zoom(self, rel_x=0.5, rel_y=0.5, old_zoom=None):
        """Apply zoom at specified relative position without resetting view"""
        if not self.displayed_image:
            return
        
        #fix this please

        # Calculate new size
        new_width = int(self.displayed_image.width * self.zoom_level)
        new_height = int(self.displayed_image.height * self.zoom_level)

        # Resize image
        if self.zoom_level == 1.0:
            resized_image = self.displayed_image
        else:
            resized_image = self.displayed_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Update photo image
        self.photo = ImageTk.PhotoImage(resized_image)

        # Store current view fractions before updating canvas
        old_x_view = self.canvas.xview()
        old_y_view = self.canvas.yview()

        # Update canvas
        self.canvas.delete(self.image_item)
        self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

        # Update scroll region
        self.canvas.configure(scrollregion=(0, 0, new_width, new_height))

        # Update the canvas.display_scale for ROI handler to use
        self.canvas.display_scale = self.display_scale * self.zoom_level

        # Make sure to redraw ROI with updated position
        if hasattr(self.main_window, 'roi_handler') and self.main_window.roi_handler.roi_coords:
            self.main_window.roi_handler.redraw_roi()

        # If coming from direct zoom level adjustment (not mouse wheel),
        # maintain the view position proportionally
        if old_zoom is not None:
            zoom_ratio = self.zoom_level / old_zoom
            center_x = old_x_view[0] + (old_x_view[1] - old_x_view[0]) * rel_x
            center_y = old_y_view[0] + (old_y_view[1] - old_y_view[0]) * rel_y

            # Calculate new view center accounting for zoom
            new_x = center_x - (rel_x * (self.canvas.winfo_width() / new_width))
            new_y = center_y - (rel_y * (self.canvas.winfo_height() / new_height))

            # Ensure we don't go out of bounds
            new_x = max(0, min(1.0 - self.canvas.winfo_width() / new_width, new_x))
            new_y = max(0, min(1.0 - self.canvas.winfo_height() / new_height, new_y))

            # Apply new view
            self.canvas.xview_moveto(new_x)
            self.canvas.yview_moveto(new_y)

    def reset_cursor(self, event):
        """Reset cursor when Ctrl key is released."""
        if self.canvas:
            self.panning = False
            self.canvas.config(cursor="")

    def check_ctrl_release(self, event):
        """Check if Ctrl key is released and reset cursor if needed"""
        # Check if Ctrl key is no longer pressed (state doesn't have Ctrl flag)
        if not (event.state & 0x0004):
            self.panning = False
            self.canvas.config(cursor="")

    def start_pan(self, event):
        """Start panning with Ctrl+click"""
        self.canvas.config(cursor="fleur")
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def end_pan(self, event):
        """End panning"""
        self.canvas.config(cursor="")

    def pan(self, event):
        """Pan the image with Ctrl+drag."""
        if self.main_window is None or not hasattr(self.main_window, 'original_image'):
            return

        # Get current canvas scroll positions (between 0 and 1)
        current_x = self.canvas.xview()[0]
        current_y = self.canvas.yview()[0]

        # Calculate the delta movement as a fraction of the canvas size
        # This matches how scrollbars work - moving by fractions of the total area
        dx = (event.x - self.pan_start_x) / self.canvas.winfo_width()
        dy = (event.y - self.pan_start_y) / self.canvas.winfo_height()

        # Move the view (negative because dragging right should move view left)
        new_x = max(0, min(1, current_x - dx))
        new_y = max(0, min(1, current_y - dy))

        # Apply the movement using moveto instead of scroll
        self.canvas.xview_moveto(new_x)
        self.canvas.yview_moveto(new_y)

        # Update start position for next movement
        self.pan_start_x = event.x
        self.pan_start_y = event.y

        # Redraw ROI to maintain its position relative to the image
        if hasattr(self.main_window, 'roi_handler') and self.main_window.roi_handler.roi_coords:
            self.main_window.roi_handler.redraw_roi()

    def show_original(self):
        """Show the original image."""
        if self.main_window and self.main_window.original_image is not None:
            self.main_window.current_image = self.main_window.original_image.copy()
            pil_image = Image.fromarray(self.main_window.current_image)
            self.display_image(pil_image)

    def show_edges(self):
        """Show edge-enhanced image."""
        if self.main_window and self.main_window.original_image is not None:
            # Get analysis region
            analysis_region = get_analysis_region(
                self.main_window.original_image, self.main_window.roi_coords)

            # Convert to grayscale
            if len(analysis_region.shape) == 3:
                gray = cv2.cvtColor(analysis_region, cv2.COLOR_RGB2GRAY)
            else:
                gray = analysis_region

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Convert back to RGB for display
            edge_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

            # If ROI is selected, create a composite image
            if self.main_window.roi_coords:
                composite = self.main_window.original_image.copy()
                x1, y1, x2, y2 = self.main_window.roi_coords
                composite[y1:y2, x1:x2] = edge_rgb
                self.main_window.current_image = composite
            else:
                self.main_window.current_image = edge_rgb

            # Display the processed image
            pil_image = Image.fromarray(self.main_window.current_image)
            self.display_image(pil_image)

    def show_gradient(self):
        """Show gradient magnitude image."""
        if self.main_window and self.main_window.original_image is not None:
            # Get analysis region
            analysis_region = get_analysis_region(
                self.main_window.original_image, self.main_window.roi_coords)

            # Convert to grayscale
            if len(analysis_region.shape) == 3:
                gray = cv2.cvtColor(analysis_region, cv2.COLOR_RGB2GRAY)
            else:
                gray = analysis_region

            # Calculate gradient
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

            # Normalize to 0-255
            gradient_normalized = cv2.normalize(gradient_magnitude, None, 0, 255, cv2.NORM_MINMAX)
            gradient_normalized = gradient_normalized.astype(np.uint8)

            # Convert to RGB
            gradient_rgb = cv2.cvtColor(gradient_normalized, cv2.COLOR_GRAY2RGB)

            # If we have ROI, create a composite image
            if self.main_window.roi_coords:
                composite = self.main_window.original_image.copy()
                x1, y1, x2, y2 = self.main_window.roi_coords
                composite[y1:y2, x1:x2] = gradient_rgb
                self.main_window.current_image = composite
            else:
                self.main_window.current_image = gradient_rgb

            pil_image = Image.fromarray(self.main_window.current_image)
            self.display_image(pil_image)

    def show_quality_map(self, preserve_view=True):
        """Toggle the visibility of the quality map overlay in the ROI

        If the quality map hasn't been generated yet, it will be created.
        Otherwise, it toggles between showing the original image and the map.

        Args:
            preserve_view: If True, maintain current zoom level and scroll position
        """
        if not self.main_window or self.main_window.original_image is None:
            return

        # Check if ROI exists
        if not hasattr(self.main_window, 'roi_handler') or not self.main_window.roi_handler.roi_coords:
            messagebox.showinfo("Information", "Please select a ROI first to generate a quality map")
            return

        # Get the ROI from the handler
        x1, y1, x2, y2 = self.main_window.roi_handler.roi_coords

        # Validate ROI dimensions
        if x2 <= x1 or y2 <= y1 or x1 < 0 or y1 < 0:
            messagebox.showinfo("Information", "Invalid ROI - please select a valid region")
            return

        # Get the current image ID - create if not present
        current_image_id = getattr(self.main_window, 'current_image_id', None)

        # If no quality map exists, or if we have a new image/ROI, regenerate the map
        regenerate_map = (
                not hasattr(self.main_window, 'quality_map') or
                self.main_window.quality_map is None or
                not hasattr(self.main_window, 'quality_map_image_id') or
                self.main_window.quality_map_image_id != current_image_id or
                getattr(self.main_window, 'quality_map_roi', None) != (x1, y1, x2, y2)
        )

        if regenerate_map:
            # Extract the ROI from the original image
            roi = self.main_window.original_image[y1:y2, x1:x2].copy()

            # Create quality map
            quality_map = self._generate_quality_map(roi)

            # Apply colormap to the quality map (jet colormap)
            colored_map = cv2.applyColorMap((quality_map * 255).astype(np.uint8), cv2.COLORMAP_JET)

            # Store the map and roi for later toggling
            self.main_window.quality_map = colored_map
            self.main_window.quality_map_roi = (x1, y1, x2, y2)
            self.main_window.quality_map_visible = True

            # Store the image ID this quality map was generated for
            self.main_window.quality_map_image_id = current_image_id

            status_msg = "Quality map generated - Red areas indicate poor quality, blue/green areas are better"
        else:
            # Toggle visibility
            self.main_window.quality_map_visible = not getattr(self.main_window, 'quality_map_visible', False)
            status_msg = "Quality map " + ("shown" if self.main_window.quality_map_visible else "hidden")

        # Display appropriate image based on toggle state
        if getattr(self.main_window, 'quality_map_visible', False) and hasattr(self.main_window, 'quality_map'):
            try:
                # Create a composite image with the quality map
                x1, y1, x2, y2 = self.main_window.quality_map_roi
                roi = self.main_window.original_image[y1:y2, x1:x2].copy()
                colored_map = self.main_window.quality_map

                # Check if shapes match before using addWeighted
                if roi.shape[:2] == colored_map.shape[:2]:
                    composite = self.main_window.original_image.copy()
                    composite[y1:y2, x1:x2] = cv2.addWeighted(
                        roi, 0.3,  # Original image with 30% opacity
                        colored_map, 0.7,  # Quality map with 70% opacity
                        0
                    )
                    # Update the current image
                    self.main_window.current_image = composite
                else:
                    # Shapes don't match, regenerate the map
                    messagebox.showinfo("Information", "Quality map needs to be regenerated")
                    self.main_window.quality_map = None
                    # Recursively call this function to regenerate the map
                    self.show_quality_map(preserve_view)
                    return
            except Exception as e:
                # If there's any error in processing, fall back to original image
                messagebox.showerror("Error", f"Error processing quality map: {str(e)}")
                self.main_window.quality_map = None
                self.main_window.current_image = self.main_window.original_image.copy()
        else:
            # Show original image
            self.main_window.current_image = self.main_window.original_image.copy()

        # Convert to PIL and display
        pil_image = Image.fromarray(self.main_window.current_image)
        self.display_image(pil_image, preserve_view)

        # Update status
        self.main_window.status_var.set(status_msg)

    def _generate_quality_map(self, roi):
        """Generate a quality map for the ROI with pixel-by-pixel analysis"""
        # Convert to grayscale if needed
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        else:
            gray = roi.copy()

        # Create an empty quality map (normalized to 0-1)
        quality_map = np.zeros_like(gray, dtype=float)

        # Window size for local analysis
        window_size = 15
        half_window = window_size // 2

        # Pad the image to handle borders
        padded = cv2.copyMakeBorder(gray, half_window, half_window, half_window, half_window,
                                    cv2.BORDER_REFLECT)

        h, w = gray.shape

        # Calculate gradient magnitude for the entire image
        grad_x = cv2.Sobel(padded, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(padded, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)

        # Perform local analysis
        for y in range(h):
            for x in range(w):
                # Extract local window from padded image
                window = padded[y:y + window_size, x:x + window_size]
                grad_window = grad_mag[y:y + window_size, x:x + window_size]

                # Calculate local quality metrics
                local_contrast = np.std(window) / (np.mean(window) + 1e-5)
                local_gradient = np.mean(grad_window)

                # Simple quality score based on contrast and gradient
                quality = (local_contrast * 0.5 + local_gradient / 50 * 0.5)
                quality_map[y, x] = quality

        # Normalize quality map to 0-1 range
        if np.max(quality_map) > 0:
            quality_map = quality_map / np.max(quality_map)

        return quality_map

    def debug_roi_coords(self):
        """Print current ROI coordinates and scales for debugging"""
        if hasattr(self.main_window, 'roi_handler') and self.main_window.roi_handler.roi_coords:
            roi = self.main_window.roi_handler.roi_coords
            print(f"ROI: {roi} | Display scale: {self.display_scale} | Zoom: {self.zoom_level}")

    def reset_display(self):
        """Reset the display by clearing ROI and showing original image"""
        # Clear ROI if it exists
        if hasattr(self.main_window, 'roi_handler'):
            self.main_window.roi_handler.clear_roi()

        # Reset to original image
        if hasattr(self.main_window, 'original_image') and self.main_window.original_image is not None:
            self.main_window.current_image = self.main_window.original_image.copy()
            pil_image = Image.fromarray(self.main_window.current_image)

            # Capture current view state
            current_zoom = self.zoom_level
            visible_x = self.canvas.xview()
            visible_y = self.canvas.yview()

            # Display image while preserving view position
            self.display_image(pil_image, preserve_view=True)

            # Store view state for later use if needed
            self.temp_zoom = current_zoom
            self.temp_x_view = visible_x
            self.temp_y_view = visible_y

        # Update status
        self.main_window.status_var.set("Display reset - ROI cleared and original image restored")

    def sync_view_state(self):
        """Capture current view state and store it for later use"""
        current_zoom = self.zoom_level
        visible_x = self.canvas.xview()
        visible_y = self.canvas.yview()

        # Debug info
        print(f"Syncing view state: zoom={current_zoom}, x={visible_x}, y={visible_y}")

        # Store for later use
        self.temp_zoom = current_zoom
        self.temp_x_view = visible_x
        self.temp_y_view = visible_y

        return current_zoom, visible_x, visible_y