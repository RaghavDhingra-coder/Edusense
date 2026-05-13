"""
Production-Grade Recognition Engine
Optimized for instant, stable recognition with zero cloud latency
"""

import numpy as np
import cv2
import time
import logging
from typing import Dict, Optional, Tuple
from collections import deque
from datetime import datetime

from embedding_cache import get_embedding_cache

logger = logging.getLogger(__name__)


class RecognitionEngine:
    """
    High-performance recognition engine
    - Instant recognition (no delays)
    - Temporal smoothing for stability
    - Zero cloud access during recognition
    - Detailed performance profiling
    """
    
    def __init__(self, face_app, confidence_threshold: float = 0.60):
        """
        Initialize recognition engine
        
        Args:
            face_app: InsightFace app for embedding extraction
            confidence_threshold: Minimum confidence for recognition
        """
        self.face_app = face_app
        self.confidence_threshold = confidence_threshold
        
        # Get embedding cache
        self.cache = get_embedding_cache(recognition_threshold=confidence_threshold)
        
        # Track-based recognition state
        self.track_identities = {}  # {track_id: identity_info}
        self.track_history = {}  # {track_id: deque of recent recognitions}
        self.track_frame_count = {}  # {track_id: frame_count}
        
        # Temporal smoothing (prevent flickering)
        self.history_size = 5  # Keep last 5 recognitions
        self.min_consensus = 3  # Need 3/5 agreement for stable identity
        
        # Performance tracking
        self.total_recognitions = 0
        self.total_embedding_time_ms = 0.0
        self.total_search_time_ms = 0.0
        self.total_recognition_time_ms = 0.0
        
        # Unknown person counter
        self.unknown_counter = 0
        
        logger.info("🎯 Recognition Engine initialized")
        logger.info(f"   Confidence threshold: {confidence_threshold}")
        logger.info(f"   Temporal smoothing: {self.history_size} frames, {self.min_consensus} consensus")
    
    def recognize(self, track_id: int, face_crop: np.ndarray, frame_number: int) -> Tuple[str, str, float, bool]:
        """
        Recognize face with instant, stable results
        
        Args:
            track_id: Tracking ID
            face_crop: Face crop image
            frame_number: Current frame number
            
        Returns:
            Tuple (identity_id, identity_name, confidence, is_registered)
        """
        start_time = time.time()
        self.total_recognitions += 1
        
        # DEBUG: Log every 30 frames
        debug = (frame_number % 30 == 0) or (frame_number <= 10)
        
        # Initialize track if new
        if track_id not in self.track_frame_count:
            self.track_frame_count[track_id] = 0
            self.track_history[track_id] = deque(maxlen=self.history_size)
            if debug:
                logger.info(f"🆕 New track: {track_id}")
        
        self.track_frame_count[track_id] += 1
        frame_count = self.track_frame_count[track_id]
        
        # Check if we have stable identity
        if track_id in self.track_identities:
            identity = self.track_identities[track_id]
            
            # For registered students, run recognition less frequently after initial confirmation
            if identity['is_registered'] and frame_count > 10:
                # Already stable, return cached identity
                elapsed = (time.time() - start_time) * 1000
                if debug:
                    logger.debug(f"⚡ Cached: {identity['name']} (Track {track_id}, {elapsed:.1f}ms)")
                return (identity['id'], identity['name'], identity['confidence'], identity['is_registered'])
        
        # Extract embedding
        embed_start = time.time()
        embedding = self._extract_embedding(face_crop)
        embed_time = (time.time() - embed_start) * 1000
        self.total_embedding_time_ms += embed_time
        
        if embedding is None:
            # Failed to extract embedding
            elapsed = (time.time() - start_time) * 1000
            if debug:
                logger.warning(f"⚠️  Embedding extraction failed (Track {track_id}, {elapsed:.1f}ms)")
            return self._get_or_create_unknown(track_id)
        
        if debug:
            logger.info(f"🔍 Extracted embedding for Track {track_id}: shape {embedding.shape}, norm {np.linalg.norm(embedding):.3f}")
        
        # Search in cache
        search_start = time.time()
        result = self.cache.search(embedding)
        search_time = (time.time() - search_start) * 1000
        self.total_search_time_ms += search_time
        
        total_time = (time.time() - start_time) * 1000
        self.total_recognition_time_ms += total_time
        
        if result:
            # Recognized as registered student
            student_id = result['student_id']
            student_name = result['student_name']
            confidence = result['confidence']
            
            if debug:
                logger.info(f"✅ Cache match: {student_name} (conf:{confidence:.3f}, embed:{embed_time:.1f}ms, search:{search_time:.1f}ms, total:{total_time:.1f}ms)")
            
            # Add to history for temporal smoothing
            self.track_history[track_id].append({
                'id': student_id,
                'name': student_name,
                'confidence': confidence,
                'frame': frame_number
            })
            
            # Check for consensus
            identity = self._get_consensus_identity(track_id)
            
            if identity:
                # Stable identity confirmed
                is_new = track_id not in self.track_identities
                
                self.track_identities[track_id] = {
                    'id': identity['id'],
                    'name': identity['name'],
                    'confidence': identity['confidence'],
                    'is_registered': True,
                    'first_seen_frame': frame_number if is_new else self.track_identities[track_id].get('first_seen_frame', frame_number),
                    'last_seen_frame': frame_number
                }
                
                if is_new:
                    logger.info(f"✅ Recognized: {identity['name']} (Track {track_id}, conf:{confidence:.3f}, embed:{embed_time:.1f}ms, search:{search_time:.1f}ms, total:{total_time:.1f}ms)")
                elif debug:
                    logger.debug(f"✅ Confirmed: {identity['name']} (Track {track_id}, {total_time:.1f}ms)")
                
                return (identity['id'], identity['name'], identity['confidence'], True)
            else:
                # Not enough consensus yet, return current best match
                if debug:
                    logger.debug(f"⏳ Pending consensus: {student_name} (Track {track_id}, {len(self.track_history[track_id])}/{self.history_size})")
                return (student_id, student_name, confidence, True)
        else:
            # Not recognized - unknown person
            if debug:
                logger.info(f"❓ Unknown (Track {track_id}, embed:{embed_time:.1f}ms, search:{search_time:.1f}ms, total:{total_time:.1f}ms)")
            return self._get_or_create_unknown(track_id)
    
    def _extract_embedding(self, face_crop: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract face embedding using InsightFace
        OPTIMIZED: Proper preprocessing for best quality
        """
        try:
            # Validate input
            if face_crop is None or face_crop.size == 0:
                return None
            
            h, w = face_crop.shape[:2]
            
            # Resize to optimal size for InsightFace (112x112)
            if h != 112 or w != 112:
                face_crop = cv2.resize(face_crop, (112, 112), interpolation=cv2.INTER_LANCZOS4)
            
            # Extract faces
            faces = self.face_app.get(face_crop)
            
            if len(faces) > 0:
                return faces[0].embedding
            else:
                return None
                
        except Exception as e:
            logger.debug(f"Embedding extraction error: {e}")
            return None
    
    def _get_consensus_identity(self, track_id: int) -> Optional[Dict]:
        """
        Get consensus identity from recent history
        Prevents flickering by requiring multiple confirmations
        """
        if track_id not in self.track_history:
            return None
        
        history = self.track_history[track_id]
        
        if len(history) < self.min_consensus:
            return None
        
        # Count occurrences of each identity
        identity_counts = {}
        identity_confidences = {}
        
        for entry in history:
            identity_id = entry['id']
            if identity_id not in identity_counts:
                identity_counts[identity_id] = 0
                identity_confidences[identity_id] = []
            
            identity_counts[identity_id] += 1
            identity_confidences[identity_id].append(entry['confidence'])
        
        # Find most common identity
        most_common_id = max(identity_counts, key=identity_counts.get)
        count = identity_counts[most_common_id]
        
        # Check if we have consensus
        if count >= self.min_consensus:
            # Get name from most recent entry with this ID
            name = None
            for entry in reversed(history):
                if entry['id'] == most_common_id:
                    name = entry['name']
                    break
            
            # Average confidence
            avg_confidence = np.mean(identity_confidences[most_common_id])
            
            return {
                'id': most_common_id,
                'name': name,
                'confidence': float(avg_confidence),
                'consensus_count': count
            }
        
        return None
    
    def _get_or_create_unknown(self, track_id: int) -> Tuple[str, str, float, bool]:
        """Get or create unknown person identity"""
        if track_id not in self.track_identities:
            self.unknown_counter += 1
            self.track_identities[track_id] = {
                'id': f'unknown_{self.unknown_counter}',
                'name': f'Unknown {self.unknown_counter}',
                'confidence': 0.0,
                'is_registered': False
            }
            logger.debug(f"❓ New unknown person: Unknown {self.unknown_counter} (Track {track_id})")
        
        identity = self.track_identities[track_id]
        return (identity['id'], identity['name'], identity['confidence'], identity['is_registered'])
    
    def handle_track_lost(self, track_id: int):
        """Handle when a track is lost"""
        if track_id in self.track_identities:
            identity = self.track_identities[track_id]
            logger.debug(f"⚠️  Track lost: {identity['name']} (Track {track_id})")
        
        # Keep identity for potential recovery (don't delete immediately)
    
    def cleanup_old_tracks(self, active_track_ids: set):
        """Clean up tracks that are no longer active"""
        all_track_ids = set(self.track_identities.keys())
        inactive_tracks = all_track_ids - active_track_ids
        
        for track_id in inactive_tracks:
            if track_id in self.track_identities:
                del self.track_identities[track_id]
            if track_id in self.track_history:
                del self.track_history[track_id]
            if track_id in self.track_frame_count:
                del self.track_frame_count[track_id]
    
    def reset_session(self):
        """Reset session state"""
        logger.info("🔄 Resetting recognition engine session...")
        
        self.track_identities.clear()
        self.track_history.clear()
        self.track_frame_count.clear()
        self.unknown_counter = 0
        
        logger.info("✅ Recognition engine session reset")
    
    def get_statistics(self) -> Dict:
        """Get detailed performance statistics"""
        avg_embedding_time = self.total_embedding_time_ms / max(1, self.total_recognitions)
        avg_search_time = self.total_search_time_ms / max(1, self.total_recognitions)
        avg_total_time = self.total_recognition_time_ms / max(1, self.total_recognitions)
        
        cache_stats = self.cache.get_statistics()
        
        return {
            'total_recognitions': self.total_recognitions,
            'avg_embedding_time_ms': round(avg_embedding_time, 2),
            'avg_search_time_ms': round(avg_search_time, 2),
            'avg_total_time_ms': round(avg_total_time, 2),
            'active_tracks': len(self.track_identities),
            'registered_tracks': sum(1 for i in self.track_identities.values() if i['is_registered']),
            'unknown_tracks': sum(1 for i in self.track_identities.values() if not i['is_registered']),
            'cache_stats': cache_stats
        }


# Global recognition engine
_recognition_engine = None


def get_recognition_engine(face_app=None, confidence_threshold: float = 0.60) -> RecognitionEngine:
    """Get or create global recognition engine"""
    global _recognition_engine
    
    if _recognition_engine is None and face_app is not None:
        _recognition_engine = RecognitionEngine(face_app, confidence_threshold)
    
    return _recognition_engine


def initialize_recognition_engine(face_app, confidence_threshold: float = 0.60) -> RecognitionEngine:
    """
    Initialize recognition engine at startup
    CRITICAL: Call this once when server starts
    """
    global _recognition_engine
    
    logger.info("🚀 Initializing recognition engine...")
    
    _recognition_engine = RecognitionEngine(face_app, confidence_threshold)
    
    logger.info("✅ Recognition engine initialized")
    
    return _recognition_engine
