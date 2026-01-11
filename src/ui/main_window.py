"""
MCSR Ranked Stats Browser UI
A graphical interface for browsing MCSR Ranked speedrun statistics.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..core.analyzer import MCSRAnalyzer
from ..visualization.chart_builder import ChartBuilder
from ..visualization.text_presenter import TextPresenter
from ..visualization.rich_text_presenter import RichTextPresenter
from .dialogs import FiltersDialog, ChartOptionsDialog
from .handlers.segment_analysis import SegmentAnalyzer
from ..visualization.chart_views import ChartViewManager
from .handlers.comparison_handler import ComparisonHandler
from .handlers.data_loader import DataLoader
from .components import TopBar, Sidebar, MainContent, StatusBar
from ..utils.filter_manager import FilterManager
from ..utils.speedrun_forecast import create_forecast_results


class MCSRStatsUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MCSR Ranked Stats Browser")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        self.analyzer = None
        self.current_plot = None
        self.match_lookup = {}  # Store match references for detail view
        self.chart_builder = None  # Initialized after figure is created
        self.text_presenter = TextPresenter()  # Legacy text formatting and generation
        self.rich_text_presenter = RichTextPresenter()  # Modern text formatting and generation
        self.filter_manager = None  # Initialized after UI setup to avoid circular dependencies
        self.segment_analyzer = None  # Initialized after UI setup to avoid circular dependencies
        self.chart_views = None  # Initialized after UI setup to avoid circular dependencies
        
        # Segment trends display mode (False = absolute times, True = split times)
        self.show_splits_var = None  # Will be initialized in UI setup
        
        # Segment text view mode (False = absolute times, True = split times)  
        self.segment_text_mode_var = None  # Will be initialized in UI setup
        
        # Chart options (user-configurable)
        self.chart_options = {
            'rolling_window': 10,
            'show_rolling_avg': True,
            'show_rolling_median': False,
            'show_rolling_std': False,
            'show_pb_line': True,
            'show_grid': True,
            'color_palette': 'default',
            'point_size': 30,
            'line_width': 2,
        }
        
        # Advanced filter state
        self._filter_date_from = None  # datetime or None
        self._filter_date_to = None    # datetime or None
        self._filter_time_min = None   # milliseconds or None
        self._filter_time_max = None   # milliseconds or None
        
        # Current view tracking
        self._current_view = 'summary'  # Track current view to preserve on filter changes
        
        # Forecast settings
        self.forecast_rolling_window = 20  # Default rolling window size for forecasts
        self.forecast_percentile = 50.0   # Default percentile for forecasts (median)
        
        # Initialize handlers early (before UI setup so buttons can reference them)
        self.comparison_handler = None  # Will be initialized after UI setup
        self.data_loader = None  # Will be initialized after UI setup
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the main UI layout"""
        # Main container
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top bar - username and controls
        top_bar = TopBar(self.main_container, self)
        top_bar.create()
        
        # Content area
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Sidebar and main content
        sidebar = Sidebar(self.content_frame, self)
        sidebar.create()
        
        main_content = MainContent(self.content_frame, self)
        main_content.create()
        
        # Initialize handlers after UI components are created
        self.chart_builder = ChartBuilder(self.fig, self.canvas)
        self.filter_manager = FilterManager(self)
        self.segment_analyzer = SegmentAnalyzer(self)
        self.chart_views = ChartViewManager(self)
        self.comparison_handler = ComparisonHandler(self)
        self.data_loader = DataLoader(self)
        
        # Bind click events for segment expansion
        self.canvas.mpl_connect('button_press_event', lambda e: self.segment_analyzer.on_chart_click(e))
        
        # Status bar
        status_bar = StatusBar(self.main_container, self)
        status_bar.create()
        
    def _show_welcome(self):
        """Show welcome message"""
        self.rich_text_presenter.render_welcome(self.stats_text)
        
    def _set_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def _time_str(self, milliseconds):
        """Convert milliseconds to MM:SS.mmm format"""
        return self.text_presenter.format_time_ms_to_string(milliseconds)
    
    def _minutes_to_str(self, minutes):
        """Convert decimal minutes to 'Xm Ys' format"""
        return self.text_presenter.format_minutes_to_string(minutes)
        
    # Legacy methods for backward compatibility - delegate to data_loader
    def _load_data(self):
        """Load data from cache (backward compatibility)"""
        self.data_loader.load_from_cache()
        
    def _refresh_data(self):
        """Fetch fresh data from API (backward compatibility)"""
        self.data_loader.refresh_from_api()
        
    def _fetch_segments(self):
        """Fetch detailed segment data (backward compatibility)"""
        self.data_loader.fetch_segments()
        
    def _update_quick_stats(self):
        """Update quick stats in sidebar"""
        if not self.analyzer:
            return
        
        # Get filter settings
        include_private = self.include_private_var.get()
            
        stats = self.analyzer.basic_stats(include_private_rooms=include_private)
        if 'error' in stats:
            return
            
        self.quick_stats_labels['Total Matches'].config(text=str(stats['total_matches']))
        self.quick_stats_labels['Completed'].config(text=str(stats['completed']))
        self.quick_stats_labels['Best Time'].config(text=self._time_str(stats['best_time']))
        self.quick_stats_labels['Average'].config(text=self._time_str(int(stats['average_time']) if stats['average_time'] is not None else None))
        
    def _get_filtered_matches(self):
        """Get completed matches (user's wins) filtered by current UI filters"""
        return self.filter_manager.get_filtered_matches(self.analyzer, completed_only=True)
    
    def _get_all_filtered_matches(self):
        """Get all matches (wins/losses/draws) filtered by current UI filters"""
        return self.filter_manager.get_all_filtered_matches(self.analyzer)
        
    def _update_display(self):
        """Update display when filter changes"""
        self._update_quick_stats()
        self._update_filter_indicator()
        self._refresh_current_view()
    
    def _get_filtered_comparison_matches(self):
        """Get comparison player's completed matches with same filters as main player"""
        return self.comparison_handler.get_filtered_matches()
    
    def _get_all_filtered_comparison_matches(self):
        """Get all comparison player matches (wins/losses/draws) with same filters as main player"""
        return self.comparison_handler.get_all_filtered_matches()
    
    # Legacy properties for backward compatibility
    @property
    def comparison_analyzer(self):
        """Get comparison analyzer (backward compatibility)"""
        return self.comparison_handler.get_analyzer() if self.comparison_handler else None
    
    @property
    def comparison_active(self):
        """Check if comparison is active (backward compatibility)"""
        return self.comparison_handler.is_active() if self.comparison_handler else False
    
    def _generate_summary_text(self, analyzer):
        """Generate summary statistics text for a given analyzer"""
        if not analyzer:
            return "No data loaded."

        # Get matches with consistent filtering
        if analyzer == self.analyzer:
            all_matches = self._get_all_filtered_matches()
        else:
            all_matches = self._get_all_filtered_comparison_matches()

        return self.text_presenter.generate_summary_text(analyzer, all_matches)
    
    def _refresh_current_view(self):
        """Refresh the currently active view after filter changes"""
        if self._current_view == 'summary':
            self._show_summary()
        elif self._current_view == 'progression':
            self.chart_views.progression.show()
        # elif self._current_view == 'elo_progression':  # Commented out - ELO feature not working
        #     self.chart_views.elo.show()
        elif self._current_view == 'best_times':
            self._show_best_times()
        elif self._current_view == 'season_stats':
            self.chart_views.season_stats.show()
        elif self._current_view == 'seed_types':
            self.chart_views.seed_types.show()
        elif self._current_view == 'segments':
            self.segment_analyzer.show_segments_text()
        elif self._current_view == 'segment_progression':
            self.segment_analyzer.show_segment_progression()
        elif self._current_view == 'distribution':
            self.chart_views.distribution.show()
        elif self._current_view == 'match_browser':
            self._show_match_browser()
        elif self._current_view == 'forecast':
            self._show_forecast()
        else:
            # Fallback to summary if no valid view is tracked
            self._show_summary()
    
    def _update_filter_indicator(self):
        """Update the filter indicator label to show active filters"""
        filters_active = []
        if self._filter_date_from or self._filter_date_to:
            filters_active.append("Date")
        if self._filter_time_min is not None or self._filter_time_max is not None:
            filters_active.append("Time")
        
        if filters_active:
            self.filter_indicator.config(text=f"[Filters: {', '.join(filters_active)}]")
        else:
            self.filter_indicator.config(text="")
    
    def _show_filters_dialog(self):
        """Show dialog for advanced filtering options"""
        def on_apply(filters):
            self._filter_date_from = filters['date_from']
            self._filter_date_to = filters['date_to']
            self._filter_time_min = filters['time_min']
            self._filter_time_max = filters['time_max']
            
            self._update_display()
            self._populate_match_tree()
            
            # Refresh current chart if on charts tab
            if hasattr(self, '_current_chart_view') and self.notebook.index(self.notebook.select()) == 1:
                self._refresh_current_chart()
        
        current_filters = {
            'date_from': self._filter_date_from,
            'date_to': self._filter_date_to,
            'time_min': self._filter_time_min,
            'time_max': self._filter_time_max
        }
        
        FiltersDialog(self.root, current_filters, on_apply)
        
    def _populate_match_tree(self):
        """Populate match tree with data"""
        # Clear existing
        for item in self.match_tree.get_children():
            self.match_tree.delete(item)
        
        # Clear match lookup
        self.match_lookup = {}
            
        if not self.analyzer:
            return
            
        matches = self._get_all_filtered_matches()
        for match in sorted(matches, key=lambda x: x.date, reverse=True):
            # Use the proper status from user's perspective
            status = match.get_status()
            
            # Map match type to readable name
            type_names = {1: 'Ranked', 2: 'Casual(?)', 3: 'Private(?)'}
            match_type_name = type_names.get(match.match_type, f'Type{match.match_type}')
            
            # Get winner info
            if match.is_draw:
                winner = "(Draw)"
            elif match.winner:
                winner = match.winner
            else:
                winner = "-"
            
            # Show user's time if they completed, otherwise show time with indicator (parentheses)
            if match.user_completed and match.match_time:
                # Actual completion - show time normally
                time_display = match.time_str()
            elif not match.user_completed and match.match_time:
                # Not completed but has a time (forfeit win, solo forfeit, draw, etc.)
                time_display = f"({match.time_str()})"
            elif match.is_user_win is False and match.winner_time:
                # User lost - show winner's time with indicator
                time_display = f"({match.winner_time_str()})"
            else:
                time_display = "-"
            
            item_id = self.match_tree.insert('', tk.END, values=(
                match.date_str(),
                time_display,
                match.season,
                match.seed_type,
                match_type_name,
                status,
                winner
            ))
            
            # Store reference to match object
            self.match_lookup[item_id] = match
    
    def _on_match_selected(self, event):
        """Handle match selection to show details"""
        selection = self.match_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        match = self.match_lookup.get(item_id)
        
        if not match:
            return
        
        # Use modern rich text presenter for match details
        self.rich_text_presenter.render_match_detail(self.detail_text, match, self.analyzer.username)
            
    def _sort_treeview(self, col):
        """Sort treeview by column"""
        items = [(self.match_tree.set(k, col), k) for k in self.match_tree.get_children('')]
        items.sort(reverse=True)
        for index, (val, k) in enumerate(items):
            self.match_tree.move(k, '', index)
            
    def _show_summary(self):
        """Show summary stats"""
        self._current_view = 'summary'
        self.notebook.select(0)  # Stats tab
        
        # Hide segment controls when not viewing segments
        if hasattr(self, 'segment_text_controls_frame'):
            self.segment_text_controls_frame.pack_forget()
        
        if not self.analyzer:
            self.stats_text.clear()
            self.stats_text.add_text("No data loaded. Please load data first.", ['error'])
            self.stats_text.finalize()
            return
        
        # Check if comparison is active
        if self.comparison_active and self.comparison_analyzer:
            # Use new structured comparison view
            main_matches = self._get_all_filtered_matches()
            comparison_matches = self._get_all_filtered_comparison_matches()
            
            # Use structured comparison renderer
            self.rich_text_presenter.render_summary_comparison(
                self.stats_text,
                self.analyzer, main_matches,
                self.comparison_analyzer, comparison_matches
            )
        else:
            # Single player view with rich formatting
            all_matches = self._get_all_filtered_matches()
            self.rich_text_presenter.render_summary(self.stats_text, self.analyzer, all_matches)
    
    def _show_best_times(self):
        """Show best times analysis"""
        self._current_view = 'best_times'
        self.notebook.select(0)  # Stats tab
        
        # Hide segment controls when not viewing segments
        if hasattr(self, 'segment_text_controls_frame'):
            self.segment_text_controls_frame.pack_forget()
        
        if not self.analyzer:
            self.stats_text.clear()
            self.stats_text.add_text("No data loaded. Please load data first.", ['error'])
            self.stats_text.finalize()
            return
        
        # Check if comparison is active
        if self.comparison_active and self.comparison_analyzer:
            self._show_best_times_comparison()
        else:
            self._show_best_times_single()
    
    def _show_best_times_comparison(self):
        """Show best times analysis with comparison"""
        # Get filtered matches for both players
        main_matches = self._get_all_filtered_matches()
        comp_matches = self._get_all_filtered_comparison_matches()
        
        if not main_matches and not comp_matches:
            self.stats_text.clear()
            self.stats_text.add_text("No matches found with the current filters for either player.", ['warning'])
            self.stats_text.finalize()
            return
        
        # Get filter settings
        include_private = self.include_private_var.get()
        season_filter = self.season_var.get()
        seed_filter = self.seed_filter_var.get()
        season_val = int(season_filter) if season_filter != 'All' else None
        seed_val = seed_filter if seed_filter != 'All' else None
        
        # Get season breakdowns for both players
        main_seasons = {}
        comp_seasons = {}
        
        if main_matches:
            main_seasons = self.analyzer.season_breakdown(include_private_rooms=include_private, 
                                                        seed_type_filter=seed_val)
        if comp_matches:
            comp_seasons = self.comparison_analyzer.season_breakdown(include_private_rooms=include_private,
                                                                   seed_type_filter=seed_val)
        
        # Use new structured best times comparison renderer
        self.rich_text_presenter.render_best_times_comparison(
            self.stats_text,
            self.analyzer, main_matches, main_seasons,
            self.comparison_analyzer, comp_matches, comp_seasons
        )
    
    def _show_best_times_single(self):
        """Show best times analysis for single player"""
        # Get all filtered matches
        all_matches = self._get_all_filtered_matches()
        
        if not all_matches:
            self.stats_text.clear()
            self.stats_text.add_text("No matches found with the current filters.", ['warning'])
            self.stats_text.finalize()
            return
        
        # Get season breakdown for text generation
        include_private = self.include_private_var.get()
        season_filter = self.season_var.get()
        seed_filter = self.seed_filter_var.get()
        season_val = int(season_filter) if season_filter != 'All' else None
        seed_val = seed_filter if seed_filter != 'All' else None
        
        seasons = self.analyzer.season_breakdown(include_private_rooms=include_private, 
                                                  seed_type_filter=seed_val)
        
        # Use RichTextPresenter to generate modern best times analysis
        self.rich_text_presenter.render_best_times(self.stats_text, self.analyzer, all_matches, seasons)
    
    def _on_chart_option_change(self):
        """Handle chart option checkbox changes - refresh current chart"""
        # Update chart_options from UI
        self.chart_options['show_rolling_avg'] = self.show_rolling_var.get()
        self.chart_options['show_rolling_median'] = self.show_rolling_median_var.get()
        self.chart_options['show_rolling_std'] = self.show_std_var.get()
        self.chart_options['show_pb_line'] = self.show_pb_var.get()
        self.chart_options['show_grid'] = self.show_grid_var.get()
        
        # Refresh the current chart if applicable
        if self.analyzer and self.notebook.index(self.notebook.select()) == 1:
            # Determine which chart is currently displayed and refresh it
            self._refresh_current_chart()
    
    def _on_match_numbers_toggle(self):
        """Handle match numbers x-axis toggle - refresh current chart"""
        # Refresh the current chart if applicable
        if self.analyzer and self.notebook.index(self.notebook.select()) == 1:
            self._refresh_current_chart()
    
    def _refresh_current_chart(self):
        """Refresh the currently displayed chart"""
        # This will be set by each chart method
        if hasattr(self, '_current_chart_view'):
            # Special handling for segment progression - preserve expanded state
            if self._current_chart_view == '_show_segment_progression' and self.segment_analyzer.is_expanded():
                expanded_seg = self.segment_analyzer.get_expanded_segment()
                if expanded_seg:
                    self.segment_analyzer.show_expanded_segment(expanded_seg)
                return
            
            # Map chart view names to their corresponding methods
            chart_view_map = {
                '_show_progression': lambda: self.chart_views.progression.show(),
                '_show_season_stats': lambda: self.chart_views.season_stats.show(),
                '_show_seed_types': lambda: self.chart_views.seed_types.show(),
                '_show_distribution': lambda: self.chart_views.distribution.show(),
                '_show_segment_progression': lambda: self.segment_analyzer.show_segment_progression(),
            }
            
            view_method = chart_view_map.get(self._current_chart_view)
            if view_method:
                view_method()
    
    def _show_chart_options_dialog(self):
        """Show dialog for advanced chart options"""
        def on_apply(options):
            self.chart_options.update(options)
            
            # Update quick toggle checkboxes
            self.show_rolling_var.set(options['show_rolling_avg'])
            self.show_rolling_median_var.set(options['show_rolling_median'])
            self.show_std_var.set(options['show_rolling_std'])
            self.show_pb_var.set(options['show_pb_line'])
            self.show_grid_var.set(options['show_grid'])
            
            # Update chart builder palette
            self.chart_builder.set_palette(options['color_palette'])
            
            self._refresh_current_chart()
        
        ChartOptionsDialog(
            self.root, 
            self.chart_options, 
            list(ChartBuilder.PALETTES.keys()),
            on_apply
        )
    
    def _set_chart_controls_visible(self, show_splits_toggle: bool, show_back_button: bool = False, 
                                   show_match_numbers_toggle: bool = False):
        """Show or hide chart control options based on current view"""
        if show_splits_toggle:
            self.splits_check.pack(side=tk.LEFT)
        else:
            self.splits_check.pack_forget()
        
        if show_match_numbers_toggle:
            self.match_numbers_check.pack(side=tk.LEFT, padx=(10, 0))
        else:
            self.match_numbers_check.pack_forget()
        
        if show_back_button:
            self.back_btn_frame.pack(fill=tk.X, pady=(0, 5), before=self.chart_controls_frame)
        else:
            self.back_btn_frame.pack_forget()

    def _show_match_browser(self):
        """Show match browser tab"""
        self._current_view = 'match_browser'
        self.notebook.select(2)  # Data tab
        
        # Hide segment controls when not viewing segments
        if hasattr(self, 'segment_text_controls_frame'):
            self.segment_text_controls_frame.pack_forget()
            
        self._populate_match_tree()
    
    def _show_forecast(self):
        """Show all-time best pace forecast view"""
        self._current_view = 'forecast'
        self.notebook.select(3)  # Forecast tab
        
        # Hide segment controls when not viewing segments
        if hasattr(self, 'segment_text_controls_frame'):
            self.segment_text_controls_frame.pack_forget()
            
        self._populate_forecast_tree()
    
    def _populate_forecast_tree(self):
        """Populate the forecast treeview with data"""
        if not self.analyzer or not self.analyzer.matches:
            return
        
        # Clear existing items
        for item in self.forecast_tree.get_children():
            self.forecast_tree.delete(item)
        
        self.forecast_lookup.clear()
        
        # Get filtered matches with segment data
        filter_kwargs = self.filter_manager.build_filter_kwargs()
        filtered_matches = self.analyzer.filter_matches(**filter_kwargs)
        
        # Only include matches with segment data for forecasting
        matches_with_segments = [m for m in filtered_matches if m.has_detailed_data]
        
        if not matches_with_segments:
            # Insert message row
            self.forecast_tree.insert('', 'end', values=('—', '—', 'No matches with segment data', '—', '—', '—'))
            return
        
        # Generate forecast results
        try:
            forecast_results = create_forecast_results(matches_with_segments, 
                                                      rolling_window=self.forecast_rolling_window,
                                                      percentile=self.forecast_percentile)
            
            if not forecast_results:
                self.forecast_tree.insert('', 'end', values=('—', '—', 'No forecastable data', '—', '—', '—'))
                return
            
            # Populate tree with forecast data
            for i, result in enumerate(forecast_results, 1):
                match = result['match']
                forecast_time = result['forecast_time']
                breakdown = result['breakdown']
                is_completed = result['is_completed']
                
                # Format values
                rank = str(i)
                date = match.date_str()
                
                # Format forecasted time
                forecast_time_str = self._format_time(forecast_time)
                
                # Status
                if is_completed:
                    status = "Completed"
                    current_progress = forecast_time_str
                    last_segment = "Run Complete"
                else:
                    status = "Forecasted"
                    if breakdown and 'current_time' in breakdown:
                        current_progress = self._format_time(breakdown['current_time'])
                    else:
                        current_progress = "—"
                    
                    if breakdown and 'last_completed_segment' in breakdown:
                        from ..core.segment_constants import get_segment_display_name
                        last_segment = get_segment_display_name(breakdown['last_completed_segment'])
                    else:
                        last_segment = "—"
                
                # Insert into tree
                item_id = self.forecast_tree.insert('', 'end', values=(
                    rank, date, forecast_time_str, status, current_progress, last_segment
                ))
                
                # Store reference for details
                self.forecast_lookup[item_id] = result
                
        except Exception as e:
            # Handle errors gracefully
            self.forecast_tree.insert('', 'end', values=('Error', '—', str(e), '—', '—', '—'))
            print(f"Forecast error: {e}")  # For debugging
    
    def _on_forecast_select(self, event):
        """Handle forecast tree selection to show details"""
        selection = self.forecast_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        if item_id not in self.forecast_lookup:
            return
        
        result = self.forecast_lookup[item_id]
        match = result['match']
        breakdown = result['breakdown']
        
        # Clear previous content
        self.forecast_detail_text.clear()
        
        if breakdown:
            if breakdown['type'] == 'completed':
                self.forecast_detail_text.add_heading("Completed Run", level=2)
                self.forecast_detail_text.add_text(f"Match ID: {match.id}", [])
                self.forecast_detail_text.add_text(f"Actual completion time: ", [])
                self.forecast_detail_text.add_text(self._format_time(breakdown['actual_time']), ['accent'])
                self.forecast_detail_text.add_line()
                self.forecast_detail_text.add_text("This is a completed run with actual finish time.", [])
                
            else:  # forecasted
                self.forecast_detail_text.add_heading("Forecasted Completion", level=2)
                self.forecast_detail_text.add_text(f"Match ID: {match.id}", [])
                self.forecast_detail_text.add_line()
                
                self.forecast_detail_text.add_text("Current progress: ", [])
                self.forecast_detail_text.add_text(self._format_time(breakdown['current_time']), ['accent'])
                self.forecast_detail_text.add_line()
                
                self.forecast_detail_text.add_text("Forecasted completion: ", [])
                self.forecast_detail_text.add_text(self._format_time(breakdown['forecast_time']), ['success'])
                self.forecast_detail_text.add_line()
                
                remaining_time = breakdown['forecast_time'] - breakdown['current_time']
                self.forecast_detail_text.add_text("Estimated remaining time: ", [])
                self.forecast_detail_text.add_text(self._format_time(remaining_time), ['warning'])
                self.forecast_detail_text.add_line()
                
                # Show completed and forecasted segments
                if breakdown['segments_completed']:
                    self.forecast_detail_text.add_text("Completed segments: ", [])
                    completed_names = [self._get_segment_display_name(seg) for seg in breakdown['segments_completed']]
                    self.forecast_detail_text.add_text(", ".join(completed_names), ['muted'])
                    self.forecast_detail_text.add_line()
                
                if breakdown['segments_forecasted']:
                    self.forecast_detail_text.add_text("Forecasted segments: ", [])
                    forecasted_names = [self._get_segment_display_name(seg) for seg in breakdown['segments_forecasted']]
                    self.forecast_detail_text.add_text(", ".join(forecasted_names), ['muted'])
                    self.forecast_detail_text.add_line()
                
                self.forecast_detail_text.add_line()
                
                # Show rolling window and percentile information
                if 'rolling_window_used' in breakdown:
                    window_used = breakdown['rolling_window_used']
                    percentile_name = self.forecast_percentile_var.get() if hasattr(self, 'forecast_percentile_var') else f"{self.forecast_percentile}th percentile"
                    self.forecast_detail_text.add_text(f"Forecast based on {percentile_name.lower()} of your {window_used} most recent completed runs before this match.", ['muted', 'italic'])
                else:
                    self.forecast_detail_text.add_text("Forecast based on your historical segment performance.", ['muted', 'italic'])
        else:
            self.forecast_detail_text.add_text("No forecast details available", ['muted', 'center'])
        
        self.forecast_detail_text.finalize()

    def _format_time(self, time_ms):
        """Format time in milliseconds to MM:SS.mmm"""
        if time_ms is None:
            return "N/A"
        seconds = time_ms / 1000
        minutes, sec_remainder = divmod(seconds, 60)
        return f'{int(minutes)}:{int(sec_remainder):02d}.{int(time_ms % 1000):03d}'
    
    def _get_segment_display_name(self, segment_key):
        """Get display name for a segment"""
        from ..core.segment_constants import get_segment_display_name
        return get_segment_display_name(segment_key)
    
    def _on_forecast_percentile_change(self, event=None):
        """Handle forecast percentile dropdown change"""
        # Parse percentile from selection
        selection = self.forecast_percentile_var.get()
        percentile_map = {
            "10th (Very Optimistic)": 10.0,
            "25th (Optimistic)": 25.0,
            "50th (Median)": 50.0,
            "75th (Conservative)": 75.0,
            "90th (Very Conservative)": 90.0
        }
        
        self.forecast_percentile = percentile_map.get(selection, 50.0)
        
        # Refresh forecast view if currently active
        if hasattr(self, '_current_view') and self._current_view == 'forecast':
            self._populate_forecast_tree()
    
    def _clear_display(self):
        """Clear all display areas"""
        # Clear text areas
        self.stats_text.clear()
        
        # Clear chart
        self.chart_builder.clear()
        self.chart_builder.finalize()
        
        # Clear match browser
        for item in self.match_tree.get_children():
            self.match_tree.delete(item)
        
        # Clear forecast browser
        if hasattr(self, 'forecast_tree'):
            for item in self.forecast_tree.get_children():
                self.forecast_tree.delete(item)
            if hasattr(self, 'forecast_detail_text'):
                self.forecast_detail_text.clear()
                self.forecast_detail_text.add_text("No data loaded", ['muted', 'center'])
                self.forecast_detail_text.finalize()
        
        # Clear quick stats
        self.quick_stats_text.config(state='normal')
        self.quick_stats_text.delete(1.0, tk.END)
        self.quick_stats_text.insert('1.0', "No data loaded")
        self.quick_stats_text.config(state='disabled')

    def _show_loading_progress(self, loading_text: str = ""):
        """Show progress bar and loading text"""
        self.progress.pack(side=tk.RIGHT, padx=(5, 0))
        self.progress.start()
        
        if loading_text:
            self.loading_text_var.set(loading_text)
            self.loading_text_label.pack(side=tk.RIGHT, padx=(0, 10))
    
    def _update_loading_progress(self, loading_text: str):
        """Update loading progress text"""
        self.loading_text_var.set(loading_text)
        self.root.update_idletasks()
    
    def _hide_loading_progress(self):
        """Hide progress bar and loading text"""
        self.progress.stop()
        self.progress.pack_forget()
        self.loading_text_label.pack_forget()
        self.loading_text_var.set("")


def main():
    root = tk.Tk()
    app = MCSRStatsUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
