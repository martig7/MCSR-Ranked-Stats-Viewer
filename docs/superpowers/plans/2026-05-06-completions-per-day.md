# Completions Per Day Chart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Completions" sidebar view showing a bar chart of user-completed runs bucketed by day/week/month, with a rolling average line overlay and a grouping toggle in the chart controls bar.

**Architecture:** New `CompletionsChart(ChartViewBase)` in `chart_views.py` uses a new `completions_by_period()` method on `MCSRAnalyzer`. A period grouping combobox (Day/Week/Month) is added to the chart controls bar following the same show/hide pattern as the existing match-numbers toggle. The sidebar gains one new button between "Segment Trends" and "Distribution".

**Tech Stack:** Python, Tkinter (ttk), Matplotlib via `ChartBuilder`, `unittest`

---

### Task 1: Add `completions_by_period()` to `MCSRAnalyzer`

**Files:**
- Modify: `src/core/analyzer.py` (after `seed_type_breakdown`, around line 545)
- Modify: `tests/test_ui.py` (append new test class)

- [ ] **Step 1: Write the failing tests**

Append this class to `tests/test_ui.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```
python -m pytest tests/test_ui.py::TestCompletionsByPeriod -v
```

Expected: all 6 tests FAIL with `AttributeError: type object 'MCSRAnalyzer' has no attribute 'completions_by_period'`

- [ ] **Step 3: Implement `completions_by_period()` in `src/core/analyzer.py`**

Add this method directly after `seed_type_breakdown` (after line ~600):

```python
def completions_by_period(
    self,
    period: str = 'day',
    include_private_rooms: bool = True,
    season_filter: Optional[int] = None,
    seed_type_filter: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Dict[str, int]:
    """Return completed-run counts bucketed by time period.

    Args:
        period: 'day', 'week', or 'month'
        include_private_rooms: Whether to include private-room matches
        season_filter: Restrict to a specific season number, or None for all
        seed_type_filter: Restrict to a specific seed type, or None for all
        date_from: Inclusive lower bound on match date
        date_to: Inclusive upper bound on match date

    Returns:
        Dict mapping period label → count, sorted chronologically.
    """
    filters: Dict[str, Any] = {
        'user_completed': True,
        'include_private_rooms': include_private_rooms,
        'date_from': date_from,
        'date_to': date_to,
    }
    if season_filter is not None:
        filters['seasons'] = [season_filter]
    if seed_type_filter is not None:
        filters['seed_types'] = [seed_type_filter]

    matches = self.filter_matches(**filters)

    fmt = {
        'day':   '%Y-%m-%d',
        'week':  '%G-W%V',
        'month': '%Y-%m',
    }.get(period, '%Y-%m-%d')

    counts: Dict[str, int] = {}
    for match in matches:
        label = match.datetime_obj.strftime(fmt)
        counts[label] = counts.get(label, 0) + 1

    return dict(sorted(counts.items()))
```

- [ ] **Step 4: Run tests to verify they pass**

```
python -m pytest tests/test_ui.py::TestCompletionsByPeriod -v
```

Expected: all 6 tests PASS

- [ ] **Step 5: Verify syntax**

```
python -m py_compile src/core/analyzer.py
```

Expected: no output (no errors)

- [ ] **Step 6: Commit**

```
git add src/core/analyzer.py tests/test_ui.py
git commit -m "feat: add completions_by_period() to MCSRAnalyzer"
```

---

### Task 2: Add period grouping widget and sidebar button

**Files:**
- Modify: `src/ui/components.py`
- Modify: `tests/test_ui.py` (append to `TestUICreation`)

- [ ] **Step 1: Write the failing tests**

Append these two test methods inside the existing `TestUICreation` class in `tests/test_ui.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```
python -m pytest tests/test_ui.py::TestUICreation::test_period_grouping_widget_exists tests/test_ui.py::TestUICreation::test_sidebar_has_eleven_buttons -v
```

Expected: both FAIL — `AttributeError: 'MCSRStatsUI' object has no attribute 'period_grouping_var'` and sidebar button count assertion error.

- [ ] **Step 3: Add the period grouping widgets in `src/ui/components.py`**

In `MainContent._create_chart_tab()`, after the block that creates `match_numbers_check` (around line 281), add:

```python
        # Period grouping toggle (shown only for Completions view)
        self.ui.period_grouping_var = tk.StringVar(value='Day')
        self.ui.period_grouping_label = ttk.Label(
            self.ui.view_controls_frame,
            text="Group by:",
            font=('Segoe UI', 9),
        )
        self.ui.period_grouping_combo = ttk.Combobox(
            self.ui.view_controls_frame,
            textvariable=self.ui.period_grouping_var,
            values=['Day', 'Week', 'Month'],
            state='readonly',
            width=8,
        )
        self.ui.period_grouping_combo.bind(
            '<<ComboboxSelected>>', self.ui._on_period_grouping_change
        )
        # Initially hidden — shown when Completions view is active
```

- [ ] **Step 4: Add the sidebar button in `src/ui/components.py`**

In `Sidebar.create()`, in the `nav_buttons` list (around line 134), insert the new entry after `("📊 Segment Trends", ...)` and before `("📉 Distribution", ...)`:

```python
            ("Completions", lambda: self.ui.chart_views.completions.show()),
```

The full updated list should look like:

```python
        nav_buttons = [
            ("📊 Summary", self.ui._show_summary),
            ("📈 Progression", lambda: self.ui.chart_views.progression.show()),
            ("🏆 Best Times", self.ui._show_best_times),
            ("📅 Season Stats", lambda: self.ui.chart_views.season_stats.show()),
            ("🌱 Seed Types", lambda: self.ui.chart_views.seed_types.show()),
            ("⏱️ Segments", lambda: self.ui.segment_analyzer.show_segments_text()),
            ("📊 Segment Trends", lambda: self.ui.segment_analyzer.show_segment_progression()),
            ("Completions", lambda: self.ui.chart_views.completions.show()),
            ("📉 Distribution", lambda: self.ui.chart_views.distribution.show()),
            ("🔍 Match Browser", self.ui._show_match_browser),
            ("🚀 All Time Best Pace", self.ui._show_forecast),
        ]
```

- [ ] **Step 5: Run tests to verify they pass**

```
python -m pytest tests/test_ui.py::TestUICreation::test_period_grouping_widget_exists tests/test_ui.py::TestUICreation::test_sidebar_has_eleven_buttons -v
```

Expected: both PASS

- [ ] **Step 6: Update the existing button-count test**

The existing test `test_sidebar_creation` asserts `len(app.nav_buttons) == 10`. Update that assertion:

```python
        self.assertEqual(len(app.nav_buttons), 11)  # 11 navigation buttons (ELO Progress is disabled)
```

- [ ] **Step 7: Run the full sidebar test**

```
python -m pytest tests/test_ui.py::TestUICreation::test_sidebar_creation -v
```

Expected: PASS

- [ ] **Step 8: Verify syntax**

```
python -m py_compile src/ui/components.py
```

Expected: no output

- [ ] **Step 9: Commit**

```
git add src/ui/components.py tests/test_ui.py
git commit -m "feat: add period grouping widget and Completions sidebar button"
```

---

### Task 3: Wire `main_window.py` — controls visibility, refresh dispatch, change handler

**Files:**
- Modify: `src/ui/main_window.py`
- Modify: `tests/test_ui.py` (append to `TestUICreation`)

- [ ] **Step 1: Write the failing test**

Append this test method inside `TestUICreation` in `tests/test_ui.py`:

```python
def test_period_grouping_toggle_visibility(self):
    """period grouping widgets are hidden by default, shown when flag is True"""
    app = MCSRStatsUI(self.root)
    # Hidden by default — pack_info raises TclError when widget is not packed
    import tkinter as tk
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
```

- [ ] **Step 2: Run test to verify it fails**

```
python -m pytest tests/test_ui.py::TestUICreation::test_period_grouping_toggle_visibility -v
```

Expected: FAIL — `TypeError: _set_chart_controls_visible() got an unexpected keyword argument 'show_period_grouping_toggle'`

- [ ] **Step 3: Add `show_period_grouping_toggle` to `_set_chart_controls_visible()` in `src/ui/main_window.py`**

Find `_set_chart_controls_visible` (around line 542) and update its signature and body:

```python
    def _set_chart_controls_visible(self, show_splits_toggle: bool, show_back_button: bool = False,
                                   show_match_numbers_toggle: bool = False,
                                   show_period_grouping_toggle: bool = False):
        """Show or hide chart control options based on current view"""
        if show_splits_toggle:
            self.splits_check.pack(side=tk.LEFT)
        else:
            self.splits_check.pack_forget()

        if show_match_numbers_toggle:
            self.match_numbers_check.pack(side=tk.LEFT, padx=(10, 0))
        else:
            self.match_numbers_check.pack_forget()

        if show_period_grouping_toggle:
            self.period_grouping_label.pack(side=tk.LEFT, padx=(10, 2))
            self.period_grouping_combo.pack(side=tk.LEFT)
        else:
            self.period_grouping_label.pack_forget()
            self.period_grouping_combo.pack_forget()

        if show_back_button:
            self.back_btn_frame.pack(fill=tk.X, pady=(0, 5), before=self.chart_controls_frame)
        else:
            self.back_btn_frame.pack_forget()
```

- [ ] **Step 4: Add `'completions'` case to `_refresh_current_view()` in `src/ui/main_window.py`**

Find `_refresh_current_view` (around line 216) and add the new case before the `else` fallback:

```python
        elif self._current_view == 'completions':
            self.chart_views.completions.show()
```

- [ ] **Step 5: Add `_on_period_grouping_change()` to `src/ui/main_window.py`**

Add this method after `_on_match_numbers_toggle` (search for that method name to find the right location):

```python
    def _on_period_grouping_change(self, event=None):
        """Re-render Completions chart when the grouping combobox changes"""
        if self._current_view == 'completions':
            self.chart_views.completions.show()
```

- [ ] **Step 6: Run test to verify it passes**

```
python -m pytest tests/test_ui.py::TestUICreation::test_period_grouping_toggle_visibility -v
```

Expected: PASS

- [ ] **Step 7: Verify syntax**

```
python -m py_compile src/ui/main_window.py
```

Expected: no output

- [ ] **Step 8: Commit**

```
git add src/ui/main_window.py tests/test_ui.py
git commit -m "feat: wire period grouping toggle and completions view refresh"
```

---

### Task 4: Add `CompletionsChart` and register it in `ChartViewManager`

**Files:**
- Modify: `src/visualization/chart_views.py`
- Modify: `tests/test_ui.py` (append new test class)

- [ ] **Step 1: Write the failing tests**

Append this class to `tests/test_ui.py`:

```python
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
        from datetime import datetime

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
```

- [ ] **Step 2: Run tests to verify they fail**

```
python -m pytest tests/test_ui.py::TestCompletionsChart -v
```

Expected: `test_completions_chart_registered_on_chart_view_manager` FAILS with `AttributeError: 'ChartViewManager' object has no attribute 'completions'`. Others fail for the same root reason.

- [ ] **Step 3: Add `CompletionsChart` class to `src/visualization/chart_views.py`**

Add this class before `ChartViewManager` (before line ~958):

```python
class CompletionsChart(ChartViewBase):
    """Handles completions-per-period chart view"""

    def show(self):
        """Show completions per day/week/month bar chart with rolling average"""
        self._prepare_chart('completions', '_show_completions',
                            show_period_grouping_toggle=True)

        if not self._check_analyzer():
            return

        period = self.ui.period_grouping_var.get().lower()  # 'day' | 'week' | 'month'

        filters = self._get_filter_settings()
        data = self.ui.analyzer.completions_by_period(
            period=period,
            include_private_rooms=filters['include_private'],
            season_filter=filters['season_val'],
            seed_type_filter=filters['seed_val'],
            date_from=self.ui._filter_date_from,
            date_to=self.ui._filter_date_to,
        )

        if not self._validate_data_minimum(list(data.keys()), 2,
                                           f'{period}s with completions'):
            return

        labels = list(data.keys())
        counts = list(data.values())
        x_pos = list(range(len(labels)))

        cb = self._setup_chart_builder()
        ax = cb.get_subplot(1, 1, 1)

        cb.plot_bar(ax, x_pos, counts, color_index=0)

        window = self.ui.chart_options['rolling_window']
        if len(counts) >= window:
            cb.add_rolling_average(
                ax, x_pos, counts,
                window=window,
                label=f'{window}-period average',
                color_index=1,
                is_comparison=False,
            )

        cb.set_labels(
            ax,
            title=f'{self.ui.analyzer.username} - Completions per {period.capitalize()}',
            xlabel=period.capitalize(),
            ylabel='Completions',
        )
        cb.set_xticks(ax, x_pos, labels, rotation=45, ha='right')
        cb.set_grid(ax, self.ui.chart_options['show_grid'])
        cb.set_legend(ax)
        cb.finalize()
```

- [ ] **Step 4: Update `_prepare_chart` to accept `show_period_grouping_toggle` in `src/visualization/chart_views.py`**

Find `_prepare_chart` in `ChartViewBase` (line ~26) and update its signature and the call to `_set_chart_controls_visible`:

```python
    def _prepare_chart(self, view_name: str, chart_view_name: str, show_splits_toggle: bool = False,
                      show_match_numbers_toggle: bool = False,
                      show_period_grouping_toggle: bool = False):
        """Common chart preparation logic"""
        self.ui._current_view = view_name
        self.ui.notebook.select(1)  # Charts tab

        # Hide segment controls when not viewing segments
        if hasattr(self.ui, 'segment_text_controls_frame'):
            self.ui.segment_text_controls_frame.pack_forget()

        self.ui._set_chart_controls_visible(
            show_splits_toggle=show_splits_toggle,
            show_match_numbers_toggle=show_match_numbers_toggle,
            show_period_grouping_toggle=show_period_grouping_toggle,
        )
        self.ui._current_chart_view = chart_view_name
```

- [ ] **Step 5: Register `CompletionsChart` in `ChartViewManager`**

Find `ChartViewManager.__init__` (around line 958) and add:

```python
        self.completions = CompletionsChart(ui_context)
```

The full `__init__` body should look like:

```python
    def __init__(self, ui_context):
        """Initialize all chart views"""
        self.progression = ProgressionChart(ui_context)
        self.season_stats = SeasonStatsChart(ui_context)
        self.seed_types = SeedTypesChart(ui_context)
        self.distribution = DistributionChart(ui_context)
        self.completions = CompletionsChart(ui_context)
        # self.elo = EloChart(ui_context)  # Commented out - ELO feature not working
```

- [ ] **Step 6: Run tests to verify they pass**

```
python -m pytest tests/test_ui.py::TestCompletionsChart -v
```

Expected: all 4 tests PASS

- [ ] **Step 7: Verify syntax**

```
python -m py_compile src/visualization/chart_views.py
```

Expected: no output

- [ ] **Step 8: Run the full test suite**

```
python -m pytest tests/test_ui.py -v
```

Expected: all tests PASS (including the previously-existing ones)

- [ ] **Step 9: Commit**

```
git add src/visualization/chart_views.py tests/test_ui.py
git commit -m "feat: add CompletionsChart view with period grouping"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** `completions_by_period()` ✓ | period grouping toggle ✓ | bar + rolling avg chart ✓ | sidebar button ✓ | respects all filters ✓ | single-player only ✓ | min 2 periods guard ✓ | `_refresh_current_view` dispatch ✓
- [x] **No placeholders:** All steps contain full code.
- [x] **Type consistency:** `completions_by_period()` defined in Task 1, called with exact same kwarg names in Task 4. `show_period_grouping_toggle` added to `_set_chart_controls_visible` in Task 3, used in `_prepare_chart` in Task 4.
- [x] **Widget names consistent:** `period_grouping_label` / `period_grouping_combo` / `period_grouping_var` used identically in Tasks 2, 3, and 4.
