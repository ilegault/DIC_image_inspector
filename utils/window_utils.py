"""
Window management utilities for cross-platform GUI operations.

This module provides utility functions for managing Tkinter windows including
positioning, centering, multi-monitor support, and window creation helpers.
It ensures consistent window behavior across different display configurations.

Usage:
    from utils.window_utils import WindowManager

    # Center a window on parent
    WindowManager.center_on_parent(dialog, parent_window)

    # Create a child window
    child = WindowManager.create_child_window(parent, title="Dialog", width=600, height=400)
"""

import tkinter as tk
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class WindowManager:
    """Utility class for proper window management across multiple displays."""
    
    @staticmethod
    def get_parent_window_info(parent: tk.Widget) -> dict:
        """
        Get comprehensive information about the parent window.
        
        Args:
            parent: Parent widget/window
            
        Returns:
            Dictionary containing window position, size, and display info
        """
        try:
            # Find the root window
            root = parent
            while root.master:
                root = root.master
            
            # Force update to get accurate geometry
            root.update_idletasks()
            
            # Get window geometry
            geometry = root.geometry()
            # Parse geometry string (e.g., "800x600+100+50")
            size_part, pos_part = geometry.split('+', 1)
            width, height = map(int, size_part.split('x'))
            x, y = map(int, pos_part.split('+'))
            
            # Get screen dimensions from parent's perspective
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            # Calculate center of parent window
            center_x = x + width // 2
            center_y = y + height // 2
            
            return {
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'center_x': center_x,
                'center_y': center_y,
                'screen_width': screen_width,
                'screen_height': screen_height,
                'geometry': geometry
            }
            
        except Exception as e:
            logger.warning(f"Could not get parent window info: {e}")
            return {
                'x': 100, 'y': 100, 'width': 800, 'height': 600,
                'center_x': 500, 'center_y': 400,
                'screen_width': 1920, 'screen_height': 1080,
                'geometry': '800x600+100+100'
            }
    
    @staticmethod
    def position_window_relative_to_parent(
        window: tk.Toplevel, 
        parent: tk.Widget,
        width: int,
        height: int,
        offset_x: int = 0,
        offset_y: int = 0,
        center: bool = True
    ) -> None:
        """
        Position a window relative to its parent window.
        
        Args:
            window: The window to position
            parent: Parent widget/window
            width: Width of the window to position
            height: Height of the window to position
            offset_x: X offset from center/parent position
            offset_y: Y offset from center/parent position
            center: If True, center on parent; if False, offset from parent's top-left
        """
        try:
            parent_info = WindowManager.get_parent_window_info(parent)
            
            if center:
                # Center the window on the parent
                new_x = parent_info['center_x'] - width // 2 + offset_x
                new_y = parent_info['center_y'] - height // 2 + offset_y
            else:
                # Position relative to parent's top-left
                new_x = parent_info['x'] + offset_x
                new_y = parent_info['y'] + offset_y
            
            # Ensure window stays within screen bounds of parent's display
            screen_width = parent_info['screen_width']
            screen_height = parent_info['screen_height']
            
            # Adjust if window would go off-screen
            if new_x + width > screen_width:
                new_x = screen_width - width - 10
            if new_y + height > screen_height:
                new_y = screen_height - height - 10
            if new_x < 0:
                new_x = 10
            if new_y < 0:
                new_y = 10
            
            # Set the window geometry
            window.geometry(f"{width}x{height}+{new_x}+{new_y}")
            
            logger.debug(f"Positioned window at {new_x}, {new_y} relative to parent at {parent_info['x']}, {parent_info['y']}")
            
        except Exception as e:
            logger.warning(f"Could not position window relative to parent: {e}")
            # Fallback to default positioning
            window.geometry(f"{width}x{height}")
    
    @staticmethod
    def create_child_window(
        parent: tk.Widget,
        title: str,
        width: int,
        height: int,
        resizable: bool = True,
        topmost: bool = False,
        center: bool = True,
        offset_x: int = 0,
        offset_y: int = 0,
        transient: bool = True
    ) -> tk.Toplevel:
        """
        Create a properly positioned child window.
        
        Args:
            parent: Parent widget/window
            title: Window title
            width: Window width
            height: Window height
            resizable: Whether window is resizable
            topmost: Whether window should stay on top
            center: Whether to center on parent
            offset_x: X offset from center/parent
            offset_y: Y offset from center/parent
            transient: Whether window should be transient (affects window controls)
            
        Returns:
            Configured Toplevel window
        """
        try:
            # Create the window
            window = tk.Toplevel(parent)
            window.title(title)
            window.resizable(resizable, resizable)
            
            # Make it transient to parent only if requested
            # (transient windows don't show standard window controls)
            if transient:
                window.transient(parent)
            
            # Position the window
            WindowManager.position_window_relative_to_parent(
                window, parent, width, height, offset_x, offset_y, center
            )
            
            # Set additional attributes
            if topmost:
                window.attributes('-topmost', True)
            
            # Ensure proper focus
            window.lift()
            window.focus_force()
            
            return window
            
        except Exception as e:
            logger.error(f"Error creating child window: {e}")
            # Fallback to basic window creation
            window = tk.Toplevel(parent)
            window.title(title)
            window.geometry(f"{width}x{height}")
            return window
    
    @staticmethod
    def ensure_window_visible(window: tk.Toplevel) -> None:
        """
        Ensure a window is visible and properly focused.
        
        Args:
            window: Window to make visible
        """
        try:
            window.deiconify()  # Show if minimized
            window.lift()       # Bring to front
            window.focus_force()  # Force focus
            window.attributes('-topmost', True)  # Temporarily on top
            window.after(100, lambda: window.attributes('-topmost', False))  # Remove topmost after brief moment
        except Exception as e:
            logger.warning(f"Could not ensure window visibility: {e}")