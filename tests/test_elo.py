"""
Unit tests for ELO charting functionality in MCSR Ranked User Statistics.
Tests ELO data extraction, progression calculation, chart rendering, and comparison features.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from datetime import datetime, timedelta
from mcsr_ui import MCSRStatsUI
from match import Match
from mcsr_stats import MCSRAnalyzer
from chart_views import EloChart


class TestMatchEloMethods(unittest.TestCase):
    """Test ELO-related methods in the Match class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_time = datetime(2024, 1, 1, 12, 0, 0)
        
    def _create_match_data_with_elo(self, elo_rate=1500, elo_change=25, nickname="testuser"):
        """Create mock match data with ELO information."""
        return {
            'id': 12345,
            'date': int(self.base_time.timestamp()),
            'category': 'Ranked',
            'forfeited': False,
            'seedType': 'Set Seed',
            'season': 5,
            'type': 1,
            'players': [
                {
                    'nickname': nickname,
                    'uuid': 'test-uuid-123',
                    'eloRate': elo_rate,
                    'eloChange': elo_change
                },
                {
                    'nickname': 'opponent',
                    'uuid': 'opponent-uuid',
                    'eloRate': 1450,
                    'eloChange': -20
                }
            ],
            'result': {
                'uuid': 'test-uuid-123',
                'time': 300000  # 5 minutes
            }
        }
    
    def test_get_user_elo_rate(self):
        """Test retrieving user's ELO rating after match."""
        match_data = self._create_match_data_with_elo(elo_rate=1525, elo_change=25)
        match = Match(match_data, "testuser")
        
        self.assertEqual(match.get_user_elo_rate(), 1525)
    
    def test_get_user_elo_change(self):
        """Test retrieving user's ELO change from match."""
        match_data = self._create_match_data_with_elo(elo_rate=1525, elo_change=25)
        match = Match(match_data, "testuser")
        
        self.assertEqual(match.get_user_elo_change(), 25)
    
    def test_get_user_elo_before(self):
        """Test calculating user's ELO before match."""
        match_data = self._create_match_data_with_elo(elo_rate=1525, elo_change=25)
        match = Match(match_data, "testuser")
        
        self.assertEqual(match.get_user_elo_before(), 1500)
    
    def test_elo_methods_with_no_user_data(self):
        """Test ELO methods when user is not in match."""
        match_data = self._create_match_data_with_elo(nickname="otheruser")
        match = Match(match_data, "testuser")
        
        self.assertIsNone(match.get_user_elo_rate())
        self.assertIsNone(match.get_user_elo_change())
        self.assertIsNone(match.get_user_elo_before())
    
    def test_elo_before_with_negative_change(self):
        """Test ELO before calculation with negative change (loss)."""
        match_data = self._create_match_data_with_elo(elo_rate=1475, elo_change=-25)
        match = Match(match_data, "testuser")
        
        self.assertEqual(match.get_user_elo_before(), 1500)
    
    def test_elo_methods_with_missing_data(self):
        """Test ELO methods when some data is missing."""
        match_data = self._create_match_data_with_elo()
        # Remove elo data
        match_data['players'][0].pop('eloRate', None)
        match_data['players'][0].pop('eloChange', None)
        
        match = Match(match_data, "testuser")
        
        self.assertIsNone(match.get_user_elo_rate())
        self.assertIsNone(match.get_user_elo_change())
        self.assertIsNone(match.get_user_elo_before())


class TestMCSRAnalyzerEloProgression(unittest.TestCase):
    """Test ELO progression functionality in MCSRAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = MCSRAnalyzer("testuser")
        self.base_time = datetime(2024, 1, 1, 12, 0, 0)
        
    def _create_mock_matches_with_elo(self, count=5):
        """Create mock matches with ELO progression."""
        matches = []
        base_elo = 1500
        
        for i in range(count):
            # Alternate wins and losses
            is_win = i % 2 == 0
            elo_change = 20 if is_win else -15
            current_elo = base_elo + (i * 5) + elo_change
            
            match_data = {
                'id': 1000 + i,
                'date': int((self.base_time + timedelta(days=i)).timestamp()),
                'category': 'Ranked',
                'forfeited': False,
                'seedType': 'Set Seed',
                'season': 5,
                'type': 1,
                'players': [
                    {
                        'nickname': 'testuser',
                        'uuid': 'test-uuid',
                        'eloRate': current_elo,
                        'eloChange': elo_change
                    }
                ],
                'result': {'uuid': 'test-uuid', 'time': 300000}
            }
            
            match = Match(match_data, "testuser")
            matches.append(match)
            base_elo = current_elo - elo_change  # Update for next iteration
        
        return matches
    
    def test_get_elo_progression_basic(self):
        """Test basic ELO progression calculation."""
        matches = self._create_mock_matches_with_elo(3)
        self.analyzer.matches = matches
        
        progression = self.analyzer.get_elo_progression()
        
        self.assertEqual(len(progression), 3)
        
        # Check structure of progression data
        first_point = progression[0]
        self.assertIn('date', first_point)
        self.assertIn('elo_after', first_point)
        self.assertIn('elo_change', first_point)
        self.assertIn('elo_before', first_point)
        self.assertIn('match_id', first_point)
        self.assertIn('result', first_point)
    
    def test_get_elo_progression_sorted_by_date(self):
        """Test that ELO progression is sorted by date."""
        matches = self._create_mock_matches_with_elo(5)
        # Shuffle matches
        matches = [matches[2], matches[0], matches[4], matches[1], matches[3]]
        self.analyzer.matches = matches
        
        progression = self.analyzer.get_elo_progression()
        
        # Should be sorted by date
        dates = [point['date'] for point in progression]
        self.assertEqual(dates, sorted(dates))
    
    def test_get_elo_progression_filters_no_elo_data(self):
        """Test that matches without ELO data are filtered out."""
        matches = self._create_mock_matches_with_elo(3)
        
        # Create a match without ELO data
        no_elo_data = {
            'id': 9999,
            'date': int(self.base_time.timestamp()),
            'category': 'Ranked',
            'forfeited': False,
            'seedType': 'Set Seed',
            'season': 5,
            'type': 1,
            'players': [{'nickname': 'testuser', 'uuid': 'test-uuid'}],
            'result': {'uuid': 'test-uuid', 'time': 300000}
        }
        no_elo_match = Match(no_elo_data, "testuser")
        matches.append(no_elo_match)
        
        self.analyzer.matches = matches
        progression = self.analyzer.get_elo_progression()
        
        # Should only include matches with ELO data
        self.assertEqual(len(progression), 3)
    
    def test_get_elo_progression_with_custom_matches(self):
        """Test ELO progression with custom match list."""
        all_matches = self._create_mock_matches_with_elo(5)
        selected_matches = all_matches[1:4]  # Select middle 3 matches
        
        self.analyzer.matches = all_matches
        progression = self.analyzer.get_elo_progression(selected_matches)
        
        self.assertEqual(len(progression), 3)
        
        # Verify the progression uses the selected matches
        match_ids = {point['match_id'] for point in progression}
        expected_ids = {match.id for match in selected_matches}
        self.assertEqual(match_ids, expected_ids)
    
    def test_get_elo_progression_empty_matches(self):
        """Test ELO progression with no matches."""
        self.analyzer.matches = []
        progression = self.analyzer.get_elo_progression()
        
        self.assertEqual(len(progression), 0)


class TestEloChartView(unittest.TestCase):
    """Test ELO chart view functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.ui = MCSRStatsUI(self.root)
        self.elo_chart = EloChart(self.ui)
        
        # Mock chart builder
        self.ui.chart_builder = Mock()
        self.ui.chart_options = {
            'color_palette': 'default',
            'show_rolling_avg': False,
            'rolling_window': 10,
            'show_grid': True
        }
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_elo_chart_initialization(self):
        """Test ELO chart initialization."""
        self.assertIsInstance(self.elo_chart, EloChart)
        self.assertEqual(self.elo_chart.ui, self.ui)
    
    @patch('tkinter.messagebox.showinfo')
    def test_show_with_no_analyzer(self, mock_msgbox):
        """Test showing ELO chart with no analyzer."""
        self.ui.analyzer = None
        self.elo_chart.show()
        
        # Should not show info message since _check_analyzer handles it
        mock_msgbox.assert_not_called()
    
    @patch('tkinter.messagebox.showinfo')
    def test_show_with_no_elo_data(self, mock_msgbox):
        """Test showing ELO chart with no ELO data."""
        mock_analyzer = Mock()
        mock_analyzer.get_elo_progression.return_value = []
        self.ui.analyzer = mock_analyzer
        self.ui._get_all_filtered_matches = Mock(return_value=[])
        
        self.elo_chart.show()
        
        mock_msgbox.assert_called_once_with("Info", "No ELO data available for the selected filters.")
    
    def test_show_with_elo_data_single_player(self):
        """Test showing ELO chart with single player data."""
        # Mock analyzer and data
        mock_analyzer = Mock()
        mock_elo_progression = [
            {
                'date': datetime(2024, 1, 1),
                'elo_after': 1520,
                'elo_change': 20,
                'elo_before': 1500,
                'match_id': 123,
                'result': 'Won'
            },
            {
                'date': datetime(2024, 1, 2), 
                'elo_after': 1505,
                'elo_change': -15,
                'elo_before': 1520,
                'match_id': 124,
                'result': 'Lost'
            }
        ]
        
        mock_analyzer.get_elo_progression.return_value = mock_elo_progression
        mock_analyzer.username = "testuser"
        
        self.ui.analyzer = mock_analyzer
        self.ui._get_all_filtered_matches = Mock(return_value=[Mock(), Mock()])
        self.ui.comparison_handler.active = False  # Set through handler
        
        # Mock UI methods
        self.ui._current_view = None
        self.ui.notebook = Mock()
        self.ui._set_chart_controls_visible = Mock()
        
        # Test the chart display
        self.elo_chart.show()
        
        # Verify chart builder was called
        self.ui.chart_builder.clear.assert_called_once()
        self.ui.chart_builder.set_palette.assert_called_once()
    
    def test_show_with_comparison_data(self):
        """Test showing ELO chart with comparison player data."""
        # Setup main player data
        mock_analyzer = Mock()
        mock_analyzer.username = "mainuser"
        main_elo_progression = [
            {
                'date': datetime(2024, 1, 1),
                'elo_after': 1520,
                'elo_change': 20,
                'elo_before': 1500,
                'match_id': 123,
                'result': 'Won'
            }
        ]
        mock_analyzer.get_elo_progression.return_value = main_elo_progression
        
        # Setup comparison player data
        mock_comp_analyzer = Mock()
        mock_comp_analyzer.username = "compuser"
        comp_elo_progression = [
            {
                'date': datetime(2024, 1, 1),
                'elo_after': 1480,
                'elo_change': -20,
                'elo_before': 1500,
                'match_id': 456,
                'result': 'Lost'
            }
        ]
        mock_comp_analyzer.get_elo_progression.return_value = comp_elo_progression
        
        self.ui.analyzer = mock_analyzer
        self.ui.comparison_handler.analyzer = mock_comp_analyzer  # Set it through the handler
        self.ui.comparison_handler.active = True
        self.ui._get_all_filtered_matches = Mock(return_value=[Mock()])
        
        # Mock comparison handler
        mock_comparison_handler = Mock()
        mock_comparison_handler.get_all_filtered_matches.return_value = [Mock()]
        self.ui.comparison_handler = mock_comparison_handler
        
        # Mock UI methods
        self.ui._current_view = None
        self.ui.notebook = Mock()
        self.ui._set_chart_controls_visible = Mock()
        
        # Test the comparison chart
        self.elo_chart.show()
        
        # Verify both analyzers were called
        mock_analyzer.get_elo_progression.assert_called_once()
        mock_comp_analyzer.get_elo_progression.assert_called_once()
        
        # Verify chart builder was used
        self.ui.chart_builder.clear.assert_called_once()


class TestEloChartIntegration(unittest.TestCase):
    """Test ELO chart integration with the main UI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.ui = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_elo_chart_in_chart_view_manager(self):
        """Test that ELO chart is properly integrated in chart view manager."""
        self.assertIsNotNone(self.ui.chart_views.elo)
        self.assertIsInstance(self.ui.chart_views.elo, EloChart)
    
    def test_elo_chart_refresh_in_current_view(self):
        """Test that ELO chart refresh works in _refresh_current_view."""
        self.ui._current_view = 'elo_progression'
        self.ui.chart_views.elo = Mock()
        
        self.ui._refresh_current_view()
        
        self.ui.chart_views.elo.show.assert_called_once()
    
    def test_navigation_button_exists(self):
        """Test that ELO chart navigation button exists."""
        # Check that the ELO Progress button was created
        elo_button_found = False
        for button_text in self.ui.nav_buttons:
            if "ELO Progress" in button_text:
                elo_button_found = True
                break
        
        self.assertTrue(elo_button_found, "ELO Progress navigation button not found")


class TestEloDataFormatting(unittest.TestCase):
    """Test ELO data formatting and display utilities."""
    
    def test_format_date_axis_with_few_dates(self):
        """Test date axis formatting with few dates."""
        root = tk.Tk()
        ui = MCSRStatsUI(root)
        elo_chart = EloChart(ui)
        
        # Mock chart builder and axis
        cb = Mock()
        ax = Mock()
        
        dates = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 3)
        ]
        
        elo_chart._format_date_axis(cb, ax, dates)
        
        # Should call set_xticks with all dates
        cb.set_xticks.assert_called_once()
        call_args = cb.set_xticks.call_args
        tick_dates = call_args[0][1]  # Second argument is the dates
        self.assertEqual(len(tick_dates), 3)  # All dates should be included
        
        root.destroy()
    
    def test_format_date_axis_with_many_dates(self):
        """Test date axis formatting with many dates."""
        root = tk.Tk()
        ui = MCSRStatsUI(root)
        elo_chart = EloChart(ui)
        
        # Mock chart builder and axis
        cb = Mock()
        ax = Mock()
        
        # Create 20 dates (more than max_ticks=8)
        dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(20)]
        
        elo_chart._format_date_axis(cb, ax, dates)
        
        # Should call set_xticks with subset of dates
        cb.set_xticks.assert_called_once()
        call_args = cb.set_xticks.call_args
        tick_dates = call_args[0][1]  # Second argument is the dates
        self.assertLessEqual(len(tick_dates), 12)  # Should be limited but allow some flexibility
        
        root.destroy()


class TestEloChartComparison(unittest.TestCase):
    """Test ELO chart comparison functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.ui = MCSRStatsUI(self.root)
        
        # Mock comparison handler
        self.ui.comparison_handler = Mock()
        self.ui.comparison_handler.get_all_filtered_matches.return_value = []
        
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_comparison_fallback_to_single_chart(self):
        """Test that comparison falls back to single chart when no comparison data."""
        elo_chart = EloChart(self.ui)
        
        # Mock chart builder
        cb = Mock()
        
        # Setup main player data
        main_elo_progression = [
            {
                'date': datetime(2024, 1, 1),
                'elo_after': 1500,
                'elo_change': 0,
                'elo_before': 1500,
                'match_id': 123,
                'result': 'Won'
            }
        ]
        
        # Mock comparison analyzer with no data
        mock_comp_analyzer = Mock()
        mock_comp_analyzer.get_elo_progression.return_value = []
        self.ui.comparison_handler.analyzer = mock_comp_analyzer
        self.ui.comparison_handler.active = True
        
        # Mock _show_single_chart to verify it's called
        elo_chart._show_single_chart = Mock()
        
        elo_chart._show_comparison_chart(cb, main_elo_progression)
        
        # Should fall back to single chart
        elo_chart._show_single_chart.assert_called_once_with(cb, main_elo_progression)


if __name__ == '__main__':
    # Run all ELO tests
    unittest.main(verbosity=2)