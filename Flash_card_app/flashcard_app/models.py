import csv
import random
from datetime import date, timedelta, datetime
class FlashCard:
    """
    Represents a single flashcard with SM-2 algorithm tracking.
    
    Attributes:
        word (str): The German word or phrase to learn
        definition (str): English definition or explanation
        reps (int): Number of successful repetitions (for spacing calculation)
        interval (int): Days until next review
        ef (float): Ease factor (1.3-5.0) - affects review difficulty
        next_due (date): Next scheduled review date
    
    SM-2 Status Mapping (based on ease factor):
        ef < 1.5: "Unknown" (very difficult)
        1.5 â‰¤ ef < 1.8: "Hard" (difficult)
        1.8 â‰¤ ef < 2.3: "Medium" (moderate difficulty)
        2.3 â‰¤ ef < 2.7: "Memorized" (well known)
        ef â‰¥ 2.7: "Perfectly Memorized" (mastered)
    """
    
    def __init__(self, word, definition,
                 reps=0, interval=0, ef=2.5, next_due=None):
        """Initialize a flashcard with word, definition, and SM-2 parameters."""
        # Ensure word and definition are valid strings
        self.word = str(word) if word else ""
        self.definition = str(definition) if definition else ""
        
        # Safely convert repetition count (must be integer)
        try:
            self.reps = int(reps) if reps else 0
        except (ValueError, TypeError):
            self.reps = 0
        
        # Safely convert interval (must be integer, in days)
        try:
            self.interval = int(interval) if interval else 0
        except (ValueError, TypeError):
            self.interval = 0
        
        # Safely convert ease factor (must be float between 1.3 and 5.0)
        try:
            self.ef = float(ef) if ef else 2.5
        except (ValueError, TypeError):
            self.ef = 2.5
        
        # Ensure ef is within valid range (minimum 1.3 for SM-2)
        if self.ef < 1.3:
            self.ef = 1.3
        
        # Parse next_due date - handles string, date, or None
        try:
            if isinstance(next_due, str):
                next_due_str = str(next_due).strip()
                if next_due_str:
                    try:
                        self.next_due = datetime.strptime(next_due_str, "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        self.next_due = date.today()
                else:
                    self.next_due = date.today()
            elif isinstance(next_due, date):
                self.next_due = next_due
            else:
                self.next_due = date.today()
        except Exception:
            self.next_due = date.today()

    def is_due(self):
        """Check if this card is scheduled for review today or earlier."""
        return self.next_due <= date.today()

    def update_sm2(self, quality):
        """
        Update card using SM-2 algorithm with direct status mapping.
        
        Quality values directly map to target status:
            0 = Unknown (ef = 1.4)
            1 = Hard (ef = 1.7)
            2 = Medium (ef = 2.0)
            3 = Memorized (ef = 2.5)
            5 = Perfectly Memorized (ef = 2.8)
        
        Each button press immediately moves card to target status and updates
        the next review date based on the interval calculation.
        """
        # Direct status mapping: set ef to achieve target status in one click
        status_to_ef = {
            0: 1.4,   # Unknown: ef < 1.5
            1: 1.7,   # Hard: 1.5 â‰¤ ef < 1.8
            2: 2.0,   # Medium: 1.8 â‰¤ ef < 2.3
            3: 2.5,   # Memorized: 2.3 â‰¤ ef < 2.7
            5: 2.8,   # Perfectly Memorized: ef â‰¥ 2.7
        }
        
        # Set ease factor to achieve the target status directly
        if quality in status_to_ef:
            self.ef = status_to_ef[quality]
        else:
            # Fallback to SM-2 if unknown quality value
            self.ef = self.ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        if self.ef < 1.3:
            self.ef = 1.3
        
        # For lower statuses (quality < 3), don't increase reps counter
        # This allows the card to stay in earlier states until progressed
        if quality < 3:
            # Lower statuses get shown again today until progressed
            self.reps = 0
            self.interval = 1
            self.next_due = date.today()
            return
        
        # Higher statuses use spaced repetition intervals based on ease factor
        # Intervals: 1 day, 6 days, then ef-based exponential spacing
        if self.reps == 0:
            self.interval = 1
        elif self.reps == 1:
            self.interval = 6
        else:
            self.interval = int(round(self.interval * self.ef))
        
        self.reps += 1
        self.next_due = date.today() + timedelta(days=self.interval)

    def reset(self):
        """Reset card to initial state (New)."""
        self.reps = 0
        self.interval = 0
        self.ef = 2.5
        self.next_due = date.today()

    def rating(self):
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


# ==================== DECK MANAGEMENT ====================
# Handles loading, saving, and querying flashcard collections

class FlashCardDeck:
    """
    Manages a collection of flashcards with CSV persistence.
    
    Provides methods for:
    - Loading/saving deck from/to CSV files
    - Querying cards by various criteria
    - Computing learning statistics
    - Managing study sessions
    """
    
    def __init__(self):
        """Initialize an empty deck."""
        self.cards = []  # List of FlashCard objects
        self.filename = None  # Current deck file path

    def load_from_csv(self, filename):
        """
        Load flashcards from CSV file with comprehensive error handling.
        
        CSV Format: word, definition, reps, interval, ef, next_due
        Handles malformed rows, missing values, and type errors gracefully.
        
        Args:
            filename (str): Path to CSV file containing flashcard data
        """
        self.cards.clear()
        self.filename = filename
        try:
            with open(filename, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Skip completely empty rows
                        if not row or all(not cell.strip() for cell in row):
                            continue
                        
                        # Need at least word and definition columns
                        if len(row) < 2:
                            print(f"Warning: Row {row_num} has less than 2 columns, skipping")
                            continue
                        
                        # Extract values with defaults
                        word = str(row[0]).strip() if len(row) > 0 else ""
                        definition = str(row[1]).strip() if len(row) > 1 else ""
                        
                        # Skip if word or definition is empty
                        if not word or not definition:
                            print(f"Warning: Row {row_num} missing word or definition, skipping")
                            continue
                        
                        # Extract optional fields with safe defaults
                        reps = 0
                        interval = 0
                        ef = 2.5
                        next_due = ""
                        
                        if len(row) > 2:
                            try:
                                reps = int(str(row[2]).strip()) if row[2].strip() else 0
                            except (ValueError, IndexError, AttributeError):
                                reps = 0
                        
                        if len(row) > 3:
                            try:
                                interval = int(str(row[3]).strip()) if row[3].strip() else 0
                            except (ValueError, IndexError, AttributeError):
                                interval = 0
                        
                        if len(row) > 4:
                            try:
                                ef = float(str(row[4]).strip()) if row[4].strip() else 2.5
                            except (ValueError, IndexError, AttributeError):
                                ef = 2.5
                        
                        if len(row) > 5:
                            try:
                                next_due = str(row[5]).strip() if row[5] else ""
                            except (IndexError, AttributeError):
                                next_due = ""
                        
                        # Create card with safe values
                        card = FlashCard(word, definition, reps, interval, ef, next_due)
                        self.cards.append(card)
                        
                    except Exception as e:
                        print(f"Warning: Error processing row {row_num}: {str(e)}")
                        continue
        except Exception as e:
            print(f"Error loading CSV file: {str(e)}")
            raise

    def save_to_csv(self):
        """
        Persist all flashcards to CSV file with proper encoding.
        
        Format: word, definition, reps, interval, ease_factor, next_due_date
        Ensures data survives application restarts and is human-readable.
        """
        if not self.filename:
            return
        with open(self.filename, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for c in self.cards:
                # Write card data in consistent CSV format with 3 decimal places for ease factor
                writer.writerow([
                    c.word,
                    c.definition,
                    c.reps,
                    c.interval,
                    f"{c.ef:.3f}",
                    c.next_due.strftime("%Y-%m-%d")
                ])

    def get_due_cards(self):
        """Filter cards that are scheduled for review today or earlier."""
        return [c for c in self.cards if c.is_due()]

    def get_random_due_card(self):
        """Get a random card from due cards list for study session."""
        due = self.get_due_cards()
        if not due:
            return None
        return random.choice(due)

    def add_card(self, word, definition):
        """Add a new card with German word and English definition."""
        self.cards.append(FlashCard(word, definition))

    def remove_card(self, index):
        """Remove a card at the specified index from the deck."""
        if 0 <= index < len(self.cards):
            del self.cards[index]

    def stats(self):
        """
        Calculate key deck statistics for progress tracking.
        
        Returns:
            tuple: (total_cards, cards_due, cards_learned_with_3+_reps)
        """
        total = len(self.cards)
        due = len(self.get_due_cards())
        learned = len([c for c in self.cards if c.reps >= 3])
        return total, due, learned

    def status_counts(self):
        new = sum(1 for c in self.cards if c.reps == 0 and c.interval == 0)
        learning = sum(1 for c in self.cards if 0 < c.reps < 3)
        learned = sum(1 for c in self.cards if c.reps >= 3)
        return new, learning, learned

    def rating_counts(self):
        """Count cards by their rating: new, unknown, hard, medium, memorized, perfectly memorized"""
        new = sum(1 for c in self.cards if c.rating() == "New")
        unknown = sum(1 for c in self.cards if c.rating() == "Unknown")
        hard = sum(1 for c in self.cards if c.rating() == "Hard")
        medium = sum(1 for c in self.cards if c.rating() == "Medium")
        memorized = sum(1 for c in self.cards if c.rating() == "Memorized")
        perfectly = sum(1 for c in self.cards if c.rating() == "Perfectly Memorized")
        return new, unknown, hard, medium, memorized, perfectly

    def get_random_card(self):
        """Get a random card from the deck (regardless of due date)"""
        if not self.cards:
            return None
        return random.choice(self.cards)

    def all_cards_mastered(self):
        """Check if all cards have reached Perfectly Memorized status"""
        if not self.cards:
            return False
        return all(c.rating() == "Perfectly Memorized" for c in self.cards)

