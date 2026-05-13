"""
Storage Manager - Abstraction Layer
Handles both cloud (Cloudinary + PostgreSQL) and local storage
Provides backward compatibility while migrating to cloud
"""

import os
import logging
import shutil
import json
import pickle
import base64
import numpy as np
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from pathlib import Path
import tempfile

from database import db_manager, get_db_session
from cloudinary_manager import cloudinary_manager
from models import (
    Student, StudentImage, Session, SessionImage,
    Analytics, RecognitionLog, UploadedVideo
)

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Unified storage manager supporting both cloud and local storage
    Automatically uses cloud when available, falls back to local
    """
    
    def __init__(self):
        self.cloud_enabled = db_manager.is_available() and cloudinary_manager.is_available()
        self.temp_dir = os.getenv('TEMP_UPLOAD_DIR', 'temp_uploads')
        self.auto_cleanup = os.getenv('AUTO_CLEANUP_TEMP_FILES', 'True').lower() == 'true'
        
        # Create temp directory
        os.makedirs(self.temp_dir, exist_ok=True)
        
        if self.cloud_enabled:
            logger.info("✅ Storage Manager: Cloud mode enabled (PostgreSQL + Cloudinary)")
        else:
            logger.warning("⚠️  Storage Manager: Local mode (cloud not configured)")
    
    # ========================================================================
    # STUDENT REGISTRATION
    # ========================================================================
    
    def register_student(
        self,
        student_name: str,
        student_id: str,
        face_images: List[np.ndarray],
        embeddings: List[np.ndarray]
    ) -> Dict:
        """
        Register student with face images and embeddings
        
        Args:
            student_name: Student's full name
            student_id: Unique student ID (USN)
            face_images: List of face crop images
            embeddings: List of face embeddings
            
        Returns:
            Dict with success status and details
        """
        if self.cloud_enabled:
            return self._register_student_cloud(student_name, student_id, face_images, embeddings)
        else:
            return self._register_student_local(student_name, student_id, face_images, embeddings)
    
    def _register_student_cloud(
        self,
        student_name: str,
        student_id: str,
        face_images: List[np.ndarray],
        embeddings: List[np.ndarray]
    ) -> Dict:
        """Register student in cloud (PostgreSQL + Cloudinary)"""
        session = None
        temp_files = []
        
        try:
            session = get_db_session()
            
            # Check if student already exists
            existing = session.query(Student).filter_by(student_id=student_id).first()
            if existing:
                return {'success': False, 'error': f'Student {student_id} already registered'}
            
            # Create student record
            cloudinary_folder = cloudinary_manager.get_folder_path('registered_students', student_id)
            
            student = Student(
                student_id=student_id,
                student_name=student_name,
                cloudinary_folder=cloudinary_folder,
                num_embeddings=len(embeddings),
                embeddings_metadata={'embedding_size': embeddings[0].shape[0] if embeddings else 0}
            )
            
            session.add(student)
            session.flush()  # Get student.id
            
            # Upload images to Cloudinary
            for idx, (face_img, embedding) in enumerate(zip(face_images, embeddings)):
                # Save temp file
                temp_path = os.path.join(self.temp_dir, f"temp_reg_{student_id}_{idx}.jpg")
                temp_files.append(temp_path)
                
                import cv2
                cv2.imwrite(temp_path, face_img)
                
                # Upload to Cloudinary
                upload_result = cloudinary_manager.upload_image(
                    file_path=temp_path,
                    folder=cloudinary_folder,
                    public_id=f"face_{idx}",
                    tags=['registration', student_id],
                    context={'student_id': student_id, 'student_name': student_name}
                )
                
                if upload_result:
                    # Save image record with embedding
                    student_image = StudentImage(
                        student_id=student.id,
                        image_url=upload_result['secure_url'],
                        public_id=upload_result['public_id'],
                        thumbnail_url=upload_result['thumbnail_url'],
                        embedding_vector=base64.b64encode(embedding.tobytes()).decode('utf-8')
                    )
                    session.add(student_image)
            
            # Commit transaction
            session.commit()
            
            logger.info(f"✅ Student registered in cloud: {student_name} ({student_id})")
            
            return {
                'success': True,
                'message': f'Student {student_name} registered successfully',
                'student_id': student_id,
                'num_embeddings': len(embeddings),
                'storage': 'cloud'
            }
            
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"❌ Failed to register student in cloud: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            if session:
                session.close()
            
            # Cleanup temp files
            if self.auto_cleanup:
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except:
                        pass
    
    def _register_student_local(
        self,
        student_name: str,
        student_id: str,
        face_images: List[np.ndarray],
        embeddings: List[np.ndarray]
    ) -> Dict:
        """Register student locally (fallback)"""
        try:
            # Use existing local registration logic
            from student_registry import StudentRegistry
            registry = StudentRegistry()
            return registry.register_student(student_name, student_id, face_images)
        except Exception as e:
            logger.error(f"❌ Failed to register student locally: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_registered_students(self) -> List[Dict]:
        """Get list of all registered students"""
        if self.cloud_enabled:
            return self._get_registered_students_cloud()
        else:
            return self._get_registered_students_local()
    
    def _get_registered_students_cloud(self) -> List[Dict]:
        """Get registered students from cloud"""
        session = None
        try:
            session = get_db_session()
            students = session.query(Student).all()
            
            result = []
            for student in students:
                result.append({
                    'student_id': student.student_id,
                    'student_name': student.student_name,
                    'num_embeddings': student.num_embeddings,
                    'registered_date': student.created_at.isoformat() if student.created_at else None,
                    'storage': 'cloud'
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get students from cloud: {e}")
            return []
        finally:
            if session:
                session.close()
    
    def _get_registered_students_local(self) -> List[Dict]:
        """Get registered students from local storage"""
        try:
            from student_registry import StudentRegistry
            registry = StudentRegistry()
            return registry.get_all_students()
        except Exception as e:
            logger.error(f"❌ Failed to get students locally: {e}")
            return []
    
    def get_student_embeddings(self, student_id: str) -> Optional[List[np.ndarray]]:
        """Get student embeddings for recognition"""
        if self.cloud_enabled:
            return self._get_student_embeddings_cloud(student_id)
        else:
            return self._get_student_embeddings_local(student_id)
    
    def _get_student_embeddings_cloud(self, student_id: str) -> Optional[List[np.ndarray]]:
        """Get student embeddings from cloud"""
        session = None
        try:
            session = get_db_session()
            
            student = session.query(Student).filter_by(student_id=student_id).first()
            if not student:
                return None
            
            # Get all student images with embeddings
            images = session.query(StudentImage).filter_by(student_id=student.id).all()
            
            embeddings = []
            for img in images:
                if img.embedding_vector:
                    # Decode base64 embedding
                    embedding_bytes = base64.b64decode(img.embedding_vector)
                    embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                    embeddings.append(embedding)
            
            return embeddings if embeddings else None
            
        except Exception as e:
            logger.error(f"❌ Failed to get embeddings from cloud: {e}")
            return None
        finally:
            if session:
                session.close()
    
    def _get_student_embeddings_local(self, student_id: str) -> Optional[List[np.ndarray]]:
        """Get student embeddings from local storage"""
        try:
            from student_registry import StudentRegistry
            registry = StudentRegistry()
            if student_id in registry.students:
                return registry.students[student_id]['embeddings']
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get embeddings locally: {e}")
            return None
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    def create_session(self, session_id: str, session_type: str) -> bool:
        """
        Create new session
        
        Args:
            session_id: Unique session identifier
            session_type: 'webcam' or 'video'
            
        Returns:
            True if successful
        """
        if self.cloud_enabled:
            return self._create_session_cloud(session_id, session_type)
        else:
            return self._create_session_local(session_id, session_type)
    
    def _create_session_cloud(self, session_id: str, session_type: str) -> bool:
        """Create session in cloud"""
        session_db = None
        try:
            session_db = get_db_session()
            
            cloudinary_folder = cloudinary_manager.get_folder_path('sessions', session_id)
            
            session = Session(
                session_id=session_id,
                session_name=session_id,
                session_type=session_type,
                cloudinary_folder=cloudinary_folder,
                status='active'
            )
            
            session_db.add(session)
            session_db.commit()
            
            logger.info(f"✅ Session created in cloud: {session_id}")
            return True
            
        except Exception as e:
            if session_db:
                session_db.rollback()
            logger.error(f"❌ Failed to create session in cloud: {e}")
            return False
        finally:
            if session_db:
                session_db.close()
    
    def _create_session_local(self, session_id: str, session_type: str) -> bool:
        """Create session locally"""
        try:
            session_dir = os.path.join('sessions', session_id)
            os.makedirs(session_dir, exist_ok=True)
            logger.info(f"✅ Session created locally: {session_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create session locally: {e}")
            return False
    
    def save_session_image(
        self,
        session_id: str,
        student_id: str,
        frame_number: int,
        face_image: np.ndarray,
        confidence: float,
        is_registered: bool,
        track_id: Optional[int] = None
    ) -> bool:
        """
        Save face crop from session
        
        Args:
            session_id: Session identifier
            student_id: Student identifier (or track ID for unknown)
            frame_number: Frame number
            face_image: Face crop image
            confidence: Detection confidence
            is_registered: Whether student is registered
            track_id: Optional track ID
            
        Returns:
            True if successful
        """
        if self.cloud_enabled:
            return self._save_session_image_cloud(
                session_id, student_id, frame_number, face_image,
                confidence, is_registered, track_id
            )
        else:
            return self._save_session_image_local(
                session_id, student_id, frame_number, face_image
            )
    
    def _save_session_image_cloud(
        self,
        session_id: str,
        student_id: str,
        frame_number: int,
        face_image: np.ndarray,
        confidence: float,
        is_registered: bool,
        track_id: Optional[int] = None
    ) -> bool:
        """Save session image to cloud"""
        session_db = None
        temp_file = None
        
        try:
            # Save temp file
            temp_file = os.path.join(self.temp_dir, f"temp_session_{session_id}_{frame_number}.jpg")
            
            import cv2
            cv2.imwrite(temp_file, face_image)
            
            # Upload to Cloudinary
            folder = cloudinary_manager.get_folder_path('sessions', session_id, student_id)
            
            upload_result = cloudinary_manager.upload_image(
                file_path=temp_file,
                folder=folder,
                public_id=f"frame_{frame_number:06d}",
                tags=['session', session_id, student_id],
                context={'session_id': session_id, 'student_id': student_id, 'frame': frame_number}
            )
            
            if not upload_result:
                return False
            
            # Save to database
            session_db = get_db_session()
            
            # Get session DB ID
            session_obj = session_db.query(Session).filter_by(session_id=session_id).first()
            if not session_obj:
                logger.warning(f"⚠️  Session not found: {session_id}")
                return False
            
            # Get student DB ID if registered
            student_db_id = None
            if is_registered:
                student_obj = session_db.query(Student).filter_by(student_id=student_id).first()
                if student_obj:
                    student_db_id = student_obj.id
            
            # Create session image record
            session_image = SessionImage(
                session_id=session_obj.id,
                student_db_id=student_db_id,
                track_id=track_id,
                frame_number=frame_number,
                image_url=upload_result['secure_url'],
                public_id=upload_result['public_id'],
                thumbnail_url=upload_result['thumbnail_url'],
                confidence=confidence,
                is_registered=is_registered
            )
            
            session_db.add(session_image)
            session_db.commit()
            
            return True
            
        except Exception as e:
            if session_db:
                session_db.rollback()
            logger.error(f"❌ Failed to save session image to cloud: {e}")
            return False
        finally:
            if session_db:
                session_db.close()
            
            # Cleanup temp file
            if self.auto_cleanup and temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def _save_session_image_local(
        self,
        session_id: str,
        student_id: str,
        frame_number: int,
        face_image: np.ndarray
    ) -> bool:
        """Save session image locally"""
        try:
            session_dir = os.path.join('sessions', session_id, student_id)
            os.makedirs(session_dir, exist_ok=True)
            
            import cv2
            image_path = os.path.join(session_dir, f"frame_{frame_number:06d}.jpg")
            cv2.imwrite(image_path, face_image)
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save session image locally: {e}")
            return False
    
    # ========================================================================
    # VIDEO UPLOAD
    # ========================================================================
    
    def save_uploaded_video(
        self,
        session_id: str,
        video_path: str,
        original_filename: str
    ) -> Optional[str]:
        """
        Save uploaded video
        
        Args:
            session_id: Session identifier
            video_path: Local video file path
            original_filename: Original filename
            
        Returns:
            Video URL or local path
        """
        if self.cloud_enabled:
            return self._save_uploaded_video_cloud(session_id, video_path, original_filename)
        else:
            return self._save_uploaded_video_local(session_id, video_path, original_filename)
    
    def _save_uploaded_video_cloud(
        self,
        session_id: str,
        video_path: str,
        original_filename: str
    ) -> Optional[str]:
        """Save uploaded video to cloud"""
        session_db = None
        
        try:
            # Upload to Cloudinary
            folder = cloudinary_manager.get_folder_path('uploads', session_id)
            
            upload_result = cloudinary_manager.upload_video(
                file_path=video_path,
                folder=folder,
                tags=['upload', session_id]
            )
            
            if not upload_result:
                return None
            
            # Save to database
            session_db = get_db_session()
            
            # Get session DB ID
            session_obj = session_db.query(Session).filter_by(session_id=session_id).first()
            if not session_obj:
                logger.warning(f"⚠️  Session not found: {session_id}")
                return upload_result['secure_url']
            
            # Get file size
            file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
            
            # Create uploaded video record
            uploaded_video = UploadedVideo(
                session_id=session_obj.id,
                original_filename=original_filename,
                video_url=upload_result['secure_url'],
                public_id=upload_result['public_id'],
                thumbnail_url=upload_result['thumbnail_url'],
                duration_seconds=upload_result.get('duration'),
                file_size_bytes=file_size,
                format=upload_result['format']
            )
            
            session_db.add(uploaded_video)
            session_db.commit()
            
            logger.info(f"✅ Video uploaded to cloud: {original_filename}")
            
            return upload_result['secure_url']
            
        except Exception as e:
            if session_db:
                session_db.rollback()
            logger.error(f"❌ Failed to save video to cloud: {e}")
            return None
        finally:
            if session_db:
                session_db.close()
    
    def _save_uploaded_video_local(
        self,
        session_id: str,
        video_path: str,
        original_filename: str
    ) -> Optional[str]:
        """Save uploaded video locally"""
        try:
            upload_dir = os.path.join('uploads', session_id)
            os.makedirs(upload_dir, exist_ok=True)
            
            dest_path = os.path.join(upload_dir, original_filename)
            shutil.copy2(video_path, dest_path)
            
            logger.info(f"✅ Video saved locally: {original_filename}")
            return dest_path
            
        except Exception as e:
            logger.error(f"❌ Failed to save video locally: {e}")
            return None
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def is_cloud_enabled(self) -> bool:
        """Check if cloud storage is enabled"""
        return self.cloud_enabled
    
    def cleanup_temp_files(self):
        """Cleanup temporary files"""
        try:
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except:
                        pass
                logger.info("✅ Temporary files cleaned up")
        except Exception as e:
            logger.error(f"❌ Failed to cleanup temp files: {e}")


# Global storage manager instance
storage_manager = StorageManager()


def get_storage_manager() -> StorageManager:
    """Get storage manager instance"""
    return storage_manager
