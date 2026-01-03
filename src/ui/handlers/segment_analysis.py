"""
Segment Analysis Module
Handles all segment-related views and interactions for MCSR Ranked Stats Browser.
"""

import tkinter as tk
from tkinter import messagebox
import statistics
from typing import Optional, Dict, List, Any
from ...visualization.match_info_dialog import show_match_info_dialog


class SegmentAnalyzer:
    """Manages segment analysis views and state"""
    
    def __init__(self, ui_context):
        """
        Initialize segment analyzer
        
        Args:
            ui_context: Reference to main UI (provides access to analyzer, chart_builder, etc.)
        """
        self.ui = ui_context
        
        # Segment expansion state
        self._segment_expanded = False
        self._expanded_segment = None
        self._segment_axes_map = {}  # Maps axes to segment names
        self._cached_segment_data = {}  # Cached data for expanded view
        self._segment_display = {}  # Display names for segments
        self._available_segments = []  # Segments with enough data
        
    def show_segments_text(self):
        """Show segment analysis in text tab"""
        self.ui._current_view = 'segments'
        self.ui.notebook.select(0)  # Stats tab
        self.ui.stats_text.delete('1.0', tk.END)
        
        if not self.ui.analyzer:
            return
        
        # Get all filtered matches with segment data (including incomplete runs)
        filtered_matches = self.ui._get_all_filtered_matches()
        detailed_matches = [m for m in filtered_matches if m.has_detailed_data]
        
        # Show filter info
        season_filter = self.ui.season_var.get()
        seed_filter = self.ui.seed_filter_var.get()
        filter_text = ""
        if season_filter != 'All' or seed_filter != 'All':
            filters = []
            if season_filter != 'All':
                filters.append(f"Season {season_filter}")
            if seed_filter != 'All':
                filters.append(f"Seed: {seed_filter}")
            filter_text = f"  Filters: {', '.join(filters)}\n"
        
        # Calculate segment stats for filtered matches using analyzer methods
        segment_stats = self.ui.analyzer.get_segment_stats(detailed_matches)
        split_stats = self.ui.analyzer.get_split_stats(detailed_matches)
        
        # Check for comparison data
        if self.ui.comparison_active:
            comparison_matches = self.ui._get_all_filtered_comparison_matches()
            comparison_detailed = [m for m in comparison_matches if m.has_detailed_data]
            comparison_segment_stats = self.ui.comparison_analyzer.get_segment_stats(comparison_detailed)
            comparison_split_stats = self.ui.comparison_analyzer.get_split_stats(comparison_detailed)
            
            # Use side-by-side comparison format
            main_text = self.ui.text_presenter.generate_segment_analysis_text(
                self.ui.analyzer, filtered_matches, segment_stats, split_stats, filter_text
            )
            comparison_text = self.ui.text_presenter.generate_segment_analysis_text(
                self.ui.comparison_analyzer, comparison_matches, comparison_segment_stats, comparison_split_stats, filter_text
            )
            
            text = self.ui.text_presenter.format_side_by_side_text(main_text, comparison_text)
        else:
            # Use TextPresenter to generate segment analysis
            text = self.ui.text_presenter.generate_segment_analysis_text(
                self.ui.analyzer, filtered_matches, segment_stats, split_stats, filter_text
            )
        
        self.ui.stats_text.insert('1.0', text)
    
    def show_segment_progression(self):
        """Show segment progression over time with individual charts"""
        self.ui._current_view = 'segment_progression'
        self.ui.notebook.select(1)  # Charts tab
        self.ui._set_chart_controls_visible(show_splits_toggle=True)
        self.ui._current_chart_view = '_show_segment_progression'
        
        # Reset expansion state when showing grid view
        self._segment_expanded = False
        self._expanded_segment = None
        self._segment_axes_map = {}
        
        if not self.ui.analyzer:
            return
        
        # Get all filtered matches with segment data (including incomplete runs)
        filtered_matches = self.ui._get_all_filtered_matches()
        detailed_matches = [m for m in filtered_matches if m.has_detailed_data]
        
        # Also get all unfiltered matches for rolling average calculation
        all_detailed_matches = [m for m in self.ui.analyzer.matches if m.has_detailed_data]
        
        if len(detailed_matches) < 5:
            messagebox.showinfo("Info", "Need at least 5 matches with segment data for progression analysis.\n\nClick 'Fetch Segment Data' to download timeline data.")
            return
        
        # Sort by date
        detailed_matches.sort(key=lambda x: x.date)
        
        # Check if we should show split times or absolute times
        show_splits = self.ui.show_splits_var.get() if self.ui.show_splits_var else False
        
        segment_names = ['nether_enter', 'bastion_enter', 'fortress_enter', 'blind_portal', 
                        'stronghold_enter', 'end_enter', 'game_end']
        
        # Display names differ based on mode
        if show_splits:
            segment_display = {
                'nether_enter': 'Overworld',
                'bastion_enter': 'Nether → Bastion',
                'fortress_enter': 'Bastion → Fortress',
                'blind_portal': 'Structures → Blind',
                'stronghold_enter': 'Blind → Stronghold',
                'end_enter': 'Stronghold → End',
                'game_end': 'End → Finish'
            }
        else:
            segment_display = {
                'nether_enter': 'Nether Enter',
                'bastion_enter': 'Bastion',
                'fortress_enter': 'Fortress',
                'blind_portal': 'Blind Portal',
                'stronghold_enter': 'Stronghold',
                'end_enter': 'End Enter',
                'game_end': 'Completion'
            }
        
        # Cache segment display names for expanded view
        self._segment_display = segment_display
        
        # Find which segments have enough data and cache data for each
        available_segments = []
        self._cached_segment_data = {}
        self._cached_full_segment_data = {}  # Cache full dataset for rolling calculations
        
        # Also cache comparison data if available
        comparison_data = {}
        comparison_full_data = {}
        if self.ui.comparison_active:
            comparison_matches = self.ui._get_all_filtered_comparison_matches()
            comparison_detailed = [m for m in comparison_matches if m.has_detailed_data]
            comparison_detailed.sort(key=lambda x: x.date)
            
            # Get all comparison matches for rolling calculations
            all_comparison_matches = [m for m in self.ui.comparison_analyzer.matches if m.has_detailed_data]
            all_comparison_matches.sort(key=lambda x: x.date)
        
        for seg in segment_names:
            # Collect filtered data (for display)
            times = []
            dates = []
            matches = []  # Store match objects for click detection
            for match in detailed_matches:
                if seg in match.segments:
                    # For game_end, only include if user actually completed the run
                    if seg == 'game_end' and not match.user_completed:
                        continue
                    
                    # For incomplete matches (draw/forfeit), skip the last segment for splits
                    if show_splits and (match.is_draw or match.forfeited):
                        last_segment = None
                        for s in segment_names:
                            if s in match.segments:
                                last_segment = s
                        if seg == last_segment:
                            continue
                    
                    if show_splits:
                        time_val = match.segments[seg]['split_time'] / 1000 / 60
                    else:
                        time_val = match.segments[seg]['absolute_time'] / 1000 / 60
                    times.append(time_val)
                    dates.append(match.datetime_obj)
                    matches.append(match)
            
            # Collect full unfiltered data (for rolling calculations)
            full_times = []
            full_dates = []
            for match in all_detailed_matches:
                if seg in match.segments:
                    # Same filtering logic but on all matches
                    if seg == 'game_end' and not match.user_completed:
                        continue
                    if show_splits and (match.is_draw or match.forfeited):
                        last_segment = None
                        for s in segment_names:
                            if s in match.segments:
                                last_segment = s
                        if seg == last_segment:
                            continue
                    
                    if show_splits:
                        time_val = match.segments[seg]['split_time'] / 1000 / 60
                    else:
                        time_val = match.segments[seg]['absolute_time'] / 1000 / 60
                    full_times.append(time_val)
                    full_dates.append(match.datetime_obj)
            
            # Cache comparison data for this segment if available
            comp_times = []
            comp_dates = []
            comp_matches = []
            comp_full_times = []
            comp_full_dates = []
            if self.ui.comparison_active:
                # Filtered comparison data
                for match in comparison_detailed:
                    if seg in match.segments:
                        # Same filtering logic as main player
                        if seg == 'game_end' and not match.user_completed:
                            continue
                        if show_splits and (match.is_draw or match.forfeited):
                            last_segment = None
                            for s in segment_names:
                                if s in match.segments:
                                    last_segment = s
                            if seg == last_segment:
                                continue
                        
                        if show_splits:
                            time_val = match.segments[seg]['split_time'] / 1000 / 60
                        else:
                            time_val = match.segments[seg]['absolute_time'] / 1000 / 60
                        comp_times.append(time_val)
                        comp_dates.append(match.datetime_obj)
                        comp_matches.append(match)
                
                # Full comparison data
                for match in all_comparison_matches:
                    if seg in match.segments:
                        # Same filtering logic
                        if seg == 'game_end' and not match.user_completed:
                            continue
                        if show_splits and (match.is_draw or match.forfeited):
                            last_segment = None
                            for s in segment_names:
                                if s in match.segments:
                                    last_segment = s
                            if seg == last_segment:
                                continue
                        
                        if show_splits:
                            time_val = match.segments[seg]['split_time'] / 1000 / 60
                        else:
                            time_val = match.segments[seg]['absolute_time'] / 1000 / 60
                        comp_full_times.append(time_val)
                        comp_full_dates.append(match.datetime_obj)
            
            if len(times) >= 5:
                available_segments.append(seg)
                self._cached_segment_data[seg] = {'times': times, 'dates': dates, 'matches': matches}
                self._cached_full_segment_data[seg] = {'times': full_times, 'dates': full_dates}
                if comp_times and len(comp_times) >= 3:  # Lower threshold for comparison
                    comparison_data[seg] = {'times': comp_times, 'dates': comp_dates, 'matches': comp_matches}
                if comp_full_times and len(comp_full_times) >= 3:
                    comparison_full_data[seg] = {'times': comp_full_times, 'dates': comp_full_dates}
        
        if not available_segments:
            messagebox.showinfo("Info", "Not enough segment data available")
            return
        
        # Store available segments and comparison data for later use
        self._available_segments = available_segments
        self._cached_comparison_data = comparison_data
        self._cached_comparison_full_data = comparison_full_data
        
        # Create grid of subplots based on available segments
        n_segments = len(available_segments)
        if n_segments <= 3:
            rows, cols = 1, n_segments
        elif n_segments <= 6:
            rows, cols = 2, 3
        else:
            rows, cols = 3, 3
        
        # Use ChartBuilder
        cb = self.ui.chart_builder
        cb.clear()
        cb.set_palette(self.ui.chart_options['color_palette'])
        
        for idx, segment in enumerate(available_segments):
            ax = cb.get_subplot(rows, cols, idx + 1)
            
            # Map this axes to the segment for click handling
            self._segment_axes_map[ax] = segment
            
            # Get cached data for this segment
            times = self._cached_segment_data[segment]['times']
            dates = self._cached_segment_data[segment]['dates']
            matches = self._cached_segment_data[segment]['matches']
            
            # Get full data for rolling calculations
            full_times = self._cached_full_segment_data[segment]['times']
            full_dates = self._cached_full_segment_data[segment]['dates']
            
            # Use 4 distinct colors per chart: main scatter, main line, comp scatter, comp line
            # Spread colors across palette to avoid similar adjacent colors
            base_color_offset = (idx * 4) % len(cb.palette)
            main_scatter_color_idx = base_color_offset
            main_line_color_idx = (base_color_offset + 1) % len(cb.palette)
            comp_scatter_color_idx = (base_color_offset + 2) % len(cb.palette)
            comp_line_color_idx = (base_color_offset + 3) % len(cb.palette)
            
            # Main player scatter plot (circles)
            cb.plot_scatter(ax, dates, times, 
                           size=self.ui.chart_options['point_size'] * 0.8,
                           alpha=0.6, color_index=main_scatter_color_idx, marker='o',
                           match_data=matches)
            
            # Add comparison data if available
            if segment in comparison_data:
                comp_times = comparison_data[segment]['times']
                comp_dates = comparison_data[segment]['dates']
                comp_matches = comparison_data[segment]['matches']
                # Plot comparison data with circles but different color and smaller size
                cb.plot_scatter(ax, comp_dates, comp_times,
                               size=self.ui.chart_options['point_size'] * 0.6,
                               alpha=0.5, color_index=comp_scatter_color_idx, marker='o',
                               match_data=comp_matches)
            
            # Rolling std dev bands (if enabled) - draw first so avg line is on top
            if self.ui.chart_options['show_rolling_std'] and len(times) >= 1:
                window = self.ui.chart_options['rolling_window']
                cb.add_rolling_std_dev(ax, dates, times,
                                       window=window, label=None, color_index=main_line_color_idx,
                                       full_x_data=full_dates, full_y_data=full_times)
            
            # Rolling average (if enabled)
            if self.ui.chart_options['show_rolling_avg'] and len(times) >= 1:
                window = self.ui.chart_options['rolling_window']
                cb.add_rolling_average(ax, dates, times, 
                                      window=window, label=None, color_index=main_line_color_idx,
                                      full_x_data=full_dates, full_y_data=full_times)
            
            # PB line (if enabled)
            if self.ui.chart_options['show_pb_line']:
                cb.add_pb_line(ax, dates, times, label=None, color_index=main_line_color_idx)
            
            # Add comparison player statistics if available
            if segment in comparison_data:
                comp_times = comparison_data[segment]['times']
                comp_dates = comparison_data[segment]['dates']
                
                # Get full comparison data for rolling calculations
                comp_full_times = comparison_full_data.get(segment, {}).get('times', [])
                comp_full_dates = comparison_full_data.get(segment, {}).get('dates', [])
                
                # Comparison rolling std dev (if enabled)
                if self.ui.chart_options['show_rolling_std'] and len(comp_times) >= 1:
                    comp_window = self.ui.chart_options['rolling_window']
                    cb.add_rolling_std_dev(ax, comp_dates, comp_times,
                                           window=comp_window, label=None, alpha=0.2, 
                                           color_index=comp_line_color_idx,
                                           full_x_data=comp_full_dates, full_y_data=comp_full_times)
                
                # Comparison rolling average (if enabled)
                if self.ui.chart_options['show_rolling_avg'] and len(comp_times) >= 1:
                    comp_window = self.ui.chart_options['rolling_window']
                    cb.add_rolling_average(ax, comp_dates, comp_times, 
                                          window=comp_window, label=None, color_index=comp_line_color_idx,
                                          full_x_data=comp_full_dates, full_y_data=comp_full_times)
                
                # Comparison PB line (if enabled)
                if self.ui.chart_options['show_pb_line']:
                    cb.add_pb_line(ax, comp_dates, comp_times, label=None, color_index=comp_line_color_idx)
            
            y_label = 'Split (min)' if show_splits else 'Time (min)'
            cb.set_labels(ax, title=segment_display[segment], 
                         xlabel='Date', ylabel=y_label,
                         title_fontsize=10, label_fontsize=8)
            cb.set_grid(ax, self.ui.chart_options['show_grid'])
            
            # Format date axis for better readability in small charts
            if len(dates) > 0:
                # Limit to max 4 ticks on small charts
                max_ticks = 4
                if len(dates) > max_ticks:
                    # Select evenly spaced dates
                    step = max(1, len(dates) // max_ticks)
                    tick_indices = list(range(0, len(dates), step))
                    if len(dates) - 1 not in tick_indices:
                        tick_indices.append(len(dates) - 1)
                    
                    tick_dates = [dates[i] for i in tick_indices]
                    tick_labels = [d.strftime('%m/%d') for d in tick_dates]
                    cb.set_xticks(ax, tick_dates, tick_labels, rotation=45, ha='right')
                else:
                    # For few data points, use all dates
                    tick_labels = [d.strftime('%m/%d') for d in dates]
                    cb.set_xticks(ax, dates, tick_labels, rotation=45, ha='right')
            
            # Add stats annotation
            avg_time = statistics.mean(times)
            best_time = min(times)
            label = 'Best' if show_splits else 'PB'
            stats_text = f'Avg: {self.ui._minutes_to_str(avg_time)}\n{label}: {self.ui._minutes_to_str(best_time)}'
            
            # Add comparison stats if available
            if segment in comparison_data:
                comp_times = comparison_data[segment]['times']
                comp_avg = statistics.mean(comp_times)
                comp_best = min(comp_times)
                stats_text += f'\n\nComp Avg: {self.ui._minutes_to_str(comp_avg)}\nComp {label}: {self.ui._minutes_to_str(comp_best)}'
            
            cb.add_annotation(ax, stats_text, x=0.02, y=0.98, fontsize=6)
            
            # Add hint to click for expansion
            ax.text(0.98, 0.02, 'Click to expand', transform=ax.transAxes,
                   fontsize=7, color='gray', alpha=0.7, ha='right', va='bottom')
        
        # Build title with filter info
        mode_str = 'Split Times' if show_splits else 'Absolute Times'
        title = f'{self.ui.analyzer.username} - Segment Progression ({mode_str})'
        if self.ui.comparison_active:
            title += f' vs {self.ui.comparison_analyzer.username}'
        filters = []
        if self.ui.season_var.get() != 'All':
            filters.append(f"Season {self.ui.season_var.get()}")
        if self.ui.seed_filter_var.get() != 'All':
            filters.append(self.ui.seed_filter_var.get())
        if filters:
            title += f" [{', '.join(filters)}]"
        title += "\n(Click any chart to expand)"
        
        cb.set_title(title, fontsize=12)
        
        # Enable click detection for match details
        cb.enable_match_click_detection(self._on_match_click)
        
        cb.finalize()
    
    def on_splits_toggle(self):
        """Handle split times checkbox toggle - refresh segment trends if visible"""
        # Only refresh if we're currently viewing segment trends (Charts tab selected)
        if self.ui.analyzer and self.ui.notebook.index(self.ui.notebook.select()) == 1:
            # Check if we have segment data loaded
            detailed_count = sum(1 for m in self.ui.analyzer.matches if m.has_detailed_data)
            if detailed_count >= 5:
                # Need to recalculate data since split/absolute changed
                # First get the current expansion state
                was_expanded = self._segment_expanded
                expanded_segment = self._expanded_segment
                
                # Refresh grid view (this will recalculate cached data)
                self.show_segment_progression()
                
                # If we were expanded, re-expand to the same segment
                if was_expanded and expanded_segment and expanded_segment in self._cached_segment_data:
                    self.show_expanded_segment(expanded_segment)
    
    def _on_match_click(self, match):
        """Handle click on a match scatter point to show detailed info"""
        show_match_info_dialog(self.ui.root, match, self.ui.text_presenter)
    
    def on_chart_click(self, event):
        """Handle click events on the chart canvas"""
        # Only handle clicks when viewing segment progression grid
        if not hasattr(self.ui, '_current_chart_view') or self.ui._current_chart_view != '_show_segment_progression':
            return
        
        # Don't handle clicks if already expanded
        if self._segment_expanded:
            return
        
        # Check if click was on one of our mapped axes
        if event.inaxes is None:
            return
        
        # Find which segment was clicked
        clicked_segment = self._segment_axes_map.get(event.inaxes)
        if clicked_segment:
            self.show_expanded_segment(clicked_segment)
    
    def show_expanded_segment(self, segment: str):
        """Show a single segment expanded to full page"""
        if segment not in self._cached_segment_data:
            return
        
        self._segment_expanded = True
        self._expanded_segment = segment
        
        # Show back button
        self.ui._set_chart_controls_visible(show_splits_toggle=True, show_back_button=True)
        
        # Get cached data
        times = self._cached_segment_data[segment]['times']
        dates = self._cached_segment_data[segment]['dates']
        matches = self._cached_segment_data[segment]['matches']
        
        # Get full data for rolling calculations
        full_times = self._cached_full_segment_data[segment]['times']
        full_dates = self._cached_full_segment_data[segment]['dates']
        
        show_splits = self.ui.show_splits_var.get() if self.ui.show_splits_var else False
        segment_name = self._segment_display.get(segment, segment)
        
        # Use ChartBuilder for full-page view
        cb = self.ui.chart_builder
        cb.clear()
        cb.set_palette(self.ui.chart_options['color_palette'])
        
        ax = cb.get_subplot(1, 1, 1)
        
        # Clear the axes map for expanded view (no clicking in expanded view)
        self._segment_axes_map = {}
        
        # Get color index from available segments and use 4-color scheme
        segment_idx = self._available_segments.index(segment) if segment in self._available_segments else 0
        base_color_offset = (segment_idx * 4) % len(cb.palette)
        main_scatter_color_idx = base_color_offset
        main_line_color_idx = (base_color_offset + 1) % len(cb.palette)
        comp_scatter_color_idx = (base_color_offset + 2) % len(cb.palette)
        comp_line_color_idx = (base_color_offset + 3) % len(cb.palette)
        
        # Main player scatter plot with larger points (circles)
        cb.plot_scatter(ax, dates, times, 
                       size=self.ui.chart_options['point_size'],
                       alpha=0.6, color_index=main_scatter_color_idx, marker='o',
                       label=self.ui.analyzer.username, match_data=matches)
        
        # Add comparison data if available
        comp_times = None
        comp_dates = None
        comp_matches = None
        comp_full_times = None
        comp_full_dates = None
        if hasattr(self, '_cached_comparison_data') and segment in self._cached_comparison_data:
            comp_times = self._cached_comparison_data[segment]['times']
            comp_dates = self._cached_comparison_data[segment]['dates']
            comp_matches = self._cached_comparison_data[segment]['matches']
            
            # Get full comparison data for rolling calculations
            if hasattr(self, '_cached_comparison_full_data') and segment in self._cached_comparison_full_data:
                comp_full_times = self._cached_comparison_full_data[segment]['times']
                comp_full_dates = self._cached_comparison_full_data[segment]['dates']
            
            cb.plot_scatter(ax, comp_dates, comp_times,
                           size=self.ui.chart_options['point_size'] * 0.8,
                           alpha=0.5, color_index=comp_scatter_color_idx, marker='o',
                           label=self.ui.comparison_analyzer.username, match_data=comp_matches)
        
        # Rolling std dev bands (if enabled) - draw first so avg line is on top
        if self.ui.chart_options['show_rolling_std'] and len(times) >= 1:
            window = self.ui.chart_options['rolling_window']
            cb.add_rolling_std_dev(ax, dates, times,
                                   window=window, label=f'±1σ ({window}-pt)', 
                                   color_index=main_line_color_idx,
                                   full_x_data=full_dates, full_y_data=full_times)
            
            # Add comparison player rolling std dev if available
            if comp_times and comp_dates and len(comp_times) >= 1:
                comp_window = self.ui.chart_options['rolling_window']
                cb.add_rolling_std_dev(ax, comp_dates, comp_times,
                                       window=comp_window, label=f'Comp ±1σ ({comp_window}-pt)',
                                       alpha=0.3, color_index=comp_line_color_idx,
                                       full_x_data=comp_full_dates, full_y_data=comp_full_times)
        
        # Rolling average (if enabled)
        if self.ui.chart_options['show_rolling_avg'] and len(times) >= 1:
            window = self.ui.chart_options['rolling_window']
            cb.add_rolling_average(ax, dates, times, 
                                  window=window, color_index=main_line_color_idx,
                                  label=f'{window}-match average',
                                  full_x_data=full_dates, full_y_data=full_times)
            
            # Add comparison player rolling average if available
            if comp_times and comp_dates and len(comp_times) >= 1:
                comp_window = self.ui.chart_options['rolling_window']
                cb.add_rolling_average(ax, comp_dates, comp_times, 
                                      window=comp_window, color_index=comp_line_color_idx,
                                      label=f'Comp {comp_window}-match avg',
                                      full_x_data=comp_full_dates, full_y_data=comp_full_times)
        
        # PB line (if enabled)
        if self.ui.chart_options['show_pb_line']:
            label = 'Best Split' if show_splits else 'PB'
            cb.add_pb_line(ax, dates, times, label=label, color_index=main_line_color_idx)
            
            # Add comparison player PB line if available
            if comp_times and comp_dates:
                comp_label = 'Comp Best Split' if show_splits else 'Comp PB'
                cb.add_pb_line(ax, comp_dates, comp_times, label=comp_label, color_index=comp_line_color_idx)
        
        y_label = 'Split Time (minutes)' if show_splits else 'Time (minutes)'
        cb.set_labels(ax, title=segment_name, 
                     xlabel='Date', ylabel=y_label,
                     title_fontsize=14, label_fontsize=10)
        cb.set_grid(ax, self.ui.chart_options['show_grid'])
        
        # Format date axis for better readability in expanded view
        if len(dates) > 0:
            # For expanded view, allow more ticks (up to 8)
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
                # For few data points, use all dates with full format
                tick_labels = [d.strftime('%m/%d/%y') for d in dates]
                cb.set_xticks(ax, dates, tick_labels, rotation=30, ha='right')
        
        # Show legend
        cb.set_legend(ax)
        
        # Add detailed stats annotation
        avg_time = statistics.mean(times)
        best_time = min(times)
        worst_time = max(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        
        stats_text = (
            f'{self.ui.analyzer.username}:\n'
            f'  Matches: {len(times)}\n'
            f'  Best: {self.ui._minutes_to_str(best_time)}\n'
            f'  Average: {self.ui._minutes_to_str(avg_time)}\n'
            f'  Median: {self.ui._minutes_to_str(median_time)}\n'
            f'  Worst: {self.ui._minutes_to_str(worst_time)}\n'
            f'  Std Dev: {self.ui._minutes_to_str(std_dev)}'
        )
        
        # Add comparison stats if available
        if comp_times:
            comp_avg = statistics.mean(comp_times)
            comp_best = min(comp_times)
            comp_worst = max(comp_times)
            comp_median = statistics.median(comp_times)
            comp_std = statistics.stdev(comp_times) if len(comp_times) > 1 else 0
            
            stats_text += (
                f'\n\n{self.ui.comparison_analyzer.username}:\n'
                f'  Matches: {len(comp_times)}\n'
                f'  Best: {self.ui._minutes_to_str(comp_best)}\n'
                f'  Average: {self.ui._minutes_to_str(comp_avg)}\n'
                f'  Median: {self.ui._minutes_to_str(comp_median)}\n'
                f'  Worst: {self.ui._minutes_to_str(comp_worst)}\n'
                f'  Std Dev: {self.ui._minutes_to_str(comp_std)}'
            )
        
        cb.add_annotation(ax, stats_text, x=0.02, y=0.98, fontsize=8)
        
        # Build title
        mode_str = 'Split Times' if show_splits else 'Absolute Times'
        title = f'{self.ui.analyzer.username} - {segment_name} ({mode_str})'
        if comp_times:
            title += f' vs {self.ui.comparison_analyzer.username}'
        filters = []
        if self.ui.season_var.get() != 'All':
            filters.append(f"Season {self.ui.season_var.get()}")
        if self.ui.seed_filter_var.get() != 'All':
            filters.append(self.ui.seed_filter_var.get())
        if filters:
            title += f" [{', '.join(filters)}]"
        
        cb.set_title(title, fontsize=14)
        
        # Enable click detection for match details
        cb.enable_match_click_detection(self._on_match_click)
        
        cb.finalize()
    
    def on_segment_back(self):
        """Handle back button click - return to segment grid view"""
        self._segment_expanded = False
        self._expanded_segment = None
        self.show_segment_progression()
    
    def is_expanded(self) -> bool:
        """Check if a segment is currently expanded"""
        return self._segment_expanded
    
    def get_expanded_segment(self) -> Optional[str]:
        """Get the currently expanded segment name"""
        return self._expanded_segment if self._segment_expanded else None
