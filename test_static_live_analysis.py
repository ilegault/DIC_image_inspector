#!/usr/bin/env python3
"""
Test script for the improved static live analysis implementation.

This script demonstrates the truly static window approach where:
1. Windows are created ONCE and never recreated
2. Only content (StringVar and canvas images) updates
3. Screenshots exclude popup windows properly
4. No window refreshing/flickering during updates
"""

import tkinter as tk
from tkinter import messagebox
import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.live_analyze.live_analyze_mode import LiveAnalyzeMode

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockMainApp:
    """Mock main application for testing."""
    
    def __init__(self):
        # Create a simple mock analyzer
        self.analyzer = self._create_mock_analyzer()
        
    def _create_mock_analyzer(self):
        """Create a mock analyzer for testing."""
        import numpy as np
        import cv2
        
        class MockAnalyzer:
            def calculate_quality_map(self, image):
                """Mock quality map calculation."""
                if len(image.shape) == 3:
                    gray = np.mean(image, axis=2).astype(np.uint8)
                else:
                    gray = image.astype(np.uint8)
                
                # Simple gradient analysis
                grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
                grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
                gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
                quality_map = gradient_magnitude / (gradient_magnitude.max() + 1e-6)
                
                overall_score = float(np.mean(quality_map))
                return quality_map, overall_score
            
            def calculate_subset_quality(self, subset):
                """Mock subset quality calculation."""
                std_val = np.std(subset)
                return min(1.0, std_val / 128.0)
            
            def calculate_live_analysis_quality(self, image, roi_coords=None, grid_size=None):
                """Mock optimized live analysis quality calculation."""
                quality_map, score = self.calculate_quality_map(image)
                return quality_map, score
        
        return MockAnalyzer()


def test_static_live_analysis():
    """Test the static live analysis implementation."""
    logger.info("Starting static live analysis test...")
    
    # Create main window
    root = tk.Tk()
    root.title("Static Live Analysis Test")
    root.geometry("400x300+100+100")
    
    # Create mock main app
    mock_app = MockMainApp()
    
    # Create live analyze mode
    live_analyzer = LiveAnalyzeMode(root, mock_app)
    
    # Create UI
    main_frame = tk.Frame(root, bg='lightgray')
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Title
    title_label = tk.Label(
        main_frame,
        text="🔬 Static Live Analysis Test",
        font=('Arial', 16, 'bold'),
        bg='lightgray',
        fg='darkblue'
    )
    title_label.pack(pady=10)
    
    # Instructions
    instructions = tk.Text(
        main_frame,
        height=8,
        wrap='word',
        bg='white',
        font=('Arial', 10)
    )
    instructions.pack(fill='both', expand=True, pady=5)
    
    instructions.insert('1.0', """Instructions for Testing Static Windows:

1. Click 'Start Live Analysis' below
2. Select a region of interest (ROI) on your screen
3. Observe the static windows that appear:
   - Quality Map window (shows colorized quality visualization)
   - Statistics Dashboard (shows real-time stats and graphs)

Key Improvements:
✓ Windows created ONCE - no recreation/refreshing
✓ Only content updates (text and images)
✓ Clean screenshots without popup interference
✓ Smooth, flicker-free operation
✓ Better performance and stability

The windows will stay static while only their content updates!""")
    
    instructions.config(state='disabled')
    
    # Control buttons
    button_frame = tk.Frame(main_frame, bg='lightgray')
    button_frame.pack(fill='x', pady=10)
    
    def start_analysis():
        """Start the live analysis."""
        try:
            live_analyzer.start_live_analysis(
                on_roi_selected=lambda coords, bounds: logger.info(f"ROI selected: {len(coords)} points"),
                on_analysis_complete=lambda qmap, score: logger.debug(f"Analysis complete: {score:.3f}")
            )
        except Exception as e:
            logger.error(f"Error starting analysis: {e}")
            messagebox.showerror("Error", f"Failed to start analysis: {e}")
    
    def stop_analysis():
        """Stop the live analysis."""
        try:
            live_analyzer.stop_live_analysis()
            logger.info("Analysis stopped")
        except Exception as e:
            logger.error(f"Error stopping analysis: {e}")
    
    start_button = tk.Button(
        button_frame,
        text="🚀 Start Live Analysis",
        command=start_analysis,
        bg='green',
        fg='white',
        font=('Arial', 12, 'bold'),
        padx=20,
        pady=5
    )
    start_button.pack(side='left', padx=5)
    
    stop_button = tk.Button(
        button_frame,
        text="⏹️ Stop Analysis",
        command=stop_analysis,
        bg='red',
        fg='white',
        font=('Arial', 12, 'bold'),
        padx=20,
        pady=5
    )
    stop_button.pack(side='left', padx=5)
    
    # Status
    status_var = tk.StringVar(value="Ready to start static live analysis...")
    status_label = tk.Label(
        main_frame,
        textvariable=status_var,
        bg='lightgray',
        fg='darkgreen',
        font=('Arial', 10, 'italic')
    )
    status_label.pack(pady=5)
    
    # Cleanup on close
    def on_closing():
        """Handle window closing."""
        try:
            live_analyzer.stop_live_analysis()
        except:
            pass
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    logger.info("Static live analysis test window created")
    logger.info("Click 'Start Live Analysis' to test the static window implementation")
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    test_static_live_analysis()