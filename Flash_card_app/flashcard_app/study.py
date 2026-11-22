import os
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox,
    QHBoxLayout, QListWidget, QGraphicsOpacityEffect, QSizePolicy,
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QRect, QTimer, QEasingCurve,
    QSequentialAnimationGroup,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .models import FlashCardDeck
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
            self.folder_btn = QPushButton("ًں“پ Change Folder")
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
            self.back_btn = QPushButton("â†گ Back to Menu")
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
            f"Total: {total} | Due: {due} | Learned (repsâ‰¥3): {learned}"
        )
        
        # Clear previous chart and prepare new visualization
        self.ax.clear()
        new, unknown, hard, medium, memorized, perfectly = self.deck.rating_counts()
        values = [new, unknown, hard, medium, memorized, perfectly]
        # Color scheme: Blueâ†’Dark Redâ†’Redâ†’Amberâ†’Greenâ†’Dark Green
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
        2. Check if all cards are mastered â†’ show completion screen
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
        self.card_label.setText(f"ًںژ‰ All {total} cards mastered! ًںژ‰\n\nAll cards are now Perfectly Memorized!")
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

