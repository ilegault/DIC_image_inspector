#!/usr/bin/env python3
"""
SpinView Camera Capture Mode for DIC Quality Analysis.

This integrates SpinView camera capture functionality into the main DIC application,
providing live analysis with proper DIC quality assessment and score visualization.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import cv2
import time
import threading
from PIL import Image, ImageGrab, ImageTk
import logging
import platform
import json
import os
from typing import Optional, Tuple, List, Callable, Dict, Any
from collections import deque

# Windows-specific imports
if platform.system() == 'Windows':
    import win32gui
    import win32ui
    import win32con
    import win32api
    from ctypes import windll

from models.roi_data import ROIData
from models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)


class SpinViewCaptureMode:
    """Enhanced SpinView capture mode integrated with main DIC analyzer."""

    def __init__(self, main_app):
        """Initialize SpinView capture mode."""
        self.main_app = main_app
        self.root = main_app.root
        
        # Get the main analyzer from the app
        self.analyzer = main_app.analyzer
        
        # SpinView capture state
        self.spinview_hwnd = None
        self.camera_region = None  # (x, y, width, height) or ('polygon', points)
        
        # Analysis state
        self.is_analyzing = False
        self.analysis_thread = None
        self.analysis_history = deque(maxlen=1000)  # Store more history for graphs
        self.current_score = 0.0
        self.current_quality_map = None
        
        # Performance tracking
        self.frame_times = deque(maxlen=50)
        self.analysis_times = deque(maxlen=50)
        
        # UI components
        self.capture_window = None
        self.results_window = None
        
        logger.info("SpinViewCaptureMode initialized")

    def _get_colors(self):
        """Get theme colors with fallback."""
        try:
            from utils.constants import get_theme_colors
            return get_theme_colors()
        except ImportError:
            return {
                'background': '#f0f0f0',
                'panel_bg': '#ffffff',
                'canvas_bg': '#ffffff',
                'text_primary': '#000000',
                'text_secondary': '#666666',
                'selected_bg': '#0078d4'
            }

    def show_capture_interface(self):
        """Show the SpinView capture interface."""
        if self.capture_window:
            self.capture_window.lift()
            return
            
        self._create_capture_window()

    def _create_capture_window(self):
        """Create the main capture interface window."""
        self.capture_window = tk.Toplevel(self.root)
        self.capture_window.title("SpinView Camera DIC Quality Analyzer")
        self.capture_window.geometry("1000x700")
        self.capture_window.protocol("WM_DELETE_WINDOW", self._on_capture_window_close)
        
        # Apply theme
        colors = self._get_colors()
        self.capture_window.configure(bg=colors['background'])
        
        self._create_capture_ui()
        
        # Initial window refresh
        self._refresh_windows()

    def _create_capture_ui(self):
        """Create the capture UI."""
        colors = self._get_colors()
        
        # Header
        header = tk.Frame(self.capture_window, bg='#1abc9c', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🔬 SpinView DIC Quality Analyzer",
            font=('Arial', 20, 'bold'),
            bg='#1abc9c',
            fg='white'
        ).pack(expand=True)

        # Main container
        main_container = tk.Frame(self.capture_window, bg=colors['background'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Left panel - Controls
        left_panel = tk.Frame(main_container, width=350, bg=colors['panel_bg'])
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)

        self._create_window_selection_panel(left_panel)
        self._create_region_selection_panel(left_panel)
        self._create_analysis_control_panel(left_panel)
        self._create_legend_panel(left_panel)

        # Right panel - Displays
        right_panel = tk.Frame(main_container, bg=colors['panel_bg'])
        right_panel.pack(side='right', fill='both', expand=True)

        self._create_display_panels(right_panel)

        # Status bar
        self._create_status_bar()

    def _create_window_selection_panel(self, parent):
        """Create window selection panel."""
        colors = self._get_colors()
        
        window_frame = tk.LabelFrame(
            parent,
            text="1. Select Target Window",
            font=('Arial', 11, 'bold'),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        )
        window_frame.pack(fill='x', pady=(0, 10), padx=5)

        # Refresh button
        tk.Button(
            window_frame,
            text="🔄 Refresh Window List",
            command=self._refresh_windows,
            bg='#3498db',
            fg='white',
            padx=10,
            pady=5
        ).pack(pady=5)

        # Window listbox with scrollbar
        list_container = tk.Frame(window_frame, bg=colors['panel_bg'])
        list_container.pack(fill='both', expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side='right', fill='y')

        self.window_listbox = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 9),
            height=6,
            bg=colors['canvas_bg'],
            fg=colors['text_primary'],
            selectbackground=colors['selected_bg']
        )
        self.window_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.window_listbox.yview)

        self.window_listbox.bind('<<ListboxSelect>>', self._on_window_select)

        # Auto-find button
        tk.Button(
            window_frame,
            text="🔍 Auto-Find SpinView",
            command=self._find_spinview,
            bg='#9b59b6',
            fg='white',
            padx=10,
            pady=3
        ).pack(pady=5)

        self.window_status = tk.Label(
            window_frame,
            text="No window selected",
            font=('Arial', 9),
            fg='gray',
            bg=colors['panel_bg']
        )
        self.window_status.pack(pady=5)

    def _create_region_selection_panel(self, parent):
        """Create region selection panel."""
        colors = self._get_colors()
        
        region_frame = tk.LabelFrame(
            parent,
            text="2. Select Camera Feed Region",
            font=('Arial', 11, 'bold'),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        )
        region_frame.pack(fill='x', pady=(0, 10), padx=5)

        # ROI mode selection
        mode_frame = tk.Frame(region_frame, bg=colors['panel_bg'])
        mode_frame.pack(pady=5)

        tk.Label(
            mode_frame, 
            text="Selection Mode:", 
            font=('Arial', 9),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        ).pack()

        self.roi_mode = tk.StringVar(value="rectangle")
        
        tk.Radiobutton(
            mode_frame,
            text="📐 Rectangle",
            variable=self.roi_mode,
            value="rectangle",
            font=('Arial', 9),
            bg=colors['panel_bg'],
            fg=colors['text_primary'],
            selectcolor=colors['selected_bg']
        ).pack(side='left', padx=5)

        tk.Radiobutton(
            mode_frame,
            text="🔺 Polygon",
            variable=self.roi_mode,
            value="polygon",
            font=('Arial', 9),
            bg=colors['panel_bg'],
            fg=colors['text_primary'],
            selectcolor=colors['selected_bg']
        ).pack(side='left', padx=5)

        self.select_region_btn = tk.Button(
            region_frame,
            text="📐 Select Feed Region",
            command=self._select_camera_region,
            bg='#9b59b6',
            fg='white',
            padx=10,
            pady=5,
            state='disabled'
        )
        self.select_region_btn.pack(pady=5)

        self.region_status = tk.Label(
            region_frame,
            text="No region selected",
            font=('Arial', 9),
            fg='gray',
            bg=colors['panel_bg']
        )
        self.region_status.pack(pady=5)

    def _create_analysis_control_panel(self, parent):
        """Create analysis control panel."""
        colors = self._get_colors()
        
        analysis_frame = tk.LabelFrame(
            parent,
            text="3. DIC Quality Analysis",
            font=('Arial', 11, 'bold'),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        )
        analysis_frame.pack(fill='x', pady=(0, 10), padx=5)

        # Performance mode selection
        perf_frame = tk.Frame(analysis_frame, bg=colors['panel_bg'])
        perf_frame.pack(pady=5)
        
        tk.Label(
            perf_frame,
            text="Performance Mode:",
            font=('Arial', 9),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        ).pack(side='left')
        
        self.performance_mode = tk.StringVar(value="balanced")
        
        perf_combo = ttk.Combobox(
            perf_frame,
            textvariable=self.performance_mode,
            values=["fast", "balanced", "accurate"],
            state="readonly",
            width=10
        )
        perf_combo.pack(side='left', padx=5)
        
        # Add tooltip-like label for performance modes
        perf_info = tk.Label(
            perf_frame,
            text="ℹ️",
            font=('Arial', 8),
            bg=colors['panel_bg'],
            fg='#3498db',
            cursor="hand2"
        )
        perf_info.pack(side='left', padx=2)
        
        # Bind tooltip functionality
        def show_perf_info(event):
            info_text = {
                "fast": "Fast: ~2-3x faster, good accuracy",
                "balanced": "Balanced: Standard speed and accuracy", 
                "accurate": "Accurate: Slower, highest precision"
            }
            current_mode = self.performance_mode.get()
            self.status_var.set(info_text.get(current_mode, "Select performance mode"))
        
        perf_info.bind("<Button-1>", show_perf_info)

        # Control buttons
        btn_frame = tk.Frame(analysis_frame, bg=colors['panel_bg'])
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(
            btn_frame,
            text="▶️ Start Analysis",
            command=self._start_analysis,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8,
            state='disabled'
        )
        self.start_btn.pack(side='left', padx=5)

        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹️ Stop",
            command=self._stop_analysis,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=5)

    def _create_legend_panel(self, parent):
        """Create legend panel in the left control panel."""
        colors = self._get_colors()
        
        # Legend frame
        legend_frame = tk.LabelFrame(
            parent,
            text="Quality Map Legend",
            font=('Arial', 11, 'bold'),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        )
        legend_frame.pack(fill='x', pady=(0, 10), padx=5)

        # Create the legend
        self._create_quality_legend(legend_frame)

        # Simple metrics display (just overall score and frame rate)
        self.metrics_vars = {}
        
        # Overall Score
        score_frame = tk.Frame(legend_frame, bg=colors['panel_bg'])
        score_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            score_frame,
            text="DIC Quality Score:",
            font=('Arial', 10, 'bold'),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        ).pack(side='left')
        
        self.metrics_vars["Overall Score"] = tk.StringVar(value="0.000")
        tk.Label(
            score_frame,
            textvariable=self.metrics_vars["Overall Score"],
            font=('Arial', 10, 'bold'),
            fg='#2c3e50',
            bg=colors['panel_bg']
        ).pack(side='right')

        # Frame Rate
        fps_frame = tk.Frame(legend_frame, bg=colors['panel_bg'])
        fps_frame.pack(fill='x', padx=10, pady=(0, 5))
        
        tk.Label(
            fps_frame,
            text="Frame Rate:",
            font=('Arial', 9),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        ).pack(side='left')
        
        self.metrics_vars["Frame Rate"] = tk.StringVar(value="0.0 fps")
        tk.Label(
            fps_frame,
            textvariable=self.metrics_vars["Frame Rate"],
            font=('Arial', 9),
            fg='#2c3e50',
            bg=colors['panel_bg']
        ).pack(side='right')

        # Analysis Time
        analysis_time_frame = tk.Frame(legend_frame, bg=colors['panel_bg'])
        analysis_time_frame.pack(fill='x', padx=10, pady=(0, 5))
        
        tk.Label(
            analysis_time_frame,
            text="Analysis Time:",
            font=('Arial', 9),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        ).pack(side='left')
        
        self.metrics_vars["Analysis Time"] = tk.StringVar(value="0.0 ms")
        tk.Label(
            analysis_time_frame,
            textvariable=self.metrics_vars["Analysis Time"],
            font=('Arial', 9),
            fg='#2c3e50',
            bg=colors['panel_bg']
        ).pack(side='right')

    def _create_display_panels(self, parent):
        """Create display panels for live feed, quality map, and quality history."""
        colors = self._get_colors()
        
        # Notebook for different views
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True)

        # Live feed tab
        live_frame = tk.Frame(self.notebook, bg=colors['canvas_bg'])
        self.notebook.add(live_frame, text="Live Camera Feed")

        self.live_canvas = tk.Canvas(live_frame, bg='black')
        self.live_canvas.pack(fill='both', expand=True)
        self.live_image_item = None

        # Quality map tab (without legend - legend is now in left panel)
        quality_frame = tk.Frame(self.notebook, bg=colors['canvas_bg'])
        self.notebook.add(quality_frame, text="DIC Quality Map")

        self.quality_canvas = tk.Canvas(quality_frame, bg='black')
        self.quality_canvas.pack(fill='both', expand=True)
        self.quality_image_item = None

        # Results graph tab
        results_frame = tk.Frame(self.notebook, bg=colors['canvas_bg'])
        self.notebook.add(results_frame, text="Quality History")
        
        self._create_results_graph(results_frame)

    def _create_quality_legend(self, parent):
        """Create horizontal legend for the quality map colors."""
        colors = self._get_colors()
        
        # Title
        tk.Label(
            parent,
            text="Quality Scale",
            font=('Arial', 10, 'bold'),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        ).pack(pady=(5, 3))
        
        # Create horizontal legend container
        legend_container = tk.Frame(parent, bg=colors['panel_bg'])
        legend_container.pack(fill='x', padx=5, pady=2)
        
        # Legend items with color swatches - arranged horizontally
        # These match the custom_dic spectrum from constants.py
        legend_items = [
            ("#FF0000", "Poor"),       # Red (255, 0, 0) - worst
            ("#FF7F00", "Fair"),       # Orange (255, 127, 0)
            ("#FFFF00", "Good"),       # Yellow (255, 255, 0)
            ("#00FF00", "Very Good"),  # Green (0, 255, 0)
            ("#0000FF", "Excellent")   # Blue (0, 0, 255) - best
        ]
        
        # Create horizontal layout with color swatches
        swatch_frame = tk.Frame(legend_container, bg=colors['panel_bg'])
        swatch_frame.pack(fill='x', pady=2)
        
        # Create color gradient bar
        for i, (color_hex, quality_text) in enumerate(legend_items):
            # Color swatch
            swatch = tk.Frame(swatch_frame, width=60, height=20, bg=color_hex)
            swatch.pack(side='left', expand=True, fill='x', padx=1)
            swatch.pack_propagate(False)
        
        # Create labels below the color bar
        label_frame = tk.Frame(legend_container, bg=colors['panel_bg'])
        label_frame.pack(fill='x', pady=(2, 0))
        
        # Add labels for the extremes and middle
        tk.Label(
            label_frame,
            text="Poor",
            font=('Arial', 7),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        ).pack(side='left')
        
        # Spacer
        tk.Frame(label_frame, bg=colors['panel_bg']).pack(side='left', expand=True, fill='x')
        
        tk.Label(
            label_frame,
            text="Good",
            font=('Arial', 7),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        ).pack(side='left')
        
        # Spacer
        tk.Frame(label_frame, bg=colors['panel_bg']).pack(side='left', expand=True, fill='x')
        
        tk.Label(
            label_frame,
            text="Excellent",
            font=('Arial', 7),
            bg=colors['panel_bg'],
            fg=colors['text_primary']
        ).pack(side='right')
        
        # Add compact note
        tk.Label(
            parent,
            text="Red = Worst ← → Blue = Best",
            font=('Arial', 7),
            bg=colors['panel_bg'],
            fg=colors['text_secondary'],
            justify='center'
        ).pack(pady=(3, 0))

    def _create_results_graph(self, parent):
        """Create the results graph for score over time."""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            
            # Create matplotlib figure
            self.fig = Figure(figsize=(10, 6), dpi=100)
            self.ax = self.fig.add_subplot(111)
            
            # Configure plot
            self.ax.set_xlabel('Time (seconds)')
            self.ax.set_ylabel('DIC Quality Score')
            self.ax.set_title('Real-time DIC Quality Score History')
            self.ax.grid(True, alpha=0.3)
            self.ax.set_ylim(0, 100)  # DIC scores are 0-100
            
            # Create line plot for only the overall DIC quality score
            self.score_line, = self.ax.plot([], [], 'b-', linewidth=3, label='DIC Quality Score', alpha=0.9)
            
            # Embed plot in tkinter
            self.graph_canvas = FigureCanvasTkAgg(self.fig, parent)
            self.graph_canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
            
            # Graph update timer
            self.graph_update_timer = None
            
        except ImportError:
            # Fallback if matplotlib not available
            tk.Label(
                parent,
                text="Matplotlib not available for graphing.\nInstall matplotlib to see quality history graphs.",
                font=('Arial', 12),
                fg='red'
            ).pack(expand=True)

    def _create_status_bar(self):
        """Create status bar."""
        colors = self._get_colors()
        
        self.status_var = tk.StringVar(value="Ready - Select a window from the list or use Auto-Find")
        status_bar = tk.Label(
            self.capture_window,
            textvariable=self.status_var,
            font=('Arial', 10),
            bg=colors['panel_bg'],
            fg=colors['text_primary'],
            anchor='w',
            padx=10
        )
        status_bar.pack(side='bottom', fill='x')

    # Window management methods
    def _refresh_windows(self):
        """Refresh window list."""
        if not hasattr(self, 'window_listbox'):
            return
            
        self.window_listbox.delete(0, tk.END)

        windows = self._list_windows()
        self.window_data = {}

        for window in windows:
            # Filter out some system windows
            if window['title'] and 'Default IME' not in window['title']:
                display_text = f"{window['title']} [{window['class']}]"
                self.window_listbox.insert(tk.END, display_text)
                self.window_data[display_text] = window

        self.window_status.config(text=f"Found {len(self.window_data)} windows", fg='blue')

    def _list_windows(self):
        """List all visible windows."""
        if platform.system() != 'Windows':
            return []
            
        windows = []

        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text:
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'class': win32gui.GetClassName(hwnd)
                    })

        win32gui.EnumWindows(enum_handler, None)
        return windows

    def _on_window_select(self, event):
        """Handle window selection."""
        selection = self.window_listbox.curselection()
        if selection:
            index = selection[0]
            selected_text = self.window_listbox.get(index)

            if selected_text in self.window_data:
                window = self.window_data[selected_text]
                self.spinview_hwnd = window['hwnd']

                self.select_region_btn.config(state='normal')
                self.window_status.config(
                    text=f"Selected: {window['title'][:30]}...",
                    fg='green'
                )
                self.status_var.set(f"Window selected: {window['title']}")

                # Try to preview the selected window
                self._preview_selected_window()

    def _preview_selected_window(self):
        """Preview the selected window."""
        if self.spinview_hwnd:
            try:
                image = self._capture_full_window(self.spinview_hwnd)
                if image is not None:
                    # Show a small preview in the live canvas
                    self._update_canvas(self.live_canvas, image, self.live_image_item)
                    self.status_var.set("Window preview loaded - now select camera region")
            except Exception as e:
                logger.error(f"Preview error: {e}")

    def _find_spinview(self):
        """Auto-find SpinView window and highlight it in the list."""
        result = self._find_spinview_window()

        if result is True:
            # Found SpinView specifically - highlight it in the list
            title = self._get_window_title(self.spinview_hwnd)
            
            # Find and select it in the listbox
            for i in range(self.window_listbox.size()):
                item_text = self.window_listbox.get(i)
                if title.lower() in item_text.lower():
                    self.window_listbox.selection_clear(0, tk.END)
                    self.window_listbox.selection_set(i)
                    self.window_listbox.see(i)
                    break
            
            self.window_status.config(text=f"Auto-found: {title[:30]}...", fg='green')
            self.select_region_btn.config(state='normal')
            self.status_var.set("SpinView auto-found! Now select the camera feed region.")
            self._preview_selected_window()
            
        elif isinstance(result, list) and result:
            # Highlight camera-related windows in the list
            camera_titles = [w['title'].lower() for w in result]
            highlighted_count = 0
            
            for i in range(self.window_listbox.size()):
                item_text = self.window_listbox.get(i).lower()
                for cam_title in camera_titles:
                    if cam_title in item_text:
                        self.window_listbox.selection_set(i)
                        highlighted_count += 1
                        break
            
            if highlighted_count > 0:
                self.status_var.set(f"Found {highlighted_count} camera-related windows - select one from the list")
                self.window_status.config(text=f"Found {highlighted_count} camera windows", fg='orange')
            else:
                self.status_var.set("No camera windows found - select any window from the list")
        else:
            messagebox.showinfo(
                "Auto-Find Result",
                "Could not auto-find SpinView specifically.\n"
                "Please manually select your camera window from the list above."
            )

    def _find_spinview_window(self):
        """Find SpinView window automatically."""
        windows = []

        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                # Look for SpinView or common camera UI patterns
                if any(pattern in window_text.lower() for pattern in
                       ['spinview', 'flir', 'camera', 'viewer', 'live', 'preview']):
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'class': win32gui.GetClassName(hwnd)
                    })

        win32gui.EnumWindows(enum_handler, None)

        # If found SpinView specifically
        for window in windows:
            if 'spinview' in window['title'].lower():
                self.spinview_hwnd = window['hwnd']
                logger.info(f"Found SpinView: {window['title']}")
                return True

        # Otherwise return all camera-related windows
        return windows

    def _get_window_title(self, hwnd):
        """Get window title from handle."""
        try:
            return win32gui.GetWindowText(hwnd)
        except:
            return None

    # Region selection methods
    def _select_camera_region(self):
        """Select camera feed region within window."""
        if not self.spinview_hwnd:
            return

        # Capture full window
        window_image = self._capture_full_window(self.spinview_hwnd)
        if window_image is None:
            messagebox.showerror("Error", "Failed to capture window")
            return

        # Get selected mode
        mode = self.roi_mode.get()

        # Show appropriate selector
        if mode == "rectangle":
            from ui.live_analyze.camera_region_selectors import CameraRegionSelector
            selector = CameraRegionSelector(
                self.capture_window,
                window_image,
                self._on_region_selected
            )
            selector.show()
        else:  # polygon
            from ui.live_analyze.camera_region_selectors import CameraPolygonSelector
            selector = CameraPolygonSelector(
                self.capture_window,
                window_image,
                self._on_region_selected
            )
            selector.show()

    def _on_region_selected(self, region):
        """Handle region selection."""
        if region:
            self.camera_region = region
            self.save_config()

            if isinstance(region, tuple) and len(region) == 2 and region[0] == 'polygon':
                # Polygon region
                points = region[1]
                self.region_status.config(
                    text=f"Polygon: {len(points)} points",
                    fg='green'
                )
                self.status_var.set("Polygon region selected! Ready to start DIC analysis.")
            else:
                # Rectangle region
                x, y, w, h = region
                self.region_status.config(
                    text=f"Rectangle: {w}x{h} at ({x},{y})",
                    fg='green'
                )
                self.status_var.set("Rectangle region selected! Ready to start DIC analysis.")
            
            self.start_btn.config(state='normal')

    # Analysis methods
    def _start_analysis(self):
        """Start DIC quality analysis."""
        self.is_analyzing = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Clear previous data
        self.analysis_history.clear()
        self.frame_times.clear()
        self.analysis_times.clear()
        
        # Start analysis thread
        self.analysis_thread = threading.Thread(target=self._analysis_loop)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        
        # Start graph updates
        if hasattr(self, 'graph_canvas'):
            self._schedule_graph_update()

        self.status_var.set("Analyzing DIC quality from camera feed...")

    def _analysis_loop(self):
        """Main analysis loop with proper DIC analysis."""
        start_time = time.time()

        while self.is_analyzing:
            try:
                loop_start = time.time()

                # Capture camera region
                camera_feed = self._capture_camera_region()

                if camera_feed is not None:
                    analysis_start = time.time()
                    
                    # Perform proper DIC analysis using main analyzer
                    result = self._analyze_with_main_analyzer(camera_feed)
                    
                    analysis_time = time.time() - analysis_start
                    self.analysis_times.append(analysis_time)

                    if result:
                        # Store results
                        self.current_score = result.overall_score
                        self.current_quality_map = result.quality_map
                        
                        # Extract all quality metrics from the result
                        quality_metrics = self._extract_all_quality_metrics(result)
                        
                        # Add to history with timestamp
                        timestamp = time.time() - start_time
                        history_entry = {
                            'timestamp': timestamp,
                            'overall_score': result.overall_score,
                            'analysis_time': analysis_time
                        }
                        history_entry.update(quality_metrics)
                        self.analysis_history.append(history_entry)

                        # Update displays on main thread
                        self.root.after(0, lambda: self._update_displays(camera_feed, result))

                # Calculate frame rate
                frame_time = time.time() - loop_start
                self.frame_times.append(frame_time)
                
                if self.frame_times:
                    fps = 1.0 / np.mean(self.frame_times)
                    self.root.after(0, lambda: self.metrics_vars["Frame Rate"].set(f"{fps:.1f} fps"))
                
                # Update analysis time display
                if self.analysis_times:
                    avg_analysis_time = np.mean(self.analysis_times) * 1000  # Convert to ms
                    self.root.after(0, lambda: self.metrics_vars["Analysis Time"].set(f"{avg_analysis_time:.1f} ms"))

                # Control frame rate based on performance mode
                perf_mode = self.performance_mode.get()
                if perf_mode == "fast":
                    target_interval = 0.2  # 5 fps for fast mode
                    min_sleep = 0.005
                elif perf_mode == "balanced":
                    target_interval = 0.5  # 2 fps for balanced mode
                    min_sleep = 0.01
                else:  # accurate
                    target_interval = 1.0  # 1 fps for accurate mode
                    min_sleep = 0.01
                
                elapsed = time.time() - loop_start
                sleep_time = max(target_interval - elapsed, min_sleep)
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Analysis error: {e}")
                time.sleep(0.5)

    def _analyze_with_main_analyzer(self, camera_feed) -> Optional[AnalysisResult]:
        """Analyze camera feed using the main DIC analyzer with performance optimization."""
        try:
            # Get performance mode settings
            perf_mode = self.performance_mode.get()
            
            # Determine analysis parameters based on performance mode
            if perf_mode == "fast":
                spectrum_type = 'fast'  # Use new fast spectrum type
                subset_size = 15  # Smaller subset for faster analysis
                step_size = 8     # Larger step for fewer analysis points
            elif perf_mode == "balanced":
                spectrum_type = 'optimized'
                subset_size = None  # Let analyzer determine optimal
                step_size = None    # Let analyzer determine optimal
            else:  # accurate
                spectrum_type = 'controlled'
                subset_size = None
                step_size = None
            
            # Handle different camera feed types
            if isinstance(camera_feed, tuple) and len(camera_feed) == 2:
                # Polygon region with mask
                image, mask = camera_feed
                
                # Create ROI data from mask for proper analysis
                roi_data = self._create_roi_from_mask(mask)
                
                # Analyze with ROI and performance parameters
                result = self.analyzer.analyze_image(
                    image,
                    roi=roi_data,
                    spectrum_type=spectrum_type,
                    subset_size=subset_size,
                    step_size=step_size
                )
            else:
                # Regular rectangular region
                result = self.analyzer.analyze_image(
                    camera_feed,
                    roi=None,
                    spectrum_type=spectrum_type,
                    subset_size=subset_size,
                    step_size=step_size
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return None

    def _create_roi_from_mask(self, mask) -> Optional[ROIData]:
        """Create ROI data from a mask for polygon regions."""
        try:
            # Find contours in the mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Use the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Simplify contour to reduce points
                epsilon = 0.02 * cv2.arcLength(largest_contour, True)
                simplified_contour = cv2.approxPolyDP(largest_contour, epsilon, True)
                
                # Convert to coordinate list
                coordinates = [(int(point[0][0]), int(point[0][1])) for point in simplified_contour]
                
                return ROIData(coordinates=coordinates, roi_type='polygon')
                
        except Exception as e:
            logger.error(f"Error creating ROI from mask: {e}")
            
        return None

    def _extract_all_quality_metrics(self, result: AnalysisResult) -> dict:
        """Extract all quality metrics from analysis result."""
        try:
            # Initialize with default values
            metrics = {
                'gradient_score': 0.0,
                'contrast_score': 0.0,
                'entropy_score': 0.0,
                'pattern_score': 0.0,
                'noise_score': 0.0
            }
            
            # The QualityCalculator returns results in quality_details
            if hasattr(result, 'quality_details') and result.quality_details:
                quality_data = result.quality_details
                
                # Extract individual metric scores - they're already 0-1 scale, convert to 0-100
                if 'gradient_metrics' in quality_data:
                    gradient_score = quality_data['gradient_metrics'].get('score', 0.0)
                    metrics['gradient_score'] = gradient_score * 100
                    
                if 'contrast_metrics' in quality_data:
                    contrast_score = quality_data['contrast_metrics'].get('score', 0.0)
                    metrics['contrast_score'] = contrast_score * 100
                    
                if 'entropy_metrics' in quality_data:
                    entropy_score = quality_data['entropy_metrics'].get('score', 0.0)
                    metrics['entropy_score'] = entropy_score * 100
                    
                if 'pattern_metrics' in quality_data:
                    pattern_score = quality_data['pattern_metrics'].get('score', 0.0)
                    metrics['pattern_score'] = pattern_score * 100
                    
                if 'noise_metrics' in quality_data:
                    # Noise score is already inverted in QualityCalculator (higher = better quality)
                    noise_score = quality_data['noise_metrics'].get('score', 0.0)
                    metrics['noise_score'] = noise_score * 100
                    
                logger.debug(f"Extracted metrics: {metrics}")
                return metrics
            
            # Fallback: if quality_details not available, use proportional distribution
            overall = getattr(result, 'overall_score', 0.0)
            # Use the same weights as in QualityCalculator
            weights = {'gradient': 0.40, 'contrast': 0.25, 'entropy': 0.20, 'pattern': 0.10, 'noise': 0.05}
            total_weight = sum(weights.values())
            
            metrics['gradient_score'] = overall * weights['gradient'] / total_weight
            metrics['contrast_score'] = overall * weights['contrast'] / total_weight
            metrics['entropy_score'] = overall * weights['entropy'] / total_weight
            metrics['pattern_score'] = overall * weights['pattern'] / total_weight
            metrics['noise_score'] = overall * weights['noise'] / total_weight
            
            logger.debug(f"Using proportional fallback metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error extracting quality metrics: {e}")
            # Return proportional fallback
            overall = getattr(result, 'overall_score', 0.0)
            weights = {'gradient': 0.40, 'contrast': 0.25, 'entropy': 0.20, 'pattern': 0.10, 'noise': 0.05}
            total_weight = sum(weights.values())
            return {
                'gradient_score': overall * weights['gradient'] / total_weight,
                'contrast_score': overall * weights['contrast'] / total_weight,
                'entropy_score': overall * weights['entropy'] / total_weight,
                'pattern_score': overall * weights['pattern'] / total_weight,
                'noise_score': overall * weights['noise'] / total_weight
            }

    def _extract_metric_score(self, result: AnalysisResult, metric_name: str) -> float:
        """Extract specific metric score from analysis result."""
        try:
            metrics = self._extract_all_quality_metrics(result)
            return metrics.get(f'{metric_name}_score', 0.0)
        except Exception as e:
            logger.error(f"Error extracting {metric_name} score: {e}")
            return 0.0

    def _update_displays(self, camera_feed, result: AnalysisResult):
        """Update display canvases and metrics."""
        try:
            # Handle camera feed display
            display_image = camera_feed
            if isinstance(camera_feed, tuple) and len(camera_feed) == 2:
                # Polygon region: extract image and apply mask for display
                image, mask = camera_feed
                if len(image.shape) == 3:
                    mask_3d = np.stack([mask] * 3, axis=2) / 255.0
                    display_image = (image * mask_3d).astype(np.uint8)
                else:
                    display_image = (image * (mask / 255.0)).astype(np.uint8)
            
            # Update live feed
            self._update_canvas(self.live_canvas, display_image, self.live_image_item)

            # Update quality map if available
            if result.quality_map is not None:
                # Convert quality map to colored visualization
                quality_colored = self._create_quality_visualization(result.quality_map)
                quality_item = self._update_canvas(
                    self.quality_canvas,
                    quality_colored,
                    self.quality_image_item
                )
                if quality_item:
                    self.quality_image_item = quality_item

            # Update metrics (only overall score now)
            self.metrics_vars["Overall Score"].set(f"{result.overall_score:.3f}")

        except Exception as e:
            logger.error(f"Display update error: {e}")

    def _create_quality_visualization(self, quality_map: np.ndarray) -> np.ndarray:
        """Create colored visualization of quality map with custom DIC colormap."""
        try:
            # Normalize quality map to 0-1
            normalized = (quality_map - quality_map.min()) / (quality_map.max() - quality_map.min() + 1e-6)
            
            # Create custom colormap: red (bad) to blue (good)
            # This matches the main app's custom_dic spectrum where blue = good, red = bad
            h, w = normalized.shape
            colored_rgb = np.zeros((h, w, 3), dtype=np.uint8)
            
            # Define color points to match custom_dic spectrum from constants.py
            # Red (bad quality) = (255, 0, 0)
            # Orange = (255, 127, 0) 
            # Yellow = (255, 255, 0)
            # Green = (0, 255, 0)
            # Blue (good quality) = (0, 0, 255)
            
            colors = np.array([
                [255, 0, 0],      # Red (worst quality)
                [255, 127, 0],    # Orange
                [255, 255, 0],    # Yellow
                [0, 255, 0],      # Green
                [0, 0, 255]       # Blue (best quality)
            ], dtype=np.float32)
            
            # Create smooth interpolation
            n_colors = len(colors)
            color_positions = np.linspace(0, 1, n_colors)
            
            # Find which color segment each pixel belongs to
            segment_indices = np.searchsorted(color_positions, normalized) - 1
            segment_indices = np.clip(segment_indices, 0, n_colors - 2)
            
            # Get interpolation factor
            pos1 = color_positions[segment_indices]
            pos2 = color_positions[segment_indices + 1]
            denominator = pos2 - pos1
            denominator[denominator == 0] = 1
            t = (normalized - pos1) / denominator
            t = np.clip(t, 0, 1)
            
            # Interpolate colors
            color1 = colors[segment_indices]
            color2 = colors[segment_indices + 1]
            t_expanded = np.expand_dims(t, axis=2)
            
            interpolated_colors = color1 * (1 - t_expanded) + color2 * t_expanded
            colored_rgb = np.clip(interpolated_colors, 0, 255).astype(np.uint8)
            
            return colored_rgb
            
        except Exception as e:
            logger.error(f"Error creating quality visualization: {e}")
            # Fallback to grayscale
            if len(quality_map.shape) == 2:
                return np.stack([quality_map] * 3, axis=2)
            return quality_map

    def _update_canvas(self, canvas, image, item):
        """Update a canvas with an image."""
        if image is None:
            return item

        try:
            # Get canvas size
            canvas_w = canvas.winfo_width()
            canvas_h = canvas.winfo_height()

            if canvas_w > 1 and canvas_h > 1:
                # Calculate scaling
                h, w = image.shape[:2]
                scale = min(canvas_w / w, canvas_h / h) * 0.95

                new_w = int(w * scale)
                new_h = int(h * scale)

                # Resize image
                resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

                # Convert to PhotoImage
                if len(resized.shape) == 2:
                    # Grayscale
                    pil_image = Image.fromarray(resized)
                else:
                    # Color
                    pil_image = Image.fromarray(resized)

                photo = ImageTk.PhotoImage(pil_image)

                # Update or create canvas item
                if item is None:
                    item = canvas.create_image(
                        canvas_w // 2, canvas_h // 2,
                        image=photo,
                        anchor='center'
                    )
                else:
                    canvas.itemconfig(item, image=photo)

                # Keep reference
                canvas.image = photo

                return item

        except Exception as e:
            logger.error(f"Canvas update error: {e}")

        return item

    def _schedule_graph_update(self):
        """Schedule graph update."""
        if hasattr(self, 'graph_canvas') and self.is_analyzing:
            self._update_graph()
            self.graph_update_timer = self.root.after(2000, self._schedule_graph_update)  # Update every 2 seconds

    def _update_graph(self):
        """Update the quality history graph with DIC quality score only."""
        try:
            if not self.analysis_history:
                return
                
            # Extract data for plotting - only overall score
            timestamps = [entry['timestamp'] for entry in self.analysis_history]
            overall_scores = [entry['overall_score'] for entry in self.analysis_history]
            
            # Update line data
            self.score_line.set_data(timestamps, overall_scores)
            
            # Adjust axes
            if timestamps:
                self.ax.set_xlim(max(0, timestamps[-1] - 300), timestamps[-1] + 10)  # Show last 5 minutes
                
                # Scale based on overall scores only
                if overall_scores:
                    min_score = max(0, min(overall_scores) - 5)  # Add small margin, but don't go below 0
                    max_score = min(100, max(overall_scores) + 5)  # Add small margin, but don't exceed 100
                    self.ax.set_ylim(min_score, max_score)
            
            # Adjust layout
            self.fig.tight_layout()
            
            # Redraw
            self.graph_canvas.draw()
            
        except Exception as e:
            logger.error(f"Graph update error: {e}")

    def _stop_analysis(self):
        """Stop analysis."""
        self.is_analyzing = False

        if self.analysis_thread:
            self.analysis_thread.join(timeout=1.0)
            
        if self.graph_update_timer:
            self.root.after_cancel(self.graph_update_timer)
            self.graph_update_timer = None

        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

        self.status_var.set("Analysis stopped")



    # Capture methods (from test file)
    def _capture_full_window(self, hwnd):
        """Capture entire window content."""
        try:
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # Get the window device context
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            # Create bitmap
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            # Copy window content
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)

            # Convert to numpy array
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            image = np.frombuffer(bmpstr, dtype='uint8')
            image.shape = (height, width, 4)

            # Clean up
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)

            # Convert BGRA to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)

            return image

        except Exception as e:
            logger.error(f"Error capturing window: {e}")
            return None

    def _capture_camera_region(self):
        """Capture only the camera feed region within the window."""
        if not self.spinview_hwnd or not self.camera_region:
            return None

        try:
            # Capture full window
            full_window = self._capture_full_window(self.spinview_hwnd)
            if full_window is None:
                return None

            # Handle different region types
            if isinstance(self.camera_region, tuple) and len(self.camera_region) == 2 and self.camera_region[0] == 'polygon':
                # Polygon region
                return self._extract_polygon_region(full_window, self.camera_region[1])
            else:
                # Rectangle region
                x, y, w, h = self.camera_region
                camera_feed = full_window[y:y + h, x:x + w]
                return camera_feed

        except Exception as e:
            logger.error(f"Error capturing camera region: {e}")
            return None

    def _extract_polygon_region(self, image, polygon_points):
        """Extract polygon region from image - returns image with mask applied."""
        try:
            # Create mask for polygon
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            
            # Convert points to numpy array
            points = np.array(polygon_points, dtype=np.int32)
            
            # Fill polygon in mask
            cv2.fillPoly(mask, [points], 255)
            
            # Return the full image with mask information
            return (image, mask)
            
        except Exception as e:
            logger.error(f"Error extracting polygon region: {e}")
            return None

    # Configuration methods
    def save_config(self):
        """Save camera region configuration."""
        if self.camera_region:
            # Handle polygon regions for JSON serialization
            region_to_save = self.camera_region
            if isinstance(self.camera_region, tuple) and len(self.camera_region) == 2 and self.camera_region[0] == 'polygon':
                # Convert polygon points to list for JSON serialization
                region_to_save = ('polygon', list(self.camera_region[1]))
            
            config = {
                'camera_region': region_to_save,
                'last_window_title': self._get_window_title(self.spinview_hwnd) if self.spinview_hwnd else None,
                'frequency': self.frequency_var.get() if hasattr(self, 'frequency_var') else "1.0"
            }

    def _on_capture_window_close(self):
        """Handle capture window close."""
        self._stop_analysis()
        if self.capture_window:
            self.capture_window.destroy()
            self.capture_window = None

    def export_results(self):
        """Export analysis results."""
        if not self.analysis_history:
            messagebox.showwarning("No Data", "No analysis data to export.")
            return
            
        try:
            filepath = filedialog.asksaveasfilename(
                title="Export Analysis Results",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filepath:
                if filepath.endswith('.csv'):
                    self._export_csv(filepath)
                else:
                    self._export_json(filepath)
                    
                messagebox.showinfo("Export Complete", f"Results exported to {filepath}")
                
        except Exception as e:
            logger.error(f"Export error: {e}")
            messagebox.showerror("Export Error", f"Failed to export results: {e}")

    def _export_json(self, filepath):
        """Export results as JSON."""
        data = {
            'export_time': time.time(),
            'analysis_count': len(self.analysis_history),
            'configuration': {
                'camera_region': self.camera_region,
                'frequency': self.frequency_var.get() if hasattr(self, 'frequency_var') else "1.0"
            },
            'results': list(self.analysis_history)
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def _export_csv(self, filepath):
        """Export results as CSV."""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Timestamp', 'Overall Score', 'Gradient Score', 'Speckle Score',
                'Contrast Score', 'Entropy Score', 'Analysis Time'
            ])
            
            # Data
            for entry in self.analysis_history:
                writer.writerow([
                    entry['timestamp'],
                    entry['overall_score'],
                    entry.get('gradient_score', 0),
                    entry.get('speckle_score', 0),
                    entry.get('contrast_score', 0),
                    entry.get('entropy_score', 0),
                    entry.get('analysis_time', 0)
                ])