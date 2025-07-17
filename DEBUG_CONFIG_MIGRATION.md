# Debug Configuration Migration Guide

## Overview

The debug and logging configuration has been centralized into a single file: `utils/debug_config.py`. This replaces the previous scattered configuration files and provides a unified, easy-to-use system for controlling debug output.

## Files Removed

The following files have been moved to `backup_old_logging/` and are no longer used:

- `utils/logging_control.py` - Dynamic logging control utilities
- `debug_zoom_pan.py` - Zoom/pan specific debug script
- `logging_config.py` - Configuration file for logging levels

## New Centralized System

All debug and logging configuration is now handled by `utils/debug_config.py`, which provides:

### Classes and Functions

1. **DebugConfig** - Central configuration class with all debug flags
2. **DebugPresets** - Pre-configured debug settings for common scenarios
3. **DebugControl** - Runtime control of debug settings
4. **setup_logging()** - Automatic logging setup based on configuration

### Key Features

- **Easy toggles** - Simple boolean flags for different debug areas
- **Preset configurations** - Quick ways to set multiple flags at once
- **Runtime control** - Change debug settings without restarting
- **Module-specific debugging** - Target specific modules for debug output
- **Performance profiling** - Built-in performance monitoring options

## Migration Examples

### Old System → New System

| Old Code | New Code |
|----------|----------|
| `from utils.logging_control import quiet_mode; quiet_mode()` | `from utils.debug_config import DebugPresets; DebugPresets.apply_preset('off')` |
| `from utils.logging_control import normal_mode; normal_mode()` | `from utils.debug_config import DebugPresets; DebugPresets.apply_preset('normal')` |
| `from utils.logging_control import debug_mode; debug_mode()` | `from utils.debug_config import DebugPresets; DebugPresets.apply_preset('debug')` |
| `from utils.logging_control import verbose_mode; verbose_mode()` | `from utils.debug_config import DebugPresets; DebugPresets.apply_preset('verbose')` |
| `from utils.logging_control import enable_zoom_pan_debug; enable_zoom_pan_debug()` | `from utils.debug_config import DebugPresets; DebugPresets.apply_preset('zoom_pan')` |
| `from utils.logging_control import toggle_zoom_pan_debug; toggle_zoom_pan_debug()` | `from utils.debug_config import DebugControl; DebugControl.toggle('ZOOM_PAN_DEBUG')` |
| `from utils.logging_control import toggle_pil_debug; toggle_pil_debug()` | `from utils.debug_config import DebugControl; DebugControl.toggle('IMAGE_LOADING_DEBUG')` |
| `from debug_zoom_pan import quick_zoom_debug; quick_zoom_debug()` | `from utils.debug_config import DebugPresets; DebugPresets.apply_preset('zoom_pan')` |
| `LoggingController().set_app_debug_level('DEBUG')` | `DebugPresets.apply_preset('debug')` |
| `LoggingController().print_current_levels()` | `DebugControl.status()` |

## Quick Start Guide

### Basic Usage

```python
from utils.debug_config import DebugPresets, DebugControl

# Apply preset configurations
DebugPresets.apply_preset('normal')    # Normal operation
DebugPresets.apply_preset('debug')     # Debug mode
DebugPresets.apply_preset('zoom_pan')  # Debug zoom/pan specifically

# Check current status
DebugControl.status()

# Toggle individual flags
DebugControl.toggle('ZOOM_PAN_DEBUG')
DebugControl.enable('IMAGE_LOADING_DEBUG')
DebugControl.disable('VERBOSE_MODE')
```

### Available Presets

- `'off'` - All debug off, quiet mode
- `'normal'` - Normal operation (INFO level)
- `'debug'` - General debug mode
- `'verbose'` - Everything at DEBUG level
- `'zoom_pan'` - Debug zoom/pan specifically
- `'images'` - Debug image loading
- `'performance'` - Debug performance

### Available Debug Flags

- `DEBUG_MODE` - Master debug switch
- `VERBOSE_MODE` - Extra verbose output
- `ZOOM_PAN_DEBUG` - Debug zoom/pan operations
- `IMAGE_LOADING_DEBUG` - Debug image loading
- `ROI_DEBUG` - Debug ROI selection
- `ANALYSIS_DEBUG` - Debug image analysis
- `UI_DEBUG` - Debug UI operations
- `PERFORMANCE_DEBUG` - Debug performance

### Configuration File Editing

You can also directly edit `utils/debug_config.py` to change default settings:

```python
class DebugConfig:
    # Master switches
    DEBUG_MODE = True  # Enable debug mode by default
    VERBOSE_MODE = False
    
    # Feature-specific debug flags
    ZOOM_PAN_DEBUG = True  # Enable zoom/pan debugging
    IMAGE_LOADING_DEBUG = False
    # ... etc
```

## Testing

Run the test script to verify everything is working:

```bash
python test_debug_config.py
```

This will test all presets, individual controls, and show migration examples.

## Benefits of the New System

1. **Centralized** - All debug configuration in one place
2. **Consistent** - Unified API for all debug operations
3. **Flexible** - Easy to add new debug categories
4. **Runtime Control** - Change settings without restarting
5. **Preset Support** - Quick configuration for common scenarios
6. **Self-Documenting** - Built-in help and status functions
7. **Backward Compatible** - Easy migration path from old system

## Help and Documentation

For detailed help on using the new system:

```python
from utils.debug_config import DebugControl
DebugControl.help()
```

This will show all available commands, flags, and presets with examples.