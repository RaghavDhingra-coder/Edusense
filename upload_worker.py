"""
Asynchronous Upload Worker
Handles background uploads to Cloudinary without blocking webcam processing
"""

import os
import time
import logging
import threading
import cv2
import numpy as np
from queue import Queue, Full, Empty
from datetime import datetime
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class UploadTask:
    """Represents a single upload task"""
    
    def __init__(
        self,
        session_id: str,
        student_id: str,
        frame_number: int,
        face_image: np.ndarray,
        confidence: float,
        is_registered: bool,
        track_id: Optional[int] = None,
        timestamp: Optional[datetime] = None
    ):
        self.session_id = session_id
        self.student_id = student_id
        self.frame_number = frame_number
        self.face_image = face_image
        self.confidence = confidence
        self.is_registered = is_registered
        self.track_id = track_id
        self.timestamp = timestamp or datetime.now()
        self.task_id = f"{session_id}_{student_id}_{frame_number}"
    
    def __repr__(self):
        return f"<UploadTask {self.task_id}>"


class UploadWorker:
    """
    Background worker for asynchronous Cloudinary uploads
    Runs in separate thread to avoid blocking webcam processing
    """
    
    def __init__(self, max_queue_size: int = 100):
        """
        Initialize upload worker
        
        Args:
            max_queue_size: Maximum number of tasks in queue
        """
        self.upload_queue = Queue(maxsize=max_queue_size)
        self.worker_thread = None
        self.running = False
        self.paused = False
        
        # Statistics
        self.total_queued = 0
        self.total_uploaded = 0
        self.total_failed = 0
        self.total_dropped = 0
        self.upload_times = []
        
        # Configuration
        self.max_queue_size = max_queue_size
        self.compress_quality = int(os.getenv('UPLOAD_JPEG_QUALITY', '85'))  # Increased from 70 to 85
        self.resize_width = int(os.getenv('UPLOAD_RESIZE_WIDTH', '256'))  # Increased from 224 to 256
        self.resize_height = int(os.getenv('UPLOAD_RESIZE_HEIGHT', '256'))  # Increased from 224 to 256
        
        # Storage manager (will be set externally)
        self.storage_manager = None
        
        logger.info("📤 Upload Worker initialized")
        logger.info(f"   Queue size: {max_queue_size}")
        logger.info(f"   Resize: {self.resize_width}x{self.resize_height}")
        logger.info(f"   JPEG quality: {self.compress_quality}")
    
    def set_storage_manager(self, storage_manager):
        """Set storage manager for uploads"""
        self.storage_manager = storage_manager
        logger.info("✅ Storage manager connected to upload worker")
    
    def start(self):
        """Start background upload worker thread"""
        if self.running:
            logger.warning("⚠️  Upload worker already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="UploadWorker"
        )
        self.worker_thread.start()
        
        logger.info("✅ Upload worker started")
    
    def stop(self):
        """Stop background upload worker"""
        if not self.running:
            return
        
        logger.info("🛑 Stopping upload worker...")
        self.running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        
        logger.info("✅ Upload worker stopped")
        self._log_statistics()
    
    def pause(self):
        """Pause uploads (queue still accepts tasks)"""
        self.paused = True
        logger.info("⏸️  Upload worker paused")
    
    def resume(self):
        """Resume uploads"""
        self.paused = False
        logger.info("▶️  Upload worker resumed")
    
    def queue_upload(self, task: UploadTask) -> bool:
        """
        Queue an upload task (NON-BLOCKING)
        
        Args:
            task: UploadTask to queue
            
        Returns:
            True if queued successfully, False if queue full
        """
        try:
            # Try to add to queue without blocking
            self.upload_queue.put_nowait(task)
            self.total_queued += 1
            
            # Log every 10th task
            if self.total_queued % 10 == 0:
                logger.debug(f"📤 Queued: {self.total_queued} tasks (queue size: {self.upload_queue.qsize()})")
            
            return True
            
        except Full:
            # Queue is full - drop task
            self.total_dropped += 1
            
            if self.total_dropped % 10 == 1:  # Log first and every 10th drop
                logger.warning(f"⚠️  Upload queue full! Dropped {self.total_dropped} tasks")
            
            return False
    
    def _worker_loop(self):
        """Main worker loop (runs in background thread)"""
        logger.info("🔄 Upload worker loop started")
        
        while self.running:
            try:
                # Check if paused
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # Get task from queue (with timeout)
                try:
                    task = self.upload_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Process upload
                self._process_upload(task)
                
                # Mark task as done
                self.upload_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ Worker loop error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1.0)
        
        logger.info("🛑 Upload worker loop stopped")
    
    def _process_upload(self, task: UploadTask):
        """
        Process a single upload task
        
        Args:
            task: UploadTask to process
        """
        start_time = time.time()
        
        try:
            # Preprocess image (resize + compress + quality check)
            processed_image = self._preprocess_image(task.face_image)
            
            # Skip if quality too low
            if processed_image is None:
                self.total_failed += 1
                logger.debug(f"⚠️  Skipped low-quality image: {task.task_id}")
                return
            
            # Upload to cloud storage
            if self.storage_manager and self.storage_manager.is_cloud_enabled():
                success = self.storage_manager.save_session_image(
                    session_id=task.session_id,
                    student_id=task.student_id,
                    frame_number=task.frame_number,
                    face_image=processed_image,
                    confidence=task.confidence,
                    is_registered=task.is_registered,
                    track_id=task.track_id
                )
                
                if success:
                    self.total_uploaded += 1
                    upload_time = (time.time() - start_time) * 1000
                    self.upload_times.append(upload_time)
                    
                    # Keep only last 100 times
                    if len(self.upload_times) > 100:
                        self.upload_times.pop(0)
                    
                    # Log every 10th upload
                    if self.total_uploaded % 10 == 0:
                        avg_time = sum(self.upload_times) / len(self.upload_times)
                        logger.info(f"✅ Uploaded: {self.total_uploaded} images (avg: {avg_time:.1f}ms)")
                else:
                    self.total_failed += 1
                    logger.warning(f"⚠️  Upload failed: {task.task_id}")
            else:
                # Cloud not available - skip
                self.total_failed += 1
                
        except Exception as e:
            self.total_failed += 1
            logger.error(f"❌ Upload error for {task.task_id}: {e}")
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image before upload (resize + compress)
        CRITICAL: Reduces upload time and bandwidth while maintaining quality
        
        Args:
            image: Original face crop
            
        Returns:
            Preprocessed image (smaller, compressed) or None if quality too low
        """
        try:
            # Validate image quality BEFORE upload
            if not self._is_valid_quality(image):
                logger.debug("⚠️  Image rejected: quality too low")
                return None
            
            # Resize to target size (use INTER_LANCZOS4 for better quality)
            if image.shape[0] != self.resize_height or image.shape[1] != self.resize_width:
                image = cv2.resize(
                    image,
                    (self.resize_width, self.resize_height),
                    interpolation=cv2.INTER_LANCZOS4  # Better quality than INTER_AREA
                )
            
            # Compress JPEG (in-memory) with higher quality
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.compress_quality]
            _, buffer = cv2.imencode('.jpg', image, encode_param)
            image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
            
            return image
            
        except Exception as e:
            logger.error(f"❌ Preprocessing error: {e}")
            return image  # Return original if preprocessing fails
    
    def _is_valid_quality(self, image: np.ndarray) -> bool:
        """
        Check if image quality is sufficient for analysis
        Rejects blurry, too dark, or too small images
        
        Args:
            image: Face crop image
            
        Returns:
            True if quality is acceptable
        """
        try:
            # Check minimum size
            if image.shape[0] < 80 or image.shape[1] < 80:
                return False
            
            # Convert to grayscale for quality checks
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Check blur (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 50:  # Too blurry
                return False
            
            # Check brightness
            brightness = np.mean(gray)
            if brightness < 30 or brightness > 225:  # Too dark or too bright
                return False
            
            # Check contrast
            contrast = gray.std()
            if contrast < 20:  # Too low contrast
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Quality check error: {e}")
            return True  # Accept if check fails
    
    def get_statistics(self) -> Dict:
        """Get upload worker statistics"""
        avg_upload_time = sum(self.upload_times) / len(self.upload_times) if self.upload_times else 0
        
        return {
            'running': self.running,
            'paused': self.paused,
            'queue_size': self.upload_queue.qsize(),
            'max_queue_size': self.max_queue_size,
            'total_queued': self.total_queued,
            'total_uploaded': self.total_uploaded,
            'total_failed': self.total_failed,
            'total_dropped': self.total_dropped,
            'avg_upload_time_ms': round(avg_upload_time, 1),
            'success_rate': f"{(self.total_uploaded / max(1, self.total_queued) * 100):.1f}%"
        }
    
    def _log_statistics(self):
        """Log final statistics"""
        stats = self.get_statistics()
        
        logger.info("=" * 60)
        logger.info("📊 Upload Worker Statistics")
        logger.info("=" * 60)
        logger.info(f"Total Queued: {stats['total_queued']}")
        logger.info(f"Total Uploaded: {stats['total_uploaded']}")
        logger.info(f"Total Failed: {stats['total_failed']}")
        logger.info(f"Total Dropped: {stats['total_dropped']}")
        logger.info(f"Success Rate: {stats['success_rate']}")
        logger.info(f"Avg Upload Time: {stats['avg_upload_time_ms']:.1f}ms")
        logger.info("=" * 60)
    
    def wait_for_completion(self, timeout: Optional[float] = None):
        """
        Wait for all queued uploads to complete
        
        Args:
            timeout: Maximum time to wait (seconds)
        """
        logger.info("⏳ Waiting for upload queue to complete...")
        
        try:
            if timeout:
                self.upload_queue.join()
            else:
                # Wait with timeout
                start_time = time.time()
                while not self.upload_queue.empty():
                    if timeout and (time.time() - start_time) > timeout:
                        logger.warning(f"⚠️  Timeout waiting for uploads ({self.upload_queue.qsize()} remaining)")
                        break
                    time.sleep(0.1)
            
            logger.info("✅ Upload queue completed")
            
        except Exception as e:
            logger.error(f"❌ Error waiting for completion: {e}")


# Global upload worker instance
_upload_worker = None


def get_upload_worker() -> UploadWorker:
    """Get or create global upload worker instance"""
    global _upload_worker
    
    if _upload_worker is None:
        max_queue_size = int(os.getenv('UPLOAD_QUEUE_SIZE', '100'))
        _upload_worker = UploadWorker(max_queue_size=max_queue_size)
    
    return _upload_worker


def start_upload_worker():
    """Start global upload worker"""
    worker = get_upload_worker()
    if not worker.running:
        worker.start()
    return worker


def stop_upload_worker():
    """Stop global upload worker"""
    global _upload_worker
    if _upload_worker:
        _upload_worker.stop()
        _upload_worker = None
