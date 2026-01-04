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
    """Enhanced component for side-by-side player comparison."""
    
    def __init__(self, title: str, player1_name: str, player1_text: str,
                 player2_name: str, player2_text: str, structured_data: Dict = None):
        self.title = title
        self.player1_name = player1_name
        self.player1_text = player1_text
        self.player2_name = player2_name
        self.player2_text = player2_text
        self.structured_data = structured_data or {}
    
    def render(self, widget: RichTextWidget):
        widget.add_heading(self.title, level=1)
        widget.add_separator()
        widget.add_line()
        
        # If we have structured data, render as comparison table
        if self.structured_data and 'player1_stats' in self.structured_data:
            self._render_structured_comparison(widget)
        else:
            # Fallback to side-by-side text layout
            self._render_text_comparison(widget)
    
    def _render_structured_comparison(self, widget: RichTextWidget):
        """Render structured data as comparison tables."""
        p1_data = self.structured_data['player1_stats']
        p2_data = self.structured_data['player2_stats']
        
        # Create comparison table
        headers = ["Statistic", self.player1_name, self.player2_name, "Difference"]
        rows = []
        
        # Compare common metrics
        common_keys = set(p1_data.keys()) & set(p2_data.keys())
        
        for key in sorted(common_keys):
            val1 = p1_data[key]
            val2 = p2_data[key]
            
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
    
    def _render_text_comparison(self, widget: RichTextWidget):
        """Render text blocks side by side."""
        # Split text into sections
        p1_sections = self._parse_text_sections(self.player1_text)
        p2_sections = self._parse_text_sections(self.player2_text)
        
        # Render player headers
        widget.add_text(f"{self.player1_name}", ['accent', 'large'])
        widget.add_text(f" vs ", ['muted'])
        widget.add_line(f"{self.player2_name}", ['accent', 'large'])
        widget.add_separator()
        widget.add_line()
        
        # Render side-by-side content
        max_sections = max(len(p1_sections), len(p2_sections))
        
        for i in range(max_sections):
            p1_section = p1_sections[i] if i < len(p1_sections) else ""
            p2_section = p2_sections[i] if i < len(p2_sections) else ""
            
            # Create side-by-side table for this section
            if p1_section or p2_section:
                headers = [self.player1_name, self.player2_name]
                p1_lines = p1_section.split('\n')
                p2_lines = p2_section.split('\n')
                max_lines = max(len(p1_lines), len(p2_lines))
                
                rows = []
                for j in range(max_lines):
                    left = p1_lines[j] if j < len(p1_lines) else ""
                    right = p2_lines[j] if j < len(p2_lines) else ""
                    rows.append([left.strip(), right.strip()])
                
                if any(row[0] or row[1] for row in rows):
                    table = TableComponent("", headers, rows)
                    table.render(widget)
    
    def _parse_text_sections(self, text: str) -> List[str]:
        """Parse text into logical sections."""
        # Split on section headers (lines with ═ or ─ patterns)
        lines = text.strip().split('\n')
        sections = []
        current_section = []
        
        for line in lines:
            if ('═' in line and len(set(line.strip())) <= 2) or \
               ('─' in line and len(set(line.strip())) <= 2) or \
               ('SUMMARY' in line.upper()) or \
               ('STATS' in line.upper()):
                # Start new section
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections


class SegmentAnalysisComponent(TextComponent):
    """Component for segment analysis display with timing data."""
    
    def __init__(self, username: str, segment_stats: Dict, split_stats: Dict, 
                 detailed_count: int, filter_text: str = "", show_split_times: bool = False):
        self.username = username
        self.segment_stats = segment_stats
        self.split_stats = split_stats
        self.detailed_count = detailed_count
        self.filter_text = filter_text
        self.show_split_times = show_split_times
        self.segment_display = {
            'nether_enter': 'Nether Enter',
            'bastion_enter': 'Bastion Enter',
            'fortress_enter': 'Fortress Enter',
            'blind_portal': 'Blind Portal',
            'stronghold_enter': 'Stronghold Enter',
            'end_enter': 'End Enter',
            'game_end': 'Run Completion'
        }
    
    def render(self, widget: RichTextWidget):
        widget.add_heading(f"Segment Analysis - {self.username}", level=1)
        
        if self.detailed_count == 0:
            widget.add_text("No segment data available", ['error'])
            if self.filter_text:
                widget.add_line(f" {self.filter_text.strip()}", ['muted'])
            else:
                widget.add_line()
            widget.add_line()
            widget.add_text("Click ", [])
            widget.add_text("'Fetch Segment Data'", ['accent'])
            widget.add_line(" to download detailed timeline data for your matches.")
            widget.add_line()
            widget.add_line("This will allow you to see:")
            widget.add_line("• Time to reach each segment (Nether, Bastion, Fortress, etc.)", ['indent'])
            widget.add_line("• Split times between segments", ['indent'])
            widget.add_line("• Performance trends for each segment", ['indent'])
            return
        
        # Data availability info
        stats_block = StatsBlockComponent("Data Availability", {
            "Matches with segment data": f"{self.detailed_count:,}",
            "Filter status": self.filter_text.strip() if self.filter_text else "All matches"
        }, 'accent', compact=True)
        stats_block.render(widget)
        
        # Show either absolute times or split times based on toggle
        if self.show_split_times and self.split_stats:
            # Split times table
            split_headers = ["Segment", "Best", "Average", "Median", "Matches"]
            split_rows = []
            
            for seg_key, seg_name in self.segment_display.items():
                if seg_key in self.split_stats:
                    s = self.split_stats[seg_key]
                    split_rows.append([
                        seg_name,
                        self._format_time_ms(s['best']),
                        self._format_time_ms(int(s['average'])),
                        self._format_time_ms(int(s['median'])),
                        f"{s['matches']:,}"
                    ])
            
            split_table = TableComponent("⏱️ Split Times (Time spent in segment)", split_headers, split_rows)
            split_table.render(widget)
        elif not self.show_split_times and self.segment_stats:
            # Absolute times table
            abs_headers = ["Segment", "Best", "Average", "Median", "Matches"]
            abs_rows = []
            
            for seg_key, seg_name in self.segment_display.items():
                if seg_key in self.segment_stats:
                    s = self.segment_stats[seg_key]
                    abs_rows.append([
                        seg_name,
                        self._format_time_ms(s['best']),
                        self._format_time_ms(int(s['average'])),
                        self._format_time_ms(int(s['median'])),
                        f"{s['matches']:,}"
                    ])
            
            abs_table = TableComponent("⏱️ Absolute Times (Time to reach segment)", abs_headers, abs_rows)
            abs_table.render(widget)
    
    def _format_time_ms(self, milliseconds: Optional[int]) -> str:
        """Format milliseconds to MM:SS.mmm."""
        if milliseconds is None:
            return "N/A"
        seconds = milliseconds / 1000
        minutes, sec_remainder = divmod(seconds, 60)
        return f'{int(minutes)}:{int(sec_remainder):02d}.{int(milliseconds % 1000):03d}'


class MatchDetailComponent(TextComponent):
    """Component for detailed match information display."""
    
    def __init__(self, match, analyzer_username: str):
        self.match = match
        self.analyzer_username = analyzer_username
        self.segment_display = {
            'nether_enter': 'Nether Enter',
            'bastion_enter': 'Bastion Enter', 
            'fortress_enter': 'Fortress Enter',
            'blind_portal': 'Blind Portal',
            'stronghold_enter': 'Stronghold Enter',
            'end_enter': 'End Enter',
            'game_end': 'Run Completion'
        }
    
    def render(self, widget: RichTextWidget):
        widget.add_heading(f"Match Details - {self.match.date_str()}", level=1)
        widget.add_separator()
        
        # Match information
        time_display = self.match.time_str() if self.match.user_completed else f"({self.match.time_str()})"
        match_type_str = 'Private Room' if self.match.match_type == 3 else 'Ranked' if self.match.match_type == 1 else f'Type {self.match.match_type}'
        
        match_info = {
            "Status": self.match.get_status(),
            "Your Time": time_display if self.match.match_time else "Did not finish",
            "Season": str(self.match.season),
            "Seed Type": str(self.match.seed_type),
            "Match Type": match_type_str,
            "Players": str(self.match.player_count),
            "Forfeited": "Yes" if self.match.forfeited else "No"
        }
        
        match_block = StatsBlockComponent("📊 Match Information", match_info, 'accent')
        match_block.render(widget)
        
        # Player information table
        if self.match.players:
            player_headers = ["Player", "ELO", "Change", "Result"]
            player_rows = []
            
            for player in self.match.players:
                nickname = player.get('nickname', 'Unknown')
                elo_rate = player.get('elo_rate', 'N/A')
                elo_change = player.get('elo_change', 0)
                
                # Mark the analyzed user and determine result
                if nickname.lower() == self.analyzer_username.lower():
                    nickname += " (You)"
                    result = self._get_user_result()
                else:
                    result = self._get_opponent_result()
                
                # Format ELO change
                elo_change_str = f"{elo_change:+d}" if isinstance(elo_change, int) and elo_change != 0 else "0"
                
                player_rows.append([nickname, str(elo_rate), elo_change_str, result])
            
            player_table = TableComponent("👥 Player Information", player_headers, player_rows)
            player_table.render(widget)
        
        # Segment timing information
        if self.match.has_detailed_data and self.match.segments:
            segment_headers = ["Segment", "Absolute Time", "Split Time"]
            segment_rows = []
            
            prev_time = 0
            for seg_key, seg_name in self.segment_display.items():
                if seg_key in self.match.segments:
                    seg_data = self.match.segments[seg_key]
                    abs_time = seg_data.get('absolute_time', 0)
                    split_time = seg_data.get('split_time', abs_time - prev_time)
                    
                    segment_rows.append([
                        seg_name,
                        self._format_time_ms(abs_time),
                        self._format_time_ms(split_time)
                    ])
                    prev_time = abs_time
            
            segment_table = TableComponent("⏱️ Segment Timing", segment_headers, segment_rows)
            segment_table.render(widget)
        else:
            widget.add_heading("⏱️ Segment Timing", level=3)
            widget.add_text("No detailed segment data available.", ['muted'])
            widget.add_line()
            widget.add_text("Click ", [])
            widget.add_text("'Fetch Segment Data'", ['accent'])
            widget.add_line(" to load timeline information.")
            widget.add_line()
    
    def _get_user_result(self) -> str:
        """Get result string for the analyzed user."""
        if self.match.is_user_win is True:
            return "Won"
        elif self.match.is_user_win is False:
            return "Lost"
        elif self.match.forfeited:
            return "Forfeit"
        else:
            return "Draw"
    
    def _get_opponent_result(self) -> str:
        """Get result string for opponents."""
        if self.match.is_user_win is True:
            return "Lost"
        elif self.match.is_user_win is False:
            return "Won"
        elif self.match.forfeited:
            return "Forfeit"
        else:
            return "Draw"
    
    def _format_time_ms(self, milliseconds: Optional[int]) -> str:
        """Format milliseconds to MM:SS.mmm."""
        if milliseconds is None:
            return "N/A"
        seconds = milliseconds / 1000
        minutes, sec_remainder = divmod(seconds, 60)
        return f'{int(minutes)}:{int(sec_remainder):02d}.{int(milliseconds % 1000):03d}'


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
    
    def render_segment_analysis(self, widget: RichTextWidget, analyzer, segment_stats: Dict, 
                               split_stats: Dict, detailed_count: int, filter_text: str = "", 
                               show_split_times: bool = False):
        """Render segment analysis using modern components."""
        widget.clear()
        
        if not analyzer:
            widget.add_text("No data loaded.", ['error'])
            widget.finalize()
            return
        
        segment_component = SegmentAnalysisComponent(
            analyzer.username, segment_stats, split_stats, detailed_count, filter_text, show_split_times
        )
        segment_component.render(widget)
        
        widget.finalize()
    
    def render_match_detail(self, widget: RichTextWidget, match, analyzer_username: str):
        """Render detailed match information using modern components."""
        widget.clear()
        
        match_component = MatchDetailComponent(match, analyzer_username)
        match_component.render(widget)
        
        widget.finalize()
    
    def render_comparison(self, widget: RichTextWidget, player1_name: str, player1_text: str,
                         player2_name: str, player2_text: str):
        """Render side-by-side player comparison using enhanced components."""
        widget.clear()
        
        comparison_component = ComparisonComponent(
            f"{player1_name} vs {player2_name}",
            player1_name, player1_text,
            player2_name, player2_text
        )
        comparison_component.render(widget)
        
        widget.finalize()
    
    def render_summary_comparison(self, widget: RichTextWidget, 
                                 player1_analyzer, player1_matches: List,
                                 player2_analyzer, player2_matches: List):
        """Render structured summary comparison with proper tables."""
        widget.clear()
        
        widget.add_heading(f"{player1_analyzer.username} vs {player2_analyzer.username}", level=1)
        widget.add_separator()
        widget.add_line()
        
        # Calculate stats for both players
        p1_stats = self._calculate_summary_stats(player1_analyzer, player1_matches)
        p2_stats = self._calculate_summary_stats(player2_analyzer, player2_matches)
        
        if not p1_stats and not p2_stats:
            widget.add_text("No data available for comparison.", ['error'])
            widget.finalize()
            return
        
        # Create comparison table
        headers = ["Statistic", player1_analyzer.username, player2_analyzer.username, "Difference"]
        rows = []
        
        # Match statistics comparison
        match_metrics = [
            "Total Matches", "Wins", "Losses", "Draws", "Forfeits", 
            "Solo Completions", "Win Rate %", "Completion Rate %"
        ]
        
        for metric in match_metrics:
            val1 = p1_stats.get(metric, "N/A")
            val2 = p2_stats.get(metric, "N/A") 
            
            # Calculate difference for numeric values
            diff_str = "-"
            try:
                if metric == "Win Rate %" or metric == "Completion Rate %":
                    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                        diff = val1 - val2
                        diff_str = f"{diff:+.1f}%"
                elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    diff = val1 - val2
                    diff_str = f"{diff:+.0f}"
            except:
                pass
            
            rows.append([metric, str(val1), str(val2), diff_str])
        
        widget.add_table(headers, rows)
        
        # Time statistics comparison (if both have completed runs)
        if p1_stats.get("Completed Runs", 0) > 0 and p2_stats.get("Completed Runs", 0) > 0:
            widget.add_heading("Time Statistics", level=2)
            
            time_headers = ["Metric", player1_analyzer.username, player2_analyzer.username, "Difference"]
            time_rows = []
            
            time_metrics = ["Personal Best", "Average Time", "Median Time", "Completed Runs"]
            
            for metric in time_metrics:
                val1 = p1_stats.get(metric, "N/A")
                val2 = p2_stats.get(metric, "N/A")
                
                # For time metrics, calculate difference in milliseconds
                diff_str = "-"
                if metric in ["Personal Best", "Average Time", "Median Time"]:
                    try:
                        if "N/A" not in [val1, val2]:
                            # Extract time values (assuming format like "14:03.024")
                            time1_ms = self._parse_time_string(val1)
                            time2_ms = self._parse_time_string(val2)
                            if time1_ms and time2_ms:
                                diff_ms = time1_ms - time2_ms
                                diff_str = self.format_time_ms_to_string(abs(diff_ms))
                                if diff_ms > 0:
                                    diff_str = f"+{diff_str}"
                                elif diff_ms < 0:
                                    diff_str = f"-{diff_str}"
                    except:
                        pass
                
                time_rows.append([metric, str(val1), str(val2), diff_str])
            
            widget.add_table(time_headers, time_rows)
        
        widget.finalize()
    
    def render_best_times_comparison(self, widget: RichTextWidget,
                                   player1_analyzer, player1_matches: List, player1_seasons: Dict,
                                   player2_analyzer, player2_matches: List, player2_seasons: Dict):
        """Render structured best times comparison."""
        widget.clear()
        
        widget.add_heading(f"Best Times - {player1_analyzer.username} vs {player2_analyzer.username}", level=1)
        widget.add_separator()
        widget.add_line()
        
        # Get completed runs for both players
        p1_completed = [m for m in player1_matches if m.user_completed and m.match_time and not m.is_draw and not m.forfeited]
        p2_completed = [m for m in player2_matches if m.user_completed and m.match_time and not m.is_draw and not m.forfeited]
        
        if not p1_completed and not p2_completed:
            widget.add_text("No completed runs found for either player.", ['warning'])
            widget.finalize()
            return
        
        # Top 10 comparison table
        widget.add_heading("🏆 Top 10 Personal Bests Comparison", level=2)
        
        headers = ["Rank", f"{player1_analyzer.username}", f"{player2_analyzer.username}", "Difference"]
        rows = []
        
        # Sort runs by time
        p1_sorted = sorted(p1_completed, key=lambda x: x.match_time)[:10] if p1_completed else []
        p2_sorted = sorted(p2_completed, key=lambda x: x.match_time)[:10] if p2_completed else []
        
        for i in range(max(len(p1_sorted), len(p2_sorted), 10)):
            rank = f"#{i+1}"
            
            p1_time = "N/A"
            p2_time = "N/A"
            diff_str = "-"
            
            if i < len(p1_sorted):
                p1_time = p1_sorted[i].time_str()
            if i < len(p2_sorted):
                p2_time = p2_sorted[i].time_str()
                
            # Calculate difference if both have times
            if p1_time != "N/A" and p2_time != "N/A":
                try:
                    time1_ms = p1_sorted[i].match_time if i < len(p1_sorted) else None
                    time2_ms = p2_sorted[i].match_time if i < len(p2_sorted) else None
                    if time1_ms and time2_ms:
                        diff_ms = time1_ms - time2_ms
                        diff_str = self.format_time_ms_to_string(abs(diff_ms))
                        if diff_ms > 0:
                            diff_str = f"+{diff_str}"
                        elif diff_ms < 0:
                            diff_str = f"-{diff_str}"
                except:
                    pass
            
            rows.append([rank, p1_time, p2_time, diff_str])
        
        widget.add_table(headers, rows)
        
        # Season breakdown comparison
        if player1_seasons or player2_seasons:
            widget.add_heading("📅 Season Breakdown Comparison", level=2)
            
            season_headers = ["Season", f"{player1_analyzer.username}", f"{player2_analyzer.username}", "Best Time Diff"]
            season_rows = []
            
            all_seasons = set(player1_seasons.keys()) | set(player2_seasons.keys())
            
            for season in sorted(all_seasons):
                p1_info = player1_seasons.get(season, {})
                p2_info = player2_seasons.get(season, {})
                
                p1_display = f"{p1_info.get('matches', 0)} runs, Best: {self.format_time_ms_to_string(p1_info.get('best', 0))}" if p1_info else "No data"
                p2_display = f"{p2_info.get('matches', 0)} runs, Best: {self.format_time_ms_to_string(p2_info.get('best', 0))}" if p2_info else "No data"
                
                # Calculate best time difference
                diff_str = "-"
                if p1_info.get('best') and p2_info.get('best'):
                    diff_ms = p1_info['best'] - p2_info['best']
                    diff_str = self.format_time_ms_to_string(abs(diff_ms))
                    if diff_ms > 0:
                        diff_str = f"+{diff_str}"
                    elif diff_ms < 0:
                        diff_str = f"-{diff_str}"
                
                season_rows.append([f"Season {season}", p1_display, p2_display, diff_str])
            
            widget.add_table(season_headers, season_rows)
        
        widget.finalize()
    
    def _calculate_summary_stats(self, analyzer, matches: List) -> Dict[str, Any]:
        """Calculate summary statistics for a player."""
        if not matches:
            return {}
        
        # Categorize matches
        wins = [m for m in matches if m.is_user_win is True]
        losses = [m for m in matches if m.is_user_win is False] 
        draws = [m for m in matches if m.is_draw]
        forfeits = [m for m in matches if m.forfeited and m.is_user_win is None and not m.is_draw]
        solo_completions = [m for m in matches if m.player_count == 1 and m.user_completed and not m.forfeited]
        completed_runs = [m for m in matches if m.user_completed and m.match_time and not m.is_draw and not m.forfeited]
        
        # Calculate rates
        competitive_matches = len(wins) + len(losses)
        win_rate = (len(wins) / competitive_matches * 100) if competitive_matches > 0 else 0
        completion_rate = (len(completed_runs) / len(matches) * 100) if matches else 0
        
        stats = {
            "Total Matches": len(matches),
            "Wins": len(wins),
            "Losses": len(losses),
            "Draws": len(draws),
            "Forfeits": len(forfeits),
            "Solo Completions": len(solo_completions),
            "Win Rate %": round(win_rate, 1),
            "Completion Rate %": round(completion_rate, 1),
            "Completed Runs": len(completed_runs)
        }
        
        # Time statistics
        if completed_runs:
            times = [m.match_time for m in completed_runs]
            stats.update({
                "Personal Best": self.format_time_ms_to_string(min(times)),
                "Average Time": self.format_time_ms_to_string(int(sum(times) / len(times))),
                "Median Time": self.format_time_ms_to_string(int(statistics.median(times)))
            })
        
        return stats
    
    def _parse_time_string(self, time_str: str) -> Optional[int]:
        """Parse time string like '14:03.024' to milliseconds."""
        try:
            if ':' in time_str and '.' in time_str:
                parts = time_str.split(':')
                minutes = int(parts[0])
                sec_parts = parts[1].split('.')
                seconds = int(sec_parts[0])
                milliseconds = int(sec_parts[1])
                return (minutes * 60 + seconds) * 1000 + milliseconds
        except:
            pass
        return None
    
    def render_segment_analysis_comparison(self, widget: RichTextWidget,
                                         player1_analyzer, player1_matches: List, player1_segment_stats: Dict, player1_split_stats: Dict,
                                         player2_analyzer, player2_matches: List, player2_segment_stats: Dict, player2_split_stats: Dict,
                                         filter_text: str = "", show_split_times: bool = False):
        """Render structured segment analysis comparison with toggle for absolute vs split times."""
        widget.clear()
        
        widget.add_heading(f"Segment Analysis - {player1_analyzer.username} vs {player2_analyzer.username}", level=1)
        
        # Get detailed match counts
        p1_detailed = [m for m in player1_matches if m.has_detailed_data]
        p2_detailed = [m for m in player2_matches if m.has_detailed_data]
        
        if not p1_detailed and not p2_detailed:
            widget.add_text("No segment data available for either player", ['error'])
            if filter_text:
                widget.add_line(f" {filter_text.strip()}", ['muted'])
            widget.add_line()
            widget.add_text("Click ", [])
            widget.add_text("'Fetch Segment Data'", ['accent'])
            widget.add_line(" to download detailed timeline data for matches.")
            widget.finalize()
            return
        
        # Data availability comparison
        availability_stats = {
            "Filter Status": filter_text.strip() if filter_text else "All matches",
            f"{player1_analyzer.username} Segment Data": f"{len(p1_detailed):,} matches",
            f"{player2_analyzer.username} Segment Data": f"{len(p2_detailed):,} matches"
        }
        
        for key, value in availability_stats.items():
            widget.add_text(f"{key}: ", ['muted'])
            widget.add_line(f"{value}", ['accent'])
        widget.add_line()
        
        # Segment display mapping
        segment_display = {
            'nether_enter': 'Nether Enter',
            'bastion_enter': 'Bastion Enter',
            'fortress_enter': 'Fortress Enter',
            'blind_portal': 'Blind Portal',
            'stronghold_enter': 'Stronghold Enter',
            'end_enter': 'End Enter',
            'game_end': 'Run Completion'
        }
        
        # Choose which data to display based on toggle
        if show_split_times:
            # Show split times table
            if player1_split_stats or player2_split_stats:
                widget.add_heading("⏱️ Split Times (Time spent in each segment)", level=2)
                
                # Define advanced table structure for split times
                main_headers = ["Segment", "Average", "Best", "Median"]
                sub_headers = [
                    [],  # Segment column has no subheaders
                    [player1_analyzer.username, player2_analyzer.username],  # Average subheaders
                    [player1_analyzer.username, player2_analyzer.username],  # Best subheaders
                    [player1_analyzer.username, player2_analyzer.username]   # Median subheaders
                ]
                
                split_rows = []
                all_split_segments = set(player1_split_stats.keys()) | set(player2_split_stats.keys())
                
                for seg_key in ['nether_enter', 'bastion_enter', 'fortress_enter', 'blind_portal', 'stronghold_enter', 'end_enter', 'game_end']:
                    if seg_key not in all_split_segments:
                        continue
                        
                    seg_name = segment_display.get(seg_key, seg_key)
                    
                    # Player 1 split data
                    p1_split = player1_split_stats.get(seg_key, {})
                    p1_avg = self._format_time_ms(int(p1_split.get('average', 0))) if p1_split.get('average') else "N/A"
                    p1_best = self._format_time_ms(p1_split.get('best', 0)) if p1_split.get('best') else "N/A"
                    p1_median = self._format_time_ms(int(p1_split.get('median', 0))) if p1_split.get('median') else "N/A"
                    
                    # Player 2 split data
                    p2_split = player2_split_stats.get(seg_key, {})
                    p2_avg = self._format_time_ms(int(p2_split.get('average', 0))) if p2_split.get('average') else "N/A"
                    p2_best = self._format_time_ms(p2_split.get('best', 0)) if p2_split.get('best') else "N/A"
                    p2_median = self._format_time_ms(int(p2_split.get('median', 0))) if p2_split.get('median') else "N/A"
                    
                    # Create row with concise format
                    split_rows.append([seg_name, p1_avg, p2_avg, p1_best, p2_best, p1_median, p2_median])
                
                widget.add_table(
                    headers=[], rows=split_rows, advanced=True,
                    main_headers=main_headers, sub_headers=sub_headers
                )
        else:
            # Show absolute times table
            if player1_segment_stats or player2_segment_stats:
                widget.add_heading("⏱️ Absolute Times (Time to reach each segment)", level=2)
                
                # Define advanced table structure
                main_headers = ["Segment", "Average", "Best", "Median"]
                sub_headers = [
                    [],  # Segment column has no subheaders
                    [player1_analyzer.username, player2_analyzer.username],  # Average subheaders
                    [player1_analyzer.username, player2_analyzer.username],  # Best subheaders  
                    [player1_analyzer.username, player2_analyzer.username]   # Median subheaders
                ]
                
                abs_rows = []
                all_segments = set(player1_segment_stats.keys()) | set(player2_segment_stats.keys())
                
                for seg_key in ['nether_enter', 'bastion_enter', 'fortress_enter', 'blind_portal', 'stronghold_enter', 'end_enter', 'game_end']:
                    if seg_key not in all_segments:
                        continue
                        
                    seg_name = segment_display.get(seg_key, seg_key)
                    
                    # Player 1 data
                    p1_data = player1_segment_stats.get(seg_key, {})
                    p1_avg = self._format_time_ms(int(p1_data.get('average', 0))) if p1_data.get('average') else "N/A"
                    p1_best = self._format_time_ms(p1_data.get('best', 0)) if p1_data.get('best') else "N/A"
                    p1_median = self._format_time_ms(int(p1_data.get('median', 0))) if p1_data.get('median') else "N/A"
                    
                    # Player 2 data
                    p2_data = player2_segment_stats.get(seg_key, {})
                    p2_avg = self._format_time_ms(int(p2_data.get('average', 0))) if p2_data.get('average') else "N/A"
                    p2_best = self._format_time_ms(p2_data.get('best', 0)) if p2_data.get('best') else "N/A"
                    p2_median = self._format_time_ms(int(p2_data.get('median', 0))) if p2_data.get('median') else "N/A"
                    
                    # Create row with concise format
                    abs_rows.append([seg_name, p1_avg, p2_avg, p1_best, p2_best, p1_median, p2_median])
                
                widget.add_table(
                    headers=[], rows=abs_rows, advanced=True, 
                    main_headers=main_headers, sub_headers=sub_headers
                )
        
        widget.finalize()
    
    def _format_time_ms(self, milliseconds: Optional[int]) -> str:
        """Format milliseconds to MM:SS.mmm (duplicate of method from SegmentAnalysisComponent for reuse)."""
        if milliseconds is None:
            return "N/A"
        seconds = milliseconds / 1000
        minutes, sec_remainder = divmod(seconds, 60)
        return f'{int(minutes)}:{int(sec_remainder):02d}.{int(milliseconds % 1000):03d}'