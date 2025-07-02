# ui/dialogs/help_dialog.py - Help Information Dialog

import tkinter as tk
from tkinter import ttk
from utils.constants import APP_CONFIG


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
        self.help_window = tk.Toplevel(self.parent)
        self.help_window.title("DIC Image Quality Inspector - Help")
        self.help_window.geometry("700x600")
        self.help_window.configure(bg=APP_CONFIG['colors']['background'])
        self.help_window.transient(self.parent)
        self.help_window.grab_set()

        # Make resizable
        self.help_window.resizable(True, True)
        self.help_window.minsize(600, 500)

    def _create_help_content(self):
        """Create the help content."""
        # Main container
        main_frame = tk.Frame(self.help_window, bg=APP_CONFIG['colors']['background'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Title
        title_label = tk.Label(
            main_frame,
            text="🔍 DIC Image Quality Inspector - Help Guide",
            font=APP_CONFIG['fonts']['title'],
            fg=APP_CONFIG['colors']['text_primary'],
            bg=APP_CONFIG['colors']['background']
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
        # Frame for text widget and scrollbar
        text_frame = tk.Frame(parent, bg=APP_CONFIG['colors']['background'])
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

═══════════════════════════════════════════════════════════════════════════════

🚀 GETTING STARTED

• Loading Images:
  - Click "Load Image" to select an image file from your computer
  - Supported formats: PNG, JPEG, TIFF, BMP
  - Or use "Screenshot" to capture a region of your screen

• Basic Workflow:
  1. Load an image or take a screenshot
  2. Optionally select a Region of Interest (ROI)
  3. Click "Analyze" to process the image
  4. View results using "Show Results" button
  5. Save comprehensive report if needed

═══════════════════════════════════════════════════════════════════════════════

🎯 REGION OF INTEREST (ROI) SELECTION

• Starting ROI Selection:
  - Click "Select ROI" button to enter selection mode
  - Cursor changes to crosshair when active

• Creating ROI Polygon:
  - Left-click to add points to your polygon
  - Move mouse to see preview line to next point
  - Need minimum 3 points for a valid polygon
  - Right-click to complete the polygon selection

• ROI Benefits:
  - Focus analysis on specific area of interest
  - Reduce processing time for large images
  - Get targeted quality assessment

• Tips:
  - Select areas with representative speckle patterns
  - Avoid edges and boundaries of specimens
  - Ensure ROI contains sufficient pattern detail

═══════════════════════════════════════════════════════════════════════════════

🖼️ IMAGE NAVIGATION & VIEWING

• Zoom Controls:
  - Mouse wheel: Zoom in/out at cursor position
  - Supports zoom levels from 10% to 500%

• Panning:
  - Hold Ctrl + Left-click and drag to pan around image
  - Essential for navigating large, zoomed images

• View Options:
  - "Original": Show unprocessed image
  - "Edges": Display edge detection visualization
  - "Gradient": Show gradient magnitude analysis
  - "Reset": Return to default view and clear all selections

• Quality Map Display:
  - "Quality Map" button toggles color overlay showing analysis results
  - Different color schemes available via dropdown menu

═══════════════════════════════════════════════════════════════════════════════

🔬 ANALYSIS & QUALITY ASSESSMENT

• Analysis Process:
  - Examines speckle pattern quality across the image
  - Evaluates gradient content, contrast, and pattern characteristics
  - Generates recommended DIC correlation parameters

• Quality Metrics:
  - Overall Score: 0-100 scale indicating DIC suitability
  - Color-coded quality map showing spatial variation
  - Detailed statistics including min/max/average quality

• Methods Options:
  - Custom DIC: Strict assessment for DIC applications only
  - ZEISS-Style: Professional pattern quality evaluation

• Understanding Scores:
  - 90-100: Excellent - Perfect for precision DIC
  - 75-90: Very Good - Suitable for most DIC applications
  - 60-75: Good - Acceptable with proper parameters
  - 45-60: Marginal - Use with caution
  - Below 45: Poor - Consider pattern improvement

═══════════════════════════════════════════════════════════════════════════════

⚙️ ADVANCED FEATURES

• Controlled Method Analysis:
  - Select "controlled" spectrum for professional assessment
  - Adjust Facet Size (11-51 pixels) and Step Size (2-20 pixels)
  - Higher density analysis with smaller step sizes

• Report Generation:
  - "Show Results": Detailed popup with comprehensive analysis
  - "Save Report": Export complete technical report to text file
  - Includes mathematical background, recommendations, and parameters

• Quality Map Features:
  - Dynamic legend shows color coding for current spectrum
  - Toggle quality map on/off to compare with original
  - Legend updates automatically when changing spectrums

═══════════════════════════════════════════════════════════════════════════════

📊 INTERPRETING RESULTS

• Executive Summary:
  - Large score display with color-coded assessment
  - Clear recommendation: Proceed, Caution, or Improve

• Technical Analysis:
  - Statistical distribution of quality across image
  - Min/Max/Average/Median quality values
  - Standard deviation indicating quality consistency

• DIC Parameters:
  - Recommended subset (facet) size for correlation
  - Optimal step size for point spacing
  - Expected measurement accuracy based on pattern quality

• Recommendations:
  - Specific guidance based on your quality score
  - Suggestions for improving pattern if needed
  - Parameter adjustments for optimal results

═══════════════════════════════════════════════════════════════════════════════

🔧 TROUBLESHOOTING

• ROI Selection Issues:
  - If ROI appears offset, try resetting view first
  - Ensure at least 3 points before right-clicking to complete
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

═══════════════════════════════════════════════════════════════════════════════

💡 BEST PRACTICES

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

═══════════════════════════════════════════════════════════════════════════════

📚 TECHNICAL BACKGROUND

This tool analyzes digital image correlation (DIC) pattern quality by:

• Gradient Analysis: Evaluates edge content and sharpness
• Contrast Assessment: Measures local and global contrast
• Speckle Morphology: Analyzes pattern size and distribution
• Information Content: Calculates entropy and uniqueness
• Noise Evaluation: Estimates signal-to-noise ratio

The analysis provides scientifically-based recommendations for DIC correlation
parameters and expected measurement accuracy.

═══════════════════════════════════════════════════════════════════════════════

🆘 SUPPORT

For additional support or feature requests:
• Check the application documentation
• Review published research on DIC pattern quality
• Consult DIC software manuals for correlation parameters

Version: 2.0.0 - Clean Architecture Implementation

═══════════════════════════════════════════════════════════════════════════════"""

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