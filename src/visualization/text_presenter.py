"""
Text presentation and formatting class for MCSR Ranked Stats UI.
Handles all text generation, formatting, and display logic.
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import statistics
from ..utils.time_formatting import format_time_ms_to_string, format_minutes_to_string


class TextPresenter:
    """Handles all text formatting and generation for the UI."""
    
    def __init__(self):
        """Initialize the text presenter."""
        pass
    
    def format_time_ms_to_string(self, milliseconds: Optional[int]) -> str:
        """Convert milliseconds to MM:SS.mmm format."""
        return format_time_ms_to_string(milliseconds)
    
    def format_minutes_to_string(self, minutes: Optional[float]) -> str:
        """Convert decimal minutes to 'Xm Ys' format."""
        return format_minutes_to_string(minutes)
    
    # Legacy ASCII art methods removed - use RichTextPresenter instead
    
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
    
    # Legacy methods removed - use RichTextPresenter for all text formatting instead
    
    
    
