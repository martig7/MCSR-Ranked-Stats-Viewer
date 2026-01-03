"""
MCSR Ranked Statistics Analyzer - Core data processing functionality.
Handles API communication, data caching, and match filtering.
"""

import requests
from datetime import datetime, timedelta
import time
import json
import os
from typing import List, Dict, Optional, Any
import statistics

from match import Match
from rate_limiter import RateLimitTracker, load_rate_limit_state, save_rate_limit_state


class MCSRAnalyzer:
    """Core analyzer for MCSR Ranked statistics with API communication and caching."""
    
    # Cache directory for all JSON files
    CACHE_DIR = "CACHE"
    
    def __init__(self, username: str):
        self.username = username
        self.base_url = "https://api.mcsrranked.com/"
        self.matches: List[Match] = []
        
        # Ensure cache directory exists
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        
        # All cache files go in the CACHE folder
        self.cache_file = os.path.join(self.CACHE_DIR, f"{username}_matches.json")
        self.segment_cache_file = os.path.join(self.CACHE_DIR, f"{username}_segments.json")
        self.rate_limit_file = os.path.join(self.CACHE_DIR, f"{username}_rate_limit.json")
        self.rate_limiter = RateLimitTracker()
        
        # Load rate limit state if exists
        load_rate_limit_state(self.rate_limiter, self.rate_limit_file)
    
    def _load_segment_cache(self) -> Dict[int, Dict]:
        """Load cached segment data"""
        try:
            if os.path.exists(self.segment_cache_file):
                with open(self.segment_cache_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_segment_cache(self, segment_data: Dict[int, Dict]):
        """Save segment data to cache"""
        try:
            with open(self.segment_cache_file, 'w') as f:
                json.dump(segment_data, f)
        except Exception:
            pass
    
    def _apply_cached_segment_data(self):
        """Apply cached segment data to loaded matches"""
        segment_cache = self._load_segment_cache()
        applied_count = 0
        
        for match in self.matches:
            if str(match.id) in segment_cache:
                cached_data = segment_cache[str(match.id)]
                match.segments = cached_data.get('segments', {})
                match.has_detailed_data = bool(match.segments)
                if match.has_detailed_data:
                    applied_count += 1
        
        return applied_count
    
    def fetch_matches_for_seasons(self, seasons: List[int] = None, use_cache: bool = True, max_matches: int = None) -> List[Match]:
        """Fetch matches for specific seasons"""
        if seasons is None:
            return self.fetch_all_matches(use_cache, max_matches)
        
        all_matches = []
        for season in seasons:
            season_cache_file = os.path.join(self.CACHE_DIR, f"{self.username}_season_{season}_matches.json")
            
            if use_cache and os.path.exists(season_cache_file):
                try:
                    with open(season_cache_file, 'r') as f:
                        cached_data = json.load(f)
                        season_matches = [Match(data, self.username) for data in cached_data]
                        all_matches.extend(season_matches)
                except Exception:
                    # Fetch fresh data if cache fails
                    season_matches = self._fetch_season_data(season, 5000)
                    all_matches.extend([Match(data, self.username) for data in season_matches])
            else:
                season_matches = self._fetch_season_data(season, 5000)
                all_matches.extend([Match(data, self.username) for data in season_matches])
                
                # Cache the season data
                try:
                    with open(season_cache_file, 'w') as f:
                        json.dump(season_matches, f, indent=2)
                except Exception:
                    pass
        
        self.matches = all_matches
        self._apply_cached_segment_data()
        save_rate_limit_state(self.rate_limiter, self.rate_limit_file)
        return self.matches
    
    def _fetch_season_data(self, season: int, max_matches: int = 5000) -> List[dict]:
        """Fetch all matches for a specific season using before/after pagination"""
        matches = []
        before_id = None
        batch_size =100  # Fetch in batches of 100
        
        while len(matches) < max_matches:
            if not self.rate_limiter.can_make_request():
                wait_time = self.rate_limiter.get_wait_time()
                if wait_time > 0:
                    time.sleep(wait_time)
            
            url = f"{self.base_url}users/{self.username}/matches"
            params = {'season': season, 'count': min(batch_size, max_matches - len(matches))}
            if before_id:
                params['before'] = before_id
                
            print(f"DEBUG: Fetching season {season}, before_id={before_id}, count={params['count']}, URL: {url}")
            
            try:
                self.rate_limiter.record_request()
                response = requests.get(url, params=params)
                print(f"DEBUG: Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    batch_matches = data.get('data', [])
                    print(f"DEBUG: Season {season} batch returned {len(batch_matches)} matches")
                    
                    if not batch_matches:
                        break
                        
                    matches.extend(batch_matches)
                    before_id = batch_matches[-1]['id']  # Use last match ID for next batch
                    
                elif response.status_code == 429:
                    time.sleep(10)
                    continue
                else:
                    break
            except requests.RequestException:
                break
        
        return matches[:max_matches]
    
    def fetch_all_matches(self, use_cache: bool = True, max_matches: int = None) -> List[Match]:
        """Fetch all matches using cache or API"""
        print(f"DEBUG: fetch_all_matches called for user {self.username}, use_cache={use_cache}")
        print(f"DEBUG: cache_file path: {self.cache_file}")
        
        if use_cache and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cached_data = json.load(f)
                    
                    # Detect cache format - new format has 'analyzed_username' field
                    if cached_data and 'analyzed_username' in cached_data[0]:
                        # New format: already processed Match objects
                        self.matches = []
                        for match_dict in cached_data:
                            match = Match.__new__(Match)  # Create without calling __init__
                            match.__dict__.update(match_dict)
                            # Convert datetime string back to datetime object if needed
                            if isinstance(match.datetime_obj, str):
                                match.datetime_obj = datetime.fromisoformat(match.datetime_obj.replace('Z', '+00:00'))
                            self.matches.append(match)
                    else:
                        # Old format: raw API data
                        self.matches = [Match(data, self.username) for data in cached_data]
                    
                    print(f"DEBUG: Loaded {len(self.matches)} matches from cache")
                    self._apply_cached_segment_data()
                    return self.matches
            except Exception:
                pass
        
        # Fetch data from API
        print("DEBUG: Cache not found or fetching fresh data from API")
        if not use_cache:
            # Fresh fetch: get all seasons (full refresh)
            seasons = self._discover_seasons()
            print(f"DEBUG: Discovered seasons: {seasons}")
            if not seasons:
                self.matches = self._fetch_current_season_only(max_matches or 5000)
            else:
                self.matches = []
                for season in seasons:
                    season_matches = self._fetch_season_data(season, 5000)
                    self.matches.extend([Match(data, self.username) for data in season_matches])
        else:
            # Incremental refresh: start from newest and stop on existing matches
            self.matches = self._fetch_incremental_data(max_matches)
        
        # Cache the data
        try:
            match_data = [match.__dict__ for match in self.matches]
            with open(self.cache_file, 'w') as f:
                json.dump(match_data, f, indent=2, default=str)
        except Exception:
            pass
        
        print(f"DEBUG: Successfully fetched {len(self.matches)} total matches")
        self._apply_cached_segment_data()
        save_rate_limit_state(self.rate_limiter, self.rate_limit_file)
        return self.matches
    
    def _discover_seasons(self) -> List[int]:
        """Discover which seasons have matches for this user"""
        seasons = []
        
        for season in range(3, 15):  # Check seasons 3-14
            if not self.rate_limiter.can_make_request():
                wait_time = self.rate_limiter.get_wait_time()
                if wait_time > 0:
                    time.sleep(wait_time)
            
            url = f"{self.base_url}users/{self.username}/matches"
            params = {'season': season, 'count': 1}  # Just check if any matches exist
            print(f"DEBUG: Discovering season {season}, URL: {url}")
            
            try:
                self.rate_limiter.record_request()
                response = requests.get(url, params=params)
                print(f"DEBUG: Season discovery response: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        seasons.append(season)
                        print(f"DEBUG: Season {season} has data, added to list")
                time.sleep(0.1)  # Small delay between requests
            except requests.RequestException:
                continue
        
        return seasons
    
    def _fetch_current_season_only(self, max_matches: int = 5000) -> List[Match]:
        """Fetch matches from current season only using before/after pagination"""
        matches_data = []
        before_id = None
        batch_size = 50
        
        while len(matches_data) < max_matches:
            if not self.rate_limiter.can_make_request():
                wait_time = self.rate_limiter.get_wait_time()
                if wait_time > 0:
                    time.sleep(wait_time)
            
            url = f"{self.base_url}users/{self.username}/matches"
            params = {'count': min(batch_size, max_matches - len(matches_data))}
            if before_id:
                params['before'] = before_id
                
            print(f"DEBUG: Fetching current season, before_id={before_id}, count={params['count']}, URL: {url}")
            
            try:
                self.rate_limiter.record_request()
                response = requests.get(url, params=params)
                print(f"DEBUG: Current season response: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    batch_matches = data.get('data', [])
                    print(f"DEBUG: Current season batch returned {len(batch_matches)} matches")
                    
                    if not batch_matches:
                        break
                        
                    matches_data.extend(batch_matches)
                    before_id = batch_matches[-1]['id']
                    
                elif response.status_code == 429:
                    time.sleep(10)
                    continue
                else:
                    break
            except requests.RequestException:
                break
        
        return [Match(data, self.username) for data in matches_data[:max_matches]]
    
    def filter_matches(
        self,
        completed_only: bool = False,
        user_completed: Optional[bool] = None,
        include_draws: bool = True,
        include_forfeits: bool = True,
        include_wins: bool = True,
        include_losses: bool = True,
        require_time: bool = False,
        min_time_ms: Optional[int] = None,
        max_time_ms: Optional[int] = None,
        include_private_rooms: bool = True,
        match_types: Optional[List[int]] = None,
        max_player_count: Optional[int] = None,
        seasons: Optional[List[int]] = None,
        seed_types: Optional[List[str]] = None,
        has_detailed_data: Optional[bool] = None,
        require_user_identified: bool = False,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = 'date',
        sort_descending: bool = True
    ) -> List[Match]:
        """Filter matches with comprehensive filtering options (see individual filter methods for details)"""
        filter_params = locals().copy()
        filter_params.pop('self')
        
        filtered = self.matches.copy()
        filtered = self._apply_completion_filters(filtered, **filter_params)
        filtered = self._apply_time_filters(filtered, **filter_params)
        filtered = self._apply_match_type_filters(filtered, **filter_params)
        filtered = self._apply_categorical_filters(filtered, **filter_params)
        filtered = self._apply_date_filters(filtered, **filter_params)
        return self._sort_matches(filtered, sort_by, sort_descending)
    
    def _apply_completion_filters(self, matches: List[Match], **kwargs) -> List[Match]:
        """Apply completion-based filters (completed_only, user_completed, wins, losses, draws, forfeits)"""
        filtered = matches
        
        # Apply completed_only filter first (most restrictive)
        if kwargs.get('completed_only', False):
            filtered = [m for m in filtered if (
                m.user_completed and 
                m.match_time is not None and 
                not m.is_draw and 
                not m.forfeited
            )]
        
        # User completion filter
        user_completed = kwargs.get('user_completed')
        if user_completed is not None:
            filtered = [m for m in filtered if m.user_completed == user_completed]
        
        # Win/loss/draw filters
        if not kwargs.get('include_draws', True):
            filtered = [m for m in filtered if not m.is_draw]
        if not kwargs.get('include_forfeits', True):
            filtered = [m for m in filtered if not m.forfeited]
        if not kwargs.get('include_wins', True):
            filtered = [m for m in filtered if m.is_user_win is not True]
        if not kwargs.get('include_losses', True):
            filtered = [m for m in filtered if m.is_user_win is not False]
        
        return filtered
    
    def _apply_time_filters(self, matches: List[Match], **kwargs) -> List[Match]:
        """Apply time-based filters (require_time, min_time_ms, max_time_ms)"""
        filtered = matches
        
        if kwargs.get('require_time', False):
            filtered = [m for m in filtered if m.match_time is not None]
        
        min_time_ms = kwargs.get('min_time_ms')
        if min_time_ms is not None:
            filtered = [m for m in filtered if m.match_time is not None and m.match_time >= min_time_ms]
        
        max_time_ms = kwargs.get('max_time_ms')
        if max_time_ms is not None:
            filtered = [m for m in filtered if m.match_time is not None and m.match_time <= max_time_ms]
        
        return filtered
    
    def _apply_match_type_filters(self, matches: List[Match], **kwargs) -> List[Match]:
        """Apply match type filters (include_private_rooms, match_types, max_player_count, require_user_identified)"""
        filtered = matches
        
        if not kwargs.get('include_private_rooms', True):
            filtered = [m for m in filtered if not (m.match_type == 3 or m.player_count > 2)]
        
        match_types = kwargs.get('match_types')
        if match_types is not None:
            filtered = [m for m in filtered if m.match_type in match_types]
        
        max_player_count = kwargs.get('max_player_count')
        if max_player_count is not None:
            filtered = [m for m in filtered if m.player_count <= max_player_count]
        
        if kwargs.get('require_user_identified', False):
            filtered = [m for m in filtered if m.user_uuid is not None or m.player_count == 1]
        
        # Data availability filters
        has_detailed_data = kwargs.get('has_detailed_data')
        if has_detailed_data is not None:
            filtered = [m for m in filtered if m.has_detailed_data == has_detailed_data]
        
        return filtered
    
    def _apply_categorical_filters(self, matches: List[Match], **kwargs) -> List[Match]:
        """Apply categorical filters (seasons, seed_types)"""
        filtered = matches
        
        seasons = kwargs.get('seasons')
        if seasons is not None:
            filtered = [m for m in filtered if m.season in seasons]
        
        seed_types = kwargs.get('seed_types')
        if seed_types is not None:
            filtered = [m for m in filtered if m.seed_type in seed_types]
        
        return filtered
    
    def _apply_date_filters(self, matches: List[Match], **kwargs) -> List[Match]:
        """Apply date range filters (date_from, date_to)"""
        filtered = matches
        
        date_from = kwargs.get('date_from')
        if date_from is not None:
            filtered = [m for m in filtered if m.datetime_obj >= date_from]
        
        date_to = kwargs.get('date_to')
        if date_to is not None:
            filtered = [m for m in filtered if m.datetime_obj <= date_to]
        
        return filtered
    
    def _sort_matches(self, matches: List[Match], sort_by: str = 'date', sort_descending: bool = True) -> List[Match]:
        """Sort matches by specified criteria"""
        if sort_by == 'date':
            matches.sort(key=lambda x: x.date, reverse=sort_descending)
        elif sort_by == 'time':
            matches.sort(key=lambda x: x.match_time if x.match_time is not None else float('inf'), 
                        reverse=sort_descending)
        elif sort_by == 'season':
            matches.sort(key=lambda x: x.season, reverse=sort_descending)
        
        return matches
    
    def get_completed_matches(self, include_private_rooms: bool = True, min_time_seconds: int = 60) -> List[Match]:
        """Get matches where user actually completed the run"""
        min_time_ms = min_time_seconds * 1000 if min_time_seconds > 0 else None
        
        return self.filter_matches(
            completed_only=True,
            min_time_ms=min_time_ms,
            include_private_rooms=include_private_rooms
        )
    
    def get_all_matches_with_result(self, include_private_rooms: bool = True) -> List[Match]:
        """Get all matches where we can determine win/loss/draw result"""
        return self.filter_matches(
            include_private_rooms=include_private_rooms,
            require_user_identified=True
        )
    
    def season_breakdown(self, include_private_rooms: bool = True, seed_type_filter: str = None) -> Dict[int, Dict]:
        """Get statistics breakdown by season"""
        filters = {
            'include_private_rooms': include_private_rooms,
            'completed_only': True
        }
        if seed_type_filter:
            filters['seed_types'] = [seed_type_filter]
            
        completed_matches = self.filter_matches(**filters)
        
        seasons = {}
        for match in completed_matches:
            if match.season not in seasons:
                seasons[match.season] = {
                    'matches': 0,
                    'times': []
                }
            seasons[match.season]['matches'] += 1
            seasons[match.season]['times'].append(match.match_time)
        
        # Calculate statistics
        for season_data in seasons.values():
            times = season_data['times']
            season_data['best'] = min(times)
            season_data['worst'] = max(times)
            season_data['average'] = statistics.mean(times)
            season_data['median'] = statistics.median(times)
            if len(times) > 1:
                season_data['std_dev'] = statistics.stdev(times)
            else:
                season_data['std_dev'] = 0
        
        return seasons
    
    def seed_type_breakdown(self, include_private_rooms: bool = True, season_filter: int = None) -> Dict[str, Dict]:
        """Get statistics breakdown by seed type"""
        filters = {
            'include_private_rooms': include_private_rooms,
            'completed_only': True
        }
        if season_filter:
            filters['seasons'] = [season_filter]
            
        completed_matches = self.filter_matches(**filters)
        
        seed_types = {}
        for match in completed_matches:
            if match.seed_type not in seed_types:
                seed_types[match.seed_type] = {
                    'matches': 0,
                    'times': []
                }
            seed_types[match.seed_type]['matches'] += 1
            seed_types[match.seed_type]['times'].append(match.match_time)
        
        # Calculate statistics
        for seed_data in seed_types.values():
            times = seed_data['times']
            seed_data['best'] = min(times)
            seed_data['worst'] = max(times)
            seed_data['average'] = statistics.mean(times)
            seed_data['median'] = statistics.median(times)
            if len(times) > 1:
                seed_data['std_dev'] = statistics.stdev(times)
            else:
                seed_data['std_dev'] = 0
        
        return seed_types
    
    def get_segment_breakdown(self) -> Dict[str, Dict]:
        """Get segment timing statistics"""
        matches_with_segments = [m for m in self.matches if m.has_detailed_data and m.segments]
        if not matches_with_segments:
            return {}
        
        segment_names = ['nether_enter', 'bastion_enter', 'fortress_enter', 'blind_portal', 
                        'stronghold_enter', 'end_enter', 'game_end']
        
        segment_stats = {}
        for segment in segment_names:
            times = []
            for match in matches_with_segments:
                if segment in match.segments:
                    # For game_end, only include if user actually completed
                    if segment == 'game_end' and not match.user_completed:
                        continue
                    times.append(match.segments[segment]['absolute_time'])
            
            if times:
                segment_stats[segment] = {
                    'matches': len(times),
                    'best': min(times),
                    'worst': max(times),
                    'average': statistics.mean(times),
                    'median': statistics.median(times),
                    'std_dev': statistics.stdev(times) if len(times) > 1 else 0
                }
        
        return segment_stats
    
    def get_elo_progression(self, matches: List[Match] = None) -> List[Dict[str, Any]]:
        """
        Get ELO progression over time for the player.
        NOTE: ELO chart feature disabled due to API data issues, but method kept for data access.
        
        Args:
            matches: Optional list of matches to analyze. If None, uses all matches.
            
        Returns:
            List of dictionaries with 'date', 'elo_after', 'elo_change', 'elo_before' keys
        """
        if matches is None:
            matches = self.matches
        
        # Filter matches that have ELO data and sort by date
        elo_matches = [m for m in matches if m.get_user_elo_rate() is not None]
        elo_matches.sort(key=lambda x: x.date)
        
        progression = []
        for match in elo_matches:
            elo_after = match.get_user_elo_rate()
            elo_change = match.get_user_elo_change()
            elo_before = match.get_user_elo_before()
            
            progression.append({
                'date': match.datetime_obj,
                'elo_after': elo_after,
                'elo_change': elo_change,
                'elo_before': elo_before,
                'match_id': match.id,
                'result': match.get_status()
            })
        
        return progression
    
    def fetch_segment_data(self, max_matches: int = 100, force_refresh: bool = False) -> int:
        """Fetch detailed segment data for matches"""
        # Load existing segment cache
        segment_cache = self._load_segment_cache()
        
        # Get matches that need segment data (sorted by date descending - newest first)
        matches_to_fetch = []
        sorted_matches = sorted(self.matches, key=lambda m: m.date, reverse=True)
        for match in sorted_matches:
            if len(matches_to_fetch) >= max_matches:
                break
            cache_key = str(match.id)
            if force_refresh or cache_key not in segment_cache:
                matches_to_fetch.append(match)
        
        if not matches_to_fetch:
            return 0
        
        fetched_count = 0
        for match in matches_to_fetch:
            if not self.rate_limiter.can_make_request():
                wait_time = self.rate_limiter.get_wait_time()
                if wait_time > 0:
                    time.sleep(wait_time)
            
            url = f"{self.base_url}matches/{match.id}"
            
            try:
                self.rate_limiter.record_request()
                response = requests.get(url)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Extract the actual match data from the nested structure
                    if 'data' not in response_data:
                        print(f"DEBUG: Match {match.id} - No 'data' field in response")
                        continue
                    
                    data = response_data['data']
                    
                    # Extract segment data from timelines (note: plural)
                    segments = {}
                    if 'timelines' in data and data['timelines']:
                        # Filter timeline events to only include recognized speedrun segments
                        segment_mappings = {
                            'story.enter_the_nether': 'nether_enter',
                            'nether.find_bastion': 'bastion_enter',
                            'nether.find_fortress': 'fortress_enter',
                            'projectelo.timeline.blind_travel': 'blind_portal',
                            'story.follow_ender_eye': 'stronghold_enter',
                            # Note: end_enter and game_end might need different mapping
                        }
                        
                        for event in data['timelines']:
                            event_type = event.get('type')
                            event_time = event.get('time')
                            player_uuid = event.get('uuid')
                            
                            # Only track events for the analyzed user
                            if (event_type in segment_mappings and 
                                event_time is not None and 
                                player_uuid == match.user_uuid):
                                
                                segment_name = segment_mappings[event_type]
                                segments[segment_name] = {
                                    'absolute_time': event_time
                                }
                    
                    # Store ELO change information if available
                    match.elo_changes = {}
                    if 'changes' in data and data['changes']:
                        # changes is a list of objects, not a dictionary
                        for change_data in data['changes']:
                            player_uuid = change_data.get('uuid')
                            if player_uuid:
                                match.elo_changes[player_uuid] = {
                                    'change': change_data.get('change'),
                                    'eloRate': change_data.get('eloRate')
                                }
                    
                    # Calculate split times
                    segment_order = ['nether_enter', 'bastion_enter', 'fortress_enter', 
                                   'blind_portal', 'stronghold_enter', 'end_enter', 'game_end']
                    
                    prev_time = 0
                    for segment in segment_order:
                        if segment in segments:
                            abs_time = segments[segment]['absolute_time']
                            segments[segment]['split_time'] = abs_time - prev_time
                            prev_time = abs_time
                    
                    # Update match
                    match.segments = segments
                    match.has_detailed_data = bool(segments)
                    
                    # Cache the data
                    segment_cache[str(match.id)] = {
                        'segments': segments,
                        'fetched_at': time.time()
                    }
                    
                    fetched_count += 1
                    
                elif response.status_code == 429:
                    time.sleep(10)
                    continue
                    
                time.sleep(0.1)  # Small delay between requests
                
            except requests.RequestException:
                continue
        
        # Save updated cache
        self._save_segment_cache(segment_cache)
        save_rate_limit_state(self.rate_limiter, self.rate_limit_file)
        
        return fetched_count
    
    def _fetch_incremental_data(self, max_matches: int = None) -> List[Match]:
        """
        Fetch new matches incrementally, starting from newest season and stopping
        when we encounter a match ID that already exists in our cache.
        """
        print("DEBUG: Starting incremental fetch")
        
        # Load existing matches to check for duplicates
        existing_match_ids = set()
        try:
            with open(self.cache_file, 'r') as f:
                cached_data = json.load(f)
                if isinstance(cached_data, list) and len(cached_data) > 0:
                    if isinstance(cached_data[0], dict) and 'id' in cached_data[0]:
                        # New format: match objects
                        existing_match_ids = {match_data['id'] for match_data in cached_data}
                    else:
                        # Old format: raw API data  
                        existing_match_ids = {data['id'] for data in cached_data}
                print(f"DEBUG: Found {len(existing_match_ids)} existing match IDs in cache")
        except Exception:
            print("DEBUG: No existing cache found")
        
        # Discover seasons and fetch newest first
        seasons = self._discover_seasons()
        if not seasons:
            print("DEBUG: No seasons found, fetching current season only")
            return self._fetch_current_season_only(max_matches or 1000)
        
        # Sort seasons in descending order (newest first)
        seasons = sorted(seasons, reverse=True)
        print(f"DEBUG: Will check seasons in order: {seasons}")
        
        all_new_matches = []
        total_fetched = 0
        
        for season in seasons:
            print(f"DEBUG: Fetching season {season}")
            season_matches = self._fetch_season_data(season, 1000)
            
            new_matches_this_season = []
            found_existing = False
            
            # Sort season matches by ID descending (newest first within season)
            season_matches_sorted = sorted(season_matches, key=lambda x: x['id'], reverse=True)
            
            for match_data in season_matches_sorted:
                match_id = match_data['id']
                
                if match_id in existing_match_ids:
                    print(f"DEBUG: Found existing match {match_id}, stopping incremental fetch")
                    found_existing = True
                    break
                
                new_matches_this_season.append(Match(match_data, self.username))
                total_fetched += 1
                
                # Respect max_matches limit
                if max_matches and total_fetched >= max_matches:
                    print(f"DEBUG: Reached max_matches limit of {max_matches}")
                    found_existing = True
                    break
            
            all_new_matches.extend(new_matches_this_season)
            print(f"DEBUG: Season {season}: fetched {len(new_matches_this_season)} new matches")
            
            # If we found existing matches, we can stop (older seasons will have older matches)
            if found_existing:
                break
        
        print(f"DEBUG: Incremental fetch complete. Total new matches: {len(all_new_matches)}")
        
        # Combine with existing matches
        if existing_match_ids:
            try:
                with open(self.cache_file, 'r') as f:
                    cached_data = json.load(f)
                    if isinstance(cached_data, list) and len(cached_data) > 0:
                        if isinstance(cached_data[0], dict) and 'id' in cached_data[0]:
                            # New format: match objects
                            existing_matches = [Match(data, self.username) for data in cached_data]
                        else:
                            # Old format: raw API data
                            existing_matches = [Match(data, self.username) for data in cached_data]
                        
                        all_new_matches.extend(existing_matches)
            except Exception:
                pass
        
        return all_new_matches
    
    def clear_user_data(self, clear_detailed: bool = False):
        """Clear cached user data"""
        files_to_remove = []
        
        # Always clear basic match data
        if os.path.exists(self.cache_file):
            files_to_remove.append(self.cache_file)
        
        # Clear rate limit data
        if os.path.exists(self.rate_limit_file):
            files_to_remove.append(self.rate_limit_file)
        
        if clear_detailed:
            # Also clear detailed segment data
            segment_cache_file = f"CACHE/{self.username}_segments.json"
            if os.path.exists(segment_cache_file):
                files_to_remove.append(segment_cache_file)
        
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f"DEBUG: Removed {file_path}")
            except Exception as e:
                print(f"DEBUG: Failed to remove {file_path}: {e}")
        
        # Reset in-memory data
        self.matches = []
        
        return len(files_to_remove)
    
    def basic_stats(self, include_private_rooms: bool = True) -> Dict[str, Any]:
        """Get basic statistics summary"""
        try:
            completed_matches = self.get_completed_matches(include_private_rooms=include_private_rooms)
            all_matches = self.get_all_matches_with_result(include_private_rooms=include_private_rooms)
            
            if not completed_matches:
                return {
                    'total_matches': len(all_matches),
                    'completed': 0,
                    'best_time': None,
                    'average_time': None,
                    'win_rate': 0
                }
            
            times = [match.match_time for match in completed_matches if match.match_time is not None]
            wins = len([m for m in all_matches if m.is_user_win is True])
            
            return {
                'total_matches': len(all_matches),
                'completed': len(completed_matches),
                'best_time': min(times) if times else None,
                'average_time': statistics.mean(times) if times else None,
                'win_rate': (wins / len(all_matches)) * 100 if all_matches else 0
            }
        except Exception:
            return {'error': 'Failed to calculate basic stats'}
    
    def fetch_detailed_match_data(self, max_new_matches: int = 100) -> int:
        """Alias for fetch_segment_data for backward compatibility"""
        return self.fetch_segment_data(max_matches=max_new_matches)
    
    def get_segment_stats(self, matches: List['Match']) -> Dict[str, Dict[str, Any]]:
        """Calculate segment stats for a list of matches.
        
        For game_end segment, only includes matches where user actually completed (killed dragon).
        
        Args:
            matches: List of Match objects to analyze
            
        Returns:
            Dict mapping segment name to stats dict with keys:
            matches, best, worst, average, median, std_dev
        """
        segment_names = ['nether_enter', 'bastion_enter', 'fortress_enter', 'blind_portal', 
                        'stronghold_enter', 'end_enter', 'game_end']
        
        segment_stats = {}
        
        for segment in segment_names:
            times = []
            for match in matches:
                if segment in match.segments:
                    # For game_end, only include if user actually completed the run
                    if segment == 'game_end' and not match.user_completed:
                        continue
                    times.append(match.segments[segment]['absolute_time'])
            
            if len(times) >= 1:
                segment_stats[segment] = {
                    'matches': len(times),
                    'best': min(times),
                    'worst': max(times),
                    'average': statistics.mean(times),
                    'median': statistics.median(times),
                    'std_dev': statistics.stdev(times) if len(times) > 1 else 0
                }
        
        return segment_stats
    
    def get_split_stats(self, matches: List['Match']) -> Dict[str, Dict[str, Any]]:
        """Calculate split stats for a list of matches.
        
        For incomplete matches (draws/forfeits), excludes the last recorded segment
        since the player was still in that segment when the match ended.
        For game_end, only includes matches where user actually completed.
        
        Args:
            matches: List of Match objects to analyze
            
        Returns:
            Dict mapping segment name to stats dict with keys:
            matches, best, worst, average, median, std_dev
        """
        segment_names = ['nether_enter', 'bastion_enter', 'fortress_enter', 'blind_portal', 
                        'stronghold_enter', 'end_enter', 'game_end']
        
        split_stats = {}
        
        for segment in segment_names:
            split_times = []
            for match in matches:
                if segment in match.segments:
                    # For game_end, only include if user actually completed the run
                    if segment == 'game_end' and not match.user_completed:
                        continue
                    
                    # For incomplete matches (draw/forfeit), skip the last segment
                    # since the player was still in that segment when match ended
                    if match.is_draw or match.forfeited:
                        # Find the last recorded segment for this match
                        last_segment = None
                        for seg in segment_names:
                            if seg in match.segments:
                                last_segment = seg
                        # Skip if this is the last segment (incomplete)
                        if segment == last_segment:
                            continue
                    
                    split_times.append(match.segments[segment]['split_time'])
            
            if len(split_times) >= 1:
                split_stats[segment] = {
                    'matches': len(split_times),
                    'best': min(split_times),
                    'worst': max(split_times),
                    'average': statistics.mean(split_times),
                    'median': statistics.median(split_times),
                    'std_dev': statistics.stdev(split_times) if len(split_times) > 1 else 0
                }
        
        return split_stats