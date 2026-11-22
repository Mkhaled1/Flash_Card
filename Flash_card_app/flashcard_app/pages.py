from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .models import FlashCardDeck
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
        self.back_btn = QPushButton("â†گ Back to Menu")
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
        self.back_btn = QPushButton("â†گ Back to Menu")
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


