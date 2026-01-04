"""
Table Widget with proper line rendering for MCSR Stats Browser.
Creates clean tables using tkinter native drawing instead of ASCII characters.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Dict, Any


class TableWidget(tk.Frame):
    """A clean table widget that uses proper line drawing instead of ASCII art."""
    
    def __init__(self, parent, headers: List[str], rows: List[List[str]], 
                 theme="dark", **kwargs):
        """
        Initialize table widget with headers and data.
        
        Args:
            parent: Parent tkinter widget
            headers: List of column headers
            rows: List of row data (each row is a list of strings)
            theme: Color theme ("dark" or "light")
            **kwargs: Additional arguments passed to Frame
        """
        super().__init__(parent, **kwargs)
        
        self.headers = headers
        self.rows = rows
        self.theme = theme
        
        # Configure colors based on theme
        if theme == "dark":
            self.colors = {
                'bg': '#1e1e1e',
                'fg': '#d4d4d4',
                'header_bg': '#2d2d30',
                'header_fg': '#ffffff',
                'row_bg': '#252526',
                'alt_row_bg': '#1e1e1e',
                'border': '#404040',
                'line': '#404040'
            }
        else:
            self.colors = {
                'bg': '#ffffff',
                'fg': '#000000',
                'header_bg': '#f6f8fa',
                'header_fg': '#2d2d2d',
                'row_bg': '#ffffff',
                'alt_row_bg': '#f6f8fa',
                'border': '#d1d9e0',
                'line': '#d1d9e0'
            }
        
        self.configure(bg=self.colors['bg'])
        self._create_table()
    
    def _create_table(self):
        """Create the table using Treeview widget for clean presentation."""
        # Create treeview with custom styling
        style = ttk.Style()
        
        # Configure treeview style for clean appearance
        style.configure(
            "Table.Treeview",
            background=self.colors['row_bg'],
            foreground=self.colors['fg'],
            fieldbackground=self.colors['row_bg'],
            borderwidth=1,
            relief="solid"
        )
        
        style.configure(
            "Table.Treeview.Heading",
            background=self.colors['header_bg'],
            foreground=self.colors['header_fg'],
            borderwidth=1,
            relief="solid"
        )
        
        # Map for alternating row colors
        style.map(
            "Table.Treeview",
            background=[('selected', '#569cd6'), ('!selected', self.colors['row_bg'])]
        )
        
        # Create treeview
        self.tree = ttk.Treeview(
            self, 
            columns=self.headers,
            show='headings',
            style="Table.Treeview",
            selectmode='none'  # Disable selection for clean table appearance
        )
        
        # Configure column headers
        for col in self.headers:
            self.tree.heading(col, text=col, anchor='w')
            # Calculate column width based on content
            col_width = max(
                len(col) * 10,  # Header width
                max((len(str(row[self.headers.index(col)])) * 8 
                    for row in self.rows if self.headers.index(col) < len(row)), 
                    default=80)  # Content width
            )
            self.tree.column(col, width=max(col_width, 80), anchor='w')
        
        # Add rows with alternating colors
        for i, row in enumerate(self.rows):
            # Ensure row has enough values
            padded_row = row + [''] * (len(self.headers) - len(row))
            tags = ('alternate',) if i % 2 == 1 else ()
            self.tree.insert('', 'end', values=padded_row, tags=tags)
        
        # Configure alternate row color
        self.tree.tag_configure('alternate', background=self.colors['alt_row_bg'])
        
        # Pack the treeview
        self.tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Add a subtle border frame
        self.configure(relief='solid', borderwidth=1, highlightbackground=self.colors['line'])


class SimpleTableWidget(tk.Frame):
    """A simpler table widget using labels with custom line drawing."""
    
    def __init__(self, parent, headers: List[str], rows: List[List[str]], 
                 theme="dark", **kwargs):
        """Initialize simple table with label-based cells and drawn borders."""
        super().__init__(parent, **kwargs)
        
        self.headers = headers
        self.rows = rows
        self.theme = theme
        
        # Configure colors
        if theme == "dark":
            self.colors = {
                'bg': '#1e1e1e',
                'fg': '#d4d4d4',
                'header_bg': '#2d2d30',
                'header_fg': '#ffffff',
                'border': '#404040'
            }
        else:
            self.colors = {
                'bg': '#ffffff',
                'fg': '#000000',
                'header_bg': '#f6f8fa',
                'header_fg': '#2d2d2d',
                'border': '#d1d9e0'
            }
        
        self.configure(bg=self.colors['bg'], relief='solid', borderwidth=1)
        self._create_simple_table()
    
    def _create_simple_table(self):
        """Create table using grid layout with labels."""
        # Create header row
        for col, header in enumerate(self.headers):
            header_label = tk.Label(
                self,
                text=header,
                bg=self.colors['header_bg'],
                fg=self.colors['header_fg'],
                font=('Segoe UI', 10, 'bold'),
                anchor='w',
                padx=10,
                pady=5,
                relief='solid',
                borderwidth=1
            )
            header_label.grid(row=0, column=col, sticky='ew')
        
        # Create data rows
        for row_idx, row in enumerate(self.rows, start=1):
            for col_idx, cell in enumerate(row):
                # Use alternating row colors
                bg_color = self.colors['bg'] if row_idx % 2 == 1 else '#252526' if self.theme == "dark" else '#f6f8fa'
                
                cell_label = tk.Label(
                    self,
                    text=str(cell),
                    bg=bg_color,
                    fg=self.colors['fg'],
                    font=('Segoe UI', 9),
                    anchor='w',
                    padx=10,
                    pady=3,
                    relief='solid',
                    borderwidth=1
                )
                cell_label.grid(row=row_idx, column=col_idx, sticky='ew')
        
        # Configure column weights for proper expansion
        for col in range(len(self.headers)):
            self.grid_columnconfigure(col, weight=1)


class AdvancedTableWidget(tk.Frame):
    """Advanced table widget with header/subheader support for comparison tables."""
    
    def __init__(self, parent, main_headers: List[str], sub_headers: List[List[str]], 
                 rows: List[List[str]], theme="dark", **kwargs):
        """
        Initialize advanced table with main headers and subheaders.
        
        Args:
            parent: Parent tkinter widget
            main_headers: List of main column headers
            sub_headers: List of subheader lists for each main header
            rows: List of row data
            theme: Color theme
        """
        super().__init__(parent, **kwargs)
        
        self.main_headers = main_headers
        self.sub_headers = sub_headers
        self.rows = rows
        self.theme = theme
        
        # Configure colors
        if theme == "dark":
            self.colors = {
                'bg': '#1e1e1e',
                'fg': '#d4d4d4',
                'main_header_bg': '#404040',
                'main_header_fg': '#ffffff',
                'sub_header_bg': '#2d2d30',
                'sub_header_fg': '#d4d4d4',
                'row_bg': '#252526',
                'alt_row_bg': '#1e1e1e',
                'border': '#404040'
            }
        else:
            self.colors = {
                'bg': '#ffffff',
                'fg': '#000000',
                'main_header_bg': '#e1e4e8',
                'main_header_fg': '#24292e',
                'sub_header_bg': '#f6f8fa',
                'sub_header_fg': '#586069',
                'row_bg': '#ffffff',
                'alt_row_bg': '#f6f8fa',
                'border': '#d1d9e0'
            }
        
        self.configure(bg=self.colors['bg'], relief='solid', borderwidth=1)
        self._create_advanced_table()
    
    def _create_advanced_table(self):
        """Create table with main headers and subheaders."""
        current_row = 0
        
        # Calculate column spans
        col_spans = []
        total_cols = 0
        for i, sub_list in enumerate(self.sub_headers):
            col_spans.append(len(sub_list) if sub_list else 1)
            total_cols += col_spans[i]
        
        # Create main headers row
        current_col = 0
        for i, (header, span) in enumerate(zip(self.main_headers, col_spans)):
            main_header = tk.Label(
                self,
                text=header,
                bg=self.colors['main_header_bg'],
                fg=self.colors['main_header_fg'],
                font=('Segoe UI', 10, 'bold'),
                anchor='center',
                padx=8,
                pady=4,
                relief='solid',
                borderwidth=1
            )
            main_header.grid(row=current_row, column=current_col, columnspan=span, sticky='ew')
            current_col += span
        
        current_row += 1
        
        # Create subheaders row
        current_col = 0
        for i, sub_list in enumerate(self.sub_headers):
            if sub_list:
                for sub_header in sub_list:
                    sub_label = tk.Label(
                        self,
                        text=sub_header,
                        bg=self.colors['sub_header_bg'],
                        fg=self.colors['sub_header_fg'],
                        font=('Segoe UI', 9),
                        anchor='center',
                        padx=6,
                        pady=3,
                        relief='solid',
                        borderwidth=1
                    )
                    sub_label.grid(row=current_row, column=current_col, sticky='ew')
                    current_col += 1
            else:
                # No subheaders for this column, create empty cell
                empty_label = tk.Label(
                    self,
                    text="",
                    bg=self.colors['sub_header_bg'],
                    relief='solid',
                    borderwidth=1
                )
                empty_label.grid(row=current_row, column=current_col, sticky='ew')
                current_col += 1
        
        current_row += 1
        
        # Create data rows
        for row_idx, row in enumerate(self.rows):
            bg_color = self.colors['alt_row_bg'] if row_idx % 2 == 1 else self.colors['row_bg']
            
            for col_idx, cell in enumerate(row):
                if col_idx >= total_cols:
                    break
                    
                cell_label = tk.Label(
                    self,
                    text=str(cell),
                    bg=bg_color,
                    fg=self.colors['fg'],
                    font=('Segoe UI', 9),
                    anchor='center',
                    padx=6,
                    pady=2,
                    relief='solid',
                    borderwidth=1
                )
                cell_label.grid(row=current_row + row_idx, column=col_idx, sticky='ew')
        
        # Configure column weights for proper expansion
        for col in range(total_cols):
            self.grid_columnconfigure(col, weight=1, minsize=60)


def create_clean_table(parent, headers: List[str], rows: List[List[str]], 
                      theme="dark", simple=False, advanced=False,
                      main_headers=None, sub_headers=None) -> tk.Widget:
    """
    Factory function to create a clean table widget.
    
    Args:
        parent: Parent widget
        headers: Column headers (used for simple/standard tables)
        rows: Table data
        theme: Color theme
        simple: Use simple label-based table instead of treeview
        advanced: Use advanced table with main/sub headers
        main_headers: Main headers for advanced table
        sub_headers: Subheaders for advanced table
        
    Returns:
        Configured table widget
    """
    if advanced and main_headers and sub_headers:
        return AdvancedTableWidget(parent, main_headers, sub_headers, rows, theme)
    elif simple:
        return SimpleTableWidget(parent, headers, rows, theme)
    else:
        return TableWidget(parent, headers, rows, theme)