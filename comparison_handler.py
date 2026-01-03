"""
Comparison Player Handler Module
Handles loading and managing comparison player data for MCSR Ranked Stats Browser.
"""

import threading
from tkinter import messagebox
from mcsr_stats import MCSRAnalyzer


class ComparisonHandler:
    """Manages comparison player functionality"""
    
    def __init__(self, ui_context):
        """
        Initialize comparison handler
        
        Args:
            ui_context: Reference to main UI (provides access to analyzer, controls, etc.)
        """
        self.ui = ui_context
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
        
        # Disable button during loading
        self.ui.load_comparison_btn.config(state='disabled', text='Loading...')
        
        def load_in_background():
            try:
                comparison_analyzer = MCSRAnalyzer(username)
                comparison_analyzer.fetch_all_matches(use_cache=True)
                
                # Update UI on main thread
                self.ui.root.after(0, lambda: self._on_loaded(comparison_analyzer, username))
                
            except Exception as e:
                error_msg = str(e)
                self.ui.root.after(0, lambda: self._on_failed(error_msg))
        
        # Start loading in background thread
        threading.Thread(target=load_in_background, daemon=True).start()
    
    def _on_loaded(self, analyzer, username):
        """Handle successful comparison player loading"""
        self.analyzer = analyzer
        self.active = True
        self.ui.load_comparison_btn.config(state='normal', text='Load')
        self.ui.comparison_var.set(username)
        self.ui.status_var.set(f"Loaded comparison data for {username}")
        
        # Refresh current view to show comparison
        self.ui._refresh_current_view()
    
    def _on_failed(self, error):
        """Handle failed comparison player loading"""
        self.ui.load_comparison_btn.config(state='normal', text='Load')
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
        if not self.analyzer:
            return []
        return self.analyzer.filter_matches(**self.ui._build_filter_kwargs(completed_only=True))
    
    def get_all_filtered_matches(self):
        """Get all comparison player matches (wins/losses/draws) with same filters as main player"""
        if not self.analyzer:
            return []
        return self.analyzer.filter_matches(**self.ui._build_filter_kwargs(completed_only=False))
    
    def is_active(self) -> bool:
        """Check if comparison is currently active"""
        return self.active
    
    def get_analyzer(self):
        """Get the comparison analyzer (or None if not loaded)"""
        return self.analyzer
