"""
Production-Grade Embedding Cache System
Optimized for instant recognition with zero cloud latency
"""

import numpy as np
import logging
import time
from typing import Dict, List, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    High-performance in-memory embedding cache
    - Loads all embeddings at startup
    - Zero cloud access during recognition
    - Optimized similarity search
    - Thread-safe operations
    """
    
    def __init__(self, recognition_threshold: float = 0.60):
        """
        Initialize embedding cache
        
        Args:
            recognition_threshold: Minimum similarity for positive match
        """
        self.recognition_threshold = recognition_threshold
        
        # Core data structures (thread-safe)
        self._lock = threading.RLock()
        self.embeddings_matrix = None  # Numpy array (N, embedding_dim)
        self.student_ids = []  # List of student IDs (parallel to embeddings)
        self.student_names = []  # List of student names (parallel to embeddings)
        self.student_metadata = {}  # {student_id: metadata dict}
        
        # Performance tracking
        self.total_searches = 0
        self.total_search_time_ms = 0.0
        self.cache_hits = 0
        
        # Warmup status
        self.is_warmed_up = False
        self.warmup_time_ms = 0.0
        
        logger.info("🚀 Embedding Cache initialized")
        logger.info(f"   Recognition threshold: {recognition_threshold}")
    
    def load_embeddings(self, students_data: List[Dict]) -> bool:
        """
        Load all student embeddings into memory
        Called once at startup
        
        Args:
            students_data: List of dicts with keys:
                - student_id: str
                - student_name: str
                - embeddings: List[np.ndarray]
                - metadata: dict (optional)
        
        Returns:
            True if successful
        """
        start_time = time.time()
        
        try:
            with self._lock:
                all_embeddings = []
                self.student_ids = []
                self.student_names = []
                self.student_metadata = {}
                
                for student in students_data:
                    student_id = student['student_id']
                    student_name = student['student_name']
                    embeddings = student['embeddings']
                    metadata = student.get('metadata', {})
                    
                    # Add each embedding
                    for embedding in embeddings:
                        all_embeddings.append(embedding)
                        self.student_ids.append(student_id)
                        self.student_names.append(student_name)
                    
                    # Store metadata
                    self.student_metadata[student_id] = {
                        'name': student_name,
                        'num_embeddings': len(embeddings),
                        'metadata': metadata
                    }
                
                # Build numpy matrix for fast similarity search
                if all_embeddings:
                    self.embeddings_matrix = np.array(all_embeddings, dtype=np.float32)
                    
                    # Normalize embeddings for faster cosine similarity
                    norms = np.linalg.norm(self.embeddings_matrix, axis=1, keepdims=True)
                    self.embeddings_matrix = self.embeddings_matrix / (norms + 1e-8)
                else:
                    self.embeddings_matrix = None
                
                self.warmup_time_ms = (time.time() - start_time) * 1000
                self.is_warmed_up = True
                
                logger.info("=" * 60)
                logger.info("✅ Embedding Cache Loaded")
                logger.info("=" * 60)
                logger.info(f"   Students: {len(self.student_metadata)}")
                logger.info(f"   Total embeddings: {len(all_embeddings)}")
                logger.info(f"   Matrix shape: {self.embeddings_matrix.shape if self.embeddings_matrix is not None else 'None'}")
                logger.info(f"   Load time: {self.warmup_time_ms:.1f}ms")
                logger.info("=" * 60)
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to load embeddings: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query_embedding: np.ndarray) -> Optional[Dict]:
        """
        Search for matching student (OPTIMIZED FOR SPEED)
        
        Args:
            query_embedding: Face embedding to search for
            
        Returns:
            Dict with student_id, student_name, confidence or None
        """
        if not self.is_warmed_up or self.embeddings_matrix is None:
            return None
        
        start_time = time.time()
        
        try:
            with self._lock:
                # Normalize query embedding
                query_norm = np.linalg.norm(query_embedding)
                if query_norm < 1e-8:
                    return None
                
                query_normalized = query_embedding / query_norm
                
                # Compute similarities (dot product since embeddings are normalized)
                similarities = np.dot(self.embeddings_matrix, query_normalized)
                
                # Find best match
                best_idx = np.argmax(similarities)
                best_similarity = float(similarities[best_idx])
                
                # Track performance
                search_time_ms = (time.time() - start_time) * 1000
                self.total_searches += 1
                self.total_search_time_ms += search_time_ms
                
                # Check threshold
                if best_similarity >= self.recognition_threshold:
                    student_id = self.student_ids[best_idx]
                    student_name = self.student_names[best_idx]
                    
                    self.cache_hits += 1
                    
                    logger.debug(f"✅ Match: {student_name} ({best_similarity:.3f}) in {search_time_ms:.1f}ms")
                    
                    return {
                        'student_id': student_id,
                        'student_name': student_name,
                        'confidence': best_similarity,
                        'search_time_ms': search_time_ms
                    }
                else:
                    # Log top 3 matches for debugging
                    top_3_indices = np.argsort(similarities)[-3:][::-1]
                    top_3_scores = [float(similarities[i]) for i in top_3_indices]
                    top_3_names = [self.student_names[i] for i in top_3_indices]
                    
                    logger.debug(f"❓ No match (threshold:{self.recognition_threshold:.3f}) in {search_time_ms:.1f}ms")
                    logger.debug(f"   Top 3: {list(zip(top_3_names, top_3_scores))}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return None
    
    def add_student(self, student_id: str, student_name: str, embeddings: List[np.ndarray], metadata: Dict = None) -> bool:
        """
        Add new student to cache (hot-reload)
        
        Args:
            student_id: Student ID
            student_name: Student name
            embeddings: List of face embeddings
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            with self._lock:
                # Add to metadata
                self.student_metadata[student_id] = {
                    'name': student_name,
                    'num_embeddings': len(embeddings),
                    'metadata': metadata or {}
                }
                
                # Add embeddings to matrix
                new_embeddings = []
                for embedding in embeddings:
                    # Normalize
                    norm = np.linalg.norm(embedding)
                    if norm > 1e-8:
                        normalized = embedding / norm
                        new_embeddings.append(normalized)
                        self.student_ids.append(student_id)
                        self.student_names.append(student_name)
                
                if new_embeddings:
                    new_matrix = np.array(new_embeddings, dtype=np.float32)
                    
                    if self.embeddings_matrix is not None:
                        self.embeddings_matrix = np.vstack([self.embeddings_matrix, new_matrix])
                    else:
                        self.embeddings_matrix = new_matrix
                    
                    logger.info(f"✅ Added student to cache: {student_name} ({len(new_embeddings)} embeddings)")
                    logger.info(f"   New matrix shape: {self.embeddings_matrix.shape}")
                    
                    return True
                else:
                    logger.warning(f"⚠️  No valid embeddings for {student_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to add student: {e}")
            return False
    
    def remove_student(self, student_id: str) -> bool:
        """
        Remove student from cache
        
        Args:
            student_id: Student ID to remove
            
        Returns:
            True if successful
        """
        try:
            with self._lock:
                if student_id not in self.student_metadata:
                    return False
                
                # Find indices to remove
                indices_to_keep = [i for i, sid in enumerate(self.student_ids) if sid != student_id]
                
                if len(indices_to_keep) == 0:
                    # No students left
                    self.embeddings_matrix = None
                    self.student_ids = []
                    self.student_names = []
                else:
                    # Rebuild arrays
                    self.embeddings_matrix = self.embeddings_matrix[indices_to_keep]
                    self.student_ids = [self.student_ids[i] for i in indices_to_keep]
                    self.student_names = [self.student_names[i] for i in indices_to_keep]
                
                # Remove metadata
                student_name = self.student_metadata[student_id]['name']
                del self.student_metadata[student_id]
                
                logger.info(f"🗑️  Removed student from cache: {student_name}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to remove student: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            avg_search_time = self.total_search_time_ms / max(1, self.total_searches)
            hit_rate = (self.cache_hits / max(1, self.total_searches)) * 100
            
            return {
                'is_warmed_up': self.is_warmed_up,
                'warmup_time_ms': round(self.warmup_time_ms, 2),
                'total_students': len(self.student_metadata),
                'total_embeddings': len(self.student_ids),
                'matrix_shape': str(self.embeddings_matrix.shape) if self.embeddings_matrix is not None else 'None',
                'total_searches': self.total_searches,
                'cache_hits': self.cache_hits,
                'hit_rate_percent': round(hit_rate, 2),
                'avg_search_time_ms': round(avg_search_time, 2),
                'recognition_threshold': self.recognition_threshold
            }
    
    def clear(self):
        """Clear all cache data"""
        with self._lock:
            self.embeddings_matrix = None
            self.student_ids = []
            self.student_names = []
            self.student_metadata = {}
            self.is_warmed_up = False
            
            logger.info("🧹 Embedding cache cleared")


# Global cache instance
_embedding_cache = None


def get_embedding_cache(recognition_threshold: float = 0.60) -> EmbeddingCache:
    """Get or create global embedding cache"""
    global _embedding_cache
    
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache(recognition_threshold=recognition_threshold)
    
    return _embedding_cache


def initialize_cache_from_database() -> bool:
    """
    Initialize embedding cache from database at startup
    CRITICAL: Call this once when server starts
    
    Returns:
        True if successful
    """
    try:
        from database import get_db_session
        from models import Student, StudentImage
        import base64
        
        logger.info("🔄 Initializing embedding cache from database...")
        
        session = get_db_session()
        if not session:
            logger.error("❌ Database session not available")
            return False
        
        try:
            students = session.query(Student).all()
            logger.info(f"📊 Found {len(students)} students in database")
            
            students_data = []
            
            for student in students:
                # Get student images with embeddings
                images = session.query(StudentImage).filter_by(student_id=student.id).all()
                logger.info(f"   Student: {student.student_name} ({student.student_id}) - {len(images)} images")
                
                # Decode embeddings
                embeddings = []
                for img in images:
                    if img.embedding_vector:
                        try:
                            embedding_bytes = base64.b64decode(img.embedding_vector)
                            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                            embeddings.append(embedding)
                            logger.debug(f"      ✅ Decoded embedding: shape {embedding.shape}")
                        except Exception as e:
                            logger.warning(f"      ⚠️  Failed to decode embedding: {e}")
                
                if embeddings:
                    students_data.append({
                        'student_id': student.student_id,
                        'student_name': student.student_name,
                        'embeddings': embeddings,
                        'metadata': {
                            'registered_date': student.created_at.isoformat() if student.created_at else None,
                            'num_embeddings': len(embeddings)
                        }
                    })
                    logger.info(f"      ✅ Added {len(embeddings)} embeddings for {student.student_name}")
                else:
                    logger.warning(f"      ⚠️  No valid embeddings for {student.student_name}")
            
            logger.info(f"📦 Prepared {len(students_data)} students for cache")
            
            # Load into cache
            cache = get_embedding_cache()
            success = cache.load_embeddings(students_data)
            
            return success
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize cache: {e}")
        import traceback
        traceback.print_exc()
        return False
