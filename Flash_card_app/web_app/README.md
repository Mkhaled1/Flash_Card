# German Flashcard Web App

A modern web-based flashcard application for learning German using spaced repetition and the SM-2 algorithm. 

## Features

✅ **SM-2 Spaced Repetition Algorithm** - Optimized review scheduling based on difficulty  
✅ **6-Level Status System** - New → Unknown → Hard → Medium → Memorized → Perfectly Memorized  
✅ **Interactive Card Flipping** - Smooth 3D flip animations  
✅ **Real-time Progress** - Track mastery percentage and learning progress  
✅ **Deck Management** - Create, delete, and organize multiple decks  
✅ **Card Editor** - Add, edit, and delete flashcards  
✅ **Progress Visualization** - Doughnut charts showing card distribution  
✅ **Modern UI** - Material Design-inspired interface with gradient buttons  
✅ **Responsive Design** - Works on desktop and mobile devices  

## Project Structure

```
web_app/
├── backend/                 # Flask REST API
│   ├── app/
│   │   ├── __init__.py     # App factory
│   │   ├── config.py       # Configuration
│   │   ├── models.py       # Database models (Deck, FlashCard)
│   │   └── routes.py       # API endpoints
│   ├── run.py              # Entry point
│   └── requirements.txt     # Python dependencies
│
└── frontend/               # React web application
    ├── index.html          # HTML entry point
    ├── app.js              # React components
    └── styles.css          # Styling
```

## Installation & Setup

### Backend (Flask API)

#### Requirements
- Python 3.8+
- pip

#### Setup Instructions

1. **Navigate to backend directory:**
```bash
cd web_app/backend
```

2. **Create virtual environment (optional but recommended):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the Flask server:**
```bash
python run.py
```

The API will be available at `http://localhost:5000`

### Frontend (React Web App)

The frontend is a single-page application that uses React via CDN. No build step required!

#### Setup Instructions

1. **Navigate to frontend directory:**
```bash
cd web_app/frontend
```

2. **Start a local web server:**

Using Python 3:
```bash
python -m http.server 8000
```

Using Python 2:
```bash
python -m SimpleHTTPServer 8000
```

Or using Node.js (if installed):
```bash
npx http-server
```

3. **Open in browser:**
```
http://localhost:8000
```

## API Endpoints

### Decks
- `GET /api/decks` - Get all decks
- `POST /api/decks` - Create new deck
- `GET /api/decks/<id>` - Get deck details
- `PUT /api/decks/<id>` - Update deck
- `DELETE /api/decks/<id>` - Delete deck
- `GET /api/decks/<id>/stats` - Get deck statistics

### Flashcards
- `GET /api/decks/<id>/cards` - Get all cards in deck
- `GET /api/decks/<id>/cards?due_only=true` - Get only due cards
- `POST /api/decks/<id>/cards` - Create new card
- `GET /api/cards/<id>` - Get card details
- `PUT /api/cards/<id>` - Update card
- `DELETE /api/cards/<id>` - Delete card
- `POST /api/cards/<id>/rate` - Rate card (updates SM-2)
- `POST /api/cards/<id>/reset` - Reset card
- `GET /api/decks/<id>/random-card` - Get random due card
- `POST /api/decks/<id>/bulk-reset` - Reset all cards

### Import
- `POST /api/decks/import-csv` - Import flashcards from CSV file

**CSV Import Request:**
```json
{
    "deck_name": "My Deck",
    "file_content": "base64_encoded_csv_content"
}
```

**CSV Format Expected:**
- Column 1: German word
- Column 2: English definition
- Optional header row (auto-detected)

**Response:**
```json
{
    "success": true,
    "deck_id": 1,
    "deck_name": "My Deck",
    "imported_cards": 50,
    "skipped_rows": 2,
    "message": "Imported 50 cards into 'My Deck'"
}
```

### System
- `GET /api/health` - Health check

## Database

The application uses **SQLite** for data persistence. The database file (`flashcards.db`) is automatically created in the backend directory.

### Models

**Deck**
- id (Integer, PK)
- name (String, unique)
- description (String)
- created_at (DateTime)
- updated_at (DateTime)

**FlashCard**
- id (Integer, PK)
- deck_id (Integer, FK)
- word (String) - German word
- definition (Text) - English definition
- reps (Integer) - Successful repetitions
- interval (Integer) - Days until next review
- ef (Float) - Ease factor (1.3-5.0)
- next_due (Date) - Next review date
- created_at (DateTime)
- updated_at (DateTime)

## SM-2 Algorithm Implementation

The SM-2 algorithm updates cards based on quality ratings:

**Quality Values:**
- 0 = Unknown (ef = 1.4)
- 1 = Hard (ef = 1.7)
- 2 = Medium (ef = 2.0)
- 3 = Memorized (ef = 2.5)
- 5 = Perfectly Memorized (ef = 2.8)

**Spaced Repetition Intervals:**
- First repetition: 1 day
- Second repetition: 6 days
- Subsequent: interval × ease factor

## Usage Guide

### Creating a Deck
1. Click **"New Deck"** on the main menu
2. Enter a name and optional description
3. Click **"Create Deck"**

### Importing from CSV File
1. Click **"📥 Import CSV"** on the main menu
2. Enter a deck name
3. Click on the file input to select your CSV file
4. Your CSV should have:
   - **Column 1:** German words
   - **Column 2:** English definitions
   - Optional header row (auto-detected)
5. Preview shows first 3 rows
6. Click **"Import Deck"** to import all cards

**Example CSV format:**
```csv
word,definition
Laufen,To run
Gehen,To go
Sprechen,To speak
```

### Adding Cards
1. Select a deck from the main menu
2. Click **"✏️ Edit Deck"** button
3. Click **"➕ Add Card"**
4. Enter German word and English definition
5. Click **"Add Card"**

### Studying
1. Select a deck to study
2. Click on the card to flip and see the definition
3. Rate your knowledge (Unknown, Hard, Medium, Memorized, or Perfect)
4. The app automatically schedules the next review based on difficulty
5. Continue until all cards are mastered

### Viewing Progress
1. While studying, check the stats at the top
2. Click **"📊 View Stats"** to see detailed progress chart
3. Mastery percentage reflects overall learning progress

### Managing Decks
1. Click **"📚 Deck Manager"** from the main menu
2. Reset all cards in a deck or delete entire decks
3. Use caution - deletion cannot be undone

## Color Scheme

The app uses a modern Material Design-inspired color palette:

- **Primary**: #4F46E5 (Indigo)
- **Secondary**: #06B6D4 (Cyan)
- **Success**: #10B981 (Green)
- **Danger**: #EF4444 (Red)
- **Warning**: #F59E0B (Amber)

## Troubleshooting

### "Failed to load decks" error
- Make sure the Flask backend is running on `http://localhost:5000`
- Check that CORS is enabled
- Open browser console (F12) for detailed error messages

### Cards not saving
- Ensure the SQLite database file has write permissions
- Check the backend console for database errors
- Try recreating the deck

### Performance issues
- For large decks (1000+ cards), consider using PostgreSQL instead of SQLite
- Clear browser cache (Ctrl+Shift+Delete)

## Future Enhancements

🔄 User authentication and sync across devices  
📱 Native mobile apps (React Native)  
🔊 Audio pronunciation guides  
🎯 Spaced repetition algorithms (Anki compatibility)  
📤 Import/Export decks (CSV, Anki format)  
🌐 Multi-language support  
☁️ Cloud backup and synchronization  

## License

Open source project. Use and modify freely for personal or educational purposes.

## Credits

Inspired by Anki, SuperMemo, and other spaced repetition learning tools.
Originally converted from PySide6 desktop application (January 2026).

---

**Happy Learning! 🎓**
