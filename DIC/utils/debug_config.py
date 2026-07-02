"""
Debug configuration and logging preset management.

This module provides a simplified debug configuration system with preset logging
levels for different use cases. It allows easy switching between logging verbosity
levels without complex configuration. Simply change the preset in app.py to adjust
logging behavior across the entire application.

Usage:
    from utils.debug_config import DebugPresets

    DebugPresets.apply_preset('debug')  # Enable debug logging

Available presets:
    - 'off': Only errors
    - 'normal': Standard operation
    - 'debug': Detailed debug output
    - 'zoom_pan': Debug zoom and pan operations
    - 'verbose': Maximum debug level
"""

import logging
from typing import Dict


class DebugPresets:
    """Simple preset system - just apply and go."""

    @staticmethod
    def apply_preset(preset_name: str):
        """Apply a preset configuration."""

        # Clear any existing handlers to start fresh
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Define presets (simple dictionaries)
        presets = {
            'off': {
                'app_level': 'ERROR',
                'library_level': 'ERROR',
                'zoom_pan_debug': False,
                'console_format': 'simple'
            },
            'normal': {
                'app_level': 'INFO',
                'library_level': 'WARNING',
                'zoom_pan_debug': False,
                'console_format': 'simple'
            },
            'debug': {
                'app_level': 'DEBUG',
                'library_level': 'WARNING',
                'zoom_pan_debug': False,
                'console_format': 'detailed'
            },
            'zoom_pan': {
                'app_level': 'INFO',
                'library_level': 'WARNING',
                'zoom_pan_debug': True,
                'console_format': 'detailed'
            },
            'verbose': {
                'app_level': 'DEBUG',
                'library_level': 'DEBUG',
                'zoom_pan_debug': True,
                'console_format': 'detailed'
            }
        }

        if preset_name not in presets:
            print(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")
            preset_name = 'normal'  # fallback

        config = presets[preset_name]

        # Set up logging based on this config
        _setup_logging_from_config(config)

        print(f"✓ Applied debug preset: {preset_name}")


def _setup_logging_from_config(config: Dict):
    """Set up logging from a simple config dict."""

    # Choose formatter
    if config['console_format'] == 'detailed':
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    else:
        formatter = logging.Formatter('%(levelname)s - %(message)s')

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, config['app_level']))
    root_logger.addHandler(console_handler)

    # File handler (always detailed)
    try:
        file_handler = logging.FileHandler('dic_inspector.log')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Could not create log file: {e}")

    # Set app modules level
    app_modules = ['app', 'ui', 'core', 'analysis', 'utils', 'models']
    for module in app_modules:
        logging.getLogger(module).setLevel(getattr(logging, config['app_level']))

    # Special case for zoom/pan debug
    if config['zoom_pan_debug']:
        logging.getLogger('ui.main_components.image_canvas').setLevel(logging.DEBUG)

    # Set library levels
    libraries = ['PIL', 'matplotlib', 'numpy', 'scipy', 'cv2', 'urllib3', 'requests']
    for lib in libraries:
        logging.getLogger(lib).setLevel(getattr(logging, config['library_level']))

    # Always quiet these noisy modules
    logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
    logging.getLogger('PIL.PngImagePlugin').setLevel(logging.ERROR)


# Backward compatibility function
def setup_logging():
    """For backward compatibility - applies 'normal' preset."""
    DebugPresets.apply_preset('normal')


# Quick access functions
def debug_on():
    """Quick function to enable debugging."""
    DebugPresets.apply_preset('debug')


def debug_off():
    """Turn off all debugging."""
    DebugPresets.apply_preset('off')