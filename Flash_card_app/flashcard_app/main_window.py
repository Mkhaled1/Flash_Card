from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel,
    QMessageBox, QStackedWidget,
)
from PySide6.QtCore import Qt
from qt_material import apply_stylesheet

from .dialogs import DeckManagerDialog, DeckSelectionDialog, EditorDialog
from .models import FlashCardDeck
from .pages import CardStatusPage, ProgressChartPage
from .study import StudyPage
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
            # Theme toggle button â†’ Amber
            color_start = "#F59E0B"
            color_end = "#FBBF24"
        elif "Quit" in text:
            # Quit button â†’ Red (indicates destructive action)
            color_start = "#EF4444"
            color_end = "#F87171"
        elif "Study" in text:
            # Study button â†’ Green (primary action)
            color_start = "#10B981"
            color_end = "#34D399"
        else:
            # Other buttons â†’ Indigo to Cyan gradient (default)
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

