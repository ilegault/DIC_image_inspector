# debug_config.py - Unified Debug Configuration
"""
Single-file debug configuration system for the DIC Inspector.
Edit this file to control all debug and logging settings.
***Go to app.py to apply presets***
"""

import logging
from typing import Dict, List, Optional


# =============================================================================
# QUICK TOGGLES - Edit these for instant debug control
# =============================================================================

class DebugConfig:
    """Central debug configuration with easy toggles."""

    # Master switches
    DEBUG_MODE = False  # Master debug switch
    VERBOSE_MODE = False  # Extra verbose output

    # Feature-specific debug flags
    ZOOM_PAN_DEBUG = False  # Debug zoom/pan operations
    IMAGE_LOADING_DEBUG = False  # Debug image loading/processing
    ROI_DEBUG = False  # Debug ROI selection
    ANALYSIS_DEBUG = False  # Debug image analysis
    UI_DEBUG = False  # Debug UI operations
    PERFORMANCE_DEBUG = False  # Debug performance metrics

    # Logging output control
    LOG_TO_CONSOLE = True  # Print logs to console
    LOG_TO_FILE = True  # Save logs to file
    LOG_FILENAME = 'dic_inspector.log'

    # Logging levels
    APP_LOG_LEVEL = 'INFO'  # Main app logging: DEBUG, INFO, WARNING, ERROR
    LIBRARY_LOG_LEVEL = 'WARNING'  # Third-party libraries (PIL, matplotlib, etc.)

    # Module-specific overrides (these modules will use DEBUG level)
    DEBUG_MODULES: List[str] = [
        # Uncomment to enable debug for specific modules:
        # 'ui.components.image_canvas',    # Canvas operations
        # 'core.image_analyzer',           # Analysis engine
        # 'ui.components.roi_selector',    # ROI selection
        # 'analysis.quality_map',          # Quality mapping
    ]

    # Modules to silence (force to ERROR level)
    QUIET_MODULES: List[str] = [
        'matplotlib.font_manager',  # Noisy font messages
        'PIL.PngImagePlugin',  # PNG processing noise
    ]

    # Performance profiling
    PROFILE_PERFORMANCE = False  # Enable performance profiling
    PROFILE_MEMORY = False  # Enable memory profiling
    SHOW_TIMING = False  # Show operation timing

    @classmethod
    def get_module_level(cls, module_name: str) -> int:
        """Get the appropriate logging level for a module."""
        # Check if in debug modules
        if any(module_name.startswith(m) for m in cls.DEBUG_MODULES):
            return logging.DEBUG

        # Check if in quiet modules
        if any(module_name.startswith(m) for m in cls.QUIET_MODULES):
            return logging.ERROR

        # Check feature-specific debug flags
        if cls.ZOOM_PAN_DEBUG and 'image_canvas' in module_name:
            return logging.DEBUG
        if cls.IMAGE_LOADING_DEBUG and ('image' in module_name or 'PIL' in module_name):
            return logging.DEBUG
        if cls.ROI_DEBUG and 'roi' in module_name:
            return logging.DEBUG
        if cls.ANALYSIS_DEBUG and 'analysis' in module_name:
            return logging.DEBUG
        if cls.UI_DEBUG and module_name.startswith('ui'):
            return logging.DEBUG

        # Use default app level
        return getattr(logging, cls.APP_LOG_LEVEL)

    @classmethod
    def to_dict(cls) -> Dict:
        """Export current configuration as dictionary."""
        return {
            'debug_mode': cls.DEBUG_MODE,
            'verbose_mode': cls.VERBOSE_MODE,
            'zoom_pan_debug': cls.ZOOM_PAN_DEBUG,
            'image_loading_debug': cls.IMAGE_LOADING_DEBUG,
            'roi_debug': cls.ROI_DEBUG,
            'analysis_debug': cls.ANALYSIS_DEBUG,
            'ui_debug': cls.UI_DEBUG,
            'performance_debug': cls.PERFORMANCE_DEBUG,
            'app_log_level': cls.APP_LOG_LEVEL,
            'library_log_level': cls.LIBRARY_LOG_LEVEL,
        }


# =============================================================================
# PRESET CONFIGURATIONS - Quick ways to set multiple flags at once
# =============================================================================

class DebugPresets:
    """Pre-configured debug settings for common scenarios."""

    @staticmethod
    def apply_preset(preset_name: str):
        """Apply a preset configuration."""
        presets = {
            'off': DebugPresets.all_off,
            'normal': DebugPresets.normal,
            'debug': DebugPresets.debug,
            'verbose': DebugPresets.verbose,
            'zoom_pan': DebugPresets.zoom_pan_debug,
            'images': DebugPresets.image_debug,
            'performance': DebugPresets.performance_debug,
        }

        if preset_name in presets:
            presets[preset_name]()
            print(f"Applied debug preset: {preset_name}")
        else:
            print(f"Unknown preset: {preset_name}")
            print(f"Available presets: {', '.join(presets.keys())}")

    @staticmethod
    def all_off():
        """Turn off all debug flags - quiet mode."""
        DebugConfig.DEBUG_MODE = False
        DebugConfig.VERBOSE_MODE = False
        DebugConfig.ZOOM_PAN_DEBUG = False
        DebugConfig.IMAGE_LOADING_DEBUG = False
        DebugConfig.ROI_DEBUG = False
        DebugConfig.ANALYSIS_DEBUG = False
        DebugConfig.UI_DEBUG = False
        DebugConfig.PERFORMANCE_DEBUG = False
        DebugConfig.APP_LOG_LEVEL = 'WARNING'
        DebugConfig.LIBRARY_LOG_LEVEL = 'ERROR'

    @staticmethod
    def normal():
        """Normal operation - INFO level logging, no debug."""
        DebugPresets.all_off()
        DebugConfig.APP_LOG_LEVEL = 'INFO'
        DebugConfig.LIBRARY_LOG_LEVEL = 'WARNING'

    @staticmethod
    def debug():
        """General debug mode - app at DEBUG, libraries quiet."""
        DebugConfig.DEBUG_MODE = True
        DebugConfig.APP_LOG_LEVEL = 'DEBUG'
        DebugConfig.LIBRARY_LOG_LEVEL = 'WARNING'

    @staticmethod
    def verbose():
        """Verbose mode - everything at DEBUG level."""
        DebugConfig.DEBUG_MODE = True
        DebugConfig.VERBOSE_MODE = True
        DebugConfig.APP_LOG_LEVEL = 'DEBUG'
        DebugConfig.LIBRARY_LOG_LEVEL = 'DEBUG'
        # Enable all debug flags
        DebugConfig.ZOOM_PAN_DEBUG = True
        DebugConfig.IMAGE_LOADING_DEBUG = True
        DebugConfig.ROI_DEBUG = True
        DebugConfig.ANALYSIS_DEBUG = True
        DebugConfig.UI_DEBUG = True
        DebugConfig.PERFORMANCE_DEBUG = True

    @staticmethod
    def zoom_pan_debug():
        """Debug zoom and pan operations specifically."""
        DebugPresets.normal()
        DebugConfig.ZOOM_PAN_DEBUG = True
        DebugConfig.DEBUG_MODULES = ['ui.components.image_canvas']

    @staticmethod
    def image_debug():
        """Debug image loading and processing."""
        DebugPresets.normal()
        DebugConfig.IMAGE_LOADING_DEBUG = True
        DebugConfig.LIBRARY_LOG_LEVEL = 'INFO'  # See PIL messages

    @staticmethod
    def performance_debug():
        """Debug performance and timing."""
        DebugPresets.normal()
        DebugConfig.PERFORMANCE_DEBUG = True
        DebugConfig.PROFILE_PERFORMANCE = True
        DebugConfig.SHOW_TIMING = True


# =============================================================================
# LOGGING SETUP - Don't modify unless you know what you're doing
# =============================================================================

def setup_logging():
    """Configure logging based on DebugConfig settings."""
    # Set up formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    # Choose formatter based on debug mode
    formatter = detailed_formatter if DebugConfig.DEBUG_MODE else simple_formatter

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, filter in handlers
    root_logger.handlers.clear()

    # Console handler
    if DebugConfig.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, DebugConfig.APP_LOG_LEVEL))
        root_logger.addHandler(console_handler)

    # File handler
    if DebugConfig.LOG_TO_FILE:
        try:
            file_handler = logging.FileHandler(DebugConfig.LOG_FILENAME)
            file_handler.setFormatter(detailed_formatter)  # Always detailed in file
            file_handler.setLevel(logging.DEBUG)  # Capture everything in file
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Could not create log file: {e}")

    # Configure app modules
    app_level = getattr(logging, DebugConfig.APP_LOG_LEVEL)
    app_modules = ['app', 'ui', 'core', 'analysis', 'utils', 'models']

    for module in app_modules:
        logger = logging.getLogger(module)
        # Check for module-specific overrides
        logger.setLevel(DebugConfig.get_module_level(module))

    # Configure third-party libraries
    library_level = getattr(logging, DebugConfig.LIBRARY_LOG_LEVEL)
    libraries = ['PIL', 'matplotlib', 'numpy', 'scipy', 'cv2', 'urllib3', 'requests']

    for lib in libraries:
        logging.getLogger(lib).setLevel(library_level)

    # Apply module-specific debug levels
    for module in DebugConfig.DEBUG_MODULES:
        logging.getLogger(module).setLevel(logging.DEBUG)

    # Apply quiet modules
    for module in DebugConfig.QUIET_MODULES:
        logging.getLogger(module).setLevel(logging.ERROR)

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Debug configuration applied: {DebugConfig.to_dict()}")


# =============================================================================
# RUNTIME CONTROL - Functions to change debug settings on the fly
# =============================================================================

class DebugControl:
    """Runtime control of debug settings."""

    @staticmethod
    def toggle(flag_name: str) -> bool:
        """Toggle a debug flag and return new state."""
        if hasattr(DebugConfig, flag_name):
            current = getattr(DebugConfig, flag_name)
            setattr(DebugConfig, flag_name, not current)
            setup_logging()  # Reapply configuration
            return not current
        else:
            print(f"Unknown debug flag: {flag_name}")
            return False

    @staticmethod
    def enable(flag_name: str):
        """Enable a specific debug flag."""
        if hasattr(DebugConfig, flag_name):
            setattr(DebugConfig, flag_name, True)
            setup_logging()
            print(f"Enabled: {flag_name}")
        else:
            print(f"Unknown debug flag: {flag_name}")

    @staticmethod
    def disable(flag_name: str):
        """Disable a specific debug flag."""
        if hasattr(DebugConfig, flag_name):
            setattr(DebugConfig, flag_name, False)
            setup_logging()
            print(f"Disabled: {flag_name}")
        else:
            print(f"Unknown debug flag: {flag_name}")

    @staticmethod
    def status():
        """Print current debug configuration."""
        print("\nDebug Configuration Status:")
        print("-" * 40)
        config = DebugConfig.to_dict()
        for key, value in config.items():
            print(f"{key:20} : {value}")
        print("-" * 40)

    @staticmethod
    def help():
        """Show help for debug control."""
        help_text = """
Debug Control Help
==================

Quick Commands:
    from debug_config import DebugControl, DebugPresets

    # Apply presets
    DebugPresets.apply_preset('normal')   # Normal operation
    DebugPresets.apply_preset('debug')    # Debug mode
    DebugPresets.apply_preset('zoom_pan') # Debug zoom/pan

    # Toggle flags
    DebugControl.toggle('ZOOM_PAN_DEBUG')
    DebugControl.enable('IMAGE_LOADING_DEBUG')
    DebugControl.disable('VERBOSE_MODE')

    # Check status
    DebugControl.status()

Available Flags:
    DEBUG_MODE          - Master debug switch
    VERBOSE_MODE        - Extra verbose output
    ZOOM_PAN_DEBUG      - Debug zoom/pan operations
    IMAGE_LOADING_DEBUG - Debug image loading
    ROI_DEBUG          - Debug ROI selection
    ANALYSIS_DEBUG     - Debug image analysis
    UI_DEBUG           - Debug UI operations
    PERFORMANCE_DEBUG  - Debug performance

Available Presets:
    'off'        - All debug off, quiet mode
    'normal'     - Normal operation (INFO level)
    'debug'      - General debug mode
    'verbose'    - Everything at DEBUG level
    'zoom_pan'   - Debug zoom/pan specifically
    'images'     - Debug image loading
    'performance'- Debug performance
"""
        print(help_text)


# =============================================================================
# QUICK ACCESS FUNCTIONS
# =============================================================================

def quick_debug(feature: Optional[str] = None):
    """Quick function to enable debugging."""
    if feature:
        DebugPresets.apply_preset(feature)
    else:
        DebugPresets.apply_preset('debug')


def debug_off():
    """Turn off all debugging."""
    DebugPresets.apply_preset('off')


# Auto-setup logging when module is imported
if __name__ != "__main__":
    setup_logging()

# Example usage when run directly
if __name__ == "__main__":
    print("Debug Configuration Utility")
    print("=" * 40)
    DebugControl.help()
    print("\nCurrent Status:")
    DebugControl.status()