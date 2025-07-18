# truly_static_test.py - Windows stay completely static, only content updates

"""
TRULY STATIC VERSION - Windows never reload, only text and image content updates.
This version creates windows ONCE and then only updates StringVar and canvas images.
"""

import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab, Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional, Tuple, List, Callable
import threading
import time
from collections import deque
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# TRULY STATIC Quality Overlay - Window Created ONCE
# =============================================================================

class TrulyStaticQualityOverlay:
    """TRULY STATIC Quality Overlay - window created once, only canvas image updates."""

    def __init__(self, parent, x, y, width, height):
        """Create window ONCE - never recreate, only update content."""
        self.parent = parent
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Create window ONCE and NEVER touch it again except content
        self._create_static_window()

        # Data that updates
        self.current_quality_map = None
        self.photo = None
        self.canvas_image_item = None  # Track the canvas image item
        self.update_counter = 0

        logger.info(f"TrulyStaticQualityOverlay window created ONCE at ({x}, {y})")

    def _create_static_window(self):
        """Create the window structure ONCE - never called again."""
        # Create window ONCE
        self.window = tk.Toplevel(self.parent)
        self.window.title("🎨 Static Quality Map")

        # Set size and position ONCE
        window_width = min(450, max(300, self.width))
        window_height = min(350, max(250, self.height))
        self.window.geometry(f"{window_width}x{window_height}+{self.x + 50}+{self.y + 50}")
        self.window.attributes('-topmost', True)

        # Prevent window from being destroyed
        self.window.protocol("WM_DELETE_WINDOW", lambda: self.window.withdraw())

        # Create ALL UI elements ONCE
        # Header (NEVER changes)
        header_frame = tk.Frame(self.window, bg='darkblue', height=30)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="🎨 Quality Map - Static Window",
            bg='darkblue',
            fg='white',
            font=('Arial', 11, 'bold')
        ).pack(side='left', padx=5, pady=5)

        # Quality info (ONLY text content changes via StringVar)
        self.quality_info_var = tk.StringVar(value="Initializing...")
        tk.Label(
            header_frame,
            textvariable=self.quality_info_var,  # ONLY this variable updates
            bg='darkblue',
            fg='yellow',
            font=('Arial', 9, 'bold')
        ).pack(side='right', padx=5, pady=5)

        # Canvas container (NEVER changes structure)
        canvas_frame = tk.Frame(self.window, bg='black', relief='sunken', bd=2)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Canvas (ONLY image content changes)
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)

        # Status bar (NEVER changes structure)
        status_frame = tk.Frame(self.window, bg='gray20', height=25)
        status_frame.pack(fill='x')
        status_frame.pack_propagate(False)

        # Status text (ONLY content changes via StringVar)
        self.status_var = tk.StringVar(value="Window created - waiting for quality data...")
        tk.Label(
            status_frame,
            textvariable=self.status_var,  # ONLY this variable updates
            bg='gray20',
            fg='lightgreen',
            font=('Arial', 8)
        ).pack(side='left', padx=5, pady=2)

        # Update counter (ONLY content changes via StringVar)
        self.update_count_var = tk.StringVar(value="Updates: 0")
        tk.Label(
            status_frame,
            textvariable=self.update_count_var,  # ONLY this variable updates
            bg='gray20',
            fg='lightblue',
            font=('Arial', 8)
        ).pack(side='right', padx=5, pady=2)

        logger.info("Static quality overlay window structure created ONCE")

    def update_quality_map(self, quality_map):
        """Update ONLY the canvas image and text variables - NO window changes."""
        try:
            self.current_quality_map = quality_map
            self.update_counter += 1

            # Get canvas size (should be stable after first time)
            self.canvas.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not ready yet
                self.status_var.set("Canvas initializing...")
                return

            # Convert quality map to image
            colorized = self._quality_map_to_image(quality_map)
            colorized_resized = colorized.resize((canvas_width, canvas_height), Image.Resampling.NEAREST)

            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(colorized_resized)

            # Update canvas image (EFFICIENT - only image data changes)
            if self.canvas_image_item is None:
                # First time - create the image item
                self.canvas_image_item = self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
                logger.info("Canvas image item created ONCE")
            else:
                # All subsequent times - just update the image data
                self.canvas.itemconfig(self.canvas_image_item, image=self.photo)

            # Update ONLY the text variables (EFFICIENT - no layout changes)
            avg_quality = np.mean(quality_map)
            min_quality = np.min(quality_map)
            max_quality = np.max(quality_map)

            self.quality_info_var.set(f"Avg: {avg_quality:.3f}")
            self.status_var.set(f"Min: {min_quality:.3f}, Max: {max_quality:.3f}, Shape: {quality_map.shape}")
            self.update_count_var.set(f"Updates: {self.update_counter}")

            logger.debug(f"Quality map updated #{self.update_counter} - ONLY content changed")

        except Exception as e:
            logger.error(f"Error updating quality map content: {e}")
            self.status_var.set(f"Error: {str(e)[:50]}...")

    def _quality_map_to_image(self, quality_map):
        """Convert quality map to colorized image."""
        try:
            normalized = (quality_map * 255).astype(np.uint8)
            height, width = normalized.shape
            colored = np.zeros((height, width, 3), dtype=np.uint8)

            # Rainbow color mapping for better visualization
            for i in range(height):
                for j in range(width):
                    value = normalized[i, j]
                    if value < 85:  # Blue to Cyan
                        colored[i, j] = [0, value * 3, 255]
                    elif value < 170:  # Cyan to Yellow
                        colored[i, j] = [(value - 85) * 3, 255, 255 - (value - 85) * 3]
                    else:  # Yellow to Red
                        colored[i, j] = [255, 255 - (value - 170) * 3, 0]

            return Image.fromarray(colored)
        except Exception as e:
            logger.error(f"Error creating quality image: {e}")
            # Simple fallback
            return Image.new('RGB', (100, 100), (64, 128, 64))

    def hide(self):
        """Hide window without destroying it."""
        if self.window:
            self.window.withdraw()

    def show(self):
        """Show window without recreating it."""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.attributes('-topmost', True)

    def close(self):
        """Destroy window when truly done."""
        try:
            if self.window:
                self.window.destroy()
                self.window = None
            logger.info("Static quality overlay window destroyed")
        except Exception as e:
            logger.error(f"Error destroying quality overlay: {e}")


# =============================================================================
# TRULY STATIC Stats Window - Window Created ONCE
# =============================================================================

class TrulyStaticStatsWindow:
    """TRULY STATIC Stats Window - created once, only data updates."""

    def __init__(self, parent, live_mode):
        """Create window ONCE - never recreate."""
        self.parent = parent
        self.live_mode = live_mode

        # Data storage
        self.timestamps = []
        self.scores = []
        self.max_points = 100
        self.start_time = time.time()
        self.graph_update_counter = 0

        # Create window structure ONCE
        self._create_static_window()

        logger.info("TrulyStaticStatsWindow created ONCE")

    def _create_static_window(self):
        """Create ALL window elements ONCE - never called again."""
        # Create window ONCE
        self.window = tk.Toplevel(self.parent)
        self.window.title("📊 Static Statistics Dashboard")
        self.window.geometry("650x550+200+200")
        self.window.attributes('-topmost', True)

        # Prevent accidental destruction
        self.window.protocol("WM_DELETE_WINDOW", lambda: self.window.withdraw())

        # Header (NEVER changes)
        header_frame = tk.Frame(self.window, bg='navy', height=40)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="📊 Static Dashboard - Window Created Once",
            bg='navy',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack(side='left', padx=10, pady=8)

        # Main content (NEVER changes structure)
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Statistics display (ONLY text content changes via StringVar)
        stats_frame = tk.LabelFrame(main_frame, text="📈 Live Statistics", font=('Arial', 10, 'bold'))
        stats_frame.pack(fill='x', pady=(0, 5))

        stats_grid = tk.Frame(stats_frame)
        stats_grid.pack(fill='x', padx=10, pady=5)

        # Create ALL labels ONCE - only StringVar content changes
        tk.Label(stats_grid, text="Current Score:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky='w', padx=5)
        self.current_score_var = tk.StringVar(value="0.000")
        tk.Label(stats_grid, textvariable=self.current_score_var, font=('Arial', 9, 'bold'), fg='blue').grid(row=0,
                                                                                                             column=1,
                                                                                                             sticky='w',
                                                                                                             padx=5)

        tk.Label(stats_grid, text="Average Score:", font=('Arial', 9, 'bold')).grid(row=0, column=2, sticky='w',
                                                                                    padx=15)
        self.avg_score_var = tk.StringVar(value="0.000")
        tk.Label(stats_grid, textvariable=self.avg_score_var, font=('Arial', 9, 'bold'), fg='green').grid(row=0,
                                                                                                          column=3,
                                                                                                          sticky='w',
                                                                                                          padx=5)

        tk.Label(stats_grid, text="Analysis Count:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky='w',
                                                                                     padx=5)
        self.count_var = tk.StringVar(value="0")
        tk.Label(stats_grid, textvariable=self.count_var, font=('Arial', 9, 'bold'), fg='purple').grid(row=1, column=1,
                                                                                                       sticky='w',
                                                                                                       padx=5)

        tk.Label(stats_grid, text="Runtime:", font=('Arial', 9, 'bold')).grid(row=1, column=2, sticky='w', padx=15)
        self.runtime_var = tk.StringVar(value="00:00")
        tk.Label(stats_grid, textvariable=self.runtime_var, font=('Arial', 9, 'bold'), fg='orange').grid(row=1,
                                                                                                         column=3,
                                                                                                         sticky='w',
                                                                                                         padx=5)

        # Control panel (NEVER changes structure)
        control_frame = tk.LabelFrame(main_frame, text="🎛️ Controls", font=('Arial', 10, 'bold'))
        control_frame.pack(fill='x', pady=(0, 5))

        controls_grid = tk.Frame(control_frame)
        controls_grid.pack(fill='x', padx=10, pady=5)

        # Create ALL buttons ONCE
        tk.Button(controls_grid, text="⏸️ Pause", command=self._pause_analysis, font=('Arial', 9)).grid(row=0, column=0,
                                                                                                        padx=2,
                                                                                                        sticky='ew')
        tk.Button(controls_grid, text="▶️ Resume", command=self._resume_analysis, font=('Arial', 9)).grid(row=0,
                                                                                                          column=1,
                                                                                                          padx=2,
                                                                                                          sticky='ew')
        tk.Button(controls_grid, text="⏹️ Stop", command=self._stop_analysis, font=('Arial', 9)).grid(row=0, column=2,
                                                                                                      padx=2,
                                                                                                      sticky='ew')

        tk.Label(controls_grid, text="ROI Frequency:", font=('Arial', 9, 'bold')).grid(row=0, column=3, padx=(15, 5),
                                                                                       sticky='w')

        self.freq_var = tk.StringVar(value="1000ms")
        freq_values = ["100ms", "250ms", "500ms", "1000ms", "2000ms", "5000ms"]
        freq_combo = ttk.Combobox(controls_grid, textvariable=self.freq_var, values=freq_values, width=8,
                                  font=('Arial', 9))
        freq_combo.grid(row=0, column=4, padx=5, sticky='ew')
        freq_combo.bind('<<ComboboxSelected>>', self._on_frequency_change)

        # Configure grid weights
        for i in range(5):
            controls_grid.grid_columnconfigure(i, weight=1 if i < 3 else 0)

        # Graph frame (CREATED ONCE)
        graph_frame = tk.LabelFrame(main_frame, text="📈 Quality History", font=('Arial', 10, 'bold'))
        graph_frame.pack(fill='both', expand=True, pady=(0, 5))

        # Create matplotlib figure ONCE
        self.fig, self.ax = plt.subplots(figsize=(8, 4), facecolor='white')
        self.ax.set_title('Real-time Quality - Static Window', fontsize=11, fontweight='bold')
        self.ax.set_xlabel('Time (seconds)', fontsize=9)
        self.ax.set_ylabel('Quality Score', fontsize=9)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(0, 1)
        self.ax.set_xlim(0, 10)

        # Create line plot ONCE - only data updates
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='Quality Score', marker='o', markersize=3)
        self.ax.legend(loc='upper right', fontsize=9)

        # Embed plot ONCE
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)

        # Status bar (ONLY text content changes via StringVar)
        status_frame = tk.Frame(self.window, bg='gray20', height=25)
        status_frame.pack(fill='x')
        status_frame.pack_propagate(False)

        self.status_var = tk.StringVar(value="Static window ready - waiting for data...")
        tk.Label(
            status_frame,
            textvariable=self.status_var,  # ONLY this variable updates
            bg='gray20',
            fg='lightgreen',
            font=('Arial', 8)
        ).pack(side='left', padx=5, pady=2)

        self.graph_update_var = tk.StringVar(value="Graph: 0")
        tk.Label(
            status_frame,
            textvariable=self.graph_update_var,  # ONLY this variable updates
            bg='gray20',
            fg='lightblue',
            font=('Arial', 8)
        ).pack(side='right', padx=5, pady=2)

        logger.info("Static stats window structure created ONCE")

    def update_stats(self, score, timestamp, history):
        """Update ONLY the data content - NO window structure changes."""
        try:
            # Update ONLY StringVar content (EFFICIENT)
            self.current_score_var.set(f"{score:.3f}")

            if history:
                scores = [item['score'] for item in history]
                self.avg_score_var.set(f"{np.mean(scores):.3f}")
                self.count_var.set(str(len(history)))

            # Update runtime
            runtime_seconds = int(timestamp - self.start_time)
            minutes = runtime_seconds // 60
            seconds = runtime_seconds % 60
            self.runtime_var.set(f"{minutes:02d}:{seconds:02d}")

            # Store data for graph
            relative_time = timestamp - self.start_time
            self.timestamps.append(relative_time)
            self.scores.append(score)

            # Limit data points
            if len(self.timestamps) > self.max_points:
                self.timestamps = self.timestamps[-self.max_points:]
                self.scores = self.scores[-self.max_points:]

            # Update graph every few cycles for performance
            if len(self.timestamps) % 3 == 0:
                self._update_graph_data_only()

            # Update status
            frequency = self.live_mode.update_frequency
            self.status_var.set(f"Active - ROI: {frequency}ms - Score: {score:.3f} - Points: {len(self.timestamps)}")

            logger.debug(f"Stats updated #{len(history)} - ONLY content changed")

        except Exception as e:
            logger.error(f"Error updating stats content: {e}")
            self.status_var.set(f"Update error: {str(e)[:40]}...")

    def _update_graph_data_only(self):
        """Update ONLY the graph data - no graph structure changes."""
        try:
            if len(self.timestamps) > 0 and len(self.scores) > 0:
                # Update ONLY the line data (EFFICIENT)
                self.line.set_data(self.timestamps, self.scores)

                # Update axis limits only when needed
                if len(self.timestamps) > 1:
                    max_time = max(self.timestamps)
                    self.ax.set_xlim(0, max(10, max_time + 1))

                if len(self.scores) > 1:
                    min_score = min(self.scores)
                    max_score = max(self.scores)
                    padding = max(0.05, (max_score - min_score) * 0.1)
                    self.ax.set_ylim(max(0, min_score - padding), min(1, max_score + padding))

                # Refresh canvas (EFFICIENT)
                self.canvas.draw_idle()

                self.graph_update_counter += 1
                self.graph_update_var.set(f"Graph: {self.graph_update_counter}")

        except Exception as e:
            logger.error(f"Error updating graph data: {e}")

    def _pause_analysis(self):
        if self.live_mode:
            self.live_mode.pause_analysis()
            self.status_var.set("⏸️ Analysis paused")

    def _resume_analysis(self):
        if self.live_mode:
            self.live_mode.resume_analysis()

    def _stop_analysis(self):
        if self.live_mode:
            self.live_mode.stop_live_analysis()
            self.status_var.set("⏹️ Analysis stopped")

    def _on_frequency_change(self, event=None):
        try:
            freq_str = self.freq_var.get()
            freq_ms = int(freq_str.replace('ms', ''))

            if self.live_mode:
                old_freq = self.live_mode.update_frequency
                self.live_mode.set_update_frequency(freq_ms)
                self.status_var.set(f"Frequency: {old_freq}ms → {freq_ms}ms")

        except Exception as e:
            logger.error(f"Error changing frequency: {e}")

    def show(self):
        if self.window:
            self.window.deiconify()
            self.window.lift()

    def hide(self):
        if self.window:
            self.window.withdraw()

    def close(self):
        try:
            if self.window:
                self.window.destroy()
                self.window = None
            logger.info("Static stats window destroyed")
        except Exception as e:
            logger.error(f"Error destroying stats window: {e}")


# =============================================================================
# Enhanced Live Analyze Mode - Uses Truly Static Windows
# =============================================================================

class TrulyStaticLiveAnalyzeMode:
    """Live Analysis Mode that uses truly static windows."""

    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app

        if hasattr(main_app, 'analyzer'):
            self.quality_calculator = main_app.analyzer
        else:
            self.quality_calculator = self._create_fallback_analyzer()

        # State management
        self.is_active = False
        self.is_paused = False
        self.roi_coords = []
        self.roi_bounds = None

        # ROI-specific frequency control
        self.update_frequency = 1000
        self.roi_timer_id = None

        # Screen capture
        self.original_screen_capture = None

        # Static windows (created once, never recreated)
        self.roi_selector_overlay = None
        self.quality_overlay = None
        self.stats_window = None

        # Analysis data
        self.current_quality_map = None
        self.current_score = None
        self.analysis_history = deque(maxlen=100)

        # Callbacks
        self.on_roi_selected_callback = None
        self.on_analysis_complete_callback = None

        logger.info("TrulyStaticLiveAnalyzeMode initialized")

    def _create_fallback_analyzer(self):
        """Create enhanced fallback analyzer."""

        class EnhancedAnalyzer:
            def calculate_quality_map(self, image):
                if len(image.shape) == 3:
                    gray = np.mean(image, axis=2).astype(np.uint8)
                else:
                    gray = image.astype(np.uint8)

                h, w = gray.shape

                # Enhanced patterns for visual interest
                grad_x = np.gradient(gray.astype(np.float32), axis=1)
                grad_y = np.gradient(gray.astype(np.float32), axis=0)
                gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
                base_quality = gradient_magnitude / 255.0

                # Dynamic time-based patterns
                y, x = np.ogrid[:h, :w]
                time_factor = time.time() % 15

                # Moving patterns
                wave1 = 0.1 * np.sin(x / 25 + time_factor * 0.4)
                wave2 = 0.1 * np.cos(y / 20 + time_factor * 0.3)

                # Central quality region
                center_y, center_x = h // 2, w // 2
                distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                center_boost = 0.25 * np.exp(-distance / (min(h, w) / 3))

                # Random variations
                noise = 0.03 * np.random.random((h, w))

                # Combine patterns
                quality_map = base_quality + wave1 + wave2 + center_boost + noise
                quality_map = np.clip(quality_map, 0, 1)

                overall_score = float(np.mean(quality_map))
                return quality_map, overall_score

        return EnhancedAnalyzer()

    def start_live_analysis(self, on_roi_selected=None, on_analysis_complete=None):
        """Start live analysis with static windows."""
        logger.info("Starting live analysis with TRULY STATIC windows")

        self.on_roi_selected_callback = on_roi_selected
        self.on_analysis_complete_callback = on_analysis_complete

        self.is_active = True
        self.is_paused = False

        # Capture screen
        try:
            self.original_screen_capture = self._capture_full_screen()
            logger.info("Screen captured for static windows")
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return

        # Start ROI selection
        self._start_roi_selection()

    def _capture_full_screen(self):
        try:
            self.root.update()
            time.sleep(0.1)
            screenshot = ImageGrab.grab()
            logger.info(f"Full screen captured: {screenshot.size}")
            return screenshot
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            raise

    def _start_roi_selection(self):
        """Start ROI selection (reuse from previous test)."""
        try:
            self.roi_selector_overlay = TransparentROISelector(
                self.root,
                self.original_screen_capture,
                on_roi_selected=self._on_roi_selection_complete,
                on_cancelled=self._on_roi_selection_cancelled
            )

            self.roi_selector_overlay.show()
            logger.info("ROI selector shown")

        except Exception as e:
            logger.error(f"Error starting ROI selection: {e}")
            self.stop_live_analysis()

    def _on_roi_selection_complete(self, screen_coords):
        """Handle ROI selection completion."""
        logger.info(f"ROI selection complete with {len(screen_coords)} points")

        self.roi_coords = screen_coords
        self.roi_bounds = self._calculate_roi_bounds(screen_coords)

        if self.roi_selector_overlay:
            self.roi_selector_overlay.close()
            self.roi_selector_overlay = None

        if self.on_roi_selected_callback:
            self.on_roi_selected_callback(screen_coords)

        # Create static windows ONCE
        self._create_static_windows()

        # Start analysis loop
        self._start_static_analysis_loop()

    def _on_roi_selection_cancelled(self):
        logger.info("ROI selection cancelled")
        self.stop_live_analysis()

    def _create_static_windows(self):
        """Create static windows ONCE - never called again."""
        try:
            if self.roi_bounds:
                x1, y1, x2, y2 = self.roi_bounds
                # Create quality overlay ONCE
                self.quality_overlay = TrulyStaticQualityOverlay(
                    self.root, x1, y1, x2 - x1, y2 - y1
                )

            # Create stats window ONCE
            self.stats_window = TrulyStaticStatsWindow(self.root, self)

            logger.info("Static windows created ONCE - will never be recreated")

        except Exception as e:
            logger.error(f"Error creating static windows: {e}")

    def _start_static_analysis_loop(self):
        """Start analysis loop with static windows."""
        if not self.roi_bounds:
            logger.error("No ROI bounds for analysis")
            return

        logger.info(f"Starting static analysis loop at {self.update_frequency}ms")
        self._schedule_next_roi_analysis()

    def _schedule_next_roi_analysis(self):
        """Schedule next ROI analysis."""
        if not self.is_active or self.is_paused:
            return

        try:
            self.roi_timer_id = self.root.after(
                self.update_frequency,
                self._perform_static_roi_analysis
            )
        except Exception as e:
            logger.error(f"Error scheduling analysis: {e}")

    def _perform_static_roi_analysis(self):
        """Perform ROI analysis with static window updates."""
        if not self.is_active or self.is_paused:
            return

        try:
            # Hide quality overlay during capture
            if self.quality_overlay:
                self.quality_overlay.hide()

            self.root.update()
            time.sleep(0.02)

            # Capture ROI
            x1, y1, x2, y2 = self.roi_bounds
            roi_capture = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            # Show quality overlay again
            if self.quality_overlay:
                self.quality_overlay.show()

            if roi_capture:
                # Analyze quality
                roi_array = np.array(roi_capture)
                quality_map, overall_score = self._analyze_roi_quality(roi_array)

                # Update ONLY the content of static windows
                self._update_static_displays(quality_map, overall_score)

                # Store in history
                self.analysis_history.append({
                    'timestamp': time.time(),
                    'score': overall_score,
                    'quality_map': quality_map,
                    'roi_size': roi_array.shape[:2]
                })

                # Notify callback
                if self.on_analysis_complete_callback:
                    self.on_analysis_complete_callback(quality_map, overall_score)

        except Exception as e:
            logger.error(f"Static analysis error: {e}")

        finally:
            # Ensure overlay is shown
            if self.quality_overlay:
                self.quality_overlay.show()
            # Schedule next update
            self._schedule_next_roi_analysis()

    def _analyze_roi_quality(self, roi_array):
        """Analyze ROI quality."""
        try:
            quality_map, overall_score = self.quality_calculator.calculate_quality_map(roi_array)
            self.current_quality_map = quality_map
            self.current_score = overall_score
            return quality_map, overall_score
        except Exception as e:
            logger.error(f"Error analyzing quality: {e}")
            return np.zeros(roi_array.shape[:2]), 0.0

    def _update_static_displays(self, quality_map, overall_score):
        """Update ONLY the content of static windows - NO window recreation."""
        try:
            # Update quality overlay content ONLY
            if self.quality_overlay:
                self.quality_overlay.update_quality_map(quality_map)

            # Update stats window content ONLY
            if self.stats_window:
                self.stats_window.update_stats(
                    overall_score,
                    time.time(),
                    list(self.analysis_history)
                )

            logger.debug("Static window content updated - NO windows recreated")

        except Exception as e:
            logger.error(f"Error updating static displays: {e}")

    def _calculate_roi_bounds(self, coords):
        """Calculate ROI bounds."""
        if not coords:
            return None

        x_coords = [coord[0] for coord in coords]
        y_coords = [coord[1] for coord in coords]

        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        padding = 5
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = x2 + padding
        y2 = y2 + padding

        return (x1, y1, x2, y2)

    # Control methods
    def set_update_frequency(self, frequency_ms):
        """Set ROI analysis frequency."""
        old_frequency = self.update_frequency
        self.update_frequency = max(100, frequency_ms)

        logger.info(f"ROI frequency: {old_frequency}ms -> {self.update_frequency}ms")

        if self.is_active and not self.is_paused and self.roi_timer_id:
            try:
                self.root.after_cancel(self.roi_timer_id)
                self.roi_timer_id = None
                self._schedule_next_roi_analysis()
            except Exception as e:
                logger.error(f"Error updating frequency: {e}")

    def pause_analysis(self):
        """Pause analysis."""
        if not self.is_active:
            return

        self.is_paused = True
        if self.roi_timer_id:
            try:
                self.root.after_cancel(self.roi_timer_id)
                self.roi_timer_id = None
            except:
                pass

        logger.info("Analysis paused")

    def resume_analysis(self):
        """Resume analysis."""
        if not self.is_active or not self.is_paused:
            return

        self.is_paused = False
        self._schedule_next_roi_analysis()
        logger.info("Analysis resumed")

    def stop_live_analysis(self):
        """Stop analysis and destroy static windows."""
        logger.info("Stopping static live analysis")

        self.is_active = False
        self.is_paused = False

        # Cancel timer
        if self.roi_timer_id:
            try:
                self.root.after_cancel(self.roi_timer_id)
            except:
                pass
            self.roi_timer_id = None

        # Close static windows
        try:
            if self.roi_selector_overlay:
                self.roi_selector_overlay.close()
                self.roi_selector_overlay = None

            if self.quality_overlay:
                self.quality_overlay.close()
                self.quality_overlay = None

            if self.stats_window:
                self.stats_window.close()
                self.stats_window = None
        except Exception as e:
            logger.error(f"Error closing static windows: {e}")

        # Clear data
        self.roi_coords = []
        self.roi_bounds = None
        self.current_quality_map = None
        self.current_score = None
        self.analysis_history.clear()
        self.original_screen_capture = None

        logger.info("Static live analysis stopped and cleaned up")


# Copy TransparentROISelector from previous test
class TransparentROISelector:
    """ROI selector overlay (same as previous)."""

    def __init__(self, parent_window, original_screenshot: Image.Image,
                 on_roi_selected: Optional[Callable] = None,
                 on_cancelled: Optional[Callable] = None):
        self.parent = parent_window
        self.original_screenshot = original_screenshot
        self.on_roi_selected = on_roi_selected
        self.on_cancelled = on_cancelled

        self.overlay = tk.Toplevel(parent_window)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-topmost', True)

        try:
            self.overlay.attributes('-alpha', 0.7)
        except:
            pass

        self.overlay.configure(bg='black')

        self.canvas = tk.Canvas(self.overlay, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)

        self.roi_points = []
        self.temp_lines = []
        self.preview_line = None

        self.point_radius = 5
        self.line_width = 3
        self.point_color = '#00FF00'
        self.line_color = '#00FF00'
        self.preview_color = '#FFFF00'

        self.overlay.after(200, self._initialize_overlay)
        logger.info("TransparentROISelector initialized")

    def _initialize_overlay(self):
        try:
            self._display_screenshot_background()
            self._show_instructions()
            self._bind_events()
            logger.info("ROI selector ready")
        except Exception as e:
            logger.error(f"Error initializing ROI selector: {e}")
            self.close()

    def _display_screenshot_background(self):
        try:
            self.overlay.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                self.overlay.after(100, self._display_screenshot_background)
                return

            screenshot_resized = self.original_screenshot.resize(
                (canvas_width, canvas_height), Image.Resampling.LANCZOS
            )

            self.photo = ImageTk.PhotoImage(screenshot_resized)
            self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

            self.scale_x = self.original_screenshot.width / canvas_width
            self.scale_y = self.original_screenshot.height / canvas_height

            logger.info(f"ROI selector background displayed: {canvas_width}x{canvas_height}")
        except Exception as e:
            logger.error(f"Failed to display background: {e}")

    def _show_instructions(self):
        instruction_text = (
            "STATIC WINDOW TEST - ROI Selection\n\n"
            "• Left-click to add points\n"
            "• Right-click or Enter to complete\n"
            "• Escape to cancel\n"
            "• Windows will be created ONCE\n\n"
            "Current points: 0"
        )

        self.instruction_text = self.canvas.create_text(
            50, 50, text=instruction_text, fill='white',
            font=('Arial', 12, 'bold'), anchor='nw'
        )

    def _bind_events(self):
        self.canvas.bind('<Button-1>', self._on_left_click)
        self.canvas.bind('<Button-3>', self._on_right_click)
        self.canvas.bind('<Motion>', self._on_mouse_move)
        self.overlay.bind('<Return>', self._on_enter_key)
        self.overlay.bind('<Escape>', self._on_escape_key)
        self.overlay.focus_set()
        self.overlay.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_left_click(self, event):
        x, y = event.x, event.y
        self.roi_points.append((x, y))
        self._draw_point(x, y)

        if len(self.roi_points) > 1:
            prev_x, prev_y = self.roi_points[-2]
            line_id = self.canvas.create_line(
                prev_x, prev_y, x, y, fill=self.line_color, width=self.line_width
            )
            self.temp_lines.append(line_id)

        self._update_status_text()
        logger.debug(f"ROI point added: ({x}, {y}), total: {len(self.roi_points)}")

    def _on_right_click(self, event):
        self._complete_roi_selection()

    def _on_mouse_move(self, event):
        if len(self.roi_points) == 0:
            return

        if self.preview_line:
            self.canvas.delete(self.preview_line)

        last_x, last_y = self.roi_points[-1]
        self.preview_line = self.canvas.create_line(
            last_x, last_y, event.x, event.y,
            fill=self.preview_color, width=1, dash=(5, 5)
        )

    def _on_enter_key(self, event):
        self._complete_roi_selection()

    def _on_escape_key(self, event):
        self._cancel_roi_selection()

    def _on_close(self):
        self._cancel_roi_selection()

    def _draw_point(self, x, y):
        self.canvas.create_oval(
            x - self.point_radius, y - self.point_radius,
            x + self.point_radius, y + self.point_radius,
            fill=self.point_color, outline='white', width=2
        )

    def _update_status_text(self):
        if hasattr(self, 'instruction_text'):
            status = f"Current points: {len(self.roi_points)}"
            if len(self.roi_points) >= 3:
                status += " (Ready! Right-click or Enter to complete)"
            elif len(self.roi_points) > 0:
                status += f" (Need {3 - len(self.roi_points)} more)"

            self.canvas.itemconfig(self.instruction_text, text=
            f"STATIC WINDOW TEST - ROI Selection\n\n"
            f"• Left-click to add points\n"
            f"• Right-click/Enter to complete\n"
            f"• Escape to cancel\n"
            f"• Windows created ONCE only\n\n"
            f"{status}"
                                   )

    def _complete_roi_selection(self):
        if len(self.roi_points) < 3:
            logger.warning("Not enough points")
            return

        screen_coords = self._canvas_to_screen_coords(self.roi_points)
        logger.info(f"ROI selection completed with {len(screen_coords)} points")

        if self.on_roi_selected:
            self.on_roi_selected(screen_coords)

    def _cancel_roi_selection(self):
        logger.info("ROI selection cancelled")
        if self.on_cancelled:
            self.on_cancelled()

    def _canvas_to_screen_coords(self, canvas_points):
        try:
            if not hasattr(self, 'scale_x') or not hasattr(self, 'scale_y'):
                return canvas_points

            screen_points = []
            for canvas_x, canvas_y in canvas_points:
                screen_x = int(canvas_x * self.scale_x)
                screen_y = int(canvas_y * self.scale_y)
                screen_points.append((screen_x, screen_y))

            logger.info(f"Converted {len(canvas_points)} points to screen coordinates")
            return screen_points
        except Exception as e:
            logger.error(f"Failed to convert coordinates: {e}")
            return canvas_points

    def close(self):
        try:
            if self.overlay:
                self.overlay.destroy()
                self.overlay = None
            logger.info("ROI selector closed")
        except Exception as e:
            logger.error(f"Error closing ROI selector: {e}")

    def show(self):
        if self.overlay:
            self.overlay.deiconify()
            self.overlay.lift()
            self.overlay.attributes('-topmost', True)


# =============================================================================
# Test Application - Uses Truly Static Windows
# =============================================================================

class TrulyStaticTest:
    """Test application with truly static windows that never reload."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏠 Truly Static Windows Test - No Reloading!")
        self.root.geometry("800x600")

        # Mock components
        self.create_mock_app()
        self.create_test_ui()

    def create_mock_app(self):
        """Create mock components."""

        class MockState:
            def has_image(self):
                return True

        class MockAnalyzer:
            def calculate_quality_map(self, image):
                if len(image.shape) == 3:
                    gray = np.mean(image, axis=2).astype(np.uint8)
                else:
                    gray = image.astype(np.uint8)

                h, w = gray.shape

                # Enhanced quality patterns
                grad_x = np.gradient(gray.astype(np.float32), axis=1)
                grad_y = np.gradient(gray.astype(np.float32), axis=0)
                gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
                base_quality = gradient_magnitude / 255.0

                # Dynamic time-based patterns for visual testing
                y, x = np.ogrid[:h, :w]
                time_factor = time.time() % 20

                # Moving patterns
                wave1 = 0.15 * np.sin(x / 30 + time_factor * 0.5)
                wave2 = 0.15 * np.cos(y / 25 + time_factor * 0.3)

                # Central quality boost
                center_y, center_x = h // 2, w // 2
                distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                center_boost = 0.3 * np.exp(-distance / (min(h, w) / 3))

                # Random variations
                noise = 0.05 * np.random.random((h, w))

                # Combine patterns
                quality_map = base_quality + wave1 + wave2 + center_boost + noise
                quality_map = np.clip(quality_map, 0, 1)

                overall_score = float(np.mean(quality_map))
                return quality_map, overall_score

        self.state = MockState()
        self.analyzer = MockAnalyzer()
        self.live_mode = None

    def create_test_ui(self):
        """Create test UI."""
        # Title
        title_label = tk.Label(
            self.root,
            text="🏠 TRULY STATIC WINDOWS TEST",
            font=('Arial', 18, 'bold'),
            fg='darkgreen'
        )
        title_label.pack(pady=15)

        # Description
        desc_label = tk.Label(
            self.root,
            text="Windows created ONCE - Only text and image content updates",
            font=('Arial', 12, 'italic'),
            fg='blue'
        )
        desc_label.pack(pady=5)

        # Instructions
        instructions = tk.Text(self.root, height=12, width=90, wrap=tk.WORD)
        instructions.pack(pady=10, padx=20, fill='both', expand=True)

        instructions.insert(tk.END,
                            "🏠 TRULY STATIC WINDOWS TEST - No Window Reloading!\n\n"
                            "This version creates windows ONCE and NEVER recreates them.\n"
                            "Only the content (text variables and canvas images) updates.\n\n"
                            "What you'll see:\n"
                            "✅ Quality Map Window: Created once, only image updates\n"
                            "✅ Statistics Window: Created once, only text and graph data updates\n"
                            "✅ No window flickering, repositioning, or reloading\n"
                            "✅ Smooth, efficient updates at selected frequency\n\n"
                            "Test Process:\n"
                            "1. Click 'Start Static Test' below\n"
                            "2. Select ROI on transparent overlay\n"
                            "3. Windows appear ONCE and stay put\n"
                            "4. Only content updates - no window recreation\n"
                            "5. Change frequency - see smooth updates\n"
                            "6. Use pause/resume controls\n\n"
                            "Key Improvements:\n"
                            "• Windows created using _create_static_window() called ONCE\n"
                            "• Content updates via StringVar.set() and canvas.itemconfig()\n"
                            "• No window.geometry(), .pack(), or structural changes during updates\n"
                            "• Efficient matplotlib graph updates with line.set_data()\n"
                            "• Canvas image updates with canvas.itemconfig(image_id, image=new_photo)\n\n"
                            "Expected Result: Smooth, flicker-free operation!"
                            )
        instructions.configure(state=tk.DISABLED)

        # Control frame
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=15)

        # Test frequency
        freq_frame = tk.Frame(control_frame)
        freq_frame.pack(pady=5)

        tk.Label(freq_frame, text="Test Frequency:", font=('Arial', 10, 'bold')).pack(side='left')

        self.test_freq_var = tk.StringVar(value="250ms")
        freq_values = ["100ms", "250ms", "500ms", "1000ms", "2000ms"]
        freq_combo = ttk.Combobox(freq_frame, textvariable=self.test_freq_var, values=freq_values, width=8)
        freq_combo.pack(side='left', padx=10)

        # Test buttons
        button_frame = tk.Frame(control_frame)
        button_frame.pack(pady=10)

        self.test_button = tk.Button(
            button_frame,
            text="🏠 Start Static Test",
            command=self.start_static_test,
            bg='#228B22',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=25,
            pady=8
        )
        self.test_button.pack(side='left', padx=10)

        self.stop_button = tk.Button(
            button_frame,
            text="⏹️ Stop Test",
            command=self.stop_test,
            bg='#DC143C',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=25,
            pady=8,
            state='disabled'
        )
        self.stop_button.pack(side='left', padx=10)

        # Status
        self.status_var = tk.StringVar(value="Ready for static window test - No reloading, only content updates!")
        status_label = tk.Label(self.root, textvariable=self.status_var, font=('Arial', 11), fg='darkblue')
        status_label.pack(pady=5)

        # Results
        results_frame = tk.LabelFrame(self.root, text="Test Progress", font=('Arial', 10, 'bold'))
        results_frame.pack(fill='x', pady=10, padx=20)

        self.results_text = tk.Text(results_frame, height=8, width=90)
        results_scrollbar = tk.Scrollbar(results_frame, orient='vertical', command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)

        self.results_text.pack(side='left', fill='both', expand=True)
        results_scrollbar.pack(side='right', fill='y')

        self.results_text.insert(tk.END, "🏠 Static Windows Test Ready\n")
        self.results_text.insert(tk.END, "Expected: Windows created once, only content updates\n")
        self.results_text.insert(tk.END, "No window reloading, repositioning, or flickering\n\n")

    def start_static_test(self):
        """Start the truly static test."""
        try:
            # Use the truly static live mode
            self.live_mode = TrulyStaticLiveAnalyzeMode(self.root, self)

            # Set test frequency
            freq_str = self.test_freq_var.get()
            freq_ms = int(freq_str.replace('ms', ''))
            self.live_mode.set_update_frequency(freq_ms)

            # Update buttons
            self.test_button.config(state='disabled')
            self.stop_button.config(state='normal')

            # Start static analysis
            self.live_mode.start_live_analysis(
                on_roi_selected=self.on_roi_selected,
                on_analysis_complete=self.on_analysis_complete
            )

            self.status_var.set("Static test started - windows will be created ONCE")
            self.log_result("🏠 Truly static test started")
            self.log_result("✅ Screen captured")
            self.log_result("✅ ROI selector should appear")
            self.log_result(f"⚡ Test frequency: {freq_ms}ms")
            self.log_result("📍 Select ROI - windows will be created ONCE")

        except Exception as e:
            self.log_result(f"❌ Static test failed: {e}")
            self.status_var.set(f"Test failed: {str(e)}")
            self.test_button.config(state='normal')
            self.stop_button.config(state='disabled')

    def stop_test(self):
        """Stop the static test."""
        try:
            if self.live_mode:
                self.live_mode.stop_live_analysis()
                self.live_mode = None

            self.test_button.config(state='normal')
            self.stop_button.config(state='disabled')

            self.status_var.set("Static test stopped - windows destroyed")
            self.log_result("✅ Static test stopped - windows properly destroyed")

        except Exception as e:
            self.log_result(f"❌ Stop error: {e}")

    def on_roi_selected(self, roi_coords):
        """Handle ROI selection."""
        self.status_var.set(f"ROI selected - static windows should appear ONCE")
        self.log_result(f"✅ ROI selected with {len(roi_coords)} points")
        self.log_result("🏠 Static windows created ONCE")
        self.log_result("📊 Quality map window: static structure, content updates only")
        self.log_result("📈 Stats window: static structure, text/graph updates only")
        self.log_result("🔄 Analysis loop starting...")

        self.update_count = 0
        self.last_log_time = time.time()

    def on_analysis_complete(self, quality_map, overall_score):
        """Handle analysis completion."""
        self.status_var.set(f"Static windows active - Score: {overall_score:.3f} - Only content updating!")

        self.update_count += 1
        current_time = time.time()

        # Log every few seconds
        if current_time - self.last_log_time >= 4:
            self.log_result(f"🔄 Content update #{self.update_count} - Score: {overall_score:.3f}")
            self.log_result(f"   ✅ Quality map: image updated, window static")
            self.log_result(f"   ✅ Stats: text/graph updated, window static")
            self.log_result(f"   ⚡ Frequency: {self.live_mode.update_frequency}ms")
            self.last_log_time = current_time

    def log_result(self, message):
        """Log test results."""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.results_text.insert(tk.END, formatted_message)
        self.results_text.see(tk.END)
        print(formatted_message.strip())

    def run(self):
        """Run the static test."""
        print("=" * 70)
        print("🏠 TRULY STATIC WINDOWS TEST")
        print("=" * 70)
        print("Testing: Windows created ONCE, only content updates")
        print("Expected: No window reloading, repositioning, or flickering")
        print("=" * 70)
        self.root.mainloop()


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    try:
        import matplotlib

        matplotlib.use('TkAgg')

        print("Starting TRULY STATIC Windows Test...")
        print("Windows will be created ONCE and never reloaded!")
        test_app = TrulyStaticTest()
        test_app.run()

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install: pip install matplotlib")

    except Exception as e:
        print(f"Test failed: {e}")
        print("Ensure tkinter, PIL, numpy, and matplotlib are installed.")