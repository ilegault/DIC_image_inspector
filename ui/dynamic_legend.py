import tkinter as tk
import numpy as np
from PIL import Image, ImageTk, ImageDraw


class DynamicLegend:
    """Dynamic legend that updates based on selected color spectrum"""

    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.legend_frame = None
        self.current_spectrum = 'custom_dic'

        # Spectrum definitions with their color mappings
        self.spectrum_definitions = {
            'custom_dic': {
                'name': 'Custom DIC',
                'colors': [
                    (32, 0, 0, "Critical"),
                    (128, 0, 0, "Very Poor"),
                    (255, 0, 0, "Poor"),
                    (255, 127, 0, "Challenging"),
                    (255, 255, 0, "Acceptable"),
                    (127, 255, 0, "Good"),
                    (0, 255, 0, "Very Good"),
                    (0, 127, 255, "Excellent")
                ]
            },
            'smooth_rainbow': {
                'name': 'Smooth Rainbow',
                'colors': [
                    (139, 0, 0, "Very Poor"),
                    (255, 0, 0, "Poor"),
                    (255, 127, 0, "Challenging"),
                    (255, 255, 0, "Acceptable"),
                    (127, 255, 0, "Good"),
                    (0, 255, 0, "Very Good"),
                    (0, 127, 255, "Excellent")
                ]
            },
            'thermal': {
                'name': 'Thermal',
                'colors': [
                    (0, 0, 0, "Very Poor"),
                    (64, 0, 0, "Poor"),
                    (128, 0, 0, "Challenging"),
                    (255, 0, 0, "Acceptable"),
                    (255, 127, 0, "Good"),
                    (255, 255, 0, "Very Good"),
                    (255, 255, 255, "Excellent")
                ]
            },
            'viridis_like': {
                'name': 'Viridis-like',
                'colors': [
                    (68, 1, 84, "Very Poor"),
                    (64, 67, 135, "Poor"),
                    (41, 120, 142, "Challenging"),
                    (34, 167, 132, "Acceptable"),
                    (121, 209, 81, "Good"),
                    (189, 223, 38, "Very Good"),
                    (253, 231, 37, "Excellent")
                ]
            },
            'opencv_jet': {
                'name': 'OpenCV Jet',
                'colors': [
                    (0, 0, 128, "Very Poor"),
                    (0, 0, 255, "Poor"),
                    (0, 127, 255, "Challenging"),
                    (0, 255, 255, "Acceptable"),
                    (127, 255, 127, "Good"),
                    (255, 255, 0, "Very Good"),
                    (255, 0, 0, "Excellent")
                ]
            },
            'opencv_viridis': {
                'name': 'OpenCV Viridis',
                'colors': [
                    (68, 1, 84, "Very Poor"),
                    (59, 82, 139, "Poor"),
                    (33, 144, 140, "Challenging"),
                    (93, 201, 99, "Acceptable"),
                    (253, 231, 37, "Good")
                ]
            },
            'opencv_plasma': {
                'name': 'OpenCV Plasma',
                'colors': [
                    (13, 8, 135, "Very Poor"),
                    (75, 3, 161, "Poor"),
                    (125, 3, 168, "Challenging"),
                    (166, 54, 134, "Acceptable"),
                    (201, 102, 94, "Good"),
                    (239, 164, 59, "Very Good"),
                    (240, 249, 33, "Excellent")
                ]
            },
            'opencv_inferno': {
                'name': 'OpenCV Inferno',
                'colors': [
                    (0, 0, 4, "Very Poor"),
                    (40, 11, 84, "Poor"),
                    (101, 21, 110, "Challenging"),
                    (159, 42, 99, "Acceptable"),
                    (212, 72, 66, "Good"),
                    (245, 125, 21, "Very Good"),
                    (252, 255, 164, "Excellent")
                ]
            }
        }
        print(f"DynamicLegend initialized with {len(self.spectrum_definitions)} spectrum definitions")

    def create_legend(self, spectrum_type='custom_dic'):
        """FIXED: Create or update the legend for the specified spectrum with proper error handling"""
        try:
            print(f"DynamicLegend.create_legend called with spectrum_type: {spectrum_type}")

            # Remove existing legend if it exists
            if self.legend_frame:
                print("Destroying existing legend frame")
                self.legend_frame.destroy()
                self.legend_frame = None

            # Validate spectrum type
            if spectrum_type not in self.spectrum_definitions:
                print(f"WARNING: Unknown spectrum type '{spectrum_type}', using 'custom_dic'")
                spectrum_type = 'custom_dic'

            # Create new legend frame
            print("Creating new legend frame")
            self.legend_frame = tk.Frame(self.parent_frame, bg='#34495e', relief='raised', bd=2)

            # Get spectrum definition
            spectrum_def = self.spectrum_definitions[spectrum_type]
            print(f"Using spectrum: {spectrum_def['name']} with {len(spectrum_def['colors'])} colors")

            # Title
            legend_title = tk.Label(self.legend_frame,
                                    text=f"Quality Map Legend - {spectrum_def['name']}:",
                                    font=('Arial', 11, 'bold'),
                                    fg='#ecf0f1', bg='#34495e')
            legend_title.pack(pady=5)

            # Color items frame
            legend_items_frame = tk.Frame(self.legend_frame, bg='#34495e')
            legend_items_frame.pack(pady=5)

            # Create color items
            items_created = 0
            for r, g, b, label in spectrum_def['colors']:
                try:
                    # Convert RGB to hex for background color
                    bg_color = f"#{r:02x}{g:02x}{b:02x}"

                    # Determine text color based on brightness
                    brightness = (r * 0.299 + g * 0.587 + b * 0.114)
                    text_color = "white" if brightness < 128 else "black"

                    # Create legend item
                    legend_item = tk.Label(legend_items_frame,
                                           text=f"  {label}  ",
                                           bg=bg_color,
                                           fg=text_color,
                                           font=('Arial', 9, 'bold'),
                                           relief='raised',
                                           bd=1,
                                           padx=8,
                                           pady=2)
                    legend_item.pack(side='left', padx=2)
                    items_created += 1

                except Exception as e:
                    print(f"Error creating legend item for {label}: {e}")
                    continue

            print(f"Created {items_created} legend items successfully")

            # Store current spectrum
            self.current_spectrum = spectrum_type

            # Show the legend immediately
            self.show_legend()

            print(f"DynamicLegend created successfully for {spectrum_def['name']}")
            return True

        except Exception as e:
            print(f"ERROR in DynamicLegend.create_legend: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_legend(self, spectrum_type):
        """FIXED: Update the legend to match the new spectrum type"""
        print(f"DynamicLegend.update_legend called: {spectrum_type} (current: {self.current_spectrum})")

        if spectrum_type != self.current_spectrum:
            success = self.create_legend(spectrum_type)
            if success:
                print(f"Legend updated successfully to {spectrum_type}")
            else:
                print(f"Failed to update legend to {spectrum_type}")
        else:
            print(f"Legend already showing {spectrum_type}, no update needed")

    def show_legend(self):
        """FIXED: Show the legend with proper error handling"""
        try:
            if self.legend_frame:
                print("Showing dynamic legend")
                self.legend_frame.pack(pady=5, fill='x')
                # Force update to ensure visibility
                self.parent_frame.update_idletasks()
                print("Dynamic legend is now visible")
            else:
                print("WARNING: No legend frame exists to show")
        except Exception as e:
            print(f"ERROR showing legend: {e}")

    def hide_legend(self):
        """FIXED: Hide the legend"""
        try:
            if self.legend_frame:
                print("Hiding dynamic legend")
                self.legend_frame.pack_forget()
                print("Dynamic legend hidden")
            else:
                print("No legend frame to hide")
        except Exception as e:
            print(f"ERROR hiding legend: {e}")

    def destroy_legend(self):
        """FIXED: Completely remove the legend"""
        try:
            if self.legend_frame:
                print("Destroying dynamic legend")
                self.legend_frame.destroy()
                self.legend_frame = None
                print("Dynamic legend destroyed")
        except Exception as e:
            print(f"ERROR destroying legend: {e}")

    def is_visible(self):
        """Check if legend is currently visible"""
        if self.legend_frame:
            try:
                # Check if the frame is packed and visible
                manager = self.legend_frame.winfo_manager()
                return manager == 'pack'
            except:
                return False
        return False