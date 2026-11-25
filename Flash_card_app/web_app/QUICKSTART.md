# Quick Start Guide

## Running the Web App

From the repository root, install dependencies and start Flask:

```bash
pip install -r requirements.txt
cd Flash_card_app/web_app/backend
python run.py
```

Open **http://localhost:5000**. Flask serves both the website and its API; no
separate frontend server is needed. The `run.bat` and `run.sh` scripts also start it.

---

## First Time Usage

1. **Import or Create a Deck**
   - **Option A: Import CSV File**
     - Click "📥 Import CSV"
     - Select your CSV file (German words in column 1, English definitions in column 2)
     - The deck name is suggested from the CSV filename and can be edited
     - Click "Import Deck"
   
   - **Option B: Create Manually**
     - Click "➕ New Deck"
     - Enter a name (e.g., "German Verbs")
     - Click "Create Deck"

2. **Add Cards (if creating manually)**
   - Click on your deck
   - Click "✏️ Edit Deck"
   - Click "➕ Add Card"
   - Enter a German word and English definition
   - Repeat for more cards

3. **Start Studying**
   - Click on your deck
   - Click the card to flip it
   - Rate your knowledge level
   - Review until all cards are mastered!

---

## CSV File Format

Your CSV file should have:
- **Column 1:** German words
- **Column 2:** English definitions
- Optional header row (will be auto-detected)

**Example CSV format:**

```csv
word,definition
Laufen,To run
Gehen,To go
Sprechen,To speak
Essen,To eat
Trinken,To drink
```

Or without headers:
```csv
Laufen,To run
Gehen,To go
Sprechen,To speak
```

### How to Create a CSV File

**Using Excel/Google Sheets:**
1. Create two columns
2. Column A: German words
3. Column B: English definitions
4. Save as "filename.csv"

**Using Notepad:**
1. Type word,definition on first line
2. Type German word,English definition on each line
3. Save with `.csv` extension

**Example (for Notepad):**
```
Arbeit,Work
Baum,Tree
Haus,House
Buch,Book
```

---

## Shutting Down

Press `Ctrl+C` in the terminal running Flask.

---

## Troubleshooting

**"Address already in use" error?**
- The port is already in use. Stop the other process using port 5000 or set a different `PORT`.

**"Failed to load decks" error?**
- Make sure the Flask server is running
- Check that it's running on `http://localhost:5000`

**Cards not showing?**
- Refresh the browser (Ctrl+R or Cmd+R)
- Make sure the Flask server is still running

---

## Converting from Desktop to Web

This web-based version includes all features from the original PySide6 desktop application:

✅ SM-2 spaced repetition algorithm  
✅ 6-level status system  
✅ Card flipping animations  
✅ Progress tracking  
✅ Deck management  
✅ Multiple decks support  
✅ CSV-compatible data format (via database)  

The main differences:
- Uses a web browser instead of desktop GUI
- Uses SQLite database instead of CSV files
- In browsers that support file write access, importing with the CSV picker lets the app
  update that file after each rating. Otherwise, use **Deck Manager → Export CSV** to
  save a progress snapshot; importing that export restores the progress.
- Responsive design works on mobile and desktop
- No installation required (just Python and a browser)

---

Happy learning! 🎓📚
