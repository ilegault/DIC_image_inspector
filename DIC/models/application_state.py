"""
Application state management with observer pattern.

Centralized state manager for the DIC Image Quality Inspector application.
Maintains image data, ROI selections, analysis results, and UI state with
observer notifications for reactive updates.

Usage:
    state = ApplicationState()
    state.set_image(image_array, filename='test.png')
    state.add_observer('image', callback_function)
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable, List
import numpy as np
import logging
from .analysis_result import AnalysisResult
from .roi_data import ROIData

logger = logging.getLogger(__name__)


@dataclass
class ImageData:
    """Image data container."""
    array: np.ndarray
    filename: Optional[str] = None
    source: str = "unknown"  # "file", "screenshot", etc.

    def __post_init__(self):
        """Validate image data."""
        if not isinstance(self.array, np.ndarray):
            raise TypeError("Image array must be numpy.ndarray")

        if len(self.array.shape) not in [2, 3]:
            raise ValueError("Image must be 2D or 3D array")


class ApplicationState:
    """
    Central application state manager.

    Manages all application state with observer pattern for UI updates.
    Follows single responsibility principle - only state management.
    """

    def __init__(self):
        """Initialize application state."""
        # Core state
        self._image: Optional[ImageData] = None
        self._roi: Optional[ROIData] = None
        self._analysis_result: Optional[AnalysisResult] = None
        self._application_state: str = 'no_image'

        # Analysis state
        self._analysis_in_progress: bool = False
        self._quality_map_visible: bool = False

        # UI state
        self._selected_spectrum: str = 'optimized'
        self._zeiss_parameters: Dict[str, Any] = {
            'facet_size': 19,
            'point_distance': 4
        }

        # Observer pattern for state changes
        self._observers: Dict[str, List[Callable]] = {
            'image': [],
            'roi': [],
            'analysis_result': [],
            'application_state': [],
            'analysis_progress': [],
            'spectrum': [],
            'quality_map_visibility': []
        }

    # Observer pattern methods
    def add_observer(self, state_key: str, callback: Callable):
        """
        Add observer for state changes.

        Args:
            state_key: Key of state to observe
            callback: Function to call when state changes
        """
        if state_key in self._observers:
            self._observers[state_key].append(callback)
        else:
            print(f"WARNING: Unknown state key: {state_key}")

    def remove_observer(self, state_key: str, callback: Callable):
        """
        Remove observer for state changes.

        Args:
            state_key: Key of state being observed
            callback: Function to remove
        """
        if state_key in self._observers and callback in self._observers[state_key]:
            self._observers[state_key].remove(callback)

    def _notify_observers(self, state_key: str, value: Any):
        """
        Notify all observers of state change.

        Args:
            state_key: Key of changed state
            value: New value
        """
        if state_key in self._observers:
            for callback in self._observers[state_key]:
                try:
                    callback(value)
                except Exception as e:
                    print(f"Error in observer callback for {state_key}: {e}")

    # Image state methods
    def set_image(self, image_data: np.ndarray, filename: Optional[str] = None, source: str = "unknown"):
        """
        Set current image.

        Args:
            image_data: Image array
            filename: Optional filename
            source: Source of image (file, screenshot, etc.)
        """
        try:
            self._image = ImageData(image_data, filename, source)
            self._notify_observers('image', self._image)

            # Reset dependent state
            self._roi = None
            self._analysis_result = None
            self._quality_map_visible = False

            # Update application state
            if self._application_state == 'no_image':
                self.set_application_state('image_loaded')

        except Exception as e:
            print(f"Error setting image: {e}")
            self._image = None
            self._notify_observers('image', None)

    def get_image(self) -> Optional[np.ndarray]:
        """Get current image array."""
        return self._image.array if self._image else None

    def get_image_data(self) -> Optional[ImageData]:
        """Get complete image data."""
        return self._image

    def has_image(self) -> bool:
        """Check if image is loaded."""
        return self._image is not None

    def clear_image(self):
        """Clear current image."""
        self._image = None
        self._notify_observers('image', None)

    # ROI state methods
    def set_roi(self, coordinates: List[tuple], roi_type: str = "polygon"):
        """
        Set ROI data.

        Args:
            coordinates: List of (x, y) coordinate tuples
            roi_type: Type of ROI (polygon, rectangle)
        """
        try:
            if coordinates and len(coordinates) >= 3:
                self._roi = ROIData(coordinates, roi_type)
                self._notify_observers('roi', self._roi)
            else:
                self._roi = None
                self._notify_observers('roi', None)

        except Exception as e:
            print(f"Error setting ROI: {e}")
            self._roi = None
            self._notify_observers('roi', None)

    def get_roi(self) -> Optional[ROIData]:
        """Get current ROI data."""
        return self._roi

    def has_roi(self) -> bool:
        """Check if ROI is defined."""
        return self._roi is not None and self._roi.has_valid_coordinates()

    def clear_roi(self):
        """Clear current ROI."""
        self._roi = None
        self._notify_observers('roi', None)

    # Analysis result state methods
    def set_analysis_result(self, result: AnalysisResult):
        """
        Set analysis result.

        Args:
            result: Analysis result object
        """
        try:
            if isinstance(result, AnalysisResult) and result.validate():
                self._analysis_result = result
                self._notify_observers('analysis_result', result)
            else:
                print("Invalid analysis result provided")

        except Exception as e:
            print(f"Error setting analysis result: {e}")

    def get_analysis_result(self) -> Optional[AnalysisResult]:
        """Get current analysis result."""
        return self._analysis_result

    def has_analysis_result(self) -> bool:
        """Check if analysis result is available."""
        return self._analysis_result is not None

    def clear_analysis_result(self):
        """Clear analysis result."""
        self._analysis_result = None
        self._notify_observers('analysis_result', None)

    # Application state methods
    def set_application_state(self, state: str):
        """
        Set application state.

        Args:
            state: New application state
        """
        valid_states = ['no_image', 'image_loaded', 'roi_selected', 'analyzing', 'analysis_complete']

        if state in valid_states:
            old_state = self._application_state
            self._application_state = state
            self._notify_observers('application_state', state)
            logger.debug(f"Application state: {old_state} -> {state}")
        else:
            logger.warning(f"Invalid application state: {state}")

    def get_application_state(self) -> str:
        """Get current application state."""
        return self._application_state

    # Analysis progress methods
    def set_analysis_in_progress(self, in_progress: bool):
        """
        Set analysis progress state.

        Args:
            in_progress: Whether analysis is in progress
        """
        self._analysis_in_progress = in_progress
        self._notify_observers('analysis_progress', in_progress)

        # Update application state
        if in_progress:
            self.set_application_state('analyzing')
        elif self.has_analysis_result():
            self.set_application_state('analysis_complete')

    def is_analysis_in_progress(self) -> bool:
        """Check if analysis is currently in progress."""
        return self._analysis_in_progress

    # UI state methods
    def set_selected_spectrum(self, spectrum: str):
        """
        Set selected color spectrum.

        Args:
            spectrum: Spectrum type
        """
        valid_spectrums = ['optimized', 'controlled']

        if spectrum in valid_spectrums:
            self._selected_spectrum = spectrum
            self._notify_observers('spectrum', spectrum)
        else:
            print(f"Invalid spectrum type: {spectrum}")

    def get_selected_spectrum(self) -> str:
        """Get selected color spectrum."""
        return self._selected_spectrum

    def set_zeiss_parameters(self, facet_size: int, point_distance: int):
        """
        Set ZEISS analysis parameters.

        Args:
            facet_size: Facet size for ZEISS analysis
            point_distance: Point distance for ZEISS analysis
        """
        self._zeiss_parameters = {
            'facet_size': max(11, min(51, facet_size)),
            'point_distance': max(2, min(20, point_distance))
        }

    def get_zeiss_parameters(self) -> Dict[str, int]:
        """Get ZEISS analysis parameters."""
        return self._zeiss_parameters.copy()

    def set_quality_map_visible(self, visible: bool):
        """
        Set quality map visibility state.

        Args:
            visible: Whether quality map is visible
        """
        self._quality_map_visible = visible
        self._notify_observers('quality_map_visibility', visible)

    def is_quality_map_visible(self) -> bool:
        """Check if quality map is currently visible."""
        return self._quality_map_visible

    # Utility methods
    def can_analyze(self) -> bool:
        """Check if analysis can be performed."""
        return (self.has_image() and
                not self.is_analysis_in_progress() and
                self._application_state in ['image_loaded', 'roi_selected', 'analysis_complete'])

    def can_select_roi(self) -> bool:
        """Check if ROI selection is allowed."""
        return (self.has_image() and
                not self.is_analysis_in_progress())

    def can_show_results(self) -> bool:
        """Check if results can be shown."""
        return self.has_analysis_result()

    def can_save_report(self) -> bool:
        """Check if report can be saved."""
        return self.has_analysis_result()

    def get_image_info(self) -> Optional[Dict[str, Any]]:
        """Get image information dictionary."""
        if not self.has_image():
            return None

        image = self.get_image()
        info = {
            'width': image.shape[1] if len(image.shape) > 1 else image.shape[0],
            'height': image.shape[0],
            'channels': image.shape[2] if len(image.shape) == 3 else 1,
            'dtype': str(image.dtype),
            'size_bytes': image.nbytes,
            'total_area': image.shape[0] * (image.shape[1] if len(image.shape) > 1 else 1)
        }

        if self._image.filename:
            info['filename'] = self._image.filename

        info['source'] = self._image.source

        return info

    def get_roi_info(self) -> Optional[Dict[str, Any]]:
        """Get ROI information dictionary."""
        if not self.has_roi():
            return None

        roi_area = self._roi.calculate_area()

        info = {
            'type': self._roi.roi_type,
            'point_count': len(self._roi.coordinates),
            'area': roi_area,
            'coordinates': self._roi.coordinates.copy()
        }

        # Calculate percentage of total image
        if self.has_image():
            image_info = self.get_image_info()
            if image_info:
                total_area = image_info['total_area']
                info['percentage'] = (roi_area / total_area * 100) if total_area > 0 else 0.0

        return info

    def get_analysis_info(self) -> Optional[Dict[str, Any]]:
        """Get analysis information dictionary."""
        if not self.has_analysis_result():
            return None

        result = self._analysis_result
        return {
            'overall_score': result.overall_score,
            'analysis_method': result.analysis_method,
            'spectrum_used': result.spectrum_used,
            'timestamp': result.timestamp,
            'processing_time': result.processing_time,
            'quality_assessment': result.get_quality_assessment(),
            'recommendation_level': result.get_recommendation_level()
        }

    def get_full_state_summary(self) -> Dict[str, Any]:
        """Get complete state summary."""
        summary = {
            'application_state': self._application_state,
            'has_image': self.has_image(),
            'has_roi': self.has_roi(),
            'has_analysis_result': self.has_analysis_result(),
            'analysis_in_progress': self.is_analysis_in_progress(),
            'quality_map_visible': self.is_quality_map_visible(),
            'selected_spectrum': self._selected_spectrum,
            'zeiss_parameters': self._zeiss_parameters.copy()
        }

        # Add detailed info if available
        if self.has_image():
            summary['image_info'] = self.get_image_info()

        if self.has_roi():
            summary['roi_info'] = self.get_roi_info()

        if self.has_analysis_result():
            summary['analysis_info'] = self.get_analysis_info()

        return summary

    def reset(self):
        """Reset all application state completely."""
        print("Resetting application state completely")

        # Clear all state
        self._image = None
        self._roi = None
        self._analysis_result = None
        self._analysis_in_progress = False
        self._quality_map_visible = False

        # Reset UI state to defaults
        self._selected_spectrum = 'optimized'
        self._zeiss_parameters = {
            'facet_size': 19,
            'point_distance': 4
        }

        # Set application state
        self._application_state = 'no_image'

        # Notify all observers
        self._notify_observers('image', None)
        self._notify_observers('roi', None)
        self._notify_observers('analysis_result', None)
        self._notify_observers('application_state', 'no_image')
        self._notify_observers('analysis_progress', False)
        self._notify_observers('quality_map_visibility', False)
        self._notify_observers('spectrum', self._selected_spectrum)

    def reset_display_and_results(self):
        """Reset display and analysis results while keeping the loaded image."""
        print("Resetting display and results (keeping image)")

        if not self.has_image():
            print("No image loaded - performing full reset instead")
            self.reset()
            return

        # Store current image data
        current_image = self._image

        # Clear analysis-related state
        self._roi = None
        self._analysis_result = None
        self._analysis_in_progress = False
        self._quality_map_visible = False

        # Reset UI state to defaults
        self._selected_spectrum = 'optimized'
        self._zeiss_parameters = {
            'facet_size': 19,
            'point_distance': 4
        }

        # Set application state back to image loaded
        self._application_state = 'image_loaded'

        # Notify observers (image stays the same, so we don't notify image observers)
        self._notify_observers('roi', None)
        self._notify_observers('analysis_result', None)
        self._notify_observers('application_state', 'image_loaded')
        self._notify_observers('analysis_progress', False)
        self._notify_observers('quality_map_visibility', False)
        self._notify_observers('spectrum', self._selected_spectrum)

    def validate_state(self) -> bool:
        """
        Validate current application state consistency.

        Returns:
            True if state is consistent, False otherwise
        """
        try:
            # Check state consistency
            if self._application_state == 'no_image' and self.has_image():
                return False

            if self._application_state in ['image_loaded', 'roi_selected', 'analyzing',
                                           'analysis_complete'] and not self.has_image():
                return False

            if self._application_state == 'roi_selected' and not self.has_roi():
                return False

            if self._application_state == 'analysis_complete' and not self.has_analysis_result():
                return False

            # Validate individual main_components
            if self._image and not isinstance(self._image, ImageData):
                return False

            if self._roi and not isinstance(self._roi, ROIData):
                return False

            if self._analysis_result and not isinstance(self._analysis_result, AnalysisResult):
                return False

            return True

        except Exception as e:
            print(f"Error validating state: {e}")
            return False

    def get_state_for_persistence(self) -> Dict[str, Any]:
        """
        Get state data suitable for persistence (excluding large objects).

        Returns:
            Dictionary with persistable state data
        """
        state = {
            'application_state': self._application_state,
            'selected_spectrum': self._selected_spectrum,
            'zeiss_parameters': self._zeiss_parameters.copy(),
            'quality_map_visible': self._quality_map_visible
        }

        # Add metadata without large arrays
        if self.has_image():
            state['has_image'] = True
            state['image_info'] = self.get_image_info()

        if self.has_roi():
            state['has_roi'] = True
            state['roi_info'] = self.get_roi_info()

        if self.has_analysis_result():
            state['has_analysis_result'] = True
            # Include analysis metadata but not the quality map array
            result_dict = self._analysis_result.to_dict()
            result_dict.pop('quality_map', None)  # Remove large array
            state['analysis_result'] = result_dict

        return state

    def __str__(self) -> str:
        """String representation of application state."""
        return (f"ApplicationState(state={self._application_state}, "
                f"image={self.has_image()}, "
                f"roi={self.has_roi()}, "
                f"result={self.has_analysis_result()})")

    def __repr__(self) -> str:
        """Detailed representation of application state."""
        return self.__str__()