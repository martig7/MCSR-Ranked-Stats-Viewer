"""
Text presentation and formatting class for MCSR Ranked Stats UI.
Handles all text generation, formatting, and display logic.
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import statistics


class TextPresenter:
    """Handles all text formatting and generation for the UI."""
    
    def __init__(self):
        """Initialize the text presenter."""
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
    
    def create_border_line(self, width: int, style: str = "thick") -> str:
        """Create a border line with box-drawing characters."""
        if style == "thick":
            return "═" * width
        elif style == "thin":
            return "─" * width
        else:
            return "─" * width
    
    def format_table_header(self, title: str, width: int = 80) -> str:
        """Create a formatted table header with borders."""
        title_line = f"║ {title:<{width-4}} ║"
        border_top = f"╔{self.create_border_line(width-2, 'thick')}╗"
        border_bottom = f"╚{self.create_border_line(width-2, 'thick')}╝"
        return f"{border_top}\n{title_line}\n{border_bottom}"
    
    def format_side_by_side_text(self, left_text: str, right_text: str, 
                                title_left: str = "Player 1", title_right: str = "Player 2") -> str:
        """Format two text blocks side by side for comparison."""
        left_lines = left_text.strip().split('\n')
        right_lines = right_text.strip().split('\n')
        
        # Ensure both sides have the same number of lines
        max_lines = max(len(left_lines), len(right_lines))
        left_lines.extend([''] * (max_lines - len(left_lines)))
        right_lines.extend([''] * (max_lines - len(right_lines)))
        
        # Calculate column width (assume 40 chars each side with separator)
        col_width = 40
        
        # Create header
        header = f"{title_left:<{col_width}} │ {title_right}"
        separator = "─" * col_width + "─┼─" + "─" * col_width
        
        # Combine lines
        result_lines = [header, separator]
        for left, right in zip(left_lines, right_lines):
            # Truncate if too long
            left_truncated = left[:col_width] if len(left) > col_width else left
            right_truncated = right[:col_width] if len(right) > col_width else right
            
            line = f"{left_truncated:<{col_width}} │ {right_truncated}"
            result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def generate_welcome_text(self) -> str:
        """Generate welcome message text."""
        return """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           MCSR Ranked User Statistics                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Welcome! This application analyzes Minecraft Speedrunning (MCSR) Ranked statistics.

To get started:
1. Enter a username in the field above and click 'Load Data'
2. Use the sidebar to navigate between different views and charts
3. Apply filters to focus on specific matches or time periods

Features:
• Comprehensive match analysis with win/loss tracking
• Best times analysis and PB progression
• Segment timing breakdown (when available)
• Season and seed type comparisons
• Interactive charts with rolling averages
• Player comparison functionality
• Advanced filtering options

The app fetches data from the MCSR Ranked API and caches it locally for faster
subsequent access. Detailed segment data is loaded on-demand.

Click 'Load Data' with a username to begin your analysis!
        """
    
    def generate_summary_text(self, analyzer, all_matches: List) -> str:
        """Generate comprehensive summary statistics text using actual UI logic."""
        if not analyzer:
            return "No data loaded."
        
        if not all_matches:
            return "No matches found with the current filters."
            
        # Categorize matches (extracted from UI logic)
        wins = [m for m in all_matches if m.is_user_win is True]
        losses = [m for m in all_matches if m.is_user_win is False]
        draws = [m for m in all_matches if m.is_draw]
        forfeits = [m for m in all_matches if m.forfeited and m.is_user_win is None and not m.is_draw]
        solo_completions = [m for m in all_matches if m.player_count == 1 and m.user_completed and not m.forfeited]
        
        # Get completed runs for time stats
        completed_runs = [m for m in all_matches if m.user_completed and m.match_time is not None and not m.is_draw and not m.forfeited]
        
        if not completed_runs:
            return "No completed runs found with valid completion times."
            
        times = [m.match_time for m in completed_runs]
        
        # Calculate win rate from competitive matches only
        competitive_matches = len(wins) + len(losses)
        win_rate = len(wins) / competitive_matches * 100 if competitive_matches > 0 else 0
        
        text = f"""
╔═══════════════════════════════════════════════════════════════╗
║  MCSR Ranked Stats for: {analyzer.username:<37} ║
╚═══════════════════════════════════════════════════════════════╝

MATCH SUMMARY
─────────────────────────────────────────────────────────────────
  Total Matches:        {len(all_matches):>6}
  Wins:                 {len(wins):>6} ({win_rate:5.1f}% win rate)
  Losses:               {len(losses):>6}
  Draws:                {len(draws):>6}
  Forfeits:             {len(forfeits):>6}
  Solo Completions:     {len(solo_completions):>6}

COMPLETION STATS (Finished Runs Only)
─────────────────────────────────────────────────────────────────
  Completed Runs:       {len(completed_runs):>6}
  Personal Best:        {self.format_time_ms_to_string(min(times)):>12}
  Average Time:         {self.format_time_ms_to_string(int(sum(times) / len(times))):>12}
  Median Time:          {self.format_time_ms_to_string(int(statistics.median(times))):>12}
  
PERCENTILES
─────────────────────────────────────────────────────────────────"""
        
        # Calculate percentiles
        sorted_times = sorted(times)
        for p in [10, 25, 50, 75, 90, 95, 99]:
            idx = int((p / 100) * (len(sorted_times) - 1))
            time_val = sorted_times[idx]
            text += f"\n  {p:2}th percentile:     {self.format_time_ms_to_string(time_val):>12}"
        
        return text
    
    def generate_best_times_text(self, analyzer, all_matches: List, seasons: Dict, include_private: bool = True) -> str:
        """Generate best times analysis text showing PB progression and top times."""
        if not all_matches:
            return "No match data available for best times analysis."
        
        # Get completed runs for time stats (sorted by time for top times)
        completed_runs = [m for m in all_matches if m.user_completed and m.match_time is not None and not m.is_draw and not m.forfeited]
        
        if not completed_runs:
            return "No completed runs found with valid completion times."
        
        # Sort by time for top times display
        completed_runs_by_time = sorted(completed_runs, key=lambda x: x.match_time)
        
        text = f"""
╔═══════════════════════════════════════════════════════════════╗
║  Best Times for: {analyzer.username:<42} ║
╚═══════════════════════════════════════════════════════════════╝

🏆 TOP 10 PERSONAL BESTS
{'─' * 63}
"""
        
        # Show top 10 times
        for i, match in enumerate(completed_runs_by_time[:10], 1):
            text += f"  {i:>2}. {match.time_str()}  |  {match.date_str()}  |  S{match.season}  |  {match.seed_type}\n"
        
        # PB progression
        text += f"""
📈 PERSONAL BEST PROGRESSION
{'─' * 63}
"""
        
        sorted_by_date = sorted(completed_runs, key=lambda x: x.date)
        current_pb = float('inf')
        pb_count = 0
        
        for match in sorted_by_date:
            if match.match_time < current_pb:
                pb_count += 1
                line = f"  PB #{pb_count}: {match.time_str()}  |  {match.date_str()}"
                if current_pb != float('inf'):
                    improvement = current_pb - match.match_time
                    line += f"  |  -{self.format_time_ms_to_string(int(improvement))}"
                text += line + "\n"
                current_pb = match.match_time
        
        # Add season breakdown at the end
        if seasons:
            text += f"""
📅 SEASON BREAKDOWN
{'─' * 63}
"""
            for season in sorted(seasons.keys(), reverse=True):
                s = seasons[season]
                text += f"  Season {season}: {s['matches']:>3} runs | "
                text += f"Best: {self.format_time_ms_to_string(s['best'])} | "
                text += f"Avg: {self.format_time_ms_to_string(int(s['average']))}\n"
        
        return text
    
    def generate_segment_analysis_text(self, analyzer, filtered_matches: List, 
                                     segment_stats: Dict, split_stats: Dict, 
                                     filter_text: str = "") -> str:
        """Generate segment analysis text using actual UI logic."""
        if not analyzer:
            return "No data loaded."
        
        # Check for segment data
        detailed_matches = [m for m in filtered_matches if m.has_detailed_data]
        detailed_count = len(detailed_matches)
        
        if detailed_count == 0:
            text = f"""
No segment data available{' for current filters' if filter_text else ''}.

{filter_text}
Click "Fetch Segment Data" to download detailed timeline data for your matches.
This will allow you to see:
  • Time to reach each segment (Nether, Bastion, Fortress, etc.)
  • Split times between segments
  • Performance trends for each segment
  
Tip: Use the Season and Seed dropdowns to filter by specific criteria.
"""
            return text
        
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
        
        text = f"""
╔═══════════════════════════════════════════════════════════════╗
║  Segment Analysis for: {analyzer.username:<38} ║
╚═══════════════════════════════════════════════════════════════╝

📊 DATA AVAILABILITY
{'-' * 60}
  Matches with segment data: {detailed_count}
{filter_text}
⏱️ ABSOLUTE TIMES (Time to reach segment)
{'-' * 60}
{'Segment':<18} {'Best':>12} {'Average':>12} {'Median':>12} {'Matches':>8}
{'-' * 60}
"""
        
        for seg_key, seg_name in segment_display.items():
            if seg_key in segment_stats:
                s = segment_stats[seg_key]
                text += f"{seg_name:<18} {self.format_time_ms_to_string(s['best']):>12} "
                text += f"{self.format_time_ms_to_string(int(s['average'])):>12} "
                text += f"{self.format_time_ms_to_string(int(s['median'])):>12} "
                text += f"{s['matches']:>8}\n"
                
        text += f"\n⏱️ SPLIT TIMES (Time spent in segment)\n{'-' * 60}\n"
        text += f"{'Segment':<18} {'Best':>12} {'Average':>12} {'Median':>12}\n"
        text += f"{'-' * 60}\n"
        
        for seg_key, seg_name in segment_display.items():
            if seg_key in split_stats:
                s = split_stats[seg_key]
                text += f"{seg_name:<18} {self.format_time_ms_to_string(s['best']):>12} "
                text += f"{self.format_time_ms_to_string(int(s['average'])):>12} "
                text += f"{self.format_time_ms_to_string(int(s['median'])):>12}\n"
        
        # Add seed type comparison (simplified version)
        seed_types = set(m.seed_type for m in detailed_matches if m.seed_type is not None)
        if len(seed_types) > 1:
            text += f"\n🌱 SEGMENT TIMES BY SEED TYPE\n{'-' * 60}\n"
            
            for seed_type in sorted(seed_types):
                seed_matches = [m for m in detailed_matches if m.seed_type == seed_type]
                if len(seed_matches) >= 3:
                    text += f"\n  {seed_type} ({len(seed_matches)} matches):\n"
                    # This would need actual seed-specific stat calculation
                    text += f"    Data available for detailed analysis\n"
        
        return text
    
    def generate_match_detail_text(self, match, analyzer_username: str) -> str:
        """Generate detailed text for a specific match using actual UI logic."""
        # Clear any existing content first (this would be done by caller)
        
        # Match header
        time_display = match.time_str() if match.user_completed else f"({match.time_str()})"
        
        text = f"""
╔{'═' * 68}╗
║  Match Details: {match.date_str():<47} ║
╚{'═' * 68}╝

📊 MATCH INFORMATION
{'─' * 70}
  Status:        {match.get_status()}
  Your Time:     {time_display if match.match_time else 'Did not finish'}
  Season:        {match.season}
  Seed Type:     {match.seed_type}
  Match Type:    {'Private Room' if match.match_type == 3 else 'Ranked' if match.match_type == 1 else f'Type {match.match_type}'}
  Players:       {match.player_count}
  Forfeited:     {'Yes' if match.forfeited else 'No'}

👥 PLAYER INFORMATION
{'─' * 70}
"""
        
        # Player information
        if match.players:
            text += f"{'Player':<20} {'ELO':>6} {'Change':>8} {'Result':>10}\n"
            text += f"{'─' * 20} {'─' * 6} {'─' * 8} {'─' * 10}\n"
            
            for player in match.players:
                nickname = player.get('nickname', 'Unknown')
                elo_rate = player.get('elo_rate', 'N/A')
                elo_change = player.get('elo_change', 0)
                
                # Mark the analyzed user and determine result
                if nickname.lower() == analyzer_username.lower():
                    nickname += " (You)"
                    if match.is_user_win is True:
                        result = "Won"
                    elif match.is_user_win is False:
                        result = "Lost"
                    elif match.forfeited:
                        result = "Forfeit"
                    else:
                        result = "Draw"
                else:
                    # Determine opponent result
                    if match.is_user_win is True:
                        result = "Lost"
                    elif match.is_user_win is False:
                        result = "Won"
                    elif match.forfeited:
                        result = "Forfeit"
                    else:
                        result = "Draw"
                
                # Format ELO change
                if isinstance(elo_change, int) and elo_change != 0:
                    elo_change_str = f"{elo_change:+d}"
                else:
                    elo_change_str = "0"
                
                # Truncate nickname if too long
                display_name = nickname[:19] if len(nickname) > 19 else nickname
                text += f"{display_name:<20} {str(elo_rate):>6} {elo_change_str:>8} {result:>10}\n"
        
        # Segment timing information
        if match.has_detailed_data and match.segments:
            text += f"\n⏱️ SEGMENT TIMING\n{'─' * 70}\n"
            
            segment_display = {
                'nether_enter': 'Nether Enter',
                'bastion_enter': 'Bastion Enter', 
                'fortress_enter': 'Fortress Enter',
                'blind_portal': 'Blind Portal',
                'stronghold_enter': 'Stronghold Enter',
                'end_enter': 'End Enter',
                'game_end': 'Run Completion'
            }
            
            text += f"{'Segment':<15} │ {'Absolute Time':>12} │ {'Split Time':>12}\n"
            text += f"{'─' * 15} │ {'─' * 12} │ {'─' * 12}\n"
            
            prev_time = 0
            for seg_key, seg_name in segment_display.items():
                if seg_key in match.segments:
                    seg_data = match.segments[seg_key]
                    abs_time = seg_data.get('absolute_time', 0)
                    split_time = seg_data.get('split_time', abs_time - prev_time)
                    
                    abs_str = self.format_time_ms_to_string(abs_time)
                    split_str = self.format_time_ms_to_string(split_time)
                    
                    text += f"{seg_name:<15} │ {abs_str:>12} │ Split: {split_str:>12}\n"
                    prev_time = abs_time
        else:
            text += f"\n{'─' * 70}\n"
            text += "  No detailed segment data available.\n"
            text += "  Click 'Fetch Segment Data' to load timeline information.\n"
        
        text += f"\n{'═' * 70}\n"
        
        return text
    
    def generate_pb_progression_text(self, analyzer, completed_matches: List) -> str:
        """Generate personal best progression and top times text."""
        if not completed_matches:
            return "No completed matches found."
            
        lines = [
            f"╔═══════════════════════════════════════════════════════════════╗",
            f"║  Best Times for: {analyzer.username:<42} ║",
            f"╚═══════════════════════════════════════════════════════════════╝",
            "",
            "🏆 TOP 10 PERSONAL BESTS",
            "─" * 60
        ]
        
        for i, match in enumerate(completed_matches[:10], 1):
            lines.append(f"  {i:>2}. {match.time_str()}  |  {match.date_str()}  |  S{match.season}  |  {match.seed_type}")
            
        # PB progression
        lines.extend([
            "",
            "📈 PERSONAL BEST PROGRESSION",
            "─" * 60
        ])
        
        sorted_by_date = sorted(completed_matches, key=lambda x: x.date)
        current_pb = float('inf')
        pb_count = 0
        
        for match in sorted_by_date:
            if match.match_time < current_pb:
                pb_count += 1
                line = f"  PB #{pb_count}: {match.time_str()}  |  {match.date_str()}"
                if current_pb != float('inf'):
                    improvement = current_pb - match.match_time
                    line += f"  |  -{self.format_time_ms_to_string(int(improvement))}"
                lines.append(line)
                current_pb = match.match_time
                
        return '\n'.join(lines)
    
    
