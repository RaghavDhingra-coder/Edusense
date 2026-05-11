"""
Test face detection on the test video file
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

def test_video_detection():
    """Test face detection on video file"""
    
    print("=" * 60)
    print("🧪 TESTING FACE DETECTION ON VIDEO")
    print("=" * 60)
    
    video_path = "testvideo.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    # Load model
    print("\n🔄 Loading YOLOv8-Face model...")
    original_load = torch.load
    
    def safe_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    
    torch.load = safe_load
    model = YOLO("yolov8n-face.pt")
    torch.load = original_load
    
    print("✅ Model loaded")
    
    # Open video
    print(f"\n🎥 Opening video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("❌ Failed to open video")
        return
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"✅ Video opened: {total_frames} frames @ {fps} FPS")
    print("\n📹 Press 'q' to quit, SPACE to pause")
    print("=" * 60)
    
    frame_count = 0
    total_detections = 0
    frames_with_detections = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("\n⚠️  End of video")
            break
        
        frame_count += 1
        
        # Run detection with lower confidence
        results = model(frame, conf=0.25, imgsz=640, verbose=False)
        
        # Count detections
        detection_count = 0
        if len(results) > 0 and results[0].boxes is not None:
            detection_count = len(results[0].boxes)
            if detection_count > 0:
                frames_with_detections += 1
                total_detections += detection_count
        
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
        info = f"Frame: {frame_count}/{total_frames} | Faces: {detection_count}"
        cv2.putText(
            annotated_frame,
            info,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )
        
        # Print to console
        if detection_count > 0:
            print(f"Frame {frame_count}: {detection_count} faces detected")
        
        # Display
        cv2.imshow("Video Face Detection Test", annotated_frame)
        
        # Check for quit or pause
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            cv2.waitKey(0)  # Wait for any key
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total frames processed: {frame_count}")
    print(f"Frames with detections: {frames_with_detections}")
    print(f"Total face detections: {total_detections}")
    if frames_with_detections > 0:
        print(f"Average faces per frame: {total_detections / frames_with_detections:.2f}")
    print("=" * 60)

if __name__ == "__main__":
    test_video_detection()
