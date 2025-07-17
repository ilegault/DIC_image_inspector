# Centralized Debug and Logging Control System

## Quick Start

The app now uses a centralized debug configuration system in `utils/debug_config.py`. This provides unified control over all debug and logging settings with easy-to-use presets and runtime controls.

### Current Setup (Default)
- **App logging**: INFO level (shows important events)
- **Library logging**: WARNING level (reduces noise from PIL, matplotlib, etc.)
- **Debug flags**: All disabled by default

## Easy Configuration

### Option 1: Use Presets (Recommended)
```python
from utils.debug_config import DebugPresets

# Quick preset configurations
DebugPresets.apply_preset('normal')     # Normal operation (recommended)
DebugPresets.apply_preset('debug')      # Debug mode for app development
DebugPresets.apply_preset('zoom_pan')   # Debug zoom/pan specifically
DebugPresets.apply_preset('verbose')    # Everything at debug level
```

### Option 2: Edit Configuration File
Edit `utils/debug_config.py` directly:
```python
class DebugConfig:
    DEBUG_MODE = True           # Enable debug mode
    ZOOM_PAN_DEBUG = True       # Debug zoom/pan operations
    IMAGE_LOADING_DEBUG = True  # Debug image loading
    APP_LOG_LEVEL = 'DEBUG'     # Set app logging level
```

## Common Scenarios

### Daily Use (Default)
```python
DebugPresets.apply_preset('normal')
```
**Result**: Clean logs showing app events, no library noise

### Debugging App Issues
```python
DebugPresets.apply_preset('debug')
```
**Result**: Detailed app debugging, libraries still quiet

### Debugging Image Loading Issues
```python
DebugPresets.apply_preset('images')
```
**Result**: Normal app logging + detailed image processing info

### Debugging Zoom/Pan Issues
```python
DebugPresets.apply_preset('zoom_pan')
```
**Result**: Detailed zoom and pan operation debugging

### Very Quiet Mode
```python
DebugPresets.apply_preset('off')
```
**Result**: Only warnings and errors

### Everything at Debug Level
```python
DebugPresets.apply_preset('verbose')
```
**Result**: Maximum verbosity for troubleshooting

## About Those Import Failures

The import failures you saw are **NOT a problem**:

```
PIL.Image - DEBUG - Image: failed to import FpxImagePlugin: No module named 'olefile'
PIL.Image - DEBUG - Image: failed to import MicImagePlugin: No module named 'olefile'
```

These are just PIL trying to import optional plugins for rare image formats (FPX and Microsoft Image Composer). Your app works perfectly without them. The `olefile` library is only needed for these specific formats.

## Runtime Control

You can control debug settings from within the running app without restarting:

```python
from utils.debug_config import DebugControl, DebugPresets

# Apply presets
DebugPresets.apply_preset('normal')
DebugPresets.apply_preset('debug')

# Toggle individual flags
DebugControl.toggle('ZOOM_PAN_DEBUG')
DebugControl.enable('IMAGE_LOADING_DEBUG')
DebugControl.disable('VERBOSE_MODE')

# Check current status
DebugControl.status()

# Get help
DebugControl.help()
```

## Available Debug Flags

- `DEBUG_MODE` - Master debug switch
- `VERBOSE_MODE` - Extra verbose output
- `ZOOM_PAN_DEBUG` - Debug zoom/pan operations
- `IMAGE_LOADING_DEBUG` - Debug image loading
- `ROI_DEBUG` - Debug ROI selection
- `ANALYSIS_DEBUG` - Debug image analysis
- `UI_DEBUG` - Debug UI operations
- `PERFORMANCE_DEBUG` - Debug performance

## File Locations

- **Main config**: `utils/debug_config.py` (centralized configuration)
- **Migration guide**: `DEBUG_CONFIG_MIGRATION.md` (how to migrate from old system)
- **Test script**: `test_debug_config.py` (test the configuration system)
- **Log file**: `dic_inspector.log` (the actual log output)

## What Changed

1. **Centralized configuration**: All debug settings in one file
2. **Unified API**: Consistent interface for all debug operations
3. **Runtime control**: Change settings without restarting
4. **Preset support**: Quick configuration for common scenarios
5. **Feature-specific debugging**: Target specific areas of the app
6. **Better organization**: Clear separation of concerns
7. **Migration support**: Easy transition from old system

## No Restart Required

Changes made through `DebugControl` and `DebugPresets` take effect immediately. Only direct edits to `utils/debug_config.py` require a restart.