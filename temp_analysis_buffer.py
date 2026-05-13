"""
Temporary Analysis Buffer Manager
Manages temporary local storage for high-quality analysis
Auto-cleanup after analysis completes
"""

import os
import shutil
import logging
import cv2
import numpy as np
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class TempAnalysisBuffer:
    """
    Manages temporary local buffer for analysis
    
    Purpose:
    - Store high-quality face crops locally for accurate analysis
    - Avoid network/decode issues from Cloudinary
    - Auto-cleanup after analysis
    
    NOT permanent storage - Cloudinary remains source of truth
    """
    
    def __init__(self, base_dir: str = 'temp_analysis_buffer'):
        """
        Initialize temp analysis buffer
        
        Args:
            base_dir: Base directory for temp buffer
        """
        self.base_dir = base_dir
        self.enabled = os.getenv('ENABLE_TEMP_ANALYSIS_BUFFER', 'True').lower() == 'true'
        
        # Image quality settings (higher than upload)
        self.jpeg_quality = int(os.getenv('ANALYSIS_JPEG_QUALITY', '95'))
        self.min_size = int(os.getenv('ANALYSIS_MIN_SIZE', '112'))
        
        if self.enabled:
            os.makedirs(self.base_dir, exist_ok=True)
            logger.info(f"✅ Temp Analysis Buffer enabled: {self.base_dir}")
            logger.info(f"   JPEG quality: {self.jpeg_quality}")
        else:
            logger.info("⚠️  Temp Analysis Buffer disabled")
    
    def save_for_analysis(
        self,
        session_id: str,
        student_id: str,
        frame_number: int,
        face_image: np.ndarray,
        confidence: float
    ) -> bool:
        """
        Save face crop to temp buffer for analysis
        
        Args:
            session_id: Session identifier
            student_id: Student identifier
            frame_number: Frame number
            face_image: Face crop image (high quality)
            confidence: Detection confidence
            
        Returns:
            True if saved successfully
        """
        if not self.enabled:
            return False
        
        try:
            # Validate image quality
            if not self._is_valid_for_analysis(face_image):
                logger.debug(f"⚠️  Image quality too low for analysis: {student_id} frame {frame_number}")
                return False
            
            # Create directory structure
            student_dir = os.path.join(self.base_dir, session_id, f"student_{student_id}")
            os.makedirs(student_dir, exist_ok=True)
            
            # Save with high quality
            image_path = os.path.join(student_dir, f"frame_{frame_number:06d}.jpg")
            
            # Use high JPEG quality for analysis
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            success = cv2.imwrite(image_path, face_image, encode_param)
            
            if success:
                logger.debug(f"💾 Saved to temp buffer: {student_id} frame {frame_number}")
                return True
            else:
                logger.warning(f"⚠️  Failed to save temp buffer: {image_path}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error saving to temp buffer: {e}")
            return False
    
    def _is_valid_for_analysis(self, image: np.ndarray) -> bool:
        """
        Check if image is suitable for analysis
        More strict than upload quality check
        
        Args:
            image: Face crop image
            
        Returns:
            True if quality is good enough for analysis
        """
        try:
            # Check minimum size
            if image.shape[0] < self.min_size or image.shape[1] < self.min_size:
                return False
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Check blur (stricter than upload)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 100:  # Stricter than upload (50)
                return False
            
            # Check brightness
            brightness = np.mean(gray)
            if brightness < 40 or brightness > 220:
                return False
            
            # Check contrast
            contrast = gray.std()
            if contrast < 25:  # Stricter than upload (20)
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Quality check error: {e}")
            return True  # Accept if check fails
    
    def get_session_images(self, session_id: str) -> Dict[str, List[str]]:
        """
        Get all images for a session from temp buffer
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict mapping student_id to list of image paths
        """
        if not self.enabled:
            return {}
        
        session_dir = os.path.join(self.base_dir, session_id)
        
        if not os.path.exists(session_dir):
            logger.warning(f"⚠️  Session not found in temp buffer: {session_id}")
            return {}
        
        result = {}
        
        try:
            # Iterate through student folders
            for student_folder in os.listdir(session_dir):
                student_path = os.path.join(session_dir, student_folder)
                
                if not os.path.isdir(student_path):
                    continue
                
                # Extract student ID from folder name (student_XXX)
                if student_folder.startswith('student_'):
                    student_id = student_folder.replace('student_', '')
                else:
                    continue
                
                # Get all images for this student
                images = []
                for img_file in sorted(os.listdir(student_path)):
                    if img_file.endswith(('.jpg', '.jpeg', '.png')):
                        img_path = os.path.join(student_path, img_file)
                        images.append(img_path)
                
                if images:
                    result[student_id] = images
            
            logger.info(f"📂 Found {len(result)} students in temp buffer for session {session_id}")
            for student_id, images in result.items():
                logger.info(f"   {student_id}: {len(images)} images")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error reading temp buffer: {e}")
            return {}
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        Cleanup temp buffer for a session after analysis
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if cleaned successfully
        """
        if not self.enabled:
            return True
        
        session_dir = os.path.join(self.base_dir, session_id)
        
        if not os.path.exists(session_dir):
            return True
        
        try:
            shutil.rmtree(session_dir)
            logger.info(f"🧹 Cleaned temp buffer for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup temp buffer: {e}")
            return False
    
    def cleanup_all(self) -> bool:
        """
        Cleanup entire temp buffer (all sessions)
        Use with caution!
        
        Returns:
            True if cleaned successfully
        """
        if not self.enabled:
            return True
        
        if not os.path.exists(self.base_dir):
            return True
        
        try:
            shutil.rmtree(self.base_dir)
            os.makedirs(self.base_dir, exist_ok=True)
            logger.info("🧹 Cleaned entire temp buffer")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup temp buffer: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get temp buffer statistics"""
        if not self.enabled:
            return {'enabled': False}
        
        try:
            total_sessions = 0
            total_students = 0
            total_images = 0
            total_size_bytes = 0
            
            if os.path.exists(self.base_dir):
                for session_folder in os.listdir(self.base_dir):
                    session_path = os.path.join(self.base_dir, session_folder)
                    
                    if not os.path.isdir(session_path):
                        continue
                    
                    total_sessions += 1
                    
                    for student_folder in os.listdir(session_path):
                        student_path = os.path.join(session_path, student_folder)
                        
                        if not os.path.isdir(student_path):
                            continue
                        
                        total_students += 1
                        
                        for img_file in os.listdir(student_path):
                            img_path = os.path.join(student_path, img_file)
                            
                            if os.path.isfile(img_path):
                                total_images += 1
                                total_size_bytes += os.path.getsize(img_path)
            
            return {
                'enabled': True,
                'base_dir': self.base_dir,
                'total_sessions': total_sessions,
                'total_students': total_students,
                'total_images': total_images,
                'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
                'jpeg_quality': self.jpeg_quality
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def is_enabled(self) -> bool:
        """Check if temp buffer is enabled"""
        return self.enabled


# Global temp buffer instance
_temp_buffer = None


def get_temp_buffer() -> TempAnalysisBuffer:
    """Get or create global temp buffer instance"""
    global _temp_buffer
    
    if _temp_buffer is None:
        _temp_buffer = TempAnalysisBuffer()
    
    return _temp_buffer
