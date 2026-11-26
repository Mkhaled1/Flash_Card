from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta, datetime
from typing import Literal

db = SQLAlchemy()


class Deck(db.Model):
    """Represents a collection of flashcards"""
    __tablename__ = 'decks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(500))
    is_archived = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cards = db.relationship('FlashCard', backref='deck', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert deck to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_archived': self.is_archived,
            'card_count': len(self.cards),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class FlashCard(db.Model):
    """Represents a single flashcard with SM-2 algorithm tracking"""
    __tablename__ = 'flashcards'
    
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False)
    
    # Card content
    word = db.Column(db.String(255), nullable=False)  # German word
    definition = db.Column(db.Text, nullable=False)   # English definition
    
    # SM-2 Algorithm parameters
    reps = db.Column(db.Integer, default=0)           # Number of successful repetitions
    interval = db.Column(db.Integer, default=0)       # Days until next review
    ef = db.Column(db.Float, default=2.5)             # Ease factor (1.3-5.0)
    next_due = db.Column(db.Date, default=date.today) # Next review date
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_due(self) -> bool:
        """Check if card is scheduled for review today or earlier"""
        return self.next_due <= date.today()
    
    def get_rating(self) -> str:
        """
        Determine card status based on ease factor (ef).
        
        Returns:
            str: One of "New", "Unknown", "Hard", "Medium", "Memorized", "Perfectly Memorized"
        """
        # Brand new card (never studied)
        if self.reps == 0 and self.interval == 0 and self.ef == 2.5:
            return "New"
        
        # Determine status based on ease factor ranges
        if self.ef < 1.5:
            return "Unknown"
        elif self.ef < 1.8:
            return "Hard"
        elif self.ef < 2.3:
            return "Medium"
        elif self.ef < 2.7:
            return "Memorized"
        return "Perfectly Memorized"
    
    def update_sm2(self, quality: int) -> None:
        """
        Update card using SM-2 algorithm.
        
        Quality values directly map to target status:
            0 = Unknown (ef = 1.4)
            1 = Hard (ef = 1.7)
            2 = Medium (ef = 2.0)
            3 = Memorized (ef = 2.5)
            5 = Perfectly Memorized (ef = 2.8)
        """
        # Direct status mapping
        status_to_ef = {
            0: 1.4,   # Unknown
            1: 1.7,   # Hard
            2: 2.0,   # Medium
            3: 2.5,   # Memorized
            5: 2.8,   # Perfectly Memorized
        }
        
        # Set ease factor based on quality
        if quality in status_to_ef:
            self.ef = status_to_ef[quality]
        else:
            # Fallback to SM-2 calculation
            self.ef = self.ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Ensure ef is within valid range
        if self.ef < 1.3:
            self.ef = 1.3
        
        # For lower statuses, don't increase reps counter
        if quality < 3:
            self.reps = 0
            self.interval = 1
            self.next_due = date.today()
            return
        
        # Use spaced repetition intervals for higher statuses
        if self.reps == 0:
            self.interval = 1
        elif self.reps == 1:
            self.interval = 6
        else:
            self.interval = int(round(self.interval * self.ef))
        
        self.reps += 1
        self.next_due = date.today() + timedelta(days=self.interval)
    
    def reset(self) -> None:
        """Reset card to initial state"""
        self.reps = 0
        self.interval = 0
        self.ef = 2.5
        self.next_due = date.today()
    
    def to_dict(self, show_definition: bool = False) -> dict:
        """Convert card to dictionary"""
        return {
            'id': self.id,
            'deck_id': self.deck_id,
            'word': self.word,
            'definition': self.definition if show_definition else None,
            'reps': self.reps,
            'interval': self.interval,
            'ef': round(self.ef, 2),
            'next_due': self.next_due.isoformat(),
            'rating': self.get_rating(),
            'is_due': self.is_due(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
