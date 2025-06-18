# ui.image_display.py

import cv2
import numpy as np
from PIL import Image, ImageTk
from tkinter import messagebox

from analysis.quality_map.map_generator import generate_quality_map, visualize_quality_map
from analysis.utils.image_processing import get_analysis_region


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
        self.quality_map_visible = False
        self.quality_map_data = None
        self.quality_visualization = None

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
            # Prevent recursion when showing quality map
            if not hasattr(self, '_updating_quality_map') or not self._updating_quality_map:
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

        # If old_zoom not provided, store current zoom level
        if old_zoom is None:
            old_zoom = self.zoom_level

        # Get current view fractions before updating canvas
        old_x_view = self.canvas.xview()
        old_y_view = self.canvas.yview()

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

        # Update canvas
        self.canvas.delete(self.image_item)
        self.image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

        # Update scroll region
        self.canvas.configure(scrollregion=(0, 0, new_width, new_height))

        # Update the canvas.display_scale for ROI handler to use
        self.canvas.display_scale = self.display_scale * self.zoom_level

        # Calculate zoom ratio
        zoom_ratio = self.zoom_level / old_zoom

        # Calculate the view center based on rel_x and rel_y
        center_x = old_x_view[0] + (old_x_view[1] - old_x_view[0]) * rel_x
        center_y = old_y_view[0] + (old_y_view[1] - old_y_view[0]) * rel_y

        # Calculate new view position
        visible_width = self.canvas.winfo_width() / new_width
        visible_height = self.canvas.winfo_height() / new_height

        # Apply zoom adjustment to maintain the relative position
        new_x = center_x - (rel_x * visible_width)
        new_y = center_y - (rel_y * visible_height)

        # Clamp values to valid range (0 to 1-visible_fraction)
        new_x = max(0, min(1.0 - visible_width, new_x))
        new_y = max(0, min(1.0 - visible_height, new_y))

        # Apply new view position
        self.canvas.xview_moveto(new_x)
        self.canvas.yview_moveto(new_y)

        # Make sure to redraw ROI with updated position
        if hasattr(self.main_window, 'roi_handler') and self.main_window.roi_handler.roi_coords:
            self.main_window.roi_handler.redraw_roi()

    def reset_display(self):
        """Reset the display to original view and state"""
        if self.main_window is None or not hasattr(self.main_window, 'original_image'):
            return

        # Reset zoom level
        self.zoom_level = 1.0

        # Reset quality map display state
        if hasattr(self, 'showing_quality_overlay'):
            self.showing_quality_overlay = False

        # Reset quality map button appearance if it exists
        if hasattr(self.main_window, 'quality_map_btn'):
            self.main_window.quality_map_btn.config(bg='#2ecc71')  # Green when inactive

        # Show original image
        self.show_original()

        # Reset scroll position to top-left
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # Clear ROI selection
        if hasattr(self.main_window, 'roi_handler'):
            self.main_window.roi_handler.clear_roi()

        # Update status
        self.main_window.status_var.set("Display reset to original view")

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
        """Display the original image"""
        if self.main_window.original_image is None:
            return

        # Reset to original image
        self.main_window.current_image = self.main_window.original_image.copy()

        # Convert NumPy array to PIL image
        pil_image = Image.fromarray(self.main_window.current_image)

        # Display the image
        self.display_image(pil_image)

        # Redraw ROI if it exists
        self.main_window.roi_handler.redraw_roi()

        # Update status
        self.main_window.status_var.set("Showing original image")

    def show_edges(self):
        """Display edge detection visualization of the image"""
        if self.main_window.original_image is None:
            return

        # Get the appropriate image region based on ROI
        image = get_analysis_region(
            self.main_window.original_image,
            self.main_window.roi_handler.roi_coords
        )

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Create a colored edge visualization
        edge_visualization = np.zeros_like(self.main_window.original_image)
        if len(self.main_window.original_image.shape) == 3:
            # For color images, create colored edge overlay
            edge_visualization[..., 2] = edges  # Set red channel to edges
        else:
            # For grayscale, create RGB visualization
            edge_visualization = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

        # Update current image
        self.main_window.current_image = edge_visualization

        # Convert to PIL and display
        pil_image = Image.fromarray(edge_visualization)
        self.display_image(pil_image)

        # Redraw ROI
        self.main_window.roi_handler.redraw_roi()

        # Update status
        self.main_window.status_var.set("Showing edge detection visualization")

    def show_gradient(self):
        """Display gradient magnitude visualization of the image"""
        if self.main_window.original_image is None:
            return

        # Get the appropriate image region based on ROI
        image = get_analysis_region(
            self.main_window.original_image,
            self.main_window.roi_handler.roi_coords
        )

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Calculate gradients
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

        # Calculate gradient magnitude
        magnitude = cv2.magnitude(grad_x, grad_y)

        # Normalize for visualization
        cv2.normalize(magnitude, magnitude, 0, 255, cv2.NORM_MINMAX)
        gradient_vis = magnitude.astype(np.uint8)

        # Apply colormap for better visualization
        gradient_vis_colored = cv2.applyColorMap(gradient_vis, cv2.COLORMAP_JET)

        # Convert to RGB if needed
        if len(gradient_vis_colored.shape) == 2:
            gradient_vis_colored = cv2.cvtColor(gradient_vis_colored, cv2.COLOR_GRAY2RGB)
        elif gradient_vis_colored.shape[2] == 3:
            gradient_vis_colored = cv2.cvtColor(gradient_vis_colored, cv2.COLOR_BGR2RGB)

        # Update current image
        self.main_window.current_image = gradient_vis_colored

        # Convert to PIL and display
        pil_image = Image.fromarray(gradient_vis_colored)
        self.display_image(pil_image)

        # Redraw ROI
        self.main_window.roi_handler.redraw_roi()

        # Update status
        self.main_window.status_var.set("Showing gradient magnitude visualization")

    def _display_array(self, array):
        """Convert a numpy array to PIL image and display it on canvas

        Args:
            array: Numpy array (grayscale, RGB, or RGBA) to display
        """
        try:
            # Convert to uint8 if not already
            if array.dtype != np.uint8:
                array = np.clip(array, 0, 255).astype(np.uint8)

            # Convert to PIL Image based on shape
            if len(array.shape) == 2:  # Grayscale
                pil_image = Image.fromarray(array, 'L')
            elif array.shape[2] == 3:  # RGB
                pil_image = Image.fromarray(array, 'RGB')
            elif array.shape[2] == 4:  # RGBA
                pil_image = Image.fromarray(array, 'RGBA')
            else:
                raise ValueError(f"Unsupported array shape: {array.shape}")

            # Display the PIL image
            self.display_image(pil_image)

        except Exception as e:
            print(f"Error displaying array: {str(e)}")
            messagebox.showerror("Display Error", f"Failed to display image: {str(e)}")

    def debug_roi_coords(self):
        """Print current ROI coordinates and scales for debugging"""
        if hasattr(self.main_window, 'roi_handler') and self.main_window.roi_handler.roi_coords:
            roi = self.main_window.roi_handler.roi_coords
            print(f"ROI: {roi} | Display scale: {self.display_scale} | Zoom: {self.zoom_level}")

    def show_quality_map(self):
        """Display quality map as overlay on original image"""
        if not hasattr(self, 'quality_map_data') or self.quality_map_data is None:
            return

        # Store current view state
        current_zoom = self.zoom_level
        visible_x = self.canvas.xview()
        visible_y = self.canvas.yview()

        # Get the original image as the base
        original_image = self.main_window.original_image.copy()

        # Get ROI coordinates
        roi_coords = self.main_window.roi_handler.roi_coords

        # Only overlay the quality map on the ROI region
        if roi_coords:
            x1, y1, x2, y2 = roi_coords

            print(f"DEBUG: ROI coordinates: {roi_coords}")
            print(f"DEBUG: Original image shape: {original_image.shape}")
            print(f"DEBUG: Quality map shape: {self.quality_map_data.shape}")

            # Create a colored version of the quality map
            normalized_map = (self.quality_map_data * 255).astype(np.uint8)
            colormap_const = getattr(cv2, f'COLORMAP_JET', cv2.COLORMAP_JET)
            colored_map = cv2.applyColorMap(normalized_map, colormap_const)
            colored_map = cv2.cvtColor(colored_map, cv2.COLOR_BGR2RGB)

            # Extract the ROI region from the original image
            roi_height, roi_width = y2 - y1, x2 - x1

            # Make sure quality map has the right dimensions for the ROI
            if colored_map.shape[:2] != (roi_height, roi_width):
                colored_map = cv2.resize(colored_map, (roi_width, roi_height))

            # Create blended overlay just for the ROI region
            roi_overlay = cv2.addWeighted(
                original_image[y1:y2, x1:x2], 0.3,  # Keep 30% of original
                colored_map, 0.7,  # Add 70% of quality map
                0
            )

            # Apply the overlay only to the ROI region of the original image
            original_image[y1:y2, x1:x2] = roi_overlay

            print(f"DEBUG: Applied quality map overlay to ROI region only")
        else:
            # No ROI selected, apply to entire image (existing behavior)
            overlay = visualize_quality_map(original_image, self.quality_map_data)
            original_image = overlay

        # Convert to PIL image for display
        visualization_pil = Image.fromarray(original_image)

        # Set a flag to prevent recursion during display
        self._updating_quality_map = True

        # Display the visualization with preserved view
        self.display_image(visualization_pil, preserve_view=True)

        # Clear the flag
        self._updating_quality_map = False

        # Restore view state exactly
        self.zoom_level = current_zoom
        self.canvas.xview_moveto(visible_x[0])
        self.canvas.yview_moveto(visible_y[0])

        # Update state
        self.showing_quality_overlay = True

    def toggle_quality_map_overlay(self):
        """Toggle quality map overlay on/off"""
        print("DEBUG: toggle_quality_map_overlay called")

        # Initialize the state if it doesn't exist
        if not hasattr(self, 'showing_quality_overlay'):
            self.showing_quality_overlay = False
            print("DEBUG: Initialized showing_quality_overlay to False")

        # Print current state before toggling
        print(f"DEBUG: Current state before toggle: showing_quality_overlay = {self.showing_quality_overlay}")

        # Toggle the state
        self.showing_quality_overlay = not self.showing_quality_overlay
        print(f"DEBUG: New state after toggle: showing_quality_overlay = {self.showing_quality_overlay}")

        # Show or hide quality map based on toggle state
        if self.showing_quality_overlay:
            print("DEBUG: Should show quality map")

            # Check if we have quality map data
            if not hasattr(self, 'quality_map_data') or self.quality_map_data is None:
                print("DEBUG: No quality map data available")
                self.main_window.analyze_image()  # Will generate quality map
                return

            print(
                f"DEBUG: quality_map_data shape: {self.quality_map_data.shape if self.quality_map_data is not None else 'None'}")

            # Change button appearance
            if hasattr(self.main_window, 'quality_map_btn'):
                print("DEBUG: Changing button to active state")
                self.main_window.quality_map_btn.config(bg='#e74c3c')  # Red when active

            # Show quality map overlay
            self.show_quality_map()
        else:
            print("DEBUG: Should hide quality map and show original")

            # Return to original image view
            self.show_original()

            # Change button appearance
            if hasattr(self.main_window, 'quality_map_btn'):
                print("DEBUG: Changing button to inactive state")
                self.main_window.quality_map_btn.config(bg='#2ecc71')  # Green when inactive

    def overlay_quality_map(self, colormap_name='JET', alpha=0.7):
        """
        Overlay quality map on the base image

        Args:
            colormap_name: OpenCV colormap name (default: JET)
            alpha: Alpha blending factor (0-1)

        Returns:
            Overlaid image with quality map visualization
        """
        from analysis.quality_map.map_generator import visualize_quality_map

        if self.quality_map_data is None:
            return None

        # Get base image
        if self.main_window.original_image is None:
            return None

        # Get analysis region based on ROI
        base_image = get_analysis_region(
            self.main_window.original_image,
            self.main_window.roi_handler.roi_coords if hasattr(self.main_window, 'roi_handler') else None
        )

        # Generate visualization overlay using the existing function
        overlay = visualize_quality_map(base_image, self.quality_map_data,
                                        colormap_name=colormap_name, alpha=alpha)

        return overlay

    def sync_view_state(self):
        """Store current view state for later restoration"""
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

    def restore_view_state(self, zoom_level, x_view, y_view):
        """Restore a previously saved view state"""
        # Debug info
        print(f"Restoring view state: zoom={zoom_level}, x={x_view}, y={y_view}")

        # First set zoom level
        self.zoom_level = zoom_level

        # Then restore scroll positions
        if x_view and y_view:
            self.canvas.xview_moveto(x_view[0])
            self.canvas.yview_moveto(y_view[0])

        # Redraw the image with the restored zoom level
        self.main_window.display_current_image()

        # Notify ROI handler to update if needed
        if hasattr(self.main_window, 'roi_handler'):
            self.main_window.roi_handler.redraw_roi()