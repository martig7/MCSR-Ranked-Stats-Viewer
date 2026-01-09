"""
Speedrun forecasting utilities for MCSR Ranked User Stats.

This module calculates estimated completion times for incomplete speedruns
based on the player's historical segment averages.
"""

from typing import List, Dict, Optional, Tuple
import statistics
from ..core.match import Match
from ..core.segment_constants import SEGMENT_ORDER


class SpeedrunForecaster:
    """
    Calculates forecasted completion times for incomplete speedruns using rolling averages.
    
    For incomplete runs, estimates remaining segment times based on the player's
    rolling averages at the time of each match, providing more accurate forecasts
    that account for skill progression over time.
    """
    
    def __init__(self, matches: List[Match], rolling_window: int = 20, percentile: float = 50.0):
        """
        Initialize forecaster with match data.
        
        Args:
            matches: List of Match objects with segment data (should be sorted by date)
            rolling_window: Number of recent matches to use for rolling calculations
            percentile: Percentile to use for forecasting (0-100, where 50 = median)
        """
        # Sort matches by date to ensure chronological order
        self.matches = sorted(matches, key=lambda m: m.date)
        self.rolling_window = rolling_window
        self.percentile = percentile
    
    def _calculate_rolling_percentiles(self, match: Match, up_to_index: int) -> Dict[str, float]:
        """
        Calculate rolling segment percentiles using completed matches up to a specific date.
        
        Args:
            match: The match for which to calculate rolling percentiles
            up_to_index: Index of the current match in the sorted matches list
            
        Returns:
            Dict mapping segment names to rolling percentile absolute times in milliseconds
        """
        # Get completed matches before this match's date
        historical_matches = []
        for i in range(up_to_index):
            historical_match = self.matches[i]
            if (historical_match.user_completed and 
                historical_match.has_detailed_data and 
                historical_match.date < match.date):
                historical_matches.append(historical_match)
        
        # Use only the most recent matches within the rolling window
        if len(historical_matches) > self.rolling_window:
            historical_matches = historical_matches[-self.rolling_window:]
        
        # Calculate rolling percentiles for each segment
        rolling_percentiles = {}
        for segment in SEGMENT_ORDER:
            segment_times = []
            for hist_match in historical_matches:
                if segment in hist_match.segments and 'absolute_time' in hist_match.segments[segment]:
                    segment_times.append(hist_match.segments[segment]['absolute_time'])
            
            # Need at least 3 data points for reliable percentile calculation
            if len(segment_times) >= 3:
                rolling_percentiles[segment] = self._calculate_percentile(segment_times, self.percentile)
        
        return rolling_percentiles
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """
        Calculate percentile from a list of values.
        
        Args:
            data: List of numeric values
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile value
        """
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        n = len(sorted_data)
        
        # Handle edge cases
        if percentile <= 0:
            return sorted_data[0]
        if percentile >= 100:
            return sorted_data[-1]
        
        # Calculate percentile using linear interpolation
        index = (percentile / 100.0) * (n - 1)
        lower_index = int(index)
        upper_index = min(lower_index + 1, n - 1)
        
        if lower_index == upper_index:
            return sorted_data[lower_index]
        
        # Linear interpolation between the two closest values
        weight = index - lower_index
        return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    def _get_last_completed_segment(self, match: Match) -> Tuple[Optional[str], Optional[int]]:
        """
        Find the last completed segment and its absolute time for an incomplete match.
        
        Args:
            match: Match object to analyze
            
        Returns:
            Tuple of (last_segment_name, absolute_time) or (None, None) if no segments
        """
        if not match.segments:
            return None, None
        
        # Find the last segment in order that exists in the match
        last_segment = None
        last_time = None
        
        for segment in SEGMENT_ORDER:
            if segment in match.segments and 'absolute_time' in match.segments[segment]:
                last_segment = segment
                last_time = match.segments[segment]['absolute_time']
        
        return last_segment, last_time
    
    def calculate_forecast(self, match: Match) -> Optional[int]:
        """
        Calculate forecasted completion time for a match using rolling averages.
        
        For completed runs, returns actual completion time.
        For incomplete runs, forecasts based on current progress + rolling segment averages
        calculated at the time of the match.
        
        Args:
            match: Match object to forecast
            
        Returns:
            Forecasted completion time in milliseconds, or None if insufficient data
        """
        # If already completed, return actual time
        if match.user_completed and match.match_time is not None:
            return match.match_time
        
        # For incomplete runs, need segment data
        if not match.has_detailed_data or not match.segments:
            return None
        
        # Find the match index in our sorted list
        match_index = None
        for i, m in enumerate(self.matches):
            if m.id == match.id:
                match_index = i
                break
        
        if match_index is None:
            return None
        
        # Calculate rolling percentiles up to this match's time
        rolling_percentiles = self._calculate_rolling_percentiles(match, match_index)
        
        if not rolling_percentiles:
            return None  # No historical data available
        
        last_segment, current_time = self._get_last_completed_segment(match)
        if last_segment is None or current_time is None:
            return None
        
        # Find remaining segments
        last_segment_index = SEGMENT_ORDER.index(last_segment)
        remaining_segments = SEGMENT_ORDER[last_segment_index + 1:]
        
        # If no remaining segments (completed game_end), return current time
        if not remaining_segments:
            return current_time
        
        # Calculate forecast using rolling percentiles at the time of this match
        forecast = current_time
        
        for segment in remaining_segments:
            if segment in rolling_percentiles:
                percentile_abs_time = rolling_percentiles[segment]
                
                # For segments after the first, we need the split time (difference from previous segment)
                if segment == remaining_segments[0]:
                    # First remaining segment: add difference from current position to percentile absolute time
                    if percentile_abs_time > current_time:
                        forecast += (percentile_abs_time - current_time)
                else:
                    # Subsequent segments: add the typical split time for this segment
                    # Calculate typical split time from rolling percentiles
                    prev_segment_index = SEGMENT_ORDER.index(segment) - 1
                    if prev_segment_index >= 0:
                        prev_segment = SEGMENT_ORDER[prev_segment_index]
                        if prev_segment in rolling_percentiles:
                            split_time = percentile_abs_time - rolling_percentiles[prev_segment]
                            if split_time > 0:
                                forecast += split_time
                        else:
                            # Fallback: use historical split times with percentile if available
                            split_times = self._get_historical_split_times(match, match_index, segment)
                            if split_times:
                                forecast += self._calculate_percentile(split_times, self.percentile)
                            else:
                                return None  # Can't forecast without data
                    else:
                        return None
            else:
                # No rolling percentile data for this segment
                return None
        
        return int(forecast)
    
    def _get_historical_split_times(self, current_match: Match, up_to_index: int, segment: str) -> List[float]:
        """
        Get historical split times for a specific segment up to a certain date.
        
        Args:
            current_match: The match for which we're calculating forecast
            up_to_index: Index of the current match in the sorted matches list
            segment: Segment name
            
        Returns:
            List of split times in milliseconds from matches before current_match
        """
        split_times = []
        
        # Get completed matches before this match's date
        for i in range(up_to_index):
            match = self.matches[i]
            if (match.user_completed and 
                match.has_detailed_data and 
                match.date < current_match.date):
                if segment in match.segments and 'split_time' in match.segments[segment]:
                    split_time = match.segments[segment]['split_time']
                    if split_time > 0:  # Valid split time
                        split_times.append(split_time)
        
        # Use only the most recent split times within the rolling window
        if len(split_times) > self.rolling_window:
            split_times = split_times[-self.rolling_window:]
        
        return split_times
    
    def get_forecast_breakdown(self, match: Match) -> Optional[Dict]:
        """
        Get detailed breakdown of forecast calculation for a match using rolling averages.
        
        Args:
            match: Match object to analyze
            
        Returns:
            Dict with forecast details or None if insufficient data
        """
        if match.user_completed and match.match_time is not None:
            return {
                'type': 'completed',
                'actual_time': match.match_time,
                'forecast_time': match.match_time,
                'segments_completed': list(match.segments.keys()) if match.segments else [],
                'segments_forecasted': [],
                'rolling_window_used': 0
            }
        
        # Find the match index in our sorted list
        match_index = None
        for i, m in enumerate(self.matches):
            if m.id == match.id:
                match_index = i
                break
        
        if match_index is None:
            return None
        
        # Calculate rolling percentiles up to this match's time
        rolling_percentiles = self._calculate_rolling_percentiles(match, match_index)
        
        forecast = self.calculate_forecast(match)
        if forecast is None:
            return None
        
        last_segment, current_time = self._get_last_completed_segment(match)
        if last_segment is None:
            return None
        
        last_segment_index = SEGMENT_ORDER.index(last_segment)
        completed_segments = SEGMENT_ORDER[:last_segment_index + 1]
        remaining_segments = SEGMENT_ORDER[last_segment_index + 1:]
        
        # Count how many historical matches were used for rolling averages
        historical_count = 0
        for i in range(match_index):
            hist_match = self.matches[i]
            if (hist_match.user_completed and 
                hist_match.has_detailed_data and 
                hist_match.date < match.date):
                historical_count += 1
        
        rolling_window_used = min(historical_count, self.rolling_window)
        
        return {
            'type': 'forecasted',
            'current_time': current_time,
            'forecast_time': forecast,
            'segments_completed': [s for s in completed_segments if s in match.segments],
            'segments_forecasted': [s for s in remaining_segments if s in rolling_percentiles],
            'last_completed_segment': last_segment,
            'rolling_window_used': rolling_window_used
        }


def create_forecast_results(matches: List[Match], rolling_window: int = 20, percentile: float = 50.0) -> List[Dict]:
    """
    Create forecast results for all matches with available data using rolling percentiles.
    
    Args:
        matches: List of matches to forecast
        rolling_window: Number of recent completed matches to use for rolling calculations
        percentile: Percentile to use for forecasting (0-100, where 25=optimistic, 50=median, 75=conservative)
        
    Returns:
        List of dicts with match info and forecast data, sorted by forecasted time
    """
    forecaster = SpeedrunForecaster(matches, rolling_window=rolling_window, percentile=percentile)
    results = []
    
    for match in matches:
        forecast = forecaster.calculate_forecast(match)
        if forecast is not None:
            breakdown = forecaster.get_forecast_breakdown(match)
            results.append({
                'match': match,
                'forecast_time': forecast,
                'breakdown': breakdown,
                'is_completed': match.user_completed,
                'actual_time': match.match_time if match.user_completed else None
            })
    
    # Sort by forecasted time (best first)
    results.sort(key=lambda x: x['forecast_time'])
    
    return results