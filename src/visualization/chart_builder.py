"""
Chart building and configuration classes for MCSR Ranked Stats visualization.
Provides centralized chart creation with consistent styling and user customization options.
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class ChartType(Enum):
    """Types of charts available"""
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    HISTOGRAM = "histogram"
    PIE = "pie"
    BOX = "box"
    AREA = "area"


@dataclass
class SeriesConfig:
    """Configuration for a single data series in a chart"""
    x_data: List[Any]
    y_data: List[float]
    chart_type: ChartType = ChartType.LINE
    label: str = ""
    color: Optional[str] = None
    alpha: float = 0.7
    linewidth: float = 2
    markersize: float = 6
    linestyle: str = "-"
    marker: Optional[str] = None
    fill: bool = False  # For area charts


@dataclass
class ChartConfig:
    """Configuration for a single chart/subplot"""
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    series: List[SeriesConfig] = field(default_factory=list)
    show_grid: bool = True
    grid_alpha: float = 0.3
    show_legend: bool = False
    legend_loc: str = "best"
    xlim: Optional[Tuple[float, float]] = None
    ylim: Optional[Tuple[float, float]] = None
    x_rotation: float = 0
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    vertical_lines: List[Dict[str, Any]] = field(default_factory=list)
    horizontal_lines: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FigureConfig:
    """Configuration for the entire figure"""
    title: str = ""
    charts: List[ChartConfig] = field(default_factory=list)
    rows: int = 1
    cols: int = 1
    figsize: Tuple[float, float] = (10, 6)
    # Theme settings
    bg_color: str = '#2d2d2d'
    text_color: str = 'white'
    grid_color: str = 'white'
    legend_bg: str = '#3d3d3d'
    # Default color palette
    color_palette: List[str] = field(default_factory=lambda: [
        '#4CAF50', '#2196F3', '#FF9800', '#E91E63', '#9C27B0',
        '#00BCD4', '#FFEB3B', '#795548', '#607D8B', '#F44336'
    ])


class ChartBuilder:
    """
    Centralized chart creation and management.
    
    Provides a fluent API for creating charts with consistent styling
    and supports user-configurable options.
    """
    
    # Default theme colors
    DEFAULT_THEME = {
        'bg_color': '#2d2d2d',
        'text_color': 'white',
        'grid_color': 'white',
        'legend_bg': '#3d3d3d',
        'legend_text': 'white',
    }
    
    # Color palettes
    PALETTES = {
        'default': ['#4CAF50', '#2196F3', '#FF9800', '#E91E63', '#9C27B0',
                   '#00BCD4', '#FFEB3B', '#795548', '#607D8B', '#F44336'],
        'warm': ['#FF6B6B', '#FFE66D', '#FF8E72', '#FFC75F', '#F9844A',
                '#F8961E', '#F3722C', '#F94144', '#90BE6D', '#43AA8B'],
        'cool': ['#3A86FF', '#8338EC', '#FF006E', '#FB5607', '#FFBE0B',
                '#06D6A0', '#118AB2', '#073B4C', '#EF476F', '#FFD166'],
        'pastel': ['#A8DADC', '#457B9D', '#F1FAEE', '#E63946', '#48C9B0',
                  '#FFB4A2', '#E5989B', '#B5838D', '#6D6875', '#FFCDB2'],
    }
    
    def __init__(self, figure: Figure, canvas: FigureCanvasTkAgg):
        """
        Initialize ChartBuilder with a matplotlib figure and canvas.
        
        Args:
            figure: The matplotlib Figure to draw on
            canvas: The Tkinter canvas widget
        """
        self.fig = figure
        self.canvas = canvas
        self.theme = self.DEFAULT_THEME.copy()
        self.palette = self.PALETTES['default'].copy()
        self.axes = []
        
        # For click detection on scatter points
        self.scatter_data = {}  # Maps axes to list of (x, y, match_data) tuples
        self.click_callbacks = {}  # Maps axes to callback functions
        
        # For hover tooltips on rolling averages and medians
        self.rolling_avg_data = {}  # Maps axes to list of (x, y) tuples for rolling averages
        self.rolling_median_data = {}  # Maps axes to list of (x, y) tuples for rolling medians
        self.comparison_rolling_avg_data = {}  # Maps axes to comparison player rolling avg data
        self.comparison_rolling_median_data = {}  # Maps axes to comparison player rolling median data
        self.hover_tooltip = None  # Current tooltip annotation
        self.hover_line = None  # Current hover line indicator
        self.time_formatter = None  # Function to format time values for display
        
    def set_theme(self, **kwargs):
        """Update theme colors"""
        self.theme.update(kwargs)
        return self
        
    def set_palette(self, palette_name: str = None, colors: List[str] = None):
        """Set color palette by name or custom colors"""
        if palette_name and palette_name in self.PALETTES:
            self.palette = self.PALETTES[palette_name].copy()
        elif colors:
            self.palette = colors.copy()
        return self
        
    def get_color(self, index: int) -> str:
        """Get color from palette by index (cycles if needed)"""
        return self.palette[index % len(self.palette)]
        
    def clear(self):
        """Clear the figure"""
        self.fig.clear()
        self.axes = []
        self.scatter_data = {}
        self.click_callbacks = {}
        self.rolling_avg_data = {}
        self.comparison_rolling_avg_data = {}
        self.rolling_median_data = {}
        self.comparison_rolling_median_data = {}
        self.hover_tooltip = None
        self.hover_line = None
        return self
        
    def create_subplots(self, rows: int = 1, cols: int = 1) -> List[plt.Axes]:
        """Create a grid of subplots and return axes list"""
        self.axes = []
        for i in range(rows * cols):
            ax = self.fig.add_subplot(rows, cols, i + 1)
            self._apply_axis_theme(ax)
            self.axes.append(ax)
        return self.axes
        
    def get_subplot(self, rows: int, cols: int, index: int) -> plt.Axes:
        """Get or create a single subplot at position"""
        ax = self.fig.add_subplot(rows, cols, index)
        self._apply_axis_theme(ax)
        return ax
        
    def _apply_axis_theme(self, ax: plt.Axes):
        """Apply theme styling to an axis"""
        ax.set_facecolor(self.theme['bg_color'])
        ax.tick_params(colors=self.theme['text_color'])
        for spine in ax.spines.values():
            spine.set_color(self.theme['text_color'])
            
    def plot_line(self, ax: plt.Axes, x_data, y_data, 
                  color: str = None, label: str = None,
                  linewidth: float = 2, linestyle: str = '-',
                  marker: str = None, markersize: float = 6,
                  alpha: float = 1.0, color_index: int = 0):
        """Plot a line on the given axis"""
        color = color or self.get_color(color_index)
        ax.plot(x_data, y_data, color=color, label=label, 
                linewidth=linewidth, linestyle=linestyle,
                marker=marker, markersize=markersize, alpha=alpha)
        return self
        
    def plot_scatter(self, ax: plt.Axes, x_data, y_data,
                     color: str = None, label: str = None,
                     size: float = 30, alpha: float = 0.6,
                     marker: str = 'o', color_index: int = 0,
                     match_data: List = None):
        """Plot scatter points on the given axis
        
        Args:
            ax: Matplotlib axes
            x_data: X coordinates
            y_data: Y coordinates  
            color: Point color
            label: Legend label
            size: Point size
            alpha: Transparency
            marker: Marker style
            color_index: Color palette index
            match_data: Optional list of Match objects corresponding to each point
        """
        color = color or self.get_color(color_index)
        ax.scatter(x_data, y_data, c=color, label=label,
                  s=size, alpha=alpha, marker=marker)
        
        # Store match data for click detection if provided
        if match_data is not None:
            if ax not in self.scatter_data:
                self.scatter_data[ax] = []
            
            # Store (x, y, match) tuples for this scatter plot
            for x, y, match in zip(x_data, y_data, match_data):
                self.scatter_data[ax].append((x, y, match))
        
        return self
        
    def plot_bar(self, ax: plt.Axes, x_data, y_data,
                 color: str = None, label: str = None,
                 alpha: float = 0.7, width: float = 0.8,
                 color_index: int = 0, colors: List[str] = None):
        """Plot bar chart on the given axis"""
        if colors:
            bar_colors = colors
        else:
            bar_colors = color or self.get_color(color_index)
        ax.bar(x_data, y_data, color=bar_colors, label=label, 
               alpha=alpha, width=width)
        return self
        
    def plot_histogram(self, ax: plt.Axes, data, bins: int = 20,
                       color: str = None, label: str = None,
                       alpha: float = 0.7, edgecolor: str = 'white',
                       color_index: int = 0):
        """Plot histogram on the given axis"""
        color = color or self.get_color(color_index)
        ax.hist(data, bins=bins, color=color, label=label,
               alpha=alpha, edgecolor=edgecolor)
        return self
        
    def plot_pie(self, ax: plt.Axes, data, labels: List[str],
                 colors: List[str] = None, autopct: str = '%1.1f%%',
                 startangle: float = 90):
        """Plot pie chart on the given axis"""
        colors = colors or [self.get_color(i) for i in range(len(data))]
        ax.pie(data, labels=labels, colors=colors, autopct=autopct,
              startangle=startangle)
        return self
        
    def plot_box(self, ax: plt.Axes, data: List[List[float]], labels: List[str],
                 color: str = None, alpha: float = 0.7, color_index: int = 0):
        """Plot box plot on the given axis"""
        color = color or self.get_color(color_index)
        bp = ax.boxplot(data, labels=labels, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor(color)
            patch.set_alpha(alpha)
        return self
        
    def plot_area(self, ax: plt.Axes, x_data, y_data,
                  color: str = None, label: str = None,
                  alpha: float = 0.3, line_alpha: float = 1.0,
                  linewidth: float = 2, color_index: int = 0):
        """Plot area chart (fill_between) on the given axis"""
        color = color or self.get_color(color_index)
        ax.fill_between(x_data, y_data, alpha=alpha, color=color, label=label)
        ax.plot(x_data, y_data, color=color, linewidth=linewidth, alpha=line_alpha)
        return self
        
    def _calculate_rolling_stats(self, ax: plt.Axes, x_data, y_data,
                                window: int, stat_func, color: str = None,
                                linewidth: float = 2, alpha: float = 0.8,
                                label: str = None, color_index: int = 1,
                                full_x_data=None, full_y_data=None,
                                is_comparison=False, data_storage_key: str = None):
        """
        Unified rolling statistics calculation with shared datetime/numeric handling.
        
        Args:
            ax: The matplotlib axes to plot on
            x_data: X values for the visible portion
            y_data: Y values for the visible portion  
            window: Rolling window size
            stat_func: Statistical function (statistics.mean, statistics.median, etc.)
            color: Line color
            linewidth: Line width
            alpha: Line transparency
            label: Legend label
            color_index: Color palette index
            full_x_data: Complete X dataset for calculation
            full_y_data: Complete Y dataset for calculation
            is_comparison: Whether this is comparison player data
            data_storage_key: Key for storing data (e.g., 'rolling_avg_data', 'rolling_median_data')
        """
        if len(y_data) < 1:
            return self
        
        color = color or self.get_color(color_index)
        
        # Use full dataset for calculation if provided, otherwise use visible data
        calc_x = full_x_data if full_x_data is not None else x_data
        calc_y = full_y_data if full_y_data is not None else y_data
        
        if len(calc_y) < window and full_y_data is None:
            return self
            
        rolling_values = []
        rolling_x = []
        
        # Calculate rolling statistics using full dataset
        for i in range(len(calc_y)):
            # Use available data if less than window size
            start_idx = max(0, i - window + 1)
            window_data = calc_y[start_idx:i+1]
            
            if len(window_data) >= 1:  # At least one point
                rolling_values.append(stat_func(window_data))
                rolling_x.append(calc_x[i])
        
        # If using full dataset, filter to only show the visible range
        if full_x_data is not None and full_y_data is not None:
            filtered_values = []
            filtered_x = []
            
            if hasattr(x_data[0], 'timestamp') if x_data else False:
                # Date filtering for datetime x_data
                min_x = min(x_data)
                max_x = max(x_data)
                for i, x_val in enumerate(rolling_x):
                    if min_x <= x_val <= max_x:
                        filtered_x.append(x_val)
                        filtered_values.append(rolling_values[i])
            else:
                # Numeric filtering for numeric x_data
                for i, x_val in enumerate(rolling_x):
                    if x_val in x_data:  # Only show points that are in visible data
                        filtered_x.append(x_val)
                        filtered_values.append(rolling_values[i])
            
            rolling_values = filtered_values
            rolling_x = filtered_x

        if rolling_values and rolling_x:
            # Sort by x values to ensure proper line plotting
            if len(rolling_x) > 1:
                # Create pairs and sort
                pairs = list(zip(rolling_x, rolling_values))
                if hasattr(rolling_x[0], 'timestamp'):
                    # Sort by timestamp for datetime objects
                    pairs.sort(key=lambda p: p[0].timestamp())
                else:
                    # Sort by value for numeric data
                    pairs.sort(key=lambda p: p[0])
                rolling_x, rolling_values = zip(*pairs)

            # Plot the rolling statistics line
            ax.plot(rolling_x, rolling_values, color=color, linewidth=linewidth,
                   alpha=alpha, label=label)

            # Store rolling data for hover tooltips if data_storage_key provided
            if data_storage_key:
                rolling_data = list(zip(rolling_x, rolling_values))
                
                if is_comparison:
                    comparison_dict = getattr(self, f"comparison_{data_storage_key}")
                    if ax not in comparison_dict:
                        comparison_dict[ax] = []
                    comparison_dict[ax] = rolling_data
                else:
                    storage_dict = getattr(self, data_storage_key)
                    if ax not in storage_dict:
                        storage_dict[ax] = []
                    storage_dict[ax] = rolling_data

        return self
        
    def add_rolling_average(self, ax: plt.Axes, x_data, y_data,
                            window: int = 10, color: str = None,
                            linewidth: float = 2, alpha: float = 0.8,
                            label: str = None, color_index: int = 1,
                            full_x_data=None, full_y_data=None,
                            is_comparison=False):
        """Add a rolling average line to the chart using shared calculation logic."""
        import statistics
        label = label or f'{window}-point average'
        return self._calculate_rolling_stats(
            ax, x_data, y_data, window, statistics.mean, color,
            linewidth, alpha, label, color_index, full_x_data, full_y_data,
            is_comparison, 'rolling_avg_data'
        )
    
    def add_rolling_median(self, ax: plt.Axes, x_data, y_data,
                          window: int = 10, color: str = None,
                          linewidth: float = 2, alpha: float = 0.8,
                          label: str = None, color_index: int = 3,
                          full_x_data=None, full_y_data=None,
                          is_comparison=False):
        """Add a rolling median line to the chart using shared calculation logic."""
        import statistics
        label = label or f'{window}-point median'
        return self._calculate_rolling_stats(
            ax, x_data, y_data, window, statistics.median, color,
            linewidth, alpha, label, color_index, full_x_data, full_y_data,
            is_comparison, 'rolling_median_data'
        )
    
    def add_rolling_std_dev(self, ax: plt.Axes, x_data, y_data,
                           window: int = 10, color: str = None,
                           linewidth: float = 1.5, alpha: float = 0.6,
                           fill_alpha: float = 0.15, label: str = None,
                           show_fill: bool = True, color_index: int = 2,
                           full_x_data=None, full_y_data=None):
        """Add rolling standard deviation bands (mean ± std dev) to the chart
        
        Args:
            ax: The matplotlib axes to plot on
            x_data: X values for the visible portion
            y_data: Y values for the visible portion  
            window: Rolling window size
            color: Line color
            linewidth: Line width
            alpha: Line transparency
            fill_alpha: Fill transparency
            label: Legend label
            show_fill: Whether to fill between bounds
            color_index: Color palette index
            full_x_data: Complete X dataset (for calculating with historical data)
            full_y_data: Complete Y dataset (for calculating with historical data)
        """
        if len(y_data) < 1:
            return self
        
        color = color or self.get_color(color_index)
        
        # Use full dataset for calculation if provided, otherwise use visible data
        calc_x = full_x_data if full_x_data is not None else x_data
        calc_y = full_y_data if full_y_data is not None else y_data
        
        if len(calc_y) < window and full_y_data is None:
            return self
        
        rolling_mean = []
        rolling_upper = []
        rolling_lower = []
        rolling_x = []
        
        # Calculate rolling std dev using full dataset
        for i in range(len(calc_y)):
            # Use available data if less than window size
            start_idx = max(0, i - window + 1)
            window_data = calc_y[start_idx:i+1]
            
            if len(window_data) >= 1:
                mean = statistics.mean(window_data)
                std = statistics.stdev(window_data) if len(window_data) > 1 else 0
                rolling_mean.append(mean)
                rolling_upper.append(mean + std)
                rolling_lower.append(mean - std)
                rolling_x.append(calc_x[i])
        
        # If using full dataset, filter to only show the visible range
        if full_x_data is not None and full_y_data is not None:
            if len(x_data) > 0:
                visible_start = x_data[0]
                visible_end = x_data[-1]
                
                # Handle datetime comparison properly
                if hasattr(visible_start, 'timestamp'):
                    # Convert to timestamps for reliable comparison
                    visible_start_ts = visible_start.timestamp()
                    visible_end_ts = visible_end.timestamp()
                    
                    # Filter rolling data to visible range
                    filtered_mean = []
                    filtered_upper = []
                    filtered_lower = []
                    filtered_x = []
                    for i, x_val in enumerate(rolling_x):
                        x_val_ts = x_val.timestamp() if hasattr(x_val, 'timestamp') else x_val
                        if visible_start_ts <= x_val_ts <= visible_end_ts:
                            filtered_mean.append(rolling_mean[i])
                            filtered_upper.append(rolling_upper[i])
                            filtered_lower.append(rolling_lower[i])
                            filtered_x.append(x_val)
                else:
                    # Numeric comparison
                    filtered_mean = []
                    filtered_upper = []
                    filtered_lower = []
                    filtered_x = []
                    for i, x_val in enumerate(rolling_x):
                        if visible_start <= x_val <= visible_end:
                            filtered_mean.append(rolling_mean[i])
                            filtered_upper.append(rolling_upper[i])
                            filtered_lower.append(rolling_lower[i])
                            filtered_x.append(x_val)
                
                rolling_mean = filtered_mean
                rolling_upper = filtered_upper
                rolling_lower = filtered_lower
                rolling_x = filtered_x
        
        if rolling_x and rolling_upper and rolling_lower:
            # Ensure data is sorted by x values before plotting
            if len(rolling_x) > 1:
                # Create list of (x, upper, lower) tuples and sort by x
                triples = list(zip(rolling_x, rolling_upper, rolling_lower))
                if hasattr(rolling_x[0], 'timestamp'):
                    # Sort datetime objects
                    triples.sort(key=lambda t: t[0])
                else:
                    # Sort numeric values
                    triples.sort(key=lambda t: t[0])
                rolling_x, rolling_upper, rolling_lower = zip(*triples)
            
            label = label or f'±1 Std Dev ({window}-pt)'
            
            # Plot upper and lower bounds
            ax.plot(rolling_x, rolling_upper, color=color, linewidth=linewidth,
                   alpha=alpha, linestyle='--', label=label)
            ax.plot(rolling_x, rolling_lower, color=color, linewidth=linewidth,
                   alpha=alpha, linestyle='--')
            
            # Optionally fill between the bounds
            if show_fill:
                ax.fill_between(rolling_x, rolling_lower, rolling_upper, 
                               color=color, alpha=fill_alpha)
        
        return self
        
    def add_pb_line(self, ax: plt.Axes, x_data, y_data,
                    color: str = None, linestyle: str = '--',
                    linewidth: float = 1.5, alpha: float = 0.7,
                    label: str = 'PB', color_index: int = 3):
        """Add a personal best progression line"""
        color = color or self.get_color(color_index)
        
        pb_progression = []
        current_pb = float('inf')
        for val in y_data:
            if val < current_pb:
                current_pb = val
            pb_progression.append(current_pb)
            
        ax.plot(x_data, pb_progression, color=color, linestyle=linestyle,
               linewidth=linewidth, alpha=alpha, label=label)
        return self
        
    def add_vertical_line(self, ax: plt.Axes, x, color: str = 'red',
                          linestyle: str = '--', label: str = None,
                          linewidth: float = 1):
        """Add a vertical line to the chart"""
        ax.axvline(x, color=color, linestyle=linestyle, label=label,
                  linewidth=linewidth)
        return self
        
    def add_horizontal_line(self, ax: plt.Axes, y, color: str = 'red',
                            linestyle: str = '--', label: str = None,
                            linewidth: float = 1):
        """Add a horizontal line to the chart"""
        ax.axhline(y, color=color, linestyle=linestyle, label=label,
                  linewidth=linewidth)
        return self
        
    def add_annotation(self, ax: plt.Axes, text: str, x: float, y: float,
                       fontsize: int = 8, ha: str = 'left', va: str = 'top',
                       bbox: bool = True):
        """Add text annotation to the chart"""
        props = dict(fontsize=fontsize, color=self.theme['text_color'],
                    ha=ha, va=va)
        if bbox:
            props['bbox'] = dict(boxstyle='round', facecolor=self.theme['legend_bg'],
                               alpha=0.7)
        ax.text(x, y, text, transform=ax.transAxes, **props)
        return self
        
    def set_labels(self, ax: plt.Axes, title: str = None,
                   xlabel: str = None, ylabel: str = None,
                   title_fontsize: int = 10, label_fontsize: int = 8):
        """Set axis labels and title"""
        if title:
            ax.set_title(title, color=self.theme['text_color'], fontsize=title_fontsize)
        if xlabel:
            ax.set_xlabel(xlabel, color=self.theme['text_color'], fontsize=label_fontsize)
        if ylabel:
            ax.set_ylabel(ylabel, color=self.theme['text_color'], fontsize=label_fontsize)
        return self
        
    def set_grid(self, ax: plt.Axes, visible: bool = True, alpha: float = 0.3):
        """Configure grid visibility"""
        if visible:
            ax.grid(True, alpha=alpha)
        else:
            ax.grid(False)
        return self
        
    def set_legend(self, ax: plt.Axes, loc: str = 'best'):
        """Add legend to the axis"""
        ax.legend(facecolor=self.theme['legend_bg'], 
                 labelcolor=self.theme['legend_text'], loc=loc)
        return self
        
    def set_xticks(self, ax: plt.Axes, ticks, labels: List[str] = None,
                   rotation: float = 0, ha: str = 'center'):
        """Set x-axis ticks and labels"""
        ax.set_xticks(ticks)
        if labels:
            ax.set_xticklabels(labels, rotation=rotation, ha=ha)
        return self
        
    def set_title(self, title: str, fontsize: int = 14):
        """Set the figure title"""
        self.fig.suptitle(title, color=self.theme['text_color'], fontsize=fontsize)
        return self
    
    def enable_match_click_detection(self, callback_func):
        """
        Enable click detection on scatter points for match info
        
        Args:
            callback_func: Function to call when a match point is clicked.
                          Should accept (match_object) as parameter.
        """
        # Store the callback
        self.match_click_callback = callback_func
        
        # Connect the click event
        self.canvas.mpl_connect('button_press_event', self._on_scatter_click)
        
        return self
    
    def _on_scatter_click(self, event):
        """Handle click events on the chart canvas"""
        if event.inaxes is None or event.inaxes not in self.scatter_data:
            return
        
        if not hasattr(self, 'match_click_callback'):
            return
        
        # Find the closest scatter point
        closest_match = self._find_closest_match(event.inaxes, event.xdata, event.ydata, 2)
        
        if closest_match:
            self.match_click_callback(closest_match)
    
    def _find_closest_match(self, ax, click_x, click_y, max_distance=None):
        """
        Find the closest scatter point to the click location
        
        Args:
            ax: The axes that was clicked
            click_x, click_y: Click coordinates in data space
            max_distance: Maximum distance to consider (None for auto)
            
        Returns:
            Match object of closest point, or None if no point is close enough
        """
        if ax not in self.scatter_data:
            return None
        
        min_distance = float('inf')
        closest_match = None
        
        # Calculate distances to all points
        for x, y, match in self.scatter_data[ax]:
            # For date-based x-axis, need to handle datetime objects
            if hasattr(x, 'timestamp'):
                # Convert datetime to matplotlib date number for distance calculation
                import matplotlib.dates as mdates
                x_num = mdates.date2num(x)
                click_x_num = mdates.date2num(click_x) if hasattr(click_x, 'timestamp') else click_x
                dx = x_num - click_x_num
            else:
                dx = x - click_x
            
            dy = y - click_y
            distance = (dx**2 + dy**2)**0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_match = match
        
        # Auto-calculate reasonable max distance if not specified
        if max_distance is None:
            # Use 5% of the data range as max distance
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            x_range = xlim[1] - xlim[0]
            y_range = ylim[1] - ylim[0]
            max_distance = ((x_range * 0.05)**2 + (y_range * 0.05)**2)**0.5
        
        return closest_match if min_distance <= max_distance else None
    
    def enable_hover_tooltips(self, time_formatter=None):
        """
        Enable hover tooltips for rolling average lines showing time values.
        
        Args:
            time_formatter: Function to format time values for display (e.g., minutes_to_str)
        """
        self.time_formatter = time_formatter or (lambda x: f"{x:.2f} min")
        
        # Connect hover event
        self.canvas.mpl_connect('motion_notify_event', self._on_hover)
        
        return self
    
    def _on_hover(self, event):
        """Handle hover events on the chart canvas"""
        try:
            if event.inaxes is None:
                self._clear_hover_elements()
                return
            
            ax = event.inaxes
            
            # Check if this axis has any rolling data (average or median)
            has_rolling_data = (ax in self.rolling_avg_data or 
                              ax in self.comparison_rolling_avg_data or
                              ax in self.rolling_median_data or
                              ax in self.comparison_rolling_median_data)
            
            if not has_rolling_data:
                self._clear_hover_elements()
                return
            
            if event.xdata is None or event.ydata is None:
                self._clear_hover_elements()
                return
            
            # Find the closest x value in rolling average data
            hover_info = self._find_hover_info(ax, event.xdata)
            
            if hover_info:
                self._show_hover_tooltip(ax, event.xdata, hover_info)
            else:
                self._clear_hover_elements()
        except Exception:
            # Silently handle any hover errors to prevent crashes
            self._clear_hover_elements()
    
    def _find_hover_info(self, ax, hover_x):
        """Find rolling data values at the hover x position (average or median)"""
        hover_info = {}
        
        # Prioritize the data type that has the most recent data for this axis
        # This handles the case where both average and median might be stored
        # but we want to show the one that's currently being displayed
        
        # Check main player rolling data
        main_value = None
        if ax in self.rolling_avg_data and self.rolling_avg_data[ax]:
            main_value = self._interpolate_rolling_data(self.rolling_avg_data[ax], hover_x)
        if main_value is None and ax in self.rolling_median_data and self.rolling_median_data[ax]:
            main_value = self._interpolate_rolling_data(self.rolling_median_data[ax], hover_x)
        
        if main_value is not None:
            hover_info['main'] = main_value
        
        # Check comparison player rolling data
        comp_value = None
        if ax in self.comparison_rolling_avg_data and self.comparison_rolling_avg_data[ax]:
            comp_value = self._interpolate_rolling_data(self.comparison_rolling_avg_data[ax], hover_x)
        if comp_value is None and ax in self.comparison_rolling_median_data and self.comparison_rolling_median_data[ax]:
            comp_value = self._interpolate_rolling_data(self.comparison_rolling_median_data[ax], hover_x)
            
        if comp_value is not None:
            hover_info['comparison'] = comp_value
        
        return hover_info if hover_info else None
    
    def _interpolate_rolling_data(self, rolling_data, hover_x):
        """Interpolate rolling data value at hover_x position"""
        if not rolling_data:
            return None
        
        x_values = [point[0] for point in rolling_data]
        y_values = [point[1] for point in rolling_data]
        
        # Handle datetime objects - ensure consistent conversion
        if len(x_values) > 0 and hasattr(x_values[0], 'timestamp'):
            # Data has datetime objects, need to convert hover_x from matplotlib datenum
            import matplotlib.dates as mdates
            
            # Convert matplotlib date number to datetime
            if hasattr(hover_x, 'timestamp'):
                # Already a datetime
                hover_x_dt = hover_x
            else:
                # Convert matplotlib date number to datetime
                hover_x_dt = mdates.num2date(hover_x)
            
            # Convert to timestamp for comparison
            hover_x_val = hover_x_dt.timestamp()
            x_vals_converted = [x.timestamp() for x in x_values]
        else:
            # Numeric data
            hover_x_val = float(hover_x)
            x_vals_converted = [float(x) for x in x_values]
        
        # Find the closest points for interpolation
        if not x_vals_converted or hover_x_val < min(x_vals_converted) or hover_x_val > max(x_vals_converted):
            return None
        
        # Linear interpolation
        for i in range(len(x_vals_converted) - 1):
            if x_vals_converted[i] <= hover_x_val <= x_vals_converted[i + 1]:
                # Interpolate between points i and i+1
                x1, x2 = x_vals_converted[i], x_vals_converted[i + 1]
                y1, y2 = y_values[i], y_values[i + 1]
                
                if x2 == x1:
                    return y1
                
                # Linear interpolation formula
                ratio = (hover_x_val - x1) / (x2 - x1)
                interpolated_y = y1 + ratio * (y2 - y1)
                return interpolated_y
        
        return None
    
    def _show_hover_tooltip(self, ax, hover_x, hover_info):
        """Display hover tooltip and vertical line"""
        self._clear_hover_elements()
        
        # Create vertical line at hover position
        ylim = ax.get_ylim()
        self.hover_line = ax.axvline(hover_x, color='white', linestyle='--', 
                                    alpha=0.7, linewidth=1)
        
        # Format tooltip text (no date/x value, only rolling data)
        tooltip_lines = []
        
        # Determine what type of rolling data is being shown
        rolling_type = "Avg"  # Default to average
        if ax in self.rolling_median_data or ax in self.comparison_rolling_median_data:
            if ax not in self.rolling_avg_data and ax not in self.comparison_rolling_avg_data:
                rolling_type = "Median"
        
        # Add rolling data values
        if 'main' in hover_info:
            formatted_time = self.time_formatter(hover_info['main'])
            tooltip_lines.append(f"Rolling {rolling_type}: {formatted_time}")
        
        if 'comparison' in hover_info:
            formatted_time = self.time_formatter(hover_info['comparison'])
            tooltip_lines.append(f"Comp. Rolling {rolling_type}: {formatted_time}")
        
        tooltip_text = '\n'.join(tooltip_lines)
        
        # Position tooltip in the upper right of the plot
        x_pos = 0.98
        y_pos = 0.98
        
        self.hover_tooltip = ax.text(x_pos, y_pos, tooltip_text,
                                   transform=ax.transAxes,
                                   bbox=dict(boxstyle='round,pad=0.3', 
                                           facecolor=self.theme['legend_bg'],
                                           alpha=0.9, edgecolor='white'),
                                   color=self.theme['text_color'],
                                   fontsize=9,
                                   ha='right', va='top',
                                   zorder=1000)
        
        # Redraw canvas
        self.canvas.draw_idle()
    
    def _clear_hover_elements(self):
        """Clear hover tooltip and line"""
        try:
            if self.hover_tooltip:
                self.hover_tooltip.remove()
                self.hover_tooltip = None
        except Exception:
            self.hover_tooltip = None
        
        try:
            if self.hover_line:
                self.hover_line.remove()
                self.hover_line = None
        except Exception:
            self.hover_line = None
        
        # Redraw canvas
        try:
            self.canvas.draw_idle()
        except Exception:
            pass
        
    def finalize(self):
        """Apply tight layout and draw the canvas"""
        self.fig.tight_layout()
        self.canvas.draw()
        return self
        
    def build_from_config(self, config: FigureConfig):
        """Build entire figure from a FigureConfig object"""
        self.clear()
        self.theme['bg_color'] = config.bg_color
        self.theme['text_color'] = config.text_color
        self.palette = config.color_palette
        
        n_charts = len(config.charts)
        if n_charts == 0:
            return self
            
        # Create subplots
        self.create_subplots(config.rows, config.cols)
        
        # Build each chart
        for i, chart_config in enumerate(config.charts):
            if i >= len(self.axes):
                break
            ax = self.axes[i]
            self._build_chart(ax, chart_config)
            
        # Set figure title
        if config.title:
            self.set_title(config.title)
            
        return self.finalize()
        
    def _build_chart(self, ax: plt.Axes, config: ChartConfig):
        """Build a single chart from ChartConfig"""
        # Plot each series
        for i, series in enumerate(config.series):
            self._plot_series(ax, series, i)
            
        # Set labels
        self.set_labels(ax, title=config.title, xlabel=config.xlabel, ylabel=config.ylabel)
        
        # Configure grid
        self.set_grid(ax, config.show_grid, config.grid_alpha)
        
        # Configure legend
        if config.show_legend:
            self.set_legend(ax, config.legend_loc)
            
        # Apply limits
        if config.xlim:
            ax.set_xlim(config.xlim)
        if config.ylim:
            ax.set_ylim(config.ylim)
            
        # Apply x rotation
        if config.x_rotation:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=config.x_rotation)
            
        # Add vertical lines
        for vline in config.vertical_lines:
            self.add_vertical_line(ax, **vline)
            
        # Add horizontal lines
        for hline in config.horizontal_lines:
            self.add_horizontal_line(ax, **hline)
            
        # Add annotations
        for annotation in config.annotations:
            self.add_annotation(ax, **annotation)
            
    def _plot_series(self, ax: plt.Axes, series: SeriesConfig, index: int):
        """Plot a single data series"""
        color = series.color or self.get_color(index)
        
        if series.chart_type == ChartType.LINE:
            self.plot_line(ax, series.x_data, series.y_data, color=color,
                          label=series.label, linewidth=series.linewidth,
                          linestyle=series.linestyle, marker=series.marker,
                          markersize=series.markersize, alpha=series.alpha)
        elif series.chart_type == ChartType.SCATTER:
            self.plot_scatter(ax, series.x_data, series.y_data, color=color,
                            label=series.label, size=series.markersize,
                            alpha=series.alpha)
        elif series.chart_type == ChartType.BAR:
            self.plot_bar(ax, series.x_data, series.y_data, color=color,
                         label=series.label, alpha=series.alpha)
        elif series.chart_type == ChartType.AREA:
            self.plot_area(ax, series.x_data, series.y_data, color=color,
                          label=series.label, alpha=series.alpha)
