"""
Match Info Dialog - Displays detailed information about a specific match.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Dict
from ..core.match import Match
from ..ui.widgets.rich_text_widget import RichTextWidget


def calculate_segment_percentiles(filtered_matches: List[Match]) -> Dict[str, Dict[str, List[float]]]:
    """
    Calculate percentile data for each segment from filtered matches.

    Args:
        filtered_matches: List of matches within the filtered range

    Returns:
        Dict mapping segment names to dicts with 'split_times' and 'absolute_times' lists
    """
    segment_data = {}

    for match in filtered_matches:
        if not match.has_detailed_data or not match.segments:
            continue

        for segment_key, segment_info in match.segments.items():
            if segment_key not in segment_data:
                segment_data[segment_key] = {'split_times': [], 'absolute_times': []}

            # Only include valid times
            split_time = segment_info.get('split_time', 0)
            abs_time = segment_info.get('absolute_time', 0)

            if split_time > 0:
                segment_data[segment_key]['split_times'].append(split_time)
            if abs_time > 0:
                segment_data[segment_key]['absolute_times'].append(abs_time)

    return segment_data


def calculate_percentile(value: float, sorted_values: List[float]) -> Optional[float]:
    """
    Calculate what percentile a value falls at within a sorted list.

    Args:
        value: The value to find the percentile for
        sorted_values: List of values sorted in ascending order

    Returns:
        Percentile (0-100) or None if insufficient data
    """
    if not sorted_values or len(sorted_values) < 3:
        return None

    n = len(sorted_values)

    # Count how many values are less than or equal to the target value
    count_below = sum(1 for v in sorted_values if v <= value)

    # Calculate percentile using the percentage rank formula
    percentile = (count_below / n) * 100

    return percentile


def get_percentile_color(percentile: Optional[float]) -> Optional[str]:
    """
    Get a color for a percentile value.
    Lower percentiles (faster times) are better and shown in green.
    Higher percentiles (slower times) are worse and shown in red/orange.

    Args:
        percentile: Percentile value (0-100) or None

    Returns:
        Hex color string or None for default color
    """
    if percentile is None:
        return None

    # Color gradient from green (fast/good) to red (slow/bad)
    # Lower percentile = faster = better = green
    # Higher percentile = slower = worse = red
    if percentile <= 15:
        return '#4ec9b0'  # Bright green - excellent
    elif percentile <= 30:
        return '#73c991'  # Green - very good
    elif percentile <= 45:
        return '#a3d977'  # Light green - good
    elif percentile <= 55:
        return '#d4d4d4'  # Default/neutral - average
    elif percentile <= 70:
        return '#ffd700'  # Yellow/gold - below average
    elif percentile <= 85:
        return '#f0a858'  # Orange - poor
    else:
        return '#f48771'  # Red/coral - very slow


def get_time_at_percentile(target_percentile: float, sorted_values: List[float]) -> Optional[float]:
    """
    Get the time value at a specific percentile from a sorted list.
    This is the inverse of calculate_percentile.

    Args:
        target_percentile: Target percentile (0-100)
        sorted_values: List of values sorted in ascending order

    Returns:
        Time value at the given percentile, or None if insufficient data
    """
    if not sorted_values or len(sorted_values) < 3:
        return None

    n = len(sorted_values)

    # Clamp percentile to valid range
    target_percentile = max(0, min(100, target_percentile))

    # Calculate the index for this percentile using linear interpolation
    index = (target_percentile / 100.0) * (n - 1)
    lower_index = int(index)
    upper_index = min(lower_index + 1, n - 1)

    if lower_index == upper_index:
        return sorted_values[lower_index]

    # Linear interpolation between the two closest values
    weight = index - lower_index
    return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight


def format_time_ms(time_ms: float) -> str:
    """Format time in milliseconds to MM:SS.mmm string."""
    time_sec = time_ms / 1000
    return f"{int(time_sec // 60)}:{int(time_sec % 60):02d}.{int((time_sec % 1) * 1000):03d}"


class MatchInfoDialog:
    """Dialog window for displaying detailed match information"""

    def __init__(self, parent, match: Match, rich_text_presenter=None, filtered_matches: Optional[List[Match]] = None):
        """
        Initialize the match info dialog

        Args:
            parent: Parent window
            match: Match object to display
            rich_text_presenter: RichTextPresenter instance for modern formatting
            filtered_matches: Optional list of filtered matches for percentile calculations
        """
        self.match = match
        self.rich_text_presenter = rich_text_presenter
        self.filtered_matches = filtered_matches

        # Calculate segment percentile data if filtered matches provided
        self.segment_percentile_data = None
        if filtered_matches:
            self.segment_percentile_data = calculate_segment_percentiles(filtered_matches)
        
        # Create the dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Match Details - {match.date_str()}")
        self.dialog.geometry("700x550")
        self.dialog.resizable(True, True)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog on parent
        self._center_dialog(parent)
        
        self._create_widgets()
        
        # Focus on dialog
        self.dialog.focus_set()
        
        # Handle close button
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _center_dialog(self, parent):
        """Center the dialog window on the parent"""
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create and layout the dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = f"Match Details - {self.match.date_str()}"
        title_label = ttk.Label(main_frame, text=title, font=("TkDefaultFont", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Create tabbed interface with enhanced rich text widgets
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Basic Info Tab - Use RichTextWidget
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="Match Details")
        self._create_enhanced_basic_info(basic_frame)
        
        # Players Tab - Use RichTextWidget  
        players_frame = ttk.Frame(notebook, padding="10")
        notebook.add(players_frame, text="Players")
        self._create_enhanced_players_info(players_frame)
        
        # Segments Tab (if available) - Use RichTextWidget
        if self.match.has_detailed_data and self.match.segments:
            segments_frame = ttk.Frame(notebook, padding="10")
            notebook.add(segments_frame, text="Segments")
            self._create_enhanced_segments_info(segments_frame)
        
        # Raw Data Tab - Keep as plain text
        raw_frame = ttk.Frame(notebook, padding="10")
        notebook.add(raw_frame, text="Raw Data")
        self._create_raw_data(raw_frame)
        
        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_button = ttk.Button(button_frame, text="Close", command=self._on_close)
        close_button.pack(side=tk.RIGHT)
    
    def _create_enhanced_basic_info(self, parent):
        """Create enhanced basic match information using RichTextWidget"""
        rich_widget = RichTextWidget(parent, theme="dark")
        rich_widget.pack(fill=tk.BOTH, expand=True)
        
        if self.rich_text_presenter:
            # Use the modern match detail renderer
            self.rich_text_presenter.render_match_detail(rich_widget, self.match, "")
        else:
            # Fallback to manual rich text formatting
            self._manual_basic_info(rich_widget)
    
    def _manual_basic_info(self, widget):
        """Manual rich text formatting for basic info when no presenter available"""
        widget.add_heading(f"Match Details - {self.match.date_str()}", level=1)
        
        # Match Information
        match_info = {
            "Status": self.match.get_status(),
            "Date": self.match.date_str(),
            "Season": str(self.match.season),
            "Seed Type": str(self.match.seed_type or "Unknown"),
            "Match Type": 'Private Room' if self.match.match_type == 3 else 'Ranked' if self.match.match_type == 1 else f'Type {self.match.match_type}',
            "Players": str(self.match.player_count),
            "Forfeited": "Yes" if self.match.forfeited else "No"
        }
        
        if self.match.match_time:
            match_info["Your Time"] = self.match.time_str() if self.match.user_completed else f"({self.match.time_str()})"
        else:
            match_info["Your Time"] = "Did not finish"
        
        widget.add_stats_block("📊 Match Information", match_info)
        widget.finalize()
    
    def _create_enhanced_players_info(self, parent):
        """Create enhanced players information using RichTextWidget"""
        rich_widget = RichTextWidget(parent, theme="dark")
        rich_widget.pack(fill=tk.BOTH, expand=True)
        
        widget = rich_widget
        widget.add_heading("Players in Match", level=2)
        
        if not hasattr(self.match, 'players') or not self.match.players:
            widget.add_text("No player information available.", ['muted'])
            widget.finalize()
            return
        
        # Create players table
        headers = ["Player", "ELO", "Change", "Result", "Time"]
        rows = []
        
        for player in self.match.players:
            username = player.get('username', 'Unknown')
            elo_rate = str(player.get('elo_rate', 'N/A'))
            elo_change = player.get('elo_change', 0)
            elo_change_str = f"{elo_change:+d}" if isinstance(elo_change, int) and elo_change != 0 else "0"
            
            # Determine result and completion time
            completion_time = "Did not finish"
            if 'completionTime' in player and player['completionTime']:
                completion_time = f"{player['completionTime'] / 1000 / 60:.2f}m"
            
            # Mark analyzed user
            if self.match.user_uuid and player.get('uuid') == self.match.user_uuid:
                username += " (You)"
                if self.match.is_user_win is True:
                    result = "Won"
                elif self.match.is_user_win is False:
                    result = "Lost"
                elif self.match.forfeited:
                    result = "Forfeit"
                else:
                    result = "Draw"
            else:
                # Opponent result (inverse of user result)
                if self.match.is_user_win is True:
                    result = "Lost"
                elif self.match.is_user_win is False:
                    result = "Won" 
                elif self.match.forfeited:
                    result = "Forfeit"
                else:
                    result = "Draw"
            
            rows.append([username, elo_rate, elo_change_str, result, completion_time])
        
        widget.add_table(headers, rows)
        widget.finalize()
    
    def _create_enhanced_segments_info(self, parent):
        """Create enhanced segments information with interactive what-if editing"""
        # Dark theme colors
        colors = {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'header_bg': '#2d2d30',
            'header_fg': '#ffffff',
            'row_bg': '#252526',
            'alt_row_bg': '#1e1e1e',
            'accent': '#569cd6',
            'success': '#4ec9b0',
            'border': '#404040'
        }

        # Main container
        main_frame = tk.Frame(parent, bg=colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(main_frame, text="Segment Timing", font=('Segoe UI', 14, 'bold'),
                              bg=colors['bg'], fg=colors['header_fg'])
        title_label.pack(anchor='w', pady=(0, 10))

        if not self.match.segments:
            no_data_label = tk.Label(main_frame, text="No segment timing data available.",
                                    bg=colors['bg'], fg=colors['fg'])
            no_data_label.pack(anchor='w')
            return

        has_percentile_data = self.segment_percentile_data is not None

        # Define segment order and display names
        self._segment_order = [
            ('nether_enter', 'Nether Enter'),
            ('bastion_enter', 'Bastion Enter'),
            ('fortress_enter', 'Fortress Enter'),
            ('blind_portal', 'Blind Portal'),
            ('stronghold_enter', 'Stronghold Enter'),
            ('end_enter', 'End Enter'),
            ('game_end', 'Game End')
        ]

        # Store original and modified split times (in ms)
        self._original_splits = {}
        self._modified_splits = {}
        self._split_labels = {}  # Store label references for updating
        self._percentile_labels = {}  # Store percentile label references

        # Table frame
        table_frame = tk.Frame(main_frame, bg=colors['border'], relief='solid', borderwidth=1)
        table_frame.pack(fill=tk.X, padx=5, pady=5)

        # Headers
        headers = ["Segment", "Absolute Time", "Split Time"]
        if has_percentile_data:
            headers.extend(["Split %ile", "Edit"])

        for col, header in enumerate(headers):
            header_label = tk.Label(table_frame, text=header, font=('Segoe UI', 10, 'bold'),
                                   bg=colors['header_bg'], fg=colors['header_fg'],
                                   padx=10, pady=5, anchor='w')
            header_label.grid(row=0, column=col, sticky='ew')

        # Data rows
        row_idx = 1
        for segment_key, display_name in self._segment_order:
            if segment_key not in self.match.segments:
                continue

            segment_data = self.match.segments[segment_key]
            abs_time_ms = segment_data.get('absolute_time', 0)
            split_time_ms = segment_data.get('split_time', 0)

            # Store original values
            self._original_splits[segment_key] = split_time_ms
            self._modified_splits[segment_key] = split_time_ms

            # Alternating row background
            row_bg = colors['alt_row_bg'] if row_idx % 2 == 0 else colors['row_bg']

            # Segment name
            name_label = tk.Label(table_frame, text=display_name, font=('Segoe UI', 9),
                                 bg=row_bg, fg=colors['fg'], padx=10, pady=3, anchor='w')
            name_label.grid(row=row_idx, column=0, sticky='ew')

            # Absolute time
            abs_label = tk.Label(table_frame, text=format_time_ms(abs_time_ms), font=('Segoe UI', 9),
                                bg=row_bg, fg=colors['fg'], padx=10, pady=3, anchor='w')
            abs_label.grid(row=row_idx, column=1, sticky='ew')

            # Split time (will be updated when edited)
            split_label = tk.Label(table_frame, text=format_time_ms(split_time_ms), font=('Segoe UI', 9),
                                  bg=row_bg, fg=colors['fg'], padx=10, pady=3, anchor='w')
            split_label.grid(row=row_idx, column=2, sticky='ew')
            self._split_labels[segment_key] = split_label

            if has_percentile_data:
                # Calculate percentile
                percentile = None
                percentile_str = "-"
                percentile_color = colors['fg']

                if segment_key in self.segment_percentile_data:
                    split_times = self.segment_percentile_data[segment_key].get('split_times', [])
                    if split_times and split_time_ms > 0:
                        sorted_times = sorted(split_times)
                        percentile = calculate_percentile(split_time_ms, sorted_times)
                        if percentile is not None:
                            percentile_str = f"{percentile:.0f}%"
                            percentile_color = get_percentile_color(percentile) or colors['fg']

                # Percentile label
                pct_label = tk.Label(table_frame, text=percentile_str, font=('Segoe UI', 9),
                                    bg=row_bg, fg=percentile_color, padx=10, pady=3, anchor='w')
                pct_label.grid(row=row_idx, column=3, sticky='ew')
                self._percentile_labels[segment_key] = pct_label

                # Edit button (pencil icon)
                edit_btn = tk.Button(table_frame, text="✏", font=('Segoe UI', 9),
                                    bg=row_bg, fg=colors['accent'], relief='flat',
                                    cursor='hand2', padx=5, pady=0,
                                    command=lambda sk=segment_key, dn=display_name: self._on_edit_split(sk, dn))
                edit_btn.grid(row=row_idx, column=4, sticky='ew', padx=2)

                # Disable edit button if no percentile data for this segment
                if segment_key not in self.segment_percentile_data or \
                   len(self.segment_percentile_data[segment_key].get('split_times', [])) < 3:
                    edit_btn.config(state='disabled', fg=colors['border'])

            row_idx += 1

        # Configure column weights
        for col in range(len(headers)):
            table_frame.grid_columnconfigure(col, weight=1)

        # Simulated time display (only if we have percentile data)
        if has_percentile_data:
            self._create_simulated_time_display(main_frame, colors)

    def _create_simulated_time_display(self, parent, colors):
        """Create the simulated time display panel"""
        # Separator
        separator = tk.Frame(parent, height=2, bg=colors['border'])
        separator.pack(fill='x', pady=10)

        # Original time
        original_time = self.match.match_time if self.match.match_time else 0
        self._original_total_time = original_time

        # Row 1: Original Time
        row1 = tk.Frame(parent, bg=colors['bg'])
        row1.pack(fill='x', pady=2)

        orig_label = tk.Label(row1, text="Original Time:", font=('Segoe UI', 10),
                             bg=colors['bg'], fg=colors['fg'], width=15, anchor='e')
        orig_label.pack(side='left', padx=(0, 5))

        orig_time_label = tk.Label(row1, text=format_time_ms(original_time),
                                   font=('Segoe UI', 10, 'bold'), bg=colors['bg'], fg=colors['fg'])
        orig_time_label.pack(side='left')

        # Row 2: Simulated Time
        row2 = tk.Frame(parent, bg=colors['bg'])
        row2.pack(fill='x', pady=2)

        sim_label = tk.Label(row2, text="Simulated Time:", font=('Segoe UI', 10),
                            bg=colors['bg'], fg=colors['fg'], width=15, anchor='e')
        sim_label.pack(side='left', padx=(0, 5))

        self._simulated_time_label = tk.Label(row2, text=format_time_ms(original_time),
                                              font=('Segoe UI', 10, 'bold'),
                                              bg=colors['bg'], fg=colors['success'])
        self._simulated_time_label.pack(side='left')

        # Row 3: Difference
        row3 = tk.Frame(parent, bg=colors['bg'])
        row3.pack(fill='x', pady=2)

        diff_label = tk.Label(row3, text="Difference:", font=('Segoe UI', 10),
                             bg=colors['bg'], fg=colors['fg'], width=15, anchor='e')
        diff_label.pack(side='left', padx=(0, 5))

        self._diff_label = tk.Label(row3, text="0.000s", font=('Segoe UI', 10, 'bold'),
                                   bg=colors['bg'], fg=colors['fg'])
        self._diff_label.pack(side='left')

        # Reset button row
        btn_row = tk.Frame(parent, bg=colors['bg'])
        btn_row.pack(fill='x', pady=(8, 0))

        reset_btn = tk.Button(btn_row, text="Reset All", font=('Segoe UI', 9),
                             bg=colors['header_bg'], fg=colors['fg'],
                             relief='raised', cursor='hand2', padx=10,
                             command=self._reset_to_original)
        reset_btn.pack(side='left')

        # Store colors reference for updates
        self._colors = colors

    def _on_edit_split(self, segment_key: str, display_name: str):
        """Handle edit button click - show percentile edit popup"""
        colors = self._colors

        # Create popup dialog
        popup = tk.Toplevel(self.dialog)
        popup.title(f"Edit {display_name} Split")
        popup.geometry("320x200")
        popup.resizable(False, False)
        popup.configure(bg=colors['bg'])

        # Make popup modal
        popup.transient(self.dialog)
        popup.grab_set()

        # Center on parent
        popup.update_idletasks()
        x = self.dialog.winfo_x() + (self.dialog.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.dialog.winfo_y() + (self.dialog.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")

        # Content frame
        content = tk.Frame(popup, bg=colors['bg'], padx=20, pady=15)
        content.pack(fill='both', expand=True)

        # Get current percentile
        current_split_ms = self._modified_splits.get(segment_key, 0)
        current_percentile = None
        sorted_times = []

        if segment_key in self.segment_percentile_data:
            split_times = self.segment_percentile_data[segment_key].get('split_times', [])
            if split_times:
                sorted_times = sorted(split_times)
                current_percentile = calculate_percentile(current_split_ms, sorted_times)

        # Info label
        info_text = f"Current split: {format_time_ms(current_split_ms)}"
        if current_percentile is not None:
            info_text += f" ({current_percentile:.0f}%)"
        info_label = tk.Label(content, text=info_text, font=('Segoe UI', 10),
                             bg=colors['bg'], fg=colors['fg'])
        info_label.pack(anchor='w', pady=(0, 10))

        # Percentile input frame
        input_frame = tk.Frame(content, bg=colors['bg'])
        input_frame.pack(fill='x', pady=10)

        pct_label = tk.Label(input_frame, text="Target Percentile:", font=('Segoe UI', 10),
                            bg=colors['bg'], fg=colors['fg'])
        pct_label.pack(side='left', padx=(0, 10))

        # Entry with validation
        vcmd = (popup.register(lambda P: P == "" or (P.replace('.', '', 1).isdigit() and 0 <= float(P) <= 100 if P.replace('.', '', 1).isdigit() else False)), '%P')
        pct_entry = tk.Entry(input_frame, width=10, font=('Segoe UI', 10),
                            validate='key', validatecommand=vcmd)
        pct_entry.pack(side='left')
        if current_percentile is not None:
            pct_entry.insert(0, f"{current_percentile:.0f}")

        pct_suffix = tk.Label(input_frame, text="%", font=('Segoe UI', 10),
                             bg=colors['bg'], fg=colors['fg'])
        pct_suffix.pack(side='left', padx=(2, 0))

        # Preview label
        preview_frame = tk.Frame(content, bg=colors['bg'])
        preview_frame.pack(fill='x', pady=10)

        preview_text_label = tk.Label(preview_frame, text="New split time:", font=('Segoe UI', 10),
                                     bg=colors['bg'], fg=colors['fg'])
        preview_text_label.pack(side='left', padx=(0, 10))

        preview_time_label = tk.Label(preview_frame, text=format_time_ms(current_split_ms),
                                     font=('Segoe UI', 10, 'bold'), bg=colors['bg'], fg=colors['success'])
        preview_time_label.pack(side='left')

        # Update preview on entry change
        def update_preview(*args):
            try:
                pct_val = float(pct_entry.get()) if pct_entry.get() else 0
                new_time = get_time_at_percentile(pct_val, sorted_times)
                if new_time is not None:
                    preview_time_label.config(text=format_time_ms(new_time))
            except ValueError:
                pass

        pct_entry.bind('<KeyRelease>', update_preview)

        # Buttons frame
        btn_frame = tk.Frame(content, bg=colors['bg'])
        btn_frame.pack(fill='x', pady=(15, 0))

        def apply_change():
            try:
                pct_val = float(pct_entry.get()) if pct_entry.get() else current_percentile or 50
                new_time = get_time_at_percentile(pct_val, sorted_times)
                if new_time is not None:
                    self._modified_splits[segment_key] = new_time
                    self._update_split_display(segment_key, new_time, pct_val)
                    self._update_simulated_time()
                popup.destroy()
            except ValueError:
                popup.destroy()

        apply_btn = tk.Button(btn_frame, text="Apply", font=('Segoe UI', 9),
                             bg=colors['accent'], fg='white', relief='raised',
                             cursor='hand2', padx=15, command=apply_change)
        apply_btn.pack(side='right', padx=(5, 0))

        cancel_btn = tk.Button(btn_frame, text="Cancel", font=('Segoe UI', 9),
                              bg=colors['header_bg'], fg=colors['fg'], relief='raised',
                              cursor='hand2', padx=15, command=popup.destroy)
        cancel_btn.pack(side='right')

        # Focus on entry
        pct_entry.focus_set()
        pct_entry.select_range(0, tk.END)

        # Bind Enter key to apply
        popup.bind('<Return>', lambda e: apply_change())
        popup.bind('<Escape>', lambda e: popup.destroy())

    def _update_split_display(self, segment_key: str, new_time_ms: float, new_percentile: float):
        """Update the split time and percentile display for a segment"""
        colors = self._colors

        # Update split time label
        if segment_key in self._split_labels:
            original_time = self._original_splits.get(segment_key, 0)
            is_modified = abs(new_time_ms - original_time) > 1  # 1ms tolerance

            self._split_labels[segment_key].config(
                text=format_time_ms(new_time_ms),
                fg=colors['accent'] if is_modified else colors['fg']
            )

        # Update percentile label
        if segment_key in self._percentile_labels:
            percentile_color = get_percentile_color(new_percentile) or colors['fg']
            self._percentile_labels[segment_key].config(
                text=f"{new_percentile:.0f}%",
                fg=percentile_color
            )

    def _update_simulated_time(self):
        """Recalculate and update the simulated total time"""
        colors = self._colors

        # Calculate total difference from modifications
        total_diff = 0
        for segment_key in self._modified_splits:
            original = self._original_splits.get(segment_key, 0)
            modified = self._modified_splits.get(segment_key, 0)
            total_diff += (modified - original)

        # Calculate simulated time
        simulated_time = self._original_total_time + total_diff

        # Update simulated time label
        self._simulated_time_label.config(text=format_time_ms(simulated_time))

        # Update difference label
        diff_seconds = total_diff / 1000
        if diff_seconds < 0:
            diff_text = f"{diff_seconds:.3f}s"
            diff_color = colors['success']  # Green for time saved
        elif diff_seconds > 0:
            diff_text = f"+{diff_seconds:.3f}s"
            diff_color = '#f48771'  # Red for time lost
        else:
            diff_text = "0.000s"
            diff_color = colors['fg']

        self._diff_label.config(text=diff_text, fg=diff_color)

    def _reset_to_original(self):
        """Reset all splits to original values"""
        colors = self._colors

        for segment_key in self._modified_splits:
            original_time = self._original_splits.get(segment_key, 0)
            self._modified_splits[segment_key] = original_time

            # Update split label
            if segment_key in self._split_labels:
                self._split_labels[segment_key].config(
                    text=format_time_ms(original_time),
                    fg=colors['fg']
                )

            # Update percentile label
            if segment_key in self._percentile_labels and segment_key in self.segment_percentile_data:
                split_times = self.segment_percentile_data[segment_key].get('split_times', [])
                if split_times and original_time > 0:
                    sorted_times = sorted(split_times)
                    percentile = calculate_percentile(original_time, sorted_times)
                    if percentile is not None:
                        percentile_color = get_percentile_color(percentile) or colors['fg']
                        self._percentile_labels[segment_key].config(
                            text=f"{percentile:.0f}%",
                            fg=percentile_color
                        )

        # Reset simulated time display
        self._simulated_time_label.config(text=format_time_ms(self._original_total_time))
        self._diff_label.config(text="0.000s", fg=colors['fg'])

    def _create_raw_data(self, parent):
        """Create raw match data display"""
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 8))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Show raw match data (excluding some large/redundant fields)
        import json
        
        # Create a clean representation of match data
        match_dict = {}
        for attr_name in dir(self.match):
            if not attr_name.startswith('_') and not callable(getattr(self.match, attr_name)):
                value = getattr(self.match, attr_name)
                # Convert datetime objects to strings
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                match_dict[attr_name] = value
        
        raw_text = json.dumps(match_dict, indent=2, default=str, ensure_ascii=False)
        text_widget.insert(tk.END, raw_text)
        text_widget.config(state=tk.DISABLED)
    
    def _on_close(self):
        """Handle dialog close"""
        self.dialog.grab_release()
        self.dialog.destroy()


def show_match_info_dialog(parent, match: Match, rich_text_presenter=None, filtered_matches: Optional[List[Match]] = None):
    """
    Convenience function to show match info dialog

    Args:
        parent: Parent window
        match: Match object to display
        rich_text_presenter: Optional RichTextPresenter for modern formatting
        filtered_matches: Optional list of filtered matches for percentile calculations
    """
    MatchInfoDialog(parent, match, rich_text_presenter, filtered_matches)