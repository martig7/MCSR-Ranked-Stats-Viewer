# Log Scale Toggle for Progression Charts

**Date:** 2026-04-09  
**Status:** Approved

## Overview

Add a "Log Scale" toggle to the progression chart's Y-axis. Speedrun improvement is nonlinear — the perceptual and practical gap between a 10:00 and 8:00 run is different from 6:00 to 4:00. A logarithmic Y-axis better represents this improvement curve.

## Scope

- Applies to **progression charts only** (`ProgressionChart` — both single-player and comparison views).
- Does **not** apply to bar charts, histograms, season stats, or any count-based charts.
- Y-axis only (X-axis remains linear: dates or match numbers).

## UI

### Quick-toggle checkbox
A new "Log Scale" `ttk.Checkbutton` added to `chart_options_frame` in `components.py`, on the right side alongside the existing Grid, PB Line, Std Dev, Rolling Median, Rolling Avg checkboxes.

- Variable: `self.ui.show_log_scale_var` (`tk.BooleanVar`, default `False`)
- Command: `self.ui._on_chart_option_change` (same as Grid toggle)

### Chart settings dialog
A new "Log Scale" checkbox in `dialogs.py` (row 11, after "Show Grid"):
- Included in `_apply()` output dict as `'log_scale'`
- Reset to `False` in `_reset()`

## Data Flow

```
show_log_scale_var (BooleanVar)
  → _on_chart_option_change()
    → chart_options['log_scale'] = bool
      → ProgressionChart._show_single_chart() / _show_comparison_chart()
        → cb.set_log_scale(ax, enabled, time_formatter)
          → ax.set_yscale('log') + FuncFormatter(time_formatter)
```

`on_apply` callback in main_window.py syncs `show_log_scale_var` back from dialog changes.

## Implementation Details

### `ChartBuilder.set_log_scale(ax, enabled, time_formatter=None)`
New method in `chart_builder.py`:
- If `enabled`: calls `ax.set_yscale('log')` then sets `ax.yaxis.set_major_formatter` using a `matplotlib.ticker.FuncFormatter` wrapping the provided `time_formatter` (which is `_minutes_to_str` — formats decimal minutes as MM:SS).
- If not `enabled`: no-op (linear scale is matplotlib's default; `clear()` is called before each render so no cleanup needed).

### Call sites in `chart_views.py`
In `ProgressionChart._show_single_chart()` and `ProgressionChart._show_comparison_chart()`, after `cb.set_grid(ax, ...)`:
```python
cb.set_log_scale(ax, self.ui.chart_options['log_scale'], self.ui._minutes_to_str)
```

### `chart_options` dict (`main_window.py`)
Add `'log_scale': False` to the initial `chart_options` dict alongside the other boolean options.

## Files Changed

| File | Change |
|------|--------|
| `src/visualization/chart_builder.py` | Add `set_log_scale()` method; import `matplotlib.ticker` |
| `src/visualization/chart_views.py` | Call `cb.set_log_scale()` in both `ProgressionChart` render methods |
| `src/ui/main_window.py` | Add `'log_scale'` to `chart_options`; update `_on_chart_option_change` and `on_apply` |
| `src/ui/components.py` | Add Log Scale checkbox to `chart_options_frame` |
| `src/ui/dialogs.py` | Add Log Scale checkbox (row 11); update `_apply()` and `_reset()` |

## Out of Scope

- Applying log scale to segment trend charts, histograms, or bar charts.
- Per-chart log scale memory/persistence across sessions.
- Log scale on the X-axis.
