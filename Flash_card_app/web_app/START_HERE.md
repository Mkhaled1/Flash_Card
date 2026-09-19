# 🚀 German Flashcard Web App - START HERE

## ✨ Your Desktop App is Now Web-Based!

Your PySide6 desktop flashcard application has been successfully converted to a modern web application.

### 📍 Quick Links
- **Quick Start:** [QUICKSTART.md](QUICKSTART.md) ← Read this first!
- **Full Docs:** [README.md](README.md)
- **Conversion Details:** [CONVERSION_SUMMARY.md](CONVERSION_SUMMARY.md)

---

## 🎯 Get Started in 30 Seconds

### Windows Users
```bash
cd web_app
run.bat
```
✅ That's it! Browser opens automatically.

### macOS/Linux Users  
```bash
cd web_app
chmod +x run.sh
./run.sh
```
✅ Browser opens automatically.

### Manual Launch (Any OS)

**Terminal 1:**
```bash
cd web_app/backend
pip install -r requirements.txt
python run.py
```

**Terminal 2:**
```bash
cd web_app/frontend
python -m http.server 8000
```

Then open: **http://localhost:8000**

---

## 🎓 What You Get

✅ **Same Features** - All original functionality preserved  
✅ **CSV Import** - Easily import flashcards from CSV files (German | English)
✅ **Better Experience** - Modern UI, responsive design  
✅ **Works Anywhere** - Browser on any device  
✅ **Easy to Deploy** - Cloud-ready architecture  
✅ **No Build Steps** - Just run and go!

---

## 📊 Folder Structure

```
web_app/
├── backend/               Flask REST API
│   ├── app/
│   │   ├── config.py     Configuration
│   │   ├── models.py     Database & SM-2 algorithm
│   │   ├── routes.py     API endpoints
│   │   └── __init__.py
│   ├── run.py            Start backend here
│   └── requirements.txt   Python dependencies
│
├── frontend/              React Web UI
│   ├── index.html        HTML page
│   ├── app.js            React components
│   └── styles.css        Styling
│
├── import_csv.py         (Optional) Import from CSV
├── run.bat               (Windows) Auto launcher
├── run.sh                (Mac/Linux) Auto launcher
│
├── QUICKSTART.md         ← Read this for setup
├── README.md             Full documentation
└── CONVERSION_SUMMARY.md Technical details
```

---

## 🎮 How It Works

1. **Create a Deck** - Give it a name
2. **Add Cards** - German word + English definition
3. **Study** - Click cards to flip, rate your knowledge
4. **Progress** - App tracks your learning with SM-2 algorithm
5. **Repeat** - Study until you master the deck!

---

## 🔧 What Changed

| Aspect | Desktop | Web |
|--------|---------|-----|
| Launch | Run .exe | Open in browser |
| Data Storage | CSV files | SQLite database |
| UI Framework | PySide6 (Qt) | React |
| Backend | Built-in | Flask server |
| Access | Local only | Any device |
| Multi-device | ❌ No | ✅ Yes |

---

## ✅ Features Included

- SM-2 spaced repetition algorithm
- 6-level card status system
- Interactive card flipping
- Progress tracking & charts
- Multiple deck support
- Real-time statistics
- Responsive design
- Modern Material Design UI
- Card editor
- Deck manager
- Study mode with rating buttons

---

## ❓ Quick FAQ

**Q: Do I need to install anything special?**  
A: Just Python 3.8+ and a web browser. That's it!

**Q: Where does my data go?**  
A: Stored in `flashcards.db` in the backend folder.

**Q: Can I use it on my phone?**  
A: Yes! It's fully responsive. Access from any device via `http://<your-ip>:8000`

**Q: What if I have CSV data?**  
A: Use `import_csv.py` to import your existing decks.

**Q: Can I deploy this online?**  
A: Yes! Backend works with Heroku, AWS, DigitalOcean. Frontend works with Vercel, Netlify.

---

## 🚀 Next Steps

1. **Read [QUICKSTART.md](QUICKSTART.md)** for detailed setup instructions
2. **Run `run.bat` (Windows) or `run.sh` (Mac/Linux)**
3. **Create your first deck**
4. **Add some flashcards**
5. **Start studying!**

---

## 📞 Need Help?

- Check [README.md](README.md) for full documentation
- Check [QUICKSTART.md](QUICKSTART.md) for common issues
- Review code comments in `backend/app/models.py` to understand SM-2

---

## 🎉 Ready to Go!

Everything is set up and ready to use. Just follow the **Get Started** section above.

**Happy Learning! 📚🎓**

---

*Converted from PySide6 desktop app → Flask + React web app*  
*Preserves all original features with modern web experience*
