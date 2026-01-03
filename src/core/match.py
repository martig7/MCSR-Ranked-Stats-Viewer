"""
Match data class for MCSR Ranked speedrun matches.
Handles match information, status determination, and time conversion.
"""

from datetime import datetime
from typing import Dict, Optional, List


class Match:
    """Represents a single MCSR Ranked speedrun match"""
    
    def __init__(self, data: dict, analyzed_username: str = None):
        self.id = data['id']
        self.analyzed_username = analyzed_username
        self.date = data['date']
        self.datetime_obj = datetime.fromtimestamp(self.date)
        self.category = data['category']
        self.forfeited = data['forfeited']
        
        # Handle cases where seed might be None/null
        seed = data.get('seed')
        if seed and isinstance(seed, dict):
            self.seed_id = seed.get('seedID', 'unknown')
        else:
            self.seed_id = data.get('seedID', 'unknown')
            
        self.seed_type = data.get('seedType', 'unknown')
        self.season = data['season']
        
        # Match type and player info for filtering
        self.match_type = data.get('type', 1)  # Default to type 1 (ranked)
        players_list = data.get('players') or []
        self.player_count = len(players_list)
        
        # Store player data for match details
        self.players = []
        self.winner = None
        self.winner_time = None
        self.user_uuid = None  # UUID of the analyzed user
        self.user_player_info = None  # Full player info for the analyzed user
        
        for player in players_list:
            self.players.append({
                'nickname': player.get('nickname', 'Unknown'),
                'uuid': player.get('uuid'),
                'elo_rate': player.get('eloRate'),
                'elo_change': player.get('eloChange')
            })
            
            # Check if this is the analyzed user
            if analyzed_username and player.get('nickname', '').lower() == analyzed_username.lower():
                self.user_uuid = player.get('uuid')
                self.user_player_info = player
        
        # Determine winner from result - handle case where result is None
        result = data.get('result') or {}
        winner_uuid = result.get('uuid')
        self.winner_time = result.get('time')  # This is the winner's completion time
        
        if winner_uuid:
            for player in self.players:
                if player['uuid'] == winner_uuid:
                    self.winner = player['nickname']
                    break
        
        # Determine if the analyzed user won, lost, or the match was a draw/forfeit
        # is_user_win: True if user won, False if user lost, None if draw/no clear winner
        self.is_user_win = None
        self.is_draw = False
        
        if self.user_uuid and winner_uuid:
            self.is_user_win = (self.user_uuid == winner_uuid)
        elif self.user_uuid and winner_uuid is None and not self.forfeited:
            self.is_draw = True
            self.is_user_win = None
        
        # match_time: For stats, we want to use the user's own completion time
        # If user won: match_time = winner_time (their time)
        # If user lost: We don't have their completion time from basic data (they didn't finish first)
        #               Set to None initially - will be populated from segment data if available
        # If draw or solo: match_time from result
        # If forfeited with no winner: no completion time
        # IMPORTANT: Forfeit wins are NOT completed runs - user didn't kill the dragon
        if self.is_user_win is True and not self.forfeited:
            self.match_time = self.winner_time
            self.user_completed = True
        elif self.is_user_win is True and self.forfeited:
            # Won by opponent forfeit - user didn't complete
            self.match_time = self.winner_time
            self.user_completed = False
        elif self.is_user_win is False:
            # Lost - we don't know user's time from basic data
            self.match_time = None
            self.user_completed = False
        elif self.is_draw:
            # Draw - use the match time from result
            self.match_time = self.winner_time
            self.user_completed = False
        elif self.player_count == 1 and not self.forfeited:
            # Solo completion
            self.match_time = self.winner_time
            self.user_completed = True
        elif self.player_count == 1 and self.forfeited:
            # Solo forfeit
            self.match_time = self.winner_time
            self.user_completed = False
        else:
            # Unknown state
            self.match_time = None
            self.user_completed = False
        
        # Initialize segment data (will be populated later if needed)
        self.segments = {}
        self.has_detailed_data = False
        
        # Initialize ELO change data (will be populated from detailed match data)
        self.elo_changes = {}
        
    def time_str(self) -> str:
        """Convert milliseconds to MM:SS.mmm format"""
        if self.match_time is None:
            return "N/A"
        seconds = self.match_time / 1000
        minutes, sec_remainder = divmod(seconds, 60)
        return f'{int(minutes)}:{int(sec_remainder):02d}.{int(self.match_time % 1000):03d}'
    
    def winner_time_str(self) -> str:
        """Convert winner's time to MM:SS.mmm format"""
        if self.winner_time is None:
            return "N/A"
        seconds = self.winner_time / 1000
        minutes, sec_remainder = divmod(seconds, 60)
        return f'{int(minutes)}:{int(sec_remainder):02d}.{int(self.winner_time % 1000):03d}'
    
    def get_status(self) -> str:
        """Get the match status from the analyzed user's perspective"""
        if self.forfeited:
            if self.is_user_win is True:
                return "Forfeit Win"
            elif self.is_user_win is False:
                return "Forfeit Loss"
            else:
                return "Forfeited"
        else:
            return "Won" if self.is_user_win is True else ("Lost" if self.is_user_win is False else "Draw")
    
    def date_str(self) -> str:
        """Format match date as YYYY-MM-DD HH:MM"""
        return self.datetime_obj.strftime("%Y-%m-%d %H:%M")
    
    def get_user_elo_rate(self) -> Optional[int]:
        """Get the user's ELO rating after this match"""
        if self.user_player_info:
            return self.user_player_info.get('eloRate')
        return None
    
    def get_user_elo_change(self) -> Optional[int]:
        """Get the user's ELO change from this match"""
        if self.user_player_info:
            return self.user_player_info.get('eloChange')
        return None
    
    def get_user_elo_before(self) -> Optional[int]:
        """Calculate the user's ELO rating before this match"""
        elo_rate = self.get_user_elo_rate()
        elo_change = self.get_user_elo_change()
        if elo_rate is not None and elo_change is not None:
            return elo_rate - elo_change
        return None
    
    def __str__(self):
        return f'{self.get_status()}: {self.date_str()}, {self.time_str()}'
