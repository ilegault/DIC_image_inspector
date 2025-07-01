# ui/components/control_panel.py - Clean UI Component

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Any
from utils.constants import APP_CONFIG


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
        self.spectrum_var = tk.StringVar(value='custom_dic')
        self.zeiss_params = {
            'facet_size': tk.StringVar(value='19'),
            'point_distance': tk.StringVar(value='4')
        }

        self._create_panel()

    def _create_panel(self):
        """Create the control panel UI."""
        # Main control frame
        self.control_frame = tk.Frame(
            self.parent,
            bg=APP_CONFIG['colors']['panel_bg'],
            relief='raised',
            bd=2
        )
        self.control_frame.pack(fill='x', padx=10, pady=5)

        # Create sections
        self._create_primary_controls()
        self._create_secondary_controls()
        self._create_spectrum_controls()
        self._create_roi_info_section()

    def _create_primary_controls(self):
        """Create primary control buttons."""
        primary_frame = tk.Frame(self.control_frame, bg=APP_CONFIG['colors']['panel_bg'])
        primary_frame.pack(pady=5)

        # Primary buttons configuration
        primary_buttons = [
            ('load_btn', "📁 Load Image", '#3498db', 'load_image'),
            ('screenshot_btn', "📸 Screenshot", '#e67e22', 'take_screenshot'),
            ('roi_btn', "🎯 Select ROI", '#9b59b6', 'select_roi'),
            ('analyze_btn', "🔬 Analyze", '#27ae60', 'analyze_image')
        ]

        for btn_id, text, color, callback_key in primary_buttons:
            btn = tk.Button(
                primary_frame,
                text=text,
                bg=color,
                fg='white',
                font=('Arial', 12, 'bold'),
                padx=20,
                pady=5,
                command=lambda k=callback_key: self._execute_callback(k)
            )
            btn.pack(side='left', padx=5)
            self.buttons[btn_id] = btn

    def _create_secondary_controls(self):
        """Create secondary control buttons."""
        secondary_frame = tk.Frame(self.control_frame, bg=APP_CONFIG['colors']['panel_bg'])
        secondary_frame.pack(pady=5)

        # Secondary buttons configuration
        secondary_buttons = [
            ('quality_map_btn', "🗺️ Quality Map", '#2ecc71', 'toggle_quality_map'),
            ('results_btn', "📊 Show Results", '#8e44ad', 'show_results'),
            ('save_btn', "💾 Save Report", '#7f8c8d', 'save_report'),
            ('help_btn', "❓ Help", '#6c7b7f', 'show_help'),
            ('reset_btn', "🔄 Reset", '#e74c3c', 'reset_application')
        ]

        for btn_id, text, color, callback_key in secondary_buttons:
            btn = tk.Button(
                secondary_frame,
                text=text,
                bg=color,
                fg='white',
                font=('Arial', 12, 'bold'),
                padx=20,
                pady=5,
                command=lambda k=callback_key: self._execute_callback(k)
            )
            btn.pack(side='left', padx=5)
            self.buttons[btn_id] = btn

    def _create_spectrum_controls(self):
        """Create spectrum selection controls."""
        spectrum_frame = tk.Frame(self.control_frame, bg=APP_CONFIG['colors']['panel_bg'])
        spectrum_frame.pack(pady=5)

        # Spectrum selection
        spectrum_label = tk.Label(
            spectrum_frame,
            text="Methods:",
            font=('Arial', 10),
            fg=APP_CONFIG['colors']['text_primary'],
            bg=APP_CONFIG['colors']['panel_bg']
        )
        spectrum_label.pack(side='left', padx=5)

        spectrum_options = [
            'custom_dic',
            'zeiss_style_dic'
        ]

        self.spectrum_combo = ttk.Combobox(
            spectrum_frame,
            textvariable=self.spectrum_var,
            values=spectrum_options,
            state='readonly',
            width=15,
            font=('Arial', 9)
        )
        self.spectrum_combo.pack(side='left', padx=5)
        self.spectrum_combo.bind('<<ComboboxSelected>>', self._on_spectrum_changed)

        # ZEISS parameters (initially hidden)
        self._create_zeiss_parameters(spectrum_frame)

    def _create_zeiss_parameters(self, parent):
        """Create ZEISS-specific parameter controls."""
        self.zeiss_frame = tk.Frame(parent, bg=APP_CONFIG['colors']['panel_bg'])

        # Title
        zeiss_title = tk.Label(
            self.zeiss_frame,
            text="📐 ZEISS Parameters:",
            font=('Arial', 10, 'bold'),
            fg='#3498db',
            bg=APP_CONFIG['colors']['panel_bg']
        )
        zeiss_title.pack(side='left', padx=5)

        # Facet size
        tk.Label(
            self.zeiss_frame,
            text="Facet:",
            font=('Arial', 9),
            fg=APP_CONFIG['colors']['text_secondary'],
            bg=APP_CONFIG['colors']['panel_bg']
        ).pack(side='left', padx=(15, 2))

        facet_spinbox = tk.Spinbox(
            self.zeiss_frame,
            from_=11,
            to=51,
            increment=2,
            textvariable=self.zeiss_params['facet_size'],
            width=4,
            font=('Arial', 8)
        )
        facet_spinbox.pack(side='left', padx=2)

        tk.Label(
            self.zeiss_frame,
            text="px",
            font=('Arial', 8),
            fg=APP_CONFIG['colors']['text_muted'],
            bg=APP_CONFIG['colors']['panel_bg']
        ).pack(side='left', padx=(0, 10))

        # Point distance
        tk.Label(
            self.zeiss_frame,
            text="Step:",
            font=('Arial', 9),
            fg=APP_CONFIG['colors']['text_secondary'],
            bg=APP_CONFIG['colors']['panel_bg']
        ).pack(side='left', padx=(10, 2))

        step_spinbox = tk.Spinbox(
            self.zeiss_frame,
            from_=2,
            to=20,
            increment=1,
            textvariable=self.zeiss_params['point_distance'],
            width=4,
            font=('Arial', 8)
        )
        step_spinbox.pack(side='left', padx=2)

        tk.Label(
            self.zeiss_frame,
            text="px",
            font=('Arial', 8),
            fg=APP_CONFIG['colors']['text_muted'],
            bg=APP_CONFIG['colors']['panel_bg']
        ).pack(side='left', padx=(0, 10))

        # Info label
        tk.Label(
            self.zeiss_frame,
            text="(Smaller values = higher density, slower analysis)",
            font=('Arial', 8),
            fg=APP_CONFIG['colors']['text_muted'],
            bg=APP_CONFIG['colors']['panel_bg']
        ).pack(side='left', padx=5)

    def _create_roi_info_section(self):
        """Create ROI information display."""
        roi_info_frame = tk.Frame(self.control_frame, bg=APP_CONFIG['colors']['panel_bg'])
        roi_info_frame.pack(pady=5)

        self.roi_info_label = tk.Label(
            roi_info_frame,
            text="ROI: Not Selected (analyzing full image)",
            font=('Arial', 10),
            fg=APP_CONFIG['colors']['text_secondary'],
            bg=APP_CONFIG['colors']['panel_bg']
        )
        self.roi_info_label.pack()

    def _execute_callback(self, callback_key: str):
        """Execute callback if it exists."""
        if callback_key in self.callbacks:
            self.callbacks[callback_key]()

    def _on_spectrum_changed(self, event=None):
        """Handle spectrum selection change."""
        spectrum_type = self.spectrum_var.get()

        # Show/hide ZEISS parameters
        if spectrum_type == 'zeiss_style_dic':
            self.zeiss_frame.pack(after=self.spectrum_combo, pady=2, fill='x')
        else:
            self.zeiss_frame.pack_forget()

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
                'enabled': ['load_btn', 'screenshot_btn', 'help_btn'],
                'disabled': ['roi_btn', 'analyze_btn', 'quality_map_btn', 'results_btn', 'save_btn'],
                'special': {}
            },
            'image_loaded': {
                'enabled': ['load_btn', 'screenshot_btn', 'roi_btn', 'analyze_btn', 'help_btn', 'reset_btn'],
                'disabled': ['quality_map_btn', 'results_btn', 'save_btn'],
                'special': {'roi_btn': {'bg': '#9b59b6', 'text': '🎯 Select ROI'}}
            },
            'roi_selected': {
                'enabled': ['load_btn', 'screenshot_btn', 'roi_btn', 'analyze_btn', 'help_btn', 'reset_btn'],
                'disabled': ['quality_map_btn', 'results_btn', 'save_btn'],
                'special': {'roi_btn': {'bg': '#9b59b6', 'text': '🎯 New ROI'}}
            },
            'analyzing': {
                'enabled': ['load_btn', 'screenshot_btn', 'help_btn'],
                'disabled': ['roi_btn', 'quality_map_btn', 'results_btn', 'save_btn'],
                'special': {'analyze_btn': {'state': 'disabled', 'text': '🔬 Analyzing...'}}
            },
            'analysis_complete': {
                'enabled': ['load_btn', 'screenshot_btn', 'roi_btn', 'analyze_btn', 'quality_map_btn', 'results_btn',
                            'save_btn', 'help_btn', 'reset_btn'],
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

    def get_zeiss_parameters(self) -> Dict[str, Any]:
        """Get ZEISS analysis parameters."""
        return {
            'facet_size': int(self.zeiss_params['facet_size'].get()),
            'point_distance': int(self.zeiss_params['point_distance'].get())
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