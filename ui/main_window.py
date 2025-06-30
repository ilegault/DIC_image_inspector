# ui/main_window.py - UPDATED: Removed right panel, added popup report system

import tkinter as tk
import cv2
from tkinter import ttk, messagebox
import numpy as np
from PIL import ImageGrab
import threading
from ui.image_display import ImageDisplay
from ui.roi_handler import ROIHandler
from ui.file_operations import FileOperations
from ui.button_state_manager import ButtonStateManager
from analysis.core.subset_analyzer import determine_optimal_subset_size


class DICQualityInspector:
    def __init__(self, root):
        self.root = root
        self.root.title("DIC Image Quality Inspector - Compact View")
        self.root.geometry("1000x700")  # Reduced width since no right panel
        self.root.configure(bg='#2c3e50')

        # Variables
        self.current_image = None
        self.original_image = None
        self.analysis_results = {}
        self.roi_coords = None
        self.roi_selection_mode = False
        self.roi_start = None
        self.roi_rect = None

        self.selected_spectrum = tk.StringVar(value='custom_dic')

        # Create GUI
        self.create_gui()

        # Create managers
        self.image_display = ImageDisplay(self.image_canvas, self)
        self.file_operations = FileOperations(self)
        self.roi_handler = ROIHandler(self)
        self.state_manager = ButtonStateManager(self)

        # Connect UI elements to manager methods
        self.load_btn.config(command=self.file_operations.load_image)
        self.roi_btn.config(command=self.roi_handler.toggle_roi_selection)
        self.screenshot_btn.config(command=self.start_screenshot)
        self.analyze_btn.config(command=self.analyze_image)
        self.quality_map_btn.config(command=self.image_display.toggle_quality_map_overlay)
        self.save_btn.config(command=self.file_operations.save_report)
        self.show_results_btn.config(command=self.show_results_popup)  # New popup button
        self.quality_map_btn.config(state='disabled')

        # Verify dynamic_legend still exists after initialization
        print(f"Final check - dynamic_legend exists: {hasattr(self, 'dynamic_legend')}")
        if hasattr(self, 'dynamic_legend'):
            print(f"Final dynamic_legend object ID: {id(self.dynamic_legend)}")

    def create_gui(self):
        # Main title
        title_frame = tk.Frame(self.root, bg='#2c3e50')
        title_frame.pack(pady=10)

        title_label = tk.Label(title_frame, text="🔍 DIC Image Quality Inspector - Compact View",
                               font=('Arial', 24, 'bold'), fg='#ecf0f1', bg='#2c3e50')
        title_label.pack()

        # Control frame
        control_frame = tk.Frame(self.root, bg='#34495e', relief='raised', bd=2)
        control_frame.pack(fill='x', padx=10, pady=5)

        # Buttons - First row
        btn_frame1 = tk.Frame(control_frame, bg='#34495e')
        btn_frame1.pack(pady=5)

        self.load_btn = tk.Button(btn_frame1, text="📁 Load Image",
                                  bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                                  padx=20, pady=5)
        self.load_btn.pack(side='left', padx=5)

        self.screenshot_btn = tk.Button(btn_frame1, text="📸 Screen Capture",
                                        bg='#e67e22', fg='white', font=('Arial', 12, 'bold'),
                                        padx=20, pady=5)
        self.screenshot_btn.pack(side='left', padx=5)

        self.roi_btn = tk.Button(btn_frame1, text="🎯 Select ROI",
                                 bg='#9b59b6', fg='white', font=('Arial', 12, 'bold'),
                                 padx=20, pady=5, state='disabled')
        self.roi_btn.pack(side='left', padx=5)

        self.analyze_btn = tk.Button(btn_frame1, text="🔬 Analyze",
                                     bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                     padx=20, pady=5, state='disabled')
        self.analyze_btn.pack(side='left', padx=5)

        # Buttons - Second row
        btn_frame2 = tk.Frame(control_frame, bg='#34495e')
        btn_frame2.pack(pady=5)

        self.quality_map_btn = tk.Button(btn_frame2, text="🗺️ Quality Map",
                                         bg='#2ecc71', fg='white', font=('Arial', 12, 'bold'),
                                         padx=20, pady=5, state='disabled')
        self.quality_map_btn.pack(side='left', padx=5)

        # NEW: Show Results button (replaces right panel)
        self.show_results_btn = tk.Button(btn_frame2, text="📊 Show Results",
                                          bg='#8e44ad', fg='white', font=('Arial', 12, 'bold'),
                                          padx=20, pady=5, state='disabled')
        self.show_results_btn.pack(side='left', padx=5)

        self.save_btn = tk.Button(btn_frame2, text="💾 Save Report",
                                  bg='#7f8c8d', fg='white', font=('Arial', 12, 'bold'),
                                  padx=20, pady=5, state='disabled')
        self.save_btn.pack(side='left', padx=5)

        # Help button
        self.help_btn = tk.Button(btn_frame2, text="❓ Help",
                                  bg="#6c7b7f", fg="white", font=("Arial", 12, "bold"),
                                  padx=15, pady=5, command=self.show_help)
        self.help_btn.pack(side='left', padx=5)

        # ROI Info
        roi_info_frame = tk.Frame(control_frame, bg='#34495e')
        roi_info_frame.pack(pady=5)

        self.roi_info_label = tk.Label(roi_info_frame, text="ROI: Not Selected (analyzing full image)",
                                       font=('Arial', 10), fg='#bdc3c7', bg='#34495e')
        self.roi_info_label.pack()

        # REMOVED: Main content frame now only contains left panel (image area)
        # UPDATED: Single main frame for image display only
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Image panel (previously left panel, now the only panel)
        self.image_panel = tk.Frame(main_frame, bg='#34495e', relief='raised', bd=2)
        self.image_panel.pack(fill='both', expand=True, padx=5)

        img_title = tk.Label(self.image_panel, text="📸 Image Preview", font=('Arial', 16, 'bold'),
                             fg='#ecf0f1', bg='#34495e')
        img_title.pack(pady=10)

        # Image canvas with scrollbars
        canvas_frame = tk.Frame(self.image_panel, bg='#34495e')
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.image_canvas = tk.Canvas(canvas_frame, bg='white', width=800, height=500)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.image_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.image_canvas.xview)

        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Position components
        self.image_canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Image processing buttons
        process_frame = tk.Frame(self.image_panel, bg='#34495e')
        process_frame.pack(pady=10)

        # First row of buttons
        button_row1 = tk.Frame(process_frame, bg='#34495e')
        button_row1.pack()

        original_btn = tk.Button(button_row1, text="Original",
                                 bg='#95a5a6', fg='white', padx=10,
                                 command=lambda: self.image_display.show_original())
        original_btn.pack(side='left', padx=2)

        edges_btn = tk.Button(button_row1, text="Edges",
                              bg='#95a5a6', fg='white', padx=10,
                              command=lambda: self.image_display.show_edges())
        edges_btn.pack(side='left', padx=2)

        gradient_btn = tk.Button(button_row1, text="Gradient",
                                 bg='#95a5a6', fg='white', padx=10,
                                 command=lambda: self.image_display.show_gradient())
        gradient_btn.pack(side='left', padx=2)

        reset_display_btn = tk.Button(button_row1, text="🔄 Full Reset",
                                      bg='#e74c3c', fg='white', padx=10,
                                      command=self.full_reset)
        reset_display_btn.pack(side='left', padx=2)

        # Spectrum selection row
        spectrum_row = tk.Frame(process_frame, bg='#34495e')
        spectrum_row.pack(pady=5)

        spectrum_label = tk.Label(spectrum_row, text="Color Spectrum:",
                                  font=('Arial', 10), fg='#ecf0f1', bg='#34495e')
        spectrum_label.pack(side='left', padx=5)

        spectrum_options = [
            'custom_dic',
            'zeiss_style_dic',
            'ultra_strict_dic',
            'focus_aware_dic'
        ]

        self.spectrum_combo = ttk.Combobox(spectrum_row,
                                           textvariable=self.selected_spectrum,
                                           values=spectrum_options,
                                           state='readonly',
                                           width=15,
                                           font=('Arial', 9))
        self.spectrum_combo.pack(side='left', padx=5)
        self.spectrum_combo.bind('<<ComboboxSelected>>', self.on_spectrum_changed)
        self.spectrum_combo.set('custom_dic')

        # ZEISS Parameters Frame (initially hidden)
        self.zeiss_frame = tk.Frame(process_frame, bg='#34495e')

        zeiss_title = tk.Label(self.zeiss_frame, text="📐 ZEISS Parameters:",
                               font=('Arial', 10, 'bold'), fg='#3498db', bg='#34495e')
        zeiss_title.pack(side='left', padx=5)

        tk.Label(self.zeiss_frame, text="Facet:",
                 font=('Arial', 9), fg='#bdc3c7', bg='#34495e').pack(side='left', padx=(15, 2))

        self.facet_size_var = tk.StringVar(value="19")
        tk.Spinbox(self.zeiss_frame, from_=11, to=51, increment=2,
                   textvariable=self.facet_size_var, width=4,
                   font=('Arial', 8)).pack(side='left', padx=2)

        tk.Label(self.zeiss_frame, text="px",
                 font=('Arial', 8), fg='#95a5a6', bg='#34495e').pack(side='left', padx=(0, 10))

        tk.Label(self.zeiss_frame, text="Step:",
                 font=('Arial', 9), fg='#bdc3c7', bg='#34495e').pack(side='left', padx=(10, 2))

        self.point_distance_var = tk.StringVar(value="4")
        tk.Spinbox(self.zeiss_frame, from_=2, to=20, increment=1,
                   textvariable=self.point_distance_var, width=4,
                   font=('Arial', 8)).pack(side='left', padx=2)

        tk.Label(self.zeiss_frame, text="px",
                 font=('Arial', 8), fg='#95a5a6', bg='#34495e').pack(side='left', padx=(0, 10))

        tk.Label(self.zeiss_frame, text="(Smaller values = higher density, slower analysis)",
                 font=('Arial', 8), fg='#7f8c8d', bg='#34495e').pack(side='left', padx=5)

        # Dynamic legend initialization
        self.create_gui_dynamic_legend_section()

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Load an image and select ROI for accurate analysis")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief='sunken',
                              anchor='w', bg='#95a5a6', fg='white')
        status_bar.pack(side='bottom', fill='x')

    def create_gui_dynamic_legend_section(self):
        """Dynamic legend initialization with stable layout"""
        print("Creating legend container frame with fixed dimensions")
        self.legend_container = tk.Frame(self.image_panel, bg='#34495e', height=60)
        self.legend_container.pack(pady=5, fill='x')
        self.legend_container.pack_propagate(False)

        print("Initializing DynamicLegend")
        from ui.dynamic_legend import DynamicLegend
        self.dynamic_legend = DynamicLegend(self.legend_container)

        if self.dynamic_legend:
            print("DynamicLegend initialized successfully")
        else:
            print("ERROR: DynamicLegend initialization failed")

        print("Initially hiding legend until quality map is shown")

    def show_results_popup(self):
        """NEW: Show analysis results in a stable popup window"""
        if not self.analysis_results:
            messagebox.showwarning("No Results", "No analysis results available. Please analyze an image first.")
            return

        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("DIC Quality Analysis Results")
        popup.geometry("1000x800")
        popup.configure(bg='#2c3e50')
        popup.transient(self.root)
        popup.grab_set()

        # Make popup fully resizable
        popup.resizable(True, True)
        popup.minsize(800, 600)

        # Create a simple scrollable frame without complex canvas bindings
        main_frame = tk.Frame(popup, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')

        # Configure scrolling with a stable approach
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind('<Configure>', configure_scroll_region)

        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Configure canvas window width to match canvas width
        def configure_canvas_window(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)

        canvas.bind('<Configure>', configure_canvas_window)

        # Populate the scrollable frame with results
        self._populate_results_popup_stable(scrollable_frame, popup)

        # Simple mousewheel binding
        def on_mousewheel(event):
            try:
                if event.delta:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
            except:
                pass  # Ignore any scroll errors

        # Bind mousewheel only to the popup window
        popup.bind("<MouseWheel>", on_mousewheel)
        popup.bind("<Button-4>", on_mousewheel)
        popup.bind("<Button-5>", on_mousewheel)

    def _populate_results_popup_stable(self, parent_frame, popup_window):
        """Populate the results popup with stable layout"""
        results = self.analysis_results

        # Title
        title_label = tk.Label(parent_frame, text="🔬 DIC Image Quality Analysis Results",
                               font=('Arial', 18, 'bold'), fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=(0, 20))

        # SECTION 1: Executive Summary
        self._add_executive_summary_stable(parent_frame, results)

        # SECTION 2: Technical Analysis
        self._add_technical_analysis_stable(parent_frame, results)

        # SECTION 3: DIC Parameters
        self._add_dic_parameters_stable(parent_frame, results)

        # SECTION 4: Mathematical Background (Add this back with stable layout)
        self._add_mathematical_explanation_stable(parent_frame, results)

        # SECTION 5: Non-Technical Explanation (simplified)
        self._add_non_technical_explanation_stable(parent_frame, results)

        # SECTION 6: Recommendations (simplified)
        self._add_recommendations_stable(parent_frame, results)

        # SECTION 7: Image Information
        self._add_image_information_stable(parent_frame, results)

        # Close button
        close_btn = tk.Button(parent_frame, text="Close Results",
                              bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                              padx=30, pady=10, command=popup_window.destroy)
        close_btn.pack(pady=20)

    def _add_mathematical_explanation_stable(self, parent, results):
        """Add mathematical background section with stable layout"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        # Header
        header_frame = tk.Frame(section_frame, bg='#34495e')
        header_frame.pack(fill='x', pady=5)

        # Simple toggle button (without complex state management)
        self.math_section_visible = True  # Track visibility

        def toggle_math_section():
            if self.math_section_visible:
                math_content_frame.pack_forget()
                toggle_btn.config(text="📐 Mathematical Background & Equations [Click to Expand]")
                self.math_section_visible = False
            else:
                math_content_frame.pack(fill='x', padx=15, pady=10)
                toggle_btn.config(text="📐 Mathematical Background & Equations [Click to Collapse]")
                self.math_section_visible = True

        toggle_btn = tk.Button(header_frame,
                               text="📐 Mathematical Background & Equations [Click to Collapse]",
                               font=('Arial', 14, 'bold'), fg='#ecf0f1', bg='#2c3e50',
                               command=toggle_math_section, relief='flat',
                               activebackground='#34495e', activeforeground='#3498db')
        toggle_btn.pack(fill='x')

        # Content frame
        math_content_frame = tk.Frame(section_frame, bg='#34495e')
        math_content_frame.pack(fill='x', padx=15, pady=10)

        # Simplified text display with basic scrolling
        text_frame = tk.Frame(math_content_frame, bg='#34495e')
        text_frame.pack(fill='x')

        # Create text widget with fixed height to prevent layout issues
        math_text = tk.Text(text_frame,
                            height=20,  # Fixed height
                            wrap='none',  # No wrapping for equations
                            bg='#2c3e50', fg='#ecf0f1',
                            font=('Courier New', 9),  # Smaller font
                            relief='sunken', bd=1,
                            padx=10, pady=10)

        # Simple vertical scrollbar only
        v_scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=math_text.yview)
        math_text.configure(yscrollcommand=v_scrollbar.set)

        # Pack side by side
        math_text.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')

        # Generate and insert mathematical content
        math_content = self._generate_mathematical_content(results)
        math_text.insert('1.0', math_content)
        math_text.config(state='normal')  # Allow selection

        # Simple copy button
        button_frame = tk.Frame(math_content_frame, bg='#34495e')
        button_frame.pack(fill='x', pady=5)

        def copy_equations_stable():
            try:
                content = math_text.get('1.0', 'end-1c')
                math_text.clipboard_clear()
                math_text.clipboard_append(content)
                copy_btn.config(text="✅ Copied!", bg='#27ae60')

                # Use a simpler approach to reset the button
                def reset_button_text():
                    try:
                        copy_btn.config(text="📋 Copy Equations", bg='#3498db')
                    except:
                        pass  # Ignore if button is destroyed

                # Schedule the reset
                parent.after(2000, reset_button_text)

            except Exception as e:
                print(f"Error copying to clipboard: {e}")
                copy_btn.config(text="❌ Error", bg='#e74c3c')

                def reset_button_text():
                    try:
                        copy_btn.config(text="📋 Copy Equations", bg='#3498db')
                    except:
                        pass

                parent.after(2000, reset_button_text)

        copy_btn = tk.Button(button_frame, text="📋 Copy Equations",
                             bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                             command=copy_equations_stable, padx=15, pady=3)
        copy_btn.pack(side='right')

        instructions = tk.Label(button_frame,
                                text="💡 Tip: Select text and use Ctrl+C to copy specific sections",
                                font=('Arial', 9), fg='#95a5a6', bg='#34495e')
        instructions.pack(side='left')

    def _add_executive_summary_stable(self, parent, results):
        """Add executive summary section with stable layout"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        # Section title
        tk.Label(section_frame, text="📋 Executive Summary",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        # Overall score display
        score_frame = tk.Frame(section_frame, bg='#34495e')
        score_frame.pack(pady=10)

        overall_score = results['overall_score']
        score_text, score_color = self.get_quality_assessment_text(overall_score / 100.0)

        # Large score display
        score_display = tk.Frame(score_frame, bg='#34495e')
        score_display.pack()

        tk.Label(score_display, text=f"{overall_score:.1f}",
                 font=('Arial', 48, 'bold'), fg=score_color, bg='#34495e').pack(side='left')
        tk.Label(score_display, text="/100",
                 font=('Arial', 24), fg='#bdc3c7', bg='#34495e').pack(side='left', anchor='s', padx=(5, 0))

        tk.Label(score_frame, text=score_text,
                 font=('Arial', 14, 'bold'), fg=score_color, bg='#34495e').pack(pady=5)

        # Analysis method
        method_text = f"Analysis Method: {results.get('analysis_method', 'Full image')}"
        tk.Label(section_frame, text=method_text,
                 font=('Arial', 10), fg='#bdc3c7', bg='#34495e').pack(pady=(0, 10))

    def _add_technical_analysis_stable(self, parent, results):
        """Add technical analysis section with stable layout"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(section_frame, text="📊 Technical Analysis",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        stats = results.get('quality_map_stats', {})

        # Create grid for statistics
        stats_grid = tk.Frame(section_frame, bg='#34495e')
        stats_grid.pack(pady=10)

        # Left column
        left_col = tk.Frame(stats_grid, bg='#34495e')
        left_col.pack(side='left', padx=20)

        tk.Label(left_col, text="Quality Statistics:",
                 font=('Arial', 12, 'bold'), fg='#3498db', bg='#34495e').pack(anchor='w')
        tk.Label(left_col, text=f"• Maximum: {stats.get('max_quality', 0):.1f}%",
                 font=('Arial', 11), fg='#2ecc71', bg='#34495e').pack(anchor='w')
        tk.Label(left_col, text=f"• Average: {results['overall_score']:.1f}%",
                 font=('Arial', 11), fg='#3498db', bg='#34495e').pack(anchor='w')
        tk.Label(left_col, text=f"• Minimum: {stats.get('min_quality', 0):.1f}%",
                 font=('Arial', 11), fg='#e74c3c', bg='#34495e').pack(anchor='w')

        # Right column
        right_col = tk.Frame(stats_grid, bg='#34495e')
        right_col.pack(side='right', padx=20)

        tk.Label(right_col, text="Distribution:",
                 font=('Arial', 12, 'bold'), fg='#3498db', bg='#34495e').pack(anchor='w')
        tk.Label(right_col, text=f"• Median: {stats.get('median_quality', 0):.1f}%",
                 font=('Arial', 11), fg='#f39c12', bg='#34495e').pack(anchor='w')
        tk.Label(right_col, text=f"• Std Deviation: {results.get('quality_std', 0):.1f}%",
                 font=('Arial', 11), fg='#9b59b6', bg='#34495e').pack(anchor='w')
        tk.Label(right_col, text=f"• Spectrum: {results.get('spectrum_used', 'custom_dic')}",
                 font=('Arial', 11), fg='#95a5a6', bg='#34495e').pack(anchor='w')

    def _add_dic_parameters_stable(self, parent, results):
        """Add DIC parameters section with stable layout"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(section_frame, text="⚙️ Recommended DIC Parameters",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        dic_params = self._calculate_dic_parameters(results)

        # Parameters grid
        params_grid = tk.Frame(section_frame, bg='#34495e')
        params_grid.pack(pady=10)

        # Left column
        left_params = tk.Frame(params_grid, bg='#34495e')
        left_params.pack(side='left', padx=30)

        tk.Label(left_params, text="Correlation Setup:",
                 font=('Arial', 12, 'bold'), fg='#3498db', bg='#34495e').pack(anchor='w')
        tk.Label(left_params, text=f"• Subset Size: {dic_params['facet_size']} pixels",
                 font=('Arial', 11), fg='#ecf0f1', bg='#34495e').pack(anchor='w')
        tk.Label(left_params, text=f"• Step Size: {dic_params['step_size']} pixels",
                 font=('Arial', 11), fg='#ecf0f1', bg='#34495e').pack(anchor='w')

        # Right column
        right_params = tk.Frame(params_grid, bg='#34495e')
        right_params.pack(side='right', padx=30)

        tk.Label(right_params, text="Expected Performance:",
                 font=('Arial', 12, 'bold'), fg='#3498db', bg='#34495e').pack(anchor='w')
        tk.Label(right_params, text=f"• Overlap: {dic_params['overlap']}%",
                 font=('Arial', 11), fg='#ecf0f1', bg='#34495e').pack(anchor='w')
        tk.Label(right_params, text=f"• Accuracy: {dic_params['accuracy']}",
                 font=('Arial', 11), fg='#ecf0f1', bg='#34495e').pack(anchor='w')

    def _add_non_technical_explanation_stable(self, parent, results):
        """Add non-technical explanation with stable layout"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(section_frame, text="🔍 What This Means (Non-Technical)",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        # Simplified text display
        explanation = self._generate_non_technical_explanation(results)

        # Split explanation into paragraphs and display as labels
        paragraphs = explanation.split('\n\n')
        for paragraph in paragraphs[:5]:  # Limit to first 5 paragraphs to prevent overflow
            if paragraph.strip():
                label = tk.Label(section_frame, text=paragraph.strip(),
                                 font=('Arial', 10), fg='#ecf0f1', bg='#34495e',
                                 wraplength=800, justify='left')
                label.pack(anchor='w', padx=15, pady=2)

    def _add_recommendations_stable(self, parent, results):
        """Add recommendations with stable layout"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(section_frame, text="💡 Recommendations",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        recommendations = self._generate_recommendations(results['overall_score'])

        # Display first 8 recommendations as labels
        for i, rec in enumerate(recommendations[:8], 1):
            label = tk.Label(section_frame, text=f"{i}. {rec}",
                             font=('Arial', 10), fg='#ecf0f1', bg='#34495e',
                             wraplength=800, justify='left')
            label.pack(anchor='w', padx=15, pady=2)

    def _add_image_information_stable(self, parent, results):
        """Add image information with stable layout"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(section_frame, text="ℹ️ Image Information",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        info_frame = tk.Frame(section_frame, bg='#34495e')
        info_frame.pack(pady=10)

        # Image dimensions
        if hasattr(self, 'original_image') and self.original_image is not None:
            h, w = self.original_image.shape[:2]
            tk.Label(info_frame, text=f"Image Size: {w} × {h} pixels",
                     font=('Arial', 11), fg='#bdc3c7', bg='#34495e').pack()

        # ROI information
        if hasattr(self, 'roi_handler') and self.roi_handler.roi_coords and len(self.roi_handler.roi_coords) >= 3:
            roi_area = self._calculate_roi_area()
            if hasattr(self, 'original_image') and self.original_image is not None:
                h, w = self.original_image.shape[:2]
                total_area = w * h
                percentage = (roi_area / total_area * 100) if total_area > 0 else 0
                tk.Label(info_frame, text=f"ROI Area: {roi_area:.0f} pixels² ({percentage:.1f}% of image)",
                         font=('Arial', 11), fg='#bdc3c7', bg='#34495e').pack()
        else:
            tk.Label(info_frame, text="ROI: Full image analyzed",
                     font=('Arial', 11), fg='#bdc3c7', bg='#34495e').pack()

    def _populate_results_popup(self, parent_frame, popup_window):
        """Populate the results popup with comprehensive analysis data"""
        results = self.analysis_results

        # Title
        title_label = tk.Label(parent_frame, text="🔬 DIC Image Quality Analysis Results",
                               font=('Arial', 18, 'bold'), fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=(0, 20))

        # SECTION 1: Executive Summary
        self._add_executive_summary(parent_frame, results)

        # SECTION 2: Technical Analysis
        self._add_technical_analysis(parent_frame, results)

        # SECTION 3: DIC Parameters
        self._add_dic_parameters(parent_frame, results)

        # SECTION 4: Mathematical Background
        self._add_mathematical_explanation(parent_frame, results)

        # SECTION 5: Non-Technical Explanation
        self._add_non_technical_explanation(parent_frame, results)

        # SECTION 6: Recommendations
        self._add_recommendations(parent_frame, results)

        # SECTION 7: Image Information
        self._add_image_information(parent_frame, results)

        # Close button
        close_btn = tk.Button(parent_frame, text="Close Results",
                              bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                              padx=30, pady=10, command=popup_window.destroy)
        close_btn.pack(pady=20)

    def _add_executive_summary(self, parent, results):
        """Add executive summary section"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        # Section title
        tk.Label(section_frame, text="📋 Executive Summary",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        # Overall score display
        score_frame = tk.Frame(section_frame, bg='#34495e')
        score_frame.pack(pady=10)

        overall_score = results['overall_score']
        score_text, score_color = self.get_quality_assessment_text(overall_score / 100.0)

        # Large score display
        score_display = tk.Frame(score_frame, bg='#34495e')
        score_display.pack()

        tk.Label(score_display, text=f"{overall_score:.1f}",
                 font=('Arial', 48, 'bold'), fg=score_color, bg='#34495e').pack(side='left')
        tk.Label(score_display, text="/100",
                 font=('Arial', 24), fg='#bdc3c7', bg='#34495e').pack(side='left', anchor='s', padx=(5, 0))

        tk.Label(score_frame, text=score_text,
                 font=('Arial', 14, 'bold'), fg=score_color, bg='#34495e').pack(pady=5)

        # Analysis method
        method_text = f"Analysis Method: {results.get('analysis_method', 'Full image')}"
        tk.Label(section_frame, text=method_text,
                 font=('Arial', 10), fg='#bdc3c7', bg='#34495e').pack(pady=(0, 10))

    def _add_technical_analysis(self, parent, results):
        """Add technical analysis section"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(section_frame, text="📊 Technical Analysis",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        stats = results.get('quality_map_stats', {})

        # Create grid for statistics
        stats_grid = tk.Frame(section_frame, bg='#34495e')
        stats_grid.pack(pady=10)

        # Left column
        left_col = tk.Frame(stats_grid, bg='#34495e')
        left_col.pack(side='left', padx=20)

        tk.Label(left_col, text="Quality Statistics:",
                 font=('Arial', 12, 'bold'), fg='#3498db', bg='#34495e').pack(anchor='w')
        tk.Label(left_col, text=f"• Maximum: {stats.get('max_quality', 0):.1f}%",
                 font=('Arial', 11), fg='#2ecc71', bg='#34495e').pack(anchor='w')
        tk.Label(left_col, text=f"• Average: {results['overall_score']:.1f}%",
                 font=('Arial', 11), fg='#3498db', bg='#34495e').pack(anchor='w')
        tk.Label(left_col, text=f"• Minimum: {stats.get('min_quality', 0):.1f}%",
                 font=('Arial', 11), fg='#e74c3c', bg='#34495e').pack(anchor='w')

        # Right column
        right_col = tk.Frame(stats_grid, bg='#34495e')
        right_col.pack(side='right', padx=20)

        tk.Label(right_col, text="Distribution:",
                 font=('Arial', 12, 'bold'), fg='#3498db', bg='#34495e').pack(anchor='w')
        tk.Label(right_col, text=f"• Median: {stats.get('median_quality', 0):.1f}%",
                 font=('Arial', 11), fg='#f39c12', bg='#34495e').pack(anchor='w')
        tk.Label(right_col, text=f"• Std Deviation: {results.get('quality_std', 0):.1f}%",
                 font=('Arial', 11), fg='#9b59b6', bg='#34495e').pack(anchor='w')
        tk.Label(right_col, text=f"• Spectrum: {results.get('spectrum_used', 'custom_dic')}",
                 font=('Arial', 11), fg='#95a5a6', bg='#34495e').pack(anchor='w')

    def _add_dic_parameters(self, parent, results):
        """Add DIC parameters section"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(section_frame, text="⚙️ Recommended DIC Parameters",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        dic_params = self._calculate_dic_parameters(results)

        # Parameters grid
        params_grid = tk.Frame(section_frame, bg='#34495e')
        params_grid.pack(pady=10)

        # Left column
        left_params = tk.Frame(params_grid, bg='#34495e')
        left_params.pack(side='left', padx=30)

        tk.Label(left_params, text="Correlation Setup:",
                 font=('Arial', 12, 'bold'), fg='#3498db', bg='#34495e').pack(anchor='w')
        tk.Label(left_params, text=f"• Subset Size: {dic_params['facet_size']} pixels",
                 font=('Arial', 11), fg='#ecf0f1', bg='#34495e').pack(anchor='w')
        tk.Label(left_params, text=f"• Step Size: {dic_params['step_size']} pixels",
                 font=('Arial', 11), fg='#ecf0f1', bg='#34495e').pack(anchor='w')

        # Right column
        right_params = tk.Frame(params_grid, bg='#34495e')
        right_params.pack(side='right', padx=30)

        tk.Label(right_params, text="Expected Performance:",
                 font=('Arial', 12, 'bold'), fg='#3498db', bg='#34495e').pack(anchor='w')
        tk.Label(right_params, text=f"• Overlap: {dic_params['overlap']}%",
                 font=('Arial', 11), fg='#ecf0f1', bg='#34495e').pack(anchor='w')
        tk.Label(right_params, text=f"• Accuracy: {dic_params['accuracy']}",
                 font=('Arial', 11), fg='#ecf0f1', bg='#34495e').pack(anchor='w')

    def _add_mathematical_explanation(self, parent, results):
        """Add mathematical background and equations section with expandable layout"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='both', expand=True, padx=10, pady=10)  # Changed to expand=True

        # Header with expand/collapse functionality
        header_frame = tk.Frame(section_frame, bg='#34495e')
        header_frame.pack(fill='x', pady=5)

        self.math_expanded = tk.BooleanVar(value=True)  # Start expanded

        def toggle_math_section():
            if self.math_expanded.get():
                math_content_frame.pack_forget()
                toggle_btn.config(text="📐 Mathematical Background & Equations [Click to Expand]")
                self.math_expanded.set(False)
            else:
                math_content_frame.pack(fill='both', expand=True, padx=15, pady=10)
                toggle_btn.config(text="📐 Mathematical Background & Equations [Click to Collapse]")
                self.math_expanded.set(True)

        toggle_btn = tk.Button(header_frame,
                               text="📐 Mathematical Background & Equations [Click to Collapse]",
                               font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#2c3e50',
                               command=toggle_math_section, relief='flat',
                               activebackground='#34495e', activeforeground='#3498db')
        toggle_btn.pack(fill='x')

        # Create expandable content frame
        math_content_frame = tk.Frame(section_frame, bg='#34495e')
        math_content_frame.pack(fill='both', expand=True, padx=15, pady=10)

        # Create frame for text widget and scrollbars
        text_container = tk.Frame(math_content_frame, bg='#34495e')
        text_container.pack(fill='both', expand=True)

        # Create text widget with both scrollbars for large content
        math_text = tk.Text(text_container,
                            wrap='none',  # No wrapping for equations
                            bg='#2c3e50', fg='#ecf0f1',
                            font=('Courier New', 10),
                            relief='sunken', bd=1,
                            padx=10, pady=10,
                            insertbackground='#ecf0f1')

        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(text_container, orient='vertical', command=math_text.yview)
        math_text.configure(yscrollcommand=v_scrollbar.set)

        # Horizontal scrollbar for wide equations
        h_scrollbar = ttk.Scrollbar(text_container, orient='horizontal', command=math_text.xview)
        math_text.configure(xscrollcommand=h_scrollbar.set)

        # Grid layout for text widget and scrollbars
        math_text.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid weights for proper expansion
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)

        # Generate and insert mathematical content
        math_content = self._generate_mathematical_content(results)
        math_text.insert('1.0', math_content)

        # Configure text widget as read-only but allow selection/copy
        math_text.config(state='normal')  # Keep normal for copy functionality

        # Add a button to copy all equations to clipboard
        button_frame = tk.Frame(math_content_frame, bg='#34495e')
        button_frame.pack(fill='x', pady=5)

        def copy_equations():
            try:
                # Get all text content
                content = math_text.get('1.0', 'end-1c')
                # Copy to clipboard
                math_text.clipboard_clear()
                math_text.clipboard_append(content)
                # Show confirmation
                copy_btn.config(text="✅ Copied!", bg='#27ae60')

                # Reset button text after 2 seconds
                def reset_button():
                    copy_btn.config(text="📋 Copy Equations", bg='#3498db')

                math_text.after(2000, reset_button)
            except Exception as e:
                print(f"Error copying to clipboard: {e}")
                copy_btn.config(text="❌ Error", bg='#e74c3c')

                # Reset button text after error
                def reset_button():
                    copy_btn.config(text="📋 Copy Equations", bg='#3498db')

                math_text.after(2000, reset_button)

        copy_btn = tk.Button(button_frame, text="📋 Copy Equations",
                             bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                             command=copy_equations, padx=15, pady=3)
        copy_btn.pack(side='right')

        # Instructions label
        instructions = tk.Label(button_frame,
                                text="💡 Tip: Use Ctrl+A to select all, Ctrl+C to copy, or click the copy button",
                                font=('Arial', 9), fg='#95a5a6', bg='#34495e')
        instructions.pack(side='left')

    def _generate_mathematical_content(self, results):
        """Generate mathematical explanation content with equations"""

        content = """MATHEMATICAL FOUNDATION OF DIC QUALITY ANALYSIS

═══════════════════════════════════════════════════════════════════════════════

1. GRADIENT CONTENT ANALYSIS
═══════════════════════════════

The primary quality metric is based on gradient analysis using the Sobel operator:

Gradient Calculation:
    Gx(x,y) = I(x+1,y-1) + 2×I(x+1,y) + I(x+1,y+1) - I(x-1,y-1) - 2×I(x-1,y) - I(x-1,y+1)
    Gy(x,y) = I(x-1,y+1) + 2×I(x,y+1) + I(x+1,y+1) - I(x-1,y-1) - 2×I(x,y-1) - I(x+1,y-1)

Gradient Magnitude:
    |∇I(x,y)| = √(Gx² + Gy²)

Sum of Squared Gradients (SSG):
    SSG = Σ Σ |∇I(x,y)|²
         x y

Normalized SSG:
    SSG_norm = SSG / (N × 255²)
    where N = total number of pixels

═══════════════════════════════════════════════════════════════════════════════

2. CONTRAST ANALYSIS
═══════════════════════

Multiple contrast measures are computed and combined:

RMS Contrast:
    C_rms = σ / μ
    where σ = standard deviation, μ = mean intensity

Michelson Contrast:
    C_michelson = (I_max - I_min) / (I_max + I_min)

Weber Contrast:
    C_weber = (I_max - μ) / μ

Local Contrast (5×5 windows):
    C_local = σ_local / μ_local

Combined Contrast Score:
    C_total = 0.4×C_rms + 0.3×C_michelson + 0.2×C_weber + 0.1×C_local

═══════════════════════════════════════════════════════════════════════════════

3. SPECKLE MORPHOLOGY ANALYSIS
═══════════════════════════════

Binary image creation using adaptive thresholding:
    B(x,y) = { 255  if I(x,y) > T(x,y)
              { 0    otherwise

where T(x,y) is the local adaptive threshold:
    T(x,y) = μ_local(x,y) - C

Connected component analysis for speckle identification:
    Area_i = number of pixels in component i

Speckle diameter estimation:
    d_i = 2 × √(Area_i / π)

Speckle density calculation:
    ρ = N_speckles / (W × H)
    where N_speckles = number of valid speckles, W×H = image dimensions

═══════════════════════════════════════════════════════════════════════════════

4. INFORMATION CONTENT (ENTROPY)
═══════════════════════════════

Shannon Entropy calculation:
    H = -Σ p_i × log₂(p_i)
        i

where p_i is the probability of intensity level i:
    p_i = n_i / N_total

Local entropy in sliding windows:
    H_local(x,y) = -Σ p_ij × log₂(p_ij)
                   ij

Information Quality Score:
    I_score = 0.6×(H/H_max) + 0.4×(H_local_avg/H_local_max)

═══════════════════════════════════════════════════════════════════════════════

5. NOISE ASSESSMENT
═══════════════════════

Signal-to-Noise Ratio calculation using bilateral filtering:
    I_denoised = BilateralFilter(I, d=5, σ_color=50, σ_space=50)

Noise estimation:
    N(x,y) = I(x,y) - I_denoised(x,y)

SNR calculation:
    SNR = σ_signal / σ_noise = σ(I_denoised) / σ(N)

SNR in decibels:
    SNR_dB = 20 × log₁₀(SNR)

Noise quality score:
    Q_noise = min(1.0, SNR / 30.0)

═══════════════════════════════════════════════════════════════════════════════

6. OVERALL QUALITY COMPUTATION
═══════════════════════════════

The final quality score is a weighted combination:

Q_total = w₁×Q_gradient + w₂×Q_contrast + w₃×Q_entropy + w₄×Q_pattern + w₅×Q_noise

Standard weights:
    w₁ = 0.40  (Gradient content - most important for DIC)
    w₂ = 0.25  (Contrast quality)
    w₃ = 0.20  (Information content)
    w₄ = 0.10  (Pattern complexity)
    w₅ = 0.05  (Noise level)

Constraint: Σwᵢ = 1.0

═══════════════════════════════════════════════════════════════════════════════

7. DIC-SPECIFIC CONSIDERATIONS
═══════════════════════════════

Subset Size Optimization:
Based on autocorrelation analysis and feature size estimation.

Recommended subset size:
    s_opt = max(11, min(51, 2.5 × d_feature))
    where d_feature is the average feature diameter

Step Size Calculation:
    step = s_opt × (1 - overlap_fraction)
    typically overlap_fraction = 0.75 (75% overlap)

Expected Displacement Accuracy:
    σ_displacement ≈ 0.01 to 0.1 pixels (depending on quality score)

Quality-Accuracy Relationship:
    σ_displacement = α × exp(-β × Q_total)
    where α, β are empirically determined constants

═══════════════════════════════════════════════════════════════════════════════

8. SPECTRUM-SPECIFIC THRESHOLDS
═══════════════════════════════

Custom DIC Spectrum (Strict):
    f(Q) = { Black     if Q < 0.75  (Unsuitable)
           { Red       if 0.75 ≤ Q < 0.80  (Minimum)
           { Orange    if 0.80 ≤ Q < 0.85  (Good)
           { Yellow    if 0.85 ≤ Q < 0.90  (Very Good)
           { Cyan      if 0.90 ≤ Q < 0.95  (Excellent)
           { Blue      if Q ≥ 0.95  (Perfect)

ZEISS-Style Spectrum:
    More lenient thresholds with professional color mapping
    emphasizing correlation reliability over strict quality requirements.

═══════════════════════════════════════════════════════════════════════════════

CURRENT ANALYSIS RESULTS:
"""

        # Add current analysis specific details
        overall_score = results['overall_score']
        content += f"\nOverall Quality Score: {overall_score:.1f}/100 ({overall_score / 100:.3f} normalized)\n"

        stats = results.get('quality_map_stats', {})
        content += f"Quality Distribution:\n"
        content += f"  • σ (Standard Deviation): {results.get('quality_std', 0):.2f}%\n"
        content += f"  • Range: [{stats.get('min_quality', 0):.1f}%, {stats.get('max_quality', 0):.1f}%]\n"
        content += f"  • Median: {stats.get('median_quality', 0):.1f}%\n"

        dic_params = self._calculate_dic_parameters(results)
        content += f"\nOptimized DIC Parameters:\n"
        content += f"  • Subset size (s_opt): {dic_params['facet_size']} pixels\n"
        content += f"  • Step size: {dic_params['step_size']} pixels\n"
        content += f"  • Overlap ratio: {dic_params['overlap'] / 100:.2f}\n"
        content += f"  • Expected accuracy: {dic_params['accuracy']}\n"

        analysis_method = results.get('analysis_method', 'Full image')
        spectrum_used = results.get('spectrum_used', 'custom_dic')
        content += f"\nAnalysis Configuration:\n"
        content += f"  • Method: {analysis_method}\n"
        content += f"  • Color spectrum: {spectrum_used}\n"

        if spectrum_used == 'zeiss_style_dic':
            content += f"  • ZEISS facet size: {getattr(self, 'facet_size_var', tk.StringVar(value='19')).get()} pixels\n"
            content += f"  • ZEISS point distance: {getattr(self, 'point_distance_var', tk.StringVar(value='4')).get()} pixels\n"

        content += "\n═══════════════════════════════════════════════════════════════════════════════\n"
        content += "References:\n"
        content += "• Pan, B. (2018). Digital image correlation for surface deformation measurement.\n"
        content += "• Sutton, M.A. et al. (2009). Image correlation for shape, motion and deformation measurements.\n"
        content += "• Reu, P.L. (2015). All about speckles: Speckle density. Experimental Techniques.\n"
        content += "• Blaber, J. et al. (2015). Ncorr: Open-source 2D digital image correlation.\n"

        return content

    def _add_non_technical_explanation(self, parent, results):
        """Add non-technical explanation section with better expandability"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='both', expand=True, padx=10, pady=10)  # Made expandable

        tk.Label(section_frame, text="🔍 What This Means (Non-Technical)",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        # Create expandable text frame
        text_frame = tk.Frame(section_frame, bg='#34495e')
        text_frame.pack(fill='both', expand=True, padx=15, pady=10)

        # Text widget with scrollbars
        explanation_text = tk.Text(text_frame,
                                   wrap='word',  # Word wrap for readability
                                   bg='#2c3e50', fg='#ecf0f1',
                                   font=('Arial', 11),
                                   relief='sunken', bd=1,
                                   padx=15, pady=10,
                                   insertbackground='#ecf0f1')

        # Scrollbar
        explanation_scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=explanation_text.yview)
        explanation_text.configure(yscrollcommand=explanation_scrollbar.set)

        # Pack with expansion
        explanation_text.pack(side='left', fill='both', expand=True)
        explanation_scrollbar.pack(side='right', fill='y')

        # Generate explanation based on score
        explanation = self._generate_non_technical_explanation(results)
        explanation_text.insert('1.0', explanation)
        explanation_text.config(state='normal')  # Allow text selection for copying

    def _add_recommendations(self, parent, results):
        """Add recommendations section with better expandability"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='both', expand=True, padx=10, pady=10)  # Made expandable

        tk.Label(section_frame, text="💡 Recommendations",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        recommendations = self._generate_recommendations(results['overall_score'])

        # Create expandable text widget for recommendations
        rec_frame = tk.Frame(section_frame, bg='#34495e')
        rec_frame.pack(fill='both', expand=True, padx=15, pady=10)

        rec_text = tk.Text(rec_frame,
                           wrap='word',
                           bg='#2c3e50', fg='#ecf0f1',
                           font=('Arial', 11),
                           relief='sunken', bd=1,
                           padx=15, pady=10,
                           insertbackground='#ecf0f1')

        # Scrollbar for recommendations
        rec_scrollbar = ttk.Scrollbar(rec_frame, orient='vertical', command=rec_text.yview)
        rec_text.configure(yscrollcommand=rec_scrollbar.set)

        # Pack with expansion
        rec_text.pack(side='left', fill='both', expand=True)
        rec_scrollbar.pack(side='right', fill='y')

        # Insert recommendations with better formatting
        for i, rec in enumerate(recommendations, 1):
            rec_text.insert('end', f"{i:2d}. {rec}\n\n")

        rec_text.config(state='normal')  # Allow text selection

    def _add_image_information(self, parent, results):
        """Add image information section"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(section_frame, text="ℹ️ Image Information",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        info_frame = tk.Frame(section_frame, bg='#34495e')
        info_frame.pack(pady=10)

        # Image dimensions
        if hasattr(self, 'original_image') and self.original_image is not None:
            h, w = self.original_image.shape[:2]
            tk.Label(info_frame, text=f"Image Size: {w} × {h} pixels",
                     font=('Arial', 11), fg='#bdc3c7', bg='#34495e').pack()

        # ROI information
        if hasattr(self, 'roi_handler') and self.roi_handler.roi_coords and len(self.roi_handler.roi_coords) >= 3:
            roi_area = self._calculate_roi_area()
            if hasattr(self, 'original_image') and self.original_image is not None:
                h, w = self.original_image.shape[:2]
                total_area = w * h
                percentage = (roi_area / total_area * 100) if total_area > 0 else 0
                tk.Label(info_frame, text=f"ROI Area: {roi_area:.0f} pixels² ({percentage:.1f}% of image)",
                         font=('Arial', 11), fg='#bdc3c7', bg='#34495e').pack()
        else:
            tk.Label(info_frame, text="ROI: Full image analyzed",
                     font=('Arial', 11), fg='#bdc3c7', bg='#34495e').pack()
        """Add non-technical explanation section"""
        section_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(section_frame, text="🔍 What This Means (Non-Technical)",
                 font=('Arial', 16, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=10)

        # Create text widget for explanation
        text_frame = tk.Frame(section_frame, bg='#34495e')
        text_frame.pack(fill='both', expand=True, padx=15, pady=10)

        explanation_text = tk.Text(text_frame, height=12, wrap='word',
                                   bg='#2c3e50', fg='#ecf0f1', font=('Arial', 11),
                                   relief='sunken', bd=1, padx=10, pady=10)
        explanation_text.pack(fill='both', expand=True)

        # Generate explanation based on score
        explanation = self._generate_non_technical_explanation(results)
        explanation_text.insert('1.0', explanation)
        explanation_text.config(state='disabled')

    def _generate_non_technical_explanation(self, results):
        """Generate a non-technical explanation of the analysis results"""
        score = results['overall_score']

        explanation = f"""Digital Image Correlation (DIC) Analysis Explanation:

WHAT WE MEASURED:
This analysis examined your image to determine how well it will work for measuring tiny movements and deformations. Think of it like checking if a photograph has enough detail and contrast to track specific points accurately.

YOUR RESULT: {score:.1f}/100

WHAT THIS SCORE MEANS:
"""

        if score >= 90:
            explanation += """• EXCELLENT: Your image has outstanding quality for precise measurements
• The pattern has excellent contrast and detail
• You can expect very accurate displacement measurements
• Perfect for critical engineering applications"""

        elif score >= 75:
            explanation += """• VERY GOOD: Your image has good quality for reliable measurements
• The pattern has good contrast and sufficient detail
• You can expect reliable displacement measurements
• Suitable for most engineering applications"""

        elif score >= 60:
            explanation += """• GOOD: Your image has acceptable quality for measurements
• The pattern has reasonable contrast and detail
• You can expect moderately accurate measurements
• May need careful analysis parameter selection"""

        elif score >= 45:
            explanation += """• ACCEPTABLE: Your image has marginal quality for measurements
• The pattern has limited contrast or detail
• Measurements may have increased uncertainty
• Consider improving lighting or pattern if possible"""

        elif score >= 30:
            explanation += """• CHALLENGING: Your image has poor quality for precise measurements
• The pattern lacks sufficient contrast or detail
• Measurements will have significant uncertainty
• Strong recommendation to improve the image quality"""

        else:
            explanation += """• POOR: Your image is not suitable for reliable measurements
• The pattern lacks the necessary contrast and detail
• Measurements will be unreliable or may fail completely
• Image quality improvement is essential before proceeding"""

        explanation += f"""

HOW THE ANALYSIS WORKS:
The software examines small regions (subsets) across your image, looking for:
• Sharp edges and clear patterns that can be tracked accurately
• Good contrast between light and dark areas
• Consistent lighting without shadows or glare
• Appropriate speckle or texture patterns for correlation

ANALYSIS METHOD USED:
{results.get('analysis_method', 'Full image')} - This tells you whether we analyzed your entire image or just the region you selected.

TECHNICAL CONTEXT:
Digital Image Correlation works by comparing images before and after deformation to calculate displacement. The quality of these measurements depends heavily on the image pattern quality, which is what this analysis evaluates.

NEXT STEPS:
Based on your score of {score:.1f}/100, please review the recommendations section for specific guidance on whether to proceed with your current setup or make improvements first."""

        return explanation

    # Keep all the existing methods from the original file
    def start_screenshot(self):
        """Start screenshot capture process"""
        from ctypes import windll

        # Set DPI awareness for consistent coordinates
        windll.shcore.SetProcessDpiAwareness(1)

        # Reset analysis results and quality map data when taking a new screenshot
        self.analysis_results = {}
        if hasattr(self.image_display, 'quality_map_data'):
            self.image_display.quality_map_data = None
            self.image_display.quality_visualization = None
            self.image_display.showing_quality_overlay = False

        # Disable buttons until analysis is performed
        self.quality_map_btn.config(state='disabled')
        self.show_results_btn.config(state='disabled')

        self.root.withdraw()  # Hide main window

        # Create screenshot window
        screenshot_window = tk.Toplevel()
        screenshot_window.attributes('-fullscreen', True)
        screenshot_window.attributes('-alpha', 0.3)
        screenshot_window.configure(bg='black')
        screenshot_window.attributes('-topmost', True)

        instructions = tk.Label(screenshot_window,
                                text="Click and drag to select a screen region, or press ESC to cancel",
                                font=('Arial', 16), fg="white", bg="black")
        instructions.pack(expand=True)

        # Create canvas for drawing selection rectangle
        selection_canvas = tk.Canvas(screenshot_window, highlightthickness=0)
        selection_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Screenshot selection variables
        self.start_x = self.start_y = 0
        self.rect_id = None

        def start_selection(event):
            self.start_x, self.start_y = event.x, event.y
            if self.rect_id:
                selection_canvas.delete(self.rect_id)

        def update_selection(event):
            if self.rect_id:
                selection_canvas.delete(self.rect_id)
            self.rect_id = selection_canvas.create_rectangle(self.start_x, self.start_y,
                                                             event.x, event.y, outline='red', width=3)

        def end_selection(event):
            # Store selection coordinates
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)

            # Close screenshot window
            screenshot_window.destroy()

            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                try:
                    # Take screenshot
                    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))

                    # Show main window after capture is ready
                    self.root.deiconify()
                    self.root.update()

                    # Store image data
                    self.original_image = np.array(screenshot)
                    self.current_image = self.original_image.copy()

                    # Clear previous ROI
                    self.roi_handler.update_roi_info()

                    # Use same approach as load_image_from_path
                    self.image_display.display_image(screenshot)

                    # Reset view position
                    self.image_canvas.xview_moveto(0)
                    self.image_canvas.yview_moveto(0)

                    # Update state to image_loaded
                    if hasattr(self, 'state_manager'):
                        self.state_manager.update_state("image_loaded")

                    self.status_var.set(f"Screenshot captured: {screenshot.width}x{screenshot.height} pixels")

                except Exception as e:
                    self.root.deiconify()
                    messagebox.showerror("Error", f"Failed to capture screenshot: {str(e)}")

                    # Reset to no_image state on error
                    if hasattr(self, 'state_manager'):
                        self.state_manager.update_state("no_image")
            else:
                self.root.deiconify()
                self.status_var.set("Screenshot cancelled - area too small")

        def cancel_screenshot(event=None):
            screenshot_window.destroy()
            self.root.deiconify()
            return "break"

        # Bind events
        screenshot_window.bind('<Button-1>', start_selection)
        screenshot_window.bind('<B1-Motion>', update_selection)
        screenshot_window.bind('<ButtonRelease-1>', end_selection)

        # Add multiple bindings to ensure ESC key is captured
        screenshot_window.bind('<Escape>', cancel_screenshot)
        selection_canvas.bind('<Escape>', cancel_screenshot)
        instructions.bind('<Escape>', cancel_screenshot)

        # Bind key press at the application level
        screenshot_window.bind_all('<Escape>', cancel_screenshot)

        # Force focus and grab all events
        screenshot_window.focus_force()
        screenshot_window.grab_set()
        screenshot_window.update()

    def _analyze_worker(self):
        """Worker thread for analysis - UPDATED with spectrum support"""
        try:
            # Get selected spectrum type
            spectrum_type = getattr(self, 'selected_spectrum', None)
            if spectrum_type:
                spectrum_type = spectrum_type.get()
            else:
                spectrum_type = 'custom_dic'  # Default

            print(f"Generating quality map with {spectrum_type} spectrum...")

            # Check if ZEISS-style analysis is requested
            if spectrum_type == 'zeiss_style_dic':
                # Get ZEISS parameters from UI
                facet_size = int(self.facet_size_var.get()) if hasattr(self, 'facet_size_var') else 19
                point_distance = int(self.point_distance_var.get()) if hasattr(self, 'point_distance_var') else 4

                print(f"Using ZEISS-style analysis: facet_size={facet_size}, point_distance={point_distance}")

                # Import the ZEISS-style function
                from analysis.quality_map.map_generator import generate_zeiss_style_quality_map

                # Generate quality map with ZEISS-style analysis
                quality_map, visualization = generate_zeiss_style_quality_map(
                    self.original_image,
                    subset_size=facet_size,
                    step_size=point_distance
                )
            else:
                # Use standard analysis
                from analysis.quality_map.map_generator import generate_quality_map

                # Generate quality map with selected spectrum
                quality_map, visualization = generate_quality_map(
                    self.original_image,
                    colormap=spectrum_type
                )

            # Store quality map data in image display for overlay
            self.image_display.quality_map_data = quality_map
            self.image_display.quality_visualization = visualization
            print(
                f"Quality map generated: shape {quality_map.shape}, range {quality_map.min():.3f}-{quality_map.max():.3f}")

            # FIXED: Initialize variables before conditional blocks
            roi_quality_scores = None
            use_roi_calculation = False

            # Calculate overall score from ROI region only (to match what user sees)
            if hasattr(self, 'roi_handler') and self.roi_handler.roi_coords and len(self.roi_handler.roi_coords) >= 3:
                try:
                    # Extract quality scores from ROI region only
                    roi_quality_scores = self._extract_roi_quality_scores(quality_map, self.roi_handler.roi_coords)
                    if roi_quality_scores is not None and len(roi_quality_scores) > 0:
                        average_quality = float(np.mean(roi_quality_scores) * 100)
                        use_roi_calculation = True
                        print(
                            f"ROI-based quality calculation: {average_quality:.1f}% (from {len(roi_quality_scores)} ROI pixels)")
                    else:
                        # ROI extraction failed, fall back to full image
                        average_quality = float(np.mean(quality_map) * 100)
                        print(f"ROI extraction failed, using full image quality: {average_quality:.1f}%")
                except Exception as e:
                    print(f"Error in ROI quality extraction: {e}")
                    # Fall back to full image calculation
                    average_quality = float(np.mean(quality_map) * 100)
                    print(f"Fallback to full image quality calculation: {average_quality:.1f}%")
            else:
                # No ROI - use full image average
                average_quality = float(np.mean(quality_map) * 100)
                print(f"Full image quality calculation: {average_quality:.1f}%")

            # Determine optimal subset size for DIC parameters
            from analysis.core.subset_analyzer import determine_optimal_subset_size
            if len(self.original_image.shape) == 3:
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)
            else:
                gray = self.original_image.copy()
            self.optimal_subset_size = determine_optimal_subset_size(gray)

            # FIXED: Use appropriate data source for statistics
            if use_roi_calculation and roi_quality_scores is not None:
                # Use ROI-based statistics
                quality_data_for_stats = roi_quality_scores
                print("Using ROI-based statistics")
            else:
                # Use full quality map statistics
                quality_data_for_stats = quality_map.flatten()
                print("Using full image statistics")

            # Create results with consistent data source
            analysis_results = {
                'overall_score': round(average_quality, 1),
                'average_quality': average_quality,
                'quality_std': float(np.std(quality_data_for_stats) * 100),
                'optimal_subset_size': self.optimal_subset_size,
                'quality_map_stats': {
                    'min_quality': float(np.min(quality_data_for_stats) * 100),
                    'max_quality': float(np.max(quality_data_for_stats) * 100),
                    'median_quality': float(np.median(quality_data_for_stats) * 100)
                },
                'analysis_method': 'ROI-based' if use_roi_calculation else 'Full image',
                'spectrum_used': spectrum_type
            }

            print(
                f"Analysis complete. Overall score: {average_quality:.1f} ({analysis_results['analysis_method']}) with {spectrum_type}")

            # Call completion handler on UI thread
            self.root.after(0, lambda: self._on_analysis_complete(analysis_results))

        except Exception as e:
            import traceback
            error_message = str(e)
            traceback_info = traceback.format_exc()
            print(f"Analysis Error: {error_message}\n{traceback_info}")
            self.root.after(0, lambda: self._on_analysis_error(error_message))

    def _extract_roi_quality_scores(self, quality_map, roi_coords):
        """Extract quality scores from ROI region only"""
        try:
            import cv2
            import numpy as np

            # Validate inputs
            if quality_map is None or roi_coords is None:
                print("Invalid inputs to _extract_roi_quality_scores")
                return None

            if len(roi_coords) < 3:
                print("ROI coords too short for polygon")
                return None

            # Create mask for ROI
            mask = np.zeros(quality_map.shape[:2], dtype=np.uint8)
            pts = np.array(roi_coords, dtype=np.int32)

            # Validate ROI coordinates are within image bounds
            h, w = quality_map.shape[:2]
            pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)  # Clamp x coordinates
            pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)  # Clamp y coordinates

            cv2.fillPoly(mask, [pts], 255)

            # Extract quality scores from ROI pixels only
            roi_mask_bool = mask > 0
            roi_pixel_count = np.sum(roi_mask_bool)

            if roi_pixel_count == 0:
                print("ROI mask is empty - no pixels selected")
                return None

            roi_quality_scores = quality_map[roi_mask_bool]

            print(f"Extracted {len(roi_quality_scores)} quality scores from ROI ({roi_pixel_count} pixels)")
            return roi_quality_scores

        except Exception as e:
            print(f"Error in _extract_roi_quality_scores: {e}")
            return None

    def analyze_image(self):
        """Enhanced analyze with state management"""
        if self.original_image is None:
            return

        # Check if analysis is allowed
        if not self.state_manager.can_analyze():
            self.status_var.set("Analysis not available in current state")
            return

        if self.state_manager.is_analysis_in_progress():
            self.status_var.set("Analysis already in progress")
            return

        # Update state to analyzing
        self.state_manager.update_state("analyzing")

        # Run analysis in separate thread
        threading.Thread(target=self._analyze_worker, daemon=True).start()

    def _on_analysis_complete(self, analysis_results):
        """Handle analysis completion - simplified version"""
        # Store results
        self.analysis_results = analysis_results

        # Get overall score (same as average quality)
        score = analysis_results.get('overall_score', 0)

        # Update state to analysis_complete and enable buttons
        self.state_manager.update_state("analysis_complete", score=score)

        # Enable quality map and results buttons
        self.quality_map_btn.config(state='normal')
        self.show_results_btn.config(state='normal')  # Enable new results button
        self.save_btn.config(state='normal')

        # Auto-show quality map after a brief delay
        self.root.after(500, self._auto_show_quality_map)

        # Update status
        self.status_var.set(f"Analysis complete - Overall score: {score}/100 - Click 'Show Results' for details")

        self.debug_dynamic_legend_state()

    def _on_analysis_error(self, error_msg):
        """Handle analysis error"""
        messagebox.showerror("Analysis Error", f"Failed to analyze image: {error_msg}")

        # Reset to appropriate state
        if (hasattr(self, 'roi_handler') and
                self.roi_handler.roi_coords and
                len(self.roi_handler.roi_coords) >= 3):
            self.state_manager.update_state("roi_selected")
        else:
            self.state_manager.update_state("image_loaded")

    def _auto_show_quality_map(self):
        """FIXED: Enhanced auto-show with proper dynamic legend creation and debugging"""
        print("DEBUG: _auto_show_quality_map_fixed called")

        if hasattr(self.image_display, 'quality_map_data') and self.image_display.quality_map_data is not None:
            print("DEBUG: Quality map data found, attempting to show")

            # Only auto-show if not already showing
            if not getattr(self.image_display, 'showing_quality_overlay', False):
                print("DEBUG: Quality overlay not currently showing, toggling on")

                # Set the flag first
                self.image_display.showing_quality_overlay = True

                # Change button appearance
                if hasattr(self, 'quality_map_btn'):
                    self.quality_map_btn.config(bg='#e74c3c')  # Red when active

                # Show the quality map with spectrum
                try:
                    self.image_display.show_quality_map_with_spectrum()

                    # FIXED: Enhanced debugging for dynamic legend
                    print(f"Checking for dynamic_legend object...")
                    print(f"hasattr(self, 'dynamic_legend'): {hasattr(self, 'dynamic_legend')}")

                    if hasattr(self, 'dynamic_legend'):
                        print(f"self.dynamic_legend is not None: {self.dynamic_legend is not None}")
                        print(f"self.dynamic_legend type: {type(self.dynamic_legend)}")
                        print(f"self.dynamic_legend object ID: {id(self.dynamic_legend)}")

                    if hasattr(self, 'dynamic_legend') and self.dynamic_legend:
                        current_spectrum = self.selected_spectrum.get()
                        print(f"Creating dynamic legend for spectrum: {current_spectrum}")

                        try:
                            # Create the legend (this also shows it)
                            success = self.dynamic_legend.create_legend(current_spectrum)
                            if success:
                                print("Dynamic legend created and shown successfully")
                            else:
                                print("Failed to create dynamic legend - create_legend returned False")
                        except Exception as legend_error:
                            print(f"Exception while creating dynamic legend: {legend_error}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print("WARNING: No dynamic_legend object available")
                        print("Available attributes:", [attr for attr in dir(self) if 'legend' in attr.lower()])

                    print("DEBUG: Quality map display completed")

                except Exception as e:
                    print(f"DEBUG: Error auto-showing quality map: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("DEBUG: Quality overlay already showing")
        else:
            print("DEBUG: No quality map data available for auto-show")

    def debug_dynamic_legend_state(self):
        """Debug method to check dynamic legend object state"""
        print("=== DYNAMIC LEGEND DEBUG ===")
        print(f"hasattr(self, 'dynamic_legend'): {hasattr(self, 'dynamic_legend')}")

        if hasattr(self, 'dynamic_legend'):
            print(f"self.dynamic_legend: {self.dynamic_legend}")
            print(f"self.dynamic_legend type: {type(self.dynamic_legend)}")
            print(f"self.dynamic_legend object ID: {id(self.dynamic_legend)}")

            if self.dynamic_legend:
                try:
                    print(f"Legend container exists: {self.dynamic_legend.legend_frame}")
                    print(f"Current spectrum: {self.dynamic_legend.current_spectrum}")
                    print(f"Is visible: {self.dynamic_legend.is_visible()}")
                except Exception as e:
                    print(f"Error accessing dynamic_legend properties: {e}")

        print(f"hasattr(self, 'legend_container'): {hasattr(self, 'legend_container')}")
        if hasattr(self, 'legend_container'):
            print(f"legend_container: {self.legend_container}")

        print("=== END DEBUG ===")

    def _calculate_dic_parameters(self, results):
        """Calculate recommended DIC parameters based on existing analysis results"""

        # Use the optimal subset size that was calculated during analysis
        if hasattr(self, 'optimal_subset_size'):
            facet_size = self.optimal_subset_size
        else:
            # Fallback: calculate it now if somehow missing
            if hasattr(self, 'original_image') and self.original_image is not None:
                gray = self.original_image
                if len(gray.shape) == 3:
                    import cv2
                    gray = cv2.cvtColor(gray, cv2.COLOR_RGB2GRAY)
                facet_size = determine_optimal_subset_size(gray)
            else:
                facet_size = 21  # Final fallback

        # Calculate step size for standard DIC overlap (75%)
        overlap_percent = 75
        step_size = max(1, int(facet_size * (1 - overlap_percent / 100)))

        # Determine expected accuracy based on pattern quality (more realistic thresholds)
        score = results.get('overall_score', 0)
        if score >= 70:
            accuracy = "±0.01 pixels"
        elif score >= 50:
            accuracy = "±0.02 pixels"
        elif score >= 30:
            accuracy = "±0.05 pixels"
        elif score >= 15:
            accuracy = "±0.1 pixels"
        else:
            accuracy = "±0.2 pixels"

        return {
            'facet_size': facet_size,
            'step_size': step_size,
            'overlap': overlap_percent,
            'accuracy': accuracy
        }

    def _calculate_roi_area(self):
        """Calculate the area of the current ROI polygon"""
        if not hasattr(self, 'roi_handler') or not self.roi_handler.roi_coords:
            return 0

        # Use shoelace formula for polygon area
        coords = self.roi_handler.roi_coords
        if len(coords) < 3:
            return 0

        area = 0.5 * abs(sum(x0 * y1 - x1 * y0 for ((x0, y0), (x1, y1)) in zip(coords, coords[1:] + [coords[0]])))
        return area

    def get_quality_assessment_text(self, score):
        """
        UPDATED: Quality thresholds that adapt to selected spectrum

        For custom_dic (strict DIC-only): Only excellent+ patterns are acceptable
        For other spectrums: Use the original realistic thresholds

        Args:
            score: Quality score from 0.0 to 1.0

        Returns:
            tuple: (description_text, color_hex)
        """
        # Check if we're using the strict DIC-only spectrum
        current_spectrum = self.selected_spectrum.get() if hasattr(self, 'selected_spectrum') else 'custom_dic'

        # Convert 0-1 score to percentage for thresholds
        score_percent = score * 100

        if current_spectrum == 'custom_dic':
            # STRICT DIC-ONLY THRESHOLDS with Black→Red→Blue color scheme
            if score_percent >= 95:
                return "Perfect for DIC", "#008cff"  # Blue
            elif score_percent >= 90:
                return "Excellent for DIC", "#78ffb4"  # Cyan
            elif score_percent >= 85:
                return "Very Good for DIC", "#ffc800"  # Yellow
            elif score_percent >= 80:
                return "Good for DIC", "#ff5000"  # Orange
            elif score_percent >= 75:
                return "Minimum for DIC", "#780000"  # Red
            else:
                return "CRITICAL - Not suitable for DIC", "#000000"  # Black
        elif current_spectrum in ['zeiss_style_dic', 'ultra_strict_dic', 'focus_aware_dic']:
            # REALISTIC THRESHOLDS for essential DIC spectrums
            if score_percent >= 75:
                return "Excellent for DIC", "#27ae60"  # Green
            elif score_percent >= 60:
                return "Very Good for DIC", "#2ecc71"  # Light Green
            elif score_percent >= 45:
                return "Good for DIC", "#f39c12"  # Orange
            elif score_percent >= 30:
                return "Acceptable for DIC", "#e67e22"  # Dark Orange
            elif score_percent >= 15:
                return "Challenging for DIC", "#e74c3c"  # Red
            else:
                return "Poor for DIC", "#8e44ad"  # Purple
        else:
            # Fallback to custom_dic thresholds
            if score_percent >= 95:
                return "Perfect for DIC", "#008cff"
            elif score_percent >= 90:
                return "Excellent for DIC", "#78ffb4"
            elif score_percent >= 85:
                return "Very Good for DIC", "#ffc800"
            elif score_percent >= 80:
                return "Good for DIC", "#ff5000"
            elif score_percent >= 75:
                return "Minimum for DIC", "#780000"
            else:
                return "CRITICAL - Not suitable for DIC", "#000000"

    def _generate_recommendations(self, score):
        """
        UPDATED: Generate recommendations that adapt to selected spectrum

        Args:
            score: Overall quality score (0-100)
        """
        # Check if we're using the strict DIC-only spectrum
        current_spectrum = self.selected_spectrum.get() if hasattr(self, 'selected_spectrum') else 'custom_dic'

        recommendations = []

        if current_spectrum == 'custom_dic':
            # STRICT DIC-ONLY RECOMMENDATIONS
            if score >= 95:
                recommendations.append("🔵 PERFECT pattern! Ideal for high-precision DIC analysis.")
                recommendations.append("Use finest correlation parameters for maximum accuracy.")
                recommendations.append("Consider this as a reference pattern for other setups.")
                recommendations.append("Expected accuracy: ±0.001-0.005 pixels")

            elif score >= 90:
                recommendations.append("🔷 EXCELLENT pattern quality for precision DIC work.")
                recommendations.append("Use standard DIC parameters with confidence.")
                recommendations.append("Expect sub-pixel accuracy in correlation results.")
                recommendations.append("Expected accuracy: ±0.005-0.01 pixels")

            elif score >= 85:
                recommendations.append("🟡 VERY GOOD pattern for DIC analysis.")
                recommendations.append("Use recommended DIC parameters - good correlation expected.")
                recommendations.append("Suitable for most strain measurement applications.")
                recommendations.append("Expected accuracy: ±0.01-0.02 pixels")

            elif score >= 80:
                recommendations.append("🟠 GOOD pattern quality for DIC applications.")
                recommendations.append("Acceptable correlation reliability with standard parameters.")
                recommendations.append("Monitor correlation quality during analysis.")
                recommendations.append("Expected accuracy: ±0.02-0.03 pixels")

            elif score >= 75:
                recommendations.append("🔴 MINIMUM pattern - threshold for DIC analysis.")
                recommendations.append("Use larger subset sizes (increase by 30-50%) for better correlation.")
                recommendations.append("Monitor correlation quality very closely during analysis.")
                recommendations.append("Strong recommendation to improve pattern if possible.")
                recommendations.append("Expected accuracy: ±0.03-0.05 pixels")

            else:
                recommendations.append("⚫ CRITICAL: Pattern NOT suitable for DIC analysis.")
                recommendations.append("🚨 MANDATORY recommendation to reapply or enhance speckle pattern.")
                recommendations.append("Current pattern will result in correlation failure and unreliable results.")
                recommendations.append("Consider alternative measurement techniques.")
                recommendations.append("❌ Do not proceed with DIC analysis using this pattern.")

        elif current_spectrum in ['zeiss_style_dic', 'ultra_strict_dic', 'focus_aware_dic']:
            # REALISTIC RECOMMENDATIONS for essential DIC spectrums
            if score >= 75:
                recommendations.append("Excellent pattern! Proceed with DIC analysis using recommended parameters.")
                recommendations.append("Consider using sub-pixel interpolation for maximum accuracy.")
                recommendations.append("Pattern has optimal gradient content and speckle morphology.")
            elif score >= 60:
                recommendations.append("Very good pattern quality. DIC analysis should work excellently.")
                recommendations.append("Use standard DIC parameters with confidence.")
                recommendations.append("Monitor correlation quality during analysis for best results.")
            elif score >= 45:
                recommendations.append("Good pattern for DIC analysis with proper setup.")
                recommendations.append("Use recommended subset sizes and overlap settings.")
                recommendations.append("Consider slightly larger subset sizes if correlation issues occur.")
            elif score >= 30:
                recommendations.append("Acceptable pattern for DIC analysis with careful setup.")
                recommendations.append("Use larger subset sizes (increase by 20-30%) for better correlation.")
                recommendations.append("Monitor correlation quality closely during analysis.")
                recommendations.append("Consider post-processing filtering if needed.")
            elif score >= 15:
                recommendations.append("Challenging but workable pattern for DIC analysis.")
                recommendations.append("Use larger subset sizes and stricter correlation criteria.")
                recommendations.append("Expect some areas to have poor correlation - filter results carefully.")
                recommendations.append("Consider pattern enhancement if critical accuracy is needed.")
            else:
                recommendations.append("Poor pattern quality - DIC will have significant limitations.")
                recommendations.append("Strong recommendation to improve or reapply speckle pattern.")
                recommendations.append("If proceeding: use maximum subset sizes and very strict filtering.")
                recommendations.append("Consider alternative measurement techniques if high accuracy needed.")
        else:
            # Fallback to custom_dic recommendations
            recommendations.extend(self._generate_recommendations_for_custom_dic(score))

        # Add spectrum-specific note
        if current_spectrum == 'custom_dic':
            recommendations.append("📊 Note: Using strict DIC-only quality assessment.")
            recommendations.append("Only patterns rated 75%+ are considered suitable for DIC work.")
        elif current_spectrum in ['zeiss_style_dic', 'ultra_strict_dic', 'focus_aware_dic']:
            spectrum_name = current_spectrum.replace('_', ' ').title()
            recommendations.append(f"📊 Note: Using {spectrum_name} spectrum assessment.")
            recommendations.append("Professional DIC quality evaluation with appropriate thresholds.")
        else:
            recommendations.append("📊 Note: Using standard DIC quality assessment.")

        return recommendations

    def _generate_recommendations_for_custom_dic(self, score):
        """Generate recommendations specifically for custom_dic spectrum"""
        recommendations = []
        if score >= 95:
            recommendations.append("🔵 PERFECT pattern! Ideal for high-precision DIC analysis.")
            recommendations.append("Use finest correlation parameters for maximum accuracy.")
        elif score >= 90:
            recommendations.append("🔷 EXCELLENT pattern quality for precision DIC work.")
            recommendations.append("Use standard DIC parameters with confidence.")
        elif score >= 85:
            recommendations.append("🟡 VERY GOOD pattern for DIC analysis.")
            recommendations.append("Use recommended DIC parameters - good correlation expected.")
        elif score >= 80:
            recommendations.append("🟠 GOOD pattern quality for DIC applications.")
            recommendations.append("Acceptable correlation reliability with standard parameters.")
        elif score >= 75:
            recommendations.append("🔴 MINIMUM pattern - threshold for DIC analysis.")
            recommendations.append("Use larger subset sizes for better correlation.")
        else:
            recommendations.append("⚫ CRITICAL: Pattern NOT suitable for DIC analysis.")
            recommendations.append("🚨 MANDATORY recommendation to reapply or enhance speckle pattern.")
        return recommendations

    def on_spectrum_changed(self, event=None):
        """Updated spectrum change handler with ZEISS parameters visibility"""

        spectrum_type = self.selected_spectrum.get()
        print(f"Spectrum changed to: {spectrum_type}")

        # Show/hide ZEISS parameters based on selection
        if hasattr(self, 'zeiss_frame'):
            if spectrum_type == 'zeiss_style_dic':
                self.zeiss_frame.pack(after=self.spectrum_combo.master, pady=2, fill='x')
                print("Showing ZEISS parameters")
            else:
                self.zeiss_frame.pack_forget()
                print("Hiding ZEISS parameters")

        # Rest of your existing spectrum change code...
        if hasattr(self, 'dynamic_legend') and self.dynamic_legend:
            if (hasattr(self.image_display, 'showing_quality_overlay') and
                    self.image_display.showing_quality_overlay):
                success = self.dynamic_legend.update_legend(spectrum_type)
                if success:
                    print(f"Dynamic legend updated to {spectrum_type}")

        # Update quality map visualization if currently shown
        if (hasattr(self.image_display, 'quality_map_data') and
                self.image_display.quality_map_data is not None and
                hasattr(self.image_display, 'showing_quality_overlay') and
                self.image_display.showing_quality_overlay):
            self.update_quality_map_with_spectrum()
            display_name = spectrum_type.replace('_', ' ').title()
            self.status_var.set(f"Updated quality map with {display_name} spectrum")

    def update_quality_map_with_spectrum(self):
        """Update quality map visualization with selected spectrum"""
        if not hasattr(self.image_display, 'quality_map_data') or self.image_display.quality_map_data is None:
            print("No quality map data available")
            return

        # Store current view state to maintain positioning
        current_zoom = self.image_display.zoom_level
        visible_x = self.image_display.canvas.xview()
        visible_y = self.image_display.canvas.yview()

        # Get selected spectrum type
        spectrum_type = self.selected_spectrum.get()
        print(f"Updating quality map with spectrum: {spectrum_type}")

        # Generate new visualization with selected spectrum
        try:
            from analysis.utils.image_processing import create_quality_map_visualization

            roi_coords = self.roi_handler.roi_coords if hasattr(self, 'roi_handler') else None

            visualization = create_quality_map_visualization(
                self.original_image.copy(),
                self.image_display.quality_map_data,
                roi_coords,
                display_scale=1.0,
                spectrum_type=spectrum_type
            )

            # Convert to PIL and display
            from PIL import Image
            visualization_pil = Image.fromarray(visualization)

            # Set flag to prevent recursion during display
            self.image_display._updating_quality_map = True

            # Display with preserved view
            self.image_display.display_image(visualization_pil, preserve_view=True)

            # Clear the flag
            self.image_display._updating_quality_map = False

            # Restore exact view state
            self.image_display.zoom_level = current_zoom
            if visible_x and visible_y:
                self.image_display.canvas.xview_moveto(visible_x[0])
                self.image_display.canvas.yview_moveto(visible_y[0])

            # Update state
            self.image_display.showing_quality_overlay = True

            print(f"Successfully updated quality map with {spectrum_type} spectrum")

        except Exception as e:
            print(f"Error updating quality map with spectrum: {e}")
            import traceback
            traceback.print_exc()

    def full_reset(self):
        """Complete application reset - everything back to initial state"""
        print("Performing full application reset...")

        # 1. CLEAR ALL DATA
        self.original_image = None
        self.current_image = None
        self.analysis_results = {}
        self.roi_coords = None
        self.roi_selection_mode = False
        self.roi_start = None
        self.roi_rect = None

        # 2. RESET IMAGE DISPLAY
        if hasattr(self, 'image_display'):
            # Clear quality map data
            self.image_display.quality_map_data = None
            self.image_display.quality_visualization = None
            self.image_display.showing_quality_overlay = False

            # Reset zoom and view
            self.image_display.zoom_level = 1.0
            self.image_display.displayed_image = None
            self.image_display.photo = None
            self.image_display.image_item = None

            # Clear canvas
            self.image_canvas.delete('all')
            self.image_canvas.configure(scrollregion=(0, 0, 0, 0))
            self.image_canvas.xview_moveto(0)
            self.image_canvas.yview_moveto(0)
            self.image_canvas.config(cursor="")

        # 3. RESET ROI HANDLER
        if hasattr(self, 'roi_handler'):
            self.roi_handler.roi_coords = []
            self.roi_handler.roi_polygon = None
            self.roi_handler.preview_line = None
            self.roi_handler.roi_selection_mode = False
            self.roi_handler.clear_roi()  # This will also update the info display

        # 4. RESET BUTTON STATES
        # Load and screenshot buttons should be enabled
        self.load_btn.config(state='normal', bg='#3498db')
        self.screenshot_btn.config(state='normal', bg='#e67e22')

        # All analysis buttons should be disabled
        self.roi_btn.config(state='disabled', bg='#9b59b6')
        self.analyze_btn.config(state='disabled', bg='#27ae60', text="🔬 Analyze")
        self.quality_map_btn.config(state='disabled', bg='#2ecc71')
        self.show_results_btn.config(state='disabled', bg='#8e44ad')  # Disable results button
        self.save_btn.config(state='disabled', bg='#7f8c8d')

        # 5. Reset dynamic legend
        if hasattr(self, 'dynamic_legend') and self.dynamic_legend:
            self.dynamic_legend.destroy_legend()

        # 6. RESET STATE MANAGER
        if hasattr(self, 'state_manager'):
            self.state_manager.current_state = "no_image"
            self.state_manager.analysis_in_progress = False
            self.state_manager.update_state("no_image")

        # 7. RESET STATUS
        self.status_var.set("Application reset - Load an image to begin")

        # 8. FORCE UI UPDATE
        self.root.update_idletasks()

        print("Full reset complete - ready for new analysis")

    def show_help(self):
        """Show comprehensive help for the application"""
        help_text = """
    DIC Image Quality Inspector - Help Guide

    • Getting Started:
      - Load an image using "Load Image" or capture with "Screen Capture"
      - Images can be in PNG, JPEG, TIFF, or BMP formats

    • Region of Interest (ROI):
      - Click "Select ROI" to enable ROI selection mode
      - Click and drag on the image to select your analysis region
      - Right-click to complete the polygon selection

    • Image Navigation:
      - Zoom: Use the mouse wheel to zoom in/out
      - Pan: Hold Ctrl + click and drag to move around
      - Reset View: Click "Reset Display" to return to original view

    • Image Processing:
      - Original: Return to the unprocessed image
      - Edges: Display edge detection visualization
      - Gradient: Display gradient magnitude visualization
      - Quality Map: Toggle overlay showing DIC quality analysis

    • Analysis:
      - Click "Analyze" to process the image quality metrics
      - Click "Show Results" to view detailed analysis in a popup window
      - Results include technical data and non-technical explanations
      - Quality map shows color-coded analysis across the image

    • Color Spectrums:
      - Choose different color schemes for quality visualization
      - Custom DIC: Strict assessment for DIC applications only
      - ZEISS Style: Professional pattern quality assessment
      - Other options: Various visualization preferences

    • Report:
      - Save a detailed analysis report using "Save Report"
      - Reports include technical metrics and recommendations

    • Troubleshooting:
      - If ROI selection appears off, try resetting the view first
      - For best results, ensure proper lighting in original images
      - Large images may take longer to process
        """

        # Create a custom dialog with scrollable text
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("DIC Image Quality Inspector - Help")
        help_dialog.geometry("600x500")
        help_dialog.transient(self.root)
        help_dialog.grab_set()

        # Add scrollable text area
        text_frame = tk.Frame(help_dialog)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(text_frame, wrap="word", bg="#f0f0f0",
                              font=("Arial", 11), padx=10, pady=10)
        text_widget.pack(side="left", fill="both", expand=True)

        # Connect scrollbar to text widget
        scrollbar.config(command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)

        # Insert help text
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")  # Make read-only

        # Close button
        close_button = tk.Button(help_dialog, text="Close",
                                 bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                                 command=help_dialog.destroy, padx=20, pady=5)
        close_button.pack(pady=10)

    def _reset_application_data(self):
        """Reset application data when loading new images"""
        print("Resetting application data for new image load...")

        # Clear analysis results
        self.analysis_results = {}

        # Clear quality map data
        if hasattr(self, 'image_display'):
            self.image_display.quality_map_data = None
            self.image_display.quality_visualization = None
            self.image_display.showing_quality_overlay = False

        # Disable results and quality map buttons
        self.quality_map_btn.config(state='disabled', bg='#2ecc71')
        self.show_results_btn.config(state='disabled', bg='#8e44ad')
        self.save_btn.config(state='disabled', bg='#7f8c8d')

        # Hide dynamic legend
        if hasattr(self, 'dynamic_legend') and self.dynamic_legend:
            self.dynamic_legend.hide_legend()

        print("Application data reset completed")