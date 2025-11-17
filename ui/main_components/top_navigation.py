"""
Top navigation bar component for DIC Image Quality Inspector.

This module implements the navigation bar containing zoom controls, analysis method
selector, and theme toggle button. It provides quick access to frequently used
display and analysis options in a compact horizontal layout.

Usage:
    from ui.main_components.top_navigation import TopNavigationBar

    nav_bar = TopNavigationBar(parent, callbacks={
        'zoom_in': on_zoom_in,
        'zoom_out': on_zoom_out,
        'toggle_theme': on_theme_toggle
    })
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable
from utils.constants import APP_CONFIG, get_theme_colors


class TopNavigationBar:
    """
    Top navigation bar component for DIC Quality Inspector.
    
    Contains zoom controls and analysis method selector for easy access.
    """

    def __init__(self, parent: tk.Widget, callbacks: Dict[str, Callable]):
        """
        Initialize top navigation bar.

        Args:
            parent: Parent widget
            callbacks: Dictionary of callback functions for each action
        """
        self.parent = parent
        self.callbacks = callbacks

        # UI elements
        self.buttons = {}
        self.spectrum_var = tk.StringVar(value='optimized')
        self.zoom_level_var = tk.StringVar(value="100%")

        self._create_navigation_bar()

    def _create_navigation_bar(self):
        """Create the top navigation bar with zoom controls and analysis method selector."""
        colors = get_theme_colors()

        # Main navigation bar frame
        self.nav_frame = tk.Frame(
            self.parent,
            bg=colors['panel_bg'],
            relief='flat',
            bd=0,
            height=50
        )
        self.nav_frame.pack(fill='x', padx=0, pady=(0, 8))
        self.nav_frame.pack_propagate(False)

        # Add subtle border at bottom
        border = tk.Frame(self.nav_frame, bg=colors['panel_border'], height=1)
        border.pack(side='bottom', fill='x')

        # Inner content frame with padding
        content_frame = tk.Frame(self.nav_frame, bg=colors['panel_bg'])
        content_frame.pack(fill='both', expand=True, padx=12, pady=6)

        # Left side: Zoom controls
        zoom_section = tk.Frame(content_frame, bg=colors['panel_bg'])
        zoom_section.pack(side='left')

        # Zoom controls title
        zoom_title = tk.Label(
            zoom_section,
            text="Zoom:",
            font=APP_CONFIG['fonts']['small_bold'],
            fg=colors['text_secondary'],
            bg=colors['panel_bg']
        )
        zoom_title.pack(side='left', padx=(0, 8))

        # Zoom buttons in horizontal layout
        zoom_buttons_frame = tk.Frame(zoom_section, bg=colors['panel_bg'])
        zoom_buttons_frame.pack(side='left', padx=(0, 12))

        zoom_buttons = [
            ('zoom_in_btn', "➕", colors.get('btn_info', '#3b82f6'), 'zoom_in'),
            ('zoom_out_btn', "➖", colors.get('btn_info', '#3b82f6'), 'zoom_out'),
            ('zoom_actual_btn', "1:1", colors.get('btn_neutral', '#64748b'), 'zoom_actual')
        ]

        for i, (btn_id, text, color, callback_key) in enumerate(zoom_buttons):
            btn = self._create_compact_button(
                zoom_buttons_frame, text, color,
                command=lambda k=callback_key: self._execute_callback(k)
            )
            btn.pack(side='left', padx=1)
            self.buttons[btn_id] = btn

        # Zoom level display
        zoom_label = tk.Label(
            zoom_section,
            textvariable=self.zoom_level_var,
            font=('Segoe UI', 10, 'bold'),
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        zoom_label.pack(side='left', padx=(8, 0))

        # Right side: Analysis method selector and theme toggle
        right_section = tk.Frame(content_frame, bg=colors['panel_bg'])
        right_section.pack(side='right')

        # Analysis method section
        analysis_section = tk.Frame(right_section, bg=colors['panel_bg'])
        analysis_section.pack(side='left', padx=(0, 12))

        # Analysis method title
        method_title = tk.Label(
            analysis_section,
            text="Method:",
            font=APP_CONFIG['fonts']['small_bold'],
            fg=colors['text_secondary'],
            bg=colors['panel_bg']
        )
        method_title.pack(side='left', padx=(0, 8))

        # Analysis method selection
        spectrum_options = ['optimized', 'controlled']

        # Styled combobox
        self.spectrum_combo = ttk.Combobox(
            analysis_section,
            textvariable=self.spectrum_var,
            values=spectrum_options,
            state='readonly',
            width=12,
            font=APP_CONFIG['fonts']['small']
        )
        self.spectrum_combo.pack(side='left')
        self.spectrum_combo.bind('<<ComboboxSelected>>', self._on_spectrum_changed)

        # Apply combobox styling based on theme
        self._style_combobox()

        # Theme toggle section
        theme_section = tk.Frame(right_section, bg=colors['panel_bg'])
        theme_section.pack(side='left')

        # Theme toggle button
        theme_text = "🌙" if APP_CONFIG['theme'] == 'light' else "☀️"
        self.theme_btn = self._create_compact_button(
            theme_section, theme_text, colors.get('btn_secondary', '#6b7280'),
            command=lambda: self._execute_callback('toggle_theme')
        )
        self.theme_btn.pack(side='left')
        self.buttons['theme_btn'] = self.theme_btn

    def _create_compact_button(self, parent, text, color, command=None):
        """Create a compact modern button."""
        colors = get_theme_colors()
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief='flat',
            bd=0,
            padx=8,
            pady=4,
            cursor='hand2',
            activebackground=self._darken_color(color),
            activeforeground='white'
        )
        
        # Add hover effects
        def on_enter(e):
            btn.configure(bg=self._darken_color(color))
        
        def on_leave(e):
            btn.configure(bg=color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def _darken_color(self, color):
        """Darken a hex color for hover effect."""
        try:
            # Remove # if present
            color = color.lstrip('#')
            # Convert to RGB
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            # Darken by 20%
            darkened = tuple(max(0, int(c * 0.8)) for c in rgb)
            # Convert back to hex
            return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        except:
            return color

    def _style_combobox(self):
        """Apply theme-appropriate styling to combobox."""
        colors = get_theme_colors()
        
        try:
            style = ttk.Style()
            
            # Configure combobox with theme colors
            style.configure('TopNav.TCombobox',
                fieldbackground=colors['canvas_bg'],
                background=colors['panel_bg'],
                foreground=colors['text_primary'],
                borderwidth=1,
                relief='flat',
                arrowcolor=colors['text_primary'],
                insertcolor=colors['text_primary']
            )

            style.map('TopNav.TCombobox',
                fieldbackground=[
                    ('readonly', colors['canvas_bg']),
                    ('focus', colors['canvas_bg']),
                    ('active', colors['canvas_bg'])
                ],
                foreground=[
                    ('readonly', colors['text_primary']),
                    ('focus', colors['text_primary']),
                    ('active', colors['text_primary'])
                ],
                selectbackground=[('readonly', colors['selected_bg'])],
                selectforeground=[('readonly', colors['text_primary'])],
                background=[('active', colors['hover_bg'])],
                arrowcolor=[
                    ('active', colors['text_primary']),
                    ('focus', colors['text_primary']),
                    ('readonly', colors['text_primary'])
                ]
            )
            
            # Apply the custom style
            self.spectrum_combo.configure(style='TopNav.TCombobox')
            
        except Exception as e:
            print(f"Warning: Could not apply combobox styling: {e}")

    def _execute_callback(self, callback_key):
        """Execute a callback function if it exists."""
        if callback_key in self.callbacks and self.callbacks[callback_key]:
            try:
                self.callbacks[callback_key]()
            except Exception as e:
                print(f"Error executing callback {callback_key}: {e}")

    def _on_spectrum_changed(self, event=None):
        """Handle spectrum analysis method change."""
        # Notify the main application about the change
        self._execute_callback('spectrum_changed')
        
        # Handle control parameters visibility if needed
        spectrum_type = self.spectrum_var.get()
        # Note: Control parameters are now handled in the control panel
        # This is just for spectrum change notification

    def update_zoom_level(self, zoom_level):
        """Update the zoom level display."""
        self.zoom_level_var.set(f"{zoom_level:.0f}%")

    def get_spectrum_method(self):
        """Get the currently selected spectrum analysis method."""
        return self.spectrum_var.get()

    def set_spectrum_method(self, method):
        """Set the spectrum analysis method."""
        if method in ['optimized', 'controlled']:
            self.spectrum_var.set(method)

    def update_button_states(self, state_dict):
        """Update button states based on application state."""
        for btn_id, enabled in state_dict.items():
            if btn_id in self.buttons:
                self.buttons[btn_id].configure(state='normal' if enabled else 'disabled')

    def update_theme_button(self):
        """Update theme button icon based on current theme."""
        if 'theme_btn' in self.buttons:
            theme_text = "🌙" if APP_CONFIG['theme'] == 'light' else "☀️"
            self.buttons['theme_btn'].config(text=theme_text)