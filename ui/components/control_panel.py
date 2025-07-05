# ui/components/control_panel.py - Clean UI Component

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Any
from utils.constants import APP_CONFIG, get_theme_colors
from utils.modern_styling import ModernStyleManager


class ControlPanel:
    """
    Control panel component for DIC Quality Inspector.

    Handles all user controls and button interactions.
    Follows single responsibility principle - only UI concerns.
    """

    def __init__(self, parent: tk.Widget, callbacks: Dict[str, Callable]):
        """
        Initialize control panel.

        Args:
            parent: Parent widget
            callbacks: Dictionary of callback functions for each action
        """
        self.parent = parent
        self.callbacks = callbacks

        # State tracking
        self.current_state = 'no_image'

        # UI elements
        self.buttons = {}
        self.spectrum_var = tk.StringVar(value='optimized')
        self.control_params = {
            'facet_size': tk.StringVar(value='19'),
            'point_distance': tk.StringVar(value='4')
        }

        self._create_panel()

    def _create_panel(self):
        """Create the control panel UI with modern styling."""
        colors = get_theme_colors()
        
        # Main control frame with modern card-like appearance
        self.control_frame = tk.Frame(
            self.parent,
            bg=colors['panel_bg'],
            relief='flat',
            bd=0
        )
        self.control_frame.pack(fill='x', padx=0, pady=APP_CONFIG['styling']['element_spacing'])
        
        # Add padding inside the panel
        self.inner_frame = tk.Frame(
            self.control_frame,
            bg=colors['panel_bg']
        )
        self.inner_frame.pack(fill='x', padx=APP_CONFIG['styling']['panel_padding'], 
                             pady=APP_CONFIG['styling']['panel_padding'])

        # Create sections
        self._create_primary_controls()
        self._create_secondary_controls()
        self._create_zoom_controls()
        self._create_spectrum_controls()
        self._create_roi_info_section()



    def _create_primary_controls(self):
        """Create primary control buttons with modern styling."""
        colors = get_theme_colors()
        
        # Section title
        title_label = tk.Label(
            self.inner_frame,
            text="Primary Controls",
            font=APP_CONFIG['fonts']['subheading'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        title_label.pack(anchor='w', pady=(0, APP_CONFIG['styling']['small_spacing']))
        
        primary_frame = tk.Frame(self.inner_frame, bg=colors['panel_bg'])
        primary_frame.pack(fill='x', pady=APP_CONFIG['styling']['small_spacing'])

        # Primary buttons configuration with modern colors
        primary_buttons = [
            ('load_btn', "📁 Load Image", colors['btn_primary'], 'load_image'),
            ('screenshot_btn', "📸 Screenshot", colors['btn_warning'], 'take_screenshot'),
            ('roi_btn', "🎯 Select ROI", colors['purple'], 'select_roi'),
            ('analyze_btn', "🔬 Analyze", colors['btn_success'], 'analyze_image')
        ]

        for btn_id, text, color, callback_key in primary_buttons:
            btn = ModernStyleManager.create_modern_button(
                primary_frame, text, color, 
                command=lambda k=callback_key: self._execute_callback(k), 
                size='normal'  # Smaller buttons for compact layout
            )
            btn.pack(fill='x', pady=2)  # Stack vertically, full width
            self.buttons[btn_id] = btn

    def _create_secondary_controls(self):
        """Create secondary control buttons with modern styling."""
        colors = get_theme_colors()
        
        # Add spacing
        spacer = tk.Frame(self.inner_frame, bg=colors['panel_bg'], height=15)
        spacer.pack(fill='x')
        
        # Section title
        title_label = tk.Label(
            self.inner_frame,
            text="Analysis & Results",
            font=APP_CONFIG['fonts']['subheading'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        title_label.pack(anchor='w', pady=(0, APP_CONFIG['styling']['small_spacing']))
        
        secondary_frame = tk.Frame(self.inner_frame, bg=colors['panel_bg'])
        secondary_frame.pack(fill='x', pady=APP_CONFIG['styling']['small_spacing'])

        # Secondary buttons configuration with modern colors
        secondary_buttons = [
            ('quality_map_btn', "🗺️ Quality Map", colors['info'], 'toggle_quality_map'),
            ('results_btn', "📊 Show Results", colors['secondary'], 'show_results'),
            ('save_btn', "💾 Save Report", colors['btn_secondary'], 'save_report'),
            ('theme_btn', "🌙 Dark Mode", colors['purple'], 'toggle_theme'),
            ('help_btn', "❓ Help", colors['btn_secondary'], 'show_help'),
            ('reset_display_btn', "🔄 Reset Display", colors['btn_warning'], 'reset_display_results'),
            ('reset_btn', "🔄 Full Reset", colors['btn_danger'], 'reset_application')
        ]

        # Split secondary buttons into two columns for compact layout
        left_col = tk.Frame(secondary_frame, bg=colors['panel_bg'])
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        right_col = tk.Frame(secondary_frame, bg=colors['panel_bg'])
        right_col.pack(side='right', fill='both', expand=True, padx=(5, 0))

        for i, (btn_id, text, color, callback_key) in enumerate(secondary_buttons):
            parent_col = left_col if i % 2 == 0 else right_col
            btn = ModernStyleManager.create_modern_button(
                parent_col, text, color,
                command=lambda k=callback_key: self._execute_callback(k),
                size='small'  # Smaller for compact layout
            )
            btn.pack(fill='x', pady=1)
            self.buttons[btn_id] = btn

    def _create_zoom_controls(self):
        """Create zoom control buttons with modern styling."""
        colors = get_theme_colors()
        
        # Add spacing
        spacer = tk.Frame(self.inner_frame, bg=colors['panel_bg'], height=15)
        spacer.pack(fill='x')
        
        # Section title
        title_label = tk.Label(
            self.inner_frame,
            text="Image Navigation",
            font=APP_CONFIG['fonts']['subheading'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        title_label.pack(anchor='w', pady=(0, APP_CONFIG['styling']['small_spacing']))
        
        zoom_frame = tk.Frame(self.inner_frame, bg=colors['panel_bg'])
        zoom_frame.pack(fill='x', pady=APP_CONFIG['styling']['small_spacing'])

        # Zoom label with modern styling
        zoom_label = tk.Label(
            zoom_frame,
            text="🔍 Zoom:",
            font=APP_CONFIG['fonts']['body_bold'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        zoom_label.pack(side='left', padx=(0, APP_CONFIG['styling']['element_spacing']))

        # Zoom buttons configuration with modern colors
        zoom_buttons = [
            ('zoom_in_btn', "➕", colors['btn_primary'], 'zoom_in'),
            ('zoom_out_btn', "➖", colors['btn_primary'], 'zoom_out'),
            ('zoom_fit_btn', "⬜ Fit", colors['btn_success'], 'zoom_fit'),
            ('zoom_actual_btn', "1:1", colors['btn_warning'], 'zoom_actual')
        ]

        # Create zoom buttons in a 2x2 grid for compact layout
        zoom_grid = tk.Frame(zoom_frame, bg=colors['panel_bg'])
        zoom_grid.pack(fill='x', pady=5)
        
        for i, (btn_id, text, color, callback_key) in enumerate(zoom_buttons):
            row = i // 2
            col = i % 2
            btn = ModernStyleManager.create_modern_button(
                zoom_grid, text, color,
                command=lambda k=callback_key: self._execute_callback(k),
                size='small'
            )
            btn.grid(row=row, column=col, padx=2, pady=1, sticky='ew')
            self.buttons[btn_id] = btn
        
        # Configure grid weights
        zoom_grid.grid_columnconfigure(0, weight=1)
        zoom_grid.grid_columnconfigure(1, weight=1)

        # Zoom level display with modern styling
        self.zoom_level_var = tk.StringVar(value="100%")
        zoom_level_label = tk.Label(
            zoom_frame,
            textvariable=self.zoom_level_var,
            font=APP_CONFIG['fonts']['body_bold'],
            fg=colors['text_secondary'],
            bg=colors['panel_bg']
        )
        zoom_level_label.pack(side='left', padx=APP_CONFIG['styling']['element_spacing'])

    def _create_spectrum_controls(self):
        """Create spectrum selection controls with modern styling."""
        colors = get_theme_colors()
        
        # Add spacing
        spacer = tk.Frame(self.inner_frame, bg=colors['panel_bg'], height=15)
        spacer.pack(fill='x')
        
        # Section title
        title_label = tk.Label(
            self.inner_frame,
            text="Analysis Configuration",
            font=APP_CONFIG['fonts']['subheading'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        title_label.pack(anchor='w', pady=(0, APP_CONFIG['styling']['small_spacing']))
        
        spectrum_frame = tk.Frame(self.inner_frame, bg=colors['panel_bg'])
        spectrum_frame.pack(fill='x', pady=APP_CONFIG['styling']['small_spacing'])

        # Spectrum selection with modern styling
        spectrum_label = tk.Label(
            spectrum_frame,
            text="Analysis Method:",
            font=APP_CONFIG['fonts']['body_bold'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        spectrum_label.pack(side='left', padx=(0, APP_CONFIG['styling']['small_spacing']))

        spectrum_options = [
            'optimized',
            'controlled'
        ]

        # Style the combobox
        style = ttk.Style()
        style.configure('Modern.TCombobox', 
                       fieldbackground='white',
                       background=colors['btn_primary'],
                       borderwidth=1,
                       relief='flat')

        self.spectrum_combo = ttk.Combobox(
            spectrum_frame,
            textvariable=self.spectrum_var,
            values=spectrum_options,
            state='readonly',
            width=15,
            font=APP_CONFIG['fonts']['body'],
            style='Modern.TCombobox'
        )
        self.spectrum_combo.pack(side='left', padx=APP_CONFIG['styling']['small_spacing'])
        self.spectrum_combo.bind('<<ComboboxSelected>>', self._on_spectrum_changed)

        # Control parameters (initially hidden)
        self._create_control_parameters(spectrum_frame)

    def _create_control_parameters(self, parent):
        """Create control-specific parameter controls with modern styling."""
        colors = get_theme_colors()
        
        # Create a separate frame for control parameters
        self.control_params_frame = tk.Frame(self.inner_frame, bg=colors['panel_bg'])
        
        # Parameters container with subtle background
        params_container = tk.Frame(
            self.control_params_frame,
            bg=colors['hover_bg'],
            relief='flat',
            bd=0
        )
        params_container.pack(fill='x', padx=10, pady=10)
        
        # Inner padding frame
        self.control_frame = tk.Frame(params_container, bg=colors['hover_bg'])
        self.control_frame.pack(fill='x', padx=15, pady=10)

        # Title with modern styling
        control_title = tk.Label(
            self.control_frame,
            text="📐 Advanced Parameters",
            font=APP_CONFIG['fonts']['body_bold'],
            fg=colors['primary'],
            bg=colors['hover_bg']
        )
        control_title.pack(anchor='w', pady=(0, 8))
        
        # Parameters row
        params_row = tk.Frame(self.control_frame, bg=colors['hover_bg'])
        params_row.pack(fill='x')

        # Facet size with modern styling
        facet_frame = tk.Frame(params_row, bg=colors['hover_bg'])
        facet_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(
            facet_frame,
            text="Facet Size:",
            font=APP_CONFIG['fonts']['small_bold'],
            fg=colors['text_secondary'],
            bg=colors['hover_bg']
        ).pack(side='left', padx=(0, 5))

        facet_spinbox = tk.Spinbox(
            facet_frame,
            from_=11,
            to=51,
            increment=2,
            textvariable=self.control_params['facet_size'],
            width=4,
            font=APP_CONFIG['fonts']['small'],
            relief='flat',
            bd=1,
            bg='white'
        )
        facet_spinbox.pack(side='left', padx=2)

        tk.Label(
            facet_frame,
            text="px",
            font=APP_CONFIG['fonts']['small'],
            fg=colors['text_muted'],
            bg=colors['hover_bg']
        ).pack(side='left', padx=(2, 0))

        # Point distance with modern styling
        step_frame = tk.Frame(params_row, bg=colors['hover_bg'])
        step_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(
            step_frame,
            text="Step Size:",
            font=APP_CONFIG['fonts']['small_bold'],
            fg=colors['text_secondary'],
            bg=colors['hover_bg']
        ).pack(side='left', padx=(0, 5))

        step_spinbox = tk.Spinbox(
            step_frame,
            from_=2,
            to=20,
            increment=1,
            textvariable=self.control_params['point_distance'],
            width=4,
            font=APP_CONFIG['fonts']['small'],
            relief='flat',
            bd=1,
            bg='white'
        )
        step_spinbox.pack(side='left', padx=2)

        tk.Label(
            step_frame,
            text="px",
            font=APP_CONFIG['fonts']['small'],
            fg=colors['text_muted'],
            bg=colors['hover_bg']
        ).pack(side='left', padx=(2, 0))

        # Info label with modern styling
        info_label = tk.Label(
            self.control_frame,
            text="💡 Smaller values provide higher density analysis but slower processing",
            font=APP_CONFIG['fonts']['small'],
            fg=colors['text_muted'],
            bg=colors['hover_bg']
        )
        info_label.pack(anchor='w', pady=(8, 0))

    def _create_roi_info_section(self):
        """Create ROI information display with modern styling."""
        colors = get_theme_colors()
        
        # Add spacing
        spacer = tk.Frame(self.inner_frame, bg=colors['panel_bg'], height=15)
        spacer.pack(fill='x')
        
        # Section title
        title_label = tk.Label(
            self.inner_frame,
            text="Region of Interest",
            font=APP_CONFIG['fonts']['subheading'],
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        title_label.pack(anchor='w', pady=(0, APP_CONFIG['styling']['small_spacing']))
        
        # ROI info container with subtle background
        roi_container = tk.Frame(
            self.inner_frame,
            bg=colors['selected_bg'],
            relief='flat',
            bd=0
        )
        roi_container.pack(fill='x', pady=APP_CONFIG['styling']['small_spacing'])
        
        roi_info_frame = tk.Frame(roi_container, bg=colors['selected_bg'])
        roi_info_frame.pack(fill='x', padx=15, pady=8)

        self.roi_info_label = tk.Label(
            roi_info_frame,
            text="🎯 ROI: Not Selected (analyzing full image)",
            font=APP_CONFIG['fonts']['body'],
            fg=colors['text_secondary'],
            bg=colors['selected_bg']
        )
        self.roi_info_label.pack(anchor='w')

    def _execute_callback(self, callback_key: str):
        """Execute callback if it exists."""
        if callback_key in self.callbacks:
            self.callbacks[callback_key]()

    def _on_spectrum_changed(self, event=None):
        """Handle spectrum selection change."""
        spectrum_type = self.spectrum_var.get()

        # Show/hide control parameters
        if spectrum_type == 'controlled':
            self.control_params_frame.pack(fill='x', pady=(10, 0))
        else:
            self.control_params_frame.pack_forget()

        # Notify parent
        self._execute_callback('spectrum_changed')

    def update_state(self, state: str):
        """
        Update button states based on application state.

        Args:
            state: Current application state
        """
        self.current_state = state

        # Define button states for each application state
        state_configs = {
            'no_image': {
                'enabled': ['load_btn', 'screenshot_btn', 'help_btn', 'reset_btn'],
                'disabled': ['roi_btn', 'analyze_btn', 'quality_map_btn', 'results_btn', 'save_btn', 'reset_display_btn',
                            'zoom_in_btn', 'zoom_out_btn', 'zoom_fit_btn', 'zoom_actual_btn'],
                'special': {}
            },
            'image_loaded': {
                'enabled': ['load_btn', 'screenshot_btn', 'roi_btn', 'analyze_btn', 'help_btn', 'reset_btn', 'reset_display_btn',
                            'zoom_in_btn', 'zoom_out_btn', 'zoom_fit_btn', 'zoom_actual_btn'],
                'disabled': ['quality_map_btn', 'results_btn', 'save_btn'],
                'special': {'roi_btn': {'bg': '#9b59b6', 'text': '🎯 Select ROI'}}
            },
            'roi_selected': {
                'enabled': ['load_btn', 'screenshot_btn', 'roi_btn', 'analyze_btn', 'help_btn', 'reset_btn', 'reset_display_btn',
                            'zoom_in_btn', 'zoom_out_btn', 'zoom_fit_btn', 'zoom_actual_btn'],
                'disabled': ['quality_map_btn', 'results_btn', 'save_btn'],
                'special': {'roi_btn': {'bg': '#9b59b6', 'text': '🎯 New ROI'}}
            },
            'analyzing': {
                'enabled': ['load_btn', 'screenshot_btn', 'help_btn', 'reset_btn',
                            'zoom_in_btn', 'zoom_out_btn', 'zoom_fit_btn', 'zoom_actual_btn'],
                'disabled': ['roi_btn', 'quality_map_btn', 'results_btn', 'save_btn', 'reset_display_btn'],
                'special': {'analyze_btn': {'state': 'disabled', 'text': '🔬 Analyzing...'}}
            },
            'analysis_complete': {
                'enabled': ['load_btn', 'screenshot_btn', 'roi_btn', 'analyze_btn', 'quality_map_btn', 'results_btn',
                            'save_btn', 'help_btn', 'reset_btn', 'reset_display_btn',
                            'zoom_in_btn', 'zoom_out_btn', 'zoom_fit_btn', 'zoom_actual_btn'],
                'disabled': [],
                'special': {
                    'analyze_btn': {'text': '🔬 Analyze'},
                    'roi_btn': {'text': '🎯 New ROI'}
                }
            }
        }

        if state in state_configs:
            config = state_configs[state]

            # Enable buttons
            for btn_id in config['enabled']:
                if btn_id in self.buttons:
                    self.buttons[btn_id].config(state='normal')

            # Disable buttons
            for btn_id in config['disabled']:
                if btn_id in self.buttons:
                    self.buttons[btn_id].config(state='disabled')

            # Apply special configurations
            for btn_id, special_config in config['special'].items():
                if btn_id in self.buttons:
                    self.buttons[btn_id].config(**special_config)

    def update_roi_info(self, roi_info: str):
        """
        Update ROI information display.

        Args:
            roi_info: ROI information string to display
        """
        self.roi_info_label.config(text=roi_info)

    def get_selected_spectrum(self) -> str:
        """Get currently selected spectrum type."""
        return self.spectrum_var.get()

    def get_control_parameters(self) -> Dict[str, Any]:
        """Get control analysis parameters."""
        return {
            'facet_size': int(self.control_params['facet_size'].get()),
            'point_distance': int(self.control_params['point_distance'].get())
        }

    def set_quality_map_active(self, active: bool):
        """
        Set quality map button appearance based on active state.

        Args:
            active: Whether quality map is currently active
        """
        if 'quality_map_btn' in self.buttons:
            if active:
                self.buttons['quality_map_btn'].config(bg='#e74c3c')  # Red when active
            else:
                self.buttons['quality_map_btn'].config(bg='#2ecc71')  # Green when inactive

    def update_zoom_level(self, zoom_level: float):
        """
        Update zoom level display.

        Args:
            zoom_level: Current zoom level (1.0 = 100%)
        """
        percentage = int(zoom_level * 100)
        self.zoom_level_var.set(f"{percentage}%")