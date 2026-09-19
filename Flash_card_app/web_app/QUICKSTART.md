# Quick Start Guide

## Running the Web App

### Step 1: Start the Backend (Flask API)

Open a terminal/PowerShell and run:

```bash
cd "d:\German\Flash card app\web_app\backend"
pip install -r requirements.txt
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

**Leave this terminal open.**

### Step 2: Start the Frontend

Open another terminal/PowerShell and run:

```bash
cd "d:\German\Flash card app\web_app\frontend"
python -m http.server 8000
```

You should see:
```
Serving HTTP on 0.0.0.0 port 8000...
```

### Step 3: Open in Browser

Navigate to: **http://localhost:8000**

That's it! Your flashcard app is now running. 🎉

---

## First Time Usage

1. **Import or Create a Deck**
   - **Option A: Import CSV File**
     - Click "📥 Import CSV"
     - Enter a deck name
     - Select your CSV file (German words in column 1, English definitions in column 2)
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

1. Stop the frontend server: Press `Ctrl+C` in the frontend terminal
2. Stop the backend server: Press `Ctrl+C` in the backend terminal

---

## Troubleshooting

**"Address already in use" error?**
- The port is already in use. Try a different port:
  ```bash
  python -m http.server 9000  # Use port 9000 instead
  ```
  Then open `http://localhost:9000`

**"Failed to load decks" error?**
- Make sure the Flask server is running
- Check that it's running on `http://localhost:5000`

**Cards not showing?**
- Refresh the browser (Ctrl+R or Cmd+R)
- Make sure both terminals are still running

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
- Responsive design works on mobile and desktop
- No installation required (just Python and a browser)

---

Happy learning! 🎓📚
