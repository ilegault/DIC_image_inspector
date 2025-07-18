# demo_live_analyze.py - Demo script for Live Analysis Mode

"""
Demo script showing how to integrate Live Analysis Mode into the main application.

This demonstrates the critical order of operations:
1. FIRST: Capture original screen without any overlays
2. THEN: Show transparent overlay for ROI selection
3. ANALYSIS: Always use fresh captures, hiding overlays before each capture
"""

import tkinter as tk
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.live_analyze import LiveAnalyzeMode


class DemoApp:
    """Demo application to test Live Analysis Mode."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Live Analysis Demo")
        self.root.geometry("400x300")
        
        # Mock analyzer for demo
        self.analyzer = MockAnalyzer()
        
        # Create live analyze mode
        self.live_mode = LiveAnalyzeMode(self.root, self)
        
        # Create UI
        self.create_ui()
    
    def create_ui(self):
        """Create demo UI."""
        # Title
        title_label = tk.Label(
            self.root, 
            text="Live Analysis Mode Demo",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=20)
        
        # Instructions
        instructions = tk.Text(self.root, height=8, width=50, wrap=tk.WORD)
        instructions.pack(pady=10, padx=20, fill='both', expand=True)
        
        instructions.insert(tk.END, 
            "Live Analysis Demo Instructions:\n\n"
            "1. Click 'Start Live Analysis' below\n"
            "2. The screen will be captured FIRST (critical!)\n"
            "3. A transparent overlay will appear for ROI selection\n"
            "4. Click points to define your ROI polygon\n"
            "5. Right-click or press Enter to complete selection\n"
            "6. Live analysis will begin with quality overlay\n"
            "7. Statistics window will show real-time results\n\n"
            "CRITICAL: Screen darkening never affects analysis results!"
        )
        instructions.configure(state=tk.DISABLED)
        
        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        start_button = tk.Button(
            button_frame,
            text="Start Live Analysis",
            command=self.start_live_analysis,
            bg='green',
            fg='white',
            font=('Arial', 12, 'bold')
        )
        start_button.pack(side='left', padx=10)
        
        stop_button = tk.Button(
            button_frame,
            text="Stop Live Analysis", 
            command=self.stop_live_analysis,
            bg='red',
            fg='white',
            font=('Arial', 12, 'bold')
        )
        stop_button.pack(side='left', padx=10)
        
        # Status
        self.status_var = tk.StringVar(value="Ready to start live analysis")
        status_label = tk.Label(self.root, textvariable=self.status_var)
        status_label.pack(pady=10)
    
    def start_live_analysis(self):
        """Start live analysis mode."""
        self.status_var.set("Starting live analysis...")
        
        # Start live analysis with callbacks
        self.live_mode.start_live_analysis(
            on_roi_selected=self.on_roi_selected,
            on_analysis_complete=self.on_analysis_complete
        )
    
    def stop_live_analysis(self):
        """Stop live analysis mode."""
        self.live_mode.stop_live_analysis()
        self.status_var.set("Live analysis stopped")
    
    def on_roi_selected(self, roi_coords):
        """Callback when ROI is selected."""
        self.status_var.set(f"ROI selected with {len(roi_coords)} points")
        print(f"ROI selected: {roi_coords}")
    
    def on_analysis_complete(self, quality_map, overall_score):
        """Callback when analysis is complete."""
        self.status_var.set(f"Analysis complete - Score: {overall_score:.3f}")
        print(f"Analysis complete: score={overall_score:.3f}, map_shape={quality_map.shape}")
    
    def run(self):
        """Run the demo application."""
        self.root.mainloop()


class MockAnalyzer:
    """Mock analyzer for demo purposes."""
    
    def __init__(self):
        from core.quality_calculator import QualityCalculator
        try:
            self.quality_calculator = QualityCalculator()
        except:
            self.quality_calculator = self
    
    def calculate_quality_map(self, image):
        """Mock quality map calculation."""
        import numpy as np
        
        # Simple gradient-based quality measure
        if len(image.shape) == 2:
            grad_x = np.gradient(image.astype(np.float32), axis=1)
            grad_y = np.gradient(image.astype(np.float32), axis=0)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Normalize to 0-1 range
            quality_map = gradient_magnitude / 255.0
            quality_map = np.clip(quality_map, 0, 1)
            
            overall_score = float(np.mean(quality_map))
            
            return quality_map, overall_score
        else:
            # Fallback for color images
            gray = np.mean(image, axis=2).astype(np.uint8)
            return self.calculate_quality_map(gray)


if __name__ == "__main__":
    print("Starting Live Analysis Demo...")
    print("CRITICAL: Screen capture happens BEFORE any overlays!")
    
    app = DemoApp()
    app.run()