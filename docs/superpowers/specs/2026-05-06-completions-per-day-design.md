# Completions Per Day Chart — Design Spec

**Date:** 2026-05-06

## Overview

Add a "Completions" chart view to the sidebar that displays the number of completed runs per time period (day/week/month) over time, as a bar chart with a rolling average line overlaid.

## Requirements

- Bar chart showing completions bucketed by time period
- Rolling average line overlaid on the bars (uses existing `rolling_window` from `chart_options`)
- Period grouping toggle: Day / Week / Month (combobox in chart controls bar, default: Day)
- Respects all existing filters (season, seed type, private rooms, date range, time range)
- Single-player view only (no comparison mode)
- Sidebar button labeled "Completions", positioned after "Segment Trends"
- Minimum 2 populated periods required; shows messagebox if insufficient data

## Files to Change

| File | Change |
|---|---|
| `src/core/analyzer.py` | Add `completions_by_period()` method |
| `src/ui/components.py` | Add period grouping combobox widget; add "Completions" sidebar button |
| `src/ui/main_window.py` | Add `show_period_grouping_toggle` to `_set_chart_controls_visible()`; add `'completions'` case to `_refresh_current_view()`; add `_on_period_grouping_change()` handler |
| `src/visualization/chart_views.py` | Add `CompletionsChart` class; register in `ChartViewManager` |

## Data Layer

### `MCSRAnalyzer.completions_by_period()`

```python
def completions_by_period(
    self,
    period: str = 'day',          # 'day' | 'week' | 'month'
    include_private_rooms: bool = True,
    season_filter=None,
    seed_type_filter=None,
    date_from=None,
    date_to=None,
) -> Dict[str, int]:
```

- Filters to matches where `user_completed=True` using the same filter kwargs pattern as other analyzer methods
- Buckets by period:
  - `'day'` → `datetime_obj.strftime('%Y-%m-%d')`
  - `'week'` → `datetime_obj.strftime('%G-W%V')` (ISO week)
  - `'month'` → `datetime_obj.strftime('%Y-%m')`
- Returns `{label: count}` dict sorted chronologically by label

## UI Layer

### Period Grouping Widget (`components.py`)

Added to `view_controls_frame` in `MainContent._create_chart_tab()`:
- `self.ui.period_grouping_var = tk.StringVar(value='Day')`
- A `ttk.Label` ("Group by:") and `ttk.Combobox` with values `['Day', 'Week', 'Month']`, state `readonly`
- Combobox bound to `self.ui._on_period_grouping_change`
- Initially not packed — shown/hidden via `_set_chart_controls_visible()`

### `_set_chart_controls_visible()` (`main_window.py`)

New parameter: `show_period_grouping_toggle: bool = False`

Packs or `pack_forget()`s the "Group by:" label and combobox based on the flag.

### `_on_period_grouping_change()` (`main_window.py`)

```python
def _on_period_grouping_change(self, event=None):
    if self._current_view == 'completions':
        self.chart_views.completions.show()
```

### `_refresh_current_view()` (`main_window.py`)

Add case:
```python
elif self._current_view == 'completions':
    self.chart_views.completions.show()
```

### Sidebar Button (`components.py`)

Insert after the "Segment Trends" entry in `nav_buttons`:
```python
("Completions", lambda: self.ui.chart_views.completions.show()),
```

No emoji.

## Chart View Layer

### `CompletionsChart(ChartViewBase)` (`chart_views.py`)

```python
def show(self):
    self._prepare_chart('completions', '_show_completions', show_period_grouping_toggle=True)

    if not self._check_analyzer():
        return

    period = self.ui.period_grouping_var.get().lower()  # 'day' | 'week' | 'month'
    filters = self._get_filter_settings()
    # plus date/time filters from self.ui._filter_date_from etc.

    data = self.ui.analyzer.completions_by_period(period, **filter_kwargs)

    if not self._validate_data_minimum(list(data.keys()), 2, f'{period}s with completions'):
        return

    cb = self._setup_chart_builder()
    ax = cb.get_subplot(1, 1, 1)

    labels = list(data.keys())
    counts = list(data.values())
    x_pos = list(range(len(labels)))

    cb.plot_bar(ax, x_pos, counts, color_index=0)

    window = self.ui.chart_options['rolling_window']
    if len(counts) >= window:
        cb.add_rolling_average(ax, x_pos, counts, window=window,
                               label=f'{window}-period average', is_comparison=False)

    cb.set_labels(ax,
                  title=f'{self.ui.analyzer.username} - Completions per {period.capitalize()}',
                  xlabel=period.capitalize(),
                  ylabel='Completions')
    cb.set_xticks(ax, x_pos, labels, rotation=45, ha='right')
    cb.set_grid(ax, self.ui.chart_options['show_grid'])
    cb.set_legend(ax)
    cb.finalize()
```

### `ChartViewManager`

```python
self.completions = CompletionsChart(ui_context)
```

## Filter Passthrough

`completions_by_period()` receives the full filter set:
- `include_private_rooms` from `self.ui.include_private_var.get()`
- `season_filter` from `self.ui.season_var.get()`
- `seed_type_filter` from `self.ui.seed_filter_var.get()`
- `date_from` / `date_to` from `self.ui._filter_date_from` / `self.ui._filter_date_to`

Time range filters (`_filter_time_min`, `_filter_time_max`) are not applicable since we're counting completions, not filtering by completion time.

## Error Handling

- No analyzer loaded: `_check_analyzer()` returns early (existing pattern)
- Fewer than 2 populated periods: `_validate_data_minimum()` shows messagebox (existing pattern)
- Rolling window larger than data: skip the rolling average line silently
