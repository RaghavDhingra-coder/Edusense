"""
Test script to verify face detection is working and boxes are drawn
"""

import cv2
import torch
import os

# Fix for PyTorch 2.6+
import torch.serialization
try:
    from ultralytics.nn.tasks import DetectionModel
    from torch.nn.modules.container import Sequential
    from torch.nn import Module
    
    torch.serialization.add_safe_globals([DetectionModel, Sequential, Module])
except:
    pass

from ultralytics import YOLO

def test_detection():
    """Test face detection with visual output"""
    
    print("=" * 60)
    print("🧪 TESTING FACE DETECTION")
    print("=" * 60)
    
    # Load model with weights_only=False
    print("\n🔄 Loading YOLOv8-Face model...")
    original_load = torch.load
    
    def safe_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    
    torch.load = safe_load
    model = YOLO("yolov8n-face.pt")
    torch.load = original_load
    
    print("✅ Model loaded")
    
    # Open webcam
    print("\n🎥 Opening webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Failed to open webcam")
        return
    
    print("✅ Webcam opened")
    print("\n📹 Press 'q' to quit")
    print("=" * 60)
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Failed to read frame")
            break
        
        frame_count += 1
        
        # Run detection
        results = model(frame, conf=0.3, imgsz=640, verbose=False)
        
        # Count detections
        detection_count = 0
        if len(results) > 0 and results[0].boxes is not None:
            detection_count = len(results[0].boxes)
        
        # Draw results
        annotated_frame = frame.copy()
        
        if len(results) > 0 and results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                
                # Draw box
                cv2.rectangle(
                    annotated_frame,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    (0, 255, 0),
                    2
                )
                
                # Draw confidence
                label = f"{conf:.2f}"
                cv2.putText(
                    annotated_frame,
                    label,
                    (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )
        
        # Draw info
        info = f"Frame: {frame_count} | Detections: {detection_count}"
        cv2.putText(
            annotated_frame,
            info,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )
        
        # Print to console every 30 frames
        if frame_count % 30 == 0:
            print(f"Frame {frame_count}: {detection_count} detections")
        
        # Display
        cv2.imshow("Face Detection Test", annotated_frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Test complete")

if __name__ == "__main__":
    test_detection()
