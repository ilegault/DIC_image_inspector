"""
Shared Logging Utility for DIC Timing Project
Provides centralized log directory management and file operations
"""

import os
import csv
from pathlib import Path
from datetime import datetime


class SharedLogger:
    """Centralized logging utility for consistent file management across the project"""
    
    def __init__(self, app_name="DICTiming"):
        """
        Initialize shared logger with standardized directory structure
        
        Args:
            app_name: Name of the application subfolder in Documents
        """
        self.app_name = app_name
        self._setup_directories()
    
    def _setup_directories(self):
        """Setup standardized directory structure in Documents"""
        # Use Documents folder as the base
        documents_path = Path.home() / "Documents"
        
        # Create main app directory
        self.base_log_directory = documents_path / self.app_name
        
        # Create subdirectories for different components
        self.camera_log_directory = self.base_log_directory / "Camera_Logs"
        self.session_log_directory = self.base_log_directory / "Session_Logs"
        self.dic_quality_directory = self.base_log_directory / "DIC_Quality_Logs"
        self.export_directory = self.base_log_directory / "Exports"
        
        # Ensure all directories exist
        for directory in [
            self.base_log_directory,
            self.camera_log_directory,
            self.session_log_directory,
            self.dic_quality_directory,
            self.export_directory
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_camera_log_directory(self):
        """Get the camera logs directory path as string"""
        return str(self.camera_log_directory)
    
    def get_forwarder_log_directory(self):
        """Get the forwarder logs directory path as string"""
        return str(self.forwarder_log_directory)
    
    def get_session_log_directory(self):
        """Get the session logs directory path as string"""
        return str(self.session_log_directory)
    
    def get_dic_quality_directory(self):
        """Get the DIC quality logs directory path as string"""
        return str(self.dic_quality_directory)
    
    def get_export_directory(self):
        """Get the exports directory path as string"""
        return str(self.export_directory)
    
    def get_base_directory(self):
        """Get the base log directory path as string"""
        return str(self.base_log_directory)
    
    def create_timestamped_filename(self, prefix, extension, include_microseconds=True):
        """
        Create a timestamped filename
        
        Args:
            prefix: Filename prefix (e.g., 'session', 'forwarder')
            extension: File extension (e.g., 'csv', 'txt')
            include_microseconds: Whether to include microseconds in timestamp
            
        Returns:
            Timestamped filename string
        """
        if include_microseconds:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Remove last 3 digits for milliseconds
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{prefix}_{timestamp}.{extension}"
    
    def get_log_file_path(self, directory_type, filename):
        """
        Get full path for a log file
        
        Args:
            directory_type: 'camera', 'forwarder', 'session', 'dic_quality', or 'export'
            filename: Name of the file
            
        Returns:
            Full file path as string
        """
        directory_map = {
            'camera': self.camera_log_directory,
            'dic_quality': self.dic_quality_directory,
            'export': self.export_directory
        }
        
        if directory_type not in directory_map:
            raise ValueError(f"Unknown directory type: {directory_type}")
        
        return str(directory_map[directory_type] / filename)
    
    def write_csv_log(self, directory_type, filename, data, fieldnames=None):
        """
        Write data to a CSV log file
        
        Args:
            directory_type: 'camera', 'forwarder', 'session', or 'export'
            filename: Name of the CSV file
            data: List of dictionaries to write
            fieldnames: List of field names (auto-detected if None)
        """
        if not data:
            return
        
        if fieldnames is None and data:
            fieldnames = list(data[0].keys())
        
        filepath = self.get_log_file_path(directory_type, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        return filepath
    
    def append_csv_log(self, directory_type, filename, data, fieldnames=None):
        """
        Append data to a CSV log file
        
        Args:
            directory_type: 'camera', 'forwarder', 'session', or 'export'
            filename: Name of the CSV file
            data: Dictionary or list of dictionaries to append
            fieldnames: List of field names (required for new files)
        """
        filepath = self.get_log_file_path(directory_type, filename)
        
        # Convert single dict to list
        if isinstance(data, dict):
            data = [data]
        
        # Check if file exists
        file_exists = os.path.exists(filepath)
        
        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            if fieldnames is None and data:
                fieldnames = list(data[0].keys())
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(data)
        
        return filepath
    
    def write_text_log(self, directory_type, filename, content, mode='w'):
        """
        Write content to a text log file
        
        Args:
            directory_type: 'camera', 'forwarder', 'session', or 'export'
            filename: Name of the text file
            content: String content to write
            mode: File mode ('w' for write, 'a' for append)
        """
        filepath = self.get_log_file_path(directory_type, filename)
        
        with open(filepath, mode, encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def list_log_files(self, directory_type, pattern="*"):
        """
        List log files in a directory
        
        Args:
            directory_type: 'camera', 'forwarder', 'session', 'dic_quality', or 'export'
            pattern: File pattern to match (default: all files)
            
        Returns:
            List of file paths
        """
        directory_map = {
            'camera': self.camera_log_directory,
            'dic_quality': self.dic_quality_directory,
            'export': self.export_directory
        }
        
        if directory_type not in directory_map:
            raise ValueError(f"Unknown directory type: {directory_type}")
        
        directory = directory_map[directory_type]
        return list(directory.glob(pattern))
    
    def get_directory_info(self):
        """Get information about all log directories"""
        info = {
            'base_directory': str(self.base_log_directory),
            'camera_logs': str(self.camera_log_directory),
            'dic_quality_logs': str(self.dic_quality_directory),
            'exports': str(self.export_directory)
        }
        return info


# Create a global instance for easy import
shared_logger = SharedLogger()

# Convenience functions for easy use
def get_camera_log_dir():
    """Get camera log directory"""
    return shared_logger.get_camera_log_directory()

def get_forwarder_log_dir():
    """Get forwarder log directory"""
    return shared_logger.get_forwarder_log_directory()

def get_session_log_dir():
    """Get session log directory"""
    return shared_logger.get_session_log_directory()

def get_dic_quality_dir():
    """Get DIC quality log directory"""
    return shared_logger.get_dic_quality_directory()

def get_export_dir():
    """Get export directory"""
    return shared_logger.get_export_directory()

def create_timestamped_filename(prefix, extension, include_microseconds=True):
    """Create timestamped filename"""
    return shared_logger.create_timestamped_filename(prefix, extension, include_microseconds)

def write_csv_log(directory_type, filename, data, fieldnames=None):
    """Write CSV log"""
    return shared_logger.write_csv_log(directory_type, filename, data, fieldnames)

def append_csv_log(directory_type, filename, data, fieldnames=None):
    """Append to CSV log"""
    return shared_logger.append_csv_log(directory_type, filename, data, fieldnames)

def write_text_log(directory_type, filename, content, mode='w'):
    """Write text log"""
    return shared_logger.write_text_log(directory_type, filename, content, mode)