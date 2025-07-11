# ui/components/control_panel.py - Fixed UI Component with Dark Mode

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Any
from utils.constants import APP_CONFIG, get_theme_colors, set_theme
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
        self.dark_mode = APP_CONFIG['theme'] == 'dark'

        # UI elements
        self.buttons = {}
        self.spectrum_var = tk.StringVar(value='optimized')
        self.control_params = {
            'step_size': tk.StringVar(value='4'),
            'subset_size': tk.StringVar(value='19')
        }

        self._create_panel()

    def _create_panel(self):
        """Create the control panel UI with modern styling and scroll functionality."""
        colors = get_theme_colors()

        # Main control frame with modern card-like appearance
        self.control_frame = tk.Frame(
            self.parent,
            bg=colors['panel_bg'],
            relief='flat',
            bd=0
        )
        self.control_frame.pack(fill='both', expand=True, padx=0, pady=APP_CONFIG['styling']['element_spacing'])

        # Create canvas and scrollbar for scrolling functionality
        self.canvas = tk.Canvas(
            self.control_frame,
            bg=colors['panel_bg'],
            highlightthickness=0,
            relief='flat',
            bd=0
        )

        self.scrollbar = tk.Scrollbar(
            self.control_frame,
            orient="vertical",
            command=self.canvas.yview,
            bg=colors['panel_bg'],
            troughcolor=colors['hover_bg'],
            activebackground=colors['selected_bg'],
            width=12  # Narrower scrollbar to save space
        )

        self.scrollable_frame = tk.Frame(self.canvas, bg=colors['panel_bg'])

        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Add padding inside the scrollable panel (minimal padding for more space)
        self.inner_frame = tk.Frame(
            self.scrollable_frame,
            bg=colors['panel_bg']
        )
        self.inner_frame.pack(fill='x', padx=8, pady=8)

        # Bind mouse wheel to canvas for scrolling
        self._bind_mousewheel()

        # Create sections
        self._create_primary_controls()
        self._create_secondary_controls()
        self._create_navigation_and_analysis_controls()

    def _bind_mousewheel(self):
        """Bind mouse wheel events for scrolling."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")

        # Bind mouse wheel when entering the control panel
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)

    def _create_primary_controls(self):
        """Create primary control buttons with modern card design."""
        colors = get_theme_colors()

        # Primary Controls Card
        primary_card = self._create_modern_card(self.inner_frame, " Primary Controls")

        # Button grid for clean layout
        button_grid = tk.Frame(primary_card, bg=colors['panel_bg'])
        button_grid.pack(fill='x', padx=16, pady=16)

        # Primary buttons with clean modern styling
        primary_buttons = [
            ('load_btn', " Load Image", colors.get('btn_primary', '#2563eb'), 'load_image'),
            ('screenshot_btn', " Screenshot", colors.get('btn_info', '#3b82f6'), 'take_screenshot'),
            ('roi_btn', " Select ROI", colors.get('btn_secondary', '#6b7280'), 'select_roi'),
            ('analyze_btn', " Analyze", colors.get('btn_success', '#10b981'), 'analyze_image')
        ]

        for i, (btn_id, text, color, callback_key) in enumerate(primary_buttons):
            btn = self._create_modern_button(
                button_grid, text, color,
                command=lambda k=callback_key: self._execute_callback(k),
                style='primary'
            )
            btn.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky='ew')
            self.buttons[btn_id] = btn

        # Configure grid weights for responsive design
        button_grid.grid_columnconfigure(0, weight=1)
        button_grid.grid_columnconfigure(1, weight=1)

        # ROI Status Information
        roi_status_frame = tk.Frame(primary_card, bg=colors['hover_bg'], relief='flat', bd=0)
        roi_status_frame.pack(fill='x', padx=16, pady=(0, 16))

        roi_title = tk.Label(
            roi_status_frame,
            text=" ROI:",
            font=APP_CONFIG['fonts']['small_bold'],
            fg=colors['text_secondary'],
            bg=colors['hover_bg']
        )
        roi_title.pack(side='left', padx=(12, 8), pady=6)

        self.roi_info_label = tk.Label(
            roi_status_frame,
            text="Not Selected (analyzing full image)",
            font=APP_CONFIG['fonts']['small'],
            fg=colors['text_secondary'],
            bg=colors['hover_bg']
        )
        self.roi_info_label.pack(side='left', pady=6)

    def _create_secondary_controls(self):
        """Create secondary control buttons with modern card design."""
        colors = get_theme_colors()

        # Actions Card
        actions_card = self._create_modern_card(self.inner_frame, " Actions & Results")

        # Action buttons in organized rows
        actions_frame = tk.Frame(actions_card, bg=colors['panel_bg'])
        actions_frame.pack(fill='x', padx=16, pady=16)

        # Row 1: Analysis Results
        results_row = tk.Frame(actions_frame, bg=colors['panel_bg'])
        results_row.pack(fill='x', pady=(0, 8))

        results_buttons = [
            ('quality_map_btn', "️ Quality Map", colors.get('btn_info', '#3b82f6'), 'toggle_quality_map'),
            ('results_btn', " Show Results", colors.get('btn_primary', '#2563eb'), 'show_results'),
        ]

        for i, (btn_id, text, color, callback_key) in enumerate(results_buttons):
            btn = self._create_modern_button(
                results_row, text, color,
                command=lambda k=callback_key: self._execute_callback(k),
                style='secondary'
            )
            btn.grid(row=0, column=i, padx=4, pady=0, sticky='ew')
            self.buttons[btn_id] = btn

        results_row.grid_columnconfigure(0, weight=1)
        results_row.grid_columnconfigure(1, weight=1)

        # Row 2: File Operations
        file_row = tk.Frame(actions_frame, bg=colors['panel_bg'])
        file_row.pack(fill='x', pady=(0, 8))

        file_buttons = [
            ('save_btn', " Save Report", colors.get('btn_success', '#10b981'), 'save_report'),
            ('help_btn', " Help", colors.get('btn_neutral', '#64748b'), 'show_help'),
        ]

        for i, (btn_id, text, color, callback_key) in enumerate(file_buttons):
            btn = self._create_modern_button(
                file_row, text, color,
                command=lambda k=callback_key: self._execute_callback(k),
                style='secondary'
            )
            btn.grid(row=0, column=i, padx=4, pady=0, sticky='ew')
            self.buttons[btn_id] = btn

        file_row.grid_columnconfigure(0, weight=1)
        file_row.grid_columnconfigure(1, weight=1)

        # Row 3: System Controls
        system_row = tk.Frame(actions_frame, bg=colors['panel_bg'])
        system_row.pack(fill='x')

        # Update button text based on current theme
        theme_text = " Light Mode" if self.dark_mode else " Dark Mode"

        system_buttons = [
            ('theme_btn', theme_text, colors.get('btn_secondary', '#6b7280'), 'toggle_theme'),
            ('reset_display_btn', " Reset View", colors.get('btn_warning', '#f59e0b'), 'reset_display_results'),
        ]

        for i, (btn_id, text, color, callback_key) in enumerate(system_buttons):
            btn = self._create_modern_button(
                system_row, text, color,
                command=lambda k=callback_key: self._execute_callback(k),
                style='secondary'
            )
            btn.grid(row=0, column=i, padx=4, pady=0, sticky='ew')
            self.buttons[btn_id] = btn

        system_row.grid_columnconfigure(0, weight=1)
        system_row.grid_columnconfigure(1, weight=1)

        # Danger Zone - Full Reset (separate, prominent)
        danger_frame = tk.Frame(actions_card, bg=colors['panel_bg'])
        danger_frame.pack(fill='x', padx=16, pady=(0, 16))

        reset_btn = self._create_modern_button(
            danger_frame, " Full Reset", colors.get('btn_danger', '#ef4444'),
            command=lambda: self._execute_callback('reset_application'),
            style='danger'
        )
        reset_btn.pack(fill='x')
        self.buttons['reset_btn'] = reset_btn

    def _create_navigation_and_analysis_controls(self):
        """Create compact zoom controls with analysis method selector on the right."""
        colors = get_theme_colors()

        # Combined Navigation & Analysis Card
        nav_card = self._create_modern_card(self.inner_frame, " Navigation & Analysis")

        nav_content = tk.Frame(nav_card, bg=colors['panel_bg'])
        nav_content.pack(fill='x', padx=16, pady=16)

        # Main horizontal container
        main_container = tk.Frame(nav_content, bg=colors['panel_bg'])
        main_container.pack(fill='x')

        # Left side: Compact zoom controls
        zoom_section = tk.Frame(main_container, bg=colors['panel_bg'])
        zoom_section.pack(side='left')

        # Zoom controls title
        zoom_title = tk.Label(
            zoom_section,
            text=" Zoom:",
            font=APP_CONFIG['fonts']['small_bold'],
            fg=colors['text_secondary'],
            bg=colors['panel_bg']
        )
        zoom_title.pack(anchor='w', pady=(0, 4))

        # Very compact zoom buttons in single row
        zoom_frame = tk.Frame(zoom_section, bg=colors['panel_bg'])
        zoom_frame.pack()

        zoom_buttons = [
            ('zoom_in_btn', "➕", colors.get('btn_info', '#3b82f6'), 'zoom_in'),
            ('zoom_out_btn', "➖", colors.get('btn_info', '#3b82f6'), 'zoom_out'),
            ('zoom_actual_btn', "1:1", colors.get('btn_neutral', '#64748b'), 'zoom_actual')
        ]

        for i, (btn_id, text, color, callback_key) in enumerate(zoom_buttons):
            btn = self._create_compact_button(
                zoom_frame, text, color,
                command=lambda k=callback_key: self._execute_callback(k)
            )
            btn.pack(side='left', padx=1)  # Very tight spacing
            self.buttons[btn_id] = btn

        # Compact zoom level display
        self.zoom_level_var = tk.StringVar(value="100%")
        zoom_label = tk.Label(
            zoom_section,
            textvariable=self.zoom_level_var,
            font=('Segoe UI', 9, 'bold'),
            fg=colors['text_primary'],
            bg=colors['panel_bg']
        )
        zoom_label.pack(pady=(4, 0))

        # Right side: Analysis method selector
        analysis_section = tk.Frame(main_container, bg=colors['panel_bg'])
        analysis_section.pack(side='right', padx=(20, 0))

        # Analysis method title
        method_title = tk.Label(
            analysis_section,
            text=" Method:",
            font=APP_CONFIG['fonts']['small_bold'],
            fg=colors['text_secondary'],
            bg=colors['panel_bg']
        )
        method_title.pack(anchor='w', pady=(0, 4))

        # Analysis method selection
        method_frame = tk.Frame(analysis_section, bg=colors['panel_bg'])
        method_frame.pack()

        spectrum_options = ['optimized', 'controlled']

        # Compact styled combobox
        self.spectrum_combo = ttk.Combobox(
            method_frame,
            textvariable=self.spectrum_var,
            values=spectrum_options,
            state='readonly',
            width=12,  # Smaller width
            font=APP_CONFIG['fonts']['small']
        )
        self.spectrum_combo.pack()
        self.spectrum_combo.bind('<<ComboboxSelected>>', self._on_spectrum_changed)

        # Apply combobox styling based on theme
        self._style_combobox()

        # Control parameters frame (initially hidden)
        self.control_params_frame = tk.Frame(nav_card, bg=colors['panel_bg'])
        self._create_control_parameters()

    def _create_control_parameters(self):
        """Create control-specific parameter controls with modern styling."""
        colors = get_theme_colors()

        # Compact parameters container
        params_container = tk.Frame(
            self.control_params_frame,
            bg=colors['hover_bg'],
            relief='flat',
            bd=0
        )
        params_container.pack(fill='x', padx=8, pady=(0, 6))

        # Minimal inner padding frame
        params_inner = tk.Frame(params_container, bg=colors['hover_bg'])
        params_inner.pack(fill='x', padx=6, pady=4)

        # Compact title
        control_title = tk.Label(
            params_inner,
            text=" Parameters",
            font=APP_CONFIG['fonts']['small_bold'],
            fg=colors['primary'],
            bg=colors['hover_bg']
        )
        control_title.pack(anchor='w', pady=(0, 4))

        # Parameters in a single row for clean layout
        params_row = tk.Frame(params_inner, bg=colors['hover_bg'])
        params_row.pack(fill='x')

        # Compact parameter layout in two rows to save vertical space
        # First row: Step size
        step_row = tk.Frame(params_row, bg=colors['hover_bg'])
        step_row.pack(fill='x', pady=(0, 3))

        step_frame = tk.Frame(step_row, bg=colors['hover_bg'])
        step_frame.pack(side='left')

        tk.Label(
            step_frame,
            text="Step:",
            font=APP_CONFIG['fonts']['small'],
            fg=colors['text_secondary'],
            bg=colors['hover_bg']
        ).pack(side='left', padx=(0, 4))

        step_options = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '18', '20']
        self.step_combo = ttk.Combobox(
            step_frame,
            textvariable=self.control_params['step_size'],
            values=step_options,
            state='readonly',
            width=6,
            font=APP_CONFIG['fonts']['small']
        )
        self.step_combo.pack(side='left', padx=1)

        tk.Label(
            step_frame,
            text="px",
            font=APP_CONFIG['fonts']['small'],
            fg=colors['text_muted'],
            bg=colors['hover_bg']
        ).pack(side='left', padx=(2, 0))

        # Second row: Subset size
        subset_row = tk.Frame(params_row, bg=colors['hover_bg'])
        subset_row.pack(fill='x')

        subset_frame = tk.Frame(subset_row, bg=colors['hover_bg'])
        subset_frame.pack(side='left')

        tk.Label(
            subset_frame,
            text="Subset:",
            font=APP_CONFIG['fonts']['small'],
            fg=colors['text_secondary'],
            bg=colors['hover_bg']
        ).pack(side='left', padx=(0, 4))

        subset_options = ['11', '13', '15', '17', '19', '21', '23', '25', '27', '29', '31', '33', '35', '37', '39', '41', '43', '45', '47', '49', '51']
        self.subset_combo = ttk.Combobox(
            subset_frame,
            textvariable=self.control_params['subset_size'],
            values=subset_options,
            state='readonly',
            width=6,
            font=APP_CONFIG['fonts']['small']
        )
        self.subset_combo.pack(side='left', padx=1)

        tk.Label(
            subset_frame,
            text="px",
            font=APP_CONFIG['fonts']['small'],
            fg=colors['text_muted'],
            bg=colors['hover_bg']
        ).pack(side='left', padx=(2, 0))

    def _create_modern_card(self, parent, title):
        """Create a modern card container with title."""
        colors = get_theme_colors()

        # Card container (reduced spacing for compact design)
        card_container = tk.Frame(parent, bg=colors['background'])
        card_container.pack(fill='x', pady=6)

        # Main card with modern styling
        card = tk.Frame(
            card_container,
            bg=colors['panel_bg'],
            relief='flat',
            bd=0,
            highlightbackground=colors['panel_border'],
            highlightthickness=1
        )
        card.pack(fill='x', padx=4, pady=2)

        # Card header (compact for smaller window)
        header = tk.Frame(card, bg=colors['hover_bg'], height=32)
        header.pack(fill='x')
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text=title,
            font=('Segoe UI', 10, 'bold'),
            fg=colors['text_primary'],
            bg=colors['hover_bg']
        )
        title_label.pack(anchor='w', padx=10, pady=5)

        return card

    def _create_modern_button(self, parent, text, color, command, style='primary'):
        """Create a modern styled button with enhanced design."""
        colors = get_theme_colors()

        # Determine text color based on background
        if APP_CONFIG['theme'] == 'dark':
            fg_color = 'white'
        else:
            # Use white text on colored buttons, dark text on light buttons
            if color in [colors.get('btn_secondary', '#6b7280'), '#f3f4f6', '#e5e7eb']:
                fg_color = colors['text_primary']
            else:
                fg_color = 'white'

        btn = tk.Button(
            parent,
            text=text,
            bg=color,
            fg=fg_color,
            font=APP_CONFIG['fonts']['button'],
            padx=12,
            pady=8,
            relief='flat',
            bd=0,
            cursor='hand2',
            command=command,
            activebackground=self._get_hover_color(color),
            activeforeground=fg_color
        )

        # Add hover effects
        def on_enter(e):
            btn.configure(bg=self._get_hover_color(color))

        def on_leave(e):
            btn.configure(bg=color)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def _create_compact_button(self, parent, text, color, command):
        """Create a compact button for zoom controls."""
        colors = get_theme_colors()

        # Very compact buttons for tight layout
        btn = tk.Button(
            parent,
            text=text,
            bg=color,
            fg='white' if APP_CONFIG['theme'] == 'dark' or color != colors.get('btn_secondary', '#6b7280') else colors[
                'text_primary'],
            font=APP_CONFIG['fonts']['small_bold'],
            width=3,  # Smaller width
            padx=2,   # Less padding
            pady=4,   # Less padding
            relief='flat',
            bd=0,
            cursor='hand2',
            command=command,
            activebackground=self._get_hover_color(color),
            activeforeground='white'
        )

        # Add hover effects
        def on_enter(e):
            btn.configure(bg=self._get_hover_color(color))

        def on_leave(e):
            btn.configure(bg=color)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def _get_hover_color(self, base_color):
        """Get hover color for a button."""
        # Darken color by 20% for hover effect
        if base_color.startswith('#'):
            return self._darken_color(base_color, 0.2)
        return base_color

    def _darken_color(self, hex_color, factor=0.2):
        """Darken a hex color by a factor."""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(c * (1 - factor))) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

    def _style_combobox(self):
        """Apply modern styling to combobox based on theme."""
        colors = get_theme_colors()

        style = ttk.Style()

        # Configure combobox for both themes with explicit text colors
        style.configure(
            'Modern.TCombobox',
            fieldbackground=colors['canvas_bg'],
            background=colors['panel_bg'],
            foreground=colors['text_primary'],
            borderwidth=1,
            relief='flat',
            arrowcolor=colors['text_primary'],
            insertcolor=colors['text_primary']  # Cursor color
        )

        # Map combobox states for proper theme switching
        style.map('Modern.TCombobox',
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

        self.spectrum_combo.configure(style='Modern.TCombobox')

        # Force update the combobox to apply new colors
        self.spectrum_combo.update_idletasks()

    def _execute_callback(self, callback_key: str):
        """Execute callback if it exists."""
        if callback_key == 'toggle_theme':
            # Handle theme toggle
            self.dark_mode = not self.dark_mode
            new_theme = 'dark' if self.dark_mode else 'light'
            set_theme(new_theme)

            # Update button text
            if 'theme_btn' in self.buttons:
                new_text = " Light Mode" if self.dark_mode else " Dark Mode"
                self.buttons['theme_btn'].config(text=new_text)

            # Notify callback to refresh UI
            if 'toggle_theme' in self.callbacks:
                self.callbacks['toggle_theme']()
        elif callback_key in self.callbacks:
            self.callbacks[callback_key]()

    def _on_spectrum_changed(self, event=None):
        """Handle spectrum selection change."""
        spectrum_type = self.spectrum_var.get()

        # Show/hide control parameters
        if spectrum_type == 'controlled':
            self.control_params_frame.pack(fill='x', pady=(0, 0))
        else:
            self.control_params_frame.pack_forget()

        # Notify parent
        self._execute_callback('spectrum_changed')

    def refresh_theme(self):
        """Refresh all UI elements with new theme colors."""
        colors = get_theme_colors()

        # Update all frames including new scrollable components
        for widget in [self.control_frame, self.inner_frame, self.scrollable_frame]:
            widget.configure(bg=colors['panel_bg'])

        # Update canvas and scrollbar
        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=colors['panel_bg'])
        if hasattr(self, 'scrollbar'):
            self.scrollbar.configure(
                bg=colors['panel_bg'],
                troughcolor=colors['hover_bg'],
                activebackground=colors['selected_bg']
            )

        # Update all cards and their children
        self._update_widget_colors(self.inner_frame, colors)

        # Re-style combobox
        self._style_combobox()

        # Update comboboxes
        if hasattr(self, 'step_combo'):
            self.step_combo.configure(style='Modern.TCombobox')
        if hasattr(self, 'subset_combo'):
            self.subset_combo.configure(style='Modern.TCombobox')

        # Update button colors - recreate buttons with proper colors
        self._refresh_button_colors(colors)

    def _refresh_button_colors(self, colors):
        """Refresh button colors based on theme."""
        # Define clean modern button color mappings
        button_color_map = {
            'load_btn': colors.get('btn_primary', '#2563eb'),
            'screenshot_btn': colors.get('btn_info', '#3b82f6'),
            'roi_btn': colors.get('btn_secondary', '#6b7280'),
            'analyze_btn': colors.get('btn_success', '#10b981'),
            'quality_map_btn': colors.get('btn_info', '#3b82f6'),
            'results_btn': colors.get('btn_primary', '#2563eb'),
            'save_btn': colors.get('btn_success', '#10b981'),
            'help_btn': colors.get('btn_neutral', '#64748b'),
            'theme_btn': colors.get('btn_secondary', '#6b7280'),
            'reset_display_btn': colors.get('btn_warning', '#f59e0b'),
            'reset_btn': colors.get('btn_danger', '#ef4444'),
            'zoom_in_btn': colors.get('btn_info', '#3b82f6'),
            'zoom_out_btn': colors.get('btn_info', '#3b82f6'),
            'zoom_actual_btn': colors.get('btn_neutral', '#64748b')
        }

        # Update each button's colors
        for btn_id, color in button_color_map.items():
            if btn_id in self.buttons:
                btn = self.buttons[btn_id]
                try:
                    btn.configure(
                        bg=color,
                        activebackground=self._get_hover_color(color)
                    )
                except:
                    pass

    def _update_widget_colors(self, widget, colors):
        """Recursively update widget colors."""
        try:
            # Update frame backgrounds
            if isinstance(widget, tk.Frame):
                try:
                    current_bg = widget.cget('bg')
                    # Check if it's a hover/accent frame
                    if current_bg in ['#f9fafb', '#1e293b', '#f3f4f6', '#374151', colors.get('hover_bg')]:
                        widget.configure(bg=colors['hover_bg'])
                    else:
                        widget.configure(bg=colors['panel_bg'])
                except:
                    widget.configure(bg=colors['panel_bg'])

            # Update label colors
            elif isinstance(widget, tk.Label):
                try:
                    parent_bg = widget.master.cget('bg')
                    # Determine text color based on label content
                    text = widget.cget('text')
                    if any(keyword in text.lower() for keyword in ['zoom:', 'method:', 'roi:', 'advanced']):
                        widget.configure(bg=parent_bg, fg=colors['text_secondary'])
                    else:
                        widget.configure(bg=parent_bg, fg=colors['text_primary'])
                except:
                    widget.configure(bg=colors['panel_bg'], fg=colors['text_primary'])

            # Recursively update children
            for child in widget.winfo_children():
                self._update_widget_colors(child, colors)

        except Exception:
            pass

    def update_state(self, state: str):
        """Update button states based on application state."""
        self.current_state = state

        # Define button states for each application state
        state_configs = {
            'no_image': {
                'enabled': ['load_btn', 'screenshot_btn', 'help_btn', 'reset_btn', 'theme_btn'],
                'disabled': ['roi_btn', 'analyze_btn', 'quality_map_btn', 'results_btn', 'save_btn',
                             'reset_display_btn',
                             'zoom_in_btn', 'zoom_out_btn', 'zoom_actual_btn'],
                'special': {}
            },
            'image_loaded': {
                'enabled': ['load_btn', 'screenshot_btn', 'roi_btn', 'analyze_btn', 'help_btn', 'reset_btn',
                            'reset_display_btn',
                            'zoom_in_btn', 'zoom_out_btn', 'zoom_actual_btn', 'theme_btn'],
                'disabled': ['quality_map_btn', 'results_btn', 'save_btn'],
                'special': {'roi_btn': {'text': ' Select ROI'}}
            },
            'roi_selected': {
                'enabled': ['load_btn', 'screenshot_btn', 'roi_btn', 'analyze_btn', 'help_btn', 'reset_btn',
                            'reset_display_btn',
                            'zoom_in_btn', 'zoom_out_btn', 'zoom_actual_btn', 'theme_btn'],
                'disabled': ['quality_map_btn', 'results_btn', 'save_btn'],
                'special': {'roi_btn': {'text': ' New ROI'}}
            },
            'analyzing': {
                'enabled': ['help_btn', 'theme_btn'],
                'disabled': ['load_btn', 'screenshot_btn', 'roi_btn', 'analyze_btn', 'quality_map_btn', 'results_btn',
                             'save_btn', 'reset_btn', 'reset_display_btn', 'zoom_in_btn', 'zoom_out_btn',
                             'zoom_actual_btn'],
                'special': {'analyze_btn': {'text': ' Analyzing...'}}
            },
            'analysis_complete': {
                'enabled': ['load_btn', 'screenshot_btn', 'roi_btn', 'analyze_btn', 'quality_map_btn', 'results_btn',
                            'save_btn', 'help_btn', 'reset_btn', 'reset_display_btn', 'zoom_in_btn', 'zoom_out_btn',
                            'zoom_actual_btn', 'theme_btn'],
                'disabled': [],
                'special': {
                    'analyze_btn': {'text': ' Analyze'},
                    'roi_btn': {'text': ' New ROI'}
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
        """Update ROI information display."""
        self.roi_info_label.config(text=roi_info)

    def get_selected_spectrum(self) -> str:
        """Get currently selected spectrum type."""
        return self.spectrum_var.get()

    def get_control_parameters(self) -> Dict[str, Any]:
        """Get control analysis parameters."""
        return {
            'step_size': int(self.control_params['step_size'].get()),
            'subset_size': int(self.control_params['subset_size'].get()),
            # Legacy compatibility - map to old parameter names if needed
            'point_distance': int(self.control_params['step_size'].get()),
            'facet_size': int(self.control_params['subset_size'].get())
        }

    def set_quality_map_active(self, active: bool):
        """Set quality map button appearance based on active state."""
        if 'quality_map_btn' in self.buttons:
            colors = get_theme_colors()
            if active:
                self.buttons['quality_map_btn'].config(bg=colors.get('btn_danger', '#ef4444'))
            else:
                self.buttons['quality_map_btn'].config(bg=colors.get('info', '#3b82f6'))

    def update_zoom_level(self, zoom_level: float):
        """Update zoom level display."""
        percentage = int(zoom_level * 100)
        self.zoom_level_var.set(f"{percentage}%")