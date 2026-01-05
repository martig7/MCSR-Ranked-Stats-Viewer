"""
Comparison Player Handler Module
Handles loading and managing comparison player data for MCSR Ranked Stats Browser.
"""

from tkinter import messagebox
from ...core.analyzer import MCSRAnalyzer
from ...utils.base_thread_handler import BaseThreadHandler


class ComparisonHandler(BaseThreadHandler):
    """Manages comparison player functionality"""
    
    def __init__(self, ui_context):
        """
        Initialize comparison handler
        
        Args:
            ui_context: Reference to main UI (provides access to analyzer, controls, etc.)
        """
        super().__init__(ui_context)
        self.analyzer = None  # MCSRAnalyzer for comparison player
        self.active = False   # Whether comparison is currently active
    
    def load_player(self, username: str):
        """
        Load comparison player data
        
        Args:
            username: Username of the player to compare with
        """
        username = username.strip()
        if not username or username.lower() == "none":
            messagebox.showwarning("Invalid Username", "Please enter a valid username to compare with.")
            return
            
        if username.lower() == (self.ui.username_var.get() or "").lower():
            messagebox.showwarning("Same Player", "Cannot compare a player with themselves.")
            return
        
        def work_func(progress_callback=None):
            comparison_analyzer = MCSRAnalyzer(username)
            comparison_analyzer.fetch_all_matches(use_cache=True)
            return (comparison_analyzer, username)
        
        self.execute_with_progress(
            f"Loading comparison player: {username}...",
            work_func,
            lambda result: self._on_loaded(result[0], result[1]),
            self._on_failed,
            button=self.ui.load_comparison_btn,
            loading_text="Loading...",
            normal_text="Load"
        )
    
    def _on_loaded(self, analyzer, username):
        """Handle successful comparison player loading"""
        self.analyzer = analyzer
        self.active = True
        # Note: Button state is handled by BaseThreadHandler
        self.ui.comparison_var.set(username)
        self.ui.status_var.set(f"Loaded comparison data for {username}")
        
        # Refresh current view to show comparison
        self.ui._refresh_current_view()
    
    def _on_failed(self, error):
        """Handle failed comparison player loading"""
        # Note: Button state is handled by BaseThreadHandler
        messagebox.showerror("Load Error", f"Failed to load comparison player: {error}")
    
    def clear(self):
        """Clear comparison player data"""
        self.analyzer = None
        self.active = False
        self.ui.comparison_var.set("None")
        self.ui.status_var.set("Comparison cleared")
        
        # Refresh current view to remove comparison
        self.ui._refresh_current_view()
    
    def get_filtered_matches(self):
        """Get comparison player's completed matches with same filters as main player"""
        return self.ui.filter_manager.get_filtered_matches(self.analyzer, completed_only=True)
    
    def get_all_filtered_matches(self):
        """Get all comparison player matches (wins/losses/draws) with same filters as main player"""
        return self.ui.filter_manager.get_all_filtered_matches(self.analyzer)
    
    def is_active(self) -> bool:
        """Check if comparison is currently active"""
        return self.active
    
    def get_analyzer(self):
        """Get the comparison analyzer (or None if not loaded)"""
        return self.analyzer
