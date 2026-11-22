import os
from PySide6.QtWidgets import (
    QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox, QDialog,
    QHBoxLayout, QListWidget, QInputDialog, QTableWidget, QTableWidgetItem,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .models import FlashCardDeck
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
        self.browse_btn = QPushButton("Browseâ€¦")
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
        self.load_all_btn = QPushButton("Load All Decks")
        self.new_btn = QPushButton("New Deck")
        self.delete_btn = QPushButton("Delete Deck")
        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.load_all_btn)
        btn_row.addWidget(self.new_btn)
        btn_row.addWidget(self.delete_btn)
        layout.addLayout(btn_row)

        self.choose_folder_btn.clicked.connect(self.choose_folder)
        self.load_btn.clicked.connect(self.load_selected)
        self.load_all_btn.clicked.connect(self.load_all_decks)
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

    def load_all_decks(self):
        """Combine CSV decks in the selected folder into a separate deck file."""
        if not self.folder:
            QMessageBox.warning(self, "No Folder", "Choose a folder first.")
            return

        filenames = [
            os.path.join(self.folder, name)
            for name in os.listdir(self.folder)
            if name.lower().endswith(".csv")
            and not name.casefold().startswith("combined - ")
        ]
        if not filenames:
            QMessageBox.information(self, "No Decks", "No source CSV decks were found.")
            return

        default_name = f"Combined - {os.path.basename(os.path.normpath(self.folder))}.csv"
        output_filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Combined Deck",
            os.path.join(self.folder, default_name),
            "CSV Files (*.csv)"
        )
        if not output_filename:
            return
        if not output_filename.lower().endswith(".csv"):
            output_filename += ".csv"
        if os.path.normcase(os.path.abspath(output_filename)) in {
            os.path.normcase(os.path.abspath(filename)) for filename in filenames
        }:
            QMessageBox.warning(self, "Invalid Destination", "Choose a new file so the source decks remain unchanged.")
            return

        try:
            combined_cards = []
            source_deck = FlashCardDeck()
            for filename in filenames:
                source_deck.load_from_csv(filename)
                combined_cards.extend(source_deck.cards)

            if not combined_cards:
                QMessageBox.information(self, "No Cards", "The source CSV decks contain no valid cards.")
                return

            self.deck.cards = combined_cards
            self.deck.filename = output_filename
            self.deck.save_to_csv()
            QMessageBox.information(
                self,
                "Combined Deck Loaded",
                f"Loaded {len(combined_cards)} cards from {len(filenames)} decks.\n"
                f"Saved combined deck to:\n{output_filename}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to combine decks:\n{e}")

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

