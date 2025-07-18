# ui/live_analyze/live_results_window.py - Live Results Window

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class LiveResultsWindow:
    """
    Live Results Window for displaying analysis results and controls.
    
    This is a simplified version that works with the existing StatsWindow.
    """
    
    def __init__(self, parent, live_analyzer):
        """
        Initialize the live results window.
        
        Args:
            parent: Parent tkinter window
            live_analyzer: Reference to the LiveAnalyzeMode instance
        """
        self.parent = parent
        self.live_analyzer = live_analyzer
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Live Analysis Results")
        self.window.attributes('-topmost', True)
        self.window.geometry("400x500+50+50")
        
        # Frequency selector
        self.create_frequency_selector()
        
        # Quality score display
        self.create_score_display()
        
        # Statistics display
        self.create_statistics_display()
        
        # Control buttons
        self.create_control_buttons()
        
        # Store frequency mapping
        self.freq_mapping = {
            "0.1 seconds": 100,
            "0.5 seconds": 500,
            "1 second": 1000,
            "2 seconds": 2000,
            "5 seconds": 5000,
            "10 seconds": 10000
        }
        
        logger.info("LiveResultsWindow initialized")
    
    def create_frequency_selector(self):
        """Create update frequency dropdown"""
        freq_frame = tk.Frame(self.window)
        freq_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(freq_frame, text="Update Frequency:").pack(side='left')
        
        self.freq_var = tk.StringVar(value="1 second")
        frequencies = [
            "0.1 seconds",
            "0.5 seconds", 
            "1 second",
            "2 seconds",
            "5 seconds",
            "10 seconds"
        ]
        
        freq_menu = tk.OptionMenu(
            freq_frame, 
            self.freq_var,
            *frequencies,
            command=self.on_frequency_change
        )
        freq_menu.pack(side='left', padx=10)
    
    def create_score_display(self):
        """Create quality score display"""
        score_frame = ttk.LabelFrame(self.window, text="Current Quality Score")
        score_frame.pack(fill='x', padx=10, pady=5)
        
        self.score_var = tk.StringVar(value="N/A")
        score_label = tk.Label(
            score_frame, 
            textvariable=self.score_var,
            font=('Arial', 16, 'bold'),
            fg='blue'
        )
        score_label.pack(pady=10)
    
    def create_statistics_display(self):
        """Create statistics display"""
        stats_frame = ttk.LabelFrame(self.window, text="Statistics")
        stats_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create text widget for statistics
        self.stats_text = tk.Text(
            stats_frame,
            height=15,
            width=40,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_control_buttons(self):
        """Create control buttons"""
        button_frame = tk.Frame(self.window)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        self.pause_button = tk.Button(
            button_frame,
            text="Pause",
            command=self.toggle_pause
        )
        self.pause_button.pack(side='left', padx=5)
        
        self.stop_button = tk.Button(
            button_frame,
            text="Stop",
            command=self.stop_analysis
        )
        self.stop_button.pack(side='left', padx=5)
        
        self.export_button = tk.Button(
            button_frame,
            text="Export",
            command=self.export_results
        )
        self.export_button.pack(side='left', padx=5)
    
    def on_frequency_change(self, selected_freq):
        """Handle frequency change"""
        try:
            frequency_ms = self.freq_mapping.get(selected_freq, 1000)
            self.live_analyzer.set_update_frequency(frequency_ms)
        except Exception as e:
            logger.error(f"Error changing frequency: {e}")
    
    def update_score(self, score: float):
        """Update the quality score display"""
        self.score_var.set(f"{score:.3f}")
    
    def update_statistics(self, stats_text: str):
        """Update the statistics display"""
        self.stats_text.configure(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
        self.stats_text.configure(state=tk.DISABLED)
    
    def update_pause_button(self, text: str):
        """Update the pause button text"""
        self.pause_button.configure(text=text)
    
    def toggle_pause(self):
        """Toggle pause state"""
        if hasattr(self.live_analyzer, 'toggle_pause'):
            self.live_analyzer.toggle_pause()
        else:
            # Fallback to individual methods
            if self.live_analyzer.is_paused:
                self.live_analyzer.resume_analysis()
            else:
                self.live_analyzer.pause_analysis()
    
    def stop_analysis(self):
        """Stop the analysis"""
        self.live_analyzer.stop_live_analysis()
        self.pause_button.configure(state='disabled')
        self.stop_button.configure(state='disabled')
    
    def export_results(self):
        """Export the results"""
        try:
            from tkinter import filedialog
            filepath = filedialog.asksaveasfilename(
                title="Export Live Analysis Results",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filepath:
                base_filepath = filepath.rsplit('.', 1)[0]
                success = self.live_analyzer.export_results(base_filepath)
                
                if success:
                    tk.messagebox.showinfo("Export Successful", 
                                         f"Results exported to:\n{base_filepath}_metadata.json\n{base_filepath}_quality_map.pkl")
                else:
                    tk.messagebox.showerror("Export Failed", "Failed to export results.")
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
    
    def close(self):
        """Close the results window"""
        try:
            if self.window:
                self.window.destroy()
                self.window = None
            logger.info("LiveResultsWindow closed")
        except Exception as e:
            logger.error(f"Error closing results window: {e}")
    
    def hide(self):
        """Hide the results window"""
        if self.window:
            self.window.withdraw()
    
    def show(self):
        """Show the results window"""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.attributes('-topmost', True)