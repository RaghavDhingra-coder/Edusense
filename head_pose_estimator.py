"""
Head Pose Estimation for Classroom Attentiveness
Uses MediaPipe Face Mesh for robust head pose detection
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class HeadPoseEstimator:
    """
    Estimates head pose (yaw, pitch, roll) from face images
    Determines if student is focused based on head orientation
    """
    
    def __init__(self):
        """Initialize MediaPipe Face Mesh"""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 3D model points for head pose estimation
        self.model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left Mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ], dtype=np.float64)
        
        # Camera internals (approximate)
        self.focal_length = 1.0
        self.camera_center = (0.5, 0.5)
        
    def get_head_pose(self, image: np.ndarray) -> Optional[Dict]:
        """
        Estimate head pose from face image
        
        Args:
            image: BGR image containing a face
            
        Returns:
            Dictionary with yaw, pitch, roll angles and focus status
            None if face not detected
        """
        try:
            if image is None or image.size == 0:
                return None
            
            h, w = image.shape[:2]
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process image
            results = self.face_mesh.process(image_rgb)
            
            if not results.multi_face_landmarks:
                return None
            
            face_landmarks = results.multi_face_landmarks[0]
            
            # Extract 2D landmarks for pose estimation
            # Using key facial points
            landmarks_2d = []
            landmark_indices = [1, 152, 33, 263, 61, 291]  # Nose, chin, eyes, mouth corners
            
            for idx in landmark_indices:
                landmark = face_landmarks.landmark[idx]
                x = landmark.x * w
                y = landmark.y * h
                landmarks_2d.append([x, y])
            
            landmarks_2d = np.array(landmarks_2d, dtype=np.float64)
            
            # Camera matrix
            camera_matrix = np.array([
                [self.focal_length * w, 0, w * self.camera_center[0]],
                [0, self.focal_length * h, h * self.camera_center[1]],
                [0, 0, 1]
            ], dtype=np.float64)
            
            # Distortion coefficients (assuming no distortion)
            dist_coeffs = np.zeros((4, 1))
            
            # Solve PnP
            success, rotation_vec, translation_vec = cv2.solvePnP(
                self.model_points,
                landmarks_2d,
                camera_matrix,
                dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if not success:
                return None
            
            # Convert rotation vector to rotation matrix
            rotation_mat, _ = cv2.Rodrigues(rotation_vec)
            
            # Calculate Euler angles
            yaw, pitch, roll = self._rotation_matrix_to_euler_angles(rotation_mat)
            
            # Detect eye closure
            eye_aspect_ratio = self._calculate_eye_aspect_ratio(face_landmarks, w, h)
            eyes_closed = eye_aspect_ratio < 0.2
            
            # Determine if focused
            is_focused = self._is_focused(yaw, pitch, roll, eyes_closed)
            
            return {
                'yaw': yaw,
                'pitch': pitch,
                'roll': roll,
                'eye_aspect_ratio': eye_aspect_ratio,
                'eyes_closed': eyes_closed,
                'is_focused': is_focused,
                'confidence': self._calculate_confidence(yaw, pitch, roll, eye_aspect_ratio)
            }
        except Exception as e:
            logger.debug(f"Head pose estimation failed: {str(e)}")
            return None
    
    def _rotation_matrix_to_euler_angles(self, R: np.ndarray) -> Tuple[float, float, float]:
        """
        Convert rotation matrix to Euler angles (yaw, pitch, roll)
        
        Returns:
            Tuple of (yaw, pitch, roll) in degrees
        """
        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        
        singular = sy < 1e-6
        
        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0
        
        # Convert to degrees
        pitch = np.degrees(x)
        yaw = np.degrees(y)
        roll = np.degrees(z)
        
        return yaw, pitch, roll
    
    def _calculate_eye_aspect_ratio(self, face_landmarks, w: int, h: int) -> float:
        """
        Calculate Eye Aspect Ratio (EAR) to detect eye closure
        
        Returns:
            EAR value (lower = more closed)
        """
        # Left eye landmarks
        left_eye_indices = [33, 160, 158, 133, 153, 144]
        # Right eye landmarks
        right_eye_indices = [362, 385, 387, 263, 373, 380]
        
        def eye_aspect_ratio(eye_indices):
            points = []
            for idx in eye_indices:
                landmark = face_landmarks.landmark[idx]
                points.append([landmark.x * w, landmark.y * h])
            points = np.array(points)
            
            # Vertical distances
            v1 = np.linalg.norm(points[1] - points[5])
            v2 = np.linalg.norm(points[2] - points[4])
            # Horizontal distance
            h = np.linalg.norm(points[0] - points[3])
            
            ear = (v1 + v2) / (2.0 * h)
            return ear
        
        left_ear = eye_aspect_ratio(left_eye_indices)
        right_ear = eye_aspect_ratio(right_eye_indices)
        
        return (left_ear + right_ear) / 2.0
    
    def _is_focused(self, yaw: float, pitch: float, roll: float, eyes_closed: bool) -> bool:
        """
        Determine if student is focused based on head pose and eye state
        
        Thresholds:
        - Yaw: -25° to +25° (left-right)
        - Pitch: -20° to +20° (up-down)
        - Roll: -30° to +30° (tilt)
        - Eyes must be open
        
        Args:
            yaw: Horizontal rotation
            pitch: Vertical rotation
            roll: Tilt rotation
            eyes_closed: Whether eyes are closed
            
        Returns:
            True if focused, False otherwise
        """
        # Relaxed thresholds for classroom setting
        yaw_threshold = 25.0
        pitch_threshold = 20.0
        roll_threshold = 30.0
        
        yaw_ok = abs(yaw) <= yaw_threshold
        pitch_ok = abs(pitch) <= pitch_threshold
        roll_ok = abs(roll) <= roll_threshold
        eyes_ok = not eyes_closed
        
        # Student is focused if head is generally forward and eyes are open
        return yaw_ok and pitch_ok and roll_ok and eyes_ok
    
    def _calculate_confidence(self, yaw: float, pitch: float, roll: float, ear: float) -> float:
        """
        Calculate confidence score for the focus prediction
        
        Returns:
            Confidence value between 0 and 1
        """
        # Distance from ideal pose (0, 0, 0)
        pose_distance = np.sqrt(yaw**2 + pitch**2 + roll**2)
        
        # Normalize to 0-1 (lower distance = higher confidence)
        max_distance = 50.0  # Maximum expected distance
        pose_confidence = max(0, 1 - (pose_distance / max_distance))
        
        # Eye openness confidence
        eye_confidence = min(1.0, ear / 0.3)
        
        # Combined confidence
        confidence = (pose_confidence * 0.7 + eye_confidence * 0.3)
        
        return confidence
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()
