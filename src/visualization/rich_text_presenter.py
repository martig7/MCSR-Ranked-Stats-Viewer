"""
Rich Text Presenter for modern text formatting in MCSR Stats Browser.
Replaces TextPresenter with component-based, responsive design.
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import statistics

from ..ui.widgets.rich_text_widget import RichTextWidget


class TextComponent:
    """Base class for text components."""
    
    def render(self, widget: RichTextWidget):
        """Render this component to the rich text widget."""
        pass


class HeaderComponent(TextComponent):
    """Component for styled section headers."""
    
    def __init__(self, text: str, level: int = 1, spacing_after: bool = True):
        self.text = text
        self.level = level
        self.spacing_after = spacing_after
    
    def render(self, widget: RichTextWidget):
        widget.add_heading(self.text, level=self.level)
        if self.spacing_after:
            widget.add_separator()
            widget.add_line()


class StatsBlockComponent(TextComponent):
    """Component for formatted statistics display."""
    
    def __init__(self, title: str, stats: Dict[str, Any], 
                 value_style: str = 'accent', compact: bool = False):
        self.title = title
        self.stats = stats
        self.value_style = value_style
        self.compact = compact
    
    def render(self, widget: RichTextWidget):
        if not self.compact:
            widget.add_heading(self.title, level=3)
        
        # Calculate alignment
        max_key_length = max(len(key) for key in self.stats.keys()) if self.stats else 0
        
        for key, value in self.stats.items():
            key_padded = f"{key}:".ljust(max_key_length + 2)
            
            if self.compact:
                widget.add_text(f"  {key_padded}", ['small', 'muted'])
            else:
                widget.add_text(f"  {key_padded}", ['muted'])
            
            # Format value with appropriate color
            widget.add_line(f"{value}", [self.value_style])
        
        if not self.compact:
            widget.add_line()  # Spacing after block


class TableComponent(TextComponent):
    """Component for responsive table display."""
    
    def __init__(self, title: str, headers: List[str], rows: List[List[str]],
                 max_rows: Optional[int] = None, show_index: bool = False):
        self.title = title
        self.headers = headers
        self.rows = rows[:max_rows] if max_rows else rows
        self.show_index = show_index
    
    def render(self, widget: RichTextWidget):
        if self.title:
            widget.add_heading(self.title, level=3)
        
        if not self.headers or not self.rows:
            widget.add_line("No data available", ['muted'])
            return
        
        headers = self.headers.copy()
        rows = []
        
        # Add index column if requested
        if self.show_index:
            headers.insert(0, "#")
            for i, row in enumerate(self.rows, 1):
                rows.append([str(i)] + row)
        else:
            rows = [list(row) for row in self.rows]
        
        widget.add_table(headers, rows)
        widget.add_line()


class PerformanceMetricsComponent(TextComponent):
    """Component for performance-specific metrics with semantic coloring."""
    
    def __init__(self, title: str, metrics: Dict[str, Any], show_trends: bool = True):
        self.title = title
        self.metrics = metrics
        self.show_trends = show_trends
    
    def render(self, widget: RichTextWidget):
        widget.add_heading(self.title, level=2)
        widget.add_separator()
        
        # Split metrics into categories
        match_stats = {}
        time_stats = {}
        rate_stats = {}
        
        for key, value in self.metrics.items():
            key_lower = key.lower()
            if any(word in key_lower for word in ['match', 'game', 'completed']):
                match_stats[key] = value
            elif any(word in key_lower for word in ['time', 'best', 'average', 'median']):
                time_stats[key] = value
            elif any(word in key_lower for word in ['rate', 'percent', '%']):
                rate_stats[key] = value
            else:
                match_stats[key] = value
        
        # Render categories
        if match_stats:
            stats_block = StatsBlockComponent("Match Statistics", match_stats, 'accent')
            stats_block.render(widget)
        
        if time_stats:
            stats_block = StatsBlockComponent("Time Statistics", time_stats, 'success')
            stats_block.render(widget)
        
        if rate_stats:
            stats_block = StatsBlockComponent("Performance Rates", rate_stats, 'warning')
            stats_block.render(widget)


class ComparisonComponent(TextComponent):
    """Component for side-by-side player comparison."""
    
    def __init__(self, title: str, player1_name: str, player1_data: Dict[str, Any],
                 player2_name: str, player2_data: Dict[str, Any]):
        self.title = title
        self.player1_name = player1_name
        self.player1_data = player1_data
        self.player2_name = player2_name
        self.player2_data = player2_data
    
    def render(self, widget: RichTextWidget):
        widget.add_heading(self.title, level=2)
        widget.add_separator()
        
        # Create comparison table
        headers = ["Statistic", self.player1_name, self.player2_name, "Difference"]
        rows = []
        
        # Compare common metrics
        common_keys = set(self.player1_data.keys()) & set(self.player2_data.keys())
        
        for key in sorted(common_keys):
            val1 = self.player1_data[key]
            val2 = self.player2_data[key]
            
            # Calculate difference for numeric values
            try:
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    diff = val1 - val2
                    diff_str = f"{diff:+.1f}" if abs(diff) < 1000 else f"{diff:+.0f}"
                else:
                    diff_str = "-"
            except:
                diff_str = "-"
            
            rows.append([key, str(val1), str(val2), diff_str])
        
        table = TableComponent("", headers, rows)
        table.render(widget)


class RichTextPresenter:
    """Modern text presenter with component-based rendering."""
    
    def __init__(self):
        """Initialize the rich text presenter."""
        pass
    
    def format_time_ms_to_string(self, milliseconds: Optional[int]) -> str:
        """Convert milliseconds to MM:SS.mmm format."""
        if milliseconds is None:
            return "N/A"
        seconds = milliseconds / 1000
        minutes, sec_remainder = divmod(seconds, 60)
        return f'{int(minutes)}:{int(sec_remainder):02d}.{int(milliseconds % 1000):03d}'
    
    def format_minutes_to_string(self, minutes: Optional[float]) -> str:
        """Convert decimal minutes to 'Xm Ys' format."""
        if minutes is None:
            return "N/A"
        m = int(minutes)
        s = int((minutes - m) * 60)
        return f'{m}m {s}s'
    
    def render_welcome(self, widget: RichTextWidget):
        """Render welcome message using components."""
        widget.clear()
        
        header = HeaderComponent("MCSR Ranked User Statistics", level=1)
        header.render(widget)
        
        widget.add_text("Welcome! ", ['large'])
        widget.add_line("This application analyzes Minecraft Speedrunning (MCSR) Ranked statistics.")
        widget.add_line()
        
        # Getting started section
        widget.add_heading("Getting Started", level=2)
        widget.add_line("1. Enter a username in the field above and click 'Load Data'", ['indent'])
        widget.add_line("2. Use the sidebar to navigate between different views and charts", ['indent'])
        widget.add_line("3. Apply filters to focus on specific matches or time periods", ['indent'])
        widget.add_line()
        
        # Features section
        widget.add_heading("Features", level=2)
        features = [
            "Comprehensive match analysis with win/loss tracking",
            "Best times analysis and PB progression",
            "Segment timing breakdown (when available)",
            "Season and seed type comparisons",
            "Interactive charts with rolling averages",
            "Player comparison functionality",
            "Advanced filtering options"
        ]
        
        for feature in features:
            widget.add_line(f"• {feature}", ['indent'])
        
        widget.add_line()
        widget.add_text("The app fetches data from the MCSR Ranked API and caches it locally ", ['small', 'muted'])
        widget.add_line("for faster subsequent access.", ['small', 'muted'])
        widget.add_line()
        
        widget.add_text("Click 'Load Data' with a username to begin your analysis!", ['accent', 'large'])
        
        widget.finalize()
    
    def render_summary(self, widget: RichTextWidget, analyzer, all_matches: List):
        """Render summary statistics using modern components."""
        widget.clear()
        
        if not analyzer:
            widget.add_text("No data loaded.", ['error'])
            widget.finalize()
            return
        
        if not all_matches:
            widget.add_text("No matches found with the current filters.", ['warning'])
            widget.finalize()
            return
        
        # Header
        header = HeaderComponent(f"MCSR Ranked Stats - {analyzer.username}", level=1, spacing_after=False)
        header.render(widget)
        
        # Categorize matches
        wins = [m for m in all_matches if m.is_user_win is True]
        losses = [m for m in all_matches if m.is_user_win is False]
        draws = [m for m in all_matches if m.is_draw]
        forfeits = [m for m in all_matches if m.forfeited and m.is_user_win is None and not m.is_draw]
        solo_completions = [m for m in all_matches if m.player_count == 1 and m.user_completed and not m.forfeited]
        
        # Get completed runs for time stats
        completed_runs = [m for m in all_matches if m.user_completed and m.match_time is not None and not m.is_draw and not m.forfeited]
        
        if not completed_runs:
            widget.add_text("No completed runs found with valid completion times.", ['warning'])
            widget.finalize()
            return
        
        # Calculate stats
        times = [m.match_time for m in completed_runs]
        competitive_matches = len(wins) + len(losses)
        win_rate = len(wins) / competitive_matches * 100 if competitive_matches > 0 else 0
        
        # Match summary
        match_stats = {
            "Total Matches": f"{len(all_matches):,}",
            "Wins": f"{len(wins):,} ({win_rate:.1f}% win rate)",
            "Losses": f"{len(losses):,}",
            "Draws": f"{len(draws):,}",
            "Forfeits": f"{len(forfeits):,}",
            "Solo Completions": f"{len(solo_completions):,}"
        }
        
        # Time stats  
        time_stats = {
            "Completed Runs": f"{len(completed_runs):,}",
            "Personal Best": self.format_time_ms_to_string(min(times)),
            "Average Time": self.format_time_ms_to_string(int(sum(times) / len(times))),
            "Median Time": self.format_time_ms_to_string(int(statistics.median(times)))
        }
        
        # Render performance metrics
        all_stats = {**match_stats, **time_stats}
        performance = PerformanceMetricsComponent("Performance Summary", all_stats)
        performance.render(widget)
        
        # Percentiles table
        sorted_times = sorted(times)
        percentile_data = []
        for p in [10, 25, 50, 75, 90, 95, 99]:
            idx = int((p / 100) * (len(sorted_times) - 1))
            time_val = self.format_time_ms_to_string(sorted_times[idx])
            percentile_data.append([f"{p}th percentile", time_val])
        
        percentile_table = TableComponent("Time Percentiles", ["Percentile", "Time"], percentile_data)
        percentile_table.render(widget)
        
        widget.finalize()
    
    def render_best_times(self, widget: RichTextWidget, analyzer, all_matches: List, seasons: Dict):
        """Render best times analysis using modern components."""
        widget.clear()
        
        if not all_matches:
            widget.add_text("No match data available for best times analysis.", ['warning'])
            widget.finalize()
            return
        
        # Header
        header = HeaderComponent(f"Best Times - {analyzer.username}", level=1, spacing_after=False)
        header.render(widget)
        
        # Get completed runs
        completed_runs = [m for m in all_matches if m.user_completed and m.match_time is not None and not m.is_draw and not m.forfeited]
        
        if not completed_runs:
            widget.add_text("No completed runs found with valid completion times.", ['warning'])
            widget.finalize()
            return
        
        # Sort by time for top times display
        completed_runs_by_time = sorted(completed_runs, key=lambda x: x.match_time)
        
        # Top 10 times table
        top_times_data = []
        for i, match in enumerate(completed_runs_by_time[:10], 1):
            top_times_data.append([
                f"#{i}",
                match.time_str(),
                match.date_str(),
                f"S{match.season}",
                match.seed_type or "Unknown"
            ])
        
        top_times_table = TableComponent(
            "🏆 Top 10 Personal Bests", 
            ["Rank", "Time", "Date", "Season", "Seed Type"], 
            top_times_data
        )
        top_times_table.render(widget)
        
        # PB Progression (show key improvements)
        pb_progression_data = []
        current_pb = float('inf')
        
        # Sort by date for progression
        runs_by_date = sorted(completed_runs, key=lambda x: x.datetime_obj)
        improvements = []
        
        for match in runs_by_date:
            if match.match_time < current_pb:
                improvement = current_pb - match.match_time if current_pb != float('inf') else 0
                improvements.append({
                    'date': match.date_str(),
                    'time': match.time_str(),
                    'improvement': improvement,
                    'season': match.season
                })
                current_pb = match.match_time
        
        # Show last 10 PB improvements
        for i, pb in enumerate(improvements[-10:], 1):
            improvement_str = f"-{self.format_time_ms_to_string(int(pb['improvement']))}" if pb['improvement'] > 0 else "First PB"
            pb_progression_data.append([
                f"PB #{i}",
                pb['time'],
                pb['date'],
                f"S{pb['season']}",
                improvement_str
            ])
        
        pb_table = TableComponent(
            "📈 Recent PB Progression",
            ["Milestone", "Time", "Date", "Season", "Improvement"],
            pb_progression_data
        )
        pb_table.render(widget)
        
        # Season breakdown if available
        if seasons:
            season_data = []
            for season_num in sorted(seasons.keys()):
                season_info = seasons[season_num]
                season_data.append([
                    f"Season {season_num}",
                    str(season_info['matches']),
                    self.format_time_ms_to_string(season_info['best']),
                    self.format_time_ms_to_string(int(season_info['average']))
                ])
            
            season_table = TableComponent(
                "📅 Season Breakdown",
                ["Season", "Matches", "Best Time", "Average"],
                season_data
            )
            season_table.render(widget)
        
        widget.finalize()
    
    def render_comparison(self, widget: RichTextWidget, player1_name: str, player1_text: str,
                         player2_name: str, player2_text: str):
        """Render side-by-side player comparison (legacy compatibility)."""
        widget.clear()
        
        header = HeaderComponent(f"{player1_name} vs {player2_name}", level=1)
        header.render(widget)
        
        # For now, render as side-by-side text blocks
        # TODO: Parse the text blocks into structured comparison
        
        widget.add_heading(player1_name, level=2)
        widget.add_text(player1_text, ['monospace'])
        widget.add_line()
        
        widget.add_heading(player2_name, level=2)
        widget.add_text(player2_text, ['monospace'])
        
        widget.finalize()