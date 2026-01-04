# ai_model.py - AI integration for Eagle Eye threat detection
import cv2
import numpy as np
from ultralytics import YOLO
import os
import random
from datetime import datetime

class EagleEyeAI:
    def __init__(self, model_path='best.pt'):
        print(f" Loading AI model from: {model_path}")
        try:
            self.model = YOLO(model_path)
            print(" AI Model loaded successfully!")
            print(f"   Model type: {type(self.model).__name__}")
            self.has_model = True
        except Exception as e:
            print(f" Error loading model: {e}")
            print("  Falling back to demo mode")
            self.model = None
            self.has_model = False
    
    def detect_in_video(self, video_path, confidence_threshold=0.5):
        if not self.has_model:
            print("  No AI model - using demo detection")
            if random.random() < 0.3:
                return {'type': 'smoke', 'confidence': 0.85}
            return None

        try:
            print(f" Processing video: {video_path}")
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f" Cannot open video: {video_path}")
                return None

            detections = []
            annotated_path = None

            for frame_num in range(10):
                ret, frame = cap.read()
                if not ret:
                    break

                results = self.model(frame, conf=confidence_threshold)
                for result in results:
                    boxes = result.boxes
                    if boxes is None:
                        continue
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = self.model.names[cls_id]
                        alert_type = self.map_class_to_alert_type(class_name)

                        if alert_type:
                            detections.append({
                                'type': alert_type,
                                'class_name': class_name,
                                'confidence': confidence,
                                'frame': frame_num
                            })
                            # Save the first annotated frame
                            if annotated_path is None:
                                annotated_dir = os.path.join('clips', 'annotated')
                                os.makedirs(annotated_dir, exist_ok=True)
                                annotated_file = f"{os.path.splitext(os.path.basename(video_path))[0]}_frame{frame_num}.jpg"
                                annotated_path = os.path.join(annotated_dir, annotated_file)
                                annotated_img = result.plot()  # ndarray with boxes drawn
                                cv2.imwrite(annotated_path, annotated_img)
                            print(f"    Frame {frame_num}: {alert_type.upper()} detected ({confidence:.0%})")

            cap.release()

            if detections:
                best_detection = max(detections, key=lambda x: x['confidence'])
                print(f" {best_detection['type'].upper()} detected! Confidence: {best_detection['confidence']:.0%}")
                return {
                    'type': best_detection['type'],
                    'confidence': best_detection['confidence'],
                    'class_name': best_detection['class_name'],
                    'image_path': annotated_path,
                    'video_path': video_path
                }
            else:
                print(" No threats detected in video")
                return None

        except Exception as e:
            print(f" Error processing video: {e}")
            return None
    
    def map_class_to_alert_type(self, class_name):
        class_lower = class_name.lower()
        if any(word in class_lower for word in ['smoke', 'smoking', 'fire', 'smog', 'fume', 'cigarette']):
            return 'smoke'
        if any(word in class_lower for word in ['weapon', 'gun', 'knife', 'pistol', 'rifle', 'sword']):
            return 'weapon'
        if any(word in class_lower for word in ['fight', 'punch', 'kick', 'assault', 'altercation', 'hitting']):
            return 'fight'
        if any(word in class_lower for word in ['person', 'intruder', 'breach', 'entry', 'trespasser', 'unauthorized']):
            return 'entry'
        return None
    
    def test_with_sample_videos(self):
        print(" Testing AI model with sample videos...")
        if not os.path.exists('clips'):
            print(" No 'clips' folder found")
            return
        
        video_files = [f for f in os.listdir('clips') if f.endswith('.mp4')]
        print(f"   Found {len(video_files)} video files")
        
        results = {}
        for video in video_files:
            video_path = os.path.join('clips', video)
            print(f"\n   Testing: {video}")
            detection = self.detect_in_video(video_path)
            results[video] = detection
        
        print("\n TEST RESULTS:")
        print("-" * 40)
        for video, detection in results.items():
            if detection:
                status = f" {detection['type'].upper()}"
            else:
                status = " No threat"
            print(f"   {video:20}  {status}")
        
        return results

def quick_test():
    print(" Quick AI Model Test")
    print("=" * 40)
    ai = EagleEyeAI('best.pt')
    smoke_video = 'clips/sample_smoke.mp4'
    if os.path.exists(smoke_video):
        print(f"\nTesting with: {smoke_video}")
        result = ai.detect_in_video(smoke_video)
        if result:
            print(f"\nResult:  {result['type'].upper()} DETECTED (Confidence: {result['confidence']:.0%})")
        else:
            print(f"\nResult:  No threat detected")
    else:
        print(f"\n Test video not found: {smoke_video}")
        print(" Please make sure clips/sample_smoke.mp4 exists")

if __name__ == "__main__":
    quick_test()
