# Live Analysis Module

## Overview

The Live Analysis Module provides real-time DIC quality assessment with the **critical requirement** that screen darkening/overlays must **NEVER** affect the image analysis results.

## Critical Order of Operations

**This order is MANDATORY for accurate analysis:**

1. **FIRST**: Capture original screen without any overlays
2. **THEN**: Show transparent overlay for ROI selection  
3. **ANALYSIS**: Always use fresh captures, hiding overlays before each capture

## Components

### 1. LiveAnalyzeMode (`live_analyze_mode.py`)
Main controller for live analysis functionality.

**Key Methods:**
- `start_live_analysis()` - Start the live analysis process
- `start_live_analyze()` - Alternative start method with window management
- `capture_full_screen()` - Capture screen without overlays
- `on_roi_selected()` - Handle ROI selection completion
- `perform_live_analysis()` - Main analysis loop
- `capture_screen_region_safely()` - Safe screen capture with overlay hiding
- `toggle_pause()` - Pause/resume analysis
- `exit_live_mode()` - Clean exit with optional result saving

### 2. TransparentROISelector (`transparent_roi_selector.py`)
Transparent overlay for ROI selection.

**Features:**
- Displays original screenshot as background
- Interactive polygon ROI selection
- Coordinate conversion from canvas to screen space
- Keyboard shortcuts (Enter to complete, Escape to cancel)

### 3. QualityOverlay (`quality_overlay.py`)
Real-time quality visualization overlay.

**Features:**
- Positioned over the selected ROI
- Color-mapped quality visualization
- Can be hidden during screen captures
- Supports custom and default colormaps

### 4. StatsWindow (`stats_window.py`)
Statistics and control interface.

**Features:**
- Real-time quality score display
- Historical data graphing with matplotlib
- Analysis controls (pause/resume/stop)
- Frequency adjustment
- Export functionality

### 5. LiveResultsWindow (`live_results_window.py`)
Simplified results display window.

**Features:**
- Current quality score display
- Statistics text display
- Control buttons
- Frequency selector

## Usage Example

```python
import tkinter as tk
from ui.live_analyze import LiveAnalyzeMode

class MyApp:
    def __init__(self):
        self.root = tk.Tk()
        self.analyzer = MyAnalyzer()  # Your analyzer
        
        # Create live analyze mode
        self.live_mode = LiveAnalyzeMode(self.root, self)
    
    def start_live_analysis(self):
        """Start live analysis with callbacks."""
        self.live_mode.start_live_analysis(
            on_roi_selected=self.on_roi_selected,
            on_analysis_complete=self.on_analysis_complete
        )
    
    def on_roi_selected(self, roi_coords):
        """Called when ROI is selected."""
        print(f"ROI selected: {len(roi_coords)} points")
    
    def on_analysis_complete(self, quality_map, score):
        """Called when analysis completes."""
        print(f"Analysis complete: score={score:.3f}")
```

## Integration with Main Application

To integrate with the main DIC application:

1. **Add to main window menu:**
```python
# In main_window.py
def create_menu(self):
    # ... existing menu code ...
    
    # Add Live Analysis menu
    live_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Live Analysis", menu=live_menu)
    live_menu.add_command(label="Start Live Analysis", command=self.start_live_analysis)

def start_live_analysis(self):
    """Start live analysis mode."""
    from ui.live_analyze import LiveAnalyzeMode
    
    if not hasattr(self, 'live_mode'):
        self.live_mode = LiveAnalyzeMode(self.root, self)
    
    self.live_mode.start_live_analysis()
```

2. **Add toolbar button:**
```python
# In control panel or toolbar
live_button = tk.Button(
    toolbar_frame,
    text="Live Analysis",
    command=self.start_live_analysis,
    bg='green',
    fg='white'
)
live_button.pack(side='left', padx=2)
```

## Technical Details

### Screen Capture Strategy
- Uses `PIL.ImageGrab.grab()` for cross-platform compatibility
- Captures entire screen first, then specific regions
- Always hides overlays before capture to ensure clean data

### Quality Analysis Integration
- Works with existing `QualityCalculator` class
- Falls back to basic gradient analysis if calculator unavailable
- Supports both quality maps and overall scores

### Overlay Management
- All overlays can be hidden/shown programmatically
- Transparent overlays don't interfere with analysis
- Proper cleanup on exit

### Error Handling
- Comprehensive exception handling throughout
- Graceful degradation when components fail
- User-friendly error messages

## Dependencies

- `tkinter` - GUI framework
- `PIL` (Pillow) - Image processing and screen capture
- `numpy` - Numerical operations
- `opencv-python` - Image processing and colormaps
- `matplotlib` - Graphing (for StatsWindow)

## Demo

Run the demo script to test the functionality:

```bash
python demo_live_analyze.py
```

This will show a demo application with the live analysis mode integrated.

## Important Notes

### Critical Requirements
1. **Screen capture MUST happen before any overlay is shown**
2. **Overlays MUST be hidden before each analysis capture**
3. **Never analyze screen content that includes overlay artifacts**

### Performance Considerations
- Default update frequency is 1 second (adjustable)
- Minimum update frequency is 100ms
- Graph updates every 2 seconds to reduce CPU usage
- History limited to 50 points for performance

### Platform Compatibility
- Tested on Windows 11
- Should work on macOS and Linux (PIL.ImageGrab is cross-platform)
- Transparency effects may vary by platform

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path includes project root

2. **Screen Capture Issues**
   - Verify PIL is properly installed
   - Check screen permissions on macOS/Linux

3. **Overlay Not Showing**
   - Check if window manager supports transparency
   - Verify tkinter version supports required attributes

4. **Analysis Errors**
   - Ensure quality calculator is properly initialized
   - Check if ROI selection is valid

### Debug Mode
Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- Multi-monitor support
- Video recording of analysis sessions
- Advanced ROI shapes (circles, rectangles)
- Real-time parameter adjustment
- Network streaming of results
- Integration with external analysis tools