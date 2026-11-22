"""Compatibility launcher for the German Flashcard application."""

import sys

from flashcard_app.dialogs import (
    CardStatusDialog, DeckManagerDialog, DeckSelectionDialog, EditorDialog,
    ProgressChartDialog,
)
from flashcard_app.main_window import MainWindow
from flashcard_app.models import FlashCard, FlashCardDeck
from flashcard_app.pages import CardStatusPage, ProgressChartPage
from flashcard_app.styles import COLORS, GLOBAL_STYLESHEET
from flashcard_app.study import StudyPage
from flashcard_app.__main__ import main


if __name__ == "__main__":
    sys.exit(main())
