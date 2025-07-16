# utils/logging_control.py - Dynamic Logging Control

"""
Utility functions for controlling logging levels at runtime.
Provides easy ways to toggle debug information without restarting the app.
"""

import logging
from typing import List, Optional
from .constants import DEBUG

class LoggingController:
    """Controller for managing application logging levels dynamically."""
    
    def __init__(self):
        self.original_levels = {}
        self._save_original_levels()
    
    def _save_original_levels(self):
        """Save original logging levels for restoration."""
        loggers_to_track = [
            '',  # root logger
            'PIL',
            'PIL.Image',
            'PIL.TiffImagePlugin',
            'matplotlib',
            'numpy',
            'app',
            'ui',
            'core',
            'analysis',
            'utils',
            'models'
        ]
        
        for logger_name in loggers_to_track:
            logger = logging.getLogger(logger_name)
            self.original_levels[logger_name] = logger.level
    
    def set_app_debug_level(self, level: str = 'DEBUG'):
        """
        Set debug level for application modules only.
        
        Args:
            level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        log_level = getattr(logging, level.upper())
        
        app_modules = [
            'app',
            'ui',
            'core', 
            'analysis',
            'utils',
            'models'
        ]
        
        for module in app_modules:
            logging.getLogger(module).setLevel(log_level)
        
        print(f"App modules logging level set to: {level}")
    
    def silence_third_party(self, level: str = 'WARNING'):
        """
        Set third-party libraries to WARNING or higher to reduce noise.
        
        Args:
            level: Minimum logging level for third-party libraries
        """
        log_level = getattr(logging, level.upper())
        
        third_party_modules = [
            'PIL',
            'PIL.Image', 
            'PIL.TiffImagePlugin',
            'PIL.PngImagePlugin',
            'PIL.JpegImagePlugin',
            'matplotlib',
            'numpy',
            'scipy',
            'cv2',
            'urllib3',
            'requests'
        ]
        
        for module in third_party_modules:
            logging.getLogger(module).setLevel(log_level)
        
        print(f"Third-party libraries logging level set to: {level}")
    
    def enable_pil_debug(self):
        """Enable PIL debug logging (useful for image format troubleshooting)."""
        logging.getLogger('PIL').setLevel(logging.DEBUG)
        logging.getLogger('PIL.Image').setLevel(logging.DEBUG)
        logging.getLogger('PIL.TiffImagePlugin').setLevel(logging.DEBUG)
        print("PIL debug logging enabled")
    
    def disable_pil_debug(self):
        """Disable PIL debug logging."""
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('PIL.Image').setLevel(logging.WARNING)
        logging.getLogger('PIL.TiffImagePlugin').setLevel(logging.WARNING)
        print("PIL debug logging disabled")
    
    def set_module_debug(self, modules: List[str], level: str = 'DEBUG'):
        """
        Set specific modules to debug level.
        
        Args:
            modules: List of module names to set to debug level
            level: Logging level to set
        """
        log_level = getattr(logging, level.upper())
        
        for module in modules:
            logging.getLogger(module).setLevel(log_level)
        
        print(f"Modules {modules} set to {level} level")
    
    def restore_original_levels(self):
        """Restore all loggers to their original levels."""
        for logger_name, level in self.original_levels.items():
            logging.getLogger(logger_name).setLevel(level)
        print("All logging levels restored to original settings")
    
    def get_current_levels(self) -> dict:
        """Get current logging levels for all tracked loggers."""
        current_levels = {}
        for logger_name in self.original_levels.keys():
            logger = logging.getLogger(logger_name)
            level_name = logging.getLevelName(logger.level)
            current_levels[logger_name or 'root'] = level_name
        return current_levels
    
    def print_current_levels(self):
        """Print current logging levels in a readable format."""
        levels = self.get_current_levels()
        print("\nCurrent Logging Levels:")
        print("-" * 30)
        for logger_name, level in sorted(levels.items()):
            print(f"{logger_name:20} : {level}")
        print("-" * 30)

# Global instance for easy access
logging_controller = LoggingController()

# Convenience functions
def quiet_mode():
    """Set logging to quiet mode - only warnings and errors."""
    logging_controller.set_app_debug_level('WARNING')
    logging_controller.silence_third_party('ERROR')
    print("Quiet mode enabled - only warnings and errors will be logged")

def normal_mode():
    """Set logging to normal mode - info level for app, warnings for third-party."""
    logging_controller.set_app_debug_level('INFO')
    logging_controller.silence_third_party('WARNING')
    print("Normal mode enabled - info level logging")

def debug_mode():
    """Set logging to debug mode - debug level for app, info for third-party."""
    logging_controller.set_app_debug_level('DEBUG')
    logging_controller.silence_third_party('INFO')
    print("Debug mode enabled - verbose logging for app modules")

def verbose_mode():
    """Set everything to debug mode - including third-party libraries."""
    logging_controller.set_app_debug_level('DEBUG')
    logging_controller.silence_third_party('DEBUG')
    print("Verbose mode enabled - debug logging for everything")

def toggle_pil_debug():
    """Toggle PIL debug logging on/off."""
    pil_logger = logging.getLogger('PIL')
    if pil_logger.level <= logging.DEBUG:
        logging_controller.disable_pil_debug()
    else:
        logging_controller.enable_pil_debug()

# Example usage functions that can be called from anywhere in the app
def show_logging_help():
    """Print help for logging control functions."""
    help_text = """
Logging Control Functions:
=========================

Quick Mode Functions:
- quiet_mode()     : Only warnings and errors
- normal_mode()    : Info for app, warnings for third-party (recommended)
- debug_mode()     : Debug for app, info for third-party  
- verbose_mode()   : Debug for everything (very noisy)

Specific Controls:
- toggle_pil_debug()                    : Toggle PIL image processing debug
- logging_controller.print_current_levels() : Show current logging levels
- logging_controller.restore_original_levels() : Reset to startup levels

Module-Specific:
- logging_controller.set_module_debug(['ui', 'core']) : Debug specific modules
- logging_controller.set_app_debug_level('INFO')      : Set app-wide level

Examples:
>>> from utils.logging_control import normal_mode, toggle_pil_debug
>>> normal_mode()  # Recommended for daily use
>>> toggle_pil_debug()  # When troubleshooting image loading
"""
    print(help_text)

if __name__ == "__main__":
    # Demo the functionality
    show_logging_help()
    logging_controller.print_current_levels()