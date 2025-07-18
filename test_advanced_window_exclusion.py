#!/usr/bin/env python3
"""
Virtual Screen Buffer Solution.

This creates a virtual representation of the screen content
excluding specified windows, allowing clean capture while
keeping all windows visible.
"""

import tkinter as tk
import numpy as np
import cv2
import time
import threading
from PIL import Image, ImageGrab, ImageDraw
import logging
from typing import List, Tuple, Optional
import platform

if platform.system() == 'Windows':
    import win32gui

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VirtualScreenBuffer:
    """
    Creates a virtual screen buffer by compositing screen regions.

    Strategy:
    1. Capture full screen
    2. Identify regions occupied by analysis windows
    3. Replace those regions with background or previous clean capture
    4. Return composite image without app windows
    """

    def __init__(self):
        self.excluded_regions = []
        self.background_image = None
        self.last_clean_capture = None

    def set_background(self, image: np.ndarray):
        """Set background image to use for excluded regions."""
        self.background_image = image.copy()
        logger.info(f"Background set: {image.shape}")

    def add_excluded_region(self, x1: int, y1: int, x2: int, y2: int, label: str = ""):
        """Add a region to exclude from captures."""
        self.excluded_regions.append({
            'bounds': (x1, y1, x2, y2),
            'label': label
        })
        logger.info(f"Added excluded region: {label} at ({x1},{y1},{x2},{y2})")

    def clear_excluded_regions(self):
        """Clear all excluded regions."""
        self.excluded_regions.clear()

    def capture_with_exclusions(self, bbox: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Capture screen with excluded regions replaced.

        Args:
            bbox: Optional capture region (x1, y1, x2, y2)

        Returns:
            Composite image with excluded regions replaced
        """
        try:
            # Capture current screen
            screenshot = ImageGrab.grab(bbox=bbox, all_screens=True)
            current = np.array(screenshot)

            # If no exclusions, return as-is
            if not self.excluded_regions:
                return current

            # Create composite
            result = current.copy()

            # Replace excluded regions
            for region in self.excluded_regions:
                x1, y1, x2, y2 = region['bounds']

                # Adjust coordinates if bbox was used
                if bbox:
                    x1 -= bbox[0]
                    y1 -= bbox[1]
                    x2 -= bbox[0]
                    y2 -= bbox[1]

                # Ensure bounds are within image
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(result.shape[1], x2)
                y2 = min(result.shape[0], y2)

                # Replace with background or blur
                if self.background_image is not None:
                    # Use background
                    try:
                        bg_region = self.background_image[y1:y2, x1:x2]
                        if bg_region.shape == result[y1:y2, x1:x2].shape:
                            result[y1:y2, x1:x2] = bg_region
                    except:
                        # Fallback to blur
                        result[y1:y2, x1:x2] = self._blur_region(result[y1:y2, x1:x2])
                else:
                    # Blur or fill
                    result[y1:y2, x1:x2] = self._blur_region(result[y1:y2, x1:x2])

            return result

        except Exception as e:
            logger.error(f"Capture error: {e}")
            return None

    def _blur_region(self, region: np.ndarray) -> np.ndarray:
        """Apply heavy blur to a region."""
        return cv2.GaussianBlur(region, (31, 31), 0)


class SmartWindowTracker:
    """Tracks window positions for automatic exclusion."""

    def __init__(self):
        self.tracked_windows = {}

    def track_window(self, window: tk.Toplevel, label: str):
        """Track a tkinter window."""
        try:
            self.tracked_windows[label] = window
            logger.info(f"Tracking window: {label}")
        except Exception as e:
            logger.error(f"Error tracking window: {e}")

    def get_window_bounds(self, label: str) -> Optional[Tuple[int, int, int, int]]:
        """Get current bounds of tracked window."""
        if label in self.tracked_windows:
            window = self.tracked_windows[label]
            try:
                if window.winfo_exists():
                    x = window.winfo_rootx()
                    y = window.winfo_rooty()
                    w = window.winfo_width()
                    h = window.winfo_height()
                    return (x, y, x + w, y + h)
            except:
                pass
        return None

    def update_all_bounds(self) -> List[Tuple[str, Tuple[int, int, int, int]]]:
        """Update and return all window bounds."""
        bounds = []
        for label, window in list(self.tracked_windows.items()):
            window_bounds = self.get_window_bounds(label)
            if window_bounds:
                bounds.append((label, window_bounds))
            else:
                # Remove if window no longer exists
                del self.tracked_windows[label]
        return bounds


class VirtualBufferTestApp:
    """Test application for virtual screen buffer approach."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Virtual Screen Buffer Test")
        self.root.geometry("800x600")

        self.virtual_buffer = VirtualScreenBuffer()
        self.window_tracker = SmartWindowTracker()
        self.analyzer_thread = None
        self.is_analyzing = False

        self._create_ui()

    def _create_ui(self):
        """Create UI."""
        # Header
        header = tk.Frame(self.root, bg='#8e44ad', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🖼️ Virtual Screen Buffer",
            font=('Arial', 22, 'bold'),
            bg='#8e44ad',
            fg='white'
        ).pack(expand=True)

        # Info
        info_frame = tk.LabelFrame(
            self.root,
            text="How Virtual Buffer Works",
            font=('Arial', 12, 'bold')
        )
        info_frame.pack(fill='x', padx=10, pady=10)

        info_text = """This advanced solution creates a virtual screen buffer:

1. Captures the full screen
2. Automatically detects positions of analysis windows
3. Replaces those regions with background or blur
4. Returns clean composite without app windows

Benefits:
• All windows stay visible to you
• Clean captures for analysis
• No window movement needed
• Works with any window arrangement"""

        tk.Label(
            info_frame,
            text=info_text,
            justify='left',
            font=('Arial', 10)
        ).pack(padx=20, pady=10)

        # Controls
        control_frame = tk.LabelFrame(
            self.root,
            text="Controls",
            font=('Arial', 12, 'bold')
        )
        control_frame.pack(fill='x', padx=10, pady=10)

        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="📸 Capture Background",
            command=self._capture_background,
            bg='#3498db',
            fg='white',
            padx=20,
            pady=10
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="🪟 Create Test Windows",
            command=self._create_test_windows,
            bg='#9b59b6',
            fg='white',
            padx=20,
            pady=10
        ).pack(side='left', padx=5)

        self.start_btn = tk.Button(
            btn_frame,
            text="▶️ Start Analysis",
            command=self._start_analysis,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=25,
            pady=10
        )
        self.start_btn.pack(side='left', padx=5)

        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹️ Stop",
            command=self._stop_analysis,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=25,
            pady=10,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=5)

        # Preview
        preview_frame = tk.LabelFrame(
            self.root,
            text="Virtual Buffer Preview",
            font=('Arial', 12, 'bold')
        )
        preview_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.preview_canvas = tk.Canvas(preview_frame, bg='black')
        self.preview_canvas.pack(fill='both', expand=True)
        self.preview_item = None

        # Status
        self.status_var = tk.StringVar(value="Ready - Capture background first")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=('Arial', 11),
            fg='#8e44ad'
        ).pack(pady=5)

    def _capture_background(self):
        """Capture clean background."""
        self.status_var.set("Hide all windows in 3 seconds...")
        self.root.after(3000, self._do_background_capture)

    def _do_background_capture(self):
        """Actually capture background."""
        try:
            # Hide main window temporarily
            self.root.withdraw()
            time.sleep(0.5)

            # Capture
            screenshot = ImageGrab.grab(all_screens=True)
            background = np.array(screenshot)

            # Show window again
            self.root.deiconify()

            # Set background
            self.virtual_buffer.set_background(background)

            self.status_var.set("Background captured! Now create test windows.")

            # Show preview
            self._update_preview(background)

        except Exception as e:
            logger.error(f"Error capturing background: {e}")
            self.root.deiconify()

    def _create_test_windows(self):
        """Create test analysis windows."""
        # Window 1
        window1 = tk.Toplevel(self.root)
        window1.title("Analysis Window 1")
        window1.geometry("300x200+50+100")
        window1.configure(bg='lightblue')

        tk.Label(
            window1,
            text="This window will be\nexcluded from capture",
            font=('Arial', 12),
            bg='lightblue'
        ).pack(expand=True)

        self.window_tracker.track_window(window1, "Analysis1")

        # Window 2
        window2 = tk.Toplevel(self.root)
        window2.title("Analysis Window 2")
        window2.geometry("300x200+400+200")
        window2.configure(bg='lightgreen')

        tk.Label(
            window2,
            text="This window also\nexcluded from capture",
            font=('Arial', 12),
            bg='lightgreen'
        ).pack(expand=True)

        self.window_tracker.track_window(window2, "Analysis2")

        self.status_var.set("Test windows created - they'll be excluded from capture")

    def _start_analysis(self):
        """Start virtual buffer analysis."""
        self.is_analyzing = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        self.analyzer_thread = threading.Thread(target=self._analysis_loop)
        self.analyzer_thread.daemon = True
        self.analyzer_thread.start()

        self.status_var.set("Analyzing with virtual buffer - windows excluded!")

    def _analysis_loop(self):
        """Main analysis loop using virtual buffer."""
        while self.is_analyzing:
            try:
                # Update excluded regions based on current window positions
                self.virtual_buffer.clear_excluded_regions()

                window_bounds = self.window_tracker.update_all_bounds()
                for label, bounds in window_bounds:
                    self.virtual_buffer.add_excluded_region(*bounds, label)

                # Also exclude our main window
                if self.root.winfo_exists():
                    x = self.root.winfo_rootx()
                    y = self.root.winfo_rooty()
                    w = self.root.winfo_width()
                    h = self.root.winfo_height()
                    self.virtual_buffer.add_excluded_region(x, y, x + w, y + h, "MainWindow")

                # Capture with exclusions
                clean_capture = self.virtual_buffer.capture_with_exclusions()

                if clean_capture is not None:
                    # Update preview
                    self.root.after(0, lambda: self._update_preview(clean_capture))

                time.sleep(0.1)  # 10 FPS

            except Exception as e:
                logger.error(f"Analysis error: {e}")
                time.sleep(0.5)

    def _update_preview(self, image: np.ndarray):
        """Update preview canvas."""
        try:
            # Get canvas size
            canvas_w = self.preview_canvas.winfo_width()
            canvas_h = self.preview_canvas.winfo_height()

            if canvas_w > 1 and canvas_h > 1:
                # Resize to fit
                h, w = image.shape[:2]
                scale = min(canvas_w / w, canvas_h / h) * 0.9

                new_w = int(w * scale)
                new_h = int(h * scale)

                resized = cv2.resize(image, (new_w, new_h))

                # Draw exclusion regions on preview
                for region in self.virtual_buffer.excluded_regions:
                    x1, y1, x2, y2 = region['bounds']
                    # Scale coordinates
                    x1 = int(x1 * scale)
                    y1 = int(y1 * scale)
                    x2 = int(x2 * scale)
                    y2 = int(y2 * scale)

                    # Draw rectangle
                    cv2.rectangle(resized, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    if region['label']:
                        cv2.putText(resized, region['label'], (x1, y1 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

                # Convert to PhotoImage
                pil_image = Image.fromarray(resized)
                photo = ImageTk.PhotoImage(pil_image)

                # Update canvas
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
            logger.error(f"Error updating preview: {e}")

    def _stop_analysis(self):
        """Stop analysis."""
        self.is_analyzing = False

        if self.analyzer_thread:
            self.analyzer_thread.join(timeout=1.0)

        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

        self.status_var.set("Analysis stopped")

    def run(self):
        """Run the app."""
        self.root.mainloop()


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("VIRTUAL SCREEN BUFFER SOLUTION")
    print("=" * 70)
    print("This creates a virtual screen buffer that excludes windows")
    print("All windows stay visible while capturing clean content!")
    print("=" * 70 + "\n")

    app = VirtualBufferTestApp()
    app.run()


if __name__ == "__main__":
    main()