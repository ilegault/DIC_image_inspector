# ui/live_analyze/transparent_roi_selector.py - Transparent ROI Selector

import tkinter as tk
from PIL import Image, ImageTk
from typing import List, Tuple, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class TransparentROISelector:
    """
    Transparent overlay for ROI selection.
    
    CRITICAL: This overlay is shown AFTER capturing the original screen,
    ensuring the overlay never affects the analysis results.
    """
    
    def __init__(self, parent_window, original_screenshot: Image.Image, 
                 completion_callback: Optional[Callable] = None):
        """
        Initialize the transparent ROI selector.
        
        Args:
            parent_window: Parent tkinter window
            original_screenshot: The original screenshot taken BEFORE overlay
            completion_callback: Callback when ROI selection is complete
        """
        self.parent = parent_window
        # CRITICAL: Store the original screenshot taken BEFORE overlay
        self.original_screenshot = original_screenshot
        self.completion_callback = completion_callback
        
        # Create fullscreen window
        self.overlay = tk.Toplevel(parent_window)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-topmost', True)
        
        # CRITICAL: Set transparency AFTER capturing original screen
        self.overlay.attributes('-alpha', 0.3)  # 30% opacity
        self.overlay.configure(bg='black')
        
        # Canvas for drawing
        self.canvas = tk.Canvas(self.overlay, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)
        
        # Display the original screenshot as background
        self.display_screenshot_background()
        
        # ROI drawing state
        self.roi_points = []
        self.temp_lines = []
        self.preview_line = None
        self.is_drawing = False
        
        # Visual elements
        self.point_radius = 5
        self.line_width = 2
        self.point_color = '#00FF00'  # Green
        self.line_color = '#00FF00'   # Green
        self.preview_color = '#FFFF00'  # Yellow
        
        # Instructions
        self.instruction_text = None
        self.show_instructions()
        
        # Bind events
        self.bind_events()
        
        logger.info("TransparentROISelector initialized")
    
    def display_screenshot_background(self):
        """Display the original screenshot on canvas."""
        try:
            # Get canvas dimensions
            self.overlay.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not ready yet, try again after a delay
                self.overlay.after(100, self.display_screenshot_background)
                return
            
            # Resize screenshot to fit canvas if needed
            screenshot_resized = self.original_screenshot.resize(
                (canvas_width, canvas_height), 
                Image.Resampling.LANCZOS
            )
            
            # Convert PIL image to PhotoImage
            self.photo = ImageTk.PhotoImage(screenshot_resized)
            self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
            
            logger.info(f"Screenshot background displayed: {canvas_width}x{canvas_height}")
            
        except Exception as e:
            logger.error(f"Failed to display screenshot background: {e}")
    
    def show_instructions(self):
        """Show instruction text on the overlay."""
        instruction_text = (
            "ROI Selection Mode\n\n"
            "• Click to add points for ROI boundary\n"
            "• Right-click or press Enter to complete selection\n"
            "• Press Escape to cancel\n"
            "• Minimum 3 points required"
        )
        
        self.instruction_text = self.canvas.create_text(
            50, 50,
            text=instruction_text,
            fill='white',
            font=('Arial', 14, 'bold'),
            anchor='nw'
        )
    
    def bind_events(self):
        """Bind mouse and keyboard events."""
        # Mouse events
        self.canvas.bind('<Button-1>', self.on_left_click)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<Motion>', self.on_mouse_move)
        
        # Keyboard events
        self.overlay.bind('<Return>', self.on_enter_key)
        self.overlay.bind('<Escape>', self.on_escape_key)
        self.overlay.focus_set()
        
        # Window events
        self.overlay.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_left_click(self, event):
        """Handle left mouse click - add ROI point."""
        x, y = event.x, event.y
        
        # Add point to ROI
        self.roi_points.append((x, y))
        
        # Draw point
        self.draw_point(x, y)
        
        # Draw line to previous point
        if len(self.roi_points) > 1:
            prev_x, prev_y = self.roi_points[-2]
            line_id = self.canvas.create_line(
                prev_x, prev_y, x, y,
                fill=self.line_color,
                width=self.line_width
            )
            self.temp_lines.append(line_id)
        
        # Update status
        self.update_status_text()
        
        logger.debug(f"ROI point added: ({x}, {y}), total points: {len(self.roi_points)}")
    
    def on_right_click(self, event):
        """Handle right mouse click - complete ROI selection."""
        self.complete_roi_selection()
    
    def on_mouse_move(self, event):
        """Handle mouse movement - show preview line."""
        if len(self.roi_points) == 0:
            return
        
        # Remove previous preview line
        if self.preview_line:
            self.canvas.delete(self.preview_line)
        
        # Draw preview line from last point to current mouse position
        last_x, last_y = self.roi_points[-1]
        self.preview_line = self.canvas.create_line(
            last_x, last_y, event.x, event.y,
            fill=self.preview_color,
            width=1,
            dash=(5, 5)
        )
    
    def on_enter_key(self, event):
        """Handle Enter key - complete ROI selection."""
        self.complete_roi_selection()
    
    def on_escape_key(self, event):
        """Handle Escape key - cancel ROI selection."""
        self.cancel_roi_selection()
    
    def on_close(self):
        """Handle window close event."""
        self.cancel_roi_selection()
    
    def draw_point(self, x, y):
        """Draw a point on the canvas."""
        self.canvas.create_oval(
            x - self.point_radius, y - self.point_radius,
            x + self.point_radius, y + self.point_radius,
            fill=self.point_color,
            outline='white',
            width=1
        )
    
    def update_status_text(self):
        """Update the status/instruction text."""
        if self.instruction_text:
            self.canvas.delete(self.instruction_text)
        
        points_count = len(self.roi_points)
        if points_count < 3:
            status_text = (
                f"ROI Selection - {points_count} points selected\n\n"
                f"• Need at least 3 points (currently have {points_count})\n"
                "• Click to add more points\n"
                "• Right-click or Enter when done\n"
                "• Escape to cancel"
            )
        else:
            status_text = (
                f"ROI Selection - {points_count} points selected\n\n"
                "• Right-click or press Enter to complete\n"
                "• Click to add more points\n"
                "• Escape to cancel"
            )
        
        self.instruction_text = self.canvas.create_text(
            50, 50,
            text=status_text,
            fill='white',
            font=('Arial', 14, 'bold'),
            anchor='nw'
        )
    
    def complete_roi_selection(self):
        """Complete the ROI selection process."""
        if len(self.roi_points) < 3:
            logger.warning(f"ROI selection incomplete: only {len(self.roi_points)} points")
            return
        
        # Close the polygon by drawing line to first point
        if len(self.roi_points) > 2:
            first_x, first_y = self.roi_points[0]
            last_x, last_y = self.roi_points[-1]
            self.canvas.create_line(
                last_x, last_y, first_x, first_y,
                fill=self.line_color,
                width=self.line_width
            )
        
        logger.info(f"ROI selection completed with {len(self.roi_points)} points")
        
        # Convert canvas coordinates to screen coordinates
        screen_roi_points = self.convert_to_screen_coordinates(self.roi_points)
        
        # Call completion callback
        if self.completion_callback:
            self.completion_callback(screen_roi_points)
        
        # Close after a brief delay to show the completed polygon
        if self.overlay:  # Check if overlay still exists
            self.overlay.after(1000, self.close)
        else:
            self.close()  # Close immediately if overlay is None
    
    def convert_to_screen_coordinates(self, canvas_points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Convert canvas coordinates to screen coordinates.
        
        Since we're displaying the screenshot scaled to fit the canvas,
        we need to convert back to original screen coordinates.
        """
        try:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            screen_width = self.original_screenshot.width
            screen_height = self.original_screenshot.height
            
            # Calculate scaling factors
            scale_x = screen_width / canvas_width
            scale_y = screen_height / canvas_height
            
            # Convert points
            screen_points = []
            for canvas_x, canvas_y in canvas_points:
                screen_x = int(canvas_x * scale_x)
                screen_y = int(canvas_y * scale_y)
                screen_points.append((screen_x, screen_y))
            
            logger.info(f"Converted {len(canvas_points)} points from canvas to screen coordinates")
            return screen_points
            
        except Exception as e:
            logger.error(f"Failed to convert coordinates: {e}")
            return canvas_points  # Return original points as fallback
    
    def cancel_roi_selection(self):
        """Cancel the ROI selection process."""
        logger.info("ROI selection cancelled")
        
        # Call completion callback with empty list
        if self.completion_callback:
            self.completion_callback([])
        
        self.close()
    
    def close(self):
        """Close the ROI selector overlay."""
        try:
            if self.overlay:
                self.overlay.destroy()
                self.overlay = None
            logger.info("ROI selector closed")
        except Exception as e:
            logger.error(f"Error closing ROI selector: {e}")
    
    def hide(self):
        """Hide the overlay temporarily."""
        if self.overlay:
            self.overlay.withdraw()
    
    def show(self):
        """Show the overlay again."""
        if self.overlay:
            self.overlay.deiconify()
            self.overlay.lift()
            self.overlay.attributes('-topmost', True)