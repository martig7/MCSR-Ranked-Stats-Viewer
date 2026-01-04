"""
Test script for RichTextPresenter functionality.
"""

import tkinter as tk
from src.ui.widgets.rich_text_widget import RichTextWidget
from src.visualization.rich_text_presenter import RichTextPresenter

def test_rich_presenter():
    """Test the RichTextPresenter with sample content."""
    root = tk.Tk()
    root.title("RichTextPresenter Test")
    root.geometry("1000x700")
    
    # Create notebook for multiple tabs
    notebook = tk.ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Welcome tab
    welcome_frame = tk.Frame(notebook)
    notebook.add(welcome_frame, text="Welcome")
    
    welcome_widget = RichTextWidget(welcome_frame, theme="dark")
    welcome_widget.pack(fill=tk.BOTH, expand=True)
    
    presenter = RichTextPresenter()
    presenter.render_welcome(welcome_widget)
    
    # Summary tab with mock data
    summary_frame = tk.Frame(notebook)
    notebook.add(summary_frame, text="Summary")
    
    summary_widget = RichTextWidget(summary_frame, theme="dark")
    summary_widget.pack(fill=tk.BOTH, expand=True)
    
    # Mock analyzer and matches for testing
    class MockAnalyzer:
        def __init__(self):
            self.username = "test_player"
    
    class MockMatch:
        def __init__(self, is_win, time_ms, completed=True, draw=False, forfeit=False):
            self.is_user_win = is_win
            self.match_time = time_ms if completed else None
            self.user_completed = completed
            self.is_draw = draw
            self.forfeited = forfeit
            self.player_count = 2
            from datetime import datetime
            self.datetime_obj = datetime(2024, 1, 15)
            self.season = 3
            self.seed_type = "RSG"
        
        def time_str(self):
            if self.match_time:
                return presenter.format_time_ms_to_string(self.match_time)
            return "N/A"
        
        def date_str(self):
            return "2024-01-15"
    
    # Create mock data
    analyzer = MockAnalyzer()
    matches = [
        MockMatch(True, 1425123),   # Win: 23:45.123
        MockMatch(False, None, False),     # Loss: no time
        MockMatch(True, 1472456),   # Win: 24:32.456  
        MockMatch(True, 1398789),   # Win: 23:18.789 (PB)
        MockMatch(None, None, False, draw=True),  # Draw
        MockMatch(True, 1501234),   # Win: 25:01.234
        MockMatch(False, 1654321),  # Loss: 27:34.321
        MockMatch(True, 1445678),   # Win: 24:05.678
    ]
    
    presenter.render_summary(summary_widget, analyzer, matches)
    
    # Best times tab
    best_times_frame = tk.Frame(notebook)
    notebook.add(best_times_frame, text="Best Times")
    
    best_times_widget = RichTextWidget(best_times_frame, theme="dark")
    best_times_widget.pack(fill=tk.BOTH, expand=True)
    
    # Mock season data
    seasons = {
        3: {'matches': 45, 'best': 1398789, 'average': 1456123.5},
        4: {'matches': 32, 'best': 1425123, 'average': 1478456.2}
    }
    
    presenter.render_best_times(best_times_widget, analyzer, matches, seasons)
    
    root.mainloop()

if __name__ == "__main__":
    # Import ttk for the notebook
    import tkinter.ttk as ttk
    tk.ttk = ttk
    test_rich_presenter()