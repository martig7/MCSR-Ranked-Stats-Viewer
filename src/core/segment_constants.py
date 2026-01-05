"""
Segment constants for MCSR Ranked User Stats.

This module centralizes segment display names and ordering that were
previously duplicated across multiple files (text_presenter.py, 
rich_text_presenter.py, segment_analysis.py, match_info_dialog.py).
"""

# Mapping of internal segment names to user-friendly display names
SEGMENT_DISPLAY_NAMES = {
    'nether_enter': 'Nether Enter',
    'bastion_enter': 'Bastion Enter',
    'fortress_enter': 'Fortress Enter',
    'blind_portal': 'Blind Portal',
    'stronghold_enter': 'Stronghold Enter',
    'end_enter': 'End Enter',
    'game_end': 'Run Completion'
}

# Standard ordering of segments for display purposes
SEGMENT_ORDER = [
    'nether_enter',
    'bastion_enter', 
    'fortress_enter',
    'blind_portal',
    'stronghold_enter',
    'end_enter',
    'game_end'
]

# Set of all valid segment keys for validation
VALID_SEGMENTS = set(SEGMENT_ORDER)

def get_segment_display_name(segment_key: str) -> str:
    """
    Get the user-friendly display name for a segment.
    
    Args:
        segment_key: Internal segment identifier
        
    Returns:
        Human-readable segment name, or the key itself if not found
    """
    return SEGMENT_DISPLAY_NAMES.get(segment_key, segment_key)

def is_valid_segment(segment_key: str) -> bool:
    """
    Check if a segment key is valid.
    
    Args:
        segment_key: Internal segment identifier
        
    Returns:
        True if the segment key is valid, False otherwise
    """
    return segment_key in VALID_SEGMENTS