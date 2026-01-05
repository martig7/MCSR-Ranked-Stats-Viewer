"""
Match statistics utilities for MCSR Ranked User Stats.

This module centralizes match categorization logic that was previously 
duplicated across text_presenter.py and rich_text_presenter.py.
"""

from typing import List, Dict
from ..core.match import Match


def categorize_matches(matches: List[Match]) -> Dict[str, List[Match]]:
    """
    Categorize matches by outcome type.
    
    Args:
        matches: List of Match objects to categorize
        
    Returns:
        Dictionary containing categorized match lists:
        - 'wins': Matches where the user won
        - 'losses': Matches where the user lost  
        - 'draws': Matches that ended in a draw
        - 'forfeits': Matches where the user forfeited
        - 'completions': Matches where the user completed the run
        - 'solo_completions': Solo matches where the user completed
    """
    wins = [m for m in matches if m.is_user_win is True]
    losses = [m for m in matches if m.is_user_win is False]
    draws = [m for m in matches if m.is_draw]
    forfeits = [m for m in matches if m.forfeited and m.is_user_win is None and not m.is_draw]
    completions = [m for m in matches if m.user_completed and m.match_time is not None and not m.is_draw and not m.forfeited]
    solo_completions = [m for m in matches if m.player_count == 1 and m.user_completed and not m.forfeited]
    
    return {
        'wins': wins,
        'losses': losses, 
        'draws': draws,
        'forfeits': forfeits,
        'completions': completions,
        'solo_completions': solo_completions
    }


def calculate_win_rate(matches: List[Match]) -> float:
    """
    Calculate win rate excluding draws and forfeits.
    
    Args:
        matches: List of Match objects
        
    Returns:
        Win rate as a decimal (0.0 to 1.0), or 0.0 if no valid matches
    """
    categories = categorize_matches(matches)
    total_games = len(categories['wins']) + len(categories['losses'])
    
    if total_games == 0:
        return 0.0
        
    return len(categories['wins']) / total_games


def calculate_completion_rate(matches: List[Match]) -> float:
    """
    Calculate completion rate for all matches.
    
    Args:
        matches: List of Match objects
        
    Returns:
        Completion rate as a decimal (0.0 to 1.0), or 0.0 if no matches
    """
    if not matches:
        return 0.0
        
    categories = categorize_matches(matches)
    completed = len(categories['completions'])
    
    return completed / len(matches)