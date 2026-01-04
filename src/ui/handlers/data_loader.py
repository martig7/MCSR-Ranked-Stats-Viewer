"""
Data loading and management for MCSR Stats UI.
Handles background data fetching and state updates.
"""

import threading
from tkinter import messagebox
from ...core.analyzer import MCSRAnalyzer


class DataLoader:
    """Manages data loading operations with background threading"""
    
    def __init__(self, ui_context):
        """
        Initialize data loader with UI context.
        
        Args:
            ui_context: Reference to main UI (MCSRStatsUI instance)
        """
        self.ui = ui_context
    
    def load_from_cache(self):
        """Load data from cache"""
        username = self.ui.username_var.get().strip()
        if not username:
            messagebox.showwarning("Warning", "Please enter a username")
            return
            
        self.ui._set_status(f"Loading data for {username}...")
        self.ui._show_loading_progress("Loading from cache...")
        
        def load_thread():
            try:
                self.ui.analyzer = MCSRAnalyzer(username)
                
                def progress_update(message):
                    self.ui.root.after(0, lambda msg=message: self.ui._update_loading_progress(msg))
                
                self.ui.analyzer.fetch_all_matches(use_cache=True, progress_callback=progress_update)
                self.ui.root.after(0, self._on_data_loaded)
            except Exception as e:
                error_msg = str(e)
                self.ui.root.after(0, lambda: self._on_load_error(error_msg))
                
        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()
        
    def refresh_from_api(self):
        """Fetch fresh data from API"""
        username = self.ui.username_var.get().strip()
        if not username:
            messagebox.showwarning("Warning", "Please enter a username")
            return
            
        self.ui._set_status(f"Fetching data from API for {username}...")
        self.ui._show_loading_progress("Fetching from API...")
        
        def refresh_thread():
            try:
                self.ui.analyzer = MCSRAnalyzer(username)
                
                def progress_update(message):
                    self.ui.root.after(0, lambda msg=message: self.ui._update_loading_progress(msg))
                
                self.ui.analyzer.fetch_all_matches(use_cache=False, progress_callback=progress_update)
                self.ui.root.after(0, self._on_data_loaded)
            except Exception as e:
                error_msg = str(e)
                self.ui.root.after(0, lambda: self._on_load_error(error_msg))
                
        thread = threading.Thread(target=refresh_thread, daemon=True)
        thread.start()
        
    def fetch_segments(self):
        """Fetch detailed segment data for next batch of matches"""
        if not self.ui.analyzer:
            messagebox.showwarning("Warning", "Please load data first")
            return
            
        self.ui._set_status("Fetching segment data...")
        self.ui._show_loading_progress("Preparing segment fetch...")
        
        def fetch_thread():
            try:
                def progress_update(message):
                    self.ui.root.after(0, lambda msg=message: self.ui._update_loading_progress(msg))
                
                fetched_count = self.ui.analyzer.fetch_segment_data(max_matches=100, force_refresh=False, progress_callback=progress_update)
                self.ui.root.after(0, lambda: self._on_segments_loaded(fetched_count))
            except Exception as e:
                error_msg = str(e)
                self.ui.root.after(0, lambda: self._on_load_error(error_msg))
                
        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()
    
    def clear_basic_data(self):
        """Clear basic match data only"""
        if not self.ui.analyzer:
            messagebox.showwarning("Warning", "No data loaded to clear")
            return
        
        username = self.ui.analyzer.username
        result = messagebox.askyesno(
            "Clear Basic Data",
            f"Are you sure you want to clear all cached match data for {username}?\n\n"
            "This will remove:\n"
            "• Match history cache\n"
            "• Rate limit data\n\n"
            "Segment data will be preserved.",
            icon='warning'
        )
        
        if result:
            try:
                files_removed = self.ui.analyzer.clear_user_data(clear_detailed=False)
                # Reset UI state
                self.ui.analyzer = None
                self.ui.season_combo['values'] = ['All']
                self.ui.seed_filter_combo['values'] = ['All']
                self.ui._clear_display()
                self.ui._set_status(f"Cleared basic data for {username} ({files_removed} files removed)")
                messagebox.showinfo("Success", f"Basic data cleared for {username}")
            except Exception as e:
                error_msg = str(e)
                self.ui._set_status(f"Error clearing data: {error_msg}")
                messagebox.showerror("Error", f"Failed to clear data: {error_msg}")
    
    def clear_all_data(self):
        """Clear all data including detailed segments"""
        if not self.ui.analyzer:
            messagebox.showwarning("Warning", "No data loaded to clear")
            return
            
        username = self.ui.analyzer.username
        result = messagebox.askyesno(
            "Clear All Data",
            f"Are you sure you want to clear ALL cached data for {username}?\n\n"
            "This will remove:\n"
            "• Match history cache\n"
            "• Detailed segment data\n"
            "• Rate limit data\n\n"
            "This action cannot be undone.",
            icon='warning'
        )
        
        if result:
            try:
                files_removed = self.ui.analyzer.clear_user_data(clear_detailed=True)
                # Reset UI state  
                self.ui.analyzer = None
                self.ui.season_combo['values'] = ['All']
                self.ui.seed_filter_combo['values'] = ['All']
                self.ui._clear_display()
                self.ui._set_status(f"Cleared all data for {username} ({files_removed} files removed)")
                messagebox.showinfo("Success", f"All data cleared for {username}")
            except Exception as e:
                error_msg = str(e)
                self.ui._set_status(f"Error clearing data: {error_msg}")
                messagebox.showerror("Error", f"Failed to clear data: {error_msg}")
        
    def _on_data_loaded(self):
        """Called when data is loaded"""
        self.ui._hide_loading_progress()
        
        # Update season filter
        seasons = set(m.season for m in self.ui.analyzer.matches)
        self.ui.season_combo['values'] = ['All'] + sorted(seasons)
        
        # Update seed type filter
        seed_types = set(m.seed_type for m in self.ui.analyzer.matches if m.seed_type is not None)
        self.ui.seed_filter_combo['values'] = ['All'] + sorted(seed_types)
        
        # Update quick stats
        self.ui._update_quick_stats()
        
        # Update match browser
        self.ui._populate_match_tree()
        
        # Show summary
        self.ui._show_summary()
        
        self.ui._set_status(f"Loaded {len(self.ui.analyzer.matches)} matches for {self.ui.analyzer.username}")
        
    def _on_segments_loaded(self, fetched_count):
        """Called when segment data is loaded"""
        self.ui._hide_loading_progress()
        
        detailed_count = sum(1 for m in self.ui.analyzer.matches if m.has_detailed_data)
        if fetched_count > 0:
            self.ui._set_status(f"Fetched {fetched_count} new segments, {detailed_count} total with segment data")
            messagebox.showinfo("Success", f"Fetched detailed segment data for {fetched_count} new matches.\nTotal matches with segment data: {detailed_count}")
        else:
            self.ui._set_status(f"No new segments fetched, {detailed_count} matches already have segment data")
            messagebox.showinfo("Info", f"No new segment data was needed.\nTotal matches with segment data: {detailed_count}")
        
    def _on_load_error(self, error):
        """Called when loading fails"""
        self.ui._hide_loading_progress()
        self.ui._set_status(f"Error: {error}")
        messagebox.showerror("Error", f"Failed to load data: {error}")
