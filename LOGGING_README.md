# Logging Control System

## Quick Start

The app now has much better control over what gets logged. The noisy PIL (image processing) messages are now suppressed by default.

### Current Setup (Recommended)
- **App logging**: INFO level (shows important events)
- **PIL logging**: WARNING level (hides the verbose import messages)
- **Third-party libraries**: WARNING level (reduces noise)

## Easy Configuration

### Option 1: Edit `logging_config.py` (Recommended)
```python
# Simple changes in logging_config.py
APP_LOG_LEVEL = 'INFO'        # For normal use
PIL_LOG_LEVEL = 'WARNING'     # Hides PIL noise
THIRD_PARTY_LOG_LEVEL = 'WARNING'  # Reduces other library noise
```

### Option 2: Use Presets
Uncomment this line in `logging_config.py`:
```python
ACTIVE_PRESET = 'normal'  # Options: 'quiet', 'normal', 'debug', 'verbose', 'image_debug'
```

## Common Scenarios

### Daily Use (Current Default)
```python
APP_LOG_LEVEL = 'INFO'
PIL_LOG_LEVEL = 'WARNING'
THIRD_PARTY_LOG_LEVEL = 'WARNING'
```
**Result**: Clean logs showing app events, no PIL noise

### Debugging App Issues
```python
APP_LOG_LEVEL = 'DEBUG'
PIL_LOG_LEVEL = 'WARNING'
THIRD_PARTY_LOG_LEVEL = 'WARNING'
```
**Result**: Detailed app debugging, still no PIL noise

### Debugging Image Loading Issues
```python
APP_LOG_LEVEL = 'INFO'
PIL_LOG_LEVEL = 'DEBUG'
THIRD_PARTY_LOG_LEVEL = 'WARNING'
```
**Result**: Normal app logging + detailed PIL image processing info

### Very Quiet Mode
```python
APP_LOG_LEVEL = 'WARNING'
PIL_LOG_LEVEL = 'ERROR'
THIRD_PARTY_LOG_LEVEL = 'ERROR'
```
**Result**: Only warnings and errors

## About Those Import Failures

The import failures you saw are **NOT a problem**:

```
PIL.Image - DEBUG - Image: failed to import FpxImagePlugin: No module named 'olefile'
PIL.Image - DEBUG - Image: failed to import MicImagePlugin: No module named 'olefile'
```

These are just PIL trying to import optional plugins for rare image formats (FPX and Microsoft Image Composer). Your app works perfectly without them. The `olefile` library is only needed for these specific formats.

## Runtime Control (Advanced)

You can also control logging from within the running app:

```python
from utils.logging_control import normal_mode, debug_mode, toggle_pil_debug

normal_mode()      # Set to recommended levels
debug_mode()       # Enable app debugging
toggle_pil_debug() # Toggle PIL debugging on/off
```

## File Locations

- **Main config**: `logging_config.py` (edit this for quick changes)
- **Advanced config**: `utils/constants.py` (DEBUG section)
- **Runtime control**: `utils/logging_control.py` (for programmatic control)
- **Log file**: `dic_inspector.log` (the actual log output)

## What Changed

1. **PIL logging suppressed**: No more verbose image plugin import messages
2. **Easy configuration**: Simple `logging_config.py` file for quick changes
3. **Preset modes**: Pre-configured logging levels for different scenarios
4. **Runtime control**: Functions to change logging levels without restarting
5. **Better organization**: Separate app logging from third-party library logging

## Restart Required

After editing `logging_config.py`, restart the app to apply changes.