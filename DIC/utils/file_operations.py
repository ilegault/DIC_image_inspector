"""
File I/O operations for image loading, report saving, and data export.

Provides centralized file operations including image loading with validation,
report generation and export, quality map data export in various formats,
and backup management with proper error handling.

Usage:
    file_mgr = FileOperationsManager()
    image = file_mgr.load_image_from_file('path/to/image.png')
    file_mgr.save_report_to_file(report_content, 'report.txt')
"""

import os
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging
from PIL import Image
import numpy as np

from DIC.utils.constants import (
    FILE_OPERATIONS, DEFAULT_FILENAMES, SUPPORTED_IMAGE_FORMATS, VALIDATION
)
from DIC.utils.shared_logging import shared_logger

logger = logging.getLogger(__name__)


class FileOperationsManager:
    """
    Handles all file I/O operations for the DIC Image Quality Inspector.

    This class provides a centralized interface for loading images, saving reports,
    exporting data, and managing file operations with proper error handling.
    """

    def __init__(self):
        """Initialize the file operations manager."""
        self.last_directory = shared_logger.get_dic_quality_directory()  # Use shared logging directory
        self.supported_extensions = self._get_supported_extensions()

    def load_image_from_file(self, filepath: Optional[str] = None) -> Optional[np.ndarray]:
        """
        Load an image from file with validation and error handling.

        Args:
            filepath: Path to image file. If None, opens file dialog.

        Returns:
            Image as numpy array in RGB format, or None if failed
        """
        if filepath is None:
            # This would typically be handled by the UI layer
            logger.warning("No filepath provided for image loading")
            return None

        try:
            # Validate file existence
            if not os.path.exists(filepath):
                logger.error(f"Image file does not exist: {filepath}")
                return None

            # Validate file extension
            if not self._is_supported_image(filepath):
                logger.error(f"Unsupported image format: {filepath}")
                return None

            # Load with PIL
            pil_image = Image.open(filepath)

            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Convert to numpy array
            image_array = np.array(pil_image)

            # Validate image dimensions
            if not self._validate_image_dimensions(image_array):
                logger.error(f"Image dimensions out of valid range: {image_array.shape}")
                return None

            # Update last directory
            self.last_directory = os.path.dirname(filepath)

            logger.info(f"Successfully loaded image: {filepath}, shape: {image_array.shape}")
            return image_array

        except Exception as e:
            logger.error(f"Failed to load image from {filepath}: {e}")
            return None

    def save_report_to_file(self, report_content: str, filepath: Optional[str] = None,
                            filename: Optional[str] = None) -> bool:
        """
        Save analysis report to file.

        Args:
            report_content: The report text content
            filepath: Full path to save file. If None, uses filename in last_directory
            filename: Filename to use. If None, uses default name

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine save path
            if filepath is None:
                if filename is None:
                    filename = self._generate_timestamped_filename(
                        DEFAULT_FILENAMES['report'],
                        FILE_OPERATIONS['report_extension']
                    )
                filepath = os.path.join(self.last_directory, filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Save report
            with open(filepath, 'w', encoding=FILE_OPERATIONS['encoding']) as f:
                f.write(report_content)

            logger.info(f"Report saved successfully to: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save report to {filepath}: {e}")
            return False

    def save_image_to_file(self, image_array: np.ndarray, filepath: Optional[str] = None,
                           filename: Optional[str] = None, format: str = 'PNG') -> bool:
        """
        Save image array to file.

        Args:
            image_array: Image as numpy array
            filepath: Full path to save file
            filename: Filename to use if filepath not provided
            format: Image format (PNG, JPEG, TIFF, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine save path
            if filepath is None:
                if filename is None:
                    extension = f".{format.lower()}"
                    filename = self._generate_timestamped_filename(
                        DEFAULT_FILENAMES['quality_map'],
                        extension
                    )
                filepath = os.path.join(self.last_directory, filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Convert numpy array to PIL Image
            if image_array.dtype != np.uint8:
                image_array = np.clip(image_array, 0, 255).astype(np.uint8)

            if len(image_array.shape) == 2:
                pil_image = Image.fromarray(image_array, 'L')
            elif image_array.shape[2] == 3:
                pil_image = Image.fromarray(image_array, 'RGB')
            elif image_array.shape[2] == 4:
                pil_image = Image.fromarray(image_array, 'RGBA')
            else:
                logger.error(f"Unsupported image array shape: {image_array.shape}")
                return False

            # Save image
            pil_image.save(filepath, format=format.upper())

            logger.info(f"Image saved successfully to: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save image to {filepath}: {e}")
            return False

    def save_data_to_csv(self, data: Union[np.ndarray, List[List]],
                         filepath: Optional[str] = None,
                         headers: Optional[List[str]] = None) -> bool:
        """
        Save data to CSV file.

        Args:
            data: Data to save (2D array or list of lists)
            filepath: Path to save file
            headers: Column headers

        Returns:
            True if successful, False otherwise
        """
        try:
            if filepath is None:
                filename = self._generate_timestamped_filename(
                    DEFAULT_FILENAMES['analysis_data'],
                    FILE_OPERATIONS['csv_extension']
                )
                filepath = os.path.join(self.last_directory, filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w', newline='', encoding=FILE_OPERATIONS['encoding']) as csvfile:
                writer = csv.writer(csvfile)

                # Write headers if provided
                if headers:
                    writer.writerow(headers)

                # Write data
                if isinstance(data, np.ndarray):
                    if len(data.shape) == 2:
                        # 2D array - write as quality map data
                        h, w = data.shape
                        for y in range(h):
                            for x in range(w):
                                writer.writerow([x, y, f"{data[y, x]:.6f}", f"{data[y, x] * 100:.2f}"])
                    else:
                        # 1D array - write as single column
                        for value in data.flatten():
                            writer.writerow([f"{value:.6f}"])
                else:
                    # List of lists
                    for row in data:
                        writer.writerow(row)

            logger.info(f"Data saved to CSV: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save data to CSV {filepath}: {e}")
            return False

    def save_analysis_results_to_json(self, results: Dict, filepath: Optional[str] = None) -> bool:
        """
        Save analysis results to JSON file.

        Args:
            results: Analysis results dictionary
            filepath: Path to save file

        Returns:
            True if successful, False otherwise
        """
        try:
            if filepath is None:
                filename = self._generate_timestamped_filename(
                    DEFAULT_FILENAMES['analysis_data'],
                    '.json'
                )
                filepath = os.path.join(self.last_directory, filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Convert numpy arrays to lists for JSON serialization
            json_results = self._convert_for_json(results)

            with open(filepath, 'w', encoding=FILE_OPERATIONS['encoding']) as f:
                json.dump(json_results, f, indent=2, ensure_ascii=False)

            logger.info(f"Analysis results saved to JSON: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save analysis results to JSON {filepath}: {e}")
            return False

    def load_analysis_results_from_json(self, filepath: str) -> Optional[Dict]:
        """
        Load analysis results from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            Analysis results dictionary or None if failed
        """
        try:
            if not os.path.exists(filepath):
                logger.error(f"JSON file does not exist: {filepath}")
                return None

            with open(filepath, 'r', encoding=FILE_OPERATIONS['encoding']) as f:
                results = json.load(f)

            logger.info(f"Analysis results loaded from JSON: {filepath}")
            return results

        except Exception as e:
            logger.error(f"Failed to load analysis results from JSON {filepath}: {e}")
            return None

    def create_backup_file(self, original_filepath: str) -> Optional[str]:
        """
        Create a backup copy of a file.

        Args:
            original_filepath: Path to original file

        Returns:
            Path to backup file or None if failed
        """
        try:
            if not os.path.exists(original_filepath):
                logger.error(f"Original file does not exist: {original_filepath}")
                return None

            # Generate backup filename
            path_obj = Path(original_filepath)
            backup_path = path_obj.parent / f"{path_obj.stem}_backup{path_obj.suffix}"

            # Copy file
            import shutil
            shutil.copy2(original_filepath, backup_path)

            logger.info(f"Backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"Failed to create backup of {original_filepath}: {e}")
            return None

    def get_file_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file.

        Args:
            filepath: Path to file

        Returns:
            Dictionary with file information or None if failed
        """
        try:
            if not os.path.exists(filepath):
                return None

            stat = os.stat(filepath)
            path_obj = Path(filepath)

            return {
                'filename': path_obj.name,
                'stem': path_obj.stem,
                'suffix': path_obj.suffix,
                'size_bytes': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_image': self._is_supported_image(filepath),
                'is_readable': os.access(filepath, os.R_OK),
                'is_writable': os.access(filepath, os.W_OK)
            }

        except Exception as e:
            logger.error(f"Failed to get file info for {filepath}: {e}")
            return None

    def validate_save_path(self, filepath: str) -> bool:
        """
        Validate that a file path is valid for saving.

        Args:
            filepath: Path to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check directory exists or can be created
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except OSError:
                    logger.error(f"Cannot create directory: {directory}")
                    return False

            # Check write permissions
            if os.path.exists(filepath):
                if not os.access(filepath, os.W_OK):
                    logger.error(f"No write permission for file: {filepath}")
                    return False
            else:
                # Check write permission for directory
                parent_dir = os.path.dirname(filepath) or '.'
                if not os.access(parent_dir, os.W_OK):
                    logger.error(f"No write permission for directory: {parent_dir}")
                    return False

            # Check filename length
            filename = os.path.basename(filepath)
            if len(filename) > FILE_OPERATIONS['max_filename_length']:
                logger.error(f"Filename too long: {filename}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating save path {filepath}: {e}")
            return False

    def get_available_space(self, directory: str) -> Optional[int]:
        """
        Get available disk space in bytes for a directory.

        Args:
            directory: Directory path

        Returns:
            Available space in bytes or None if failed
        """
        try:
            import shutil
            return shutil.disk_usage(directory).free
        except Exception as e:
            logger.error(f"Failed to get disk space for {directory}: {e}")
            return None

    def cleanup_temp_files(self, temp_directory: Optional[str] = None) -> bool:
        """
        Clean up temporary files.

        Args:
            temp_directory: Temporary directory to clean. If None, uses system temp.

        Returns:
            True if successful, False otherwise
        """
        try:
            import tempfile
            import shutil

            if temp_directory is None:
                temp_directory = tempfile.gettempdir()

            # Look for our temporary files
            temp_pattern = "dic_inspector_temp_*"

            for temp_file in Path(temp_directory).glob(temp_pattern):
                try:
                    if temp_file.is_file():
                        temp_file.unlink()
                    elif temp_file.is_dir():
                        shutil.rmtree(temp_file)
                    logger.debug(f"Cleaned up temp file: {temp_file}")
                except OSError as e:
                    logger.warning(f"Could not remove temp file {temp_file}: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return False

    def _get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        extensions = []
        for format_name, pattern in SUPPORTED_IMAGE_FORMATS:
            if pattern != "*.*":
                # Extract extensions from pattern like "*.png;*.jpg"
                exts = pattern.split(';')
                for ext in exts:
                    if ext.startswith('*.'):
                        extensions.append(ext[1:].lower())  # Remove '*' and lowercase
        return extensions

    def _is_supported_image(self, filepath: str) -> bool:
        """Check if file has a supported image extension."""
        ext = Path(filepath).suffix.lower()
        return ext in self.supported_extensions

    def _validate_image_dimensions(self, image_array: np.ndarray) -> bool:
        """Validate image dimensions are within acceptable limits."""
        if len(image_array.shape) < 2:
            return False

        height, width = image_array.shape[:2]
        min_w, min_h = VALIDATION['min_image_size']
        max_w, max_h = VALIDATION['max_image_size']

        return (min_w <= width <= max_w) and (min_h <= height <= max_h)

    def _generate_timestamped_filename(self, base_name: str, extension: str) -> str:
        """Generate a filename with timestamp."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}{extension}"

    def _convert_for_json(self, obj: Any) -> Any:
        """Convert object to JSON-serializable format."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_for_json(item) for item in obj]
        else:
            return obj

    def set_last_directory(self, directory: str) -> None:
        """Set the last used directory."""
        if os.path.isdir(directory):
            self.last_directory = directory
        else:
            logger.warning(f"Invalid directory: {directory}")

    def get_last_directory(self) -> str:
        """Get the last used directory."""
        return self.last_directory

    def save_analysis_results_with_shared_logging(self, results_data: Dict, filename: Optional[str] = None) -> Optional[str]:
        """
        Save analysis results using shared logging system.
        
        Args:
            results_data: Analysis results dictionary
            filename: Optional filename, will generate timestamped name if None
            
        Returns:
            Path to saved file or None if failed
        """
        try:
            if filename is None:
                filename = shared_logger.create_timestamped_filename("quality_analysis", "json")
            
            # Convert results to JSON-serializable format
            json_results = self._convert_for_json(results_data)
            
            # Save using shared logging
            filepath = shared_logger.write_text_log('dic_quality', filename, 
                                                   json.dumps(json_results, indent=2, ensure_ascii=False))
            
            logger.info(f"Analysis results saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save analysis results with shared logging: {e}")
            return None

    def save_quality_map_csv_with_shared_logging(self, quality_map: np.ndarray, filename: Optional[str] = None) -> Optional[str]:
        """
        Save quality map data as CSV using shared logging system.
        
        Args:
            quality_map: Quality map data (0-1 range)
            filename: Optional filename, will generate timestamped name if None
            
        Returns:
            Path to saved file or None if failed
        """
        try:
            if filename is None:
                filename = shared_logger.create_timestamped_filename("quality_map_data", "csv")
            
            # Prepare data for CSV
            h, w = quality_map.shape
            data = []
            for y in range(h):
                for x in range(w):
                    quality_01 = quality_map[y, x]
                    quality_percent = quality_01 * 100
                    data.append({
                        'X_Pixel': x,
                        'Y_Pixel': y,
                        'Quality_Score_0_1': f"{quality_01:.6f}",
                        'Quality_Percentage': f"{quality_percent:.2f}"
                    })
            
            # Save using shared logging
            filepath = shared_logger.write_csv_log('dic_quality', filename, data)
            
            logger.info(f"Quality map data saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save quality map CSV with shared logging: {e}")
            return None

    def export_final_report_to_shared_export(self, report_content: str, report_name: str) -> Optional[str]:
        """
        Export final report to shared export directory.
        
        Args:
            report_content: The report text content
            report_name: Name for the report file
            
        Returns:
            Path to exported file or None if failed
        """
        try:
            # Save to shared export directory for cross-app access
            filepath = shared_logger.write_text_log('export', report_name, report_content)
            
            logger.info(f"Report exported to shared directory: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export report to shared directory: {e}")
            return None


class ExportManager:
    """
    Specialized class for handling various export operations.
    """

    def __init__(self, file_manager: FileOperationsManager):
        """Initialize with a file operations manager."""
        self.file_manager = file_manager

    def export_quality_map_visualization(self, original_image: np.ndarray,
                                         quality_map: np.ndarray,
                                         spectrum_type: str,
                                         filepath: Optional[str] = None) -> bool:
        """
        Export quality map visualization as image.

        Args:
            original_image: Original image array
            quality_map: Quality map data
            spectrum_type: Color spectrum type
            filepath: Save path

        Returns:
            True if successful, False otherwise
        """
        try:
            from DIC.analysis.quality_map.colormap import ColormapGenerator

            # Generate colored visualization
            colormap_gen = ColormapGenerator()
            colored_map = colormap_gen.apply_colormap(quality_map, spectrum_type)

            # Blend with original image
            visualization = colormap_gen.apply_overlay_blend(original_image, colored_map)

            # Save visualization
            return self.file_manager.save_image_to_file(visualization, filepath)

        except Exception as e:
            logger.error(f"Failed to export quality map visualization: {e}")
            return False

    def export_quality_data_csv(self, quality_map: np.ndarray,
                                filepath: Optional[str] = None) -> bool:
        """
        Export quality map data as CSV.

        Args:
            quality_map: Quality map data (0-1 range)
            filepath: Save path

        Returns:
            True if successful, False otherwise
        """
        try:
            headers = ['X_Pixel', 'Y_Pixel', 'Quality_Score_0_1', 'Quality_Percentage']

            # Prepare data
            h, w = quality_map.shape
            data = []
            for y in range(h):
                for x in range(w):
                    quality_01 = quality_map[y, x]
                    quality_percent = quality_01 * 100
                    data.append([x, y, f"{quality_01:.6f}", f"{quality_percent:.2f}"])

            return self.file_manager.save_data_to_csv(data, filepath, headers)

        except Exception as e:
            logger.error(f"Failed to export quality data as CSV: {e}")
            return False

    def export_analysis_summary_csv(self, analysis_results: Dict,
                                    filepath: Optional[str] = None) -> bool:
        """
        Export analysis summary as CSV.

        Args:
            analysis_results: Analysis results dictionary
            filepath: Save path

        Returns:
            True if successful, False otherwise
        """
        try:
            headers = ['Metric', 'Value', 'Unit', 'Description']
            data = []

            # Overall score
            data.append([
                'Overall Quality Score',
                f"{analysis_results.get('overall_score', 0):.1f}",
                '%',
                'Combined quality assessment score'
            ])

            # Quality statistics
            stats = analysis_results.get('quality_map_stats', {})
            for key, value in stats.items():
                readable_key = key.replace('_', ' ').title()
                data.append([readable_key, f"{value:.1f}", '%', 'Quality map statistic'])

            # Analysis method
            data.append([
                'Analysis Method',
                analysis_results.get('analysis_method', 'Unknown'),
                '',
                'Type of analysis performed'
            ])

            # Spectrum used
            data.append([
                'Methods',
                analysis_results.get('spectrum_used', 'Unknown'),
                '',
                'Color visualization spectrum used'
            ])

            return self.file_manager.save_data_to_csv(data, filepath, headers)

        except Exception as e:
            logger.error(f"Failed to export analysis summary as CSV: {e}")
            return False

    def export_dic_parameters_csv(self, analysis_results: Dict,
                                  filepath: Optional[str] = None) -> bool:
        """
        Export recommended DIC parameters as CSV.

        Args:
            analysis_results: Analysis results dictionary
            filepath: Save path

        Returns:
            True if successful, False otherwise
        """
        try:
            from DIC.core.report_generator import ReportGenerator

            # Calculate DIC parameters
            report_gen = ReportGenerator()
            dic_params = report_gen._calculate_dic_parameters(analysis_results)

            headers = ['Parameter', 'Value', 'Unit', 'Description']
            data = [
                ['Subset Size (Facet)', str(dic_params['facet_size']), 'pixels',
                 'Recommended correlation window size'],
                ['Step Size', str(dic_params['step_size']), 'pixels',
                 'Recommended spacing between correlation points'],
                ['Overlap Percentage', str(dic_params['overlap']), '%',
                 'Overlap between adjacent subsets'],
                ['Expected Accuracy', dic_params['accuracy'], 'pixels',
                 'Predicted displacement measurement precision']
            ]

            return self.file_manager.save_data_to_csv(data, filepath, headers)

        except Exception as e:
            logger.error(f"Failed to export DIC parameters as CSV: {e}")
            return False


# Utility functions for file operations
def get_file_size_string(size_bytes: int) -> str:
    """Convert file size in bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def is_valid_filename(filename: str) -> bool:
    """Check if filename is valid for the current operating system."""

    # Check for invalid characters (Windows is most restrictive)
    invalid_chars = '<>:"/\\|?*'
    if any(char in filename for char in invalid_chars):
        return False

    # Check for reserved names (Windows)
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]

    base_name = os.path.splitext(filename)[0].upper()
    if base_name in reserved_names:
        return False

    # Check length
    if len(filename) > FILE_OPERATIONS['max_filename_length']:
        return False

    return True


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing or replacing invalid characters."""
    import re

    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')

    # Ensure not empty
    if not sanitized:
        sanitized = "untitled"

    # Truncate if too long
    if len(sanitized) > FILE_OPERATIONS['max_filename_length']:
        name, ext = os.path.splitext(sanitized)
        max_name_length = FILE_OPERATIONS['max_filename_length'] - len(ext)
        sanitized = name[:max_name_length] + ext

    return sanitized