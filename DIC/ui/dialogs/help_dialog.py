"""
Help dialog for DIC Image Quality Inspector.

This module provides a comprehensive help dialog displaying detailed usage
instructions, feature explanations, and troubleshooting guidance. Content is
organised into topic tabs using ttk.Notebook for quick navigation.

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

    Shows comprehensive help information in a tabbed dialog.
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
            height=620,
            resizable=True,
            topmost=False,
            center=True
        )

        colors = get_theme_colors()
        self.help_window.configure(bg=colors['background'])
        self.help_window.grab_set()
        self.help_window.minsize(600, 500)

    def _create_help_content(self):
        """Create the help content with tabbed notebook."""
        colors = get_theme_colors()

        main_frame = tk.Frame(self.help_window, bg=colors['background'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Title
        tk.Label(
            main_frame,
            text="DIC Image Quality Inspector - Help Guide",
            font=APP_CONFIG['fonts']['title'],
            fg=colors['text_primary'],
            bg=colors['background']
        ).pack(pady=(0, 12))

        # Notebook
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)

        self._add_tab(notebook, "Getting Started", self._text_getting_started())
        self._add_tab(notebook, "Workflow",        self._text_workflow())
        self._add_tab(notebook, "Reading Results", self._text_reading_results())
        self._add_tab(notebook, "Quality Map",     self._text_quality_map())
        self._add_tab(notebook, "DIC Parameters",  self._text_dic_parameters())
        self._add_tab(notebook, "Definitions",     self._text_definitions())
        self._add_tab(notebook, "Troubleshooting", self._text_troubleshooting())

        # Close button
        tk.Button(
            main_frame,
            text="Close",
            bg='#3498db',
            fg='white',
            font=('Arial', 11, 'bold'),
            command=self._close_help,
            padx=20,
            pady=5
        ).pack(pady=10)

    def _add_tab(self, notebook: ttk.Notebook, title: str, content: str):
        """Add a scrollable read-only text tab to the notebook."""
        colors = get_theme_colors()

        frame = tk.Frame(notebook, bg=colors['background'])
        notebook.add(frame, text=title)

        text = tk.Text(
            frame,
            wrap='word',
            bg='#f7f7f7',
            fg='#222222',
            font=('Arial', 11),
            padx=12,
            pady=12,
            relief='flat',
            bd=0
        )
        scroll = ttk.Scrollbar(frame, orient='vertical', command=text.yview)
        text.configure(yscrollcommand=scroll.set)

        text.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

        text.tag_configure('header', font=('Arial', 13, 'bold'), foreground='#2c3e50')
        text.tag_configure('subheader', font=('Arial', 11, 'bold'), foreground='#34495e')

        # Insert content: lines starting with "##" get header tag, "#" get subheader
        for line in content.split('\n'):
            if line.startswith('## '):
                text.insert('end', line[3:] + '\n', 'header')
            elif line.startswith('# '):
                text.insert('end', line[2:] + '\n', 'subheader')
            else:
                text.insert('end', line + '\n')

        text.config(state='disabled')

    # ------------------------------------------------------------------
    # Tab content
    # ------------------------------------------------------------------

    def _text_getting_started(self) -> str:
        return """\
## Getting Started

# Loading Images

  - Click "Load Image" to open a file from disk.
  - Supported formats: PNG, JPEG, TIFF, BMP.
  - Use "Screenshot" to capture any region of your screen (multi-monitor supported).
  - Use "SpinView Camera Capture" (Windows) to grab directly from a live camera feed.

# Supported Workflows

  - Static image analysis: load file -> (optional ROI) -> Analyze -> review results.
  - Live camera analysis: SpinView capture with real-time quality tracking.
  - Screenshot mode: analyze a camera view without direct SDK integration.

# Interface at a Glance

  - Left panel: load/ROI/analyze/export controls.
  - Top bar: zoom, metric map selector, color spectrum, theme toggle.
  - Center: image canvas with quality map overlay and floating legend.
  - Bottom: status bar with progress indicator.
"""

    def _text_workflow(self) -> str:
        return """\
## Recommended Workflow

1. Load Image
   Click "Load Image" (or Screenshot / SpinView) and select your image.

2. Select Region of Interest (optional but recommended)
   Click "Select ROI" and left-click to place polygon vertices.
   Press Enter to close the polygon.
   Focusing on the speckled gauge section gives more accurate results
   than including fixture hardware or background.

3. Analyze
   Click "Analyze". A progress bar shows the map generation and scoring steps.
   Analysis runs on a background thread — the UI stays responsive.

4. View Quality Map
   The colored overlay appears automatically. Toggle between Overall, Gradient,
   Contrast, Entropy, Pattern, and Noise maps using the buttons in the top bar.

5. Show Results
   Click "Show Results" for the full popup:
     - Headline score (weighted 5-component sum)
     - Score Breakdown table
     - Improvement Feedback
     - Recommended DIC parameters

6. Export Report
   Click "Export Report" to write a text report to disk. The report includes
   the Score Breakdown, corrected math, and DIC parameter recommendations.

# Parameter Adjustments

  - Subset Size (11-51 px): larger = more stable but lower spatial resolution.
  - Step Size (1-8 px): smaller = denser map but slower.
  - Color Spectrum: "Optimized DIC" is recommended; Viridis/Jet for alternative views.
"""

    def _text_reading_results(self) -> str:
        return """\
## Reading the Results Popup

# Headline Score

  The large number at the top is the Overall Quality Score (0-100).
  This is the ONLY score that matters — it equals the sum of the five
  weighted component contributions shown in the Score Breakdown below it.

# Score Breakdown

  Each row shows one component:

    Component  — Weight % of total score
    Score/100  — How well the image performs on that metric (0-100)
    Contributes X pts — score × weight (these five sum to the headline)

  The bottom line "Sum of weighted contributions = X / 100" confirms that
  the five rows add up to the headline exactly.

# Improvement Feedback

  Components below 60 are flagged with specific advice:
    "Needs work" (40-59) — orange label with targeted tip.
    "Poor" (<40)         — red label with higher-priority advice.

  The strongest component is also highlighted as a positive reinforcement.

# DIC Parameter Recommendations

  Based on the headline score and image characteristics:
    - Subset Size: correlation window in pixels.
    - Step Size: spacing between subsets.
    - Overlap %: typically 75%.
    - Expected Accuracy: displacement precision estimate.

# Band Thresholds (Optimized spectrum)

  75-100: Excellent     — green
  60-75:  Very Good     — cyan
  45-60:  Good          — yellow
  30-45:  Acceptable    — orange
  15-30:  Challenging   — dark red
  0-15:   Poor          — black
"""

    def _text_quality_map(self) -> str:
        return """\
## Quality Map

# What the Colors Mean (Optimized DIC spectrum)

  Green       — Excellent (75-100): ideal for DIC, high gradient and contrast.
  Cyan        — Very Good (60-75): reliable correlation expected.
  Yellow      — Good (45-60): suitable for most measurements.
  Orange      — Acceptable (30-45): usable with care, consider larger subsets.
  Dark Red    — Challenging (15-30): poor correlation likely, improve pattern.
  Black       — Poor (0-15): not suitable; region will fail to correlate.

  The map colors and the Score Breakdown numbers are computed with IDENTICAL
  math since Task 2 was applied. A region shown in yellow on the map will
  also score ~45-60 in the per-component breakdown for that metric.

# Metric Map Buttons

  Overall — weighted combination of all five components.
  Gradient — sharpness / edge content of each subset.
  Contrast — light-vs-dark spread.
  Entropy  — information / randomness of the pattern.
  Pattern  — speckle size and coverage quality.
  Noise    — SNR-based resistance to sensor noise.

  Toggle between maps to pinpoint which component is weakest spatially.
  Look for dark areas in one map while the overall map looks fine — those
  are localized weaknesses worth investigating.

# Legend Panel

  The floating legend shows the color-to-quality mapping for the active map.
  Bands match the thresholds in "Reading Results".

# Tips

  - Focus measurements on high-quality (green/cyan) regions.
  - Avoid placing strain gauges or extensometers in red/black areas.
  - Uniform color across the map = consistent speckle application.
"""

    def _text_dic_parameters(self) -> str:
        return """\
## DIC Parameters

# Subset (Facet) Size

  The small window the DIC algorithm tracks between images.
  - Recommended range: 11-51 pixels.
  - Larger subset = more stable correlation, but lower spatial resolution.
  - Rule of thumb: subset should contain 3-5 speckles on average.
  - The app estimates optimal size from speckle diameter.

# Step Size

  Spacing between consecutive subset centers.
  - Small step = denser displacement field, slower computation.
  - Typical: step = subset_size × (1 - overlap_fraction).
  - Default 75% overlap → step = subset_size / 4.

# Overlap

  Percentage of adjacent subsets that share pixels.
  - 75% overlap is the standard starting point.
  - Higher overlap = smoother displacement field.
  - Lower overlap = faster computation.

# Expected Accuracy

  Estimated displacement measurement precision based on quality score:
  - Score ≥ 90: ±0.005-0.01 pixels
  - Score ≥ 75: ±0.01-0.02 pixels
  - Score ≥ 60: ±0.02-0.05 pixels
  - Score ≥ 45: ±0.05-0.1 pixels
  - Score < 45: ±0.1+ pixels (use with extreme caution)

# Adjusting Parameters

  If correlation quality is poor after analysis:
  1. Increase subset size by 30-50%.
  2. Verify step ≤ subset/2 (at least 50% overlap).
  3. Apply stricter correlation coefficient threshold in your DIC software.
"""

    def _text_definitions(self) -> str:
        return """\
## Definitions

# DIC — Digital Image Correlation

  A full-field optical measurement technique that tracks a random speckle
  pattern painted on a specimen's surface. By comparing images before and
  after deformation, it computes displacement and strain fields without
  contact. Pattern quality directly determines measurement accuracy — a
  poor pattern means poor measurements regardless of DIC software used.

# Subset / Facet

  A small rectangular window (e.g. 21×21 px) that the DIC algorithm tracks
  from the reference image to each deformed image. Larger subsets are more
  stable (more pixels = better statistics) but reduce spatial resolution.

# Step Size / Overlap

  Step is the pixel distance between adjacent subset centers. Overlap =
  1 - (step / subset_size). The default 75% overlap means each step is
  1/4 of the subset width, producing a dense displacement grid.

# The Five Components and Their Weights
  (keep in sync with QualityCalculator.__init__)

  Gradient  40%
    Measures how sharp and edgy the pattern is — the single biggest driver
    of DIC accuracy. Computed via MIG and Ef (see below). High gradient means
    the correlation peak is narrow and precise.

  Contrast  25%
    Light-vs-dark separation across the image. Combines RMS, Michelson, and
    Weber contrast measures. Too flat (low contrast) = nothing to track.
    Over-exposure that washes out speckles hurts contrast severely.

  Entropy   20%
    Shannon information content of the intensity histogram. Higher entropy =
    more unique local patterns = better subset identifiability. Repetitive
    or very regular speckle patterns score low on entropy.

  Pattern   10%
    Evaluates speckle size and coverage using connected-component analysis.
    Ideal speckles are a few pixels across (3-5 px diameter) with good
    density (50-5000 speckles per million pixels). Too large or too small
    speckles reduce this score.

  Noise      5%
    SNR-based resistance to sensor noise. Computed by comparing the raw
    image to a bilaterally-filtered version. High sensor gain / ISO or
    out-of-focus images lower this score.

# MIG — Mean Intensity Gradient (Pan et al. 2009)

  MIG = (1/N) × Σ |∇I(x,y)|   (average gradient magnitude over all pixels)

  Higher MIG → sharper speckle edges → more trackable detail.
  Normalisation: MIG_score = min(1.0, (MIG / 50) × 2.0)
  (normalization_factor=50, score_multiplier=2.0 in QualityCalculator)

# Ef — Enhanced Feature (Hu et al. 2021)

  Ef = 0.7 × MIG + 0.3 × mean|∇²I|

  Combines first-order (MIG) and second-order gradients. The Laplacian term
  captures curvature detail that MIG misses (e.g. speckle interiors with
  curved edges). Scored as: Ef_score = min(1.0, (Ef / 40) × 1.2)
  (normalization_factor=40, score_multiplier=1.2 in QualityCalculator)

  Q_gradient = (Ef_score × 0.8 + MIG_score × 0.2) × distribution_bonus

# Distribution Bonus

  A multiplier (≥1.0) that rewards gradient energy spread uniformly across
  the whole ROI rather than concentrated in a few bright spots. A speckle
  pattern with uniform coverage scores higher than an equivalent pattern
  with hot-spots.

# RMS / Michelson / Weber Contrast

  RMS contrast:      C_rms = σ / μ   (std / mean intensity)
  Michelson:         C_m   = (I_max - I_min) / (I_max + I_min)
  Weber:             C_w   = (I_max - μ) / μ

  Combined: 0.4×C_rms + 0.3×C_m + 0.2×C_w + 0.1×C_local

# SNR — Signal-to-Noise Ratio (dB)

  SNR = signal_std / noise_std   (noise estimated via bilateral filtering)
  SNR_dB = 20 × log10(SNR)
  Noise score = min(1.0, SNR_dB / 30)

  A good speckle image typically has SNR_dB > 20 dB (score > 0.67).

# Overall Score

  The headline score is the sum of the five weighted contributions:

    Q_total = 0.40×Q_gradient + 0.25×Q_contrast + 0.20×Q_entropy
            + 0.10×Q_pattern + 0.05×Q_noise

  Each Q is on 0-100 scale. The five "Contributes X pts" values in the
  Score Breakdown sum exactly to this number.
"""

    def _text_troubleshooting(self) -> str:
        return """\
## Troubleshooting

# Score Inconsistency

  If the headline score and the "Sum of weighted contributions" line in the
  popup differ by more than 0.2 pts, re-run the analysis — the breakdown
  path may have failed silently. Check the log for warnings.

# Dark Red Map Despite Decent Score

  Before the fix (Tasks 1-2), fast per-subset functions systematically scored
  lower than the full functions used for the breakdown. After applying the
  fix, the map uses the same full functions. If you still see dark red:
  - The component really is low for those subsets.
  - Open the Noise or Entropy map to identify which component is pulling the
    color down spatially.

# ROI Selection Issues

  - Left-click to place polygon vertices.
  - Press Enter to close the polygon (need ≥ 3 points).
  - Hold Ctrl for enhanced mode (auto-closes when Ctrl is released).
  - "New ROI" clears the current selection.

# Analysis Performance

  - Use ROI to limit the region — smaller area = faster analysis.
  - Large images (>1500 px) are automatically downscaled for map generation.
  - If analysis takes too long, increase step size (lower map density).

# Low Gradient Score

  - Speckles have soft edges or are too large.
  - Use finer airbrush nozzle or higher-contrast paint.
  - Check that the image is in sharp focus.

# Low Contrast Score

  - Use true matte black on matte white paint (avoid gloss).
  - Check for lighting glare or over-exposure washout.
  - Histogram should span most of 0-255 range.

# Low Entropy Score

  - Pattern is too repetitive or regular.
  - Increase randomness in speckle application.
  - Avoid stamping or stencil methods that create periodic patterns.

# Low Noise Score

  - Reduce ISO/gain on the camera.
  - Improve lighting to allow shorter exposure without high gain.
  - Ensure the specimen is in focus.

# Image Loading Problems

  - Supported formats: PNG, JPEG, TIFF, BMP.
  - Check file permissions.
  - Try reducing image size if memory errors occur.

# Camera Capture (SpinView, Windows only)

  - Verify SpinView is running and the camera feed is visible.
  - Ensure proper region selection before capturing.
  - Switch to "Balanced" or "Accurate" performance mode for better quality.
"""

    # ------------------------------------------------------------------

    def _close_help(self):
        """Close the help dialog."""
        if self.help_window:
            self.help_window.destroy()
            self.help_window = None

    def _center_window(self):
        """Center the help window on the parent."""
        if not self.help_window:
            return

        self.help_window.update_idletasks()

        window_width = self.help_window.winfo_width()
        window_height = self.help_window.winfo_height()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        x = max(0, x)
        y = max(0, y)

        self.help_window.geometry(f"+{x}+{y}")

    def is_open(self) -> bool:
        """Check if help dialog is currently open."""
        return self.help_window is not None and self.help_window.winfo_exists()

    def bring_to_front(self):
        """Bring help dialog to front if it's open."""
        if self.is_open():
            self.help_window.lift()
            self.help_window.focus_set()
