# utils/modern_styling.py - Modern UI Styling Utilities

"""
Modern styling utilities for the DIC Image Quality Inspector.
Provides consistent modern styling across all UI main_components.
"""

import tkinter as tk
from tkinter import ttk
from utils.constants import APP_CONFIG, get_theme_colors


class ModernStyleManager:
    """
    Manages modern styling for the application.
    Provides consistent styling methods and ttk style configuration.
    """
    
    def __init__(self):
        """Initialize the style manager."""
        self.style = ttk.Style()
        self._configure_ttk_styles()
    
    def _configure_ttk_styles(self):
        """Configure modern ttk styles."""
        try:
            colors = get_theme_colors()
            
            # Configure modern combobox style with proper text color handling
            self.style.configure(
                'Modern.TCombobox',
                fieldbackground=colors['canvas_bg'],
                background=colors['panel_bg'],
                foreground=colors['text_primary'],
                borderwidth=1,
                relief='flat',
                focuscolor=colors['primary'],
                selectbackground=colors['selected_bg'],
                selectforeground=colors['text_primary'],
                arrowcolor=colors['text_primary'],
                insertcolor=colors['text_primary']
            )
            
            # Configure combobox dropdown with explicit text colors
            self.style.map('Modern.TCombobox',
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
                arrowcolor=[
                    ('active', colors['text_primary']),
                    ('focus', colors['text_primary']),
                    ('readonly', colors['text_primary'])
                ]
            )
            
            # Configure modern scrollbar styles
            self.style.configure(
                'Modern.Vertical.TScrollbar',
                background=colors['panel_bg'],
                troughcolor=colors['hover_bg'],
                borderwidth=0,
                arrowcolor=colors['text_secondary'],
                darkcolor=colors['panel_bg'],
                lightcolor=colors['panel_bg']
            )
            
            # Map scrollbar states
            self.style.map('Modern.Vertical.TScrollbar',
                background=[('active', colors['selected_bg']), ('pressed', colors['primary'])],
                arrowcolor=[('active', colors['text_primary'])]
            )
            
            self.style.configure(
                'Modern.Horizontal.TScrollbar',
                background=colors['panel_bg'],
                troughcolor=colors['hover_bg'],
                borderwidth=0,
                arrowcolor=colors['text_secondary'],
                darkcolor=colors['panel_bg'],
                lightcolor=colors['panel_bg']
            )
            
            # Map horizontal scrollbar states
            self.style.map('Modern.Horizontal.TScrollbar',
                background=[('active', colors['selected_bg']), ('pressed', colors['primary'])],
                arrowcolor=[('active', colors['text_primary'])]
            )
            
            # Configure modern progressbar style
            self.style.configure(
                'Modern.TProgressbar',
                background=colors['primary'],
                troughcolor=colors['hover_bg'],
                borderwidth=0,
                lightcolor=colors['primary'],
                darkcolor=colors['primary']
            )
            
            # Configure modern frame style
            self.style.configure(
                'Modern.TFrame',
                background=colors['panel_bg'],
                borderwidth=0,
                relief='flat'
            )
            
            # Configure modern label style
            self.style.configure(
                'Modern.TLabel',
                background=colors['panel_bg'],
                foreground=colors['text_primary']
            )
            
        except Exception as e:
            print(f"Warning: Could not configure ttk styles: {e}")
    
    @staticmethod
    def create_modern_button(parent, text, bg_color, command=None, size='normal', style='primary'):
        """
        Create a modern styled button.
        
        Args:
            parent: Parent widget
            text: Button text
            bg_color: Background color
            command: Button command
            size: Button size ('small', 'normal', 'large')
            style: Button style ('primary', 'secondary', 'success', 'warning', 'danger')
        
        Returns:
            tk.Button: Configured modern button
        """
        # Button styling based on size
        if size == 'large':
            font = APP_CONFIG['fonts']['button_large']
            padx = APP_CONFIG['styling']['button_padding_x'] + 5
            pady = APP_CONFIG['styling']['button_padding_y'] + 2
        elif size == 'small':
            font = APP_CONFIG['fonts']['small_bold']
            padx = APP_CONFIG['styling']['button_padding_x'] - 5
            pady = APP_CONFIG['styling']['button_padding_y'] - 2
        else:
            font = APP_CONFIG['fonts']['button']
            padx = APP_CONFIG['styling']['button_padding_x']
            pady = APP_CONFIG['styling']['button_padding_y']
        
        # Get colors based on style
        colors = ModernStyleManager._get_button_colors(style)
        if bg_color:  # Override with provided color
            colors['bg'] = bg_color
            colors['hover'] = ModernStyleManager._get_hover_color(bg_color)
        
        btn = tk.Button(
            parent,
            text=text,
            bg=colors['bg'],
            fg='white',
            font=font,
            padx=padx,
            pady=pady,
            relief='flat',
            bd=0,
            cursor='hand2',
            command=command,
            activebackground=colors['hover'],
            activeforeground='white'
        )
        
        # Add hover effects
        def on_enter(e):
            btn.configure(bg=colors['hover'])
        
        def on_leave(e):
            btn.configure(bg=colors['bg'])
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    @staticmethod
    def _get_button_colors(style):
        """Get button colors for a given style."""
        colors = get_theme_colors()  # Use this instead of APP_CONFIG['colors']

        color_map = {
            'primary': {
                'bg': colors['btn_primary'],  # Instead of APP_CONFIG['colors']['btn_primary']
                'hover': colors['btn_primary_hover']
            },
            'secondary': {
                'bg': colors['btn_secondary'],
                'hover': colors['btn_secondary_hover']
            },
            'success': {
                'bg': colors['btn_success'],
                'hover': colors['btn_success_hover']
            },
            'warning': {
                'bg': colors['btn_warning'],
                'hover': colors['btn_warning_hover']
            },
            'danger': {
                'bg': colors['btn_danger'],
                'hover': colors['btn_danger_hover']
            }
        }
        return color_map.get(style, color_map['primary'])
    
    @staticmethod
    def _get_hover_color(base_color):
        """Get hover color for a button."""
        colors = get_theme_colors()  # Add this line

        hover_colors = {
            colors['btn_primary']: colors['btn_primary_hover'],  # Use colors[] instead of APP_CONFIG['colors']
            colors['btn_secondary']: colors['btn_secondary_hover'],
            colors['btn_success']: colors['btn_success_hover'],
            colors['btn_warning']: colors['btn_warning_hover'],
            colors['btn_danger']: colors['btn_danger_hover'],
            '#3498db': '#2563eb',  # Legacy blue
            '#e67e22': '#d97706',  # Legacy orange
            '#9b59b6': '#7c3aed',  # Legacy purple
            '#27ae60': '#059669',  # Legacy green
            '#2ecc71': '#059669',  # Legacy green
            '#8e44ad': '#7c3aed',  # Legacy purple
            '#7f8c8d': '#4b5563',  # Legacy gray
            '#6c7b7f': '#4b5563',  # Legacy gray
            '#f39c12': '#d97706',  # Legacy orange
            '#e74c3c': '#dc2626'   # Legacy red
        }
        return hover_colors.get(base_color, base_color)
    
    @staticmethod
    def create_modern_frame(parent, bg_color=None, padding=True, border=False):
        """
        Create a modern styled frame.
        
        Args:
            parent: Parent widget
            bg_color: Background color (defaults to panel_bg)
            padding: Whether to add padding
            border: Whether to add a subtle border
        
        Returns:
            tk.Frame: Configured modern frame
        """
        if bg_color is None:
            bg_color = APP_CONFIG['colors']['panel_bg']
        
        frame = tk.Frame(
            parent,
            bg=bg_color,
            relief='flat',
            bd=0
        )
        
        if border:
            # Add a subtle border frame
            border_frame = tk.Frame(
                parent,
                bg=APP_CONFIG['colors']['panel_border'],
                relief='flat',
                bd=0
            )
            frame = tk.Frame(
                border_frame,
                bg=bg_color,
                relief='flat',
                bd=0
            )
            if padding:
                frame.pack(fill='both', expand=True, padx=1, pady=1)
            else:
                frame.pack(fill='both', expand=True)
            return border_frame, frame
        
        return frame
    
    @staticmethod
    def create_modern_label(parent, text, font_type='body', color_type='primary', bg_color=None):
        """
        Create a modern styled label.
        
        Args:
            parent: Parent widget
            text: Label text
            font_type: Font type from APP_CONFIG['fonts']
            color_type: Color type ('primary', 'secondary', 'muted', 'accent')
            bg_color: Background color (defaults to panel_bg)
        
        Returns:
            tk.Label: Configured modern label
        """
        if bg_color is None:
            bg_color = APP_CONFIG['colors']['panel_bg']
        
        # Get font
        font = APP_CONFIG['fonts'].get(font_type, APP_CONFIG['fonts']['body'])
        
        # Get text color
        color_map = {
            'primary': APP_CONFIG['colors']['text_primary'],
            'secondary': APP_CONFIG['colors']['text_secondary'],
            'muted': APP_CONFIG['colors']['text_muted'],
            'accent': APP_CONFIG['colors']['text_accent']
        }
        text_color = color_map.get(color_type, APP_CONFIG['colors']['text_primary'])
        
        label = tk.Label(
            parent,
            text=text,
            font=font,
            fg=text_color,
            bg=bg_color,
            relief='flat',
            bd=0
        )
        
        return label
    
    @staticmethod
    def apply_modern_scrollbars(canvas, parent):
        """
        Apply modern styled scrollbars to a canvas.
        
        Args:
            canvas: Canvas widget
            parent: Parent widget for scrollbars
        
        Returns:
            tuple: (vertical_scrollbar, horizontal_scrollbar)
        """
        style_manager = ModernStyleManager()
        
        v_scrollbar = ttk.Scrollbar(
            parent, 
            orient='vertical', 
            command=canvas.yview,
            style='Modern.Vertical.TScrollbar'
        )
        h_scrollbar = ttk.Scrollbar(
            parent, 
            orient='horizontal', 
            command=canvas.xview,
            style='Modern.Horizontal.TScrollbar'
        )
        
        canvas.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        return v_scrollbar, h_scrollbar


# Global style manager instance
_style_manager = None

def get_style_manager():
    """Get the global style manager instance."""
    global _style_manager
    if _style_manager is None:
        _style_manager = ModernStyleManager()
    return _style_manager


def apply_modern_theme():
    """Apply modern theme to the application."""
    get_style_manager()


def toggle_theme():
    """Toggle between light and dark themes."""
    from utils.constants import set_theme, get_current_theme
    current = get_current_theme()
    new_theme = 'dark' if current == 'light' else 'light'
    set_theme(new_theme)
    
    # Reinitialize style manager with new theme
    global _style_manager
    _style_manager = ModernStyleManager()
    
    return new_theme