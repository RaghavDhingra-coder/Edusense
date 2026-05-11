"""
Video processing module for handling webcam and video file input
"""

import cv2
import time
import config


class VideoProcessor:
    """
    Handles video input from webcam or video file
    """
    
    def __init__(self, source=0):
        """
        Initialize video processor
        
        Args:
            source: Video source (0 for webcam, or path to video file)
        """
        self.source = source
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        self.target_fps = config.TARGET_FPS
        self.display_scale = config.DISPLAY_SCALE
        
        # FPS calculation
        self.fps_start_time = time.time()
        self.fps_frame_count = 0
        
        self._initialize_capture()
    
    def _initialize_capture(self):
        """
        Initialize video capture
        """
        try:
            print(f"🎥 Opening video source: {self.source}")
            self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open video source: {self.source}")
            
            # Get video properties
            if isinstance(self.source, int):
                print("✅ Webcam opened successfully")
            else:
                total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = int(self.cap.get(cv2.CAP_PROP_FPS))
                print(f"✅ Video file opened: {total_frames} frames @ {fps} FPS")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize video capture: {str(e)}")
    
    def read_frame(self):
        """
        Read next frame from video source
        
        Returns:
            Tuple (success, frame)
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None
        
        ret, frame = self.cap.read()
        
        if ret:
            self.frame_count += 1
            self.fps_frame_count += 1
            
            # Calculate FPS
            current_time = time.time()
            elapsed = current_time - self.fps_start_time
            
            if elapsed >= 1.0:
                self.fps = self.fps_frame_count / elapsed
                self.fps_frame_count = 0
                self.fps_start_time = current_time
        
        return ret, frame
    
    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes and IDs on frame
        
        Args:
            frame: Input frame
            detections: List of (x1, y1, x2, y2, track_id, confidence)
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        for detection in detections:
            x1, y1, x2, y2, track_id, confidence = detection
            
            # Draw bounding box
            cv2.rectangle(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                config.BBOX_COLOR,
                config.BBOX_THICKNESS
            )
            
            # Draw ID label
            label = f"ID {track_id}"
            label_size, _ = cv2.getTextSize(
                label,
                config.TEXT_FONT,
                config.TEXT_SCALE,
                config.TEXT_THICKNESS
            )
            
            # Draw label background
            cv2.rectangle(
                annotated_frame,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0] + 10, y1),
                config.BBOX_COLOR,
                -1
            )
            
            # Draw label text
            cv2.putText(
                annotated_frame,
                label,
                (x1 + 5, y1 - 5),
                config.TEXT_FONT,
                config.TEXT_SCALE,
                (0, 0, 0),
                config.TEXT_THICKNESS
            )
        
        return annotated_frame
    
    def draw_fps(self, frame):
        """
        Draw FPS counter on frame
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with FPS counter
        """
        fps_text = f"FPS: {self.fps:.1f}"
        
        cv2.putText(
            frame,
            fps_text,
            (10, 30),
            config.TEXT_FONT,
            config.TEXT_SCALE,
            config.FPS_COLOR,
            config.TEXT_THICKNESS
        )
        
        return frame
    
    def draw_info(self, frame, student_count, total_images):
        """
        Draw additional info on frame
        
        Args:
            frame: Input frame
            student_count: Number of unique students
            total_images: Total images saved
            
        Returns:
            Frame with info
        """
        info_text = f"Students: {student_count} | Images: {total_images}"
        
        cv2.putText(
            frame,
            info_text,
            (10, 60),
            config.TEXT_FONT,
            0.6,
            (255, 255, 255),
            2
        )
        
        return frame
    
    def display_frame(self, frame, window_name="Classroom Face Tracking"):
        """
        Display frame in window
        
        Args:
            frame: Frame to display
            window_name: Name of display window
        """
        if frame is None:
            return
        
        # Scale frame if needed
        if self.display_scale != 1.0:
            width = int(frame.shape[1] * self.display_scale)
            height = int(frame.shape[0] * self.display_scale)
            frame = cv2.resize(frame, (width, height))
        
        cv2.imshow(window_name, frame)
    
    def release(self):
        """
        Release video capture and close windows
        """
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        print("🔒 Video capture released")
    
    def get_fps(self):
        """
        Get current FPS
        
        Returns:
            Current FPS
        """
        return self.fps
    
    def is_opened(self):
        """
        Check if video capture is opened
        
        Returns:
            True if opened, False otherwise
        """
        return self.cap is not None and self.cap.isOpened()
