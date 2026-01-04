"""
Test script for RichTextWidget functionality.
"""

import tkinter as tk
from src.ui.widgets.rich_text_widget import RichTextWidget

def test_rich_text_widget():
    """Test the RichTextWidget with sample content."""
    root = tk.Tk()
    root.title("RichTextWidget Test")
    root.geometry("800x600")
    
    # Create RichTextWidget
    rich_text = RichTextWidget(root, theme="dark")
    rich_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Add sample content
    rich_text.add_heading("MCSR Ranked Stats Test", level=1)
    rich_text.add_line("This is a test of the new rich text formatting system.", ['muted'])
    rich_text.add_line()
    
    rich_text.add_heading("Match Summary", level=2)
    rich_text.add_separator()
    
    # Test stats block
    stats = {
        "Total Matches": "156",
        "Wins": "89 (57.1%)",
        "Personal Best": "23:45.123",
        "Average Time": "26:32.456"
    }
    rich_text.add_stats_block("Performance Stats", stats)
    
    # Test table
    headers = ["Date", "Time", "Result", "Season"]
    rows = [
        ["2024-01-15", "23:45.123", "Win", "3"],
        ["2024-01-14", "24:12.456", "Loss", "3"],
        ["2024-01-13", "25:33.789", "Win", "3"],
    ]
    
    rich_text.add_heading("Recent Matches", level=3)
    rich_text.add_table(headers, rows)
    
    rich_text.add_line()
    rich_text.add_text("Success: ", ['success'])
    rich_text.add_line("New personal best achieved!")
    
    rich_text.add_text("Warning: ", ['warning'])
    rich_text.add_line("Rate limit approaching")
    
    rich_text.add_text("Error: ", ['error'])
    rich_text.add_line("Failed to fetch segment data")
    
    rich_text.finalize()
    
    root.mainloop()

if __name__ == "__main__":
    test_rich_text_widget()