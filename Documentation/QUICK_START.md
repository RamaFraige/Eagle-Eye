# Eagle Eye - Quick Start Guide

## TL;DR (5 Minutes)

### Prerequisites
- Python 3.8+ installed
- 2GB disk space free

### Installation (2 minutes)
```powershell
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\Activate.ps1

# Install dependencies
pip install flask opencv-python numpy ultralytics twilio pillow
```

### Run (1 minute)
```powershell
python app.py
```

### Access
Open browser: **http://127.0.0.1:5000**

### Login Credentials
```
Username: Rama Fraige
Email: rama.f.fraige@gmail.com
Phone: +962775603083
Password: rorolovemomo
```

---

## What Happens on First Run?

1. **Database Created**: `security.db` is created automatically
2. **AI Models Download**: YOLOv8 models (~1-2 min on first run)
3. **Server Starts**: Flask runs on `http://127.0.0.1:5000`
4. **Login Page Loads**: Greets you with login form
5. **Dashboard Loads**: After login, shows alert dashboard

---

## Common Commands

### Check Python Version
```powershell
python --version  # Should be 3.8+
```

### Activate Virtual Environment
```powershell
# Windows PowerShell
venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

### Deactivate Virtual Environment
```powershell
deactivate
```

### Stop Flask Server
```
Press Ctrl+C in terminal
```

### Change Login Credentials
Edit `app.py`, find `ALLOWED_USER` dictionary and update values

---

## File Structure Overview

```
Eagle_Eye/
├── app.py                 ← Main application (Run this!)
├── ai_model.py           ← AI detection logic
├── best.pt               ← Smoke model
├── guns11n.pt            ← Weapon model
├── security.db           ← Database (created on first run)
├── FrontEnd/             ← Web interface
│   ├── index.html        ← Dashboard
│   ├── login.html        ← Login page
│   ├── script.js         ← JavaScript logic
│   └── style.css         ← Styling
└── clips/                ← Video storage
```

---

## Dashboard Features

### Tabs
- **All Alerts**: Show all detections
- **Weapons**: Filter weapon detections
- **Fights**: Filter fight detections
- **Smoke**: Filter smoke detections
- **Entries**: Filter unauthorized entry detections

### Actions
- **Search**: Find alerts by keyword
- **View Details**: Click alert to see full information
- **Dismiss**: Remove alert from active list
- **Send Feedback**: Report false positives to support team

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run `pip install flask opencv-python numpy ultralytics` |
| Port 5000 in use | Change port in app.py (search for `app.run`) |
| Models won't load | First run takes 1-2 min, be patient. Or pre-download from YOLOv8 hub |
| Blank page in browser | Clear cache (Ctrl+Shift+Delete), close and reopen browser |
| Can't login | Check credentials in app.py `ALLOWED_USER` dict |

---

## Default Configuration

| Setting | Value |
|---------|-------|
| **Server URL** | http://127.0.0.1:5000 |
| **Database** | SQLite (security.db) |
| **Debug Mode** | Enabled (auto-reload on file changes) |
| **AI System** | Real YOLOv8 models |

---

## Next Steps After Running

1. **Explore the Dashboard**: Click around, view alerts, try filtering
2. **Test Detection**: Upload videos to `clips/` folder
3. **Review Code**: Check `app.py` to understand the backend
4. **Customize**: Modify alert types, styling, or logic as needed
5. **Deploy**: For production, follow full INSTALLATION.md guide

---

## Useful Links

- Flask Docs: https://flask.palletsprojects.com/
- YOLOv8 Docs: https://docs.ultralytics.com/
- Python Official: https://www.python.org/

---

## Still Need Help?

See **INSTALLATION.md** for comprehensive troubleshooting and detailed setup instructions.

---

**Version**: 1.0  
**Last Updated**: January 2026
