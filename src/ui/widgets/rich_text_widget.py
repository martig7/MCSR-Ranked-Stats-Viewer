"""
Rich Text Widget for enhanced text presentation in MCSR Stats Browser.
Provides styled text with semantic formatting, responsive tables, and modern typography.
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Dict, Optional, Tuple, Any, List


class RichTextWidget(tk.Text):
    """Enhanced Text widget with rich formatting capabilities."""
    
    def __init__(self, parent, theme="dark", **kwargs):
        """
        Initialize RichTextWidget with styling capabilities.
        
        Args:
            parent: Parent tkinter widget
            theme: Color theme ("dark" or "light")
            **kwargs: Additional arguments passed to tk.Text
        """
        # Set default text widget options
        default_options = {
            'wrap': tk.WORD,
            'state': tk.NORMAL,
            'relief': 'flat',
            'borderwidth': 0,
            'padx': 20,
            'pady': 15,
            'spacing1': 5,  # Space above paragraphs
            'spacing2': 2,  # Space between lines
            'spacing3': 5,  # Space below paragraphs
        }
        default_options.update(kwargs)
        
        super().__init__(parent, **default_options)
        
        self.theme = theme
        self._setup_fonts()
        self._setup_colors()
        self._setup_tags()
        
        # Bind resize event for responsive behavior
        self.bind('<Configure>', self._on_resize)
        
        # Track content for responsive adjustments
        self._last_width = 0
        
    def _setup_fonts(self):
        """Setup font families and sizes for different text elements."""
        try:
            # Try to use system fonts, fallback to defaults
            self.fonts = {
                'default': tkfont.Font(family='Segoe UI', size=10),
                'heading1': tkfont.Font(family='Segoe UI', size=16, weight='bold'),
                'heading2': tkfont.Font(family='Segoe UI', size=14, weight='bold'),
                'heading3': tkfont.Font(family='Segoe UI', size=12, weight='bold'),
                'monospace': tkfont.Font(family='Consolas', size=10),
                'monospace_bold': tkfont.Font(family='Consolas', size=10, weight='bold'),
                'small': tkfont.Font(family='Segoe UI', size=9),
                'large': tkfont.Font(family='Segoe UI', size=12),
            }
        except Exception:
            # Fallback to default fonts if system fonts not available
            self.fonts = {
                'default': tkfont.Font(size=10),
                'heading1': tkfont.Font(size=16, weight='bold'),
                'heading2': tkfont.Font(size=14, weight='bold'),
                'heading3': tkfont.Font(size=12, weight='bold'),
                'monospace': tkfont.Font(family='Courier', size=10),
                'monospace_bold': tkfont.Font(family='Courier', size=10, weight='bold'),
                'small': tkfont.Font(size=9),
                'large': tkfont.Font(size=12),
            }
    
    def _setup_colors(self):
        """Setup color schemes for different themes."""
        if self.theme == "dark":
            self.colors = {
                'bg': '#1e1e1e',
                'fg': '#d4d4d4',
                'heading': '#ffffff',
                'accent': '#569cd6',
                'success': '#4ec9b0',
                'warning': '#ffd700',
                'error': '#f48771',
                'muted': '#808080',
                'table_header': '#2d2d30',
                'table_row': '#252526',
                'table_alt': '#1e1e1e',
                'border': '#404040',
            }
        else:  # light theme
            self.colors = {
                'bg': '#ffffff',
                'fg': '#000000',
                'heading': '#2d2d2d',
                'accent': '#0066cc',
                'success': '#008751',
                'warning': '#b8860b',
                'error': '#d73a49',
                'muted': '#586069',
                'table_header': '#f6f8fa',
                'table_row': '#ffffff',
                'table_alt': '#f6f8fa',
                'border': '#d1d9e0',
            }
        
        # Apply background color
        self.config(bg=self.colors['bg'], fg=self.colors['fg'])
        
    def _setup_tags(self):
        """Setup text tags for semantic styling."""
        # Heading tags
        self.tag_configure('h1', 
                          font=self.fonts['heading1'], 
                          foreground=self.colors['heading'],
                          spacing1=15, spacing3=10)
        
        self.tag_configure('h2', 
                          font=self.fonts['heading2'], 
                          foreground=self.colors['heading'],
                          spacing1=12, spacing3=8)
        
        self.tag_configure('h3', 
                          font=self.fonts['heading3'], 
                          foreground=self.colors['heading'],
                          spacing1=10, spacing3=6)
        
        # Text style tags
        self.tag_configure('bold', font=self.fonts['monospace_bold'])
        self.tag_configure('monospace', font=self.fonts['monospace'])
        self.tag_configure('small', font=self.fonts['small'])
        self.tag_configure('large', font=self.fonts['large'])
        
        # Semantic color tags
        self.tag_configure('accent', foreground=self.colors['accent'])
        self.tag_configure('success', foreground=self.colors['success'])
        self.tag_configure('warning', foreground=self.colors['warning'])
        self.tag_configure('error', foreground=self.colors['error'])
        self.tag_configure('muted', foreground=self.colors['muted'])
        
        # Layout tags
        self.tag_configure('center', justify=tk.CENTER)
        self.tag_configure('right', justify=tk.RIGHT)
        self.tag_configure('indent', lmargin1=20, lmargin2=20)
        
        # Table tags
        self.tag_configure('table_header', 
                          font=self.fonts['monospace_bold'],
                          foreground=self.colors['heading'],
                          background=self.colors['table_header'])
        
        self.tag_configure('table_row', 
                          font=self.fonts['monospace'],
                          background=self.colors['table_row'])
        
        self.tag_configure('table_alt', 
                          font=self.fonts['monospace'],
                          background=self.colors['table_alt'])
        
        # Special formatting tags
        self.tag_configure('separator', 
                          foreground=self.colors['border'],
                          font=self.fonts['monospace'])
        
    def _on_resize(self, event=None):
        """Handle widget resize for responsive behavior."""
        if event and event.widget == self:
            current_width = self.winfo_width()
            if current_width != self._last_width and current_width > 1:
                self._last_width = current_width
                # Could trigger responsive table recalculation here if needed
    
    def clear(self):
        """Clear all text content."""
        self.config(state=tk.NORMAL)
        self.delete('1.0', tk.END)
    
    def add_heading(self, text: str, level: int = 1):
        """Add a styled heading."""
        if level == 1:
            tag = 'h1'
        elif level == 2:
            tag = 'h2'
        else:
            tag = 'h3'
        
        self.insert(tk.END, text + '\n', tag)
    
    def add_text(self, text: str, tags: Optional[List[str]] = None):
        """Add text with optional styling tags."""
        if tags is None:
            tags = []
        self.insert(tk.END, text, tags)
    
    def add_line(self, text: str = "", tags: Optional[List[str]] = None):
        """Add a line of text with newline."""
        self.add_text(text + '\n', tags)
    
    def add_separator(self, char: str = '─', width: Optional[int] = None):
        """Add a separator line."""
        if width is None:
            # Calculate width based on current widget size
            try:
                widget_width = self.winfo_width()
                char_width = self.fonts['monospace'].measure(char)
                if widget_width > 1 and char_width > 0:
                    width = max(1, (widget_width - 40) // char_width)  # Account for padding
                else:
                    width = 60  # Default width
            except:
                width = 60
        
        separator = char * width
        self.add_line(separator, ['separator'])
    
    def add_table(self, headers: List[str], rows: List[List[str]], 
                  column_widths: Optional[List[int]] = None):
        """Add a formatted table."""
        if not headers or not rows:
            return
        
        # Calculate column widths if not provided
        if column_widths is None:
            column_widths = self._calculate_column_widths(headers, rows)
        
        # Add table header
        header_line = self._format_table_row(headers, column_widths)
        self.add_line(header_line, ['table_header'])
        
        # Add separator
        separator_parts = []
        for width in column_widths:
            separator_parts.append('─' * width)
        separator = '─'.join(separator_parts)
        self.add_line(separator, ['separator'])
        
        # Add table rows with alternating colors
        for i, row in enumerate(rows):
            row_line = self._format_table_row(row, column_widths)
            tag = 'table_alt' if i % 2 == 1 else 'table_row'
            self.add_line(row_line, [tag])
    
    def _calculate_column_widths(self, headers: List[str], rows: List[List[str]]) -> List[int]:
        """Calculate optimal column widths for a table."""
        if not headers:
            return []
        
        # Start with header widths
        widths = [len(header) for header in headers]
        
        # Check all row data
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))
        
        # Add padding
        widths = [w + 2 for w in widths]
        
        # Ensure minimum width and handle very wide tables
        try:
            widget_width = self.winfo_width()
            if widget_width > 1:
                available_width = widget_width - 60  # Account for padding and scrollbar
                total_width = sum(widths)
                
                # If table is too wide, proportionally reduce column widths
                if total_width > available_width:
                    scale_factor = available_width / total_width
                    widths = [max(8, int(w * scale_factor)) for w in widths]
        except:
            pass  # Use calculated widths as-is if widget size unavailable
        
        return widths
    
    def _format_table_row(self, cells: List[str], widths: List[int]) -> str:
        """Format a table row with proper alignment."""
        formatted_cells = []
        for i, cell in enumerate(cells):
            if i < len(widths):
                width = widths[i]
                # Truncate if too long, pad if too short
                cell_str = str(cell)
                if len(cell_str) > width - 2:
                    cell_str = cell_str[:width - 5] + '...'
                formatted_cells.append(f" {cell_str:<{width-2}} ")
            else:
                formatted_cells.append(f" {str(cell)} ")
        
        return '│'.join(formatted_cells)
    
    def add_stats_block(self, title: str, stats: Dict[str, Any], 
                       value_color: str = 'accent'):
        """Add a formatted statistics block."""
        self.add_heading(title, level=3)
        
        # Find the longest key for alignment
        max_key_length = max(len(key) for key in stats.keys()) if stats else 0
        
        for key, value in stats.items():
            key_padded = f"{key}:".ljust(max_key_length + 2)
            self.add_text(f"  {key_padded}", ['muted'])
            self.add_line(f"{value}", [value_color])
        
        self.add_line()  # Empty line after stats block
    
    def finalize(self):
        """Finalize the text widget (disable editing)."""
        self.config(state=tk.DISABLED)