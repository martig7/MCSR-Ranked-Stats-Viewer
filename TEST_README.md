# UI Test Suite

Comprehensive test suite for the MCSR Ranked Stats Browser UI components.

## Running Tests

```bash
python test_ui.py
```

## Test Coverage

### TestUICreation (5 tests)
- ✅ UI initialization
- ✅ Top bar controls creation
- ✅ Sidebar navigation creation
- ✅ Main content area creation
- ✅ Chart controls creation

### TestNavigationButtons (9 tests)
- ✅ Summary view navigation
- ✅ Best times view navigation
- ✅ Match browser navigation
- ✅ Progression chart navigation
- ✅ Season stats chart navigation
- ✅ Seed types chart navigation
- ✅ Distribution chart navigation
- ✅ Segments text view navigation
- ✅ Segment progression navigation

### TestFilterFunctionality (6 tests)
- ✅ Season filter initialization and values
- ✅ Seed type filter initialization and values
- ✅ Private rooms filter toggle
- ✅ Filter kwargs building
- ✅ Filter kwargs with season
- ✅ Filter kwargs with seed type

### TestChartOptions (5 tests)
- ✅ Default chart options
- ✅ Rolling average toggle
- ✅ Standard deviation toggle
- ✅ PB line toggle
- ✅ Grid toggle

### TestComparisonPlayer (2 tests)
- ✅ Comparison player initial state
- ✅ Clear comparison functionality

### TestSegmentAnalyzer (2 tests)
- ✅ Segment analyzer initialization
- ✅ Splits toggle variable

### TestChartViews (2 tests)
- ✅ Chart views manager initialization
- ✅ Chart view context access

### TestRefreshCurrentChart (5 tests)
- ✅ Refresh progression chart
- ✅ Refresh season stats chart
- ✅ Refresh seed types chart
- ✅ Refresh distribution chart
- ✅ Refresh segment progression

### TestMatchBrowser (2 tests)
- ✅ Match tree initialization
- ✅ Match lookup dictionary initialization

### TestUtilityMethods (3 tests)
- ✅ Time string formatting
- ✅ Minutes to string formatting
- ✅ Status bar update

### TestChartControlsVisibility (4 tests)
- ✅ Show splits toggle
- ✅ Hide splits toggle
- ✅ Show back button
- ✅ Hide back button

## Total: 45 Tests - All Passing ✅

## Test Philosophy

These tests verify:
1. **Component Creation** - All UI elements are created without errors
2. **Navigation** - All views can be navigated to
3. **Filters** - Filter controls work correctly
4. **Chart Options** - Chart customization options function properly
5. **State Management** - UI state is maintained correctly
6. **Utility Functions** - Helper methods produce correct output
7. **Control Visibility** - UI elements show/hide appropriately

## Future Enhancements

Consider adding:
- Integration tests with mock data
- Tests for data loading/refreshing
- Tests for match detail display
- Tests for comparison player loading
- Tests for segment expansion/collapse
- Performance tests for large datasets
