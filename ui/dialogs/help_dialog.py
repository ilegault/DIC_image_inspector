# ui/dialogs/help_dialog.py - Fixed version
# Replace your current help_dialog.py with this corrected version

import tkinter as tk
from tkinter import ttk
from utils.constants import APP_CONFIG, get_theme_colors
from utils.window_utils import WindowManager


class HelpDialog:
    """
    Help dialog for displaying application usage information.

    Shows comprehensive help information in a scrollable dialog.
    Follows single responsibility principle - only help display.
    """

    def __init__(self, parent: tk.Widget):
        """
        Initialize help dialog.

        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.help_window = None

    def show(self):
        """Show the help dialog."""
        try:
            self._create_help_window()
            self._create_help_content()
            self._center_window()

        except Exception as e:
            print(f"Error showing help dialog: {e}")

    def _create_help_window(self):
        """Create the help window."""
        self.help_window = WindowManager.create_child_window(
            parent=self.parent,
            title="DIC Image Quality Inspector - Help",
            width=700,
            height=600,
            resizable=True,
            topmost=False,
            center=True
        )

        # FIX: Use get_theme_colors() instead of direct access
        colors = get_theme_colors()
        self.help_window.configure(bg=colors['background'])

        self.help_window.grab_set()
        self.help_window.minsize(600, 500)

    def _create_help_content(self):
        """Create the help content."""
        # FIX: Use get_theme_colors() throughout
        colors = get_theme_colors()

        # Main container
        main_frame = tk.Frame(self.help_window, bg=colors['background'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Title
        title_label = tk.Label(
            main_frame,
            text="🔍 DIC Image Quality Inspector - Help Guide",
            font=APP_CONFIG['fonts']['title'],
            fg=colors['text_primary'],
            bg=colors['background']
        )
        title_label.pack(pady=(0, 20))

        # Create scrollable text area
        self._create_scrollable_help_text(main_frame)

        # Close button
        close_button = tk.Button(
            main_frame,
            text="Close",
            bg='#3498db',
            fg='white',
            font=('Arial', 11, 'bold'),
            command=self._close_help,
            padx=20,
            pady=5
        )
        close_button.pack(pady=10)

    def _create_scrollable_help_text(self, parent):
        """Create scrollable text area with help content."""
        colors = get_theme_colors()

        # Frame for text widget and scrollbar
        text_frame = tk.Frame(parent, bg=colors['background'])
        text_frame.pack(fill='both', expand=True)

        # Text widget with scrollbar
        self.help_text = tk.Text(
            text_frame,
            wrap='word',
            bg='#f0f0f0',
            fg='#333333',
            font=('Arial', 11),
            padx=10,
            pady=10,
            relief='sunken',
            bd=1
        )

        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.help_text.yview)
        self.help_text.configure(yscrollcommand=scrollbar.set)

        # Pack text widget and scrollbar
        self.help_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Insert help content
        self._insert_help_content()

        # Make text read-only
        self.help_text.config(state='disabled')

    def _insert_help_content(self):
        """Insert comprehensive help content."""
        help_content = self._get_help_content()

        # Insert content with formatting
        self.help_text.insert('1.0', help_content)

        # Configure text tags for better formatting
        self._configure_text_formatting()

    def _configure_text_formatting(self):
        """Configure text formatting tags."""
        # Header styling
        self.help_text.tag_configure('header', font=('Arial', 14, 'bold'), foreground='#2c3e50')
        self.help_text.tag_configure('subheader', font=('Arial', 12, 'bold'), foreground='#34495e')
        self.help_text.tag_configure('bullet', font=('Arial', 11), foreground='#27ae60')
        self.help_text.tag_configure('important', font=('Arial', 11, 'bold'), foreground='#e74c3c')
        self.help_text.tag_configure('code', font=('Courier New', 10), background='#ecf0f1')

    def _get_help_content(self) -> str:
        """Get comprehensive help content."""
        return """DIC IMAGE QUALITY INSPECTOR - COMPREHENSIVE HELP GUIDE



📋 GETTING STARTED

• Loading Images:
  - Click "Load Image" to select an image file from your computer
  - Supported formats: PNG, JPEG, TIFF, BMP
  - Or use "Screenshot" to capture a region of your screen

• Basic Workflow:
  1. Load an image or take a screenshot
  2. Optionally select a Region of Interest (ROI)
  3. Click "Analyze" to process the image
  4. View results using "Show Results" button
  5. Export reports using "Export Report" button

• Analysis Parameters:
  - Select between Standard and ZEISS-style analysis methods
  - Adjust subset size and overlap based on your needs
  - Use color spectrum options to visualize quality maps



🎯 REGION OF INTEREST (ROI) SELECTION

• ROI Purpose:
  - Focus analysis on specific image areas
  - Reduce processing time for large images
  - Analyze only relevant regions for your DIC setup

• How to Select ROI:
  - Click "Select ROI" button
  - Left-click to start creating rectangle
  - Drag to define the region boundary
  - Right-click to complete selection
  - Clear existing ROI by clicking "Select ROI" again

• ROI Tips:
  - Select representative areas with good speckle patterns
  - Avoid edges and areas with poor lighting
  - Multiple ROI analyses can validate pattern consistency



📊 UNDERSTANDING RESULTS

• Overall Quality Score:
  - Score range: 0-100 (higher = better for DIC)
  - Excellent (80-100): Ideal for high-precision DIC
  - Good (60-79): Suitable for most DIC applications
  - Fair (40-59): May work with careful parameter selection
  - Poor (<40): Consider pattern improvement

• Quality Map Colors:
  - Hot colors (red/yellow): High quality areas
  - Cool colors (blue/green): Lower quality areas
  - Use different color spectrums for better visualization

• DIC Parameter Recommendations:
  - Subset size suggestions based on speckle characteristics
  - Overlap recommendations for measurement accuracy
  - Step size guidance for correlation analysis



⚙️ ANALYSIS METHODS

• Standard Analysis:
  - Fast processing suitable for most applications
  - Balanced between speed and accuracy
  - Good for initial pattern assessment

• ZEISS-style Analysis:
  - More detailed analysis with smaller steps
  - Higher accuracy but slower processing
  - Recommended for critical measurements
  - Mimics commercial DIC software analysis



🎨 COLOR SPECTRUM OPTIONS

• Optimized (Hot-Cold):
  - Custom spectrum designed for DIC quality visualization
  - Clear distinction between quality levels
  - Recommended for most users

• Viridis (Purple-Yellow):
  - Perceptually uniform color scale
  - Good for scientific publications
  - Color-blind friendly option

• Plasma (Purple-Pink):
  - High contrast visualization
  - Good for identifying subtle variations

• Jet (Blue-Red):
  - Traditional color scale
  - Familiar to many users
  - High dynamic range



💾 EXPORT AND REPORTING

• Report Formats:
  - Complete Package: Text report + images + original
  - Text Only: Detailed analysis results in text format

• Export Options:
  - Quality map overlay on original image
  - Raw quality map visualization
  - Multiple color spectrum options
  - Comprehensive text analysis

• File Organization:
  - All exports saved to timestamped folders
  - Package summary included for easy reference
  - Results compatible with documentation needs



TROUBLESHOOTING

• Image Loading Issues:
  - Ensure image format is supported (PNG, JPEG, TIFF, BMP)
  - Check file permissions and path
  - Try reducing image size if memory errors occur

• Analysis Problems:
  - Verify image has sufficient speckle pattern
  - Try different ROI selection if results seem inconsistent
  - Use Standard analysis for faster processing

• Display Issues:
  - If quality map doesn't appear, ensure analysis completed
  - Try different color spectrums for better visibility
  - Check that legend panel is enabled

• ROI Selection Problems:
  - Ensure you're left-clicking to start selection
  - Use right-clicking to complete
  - Clear existing ROI by clicking "Select ROI" again

• Image Display Problems:
  - Large images are automatically scaled for display
  - Use zoom and pan to examine details
  - "Reset" button returns to original view

• Analysis Performance:
  - Large images may take longer to process
  - ROI selection can speed up analysis
  - ZEISS-style analysis with small step sizes is slower

• Quality Map Visualization:
  - If quality map doesn't appear, ensure analysis completed successfully
  - Try different color spectrums if colors are hard to distinguish
  - Legend panel shows meaning of each color



BEST PRACTICES

• Image Preparation:
  - Ensure good lighting and focus before capture
  - Avoid reflections and shadows
  - Use appropriate speckle pattern density

• Pattern Assessment:
  - Look for random, non-repetitive patterns
  - Avoid regular geometric patterns
  - Ensure sufficient contrast between speckles

• Analysis Strategy:
  - Test multiple ROI regions for consistency
  - Compare results with different color spectrums
  - Save reports for documentation and comparison

• Parameter Selection:
  - Use recommended subset sizes from analysis
  - Consider larger subsets for lower quality patterns
  - Adjust overlap based on measurement requirements



🔬 TECHNICAL BACKGROUND

This tool analyzes digital image correlation (DIC) pattern quality by:

• Gradient Analysis: Evaluates edge content and sharpness
• Contrast Assessment: Measures local and global contrast
• Speckle Morphology: Analyzes pattern size and distribution
• Information Content: Calculates entropy and uniqueness
• Noise Evaluation: Estimates signal-to-noise ratio

The analysis provides scientifically-based recommendations for DIC correlation
parameters and expected measurement accuracy.



📞 SUPPORT

For additional support or feature requests:
• Check the application documentation
• Review published research on DIC pattern quality
• Consult DIC software manuals for correlation parameters

Version: 2.0.0 - Clean Architecture Implementation

"""

    def _close_help(self):
        """Close the help dialog."""
        if self.help_window:
            self.help_window.destroy()
            self.help_window = None

    def _center_window(self):
        """Center the help window on the parent."""
        if not self.help_window:
            return

        # Update window to get accurate dimensions
        self.help_window.update_idletasks()

        # Get window dimensions
        window_width = self.help_window.winfo_width()
        window_height = self.help_window.winfo_height()

        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Calculate center position
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        # Ensure window is not off-screen
        x = max(0, x)
        y = max(0, y)

        # Set window position
        self.help_window.geometry(f"+{x}+{y}")

    def is_open(self) -> bool:
        """Check if help dialog is currently open."""
        return self.help_window is not None and self.help_window.winfo_exists()

    def bring_to_front(self):
        """Bring help dialog to front if it's open."""
        if self.is_open():
            self.help_window.lift()
            self.help_window.focus_set()