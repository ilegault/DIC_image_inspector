# ui/live_analyze/live_analyze_mode.py - Optimized Implementation

import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab, Image, ImageTk
import numpy as np
from typing import Optional, Tuple, List, Callable
import threading
import time
from collections import deque
import logging
import cv2
import hashlib

from ui.live_analyze.transparent_roi_selector import TransparentROISelector
from ui.live_analyze.quality_overlay import QualityOverlay
from ui.live_analyze.stats_window import StatsWindow

logger = logging.getLogger(__name__)


class LiveAnalyzeMode:
    """
    Optimized Live Analysis Mode for real-time DIC quality assessment.

    Key optimizations:
    - Grid-based quality map calculation for visualization
    - Accurate quality scores using full DIC parameters
    - Smart caching for identical frames
    - Performance monitoring and auto-adjustment
    - Efficient display updates
    """

    def __init__(self, root, main_app):
        """Initialize Live Analyze Mode with optimizations."""
        self.root = root
        self.main_app = main_app

        # Get quality calculator
        if hasattr(main_app, 'analyzer') and hasattr(main_app.analyzer, 'quality_calculator'):
            self.quality_calculator = main_app.analyzer.quality_calculator
        elif hasattr(main_app, 'analyzer'):
            self.quality_calculator = main_app.analyzer
        else:
            self.quality_calculator = self._create_fallback_analyzer()

        # State management
        self.is_active = False
        self.is_paused = False
        self.roi_coords = []
        self.roi_bounds = None  # (x1, y1, x2, y2)

        # ROI-specific frequency control
        self.update_frequency = 1000  # Default 1 second for ROI updates
        self.roi_timer_id = None  # Separate timer for ROI updates

        # Optimization settings
        self.calculation_mode = 'balanced'  # 'fast', 'balanced', 'full'
        self._last_roi_hash = None
        self._last_quality_result = None
        self._last_calc_time = 0
        self._cache_validity_ms = 50  # Cache valid for 50ms

        # Performance monitoring
        self.perf_stats = {
            'capture_times': deque(maxlen=50),
            'calc_times': deque(maxlen=50),
            'display_times': deque(maxlen=50),
            'total_times': deque(maxlen=50)
        }

        # Screen capture data
        self.original_screen_capture = None

        # Overlay windows
        self.roi_selector_overlay = None
        self.quality_overlay = None
        self.stats_window = None

        # Analysis data - ROI specific
        self.current_quality_map = None
        self.current_score = None
        self.analysis_history = deque(maxlen=100)

        # Callbacks
        self.on_roi_selected_callback = None
        self.on_analysis_complete_callback = None

        logger.info("LiveAnalyzeMode initialized with optimizations")

    def _create_fallback_analyzer(self):
        """Create fallback analyzer if none available."""

        class FallbackAnalyzer:
            def calculate_quality_map(self, image):
                if len(image.shape) == 3:
                    gray = np.mean(image, axis=2).astype(np.uint8)
                else:
                    gray = image.astype(np.uint8)

                # Basic gradient analysis
                grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
                grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
                gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
                quality_map = gradient_magnitude / (gradient_magnitude.max() + 1e-6)

                overall_score = float(np.mean(quality_map))
                return quality_map, overall_score

            def calculate_subset_quality(self, subset):
                std_val = np.std(subset)
                return min(1.0, std_val / 128.0)

            def calculate_live_analysis_quality(self, image, grid_size=None):
                # Simplified version for fallback
                quality_map, score = self.calculate_quality_map(image)
                return quality_map, score

        return FallbackAnalyzer()

    def start_live_analysis(self, on_roi_selected=None, on_analysis_complete=None):
        """Start live analysis process."""
        if self.is_active:
            logger.warning("Live analysis already active")
            return

        logger.info("Starting live analysis...")

        # Set callbacks
        self.on_roi_selected_callback = on_roi_selected
        self.on_analysis_complete_callback = on_analysis_complete

        # Reset state
        self.is_active = True
        self.is_paused = False
        self.roi_coords = []
        self.roi_bounds = None
        self.analysis_history.clear()

        # Auto-select calculation mode based on frequency
        self._auto_select_calculation_mode()

        # Capture original screen state BEFORE showing overlays
        self._capture_original_screen()

        # Show ROI selector
        self._show_roi_selector()

    def _auto_select_calculation_mode(self):
        """Automatically select calculation mode based on frequency."""
        if self.update_frequency < 500:
            self.calculation_mode = 'fast'
        elif self.update_frequency < 2000:
            self.calculation_mode = 'balanced'
        else:
            self.calculation_mode = 'full'

        logger.info(f"Auto-selected {self.calculation_mode} mode for {self.update_frequency}ms updates")

    def _capture_original_screen(self):
        """Capture the original screen state."""
        try:
            logger.info("Capturing original screen...")
            self.original_screen_capture = ImageGrab.grab()
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            self._show_error("Failed to capture screen. Please check permissions.")

    def _show_roi_selector(self):
        """Show the ROI selection overlay."""
        try:
            # Create ROI selector if not exists
            if not self.roi_selector_overlay:
                # TransparentROISelector expects the original screenshot
                if not self.original_screen_capture:
                    logger.error("No original screen capture available")
                    self._show_error("Failed to capture screen for ROI selection")
                    return

                self.roi_selector_overlay = TransparentROISelector(
                    self.root,
                    self.original_screen_capture,  # Pass the screenshot
                    on_roi_selected=self._on_roi_selection_complete,  # Correct parameter name
                    on_cancelled=self._on_roi_selection_cancel  # Correct parameter name
                )

            # Note: TransparentROISelector shows itself automatically in __init__
            # No need to call start_selection()

        except Exception as e:
            logger.error(f"Failed to show ROI selector: {e}")
            self._show_error(f"Failed to show ROI selector: {str(e)}")

    def _on_roi_selection_complete(self, coords: List[Tuple[int, int]]):
        """Handle ROI selection completion."""
        logger.info(f"ROI selection complete with {len(coords)} points")

        if len(coords) < 3:
            self._show_error("Please select at least 3 points for ROI")
            return

        # Store ROI coordinates
        self.roi_coords = coords
        self.roi_bounds = self._calculate_roi_bounds(coords)

        logger.info(f"ROI bounds: {self.roi_bounds}")

        # Hide selector
        if self.roi_selector_overlay:
            self.roi_selector_overlay.hide()

        # Callback
        if self.on_roi_selected_callback:
            self.on_roi_selected_callback(coords, self.roi_bounds)

        # Create overlay windows
        self._create_overlay_windows()

        # Start ROI analysis with timer
        self._start_roi_analysis_timer()

    def _calculate_roi_bounds(self, coords):
        """Calculate ROI bounds from coordinates."""
        if not coords:
            return None

        x_coords = [coord[0] for coord in coords]
        y_coords = [coord[1] for coord in coords]

        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        # Add small padding
        padding = 5
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = x2 + padding
        y2 = y2 + padding

        return (x1, y1, x2, y2)

    def _create_overlay_windows(self):
        """Create the overlay windows for display."""
        try:
            # Create quality overlay
            if not self.quality_overlay and self.roi_bounds:
                self.quality_overlay = QualityOverlay(
                    self.root,
                    self.roi_bounds,
                    getattr(self.main_app, 'colormap_generator', None)
                )

            # Create stats window
            if not self.stats_window:
                self.stats_window = StatsWindow(self.root, self)
                self.stats_window.show()

        except Exception as e:
            logger.error(f"Error creating overlay windows: {e}")

    def _start_roi_analysis_timer(self):
        """Start the ROI analysis timer."""
        if not self.roi_bounds:
            logger.warning("No ROI bounds set, cannot start analysis")
            return

        logger.info(f"Starting ROI analysis timer with {self.update_frequency}ms frequency")

        # Perform first analysis immediately
        self._perform_roi_analysis()

    def _schedule_next_roi_analysis(self):
        """Schedule the next ROI analysis."""
        if self.is_active and not self.is_paused:
            self.roi_timer_id = self.root.after(
                self.update_frequency,
                self._perform_roi_analysis
            )

    def _perform_roi_analysis(self):
        """Perform optimized ROI analysis with performance monitoring."""
        if self.is_paused or not self.roi_bounds:
            return

        total_start = time.time()

        try:
            # Phase 1: Capture screen
            capture_start = time.time()

            # Hide overlays before capture
            if self.quality_overlay:
                self.quality_overlay.hide()

            # Brief delay to ensure overlay is hidden
            self.root.update_idletasks()
            time.sleep(0.01)

            # Capture only ROI area for efficiency
            screenshot = ImageGrab.grab(bbox=self.roi_bounds)
            roi_array = np.array(screenshot)

            capture_time = time.time() - capture_start
            self.perf_stats['capture_times'].append(capture_time)

            # Phase 2: Check cache
            roi_hash = self._get_roi_hash(roi_array)
            current_time_ms = time.time() * 1000

            if (self._last_roi_hash == roi_hash and
                    self._last_quality_result is not None and
                    (current_time_ms - self._last_calc_time) < self._cache_validity_ms):

                # Use cached result
                quality_map, overall_score = self._last_quality_result
                calc_time = 0
                logger.debug("Using cached quality result")

            else:
                # Phase 3: Calculate quality
                calc_start = time.time()

                quality_map, overall_score = self._calculate_optimized_quality(roi_array)

                calc_time = time.time() - calc_start
                self.perf_stats['calc_times'].append(calc_time)

                # Update cache
                self._last_roi_hash = roi_hash
                self._last_quality_result = (quality_map, overall_score)
                self._last_calc_time = current_time_ms

            # Phase 4: Update displays
            display_start = time.time()

            # Store results
            self.current_quality_map = quality_map
            self.current_score = overall_score

            # Add to history
            timestamp = time.time()
            self.analysis_history.append({
                'timestamp': timestamp,
                'score': overall_score,
                'roi_size': roi_array.shape[:2]
            })

            # Update displays
            self._update_displays(quality_map, overall_score)

            # Show overlay again
            if self.quality_overlay:
                self.quality_overlay.show()

            display_time = time.time() - display_start
            self.perf_stats['display_times'].append(display_time)

            # Total time
            total_time = time.time() - total_start
            self.perf_stats['total_times'].append(total_time)

            # Performance monitoring
            if total_time > (self.update_frequency * 0.5 / 1000):  # >50% of update frequency
                logger.warning(f"Performance warning - Total: {total_time * 1000:.1f}ms "
                               f"(Capture: {capture_time * 1000:.1f}ms, "
                               f"Calc: {calc_time * 1000:.1f}ms, "
                               f"Display: {display_time * 1000:.1f}ms)")

            # Callback
            if self.on_analysis_complete_callback:
                self.on_analysis_complete_callback(quality_map, overall_score)

        except Exception as e:
            logger.error(f"Error in ROI analysis: {e}")

        finally:
            # Schedule next analysis
            self._schedule_next_roi_analysis()

    def _get_roi_hash(self, roi_array: np.ndarray) -> int:
        """Generate fast hash of ROI for caching."""
        # Downsample for faster hashing if large
        if roi_array.size > 10000:
            sample = roi_array[::10, ::10]
        else:
            sample = roi_array

        return hash((
            roi_array.shape,
            round(float(np.mean(sample)), 2),
            round(float(np.std(sample)), 2)
        ))

    def _calculate_optimized_quality(self, roi_array: np.ndarray) -> tuple:
        """Calculate quality using optimized method based on current mode."""
        try:
            # Convert to grayscale
            if len(roi_array.shape) == 3:
                gray = cv2.cvtColor(roi_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = roi_array.copy()

            # Convert screen ROI coordinates to image-relative coordinates
            roi_coords_relative = None
            if self.roi_coords and len(self.roi_coords) >= 3:
                x1, y1, x2, y2 = self.roi_bounds
                roi_coords_relative = [(x - x1, y - y1) for x, y in self.roi_coords]

            # Check if calculator has optimized method
            if hasattr(self.quality_calculator, 'calculate_live_analysis_quality'):
                # Use optimized method with ROI coordinates
                grid_size = self._get_optimal_grid_size(gray.shape)
                quality_map, overall_score = self.quality_calculator.calculate_live_analysis_quality(
                    gray, roi_coords=roi_coords_relative, grid_size=grid_size
                )
            else:
                # Fall back to mode-specific calculation with ROI masking
                quality_map, overall_score = self._calculate_quality_with_roi_mask(gray, roi_coords_relative)

            return quality_map, overall_score

        except Exception as e:
            logger.error(f"Error in optimized quality calculation: {e}")
            return np.zeros(roi_array.shape[:2], dtype=np.float32), 0.0

    def _calculate_quality_with_roi_mask(self, gray: np.ndarray, roi_coords: Optional[List[Tuple[int, int]]]) -> tuple:
        """Calculate quality with ROI masking fallback."""
        # Create ROI mask if coordinates provided
        if roi_coords and len(roi_coords) >= 3:
            mask = np.zeros(gray.shape[:2], dtype=np.uint8)
            pts = np.array(roi_coords, dtype=np.int32)

            # Clamp coordinates to image bounds
            h, w = gray.shape
            pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)
            pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)

            cv2.fillPoly(mask, [pts], 255)

            # Apply mask to image
            masked_gray = cv2.bitwise_and(gray, gray, mask=mask)
        else:
            masked_gray = gray
            mask = None

        # Calculate quality based on current mode
        if self.calculation_mode == 'fast':
            quality_map, overall_score = self._calculate_fast_quality(masked_gray)
        elif self.calculation_mode == 'balanced':
            quality_map, overall_score = self._calculate_balanced_quality(masked_gray)
        else:  # full
            quality_map, overall_score = self._calculate_full_quality(masked_gray)

        # If we used a mask, calculate score only from ROI pixels
        if mask is not None:
            roi_pixels = quality_map[mask > 0]
            if len(roi_pixels) > 0:
                overall_score = float(np.mean(roi_pixels))

        return quality_map, overall_score

    def _get_optimal_grid_size(self, image_shape: tuple) -> tuple:
        """Determine optimal grid size based on image size and mode."""
        h, w = image_shape[:2]
        min_dim = min(h, w)

        if self.calculation_mode == 'fast':
            # Always use small grid for speed
            return (5, 5)
        elif self.calculation_mode == 'balanced':
            # Adaptive grid based on size
            if min_dim < 100:
                return (5, 5)
            elif min_dim < 300:
                return (10, 10)
            elif min_dim < 600:
                return (15, 15)
            else:
                return (20, 20)
        else:  # full
            # Larger grid for more detail
            if min_dim < 200:
                return (10, 10)
            elif min_dim < 400:
                return (20, 20)
            else:
                return (30, 30)

    def _calculate_fast_quality(self, gray: np.ndarray) -> tuple:
        """Fast quality calculation using simple gradient analysis."""
        # Simple gradient-based quality map
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

        # Normalize
        quality_map = gradient_magnitude / (gradient_magnitude.max() + 1e-6)
        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.5)

        # Calculate accurate score if possible
        if hasattr(self.quality_calculator, 'calculate_subset_quality'):
            overall_score = self.quality_calculator.calculate_subset_quality(gray)
        else:
            overall_score = np.mean(quality_map)

        return quality_map, overall_score

    def _calculate_balanced_quality(self, gray: np.ndarray) -> tuple:
        """Balanced quality calculation using grid approach."""
        h, w = gray.shape
        grid_size = self._get_optimal_grid_size(gray.shape)
        grid_rows, grid_cols = grid_size

        # Calculate cell dimensions
        cell_h = h // grid_rows
        cell_w = w // grid_cols

        # Initialize quality grid
        quality_grid = np.zeros((grid_rows, grid_cols), dtype=np.float32)

        # Process each grid cell
        for i in range(grid_rows):
            for j in range(grid_cols):
                y_start = i * cell_h
                y_end = min((i + 1) * cell_h, h)
                x_start = j * cell_w
                x_end = min((j + 1) * cell_w, w)

                cell = gray[y_start:y_end, x_start:x_end]

                # Calculate quality for this cell
                if hasattr(self.quality_calculator, 'calculate_subset_quality'):
                    cell_quality = self.quality_calculator.calculate_subset_quality(cell)
                else:
                    cell_quality = np.std(cell) / 128.0

                quality_grid[i, j] = cell_quality

        # Upscale to full size
        quality_map = cv2.resize(quality_grid, (w, h), interpolation=cv2.INTER_CUBIC)
        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.5)
        quality_map = np.clip(quality_map, 0, 1)

        # Calculate overall score using full analysis if available
        if hasattr(self.quality_calculator, 'analyze_comprehensive'):
            try:
                full_metrics = self.quality_calculator.analyze_comprehensive(gray)
                overall_score = self.quality_calculator.calculate_overall_quality_score(full_metrics)
            except:
                overall_score = np.mean(quality_map)
        else:
            overall_score = np.mean(quality_map)

        return quality_map, overall_score

    def _calculate_full_quality(self, gray: np.ndarray) -> tuple:
        """Full quality calculation using original method."""
        if hasattr(self.quality_calculator, 'calculate_quality_map'):
            return self.quality_calculator.calculate_quality_map(gray)
        else:
            # Fall back to balanced
            return self._calculate_balanced_quality(gray)

    def _update_displays(self, quality_map: np.ndarray, overall_score: float):
        """Update all display components."""
        try:
            # Update quality overlay
            if self.quality_overlay:
                self.quality_overlay.update_quality_map(quality_map)

            # Update stats window
            if self.stats_window:
                self.stats_window.update_stats(
                    overall_score,
                    time.time(),
                    list(self.analysis_history)
                )

            logger.debug(f"Displays updated - Score: {overall_score:.3f}")

        except Exception as e:
            logger.error(f"Error updating displays: {e}")

    def set_update_frequency(self, frequency_ms):
        """Set ROI analysis update frequency with auto-optimization."""
        old_frequency = self.update_frequency
        self.update_frequency = max(100, frequency_ms)

        # Auto-adjust calculation mode
        self._auto_select_calculation_mode()

        # Adjust cache validity based on frequency
        if frequency_ms < 500:
            self._cache_validity_ms = min(100, frequency_ms // 2)
        else:
            self._cache_validity_ms = 50

        logger.info(f"ROI frequency: {old_frequency}ms -> {self.update_frequency}ms "
                    f"(Mode: {self.calculation_mode}, Cache: {self._cache_validity_ms}ms)")

        # Restart timer with new frequency if active
        if self.is_active and not self.is_paused and self.roi_timer_id:
            try:
                self.root.after_cancel(self.roi_timer_id)
                self.roi_timer_id = None
                self._schedule_next_roi_analysis()
            except Exception as e:
                logger.error(f"Error updating ROI frequency: {e}")

    def pause_analysis(self):
        """Pause ROI analysis."""
        if not self.is_active:
            return

        self.is_paused = True

        if self.roi_timer_id:
            try:
                self.root.after_cancel(self.roi_timer_id)
                self.roi_timer_id = None
            except:
                pass

        logger.info("ROI analysis paused")

    def resume_analysis(self):
        """Resume ROI analysis."""
        if not self.is_active or not self.is_paused:
            return

        self.is_paused = False
        self._schedule_next_roi_analysis()
        logger.info("ROI analysis resumed")

    def stop_live_analysis(self):
        """Stop live analysis and clean up."""
        logger.info("Stopping live analysis...")

        self.is_active = False
        self.is_paused = False

        # Cancel timer
        if self.roi_timer_id:
            try:
                self.root.after_cancel(self.roi_timer_id)
                self.roi_timer_id = None
            except:
                pass

        # Clean up windows
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
            logger.error(f"Error cleaning up windows: {e}")

        # Log performance summary
        self.log_performance_summary()

        logger.info("Live analysis stopped")

    def get_performance_stats(self) -> dict:
        """Get performance statistics."""
        stats = {}

        for key, values in self.perf_stats.items():
            if values:
                stats[key] = {
                    'mean': np.mean(values) * 1000,  # Convert to ms
                    'max': np.max(values) * 1000,
                    'min': np.min(values) * 1000,
                    'latest': values[-1] * 1000
                }

        # Calculate actual vs requested frequency
        if self.perf_stats['total_times']:
            avg_cycle_time = np.mean(self.perf_stats['total_times']) * 1000  # ms
            actual_frequency = 1000 / avg_cycle_time if avg_cycle_time > 0 else 0
            requested_frequency = 1000 / self.update_frequency

            stats['frequency'] = {
                'requested': requested_frequency,
                'actual': actual_frequency,
                'efficiency': (actual_frequency / requested_frequency * 100) if requested_frequency > 0 else 0
            }

        return stats

    def log_performance_summary(self):
        """Log a summary of performance statistics."""
        stats = self.get_performance_stats()

        if stats:
            logger.info("=== Live Analysis Performance Summary ===")
            logger.info(f"Mode: {self.calculation_mode}")
            logger.info(f"Update Frequency: {self.update_frequency}ms")
            logger.info(f"Cache Validity: {self._cache_validity_ms}ms")

            if 'capture_times' in stats:
                logger.info(f"Capture: {stats['capture_times']['mean']:.1f}ms avg "
                            f"({stats['capture_times']['min']:.1f}-{stats['capture_times']['max']:.1f}ms)")
            if 'calc_times' in stats:
                logger.info(f"Calculation: {stats['calc_times']['mean']:.1f}ms avg "
                            f"({stats['calc_times']['min']:.1f}-{stats['calc_times']['max']:.1f}ms)")
            if 'display_times' in stats:
                logger.info(f"Display: {stats['display_times']['mean']:.1f}ms avg "
                            f"({stats['display_times']['min']:.1f}-{stats['display_times']['max']:.1f}ms)")
            if 'total_times' in stats:
                logger.info(f"Total: {stats['total_times']['mean']:.1f}ms avg "
                            f"({stats['total_times']['min']:.1f}-{stats['total_times']['max']:.1f}ms)")
            if 'frequency' in stats:
                logger.info(f"Actual Frequency: {stats['frequency']['actual']:.1f}Hz "
                            f"({stats['frequency']['efficiency']:.0f}% efficiency)")
            logger.info("=======================================")

    def _on_roi_selection_cancel(self):
        """Handle ROI selection cancellation."""
        logger.info("ROI selection cancelled")

        if self.roi_selector_overlay:
            self.roi_selector_overlay.hide()

        self.stop_live_analysis()

    def _show_error(self, message):
        """Show error message to user."""
        try:
            messagebox.showerror("Live Analysis Error", message)
        except:
            print(f"Live Analysis Error: {message}")