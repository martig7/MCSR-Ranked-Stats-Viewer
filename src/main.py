#!/usr/bin/env python3
"""
Main entry point for MCSR Ranked User Statistics Application
"""

import sys
import os
import tkinter as tk

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.ui.main_window import MCSRStatsUI


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = MCSRStatsUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()