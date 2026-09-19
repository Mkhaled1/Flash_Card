import os
from datetime import datetime

class Config:
    """Flask application configuration"""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///flashcards.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    
    # Color scheme (matching the original app)
    COLORS = {
        "primary": "#4F46E5",
        "secondary": "#06B6D4",
        "success": "#10B981",
        "danger": "#EF4444",
        "warning": "#F59E0B",
        "light": "#F9FAFB",
        "dark": "#111827",
        "card_bg": "#FFFFFF",
        "gradient_start": "#4F46E5",
        "gradient_end": "#06B6D4",
    }
