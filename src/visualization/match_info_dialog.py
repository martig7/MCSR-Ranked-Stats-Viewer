"""
Match Info Dialog - Displays detailed information about a specific match.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from ..core.match import Match
from ..ui.widgets.rich_text_widget import RichTextWidget


class MatchInfoDialog:
    """Dialog window for displaying detailed match information"""
    
    def __init__(self, parent, match: Match, rich_text_presenter=None):
        """
        Initialize the match info dialog
        
        Args:
            parent: Parent window
            match: Match object to display
            rich_text_presenter: RichTextPresenter instance for modern formatting
        """
        self.match = match
        self.rich_text_presenter = rich_text_presenter
        
        # Create the dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Match Details - {match.date_str()}")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog on parent
        self._center_dialog(parent)
        
        self._create_widgets()
        
        # Focus on dialog
        self.dialog.focus_set()
        
        # Handle close button
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _center_dialog(self, parent):
        """Center the dialog window on the parent"""
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create and layout the dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = f"Match Details - {self.match.date_str()}"
        title_label = ttk.Label(main_frame, text=title, font=("TkDefaultFont", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Create tabbed interface with enhanced rich text widgets
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Basic Info Tab - Use RichTextWidget
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="Match Details")
        self._create_enhanced_basic_info(basic_frame)
        
        # Players Tab - Use RichTextWidget  
        players_frame = ttk.Frame(notebook, padding="10")
        notebook.add(players_frame, text="Players")
        self._create_enhanced_players_info(players_frame)
        
        # Segments Tab (if available) - Use RichTextWidget
        if self.match.has_detailed_data and self.match.segments:
            segments_frame = ttk.Frame(notebook, padding="10")
            notebook.add(segments_frame, text="Segments")
            self._create_enhanced_segments_info(segments_frame)
        
        # Raw Data Tab - Keep as plain text
        raw_frame = ttk.Frame(notebook, padding="10")
        notebook.add(raw_frame, text="Raw Data")
        self._create_raw_data(raw_frame)
        
        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_button = ttk.Button(button_frame, text="Close", command=self._on_close)
        close_button.pack(side=tk.RIGHT)
    
    def _create_enhanced_basic_info(self, parent):
        """Create enhanced basic match information using RichTextWidget"""
        rich_widget = RichTextWidget(parent, theme="dark")
        rich_widget.pack(fill=tk.BOTH, expand=True)
        
        if self.rich_text_presenter:
            # Use the modern match detail renderer
            self.rich_text_presenter.render_match_detail(rich_widget, self.match, "")
        else:
            # Fallback to manual rich text formatting
            self._manual_basic_info(rich_widget)
    
    def _manual_basic_info(self, widget):
        """Manual rich text formatting for basic info when no presenter available"""
        widget.add_heading(f"Match Details - {self.match.date_str()}", level=1)
        
        # Match Information
        match_info = {
            "Status": self.match.get_status(),
            "Date": self.match.date_str(),
            "Season": str(self.match.season),
            "Seed Type": str(self.match.seed_type or "Unknown"),
            "Match Type": 'Private Room' if self.match.match_type == 3 else 'Ranked' if self.match.match_type == 1 else f'Type {self.match.match_type}',
            "Players": str(self.match.player_count),
            "Forfeited": "Yes" if self.match.forfeited else "No"
        }
        
        if self.match.match_time:
            match_info["Your Time"] = self.match.time_str() if self.match.user_completed else f"({self.match.time_str()})"
        else:
            match_info["Your Time"] = "Did not finish"
        
        widget.add_stats_block("📊 Match Information", match_info)
        widget.finalize()
    
    def _create_enhanced_players_info(self, parent):
        """Create enhanced players information using RichTextWidget"""
        rich_widget = RichTextWidget(parent, theme="dark")
        rich_widget.pack(fill=tk.BOTH, expand=True)
        
        widget = rich_widget
        widget.add_heading("Players in Match", level=2)
        
        if not hasattr(self.match, 'players') or not self.match.players:
            widget.add_text("No player information available.", ['muted'])
            widget.finalize()
            return
        
        # Create players table
        headers = ["Player", "ELO", "Change", "Result", "Time"]
        rows = []
        
        for player in self.match.players:
            username = player.get('username', 'Unknown')
            elo_rate = str(player.get('elo_rate', 'N/A'))
            elo_change = player.get('elo_change', 0)
            elo_change_str = f"{elo_change:+d}" if isinstance(elo_change, int) and elo_change != 0 else "0"
            
            # Determine result and completion time
            completion_time = "Did not finish"
            if 'completionTime' in player and player['completionTime']:
                completion_time = f"{player['completionTime'] / 1000 / 60:.2f}m"
            
            # Mark analyzed user
            if self.match.user_uuid and player.get('uuid') == self.match.user_uuid:
                username += " (You)"
                if self.match.is_user_win is True:
                    result = "Won"
                elif self.match.is_user_win is False:
                    result = "Lost"
                elif self.match.forfeited:
                    result = "Forfeit"
                else:
                    result = "Draw"
            else:
                # Opponent result (inverse of user result)
                if self.match.is_user_win is True:
                    result = "Lost"
                elif self.match.is_user_win is False:
                    result = "Won" 
                elif self.match.forfeited:
                    result = "Forfeit"
                else:
                    result = "Draw"
            
            rows.append([username, elo_rate, elo_change_str, result, completion_time])
        
        widget.add_table(headers, rows)
        widget.finalize()
    
    def _create_enhanced_segments_info(self, parent):
        """Create enhanced segments information using RichTextWidget"""
        rich_widget = RichTextWidget(parent, theme="dark")
        rich_widget.pack(fill=tk.BOTH, expand=True)
        
        widget = rich_widget
        widget.add_heading("Segment Timing", level=2)
        
        if not self.match.segments:
            widget.add_text("No segment timing data available.", ['muted'])
            widget.finalize()
            return
        
        # Create segments table
        headers = ["Segment", "Absolute Time", "Split Time"]
        rows = []
        
        # Define segment order and display names
        segment_order = [
            ('nether_enter', 'Nether Enter'),
            ('bastion_enter', 'Bastion Enter'),
            ('fortress_enter', 'Fortress Enter'),
            ('blind_portal', 'Blind Portal'),
            ('stronghold_enter', 'Stronghold Enter'),
            ('end_enter', 'End Enter'),
            ('game_end', 'Game End')
        ]
        
        for segment_key, display_name in segment_order:
            if segment_key not in self.match.segments:
                continue
            
            segment_data = self.match.segments[segment_key]
            abs_time = segment_data.get('absolute_time', 0) / 1000  # Convert to seconds
            split_time = segment_data.get('split_time', 0) / 1000
            
            # Format as MM:SS.mmm
            abs_str = f"{int(abs_time // 60)}:{int(abs_time % 60):02d}.{int((abs_time % 1) * 1000):03d}"
            split_str = f"{int(split_time // 60)}:{int(split_time % 60):02d}.{int((split_time % 1) * 1000):03d}"
            
            rows.append([display_name, abs_str, split_str])
        
        widget.add_table(headers, rows)
        widget.finalize()

    def _create_raw_data(self, parent):
        """Create raw match data display"""
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 8))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Show raw match data (excluding some large/redundant fields)
        import json
        
        # Create a clean representation of match data
        match_dict = {}
        for attr_name in dir(self.match):
            if not attr_name.startswith('_') and not callable(getattr(self.match, attr_name)):
                value = getattr(self.match, attr_name)
                # Convert datetime objects to strings
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                match_dict[attr_name] = value
        
        raw_text = json.dumps(match_dict, indent=2, default=str, ensure_ascii=False)
        text_widget.insert(tk.END, raw_text)
        text_widget.config(state=tk.DISABLED)
    
    def _on_close(self):
        """Handle dialog close"""
        self.dialog.grab_release()
        self.dialog.destroy()


def show_match_info_dialog(parent, match: Match, rich_text_presenter=None):
    """
    Convenience function to show match info dialog
    
    Args:
        parent: Parent window
        match: Match object to display
        rich_text_presenter: Optional RichTextPresenter for modern formatting
    """
    MatchInfoDialog(parent, match, rich_text_presenter)