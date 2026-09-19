"""
================================================================================
FLASHCARD APPLICATION - German Language Learning Tool
================================================================================
A modern spaced repetition flashcard application using SM-2 algorithm for
efficient learning. Features include:
- 6-level status system (New, Unknown, Hard, Medium, Memorized, Perfectly Memorized)
- SM-2 spaced repetition algorithm with ease factor tracking
- Interactive card flipping with smooth animations
- Real-time progress visualization with donut chart
- CSV-based deck persistence
- Continuous study mode until all cards are mastered

Author: AI Assistant
Date: January 2026
================================================================================
"""

# ==================== IMPORTS ====================
# Standard library modules for core functionality
import sys                    # System-level operations
import os                     # File system operations
import csv                    # CSV file handling
import random                 # Random selection of cards
from datetime import date, timedelta, datetime  # Date/time calculations for spaced repetition

# ==================== PySide6 UI FRAMEWORK ====================
# Qt framework for cross-platform GUI development
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QDialog, QHBoxLayout, QListWidget, QInputDialog,
    QTableWidget, QTableWidgetItem, QStackedWidget, QGraphicsOpacityEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QTimer, QEasingCurve, QSequentialAnimationGroup, QParallelAnimationGroup
from PySide6.QtGui import QFont, QLinearGradient, QColor, QPalette
from qt_material import apply_stylesheet

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# ==================== MATERIAL DESIGN THEMING ====================
# qt-material provides modern Material Design themes for PySide6 applications
from qt_material import apply_stylesheet

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

# ==================== SM-2 SPACED REPETITION MODEL ====================
# Implements the SuperMemo-2 algorithm for optimized learning intervals

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
        1.5 ≤ ef < 1.8: "Hard" (difficult)
        1.8 ≤ ef < 2.3: "Medium" (moderate difficulty)
        2.3 ≤ ef < 2.7: "Memorized" (well known)
        ef ≥ 2.7: "Perfectly Memorized" (mastered)
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
            1: 1.7,   # Hard: 1.5 ≤ ef < 1.8
            2: 2.0,   # Medium: 1.8 ≤ ef < 2.3
            3: 2.5,   # Memorized: 2.3 ≤ ef < 2.7
            5: 2.8,   # Perfectly Memorized: ef ≥ 2.7
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

# ==================== DIALOG WINDOWS ====================
# Modal dialogs for deck selection, management, editing, and statistics

class DeckSelectionDialog(QDialog):
    """Dialog for browsing and loading flashcard decks from CSV files."""
    def __init__(self, deck: FlashCardDeck, parent=None):
        super().__init__(parent)
        self.deck = deck  # Reference to main deck object
        self.setWindowTitle("Select Deck")

        layout = QVBoxLayout(self)

        self.info_label = QLabel("Choose a CSV deck file")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        btn_layout = QHBoxLayout()
        self.browse_btn = QPushButton("Browse…")
        self.close_btn = QPushButton("Close")
        btn_layout.addWidget(self.browse_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self.browse_btn.clicked.connect(self.browse)
        self.close_btn.clicked.connect(self.accept)

    def browse(self):
        """Open file dialog to select and load a CSV deck file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV Deck",
            "",
            "CSV Files (*.csv)"
        )
        if filename:
            try:
                # Load deck from selected CSV file
                self.deck.load_from_csv(filename)
                # Persist any changes immediately
                self.deck.save_to_csv()
                # Confirm successful load to user
                QMessageBox.information(
                    self,
                    "Deck Loaded",
                    f"Loaded {len(self.deck.cards)} cards."
                )
            except Exception as e:
                # Report loading errors clearly
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load deck:\n{e}"
                )

class DeckManagerDialog(QDialog):
    """Dialog for managing multiple deck files in a folder.
    
    Features:
    - Browse and organize decks in folders
    - Load existing decks
    - Create new empty decks
    - Delete deck files
    """
    def __init__(self, deck: FlashCardDeck, parent=None):
        super().__init__(parent)
        self.deck = deck  # Reference to main deck object
        self.setWindowTitle("Deck Manager")
        self.resize(500, 400)

        self.folder = ""  # Currently selected folder path

        layout = QVBoxLayout(self)

        self.folder_label = QLabel("No folder selected")
        layout.addWidget(self.folder_label)

        folder_btn_row = QHBoxLayout()
        self.choose_folder_btn = QPushButton("Choose Folder")
        folder_btn_row.addWidget(self.choose_folder_btn)
        layout.addLayout(folder_btn_row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.load_btn = QPushButton("Load Selected")
        self.new_btn = QPushButton("New Deck")
        self.delete_btn = QPushButton("Delete Deck")
        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.new_btn)
        btn_row.addWidget(self.delete_btn)
        layout.addLayout(btn_row)

        self.choose_folder_btn.clicked.connect(self.choose_folder)
        self.load_btn.clicked.connect(self.load_selected)
        self.new_btn.clicked.connect(self.new_deck)
        self.delete_btn.clicked.connect(self.delete_deck)

    def choose_folder(self):
        """Open folder selection dialog to browse deck directory."""
        folder = QFileDialog.getExistingDirectory(self, "Select Deck Folder", "")
        if folder:
            self.folder = folder  # Store folder path
            self.folder_label.setText(f"Folder: {self.folder}")
            self.refresh_list()  # Update list with CSV files in folder

    def refresh_list(self):
        """Populate list widget with all CSV files in current folder."""
        self.list_widget.clear()
        if not self.folder:
            return
        # Scan folder for CSV files
        for name in os.listdir(self.folder):
            if name.lower().endswith(".csv"):
                self.list_widget.addItem(name)

    def load_selected(self):
        """Load the currently selected deck file from the list."""
        if not self.folder:
            return
        item = self.list_widget.currentItem()
        if not item:
            return
        # Construct full path and load deck
        filename = os.path.join(self.folder, item.text())
        try:
            self.deck.load_from_csv(filename)
            self.deck.save_to_csv()  # Validate and save
            QMessageBox.information(self, "Deck Loaded", f"Loaded {len(self.deck.cards)} cards.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load deck:\n{e}")

    def new_deck(self):
        """Create a new empty deck CSV file in the selected folder."""
        if not self.folder:
            QMessageBox.warning(self, "No Folder", "Choose a folder first.")
            return
        # Prompt user for deck name
        name, ok = QInputDialog.getText(self, "New Deck", "Deck name (without .csv):")
        if not ok or not name.strip():
            return
        # Construct filename with .csv extension
        filename = os.path.join(self.folder, name.strip() + ".csv")
        # Check if file already exists
        if os.path.exists(filename):
            QMessageBox.warning(self, "Exists", "A deck with that name already exists.")
            return
        # Create empty CSV file
        with open(filename, "w", newline='', encoding='utf-8') as f:
            pass
        self.refresh_list()  # Update UI to show new deck

    def delete_deck(self):
        """Delete the selected deck file after confirmation."""
        if not self.folder:
            return
        item = self.list_widget.currentItem()
        if not item:
            return
        filename = os.path.join(self.folder, item.text())
        # Confirm deletion with user
        reply = QMessageBox.question(
            self,
            "Delete Deck",
            f"Delete deck '{item.text()}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                # Remove the file from disk
                os.remove(filename)
                self.refresh_list()  # Update UI
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete deck:\n{e}")


# ==================== STUDY INTERFACE ====================
# Main UI for flashcard study sessions with animations and progress tracking

class StudyPage(QWidget):
    """
    Main study interface for flashcard learning sessions.
    
    Features:
    - Interactive card flipping with smooth animations
    - Real-time progress visualization (donut chart)
    - Deck management and switching
    - 6-level rating system for immediate status changes
    - Continuous study mode until all cards are mastered
    """
    
    def __init__(self, deck: FlashCardDeck, main_window):
        """Initialize study page with deck and UI components."""
        super().__init__()
        try:
            self.deck = deck  # Reference to current flashcard deck
            self.main_window = main_window
            self.current_card = None  # Currently displayed card
            self.showing_definition = False  # Card flip state (word vs definition)
            self.flip_animation = None  # Flip animation object
            self.flip_animation_group = None  # Animation group for multi-phase flip
            self.flip_timer = None  # Timer for mid-flip text update
            self.deck_folder = ""  # Current deck directory
            self.next_card_to_load = None  # Card queued for display
            self.card_transition_out = None  # Fade-out animation
            self.card_transition_in = None  # Fade-in animation

            main_layout = QHBoxLayout(self)

            # ===== LEFT SIDE: DECK SWITCHER AND PIE CHART =====
            left_layout = QVBoxLayout()
            
            # Deck switcher label
            deck_label = QLabel("Current Deck:")
            deck_label.setStyleSheet("font-size: 11px; font-weight: bold;")
            left_layout.addWidget(deck_label)
            
            # Displays currently loaded deck name
            self.deck_name_label = QLabel("No deck")
            self.deck_name_label.setAlignment(Qt.AlignCenter)
            self.deck_name_label.setStyleSheet("font-size: 10px; margin-bottom: 5px;")
            left_layout.addWidget(self.deck_name_label)
            
            # Deck list
            self.deck_list = QListWidget()
            self.deck_list.itemClicked.connect(self.load_selected_deck)
            left_layout.addWidget(self.deck_list, 1)
            
            # Folder button
            self.folder_btn = QPushButton("📁 Change Folder")
            self.folder_btn.setStyleSheet("""
                QPushButton {
                    font-size: 10px;
                    padding: 5px;
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
            self.folder_btn.clicked.connect(self.choose_folder)
            left_layout.addWidget(self.folder_btn)
            
            left_layout.addSpacing(10)
            
            # Pie chart section
            fig = Figure(figsize=(4, 4), dpi=100)
            self.canvas = FigureCanvas(fig)
            self.ax = fig.add_subplot(111)
            left_layout.addWidget(self.canvas)

            # Progress label
            self.progress_label = QLabel("")
            self.progress_label.setAlignment(Qt.AlignCenter)
            self.progress_label.setStyleSheet("font-size: 11px;")
            left_layout.addWidget(self.progress_label)
            
            main_layout.addLayout(left_layout, 1)

            # ===== RIGHT SIDE: CARD AND CONTROLS =====
            right_layout = QVBoxLayout()

            # Back button
            self.back_btn = QPushButton("← Back to Menu")
            self.back_btn.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    padding: 8px 16px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #6B7280, stop:1 #4B5563);
                    color: white;
                    font-weight: 600;
                    border: none;
                    border-radius: 6px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4B5563, stop:1 #374151);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }
                QPushButton:pressed {
                    padding: 9px 16px 7px 16px;
                }
            """)
            self.back_btn.clicked.connect(self.main_window.go_back_to_main)
            right_layout.addWidget(self.back_btn)

            # Card display with modern gradient design
            self.card_label = QLabel("No deck loaded")
            self.card_label.setAlignment(Qt.AlignCenter)
            self.card_label.setWordWrap(True)
            self.card_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.card_label.setStyleSheet("""
                QLabel {
                    font-size: 28px;
                    font-weight: 600;
                    padding: 40px;
                    border: none;
                    border-radius: 16px;
                    min-height: 200px;
                    min-width: 300px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4F46E5, stop:1 #06B6D4);
                    color: white;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                }
            """)
            right_layout.addWidget(self.card_label, 1)

            # Flip button with enhanced styling
            self.flip_btn = QPushButton("Flip Card")
            self.flip_btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    padding: 12px 24px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4F46E5, stop:1 #06B6D4);
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4338CA, stop:1 #0891B2);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #3730A3, stop:1 #0E7490);
                }
            """)
            right_layout.addWidget(self.flip_btn)

            # Spacer
            right_layout.addSpacing(20)

            # Rating label (hidden initially)
            self.rating_label = QLabel("Rate this card:")
            self.rating_label.setAlignment(Qt.AlignCenter)
            self.rating_label.setStyleSheet("font-size: 12px; font-weight: bold;")
            self.rating_label.setVisible(False)
            right_layout.addWidget(self.rating_label)

            # Rating buttons (hidden initially)
            self.btn_row_widget = QWidget()
            btn_row = QHBoxLayout(self.btn_row_widget)
            self.perfectly_btn = QPushButton("Perfectly Memorized")
            self.memorized_btn = QPushButton("Memorized")
            self.medium_btn = QPushButton("Medium")
            self.hard_btn = QPushButton("Hard")
            self.unknown_btn = QPushButton("Unknown")
            
            # Enhanced button styling with modern colors for 6-level system
            self.unknown_btn.setStyleSheet("""
                QPushButton {
                    background-color: #C0392B;
                    font-size: 11px;
                    padding: 8px 12px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #A93226;
                }
                QPushButton:pressed {
                    background-color: #922B21;
                }
            """)
            self.hard_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EF4444;
                    font-size: 11px;
                    padding: 8px 12px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                }
                QPushButton:pressed {
                    background-color: #B91C1C;
                }
            """)
            self.medium_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F59E0B;
                    font-size: 11px;
                    padding: 8px 12px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #D97706;
                }
                QPushButton:pressed {
                    background-color: #B45309;
                }
            """)
            self.memorized_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7ED321;
                    font-size: 11px;
                    padding: 8px 12px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #5CA917;
                }
                QPushButton:pressed {
                    background-color: #4A8B0D;
                }
            """)
            self.perfectly_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    font-size: 11px;
                    padding: 8px 12px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #1E8449;
                }
                QPushButton:pressed {
                    background-color: #186A3B;
                }
            """)
            
            btn_row.addWidget(self.unknown_btn)
            btn_row.addWidget(self.hard_btn)
            btn_row.addWidget(self.medium_btn)
            btn_row.addWidget(self.memorized_btn)
            btn_row.addWidget(self.perfectly_btn)
            self.btn_row_widget.setVisible(False)
            right_layout.addWidget(self.btn_row_widget)

            self.flip_btn.clicked.connect(self.flip_card)
            self.unknown_btn.clicked.connect(lambda: self.rate_card(0))
            self.hard_btn.clicked.connect(lambda: self.rate_card(1))
            self.medium_btn.clicked.connect(lambda: self.rate_card(2))
            self.memorized_btn.clicked.connect(lambda: self.rate_card(3))
            self.perfectly_btn.clicked.connect(lambda: self.rate_card(5))

            main_layout.addLayout(right_layout, 1)

            self.update_progress()
            self.next_card()
        except Exception as e:
            print(f"Error initializing StudyPage: {str(e)}")
            import traceback
            traceback.print_exc()
            # Show error message
            QMessageBox.critical(None, "Error", f"Failed to initialize study page:\n{str(e)}")


    def reset(self):
        """Reset the study page when reopened"""
        self.current_card = None
        self.showing_definition = False
        self.refresh_deck_list()
        self.update_progress()
        self.next_card()

    def choose_folder(self):
        """Open folder dialog to select deck folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Deck Folder", "")
        if folder:
            self.deck_folder = folder
            self.refresh_deck_list()

    def refresh_deck_list(self):
        """Refresh the list of available decks"""
        self.deck_list.clear()
        if not self.deck_folder:
            return
        try:
            for name in os.listdir(self.deck_folder):
                if name.lower().endswith(".csv"):
                    self.deck_list.addItem(name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read folder:\n{e}")

    def load_selected_deck(self):
        """Load the selected deck from the list"""
        item = self.deck_list.currentItem()
        if not item or not self.deck_folder:
            return
        
        filename = os.path.join(self.deck_folder, item.text())
        try:
            self.deck.load_from_csv(filename)
            self.deck_name_label.setText(item.text().replace(".csv", ""))
            self.current_card = None
            self.showing_definition = False
            self.update_progress()
            self.next_card()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load deck:\n{e}")

    def update_progress(self):
        """
        Update progress statistics and donut chart visualization.
        
        Displays:
        - Total cards, due for review, and learned counts
        - 6-category donut chart with card distribution
        - Overall mastery percentage weighted by status
        
        Mastery calculation weights:
            Perfectly Memorized: 3.0x
            Memorized: 2.5x
            Medium: 2.0x
            Hard: 1.0x
            Unknown: 0x
            New: 0x
        """
        total, due, learned = self.deck.stats()
        # Update statistics label at top of chart
        self.progress_label.setText(
            f"Total: {total} | Due: {due} | Learned (reps≥3): {learned}"
        )
        
        # Clear previous chart and prepare new visualization
        self.ax.clear()
        new, unknown, hard, medium, memorized, perfectly = self.deck.rating_counts()
        values = [new, unknown, hard, medium, memorized, perfectly]
        # Color scheme: Blue→Dark Red→Red→Amber→Green→Dark Green
        colors = ["#4A90E2", "#C0392B", "#E74C3C", "#F5A623", "#7ED321", "#27AE60"]
        
        # Create legend labels with card counts
        labels = [f"New ({new})", f"Unknown ({unknown})", f"Hard ({hard})", 
                  f"Medium ({medium})", f"Memorized ({memorized})", f"Perfectly ({perfectly})"]
        
        # Calculate weighted mastery percentage
        total_cards = sum(values)
        if total_cards > 0:
            # Weight formula: higher statuses contribute more to overall mastery
            mastery = (perfectly * 3 + memorized * 2.5 + medium * 2 + hard * 1) / (total_cards * 3) * 100
        else:
            mastery = 0
        
        # Draw donut chart only if cards exist
        if sum(values) > 0:
            # Create donut chart with colored segments and white borders
            wedges, texts = self.ax.pie(values, colors=colors, startangle=90,
                                        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2))
            
            # Display mastery percentage in center of donut
            self.ax.text(0, 0, f"{mastery:.1f}%\nMastery", ha='center', va='center', 
                        fontsize=16, fontweight='bold', color='#111827')
            
            # Add legend outside the donut chart
            self.ax.legend(labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=True)
        else:
            # Show placeholder when no cards
            self.ax.text(0.5, 0.5, "No Cards", ha='center', va='center', transform=self.ax.transAxes)
        
        self.ax.set_title("Progress by Rating", fontsize=12, fontweight='bold')
        self.canvas.draw()

    def _get_weighted_random_card(self):
        """Select a random card weighted by difficulty and due status."""
        if not self.deck.cards:
            return None

        # Prefer due cards first, but fall back to the whole deck if none are due.
        candidates = self.deck.get_due_cards() or list(self.deck.cards)

        # Assign higher weights to more difficult cards.
        def card_weight(card):
            rating = card.rating()
            return {
                "New": 5.0,
                "Unknown": 4.0,
                "Hard": 3.0,
                "Medium": 2.0,
                "Memorized": 1.0,
                "Perfectly Memorized": 0.5,
            }.get(rating, 1.0)

        weights = [card_weight(card) for card in candidates]
        total_weight = sum(weights)
        if total_weight <= 0:
            return random.choice(candidates)

        return random.choices(candidates, weights=weights, k=1)[0]

    def next_card(self):
        """
        Select next card for study and animate transition.
        
        Logic:
        1. Save current deck state to CSV
        2. Check if all cards are mastered → show completion screen
        3. Get random card from entire deck (continuous study mode)
        4. Animate current card out, load new card in
        """
        self.deck.save_to_csv()
        
        # Check if all cards have reached Perfectly Memorized status
        if self.deck.all_cards_mastered():
            card = None
        else:
            # Get a random card from the deck (allows cycling through all cards multiple times)
            # Get a random card weighted by difficulty (lower ratings = higher probability)
            card = self._get_weighted_random_card()
        
        # Animate current card out if one exists
        if self.current_card:
            self._animate_card_out()
        
        # Store the next card to load after animation
        self.next_card_to_load = card
        
        # If all cards are mastered, show completion screen
        if not card:
            self.show_completion_screen()
        else:
            # Schedule loading the new card after animation completes
            QTimer.singleShot(400, self._load_next_card)

    def show_completion_screen(self):
        """Display the completion screen when all cards are mastered"""
        self.current_card = None
        new, unknown, hard, medium, memorized, perfectly = self.deck.rating_counts()
        total = new + unknown + hard + medium + memorized + perfectly
        
        # Display mastery completion message
        self.card_label.setText(f"🎉 All {total} cards mastered! 🎉\n\nAll cards are now Perfectly Memorized!")
        self.card_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 600;
                padding: 40px;
                border: none;
                border-radius: 16px;
                min-height: 200px;
                min-width: 300px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7ED321, stop:1 #5DB312);
                color: white;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            }
        """)
        self.set_buttons_enabled(False)
        self.rating_label.setVisible(False)
        self.btn_row_widget.setVisible(False)
        self.update_progress()

    def _load_next_card(self):
        """Load the next card with a slide-in animation"""
        card = self.next_card_to_load
        if not card:
            return
        
        self.current_card = card
        self.showing_definition = False
        self.card_label.setText(self.current_card.word)
        self.card_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 600;
                padding: 40px;
                border: none;
                border-radius: 16px;
                min-height: 250px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4F46E5, stop:1 #06B6D4);
                color: white;
            }
        """)
        self.rating_label.setVisible(False)
        self.btn_row_widget.setVisible(False)
        self.set_buttons_enabled(True)
        self.update_progress()
        
        # Trigger slide-in animation
        self._animate_card_in()
    
    def _animate_card_out(self):
        """Animate current card fading out with smooth transition"""
        # Create opacity effect for fade out
        if not hasattr(self.card_label, 'opacity_effect'):
            self.card_label.opacity_effect = QGraphicsOpacityEffect()
            self.card_label.setGraphicsEffect(self.card_label.opacity_effect)
        
        # Opacity animation (fade out only - no geometry movement)
        opacity_anim = QPropertyAnimation(self.card_label.opacity_effect, b"opacity")
        opacity_anim.setDuration(300)
        opacity_anim.setEasingCurve(QEasingCurve.InCubic)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        
        self.card_transition_out = opacity_anim
        opacity_anim.start()

    def _animate_card_in(self):
        """Animate new card fading in with smooth transition"""
        # Create opacity effect for fade in
        if not hasattr(self.card_label, 'opacity_effect'):
            self.card_label.opacity_effect = QGraphicsOpacityEffect()
            self.card_label.setGraphicsEffect(self.card_label.opacity_effect)
        
        # Start with transparent
        self.card_label.opacity_effect.setOpacity(0.0)
        
        # Opacity animation (fade in only - no geometry movement)
        opacity_anim = QPropertyAnimation(self.card_label.opacity_effect, b"opacity")
        opacity_anim.setDuration(300)
        opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        
        self.card_transition_in = opacity_anim
        opacity_anim.start()

    def _animate_card_transition(self):
        """Animate card transition - kept for compatibility"""
        pass

    def set_buttons_enabled(self, enabled: bool):
        for btn in (self.unknown_btn, self.hard_btn, self.medium_btn, self.memorized_btn, self.perfectly_btn, self.flip_btn):
            btn.setEnabled(enabled)

    def get_card_color_gradient(self, card):
        """Get gradient colors based on card status"""
        rating = card.rating()
        
        # Color mapping: (start_color, end_color) for 6-level system
        color_map = {
            "New": ("#4A90E2", "#2E7CC4"),                  # Blue gradient
            "Unknown": ("#C0392B", "#8B2E1F"),              # Dark red gradient
            "Hard": ("#E74C3C", "#C23321"),                 # Red gradient
            "Medium": ("#F5A623", "#D68910"),               # Amber gradient
            "Memorized": ("#7ED321", "#5CA917"),            # Green gradient
            "Perfectly Memorized": ("#27AE60", "#1E8449"),  # Dark green gradient
        }
        
        start, end = color_map.get(rating, ("#4A90E2", "#2E7CC4"))
        return f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {start}, stop:1 {end})"

    def _load_next_card(self):
        """Load the next card with a slide-in animation"""
        card = self.next_card_to_load
        if not card:
            return
        
        self.current_card = card
        self.showing_definition = False
        self.card_label.setText(self.current_card.word)
        
        # Get color based on card status
        card_gradient = self.get_card_color_gradient(card)
        
        self.card_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: 600;
                padding: 40px;
                border: none;
                border-radius: 16px;
                min-height: 200px;
                min-width: 300px;
                background: {card_gradient};
                color: white;
            }}
        """)
        self.rating_label.setVisible(False)
        self.btn_row_widget.setVisible(False)
        self.set_buttons_enabled(True)
        self.update_progress()
        
        # Trigger slide-in animation
        self._animate_card_in()

    def flip_card(self):
        if not self.current_card:
            return
        
        # Disable button during animation
        self.flip_btn.setEnabled(False)
        
        # Create a sequential animation group for a realistic 3D flip effect
        self.flip_animation_group = QSequentialAnimationGroup()
        
        current_geo = self.card_label.geometry()
        center_x = current_geo.x() + current_geo.width() // 2
        center_y = current_geo.y() + current_geo.height() // 2
        
        # ===== PHASE 1: Flip Away (Shrink horizontally - 350ms) =====
        # Horizontal squeeze to simulate card rotating away
        flip_away_anim = QPropertyAnimation(self.card_label, b"geometry")
        flip_away_anim.setDuration(350)
        flip_away_anim.setEasingCurve(QEasingCurve.InCubic)
        
        # Shrink only horizontally (card width becomes 0), keep vertical center
        squeezed_geo = QRect(center_x, current_geo.y(), 0, current_geo.height())
        flip_away_anim.setStartValue(current_geo)
        flip_away_anim.setEndValue(squeezed_geo)
        
        # ===== PHASE 2: Change text at midpoint =====
        self.flip_timer = QTimer()
        self.flip_timer.setSingleShot(True)
        self.flip_timer.timeout.connect(self._update_card_text)
        
        # ===== PHASE 3: Flip Back (Expand horizontally - 350ms) =====
        # Card comes back with a slight rotation effect via expansion
        flip_back_anim = QPropertyAnimation(self.card_label, b"geometry")
        flip_back_anim.setDuration(350)
        flip_back_anim.setEasingCurve(QEasingCurve.OutCubic)
        flip_back_anim.setStartValue(squeezed_geo)
        
        # Expand back to original with slight overshoot for dynamic effect
        expanded_geo = QRect(current_geo.x() - 5, current_geo.y() - 2, 
                           current_geo.width() + 10, current_geo.height() + 4)
        flip_back_anim.setEndValue(expanded_geo)
        
        # ===== PHASE 4: Settle back to original position (100ms) =====
        settle_anim = QPropertyAnimation(self.card_label, b"geometry")
        settle_anim.setDuration(100)
        settle_anim.setEasingCurve(QEasingCurve.OutQuad)
        settle_anim.setStartValue(expanded_geo)
        settle_anim.setEndValue(current_geo)
        
        # Add all animations to group with proper timing
        self.flip_animation_group.addAnimation(flip_away_anim)
        self.flip_animation_group.addPause(50)  # Brief pause at flip point
        self.flip_animation_group.addAnimation(flip_back_anim)
        self.flip_animation_group.addAnimation(settle_anim)
        
        # Schedule text update at the midpoint (flip away duration)
        self.flip_timer.start(350)
        
        # Re-enable button and restore normal glow when animation finishes
        def restore_and_enable():
            self.flip_btn.setEnabled(True)
            # Restore the card color based on status
            card_gradient = self.get_card_color_gradient(self.current_card)
            self.card_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 28px;
                    font-weight: 600;
                    padding: 40px;
                    border: none;
                    border-radius: 16px;
                    min-height: 200px;
                    min-width: 300px;
                    background: {card_gradient};
                    color: white;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                }}
            """)
        
        self.flip_animation_group.finished.connect(restore_and_enable)
        
        self.flip_animation_group.start()
    
    def _update_card_text(self):
        """Update card text during flip animation"""
        # Get the card's color gradient based on its status
        card_gradient = self.get_card_color_gradient(self.current_card)
        
        # Add a subtle glow effect during text change for realism
        self.card_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: 600;
                padding: 40px;
                border: none;
                border-radius: 16px;
                min-height: 200px;
                min-width: 300px;
                background: {card_gradient};
                color: white;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
                           0 0 30px rgba(0, 0, 0, 0.3);
            }}
        """)
        
        if self.showing_definition:
            self.card_label.setText(self.current_card.word)
            self.rating_label.setVisible(False)
            self.btn_row_widget.setVisible(False)
        else:
            self.card_label.setText(self.current_card.definition)
            self.rating_label.setVisible(True)
            self.btn_row_widget.setVisible(True)
        self.showing_definition = not self.showing_definition

    def rate_card(self, quality):
        """
        Rate the current card and advance to next card.
        
        Process:
        1. Apply SM-2 algorithm update with quality value
        2. Update donut chart to reflect status change
        3. Load next card with animation
        
        Args:
            quality (int): Rating quality (0=Unknown, 1=Hard, 2=Medium, 3=Memorized, 5=Perfectly Memorized)
        """
        if not self.current_card:
            return
        # Update card's ease factor and schedule based on rating
        self.current_card.update_sm2(quality)
        # Immediately update chart to show status change
        self.update_progress()
        # Move to next card in study session
        self.next_card()

class EditorDialog(QDialog):
    """Dialog for adding, editing, and deleting cards in the current deck."""
    def __init__(self, deck: FlashCardDeck, parent=None):
        super().__init__(parent)
        self.deck = deck  # Reference to current deck
        self.setWindowTitle("Deck Editor")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.save_btn = QPushButton("Save")
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.delete_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        self.add_btn.clicked.connect(self.add_card)
        self.edit_btn.clicked.connect(self.edit_card)
        self.delete_btn.clicked.connect(self.delete_card)
        self.save_btn.clicked.connect(self.save)

        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        for i, c in enumerate(self.deck.cards):
            self.list_widget.addItem(
                f"{i+1}. {c.word} -> {c.definition} (reps={c.reps}, due={c.next_due})"
            )

    def add_card(self):
        """Add a new card to the deck via input dialogs."""
        # Get German word from user
        word, ok = QInputDialog.getText(self, "New Card", "Word:")
        if not ok or not word.strip():
            return
        # Get English definition from user
        definition, ok = QInputDialog.getText(self, "New Card", "Definition:")
        if not ok or not definition.strip():
            return
        # Add card to deck and refresh display
        self.deck.add_card(word.strip(), definition.strip())
        self.refresh_list()

    def edit_card(self):
        """Edit the currently selected card's word and definition."""
        row = self.list_widget.currentRow()
        if row < 0:
            return
        card = self.deck.cards[row]
        # Edit word with current value pre-filled
        word, ok = QInputDialog.getText(self, "Edit Card", "Word:", text=card.word)
        if not ok or not word.strip():
            return
        # Edit definition with current value pre-filled
        definition, ok = QInputDialog.getText(
            self, "Edit Card", "Definition:", text=card.definition
        )
        if not ok or not definition.strip():
            return
        # Update card and refresh display
        card.word = word.strip()
        card.definition = definition.strip()
        self.refresh_list()

    def delete_card(self):
        """Delete the selected card after confirmation."""
        row = self.list_widget.currentRow()
        if row < 0:
            return
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete",
            "Delete selected card?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.deck.remove_card(row)  # Remove from deck
            self.refresh_list()  # Update display

    def save(self):
        """Save all deck changes to CSV file."""
        self.deck.save_to_csv()
        QMessageBox.information(self, "Saved", "Deck saved.")

class CardStatusPage(QWidget):
    """Page displaying all cards with their current status ratings.
    
    Features:
    - Table view of all cards and ratings
    - Bulk reset functionality
    - Individual card reset option
    """
    def __init__(self, deck: FlashCardDeck, main_window):
        super().__init__()
        self.deck = deck  # Reference to current deck
        self.main_window = main_window  # Reference to main window for navigation

        layout = QVBoxLayout(self)

        # Back button
        self.back_btn = QPushButton("← Back to Menu")
        self.back_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 8px;
                background-color: #95A5A6;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                max-width: 150px;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        self.back_btn.clicked.connect(self.main_window.go_back_to_main)
        layout.addWidget(self.back_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Word", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.reset_selected_btn = QPushButton("Reset Selected")
        self.reset_all_btn = QPushButton("Reset All")
        btn_row.addWidget(self.reset_selected_btn)
        btn_row.addWidget(self.reset_all_btn)
        layout.addLayout(btn_row)

        self.reset_selected_btn.clicked.connect(self.reset_selected)
        self.reset_all_btn.clicked.connect(self.reset_all)

        self.refresh()

    def refresh(self):
        self.table.setRowCount(len(self.deck.cards))
        for i, c in enumerate(self.deck.cards):
            self.table.setItem(i, 0, QTableWidgetItem(c.word))
            self.table.setItem(i, 1, QTableWidgetItem(c.rating()))

    def reset_selected(self):
        """Reset the selected card to New status."""
        row = self.table.currentRow()
        if row < 0:
            return
        # Reset card to initial state (0 reps, default ef)
        self.deck.cards[row].reset()
        # Persist changes to file
        self.deck.save_to_csv()
        self.refresh()  # Update table display

    def reset_all(self):
        """Reset all cards in the deck to New status."""
        for c in self.deck.cards:
            # Reset each card to initial state
            c.reset()
        # Persist changes to file
        self.deck.save_to_csv()
        self.refresh()  # Update table display


class CardStatusDialog(QDialog):
    """Modal dialog version of card status display for quick access."""
    def __init__(self, deck: FlashCardDeck, parent=None):
        super().__init__(parent)
        self.deck = deck  # Reference to current deck
        self.setWindowTitle("Card Status")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Word", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.reset_selected_btn = QPushButton("Reset Selected")
        self.reset_all_btn = QPushButton("Reset All")
        self.close_btn = QPushButton("Close")
        btn_row.addWidget(self.reset_selected_btn)
        btn_row.addWidget(self.reset_all_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        self.reset_selected_btn.clicked.connect(self.reset_selected)
        self.reset_all_btn.clicked.connect(self.reset_all)
        self.close_btn.clicked.connect(self.accept)

        self.refresh()

    def refresh(self):
        self.table.setRowCount(len(self.deck.cards))
        for i, c in enumerate(self.deck.cards):
            self.table.setItem(i, 0, QTableWidgetItem(c.word))
            self.table.setItem(i, 1, QTableWidgetItem(c.rating()))

    def reset_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.deck.cards[row].reset()
        self.deck.save_to_csv()
        self.refresh()

    def reset_all(self):
        for c in self.deck.cards:
            c.reset()
        self.deck.save_to_csv()
        self.refresh()

class ProgressChartPage(QWidget):
    """Page displaying detailed progress visualization using matplotlib.
    
    Shows:
    - Donut chart with 6-level card distribution
    - Overall mastery percentage
    - Real-time statistics updates
    """
    def __init__(self, deck: FlashCardDeck, main_window):
        super().__init__()
        self.deck = deck  # Reference to current deck
        self.main_window = main_window  # Reference to main window for navigation

        layout = QVBoxLayout(self)

        # Back button
        self.back_btn = QPushButton("← Back to Menu")
        self.back_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 8px;
                background-color: #95A5A6;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                max-width: 150px;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        self.back_btn.clicked.connect(self.main_window.go_back_to_main)
        layout.addWidget(self.back_btn)

        fig = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(fig)
        layout.addWidget(self.canvas)

        self.ax = fig.add_subplot(111)
        self.refresh()

    def refresh(self):
        """Redraw progress chart with current deck statistics."""
        self.ax.clear()  # Clear previous chart
        # Get card counts by rating
        new, hard, medium, easy = self.deck.rating_counts()
        values = [new, hard, medium, easy]
        # Color scheme for chart segments
        colors = ["#4A90E2", "#E74C3C", "#F5A623", "#7ED321"]
        
        # Create legend labels with card counts for readability
        labels = [f"New ({new})", f"Hard ({hard})", f"Medium ({medium})", f"Easy ({easy})"]
        
        # Calculate weighted mastery percentage
        # Weighting: easy cards worth 3x, medium 2x, hard 1x, new 0x
        total_cards = sum(values)
        if total_cards > 0:
            mastery = (easy * 3 + medium * 2 + hard * 1) / (total_cards * 3) * 100
        else:
            mastery = 0
        
        # Render donut chart only if cards exist
        if sum(values) > 0:
            # Create donut chart with white borders for clean separation
            wedges, texts = self.ax.pie(values, colors=colors, startangle=90,
                                        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2))
            
            # Display mastery percentage in center of donut for immediate visual feedback
            self.ax.text(0, 0, f"{mastery:.1f}%\nMastery", ha='center', va='center', 
                        fontsize=16, fontweight='bold', color='#111827')
            
            # Add legend outside donut showing card counts per category
            self.ax.legend(labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=True)
        else:
            # Show placeholder when no cards loaded
            self.ax.text(0.5, 0.5, "No Cards", ha='center', va='center', transform=self.ax.transAxes)
        
        # Add title and redraw
        self.ax.set_title("Progress by Rating", fontsize=12, fontweight='bold')
        self.canvas.draw()


class ProgressChartDialog(QDialog):
    def __init__(self, deck: FlashCardDeck, parent=None):
        super().__init__(parent)
        self.deck = deck
        self.setWindowTitle("Progress Chart")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        fig = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(fig)
        layout.addWidget(self.canvas)

        ax = fig.add_subplot(111)
        new, learning, learned = self.deck.status_counts()
        labels = ["New", "Learning", "Learned"]
        values = [new, learning, learned]
        ax.bar(labels, values, color=["#4A90E2", "#F5A623", "#7ED321"])
        ax.set_ylabel("Number of cards")
        ax.set_title("Card Progress")
        fig.tight_layout()

        self.canvas.draw()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

# ==================== MAIN APPLICATION WINDOW ====================
# Entry point and central hub for all application functionality

class MainWindow(QMainWindow):
    """Main application window with menu navigation and page management.
    
    Manages:
    - Page switching between study, editing, stats views
    - Deck loading and persistence
    - Dark mode theming
    - Overall application state
    """
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app  # Reference to QApplication
        self.deck = FlashCardDeck()  # Main deck object for current session
        self.dark_mode = False  # Dark mode toggle state

        self.setWindowTitle("German Flashcard App")
        self.resize(1000, 700)

        # Create stacked widget for multi-page navigation (main menu, study, stats, etc.)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize main page and lazy-load other pages on demand
        self.main_page = self.create_main_page()
        self.study_page = None          # Created when user enters study mode
        self.deck_manager_page = None   # Deck management dialog
        self.editor_page = None         # Card editing dialog
        self.status_page = None         # Card status view
        self.progress_page = None       # Progress chart view

        # Add main page to stacked widget
        self.stacked_widget.addWidget(self.main_page)

    def create_main_page(self):
        """Create the main menu page with navigation buttons.
        
        Displays:
        - Current deck information
        - Navigation buttons to study, edit, manage, and view stats
        - Theme toggle and quit options
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        # Center all widgets and add spacing for modern look
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("German Flashcard App")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 10px;
                color: #111827;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4F46E5, stop:1 #06B6D4);
                -qt-background-role: window;
                padding: 20px;
                border-radius: 12px;
                color: white;
            }
        """)
        layout.addWidget(title)

        deck_info = QLabel("No deck loaded")
        deck_info.setAlignment(Qt.AlignCenter)
        deck_info.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #6B7280;
                padding: 10px;
            }
        """)
        self.deck_info_label = deck_info
        layout.addWidget(deck_info)

        layout.addSpacing(20)

        self.select_btn = self.create_button("Select Deck", self.select_deck)
        self.deck_manager_btn = self.create_button("Deck Manager", self.open_deck_manager)
        self.study_btn = self.create_button("Study", self.open_study)
        self.edit_btn = self.create_button("Edit Deck", self.open_editor)
        self.status_btn = self.create_button("Show Status", self.show_status)
        self.progress_btn = self.create_button("Progress Chart", self.show_progress_chart)
        self.dark_btn = self.create_button("Toggle Dark Mode", self.toggle_dark_mode)
        self.quit_btn = self.create_button("Quit", self.close)

        for btn in (self.select_btn, self.deck_manager_btn, self.study_btn, self.edit_btn,
                    self.status_btn, self.progress_btn, self.dark_btn, self.quit_btn):
            layout.addWidget(btn)

        layout.addStretch()
        return page

    def create_button(self, text, callback):
        """Helper method to create consistently-styled buttons with gradients.
        
        Args:
            text (str): Button label text
            callback: Function to call on button click
            
        Returns:
            QPushButton: Styled button with gradient background and hover effects
        """
        btn = QPushButton(text)
        btn.setMinimumHeight(45)
        btn.setMinimumWidth(200)
        
        # Select gradient colors based on button purpose for visual categorization
        if "Dark" in text:
            # Theme toggle button → Amber
            color_start = "#F59E0B"
            color_end = "#FBBF24"
        elif "Quit" in text:
            # Quit button → Red (indicates destructive action)
            color_start = "#EF4444"
            color_end = "#F87171"
        elif "Study" in text:
            # Study button → Green (primary action)
            color_start = "#10B981"
            color_end = "#34D399"
        else:
            # Other buttons → Indigo to Cyan gradient (default)
            color_start = "#4F46E5"
            color_end = "#06B6D4"
        
        btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 14px;
                font-weight: 600;
                padding: 12px 20px;
                border-radius: 10px;
                border: none;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color_start}, stop:1 {color_end});
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }}
            
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color_start}, stop:1 {color_end});
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
            }}
            
            QPushButton:pressed {{
                padding: 13px 20px 11px 20px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def go_back_to_main(self):
        """Return to main menu page and refresh deck information."""
        # Switch to main page
        self.stacked_widget.setCurrentWidget(self.main_page)
        # Update deck status display
        self.update_deck_info()

    def update_deck_info(self):
        """Update deck information display on main menu.
        
        Shows deck filename and total card count.
        """
        if self.deck.cards:
            # Extract filename from full path and show card count
            self.deck_info_label.setText(f"Deck: {self.deck.filename.split('/')[-1]} ({len(self.deck.cards)} cards)")
        else:
            # Show placeholder when no deck loaded
            self.deck_info_label.setText("No deck loaded")

    def select_deck(self):
        """Open deck selection dialog."""
        # Show dialog for browsing and loading deck files
        dlg = DeckSelectionDialog(self.deck, self)
        dlg.exec()
        # Update main menu to show newly loaded deck
        self.update_deck_info()

    def open_deck_manager(self):
        """Open deck manager dialog for file organization."""
        # Show dialog for managing multiple deck files
        dlg = DeckManagerDialog(self.deck, self)
        dlg.exec()
        # Update main menu after potential deck changes
        self.update_deck_info()

    def open_study(self):
        """Switch to study page or create it if first time.
        
        Uses lazy loading to only create study page when needed.
        Resets page state on each entry.
        """
        # Require a loaded deck first
        if not self.deck.cards:
            QMessageBox.warning(self, "No Deck", "Load a deck first.")
            return
        
        try:
            if self.study_page is None:
                # First time: create and add study page to stacked widget
                self.study_page = StudyPage(self.deck, self)
                self.stacked_widget.addWidget(self.study_page)
            else:
                # Update deck reference and reset page state
                self.study_page.deck = self.deck
                self.study_page.reset()  # Reload cards and animations
            # Switch to study page
            self.stacked_widget.setCurrentWidget(self.study_page)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open study mode:\n{str(e)}")

    def open_editor(self):
        """Open card editor dialog for adding, editing, or deleting cards."""
        # Require a loaded deck first
        if not self.deck.cards:
            QMessageBox.warning(self, "No Deck", "Load a deck first.")
            return
        # Show modal editor dialog
        dlg = EditorDialog(self.deck, self)
        dlg.exec()

    def show_status(self):
        """Show card status page with detailed card information."""
        # Require a loaded deck first
        if not self.deck.cards:
            QMessageBox.warning(self, "No Deck", "Load a deck first.")
            return
        # Reload deck from file to get latest data
        if self.deck.filename:
            self.deck.load_from_csv(self.deck.filename)
        # Create status page on first use (lazy loading)
        if self.status_page is None:
            self.status_page = CardStatusPage(self.deck, self)
            self.stacked_widget.addWidget(self.status_page)
        else:
            # Update deck reference and refresh table
            self.status_page.deck = self.deck
            self.status_page.refresh()
        # Switch to status page
        self.stacked_widget.setCurrentWidget(self.status_page)

    def show_progress_chart(self):
        """Show detailed progress chart page with statistics visualization."""
        # Require a loaded deck first
        if not self.deck.cards:
            QMessageBox.warning(self, "No Deck", "Load a deck first.")
            return
        # Reload deck from file to get latest data
        if self.deck.filename:
            self.deck.load_from_csv(self.deck.filename)
        # Create progress page on first use (lazy loading)
        if self.progress_page is None:
            self.progress_page = ProgressChartPage(self.deck, self)
            self.stacked_widget.addWidget(self.progress_page)
        else:
            # Update deck reference and refresh chart
            self.progress_page.deck = self.deck
            self.progress_page.refresh()
        # Switch to progress page
        self.stacked_widget.setCurrentWidget(self.progress_page)

    def toggle_dark_mode(self):
        """Toggle between light and dark theme modes.
        
        Uses qt-material themes for consistent Material Design styling.
        """
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            # Apply dark blue Material Design theme
            apply_stylesheet(self.app, theme="dark_blue.xml")
        else:
            # Apply light blue Material Design theme
            apply_stylesheet(self.app, theme="light_blue.xml")

# ==================== APPLICATION ENTRY POINT ====================
# Main execution block - initializes and runs the application

if __name__ == "__main__":
    # Create Qt application instance
    app = QApplication(sys.argv)
    
    # Apply custom global stylesheet for consistent styling
    app.setStyleSheet(GLOBAL_STYLESHEET)
    
    # Apply modern Material Design theme via qt-material
    apply_stylesheet(app, theme="light_blue.xml")
    
    # Create and display main window
    window = MainWindow(app)
    window.show()
    
    # Start event loop
    sys.exit(app.exec())