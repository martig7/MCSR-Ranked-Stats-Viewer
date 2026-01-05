"""
Dialog windows for MCSR Stats UI.
Contains reusable dialog classes for filters and chart options.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List


class FiltersDialog:
    """Advanced filters dialog for date and time range filtering."""
    
    def __init__(self, parent: tk.Tk, current_filters: Dict[str, Any], 
                 on_apply: Callable[[Dict[str, Any]], None],
                 size: tuple = (450, 350)):
        """
        Initialize the filters dialog.
        
        Args:
            parent: Parent window
            current_filters: Dict with keys 'date_from', 'date_to', 'time_min', 'time_max'
            on_apply: Callback function receiving the new filter values
            size: Tuple of (width, height) for dialog size
        """
        self.parent = parent
        self.current_filters = current_filters
        self.on_apply = on_apply
        self.size = size
        
        self._create_dialog()
    
    def _create_dialog(self):
        """Create and display the dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Advanced Filters")
        self.dialog.geometry(f"{self.size[0]}x{self.size[1]}")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Date Range Section
        ttk.Label(main_frame, text="Date Range:", font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=0, columnspan=4, sticky='w', pady=(0, 10))
        
        ttk.Label(main_frame, text="From:").grid(row=1, column=0, sticky='w', pady=5)
        date_from = self.current_filters.get('date_from')
        self.date_from_var = tk.StringVar(value=date_from.strftime('%Y-%m-%d') if date_from else "")
        date_from_entry = ttk.Entry(main_frame, textvariable=self.date_from_var, width=12)
        date_from_entry.grid(row=1, column=1, sticky='w', pady=5, padx=5)
        ttk.Label(main_frame, text="(YYYY-MM-DD)", font=('Segoe UI', 8)).grid(row=1, column=2, sticky='w')
        
        ttk.Label(main_frame, text="To:").grid(row=2, column=0, sticky='w', pady=5)
        date_to = self.current_filters.get('date_to')
        self.date_to_var = tk.StringVar(value=date_to.strftime('%Y-%m-%d') if date_to else "")
        date_to_entry = ttk.Entry(main_frame, textvariable=self.date_to_var, width=12)
        date_to_entry.grid(row=2, column=1, sticky='w', pady=5, padx=5)
        ttk.Label(main_frame, text="(YYYY-MM-DD)", font=('Segoe UI', 8)).grid(row=2, column=2, sticky='w')
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=3, column=0, columnspan=4, sticky='ew', pady=15)
        
        # Completion Time Range Section
        ttk.Label(main_frame, text="Completion Time Range:", font=('Segoe UI', 10, 'bold')).grid(
            row=4, column=0, columnspan=4, sticky='w', pady=(0, 10))
        
        ttk.Label(main_frame, text="Min Time:").grid(row=5, column=0, sticky='w', pady=5)
        self.time_min_var = tk.StringVar(value=self._ms_to_mmss(self.current_filters.get('time_min')))
        time_min_entry = ttk.Entry(main_frame, textvariable=self.time_min_var, width=12)
        time_min_entry.grid(row=5, column=1, sticky='w', pady=5, padx=5)
        ttk.Label(main_frame, text="(MM:SS or minutes)", font=('Segoe UI', 8)).grid(row=5, column=2, sticky='w')
        
        ttk.Label(main_frame, text="Max Time:").grid(row=6, column=0, sticky='w', pady=5)
        self.time_max_var = tk.StringVar(value=self._ms_to_mmss(self.current_filters.get('time_max')))
        time_max_entry = ttk.Entry(main_frame, textvariable=self.time_max_var, width=12)
        time_max_entry.grid(row=6, column=1, sticky='w', pady=5, padx=5)
        ttk.Label(main_frame, text="(MM:SS or minutes)", font=('Segoe UI', 8)).grid(row=6, column=2, sticky='w')
        
        # Helper text
        ttk.Label(main_frame, text="Examples: '15:30' or '15.5' for 15 min 30 sec", 
                 font=('Segoe UI', 8), foreground='gray').grid(
            row=7, column=0, columnspan=4, sticky='w', pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=4, pady=25)
        
        ttk.Button(button_frame, text="Apply", command=self._apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self._clear_and_apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    @staticmethod
    def _ms_to_mmss(ms: Optional[int]) -> str:
        """Convert milliseconds to MM:SS format."""
        if ms is None:
            return ""
        total_seconds = ms / 1000
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    @staticmethod
    def _parse_time_string(time_str: str) -> Optional[int]:
        """Parse time string (MM:SS or decimal minutes) to milliseconds."""
        time_str = time_str.strip()
        if not time_str:
            return None
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = int(parts[1]) if len(parts) > 1 else 0
                return (minutes * 60 + seconds) * 1000
            else:
                # Treat as decimal minutes
                minutes = float(time_str)
                return int(minutes * 60 * 1000)
        except ValueError:
            return None
    
    @staticmethod
    def _parse_date_string(date_str: str) -> Optional[datetime]:
        """Parse date string (YYYY-MM-DD) to datetime."""
        date_str = date_str.strip()
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None
    
    def _apply(self):
        """Apply the current filter settings."""
        # Parse and validate date filters
        date_from = self._parse_date_string(self.date_from_var.get())
        date_to = self._parse_date_string(self.date_to_var.get())
        
        # If date_to is specified, set it to end of day
        if date_to:
            date_to = date_to.replace(hour=23, minute=59, second=59)
        
        # Parse and validate time filters
        time_min = self._parse_time_string(self.time_min_var.get())
        time_max = self._parse_time_string(self.time_max_var.get())
        
        # Validate time range
        if time_min is not None and time_max is not None and time_min > time_max:
            messagebox.showwarning("Invalid Range", "Min time cannot be greater than max time")
            return
        
        # Validate date range
        if date_from and date_to and date_from > date_to:
            messagebox.showwarning("Invalid Range", "From date cannot be after To date")
            return
        
        # Apply filters via callback
        self.on_apply({
            'date_from': date_from,
            'date_to': date_to,
            'time_min': time_min,
            'time_max': time_max
        })
        
        self.dialog.destroy()
    
    def _clear_and_apply(self):
        """Clear all filters and apply."""
        self.on_apply({
            'date_from': None,
            'date_to': None,
            'time_min': None,
            'time_max': None
        })
        self.dialog.destroy()


class ChartOptionsDialog:
    """Dialog for configuring chart display options."""
    
    def __init__(self, parent: tk.Tk, chart_options: Dict[str, Any],
                 palettes: List[str], on_apply: Callable[[Dict[str, Any]], None],
                 size: tuple = (450, 400)):
        """
        Initialize the chart options dialog.
        
        Args:
            parent: Parent window
            chart_options: Current chart options dictionary
            palettes: List of available color palette names
            on_apply: Callback function receiving the new options
            size: Tuple of (width, height) for dialog size
        """
        self.parent = parent
        self.chart_options = chart_options
        self.palettes = palettes
        self.on_apply = on_apply
        self.size = size
        
        self._create_dialog()
    
    def _create_dialog(self):
        """Create and display the dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Chart Options")
        self.dialog.geometry(f"{self.size[0]}x{self.size[1]}")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Rolling average window
        ttk.Label(main_frame, text="Rolling Average Window:").grid(row=0, column=0, sticky='w', pady=5)
        self.rolling_var = tk.IntVar(value=self.chart_options['rolling_window'])
        rolling_spin = ttk.Spinbox(main_frame, from_=3, to=50, textvariable=self.rolling_var, width=10)
        rolling_spin.grid(row=0, column=1, sticky='w', pady=5, padx=10)
        
        # Point size
        ttk.Label(main_frame, text="Point Size:").grid(row=1, column=0, sticky='w', pady=5)
        self.point_var = tk.IntVar(value=self.chart_options['point_size'])
        point_spin = ttk.Spinbox(main_frame, from_=10, to=100, textvariable=self.point_var, width=10)
        point_spin.grid(row=1, column=1, sticky='w', pady=5, padx=10)
        
        # Line width
        ttk.Label(main_frame, text="Line Width:").grid(row=2, column=0, sticky='w', pady=5)
        self.line_var = tk.IntVar(value=self.chart_options['line_width'])
        line_spin = ttk.Spinbox(main_frame, from_=1, to=5, textvariable=self.line_var, width=10)
        line_spin.grid(row=2, column=1, sticky='w', pady=5, padx=10)
        
        # Color palette
        ttk.Label(main_frame, text="Color Palette:").grid(row=3, column=0, sticky='w', pady=5)
        self.palette_var = tk.StringVar(value=self.chart_options['color_palette'])
        palette_combo = ttk.Combobox(main_frame, textvariable=self.palette_var, width=15, state='readonly')
        palette_combo['values'] = self.palettes
        palette_combo.grid(row=3, column=1, sticky='w', pady=5, padx=10)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky='ew', pady=15)
        
        # Display options
        ttk.Label(main_frame, text="Display Options:", font=('Segoe UI', 10, 'bold')).grid(
            row=5, column=0, columnspan=2, sticky='w', pady=5)
        
        self.show_rolling = tk.BooleanVar(value=self.chart_options['show_rolling_avg'])
        ttk.Checkbutton(main_frame, text="Show Rolling Average", variable=self.show_rolling).grid(
            row=6, column=0, columnspan=2, sticky='w', pady=2)
        
        self.show_rolling_median = tk.BooleanVar(value=self.chart_options['show_rolling_median'])
        ttk.Checkbutton(main_frame, text="Show Rolling Median", variable=self.show_rolling_median).grid(
            row=7, column=0, columnspan=2, sticky='w', pady=2)
        
        self.show_std = tk.BooleanVar(value=self.chart_options['show_rolling_std'])
        ttk.Checkbutton(main_frame, text="Show Rolling Std Dev (±1σ bands)", variable=self.show_std).grid(
            row=8, column=0, columnspan=2, sticky='w', pady=2)
        
        self.show_pb = tk.BooleanVar(value=self.chart_options['show_pb_line'])
        ttk.Checkbutton(main_frame, text="Show PB Progression Line", variable=self.show_pb).grid(
            row=9, column=0, columnspan=2, sticky='w', pady=2)
        
        self.show_grid = tk.BooleanVar(value=self.chart_options['show_grid'])
        ttk.Checkbutton(main_frame, text="Show Grid", variable=self.show_grid).grid(
            row=10, column=0, columnspan=2, sticky='w', pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=11, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Apply", command=self._apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset Defaults", command=self._reset_defaults).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _apply(self):
        """Apply the current options."""
        self.on_apply({
            'rolling_window': self.rolling_var.get(),
            'point_size': self.point_var.get(),
            'line_width': self.line_var.get(),
            'color_palette': self.palette_var.get(),
            'show_rolling_avg': self.show_rolling.get(),
            'show_rolling_median': self.show_rolling_median.get(),
            'show_rolling_std': self.show_std.get(),
            'show_pb_line': self.show_pb.get(),
            'show_grid': self.show_grid.get(),
        })
        self.dialog.destroy()
    
    def _reset_defaults(self):
        """Reset all options to defaults."""
        self.rolling_var.set(10)
        self.point_var.set(30)
        self.line_var.set(2)
        self.palette_var.set('default')
        self.show_rolling.set(True)
        self.show_rolling_median.set(False)
        self.show_std.set(False)
        self.show_pb.set(True)
        self.show_grid.set(True)
