#!/usr/bin/env python3
# debug_zoom_pan.py - Quick Debug Script for Zoom/Pan Issues

"""
Quick debugging script for zoom and pan functionality.
Run this script or import functions to enable detailed debugging.
"""

import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging_control import (
    enable_zoom_pan_debug, 
    disable_zoom_pan_debug, 
    toggle_zoom_pan_debug,
    logging_controller,
    show_logging_help
)

def quick_zoom_debug():
    """
    Quick function to enable zoom/pan debugging.
    Call this from anywhere in your app to start debugging.
    """
    print("=" * 60)
    print("ZOOM/PAN DEBUG MODE ACTIVATED")
    print("=" * 60)
    
    enable_zoom_pan_debug()
    
    print("\nWhat this enables:")
    print("- Detailed logging for image canvas operations")
    print("- Mouse wheel zoom event tracking")
    print("- Pan operation tracking")
    print("- Image positioning and scaling calculations")
    print("- Scroll region and coordinate transformations")
    
    print("\nTo disable debug mode, call:")
    print(">>> from debug_zoom_pan import disable_zoom_pan_debug")
    print(">>> disable_zoom_pan_debug()")
    
    print("\nTo see current logging levels:")
    print(">>> logging_controller.print_current_levels()")
    
    print("=" * 60)

def show_debug_info():
    """Show current debug status and available functions."""
    print("\nZoom/Pan Debug Information:")
    print("-" * 40)
    
    canvas_logger_level = logging_controller.get_current_levels().get('ui.components.image_canvas', 'UNKNOWN')
    print(f"Image Canvas Logger Level: {canvas_logger_level}")
    
    if canvas_logger_level == 'DEBUG':
        print("✓ Zoom/Pan debugging is ENABLED")
    else:
        print("✗ Zoom/Pan debugging is DISABLED")
    
    print("\nAvailable functions:")
    print("- quick_zoom_debug()     : Enable detailed zoom/pan debugging")
    print("- disable_zoom_pan_debug() : Disable zoom/pan debugging")
    print("- toggle_zoom_pan_debug()  : Toggle zoom/pan debugging on/off")
    print("- show_debug_info()        : Show this information")
    
    print("\nFor full logging help:")
    print("- show_logging_help()      : Show all logging control functions")

def main():
    """Main function when script is run directly."""
    print("Zoom/Pan Debug Utility")
    print("=" * 30)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ['enable', 'on', 'start']:
            quick_zoom_debug()
        elif command in ['disable', 'off', 'stop']:
            disable_zoom_pan_debug()
        elif command in ['toggle']:
            toggle_zoom_pan_debug()
        elif command in ['status', 'info']:
            show_debug_info()
        elif command in ['help']:
            show_logging_help()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: enable, disable, toggle, status, help")
    else:
        show_debug_info()
        print("\nUsage:")
        print("python debug_zoom_pan.py [enable|disable|toggle|status|help]")
        print("\nOr import and use functions directly:")
        print(">>> from debug_zoom_pan import quick_zoom_debug")
        print(">>> quick_zoom_debug()")

if __name__ == "__main__":
    main()