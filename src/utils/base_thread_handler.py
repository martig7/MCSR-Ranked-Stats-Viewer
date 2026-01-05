"""
Base thread handler for common threading patterns in MCSR Ranked User Stats.

This module consolidates threading patterns that were previously duplicated
across DataLoader and ComparisonHandler classes.
"""

import threading
from typing import Callable, Optional, Any
from contextlib import contextmanager


class BaseThreadHandler:
    """
    Base class providing common threading patterns with progress updates
    and thread-safe UI operations.
    """
    
    def __init__(self, ui_context):
        """
        Initialize the base thread handler.
        
        Args:
            ui_context: Reference to the main UI class for thread-safe operations
        """
        self.ui = ui_context
    
    def execute_in_background(self, 
                            work_func: Callable,
                            success_callback: Callable[[Any], None],
                            error_callback: Callable[[str], None],
                            progress_callback: Optional[Callable[[str], None]] = None):
        """
        Execute a function in a background thread with proper error handling
        and thread-safe UI updates.
        
        Args:
            work_func: Function to execute in background (should return result)
            success_callback: Called on main thread with work_func result
            error_callback: Called on main thread with error message string
            progress_callback: Optional progress update function
        """
        def background_worker():
            try:
                # Execute the work function
                if progress_callback:
                    result = work_func(progress_callback)
                else:
                    result = work_func()
                
                # Schedule success callback on main thread
                self.ui.root.after(0, lambda: success_callback(result))
                
            except Exception as e:
                # Capture error message before lambda to avoid closure issues
                error_msg = str(e)
                self.ui.root.after(0, lambda: error_callback(error_msg))
        
        # Start background thread
        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()
    
    def create_progress_callback(self, 
                               progress_method: Optional[Callable[[str], None]] = None) -> Callable[[str], None]:
        """
        Create a thread-safe progress callback function.
        
        Args:
            progress_method: Custom progress method, defaults to UI._update_loading_progress
            
        Returns:
            Thread-safe progress callback function
        """
        if progress_method is None:
            progress_method = getattr(self.ui, '_update_loading_progress', lambda msg: None)
        
        def progress_update(message: str):
            self.ui.root.after(0, lambda msg=message: progress_method(msg))
        
        return progress_update
    
    @contextmanager
    def button_state_manager(self, button, loading_text: str = "Loading...", 
                           normal_text: str = "Load"):
        """
        Context manager for handling button state during background operations.
        
        Args:
            button: The tkinter button widget
            loading_text: Text to show while loading
            normal_text: Text to restore after operation
        """
        try:
            # Disable button and show loading state
            if button:
                button.config(state='disabled', text=loading_text)
            yield
        finally:
            # Re-enable button and restore normal state
            if button:
                button.config(state='normal', text=normal_text)
    
    def execute_with_progress(self, 
                            operation_name: str,
                            work_func: Callable,
                            success_callback: Callable[[Any], None],
                            error_callback: Callable[[str], None],
                            button=None,
                            loading_text: str = "Loading...",
                            normal_text: str = "Load"):
        """
        Convenience method combining progress updates and button state management.
        
        Args:
            operation_name: Name of operation for progress display
            work_func: Function to execute (will be passed progress callback)
            success_callback: Success handler
            error_callback: Error handler
            button: Optional button to manage state
            loading_text: Button text during loading
            normal_text: Button text when idle
        """
        def wrapped_work_func(progress_callback):
            # Show initial progress
            progress_callback(operation_name)
            
            # Execute actual work
            return work_func(progress_callback)
        
        def wrapped_success_callback(result):
            try:
                success_callback(result)
            finally:
                # Restore button state
                if button:
                    button.config(state='normal', text=normal_text)
        
        def wrapped_error_callback(error_msg):
            try:
                error_callback(error_msg)
            finally:
                # Restore button state
                if button:
                    button.config(state='normal', text=normal_text)
        
        # Set button state
        if button:
            button.config(state='disabled', text=loading_text)
        
        # Create progress callback
        progress_callback = self.create_progress_callback()
        
        # Execute in background
        self.execute_in_background(
            lambda: wrapped_work_func(progress_callback),
            wrapped_success_callback,
            wrapped_error_callback
        )