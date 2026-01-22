# Eagle Eye - Installation & Setup Guide

## Project Overview
**Eagle Eye** is a full-stack web application for real-time threat detection in surveillance videos. It uses AI-powered computer vision to detect anomalies such as weapons, fights, smoke, and unauthorized entries, providing security teams with real-time alerts.

### Technology Stack
- **Backend**: Flask (Python web framework)
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Database**: SQLite
- **AI Models**: YOLOv8 for object/weapon detection, custom models for fight detection
- **Video Processing**: OpenCV (cv2)

---

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **RAM**: 4GB minimum (8GB+ recommended for AI processing)
- **Disk Space**: 2GB minimum
- **GPU** (Optional but recommended): NVIDIA GPU with CUDA support for faster inference

### Python Version Check
Before installation, verify your Python version:
```powershell
python --version
```
If Python 3.8+ is not installed, download it from https://www.python.org/downloads/

---

## Installation Steps

### Step 1: Verify Python Installation
```powershell
python --version
pip --version
```

### Step 2: Clone or Download the Project
If using Git:
```powershell
git clone <repository-url>
cd Eagle_Eye
```

Or simply extract the provided project folder to your desired location.

### Step 3: Create a Virtual Environment (Recommended)
A virtual environment isolates project dependencies from your system Python.

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\Activate.ps1

# macOS/Linux:
source venv/bin/activate
```

**Note**: You should see `(venv)` in your terminal prompt after activation.

### Step 4: Install Required Dependencies
First, create a `requirements.txt` file with the necessary packages, then install:

```powershell
# Install dependencies
pip install flask opencv-python numpy ultralytics twilio pillow

# Optional: If you encounter issues with YOLO models, upgrade:
pip install --upgrade ultralytics
```

#### Required Packages:
- **flask** (2.0+): Web framework for the backend
- **opencv-python** (4.5+): Video processing and computer vision
- **numpy**: Numerical computing
- **ultralytics** (8.0+): YOLOv8 model framework
- **twilio**: SMS notifications (optional, requires API keys)
- **pillow**: Image processing

### Step 5: Download or Verify AI Model Files
The project requires pre-trained AI models:

```
Eagle_Eye/
├── best.pt              (Smoke detection model - YOLOv8)
├── guns11n.pt           (Weapon detection model - YOLOv8)
└── clips/
    └── weights/
        ├── action.pth   (Fight detection model)
        └── yolo11n-pose.pt (Pose estimation for fight detection)
```

If these files are missing:
1. **Smoke Model** (best.pt): Will be auto-downloaded on first run, or download from Roboflow/YOLOv8 model hub
2. **Weapon Model** (guns11n.pt): Download from the trained model repository or use YOLOv8 pre-trained weights
3. **Fight Detection Models**: Included in the project or auto-downloaded on first use

**Note**: First run may take longer as models are downloaded (~500MB-1GB total).

### Step 6: Database Initialization
The database (`security.db`) is automatically created when the Flask app starts for the first time. No manual setup needed.

---

## Configuration

### User Credentials
The default login credentials are hardcoded in `app.py`:

```
Username: Rama Fraige
Email: rama.f.fraige@gmail.com
Phone: +962775603083
Password: rorolovemomo
```

To change credentials, edit the `ALLOWED_USER` dictionary in `app.py`:
```python
ALLOWED_USER = {
    'username': 'Your Name',
    'email': 'your.email@example.com',
    'phone': '+1234567890',
    'password': 'your_password'
}
```

### Optional: Twilio SMS Integration
To enable SMS alerts, set environment variables:

```powershell
# Windows PowerShell
$env:TWILIO_ACCOUNT_SID = 'your_account_sid'
$env:TWILIO_AUTH_TOKEN = 'your_auth_token'
$env:TWILIO_PHONE = '+1234567890'
```

Get these credentials from https://www.twilio.com/

### Optional: Email Configuration
Email notifications use Gmail SMTP. If using real emails, update the credentials in `app.py`:
```python
SENDER_EMAIL = 'your_email@gmail.com'
SENDER_PASSWORD = 'your_app_password'  # Use app-specific password for Gmail
```

---

## Running the Application

### Start the Flask Server

```powershell
# Activate virtual environment first (if using one)
venv\Scripts\Activate.ps1

# Navigate to project directory
cd path/to/Eagle_Eye

# Run the Flask application
python app.py
```

### Expected Output
```
 * Running on http://127.0.0.1:5000
 Press CTRL+C to quit
✅ Smoke/Weapon AI System initialized successfully!
```

### Access the Application
1. Open your web browser
2. Navigate to: **http://127.0.0.1:5000**
3. Login with the credentials provided above
4. After login, you'll be redirected to the **Dashboard**

---

## Project Directory Structure

```
Eagle_Eye/
├── app.py                       # Main Flask application
├── ai_model.py                  # AI detection models
├── best.pt                      # Smoke detection model (YOLO)
├── guns11n.pt                   # Weapon detection model (YOLO)
├── security.db                  # SQLite database (auto-created)
├── README.md                    # Project overview
├── INSTALLATION.md              # This file
├── QUICK_START.md              # Quick reference guide
├──FrontEnd/                     # Frontend files
│   ├── index.html               # Dashboard UI
│   ├── login.html               # Login page
│   ├── script.js                # JavaScript logic
│   ├── style.css                # Styling
│   └── live-demo.html           # Live detection demo
├── clips/                       # Video clips directory
│   ├── annotated/              # Annotated video outputs
│   └── weights/                # Additional model weights
├── BackEnd/                     # Backend utilities (optional)
└── Farah_Project/              # Experimental modules
```

---

## Troubleshooting

### Issue: "Module not found" errors
**Solution**: Ensure all dependencies are installed:
```powershell
pip install -r requirements.txt
```

### Issue: Port 5000 already in use
**Solution**: Change the port in `app.py`:
```python
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
```

### Issue: AI models failing to load
**Solution**:
1. Verify model files exist in the project root
2. Check file permissions
3. On first run, models may auto-download (be patient, ~1-2 minutes)
4. If models are missing, download from official YOLOv8 hub

### Issue: Browser shows "Connection refused"
**Solution**: Ensure Flask is running and check the terminal output for errors

### Issue: Login page stays blank or doesn't load
**Solution**: 
1. Check browser console for JavaScript errors (F12)
2. Clear browser cache
3. Try a different browser

### Issue: High CPU/Memory usage
**Solution**: AI models consume significant resources
- Close other applications
- Use GPU acceleration if available
- Adjust confidence thresholds in `app.py` to reduce detections

---

## Features Overview

### Dashboard
- **Real-time Alerts**: View detected threats with timestamps
- **Alert Filtering**: Filter by alert type (weapon, fight, smoke, entry)
- **Search**: Search alerts by keywords
- **Alert Management**: Dismiss or report false positives

### Alert Types
1. **Weapon**: Firearms or sharp objects detected
2. **Fight**: Physical altercation detected
3. **Smoke**: Fire/smoke detected
4. **Entry**: Unauthorized entry detected

### Video Playback
- View alert video clips (when AI detects the threat)
- Annotated frames showing detection regions
- Confidence scores for each detection

---

## API Endpoints

The Flask backend provides RESTful API endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/alerts` | GET | Retrieve all alerts |
| `/api/check_detection` | GET | Poll for new detections |
| `/api/dismiss_alert` | POST | Dismiss an alert |
| `/api/feedback` | POST | Submit feedback/false positive report |
| `/login` | POST | User authentication |
| `/logout` | POST | Clear session |
| `/dashboard` | GET | Main dashboard page |

---

## Next Steps for Your Professor

1. **Review the Code**: Start with `app.py` to understand the Flask routes
2. **Explore the Frontend**: Check `FrontEnd/script.js` for JavaScript logic
3. **Test the AI**: Upload sample videos to `clips/` and trigger detections
4. **Customize**: Modify user credentials, alert types, or styling as needed
5. **Deploy**: For production, migrate from SQLite to PostgreSQL and use a production WSGI server (Gunicorn, uWSGI)

---

## Support & Maintenance

For issues or questions:
1. Check the troubleshooting section above
2. Review Flask documentation: https://flask.palletsprojects.com/
3. Check YOLO documentation: https://docs.ultralytics.com/

---

## System Specifications Used During Development
- Python 3.10+
- Flask 2.3+
- OpenCV 4.8+
- YOLOv8 / YOLOv11
- CUDA 11.8+ (optional for GPU acceleration)

---

**Last Updated**: January 2026
