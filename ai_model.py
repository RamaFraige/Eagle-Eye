# ai_model.py - AI integration for Eagle Eye threat detection
import cv2
import numpy as np
from ultralytics import YOLO
import os
import random
from datetime import datetime

class EagleEyeAI:
    def __init__(self, smoke_model_path='best.pt', weapon_model_path='guns11n.pt'):
        print(f" Loading smoke model from: {smoke_model_path}")
        self.smoke_model = None
        self.weapon_model = None
        self.has_smoke_model = False
        self.has_weapon_model = False
        try:
            self.smoke_model = YOLO(smoke_model_path)
            print(" ✅ Smoke model loaded!")
            self.has_smoke_model = True
        except Exception as e:
            print(f" Error loading smoke model: {e}")
        print(f" Loading weapon model from: {weapon_model_path}")
        try:
            self.weapon_model = YOLO(weapon_model_path)
            print(" ✅ Weapon model loaded!")
            self.has_weapon_model = True
        except Exception as e:
            print(f" Error loading weapon model: {e}")
    
    def detect_in_video(self, video_path, confidence_threshold=0.5):
        if not (self.has_smoke_model or self.has_weapon_model):
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

                # Run both models if available
                model_results = []
                if self.has_smoke_model:
                    model_results.extend(self.smoke_model(frame, conf=confidence_threshold))
                if self.has_weapon_model:
                    model_results.extend(self.weapon_model(frame, conf=confidence_threshold))

                for result in model_results:
                    boxes = result.boxes
                    if boxes is None:
                        continue
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        # Prefer names from the specific model that generated the result
                        try:
                            class_name = result.names[cls_id]
                        except Exception:
                            class_name = 'unknown'
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

class FightingAIDetector:
    """
    Fighting/action detection using torch-based LSTM model.
    Wraps the fight_detection package from Farah's project.
    """
    def __init__(self, yolo_pose_path='clips/weights/yolo11n-pose.pt', 
                 action_model_path='clips/weights/action.pth',
                 confidence_threshold=0.5):
        self.has_fighting_model = False
        self.backend = None
        self.confidence_threshold = confidence_threshold
        
        try:
            # Dynamically import fight_detection components
            from fight_detection.backends.torch import TorchFightBackend
            from fight_detection import fight_pipeline
            
            print(f"[FIGHTING] Loading pose model from: {yolo_pose_path}")
            print(f"[FIGHTING] Loading action model from: {action_model_path}")
            
            # Initialize the TorchFightBackend
            self.backend = TorchFightBackend(
                yolo_model_path=yolo_pose_path,
                action_model_path=action_model_path,
                confidence_threshold=confidence_threshold
            )
            self.fight_pipeline = fight_pipeline
            self.has_fighting_model = True
            print("[FIGHTING] ✅ Fighting detector initialized successfully!")
            
        except ImportError as e:
            print(f"[FIGHTING] ⚠️  fight_detection package not available: {e}")
            print("[FIGHTING] Fighting detection disabled - wheel needs to be installed")
            self.has_fighting_model = False
        except Exception as e:
            print(f"[FIGHTING] ❌ Error initializing fighting detector: {e}")
            self.has_fighting_model = False
    
    def detect_in_video(self, video_path, confidence_threshold=None):
        """Detect fighting/actions in video frames."""
        if not self.has_fighting_model:
            print(f"[FIGHTING] Model not available for: {video_path}")
            return None
        
        if confidence_threshold is None:
            confidence_threshold = self.confidence_threshold
        
        try:
            print(f"[FIGHTING] Processing video: {video_path}")
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"[FIGHTING] Cannot open video: {video_path}")
                return None
            
            detections = []
            annotated_path = None
            frames_buffer = []
            max_frames = 10
            
            # Collect frames for analysis
            for frame_num in range(max_frames):
                ret, frame = cap.read()
                if not ret:
                    break
                frames_buffer.append((frame_num, frame))
            
            cap.release()
            
            if not frames_buffer:
                print(f"[FIGHTING] No frames read from: {video_path}")
                return None
            
            # Process frames through pipeline
            for frame_num, frame in frames_buffer:
                try:
                    # Run fight_pipeline on the frame
                    generator = self.fight_pipeline(frame, backend=self.backend)
                    _, result = next(generator)
                    
                    if result is None:
                        continue
                    
                    # Extract detections from result
                    detection_list = result.interactions if result.interactions else (result.actions if hasattr(result, 'actions') else [])
                    
                    for detection in detection_list:
                        confidence = float(detection.conf) if hasattr(detection, 'conf') else 0.0
                        if confidence >= confidence_threshold:
                            label = detection.label if hasattr(detection, 'label') else 'fight'
                            detections.append({
                                'type': 'fight',
                                'class_name': label,
                                'confidence': confidence,
                                'frame': frame_num
                            })
                            
                            # Save annotated frame on first detection
                            if annotated_path is None:
                                annotated_dir = os.path.join('clips', 'annotated')
                                os.makedirs(annotated_dir, exist_ok=True)
                                annotated_file = f"{os.path.splitext(os.path.basename(video_path))[0]}_frame{frame_num}.jpg"
                                annotated_path = os.path.join(annotated_dir, annotated_file)
                                try:
                                    annotated_img = result.plot()  # ndarray with boxes drawn
                                    cv2.imwrite(annotated_path, annotated_img)
                                except Exception as e:
                                    print(f"[FIGHTING] Could not save annotated frame: {e}")
                                    annotated_path = None
                            
                            print(f"[FIGHTING] Frame {frame_num}: FIGHT detected ({confidence:.0%})")
                
                except StopIteration:
                    continue
                except Exception as e:
                    print(f"[FIGHTING] Error processing frame {frame_num}: {e}")
                    continue
            
            if detections:
                best_detection = max(detections, key=lambda x: x['confidence'])
                print(f"[FIGHTING] FIGHT detected! Confidence: {best_detection['confidence']:.0%}")
                return {
                    'type': 'fight',
                    'confidence': best_detection['confidence'],
                    'class_name': best_detection['class_name'],
                    'image_path': annotated_path,
                    'video_path': video_path
                }
            else:
                print(f"[FIGHTING] No fights detected in video")
                return None
        
        except Exception as e:
            print(f"[FIGHTING] Error processing video: {e}")
            return None


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
