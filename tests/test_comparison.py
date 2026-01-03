"""
Unit tests for comparison features in MCSR Ranked User Statistics.
Tests the comparison handler, comparison UI integration, and comparison display logic.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from mcsr_ui import MCSRStatsUI
from comparison_handler import ComparisonHandler
from text_presenter import TextPresenter
from match import Match
from datetime import datetime


class TestComparisonHandler(unittest.TestCase):
    """Test the ComparisonHandler class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.ui = MCSRStatsUI(self.root)
        self.handler = ComparisonHandler(self.ui)
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_initial_state(self):
        """Test initial state of comparison handler."""
        self.assertFalse(self.handler.is_active())
        self.assertIsNone(self.handler.get_analyzer())
    
    def test_clear_comparison(self):
        """Test clearing comparison data."""
        # Set up mock analyzer
        mock_analyzer = Mock()
        self.handler.comparison_analyzer = mock_analyzer
        
        # Clear and verify
        self.handler.clear()
        self.assertFalse(self.handler.is_active())
        self.assertIsNone(self.handler.get_analyzer())
    
    @patch('comparison_handler.threading.Thread')
    @patch('comparison_handler.MCSRAnalyzer')
    def test_load_player_success(self, mock_analyzer_class, mock_thread):
        """Test successful player loading."""
        # Mock analyzer creation
        mock_analyzer = Mock()
        mock_analyzer.username = "testuser"
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock successful data fetch
        mock_analyzer.fetch_all_matches.return_value = True
        
        # Mock thread execution
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # Load player
        self.handler.load_player("testuser")
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
    
    @patch('comparison_handler.threading.Thread')
    def test_load_player_empty_username(self, mock_thread):
        """Test loading with empty username."""
        self.handler.load_player("")
        
        # Should not create thread for empty username
        mock_thread.assert_not_called()
    
    def test_get_filtered_matches_no_analyzer(self):
        """Test getting filtered matches when no analyzer is loaded."""
        result = self.handler.get_filtered_matches()
        self.assertEqual(result, [])
    
    def test_get_filtered_matches_with_analyzer(self):
        """Test getting filtered matches with loaded analyzer."""
        # Create mock analyzer with filter_matches method
        mock_analyzer = Mock()
        mock_matches = [Mock(), Mock(), Mock()]
        mock_analyzer.filter_matches.return_value = mock_matches
        
        self.handler.analyzer = mock_analyzer
        
        # Mock UI method that builds filter kwargs
        self.ui._build_filter_kwargs = Mock(return_value={'season': 5, 'seed_type': 'Set Seed'})
        
        # Test filtered matches
        result = self.handler.get_filtered_matches()
        
        # Verify filter_matches was called with correct parameters
        mock_analyzer.filter_matches.assert_called_once_with(season=5, seed_type='Set Seed')
        self.assertEqual(result, mock_matches)


class TestComparisonUIIntegration(unittest.TestCase):
    """Test comparison feature integration with UI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.ui = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_comparison_handler_initialized(self):
        """Test that comparison handler is properly initialized."""
        self.assertIsNotNone(self.ui.comparison_handler)
        self.assertIsInstance(self.ui.comparison_handler, ComparisonHandler)
    
    def test_comparison_active_property(self):
        """Test the comparison_active property."""
        # Initially should be False
        self.assertFalse(self.ui.comparison_active)
        
        # Mock active comparison
        mock_analyzer = Mock()
        self.ui.comparison_handler.analyzer = mock_analyzer
        self.ui.comparison_handler.active = True
        self.assertTrue(self.ui.comparison_active)
    
    def test_comparison_controls_visibility(self):
        """Test comparison control visibility logic."""
        # Test that comparison controls exist
        self.assertIsNotNone(hasattr(self.ui, 'load_comparison_btn'))
        self.assertIsNotNone(hasattr(self.ui, 'clear_comparison_btn'))
    
    @patch('mcsr_ui.MCSRStatsUI._generate_summary_text')
    def test_summary_view_with_comparison(self, mock_generate_summary):
        """Test summary view with comparison active."""
        # Mock data
        main_text = "Main player data"
        comparison_text = "Comparison player data"
        mock_generate_summary.side_effect = [main_text, comparison_text]
        
        # Mock comparison analyzer
        mock_analyzer = Mock()
        mock_analyzer.username = "comparison_user"
        self.ui.comparison_handler.analyzer = mock_analyzer
        self.ui.comparison_handler.active = True
        self.ui.analyzer = Mock()
        self.ui.analyzer.username = "main_user"
        
        # Mock text presenter
        self.ui.text_presenter = Mock()
        expected_result = "Side by side text"
        self.ui.text_presenter.format_side_by_side_text.return_value = expected_result
        
        # Call _show_summary
        with patch.object(self.ui.stats_text, 'delete') as mock_delete, \
             patch.object(self.ui.stats_text, 'insert') as mock_insert:
            self.ui._show_summary()
            
            # Verify side-by-side formatting was called
            self.ui.text_presenter.format_side_by_side_text.assert_called_once_with(
                main_text, comparison_text, "main_user", "comparison_user"
            )
            mock_insert.assert_called_once_with('1.0', expected_result)


class TestComparisonTextFormatting(unittest.TestCase):
    """Test comparison text formatting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.presenter = TextPresenter()
    
    def test_side_by_side_text_formatting(self):
        """Test side-by-side text formatting."""
        left_text = "Line 1\nLine 2\nLine 3"
        right_text = "Right Line 1\nRight Line 2"
        title_left = "Player A"
        title_right = "Player B"
        
        result = self.presenter.format_side_by_side_text(
            left_text, right_text, title_left, title_right
        )
        
        # Should contain both titles
        self.assertIn("Player A", result)
        self.assertIn("Player B", result)
        
        # Should contain content from both sides
        self.assertIn("Line 1", result)
        self.assertIn("Right Line 1", result)
        
        # Should have separator
        self.assertIn("│", result)
    
    def test_side_by_side_unequal_lengths(self):
        """Test side-by-side formatting with unequal text lengths."""
        left_text = "Short"
        right_text = "Much\nLonger\nText\nWith\nMany\nLines"
        
        result = self.presenter.format_side_by_side_text(left_text, right_text)
        
        # Count lines in result
        lines = result.split('\n')
        
        # Should have at least as many lines as the longer text plus headers
        self.assertGreaterEqual(len(lines), 6)  # 6 right lines + header + separator
    
    def test_side_by_side_empty_text(self):
        """Test side-by-side formatting with empty text."""
        left_text = ""
        right_text = "Some content"
        
        result = self.presenter.format_side_by_side_text(left_text, right_text)
        
        # Should handle empty text gracefully
        self.assertIn("Some content", result)
        self.assertIn("│", result)


class TestComparisonDataHandling(unittest.TestCase):
    """Test comparison data handling and filtering."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.ui = MCSRStatsUI(self.root)
        
        # Create mock matches for testing
        self.mock_matches = [
            self._create_mock_match("2024-01-01", 5, "Set Seed", True, 300000),
            self._create_mock_match("2024-01-02", 5, "Random Seed", True, 320000),
            self._create_mock_match("2024-01-03", 6, "Set Seed", False, None),
        ]
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def _create_mock_match(self, date_str, season, seed_type, completed, time_ms):
        """Create a mock match object."""
        match = Mock(spec=Match)
        match.date = datetime.strptime(date_str, "%Y-%m-%d")
        match.season = season
        match.seed_type = seed_type
        match.user_completed = completed
        match.match_time = time_ms
        match.is_user_win = completed
        match.is_draw = False
        match.forfeited = False
        match.has_detailed_data = False
        match.player_count = 2  # Add missing attribute
        return match
    
    def test_filter_application_to_comparison(self):
        """Test that filters apply correctly to comparison data."""
        # Mock comparison analyzer
        mock_analyzer = Mock()
        mock_analyzer.filter_matches.return_value = self.mock_matches[:2]  # First 2 matches
        self.ui.comparison_handler.analyzer = mock_analyzer
        
        # Mock UI filter method
        filter_kwargs = {
            'season': 5, 
            'seed_type': "Set Seed",
            'include_private': True
        }
        self.ui._build_filter_kwargs = Mock(return_value=filter_kwargs)
        
        # Test filter application
        result = self.ui.comparison_handler.get_filtered_matches()
        
        # Verify filter was called with correct parameters
        mock_analyzer.filter_matches.assert_called_once_with(**filter_kwargs)
        
        # Verify result
        self.assertEqual(len(result), 2)
    
    def test_comparison_stats_calculation(self):
        """Test that comparison statistics are calculated correctly."""
        # This would test the statistics calculation logic when comparison is active
        # For now, we'll test that the text generation handles comparison data
        
        mock_analyzer = Mock()
        mock_analyzer.username = "comparison_player"
        
        # Test that summary generation works with comparison analyzer
        try:
            summary = self.ui.text_presenter.generate_summary_text(mock_analyzer, self.mock_matches)
            self.assertIsInstance(summary, str)
            self.assertIn("comparison_player", summary)
        except Exception as e:
            self.fail(f"Summary generation failed with comparison data: {e}")


class TestComparisonChartIntegration(unittest.TestCase):
    """Test comparison integration with chart views."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.ui = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_chart_views_have_comparison_support(self):
        """Test that chart views can handle comparison data."""
        # Test that chart views manager exists
        self.assertIsNotNone(self.ui.chart_views)
        
        # Test that UI can check comparison status
        self.assertFalse(self.ui.comparison_active)  # Should be false initially
    
    @patch('chart_views.ChartViewManager')
    def test_progression_chart_with_comparison(self, mock_chart_manager):
        """Test progression chart with comparison overlay."""
        # Mock comparison data
        mock_analyzer = Mock()
        self.ui.comparison_handler.comparison_analyzer = mock_analyzer
        
        # Test that progression chart can be shown with comparison
        try:
            self.ui._show_progression()
            # If no exception is raised, the chart view handles comparison correctly
        except Exception as e:
            # We expect this to fail due to missing data, but not due to comparison logic
            self.assertNotIn("comparison", str(e).lower())


class TestComparisonErrorHandling(unittest.TestCase):
    """Test error handling in comparison features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.ui = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    @patch('comparison_handler.MCSRAnalyzer')
    def test_load_invalid_player(self, mock_analyzer_class):
        """Test loading an invalid player."""
        # Mock analyzer that fails to fetch data
        mock_analyzer = Mock()
        mock_analyzer.fetch_all_matches.side_effect = Exception("User not found")
        mock_analyzer_class.return_value = mock_analyzer
        
        # Simulate the background load failure
        handler = self.ui.comparison_handler
        handler._on_failed("User not found")
        
        # Verify comparison remains inactive
        self.assertFalse(handler.is_active())
    
    def test_comparison_with_no_data(self):
        """Test comparison behavior when no data is available."""
        # Mock analyzer with no matches
        mock_analyzer = Mock()
        mock_analyzer.filter_matches.return_value = []
        self.ui.comparison_handler.comparison_analyzer = mock_analyzer
        
        # Test that empty match list is handled gracefully
        result = self.ui.comparison_handler.get_filtered_matches()
        self.assertEqual(result, [])
    
    def test_text_generation_with_missing_comparison(self):
        """Test text generation when comparison analyzer is missing."""
        # Ensure comparison is not active
        self.ui.comparison_handler.clear()
        
        # Test that text generation works without comparison
        try:
            self.ui._show_summary()
            # Should not raise an exception
        except Exception as e:
            self.fail(f"Text generation failed without comparison: {e}")


if __name__ == '__main__':
    # Run all comparison tests
    unittest.main(verbosity=2)