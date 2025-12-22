from flask import Flask, send_from_directory, jsonify, request
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
# Add import for your AI model here
# from your_ai_model import YourAIModelClass

app = Flask(__name__)

# Database setup
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

class RealAISystem:
    def __init__(self):
        # Initialize your real AI model here
        # self.model = YourAIModelClass()
        # self.model.load_weights('path/to/weights')
        # self.camera = cv2.VideoCapture(0)  # or your video source
        pass
    
    def detect_anomalies(self):
        """
        Run real detection on video feed
        Return detection dict if found, None otherwise
        """
        # Example structure - adapt to your model's output
        # ret, frame = self.camera.read()
        # if not ret:
        #     return None
        # 
        # results = self.model.predict(frame)
        # for result in results:
        #     if result.confidence > 0.8:  # threshold
        #         alert_type = self.map_result_to_type(result)
        #         return self.create_alert_dict(alert_type, result)
        # 
        return None
    
    def map_result_to_type(self, result):
        # Map your model's output to alert types
        # return 'weapon' or 'fight' etc.
        pass
    
    def create_alert_dict(self, alert_type, result):
        # Create the alert dict with clip, etc.
        pass

# Choose which system to use
USE_REAL_AI = False  # Set to True when ready

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
    return send_from_directory('FrontEnd', 'login.html')

@app.route('/dashboard')
def serve_dashboard():
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
    
    if username and email and phone and password:
        # In production, validate and store user in database
        print(f"👤 User logged in: {username} ({email}) - {phone}")
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/logout')
def logout():
    # Mock logout
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
    # For demo, return a placeholder response
    print(f"🎥 Clip requested: {filename} - not available in demo")
    return "Video clip not available in demo. Real clips would be stored here.", 404

if __name__ == '__main__':
    # Add some initial sample data
    sample_data = [
        {'type': 'weapon', 'title': 'Weapon detected', 'message': 'Possible weapon seen near gate', 'time': datetime.datetime.now().isoformat(), 'clipUrl': ''},
        {'type': 'fight', 'title': 'Fight detected', 'message': 'Physical altercation in cafeteria', 'time': datetime.datetime.now().isoformat(), 'clipUrl': ''},
        {'type': 'smoke', 'title': 'Smoke detected', 'message': 'Smoke in parking area', 'time': datetime.datetime.now().isoformat(), 'clipUrl': ''},
        {'type': 'entry', 'title': 'Unauthorized entry', 'message': 'Door breach at back entrance', 'time': datetime.datetime.now().isoformat(), 'clipUrl': ''},
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