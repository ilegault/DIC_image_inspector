# app.py

import tkinter as tk
import logging
import sys

try:
    # When run as a package
    from ui.main_window import DICQualityInspector
    from utils.constants import DEBUG
    import logging_config
except ImportError:
    # For direct execution
    from ui.main_window import DICQualityInspector
    from utils.constants import DEBUG
    import logging_config

def setup_logging():
    """Set up logging configuration based on constants."""
    if not DEBUG.get('enable_logging', True):
        return
    
    # Get logging level from logging_config.py or fall back to constants
    def get_app_log_level():
        if hasattr(logging_config, 'ACTIVE_PRESET') and logging_config.ACTIVE_PRESET:
            preset = logging_config.PRESETS.get(logging_config.ACTIVE_PRESET, {})
            level_str = preset.get('APP_LOG_LEVEL', getattr(logging_config, 'APP_LOG_LEVEL', 'INFO'))
        else:
            level_str = getattr(logging_config, 'APP_LOG_LEVEL', DEBUG.get('log_level', 'INFO'))
        return getattr(logging, level_str.upper())
    
    # Configure logging level
    log_level = get_app_log_level()
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if DEBUG.get('log_to_console', True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if DEBUG.get('log_to_file', True):
        try:
            file_handler = logging.FileHandler('dic_inspector.log')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Could not set up file logging: {e}")
    
    # Configure third-party library logging levels
    _configure_third_party_logging()
    
    # Log the logging configuration
    logger = logging.getLogger(__name__)
    app_level = logging.getLevelName(log_level)
    pil_level = logging.getLevelName(logging.getLogger('PIL').level)
    logger.info(f"Logging configured - App: {app_level}, PIL: {pil_level}, Console: {DEBUG.get('log_to_console', True)}, File: {DEBUG.get('log_to_file', True)}")

def _configure_third_party_logging():
    """Configure logging levels for third-party libraries to reduce noise."""
    
    # Get configuration from logging_config.py or fall back to constants
    def get_log_level(config_var, fallback_key, default='WARNING'):
        if hasattr(logging_config, 'ACTIVE_PRESET') and logging_config.ACTIVE_PRESET:
            preset = logging_config.PRESETS.get(logging_config.ACTIVE_PRESET, {})
            level_str = preset.get(config_var, getattr(logging_config, config_var, default))
        else:
            level_str = getattr(logging_config, config_var, DEBUG.get(fallback_key, default))
        return getattr(logging, level_str.upper())
    
    # PIL/Pillow logging - very verbose at DEBUG level
    pil_level = get_log_level('PIL_LOG_LEVEL', 'pil_log_level', 'WARNING')
    pil_loggers = [
        'PIL',
        'PIL.Image', 
        'PIL.TiffImagePlugin',
        'PIL.PngImagePlugin',
        'PIL.JpegImagePlugin',
        'PIL.BmpImagePlugin',
        'PIL.GifImagePlugin'
    ]
    
    for logger_name in pil_loggers:
        logging.getLogger(logger_name).setLevel(pil_level)
    
    # Other common third-party libraries
    third_party_level = get_log_level('THIRD_PARTY_LOG_LEVEL', 'third_party_log_level', 'WARNING')
    third_party_loggers = [
        'matplotlib',
        'numpy',
        'scipy', 
        'cv2',
        'urllib3',
        'requests'
    ]
    
    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(third_party_level)
    
    # Enable DEBUG for specific app modules if configured
    debug_modules = getattr(logging_config, 'DEBUG_MODULES', [])
    if debug_modules:
        debug_level = getattr(logging, 'DEBUG')
        for module_name in debug_modules:
            logging.getLogger(module_name).setLevel(debug_level)
    
    # Silence specific modules if configured
    silent_modules = getattr(logging_config, 'SILENT_MODULES', [])
    if silent_modules:
        error_level = getattr(logging, 'ERROR')
        for module_name in silent_modules:
            logging.getLogger(module_name).setLevel(error_level)

def main():
    # Set up logging first
    setup_logging()
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info("Starting DIC Image Quality Inspector")
    
    root = tk.Tk()
    app = DICQualityInspector(root)
    root.mainloop()

if __name__ == "__main__":
    main()