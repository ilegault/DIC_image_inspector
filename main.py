"""
Entry point for DIC Image Quality Inspector application.

Launches the main application window for analyzing DIC (Digital Image Correlation)
image quality. This tool helps assess speckle pattern quality and provides
recommendations for optimal DIC analysis parameters.

Usage:
    python main.py
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now use a direct import
from app import main

if __name__ == "__main__":
    main()