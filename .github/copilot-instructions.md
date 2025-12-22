# Eagle Eye Project - Copilot Instructions

## Project Overview
Eagle Eye is a full-stack web application for real-time threat detection in surveillance videos. It simulates AI-powered anomaly detection for security monitoring, with a focus on detecting weapons, fights, smoke, and unauthorized entries.

## Architecture
- **Backend**: Flask (Python) server with SQLite database (`security.db`)
- **Frontend**: Vanilla JavaScript, HTML, CSS served from `FrontEnd/` folder
- **AI Component**: Real AI model for computer vision anomaly detection (weapons, fights, smoke, entries) - replace DummyAISystem when ready
- **Data Storage**: SQLite alerts table with fields: id, type, title, message, time, clipUrl, status

## Key Components
- `app.py`: Main Flask application with API endpoints, database, email support, and Twilio SMS integration
- `FrontEnd/index.html`: Dashboard UI with alert tabs, search, and modals
- `FrontEnd/script.js`: Client-side logic for alerts management, video playback, and user interactions
- `FrontEnd/style.css`: Responsive styling with color-coded alert types
- `clips/`: Directory for sample video clips (e.g., `sample_weapon.mp4`)

## Critical Workflows
### Starting the Application
Run `py app.py` from project root. Opens login page at `http://127.0.0.1:5000`. After login, redirects to dashboard at `/dashboard`.

### User Authentication
- Login required with username, email, phone, password
- Stored in localStorage as JSON object
- Phone number used for SMS notifications (when Twilio integrated)

### Alert Management
- Alerts polled via `/api/alerts` (GET)
- New detections checked via `/api/check_detection` (GET) - returns random simulated alerts
- Dismiss alerts via `/api/dismiss_alert` (POST) with `alert_id`
- Feedback submitted via `/api/feedback` (POST) - sends email to `eagleeye.suppteam@gmail.com` with user info, alert details, and message

### Frontend Interactions
- Filter alerts by type (all, weapon, smoke, fight, entry) using tab buttons
- Search alerts by title, message, or type
- View alert details in modal (no video in demo)
- Save clip: Shows demo message (real clips require AI integration)
- Dismiss alerts (stored in localStorage as `eagle_dismissed_alerts`)
- Send to support: Opens modal, sends email to support team

## Project-Specific Conventions
- **Alert Types**: `weapon`, `fight`, `smoke`, `entry` - use these consistently
- **API Endpoints**: RESTful, JSON responses
- **File Structure**: Backend in root, frontend in `FrontEnd/`, clips in `clips/`
- **Database**: SQLite with alerts table; status defaults to 'active', dismissed set to 'dismissed'
- **Video URLs**: Relative paths like `/clips/sample_weapon.mp4`
- **Error Handling**: Frontend falls back to sample data if API fails
- **Styling**: CSS variables for colors, responsive design

## Integration Points
- **AI Replacement**: Swap `DummyAISystem` in `app.py` with real CV model (e.g., OpenCV, TensorFlow)
- **Video Processing**: Integrate real-time video stream analysis instead of random generation
- **Database Scaling**: Migrate from SQLite to PostgreSQL/MySQL for production
- **Authentication**: Add user login/session management
- **Real-time Updates**: Implement WebSockets for live alert notifications
- **Clip Storage**: Use cloud storage (AWS S3, etc.) for video files

## Development Patterns
- **Backend**: Class-based design (`AlertSystem`, `DummyAISystem`)
- **Frontend**: Event-driven with DOM manipulation, debounced search
- **Data Flow**: API-first, with frontend handling UI state
- **Persistence**: Server-side for alerts, client-side for dismissed state
- **Modals**: Accessible dialogs for video playback and feedback

## Key Files Reference
- [app.py](app.py): Flask server, database init, API routes
- [FrontEnd/script.js](FrontEnd/script.js): Alert loading, filtering, modal handling
- [FrontEnd/index.html](FrontEnd/index.html): Main dashboard structure
- [FrontEnd/style.css](FrontEnd/style.css): UI styling and themes

## Common Tasks
- Add new alert type: Update `alert_types` in `DummyAISystem`, add CSS class in `style.css`, update HTML tabs
- Integrate real AI: Modify `generate_dummy_detection()` to call actual model
- Add new API: Follow REST pattern in `app.py`, update frontend fetch calls
- Style changes: Use CSS variables, maintain responsive design</content>
<parameter name="filePath">c:\Users\fraig\Dropbox\My PC (LAPTOP-7L37VIE0)\Desktop\GRADUATION_PROJECT\Eagle_Eye\.github\copilot-instructions.md