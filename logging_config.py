# logging_config.py - Easy Logging Configuration

"""
Simple configuration file for adjusting logging levels.
Edit this file to quickly change what gets logged without diving into constants.py
"""

# =============================================================================
# QUICK LOGGING CONFIGURATION
# =============================================================================

# Main application logging level
# Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
APP_LOG_LEVEL = 'INFO'  # Recommended: 'INFO' for normal use, 'DEBUG' for troubleshooting

# Third-party library logging (PIL, matplotlib, etc.)
# Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'  
THIRD_PARTY_LOG_LEVEL = 'WARNING'  # Recommended: 'WARNING' to reduce noise

# PIL/Pillow specific logging (image processing library)
# Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
PIL_LOG_LEVEL = 'WARNING'  # Set to 'DEBUG' only when troubleshooting image loading

# Enable/disable logging to file
LOG_TO_FILE = True

# Enable/disable logging to console
LOG_TO_CONSOLE = True

# =============================================================================
# ADVANCED CONFIGURATION
# =============================================================================

# Specific modules to keep at DEBUG level (even when APP_LOG_LEVEL is higher)
# Useful for debugging specific parts of the application
DEBUG_MODULES = [
    # Examples (uncomment to enable):
    # 'ui.main_window',           # Main window debugging
    # 'core.image_analyzer',      # Image analysis debugging  
    # 'analysis.quality_map',     # Quality map generation debugging
    # 'ui.components.roi_selector', # ROI selection debugging
    # 'ui.components.image_canvas', # Image canvas zoom/pan debugging
]

# Modules to completely silence (set to ERROR level)
SILENT_MODULES = [
    # Examples (uncomment to enable):
    # 'matplotlib.font_manager',  # Silence font loading messages
    # 'PIL.PngImagePlugin',       # Silence PNG-specific messages
]

# =============================================================================
# PRESET CONFIGURATIONS
# =============================================================================

PRESETS = {
    'quiet': {
        'APP_LOG_LEVEL': 'WARNING',
        'THIRD_PARTY_LOG_LEVEL': 'ERROR', 
        'PIL_LOG_LEVEL': 'ERROR',
        'description': 'Only warnings and errors - minimal logging'
    },
    
    'normal': {
        'APP_LOG_LEVEL': 'INFO',
        'THIRD_PARTY_LOG_LEVEL': 'WARNING',
        'PIL_LOG_LEVEL': 'WARNING', 
        'description': 'Recommended for daily use - informative but not noisy'
    },
    
    'debug': {
        'APP_LOG_LEVEL': 'DEBUG',
        'THIRD_PARTY_LOG_LEVEL': 'INFO',
        'PIL_LOG_LEVEL': 'WARNING',
        'description': 'Debug app code, minimal third-party noise'
    },
    
    'verbose': {
        'APP_LOG_LEVEL': 'DEBUG',
        'THIRD_PARTY_LOG_LEVEL': 'DEBUG',
        'PIL_LOG_LEVEL': 'DEBUG',
        'description': 'Everything at debug level - very verbose'
    },
    
    'image_debug': {
        'APP_LOG_LEVEL': 'INFO', 
        'THIRD_PARTY_LOG_LEVEL': 'WARNING',
        'PIL_LOG_LEVEL': 'DEBUG',
        'description': 'Debug image loading issues specifically'
    },
    
    'zoom_pan_debug': {
        'APP_LOG_LEVEL': 'INFO',
        'THIRD_PARTY_LOG_LEVEL': 'WARNING', 
        'PIL_LOG_LEVEL': 'WARNING',
        'DEBUG_MODULES': ['ui.components.image_canvas'],
        'description': 'Debug zoom and pan functionality specifically'
    }
}

# =============================================================================
# ACTIVE PRESET (uncomment one to use a preset instead of individual settings)
# =============================================================================

ACTIVE_PRESET = 'zoom_pan_debug'  # Uncomment and change to use a preset

# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================

"""
HOW TO USE THIS FILE:

1. SIMPLE USAGE:
   - Change APP_LOG_LEVEL to 'DEBUG' when you want detailed app logging
   - Change PIL_LOG_LEVEL to 'DEBUG' when troubleshooting image loading
   - Keep THIRD_PARTY_LOG_LEVEL at 'WARNING' to avoid noise

2. PRESET USAGE:
   - Uncomment ACTIVE_PRESET line above and set it to one of:
     'quiet', 'normal', 'debug', 'verbose', 'image_debug'

3. MODULE-SPECIFIC DEBUGGING:
   - Add module names to DEBUG_MODULES to debug specific parts
   - Add module names to SILENT_MODULES to completely silence them

4. EXAMPLES:
   
   For normal daily use:
   APP_LOG_LEVEL = 'INFO'
   THIRD_PARTY_LOG_LEVEL = 'WARNING' 
   PIL_LOG_LEVEL = 'WARNING'
   
   When troubleshooting image loading:
   APP_LOG_LEVEL = 'INFO'
   THIRD_PARTY_LOG_LEVEL = 'WARNING'
   PIL_LOG_LEVEL = 'DEBUG'
   
   When debugging the app:
   APP_LOG_LEVEL = 'DEBUG'
   THIRD_PARTY_LOG_LEVEL = 'WARNING'
   PIL_LOG_LEVEL = 'WARNING'
   DEBUG_MODULES = ['core.image_analyzer', 'analysis.quality_map']

RESTART THE APP after making changes to this file.
"""