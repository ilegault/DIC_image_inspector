# ui/live_analyze/stats_window.py - Statistics Window for Live Analysis

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from typing import List, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


class StatsWindow:
    """
    Statistics window for live analysis mode.
    
    Displays real-time statistics, history graphs, and control buttons.
    Can be hidden during screen captures to ensure clean analysis data.
    """
    
    def __init__(self, parent_window, live_analyze_mode):
        """
        Initialize the statistics window.
        
        Args:
            parent_window: Parent tkinter window
            live_analyze_mode: Reference to the LiveAnalyzeMode instance
        """
        self.parent = parent_window
        self.live_analyze_mode = live_analyze_mode
        
        # Create window
        self.window = tk.Toplevel(parent_window)
        self.window.title("Live Analysis Statistics")
        self.window.geometry("600x500")
        self.window.attributes('-topmost', True)
        
        # Make window resizable
        self.window.resizable(True, True)
        
        # Configure grid weights
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Create UI components
        self._create_control_panel()
        self._create_stats_display()
        self._create_graph_display()
        
        # Data for plotting
        self.timestamps = []
        self.scores = []
        self.max_history_points = 50
        
        # Update timer
        self.update_timer_id = None
        self.graph_update_interval = 2000  # Update graph every 2 seconds
        
        # Start graph updates
        self._schedule_graph_update()
        
        # Window close handler
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        logger.info("StatsWindow initialized")
    
    def _create_control_panel(self):
        """Create the control panel with buttons and settings."""
        control_frame = ttk.Frame(self.window)
        control_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side='left', fill='x', expand=True)
        
        self.pause_button = ttk.Button(
            button_frame, 
            text="Pause", 
            command=self._toggle_pause
        )
        self.pause_button.pack(side='left', padx=2)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="Stop", 
            command=self._stop_analysis
        )
        self.stop_button.pack(side='left', padx=2)
        
        self.export_button = ttk.Button(
            button_frame, 
            text="Export", 
            command=self._export_results
        )
        self.export_button.pack(side='left', padx=2)
        
        # Frequency control
        freq_frame = ttk.Frame(control_frame)
        freq_frame.pack(side='right')
        
        ttk.Label(freq_frame, text="Update Frequency:").pack(side='left', padx=2)
        
        self.freq_var = tk.StringVar(value="1.0")
        freq_spinbox = ttk.Spinbox(
            freq_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            width=6,
            textvariable=self.freq_var,
            command=self._update_frequency
        )
        freq_spinbox.pack(side='left', padx=2)
        
        ttk.Label(freq_frame, text="sec").pack(side='left', padx=2)
    
    def _create_stats_display(self):
        """Create the statistics display area."""
        stats_frame = ttk.LabelFrame(self.window, text="Current Statistics")
        stats_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=2)
        
        # Create a frame for stats with grid layout
        inner_frame = ttk.Frame(stats_frame)
        inner_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Current score
        ttk.Label(inner_frame, text="Current Score:").grid(row=0, column=0, sticky='w', padx=2)
        self.current_score_var = tk.StringVar(value="N/A")
        ttk.Label(inner_frame, textvariable=self.current_score_var, font=('Arial', 12, 'bold')).grid(row=0, column=1, sticky='w', padx=10)
        
        # Average score
        ttk.Label(inner_frame, text="Average Score:").grid(row=0, column=2, sticky='w', padx=2)
        self.avg_score_var = tk.StringVar(value="N/A")
        ttk.Label(inner_frame, textvariable=self.avg_score_var).grid(row=0, column=3, sticky='w', padx=10)
        
        # Min/Max scores
        ttk.Label(inner_frame, text="Min Score:").grid(row=1, column=0, sticky='w', padx=2)
        self.min_score_var = tk.StringVar(value="N/A")
        ttk.Label(inner_frame, textvariable=self.min_score_var).grid(row=1, column=1, sticky='w', padx=10)
        
        ttk.Label(inner_frame, text="Max Score:").grid(row=1, column=2, sticky='w', padx=2)
        self.max_score_var = tk.StringVar(value="N/A")
        ttk.Label(inner_frame, textvariable=self.max_score_var).grid(row=1, column=3, sticky='w', padx=10)
        
        # Analysis count and time
        ttk.Label(inner_frame, text="Analyses:").grid(row=2, column=0, sticky='w', padx=2)
        self.analysis_count_var = tk.StringVar(value="0")
        ttk.Label(inner_frame, textvariable=self.analysis_count_var).grid(row=2, column=1, sticky='w', padx=10)
        
        ttk.Label(inner_frame, text="Runtime:").grid(row=2, column=2, sticky='w', padx=2)
        self.runtime_var = tk.StringVar(value="00:00")
        ttk.Label(inner_frame, textvariable=self.runtime_var).grid(row=2, column=3, sticky='w', padx=10)
        
        # ROI info
        ttk.Label(inner_frame, text="ROI Size:").grid(row=3, column=0, sticky='w', padx=2)
        self.roi_size_var = tk.StringVar(value="N/A")
        ttk.Label(inner_frame, textvariable=self.roi_size_var).grid(row=3, column=1, sticky='w', padx=10)
        
        ttk.Label(inner_frame, text="Status:").grid(row=3, column=2, sticky='w', padx=2)
        self.status_var = tk.StringVar(value="Starting...")
        self.status_label = ttk.Label(inner_frame, textvariable=self.status_var, foreground='green')
        self.status_label.grid(row=3, column=3, sticky='w', padx=10)
    
    def _create_graph_display(self):
        """Create the graph display area."""
        graph_frame = ttk.LabelFrame(self.window, text="Quality History")
        graph_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=2)
        
        # Configure graph frame to expand
        self.window.grid_rowconfigure(2, weight=1)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.fig.patch.set_facecolor('white')
        
        # Configure plot
        self.ax.set_xlabel('Time (seconds)')
        self.ax.set_ylabel('Quality Score')
        self.ax.set_title('Real-time Quality Score History')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(0, 1)
        
        # Create empty line plot
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='Quality Score')
        self.ax.legend()
        
        # Embed plot in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
        
        # Start time for relative timestamps
        self.start_time = time.time()
    
    def update_stats(self, score: float, timestamp: float, history: List[Dict[str, Any]]):
        """
        Update the statistics display.
        
        Args:
            score: Current quality score
            timestamp: Current timestamp
            history: List of historical analysis data
        """
        try:
            # Update current score
            self.current_score_var.set(f"{score:.3f}")
            
            # Calculate statistics from history
            if history:
                scores = [item['score'] for item in history]
                self.avg_score_var.set(f"{np.mean(scores):.3f}")
                self.min_score_var.set(f"{np.min(scores):.3f}")
                self.max_score_var.set(f"{np.max(scores):.3f}")
                self.analysis_count_var.set(str(len(history)))
                
                # Get ROI size from latest entry
                if 'roi_size' in history[-1]:
                    roi_size = history[-1]['roi_size']
                    self.roi_size_var.set(f"{roi_size[1]}x{roi_size[0]}")
            
            # Update runtime
            runtime_seconds = int(timestamp - self.start_time)
            minutes = runtime_seconds // 60
            seconds = runtime_seconds % 60
            self.runtime_var.set(f"{minutes:02d}:{seconds:02d}")
            
            # Update status
            if self.live_analyze_mode.is_paused:
                self.status_var.set("Paused")
                self.status_label.configure(foreground='orange')
            elif self.live_analyze_mode.is_active:
                self.status_var.set("Running")
                self.status_label.configure(foreground='green')
            else:
                self.status_var.set("Stopped")
                self.status_label.configure(foreground='red')
            
            # Store data for graph
            relative_time = timestamp - self.start_time
            self.timestamps.append(relative_time)
            self.scores.append(score)
            
            # Limit history for performance
            if len(self.timestamps) > self.max_history_points:
                self.timestamps = self.timestamps[-self.max_history_points:]
                self.scores = self.scores[-self.max_history_points:]
            
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
    
    def _update_graph(self):
        """Update the graph display."""
        try:
            if len(self.timestamps) > 0 and len(self.scores) > 0:
                # Update line data
                self.line.set_data(self.timestamps, self.scores)
                
                # Update axis limits
                if len(self.timestamps) > 1:
                    self.ax.set_xlim(min(self.timestamps), max(self.timestamps))
                
                # Refresh canvas
                self.canvas.draw_idle()
                
        except Exception as e:
            logger.error(f"Error updating graph: {e}")
    
    def _schedule_graph_update(self):
        """Schedule the next graph update."""
        if self.window and self.window.winfo_exists():
            self._update_graph()
            self.update_timer_id = self.window.after(
                self.graph_update_interval, 
                self._schedule_graph_update
            )
    
    def _toggle_pause(self):
        """Toggle pause/resume of the analysis."""
        if self.live_analyze_mode.is_paused:
            self.live_analyze_mode.resume_analysis()
            self.pause_button.configure(text="Pause")
        else:
            self.live_analyze_mode.pause_analysis()
            self.pause_button.configure(text="Resume")

    def _stop_analysis(self):
        """Stop the live analysis."""
        try:
            # Stop analysis first
            if hasattr(self, 'live_analyze_mode') and self.live_analyze_mode:
                self.live_analyze_mode.stop_live_analysis()

            # Then update buttons safely
            try:
                if hasattr(self, 'pause_button') and self.pause_button and self.pause_button.winfo_exists():
                    self.pause_button.configure(text="Pause", state='disabled')
            except (tk.TclError, AttributeError):
                pass  # Button already destroyed or doesn't exist

            try:
                if hasattr(self, 'stop_button') and self.stop_button and self.stop_button.winfo_exists():
                    self.stop_button.configure(state='disabled')
            except (tk.TclError, AttributeError):
                pass  # Button already destroyed or doesn't exist

        except Exception as e:
            logger.error(f"Error in stop analysis: {e}")
    
    def _export_results(self):
        """Export the current results."""
        from tkinter import filedialog
        
        try:
            filepath = filedialog.asksaveasfilename(
                title="Export Live Analysis Results",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if filepath:
                # Remove extension for the export method
                base_filepath = filepath.rsplit('.', 1)[0]
                success = self.live_analyze_mode.export_results(base_filepath)
                
                if success:
                    tk.messagebox.showinfo("Export Successful", 
                                         f"Results exported to:\n{base_filepath}_metadata.json\n{base_filepath}_quality_map.pkl")
                else:
                    tk.messagebox.showerror("Export Failed", "Failed to export results.")
                    
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            tk.messagebox.showerror("Export Error", f"Error exporting results: {e}")
    
    def _update_frequency(self):
        """Update the analysis frequency."""
        try:
            frequency_seconds = float(self.freq_var.get())
            frequency_ms = int(frequency_seconds * 1000)
            self.live_analyze_mode.set_update_frequency(frequency_ms)
        except ValueError:
            logger.warning("Invalid frequency value")
    
    def _on_close(self):
        """Handle window close event."""
        # Don't close the window, just hide it
        self.hide()
    
    def hide(self):
        """Hide the statistics window."""
        if self.window:
            self.window.withdraw()
    
    def show(self):
        """Show the statistics window."""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.attributes('-topmost', True)
    
    def close(self):
        """Close the statistics window."""
        try:
            # Cancel update timer
            if self.update_timer_id:
                self.window.after_cancel(self.update_timer_id)
                self.update_timer_id = None
            
            # Close matplotlib figure
            if hasattr(self, 'fig'):
                plt.close(self.fig)
            
            # Destroy window
            if self.window:
                self.window.destroy()
                self.window = None
                
            logger.info("StatsWindow closed")
            
        except Exception as e:
            logger.error(f"Error closing stats window: {e}")
    
    def save_graph(self, filepath: str) -> bool:
        """
        Save the current graph to file.
        
        Args:
            filepath: Path to save the graph image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"Graph saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save graph: {e}")
            return False