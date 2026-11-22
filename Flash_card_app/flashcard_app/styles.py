# ==================== COLOR SCHEME ====================
# Carefully selected modern color palette for consistent branding throughout the app
COLORS = {
    "primary": "#4F46E5",      # Indigo
    "secondary": "#06B6D4",    # Cyan
    "success": "#10B981",      # Green
    "danger": "#EF4444",       # Red
    "warning": "#F59E0B",      # Amber
    "light": "#F9FAFB",        # Light gray
    "dark": "#111827",         # Dark gray
    "card_bg": "#FFFFFF",      # White
    "gradient_start": "#4F46E5",
    "gradient_end": "#06B6D4",
}

# Global stylesheet with modern design
GLOBAL_STYLESHEET = """
    * {
        border-radius: 8px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    QMainWindow {
        background-color: #F3F4F6;
    }
    
    QWidget {
        background-color: transparent;
    }
    
    QPushButton {
        background-color: #4F46E5;
        color: white;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
        border-radius: 8px;
        font-size: 13px;
    }
    
    QPushButton:hover {
        background-color: #4338CA;
    }
    
    QPushButton:pressed {
        background-color: #3730A3;
    }
    
    QLabel {
        color: #111827;
    }
    
    QListWidget {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        background-color: white;
        padding: 5px;
    }
    
    QListWidget::item:selected {
        background-color: #4F46E5;
        color: white;
    }
    
    QTableWidget {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        background-color: white;
    }
    
    QTableWidget::item:selected {
        background-color: #4F46E5;
        color: white;
    }
    
    QHeaderView::section {
        background-color: #F3F4F6;
        padding: 5px;
        border: none;
        font-weight: 600;
    }
"""

