"""
Common UI imports for MCSR Ranked User Stats.

This module consolidates frequently used UI imports that appear across 
multiple files in the project, reducing import duplication and ensuring
consistency.
"""

# Core tkinter imports
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font

# Matplotlib imports for chart integration
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Common typing imports for type hints
from typing import List, Dict, Optional, Any, Union, Callable, Tuple

# Common standard library imports
import threading
import json
from datetime import datetime
import statistics