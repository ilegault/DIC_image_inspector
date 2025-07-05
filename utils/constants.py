# utils/constants.py - Application Constants

"""
Application-wide constants and configuration.
Centralized configuration following clean architecture principles.
"""

# Application metadata
APP_NAME = "DIC Image Quality Inspector"
APP_VERSION = "2.0.0"
APP_AUTHOR = "DIC Analysis Team"

# UI Colors and Themes
APP_CONFIG = {
    'theme': 'light',  # Default theme
    'colors': {
        # Light theme colors
        'light': {
            # Modern gradient background scheme
            'background': '#f8fafc',  # Light gray-blue background
            'panel_bg': '#ffffff',    # Pure white panels
            'panel_border': '#e2e8f0', # Subtle border
            'panel_shadow': '#64748b20', # Subtle shadow
            
            # Text colors
            'text_primary': '#1e293b',   # Dark slate
            'text_secondary': '#475569', # Medium slate
            'text_muted': '#94a3b8',     # Light slate
            'text_accent': '#0f172a',    # Very dark for emphasis
            
            # Status and UI elements
            'status_bar': '#334155',     # Dark slate for status
            'canvas_bg': '#ffffff',      # White canvas background
            'hover_bg': '#f1f5f9',       # Light hover background
            'selected_bg': '#e0e7ff',    # Light blue selection
        },
        
        # Dark theme colors
        'dark': {
            # Dark modern background scheme
            'background': '#0f172a',     # Very dark slate
            'panel_bg': '#1e293b',       # Dark slate panels
            'panel_border': '#334155',   # Medium slate border
            'panel_shadow': '#00000040', # Dark shadow
            
            # Text colors (inverted)
            'text_primary': '#f8fafc',   # Light gray-blue
            'text_secondary': '#cbd5e1', # Light slate
            'text_muted': '#64748b',     # Medium slate
            'text_accent': '#ffffff',    # Pure white for emphasis
            
            # Status and UI elements
            'status_bar': '#cbd5e1',     # Light slate for status
            'canvas_bg': '#1e293b',      # Dark slate canvas
            'hover_bg': '#334155',       # Medium slate hover
            'selected_bg': '#1e40af',    # Dark blue selection
        },
        
        # Modern accent colors (same for both themes)
        'primary': '#3b82f6',        # Modern blue
        'secondary': '#6366f1',      # Indigo
        'success': '#10b981',        # Emerald green
        'warning': '#f59e0b',        # Amber
        'danger': '#ef4444',         # Red
        'info': '#06b6d4',           # Cyan
        'purple': '#8b5cf6',         # Violet
        'pink': '#ec4899',           # Pink
        
        # Button specific colors
        'btn_primary': '#3b82f6',
        'btn_primary_hover': '#2563eb',
        'btn_secondary': '#6b7280',
        'btn_secondary_hover': '#4b5563',
        'btn_success': '#10b981',
        'btn_success_hover': '#059669',
        'btn_warning': '#f59e0b',
        'btn_warning_hover': '#d97706',
        'btn_danger': '#ef4444',
        'btn_danger_hover': '#dc2626',
        
        # Legacy compatibility (keeping old names for existing code)
        'accent_blue': '#3b82f6',
        'accent_green': '#10b981',
        'accent_orange': '#f59e0b',
        'accent_red': '#ef4444',
        'accent_purple': '#8b5cf6'
    },

    'fonts': {
        'title': ('Segoe UI', 28, 'bold'),
        'heading': ('Segoe UI', 18, 'bold'),
        'subheading': ('Segoe UI', 14, 'bold'),
        'body': ('Segoe UI', 11),
        'body_bold': ('Segoe UI', 11, 'bold'),
        'small': ('Segoe UI', 9),
        'small_bold': ('Segoe UI', 9, 'bold'),
        'button': ('Segoe UI', 10, 'bold'),
        'button_large': ('Segoe UI', 12, 'bold'),
        'monospace': ('Consolas', 10),
        'status': ('Segoe UI', 9)
    },

    'display': {
        'max_image_size': 800,
        'quality_map_alpha': 0.7,
        'canvas_bg': 'white',
        'min_window_width': 800,
        'min_window_height': 600,
        'default_window_size': (1200, 800)
    },

    'styling': {
        # Modern button styling
        'button_padding_x': 20,
        'button_padding_y': 8,
        'button_border_radius': 6,
        'button_border_width': 0,
        'button_relief': 'flat',
        
        # Panel styling
        'panel_padding': 15,
        'panel_border_radius': 8,
        'panel_relief': 'flat',
        'panel_border_width': 1,
        
        # Spacing
        'section_spacing': 20,
        'element_spacing': 10,
        'small_spacing': 5,
        
        # Shadows and effects
        'shadow_offset': 2,
        'shadow_blur': 4,
        'hover_lift': 1,
        
        # Modern UI elements
        'card_elevation': 2,
        'border_radius': 8,
        'input_border_radius': 6,
        'button_hover_lift': 2
    },

    'roi': {
        'normal_color': '#3498db',  # Blue for completed ROI
        'selection_color': '#e74c3c',  # Red for active selection
        'line_width': 2,
        'min_points': 3,  # Minimum points for polygon
        'selection_tolerance': 5  # Pixels tolerance for selection
    },

    'analysis': {
        'default_spectrum': 'optimized',
        'default_facet_size': 19,
        'default_point_distance': 4,
        'quality_thresholds': {
            'optimized': {
                'perfect': 95,
                'excellent': 90,
                'very_good': 85,
                'good': 80,
                'minimum': 75,
                'critical': 0
            },
            'controlled': {
                'excellent': 95,
                'very_good': 90,
                'good': 85,
                'acceptable': 80,
                'poor': 70,
                'unusable': 0
            }
        }
    }
}

# File operation constants
FILE_OPERATIONS = {
    'supported_formats': {
        'input': ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'],
        'output': ['.txt', '.pdf', '.csv', '.png', '.jpg']
    },

    'default_extensions': {
        'report': '.txt',
        'image_export': '.png',
        'data_export': '.csv'
    },

    'file_dialogs': {
        'image_load': [
            ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff"),
            ("All files", "*.*")
        ],
        'report_save': [
            ("Text files", "*.txt"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ],
        'image_export': [
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg"),
            ("All files", "*.*")
        ]
    },

    'encoding': 'utf-8',
    'report_extension': '.txt',
    'csv_extension': '.csv'
}

# Supported image formats for file dialogs
SUPPORTED_IMAGE_FORMATS = [
    ("PNG files", "*.png"),
    ("JPEG files", "*.jpg;*.jpeg"),
    ("BMP files", "*.bmp"),
    ("TIFF files", "*.tif;*.tiff"),
    ("All image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff"),
    ("All files", "*.*")
]

# Default filenames for various operations
DEFAULT_FILENAMES = {
    'report': 'dic_analysis_report',
    'quality_map': 'quality_map',
    'analysis_data': 'analysis_data',
    'screenshot': 'screenshot',
    'backup': 'backup'
}

# Export format configurations
EXPORT_FORMATS = {
    'report': {
        'txt': {'extension': '.txt', 'description': 'Plain text report'},
        'pdf': {'extension': '.pdf', 'description': 'PDF report'},
        'html': {'extension': '.html', 'description': 'HTML report'}
    },
    'data': {
        'csv': {'extension': '.csv', 'description': 'Comma-separated values'},
        'json': {'extension': '.json', 'description': 'JSON data format'},
        'xlsx': {'extension': '.xlsx', 'description': 'Excel spreadsheet'}
    },
    'image': {
        'png': {'extension': '.png', 'description': 'PNG image'},
        'jpg': {'extension': '.jpg', 'description': 'JPEG image'},
        'tiff': {'extension': '.tiff', 'description': 'TIFF image'}
    }
}

# Validation constants
VALIDATION = {
    'min_image_size': (50, 50),  # Minimum width, height in pixels
    'max_image_size': (4096, 4096),  # Maximum width, height in pixels
    'min_roi_area': 100,  # Minimum ROI area in pixels
    'max_file_size': 50 * 1024 * 1024,  # 50MB maximum file size
    'supported_image_extensions': ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'],
    'max_filename_length': 255,
    'reserved_names': ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                      'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                      'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
}

# Canvas constants for UI
CANVAS = {
    'background_color': '#f0f0f0',
    'grid_color': '#d0d0d0',
    'selection_color': '#ff0000',
    'roi_color': '#0000ff',
    'zoom_factor': 1.2,
    'max_zoom': 10.0,
    'min_zoom': 0.1
}

# Analysis algorithm constants
ANALYSIS_CONFIG = {
    'gradient_analysis': {
        'sobel_kernel_size': 3,
        'gradient_threshold': 50,
        'normalization_factor': 255.0
    },

    'contrast_analysis': {
        'rms_weight': 0.4,
        'michelson_weight': 0.3,
        'weber_weight': 0.2,
        'local_weight': 0.1,
        'local_window_size': 5
    },

    'speckle_analysis': {
        'adaptive_threshold_block_size': 11,
        'adaptive_threshold_c': 2,
        'min_speckle_area': 4,
        'max_speckle_ratio': 0.05,  # 5% of total area
        'optimal_speckle_density': 0.3,  # 30% coverage
        'speckle_size_range': (2, 50)  # pixels
    },

    'quality_scoring': {
        'gradient_weight': 0.40,
        'contrast_weight': 0.25,
        'entropy_weight': 0.20,
        'pattern_weight': 0.10,
        'noise_weight': 0.05
    },

    'subset_analysis': {
        'default_subset_size': 21,
        'subset_range': (11, 51),
        'step_size_factor': 0.25,  # step = subset_size * factor
        'overlap_percent': 75.0
    }
}

# Quality assessment thresholds
QUALITY_THRESHOLDS = {
    'optimized': {
        'excellent': 80.0,
        'very_good': 60.0,
        'good': 40.0,
        'fair': 25.0,
        'poor': 10.0,
        'critical': 0.0
    },

    'controlled': {
        'excellent': 75.0,
        'good': 60.0,
        'acceptable': 45.0,
        'challenging': 30.0,
        'poor': 15.0,
        'unusable': 0.0
    },

    'custom_dic': {
        'excellent': 85.0,
        'very_good': 70.0,
        'good': 50.0,
        'fair': 30.0,
        'poor': 15.0,
        'very_poor': 5.0,
        'critical': 0.0
    }
}

# Color spectrum definitions
COLOR_SPECTRUMS = {


    'optimized': {
        'name': 'Optimized (Rainbow: Red→Blue)',
        'description': 'Optimized assessment with realistic DIC thresholds',
        'colors': [
            (0, 0, 0, "Critical (0-10%): Black - Not suitable for DIC"),
            (255, 0, 0, "Poor (10-25%): Red - Unreliable for DIC"),
            (255, 127, 0, "Fair (25-40%): Orange - Challenging for DIC"),
            (255, 255, 0, "Good (40-60%): Yellow - Acceptable for DIC"),
            (0, 255, 0, "Very Good (60-80%): Green - Good for DIC"),
            (0, 0, 255, "Excellent (80-100%): Blue - Ideal for DIC")
        ]
    },

    'controlled': {
        'name': 'Controlled Pattern Quality (Colorblind-Friendly)',
        'description': 'Controlled assessment with realistic DIC thresholds',
        'colors': [
            (50, 0, 0, "Unusable (0-15%): Dark Red - No correlation possible"),
            (255, 0, 0, "Poor (15-30%): Red - Unreliable correlation"),
            (255, 140, 0, "Challenging (30-45%): Orange - Difficult correlation"),
            (255, 255, 0, "Acceptable (45-60%): Yellow - Usable with uncertainty"),
            (0, 255, 255, "Good (60-75%): Cyan - Good correlation quality"),
            (0, 100, 255, "Excellent (75-100%): Blue - Optimal pattern")
        ]
    },

    'custom_dic': {
        'name': 'Custom DIC (Artificial Speckle Optimized)',
        'description': 'Optimized for artificial speckle patterns and manufactured surfaces',
        'colors': [
            (0, 0, 0, "Critical (0-5%): Black - Not suitable for DIC"),
            (128, 0, 0, "Very Poor (5-15%): Dark Red - Unreliable correlation"),
            (255, 0, 0, "Poor (15-30%): Red - Poor correlation"),
            (255, 127, 0, "Fair (30-50%): Orange - Challenging but usable"),
            (255, 255, 0, "Good (50-70%): Yellow - Good for DIC"),
            (0, 255, 0, "Very Good (70-85%): Green - Very good for DIC"),
            (0, 0, 255, "Excellent (85-100%): Blue - Ideal for DIC")
        ]
    }
}

# Error messages
ERROR_MESSAGES = {
    'no_image': "No image loaded. Please load an image first.",
    'no_roi': "No ROI selected. Please select a region of interest first.",
    'no_analysis': "No analysis results available. Please analyze an image first.",
    'analysis_in_progress': "Analysis is currently in progress. Please wait.",
    'invalid_roi': "Invalid ROI selection. Please select at least 3 points.",
    'load_failed': "Failed to load image. Please check the file format and try again.",
    'save_failed': "Failed to save file. Please check permissions and try again.",
    'analysis_failed': "Analysis failed. Please try again or check image quality."
}

# Success messages
SUCCESS_MESSAGES = {
    'image_loaded': "Image loaded successfully",
    'roi_selected': "ROI selected successfully",
    'analysis_complete': "Analysis completed successfully",
    'report_saved': "Report saved successfully",
    'screenshot_captured': "Screenshot captured successfully"
}

# Application limits
LIMITS = {
    'max_image_size': 4096,  # Maximum image dimension in pixels
    'min_image_size': 50,  # Minimum image dimension in pixels
    'max_roi_points': 100,  # Maximum ROI polygon points
    'min_roi_points': 3,  # Minimum ROI polygon points
    'max_file_size': 50 * 1024 * 1024,  # 50MB maximum file size
    'analysis_timeout': 300,  # 5 minutes maximum analysis time
    'ui_update_interval': 100  # UI update interval in milliseconds
}

# Performance settings
PERFORMANCE = {
    'enable_multiprocessing': True,
    'max_worker_threads': 4,
    'chunk_size': 1000,
    'memory_limit_mb': 2048,
    'enable_caching': True,
    'cache_size_mb': 512
}

# Debug settings
DEBUG = {
    'enable_debug_output': False,
    'save_intermediate_results': False,
    'debug_output_dir': 'debug_output',
    'log_level': 'INFO',
    'enable_performance_timing': False
}

# Version information
VERSION_INFO = {
    'version': APP_VERSION,
    'build_date': '2024-01-15',
    'api_version': '2.0',
    'min_python_version': '3.8',
    'dependencies': {
        'numpy': '>=1.19.0',
        'opencv-python': '>=4.5.0',
        'pillow': '>=8.0.0',
        'scipy': '>=1.6.0',
        'tkinter': 'built-in'
    }
}


def get_theme_colors():
    """Get colors for the current theme."""
    theme = APP_CONFIG['theme']
    theme_colors = APP_CONFIG['colors'][theme].copy()
    
    # Add common colors that don't change between themes
    common_colors = {
        'primary': APP_CONFIG['colors']['primary'],
        'secondary': APP_CONFIG['colors']['secondary'],
        'success': APP_CONFIG['colors']['success'],
        'warning': APP_CONFIG['colors']['warning'],
        'danger': APP_CONFIG['colors']['danger'],
        'info': APP_CONFIG['colors']['info'],
        'purple': APP_CONFIG['colors']['purple'],
        'pink': APP_CONFIG['colors']['pink'],
        'btn_primary': APP_CONFIG['colors']['btn_primary'],
        'btn_primary_hover': APP_CONFIG['colors']['btn_primary_hover'],
        'btn_secondary': APP_CONFIG['colors']['btn_secondary'],
        'btn_secondary_hover': APP_CONFIG['colors']['btn_secondary_hover'],
        'btn_success': APP_CONFIG['colors']['btn_success'],
        'btn_success_hover': APP_CONFIG['colors']['btn_success_hover'],
        'btn_warning': APP_CONFIG['colors']['btn_warning'],
        'btn_warning_hover': APP_CONFIG['colors']['btn_warning_hover'],
        'btn_danger': APP_CONFIG['colors']['btn_danger'],
        'btn_danger_hover': APP_CONFIG['colors']['btn_danger_hover'],
        'accent_blue': APP_CONFIG['colors']['accent_blue'],
        'accent_green': APP_CONFIG['colors']['accent_green'],
        'accent_orange': APP_CONFIG['colors']['accent_orange'],
        'accent_red': APP_CONFIG['colors']['accent_red'],
        'accent_purple': APP_CONFIG['colors']['accent_purple']
    }
    
    theme_colors.update(common_colors)
    return theme_colors


def set_theme(theme_name):
    """Set the application theme."""
    if theme_name in ['light', 'dark']:
        APP_CONFIG['theme'] = theme_name
        return True
    return False


def get_current_theme():
    """Get the current theme name."""
    return APP_CONFIG['theme']


# Export configuration for other modules
__all__ = [
    'APP_NAME',
    'APP_VERSION',
    'APP_AUTHOR',
    'APP_CONFIG',
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
    'get_theme_colors',
    'set_theme',
    'get_current_theme'
]