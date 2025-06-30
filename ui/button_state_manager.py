# ui/button_state_manager.py - UPDATED: Handle new Show Results button

class ButtonStateManager:
    """Manages button states and operation flow for DIC Quality Inspector"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.current_state = "no_image"  # Tracks current application state
        self.analysis_in_progress = False

    def update_state(self, new_state, **kwargs):
        """Update application state and manage button availability

        States:
        - no_image: No image loaded
        - image_loaded: Image loaded but no ROI
        - roi_selected: ROI has been selected
        - analyzing: Analysis in progress
        - analysis_complete: Analysis finished, quality map available
        """
        print(f"State transition: {self.current_state} -> {new_state}")
        self.current_state = new_state

        # Disable all buttons first
        self._disable_all_buttons()

        # Enable buttons based on current state
        if new_state == "no_image":
            self._handle_no_image_state()
        elif new_state == "image_loaded":
            self._handle_image_loaded_state()
        elif new_state == "roi_selected":
            self._handle_roi_selected_state()
        elif new_state == "analyzing":
            self._handle_analyzing_state()
        elif new_state == "analysis_complete":
            self._handle_analysis_complete_state()

        # Update status message
        self._update_status_message(new_state, **kwargs)

    def _disable_all_buttons(self):
        """Disable all operation buttons"""
        buttons = [
            'roi_btn', 'analyze_btn', 'quality_map_btn',
            'show_results_btn', 'save_btn'  # Added new button
        ]
        for btn_name in buttons:
            if hasattr(self.main_window, btn_name):
                getattr(self.main_window, btn_name).config(state='disabled')

    def _handle_no_image_state(self):
        """Handle state when no image is loaded"""
        # Only load and screenshot buttons should be available
        self.main_window.load_btn.config(state='normal')
        self.main_window.screenshot_btn.config(state='normal')

        # Reset button appearances
        if hasattr(self.main_window, 'quality_map_btn'):
            self.main_window.quality_map_btn.config(bg='#2ecc71')  # Green when inactive
        if hasattr(self.main_window, 'show_results_btn'):
            self.main_window.show_results_btn.config(bg='#8e44ad')  # Purple when inactive

    def _handle_image_loaded_state(self):
        """Handle state when image is loaded but no ROI selected"""
        # Enable basic buttons
        self.main_window.load_btn.config(state='normal')
        self.main_window.screenshot_btn.config(state='normal')
        self.main_window.roi_btn.config(state='normal')

        # Can analyze full image if desired
        self.main_window.analyze_btn.config(state='normal')

        # Reset ROI button appearance
        self.main_window.roi_btn.config(bg='#9b59b6')  # Purple when ready

    def _handle_roi_selected_state(self):
        """Handle state when ROI has been selected"""
        # Enable all relevant buttons except results/quality map (need analysis first)
        self.main_window.load_btn.config(state='normal')
        self.main_window.screenshot_btn.config(state='normal')
        self.main_window.roi_btn.config(state='normal')
        self.main_window.analyze_btn.config(state='normal')

        # Reset button appearances
        self.main_window.roi_btn.config(bg='#9b59b6')  # Purple when ready

    def _handle_analyzing_state(self):
        """Handle state when analysis is in progress"""
        self.analysis_in_progress = True

        # Only allow loading new image/screenshot to cancel current operation
        self.main_window.load_btn.config(state='normal')
        self.main_window.screenshot_btn.config(state='normal')

        # Change analyze button to show it's working
        self.main_window.analyze_btn.config(state='disabled', text="🔬 Analyzing...")

    def _handle_analysis_complete_state(self):
        """Handle state when analysis is complete"""
        self.analysis_in_progress = False

        # Enable all buttons
        self.main_window.load_btn.config(state='normal')
        self.main_window.screenshot_btn.config(state='normal')
        self.main_window.roi_btn.config(state='normal')
        self.main_window.analyze_btn.config(state='normal', text="🔬 Analyze")
        self.main_window.quality_map_btn.config(state='normal')
        self.main_window.show_results_btn.config(state='normal')  # Enable results button
        self.main_window.save_btn.config(state='normal')

    def _update_status_message(self, state, **kwargs):
        """Update status message based on current state"""
        messages = {
            "no_image": "Ready - Load an image to begin analysis",
            "image_loaded": "Image loaded - Select ROI for targeted analysis or analyze full image",
            "roi_selected": "ROI selected - Ready for analysis",
            "analyzing": "Analysis in progress - Please wait...",
            "analysis_complete": f"Analysis complete - Overall score: {kwargs.get('score', 'N/A')}/100 - Click 'Show Results' for details"
        }

        if state in messages:
            self.main_window.status_var.set(messages[state])

    def is_analysis_in_progress(self):
        """Check if analysis is currently running"""
        return self.analysis_in_progress

    def can_select_roi(self):
        """Check if ROI selection is allowed in current state"""
        return self.current_state in ["image_loaded", "roi_selected", "analysis_complete"]

    def can_analyze(self):
        """Check if analysis is allowed in current state"""
        return self.current_state in ["image_loaded", "roi_selected", "analysis_complete"]