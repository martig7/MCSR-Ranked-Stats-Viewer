"""
UI component builders for MCSR Stats UI.
Creates and configures all UI elements.
"""

import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class TopBar:
    """Creates and manages the top control bar"""
    
    def __init__(self, parent, ui_context):
        """
        Initialize top bar.
        
        Args:
            parent: Parent frame to attach to
            ui_context: Reference to main UI (MCSRStatsUI instance)
        """
        self.parent = parent
        self.ui = ui_context
        self.frame = None
        
    def create(self):
        """Create the top control bar"""
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.X)
        
        # Username entry
        ttk.Label(self.frame, text="Username:", font=('Segoe UI', 10)).pack(side=tk.LEFT)
        
        self.ui.username_var = tk.StringVar(value="gcm_0")
        self.ui.username_entry = ttk.Entry(self.frame, textvariable=self.ui.username_var, width=20, font=('Segoe UI', 10))
        self.ui.username_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.ui.username_entry.bind('<Return>', lambda e: self.ui._load_data())
        
        # Load button
        self.ui.load_btn = ttk.Button(self.frame, text="Load", command=lambda: self.ui.data_loader.load_from_cache() if self.ui.data_loader else None)
        self.ui.load_btn.pack(side=tk.LEFT, padx=5)
        
        # Refresh button (fetch new)
        self.ui.refresh_btn = ttk.Button(self.frame, text="Refresh", command=lambda: self.ui.data_loader.refresh_from_api() if self.ui.data_loader else None)
        self.ui.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Fetch segments button
        self.ui.fetch_segments_btn = ttk.Button(self.frame, text="Fetch Segments", command=lambda: self.ui.data_loader.fetch_segments() if self.ui.data_loader else None)
        self.ui.fetch_segments_btn.pack(side=tk.LEFT, padx=5)
        
        # Season filter
        ttk.Label(self.frame, text="Season:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20, 5))
        self.ui.season_var = tk.StringVar(value="All")
        self.ui.season_combo = ttk.Combobox(self.frame, textvariable=self.ui.season_var, width=10, state='readonly')
        self.ui.season_combo['values'] = ['All']
        self.ui.season_combo.pack(side=tk.LEFT)
        self.ui.season_combo.bind('<<ComboboxSelected>>', lambda e: self.ui._update_display())
        
        # Seed type filter
        ttk.Label(self.frame, text="Seed:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20, 5))
        self.ui.seed_filter_var = tk.StringVar(value="All")
        self.ui.seed_filter_combo = ttk.Combobox(self.frame, textvariable=self.ui.seed_filter_var, width=12, state='readonly')
        self.ui.seed_filter_combo['values'] = ['All']
        self.ui.seed_filter_combo.pack(side=tk.LEFT)
        self.ui.seed_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.ui._update_display())
        
        # Private room filter
        self.ui.include_private_var = tk.BooleanVar(value=True)
        self.ui.private_check = ttk.Checkbutton(self.frame, text="Include Private Rooms", 
                                               variable=self.ui.include_private_var,
                                               command=self.ui._update_display)
        self.ui.private_check.pack(side=tk.LEFT, padx=(20, 5))
        
        # More filters button
        self.ui.more_filters_btn = ttk.Button(self.frame, text="🔍 More Filters", 
                                               command=self.ui._show_filters_dialog)
        self.ui.more_filters_btn.pack(side=tk.LEFT, padx=(10, 5))
        
        # Player comparison controls
        ttk.Label(self.frame, text="Compare with:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20, 5))
        self.ui.comparison_var = tk.StringVar(value="None")
        self.ui.comparison_entry = ttk.Entry(self.frame, textvariable=self.ui.comparison_var, width=15)
        self.ui.comparison_entry.pack(side=tk.LEFT, padx=2)
        
        self.ui.load_comparison_btn = ttk.Button(self.frame, text="Load", command=lambda: self.ui.comparison_handler.load_player(self.ui.comparison_var.get()))
        self.ui.load_comparison_btn.pack(side=tk.LEFT, padx=2)
        
        self.ui.clear_comparison_btn = ttk.Button(self.frame, text="Clear", command=lambda: self.ui.comparison_handler.clear())
        self.ui.clear_comparison_btn.pack(side=tk.LEFT, padx=2)
        
        # Data management buttons
        ttk.Separator(self.frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=10)
        ttk.Label(self.frame, text="Clear Data:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(5, 2))
        
        self.ui.clear_basic_btn = ttk.Button(self.frame, text="Basic", command=lambda: self.ui.data_loader.clear_basic_data())
        self.ui.clear_basic_btn.pack(side=tk.LEFT, padx=2)
        
        self.ui.clear_all_btn = ttk.Button(self.frame, text="All", command=lambda: self.ui.data_loader.clear_all_data())
        self.ui.clear_all_btn.pack(side=tk.LEFT, padx=2)
        
        # Filter indicator label (shows when filters are active)
        self.ui.filter_indicator = ttk.Label(self.frame, text="", foreground="orange", 
                                              font=('Segoe UI', 9, 'bold'))
        self.ui.filter_indicator.pack(side=tk.LEFT, padx=5)


class Sidebar:
    """Creates and manages the left sidebar navigation"""
    
    def __init__(self, parent, ui_context):
        """
        Initialize sidebar.
        
        Args:
            parent: Parent frame to attach to
            ui_context: Reference to main UI (MCSRStatsUI instance)
        """
        self.parent = parent
        self.ui = ui_context
        self.frame = None
        
    def create(self):
        """Create the left sidebar with navigation"""
        self.ui.sidebar = ttk.Frame(self.parent, width=200)
        self.ui.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.ui.sidebar.pack_propagate(False)
        
        # Navigation label
        ttk.Label(self.ui.sidebar, text="Views", font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))
        
        # Navigation buttons
        nav_buttons = [
            ("📊 Summary", self.ui._show_summary),
            ("📈 Progression", lambda: self.ui.chart_views.progression.show()),
            # ("🎯 ELO Progress", lambda: self.ui.chart_views.elo.show()),  # Commented out - ELO feature not working
            ("🏆 Best Times", self.ui._show_best_times),
            ("📅 Season Stats", lambda: self.ui.chart_views.season_stats.show()),
            ("🌱 Seed Types", lambda: self.ui.chart_views.seed_types.show()),
            ("⏱️ Segments", lambda: self.ui.segment_analyzer.show_segments_text()),
            ("📊 Segment Trends", lambda: self.ui.segment_analyzer.show_segment_progression()),
            ("📉 Distribution", lambda: self.ui.chart_views.distribution.show()),
            ("🔍 Match Browser", self.ui._show_match_browser),
        ]
        
        self.ui.nav_buttons = {}
        for text, command in nav_buttons:
            btn = ttk.Button(self.ui.sidebar, text=text, command=command, width=18)
            btn.pack(pady=2, fill=tk.X)
            self.ui.nav_buttons[text] = btn
            
        # Separator
        ttk.Separator(self.ui.sidebar, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # Quick stats frame
        self.ui.quick_stats_frame = ttk.LabelFrame(self.ui.sidebar, text="Quick Stats", padding=10)
        self.ui.quick_stats_frame.pack(fill=tk.X, pady=5)
        
        self.ui.quick_stats_labels = {}
        for stat in ['Total Matches', 'Completed', 'Best Time', 'Average']:
            frame = ttk.Frame(self.ui.quick_stats_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{stat}:", font=('Segoe UI', 9)).pack(side=tk.LEFT)
            label = ttk.Label(frame, text="-", font=('Segoe UI', 9, 'bold'))
            label.pack(side=tk.RIGHT)
            self.ui.quick_stats_labels[stat] = label


class MainContent:
    """Creates and manages the main content area with tabs"""
    
    def __init__(self, parent, ui_context):
        """
        Initialize main content area.
        
        Args:
            parent: Parent frame to attach to
            ui_context: Reference to main UI (MCSRStatsUI instance)
        """
        self.parent = parent
        self.ui = ui_context
        
    def create(self):
        """Create the main content area"""
        self.ui.main_content = ttk.Frame(self.parent)
        self.ui.main_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Notebook for tabs
        self.ui.notebook = ttk.Notebook(self.ui.main_content)
        self.ui.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self._create_stats_tab()
        self._create_chart_tab()
        self._create_data_tab()
        
        # Show welcome message
        self.ui._show_welcome()
        
    def _create_stats_tab(self):
        """Create the statistics text tab"""
        self.ui.stats_frame = ttk.Frame(self.ui.notebook, padding=10)
        self.ui.notebook.add(self.ui.stats_frame, text="Statistics")
        
        # Create text widget for stats
        self.ui.stats_text = tk.Text(self.ui.stats_frame, wrap=tk.WORD, font=('Consolas', 10), 
                                      bg='#1e1e1e', fg='#d4d4d4', insertbackground='white')
        stats_scroll = ttk.Scrollbar(self.ui.stats_frame, orient=tk.VERTICAL, command=self.ui.stats_text.yview)
        self.ui.stats_text.configure(yscrollcommand=stats_scroll.set)
        stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.ui.stats_text.pack(fill=tk.BOTH, expand=True)
        
    def _create_chart_tab(self):
        """Create the chart visualization tab"""
        self.ui.chart_frame = ttk.Frame(self.ui.notebook, padding=10)
        self.ui.notebook.add(self.ui.chart_frame, text="Charts")
        
        # Back button frame (separate line, initially hidden)
        self.ui.back_btn_frame = ttk.Frame(self.ui.chart_frame)
        # Initially not packed - will be shown when a segment is expanded
        
        self.ui.back_btn = ttk.Button(
            self.ui.back_btn_frame,
            text="← Back to All Segments",
            command=lambda: self.ui.segment_analyzer.on_segment_back()
        )
        self.ui.back_btn.pack(side=tk.LEFT)
        
        # Chart controls frame (for view-specific options)
        self.ui.chart_controls_frame = ttk.Frame(self.ui.chart_frame)
        self.ui.chart_controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Left side - view-specific controls
        self.ui.view_controls_frame = ttk.Frame(self.ui.chart_controls_frame)
        self.ui.view_controls_frame.pack(side=tk.LEFT, fill=tk.X)
        
        # Split times toggle (shown only for Segment Trends view)
        self.ui.show_splits_var = tk.BooleanVar(value=False)
        self.ui.splits_check = ttk.Checkbutton(
            self.ui.view_controls_frame, 
            text="Show Split Times (time spent in each segment)", 
            variable=self.ui.show_splits_var,
            command=lambda: self.ui.segment_analyzer.on_splits_toggle()
        )
        # Initially hidden - will be shown when segment trends is selected
        
        # Match number x-axis toggle (shown for charts with date progression)
        self.ui.show_match_numbers_var = tk.BooleanVar(value=False)
        self.ui.match_numbers_check = ttk.Checkbutton(
            self.ui.view_controls_frame,
            text="Show Match Numbers (instead of dates)",
            variable=self.ui.show_match_numbers_var,
            command=self.ui._on_match_numbers_toggle
        )
        # Initially hidden - will be shown when date-based progression charts are active
        
        # Right side - general chart options
        self.ui.chart_options_frame = ttk.Frame(self.ui.chart_controls_frame)
        self.ui.chart_options_frame.pack(side=tk.RIGHT, fill=tk.X)
        
        # Chart options button to open settings dialog
        self.ui.chart_settings_btn = ttk.Button(
            self.ui.chart_options_frame, 
            text="⚙ Chart Options", 
            command=self.ui._show_chart_options_dialog
        )
        self.ui.chart_settings_btn.pack(side=tk.RIGHT, padx=5)
        
        # Quick toggles for common options
        self.ui.show_rolling_var = tk.BooleanVar(value=True)
        self.ui.rolling_check = ttk.Checkbutton(
            self.ui.chart_options_frame,
            text="Rolling Avg",
            variable=self.ui.show_rolling_var,
            command=self.ui._on_chart_option_change
        )
        self.ui.rolling_check.pack(side=tk.RIGHT, padx=5)
        
        self.ui.show_std_var = tk.BooleanVar(value=False)
        self.ui.std_check = ttk.Checkbutton(
            self.ui.chart_options_frame,
            text="Std Dev",
            variable=self.ui.show_std_var,
            command=self.ui._on_chart_option_change
        )
        self.ui.std_check.pack(side=tk.RIGHT, padx=5)
        
        self.ui.show_pb_var = tk.BooleanVar(value=True)
        self.ui.pb_check = ttk.Checkbutton(
            self.ui.chart_options_frame,
            text="PB Line",
            variable=self.ui.show_pb_var,
            command=self.ui._on_chart_option_change
        )
        self.ui.pb_check.pack(side=tk.RIGHT, padx=5)
        
        self.ui.show_grid_var = tk.BooleanVar(value=True)
        self.ui.grid_check = ttk.Checkbutton(
            self.ui.chart_options_frame,
            text="Grid",
            variable=self.ui.show_grid_var,
            command=self.ui._on_chart_option_change
        )
        self.ui.grid_check.pack(side=tk.RIGHT, padx=5)
        
        # Create matplotlib figure
        self.ui.fig = Figure(figsize=(10, 6), dpi=100)
        self.ui.fig.patch.set_facecolor('#2d2d2d')
        self.ui.canvas = FigureCanvasTkAgg(self.ui.fig, master=self.ui.chart_frame)
        self.ui.canvas.draw()
        
        # Toolbar
        toolbar_frame = ttk.Frame(self.ui.chart_frame)
        toolbar_frame.pack(fill=tk.X)
        self.ui.toolbar = NavigationToolbar2Tk(self.ui.canvas, toolbar_frame)
        self.ui.toolbar.update()
        
        self.ui.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def _create_data_tab(self):
        """Create the match browser data tab"""
        self.ui.data_frame = ttk.Frame(self.ui.notebook, padding=10)
        self.ui.notebook.add(self.ui.data_frame, text="Match Data")
        
        # Create paned window to allow resizing between tree and details
        self.ui.match_paned = ttk.PanedWindow(self.ui.data_frame, orient=tk.VERTICAL)
        self.ui.match_paned.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for treeview
        tree_frame = ttk.Frame(self.ui.match_paned)
        self.ui.match_paned.add(tree_frame, weight=3)
        
        # Create treeview for match data
        columns = ('Date', 'Time', 'Season', 'Seed Type', 'Type', 'Status', 'Winner')
        self.ui.match_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        col_widths = {'Date': 140, 'Time': 100, 'Season': 60, 'Seed Type': 100, 'Type': 80, 'Status': 80, 'Winner': 120}
        for col in columns:
            self.ui.match_tree.heading(col, text=col, command=lambda c=col: self.ui._sort_treeview(c))
            self.ui.match_tree.column(col, width=col_widths.get(col, 100))
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.ui.match_tree.yview)
        self.ui.match_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.ui.match_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.ui.match_tree.bind('<<TreeviewSelect>>', self.ui._on_match_selected)
        
        # Bottom frame for match details
        self.ui.detail_frame = ttk.LabelFrame(self.ui.match_paned, text="Match Details", padding=10)
        self.ui.match_paned.add(self.ui.detail_frame, weight=1)
        
        # Create detail text widget
        self.ui.detail_text = tk.Text(self.ui.detail_frame, wrap=tk.WORD, font=('Consolas', 10), 
                                       bg='#1e1e1e', fg='#d4d4d4', height=10, insertbackground='white')
        detail_scroll = ttk.Scrollbar(self.ui.detail_frame, orient=tk.VERTICAL, command=self.ui.detail_text.yview)
        self.ui.detail_text.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.ui.detail_text.pack(fill=tk.BOTH, expand=True)
        self.ui.detail_text.insert('1.0', "Select a match above to view details")
        self.ui.detail_text.config(state=tk.DISABLED)
        
        # Store match references for detail lookup
        self.ui.match_lookup = {}


class StatusBar:
    """Creates and manages the status bar"""
    
    def __init__(self, parent, ui_context):
        """
        Initialize status bar.
        
        Args:
            parent: Parent frame to attach to
            ui_context: Reference to main UI (MCSRStatsUI instance)
        """
        self.parent = parent
        self.ui = ui_context
        
    def create(self):
        """Create the status bar"""
        self.ui.status_frame = ttk.Frame(self.parent)
        self.ui.status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.ui.status_var = tk.StringVar(value="Ready - Enter a username and click 'Load Data'")
        self.ui.status_label = ttk.Label(self.ui.status_frame, textvariable=self.ui.status_var, font=('Segoe UI', 9))
        self.ui.status_label.pack(side=tk.LEFT)
        
        # Right side frame for progress elements
        self.ui.progress_frame = ttk.Frame(self.ui.status_frame)
        self.ui.progress_frame.pack(side=tk.RIGHT)
        
        # Loading text (hidden by default)
        self.ui.loading_text_var = tk.StringVar(value="")
        self.ui.loading_text_label = ttk.Label(self.ui.progress_frame, textvariable=self.ui.loading_text_var, 
                                               font=('Segoe UI', 9), foreground='blue')
        # Initially not packed - will be shown during loading
        
        # Progress bar (hidden by default)
        self.ui.progress = ttk.Progressbar(self.ui.progress_frame, mode='indeterminate', length=200)
        # Initially not packed - will be shown during loading
