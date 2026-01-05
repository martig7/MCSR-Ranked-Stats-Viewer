"""
Filter management utilities for MCSR Ranked User Stats.

This module centralizes filter logic that was previously duplicated
across main_window.py, comparison_handler.py, and segment_analysis.py.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class FilterManager:
    """
    Manages filter state and provides centralized filter operations.
    
    Eliminates duplicate filter logic across UI components and handlers.
    """
    
    def __init__(self, ui_context):
        """
        Initialize filter manager with UI context.
        
        Args:
            ui_context: Reference to main UI class for accessing filter variables
        """
        self.ui = ui_context
    
    def build_filter_kwargs(self, completed_only: bool = False) -> Dict[str, Any]:
        """
        Build filter parameters from current UI state.
        
        Args:
            completed_only: Whether to include only completed matches
            
        Returns:
            Dictionary of filter parameters for analyzer.filter_matches()
        """
        filter_kwargs = {}
        
        # Season filter
        season_filter = self.ui.season_var.get()
        if season_filter != 'All':
            try:
                filter_kwargs['seasons'] = [int(season_filter)]
            except (ValueError, AttributeError):
                pass
        
        # Seed type filter  
        seed_filter = self.ui.seed_filter_var.get()
        if seed_filter != 'All':
            filter_kwargs['seed_types'] = [seed_filter]
        
        # Private rooms filter
        if hasattr(self.ui, 'include_private_var'):
            filter_kwargs['include_private_rooms'] = self.ui.include_private_var.get()
        
        # Completion filter
        if completed_only:
            filter_kwargs['completed_only'] = True
        
        # Advanced filters (if available)
        if hasattr(self.ui, '_filter_date_from') and self.ui._filter_date_from:
            filter_kwargs['date_from'] = self.ui._filter_date_from
            
        if hasattr(self.ui, '_filter_date_to') and self.ui._filter_date_to:
            filter_kwargs['date_to'] = self.ui._filter_date_to
            
        if hasattr(self.ui, '_filter_time_min') and self.ui._filter_time_min is not None:
            filter_kwargs['min_time_ms'] = self.ui._filter_time_min
            
        if hasattr(self.ui, '_filter_time_max') and self.ui._filter_time_max is not None:
            filter_kwargs['max_time_ms'] = self.ui._filter_time_max
            
        if hasattr(self.ui, '_filter_result') and self.ui._filter_result and self.ui._filter_result != 'All':
            filter_kwargs['result'] = self.ui._filter_result
            
        if hasattr(self.ui, '_filter_forfeit_matches') and not self.ui._filter_forfeit_matches:
            filter_kwargs['exclude_forfeits'] = True
            
        if hasattr(self.ui, '_filter_require_time') and self.ui._filter_require_time:
            filter_kwargs['require_time'] = True
        
        return filter_kwargs
    
    def get_filtered_matches(self, analyzer, completed_only: bool = True):
        """
        Get filtered matches from analyzer using current filter state.
        
        Args:
            analyzer: MCSRAnalyzer instance
            completed_only: Whether to include only completed matches
            
        Returns:
            List of filtered matches
        """
        if not analyzer:
            return []
            
        filter_kwargs = self.build_filter_kwargs(completed_only=completed_only)
        return analyzer.filter_matches(**filter_kwargs)
    
    def get_all_filtered_matches(self, analyzer):
        """
        Get all filtered matches (including incomplete) using current filter state.
        
        Args:
            analyzer: MCSRAnalyzer instance
            
        Returns:
            List of all filtered matches
        """
        return self.get_filtered_matches(analyzer, completed_only=False)
    
    def get_comparison_filtered_matches(self, comparison_handler, completed_only: bool = True):
        """
        Get filtered matches from comparison player using same filter state.
        
        Args:
            comparison_handler: ComparisonHandler instance
            completed_only: Whether to include only completed matches
            
        Returns:
            List of filtered comparison matches, or empty list if no comparison
        """
        if not comparison_handler or not comparison_handler.analyzer:
            return []
            
        return self.get_filtered_matches(comparison_handler.analyzer, completed_only)
    
    def get_filter_text(self) -> str:
        """
        Generate descriptive filter text for display purposes.
        
        Returns:
            String describing current active filters, or empty string if none
        """
        filters = []
        
        season_filter = self.ui.season_var.get()
        if season_filter != 'All':
            filters.append(f"Season {season_filter}")
            
        seed_filter = self.ui.seed_filter_var.get()
        if seed_filter != 'All':
            filters.append(f"Seed: {seed_filter}")
        
        # Advanced filters
        if hasattr(self.ui, '_filter_date_from') and self.ui._filter_date_from:
            date_str = self.ui._filter_date_from.strftime('%Y-%m-%d')
            filters.append(f"From: {date_str}")
            
        if hasattr(self.ui, '_filter_date_to') and self.ui._filter_date_to:
            date_str = self.ui._filter_date_to.strftime('%Y-%m-%d')
            filters.append(f"To: {date_str}")
            
        if hasattr(self.ui, '_filter_time_min') and self.ui._filter_time_min is not None:
            from .time_formatting import format_time_ms_to_string
            time_str = format_time_ms_to_string(self.ui._filter_time_min)
            filters.append(f"Min time: {time_str}")
            
        if hasattr(self.ui, '_filter_time_max') and self.ui._filter_time_max is not None:
            from .time_formatting import format_time_ms_to_string
            time_str = format_time_ms_to_string(self.ui._filter_time_max)
            filters.append(f"Max time: {time_str}")
            
        if hasattr(self.ui, '_filter_result') and self.ui._filter_result and self.ui._filter_result != 'All':
            filters.append(f"Result: {self.ui._filter_result}")
        
        if filters:
            return f"Filters: {' | '.join(filters)}"
        else:
            return ""
    
    def get_filter_indicator(self) -> str:
        """
        Generate short filter indicator text for UI display.
        
        Returns:
            Compact string indicating active filters, or "All" if none
        """
        filter_kwargs = self.build_filter_kwargs()
        
        if not filter_kwargs:
            return "All"
        
        indicators = []
        
        if 'seasons' in filter_kwargs:
            indicators.append(f"S{filter_kwargs['seasons'][0]}")
            
        if 'seed_types' in filter_kwargs:
            indicators.append(filter_kwargs['seed_types'][0])
        
        if 'include_private_rooms' in filter_kwargs and not filter_kwargs['include_private_rooms']:
            indicators.append("Public")
            
        if len(indicators) == 0 and len(filter_kwargs) > 0:
            indicators.append("Filtered")
            
        return " | ".join(indicators) if indicators else "All"
    
    def has_active_filters(self) -> bool:
        """
        Check if any filters are currently active.
        
        Returns:
            True if any filters are active, False otherwise
        """
        filter_kwargs = self.build_filter_kwargs()
        return bool(filter_kwargs)
    
    def get_active_filter_count(self) -> int:
        """
        Get the number of active filters.
        
        Returns:
            Number of active filter parameters
        """
        filter_kwargs = self.build_filter_kwargs()
        return len(filter_kwargs)
    
    def clear_advanced_filters(self):
        """
        Clear advanced filter settings (date, time, result filters).
        
        Note: Season and seed filters are managed by UI dropdowns separately.
        """
        if hasattr(self.ui, '_filter_date_from'):
            self.ui._filter_date_from = None
        if hasattr(self.ui, '_filter_date_to'):
            self.ui._filter_date_to = None
        if hasattr(self.ui, '_filter_time_min'):
            self.ui._filter_time_min = None
        if hasattr(self.ui, '_filter_time_max'):
            self.ui._filter_time_max = None
        if hasattr(self.ui, '_filter_result'):
            self.ui._filter_result = 'All'
        if hasattr(self.ui, '_filter_forfeit_matches'):
            self.ui._filter_forfeit_matches = True
        if hasattr(self.ui, '_filter_require_time'):
            self.ui._filter_require_time = False