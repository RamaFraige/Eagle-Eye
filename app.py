from flask import Flask, send_from_directory, jsonify, request, redirect, url_for, session, Response
import sqlite3
import datetime
import random
import time
import os 
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart 
from twilio.rest import Client
from ai_model import EagleEyeAI, FightingAIDetector
import cv2
import numpy as np

app = Flask(__name__)
app.secret_key = f'demo-secret-{int(time.time())}'  # New key each startup = fresh login

# Temporary flag to bypass login for debugging UI.
# Read from environment for easy toggling without code changes.
# Login bypass is disabled by default; set EAGLE_SKIP_LOGIN=1 to enable.
SKIP_LOGIN = False  # Always require login for demo
print(f"Login bypass (SKIP_LOGIN): {SKIP_LOGIN}")

ALLOWED_USER = {
    'username': 'Rama Fraige',
    'email': 'rama.f.fraige@gmail.com',
    'phone': '+962775603083',
    'password': 'rorolovemomo'
}

def init_db():
    conn = sqlite3.connect('security.db') 
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT NOT NULL,
                  title TEXT NOT NULL,
                  message TEXT NOT NULL,
                  time TEXT NOT NULL,
                  clipUrl TEXT,
                  status TEXT DEFAULT 'active')''')
    
    # Clear all existing alerts for fresh start
    c.execute('DELETE FROM alerts')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

class DummyAISystem:
    def __init__(self):
        self.alert_types = ['weapon', 'fight', 'smoke', 'entry']
        self.titles = {
            'weapon': 'Weapon detected',
            'fight': 'Fight detected', 
            'smoke': 'Smoke detected',
            'entry': 'Unauthorized entry'
        }
        self.messages = {
            'weapon': 'Possible weapon seen near gate',
            'fight': 'Physical altercation in progress',
            'smoke': 'Smoke detected in restricted area',
            'entry': 'Door breach at secured entrance'
        }
    
    def generate_dummy_detection(self):
        """Generate a random fake detection"""
        if random.random() < 0.3:  # 30% chance of detection
            alert_type = random.choice(self.alert_types)
            
            return {
                'id': f"alert_{int(time.time())}_{random.randint(1000,9999)}",
                'type': alert_type,
                'title': self.titles[alert_type],
                'message': self.messages[alert_type],
                'time': datetime.datetime.now().isoformat(),
                'clipUrl': ''  # No clip in demo
            }
        return None
    
# REAL AI SYSTEM - VER 1

class RealAISystem:
    def __init__(self):
        # Initialize smoke/weapon detectors at startup
        self.ai_detector = None
        self.fighting_detector = None  # Will be lazy-loaded on first use
        
        try:
            self.ai_detector = EagleEyeAI(smoke_model_path='best.pt', weapon_model_path='guns11n.pt')
            print("✅ Smoke/Weapon AI System initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize Smoke/Weapon AI system: {e}")
            self.ai_detector = None
        
        # Create fighting detector instance (models load lazily on first use)
        self.fighting_detector = FightingAIDetector(
            yolo_pose_path='clips/weights/yolo11n-pose.pt',
            action_model_path='clips/weights/action.pth'
        )
        print("✅ Fighting AI System initialized (lazy-loading enabled)!")
    
    def detect_anomalies(self):
        """
        Run real detection on video feed.
        Checks all AI detectors (smoke, weapon, fighting).
        Fighting models load on first detection (lazy loading).
        Uses 3 specific sample videos for testing.
        Return detection dict if found, None otherwise.
        """
        if self.ai_detector is None and self.fighting_detector is None:
            return None
        
        # Use specific sample videos (one from each category)
        sample_videos = [
            'clips/smoking sample_3.mp4',
            'clips/guns sample_3.mp4',
            'clips/fight sample_3.mp4'
        ]
        
        if random.random() < 0.3:  # 30% chance of checking a video
            video_path = random.choice(sample_videos)
            
            # Verify file exists before processing
            if not os.path.exists(video_path):
                print(f" Video not found: {video_path}")
                return None
            
            # Try smoke/weapon detection first
            if self.ai_detector:
                detection = self.ai_detector.detect_in_video(video_path)
                if detection:
                    image_path = detection.get('image_path')
                    alert_dict = self.create_alert_dict(
                        detection['type'],
                        detection['confidence'],
                        image_path or video_path
                    )
                    return alert_dict
            
            # Try fighting detection (models lazy-load on first call)
            if self.fighting_detector:
                detection = self.fighting_detector.detect_in_video(video_path)
                if detection:
                    image_path = detection.get('image_path')
                    alert_dict = self.create_alert_dict(
                        detection['type'],
                        detection['confidence'],
                        image_path or video_path
                    )
                    return alert_dict
        
        return None
    
    def map_result_to_type(self, result):
        # Map your model's output to alert types
        # return 'weapon' or 'fight' etc.
        pass
    
    def create_alert_dict(self, alert_type, confidence, video_source=''):
        """Create the alert dict with clip or annotated frame."""
        clip_url = ''
        if video_source:
            clip_url = '/' + video_source.replace('\\', '/').lstrip('/')
        return {
            'type': alert_type,
            'title': f'{alert_type.capitalize()} detected',
            'message': f'Possible {alert_type} threat detected (Confidence: {confidence:.0%})',
            'time': datetime.datetime.now().isoformat(),
            'clipUrl': clip_url,
            'confidence': confidence
        }




# Choose which system to use
USE_REAL_AI = True  # Set to True when ready

if USE_REAL_AI:
    ai_system = RealAISystem()
else:
    ai_system = DummyAISystem()

class AlertSystem:
    def __init__(self):
        self.ai_system = ai_system  # Use the global ai_system
    
    def check_for_alerts(self):
        """Check for new alerts and save them"""
        detection = self.ai_system.detect_anomalies()  # Changed from generate_dummy_detection
        if detection:
            self.save_alert(detection)
            return detection
        return None
    
    def save_alert(self, alert_data):
        """Save alert to database"""
        conn = sqlite3.connect('security.db')
        c = conn.cursor()

        # Skip if an active alert already exists for the same clip/image
        clip_url = alert_data.get('clipUrl', '')
        c.execute('''SELECT id FROM alerts WHERE status = "active" AND clipUrl = ? LIMIT 1''', (clip_url,))
        if c.fetchone():
            conn.close()
            return False
        
        c.execute('''INSERT INTO alerts (type, title, message, time, clipUrl)
                     VALUES (?, ?, ?, ?, ?)''', 
                 (alert_data['type'], alert_data['title'], alert_data['message'],
                  alert_data['time'], alert_data['clipUrl']))
        
        conn.commit()
        conn.close()
        return True
    
    def get_active_alerts(self):
        """Get all active alerts from database"""
        conn = sqlite3.connect('security.db')
        c = conn.cursor()
        
        c.execute('''SELECT * FROM alerts WHERE status = "active" ORDER BY time DESC LIMIT 20''')
        alerts = c.fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries matching your frontend format
        alert_list = []
        for alert in alerts:
            alert_list.append({
                'id': str(alert[0]),  # Convert to string for JS compatibility
                'type': alert[1],
                'title': alert[2],
                'message': alert[3],
                'time': alert[4],
                'clipUrl': alert[5] or ''  # No default clip in demo
            })
        
        return alert_list
    
    def dismiss_alert(self, alert_id):
        """Dismiss an alert"""
        conn = sqlite3.connect('security.db')
        c = conn.cursor()
        
        c.execute('''UPDATE alerts SET status = "dismissed" WHERE id = ?''', (alert_id,))
        conn.commit()
        conn.close()
        return True

# Create the alert system
alert_system = AlertSystem()

# Twilio SMS Configuration - REPLACE WITH YOUR CREDENTIALS
TWILIO_ACCOUNT_SID = 'your_account_sid_here'  # From Twilio Dashboard
TWILIO_AUTH_TOKEN = 'your_auth_token_here'    # From Twilio Dashboard  
TWILIO_PHONE_NUMBER = '+1234567890'          # Your Twilio phone number

def background_detection():
    """Run continuous detection in background"""
    while True:
        if USE_REAL_AI:
            alert_system.check_for_alerts()
        time.sleep(5)  # Check every 5 seconds

# Start background thread
detection_thread = threading.Thread(target=background_detection, daemon=True)
detection_thread.start()

# FIXED ROUTES - Serve from FrontEnd folder
@app.route('/')
def serve_index():
    if SKIP_LOGIN or session.get('authenticated'):
        # Directly load dashboard while keeping login page intact
        return redirect(url_for('serve_dashboard'))
    return send_from_directory('FrontEnd', 'login.html')

@app.route('/dashboard')
def serve_dashboard():
    if not SKIP_LOGIN and not session.get('authenticated'):
        return redirect(url_for('serve_index'))
    return send_from_directory('FrontEnd', 'index.html')

@app.route('/style.css')
def serve_css():
    return send_from_directory('FrontEnd', 'style.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory('FrontEnd', 'script.js')

@app.route('/Images/<path:filename>')
def serve_images(filename):
    return send_from_directory('Images', filename)

@app.route('/LOGO.jpg')
def serve_logo():
    return send_from_directory('.', 'LOGO.jpg')

# API Routes
@app.route('/api/alerts')
def get_alerts():
    alerts = alert_system.get_active_alerts()
    print(f"📋 Returning {len(alerts)} active alerts")
    return jsonify(alerts)

@app.route('/api/dismiss_alert', methods=['POST'])
def dismiss_alert():
    data = request.get_json()
    alert_id = data.get('alert_id')
    print(f"📝 Dismiss request for alert {alert_id}")
    if alert_id:
        alert_system.dismiss_alert(alert_id)
        print("✅ Alert dismissed")
        return jsonify({'success': True})
    print("❌ No alert_id provided")
    return jsonify({'success': False})

@app.route('/api/check_detection')
def check_detection():
    """Endpoint for frontend to check for new detections"""
    new_alert = alert_system.check_for_alerts()
    if new_alert:
        print(f"🆕 New alert detected: {new_alert['title']}")
        return jsonify({'alert': new_alert})
    return jsonify({'alert': None})

@app.route('/api/feedback', methods=['POST'])
def handle_feedback():
    """Send feedback to support team via email"""
    data = request.get_json()
    alert_id = data.get('alertId')
    message = data.get('message')
    user_data = data.get('userData', {})
    
    print(f"📧 Sending feedback for alert {alert_id} from user {user_data.get('username', 'Unknown')}")
    
    # Get alert details for context
    alert_details = None
    try:
        conn = sqlite3.connect('security.db')
        c = conn.cursor()
        c.execute('SELECT type, message FROM alerts WHERE id = ?', (alert_id,))
        result = c.fetchone()
        conn.close()
        if result:
            alert_details = {'type': result[0], 'message': result[1]}
    except Exception as e:
        print(f"Error fetching alert details: {e}")
    
    # Send email to support team
    try:
        # Email configuration - REPLACE WITH YOUR REAL CREDENTIALS
        SMTP_SERVER = 'smtp.gmail.com'
        SMTP_PORT = 587
        SENDER_EMAIL = 'rama.f.fraige@gmail.com'  # ← Replace with your Gmail
        SENDER_PASSWORD = 'nlbp fkrm jkqj hakk'  # ← Replace with Gmail App Password
        RECEIVER_EMAIL = 'eagleeye.suppteam@gmail.com'
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f'Eagle Eye Support Request - Alert {alert_id}'
        
        body = f"""
New support request from Eagle Eye system:

USER INFORMATION:
Name: {user_data.get('username', 'Not provided')}
Email: {user_data.get('email', 'Not provided')}
Phone: {user_data.get('phone', 'Not provided')}

ALERT DETAILS:
Alert ID: {alert_id}
Alert Type: {alert_details['type'] if alert_details else 'Unknown'}
Alert Description: {alert_details['message'] if alert_details else 'N/A'}

USER MESSAGE:
{message}

Please review this case promptly.
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, text)
        server.quit()
        
        print("✅ Support email sent successfully")
        response_msg = "Your message has been sent to our support team. We will respond within 24 hours."
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        response_msg = "Your message has been logged. Our support team will review it."
    
    return jsonify({
        'success': True,
        'bot_response': response_msg
    })

@app.route('/login.html')
def serve_login():
    return send_from_directory('FrontEnd', 'login.html')

@app.route('/login.js')
def serve_login_js():
    return send_from_directory('FrontEnd', 'login.js')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

    # Temporary bypass for faster UI testing
    if SKIP_LOGIN:
        print("🔓 SKIP_LOGIN enabled - auto-success")
        session['authenticated'] = True
        session['user'] = username or 'Demo User'
        return jsonify({'success': True})

    def norm(val):
        return (val or '').strip()

    provided = {
        'username': norm(username),
        'email': norm(email),
        'phone': norm(phone),
        'password': norm(password)
    }
    if all(provided[k] and provided[k] == ALLOWED_USER[k] for k in ALLOWED_USER):
        session['authenticated'] = True
        session['user'] = ALLOWED_USER['username']
        print(f"👤 User logged in: {username} ({email}) - {phone}")
        return jsonify({'success': True})

    print(f"❌ Invalid login attempt for user: {username} ({email}) - {phone}")
    return jsonify({'success': False}), 401

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/send_sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone = data.get('phone')
    message = data.get('message')
    
    if not phone or not message:
        return jsonify({'success': False, 'error': 'Missing phone or message'})
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        print(f"📱 SMS sent to {phone}: {message}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ SMS failed: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Catch-all route for any other static files
@app.route('/<path:filename>')
def serve_static(filename):
    if os.path.exists(os.path.join('FrontEnd', filename)):
        return send_from_directory('FrontEnd', filename)
    else:
        return "File not found", 404

@app.route('/clips/<path:filename>')
def serve_clips(filename):
    # Serve real clips or annotated frames from the clips folder
    return send_from_directory('clips', filename)

# Live Demo Routes
@app.route('/live-demo')
def serve_live_demo():
    if not SKIP_LOGIN and not session.get('authenticated'):
        return redirect(url_for('serve_index'))
    return send_from_directory('FrontEnd', 'live-demo.html')

# Global camera object for streaming
camera_cap = None
camera_lock = threading.Lock()

@app.route('/video_feed')
def video_feed():
    """Stream video frames with smoke detection in MJPEG format"""
    def generate():
        global camera_cap
        
        with camera_lock:
            # Initialize camera if not already done
            if camera_cap is None:
                camera_cap = cv2.VideoCapture(0)  # 0 = default laptop camera
                if not camera_cap.isOpened():
                    print("❌ Failed to open camera")
                    return
                
                # Set camera resolution for better performance
                camera_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                camera_cap.set(cv2.CAP_PROP_FPS, 30)
                print("✅ Camera initialized")
        
        frame_count = 0
        detection_cooldown = 0
        
        while True:
            try:
                with camera_lock:
                    if camera_cap is None or not camera_cap.isOpened():
                        break
                    
                    ret, frame = camera_cap.read()
                
                if not ret:
                    break
                
                frame_count += 1
                detection_cooldown = max(0, detection_cooldown - 1)
                
                # Run smoke detection every 5 frames to save CPU
                if frame_count % 5 == 0 and ai_system.ai_detector and ai_system.ai_detector.has_smoke_model:
                    try:
                        # Run inference
                        results = ai_system.ai_detector.smoke_model(frame, conf=0.5)
                        
                        # Draw bounding boxes for detections
                        for result in results:
                            boxes = result.boxes
                            if boxes is not None:
                                for box in boxes:
                                    confidence = float(box.conf[0])
                                    # Only trigger alert on high confidence (85% minimum)
                                    if confidence >= 0.85 and detection_cooldown == 0:
                                        # Save the detection frame
                                        try:
                                            annotated_dir = os.path.join('clips', 'annotated')
                                            os.makedirs(annotated_dir, exist_ok=True)
                                            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                                            frame_filename = f"live_smoke_{timestamp}_{random.randint(1000, 9999)}.jpg"
                                            frame_path = os.path.join(annotated_dir, frame_filename)
                                            cv2.imwrite(frame_path, frame)
                                            clip_url = '/' + frame_path.replace('\\', '/').lstrip('/')
                                        except Exception as e:
                                            print(f"Error saving frame: {e}")
                                            clip_url = ''
                                        
                                        # Create alert with frame image as clipUrl
                                        alert_data = {
                                            'type': 'smoke',
                                            'title': 'Smoke Detected (Live)',
                                            'message': f'Smoke detected in real-time camera feed (Confidence: {confidence:.0%})',
                                            'time': datetime.datetime.now().isoformat(),
                                            'clipUrl': clip_url,
                                            'confidence': confidence
                                        }
                                        alert_system.save_alert(alert_data)
                                        print(f"🔔 Live Alert: {alert_data['title']} ({confidence:.0%}) - Frame: {clip_url}")
                                        detection_cooldown = 30  # Wait 30 frames before next alert
                                    
                                    # Draw box on frame
                                    x1, y1, x2, y2 = box.xyxy[0]
                                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                                    color = (0, 165, 255) if confidence >= 0.70 else (0, 255, 255)
                                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                                    label = f'Smoke {confidence:.0%}'
                                    cv2.putText(frame, label, (x1, y1 - 10),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    except Exception as e:
                        print(f"Error during detection: {e}")
                
                # Add FPS counter
                cv2.putText(frame, f'Frame: {frame_count}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
                
                # Encode frame to JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                # Yield frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                       + frame_bytes + b'\r\n')
                
            except Exception as e:
                print(f"Error in video stream: {e}")
                break
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stop_camera', methods=['POST'])
def stop_camera():
    """Stop the camera stream"""
    global camera_cap
    
    with camera_lock:
        if camera_cap is not None:
            camera_cap.release()
            camera_cap = None
            print("📹 Camera stopped")
    
    return jsonify({'success': True})

if __name__ == '__main__':
    # Add some initial sample data with unique clipUrls so they don't get deduplicated
    sample_data = [
        {'type': 'weapon', 'title': 'Weapon detected', 'message': 'Possible weapon seen near gate', 'time': datetime.datetime.now().isoformat(), 'clipUrl': f'sample_weapon_{int(time.time())}'},
        {'type': 'fight', 'title': 'Fight detected', 'message': 'Physical altercation in cafeteria', 'time': datetime.datetime.now().isoformat(), 'clipUrl': f'sample_fight_{int(time.time())}'},
        {'type': 'smoke', 'title': 'Smoke detected', 'message': 'Smoke in parking area', 'time': datetime.datetime.now().isoformat(), 'clipUrl': f'sample_smoke_{int(time.time())}'},
        {'type': 'entry', 'title': 'Unauthorized entry', 'message': 'Door breach at back entrance', 'time': datetime.datetime.now().isoformat(), 'clipUrl': f'sample_entry_{int(time.time())}'},
    ]
    
    for alert in sample_data:
        alert_system.save_alert(alert)
    
    print("🚀 Eagle Eye System Starting...")
    print("📊 Database initialized with sample data")
    print("📁 Serving from FrontEnd folder")
    print("🌐 Open: http://127.0.0.1:5000")
    print("⏹️  Press Ctrl+C to stop")
    print("")
    print("If you still see 404 errors, try: http://127.0.0.1:5000/")
    
    app.run(debug=True, host='127.0.0.1', port=5000)

