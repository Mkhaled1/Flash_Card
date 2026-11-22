import os


database_url = os.environ.get("DATABASE_URL", "sqlite:///flashcards.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)


class Config:
    """Flask application configuration"""
    SQLALCHEMY_DATABASE_URI = database_url
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
