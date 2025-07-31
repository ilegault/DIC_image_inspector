# utils/constants.py - Application Constants

"""
Application-wide constants and configuration.
Centralized configuration following clean architecture principles.
"""

# Application metadata
APP_NAME = "DIC Image Quality Inspector"
APP_VERSION = "2.1.0"
APP_AUTHOR = "DIC Analysis Team"

# ===== FILE OPERATIONS CONFIGURATION =====
FILE_OPERATIONS = {
    'auto_backup': True,
    'backup_dir': 'backups',
    'max_backups': 10,
    'compress_backups': True,
    'backup_format': 'zip',
    'temp_dir': 'temp',
    'clean_temp_on_exit': True,
    'max_temp_age_hours': 24,
    'encoding': 'utf-8',

    # File format configurations
    'supported_formats': {
        'input': ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.gif', '.webp', '.ico'],
        'output': ['.txt', '.pdf', '.csv', '.png', '.jpg', '.html', '.xlsx', '.json']
    },

    'default_extensions': {
        'report': '.txt',
        'image_export': '.png',
        'data_export': '.csv'
    },

    'file_dialogs': {
        'image_load': [
            ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff;*.gif;*.webp"),
            ("All files", "*.*")
        ],
        'report_save': [
            ("Text files", "*.txt"),
            ("PDF files", "*.pdf"),
            ("HTML files", "*.html"),
            ("All files", "*.*")
        ],
        'image_export': [
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg"),
            ("TIFF files", "*.tiff"),
            ("All files", "*.*")
        ],
        'data_export': [
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx"),
            ("JSON files", "*.json"),
            ("All files", "*.*")
        ]
    }
}

# Supported image formats for file dialogs and processing
SUPPORTED_IMAGE_FORMATS = [
    ("PNG files", "*.png"),
    ("JPEG files", "*.jpg;*.jpeg"),
    ("BMP files", "*.bmp"),
    ("TIFF files", "*.tif;*.tiff"),
    ("GIF files", "*.gif"),
    ("WebP files", "*.webp"),
    ("ICO files", "*.ico"),
    ("All image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff;*.gif;*.webp;*.ico"),
    ("All files", "*.*")
]

# Default filenames
DEFAULT_FILENAMES = {
    'report': 'quality_report',
    'screenshot': 'screenshot',
    'analysis_data': 'analysis_data',
    'config': 'config.json',
    'log': 'application.log',
    'temp_image': 'temp_image',
    'roi_data': 'roi_selection',
    'quality_map': 'quality_map',
}

# Export formats
EXPORT_FORMATS = {
    'image': ['png', 'jpg', 'tiff', 'bmp'],
    'data': ['csv', 'xlsx', 'json', 'txt'],
    'report': ['pdf', 'html', 'docx', 'txt'],
    'combined': ['pdf', 'html'],
}

# ===== VALIDATION RULES =====
VALIDATION = {
    # Image validation
    'image_max_size_mb': 100,
    'image_min_size_px': 50,
    'image_max_size_px': 8192,
    'min_image_size': (50, 50),  # Minimum width, height in pixels
    'max_image_size': (8192, 8192),  # Maximum width, height in pixels
    'max_file_size': 100 * 1024 * 1024,  # 100MB maximum file size
    'supported_image_extensions': ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.gif', '.webp', '.ico'],

    # ROI validation
    'roi_min_size_px': 10,
    'roi_max_size_percent': 90,
    'min_roi_area': 100,  # Minimum ROI area in pixels

    # Analysis parameters validation
    'facet_size_min': 3,
    'facet_size_max': 200,
    'point_distance_min': 1,
    'point_distance_max': 50,
    'quality_threshold_min': 0.0,
    'quality_threshold_max': 1.0,

    # File system validation
    'max_filename_length': 255,
    'reserved_names': ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                       'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                       'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
}

# ===== CANVAS CONFIGURATION (CONSOLIDATED) =====
CANVAS = {
    'default_width': 800,
    'default_height': 600,
    'min_width': 400,
    'min_height': 300,
    'max_width': 4000,
    'max_height': 3000,
    'zoom_factor': 1.2,
    'max_zoom': 2.0,
    'min_zoom': 0.05,
    'scroll_speed': 3,
    'selection_handles_size': 8,
    'grid_spacing': 50,
    'ruler_height': 20,
    'crosshair_length': 20,
    'selection_color': '#3b82f6',
    'selection_width': 2,
    'grid_color': '#e5e7eb',
    'grid_alpha': 0.3,
}

# ===== ANALYSIS CONFIGURATION (CONSOLIDATED) =====
ANALYSIS_CONFIG = {
    'default_method': 'optimized_dic',
    'available_methods': ['dic', 'optimized_dic', 'fast_dic', 'high_quality_dic'],
    'default_facet_size': 19,
    'default_overlap': 0.5,
    'default_point_distance': 4,
    'max_facet_size': 100,
    'min_facet_size': 5,
    'max_point_distance': 20,
    'min_point_distance': 1,
    'interpolation_method': 'bicubic',
    'correlation_threshold': 0.6,
    'max_iterations': 100,
    'convergence_tolerance': 1e-6,
    'multiprocessing': True,
    'max_workers': None,  # Auto-detect CPU cores
    'chunk_size': 1000,
    'memory_limit_mb': 2048,
    'default_spectrum': 'optimized',
    'available_spectra': ['optimized', 'jet', 'viridis', 'plasma', 'inferno'],
}

# ===== QUALITY ASSESSMENT =====
QUALITY_THRESHOLDS = {
    'excellent': {'min': 0.9, 'color': '#10b981', 'label': 'Excellent'},
    'good': {'min': 0.7, 'color': '#3b82f6', 'label': 'Good'},
    'fair': {'min': 0.5, 'color': '#f59e0b', 'label': 'Fair'},
    'poor': {'min': 0.3, 'color': '#ef4444', 'label': 'Poor'},
    'very_poor': {'min': 0.0, 'color': '#7f1d1d', 'label': 'Very Poor'},
}

# ===== COLOR SPECTRUMS =====
COLOR_SPECTRUMS = {
    'optimized': {
        'name': 'Optimized DIC',
        'description': 'Optimized for DIC analysis visualization',
        'colors': [
            (0, 0, 0, "Unusable: No correlation possible"),        # Black for worst
            (139, 0, 0, "Poor: Unreliable correlation"),           # Dark red
            (255, 140, 0, "Acceptable: Usable with uncertainty"),  # Orange
            (255, 255, 0, "Good: Good correlation quality"),       # Yellow
            (0, 255, 255, "Very Good: Very reliable"),             # Cyan
            (0, 255, 0, "Excellent: Optimal pattern")              # Green for best
        ]
    },
    'controlled': {
        'name': 'Controlled Pattern Quality',
        'description': 'High-precision pattern quality assessment',
        'colors': [
            (0, 0, 0, "Unusable: No correlation possible"),        # Black for worst
            (139, 0, 0, "Poor: Unreliable correlation"),           # Dark red
            (255, 140, 0, "Acceptable: Usable with uncertainty"),  # Orange
            (255, 255, 0, "Good: Good correlation quality"),       # Yellow
            (0, 255, 255, "Very Good: Very reliable"),             # Cyan
            (0, 255, 0, "Excellent: Optimal pattern")              # Green for best
        ]
    },
    'custom_dic': {
        'name': 'Custom DIC Assessment',
        'description': 'Custom colormap for DIC quality visualization',
        'colors': [
            (0, 0, 0, "Critical: Not suitable for DIC"),
            (255, 0, 0, "Minimum: Threshold for DIC"),
            (255, 127, 0, "Good: Acceptable for DIC"),
            (255, 255, 0, "Very Good: Good for DIC"),
            (0, 255, 0, "Excellent: Excellent for DIC"),
            (0, 0, 255, "Perfect: Ideal for DIC")
        ]
    }
}

# ===== MESSAGES =====
ERROR_MESSAGES = {
    'file_not_found': 'The specified file could not be found.',
    'file_not_supported': 'The file format is not supported.',
    'file_too_large': 'The file size exceeds the maximum limit.',
    'file_corrupted': 'The file appears to be corrupted or invalid.',
    'memory_error': 'Insufficient memory to process the image.',
    'analysis_failed': 'Analysis failed. Please check your parameters.',
    'roi_invalid': 'The selected ROI is invalid or too small.',
    'roi_not_selected': 'Please select a region of interest first.',
    'no_image_loaded': 'No image is currently loaded.',
    'save_failed': 'Failed to save the file.',
    'export_failed': 'Failed to export the data.',
    'permission_denied': 'Permission denied. Check file permissions.',
    'disk_space_low': 'Insufficient disk space.',
    'gpu_not_available': 'GPU acceleration is not available.',
    'invalid_parameters': 'Invalid analysis parameters provided.',
}

SUCCESS_MESSAGES = {
    'image_loaded': 'Image loaded successfully.',
    'analysis_complete': 'Analysis completed successfully.',
    'roi_selected': 'Region of interest selected.',
    'file_saved': 'File saved successfully.',
    'data_exported': 'Data exported successfully.',
    'report_generated': 'Report generated successfully.',
    'screenshot_taken': 'Screenshot captured successfully.',
    'settings_saved': 'Settings saved successfully.',
    'backup_created': 'Backup created successfully.',
    'cache_cleared': 'Cache cleared successfully.',
}

# ===== SYSTEM CONFIGURATION =====
LIMITS = {
    'max_concurrent_analyses': 3,
    'max_undo_history': 20,
    'max_recent_files': 15,
    'max_log_size_mb': 10,
    'max_cache_size_mb': 500,
    'session_timeout_minutes': 120,
    'auto_save_interval_minutes': 5,
    'progress_update_interval_ms': 100,
}

PERFORMANCE = {
    'enable_gpu_acceleration': True,
    'enable_multiprocessing': True,
    'enable_caching': True,
    'enable_lazy_loading': True,
    'enable_image_compression': True,
    'compression_quality': 85,
    'thumbnail_size': 256,
    'preview_quality': 'medium',
    'memory_optimization': True,
    'garbage_collection_interval': 60,  # seconds
    'max_image_display_size': 4096,  # Max dimension for display
    'thread_pool_size': 4,  # Number of worker threads
}

DEBUG = {
    'enable_logging': True,
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'log_to_file': True,
    'log_to_console': True,
    'enable_profiling': False,
    'profile_memory': False,
    'enable_debug_mode': False,
    'show_debug_info': False,
    'measure_performance': False,
    
    # Fine-grained logging control
    'pil_log_level': 'WARNING',  # Suppress noisy PIL debug messages
    'third_party_log_level': 'WARNING',  # General third-party library logging
    'app_debug_modules': [],  # Specific modules to keep at DEBUG level
}

# ===== VERSION INFORMATION =====
VERSION_INFO = {
    'major': 2,
    'minor': 1,
    'patch': 0,
    'build': 1,
    'release_date': '2024-01-01',
    'python_min_version': '3.8',
    'dependencies': {
        'numpy': '>=1.20.0',
        'opencv-python': '>=4.5.0',
        'pillow': '>=8.0.0',
        'matplotlib': '>=3.3.0',
        'scipy': '>=1.6.0',
        'tkinter': 'built-in',
    }
}

# ===== UI CONFIGURATION =====
APP_CONFIG = {
    'theme': 'light',  # Default theme

    # Window configuration
    'window': {
        'min_width': 800,
        'min_height': 500,
        'default_width': 960,
        'default_height': 750,
        'resizable': True,
        'icon': None,  # Set to icon path if available
    },

    # ROI (Region of Interest) configuration
    'roi': {
        'normal_color': '#2563eb',
        'selection_color': '#dc2626',
        'line_width': 2,
        'min_points': 3,
        'selection_tolerance': 5
    },

    # Accessibility configuration
    'accessibility': {
        'high_contrast_mode': False,
        'large_text_mode': False,
        'keyboard_navigation': True,
        'screen_reader_support': True,
        'color_blind_friendly': True,
        'minimum_contrast_ratio': 4.5,
        'focus_indicators': True,
        'reduced_motion': False,
    },

    # Colors dictionary
    'colors': {
        # Modern accent colors (same for both themes)
        'primary': '#2563eb',
        'secondary': '#64748b',
        'success': '#10B981',
        'warning': '#d97706',
        'danger': '#dc2626',
        'info': '#0891b2',
        'purple': '#7c3aed',
        'pink': '#ec4899',

        # Modern Clean Button Colors
        'btn_primary': '#2563eb',
        'btn_primary_hover': '#1d4ed8',
        'btn_secondary': '#6b7280',
        'btn_secondary_hover': '#4b5563',
        'btn_success': '#10b981',
        'btn_success_hover': '#059669',
        'btn_warning': '#f59e0b',
        'btn_warning_hover': '#d97706',
        'btn_danger': '#ef4444',
        'btn_danger_hover': '#dc2626',
        'btn_info': '#3b82f6',
        'btn_info_hover': '#2563eb',
        'btn_neutral': '#64748b',
        'btn_neutral_hover': '#475569',
        'btn_disabled': '#d1d5db',
        'btn_disabled_text': '#9ca3af',
        'btn_focus_ring': '#3b82f6',
        'btn_focus_ring_offset': '#ffffff',

        # Light theme colors
        'light': {
            'background': '#f8fafc',
            'panel_bg': '#ffffff',
            'panel_border': '#e5e7eb',
            'panel_shadow': '#1f293720',
            'text_primary': '#111827',
            'text_secondary': '#4b5563',
            'text_muted': '#9ca3af',
            'text_accent': '#000000',
            'status_bar': '#f3f4f6',
            'canvas_bg': '#ffffff',
            'hover_bg': '#f9fafb',
            'selected_bg': '#dbeafe',
        },

        # Dark theme colors
        'dark': {
            'background': '#0f172a',
            'panel_bg': '#1e293b',
            'panel_border': '#374151',
            'panel_shadow': '#00000060',
            'text_primary': '#f1f5f9',
            'text_secondary': '#cbd5e1',
            'text_muted': '#94a3b8',
            'text_accent': '#ffffff',
            'status_bar': '#374151',
            'canvas_bg': '#1e293b',
            'hover_bg': '#374151',
            'selected_bg': '#3730a3',
        },
    },

    # Styling configuration
    'styling': {
        'border_radius': 12,
        'card_shadow': 4,
        'card_border_width': 1,
        'button_border_radius': 6,
        'button_padding_x': 16,
        'button_padding_y': 10,
        'compact_button_size': 36,
        'card_padding': 16,
        'card_header_height': 48,
        'element_spacing': 12,
        'section_spacing': 20,
        'hover_transition': 200,
        'focus_ring_width': 2,
        'shadow_blur': 8,
        'small_button_padding_x': 12,
        'small_button_padding_y': 6,
        'large_button_padding_x': 24,
        'large_button_padding_y': 12,
        'panel_padding': 16,
        'small_spacing': 4,
    },

    # Font configuration
    'fonts': {
        'default': ('Segoe UI', 10),
        'heading': ('Segoe UI', 14, 'bold'),
        'subheading': ('Segoe UI', 12, 'bold'),
        'button': ('Segoe UI', 10),
        'small': ('Segoe UI', 9),
        'monospace': ('Consolas', 10),
        'large': ('Segoe UI', 12),
        'body': ('Segoe UI', 10),
        'title': ('Segoe UI', 16, 'bold'),
        'status': ('Segoe UI', 9),
        'body_bold': ('Segoe UI', 11, 'bold'),
        'small_bold': ('Segoe UI', 9, 'bold'),
        'button_large': ('Segoe UI', 12, 'bold'),
    },
}


# ===== HELPER FUNCTIONS =====

def get_theme_colors():
    """Get colors for the current theme."""
    theme = APP_CONFIG['theme']
    colors = APP_CONFIG['colors'].copy()

    # Merge theme-specific colors with general colors
    if theme in colors:
        theme_colors = colors[theme]
        colors.pop('light', None)
        colors.pop('dark', None)
        colors.update(theme_colors)

    return colors


def set_theme(theme_name):
    """Set the application theme."""
    if theme_name in ['light', 'dark']:
        APP_CONFIG['theme'] = theme_name
        return True
    return False


def get_color_palette():
    """Get the complete color palette for the current theme."""
    colors = get_theme_colors()

    palette = {
        'colors': colors,
        'accessibility': {
            'high_contrast_pairs': [
                ('text_primary', 'background'),
                ('text_accent', 'panel_bg'),
                ('btn_primary', 'white'),
                ('btn_danger', 'white'),
                ('btn_success', 'white'),
            ],
            'color_blind_safe': [
                'btn_primary', 'btn_secondary', 'btn_success',
                'btn_warning', 'btn_danger', 'info', 'purple'
            ],
            'semantic_colors': {
                'positive': 'btn_success',
                'negative': 'btn_danger',
                'neutral': 'btn_secondary',
                'info': 'info',
                'warning': 'btn_warning',
                'primary': 'btn_primary',
            }
        },
        'gradients': {
            'primary': f"linear-gradient(135deg, {colors['btn_primary']}, {colors['btn_primary_hover']})",
            'success': f"linear-gradient(135deg, {colors['btn_success']}, {colors['btn_success_hover']})",
            'warning': f"linear-gradient(135deg, {colors['btn_warning']}, {colors['btn_warning_hover']})",
            'danger': f"linear-gradient(135deg, {colors['btn_danger']}, {colors['btn_danger_hover']})",
        }
    }

    return palette


def get_button_style(style_type='primary', size='normal', state='normal'):
    """Get button styling configuration."""
    colors = get_theme_colors()
    styling = APP_CONFIG['styling']

    # Base button styles
    base_styles = {
        'primary': {
            'bg': colors['btn_primary'],
            'fg': '#ffffff',
            'hover_bg': colors['btn_primary_hover'],
            'hover_fg': '#ffffff',
        },
        'secondary': {
            'bg': colors['btn_secondary'],
            'fg': '#ffffff',
            'hover_bg': colors['btn_secondary_hover'],
            'hover_fg': '#ffffff',
        },
        'success': {
            'bg': colors['btn_success'],
            'fg': '#ffffff',
            'hover_bg': colors['btn_success_hover'],
            'hover_fg': '#ffffff',
        },
        'warning': {
            'bg': colors['btn_warning'],
            'fg': '#ffffff',
            'hover_bg': colors['btn_warning_hover'],
            'hover_fg': '#ffffff',
        },
        'danger': {
            'bg': colors['btn_danger'],
            'fg': '#ffffff',
            'hover_bg': colors['btn_danger_hover'],
            'hover_fg': '#ffffff',
        },
        'info': {
            'bg': colors['btn_info'],
            'fg': '#ffffff',
            'hover_bg': colors['btn_info_hover'],
            'hover_fg': '#ffffff',
        },
        'neutral': {
            'bg': colors['btn_neutral'],
            'fg': '#ffffff',
            'hover_bg': colors['btn_neutral_hover'],
            'hover_fg': '#ffffff',
        },
    }

    # Size configurations
    size_configs = {
        'small': {
            'padx': styling['small_button_padding_x'],
            'pady': styling['small_button_padding_y'],
            'font': APP_CONFIG['fonts']['small'],
        },
        'normal': {
            'padx': styling['button_padding_x'],
            'pady': styling['button_padding_y'],
            'font': APP_CONFIG['fonts']['button'],
        },
        'large': {
            'padx': styling['large_button_padding_x'],
            'pady': styling['large_button_padding_y'],
            'font': APP_CONFIG['fonts']['large'],
        },
    }

    # Get base style
    style = base_styles.get(style_type, base_styles['primary']).copy()

    # Apply size configuration
    size_config = size_configs.get(size, size_configs['normal'])
    style.update(size_config)

    # Apply state modifications
    if state == 'disabled':
        style['bg'] = colors['btn_disabled']
        style['fg'] = colors['btn_disabled_text']
        style['hover_bg'] = colors['btn_disabled']
        style['hover_fg'] = colors['btn_disabled_text']
    elif state == 'focus':
        style['relief'] = 'solid'
        style['highlightbackground'] = colors['btn_focus_ring']
        style['highlightcolor'] = colors['btn_focus_ring']
        style['highlightthickness'] = styling['focus_ring_width']

    # Add common styling
    style.update({
        'relief': 'flat',
        'borderwidth': 0,
        'cursor': 'hand2' if state != 'disabled' else 'arrow',
        'compound': 'left',
        'anchor': 'center',
        'justify': 'center',
    })

    return style


def validate_color(color):
    """Validate if a color string is valid."""
    if not isinstance(color, str):
        return False

    # Check hex color format
    if color.startswith('#'):
        if len(color) in [4, 7]:  # #RGB or #RRGGBB
            try:
                int(color[1:], 16)
                return True
            except ValueError:
                return False

    # Check named colors
    named_colors = {'red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'black', 'white'}
    return color.lower() in named_colors


def get_contrast_ratio(color1, color2):
    """Calculate contrast ratio between two colors (simplified)."""
    # This is a simplified version - in production, use proper color contrast calculation
    return 4.5  # WCAG AA minimum


def get_current_theme():
    """Get the current theme name."""
    return APP_CONFIG['theme']


# ===== EXPORTS =====
__all__ = [
    # Application metadata
    'APP_NAME',
    'APP_VERSION',
    'APP_AUTHOR',
    'APP_CONFIG',

    # Configuration sections
    'FILE_OPERATIONS',
    'SUPPORTED_IMAGE_FORMATS',
    'DEFAULT_FILENAMES',
    'EXPORT_FORMATS',
    'VALIDATION',
    'CANVAS',
    'ANALYSIS_CONFIG',
    'QUALITY_THRESHOLDS',
    'COLOR_SPECTRUMS',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    'LIMITS',
    'PERFORMANCE',
    'DEBUG',
    'VERSION_INFO',

    # Theme and color functions
    'get_theme_colors',
    'set_theme',
    'get_current_theme',
    'get_color_palette',
    'get_button_style',
    'validate_color',
    'get_contrast_ratio',
]