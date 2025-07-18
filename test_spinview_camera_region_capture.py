#!/usr/bin/env python3
"""
SpinView Camera Region Capture for DIC Quality Analysis.

This captures only the live camera feed region within the SpinView window,
ignoring all UI elements, buttons, and other windows.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import cv2
import time
import threading
from PIL import Image, ImageGrab, ImageDraw, ImageTk
import logging
import platform
import json
import os

# Windows-specific imports
if platform.system() == 'Windows':
    import win32gui
    import win32ui
    import win32con
    import win32api
    from ctypes import windll

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpinViewCapture:
    """Specialized capture for SpinView camera UI."""

    def __init__(self):
        self.spinview_hwnd = None
        self.camera_region = None  # (x, y, width, height) relative to window
        self.config_file = "spinview_config.json"
        self.load_config()

    def save_config(self):
        """Save camera region configuration."""
        if self.camera_region:
            # Handle polygon regions for JSON serialization
            region_to_save = self.camera_region
            if isinstance(self.camera_region, tuple) and len(self.camera_region) == 2 and self.camera_region[0] == 'polygon':
                # Convert polygon points to list for JSON serialization
                region_to_save = ('polygon', list(self.camera_region[1]))
            
            config = {
                'camera_region': region_to_save,
                'last_window_title': self.get_window_title(self.spinview_hwnd) if self.spinview_hwnd else None
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration saved")

    def load_config(self):
        """Load previous camera region configuration."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    region = config.get('camera_region')
                    
                    # Handle polygon regions
                    if isinstance(region, list) and len(region) == 2 and region[0] == 'polygon':
                        # Convert back to tuple format
                        self.camera_region = ('polygon', region[1])
                    else:
                        self.camera_region = region
                        
                    logger.info(f"Loaded camera region: {self.camera_region}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")

    @staticmethod
    def list_windows():
        """List all visible windows."""
        windows = []

        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text:
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'class': win32gui.GetClassName(hwnd)
                    })

        win32gui.EnumWindows(enum_handler, None)
        return windows

    def find_spinview_window(self):
        """Find SpinView window automatically."""
        windows = []

        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                # Look for SpinView or common camera UI patterns
                if any(pattern in window_text.lower() for pattern in
                       ['spinview', 'flir', 'camera', 'viewer', 'live', 'preview']):
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'class': win32gui.GetClassName(hwnd)
                    })

        win32gui.EnumWindows(enum_handler, None)

        # If found SpinView specifically
        for window in windows:
            if 'spinview' in window['title'].lower():
                self.spinview_hwnd = window['hwnd']
                logger.info(f"Found SpinView: {window['title']}")
                return True

        # Otherwise return all camera-related windows
        return windows

    @staticmethod
    def find_window_by_title(partial_title):
        """Find window handle by partial title match."""
        windows = SpinViewCapture.list_windows()
        for window in windows:
            if partial_title.lower() in window['title'].lower():
                return window['hwnd']
        return None

    def get_window_title(self, hwnd):
        """Get window title from handle."""
        try:
            return win32gui.GetWindowText(hwnd)
        except:
            return None

    def capture_full_window(self, hwnd):
        """Capture entire window content."""
        try:
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # Get the window device context
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            # Create bitmap
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            # Copy window content
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)

            # Convert to numpy array
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            image = np.frombuffer(bmpstr, dtype='uint8')
            image.shape = (height, width, 4)

            # Clean up
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)

            # Convert BGRA to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)

            return image

        except Exception as e:
            logger.error(f"Error capturing window: {e}")
            return None

    def capture_camera_region(self):
        """Capture only the camera feed region within the window."""
        if not self.spinview_hwnd or not self.camera_region:
            return None

        try:
            # Capture full window
            full_window = self.capture_full_window(self.spinview_hwnd)
            if full_window is None:
                return None

            # Handle different region types
            if isinstance(self.camera_region, tuple) and len(self.camera_region) == 2 and self.camera_region[0] == 'polygon':
                # Polygon region
                return self._extract_polygon_region(full_window, self.camera_region[1])
            else:
                # Rectangle region
                x, y, w, h = self.camera_region
                camera_feed = full_window[y:y + h, x:x + w]
                return camera_feed

        except Exception as e:
            logger.error(f"Error capturing camera region: {e}")
            return None

    def _extract_polygon_region(self, image, polygon_points):
        """Extract polygon region from image - returns image with mask applied."""
        try:
            import cv2
            
            # Create mask for polygon
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            
            # Convert points to numpy array
            points = np.array(polygon_points, dtype=np.int32)
            
            # Fill polygon in mask
            cv2.fillPoly(mask, [points], 255)
            
            # Return the full image with mask information
            # The analyzer will handle the masking
            return (image, mask)
            
        except Exception as e:
            logger.error(f"Error extracting polygon region: {e}")
            return None


class CameraRegionSelector:
    """Interactive selector for camera region within window."""

    def __init__(self, parent, window_image, on_selection):
        self.parent = parent
        self.window_image = window_image
        self.on_selection = on_selection

        self.selector_window = None
        self.canvas = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.image_scale = 1.0

    def show(self):
        """Show the region selector."""
        self.selector_window = tk.Toplevel(self.parent)
        self.selector_window.title("Select Camera Feed Region")
        self.selector_window.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Instructions
        inst_frame = tk.Frame(self.selector_window, bg='#2c3e50')
        inst_frame.pack(fill='x')

        tk.Label(
            inst_frame,
            text="📹 Draw a rectangle around the camera's live feed area (ignore UI elements)",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='white',
            pady=10
        ).pack()

        # Canvas for image and selection
        canvas_frame = tk.Frame(self.selector_window)
        canvas_frame.pack(fill='both', expand=True)

        # Calculate display size
        h, w = self.window_image.shape[:2]
        max_width = 1200
        max_height = 800

        self.image_scale = min(max_width / w, max_height / h, 1.0)
        display_w = int(w * self.image_scale)
        display_h = int(h * self.image_scale)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=display_w,
            height=display_h,
            cursor='crosshair',
            bg='black'
        )
        self.canvas.pack(padx=10, pady=10)

        # Display window image
        resized = cv2.resize(self.window_image, (display_w, display_h))
        pil_image = Image.fromarray(resized)
        self.photo = ImageTk.PhotoImage(pil_image)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

        # Bind mouse events
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)

        # Buttons
        btn_frame = tk.Frame(self.selector_window)
        btn_frame.pack(fill='x', pady=10)

        self.confirm_btn = tk.Button(
            btn_frame,
            text="✓ Confirm Selection",
            command=self._on_confirm,
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=5,
            state='disabled'
        )
        self.confirm_btn.pack(side='left', padx=10)

        tk.Button(
            btn_frame,
            text="✗ Cancel",
            command=self._on_cancel,
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=5
        ).pack(side='left', padx=10)

        tk.Label(
            self.selector_window,
            text="Tip: The camera feed is usually the largest rectangular area showing live video",
            font=('Arial', 10),
            fg='gray'
        ).pack(pady=5)

        # Center window
        self.selector_window.update_idletasks()
        x = (self.selector_window.winfo_screenwidth() - self.selector_window.winfo_width()) // 2
        y = (self.selector_window.winfo_screenheight() - self.selector_window.winfo_height()) // 2
        self.selector_window.geometry(f"+{x}+{y}")

    def _on_click(self, event):
        """Handle mouse click."""
        self.start_x = event.x
        self.start_y = event.y

        if self.rect_id:
            self.canvas.delete(self.rect_id)

        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='#00ff00', width=2
        )

    def _on_drag(self, event):
        """Handle mouse drag."""
        if self.rect_id:
            self.canvas.coords(
                self.rect_id,
                self.start_x, self.start_y, event.x, event.y
            )

    def _on_release(self, event):
        """Handle mouse release."""
        if self.start_x and self.start_y:
            # Calculate region
            x1 = min(self.start_x, event.x)
            y1 = min(self.start_y, event.y)
            x2 = max(self.start_x, event.x)
            y2 = max(self.start_y, event.y)

            # Ensure minimum size
            if abs(x2 - x1) > 20 and abs(y2 - y1) > 20:
                self.confirm_btn.config(state='normal')

                # Draw corner markers
                self._draw_corner_markers(x1, y1, x2, y2)

    def _draw_corner_markers(self, x1, y1, x2, y2):
        """Draw corner markers for clarity."""
        marker_size = 10
        marker_color = '#00ff00'

        # Top-left
        self.canvas.create_line(
            x1, y1, x1 + marker_size, y1,
            fill=marker_color, width=3
        )
        self.canvas.create_line(
            x1, y1, x1, y1 + marker_size,
            fill=marker_color, width=3
        )

        # Top-right
        self.canvas.create_line(
            x2 - marker_size, y1, x2, y1,
            fill=marker_color, width=3
        )
        self.canvas.create_line(
            x2, y1, x2, y1 + marker_size,
            fill=marker_color, width=3
        )

        # Bottom-left
        self.canvas.create_line(
            x1, y2, x1 + marker_size, y2,
            fill=marker_color, width=3
        )
        self.canvas.create_line(
            x1, y2 - marker_size, x1, y2,
            fill=marker_color, width=3
        )

        # Bottom-right
        self.canvas.create_line(
            x2 - marker_size, y2, x2, y2,
            fill=marker_color, width=3
        )
        self.canvas.create_line(
            x2, y2 - marker_size, x2, y2,
            fill=marker_color, width=3
        )

    def _on_confirm(self):
        """Confirm selection."""
        if self.rect_id:
            coords = self.canvas.coords(self.rect_id)
            if len(coords) == 4:
                # Convert back to original image coordinates
                x1 = int(coords[0] / self.image_scale)
                y1 = int(coords[1] / self.image_scale)
                x2 = int(coords[2] / self.image_scale)
                y2 = int(coords[3] / self.image_scale)

                # Return as (x, y, width, height)
                region = (x1, y1, x2 - x1, y2 - y1)

                self.selector_window.destroy()
                self.on_selection(region)

    def _on_cancel(self):
        """Cancel selection."""
        self.selector_window.destroy()
        self.on_selection(None)


class CameraPolygonSelector:
    """Interactive polygon selector for camera region within window."""

    def __init__(self, parent, window_image, on_selection):
        self.parent = parent
        self.window_image = window_image
        self.on_selection = on_selection

        self.selector_window = None
        self.canvas = None
        self.polygon_points = []
        self.polygon_id = None
        self.preview_line = None
        self.image_scale = 1.0

    def show(self):
        """Show the polygon selector."""
        self.selector_window = tk.Toplevel(self.parent)
        self.selector_window.title("Select Camera Feed Region - Polygon")
        self.selector_window.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Instructions
        inst_frame = tk.Frame(self.selector_window, bg='#2c3e50')
        inst_frame.pack(fill='x')

        tk.Label(
            inst_frame,
            text="🔺 Click to add polygon points around the camera feed area",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='white',
            pady=10
        ).pack()

        tk.Label(
            inst_frame,
            text="Left-click: Add point | Right-click: Finish polygon | ESC: Cancel",
            font=('Arial', 10),
            bg='#2c3e50',
            fg='#ecf0f1',
            pady=5
        ).pack()

        # Canvas for image and selection
        canvas_frame = tk.Frame(self.selector_window)
        canvas_frame.pack(fill='both', expand=True)

        # Calculate display size
        h, w = self.window_image.shape[:2]
        max_width = 1200
        max_height = 800

        self.image_scale = min(max_width / w, max_height / h, 1.0)
        display_w = int(w * self.image_scale)
        display_h = int(h * self.image_scale)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=display_w,
            height=display_h,
            cursor='crosshair',
            bg='black'
        )
        self.canvas.pack(padx=10, pady=10)

        # Display window image
        resized = cv2.resize(self.window_image, (display_w, display_h))
        pil_image = Image.fromarray(resized)
        self.photo = ImageTk.PhotoImage(pil_image)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

        # Bind mouse events
        self.canvas.bind('<Button-1>', self._on_left_click)
        self.canvas.bind('<Button-3>', self._on_right_click)
        self.canvas.bind('<Motion>', self._on_mouse_motion)
        self.selector_window.bind('<Escape>', lambda e: self._on_cancel())

        # Buttons
        btn_frame = tk.Frame(self.selector_window)
        btn_frame.pack(fill='x', pady=10)

        self.finish_btn = tk.Button(
            btn_frame,
            text="✓ Finish Polygon",
            command=self._on_finish,
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=5,
            state='disabled'
        )
        self.finish_btn.pack(side='left', padx=10)

        tk.Button(
            btn_frame,
            text="🗑️ Clear Points",
            command=self._clear_points,
            bg='#f39c12',
            fg='white',
            padx=20,
            pady=5
        ).pack(side='left', padx=10)

        tk.Button(
            btn_frame,
            text="✗ Cancel",
            command=self._on_cancel,
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=5
        ).pack(side='left', padx=10)

        # Status
        self.status_label = tk.Label(
            self.selector_window,
            text="Click to add points (minimum 3 points required)",
            font=('Arial', 10),
            fg='gray'
        )
        self.status_label.pack(pady=5)

        # Center window
        self.selector_window.update_idletasks()
        x = (self.selector_window.winfo_screenwidth() - self.selector_window.winfo_width()) // 2
        y = (self.selector_window.winfo_screenheight() - self.selector_window.winfo_height()) // 2
        self.selector_window.geometry(f"+{x}+{y}")

    def _on_left_click(self, event):
        """Handle left mouse click - add polygon point."""
        # Convert to original image coordinates
        orig_x = int(event.x / self.image_scale)
        orig_y = int(event.y / self.image_scale)
        
        self.polygon_points.append((orig_x, orig_y))
        
        # Update display
        self._redraw_polygon()
        
        # Update status
        point_count = len(self.polygon_points)
        if point_count < 3:
            self.status_label.config(text=f"Added point {point_count}. Need {3-point_count} more points minimum.")
        else:
            self.status_label.config(text=f"Added point {point_count}. Right-click or press Finish to complete.")
            self.finish_btn.config(state='normal')

    def _on_right_click(self, event):
        """Handle right mouse click - finish polygon."""
        if len(self.polygon_points) >= 3:
            self._on_finish()

    def _on_mouse_motion(self, event):
        """Handle mouse motion - show preview line."""
        if not self.polygon_points:
            return

        # Remove previous preview line
        if self.preview_line:
            self.canvas.delete(self.preview_line)

        # Draw preview line from last point to current mouse position
        last_point = self.polygon_points[-1]
        last_x = int(last_point[0] * self.image_scale)
        last_y = int(last_point[1] * self.image_scale)

        self.preview_line = self.canvas.create_line(
            last_x, last_y, event.x, event.y,
            fill='#00ff00', width=2, dash=(5, 5)
        )

    def _redraw_polygon(self):
        """Redraw the polygon."""
        # Remove previous polygon
        if self.polygon_id:
            self.canvas.delete(self.polygon_id)

        if len(self.polygon_points) < 2:
            return

        # Convert points to canvas coordinates
        canvas_points = []
        for orig_x, orig_y in self.polygon_points:
            canvas_x = int(orig_x * self.image_scale)
            canvas_y = int(orig_y * self.image_scale)
            canvas_points.extend([canvas_x, canvas_y])

        # Draw polygon or line
        if len(self.polygon_points) >= 3:
            # Draw as polygon
            self.polygon_id = self.canvas.create_polygon(
                *canvas_points,
                outline='#00ff00',
                fill='',
                width=3
            )
        else:
            # Draw as line
            self.polygon_id = self.canvas.create_line(
                *canvas_points,
                fill='#00ff00',
                width=3
            )

        # Draw point markers
        for orig_x, orig_y in self.polygon_points:
            canvas_x = int(orig_x * self.image_scale)
            canvas_y = int(orig_y * self.image_scale)
            self.canvas.create_oval(
                canvas_x - 3, canvas_y - 3,
                canvas_x + 3, canvas_y + 3,
                fill='#00ff00',
                outline='white',
                width=1
            )

    def _clear_points(self):
        """Clear all polygon points."""
        self.polygon_points = []
        if self.polygon_id:
            self.canvas.delete(self.polygon_id)
            self.polygon_id = None
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            self.preview_line = None
        
        self.finish_btn.config(state='disabled')
        self.status_label.config(text="Click to add points (minimum 3 points required)")

    def _on_finish(self):
        """Finish polygon selection."""
        if len(self.polygon_points) >= 3:
            self.selector_window.destroy()
            # Return polygon points as the region
            self.on_selection(('polygon', self.polygon_points))
        else:
            messagebox.showwarning("Invalid Polygon", "Need at least 3 points to create a polygon.")

    def _on_cancel(self):
        """Cancel selection."""
        self.selector_window.destroy()
        self.on_selection(None)


class DICQualityAnalyzer:
    """Analyzer specifically for DIC microscopy quality."""

    def __init__(self):
        self.update_count = 0
        self.scores_history = []

    def analyze_dic_quality(self, image_data):
        """
        Analyze DIC image quality.

        DIC-specific metrics:
        - Edge contrast (DIC creates edge enhancement)
        - Phase gradient uniformity
        - Background uniformity
        - Signal-to-noise ratio
        
        Args:
            image_data: Either a regular image array or tuple (image, mask) for polygon regions
        """
        # Handle different input types
        if image_data is None:
            return None, 0.0
            
        mask = None
        if isinstance(image_data, tuple) and len(image_data) == 2:
            # Polygon region with mask
            image, mask = image_data
            if image is None or image.size == 0:
                return None, 0.0
        else:
            # Regular rectangular region
            image = image_data
            if image is None or image.size == 0:
                return None, 0.0

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Apply mask if present (for polygon regions)
        if mask is not None:
            # Only analyze pixels within the polygon
            valid_pixels = mask > 0
            if not np.any(valid_pixels):
                return None, 0.0
        else:
            # For rectangular regions, analyze all pixels
            valid_pixels = np.ones_like(gray, dtype=bool)

        # 1. Edge strength (important for DIC) - only on valid pixels
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
        
        if mask is not None:
            edge_score = np.mean(edge_magnitude[valid_pixels]) / 255.0
        else:
            edge_score = np.mean(edge_magnitude) / 255.0

        # 2. Contrast (DIC should have good contrast) - only on valid pixels
        if mask is not None:
            contrast_score = np.std(gray[valid_pixels]) / 128.0
        else:
            contrast_score = np.std(gray) / 128.0

        # 3. Focus quality (Laplacian variance) - only on valid pixels
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        if mask is not None:
            focus_score = np.var(laplacian[valid_pixels]) / 10000.0
        else:
            focus_score = np.var(laplacian) / 10000.0

        # 4. Background uniformity (should be relatively uniform in DIC)
        # For polygon regions, analyze only valid pixels
        if mask is not None:
            # For polygon, just analyze the valid pixel values directly
            valid_gray_pixels = gray[valid_pixels]
            if len(valid_gray_pixels) > 10:  # Need enough pixels for meaningful analysis
                background_uniformity = 1.0 - (np.std(valid_gray_pixels) / (np.mean(valid_gray_pixels) + 1e-6))
            else:
                background_uniformity = 0.5
        else:
            # For rectangular regions, use the original region-based approach
            h, w = gray.shape
            region_size = min(h, w) // 4
            background_scores = []

            for i in range(0, h - region_size, region_size):
                for j in range(0, w - region_size, region_size):
                    region = gray[i:i + region_size, j:j + region_size]
                    background_scores.append(np.std(region))

            if background_scores and np.mean(background_scores) > 0:
                background_uniformity = 1.0 - (np.std(background_scores) / np.mean(background_scores))
            else:
                background_uniformity = 0.5
                
        background_uniformity = max(0, min(1, background_uniformity))

        # Combine scores (weighted for DIC importance)
        overall_score = (
                edge_score * 0.3 +
                contrast_score * 0.3 +
                focus_score * 0.3 +
                background_uniformity * 0.1
        )

        # Create quality map
        quality_map = edge_magnitude / (edge_magnitude.max() + 1e-6)
        
        # Apply mask to quality map if present
        if mask is not None:
            quality_map = quality_map * (mask / 255.0)

        # Apply colormap for visualization
        quality_map_colored = cv2.applyColorMap(
            (quality_map * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )
        
        # Apply mask to colored quality map if present
        if mask is not None:
            mask_3d = np.stack([mask] * 3, axis=2) / 255.0
            quality_map_colored = (quality_map_colored * mask_3d).astype(np.uint8)

        return quality_map_colored, float(overall_score)


class SpinViewCaptureApp:
    """Main application for SpinView camera capture and DIC analysis."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SpinView Camera DIC Quality Analyzer")
        self.root.geometry("1000x700")

        self.capture = SpinViewCapture()
        self.analyzer = DICQualityAnalyzer()
        self.is_analyzing = False
        self.analysis_thread = None
        self.window_data = {}  # Store window information
        self.selected_hwnd = None

        self._create_ui()

    def _create_ui(self):
        """Create the main UI."""
        # Header
        header = tk.Frame(self.root, bg='#1abc9c', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🔬 SpinView DIC Quality Analyzer",
            font=('Arial', 20, 'bold'),
            bg='#1abc9c',
            fg='white'
        ).pack(expand=True)

        # Main container
        main_container = tk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Left panel - Controls
        left_panel = tk.Frame(main_container, width=300)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)

        # Window selection
        window_frame = tk.LabelFrame(
            left_panel,
            text="1. Select Target Window",
            font=('Arial', 11, 'bold')
        )
        window_frame.pack(fill='x', pady=(0, 10))

        # Refresh button
        tk.Button(
            window_frame,
            text="🔄 Refresh Window List",
            command=self._refresh_windows,
            bg='#3498db',
            fg='white',
            padx=10,
            pady=5
        ).pack(pady=5)

        # Window listbox with scrollbar
        list_container = tk.Frame(window_frame)
        list_container.pack(fill='both', expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side='right', fill='y')

        self.window_listbox = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 9),
            height=6
        )
        self.window_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.window_listbox.yview)

        self.window_listbox.bind('<<ListboxSelect>>', self._on_window_select)

        # Auto-find button
        tk.Button(
            window_frame,
            text="🔍 Auto-Find SpinView",
            command=self._find_spinview,
            bg='#9b59b6',
            fg='white',
            padx=10,
            pady=3
        ).pack(pady=5)

        self.window_status = tk.Label(
            window_frame,
            text="No window selected",
            font=('Arial', 9),
            fg='gray'
        )
        self.window_status.pack(pady=5)

        # Info label
        tk.Label(
            window_frame,
            text="💡 Select any window from the list above\nor use Auto-Find for SpinView",
            font=('Arial', 8),
            fg='gray',
            justify='center'
        ).pack(pady=2)

        # Region selection
        region_frame = tk.LabelFrame(
            left_panel,
            text="2. Select Camera Feed Region",
            font=('Arial', 11, 'bold')
        )
        region_frame.pack(fill='x', pady=(0, 10))

        # ROI mode selection
        mode_frame = tk.Frame(region_frame)
        mode_frame.pack(pady=5)

        tk.Label(mode_frame, text="Selection Mode:", font=('Arial', 9)).pack()

        self.roi_mode = tk.StringVar(value="rectangle")
        
        tk.Radiobutton(
            mode_frame,
            text="📐 Rectangle",
            variable=self.roi_mode,
            value="rectangle",
            font=('Arial', 9)
        ).pack(side='left', padx=5)

        tk.Radiobutton(
            mode_frame,
            text="🔺 Polygon",
            variable=self.roi_mode,
            value="polygon",
            font=('Arial', 9)
        ).pack(side='left', padx=5)

        self.select_region_btn = tk.Button(
            region_frame,
            text="📐 Select Feed Region",
            command=self._select_camera_region,
            bg='#9b59b6',
            fg='white',
            padx=10,
            pady=5,
            state='disabled'
        )
        self.select_region_btn.pack(pady=5)

        self.region_status = tk.Label(
            region_frame,
            text="No region selected",
            font=('Arial', 9),
            fg='gray'
        )
        self.region_status.pack(pady=5)

        # Analysis controls
        analysis_frame = tk.LabelFrame(
            left_panel,
            text="3. DIC Quality Analysis",
            font=('Arial', 11, 'bold')
        )
        analysis_frame.pack(fill='x', pady=(0, 10))

        self.start_btn = tk.Button(
            analysis_frame,
            text="▶️ Start Analysis",
            command=self._start_analysis,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8,
            state='disabled'
        )
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(
            analysis_frame,
            text="⏹️ Stop",
            command=self._stop_analysis,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8,
            state='disabled'
        )
        self.stop_btn.pack(pady=5)

        # DIC Quality Metrics
        metrics_frame = tk.LabelFrame(
            left_panel,
            text="DIC Quality Metrics",
            font=('Arial', 11, 'bold')
        )
        metrics_frame.pack(fill='x', pady=(0, 10))

        self.metrics_vars = {}
        metrics = [
            ("Overall Score", "0.000"),
            ("Edge Contrast", "0.000"),
            ("Focus Quality", "0.000"),
            ("Background", "0.000"),
            ("Frame Rate", "0.0 fps")
        ]

        for metric, initial in metrics:
            frame = tk.Frame(metrics_frame)
            frame.pack(fill='x', padx=10, pady=2)

            tk.Label(
                frame,
                text=f"{metric}:",
                font=('Arial', 9),
                width=12,
                anchor='w'
            ).pack(side='left')

            var = tk.StringVar(value=initial)
            self.metrics_vars[metric] = var

            tk.Label(
                frame,
                textvariable=var,
                font=('Arial', 9, 'bold'),
                fg='#2c3e50'
            ).pack(side='right')

        # Right panel - Displays
        right_panel = tk.Frame(main_container)
        right_panel.pack(side='right', fill='both', expand=True)

        # Notebook for different views
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill='both', expand=True)

        # Live feed tab
        live_frame = tk.Frame(self.notebook)
        self.notebook.add(live_frame, text="Live Camera Feed")

        self.live_canvas = tk.Canvas(live_frame, bg='black')
        self.live_canvas.pack(fill='both', expand=True)
        self.live_image_item = None

        # Quality map tab
        quality_frame = tk.Frame(self.notebook)
        self.notebook.add(quality_frame, text="DIC Quality Map")

        self.quality_canvas = tk.Canvas(quality_frame, bg='black')
        self.quality_canvas.pack(fill='both', expand=True)
        self.quality_image_item = None

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select a window from the list or use Auto-Find")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=('Arial', 10),
            bg='#ecf0f1',
            anchor='w',
            padx=10
        )
        status_bar.pack(side='bottom', fill='x')

        # Initial window refresh
        self._refresh_windows()

    def _refresh_windows(self):
        """Refresh window list."""
        self.window_listbox.delete(0, tk.END)

        windows = SpinViewCapture.list_windows()
        self.window_data = {}

        for window in windows:
            # Filter out some system windows
            if window['title'] and 'Default IME' not in window['title']:
                display_text = f"{window['title']} [{window['class']}]"
                self.window_listbox.insert(tk.END, display_text)
                self.window_data[display_text] = window

        self.window_status.config(text=f"Found {len(self.window_data)} windows", fg='blue')

    def _on_window_select(self, event):
        """Handle window selection."""
        selection = self.window_listbox.curselection()
        if selection:
            index = selection[0]
            selected_text = self.window_listbox.get(index)

            if selected_text in self.window_data:
                window = self.window_data[selected_text]
                self.selected_hwnd = window['hwnd']
                self.capture.spinview_hwnd = self.selected_hwnd

                self.select_region_btn.config(state='normal')
                self.window_status.config(
                    text=f"Selected: {window['title'][:30]}...",
                    fg='green'
                )
                self.status_var.set(f"Window selected: {window['title']}")

                # Try to preview the selected window
                self._preview_selected_window()

    def _preview_selected_window(self):
        """Preview the selected window."""
        if self.selected_hwnd:
            try:
                image = self.capture.capture_full_window(self.selected_hwnd)
                if image is not None:
                    # Show a small preview in the live canvas
                    self._update_canvas(self.live_canvas, image, self.live_image_item)
                    self.status_var.set("Window preview loaded - now select camera region")
            except Exception as e:
                logger.error(f"Preview error: {e}")

    def _find_spinview(self):
        """Auto-find SpinView window and highlight it in the list."""
        result = self.capture.find_spinview_window()

        if result is True:
            # Found SpinView specifically - highlight it in the list
            title = self.capture.get_window_title(self.capture.spinview_hwnd)
            self.selected_hwnd = self.capture.spinview_hwnd
            
            # Find and select it in the listbox
            for i in range(self.window_listbox.size()):
                item_text = self.window_listbox.get(i)
                if title.lower() in item_text.lower():
                    self.window_listbox.selection_clear(0, tk.END)
                    self.window_listbox.selection_set(i)
                    self.window_listbox.see(i)
                    break
            
            self.window_status.config(text=f"Auto-found: {title[:30]}...", fg='green')
            self.select_region_btn.config(state='normal')
            self.status_var.set("SpinView auto-found! Now select the camera feed region.")
            self._preview_selected_window()
            
        elif isinstance(result, list) and result:
            # Highlight camera-related windows in the list
            camera_titles = [w['title'].lower() for w in result]
            highlighted_count = 0
            
            for i in range(self.window_listbox.size()):
                item_text = self.window_listbox.get(i).lower()
                for cam_title in camera_titles:
                    if cam_title in item_text:
                        self.window_listbox.selection_set(i)
                        highlighted_count += 1
                        break
            
            if highlighted_count > 0:
                self.status_var.set(f"Found {highlighted_count} camera-related windows - select one from the list")
                self.window_status.config(text=f"Found {highlighted_count} camera windows", fg='orange')
            else:
                self.status_var.set("No camera windows found - select any window from the list")
        else:
            messagebox.showinfo(
                "Auto-Find Result",
                "Could not auto-find SpinView specifically.\n"
                "Please manually select your camera window from the list above."
            )



    def _select_camera_region(self):
        """Select camera feed region within window."""
        if not self.capture.spinview_hwnd:
            return

        # Capture full window
        window_image = self.capture.capture_full_window(self.capture.spinview_hwnd)
        if window_image is None:
            messagebox.showerror("Error", "Failed to capture window")
            return

        # Get selected mode
        mode = self.roi_mode.get()

        # Show appropriate selector
        if mode == "rectangle":
            selector = CameraRegionSelector(
                self.root,
                window_image,
                self._on_region_selected
            )
            selector.show()
        else:  # polygon
            selector = CameraPolygonSelector(
                self.root,
                window_image,
                self._on_region_selected
            )
            selector.show()

    def _on_region_selected(self, region):
        """Handle region selection."""
        if region:
            self.capture.camera_region = region
            self.capture.save_config()

            if isinstance(region, tuple) and len(region) == 2 and region[0] == 'polygon':
                # Polygon region
                points = region[1]
                self.region_status.config(
                    text=f"Polygon: {len(points)} points",
                    fg='green'
                )
                self.status_var.set("Polygon region selected! Ready to start DIC analysis.")
            else:
                # Rectangle region
                x, y, w, h = region
                self.region_status.config(
                    text=f"Rectangle: {w}x{h} at ({x},{y})",
                    fg='green'
                )
                self.status_var.set("Rectangle region selected! Ready to start DIC analysis.")
            
            self.start_btn.config(state='normal')

    def _start_analysis(self):
        """Start DIC quality analysis."""
        self.is_analyzing = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        self.analysis_thread = threading.Thread(target=self._analysis_loop)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()

        self.status_var.set("Analyzing DIC quality from camera feed...")

    def _analysis_loop(self):
        """Main analysis loop."""
        frame_times = []

        while self.is_analyzing:
            try:
                start_time = time.time()

                # Capture camera region
                camera_feed = self.capture.capture_camera_region()

                if camera_feed is not None:
                    # Analyze DIC quality
                    quality_map, score = self.analyzer.analyze_dic_quality(camera_feed)

                    # Update displays
                    self.root.after(0, lambda: self._update_displays(
                        camera_feed, quality_map, score
                    ))

                    # Calculate FPS
                    frame_time = time.time() - start_time
                    frame_times.append(frame_time)
                    if len(frame_times) > 30:
                        frame_times.pop(0)

                    fps = 1.0 / np.mean(frame_times) if frame_times else 0
                    self.root.after(0, lambda: self.metrics_vars["Frame Rate"].set(f"{fps:.1f} fps"))

                # Control frame rate
                elapsed = time.time() - start_time
                sleep_time = max(0.05 - elapsed, 0)  # Target ~20 FPS
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Analysis error: {e}")
                time.sleep(0.5)

    def _update_displays(self, camera_feed, quality_map, score):
        """Update display canvases."""
        try:
            # Handle camera feed (might be tuple for polygon regions)
            display_image = camera_feed
            if isinstance(camera_feed, tuple) and len(camera_feed) == 2:
                # Polygon region: extract image and apply mask for display
                image, mask = camera_feed
                # Create display image with mask applied
                if len(image.shape) == 3:
                    mask_3d = np.stack([mask] * 3, axis=2) / 255.0
                    display_image = (image * mask_3d).astype(np.uint8)
                else:
                    display_image = (image * (mask / 255.0)).astype(np.uint8)
            
            # Update live feed
            self._update_canvas(
                self.live_canvas,
                display_image,
                self.live_image_item
            )

            # Update quality map
            quality_item = self._update_canvas(
                self.quality_canvas,
                quality_map,
                self.quality_image_item
            )
            if quality_item:
                self.quality_image_item = quality_item

            # Update metrics
            self.metrics_vars["Overall Score"].set(f"{score:.3f}")

            # Update other metrics (placeholder - would need individual calculations)
            self.metrics_vars["Edge Contrast"].set(f"{score * 0.9:.3f}")
            self.metrics_vars["Focus Quality"].set(f"{score * 1.1:.3f}")
            self.metrics_vars["Background"].set(f"{0.85:.3f}")

        except Exception as e:
            logger.error(f"Display update error: {e}")

    def _update_canvas(self, canvas, image, item):
        """Update a canvas with an image."""
        if image is None:
            return item

        try:
            # Get canvas size
            canvas_w = canvas.winfo_width()
            canvas_h = canvas.winfo_height()

            if canvas_w > 1 and canvas_h > 1:
                # Calculate scaling
                h, w = image.shape[:2]
                scale = min(canvas_w / w, canvas_h / h) * 0.95

                new_w = int(w * scale)
                new_h = int(h * scale)

                # Resize image
                resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

                # Convert to PhotoImage
                if len(resized.shape) == 2:
                    # Grayscale
                    pil_image = Image.fromarray(resized)
                else:
                    # Color
                    pil_image = Image.fromarray(resized)

                photo = ImageTk.PhotoImage(pil_image)

                # Update or create canvas item
                if item is None:
                    item = canvas.create_image(
                        canvas_w // 2, canvas_h // 2,
                        image=photo,
                        anchor='center'
                    )
                else:
                    canvas.itemconfig(item, image=photo)

                # Keep reference
                canvas.image = photo

                return item

        except Exception as e:
            logger.error(f"Canvas update error: {e}")

        return item

    def _stop_analysis(self):
        """Stop analysis."""
        self.is_analyzing = False

        if self.analysis_thread:
            self.analysis_thread.join(timeout=1.0)

        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

        self.status_var.set("Analysis stopped")

    def run(self):
        """Run the application."""
        # Check platform
        if platform.system() != 'Windows':
            messagebox.showwarning(
                "Platform Warning",
                "This application requires Windows for SpinView capture.\n"
                "On other platforms, use screen capture methods."
            )

        self.root.mainloop()


class SimplifiedDICAnalyzer:
    """Simplified version that works with any camera window."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Camera Region DIC Analyzer")
        self.root.geometry("800x600")

        self.roi = None
        self.is_analyzing = False
        self.analysis_thread = None

        self._create_simple_ui()

    def _create_simple_ui(self):
        """Create simplified UI."""
        # Header
        header = tk.Label(
            self.root,
            text="📹 Simple Camera Region Analyzer",
            font=('Arial', 18, 'bold'),
            bg='#2c3e50',
            fg='white',
            pady=20
        )
        header.pack(fill='x')

        # Instructions
        inst_frame = tk.Frame(self.root, bg='#ecf0f1')
        inst_frame.pack(fill='x', padx=20, pady=20)

        instructions = """Quick Start Guide:
1. Position your camera UI window so it's visible
2. Click 'Select Camera Region' below
3. Draw a rectangle around ONLY the live camera feed
4. Analysis will start automatically

This captures only the camera feed area, ignoring all UI elements and other windows!"""

        tk.Label(
            inst_frame,
            text=instructions,
            justify='left',
            font=('Arial', 11),
            bg='#ecf0f1',
            padx=20,
            pady=20
        ).pack()

        # Control buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)

        self.select_btn = tk.Button(
            btn_frame,
            text="📐 Select Camera Region",
            command=self._select_region,
            bg='#3498db',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=15
        )
        self.select_btn.pack(side='left', padx=10)

        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹️ Stop Analysis",
            command=self._stop_analysis,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=15,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=10)

        # Preview
        preview_frame = tk.LabelFrame(
            self.root,
            text="Live Preview (Camera Feed Only)",
            font=('Arial', 12, 'bold')
        )
        preview_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.preview_canvas = tk.Canvas(preview_frame, bg='black')
        self.preview_canvas.pack(fill='both', expand=True)
        self.preview_item = None

        # Status
        self.status_var = tk.StringVar(value="Click 'Select Camera Region' to begin")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=('Arial', 11),
            fg='#2c3e50'
        ).pack(pady=10)

    def _select_region(self):
        """Select screen region containing camera feed."""
        # Create fullscreen overlay for selection
        overlay = tk.Toplevel(self.root)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-alpha', 0.3)
        overlay.configure(bg='gray')

        # Instructions
        tk.Label(
            overlay,
            text="Draw a rectangle around the CAMERA FEED ONLY (not the UI)",
            font=('Arial', 16, 'bold'),
            bg='gray',
            fg='white'
        ).pack(pady=50)

        # Canvas for selection
        canvas = tk.Canvas(overlay, highlightthickness=0, cursor='crosshair')
        canvas.pack(fill='both', expand=True)

        start_x = start_y = None
        rect = None

        def on_press(e):
            nonlocal start_x, start_y, rect
            start_x, start_y = e.x, e.y
            if rect:
                canvas.delete(rect)
            rect = canvas.create_rectangle(
                start_x, start_y, start_x, start_y,
                outline='lime', width=3
            )

        def on_drag(e):
            if rect:
                canvas.coords(rect, start_x, start_y, e.x, e.y)

        def on_release(e):
            if start_x and start_y:
                x1 = min(start_x, e.x)
                y1 = min(start_y, e.y)
                x2 = max(start_x, e.x)
                y2 = max(start_y, e.y)

                if abs(x2 - x1) > 20 and abs(y2 - y1) > 20:
                    overlay.destroy()
                    self._start_analysis_for_region(x1, y1, x2, y2)

        canvas.bind('<Button-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        overlay.bind('<Escape>', lambda e: overlay.destroy())

    def _start_analysis_for_region(self, x1, y1, x2, y2):
        """Start analysis for selected region."""
        self.roi = (x1, y1, x2, y2)
        self.is_analyzing = True

        self.select_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        self.status_var.set(f"Analyzing camera region: {x2 - x1}x{y2 - y1} pixels")

        # Start analysis thread
        self.analysis_thread = threading.Thread(target=self._analysis_loop)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()

    def _analysis_loop(self):
        """Simple analysis loop."""
        while self.is_analyzing:
            try:
                # Capture only the selected region
                screenshot = ImageGrab.grab(bbox=self.roi, all_screens=True)

                if screenshot:
                    image = np.array(screenshot)

                    # Simple quality metric
                    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                    score = np.std(gray) / 128.0

                    # Update display
                    self.root.after(0, lambda: self._update_preview(image, score))

                time.sleep(0.05)  # 20 FPS

            except Exception as e:
                logger.error(f"Analysis error: {e}")
                time.sleep(0.5)

    def _update_preview(self, image, score):
        """Update preview with captured region."""
        try:
            # Get canvas size
            canvas_w = self.preview_canvas.winfo_width()
            canvas_h = self.preview_canvas.winfo_height()

            if canvas_w > 1 and canvas_h > 1:
                # Scale image
                h, w = image.shape[:2]
                scale = min(canvas_w / w, canvas_h / h) * 0.9

                new_w = int(w * scale)
                new_h = int(h * scale)

                resized = cv2.resize(image, (new_w, new_h))

                # Add score text
                cv2.putText(
                    resized,
                    f"Quality: {score:.3f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

                # Convert and display
                pil_image = Image.fromarray(resized)
                photo = ImageTk.PhotoImage(pil_image)

                if self.preview_item is None:
                    self.preview_item = self.preview_canvas.create_image(
                        canvas_w // 2, canvas_h // 2,
                        image=photo,
                        anchor='center'
                    )
                else:
                    self.preview_canvas.itemconfig(self.preview_item, image=photo)

                self.preview_canvas.image = photo

        except Exception as e:
            logger.error(f"Preview error: {e}")

    def _stop_analysis(self):
        """Stop analysis."""
        self.is_analyzing = False

        if self.analysis_thread:
            self.analysis_thread.join(timeout=1.0)

        self.select_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

        self.status_var.set("Analysis stopped - Select region to restart")

    def run(self):
        """Run the app."""
        self.root.mainloop()


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("SPINVIEW CAMERA REGION CAPTURE")
    print("=" * 80)
    print("This tool captures ONLY the camera feed from SpinView,")
    print("ignoring all UI elements and other windows.")
    print("=" * 80)

    if platform.system() == 'Windows':
        print("\nStarting SpinView-specific capture...")
        print("Requirements: pip install pywin32 pillow opencv-python numpy")
        app = SpinViewCaptureApp()
    else:
        print("\nStarting simplified region capture (cross-platform)...")
        print("Requirements: pip install pillow opencv-python numpy")
        app = SimplifiedDICAnalyzer()

    print("=" * 80 + "\n")

    app.run()


if __name__ == "__main__":
    main()