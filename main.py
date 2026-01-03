#!/usr/bin/env python3
"""
MCSR Ranked User Statistics Application

Main entry point - run this file to start the application.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the application
from src.main import main

if __name__ == "__main__":
    main()