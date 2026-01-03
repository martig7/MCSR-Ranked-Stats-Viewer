"""
Match Info Dialog - Displays detailed information about a specific match.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from match import Match


class MatchInfoDialog:
    """Dialog window for displaying detailed match information"""
    
    def __init__(self, parent, match: Match, text_presenter=None):
        """
        Initialize the match info dialog
        
        Args:
            parent: Parent window
            match: Match object to display
            text_presenter: TextPresenter instance for formatting
        """
        self.match = match
        self.text_presenter = text_presenter
        
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
        
        # Create notebook for different info tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Basic Info Tab
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="Basic Info")
        self._create_basic_info(basic_frame)
        
        # Players Tab
        players_frame = ttk.Frame(notebook, padding="10")
        notebook.add(players_frame, text="Players")
        self._create_players_info(players_frame)
        
        # Segments Tab (if available)
        if self.match.has_detailed_data and self.match.segments:
            segments_frame = ttk.Frame(notebook, padding="10")
            notebook.add(segments_frame, text="Segments")
            self._create_segments_info(segments_frame)
        
        # Raw Data Tab
        raw_frame = ttk.Frame(notebook, padding="10")
        notebook.add(raw_frame, text="Raw Data")
        self._create_raw_data(raw_frame)
        
        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_button = ttk.Button(button_frame, text="Close", command=self._on_close)
        close_button.pack(side=tk.RIGHT)
    
    def _create_basic_info(self, parent):
        """Create basic match information display"""
        # Use scrollable text widget
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Generate basic match info
        info_text = self._generate_basic_info_text()
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)
    
    def _generate_basic_info_text(self) -> str:
        """Generate basic match information text"""
        lines = []
        
        # Match identification
        lines.append("=== MATCH IDENTIFICATION ===")
        lines.append(f"Match ID: {self.match.id}")
        lines.append(f"Date: {self.match.date_str()}")
        lines.append(f"Time: {self.match.time_str()}")
        lines.append("")
        
        # Match outcome
        lines.append("=== MATCH OUTCOME ===")
        lines.append(f"Status: {self.match.get_status()}")
        lines.append(f"User completed: {'Yes' if self.match.user_completed else 'No'}")
        
        if self.match.match_time:
            completion_time = self.match.match_time / 1000 / 60  # Convert to minutes
            lines.append(f"Completion time: {completion_time:.2f} minutes ({self.match.match_time}ms)")
        else:
            lines.append("Completion time: N/A")
        
        if self.match.is_user_win is not None:
            result = "Win" if self.match.is_user_win else "Loss"
            lines.append(f"Result: {result}")
        else:
            lines.append("Result: Draw/Unknown")
        
        lines.append("")
        
        # Match settings
        lines.append("=== MATCH SETTINGS ===")
        lines.append(f"Season: {self.match.season}")
        lines.append(f"Seed type: {self.match.seed_type or 'Unknown'}")
        lines.append(f"Match type: {self.match.match_type}")
        lines.append(f"Player count: {self.match.player_count}")
        lines.append(f"Forfeited: {'Yes' if self.match.forfeited else 'No'}")
        lines.append(f"Is draw: {'Yes' if self.match.is_draw else 'No'}")
        lines.append("")
        
        # User info
        lines.append("=== USER INFORMATION ===")
        lines.append(f"User UUID: {self.match.user_uuid or 'Not identified'}")
        if hasattr(self.match, 'user_player_info') and self.match.user_player_info:
            user_info = self.match.user_player_info
            lines.append(f"Username: {user_info.get('username', 'Unknown')}")
            if 'eloRate' in user_info:
                lines.append(f"ELO Rating: {user_info['eloRate']}")
            if 'eloChange' in user_info:
                change = user_info['eloChange']
                change_str = f"+{change}" if change > 0 else str(change)
                lines.append(f"ELO Change: {change_str}")
        lines.append("")
        
        # Data availability
        lines.append("=== DATA AVAILABILITY ===")
        lines.append(f"Has detailed data: {'Yes' if self.match.has_detailed_data else 'No'}")
        if self.match.has_detailed_data and self.match.segments:
            segment_count = len(self.match.segments)
            lines.append(f"Segments available: {segment_count}")
            lines.append(f"Segments: {', '.join(self.match.segments.keys())}")
        
        return "\n".join(lines)
    
    def _create_players_info(self, parent):
        """Create players information display"""
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Generate players info
        info_text = self._generate_players_info_text()
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)
    
    def _generate_players_info_text(self) -> str:
        """Generate players information text"""
        lines = []
        
        if not hasattr(self.match, 'players') or not self.match.players:
            lines.append("No player information available.")
            return "\n".join(lines)
        
        lines.append("=== PLAYERS IN MATCH ===")
        lines.append("")
        
        for i, player in enumerate(self.match.players, 1):
            lines.append(f"--- Player {i} ---")
            lines.append(f"Username: {player.get('username', 'Unknown')}")
            lines.append(f"UUID: {player.get('uuid', 'Unknown')}")
            
            if 'eloRate' in player:
                lines.append(f"ELO Rating: {player['eloRate']}")
            if 'eloChange' in player:
                change = player['eloChange']
                change_str = f"+{change}" if change > 0 else str(change)
                lines.append(f"ELO Change: {change_str}")
            
            if 'completionTime' in player:
                if player['completionTime']:
                    completion_time = player['completionTime'] / 1000 / 60
                    lines.append(f"Completion time: {completion_time:.2f} minutes")
                else:
                    lines.append("Completion time: Did not finish")
            
            lines.append(f"Forfeited: {'Yes' if player.get('forfeited', False) else 'No'}")
            
            # Identify if this is the analyzed user
            if self.match.user_uuid and player.get('uuid') == self.match.user_uuid:
                lines.append(">>> This is the analyzed player <<<")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _create_segments_info(self, parent):
        """Create segments information display"""
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Generate segments info
        info_text = self._generate_segments_info_text()
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)
    
    def _generate_segments_info_text(self) -> str:
        """Generate segments timing information"""
        if not self.match.segments:
            return "No segment timing data available."
        
        lines = []
        lines.append("=== SEGMENT TIMING ===")
        lines.append("")
        
        # Define display names
        segment_display = {
            'nether_enter': 'Nether Enter',
            'bastion_enter': 'Bastion Enter', 
            'fortress_enter': 'Fortress Enter',
            'blind_portal': 'Blind Portal',
            'stronghold_enter': 'Stronghold Enter',
            'end_enter': 'End Enter',
            'game_end': 'Game End'
        }
        
        lines.append(f"{'Segment':<20} {'Absolute':<12} {'Split':<12}")
        lines.append("-" * 45)
        
        for segment_key, segment_data in self.match.segments.items():
            display_name = segment_display.get(segment_key, segment_key)
            abs_time = segment_data.get('absolute_time', 0) / 1000  # Convert to seconds
            split_time = segment_data.get('split_time', 0) / 1000
            
            abs_str = f"{abs_time/60:.2f}m" if abs_time > 60 else f"{abs_time:.1f}s"
            split_str = f"{split_time/60:.2f}m" if split_time > 60 else f"{split_time:.1f}s"
            
            lines.append(f"{display_name:<20} {abs_str:<12} {split_str:<12}")
        
        return "\n".join(lines)
    
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


def show_match_info_dialog(parent, match: Match, text_presenter=None):
    """
    Convenience function to show match info dialog
    
    Args:
        parent: Parent window
        match: Match object to display
        text_presenter: Optional TextPresenter for formatting
    """
    MatchInfoDialog(parent, match, text_presenter)