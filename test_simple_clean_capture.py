#!/usr/bin/env python3
"""
Multi-monitor capture solution for clean analysis.

This allows you to:
1. Keep analysis windows visible on one monitor
2. Capture clean screenshots from another monitor
3. No window hiding needed!
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import cv2
import time
import threading
from PIL import Image, ImageGrab, ImageTk
import logging
from screeninfo import get_monitors
from typing import Optional, Tuple, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MonitorSelector:
    """Helper to select which monitor to capture."""

    @staticmethod
    def get_monitors_info():
        """Get information about all monitors."""
        monitors = []
        try:
            for i, m in enumerate(get_monitors()):
                monitors.append({
                    'index': i,
                    'name': m.name,
                    'x': m.x,
                    'y': m.y,
                    'width': m.width,
                    'height': m.height,
                    'primary': m.is_primary
                })
        except Exception as e:
            logger.error(f"Error getting monitors: {e}")
            # Fallback - at least primary monitor
            monitors.append({
                'index': 0,
                'name': 'Primary',
                'x': 0,
                'y': 0,
                'width': 1920,
                'height': 1080,
                'primary': True
            })
        return monitors

    @staticmethod
    def get_monitor_bounds(monitor_index: int) -> Tuple[int, int, int, int]:
        """Get bounds for specific monitor."""
        monitors = MonitorSelector.get_monitors_info()
        if 0 <= monitor_index < len(monitors):
            m = monitors[monitor_index]
            return (m['x'], m['y'], m['x'] + m['width'], m['y'] + m['height'])
        return None


class MultiMonitorAnalyzer:
    """Analyzer that captures from specific monitor."""

    def __init__(self):
        self.capture_monitor = 0  # Which monitor to capture
        self.roi = None  # ROI within the monitor
        self.is_running = False
        self.thread = None

    def set_capture_monitor(self, monitor_index: int):
        """Set which monitor to capture from."""
        self.capture_monitor = monitor_index
        logger.info(f"Set capture monitor to: {monitor_index}")

    def set_roi(self, x1, y1, x2, y2):
        """Set ROI within the monitor."""
        self.roi = (x1, y1, x2, y2)
        logger.info(f"ROI set to: {self.roi}")

    def start(self, on_update=None):
        """Start analysis."""
        self.is_running = True
        self.on_update = on_update

        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop analysis."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _capture_loop(self):
        """Main capture loop."""
        update_count = 0

        while self.is_running:
            try:
                # Get monitor bounds
                monitor_bounds = MonitorSelector.get_monitor_bounds(self.capture_monitor)
                if not monitor_bounds:
                    logger.error("Invalid monitor")
                    break

                # Calculate actual capture area
                if self.roi:
                    # ROI is relative to monitor
                    x1 = monitor_bounds[0] + self.roi[0]
                    y1 = monitor_bounds[1] + self.roi[1]
                    x2 = monitor_bounds[0] + self.roi[2]
                    y2 = monitor_bounds[1] + self.roi[3]
                    capture_bounds = (x1, y1, x2, y2)
                else:
                    # Capture entire monitor
                    capture_bounds = monitor_bounds

                # Capture
                screenshot = ImageGrab.grab(bbox=capture_bounds, all_screens=True)

                if screenshot:
                    image = np.array(screenshot)

                    # Simple analysis
                    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                    score = np.std(gray) / 128.0  # Simple quality metric

                    update_count += 1

                    if self.on_update:
                        self.on_update(image, score, update_count)

                time.sleep(0.1)  # 10 FPS

            except Exception as e:
                logger.error(f"Capture error: {e}")
                time.sleep(0.5)


class MultiMonitorTestApp:
    """Test app for multi-monitor capture."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Monitor Clean Capture")
        self.root.geometry("800x600")

        self.analyzer = MultiMonitorAnalyzer()
        self.result_windows = []

        self._create_ui()

    def _create_ui(self):
        """Create UI."""
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="🖥️ Multi-Monitor Clean Capture",
            font=('Arial', 20, 'bold'),
            bg='#2c3e50',
            fg='white'
        ).pack(expand=True)

        # Monitor info
        info_frame = tk.LabelFrame(
            self.root,
            text="Monitor Configuration",
            font=('Arial', 12, 'bold')
        )
        info_frame.pack(fill='x', padx=10, pady=10)

        # Get monitors
        monitors = MonitorSelector.get_monitors_info()

        # Display monitor info
        for i, monitor in enumerate(monitors):
            monitor_text = (
                f"Monitor {i}: {monitor['name']} "
                f"({monitor['width']}x{monitor['height']}) "
                f"at ({monitor['x']}, {monitor['y']})"
            )
            if monitor['primary']:
                monitor_text += " [PRIMARY]"

            tk.Label(
                info_frame,
                text=monitor_text,
                font=('Consolas', 10)
            ).pack(anchor='w', padx=20, pady=2)

        # Monitor selection
        select_frame = tk.LabelFrame(
            self.root,
            text="Select Capture Monitor",
            font=('Arial', 12, 'bold')
        )
        select_frame.pack(fill='x', padx=10, pady=10)

        self.monitor_var = tk.IntVar(value=0)

        for i, monitor in enumerate(monitors):
            tk.Radiobutton(
                select_frame,
                text=f"Monitor {i} ({monitor['width']}x{monitor['height']})",
                variable=self.monitor_var,
                value=i,
                command=self._on_monitor_change
            ).pack(anchor='w', padx=20)

        # Instructions
        inst_frame = tk.LabelFrame(
            self.root,
            text="Instructions",
            font=('Arial', 12, 'bold')
        )
        inst_frame.pack(fill='x', padx=10, pady=10)

        instructions = """
1. Move this window and result windows to your secondary monitor
2. Select which monitor has your camera UI (usually Monitor 0)
3. Click 'Start Capture' to begin analysis
4. The selected monitor will be captured WITHOUT any windows on other monitors!

This way you can see all results while capturing clean screenshots.
        """

        tk.Label(
            inst_frame,
            text=instructions.strip(),
            justify='left',
            font=('Arial', 10)
        ).pack(padx=20, pady=10)

        # Controls
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=20)

        self.start_btn = tk.Button(
            control_frame,
            text="▶️ Start Capture",
            command=self._start_capture,
            bg='#27ae60',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10
        )
        self.start_btn.pack(side='left', padx=10)

        self.stop_btn = tk.Button(
            control_frame,
            text="⏹️ Stop",
            command=self._stop_capture,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=10)

        tk.Button(
            control_frame,
            text="📊 Show Results",
            command=self._create_result_windows,
            bg='#3498db',
            fg='white',
            font=('Arial', 12),
            padx=20,
            pady=10
        ).pack(side='left', padx=10)

        # Status
        self.status_var = tk.StringVar(value="Ready - Move windows to secondary monitor")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=('Arial', 12),
            fg='#2c3e50'
        ).pack(pady=10)

    def _on_monitor_change(self):
        """Handle monitor selection change."""
        monitor = self.monitor_var.get()
        self.analyzer.set_capture_monitor(monitor)
        self.status_var.set(f"Selected Monitor {monitor} for capture")

    def _create_result_windows(self):
        """Create result windows on current monitor."""
        # Create windows that will show results
        # These can be on a different monitor than the capture monitor

        # Live view window
        live_window = tk.Toplevel(self.root)
        live_window.title("Live Capture View")
        live_window.geometry("400x300+850+50")

        live_canvas = tk.Canvas(live_window, bg='black')
        live_canvas.pack(fill='both', expand=True)

        self.live_canvas = live_canvas
        self.live_image_item = None

        # Stats window
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Analysis Stats")
        stats_window.geometry("400x200+850+400")

        self.stats_text = tk.Text(stats_window, bg='#1e1e1e', fg='#00ff00')
        self.stats_text.pack(fill='both', expand=True)

        self.result_windows.extend([live_window, stats_window])

        self.status_var.set("Result windows created - place on secondary monitor")

    def _start_capture(self):
        """Start capture from selected monitor."""
        # Update UI
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        # Start analyzer
        self.analyzer.start(on_update=self._on_update)

        monitor = self.monitor_var.get()
        self.status_var.set(f"Capturing from Monitor {monitor} - NO windows interfering!")

    def _on_update(self, image, score, count):
        """Handle capture updates."""
        # Update live view if available
        if hasattr(self, 'live_canvas'):
            try:
                # Resize for display
                h, w = image.shape[:2]
                scale = min(380 / w, 280 / h)
                new_w = int(w * scale)
                new_h = int(h * scale)

                resized = cv2.resize(image, (new_w, new_h))

                # Convert to PhotoImage
                pil_image = Image.fromarray(resized)
                photo = ImageTk.PhotoImage(pil_image)

                # Update canvas
                if self.live_image_item is None:
                    self.live_image_item = self.live_canvas.create_image(
                        200, 150, image=photo, anchor='center'
                    )
                else:
                    self.live_canvas.itemconfig(self.live_image_item, image=photo)

                self.live_canvas.image = photo

            except Exception as e:
                logger.error(f"Error updating live view: {e}")

        # Update stats
        if hasattr(self, 'stats_text'):
            if count % 5 == 0:  # Update every 5 frames
                stats = f"[{time.strftime('%H:%M:%S')}] "
                stats += f"Frame #{count} - Score: {score:.3f}\n"
                self.stats_text.insert('end', stats)
                self.stats_text.see('end')

                # Limit lines
                lines = int(self.stats_text.index('end-1c').split('.')[0])
                if lines > 50:
                    self.stats_text.delete('1.0', '2.0')

        # Update status
        if count % 10 == 0:
            self.status_var.set(f"Capturing Monitor {self.monitor_var.get()} - Frame #{count}")

    def _stop_capture(self):
        """Stop capture."""
        self.analyzer.stop()

        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

        self.status_var.set("Capture stopped")

    def run(self):
        """Run the app."""
        # Set initial monitor
        self._on_monitor_change()

        self.root.mainloop()


# Alternative: Virtual Desktop Capture (Windows 10/11)
class VirtualDesktopCapture:
    """
    Alternative approach using Windows Virtual Desktops.

    Put camera UI on one virtual desktop, analysis windows on another.
    Switch between them or use Windows 11's snap layouts.
    """

    @staticmethod
    def capture_specific_window_content(window_title):
        """
        Capture content of a specific window by title.
        This could capture just the camera UI window.
        """
        # This would require win32gui to find and capture specific window
        # Left as example of alternative approach
        pass


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("MULTI-MONITOR CLEAN CAPTURE SOLUTION")
    print("=" * 70)
    print("This solution allows you to:")
    print("1. Keep analysis windows visible on one monitor")
    print("2. Capture clean screenshots from another monitor")
    print("3. No window hiding needed - see results while capturing!")
    print("=" * 70)
    print("\nRequires: pip install screeninfo pillow opencv-python")
    print("=" * 70 + "\n")

    app = MultiMonitorTestApp()
    app.run()


if __name__ == "__main__":
    main()