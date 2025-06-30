# ui/dynamic_legend.py - CLEANED: Only 4 essential DIC spectrums

import tkinter as tk

class DynamicLegend:
    """Dynamic legend that updates based on selected color spectrum with stable layout"""

    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.legend_frame = None
        self.current_spectrum = 'custom_dic'

        # CLEANED: Only the 4 essential DIC spectrums
        self.spectrum_definitions = {
            'custom_dic': {
                'name': 'Custom DIC (Black→Red→Blue)',
                'colors': [
                    (0, 0, 0, "Critical (0-75%): Black - Not suitable for DIC"),
                    (120, 0, 0, "Minimum (75%): Red - Threshold for DIC"),
                    (255, 80, 0, "Good (80-85%): Orange - Acceptable for DIC"),
                    (255, 200, 0, "Very Good (85-90%): Yellow - Good for DIC"),
                    (120, 255, 180, "Excellent (90-95%): Cyan - Excellent for DIC"),
                    (0, 140, 255, "Perfect (95-100%): Blue - Ideal for DIC")
                ]
            },
            'zeiss_style_dic': {
                'name': 'ZEISS-Style Pattern Quality (Colorblind-Friendly)',
                'colors': [
                    (50, 0, 0, "Unusable (0-70%): No correlation possible"),
                    (255, 0, 0, "Poor (70-80%): Unreliable correlation"),
                    (255, 140, 0, "Acceptable (80-85%): Usable with uncertainty"),
                    (255, 255, 0, "Good (85-90%): Good correlation quality"),
                    (0, 255, 255, "Very Good (90-95%): Very reliable"),
                    (0, 100, 255, "Excellent (95-100%): Optimal pattern")
                ]
            },
            'ultra_strict_dic': {
                'name': 'Ultra-Strict DIC (Focus Quality)',
                'colors': [
                    (0, 0, 0, "Critical (0-90%): Black - Completely unsuitable"),
                    (80, 0, 0, "Poor (90-93%): Dark Red - Major issues"),
                    (180, 0, 0, "Marginal (93-95%): Red - Barely acceptable"),
                    (255, 140, 0, "Acceptable (95-97%): Orange - OK for DIC"),
                    (255, 255, 0, "Good (97-98%): Yellow - Good for DIC"),
                    (0, 255, 255, "Very Good (98-99%): Cyan - Very good"),
                    (0, 100, 255, "Perfect (99-100%): Blue - Ideal")
                ]
            },
            'focus_aware_dic': {
                'name': 'Focus-Aware DIC',
                'colors': [
                    (30, 0, 0, "Out of Focus (0-85%): Black-Red"),
                    (180, 50, 0, "Soft Focus (85-92%): Red-Orange"),
                    (255, 180, 0, "Acceptable (92-96%): Orange-Yellow"),
                    (128, 255, 128, "Good Focus (96-98%): Yellow-Cyan"),
                    (0, 180, 255, "Excellent (98-100%): Cyan-Blue")
                ]
            }
        }
        print(f"DynamicLegend initialized with 4 essential DIC spectrums")

    def create_legend(self, spectrum_type='custom_dic'):
        """Create legend with stable layout that doesn't affect canvas size"""
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

            # Create new legend frame with stable dimensions
            print("Creating new legend frame with fixed height")
            self.legend_frame = tk.Frame(self.parent_frame, bg='#34495e', relief='raised', bd=1)

            # Get spectrum definition
            spectrum_def = self.spectrum_definitions[spectrum_type]
            print(f"Using spectrum: {spectrum_def['name']} with {len(spectrum_def['colors'])} colors")

            # Title - smaller and more compact
            legend_title = tk.Label(self.legend_frame,
                                    text=f"Quality Legend - {spectrum_def['name']}:",
                                    font=('Arial', 9, 'bold'),
                                    fg='#ecf0f1', bg='#34495e')
            legend_title.pack(pady=(2, 1))

            # Color items frame with controlled height
            legend_items_frame = tk.Frame(self.legend_frame, bg='#34495e')
            legend_items_frame.pack(pady=2, expand=True, fill='both')

            # Create color items - more compact
            items_created = 0
            for r, g, b, label in spectrum_def['colors']:
                try:
                    # Convert RGB to hex for background color
                    bg_color = f"#{r:02x}{g:02x}{b:02x}"

                    # Determine text color based on brightness
                    brightness = (r * 0.299 + g * 0.587 + b * 0.114)
                    text_color = "white" if brightness < 128 else "black"

                    # Create more compact legend item
                    legend_item = tk.Label(legend_items_frame,
                                           text=f"  {label.split(':')[0]}  ",  # Only first part of label
                                           bg=bg_color,
                                           fg=text_color,
                                           font=('Arial', 8, 'bold'),
                                           relief='raised',
                                           bd=1,
                                           padx=4,
                                           pady=1)
                    legend_item.pack(side='left', padx=1, expand=True, fill='both')
                    items_created += 1

                except Exception as e:
                    print(f"Error creating legend item for {label}: {e}")
                    continue

            print(f"Created {items_created} legend items successfully")

            # Store current spectrum
            self.current_spectrum = spectrum_type

            # Show the legend with controlled layout
            self.show_legend()

            print(f"DynamicLegend created successfully for {spectrum_def['name']}")
            return True

        except Exception as e:
            print(f"ERROR in DynamicLegend.create_legend: {e}")
            import traceback
            traceback.print_exc()
            return False

    def show_legend(self):
        """Show the legend without affecting parent layout"""
        try:
            if self.legend_frame:
                print("Showing dynamic legend with controlled layout")
                # Use expand=True and fill='both' to use available space efficiently
                self.legend_frame.pack(expand=True, fill='both')

                # Force update to ensure visibility
                self.parent_frame.update_idletasks()
                print("Dynamic legend is now visible")
            else:
                print("WARNING: No legend frame exists to show")
        except Exception as e:
            print(f"ERROR showing legend: {e}")

    def hide_legend(self):
        """Hide the legend"""
        try:
            if self.legend_frame:
                print("Hiding dynamic legend")
                self.legend_frame.pack_forget()
                print("Dynamic legend hidden")
            else:
                print("No legend frame to hide")
        except Exception as e:
            print(f"ERROR hiding legend: {e}")

    def update_legend(self, spectrum_type):
        """Update the legend to match the new spectrum type"""
        print(f"DynamicLegend.update_legend called: {spectrum_type} (current: {self.current_spectrum})")

        if spectrum_type != self.current_spectrum:
            success = self.create_legend(spectrum_type)
            if success:
                print(f"Legend updated successfully to {spectrum_type}")
            else:
                print(f"Failed to update legend to {spectrum_type}")
        else:
            print(f"Legend already showing {spectrum_type}, no update needed")

    def destroy_legend(self):
        """Completely remove the legend"""
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