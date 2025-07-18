# ui/live_analyze/live_analyze_mode.py - Live Analysis Mode Implementation

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

from .transparent_roi_selector import TransparentROISelector
from .quality_overlay import QualityOverlay
from .stats_window import StatsWindow

logger = logging.getLogger(__name__)

# ui/live_analyze/live_analyze_mode.py - FIXED Live Analysis Mode Implementation

import tkinter as tk
from PIL import ImageGrab, Image, ImageTk
import numpy as np
from typing import Optional, Tuple, List, Callable
import threading
import time
from collections import deque
import logging

logger = logging.getLogger(__name__)


class LiveAnalyzeMode:
    """
    FIXED Live Analysis Mode for real-time DIC quality assessment.

    CRITICAL REQUIREMENT: Screen darkening must NEVER affect image analysis results.

    Order of Operations:
    1. FIRST: Capture original screen without any overlays
    2. THEN: Show transparent overlay for ROI selection
    3. ANALYSIS: Always use fresh captures, hiding overlays before each capture
    """

    def __init__(self, root, main_app):
        """Initialize Live Analyze Mode."""
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

        # CRITICAL FIX: ROI-specific frequency control
        self.update_frequency = 1000  # Default 1 second for ROI updates
        self.roi_timer_id = None  # Separate timer for ROI updates

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

        logger.info("LiveAnalyzeMode initialized with ROI-specific frequency control")

    def _create_fallback_analyzer(self):
        """Create fallback analyzer if none available."""

        class FallbackAnalyzer:
            def calculate_quality_map(self, image):
                # Simple gradient-based analysis
                if len(image.shape) == 3:
                    gray = np.mean(image, axis=2).astype(np.uint8)
                else:
                    gray = image.astype(np.uint8)

                # Calculate gradients
                grad_x = np.gradient(gray.astype(np.float32), axis=1)
                grad_y = np.gradient(gray.astype(np.float32), axis=0)
                gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

                # Normalize to 0-1 range
                quality_map = gradient_magnitude / 255.0
                quality_map = np.clip(quality_map, 0, 1)

                overall_score = float(np.mean(quality_map))
                return quality_map, overall_score

        return FallbackAnalyzer()

    def start_live_analysis(self, on_roi_selected=None, on_analysis_complete=None):
        """Start live analysis with ROI-specific frequency control."""
        logger.info("Starting live analysis with ROI-specific updates")

        # Store callbacks
        self.on_roi_selected_callback = on_roi_selected
        self.on_analysis_complete_callback = on_analysis_complete

        # Set active state
        self.is_active = True
        self.is_paused = False

        # CRITICAL: Capture original screen FIRST, before any overlays
        try:
            self.original_screen_capture = self._capture_full_screen()
            logger.info("Original screen captured successfully")
        except Exception as e:
            logger.error(f"Failed to capture original screen: {e}")
            self._show_error("Failed to capture screen. Please try again.")
            return

        # Start ROI selection
        self._start_roi_selection()

    def _capture_full_screen(self):
        """Capture full screen without any overlays."""
        try:
            # Ensure no overlays are present
            self._hide_all_overlays()

            # Small delay to ensure clean capture
            self.root.update()
            time.sleep(0.1)

            # Capture full screen
            screenshot = ImageGrab.grab()
            logger.info(f"Full screen captured: {screenshot.size}")

            return screenshot

        except Exception as e:
            logger.error(f"Error capturing full screen: {e}")
            raise

    def _start_roi_selection(self):
        """Start ROI selection with transparent overlay."""
        try:
            # Create ROI selector overlay
            self.roi_selector_overlay = TransparentROISelector(
                self.root,
                self.original_screen_capture,
                on_roi_selected=self._on_roi_selection_complete,
                on_cancelled=self._on_roi_selection_cancelled
            )

            self.roi_selector_overlay.show()
            logger.info("ROI selector overlay shown")

        except Exception as e:
            logger.error(f"Error starting ROI selection: {e}")
            self._show_error(f"Failed to start ROI selection: {str(e)}")
            self.stop_live_analysis()

    def _on_roi_selection_complete(self, screen_coords):
        """Handle ROI selection completion."""
        logger.info(f"ROI selection complete with {len(screen_coords)} points")

        # Store ROI coordinates and calculate bounds
        self.roi_coords = screen_coords
        self.roi_bounds = self._calculate_roi_bounds(screen_coords)

        # Close ROI selector
        if self.roi_selector_overlay:
            self.roi_selector_overlay.close()
            self.roi_selector_overlay = None

        # Notify callback
        if self.on_roi_selected_callback:
            self.on_roi_selected_callback(screen_coords)

        # CRITICAL: Start ROI-specific analysis loop
        self._start_roi_analysis_loop()

    def _on_roi_selection_cancelled(self):
        """Handle ROI selection cancellation."""
        logger.info("ROI selection cancelled")
        self.stop_live_analysis()

    def _start_roi_analysis_loop(self):
        """Start the ROI-specific analysis loop."""
        if not self.roi_bounds:
            logger.error("No ROI bounds available for analysis")
            return

        logger.info(f"Starting ROI analysis loop at {self.update_frequency}ms intervals")

        # Show monitoring windows
        self._show_stats_window()
        self._show_quality_overlay()

        # CRITICAL: Start ROI-specific timer
        self._schedule_next_roi_analysis()

    def _schedule_next_roi_analysis(self):
        """Schedule the next ROI analysis - ONLY affects ROI updates."""
        if not self.is_active or self.is_paused:
            return

        try:
            # CRITICAL: This timer ONLY controls ROI analysis frequency
            self.roi_timer_id = self.root.after(
                self.update_frequency,
                self._perform_roi_analysis
            )
            logger.debug(f"Next ROI analysis scheduled in {self.update_frequency}ms")

        except Exception as e:
            logger.error(f"Error scheduling ROI analysis: {e}")

    def _perform_roi_analysis(self):
        """Perform analysis ONLY on the ROI region at specified frequency."""
        if not self.is_active or self.is_paused:
            return

        try:
            # CRITICAL: Capture ONLY the ROI region
            roi_image = self._capture_roi_region()

            if roi_image is None:
                logger.warning("Failed to capture ROI region")
                self._schedule_next_roi_analysis()
                return

            # Analyze ROI quality
            roi_array = np.array(roi_image)
            quality_map, overall_score = self._analyze_roi_quality(roi_array)

            # Update displays
            self._update_roi_displays(quality_map, overall_score)

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
            logger.error(f"ROI analysis error: {e}")

        finally:
            # CRITICAL: Schedule next ROI update at specified frequency
            self._schedule_next_roi_analysis()

    def _capture_roi_region(self):
        """Capture ONLY the ROI region safely."""
        try:
            # CRITICAL: Hide overlays before capture
            self._hide_all_overlays()

            # Small delay to ensure overlays are hidden
            self.root.update()
            time.sleep(0.02)  # Minimal delay

            # Capture only the ROI bounding box
            x1, y1, x2, y2 = self.roi_bounds
            roi_capture = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            # Restore overlays
            self._show_all_overlays()

            return roi_capture

        except Exception as e:
            logger.error(f"Error capturing ROI region: {e}")
            self._show_all_overlays()  # Ensure overlays are restored
            return None

    def _analyze_roi_quality(self, roi_array):
        """Analyze quality of ROI region."""
        try:
            # Use the quality calculator
            quality_map, overall_score = self.quality_calculator.calculate_quality_map(roi_array)

            # Store current results
            self.current_quality_map = quality_map
            self.current_score = overall_score

            return quality_map, overall_score

        except Exception as e:
            logger.error(f"Error analyzing ROI quality: {e}")
            # Return fallback results
            return np.zeros(roi_array.shape[:2]), 0.0

    def _update_roi_displays(self, quality_map, overall_score):
        """Update displays with ROI analysis results."""
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

        except Exception as e:
            logger.error(f"Error updating ROI displays: {e}")

    def _calculate_roi_bounds(self, coords):
        """Calculate bounding box for ROI coordinates."""
        if not coords:
            return None

        x_coords = [coord[0] for coord in coords]
        y_coords = [coord[1] for coord in coords]

        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        # Add padding for better capture
        padding = 5
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = x2 + padding
        y2 = y2 + padding

        return (x1, y1, x2, y2)

    def _show_stats_window(self):
        """Show statistics window."""
        try:
            from .stats_window import StatsWindow

            if not self.stats_window:
                self.stats_window = StatsWindow(self.root, self)

            self.stats_window.show()

        except ImportError:
            logger.warning("StatsWindow not available")
        except Exception as e:
            logger.error(f"Error showing stats window: {e}")

    def _show_quality_overlay(self):
        """Show quality overlay over ROI."""
        try:
            from .quality_overlay import QualityOverlay

            if not self.quality_overlay and self.roi_bounds:
                x1, y1, x2, y2 = self.roi_bounds
                self.quality_overlay = QualityOverlay(
                    self.root,
                    x1, y1, x2 - x1, y2 - y1
                )

            if self.quality_overlay:
                self.quality_overlay.show()

        except ImportError:
            logger.warning("QualityOverlay not available")
        except Exception as e:
            logger.error(f"Error showing quality overlay: {e}")

    def _hide_all_overlays(self):
        """Hide all overlays during capture."""
        try:
            if self.quality_overlay:
                self.quality_overlay.hide()
        except Exception as e:
            logger.error(f"Error hiding overlays: {e}")

    def _show_all_overlays(self):
        """Show all overlays after capture."""
        try:
            if self.quality_overlay:
                self.quality_overlay.show()
        except Exception as e:
            logger.error(f"Error showing overlays: {e}")

    def _show_error(self, message):
        """Show error message to user."""
        try:
            from tkinter import messagebox
            messagebox.showerror("Live Analysis Error", message)
        except:
            print(f"Live Analysis Error: {message}")

    # Public control methods
    def set_update_frequency(self, frequency_ms):
        """Set ROI analysis update frequency (ROI-specific only)."""
        old_frequency = self.update_frequency
        self.update_frequency = max(100, frequency_ms)  # Minimum 100ms

        logger.info(f"ROI analysis frequency: {old_frequency}ms -> {self.update_frequency}ms")

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
        """Stop live analysis and clean up completely."""
        logger.info("Stopping live analysis")

        # Set inactive state
        self.is_active = False
        self.is_paused = False

        # Cancel ROI timer
        if self.roi_timer_id:
            try:
                self.root.after_cancel(self.roi_timer_id)
            except:
                pass
            self.roi_timer_id = None

        # Close all overlays and windows
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
            logger.error(f"Error closing overlays: {e}")

        # Clear data
        self.roi_coords = []
        self.roi_bounds = None
        self.current_quality_map = None
        self.current_score = None
        self.analysis_history.clear()
        self.original_screen_capture = None

        logger.info("Live analysis stopped and cleaned up")

    def get_current_results(self):
        """Get current analysis results."""
        if self.current_quality_map is not None and self.current_score is not None:
            return {
                'quality_map': self.current_quality_map,
                'overall_score': self.current_score,
                'roi_bounds': self.roi_bounds,
                'roi_coords': self.roi_coords,
                'history': list(self.analysis_history)
            }
        return None

    def start_live_analyze(self):
        """Start live analysis mode with proper capture order"""
        try:
            # 1. CRITICAL: Capture screen FIRST, before ANY overlay
            print("Capturing original screen...")
            self.original_screen_capture = self.capture_full_screen()
            
            # 2. Minimize main window
            self.main_app.root.withdraw()
            
            # 3. Small delay to ensure window is hidden
            time.sleep(0.1)
            
            # 4. NOW show the transparent overlay for ROI selection
            self.show_roi_selector()
            
            # 5. Set active state
            self.is_active = True
            
        except Exception as e:
            self.handle_error(f"Failed to start live analyze: {e}")
            self.main_app.root.deiconify()
    
    def capture_full_screen(self):
        """Capture the full screen WITHOUT any overlays"""
        # Use PIL ImageGrab for cross-platform compatibility
        # This captures the screen as it appears to the user
        screenshot = ImageGrab.grab()
        return screenshot
    
    def show_roi_selector(self):
        """Show ROI selector overlay AFTER capturing original screen"""
        self.roi_selector_overlay = TransparentROISelector(
            self.root, 
            self.original_screen_capture,  # Pass the pre-captured screen
            completion_callback=self.on_roi_selected
        )
    
    def _capture_original_screen(self):
        """CRITICAL: Capture the original screen without any overlays."""
        try:
            logger.info("Capturing original screen (no overlays)")
            # Capture entire screen
            self.original_screen_capture = ImageGrab.grab()
            logger.info(f"Original screen captured: {self.original_screen_capture.size}")
        except Exception as e:
            logger.error(f"Failed to capture original screen: {e}")
            raise
    
    def _show_roi_selector(self):
        """Show the transparent ROI selector overlay."""
        if not self.original_screen_capture:
            logger.error("No original screen capture available")
            return
        
        try:
            logger.info("Showing ROI selector overlay")
            self.roi_selector_overlay = TransparentROISelector(
                self.root, 
                self.original_screen_capture,
                completion_callback=self._on_roi_selection_complete
            )
        except Exception as e:
            logger.error(f"Failed to show ROI selector: {e}")
            self.stop_live_analysis()
    
    def on_roi_selected(self, roi_coords: List[Tuple[int, int]]):
        """Handle ROI selection completion"""
        # Store ROI coordinates
        self.roi_coords = roi_coords
        
        # Calculate ROI bounding box
        self.roi_bounds_dict = self.calculate_roi_bounds(roi_coords)
        
        # Convert to tuple format for compatibility
        if roi_coords:
            x_coords = [point[0] for point in roi_coords]
            y_coords = [point[1] for point in roi_coords]
            self.roi_bounds = (
                min(x_coords), min(y_coords),
                max(x_coords), max(y_coords)
            )
        
        # Close ROI selector overlay
        if self.roi_selector_overlay:
            self.roi_selector_overlay.close()
            self.roi_selector_overlay = None
        
        # Start live analysis loop
        self.start_analysis_loop()
        
        # Show results window
        self.show_results_window()
    
    def calculate_roi_bounds(self, coords):
        """Calculate bounding box of ROI"""
        if not coords:
            return {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        
        x_coords = [x for x, y in coords]
        y_coords = [y for x, y in coords]
        return {
            'x': min(x_coords),
            'y': min(y_coords),
            'width': max(x_coords) - min(x_coords),
            'height': max(y_coords) - min(y_coords)
        }
    
    def _start_continuous_analysis(self):
        """Start the continuous analysis loop."""
        if not self.roi_bounds:
            logger.error("No ROI bounds available for analysis")
            return
        
        logger.info("Starting continuous analysis")
        
        # Show stats window
        self._show_stats_window()
        
        # Start analysis timer
        self._schedule_next_analysis()
    
    def start_analysis_loop(self):
        """Start the live analysis update loop"""
        # Cancel any existing timer
        if self.update_timer_id:
            try:
                self.root.after_cancel(self.update_timer_id)
            except:
                pass  # Timer may have already been cancelled or executed
            self.update_timer_id = None
        
        # Perform first analysis immediately
        self.perform_live_analysis()
    
    def perform_live_analysis(self):
        """Perform analysis on current screen content"""
        if not self.is_active or self.is_paused:
            return
        
        try:
            # CRITICAL: Capture current screen WITHOUT any overlays
            current_screen = self.capture_screen_region_safely()
            
            # Extract ROI from captured screen
            roi_image = self.extract_roi_from_screen(current_screen)
            
            # Convert to numpy array for analysis
            roi_array = np.array(roi_image)
            
            # Generate quality map
            quality_map, visualization = self.generate_quality_analysis(roi_array)
            
            # Calculate overall score
            quality_score = self.calculate_overall_score(quality_map)
            
            # Update displays
            self.update_all_displays(quality_map, visualization, quality_score)
            
            # Store in history
            self.analysis_history.append({
                'timestamp': time.time(),
                'score': quality_score,
                'quality_map': quality_map
            })
            
        except Exception as e:
            print(f"Analysis error: {e}")
            logger.error(f"Analysis error: {e}")
        
        finally:
            # Schedule next update
            if self.is_active and not self.is_paused:
                try:
                    self.update_timer_id = self.root.after(
                        self.update_frequency,
                        self.perform_live_analysis
                    )
                except Exception as e:
                    logger.error(f"Error scheduling next analysis: {e}")
                    self.update_timer_id = None
    
    def capture_screen_region_safely(self):
        """Capture screen region ensuring no overlay interference"""
        # CRITICAL: Hide any quality overlay before capture
        if self.quality_overlay:
            self.quality_overlay.hide()
        
        # Small delay to ensure overlay is hidden
        time.sleep(0.05)
        
        # Capture the screen region
        if hasattr(self, 'roi_bounds_dict') and self.roi_bounds_dict:
            bbox = (
                self.roi_bounds_dict['x'],
                self.roi_bounds_dict['y'],
                self.roi_bounds_dict['x'] + self.roi_bounds_dict['width'],
                self.roi_bounds_dict['y'] + self.roi_bounds_dict['height']
            )
        elif self.roi_bounds:
            x1, y1, x2, y2 = self.roi_bounds
            bbox = (x1, y1, x2, y2)
        else:
            bbox = None
        
        screenshot = ImageGrab.grab(bbox=bbox)
        
        # Show quality overlay again
        if self.quality_overlay:
            self.quality_overlay.show()
        
        return screenshot
    
    def _schedule_next_analysis(self):
        """Schedule the next analysis iteration."""
        if not self.is_active or self.is_paused:
            return
        
        # Cancel any existing timer
        if self.update_timer_id:
            try:
                self.root.after_cancel(self.update_timer_id)
            except:
                pass  # Timer may have already been cancelled or executed
            self.update_timer_id = None
        
        # Schedule next analysis
        try:
            self.update_timer_id = self.root.after(self.update_frequency, self._perform_analysis)
        except Exception as e:
            logger.error(f"Error scheduling next analysis: {e}")
            self.update_timer_id = None
    
    def _perform_analysis(self):
        """
        Perform a single analysis iteration.
        
        CRITICAL: Always capture fresh screen data, hiding overlays first.
        """
        if not self.is_active or self.is_paused:
            return
        
        try:
            # CRITICAL: Hide all overlays before capturing
            self._hide_overlays_temporarily()
            
            # Small delay to ensure overlays are hidden
            self.root.after(50, self._capture_and_analyze)
            
        except Exception as e:
            logger.error(f"Error in analysis iteration: {e}")
            self._schedule_next_analysis()
    
    def _hide_overlays_temporarily(self):
        """Temporarily hide all overlays for clean capture."""
        if self.quality_overlay:
            self.quality_overlay.hide()
        if self.stats_window:
            self.stats_window.hide()
    
    def _show_overlays_after_capture(self):
        """Show overlays again after capture."""
        if self.quality_overlay:
            self.quality_overlay.show()
        if self.stats_window:
            self.stats_window.show()
    
    def _capture_and_analyze(self):
        """Capture screen and perform analysis."""
        try:
            # CRITICAL: Capture fresh screen without overlays
            current_screen = ImageGrab.grab()
            
            # Extract ROI from current screen
            if self.roi_bounds:
                x1, y1, x2, y2 = self.roi_bounds
                roi_image = current_screen.crop((x1, y1, x2, y2))
            else:
                roi_image = current_screen
            
            # Convert to numpy array for analysis
            roi_array = np.array(roi_image)
            
            # Perform quality analysis
            self._analyze_roi(roi_array)
            
            # Show overlays again
            self._show_overlays_after_capture()
            
            # Schedule next analysis
            self._schedule_next_analysis()
            
        except Exception as e:
            logger.error(f"Error in capture and analysis: {e}")
            self._show_overlays_after_capture()
            self._schedule_next_analysis()
    
    def _analyze_roi(self, roi_array: np.ndarray):
        """Analyze the ROI and update results."""
        try:
            # Convert to grayscale if needed
            if len(roi_array.shape) == 3:
                roi_gray = np.mean(roi_array, axis=2).astype(np.uint8)
            else:
                roi_gray = roi_array
            
            # Perform quality analysis
            if hasattr(self.quality_calculator, 'calculate_quality_map'):
                quality_map, overall_score = self.quality_calculator.calculate_quality_map(roi_gray)
            else:
                # Fallback method
                overall_score = self._calculate_basic_quality(roi_gray)
                quality_map = np.ones_like(roi_gray, dtype=np.float32) * overall_score
            
            # Store results
            self.current_quality_map = quality_map
            self.current_score = overall_score
            
            # Add to history
            timestamp = time.time()
            self.analysis_history.append({
                'timestamp': timestamp,
                'score': overall_score,
                'roi_size': roi_gray.shape
            })
            
            # Update displays
            self._update_quality_overlay(quality_map)
            self._update_stats_window(overall_score, timestamp)
            
            # Callback
            if self.on_analysis_complete_callback:
                self.on_analysis_complete_callback(quality_map, overall_score)
            
            logger.debug(f"Analysis complete: score={overall_score:.3f}")
            
        except Exception as e:
            logger.error(f"Error in ROI analysis: {e}")
    
    def _calculate_basic_quality(self, image: np.ndarray) -> float:
        """Calculate basic quality score as fallback."""
        try:
            # Simple gradient-based quality measure
            grad_x = np.gradient(image.astype(np.float32), axis=1)
            grad_y = np.gradient(image.astype(np.float32), axis=0)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Normalize to 0-1 range
            quality_score = np.mean(gradient_magnitude) / 255.0
            return min(1.0, max(0.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error in basic quality calculation: {e}")
            return 0.0
    
    def extract_roi_from_screen(self, screen_capture):
        """Extract the exact ROI polygon from screen capture"""
        import cv2
        from PIL import Image, ImageDraw
        
        # Convert PIL Image to numpy array
        screen_array = np.array(screen_capture)
        
        # Create mask for ROI polygon
        mask = Image.new('L', screen_capture.size, 0)
        draw = ImageDraw.Draw(mask)
        
        # Adjust coordinates relative to capture region
        if hasattr(self, 'roi_bounds_dict') and self.roi_bounds_dict:
            adjusted_coords = [
                (x - self.roi_bounds_dict['x'], y - self.roi_bounds_dict['y']) 
                for x, y in self.roi_coords
            ]
        else:
            # Use original coordinates if no bounds dict
            adjusted_coords = self.roi_coords
        
        # Draw polygon mask
        if adjusted_coords:
            draw.polygon(adjusted_coords, fill=255)
        
        # Apply mask
        mask_array = np.array(mask)
        masked_image = cv2.bitwise_and(screen_array, screen_array, mask=mask_array)
        
        return Image.fromarray(masked_image)
    
    def generate_quality_analysis(self, roi_array):
        """Generate quality map and visualization from ROI array"""
        try:
            # Convert to grayscale if needed
            if len(roi_array.shape) == 3:
                roi_gray = np.mean(roi_array, axis=2).astype(np.uint8)
            else:
                roi_gray = roi_array
            
            # Perform quality analysis
            if hasattr(self.quality_calculator, 'calculate_quality_map'):
                quality_map, overall_score = self.quality_calculator.calculate_quality_map(roi_gray)
            else:
                # Fallback method
                overall_score = self._calculate_basic_quality(roi_gray)
                quality_map = np.ones_like(roi_gray, dtype=np.float32) * overall_score
            
            # Generate visualization
            visualization = self._generate_colored_quality_map(quality_map)
            
            return quality_map, visualization
            
        except Exception as e:
            logger.error(f"Error in quality analysis: {e}")
            # Return fallback values
            fallback_map = np.zeros((100, 100), dtype=np.float32)
            fallback_viz = np.zeros((100, 100, 3), dtype=np.uint8)
            return fallback_map, fallback_viz
    
    def _generate_colored_quality_map(self, quality_map):
        """Generate colored quality map visualization"""
        try:
            if self.colormap_generator and hasattr(self.colormap_generator, 'apply_colormap'):
                return self.colormap_generator.apply_colormap(quality_map, spectrum_type='optimized')
            else:
                # Default colormap using OpenCV
                normalized = (quality_map * 255).astype(np.uint8)
                colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
                return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
        except Exception as e:
            logger.error(f"Error generating colored quality map: {e}")
            # Return a proper 3-channel image as fallback
            normalized = (quality_map * 255).astype(np.uint8)
            return np.stack([normalized, normalized, normalized], axis=-1)
    
    def calculate_overall_score(self, quality_map):
        """Calculate overall quality score from quality map"""
        try:
            return float(np.mean(quality_map))
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0
    
    def update_all_displays(self, quality_map, visualization, quality_score):
        """Update all display components with new analysis results"""
        try:
            # Update quality overlay
            self._update_quality_overlay(quality_map)
            
            # Update stats window
            timestamp = time.time()
            self._update_stats_window(quality_score, timestamp)
            
            # Store current results
            self.current_quality_map = quality_map
            self.current_score = quality_score
            
        except Exception as e:
            logger.error(f"Error updating displays: {e}")
    
    def show_results_window(self):
        """Show the results/statistics window"""
        self._show_stats_window()
    
    def show_quality_overlay(self, quality_map, visualization):
        """Show quality map overlay at ROI location"""
        if not self.quality_overlay and self.roi_bounds:
            self._create_quality_overlay()
        
        if self.quality_overlay:
            self.quality_overlay.update_quality_map(quality_map)
    
    def display_quality_visualization(self, visualization):
        """Display quality visualization on overlay canvas"""
        if self.quality_overlay:
            self.quality_overlay.update_quality_map(visualization)
    
    def _update_quality_overlay(self, quality_map: np.ndarray):
        """Update the quality overlay display."""
        if not self.quality_overlay and self.roi_bounds:
            self._create_quality_overlay()
        
        if self.quality_overlay:
            self.quality_overlay.update_quality_map(quality_map)
    
    def _create_quality_overlay(self):
        """Create the quality overlay window."""
        if not self.roi_bounds:
            return
        
        try:
            self.quality_overlay = QualityOverlay(
                self.root,
                self.roi_bounds,
                self.colormap_generator
            )
        except Exception as e:
            logger.error(f"Failed to create quality overlay: {e}")
    
    def _update_stats_window(self, score: float, timestamp: float):
        """Update the statistics window."""
        if self.stats_window:
            self.stats_window.update_stats(score, timestamp, list(self.analysis_history))
    
    def _show_stats_window(self):
        """Show the statistics window."""
        try:
            self.stats_window = StatsWindow(self.root, self)
        except Exception as e:
            logger.error(f"Failed to create stats window: {e}")
    
    def toggle_pause(self):
        """Toggle pause state of live analysis"""
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            # Cancel current timer
            if self.update_timer_id:
                try:
                    self.root.after_cancel(self.update_timer_id)
                except:
                    pass  # Timer may have already been cancelled or executed
                self.update_timer_id = None
            
            # Update UI to show paused state
            if self.stats_window:
                self.stats_window.pause_button.configure(text="Resume")
        else:
            # Resume analysis
            self.perform_live_analysis()
            
            # Update UI
            if self.stats_window:
                self.stats_window.pause_button.configure(text="Pause")
    
    def exit_live_mode(self):
        """Exit live analysis mode cleanly"""
        # Set inactive
        self.is_active = False
        
        # Stop analysis timer
        if self.update_timer_id:
            self.root.after_cancel(self.update_timer_id)
            self.update_timer_id = None
        
        # Close all overlay windows
        if self.quality_overlay:
            self.quality_overlay.close()
            self.quality_overlay = None
        
        if self.stats_window:
            self.stats_window.close()
            self.stats_window = None
        
        if self.roi_selector_overlay:
            self.roi_selector_overlay.close()
            self.roi_selector_overlay = None
        
        # Ask to save results
        if self.analysis_history and self.prompt_save_results():
            self.save_analysis_session()
        
        # Restore main window
        self.main_app.root.deiconify()
        
        # Optionally transfer last analysis to main app
        if self.current_quality_map is not None:
            self.transfer_to_main_app()
    
    def handle_error(self, error_message):
        """Handle errors during live analysis"""
        logger.error(error_message)
        print(f"Error: {error_message}")
        
        # Show error dialog if possible
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Live Analysis Error", error_message)
        except:
            pass
    
    def prompt_save_results(self):
        """Prompt user to save analysis results"""
        try:
            import tkinter.messagebox as messagebox
            return messagebox.askyesno(
                "Save Results", 
                "Do you want to save the live analysis results?"
            )
        except:
            return False
    
    def save_analysis_session(self):
        """Save the current analysis session"""
        try:
            from tkinter import filedialog
            filepath = filedialog.asksaveasfilename(
                title="Save Live Analysis Session",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filepath:
                base_filepath = filepath.rsplit('.', 1)[0]
                return self.export_results(base_filepath)
        except Exception as e:
            logger.error(f"Error saving analysis session: {e}")
            return False
    
    def transfer_to_main_app(self):
        """Transfer current analysis results to main application"""
        try:
            if hasattr(self.main_app, 'load_analysis_results'):
                self.main_app.load_analysis_results({
                    'quality_map': self.current_quality_map,
                    'overall_score': self.current_score,
                    'roi_coords': self.roi_coords,
                    'roi_bounds': self.roi_bounds
                })
        except Exception as e:
            logger.error(f"Error transferring results to main app: {e}")
    
    def pause_analysis(self):
        """Pause the live analysis."""
        self.is_paused = True
        if self.update_timer_id:
            self.root.after_cancel(self.update_timer_id)
            self.update_timer_id = None
        logger.info("Live analysis paused")
    
    def resume_analysis(self):
        """Resume the live analysis."""
        if not self.is_active:
            return
        
        self.is_paused = False
        self._schedule_next_analysis()
        logger.info("Live analysis resumed")
    
    def get_current_results(self) -> Optional[dict]:
        """Get current analysis results."""
        if not self.current_quality_map is None and self.current_score is not None:
            return {
                'quality_map': self.current_quality_map,
                'overall_score': self.current_score,
                'roi_bounds': self.roi_bounds,
                'roi_coords': self.roi_coords,
                'history': list(self.analysis_history)
            }
        return None
    
    def export_results(self, filepath: str):
        """Export current results to file."""
        results = self.get_current_results()
        if not results:
            logger.warning("No results to export")
            return False
        
        try:
            import json
            import pickle
            
            # Export as JSON for metadata
            metadata = {
                'overall_score': results['overall_score'],
                'roi_bounds': results['roi_bounds'],
                'roi_coords': results['roi_coords'],
                'history': results['history'],
                'timestamp': time.time()
            }
            
            with open(f"{filepath}_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Export quality map as pickle
            with open(f"{filepath}_quality_map.pkl", 'wb') as f:
                pickle.dump(results['quality_map'], f)
            
            logger.info(f"Results exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False