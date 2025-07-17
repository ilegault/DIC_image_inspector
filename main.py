# This script is used to run the application from the command line.
# main.py
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now use a direct import
from app import main

if __name__ == "__main__":
    main()