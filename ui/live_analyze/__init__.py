# ui/live_analyze/__init__.py - Live Analysis Module

"""
Live Analysis Module for DIC Image Quality Inspector

This module provides real-time analysis capabilities with the critical requirement
that screen darkening/overlays must NEVER affect the image analysis results.

Key Components:
- LiveAnalyzeMode: Main controller for live analysis
- TransparentROISelector: ROI selection with transparent overlay
- QualityOverlay: Real-time quality visualization
- StatsWindow: Statistics and control interface

Critical Order of Operations:
1. FIRST: Capture original screen without any overlays
2. THEN: Show transparent overlay for ROI selection  
3. ANALYSIS: Always use fresh captures, hiding overlays before each capture
"""

from .live_analyze_mode import LiveAnalyzeMode
from .transparent_roi_selector import TransparentROISelector
from .quality_overlay import QualityOverlay
from .stats_window import StatsWindow
from .live_results_window import LiveResultsWindow

__all__ = [
    'LiveAnalyzeMode',
    'TransparentROISelector', 
    'QualityOverlay',
    'StatsWindow',
    'LiveResultsWindow'
]