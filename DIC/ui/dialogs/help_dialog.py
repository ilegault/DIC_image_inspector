"""
Help dialog for DIC Image Quality Inspector.

This module provides a comprehensive help dialog displaying detailed usage
instructions, feature explanations, and troubleshooting guidance. It presents
information in a scrollable, formatted text area with proper theming support.

Usage:
    from ui.dialogs.help_dialog import HelpDialog

    help_dialog = HelpDialog(parent_window)
    help_dialog.show()
"""

import tkinter as tk
from tkinter import ttk
from DIC.utils.constants import APP_CONFIG, get_theme_colors
from DIC.utils.window_utils import WindowManager


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
      - Adjust subset size (11-51 pixels) and step size (1-8 pixels)
      - Choose between different color spectrums for visualization
      - Use zoom controls for detailed examination



    🎯 REGION OF INTEREST (ROI) SELECTION

    • ROI Purpose:
      - Focus analysis on specific image areas
      - Reduce processing time for large images
      - Analyze only relevant regions for your DIC setup

    • How to Select ROI:
      - Click "Select ROI" button
      - Left-click to add points to your polygon
      - Move mouse to see preview line to next point
      - Need minimum 3 points for a valid polygon
      - Press Enter to complete the polygon selection

    • Advanced ROI Features:
      - Hold Ctrl key for enhanced ROI selection mode (auto-completes when Ctrl released)
      - ROI information displayed in control panel
      - Multiple ROI analyses can validate pattern consistency
      - Right-click is used for panning, not ROI completion



    🖥️ USER INTERFACE OVERVIEW

    • Control Panel (Left Side):
      - Image Loading: Load Image, Screenshot buttons
      - ROI Selection: Select ROI, New ROI options
      - Analysis: Analyze button with parameter controls
      - Results: Quality Map, Show Results buttons
      - Export: Export Report with multiple format options
      - System: Reset Display, Reset Application, Help
      - Camera: SpinView Camera Capture (Windows only)

    • Top Navigation Bar:
      - Zoom Controls: Zoom In, Zoom Out, Zoom to Actual Size
      - Color Spectrum: Choose visualization method
      - Theme Toggle: Switch between dark and light themes

    • Image Display Area:
      - Main image viewing with zoom and pan support
      - Quality map overlay visualization
      - ROI selection and editing
      - Legend panel for color spectrum interpretation

    • Status Bar:
      - Current operation status and progress updates
      - Error messages and completion notifications



    📊 ANALYSIS FEATURES

    • DIC Quality Analysis:
      - Gradient Analysis: Evaluates edge content and sharpness
      - Contrast Assessment: Measures local and global contrast
      - Speckle Morphology: Analyzes pattern size and distribution
      - Information Content: Calculates entropy and uniqueness
      - Noise Evaluation: Estimates signal-to-noise ratio

    • Parameter Controls:
      - Subset Size: 11-51 pixels (affects analysis precision)
      - Step Size: 1-8 pixels (affects processing speed and resolution)
      - Automatic parameter optimization based on pattern characteristics

    • Performance Optimization:
      - ROI selection for faster processing
      - Optimized algorithms for large images
      - Progress tracking during analysis



    🎨 VISUALIZATION OPTIONS

    • Color Spectrums Available:
      - Optimized DIC: Custom spectrum designed for DIC quality visualization
      - Viridis: Perceptually uniform, color-blind friendly
      - Plasma: High contrast for identifying subtle variations
      - Jet: Traditional blue-to-red color scale

    • Quality Map Features:
      - Toggle quality map overlay on/off
      - Interactive legend panel with color meanings
      - Adjustable transparency and visualization options
      - Hot colors (red/yellow) = High quality areas
      - Cool colors (blue/green) = Lower quality areas



    📈 UNDERSTANDING RESULTS

    • Overall Quality Score:
      - Score range: 0-100 (higher = better for DIC)
      - 90-100: Excellent - Ideal for high-precision DIC
      - 75-89: Very Good - Good for DIC applications
      - 60-74: Good - Suitable for most DIC applications
      - 45-59: Fair - May work with careful parameter selection
      - 30-44: Challenging - Consider pattern improvement
      - 0-29: Poor - Not suitable for reliable DIC

    • DIC Parameter Recommendations:
      - Optimized subset size based on speckle characteristics
      - Step size recommendations for measurement accuracy
      - Expected displacement accuracy estimates
      - Overlap ratio suggestions for correlation analysis

    • Quality Map Interpretation:
      - Spatial distribution of DIC suitability across image
      - Identify best regions for measurement placement
      - Avoid poor quality areas for critical measurements
      - Use legend panel to understand color meanings



    💾 EXPORT AND REPORTING

    • Export Report Options:
      - Complete Package: Text report + images + original + summary
      - Text Only: Detailed analysis results in text format

    • Export File Contents:
      - Comprehensive text analysis report with statistics
      - Original image for reference and documentation
      - Quality map overlay visualization with chosen spectrum
      - Package summary with usage notes and interpretation
      - Timestamped folders for easy organization

    • Report Information Includes:
      - Overall quality score and interpretation
      - DIC parameter recommendations (subset size, step size)
      - Technical analysis details and metrics
      - Image information and ROI details
      - Quality assessment criteria and thresholds



    🔧 DISPLAY AND NAVIGATION CONTROLS

    • Zoom Controls:
      - Zoom In/Out: Examine image details at different scales
      - Zoom to Actual Size: View image at 100% scale
      - Mouse wheel scrolling for smooth zoom adjustment
      - Pan functionality for navigating large images

    • View Controls:
      - Reset Display: Clear overlays and return to original view
      - Quality Map Toggle: Show/hide quality visualization
      - Theme Toggle: Switch between dark and light interface themes
      - ROI visibility controls integrated with selection tools

    • Window Management:
      - Resizable interface with responsive layout
      - Floating legend panel with quality interpretation
      - Context-sensitive status updates
      - Multi-monitor support for screenshot capture



    📷 SCREENSHOT AND CAMERA FEATURES

    • Screenshot Capture:
      - Full screen or region-based capture
      - Multi-monitor support for complex setups
      - Interactive selection with visual feedback
      - Automatic window hiding during capture

    • SpinView Camera Capture (Windows only):
      - Real-time camera feed analysis
      - Region selection for focused monitoring
      - Performance mode options: Fast, Balanced, Accurate
      - Live quality assessment with historical tracking
      - Rectangle and polygon region selection modes

    • Capture Tips:
      - Ensure good lighting and focus before capture
      - Avoid reflections and shadows in camera feeds
      - Use appropriate region selection for optimal analysis
      - Consider lighting consistency for reliable results



    🛠️ TROUBLESHOOTING

    • Common Issues and Solutions:

      Image Loading Problems:
      - Check file format (PNG, JPEG, TIFF, BMP supported)
      - Verify file permissions and path accessibility
      - Try reducing image size if memory errors occur

      ROI Selection Issues:
      - Ensure left-clicking to start selection
      - Use right-clicking to complete ROI definition
      - Clear existing ROI by clicking "New ROI"
      - Hold Ctrl key for enhanced selection mode

      Analysis Performance:
      - Use ROI selection to focus on specific regions
      - Adjust step size to balance speed vs. resolution
      - Monitor progress in status bar during analysis

      Quality Map Display:
      - Ensure analysis completed successfully before viewing
      - Try different color spectrums for better visibility
      - Check that legend panel is enabled and visible
      - Use Reset Display to clear any display issues

      Camera Capture (Windows):
      - Verify SpinView application is running
      - Check camera feed visibility and positioning
      - Ensure proper region selection before analysis
      - Monitor performance mode for optimal results



    💡 BEST PRACTICES

    • Image Preparation:
      - Ensure good lighting and focus before capture
      - Avoid reflections, shadows, and glare
      - Use appropriate speckle pattern density for DIC
      - Maintain consistent illumination across the image

    • Pattern Assessment:
      - Look for random, non-repetitive speckle patterns
      - Avoid regular geometric patterns or periodic structures
      - Ensure sufficient contrast between speckles and background
      - Test multiple ROI regions for pattern consistency

    • Analysis Strategy:
      - Start with full image analysis, then use ROI for detail
      - Compare results with different color spectrums
      - Save reports for documentation and comparison
      - Use recommended parameters from analysis results

    • Parameter Selection:
      - Use larger subset sizes for lower quality patterns
      - Adjust step size based on measurement requirements
      - Consider processing time vs. accuracy trade-offs
      - Follow automated recommendations when available

    • Results Interpretation:
      - Focus measurements on high-quality regions (warm colors)
      - Avoid critical measurements in poor-quality areas
      - Use quality scores to validate pattern suitability
      - Document analysis settings for reproducible results



    ⚙️ ADVANCED FEATURES

    • Keyboard Shortcuts:
      - Ctrl + Hold: Enhanced ROI selection mode
      - Mouse wheel: Zoom in/out on image
      - Right-click: Complete ROI selection
      - Left-click + drag: Create ROI rectangle

    • Theme Support:
      - Dark and light themes for different preferences
      - Automatic color scheme adaptation
      - Consistent styling across all interface elements
      - Theme persistence between application sessions

    • Technical Features:
      - Multi-threading for responsive user interface
      - DPI awareness for consistent display scaling
      - Robust error handling and recovery mechanisms
      - Modern clean architecture for reliability

    • Integration Capabilities:
      - Compatible export formats for documentation
      - Timestamped file organization for project management
      - Comprehensive logging for troubleshooting
      - Extensible design for future enhancements



    🔬 TECHNICAL BACKGROUND

    This tool analyzes digital image correlation (DIC) pattern quality by evaluating:

    • Gradient Analysis: Edge content and sharpness assessment
    • Contrast Evaluation: Local and global contrast measurement
    • Speckle Morphology: Pattern size and distribution analysis
    • Information Content: Entropy and uniqueness calculation
    • Noise Assessment: Signal-to-noise ratio estimation

    The analysis provides scientifically-based recommendations for DIC correlation
    parameters and expected measurement accuracy. Quality scores are calculated
    using established metrics from DIC research literature.

    DIC Parameter Calculations:
    • Subset size optimization based on speckle characteristics
    • Step size recommendations for desired overlap ratios
    • Expected displacement accuracy estimates
    • Pattern quality thresholds for reliable correlation



    📞 SUPPORT AND RESOURCES

    For additional support:
    • Review the comprehensive analysis reports generated by the tool
    • Consult published research on DIC pattern quality assessment
    • Check DIC software manuals for correlation parameter guidance
    • Use the export features to document and share analysis results

    Version: 2.0.0 - Clean Architecture Implementation
    Last Updated: 2025

    This application provides professional-grade DIC pattern quality assessment
    with comprehensive analysis capabilities and user-friendly visualization tools.

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