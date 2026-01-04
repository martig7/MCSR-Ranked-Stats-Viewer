"""
Chart Views Module
Handles all chart rendering views for MCSR Ranked Stats Browser.
"""

import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
import statistics
from typing import Optional, List, Dict, Any
from .match_info_dialog import show_match_info_dialog


class ChartViewBase:
    """Base class for chart views with common functionality"""
    
    def __init__(self, ui_context):
        """
        Initialize chart view
        
        Args:
            ui_context: Reference to main UI (provides access to analyzer, chart_builder, etc.)
        """
        self.ui = ui_context
    
    def _prepare_chart(self, view_name: str, chart_view_name: str, show_splits_toggle: bool = False):
        """Common chart preparation logic"""
        self.ui._current_view = view_name
        self.ui.notebook.select(1)  # Charts tab
        self.ui._set_chart_controls_visible(show_splits_toggle=show_splits_toggle)
        self.ui._current_chart_view = chart_view_name
        
    def _check_analyzer(self) -> bool:
        """Check if analyzer exists"""
        return self.ui.analyzer is not None
    
    def _on_match_click(self, match):
        """Handle click on a match scatter point to show detailed info"""
        show_match_info_dialog(self.ui.root, match, self.ui.text_presenter)


class ProgressionChart(ChartViewBase):
    """Handles progression chart view"""
    
    def show(self):
        """Show progression chart"""
        self._prepare_chart('progression', '_show_progression')
        
        if not self._check_analyzer():
            return
            
        completed = sorted([m for m in self.ui._get_filtered_matches() if not m.forfeited], 
                          key=lambda x: x.date)
        
        if len(completed) < 10:
            messagebox.showinfo("Info", "Need at least 10 matches for progression chart")
            return
        
        dates = [m.datetime_obj for m in completed]
        times = [m.match_time / 1000 / 60 for m in completed]
        
        # Use ChartBuilder
        cb = self.ui.chart_builder
        cb.clear()
        cb.set_palette(self.ui.chart_options['color_palette'])
        
        ax = cb.get_subplot(1, 1, 1)
        
        # Check if comparison is active
        if self.ui.comparison_active and self.ui.comparison_analyzer:
            self._show_comparison_chart(cb, ax, dates, times, completed)
            return
        
        # Single player view
        self._show_single_chart(cb, ax, dates, times, completed)
    
    def _show_comparison_chart(self, cb, ax, dates, times, completed):
        """Show progression chart with comparison player"""
        # Get comparison data with same filtering as main player
        comp_completed = sorted([m for m in self.ui._get_filtered_comparison_matches() if not m.forfeited], 
                              key=lambda x: x.date)
        
        if len(comp_completed) < 10:
            # Fall back to single player view if comparison doesn't have enough data
            self._show_single_chart(cb, ax, dates, times, completed)
            return
        
        comp_dates = [m.datetime_obj for m in comp_completed]
        comp_times = [m.match_time / 1000 / 60 for m in comp_completed]
        
        # Use palette colors for each player (0 = main, 1 = comparison)
        main_color_idx = 0
        comp_color_idx = 1
        main_color = cb.get_color(main_color_idx)
        comp_color = cb.get_color(comp_color_idx)
        
        # Scatter plots for both players
        cb.plot_scatter(ax, dates, times, 
                       label=f'{self.ui.analyzer.username}',
                       color_index=main_color_idx,
                       size=self.ui.chart_options['point_size'],
                       alpha=0.5, match_data=completed)
        cb.plot_scatter(ax, comp_dates, comp_times,
                       label=f'{self.ui.comparison_analyzer.username}', 
                       color_index=comp_color_idx,
                       size=self.ui.chart_options['point_size'],
                       alpha=0.5, match_data=comp_completed)
        
        window = self.ui.chart_options['rolling_window']
        
        # Rolling standard deviation bands (if enabled) - draw first so avg line is on top
        if self.ui.chart_options['show_rolling_std']:
            cb.add_rolling_std_dev(ax, dates, times, window=window,
                                   color=main_color, fill_alpha=0.15)
            cb.add_rolling_std_dev(ax, comp_dates, comp_times, window=window,
                                   color=comp_color, fill_alpha=0.15)
        
        # Rolling average (if enabled)
        if self.ui.chart_options['show_rolling_avg']:
            cb.add_rolling_average(ax, dates, times, window=window, 
                                  color=main_color,
                                  label=f'{self.ui.analyzer.username} avg',
                                  is_comparison=False)
            cb.add_rolling_average(ax, comp_dates, comp_times, window=window,
                                  color=comp_color,
                                  label=f'{self.ui.comparison_analyzer.username} avg',
                                  is_comparison=True)
        
        # PB lines (if enabled)
        if self.ui.chart_options['show_pb_line']:
            cb.add_pb_line(ax, dates, times, color=main_color, 
                          label=f'{self.ui.analyzer.username} PB')
            cb.add_pb_line(ax, comp_dates, comp_times, color=comp_color,
                          label=f'{self.ui.comparison_analyzer.username} PB')
        
        cb.set_labels(ax, title=f'Progression Comparison: {self.ui.analyzer.username} vs {self.ui.comparison_analyzer.username}',
                    xlabel='Match Date', ylabel='Time (minutes)')
        cb.set_grid(ax, self.ui.chart_options['show_grid'])
        cb.set_legend(ax)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Enable click detection for match details
        cb.enable_match_click_detection(self._on_match_click)
        
        # Enable hover tooltips for rolling averages
        cb.enable_hover_tooltips(self.ui._minutes_to_str)
        
        cb.finalize()
    
    def _show_single_chart(self, cb, ax, dates, times, matches):
        """Show progression chart for single player"""
        # Scatter plot
        cb.plot_scatter(ax, dates, times, 
                       label='Individual matches',
                       size=self.ui.chart_options['point_size'],
                       alpha=0.5, match_data=matches)
        
        # Rolling standard deviation bands (if enabled) - draw first so avg line is on top
        if self.ui.chart_options['show_rolling_std']:
            window = self.ui.chart_options['rolling_window']
            cb.add_rolling_std_dev(ax, dates, times, window=window,
                                   label=f'±1σ ({window}-pt)')
        
        # Rolling average (if enabled)
        if self.ui.chart_options['show_rolling_avg']:
            window = self.ui.chart_options['rolling_window']
            cb.add_rolling_average(ax, dates, times, window=window, 
                                  label=f'{window}-match average',
                                  is_comparison=False)
        
        # PB line (if enabled)
        if self.ui.chart_options['show_pb_line']:
            cb.add_pb_line(ax, dates, times, label='PB')
        
        cb.set_labels(ax, 
                     title=f'{self.ui.analyzer.username} - Performance Progression',
                     xlabel='Date', ylabel='Time (minutes)')
        cb.set_grid(ax, self.ui.chart_options['show_grid'])
        cb.set_legend(ax)
        
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Enable click detection for match details
        cb.enable_match_click_detection(self._on_match_click)
        
        # Enable hover tooltips for rolling averages
        cb.enable_hover_tooltips(self.ui._minutes_to_str)
        
        cb.finalize()


class SeasonStatsChart(ChartViewBase):
    """Handles season statistics chart view"""
    
    def show(self):
        """Show season comparison"""
        self._prepare_chart('season_stats', '_show_season_stats')
        
        if not self._check_analyzer():
            return
        
        include_private = self.ui.include_private_var.get()
        seed_filter = self.ui.seed_filter_var.get()
        seed_val = seed_filter if seed_filter != 'All' else None
        
        seasons_data = self.ui.analyzer.season_breakdown(include_private_rooms=include_private,
                                                       seed_type_filter=seed_val)
        if len(seasons_data) < 1:
            messagebox.showinfo("Info", "No season data available")
            return
        
        # Use ChartBuilder
        cb = self.ui.chart_builder
        cb.clear()
        cb.set_palette(self.ui.chart_options['color_palette'])
        
        # Check if comparison is active
        if self.ui.comparison_active and self.ui.comparison_analyzer:
            self._show_comparison_chart(cb, seasons_data, include_private, seed_val)
        else:
            self._show_single_chart(cb, seasons_data)
    
    def _show_comparison_chart(self, cb, seasons_data, include_private, seed_val):
        """Show season stats chart with comparison player"""
        # Get comparison data with same filtering
        comp_seasons_data = self.ui.comparison_analyzer.season_breakdown(
            include_private_rooms=include_private,
            seed_type_filter=seed_val
        )
        
        if len(comp_seasons_data) < 1:
            # Fall back to single player view if comparison has no data
            self._show_single_chart(cb, seasons_data)
            return
        
        # Get all seasons from both players
        all_seasons = sorted(set(list(seasons_data.keys()) + list(comp_seasons_data.keys())))
        
        axes = cb.create_subplots(2, 2)
        ax1, ax2, ax3, ax4 = axes
        
        # Prepare data arrays for both players
        main_avg_times = []
        comp_avg_times = []
        main_best_times = []
        comp_best_times = []
        main_counts = []
        comp_counts = []
        main_median_times = []
        comp_median_times = []
        
        for season in all_seasons:
            # Main player data
            if season in seasons_data:
                main_avg_times.append(seasons_data[season]['average']/1000/60)
                main_best_times.append(seasons_data[season]['best']/1000/60)
                main_counts.append(seasons_data[season]['matches'])
                main_median_times.append(seasons_data[season]['median']/1000/60)
            else:
                main_avg_times.append(0)
                main_best_times.append(0)
                main_counts.append(0)
                main_median_times.append(0)
            
            # Comparison player data
            if season in comp_seasons_data:
                comp_avg_times.append(comp_seasons_data[season]['average']/1000/60)
                comp_best_times.append(comp_seasons_data[season]['best']/1000/60)
                comp_counts.append(comp_seasons_data[season]['matches'])
                comp_median_times.append(comp_seasons_data[season]['median']/1000/60)
            else:
                comp_avg_times.append(0)
                comp_best_times.append(0)
                comp_counts.append(0)
                comp_median_times.append(0)
        
        # Plot 1: Average times (side-by-side bars)
        self._plot_side_by_side_bars(ax1, all_seasons, main_avg_times, comp_avg_times, cb)
        cb.set_labels(ax1, title='Average Time by Season', xlabel='Season', ylabel='Time (minutes)')
        cb.set_grid(ax1, self.ui.chart_options['show_grid'])
        cb.set_legend(ax1)
        
        # Plot 2: Best times (dual line plot)
        cb.plot_line(ax2, all_seasons, main_best_times, color_index=0, marker='o',
                    linewidth=self.ui.chart_options['line_width'], markersize=8,
                    label=self.ui.analyzer.username)
        cb.plot_line(ax2, all_seasons, comp_best_times, color_index=1, marker='s',
                    linewidth=self.ui.chart_options['line_width'], markersize=8,
                    label=self.ui.comparison_analyzer.username)
        cb.set_labels(ax2, title='Best Time by Season', xlabel='Season', ylabel='Time (minutes)')
        cb.set_grid(ax2, self.ui.chart_options['show_grid'])
        cb.set_legend(ax2)
        
        # Plot 3: Match counts (side-by-side bars)
        self._plot_side_by_side_bars(ax3, all_seasons, main_counts, comp_counts, cb)
        cb.set_labels(ax3, title='Matches by Season', xlabel='Season', ylabel='Count')
        cb.set_grid(ax3, self.ui.chart_options['show_grid'])
        cb.set_legend(ax3)
        
        # Plot 4: Median times (side-by-side bars)
        self._plot_side_by_side_bars(ax4, all_seasons, main_median_times, comp_median_times, cb)
        cb.set_labels(ax4, title='Median Time by Season', xlabel='Season', ylabel='Time (minutes)')
        cb.set_grid(ax4, self.ui.chart_options['show_grid'])
        cb.set_legend(ax4)
        
        cb.set_title(f'Season Analysis Comparison: {self.ui.analyzer.username} vs {self.ui.comparison_analyzer.username}')
        cb.finalize()
    
    def _plot_side_by_side_bars(self, ax, x_labels, data1, data2, cb):
        """Plot side-by-side bars for comparison"""
        import numpy as np
        x = np.arange(len(x_labels))
        width = 0.35
        
        # Plot bars for both players
        bars1 = ax.bar(x - width/2, data1, width, color=cb.get_color(0), 
                      label=self.ui.analyzer.username, alpha=0.8)
        bars2 = ax.bar(x + width/2, data2, width, color=cb.get_color(1), 
                      label=self.ui.comparison_analyzer.username, alpha=0.8)
        
        # Set x-tick labels to season numbers
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels)
        
        # Apply theme styling
        cb._apply_axis_theme(ax)
    
    def _show_single_chart(self, cb, seasons_data):
        """Show season stats chart for single player"""
        seasons = sorted(seasons_data.keys())
        
        axes = cb.create_subplots(2, 2)
        ax1, ax2, ax3, ax4 = axes
        
        # Average times
        avg_times = [seasons_data[s]['average']/1000/60 for s in seasons]
        cb.plot_bar(ax1, seasons, avg_times, color_index=0)
        cb.set_labels(ax1, title='Average Time by Season', xlabel='Season', ylabel='Time (minutes)')
        cb.set_grid(ax1, self.ui.chart_options['show_grid'])
        
        # Best times - line plot
        best_times = [seasons_data[s]['best']/1000/60 for s in seasons]
        cb.plot_line(ax2, seasons, best_times, color='red', marker='o', 
                    linewidth=self.ui.chart_options['line_width'], markersize=8)
        cb.set_labels(ax2, title='Best Time by Season', xlabel='Season', ylabel='Time (minutes)')
        cb.set_grid(ax2, self.ui.chart_options['show_grid'])
        
        # Match counts
        counts = [seasons_data[s]['matches'] for s in seasons]
        cb.plot_bar(ax3, seasons, counts, color_index=1)
        cb.set_labels(ax3, title='Matches by Season', xlabel='Season', ylabel='Count')
        cb.set_grid(ax3, self.ui.chart_options['show_grid'])
        
        # Median times
        median_times = [seasons_data[s]['median']/1000/60 for s in seasons]
        cb.plot_bar(ax4, seasons, median_times, color_index=2)
        cb.set_labels(ax4, title='Median Time by Season', xlabel='Season', ylabel='Time (minutes)')
        cb.set_grid(ax4, self.ui.chart_options['show_grid'])
        
        cb.set_title(f'{self.ui.analyzer.username} - Season Analysis')
        cb.finalize()


class SeedTypesChart(ChartViewBase):
    """Handles seed type analysis chart view"""
    
    def show(self):
        """Show seed type analysis"""
        self._prepare_chart('seed_types', '_show_seed_types')
        
        if not self._check_analyzer():
            return
        
        include_private = self.ui.include_private_var.get()
        season_filter = self.ui.season_var.get()
        season_val = int(season_filter) if season_filter != 'All' else None
        
        seed_types = self.ui.analyzer.seed_type_breakdown(include_private_rooms=include_private,
                                                        season_filter=season_val)
        if len(seed_types) < 1:
            messagebox.showinfo("Info", "No seed type data available")
            return
        
        # Use ChartBuilder
        cb = self.ui.chart_builder
        cb.clear()
        cb.set_palette(self.ui.chart_options['color_palette'])
        
        # Check if comparison is active
        if self.ui.comparison_active and self.ui.comparison_analyzer:
            self._show_comparison_chart(cb, seed_types, include_private, season_val)
        else:
            self._show_single_chart(cb, seed_types)
    
    def _show_comparison_chart(self, cb, seed_types, include_private, season_val):
        """Show seed type chart with comparison player"""
        # Get comparison data with same filtering
        comp_seed_types = self.ui.comparison_analyzer.seed_type_breakdown(
            include_private_rooms=include_private,
            season_filter=season_val
        )
        
        if len(comp_seed_types) < 1:
            # Fall back to single player view if comparison has no data
            self._show_single_chart(cb, seed_types)
            return
        
        # Get all seed types from both players, filtering out None values
        all_seeds_set = set(list(seed_types.keys()) + list(comp_seed_types.keys()))
        all_seeds_set.discard(None)  # Remove None if present
        all_seeds = sorted(all_seeds_set)
        
        axes = cb.create_subplots(2, 2)
        ax1, ax2, ax3, ax4 = axes
        
        # Prepare data arrays for both players
        main_avg_times = []
        comp_avg_times = []
        main_best_times = []
        comp_best_times = []
        main_counts = []
        comp_counts = []
        
        for seed in all_seeds:
            # Main player data
            if seed in seed_types:
                main_avg_times.append(seed_types[seed]['average']/1000/60)
                main_best_times.append(seed_types[seed]['best']/1000/60)
                main_counts.append(seed_types[seed]['matches'])
            else:
                main_avg_times.append(0)
                main_best_times.append(0)
                main_counts.append(0)
            
            # Comparison player data
            if seed in comp_seed_types:
                comp_avg_times.append(comp_seed_types[seed]['average']/1000/60)
                comp_best_times.append(comp_seed_types[seed]['best']/1000/60)
                comp_counts.append(comp_seed_types[seed]['matches'])
            else:
                comp_avg_times.append(0)
                comp_best_times.append(0)
                comp_counts.append(0)
        
        # Plot 1: Average times (side-by-side bars)
        self._plot_seed_comparison_bars(ax1, all_seeds, main_avg_times, comp_avg_times, cb)
        cb.set_labels(ax1, title='Average Time by Seed', ylabel='Time (minutes)')
        cb.set_grid(ax1, self.ui.chart_options['show_grid'])
        cb.set_legend(ax1)
        
        # Plot 2: Best times (side-by-side bars)
        self._plot_seed_comparison_bars(ax2, all_seeds, main_best_times, comp_best_times, cb)
        cb.set_labels(ax2, title='Best Time by Seed', ylabel='Time (minutes)')
        cb.set_grid(ax2, self.ui.chart_options['show_grid'])
        cb.set_legend(ax2)
        
        # Plot 3: Match counts (side-by-side bars)
        self._plot_seed_comparison_bars(ax3, all_seeds, main_counts, comp_counts, cb)
        cb.set_labels(ax3, title='Matches by Seed', ylabel='Count')
        cb.set_grid(ax3, self.ui.chart_options['show_grid'])
        cb.set_legend(ax3)
        
        # Plot 4: Distribution pie charts (side by side)
        ax4.clear()
        ax4.axis('off')
        
        # Create two sub-axes for pie charts
        from matplotlib.gridspec import GridSpecFromSubplotSpec
        gs = GridSpecFromSubplotSpec(1, 2, ax4.get_subplotspec(), wspace=0.3)
        ax4a = ax4.figure.add_subplot(gs[0])
        ax4b = ax4.figure.add_subplot(gs[1])
        
        # Main player pie chart
        if any(main_counts):
            cb.plot_pie(ax4a, main_counts, all_seeds, autopct='%1.1f%%')
            ax4a.set_title(f'{self.ui.analyzer.username}', fontsize=10, color='white')
        
        # Comparison player pie chart
        if any(comp_counts):
            cb.plot_pie(ax4b, comp_counts, all_seeds, autopct='%1.1f%%')
            ax4b.set_title(f'{self.ui.comparison_analyzer.username}', fontsize=10, color='white')
        
        cb.set_title(f'Seed Type Analysis Comparison: {self.ui.analyzer.username} vs {self.ui.comparison_analyzer.username}')
        cb.finalize()
    
    def _plot_seed_comparison_bars(self, ax, seed_labels, data1, data2, cb):
        """Plot side-by-side bars for seed comparison"""
        import numpy as np
        x = np.arange(len(seed_labels))
        width = 0.35
        
        # Plot bars for both players
        bars1 = ax.bar(x - width/2, data1, width, color=cb.get_color(0), 
                      label=self.ui.analyzer.username, alpha=0.8)
        bars2 = ax.bar(x + width/2, data2, width, color=cb.get_color(1), 
                      label=self.ui.comparison_analyzer.username, alpha=0.8)
        
        # Set x-tick labels to seed names with rotation
        cb.set_xticks(ax, x, seed_labels, rotation=45, ha='right')
        
        # Apply theme styling
        cb._apply_axis_theme(ax)
    
    def _show_single_chart(self, cb, seed_types):
        """Show seed type chart for single player"""
        seeds = list(seed_types.keys())
        
        axes = cb.create_subplots(2, 2)
        ax1, ax2, ax3, ax4 = axes
        
        # Generate colors for each seed type
        colors = [cb.get_color(i) for i in range(len(seeds))]
        
        # Average times
        avg_times = [seed_types[s]['average']/1000/60 for s in seeds]
        cb.plot_bar(ax1, range(len(seeds)), avg_times, colors=colors)
        cb.set_labels(ax1, title='Average Time by Seed', ylabel='Time (minutes)')
        cb.set_xticks(ax1, range(len(seeds)), seeds, rotation=45, ha='right')
        cb.set_grid(ax1, self.ui.chart_options['show_grid'])
        
        # Best times
        best_times = [seed_types[s]['best']/1000/60 for s in seeds]
        cb.plot_bar(ax2, range(len(seeds)), best_times, colors=colors)
        cb.set_labels(ax2, title='Best Time by Seed', ylabel='Time (minutes)')
        cb.set_xticks(ax2, range(len(seeds)), seeds, rotation=45, ha='right')
        cb.set_grid(ax2, self.ui.chart_options['show_grid'])
        
        # Match counts
        counts = [seed_types[s]['matches'] for s in seeds]
        cb.plot_bar(ax3, range(len(seeds)), counts, colors=colors)
        cb.set_labels(ax3, title='Matches by Seed', ylabel='Count')
        cb.set_xticks(ax3, range(len(seeds)), seeds, rotation=45, ha='right')
        cb.set_grid(ax3, self.ui.chart_options['show_grid'])
        
        # Pie chart
        cb.plot_pie(ax4, counts, seeds, colors=colors)
        cb.set_labels(ax4, title='Distribution')
        
        cb.set_title(f'{self.ui.analyzer.username} - Seed Type Analysis')
        cb.finalize()


class DistributionChart(ChartViewBase):
    """Handles time distribution chart view"""
    
    def show(self):
        """Show time distribution chart"""
        self._prepare_chart('distribution', '_show_distribution')
        
        if not self._check_analyzer():
            return
            
        completed = [m for m in self.ui._get_filtered_matches() if not m.forfeited]
        
        if len(completed) < 10:
            messagebox.showinfo("Info", "Need at least 10 matches for distribution analysis")
            return
            
        times_minutes = [m.match_time/1000/60 for m in completed]
        
        # Use ChartBuilder
        cb = self.ui.chart_builder
        cb.clear()
        cb.set_palette(self.ui.chart_options['color_palette'])
        
        axes = cb.create_subplots(2, 2)
        ax1, ax2, ax3, ax4 = axes
        
        # Histogram
        cb.plot_histogram(ax1, times_minutes, bins=20, color_index=0)
        mean_time = statistics.mean(times_minutes)
        median_time = statistics.median(times_minutes)
        cb.add_vertical_line(ax1, mean_time, color='red', linestyle='--', 
                            label=f'Mean: {self.ui._minutes_to_str(mean_time)}')
        cb.add_vertical_line(ax1, median_time, color='yellow', linestyle='--',
                            label=f'Median: {self.ui._minutes_to_str(median_time)}')
        cb.set_labels(ax1, title='Time Distribution', xlabel='Time (minutes)', ylabel='Frequency')
        cb.set_legend(ax1)
        cb.set_grid(ax1, self.ui.chart_options['show_grid'])
        
        # Cumulative distribution
        sorted_times = sorted(times_minutes)
        y_vals = [i/len(sorted_times) for i in range(len(sorted_times))]
        cb.plot_line(ax2, sorted_times, y_vals, color='#2196F3', 
                    linewidth=self.ui.chart_options['line_width'])
        cb.set_labels(ax2, title='Cumulative Distribution', xlabel='Time (minutes)', ylabel='Probability')
        cb.set_grid(ax2, self.ui.chart_options['show_grid'])
        
        # Box plot by season
        seasons_data = {}
        for m in completed:
            if m.season not in seasons_data:
                seasons_data[m.season] = []
            seasons_data[m.season].append(m.match_time/1000/60)
            
        if seasons_data:
            seasons = sorted(seasons_data.keys())
            data = [seasons_data[s] for s in seasons]
            cb.plot_box(ax3, data, [f'S{s}' for s in seasons], color_index=0)
            cb.set_labels(ax3, title='Distribution by Season', xlabel='Season', ylabel='Time (minutes)')
            cb.set_grid(ax3, self.ui.chart_options['show_grid'])
            
        # PB progression (area chart)
        sorted_matches = sorted(completed, key=lambda x: x.date)
        pb_progression = []
        current_pb = float('inf')
        for m in sorted_matches:
            if m.match_time < current_pb:
                current_pb = m.match_time
            pb_progression.append(current_pb/1000/60)
        
        cb.plot_area(ax4, range(len(pb_progression)), pb_progression, color='green',
                    linewidth=self.ui.chart_options['line_width'])
        cb.set_labels(ax4, title='Personal Best Progression', xlabel='Match Number', ylabel='PB (minutes)')
        cb.set_grid(ax4, self.ui.chart_options['show_grid'])
        
        cb.set_title(f'{self.ui.analyzer.username} - Time Distribution Analysis')
        cb.finalize()


# COMMENTED OUT - ELO feature not working properly due to API data issues
# The entire EloChart class has been disabled due to API data structure issues
# where historical ELO progression cannot be accurately calculated.

if False:  # Disabled ELO chart functionality
    class EloChart(ChartViewBase):
        """Handles ELO progression chart view"""
    
    def show(self):
        """Show ELO progression chart with comparison support"""
        self._prepare_chart('elo_progression', '_show_elo_progression')
        
        if not self._check_analyzer():
            return
        
        # Get filtered matches for main player
        filtered_matches = self.ui._get_all_filtered_matches()
        elo_progression = self.ui.analyzer.get_elo_progression(filtered_matches)
        
        if not elo_progression:
            messagebox.showinfo("Info", "No ELO data available for the selected filters.")
            return
        
        # Use ChartBuilder
        cb = self.ui.chart_builder
        cb.clear()
        cb.set_palette(self.ui.chart_options['color_palette'])
        
        # Check if comparison is active
        if self.ui.comparison_active and self.ui.comparison_analyzer:
            self._show_comparison_chart(cb, elo_progression)
        else:
            self._show_single_chart(cb, elo_progression)
    
    def _show_single_chart(self, cb, elo_progression):
        """Show single player ELO chart"""
        ax = cb.get_subplot(1, 1, 1)
        
        dates = [point['date'] for point in elo_progression]
        elo_values = [point['elo_after'] for point in elo_progression]
        
        # Main ELO line chart
        cb.plot_line(ax, dates, elo_values, 
                     label=f'{self.ui.analyzer.username} ELO',
                     color_index=0, linewidth=2)
        
        # Add ELO change markers (wins/losses with different colors)
        win_dates = []
        win_elos = []
        loss_dates = []
        loss_elos = []
        
        for point in elo_progression:
            if point['elo_change'] and point['elo_change'] > 0:
                win_dates.append(point['date'])
                win_elos.append(point['elo_after'])
            elif point['elo_change'] and point['elo_change'] < 0:
                loss_dates.append(point['date'])
                loss_elos.append(point['elo_after'])
        
        # Plot win/loss markers
        if win_dates:
            cb.plot_scatter(ax, win_dates, win_elos, 
                           color='green', marker='^', size=30, alpha=0.7,
                           label='Wins')
        if loss_dates:
            cb.plot_scatter(ax, loss_dates, loss_elos, 
                           color='red', marker='v', size=30, alpha=0.7,
                           label='Losses')
        
        # Add rolling average if enabled
        if self.ui.chart_options['show_rolling_avg'] and len(elo_values) >= 5:
            window = min(self.ui.chart_options['rolling_window'], len(elo_values))
            cb.add_rolling_average(ax, dates, elo_values, 
                                  window=window, color_index=1,
                                  label=f'{window}-match ELO average')
        
        # Set labels and formatting
        cb.set_labels(ax, title=f'{self.ui.analyzer.username} - ELO Progression',
                     xlabel='Date', ylabel='ELO Rating')
        cb.set_grid(ax, self.ui.chart_options['show_grid'])
        
        # Format date axis for better readability
        self._format_date_axis(cb, ax, dates)
        
        # Add stats annotation
        if elo_values:
            current_elo = elo_values[-1]
            peak_elo = max(elo_values)
            lowest_elo = min(elo_values)
            elo_range = peak_elo - lowest_elo
            
            stats_text = f'Current: {current_elo}\nPeak: {peak_elo}\nLowest: {lowest_elo}\nRange: {elo_range}'
            cb.add_annotation(ax, stats_text, x=0.02, y=0.98, fontsize=10)
        
        cb.set_legend(ax)
        cb.finalize()
    
    def _show_comparison_chart(self, cb, main_elo_progression):
        """Show comparison chart with both players"""
        # Get comparison player ELO data
        comp_matches = self.ui.comparison_handler.get_all_filtered_matches()
        comp_elo_progression = self.ui.comparison_analyzer.get_elo_progression(comp_matches)
        
        if not comp_elo_progression:
            # Fall back to single chart if no comparison data
            self._show_single_chart(cb, main_elo_progression)
            return
        
        ax = cb.get_subplot(1, 1, 1)
        
        # Main player data
        main_dates = [point['date'] for point in main_elo_progression]
        main_elo_values = [point['elo_after'] for point in main_elo_progression]
        
        # Comparison player data
        comp_dates = [point['date'] for point in comp_elo_progression]
        comp_elo_values = [point['elo_after'] for point in comp_elo_progression]
        
        # Plot both ELO progressions
        cb.plot_line(ax, main_dates, main_elo_values,
                     label=f'{self.ui.analyzer.username} ELO',
                     color_index=0, linewidth=2)
        cb.plot_line(ax, comp_dates, comp_elo_values,
                     label=f'{self.ui.comparison_analyzer.username} ELO',
                     color_index=1, linewidth=2)
        
        # Add rolling averages if enabled
        if self.ui.chart_options['show_rolling_avg']:
            if len(main_elo_values) >= 5:
                window = min(self.ui.chart_options['rolling_window'], len(main_elo_values))
                cb.add_rolling_average(ax, main_dates, main_elo_values,
                                      window=window, color_index=0, alpha=0.6,
                                      label=f'{self.ui.analyzer.username} {window}-match avg')
            
            if len(comp_elo_values) >= 5:
                comp_window = min(self.ui.chart_options['rolling_window'], len(comp_elo_values))
                cb.add_rolling_average(ax, comp_dates, comp_elo_values,
                                      window=comp_window, color_index=1, alpha=0.6,
                                      label=f'{self.ui.comparison_analyzer.username} {comp_window}-match avg')
        
        # Set labels and formatting
        cb.set_labels(ax, title=f'ELO Progression Comparison',
                     xlabel='Date', ylabel='ELO Rating')
        cb.set_grid(ax, self.ui.chart_options['show_grid'])
        
        # Format date axis combining both datasets
        all_dates = sorted(set(main_dates + comp_dates))
        self._format_date_axis(cb, ax, all_dates)
        
        # Add comparison stats
        if main_elo_values and comp_elo_values:
            main_current = main_elo_values[-1]
            comp_current = comp_elo_values[-1]
            main_peak = max(main_elo_values)
            comp_peak = max(comp_elo_values)
            
            stats_text = (f'{self.ui.analyzer.username}:\n'
                         f'  Current: {main_current}\n'
                         f'  Peak: {main_peak}\n\n'
                         f'{self.ui.comparison_analyzer.username}:\n'
                         f'  Current: {comp_current}\n'
                         f'  Peak: {comp_peak}')
            
            cb.add_annotation(ax, stats_text, x=0.02, y=0.98, fontsize=9)
        
        cb.set_legend(ax)
        cb.finalize()
    
    def _format_date_axis(self, cb, ax, dates):
        """Format date axis for better readability"""
        if len(dates) > 0:
            max_ticks = 8
            if len(dates) > max_ticks:
                # Select evenly spaced dates
                step = max(1, len(dates) // max_ticks)
                tick_indices = list(range(0, len(dates), step))
                if len(dates) - 1 not in tick_indices:
                    tick_indices.append(len(dates) - 1)
                
                tick_dates = [dates[i] for i in tick_indices]
                tick_labels = [d.strftime('%m/%d/%y') for d in tick_dates]
                cb.set_xticks(ax, tick_dates, tick_labels, rotation=30, ha='right')
            else:
                # For few data points, use all dates
                tick_labels = [d.strftime('%m/%d/%y') for d in dates]
                cb.set_xticks(ax, dates, tick_labels, rotation=30, ha='right')


# END OF COMMENTED OUT ELO CHART CLASS

class ChartViewManager:
    """Manages all chart views"""
    
    def __init__(self, ui_context):
        """Initialize all chart views"""
        self.progression = ProgressionChart(ui_context)
        self.season_stats = SeasonStatsChart(ui_context)
        self.seed_types = SeedTypesChart(ui_context)
        self.distribution = DistributionChart(ui_context)
        # self.elo = EloChart(ui_context)  # Commented out - ELO feature not working
