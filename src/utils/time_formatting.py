"""
Shared time formatting utilities for MCSR Ranked User Stats.

This module consolidates time formatting methods that were previously
duplicated across multiple files (text_presenter.py, rich_text_presenter.py, 
segment_analysis.py, match_info_dialog.py).
"""

from typing import Optional


def format_time_ms_to_string(milliseconds: Optional[int]) -> str:
    """
    Convert milliseconds to MM:SS.mmm format.
    
    Args:
        milliseconds: Time in milliseconds, or None
        
    Returns:
        Formatted time string (e.g., "23:45.123") or "N/A" if None
    """
    if milliseconds is None:
        return "N/A"
    
    seconds = milliseconds / 1000
    minutes, sec_remainder = divmod(seconds, 60)
    return f'{int(minutes)}:{int(sec_remainder):02d}.{int(milliseconds % 1000):03d}'


def format_minutes_to_string(minutes: Optional[float]) -> str:
    """
    Convert decimal minutes to 'Xm Ys' format.
    
    Args:
        minutes: Time in decimal minutes, or None
        
    Returns:
        Formatted duration string (e.g., "23m 45s") or "N/A" if None
    """
    if minutes is None:
        return "N/A"
    
    m = int(minutes)
    s = int((minutes - m) * 60)
    return f'{m}m {s}s'