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
    'colors': {
        'background': '#2c3e50',
        'panel_bg': '#34495e',
        'text_primary': '#ecf0f1',
        'text_secondary': '#bdc3c7',
        'text_muted': '#95a5a6',
        'status_bar': '#95a5a6',
        'accent_blue': '#3498db',
        'accent_green': '#2ecc71',
        'accent_orange': '#e67e22',
        'accent_red': '#e74c3c',
        'accent_purple': '#9b59b6'
    },

    'fonts': {
        'title': ('Arial', 24, 'bold'),
        'heading': ('Arial', 16, 'bold'),
        'subheading': ('Arial', 12, 'bold'),
        'body': ('Arial', 10),
        'small': ('Arial', 8),
        'monospace': ('Courier New', 10)
    },

    'display': {
        'max_image_size': 800,
        'quality_map_alpha': 0.7,
        'canvas_bg': 'white',
        'min_window_width': 800,
        'min_window_height': 600,
        'default_window_size': (1200, 800)
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
    'VERSION_INFO'
]