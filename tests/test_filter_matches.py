"""
Test suite for MCSRAnalyzer.filter_matches() method.

Tests all filtering parameters to ensure correct match filtering behavior.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from mcsr_stats import MCSRAnalyzer, Match


def create_mock_match(
    match_id=1,
    user_completed=True,
    is_user_win=True,
    is_draw=False,
    forfeited=False,
    match_time=300000,  # 5 minutes in ms
    match_type=1,
    player_count=2,
    season=9,
    seed_type="village",
    has_detailed_data=False,
    user_uuid="test-uuid-123",
    date=None
):
    """Create a mock Match object with specified properties."""
    mock = MagicMock(spec=Match)
    mock.id = match_id
    mock.user_completed = user_completed
    mock.is_user_win = is_user_win
    mock.is_draw = is_draw
    mock.forfeited = forfeited
    mock.match_time = match_time
    mock.match_type = match_type
    mock.player_count = player_count
    mock.season = season
    mock.seed_type = seed_type
    mock.has_detailed_data = has_detailed_data
    mock.user_uuid = user_uuid
    mock.date = date if date else 1704067200 + match_id * 3600  # Base date + hours
    mock.datetime_obj = datetime.fromtimestamp(mock.date)
    return mock


class TestFilterMatchesCompletionFilters(unittest.TestCase):
    """Test completion-related filters."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        self.analyzer.matches = []
    
    def test_completed_only_true(self):
        """Test completed_only=True filters to only completed matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, user_completed=True, is_draw=False, forfeited=False, match_time=300000),
            create_mock_match(match_id=2, user_completed=False, is_draw=False, forfeited=False, match_time=None),
            create_mock_match(match_id=3, user_completed=True, is_draw=True, forfeited=False, match_time=300000),
            create_mock_match(match_id=4, user_completed=False, is_draw=False, forfeited=True, match_time=200000),
        ]
        
        result = self.analyzer.filter_matches(completed_only=True)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)
    
    def test_user_completed_filter_true(self):
        """Test user_completed=True filter."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, user_completed=True),
            create_mock_match(match_id=2, user_completed=False),
            create_mock_match(match_id=3, user_completed=True),
        ]
        
        result = self.analyzer.filter_matches(user_completed=True)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.user_completed for m in result))
    
    def test_user_completed_filter_false(self):
        """Test user_completed=False filter."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, user_completed=True),
            create_mock_match(match_id=2, user_completed=False),
            create_mock_match(match_id=3, user_completed=False),
        ]
        
        result = self.analyzer.filter_matches(user_completed=False)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(not m.user_completed for m in result))
    
    def test_include_draws_false(self):
        """Test include_draws=False excludes draw matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, is_draw=False),
            create_mock_match(match_id=2, is_draw=True),
            create_mock_match(match_id=3, is_draw=False),
        ]
        
        result = self.analyzer.filter_matches(include_draws=False)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(not m.is_draw for m in result))
    
    def test_include_forfeits_false(self):
        """Test include_forfeits=False excludes forfeited matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, forfeited=False),
            create_mock_match(match_id=2, forfeited=True),
            create_mock_match(match_id=3, forfeited=False),
        ]
        
        result = self.analyzer.filter_matches(include_forfeits=False)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(not m.forfeited for m in result))
    
    def test_include_wins_false(self):
        """Test include_wins=False excludes winning matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, is_user_win=True),
            create_mock_match(match_id=2, is_user_win=False),
            create_mock_match(match_id=3, is_user_win=None),  # Draw/unknown
        ]
        
        result = self.analyzer.filter_matches(include_wins=False)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.is_user_win is not True for m in result))
    
    def test_include_losses_false(self):
        """Test include_losses=False excludes losing matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, is_user_win=True),
            create_mock_match(match_id=2, is_user_win=False),
            create_mock_match(match_id=3, is_user_win=None),
        ]
        
        result = self.analyzer.filter_matches(include_losses=False)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.is_user_win is not False for m in result))


class TestFilterMatchesTimeFilters(unittest.TestCase):
    """Test time-related filters."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        self.analyzer.matches = []
    
    def test_require_time_true(self):
        """Test require_time=True filters out matches without time."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, match_time=300000),
            create_mock_match(match_id=2, match_time=None),
            create_mock_match(match_id=3, match_time=400000),
        ]
        
        result = self.analyzer.filter_matches(require_time=True)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.match_time is not None for m in result))
    
    def test_min_time_ms_filter(self):
        """Test min_time_ms filters out fast matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, match_time=60000),   # 1 minute
            create_mock_match(match_id=2, match_time=300000),  # 5 minutes
            create_mock_match(match_id=3, match_time=600000),  # 10 minutes
        ]
        
        result = self.analyzer.filter_matches(min_time_ms=120000)  # 2 minutes min
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.match_time >= 120000 for m in result))
    
    def test_max_time_ms_filter(self):
        """Test max_time_ms filters out slow matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, match_time=60000),   # 1 minute
            create_mock_match(match_id=2, match_time=300000),  # 5 minutes
            create_mock_match(match_id=3, match_time=600000),  # 10 minutes
        ]
        
        result = self.analyzer.filter_matches(max_time_ms=400000)  # ~6.6 minutes max
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.match_time <= 400000 for m in result))
    
    def test_time_range_filter(self):
        """Test combining min and max time filters."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, match_time=60000),   # 1 minute
            create_mock_match(match_id=2, match_time=300000),  # 5 minutes
            create_mock_match(match_id=3, match_time=600000),  # 10 minutes
        ]
        
        result = self.analyzer.filter_matches(min_time_ms=120000, max_time_ms=400000)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 2)
    
    def test_min_time_ms_excludes_null_times(self):
        """Test min_time_ms filter excludes matches with None time."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, match_time=300000),
            create_mock_match(match_id=2, match_time=None),
        ]
        
        result = self.analyzer.filter_matches(min_time_ms=60000)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)


class TestFilterMatchesMatchTypeFilters(unittest.TestCase):
    """Test match type and player count filters."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        self.analyzer.matches = []
    
    def test_include_private_rooms_false(self):
        """Test include_private_rooms=False excludes private room matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, match_type=1, player_count=2),  # Ranked
            create_mock_match(match_id=2, match_type=3, player_count=2),  # Private room
            create_mock_match(match_id=3, match_type=1, player_count=4),  # Multi-player room
            create_mock_match(match_id=4, match_type=2, player_count=2),  # Casual
        ]
        
        result = self.analyzer.filter_matches(include_private_rooms=False)
        
        self.assertEqual(len(result), 2)
        match_ids = [m.id for m in result]
        self.assertIn(1, match_ids)
        self.assertIn(4, match_ids)
    
    def test_match_types_filter(self):
        """Test match_types filter for specific match types."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, match_type=1),
            create_mock_match(match_id=2, match_type=2),
            create_mock_match(match_id=3, match_type=3),
        ]
        
        result = self.analyzer.filter_matches(match_types=[1, 2])
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.match_type in [1, 2] for m in result))
    
    def test_max_player_count_filter(self):
        """Test max_player_count filter."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, player_count=1),
            create_mock_match(match_id=2, player_count=2),
            create_mock_match(match_id=3, player_count=4),
        ]
        
        result = self.analyzer.filter_matches(max_player_count=2)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.player_count <= 2 for m in result))


class TestFilterMatchesSeasonSeedFilters(unittest.TestCase):
    """Test season and seed type filters."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        self.analyzer.matches = []
    
    def test_seasons_filter_single(self):
        """Test filtering by single season."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, season=8),
            create_mock_match(match_id=2, season=9),
            create_mock_match(match_id=3, season=9),
        ]
        
        result = self.analyzer.filter_matches(seasons=[9])
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.season == 9 for m in result))
    
    def test_seasons_filter_multiple(self):
        """Test filtering by multiple seasons."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, season=7),
            create_mock_match(match_id=2, season=8),
            create_mock_match(match_id=3, season=9),
        ]
        
        result = self.analyzer.filter_matches(seasons=[8, 9])
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.season in [8, 9] for m in result))
    
    def test_seed_types_filter_single(self):
        """Test filtering by single seed type."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, seed_type="village"),
            create_mock_match(match_id=2, seed_type="buried_treasure"),
            create_mock_match(match_id=3, seed_type="village"),
        ]
        
        result = self.analyzer.filter_matches(seed_types=["village"])
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.seed_type == "village" for m in result))
    
    def test_seed_types_filter_multiple(self):
        """Test filtering by multiple seed types."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, seed_type="village"),
            create_mock_match(match_id=2, seed_type="buried_treasure"),
            create_mock_match(match_id=3, seed_type="shipwreck"),
        ]
        
        result = self.analyzer.filter_matches(seed_types=["village", "shipwreck"])
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.seed_type in ["village", "shipwreck"] for m in result))


class TestFilterMatchesDataAvailabilityFilters(unittest.TestCase):
    """Test data availability filters."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        self.analyzer.matches = []
    
    def test_has_detailed_data_true(self):
        """Test has_detailed_data=True filter."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, has_detailed_data=True),
            create_mock_match(match_id=2, has_detailed_data=False),
            create_mock_match(match_id=3, has_detailed_data=True),
        ]
        
        result = self.analyzer.filter_matches(has_detailed_data=True)
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all(m.has_detailed_data for m in result))
    
    def test_has_detailed_data_false(self):
        """Test has_detailed_data=False filter."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, has_detailed_data=True),
            create_mock_match(match_id=2, has_detailed_data=False),
        ]
        
        result = self.analyzer.filter_matches(has_detailed_data=False)
        
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0].has_detailed_data)
    
    def test_require_user_identified_true(self):
        """Test require_user_identified=True filter."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, user_uuid="uuid-123", player_count=2),
            create_mock_match(match_id=2, user_uuid=None, player_count=2),
            create_mock_match(match_id=3, user_uuid=None, player_count=1),  # Solo match
        ]
        
        result = self.analyzer.filter_matches(require_user_identified=True)
        
        self.assertEqual(len(result), 2)
        match_ids = [m.id for m in result]
        self.assertIn(1, match_ids)  # Has UUID
        self.assertIn(3, match_ids)  # Solo match (player_count=1)


class TestFilterMatchesSorting(unittest.TestCase):
    """Test sorting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        self.analyzer.matches = []
    
    def test_sort_by_date_ascending(self):
        """Test sorting by date ascending."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, date=1704067200),
            create_mock_match(match_id=2, date=1704153600),
            create_mock_match(match_id=3, date=1704110400),
        ]
        
        result = self.analyzer.filter_matches(sort_by='date', sort_descending=False)
        
        self.assertEqual([m.id for m in result], [1, 3, 2])
    
    def test_sort_by_date_descending(self):
        """Test sorting by date descending."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, date=1704067200),
            create_mock_match(match_id=2, date=1704153600),
            create_mock_match(match_id=3, date=1704110400),
        ]
        
        result = self.analyzer.filter_matches(sort_by='date', sort_descending=True)
        
        self.assertEqual([m.id for m in result], [2, 3, 1])
    
    def test_sort_by_time_ascending(self):
        """Test sorting by time ascending."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, match_time=400000),
            create_mock_match(match_id=2, match_time=200000),
            create_mock_match(match_id=3, match_time=300000),
        ]
        
        result = self.analyzer.filter_matches(sort_by='time', sort_descending=False)
        
        self.assertEqual([m.id for m in result], [2, 3, 1])
    
    def test_sort_by_time_with_none_values(self):
        """Test sorting by time handles None values."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, match_time=400000),
            create_mock_match(match_id=2, match_time=None),
            create_mock_match(match_id=3, match_time=200000),
        ]
        
        result = self.analyzer.filter_matches(sort_by='time', sort_descending=False)
        
        # None should sort to end (infinity)
        self.assertEqual(result[0].id, 3)
        self.assertEqual(result[1].id, 1)
        self.assertEqual(result[2].id, 2)
    
    def test_sort_by_season_ascending(self):
        """Test sorting by season ascending."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, season=9),
            create_mock_match(match_id=2, season=7),
            create_mock_match(match_id=3, season=8),
        ]
        
        result = self.analyzer.filter_matches(sort_by='season', sort_descending=False)
        
        self.assertEqual([m.id for m in result], [2, 3, 1])


class TestFilterMatchesCombinedFilters(unittest.TestCase):
    """Test combining multiple filters."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        self.analyzer.matches = []
    
    def test_combined_completion_and_time_filters(self):
        """Test combining completion and time filters."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, user_completed=True, match_time=300000, forfeited=False, is_draw=False),
            create_mock_match(match_id=2, user_completed=True, match_time=60000, forfeited=False, is_draw=False),  # Too fast
            create_mock_match(match_id=3, user_completed=False, match_time=300000, forfeited=False, is_draw=False),
            create_mock_match(match_id=4, user_completed=True, match_time=400000, forfeited=True, is_draw=False),  # Forfeit
        ]
        
        result = self.analyzer.filter_matches(
            completed_only=True,
            min_time_ms=120000
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)
    
    def test_combined_season_seed_and_sorting(self):
        """Test combining season, seed type filters with sorting."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, season=9, seed_type="village", match_time=400000),
            create_mock_match(match_id=2, season=9, seed_type="buried_treasure", match_time=300000),
            create_mock_match(match_id=3, season=8, seed_type="village", match_time=350000),
            create_mock_match(match_id=4, season=9, seed_type="village", match_time=250000),
        ]
        
        result = self.analyzer.filter_matches(
            seasons=[9],
            seed_types=["village"],
            sort_by='time',
            sort_descending=False
        )
        
        self.assertEqual(len(result), 2)
        self.assertEqual([m.id for m in result], [4, 1])
    
    def test_all_filters_empty_result(self):
        """Test that impossible filter combination returns empty list."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, season=9, seed_type="village"),
            create_mock_match(match_id=2, season=8, seed_type="buried_treasure"),
        ]
        
        result = self.analyzer.filter_matches(
            seasons=[7],  # No matches in season 7
            seed_types=["shipwreck"]  # No shipwreck matches
        )
        
        self.assertEqual(len(result), 0)
    
    def test_no_filters_returns_all(self):
        """Test that no filters returns all matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1),
            create_mock_match(match_id=2),
            create_mock_match(match_id=3),
        ]
        
        result = self.analyzer.filter_matches()
        
        self.assertEqual(len(result), 3)


class TestFilterMatchesEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        self.analyzer.matches = []
    
    def test_empty_matches_list(self):
        """Test filtering empty matches list."""
        self.analyzer.matches = []
        
        result = self.analyzer.filter_matches(completed_only=True)
        
        self.assertEqual(result, [])
    
    def test_single_match_passes_all_filters(self):
        """Test single match that passes all filters."""
        self.analyzer.matches = [
            create_mock_match(
                match_id=1,
                user_completed=True,
                match_time=300000,
                season=9,
                seed_type="village",
                has_detailed_data=True
            )
        ]
        
        result = self.analyzer.filter_matches(
            completed_only=True,
            min_time_ms=60000,
            seasons=[9],
            seed_types=["village"],
            has_detailed_data=True
        )
        
        self.assertEqual(len(result), 1)
    
    def test_single_match_fails_one_filter(self):
        """Test single match that fails one filter."""
        self.analyzer.matches = [
            create_mock_match(
                match_id=1,
                user_completed=True,
                match_time=300000,
                season=8,  # Wrong season
                seed_type="village"
            )
        ]
        
        result = self.analyzer.filter_matches(
            completed_only=True,
            seasons=[9]  # Looking for season 9
        )
        
        self.assertEqual(len(result), 0)
    
    def test_is_user_win_none_handling(self):
        """Test proper handling of is_user_win=None (draws/unknown)."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, is_user_win=True),
            create_mock_match(match_id=2, is_user_win=False),
            create_mock_match(match_id=3, is_user_win=None),
        ]
        
        # Exclude wins AND losses should leave only None
        result = self.analyzer.filter_matches(include_wins=False, include_losses=False)
        
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0].is_user_win)


class TestGetCompletedMatches(unittest.TestCase):
    """Test get_completed_matches uses filter_matches correctly."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        self.analyzer.matches = []
    
    def test_get_completed_matches_uses_filter(self):
        """Test get_completed_matches delegates to filter_matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, user_completed=True, match_time=300000, forfeited=False, is_draw=False),
            create_mock_match(match_id=2, user_completed=False, match_time=300000, forfeited=False, is_draw=False),
            create_mock_match(match_id=3, user_completed=True, match_time=30000, forfeited=False, is_draw=False),  # Too fast (30s)
        ]
        
        result = self.analyzer.get_completed_matches(min_time_seconds=60)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)


class TestGetAllMatchesWithResult(unittest.TestCase):
    """Test get_all_matches_with_result uses filter_matches correctly."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        self.analyzer.matches = []
    
    def test_get_all_matches_with_result_uses_filter(self):
        """Test get_all_matches_with_result delegates to filter_matches."""
        self.analyzer.matches = [
            create_mock_match(match_id=1, user_uuid="uuid-123", player_count=2),
            create_mock_match(match_id=2, user_uuid=None, player_count=2),  # No UUID, not solo
            create_mock_match(match_id=3, user_uuid=None, player_count=1),  # Solo match
        ]
        
        result = self.analyzer.get_all_matches_with_result()
        
        self.assertEqual(len(result), 2)
        match_ids = [m.id for m in result]
        self.assertIn(1, match_ids)
        self.assertIn(3, match_ids)


if __name__ == '__main__':
    unittest.main(verbosity=2)
