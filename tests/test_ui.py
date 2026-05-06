"""
Test suite for MCSR Ranked Stats Browser UI
Tests all UI components, navigation, and interactions
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

import sys
import os
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.main_window import MCSRStatsUI
from src.core.analyzer import MCSRAnalyzer
from src.core.match import Match


class TestUICreation(unittest.TestCase):
    """Test that UI components are created without errors"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_ui_initialization(self):
        """Test that the UI initializes without errors"""
        app = MCSRStatsUI(self.root)
        self.assertIsNotNone(app)
        self.assertEqual(app.analyzer, None)
        self.assertIsNotNone(app.chart_builder)
        self.assertIsNotNone(app.text_presenter)
        self.assertIsNotNone(app.segment_analyzer)
        self.assertIsNotNone(app.chart_views)
    
    def test_top_bar_creation(self):
        """Test that top bar controls are created"""
        app = MCSRStatsUI(self.root)
        self.assertIsNotNone(app.username_var)
        self.assertIsNotNone(app.username_entry)
        self.assertIsNotNone(app.load_btn)
        self.assertIsNotNone(app.refresh_btn)
        self.assertIsNotNone(app.fetch_segments_btn)
        self.assertIsNotNone(app.season_var)
        self.assertIsNotNone(app.season_combo)
        self.assertIsNotNone(app.seed_filter_var)
        self.assertIsNotNone(app.seed_filter_combo)
        self.assertIsNotNone(app.include_private_var)
    
    def test_sidebar_creation(self):
        """Test that sidebar navigation is created"""
        app = MCSRStatsUI(self.root)
        self.assertIsNotNone(app.sidebar)
        self.assertIsNotNone(app.nav_buttons)
        self.assertEqual(len(app.nav_buttons), 11)  # 11 navigation buttons (ELO Progress is disabled)
        self.assertIsNotNone(app.quick_stats_frame)
        self.assertIsNotNone(app.quick_stats_labels)
    
    def test_main_content_creation(self):
        """Test that main content area is created"""
        app = MCSRStatsUI(self.root)
        self.assertIsNotNone(app.notebook)
        self.assertIsNotNone(app.stats_frame)
        self.assertIsNotNone(app.stats_text)
        self.assertIsNotNone(app.chart_frame)
        self.assertIsNotNone(app.fig)
        self.assertIsNotNone(app.canvas)
        self.assertIsNotNone(app.data_frame)
        self.assertIsNotNone(app.match_tree)
    
    def test_chart_controls_creation(self):
        """Test that chart controls are created"""
        app = MCSRStatsUI(self.root)
        self.assertIsNotNone(app.show_splits_var)
        self.assertIsNotNone(app.splits_check)
        self.assertIsNotNone(app.show_rolling_var)
        self.assertIsNotNone(app.show_std_var)
        self.assertIsNotNone(app.show_pb_var)
        self.assertIsNotNone(app.show_grid_var)

    def test_period_grouping_widget_exists(self):
        """period_grouping_var and combo widget are created on the UI"""
        app = MCSRStatsUI(self.root)
        self.assertIsNotNone(app.period_grouping_var)
        self.assertEqual(app.period_grouping_var.get(), 'Day')
        self.assertIsNotNone(app.period_grouping_label)
        self.assertIsNotNone(app.period_grouping_combo)

    def test_sidebar_has_eleven_buttons(self):
        """Sidebar now has 11 nav buttons (Completions added)"""
        app = MCSRStatsUI(self.root)
        self.assertEqual(len(app.nav_buttons), 11)
        self.assertIn('Completions', app.nav_buttons)


class TestNavigationButtons(unittest.TestCase):
    """Test that navigation buttons work correctly"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_summary_view(self):
        """Test summary view navigation"""
        self.app._show_summary()
        self.assertEqual(self.app._current_view, 'summary')
        self.assertEqual(self.app.notebook.index(self.app.notebook.select()), 0)  # Stats tab
    
    def test_best_times_view(self):
        """Test best times view navigation"""
        self.app._show_best_times()
        self.assertEqual(self.app._current_view, 'best_times')
        self.assertEqual(self.app.notebook.index(self.app.notebook.select()), 0)  # Stats tab
    
    def test_match_browser_view(self):
        """Test match browser view navigation"""
        self.app._show_match_browser()
        self.assertEqual(self.app._current_view, 'match_browser')
        self.assertEqual(self.app.notebook.index(self.app.notebook.select()), 2)  # Data tab
    
    def test_progression_chart_view(self):
        """Test progression chart view navigation (without data)"""
        self.app.chart_views.progression.show()
        self.assertEqual(self.app._current_view, 'progression')
        # Should switch to charts tab
        self.assertEqual(self.app.notebook.index(self.app.notebook.select()), 1)
    
    def test_season_stats_chart_view(self):
        """Test season stats chart view navigation (without data)"""
        self.app.chart_views.season_stats.show()
        self.assertEqual(self.app._current_view, 'season_stats')
        self.assertEqual(self.app.notebook.index(self.app.notebook.select()), 1)
    
    def test_seed_types_chart_view(self):
        """Test seed types chart view navigation (without data)"""
        self.app.chart_views.seed_types.show()
        self.assertEqual(self.app._current_view, 'seed_types')
        self.assertEqual(self.app.notebook.index(self.app.notebook.select()), 1)
    
    def test_distribution_chart_view(self):
        """Test distribution chart view navigation (without data)"""
        self.app.chart_views.distribution.show()
        self.assertEqual(self.app._current_view, 'distribution')
        self.assertEqual(self.app.notebook.index(self.app.notebook.select()), 1)
    
    def test_segments_text_view(self):
        """Test segments text view navigation"""
        self.app.segment_analyzer.show_segments_text()
        self.assertEqual(self.app._current_view, 'segments')
        self.assertEqual(self.app.notebook.index(self.app.notebook.select()), 0)
    
    def test_segment_progression_view(self):
        """Test segment progression view navigation (without data)"""
        self.app.segment_analyzer.show_segment_progression()
        self.assertEqual(self.app._current_view, 'segment_progression')
        self.assertEqual(self.app.notebook.index(self.app.notebook.select()), 1)


class TestFilterFunctionality(unittest.TestCase):
    """Test filter controls and data filtering"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_season_filter_values(self):
        """Test season filter initialization"""
        self.assertEqual(self.app.season_var.get(), 'All')
        self.assertIn('All', self.app.season_combo['values'])
    
    def test_seed_type_filter_values(self):
        """Test seed type filter initialization"""
        self.assertEqual(self.app.seed_filter_var.get(), 'All')
        self.assertIn('All', self.app.seed_filter_combo['values'])
    
    def test_private_rooms_filter(self):
        """Test private rooms filter"""
        self.assertTrue(self.app.include_private_var.get())  # Default is True
        self.app.include_private_var.set(False)
        self.assertFalse(self.app.include_private_var.get())
    
    def test_build_filter_kwargs(self):
        """Test filter kwargs building via filter_manager"""
        kwargs = self.app.filter_manager.build_filter_kwargs(completed_only=True)
        self.assertIn('include_private_rooms', kwargs)
        self.assertIn('completed_only', kwargs)
        self.assertTrue(kwargs['completed_only'])

    def test_build_filter_kwargs_with_season(self):
        """Test filter kwargs with season filter"""
        self.app.season_var.set('6')
        kwargs = self.app.filter_manager.build_filter_kwargs()
        self.assertIn('seasons', kwargs)
        self.assertEqual(kwargs['seasons'], [6])

    def test_build_filter_kwargs_with_seed_type(self):
        """Test filter kwargs with seed type filter"""
        self.app.seed_filter_var.set('Random Seed')
        kwargs = self.app.filter_manager.build_filter_kwargs()
        self.assertIn('seed_types', kwargs)
        self.assertEqual(kwargs['seed_types'], ['Random Seed'])


class TestChartOptions(unittest.TestCase):
    """Test chart option controls"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_default_chart_options(self):
        """Test default chart options"""
        self.assertEqual(self.app.chart_options['rolling_window'], 10)
        self.assertTrue(self.app.chart_options['show_rolling_avg'])
        self.assertFalse(self.app.chart_options['show_rolling_std'])
        self.assertTrue(self.app.chart_options['show_pb_line'])
        self.assertTrue(self.app.chart_options['show_grid'])
        self.assertEqual(self.app.chart_options['color_palette'], 'default')
    
    def test_rolling_average_toggle(self):
        """Test rolling average checkbox"""
        self.assertTrue(self.app.show_rolling_var.get())
        self.app.show_rolling_var.set(False)
        self.assertFalse(self.app.show_rolling_var.get())
    
    def test_std_dev_toggle(self):
        """Test standard deviation checkbox"""
        self.assertFalse(self.app.show_std_var.get())
        self.app.show_std_var.set(True)
        self.assertTrue(self.app.show_std_var.get())
    
    def test_pb_line_toggle(self):
        """Test PB line checkbox"""
        self.assertTrue(self.app.show_pb_var.get())
        self.app.show_pb_var.set(False)
        self.assertFalse(self.app.show_pb_var.get())
    
    def test_grid_toggle(self):
        """Test grid checkbox"""
        self.assertTrue(self.app.show_grid_var.get())
        self.app.show_grid_var.set(False)
        self.assertFalse(self.app.show_grid_var.get())


class TestComparisonPlayer(unittest.TestCase):
    """Test comparison player functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_comparison_initial_state(self):
        """Test comparison player initial state"""
        self.assertFalse(self.app.comparison_active)
        self.assertIsNone(self.app.comparison_analyzer)
        self.assertEqual(self.app.comparison_var.get(), 'None')
    
    def test_clear_comparison(self):
        """Test clearing comparison player"""
        # Simulate having a comparison loaded
        mock_analyzer = Mock()
        self.app.comparison_handler.analyzer = mock_analyzer
        self.app.comparison_handler.active = True
        self.app.comparison_var.set('test_player')
        
        # Clear it
        self.app.comparison_handler.clear()
        
        self.assertFalse(self.app.comparison_active)
        self.assertIsNone(self.app.comparison_analyzer)
        self.assertEqual(self.app.comparison_var.get(), 'None')


class TestSegmentAnalyzer(unittest.TestCase):
    """Test segment analyzer functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_segment_analyzer_initialization(self):
        """Test segment analyzer is properly initialized"""
        self.assertIsNotNone(self.app.segment_analyzer)
        self.assertFalse(self.app.segment_analyzer.is_expanded())
        self.assertIsNone(self.app.segment_analyzer.get_expanded_segment())
    
    def test_splits_toggle_var(self):
        """Test splits toggle variable"""
        self.assertFalse(self.app.show_splits_var.get())
        self.app.show_splits_var.set(True)
        self.assertTrue(self.app.show_splits_var.get())


class TestChartViews(unittest.TestCase):
    """Test chart views manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_chart_views_initialization(self):
        """Test chart views manager is properly initialized"""
        self.assertIsNotNone(self.app.chart_views)
        self.assertIsNotNone(self.app.chart_views.progression)
        self.assertIsNotNone(self.app.chart_views.season_stats)
        self.assertIsNotNone(self.app.chart_views.seed_types)
        self.assertIsNotNone(self.app.chart_views.distribution)
    
    def test_chart_view_context(self):
        """Test that chart views have access to UI context"""
        self.assertEqual(self.app.chart_views.progression.ui, self.app)
        self.assertEqual(self.app.chart_views.season_stats.ui, self.app)
        self.assertEqual(self.app.chart_views.seed_types.ui, self.app)
        self.assertEqual(self.app.chart_views.distribution.ui, self.app)


class TestRefreshCurrentChart(unittest.TestCase):
    """Test chart refresh functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_refresh_progression_chart(self):
        """Test refreshing progression chart"""
        self.app._current_chart_view = '_show_progression'
        # Should not crash even without data
        self.app._refresh_current_chart()
    
    def test_refresh_season_stats_chart(self):
        """Test refreshing season stats chart"""
        self.app._current_chart_view = '_show_season_stats'
        self.app._refresh_current_chart()
    
    def test_refresh_seed_types_chart(self):
        """Test refreshing seed types chart"""
        self.app._current_chart_view = '_show_seed_types'
        self.app._refresh_current_chart()
    
    def test_refresh_distribution_chart(self):
        """Test refreshing distribution chart"""
        self.app._current_chart_view = '_show_distribution'
        self.app._refresh_current_chart()
    
    def test_refresh_segment_progression(self):
        """Test refreshing segment progression chart"""
        self.app._current_chart_view = '_show_segment_progression'
        self.app._refresh_current_chart()


class TestMatchBrowser(unittest.TestCase):
    """Test match browser functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_match_tree_initialization(self):
        """Test match tree is created properly"""
        self.assertIsNotNone(self.app.match_tree)
        # Check columns
        columns = self.app.match_tree['columns']
        self.assertIn('Date', columns)
        self.assertIn('Time', columns)
        self.assertIn('Season', columns)
        self.assertIn('Seed Type', columns)
    
    def test_match_lookup_initialization(self):
        """Test match lookup dictionary is initialized"""
        self.assertIsNotNone(self.app.match_lookup)
        self.assertIsInstance(self.app.match_lookup, dict)
        self.assertEqual(len(self.app.match_lookup), 0)


class TestUtilityMethods(unittest.TestCase):
    """Test utility methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = MCSRStatsUI(self.root)
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_time_str_formatting(self):
        """Test time string formatting"""
        # 15 minutes = 900000 ms
        time_str = self.app._time_str(900000)
        self.assertEqual(time_str, '15:00.000')
        
        # 1 minute 30 seconds = 90000 ms
        time_str = self.app._time_str(90000)
        self.assertEqual(time_str, '1:30.000')
    
    def test_minutes_to_str_formatting(self):
        """Test minutes to string formatting"""
        # 15.5 minutes
        time_str = self.app._minutes_to_str(15.5)
        self.assertEqual(time_str, '15m 30s')
        
        # 1.25 minutes
        time_str = self.app._minutes_to_str(1.25)
        self.assertEqual(time_str, '1m 15s')
    
    def test_set_status(self):
        """Test status bar update"""
        test_msg = "Test status message"
        self.app._set_status(test_msg)
        self.assertEqual(self.app.status_var.get(), test_msg)


class TestChartControlsVisibility(unittest.TestCase):
    """Test chart controls visibility management"""

    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = MCSRStatsUI(self.root)

    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass

    def test_show_splits_toggle(self):
        """Test showing splits toggle"""
        self.app._set_chart_controls_visible(show_splits_toggle=True)
        # Verify splits check is packed
        self.assertIn(self.app.splits_check, self.app.view_controls_frame.pack_slaves())

    def test_hide_splits_toggle(self):
        """Test hiding splits toggle"""
        self.app._set_chart_controls_visible(show_splits_toggle=False)
        # Verify splits check is not packed
        self.assertNotIn(self.app.splits_check, self.app.view_controls_frame.pack_slaves())

    def test_show_back_button(self):
        """Test showing back button"""
        self.app._set_chart_controls_visible(show_splits_toggle=False, show_back_button=True)
        # Verify back button frame is packed
        self.assertIn(self.app.back_btn_frame, self.app.chart_frame.pack_slaves())

    def test_hide_back_button(self):
        """Test hiding back button"""
        self.app._set_chart_controls_visible(show_splits_toggle=False, show_back_button=False)
        # Verify back button frame is not packed
        self.assertNotIn(self.app.back_btn_frame, self.app.chart_frame.pack_slaves())

    def test_period_grouping_toggle_visibility(self):
        """period grouping widgets are hidden by default, shown when flag is True"""
        app = MCSRStatsUI(self.root)
        # Hidden by default — pack_info raises TclError when widget is not packed
        try:
            app.period_grouping_label.pack_info()
            label_packed = True
        except tk.TclError:
            label_packed = False
        self.assertFalse(label_packed, "period_grouping_label should be hidden initially")

        # Show it
        app._set_chart_controls_visible(
            show_splits_toggle=False,
            show_period_grouping_toggle=True,
        )
        try:
            app.period_grouping_label.pack_info()
            label_packed = True
        except tk.TclError:
            label_packed = False
        self.assertTrue(label_packed, "period_grouping_label should be visible after show")

        # Hide it again
        app._set_chart_controls_visible(
            show_splits_toggle=False,
            show_period_grouping_toggle=False,
        )
        try:
            app.period_grouping_label.pack_info()
            label_packed = True
        except tk.TclError:
            label_packed = False
        self.assertFalse(label_packed, "period_grouping_label should be hidden again")


class TestCompletionsByPeriod(unittest.TestCase):
    """Tests for MCSRAnalyzer.completions_by_period()"""

    def _make_completion_match(self, timestamp, season=1, seed_type='random'):
        """Return a Match where user_completed=True for the given Unix timestamp."""
        data = {
            'id': timestamp,
            'date': timestamp,
            'category': 'ANY',
            'forfeited': False,
            'seed': None,
            'seedType': seed_type,
            'season': season,
            'type': 1,
            'players': [{'nickname': 'tester', 'uuid': 'u1', 'eloRate': 1000, 'eloChange': 10}],
            'result': {'uuid': 'u1', 'time': 300000},
        }
        return Match(data, 'tester')

    def _make_analyzer_with(self, matches):
        analyzer = MCSRAnalyzer.__new__(MCSRAnalyzer)
        analyzer.matches = matches
        return analyzer

    def test_day_grouping_counts_correctly(self):
        from datetime import datetime
        t1 = int(datetime(2024, 3, 1, 10, 0).timestamp())
        t2 = int(datetime(2024, 3, 1, 15, 0).timestamp())
        t3 = int(datetime(2024, 3, 3, 9, 0).timestamp())
        analyzer = self._make_analyzer_with([
            self._make_completion_match(t1),
            self._make_completion_match(t2),
            self._make_completion_match(t3),
        ])
        result = analyzer.completions_by_period('day')
        self.assertEqual(result.get('2024-03-01'), 2)
        self.assertEqual(result.get('2024-03-03'), 1)
        self.assertEqual(len(result), 2)

    def test_week_grouping(self):
        from datetime import datetime
        # 2024-03-04 (Mon) and 2024-03-05 (Tue) are both ISO week 10
        t1 = int(datetime(2024, 3, 4, 10, 0).timestamp())
        t2 = int(datetime(2024, 3, 5, 10, 0).timestamp())
        # 2024-03-11 (Mon) is ISO week 11
        t3 = int(datetime(2024, 3, 11, 10, 0).timestamp())
        analyzer = self._make_analyzer_with([
            self._make_completion_match(t1),
            self._make_completion_match(t2),
            self._make_completion_match(t3),
        ])
        result = analyzer.completions_by_period('week')
        self.assertEqual(result.get('2024-W10'), 2)
        self.assertEqual(result.get('2024-W11'), 1)

    def test_month_grouping(self):
        from datetime import datetime
        t1 = int(datetime(2024, 1, 5, 10, 0).timestamp())
        t2 = int(datetime(2024, 1, 20, 10, 0).timestamp())
        t3 = int(datetime(2024, 2, 3, 10, 0).timestamp())
        analyzer = self._make_analyzer_with([
            self._make_completion_match(t1),
            self._make_completion_match(t2),
            self._make_completion_match(t3),
        ])
        result = analyzer.completions_by_period('month')
        self.assertEqual(result.get('2024-01'), 2)
        self.assertEqual(result.get('2024-02'), 1)

    def test_excludes_non_completed_matches(self):
        from datetime import datetime
        t1 = int(datetime(2024, 3, 1, 10, 0).timestamp())
        data = {
            'id': t1, 'date': t1, 'category': 'ANY', 'forfeited': True,
            'seed': None, 'seedType': 'random', 'season': 1, 'type': 1,
            'players': [{'nickname': 'tester', 'uuid': 'u1', 'eloRate': 1000, 'eloChange': 10},
                        {'nickname': 'other',  'uuid': 'u2', 'eloRate': 900,  'eloChange': -10}],
            'result': {'uuid': 'u2', 'time': 290000},
        }
        loss_match = Match(data, 'tester')  # user lost
        analyzer = self._make_analyzer_with([loss_match])
        result = analyzer.completions_by_period('day')
        self.assertEqual(len(result), 0)

    def test_result_is_sorted_chronologically(self):
        from datetime import datetime
        t_early = int(datetime(2024, 1, 1, 10, 0).timestamp())
        t_late  = int(datetime(2024, 6, 1, 10, 0).timestamp())
        analyzer = self._make_analyzer_with([
            self._make_completion_match(t_late),
            self._make_completion_match(t_early),
        ])
        result = analyzer.completions_by_period('month')
        keys = list(result.keys())
        self.assertEqual(keys, sorted(keys))

    def test_season_filter(self):
        from datetime import datetime
        t1 = int(datetime(2024, 3, 1, 10, 0).timestamp())
        t2 = int(datetime(2024, 3, 2, 10, 0).timestamp())
        analyzer = self._make_analyzer_with([
            self._make_completion_match(t1, season=5),
            self._make_completion_match(t2, season=6),
        ])
        result = analyzer.completions_by_period('day', season_filter=5)
        self.assertIn('2024-03-01', result)
        self.assertNotIn('2024-03-02', result)


class TestCompletionsChart(unittest.TestCase):
    """Tests for CompletionsChart chart view"""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_completions_chart_registered_on_chart_view_manager(self):
        app = MCSRStatsUI(self.root)
        self.assertTrue(hasattr(app.chart_views, 'completions'))

    def test_show_without_analyzer_does_not_crash(self):
        """Calling show() before any data is loaded must not raise."""
        app = MCSRStatsUI(self.root)
        app.analyzer = None
        app.chart_views.completions.show()  # must not raise

    def test_show_with_insufficient_data_shows_messagebox(self):
        """Fewer than 2 populated periods triggers an info messagebox."""
        from unittest.mock import patch, MagicMock

        app = MCSRStatsUI(self.root)
        mock_analyzer = MagicMock()
        mock_analyzer.username = 'tester'
        # Only one period of data
        mock_analyzer.completions_by_period.return_value = {'2024-01-01': 3}
        app.analyzer = mock_analyzer

        with patch('tkinter.messagebox.showinfo') as mock_info:
            app.chart_views.completions.show()
            mock_info.assert_called_once()

    def test_show_renders_without_error(self):
        """show() completes without exception when sufficient data is present."""
        from unittest.mock import MagicMock

        app = MCSRStatsUI(self.root)
        mock_analyzer = MagicMock()
        mock_analyzer.username = 'tester'
        mock_analyzer.completions_by_period.return_value = {
            '2024-01-01': 2,
            '2024-01-02': 1,
            '2024-01-03': 4,
        }
        app.analyzer = mock_analyzer
        app.chart_views.completions.show()  # must not raise


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestUICreation))
    suite.addTests(loader.loadTestsFromTestCase(TestNavigationButtons))
    suite.addTests(loader.loadTestsFromTestCase(TestFilterFunctionality))
    suite.addTests(loader.loadTestsFromTestCase(TestChartOptions))
    suite.addTests(loader.loadTestsFromTestCase(TestComparisonPlayer))
    suite.addTests(loader.loadTestsFromTestCase(TestSegmentAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestChartViews))
    suite.addTests(loader.loadTestsFromTestCase(TestRefreshCurrentChart))
    suite.addTests(loader.loadTestsFromTestCase(TestMatchBrowser))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilityMethods))
    suite.addTests(loader.loadTestsFromTestCase(TestChartControlsVisibility))
    suite.addTests(loader.loadTestsFromTestCase(TestCompletionsByPeriod))
    suite.addTests(loader.loadTestsFromTestCase(TestCompletionsChart))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    result = run_tests()
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
