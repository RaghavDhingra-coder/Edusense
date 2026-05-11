"""
Test if the drawing function works correctly
"""

import cv2
import numpy as np

def test_drawing():
    """Test drawing bounding boxes on a frame"""
    
    print("=" * 60)
    print("🧪 TESTING BOUNDING BOX DRAWING")
    print("=" * 60)
    
    # Create a test frame (640x480, black background)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some color to make it visible
    frame[:] = (50, 50, 50)  # Dark gray
    
    # Create fake detections
    detections = [
        (100, 100, 200, 200, 1, 0.95),  # x1, y1, x2, y2, id, confidence
        (300, 150, 400, 250, 2, 0.87),
        (450, 200, 550, 300, 3, 0.76),
    ]
    
    print(f"\n📦 Created test frame: {frame.shape}")
    print(f"📦 Created {len(detections)} fake detections")
    
    # Draw detections
    annotated_frame = frame.copy()
    
    for detection in detections:
        x1, y1, x2, y2, track_id, confidence = detection
        
        print(f"\n🎨 Drawing detection:")
        print(f"   ID: {track_id}")
        print(f"   Box: ({x1}, {y1}) to ({x2}, {y2})")
        print(f"   Confidence: {confidence:.2f}")
        
        # Draw bounding box (GREEN)
        cv2.rectangle(
            annotated_frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),  # Green
            3  # Thick line
        )
        
        # Draw ID label
        label = f"ID {track_id}"
        label_size, _ = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            2
        )
        
        # Draw label background (GREEN)
        cv2.rectangle(
            annotated_frame,
            (x1, y1 - label_size[1] - 10),
            (x1 + label_size[0] + 10, y1),
            (0, 255, 0),
            -1
        )
        
        # Draw label text (BLACK)
        cv2.putText(
            annotated_frame,
            label,
            (x1 + 5, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            2
        )
        
        # Draw confidence
        conf_text = f"{confidence:.2f}"
        cv2.putText(
            annotated_frame,
            conf_text,
            (x1, y2 + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )
    
    # Add title
    cv2.putText(
        annotated_frame,
        "Drawing Test - Press 'q' to quit",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )
    
    print("\n✅ Drawing complete")
    print("\n📺 Displaying frame...")
    print("   Press 'q' to quit")
    print("=" * 60)
    
    # Display
    cv2.imshow("Drawing Test", annotated_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("\n✅ Test complete")

if __name__ == "__main__":
    test_drawing()
