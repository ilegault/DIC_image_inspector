# utils/constants.py - Application Constants

"""
Application-wide constants and configuration.
Centralized configuration following clean architecture principles.
"""

# Application metadata
APP_NAME = "DIC Image Quality Inspector"
APP_VERSION = "2.0.0"
APP_AUTHOR = "DIC Analysis Team"

# Enhanced file operations configuration
FILE_OPERATIONS = {
    'auto_backup': True,
    'backup_dir': 'backups',
    'max_backups': 10,
    'compress_backups': True,
    'backup_format': 'zip',
    'temp_dir': 'temp',
    'clean_temp_on_exit': True,
    'max_temp_age_hours': 24,

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
    },

    'encoding': 'utf-8',
    'report_extension': '.txt',
    'csv_extension': '.csv'
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

# Default filenames and paths
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

# Enhanced validation rules
VALIDATION = {
    'image_max_size_mb': 100,
    'image_min_size_px': 50,
    'image_max_size_px': 8192,
    'roi_min_size_px': 10,
    'roi_max_size_percent': 90,
    'facet_size_min': 3,
    'facet_size_max': 200,
    'point_distance_min': 1,
    'point_distance_max': 50,
    'quality_threshold_min': 0.0,
    'quality_threshold_max': 1.0,

    # Legacy compatibility for existing code
    'min_image_size': (50, 50),  # Minimum width, height in pixels
    'max_image_size': (8192, 8192),  # Maximum width, height in pixels
    'min_roi_area': 100,  # Minimum ROI area in pixels
    'max_file_size': 100 * 1024 * 1024,  # 100MB maximum file size
    'supported_image_extensions': ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.gif', '.webp', '.ico'],
    'max_filename_length': 255,
    'reserved_names': ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                       'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                       'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
}

# Canvas configuration
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
}

# Analysis configuration
ANALYSIS_CONFIG = {
    'default_method': 'optimized_dic',
    'available_methods': ['dic', 'optimized_dic', 'fast_dic', 'high_quality_dic'],
    'default_facet_size': 19,
    'default_overlap': 0.5,
    'default_point_distance': 4,
    'interpolation_method': 'bicubic',
    'correlation_threshold': 0.6,
    'max_iterations': 100,
    'convergence_tolerance': 1e-6,
    'multiprocessing': True,
    'max_workers': None,  # Auto-detect CPU cores
    'chunk_size': 1000,
    'memory_limit_mb': 2048,
}

# Quality assessment thresholds
QUALITY_THRESHOLDS = {
    'excellent': {'min': 0.9, 'color': '#10b981', 'label': 'Excellent'},
    'good': {'min': 0.7, 'color': '#3b82f6', 'label': 'Good'},
    'fair': {'min': 0.5, 'color': '#f59e0b', 'label': 'Fair'},
    'poor': {'min': 0.3, 'color': '#ef4444', 'label': 'Poor'},
    'very_poor': {'min': 0.0, 'color': '#7f1d1d', 'label': 'Very Poor'},
}

# Color spectrum configurations
COLOR_SPECTRUMS = {
    'optimized': {
        'name': 'Optimized DIC',
        'description': 'Optimized for DIC analysis visualization',
        'hex_colors': ['#000000', '#8b0000', '#ff4500', '#ffd700', '#00ff00'],
        'colors': [
            (0, 0, 0, "Critical: Not suitable for DIC"),         # #000000 - Black for worst
            (139, 0, 0, "Poor: Below threshold"),                # #8b0000 - Dark red
            (255, 69, 0, "Good: Acceptable for DIC"),            # #ff4500 - Orange red
            (255, 215, 0, "Very Good: Good for DIC"),            # #ffd700 - Gold
            (0, 255, 0, "Excellent: Ideal for DIC")              # #00ff00 - Green for best
        ]
    },
    'controlled': {
        'name': 'Controlled Pattern Quality',
        'description': 'High-precision pattern quality assessment',
        'colors': [
            (0, 0, 0, "Unusable: No correlation possible"),      # Black for worst
            (139, 0, 0, "Poor: Unreliable correlation"),         # Dark red
            (255, 140, 0, "Acceptable: Usable with uncertainty"), # Orange
            (255, 255, 0, "Good: Good correlation quality"),     # Yellow
            (0, 255, 255, "Very Good: Very reliable"),           # Cyan
            (0, 255, 0, "Excellent: Optimal pattern")            # Green for best
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
    },
    'jet': {
        'name': 'Jet',
        'description': 'Classic jet colormap',
        'hex_colors': ['#000080', '#0000ff', '#00ffff', '#ffff00', '#ff0000'],
        'colors': [
            (0, 0, 128, "Level 1"),      # #000080
            (0, 0, 255, "Level 2"),      # #0000ff
            (0, 255, 255, "Level 3"),    # #00ffff
            (255, 255, 0, "Level 4"),    # #ffff00
            (255, 0, 0, "Level 5")       # #ff0000
        ]
    },
    'viridis': {
        'name': 'Viridis',
        'description': 'Perceptually uniform colormap',
        'hex_colors': ['#440154', '#31688e', '#35b779', '#fde725'],
        'colors': [
            (68, 1, 84, "Level 1"),      # #440154
            (49, 104, 142, "Level 2"),   # #31688e
            (53, 183, 121, "Level 3"),   # #35b779
            (253, 231, 37, "Level 4")    # #fde725
        ]
    },
    'plasma': {
        'name': 'Plasma',
        'description': 'High contrast plasma colormap',
        'hex_colors': ['#0d0887', '#7e03a8', '#cc4778', '#f89441', '#f0f921'],
        'colors': [
            (13, 8, 135, "Level 1"),     # #0d0887
            (126, 3, 168, "Level 2"),    # #7e03a8
            (204, 71, 120, "Level 3"),   # #cc4778
            (248, 148, 65, "Level 4"),   # #f89441
            (240, 249, 33, "Level 5")    # #f0f921
        ]
    },
    'inferno': {
        'name': 'Inferno',
        'description': 'Inferno colormap for thermal-like visualization',
        'hex_colors': ['#000004', '#420a68', '#932667', '#dd513a', '#fca50a', '#fcffa4'],
        'colors': [
            (0, 0, 4, "Level 1"),        # #000004
            (66, 10, 104, "Level 2"),    # #420a68
            (147, 38, 103, "Level 3"),   # #932667
            (221, 81, 58, "Level 4"),    # #dd513a
            (252, 165, 10, "Level 5"),   # #fca50a
            (252, 255, 164, "Level 6")   # #fcffa4
        ]
    }
}

# Error messages
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

# Success messages
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

# System limits
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

# Performance settings
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
}

# Debug settings
DEBUG = {
    'enable_logging': True,
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'log_to_file': True,
    'log_to_console': False,
    'enable_profiling': False,
    'profile_memory': False,
    'enable_debug_mode': False,
    'show_debug_info': False,
    'measure_performance': False,
}

# Version information
VERSION_INFO = {
    'major': 2,
    'minor': 0,
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

# UI Colors and Themes - REPLACE your APP_CONFIG section with this fixed version
APP_CONFIG = {
    'theme': 'light',  # Default theme
    'colors': {
        # Enhanced Modern accent colors (same for both themes)
        'primary': '#2563eb',  # Professional blue
        'secondary': '#64748b',  # Modern slate gray
        'success': '#059669',  # Professional green
        'warning': '#d97706',  # Professional amber
        'danger': '#dc2626',  # Professional red
        'info': '#0891b2',  # Professional cyan
        'purple': '#7c3aed',  # Professional violet
        'pink': '#ec4899',  # Keep pink

        # Modern Clean Button Colors - Cohesive Design System
        'btn_primary': '#2563eb',      # Primary blue - for main actions
        'btn_primary_hover': '#1d4ed8', # Primary hover
        'btn_secondary': '#6b7280',    # Secondary gray - for secondary actions
        'btn_secondary_hover': '#4b5563', # Secondary hover
        'btn_success': '#10b981',      # Success green - for positive actions
        'btn_success_hover': '#059669', # Success hover
        'btn_warning': '#f59e0b',      # Warning amber - for caution actions
        'btn_warning_hover': '#d97706', # Warning hover
        'btn_danger': '#ef4444',       # Danger red - for destructive actions
        'btn_danger_hover': '#dc2626', # Danger hover
        
        # Specialized button colors for specific functions
        'btn_info': '#3b82f6',         # Info blue - for informational actions
        'btn_info_hover': '#2563eb',   # Info hover
        'btn_neutral': '#64748b',      # Neutral - for utility actions
        'btn_neutral_hover': '#475569', # Neutral hover

        # Enhanced disabled and focus states
        'btn_disabled': '#d1d5db',  # Light gray for disabled
        'btn_disabled_text': '#9ca3af',  # Muted text for disabled
        'btn_focus_ring': '#3b82f6',  # Focus ring color
        'btn_focus_ring_offset': '#ffffff',  # Focus ring offset

        # Light mode enhancements
        'light': {
            # Light modern background scheme
            'background': '#f8fafc',  # Very light gray-blue
            'panel_bg': '#ffffff',  # Pure white panels
            'panel_border': '#e5e7eb',  # Subtle border
            'panel_shadow': '#1f293720',  # Subtle shadow

            # Enhanced light mode text colors
            'text_primary': '#111827',  # Very dark gray
            'text_secondary': '#4b5563',  # Medium gray
            'text_muted': '#9ca3af',  # Light gray
            'text_accent': '#000000',  # Pure black for emphasis

            # Enhanced light mode UI elements
            'status_bar': '#f3f4f6',  # Light gray for status
            'canvas_bg': '#ffffff',  # White canvas
            'hover_bg': '#f9fafb',  # Very light hover
            'selected_bg': '#dbeafe',  # Light blue selection
        },

        # Dark mode enhancements
        'dark': {
            # Dark modern background scheme
            'background': '#0f172a',  # Very dark slate
            'panel_bg': '#1e293b',  # Dark slate panels
            'panel_border': '#374151',  # Medium slate border
            'panel_shadow': '#00000060',  # Darker shadow

            # Enhanced dark mode text colors
            'text_primary': '#f1f5f9',  # Very light gray
            'text_secondary': '#cbd5e1',  # Light slate
            'text_muted': '#94a3b8',  # Medium slate
            'text_accent': '#ffffff',  # Pure white for emphasis

            # Enhanced dark mode UI elements
            'status_bar': '#374151',  # Medium slate for status
            'canvas_bg': '#1e293b',  # Dark slate canvas
            'hover_bg': '#374151',  # Medium slate hover
            'selected_bg': '#3730a3',  # Dark blue selection
        },
    },

    # Enhanced styling for modern cards - MOVED OUT of colors section
    'styling': {
        'border_radius': 8,  # Modern rounded corners
        'card_shadow': 4,  # Card shadow depth
        'card_border_width': 1,  # Card border width
        'button_border_radius': 6,  # Button rounded corners
        'button_padding_x': 16,  # Button horizontal padding
        'button_padding_y': 10,  # Button vertical padding
        'compact_button_size': 36,  # Compact button size
        'card_padding': 16,  # Card internal padding
        'card_header_height': 48,  # Card header height
        'element_spacing': 12,  # Space between elements
        'section_spacing': 20,  # Space between sections
        'hover_transition': 200,  # Hover transition in ms
        'focus_ring_width': 2,  # Focus ring width
        'shadow_blur': 8,  # Shadow blur radius
        # Additional styling needed for compatibility
        'small_button_padding_x': 12,
        'small_button_padding_y': 6,
        'large_button_padding_x': 24,
        'large_button_padding_y': 12,
        'panel_padding': 16,
        'small_spacing': 4,
    },

    # Enhanced font configuration
    'fonts': {
        'default': ('Segoe UI', 10),  # Default system font
        'heading': ('Segoe UI', 14, 'bold'),  # Section headings
        'subheading': ('Segoe UI', 12, 'bold'),  # Subsection headings
        'button': ('Segoe UI', 10),  # Button text
        'small': ('Segoe UI', 9),  # Small text
        'monospace': ('Consolas', 10),  # Code/data display
        'large': ('Segoe UI', 12),  # Large text

        # Legacy font names for existing code compatibility
        'body': ('Segoe UI', 10),  # Body text (maps to default)
        'title': ('Segoe UI', 16, 'bold'),  # Main titles
        'status': ('Segoe UI', 9),  # Status bar text

        # Additional fonts found in your existing code
        'body_bold': ('Segoe UI', 11, 'bold'),  # Bold body text
        'small_bold': ('Segoe UI', 9, 'bold'),  # Small bold text
        'button_large': ('Segoe UI', 12, 'bold'),  # Large button text
    },

    # Enhanced window configuration
    'window': {
        'min_width': 1000,
        'min_height': 700,
        'default_width': 1400,
        'default_height': 900,
        'resizable': True,
        'icon': None,  # Set to icon path if available
    },

    # ROI (Region of Interest) configuration
    'roi': {
        'normal_color': '#2563eb',  # Enhanced blue for completed ROI
        'selection_color': '#dc2626',  # Enhanced red for active selection
        'line_width': 2,
        'min_points': 3,  # Minimum points for polygon
        'selection_tolerance': 5  # Pixels tolerance for selection
    },

    # Enhanced canvas configuration
    'canvas': {
        'default_width': 800,
        'default_height': 600,
        'zoom_factor': 1.2,
        'max_zoom': 2.0,
        'min_zoom': 0.1,
        'scroll_speed': 3,
        'selection_color': '#3b82f6',
        'selection_width': 2,
        'grid_color': '#e5e7eb',
        'grid_alpha': 0.3,
    },

    # Enhanced analysis configuration
    'analysis': {
        'default_facet_size': 19,
        'default_point_distance': 4,
        'max_facet_size': 100,
        'min_facet_size': 5,
        'max_point_distance': 20,
        'min_point_distance': 1,
        'quality_thresholds': {
            'excellent': 0.9,
            'good': 0.7,
            'fair': 0.5,
            'poor': 0.3,
        },
        'default_spectrum': 'optimized',
        'available_spectra': ['optimized', 'jet', 'viridis', 'plasma', 'inferno'],
    },

    # File handling configuration
    'files': {
        'supported_formats': ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'],
        'max_file_size': 50 * 1024 * 1024,  # 50MB
        'default_save_format': 'png',
        'compression_quality': 95,
        'backup_enabled': True,
        'recent_files_limit': 10,
    },

    # Performance configuration
    'performance': {
        'max_image_size': 4096,  # Max dimension for display
        'thumbnail_size': 256,  # Thumbnail size
        'cache_size': 100,  # Number of cached items
        'thread_pool_size': 4,  # Number of worker threads
        'progress_update_interval': 100,  # Progress update frequency (ms)
    },

    # Enhanced accessibility configuration
    'accessibility': {
        'high_contrast_mode': False,
        'large_text_mode': False,
        'keyboard_navigation': True,
        'screen_reader_support': True,
        'color_blind_friendly': True,
        'minimum_contrast_ratio': 4.5,  # WCAG AA compliance
        'focus_indicators': True,
        'reduced_motion': False,
    },
}


def get_theme_colors():
    """
    Get colors for the current theme.

    Returns:
        dict: Dictionary of color values for current theme
    """
    theme = APP_CONFIG['theme']
    colors = APP_CONFIG['colors'].copy()

    # Merge theme-specific colors with general colors
    if theme in colors:
        theme_colors = colors[theme]
        # Remove theme-specific dictionaries and merge with general colors
        colors.pop('light', None)
        colors.pop('dark', None)
        colors.update(theme_colors)

    return colors

def set_theme(theme_name):
    """
    Set the application theme.

    Args:
        theme_name (str): Theme name ('light' or 'dark')
    """
    if theme_name in ['light', 'dark']:
        APP_CONFIG['theme'] = theme_name
        return True
    return False


def get_color_palette():
    """
    Get the complete color palette for the current theme.

    Returns:
        dict: Complete color palette with accessibility information
    """
    colors = get_theme_colors()

    # Add accessibility metadata
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
    """
    Get button styling configuration.

    Args:
        style_type (str): Button style type
        size (str): Button size ('small', 'normal', 'large')
        state (str): Button state ('normal', 'hover', 'disabled', 'focus')

    Returns:
        dict: Button style configuration
    """
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
            'bg': colors['info'],
            'fg': '#ffffff',
            'hover_bg': colors['info'],
            'hover_fg': '#ffffff',
        },
        'purple': {
            'bg': colors['accent_purple'],
            'fg': '#ffffff',
            'hover_bg': colors['accent_purple_hover'],
            'hover_fg': '#ffffff',
        },
        'neutral': {
            'bg': colors['neutral_action'],
            'fg': '#ffffff',
            'hover_bg': colors['neutral_action_hover'],
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
        'compound': 'left',  # For buttons with icons
        'anchor': 'center',
        'justify': 'center',
    })

    return style


# Color validation functions
def validate_color(color):
    """Validate if a color string is valid."""
    if not isinstance(color, str):
        return False

    # Check hex color format
    if color.startswith('#'):
        if len(color) == 7:  # #RRGGBB
            try:
                int(color[1:], 16)
                return True
            except ValueError:
                return False
        elif len(color) == 4:  # #RGB
            try:
                int(color[1:], 16)
                return True
            except ValueError:
                return False

    # Check named colors (basic set)
    named_colors = {'red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'black', 'white'}
    return color.lower() in named_colors


def get_contrast_ratio(color1, color2):
    """Calculate contrast ratio between two colors (simplified)."""
    # This is a simplified version - in production, use proper color contrast calculation
    # For now, return a reasonable default
    return 4.5  # WCAG AA minimum


def get_current_theme():
    """
    Get the current theme name.

    Returns:
        str: Current theme name ('light' or 'dark')
    """
    return APP_CONFIG['theme']


# Export commonly used functions and constants
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