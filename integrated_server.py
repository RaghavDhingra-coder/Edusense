"""
Integrated Flask Server for EduSence AI
Combines camera streaming, detection, tracking, and analytics in one unified dashboard

SESSION ISOLATION FIX: All per-user state is now keyed by Flask session ID.
Global variables (camera_system, current_session_id, analytics_engine, etc.)
have been replaced with a per-user dict (user_sessions) so concurrent users
never see each other's uploads, progress, or results.
"""

from flask import Flask, jsonify, request, send_from_directory, Response, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import logging
import uuid
import secrets
from datetime import datetime
import cv2
import threading
import time
from queue import Queue
import numpy as np
import shutil
from pathlib import Path

# Import existing components - NO CHANGES TO LOGIC
from face_detector import FaceDetector
from image_manager import ImageManager
from face_reid import FaceReID
from hybrid_attentiveness import HybridAttentivenessAnalyzer
from student_registry import StudentRegistry
from face_reid_recognition import FaceReIDWithRecognition
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='frontend', static_url_path='')

# SESSION ISOLATION FIX: secret key required for signed session cookies
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# SESSION ISOLATION FIX + CLOUDFLARE: cookie settings for HTTPS proxy environments.
# Cloudflare terminates TLS, so the browser sees HTTPS but Flask runs on HTTP internally.
# Secure=True works because Cloudflare always forwards via HTTPS to clients.
# SameSite=Lax allows cookies on top-level navigations (normal browser usage).
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configure CORS - allow all origins since the app is served via Cloudflare public URL.
# The frontend is served from the same origin as the API, so CORS headers are only
# needed for any future cross-origin callers.
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm'}
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# SESSION ISOLATION FIX: replaces bare globals (camera_system, current_session_id,
# video_processing_active, analytics_engine).  Keyed by browser session UUID.
user_sessions = {}
user_sessions_lock = threading.Lock()

# Per-webcam-session processors (already existed; unchanged)
session_processors = {}
session_lock = threading.Lock()

# Student registry — shared/global is fine; it is read-only during recognition
student_registry = StudentRegistry(registry_dir='registered_students')
logger.info(f"📚 Loaded {len(student_registry.students)} registered students")

# InsightFace — global, shared for recognition (thread-safe reads)
try:
    import insightface
    from insightface.app import FaceAnalysis

    logger.info("🔄 Initializing InsightFace for student registry...")
    face_app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
    face_app.prepare(ctx_id=0, det_size=(160, 160))
    student_registry.set_face_app(face_app)
    logger.info("✅ InsightFace initialized for student registry")

except Exception as e:
    logger.error(f"⚠️  InsightFace initialization failed: {e}")
    logger.warning("   Student registration will not work without InsightFace")
    logger.warning("   Install with: pip3 install insightface onnxruntime")


# ============================================================================
# SESSION ISOLATION FIX: per-browser session helpers
# ============================================================================

@app.before_request
def ensure_session():
    """SESSION ISOLATION FIX: assign a unique UUID to every new browser."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())


def get_session_id():
    """SESSION ISOLATION FIX: return the current browser's session UUID."""
    return session['session_id']


def get_session_base_dir():
    """SESSION ISOLATION FIX: per-browser upload/data directory."""
    d = Path('sessions') / get_session_id()
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_user_state():
    """
    SESSION ISOLATION FIX: return (and lazily create) the mutable state dict
    for the current browser session.  All video-processing state lives here.
    """
    sid = get_session_id()
    with user_sessions_lock:
        if sid not in user_sessions:
            user_sessions[sid] = {
                'camera_system': None,
                'current_session_id': None,
                'video_processing_active': False,
                'analytics_engine': None,
                'last_activity': time.time(),
                # MODE FIX: tracks whether the user is in 'idle', 'camera', or 'video' mode
                # so /api/camera/status can return the correct shape without reading stale
                # video CameraSystem data when the user is actually in webcam mode.
                'mode': 'idle',
                # WEBCAM ANALYTICS FIX: directory that the analytics engine should scan.
                # Set by start_camera() for webcam and by process_video() for uploaded
                # videos.  Never cleared on stop so Analyze Classroom works after both
                # modes.
                'analytics_dir': None,
            }
        else:
            user_sessions[sid]['last_activity'] = time.time()
        return user_sessions[sid]


def _cleanup_user_sessions(max_age_seconds=7200):
    """SESSION ISOLATION FIX: evict user state that has been idle too long."""
    with user_sessions_lock:
        now = time.time()
        stale = [
            sid for sid, state in user_sessions.items()
            if now - state.get('last_activity', 0) > max_age_seconds
        ]
        for sid in stale:
            cam = user_sessions[sid].get('camera_system')
            if cam and cam.running:
                cam.stop()
            del user_sessions[sid]
            logger.info(f"🧹 Evicted stale user session: {sid[:8]}...")
        return len(stale)


def _session_gc_worker():
    while True:
        time.sleep(600)
        try:
            n = _cleanup_user_sessions()
            if n:
                logger.info(f"🧹 Session GC removed {n} stale user session(s)")
        except Exception as e:
            logger.error(f"Session GC error: {e}")


threading.Thread(target=_session_gc_worker, daemon=True).start()

# ============================================================================
# END session isolation helpers
# ============================================================================


# WEBCAM RECOGNITION FIX: SessionProcessor now mirrors the CameraSystem pipeline
# exactly.  The original version had three bugs that caused every face to show
# as "Unknown":
#   1. Called student_registry.search_face() — method does not exist.
#      (real method: recognize_face(); error was silently swallowed by try/except)
#   2. Read result['name'] / result['similarity'] — wrong keys.
#      (real keys: 'student_name' / 'confidence')
#   3. Used detect_faces() (no track IDs) — FaceReIDWithRecognition needs stable
#      track IDs across frames for its recognition cache to work.
#   Additionally: no FaceReIDWithRecognition, no ImageManager, so student counts
#   and image saving were structurally impossible.
class SessionProcessor:
    """
    WEBCAM RECOGNITION FIX: Per-webcam-session processor that uses the same
    recognition pipeline as CameraSystem (video mode):
      - FaceDetector.track_faces()  →  stable track IDs for the ReID cache
      - FaceReIDWithRecognition     →  cached InsightFace recognition
      - ImageManager               →  saves face crops for recognized students
    """

    def __init__(self, session_id):
        self.session_id = session_id
        self.session_dir = os.path.join('sessions', session_id)
        os.makedirs(self.session_dir, exist_ok=True)

        # WEBCAM RECOGNITION FIX: same detector as CameraSystem
        self.face_detector = FaceDetector()

        # WEBCAM RECOGNITION FIX: full ReID + recognition pipeline, same as CameraSystem
        if config.ENABLE_REID:
            self.reid_system = FaceReIDWithRecognition(
                student_registry=student_registry,
                similarity_threshold=config.REID_SIMILARITY_THRESHOLD,
                embedding_size=512
            )
            self.reid_system.reset_session()
            logger.info(
                f"# WEBCAM RECOGNITION FIX: ReID system initialised for session "
                f"{session_id} — {len(student_registry.students)} registered students loaded"
            )
        else:
            self.reid_system = None
            logger.warning("# WEBCAM RECOGNITION FIX: ENABLE_REID=False — falling back to direct registry search")

        # WEBCAM RECOGNITION FIX: ImageManager writes face crops to the session dir
        self.image_manager = ImageManager(self.session_dir)

        # Track IDs visible in the most recent frame (for lost-track cleanup)
        self.active_tracks = set()

        # Per-session stats
        self.frame_count = 0
        self.detection_count = 0
        self.students_seen = set()   # identity IDs of recognised registered students
        self.last_activity = time.time()

        logger.info(f"✅ SessionProcessor created for {session_id}")

    def process_frame(self, frame):
        """
        WEBCAM RECOGNITION FIX: mirrors CameraSystem._process_frame() exactly
        but returns a JSON-serialisable list of detection dicts instead of an
        annotated numpy frame so the JS canvas overlay can draw them.
        """
        self.frame_count += 1
        self.last_activity = time.time()
        current_time = time.time()

        detections = []

        # WEBCAM RECOGNITION FIX: use track_faces (not detect_faces) so every
        # face has a stable track_id across frames — required by the ReID cache.
        debug = self.frame_count <= 5
        raw_tracks = self.face_detector.track_faces(frame, self.frame_count, debug=debug)
        current_tracks = set()

        # WEBCAM RECOGNITION FIX: debug log on first frame and every 30 thereafter
        if self.frame_count == 1 or self.frame_count % 30 == 0:
            logger.info(
                f"# WEBCAM RECOGNITION FIX: session={self.session_id[:16]} "
                f"frame={self.frame_count} raw_tracks={len(raw_tracks)} "
                f"registered_students={len(student_registry.students)}"
            )

        for track in raw_tracks:
            x1, y1, x2, y2, track_id, confidence, track_age = track
            current_tracks.add(track_id)

            bbox_tuple = (x1, y1, x2, y2)
            if not self.face_detector.is_valid_face_detection(bbox_tuple, confidence):
                continue

            face_crop = self.image_manager.crop_face(frame, bbox_tuple)
            if face_crop is None:
                continue

            name = f"Unknown"
            recog_confidence = 0.0
            is_registered = False
            identity_id = str(track_id)

            if self.reid_system and config.ENABLE_REID:
                # WEBCAM RECOGNITION FIX: identical call to CameraSystem._process_frame()
                identity_id, identity_name, is_new, conf, is_reg = \
                    self.reid_system.register_or_match_face(
                        track_id, face_crop, current_time, force_extract=False
                    )

                name = identity_name
                recog_confidence = conf
                is_registered = is_reg

                # WEBCAM RECOGNITION FIX: debug log for every recognition result
                if self.frame_count <= 5 or is_new:
                    logger.info(
                        f"# WEBCAM RECOGNITION FIX: track={track_id} "
                        f"name={identity_name} is_registered={is_reg} "
                        f"confidence={conf:.3f} is_new={is_new}"
                    )

                if is_registered:
                    # Save face crop and track unique students — same as CameraSystem
                    self.image_manager.save_face_image(frame, bbox_tuple, identity_id, confidence)
                    self.students_seen.add(identity_id)

            else:
                # WEBCAM RECOGNITION FIX: ReID disabled — call recognize_face() directly
                # (fixes the original bug: search_face does not exist; wrong key names)
                try:
                    result = student_registry.recognize_face(face_crop)
                    if result:
                        name = result['student_name']      # FIXED: was result['name']
                        recog_confidence = result['confidence']  # FIXED: was result['similarity']
                        is_registered = True
                        identity_id = result['student_id']
                        logger.info(
                            f"# WEBCAM RECOGNITION FIX: direct match "
                            f"name={name} confidence={recog_confidence:.3f}"
                        )
                        self.image_manager.save_face_image(frame, bbox_tuple, identity_id, confidence)
                        self.students_seen.add(identity_id)
                except Exception as e:
                    logger.error(f"# WEBCAM RECOGNITION FIX: direct recognition error: {e}")

            detections.append({
                'bbox': [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],
                'name': name,
                'confidence': float(recog_confidence),
                'is_registered': is_registered
            })

        # WEBCAM RECOGNITION FIX: clean up lost tracks in the ReID cache
        if self.reid_system and config.ENABLE_REID:
            for lost_track in (self.active_tracks - current_tracks):
                self.reid_system.handle_track_lost(lost_track)
            if self.frame_count % 100 == 0:
                self.reid_system.cleanup_old_tracks(current_time, timeout=30.0)

        self.active_tracks = current_tracks
        self.detection_count += len(detections)

        # WEBCAM RECOGNITION FIX: summary log every 30 frames
        if self.frame_count % 30 == 0:
            registered_in_frame = sum(1 for d in detections if d['is_registered'])
            img_stats = self.image_manager.get_statistics()
            logger.info(
                f"# WEBCAM RECOGNITION FIX: frame={self.frame_count} "
                f"faces={len(detections)} registered_in_frame={registered_in_frame} "
                f"unique_students_seen={len(self.students_seen)} "
                f"images_saved={img_stats.get('total_images', 0)}"
            )

        return detections

    def get_stats(self):
        img_stats = self.image_manager.get_statistics()
        return {
            'frame_count': self.frame_count,
            'detection_count': self.detection_count,
            'students_count': len(self.students_seen),
            'images_saved': img_stats.get('total_images', 0),
            'last_activity': self.last_activity,
        }


def get_or_create_session_processor(session_id):
    with session_lock:
        if session_id not in session_processors:
            session_processors[session_id] = SessionProcessor(session_id)
        return session_processors[session_id]


def cleanup_inactive_sessions(max_age_seconds=3600):
    with session_lock:
        current_time = time.time()
        inactive = [
            sid for sid, p in session_processors.items()
            if current_time - p.last_activity > max_age_seconds
        ]
        for sid in inactive:
            logger.info(f"🧹 Cleaning up inactive webcam session: {sid}")
            del session_processors[sid]
        return len(inactive)


def generate_session_id(prefix="session"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_session_dir(session_id):
    return os.path.join('sessions', session_id)


def clear_temp_session_data(session_dir):
    try:
        if os.path.exists(session_dir):
            logger.info(f"🧹 Clearing temporary session data: {session_dir}")
            shutil.rmtree(session_dir)
        os.makedirs(session_dir, exist_ok=True)
        logger.info(f"📁 Created fresh session directory: {session_dir}")
    except Exception as e:
        logger.error(f"❌ Failed to clear session data: {e}")
        raise


class CameraSystem:
    """
    Camera processing system — PRESERVES ALL EXISTING LOGIC.

    SESSION ISOLATION FIX: uses a per-instance lock (self._camera_lock) instead
    of the old module-level camera_lock so multiple users can start/stop their
    own cameras independently without blocking each other.
    """

    def __init__(self, video_source=0, session_id=None, is_video_file=False):
        self.video_source = video_source
        self.is_video_file = is_video_file
        self.session_id = session_id or generate_session_id()
        self.session_dir = get_session_dir(self.session_id)

        self.running = False
        self.thread = None
        self.frame_queue = Queue(maxsize=2)
        self.latest_frame = None
        self.frame_lock = threading.Lock()

        # SESSION ISOLATION FIX: per-instance lock (was a shared global)
        self._camera_lock = threading.Lock()

        self.frame_number = 0
        self.active_tracks = set()
        self.fps = 0
        self.last_fps_time = time.time()
        self.fps_counter = 0

        self.total_frames = 0
        self.processing_complete = False
        self.processing_error = None

        self.detector = None
        self.image_manager = None
        self.reid_system = None
        self.cap = None

        logger.info("=" * 60)
        logger.info(f"🎓 Initializing Camera System - Session: {self.session_id}")
        logger.info("=" * 60)

        self._prepare_session()
        self._initialize_components()

    def _prepare_session(self):
        logger.info("🔄 Preparing new session...")
        clear_temp_session_data(self.session_dir)
        logger.info("✅ Session prepared")

    def _initialize_components(self):
        try:
            logger.info("📦 Initializing components...")
            self.detector = FaceDetector()
            self.image_manager = ImageManager(self.session_dir)

            if config.ENABLE_REID:
                logger.info("🔄 Initializing Face Re-Identification with Recognition...")
                self.reid_system = FaceReIDWithRecognition(
                    student_registry=student_registry,
                    similarity_threshold=config.REID_SIMILARITY_THRESHOLD,
                    embedding_size=512
                )
                self.reid_system.reset_session()
                logger.info(f"✅ Recognition enabled with {len(student_registry.students)} registered students")
            else:
                logger.info("⚠️  Face ReID disabled")
                self.reid_system = None

            logger.info("✅ Components initialized")
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise

    def start(self):
        with self._camera_lock:
            if self.running:
                logger.warning("Processing already running")
                return False

            try:
                if self.video_source is None:
                    self.processing_error = "Video source is None"
                    logger.error(f"[CAMERA] ❌ {self.processing_error}")
                    return False

                if self.is_video_file:
                    logger.info(f"[VIDEO] Opening video file: {self.video_source}")
                    logger.info(f"[VIDEO] File exists: {os.path.exists(self.video_source)}")
                else:
                    logger.info("[CAMERA] Opening camera...")

                self.cap = cv2.VideoCapture(self.video_source)
                if not self.cap.isOpened():
                    self.processing_error = (
                        f"Failed to open {'video file' if self.is_video_file else 'camera'}: "
                        f"{self.video_source}"
                    )
                    logger.error(f"[CAMERA] ❌ {self.processing_error}")
                    return False

                if self.is_video_file:
                    self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    video_fps = self.cap.get(cv2.CAP_PROP_FPS)
                    width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    logger.info(f"[VIDEO] ✅ {width}x{height}, {video_fps:.1f} FPS, {self.total_frames} frames")
                else:
                    logger.info("[CAMERA] ✅ Camera opened successfully")
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)

                ret, test_frame = self.cap.read()
                if not ret or test_frame is None:
                    self.processing_error = (
                        f"Failed to read test frame from "
                        f"{'video file' if self.is_video_file else 'camera'}"
                    )
                    logger.error(f"[CAMERA] ❌ {self.processing_error}")
                    self.cap.release()
                    return False

                logger.info(f"[CAMERA] ✅ Test frame captured: {test_frame.shape}")

                if self.is_video_file:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

                self.running = True
                self.frame_number = 0
                self.active_tracks = set()
                self.processing_complete = False
                self.processing_error = None

                self.thread = threading.Thread(target=self._process_loop, daemon=True)
                self.thread.start()

                logger.info("[CAMERA] ✅ Processing thread started")
                logger.info("=" * 60)
                return True

            except Exception as e:
                self.processing_error = f"Failed to start: {str(e)}"
                logger.error(f"[CAMERA] ❌ {self.processing_error}")
                import traceback
                traceback.print_exc()
                return False

    def stop(self):
        with self._camera_lock:
            if not self.running:
                return False
            self.running = False
            if self.thread:
                self.thread.join(timeout=2.0)
            if self.cap:
                self.cap.release()
                self.cap = None
            source_type = "video" if self.is_video_file else "camera"
            logger.info(f"🛑 {source_type.capitalize()} stopped")
            return True

    def _process_loop(self):
        logger.info("[STREAM] 🚀 Processing loop started")
        frame_count = 0
        try:
            while self.running:
                ret, frame = self.cap.read()

                if not ret or frame is None:
                    if self.is_video_file:
                        logger.info("[STREAM] ✅ Video processing complete")
                        self.processing_complete = True
                        self.running = False
                        break
                    else:
                        logger.warning("[STREAM] ⚠️ Failed to read frame")
                        time.sleep(0.1)
                        continue

                frame_count += 1
                if frame_count % 30 == 0:
                    logger.info(f"[STREAM] Frame {frame_count} captured: {frame.shape}")

                processed_frame = self._process_frame(frame)

                with self.frame_lock:
                    self.latest_frame = processed_frame.copy()

                self._update_fps()

                if not self.is_video_file:
                    time.sleep(0.01)

        except Exception as e:
            logger.error(f"[STREAM] ❌ Processing loop error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            logger.info(f"[STREAM] Processing loop stopped — {frame_count} frames")

    def _process_frame(self, frame):
        self.frame_number += 1
        current_time = time.time()
        debug = self.frame_number <= 50

        detections = self.detector.track_faces(frame, self.frame_number, debug=debug)
        current_tracks = set()
        reid_detections = []

        for detection in detections:
            x1, y1, x2, y2, track_id, confidence, track_age = detection
            current_tracks.add(track_id)

            bbox = (x1, y1, x2, y2)
            if not self.detector.is_valid_face_detection(bbox, confidence):
                continue

            face_crop = self.image_manager.crop_face(frame, bbox)
            if face_crop is None:
                continue

            if self.reid_system and config.ENABLE_REID:
                identity_id, identity_name, is_new, confidence_score, is_registered = \
                    self.reid_system.register_or_match_face(
                        track_id, face_crop, current_time, force_extract=False
                    )
                if is_registered:
                    if is_new:
                        logger.info(f"✅ Recognized: {identity_name} (Track {track_id})")
                    self.image_manager.save_face_image(frame, bbox, identity_id, confidence)
                    reid_detections.append((x1, y1, x2, y2, identity_id, confidence, identity_name, True))
                else:
                    reid_detections.append((x1, y1, x2, y2, track_id, confidence, identity_name, False))
            else:
                self.image_manager.save_face_image(frame, bbox, track_id, confidence)
                reid_detections.append((x1, y1, x2, y2, track_id, confidence, f"Student {track_id}", True))

        if self.reid_system and config.ENABLE_REID:
            for lost_track in (self.active_tracks - current_tracks):
                self.reid_system.handle_track_lost(lost_track)
            if self.frame_number % 100 == 0:
                self.reid_system.cleanup_old_tracks(current_time, timeout=30.0)

        self.active_tracks = current_tracks
        annotated_frame = self._draw_detections(frame, reid_detections)
        annotated_frame = self._draw_info_overlay(annotated_frame, len(reid_detections))
        return annotated_frame

    def _draw_detections(self, frame, detections):
        for detection in detections:
            if len(detection) == 8:
                x1, y1, x2, y2, student_id, confidence, student_name, is_registered = detection
            else:
                x1, y1, x2, y2, student_id, confidence = detection
                student_name = f"Student {student_id}"
                is_registered = True

            color = (0, 255, 0) if is_registered else (0, 165, 255)
            label = student_name if is_registered else "Unknown Person"

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame,
                          (int(x1), int(y1) - label_size[1] - 10),
                          (int(x1) + label_size[0], int(y1)),
                          color, -1)
            cv2.putText(frame, label, (int(x1), int(y1) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            cv2.putText(frame, f"{confidence:.2f}", (int(x1), int(y2) + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return frame

    def _draw_info_overlay(self, frame, num_faces):
        stats = self.image_manager.get_statistics()
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 80), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Faces: {num_faces}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Students: {stats['total_students']}", (200, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
        cv2.putText(frame, f"Images: {stats['total_images']}", (200, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        return frame

    def _update_fps(self):
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.fps_counter / (current_time - self.last_fps_time)
            self.fps_counter = 0
            self.last_fps_time = current_time

    def get_frame(self):
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None

    def get_stats(self):
        stats = self.image_manager.get_statistics()
        stats['fps'] = self.fps
        stats['frame_number'] = self.frame_number
        stats['active_tracks'] = len(self.active_tracks)
        stats['running'] = self.running
        stats['is_video_file'] = self.is_video_file
        stats['total_frames'] = self.total_frames
        stats['processing_complete'] = self.processing_complete
        stats['processing_error'] = self.processing_error
        stats['progress_percent'] = (
            (self.frame_number / self.total_frames * 100) if self.total_frames > 0 else 0
        )
        return stats


def get_analytics_engine(user_state):
    """
    SESSION ISOLATION FIX: create a fresh analytics engine scoped to this
    user's session directory, then cache it in user_state.
    WEBCAM ANALYTICS FIX: prefer analytics_dir (set by both start_camera and
    process_video, never cleared on stop) over the legacy cam_sys path.
    """
    # WEBCAM ANALYTICS FIX: analytics_dir is the authoritative source for where
    # face crops were saved.  It is set at session start and kept after stop.
    analytics_dir = user_state.get('analytics_dir')
    if analytics_dir and os.path.exists(analytics_dir):
        students_dir = analytics_dir
    else:
        # Legacy fallback for sessions created before this fix
        current_session_id = user_state.get('current_session_id')
        cam_sys = user_state.get('camera_system')
        students_dir = get_session_dir(current_session_id) if (cam_sys and current_session_id) else 'students'

    logger.info(f"📊 Creating analytics engine for: {students_dir}")
    engine = HybridAttentivenessAnalyzer(
        students_dir=students_dir,
        focus_threshold=0.65,
        yaw_threshold=30.0,
        pitch_threshold=30.0,
        roll_threshold=35.0,
        consecutive_distraction_threshold=2
    )
    user_state['analytics_engine'] = engine
    return engine


def generate_frames(browser_session_id):
    """
    SESSION ISOLATION FIX: MJPEG generator scoped to one browser session.
    browser_session_id is captured at request time so the generator always
    reads the correct camera regardless of what other users are doing.
    """
    frame_count = 0
    logger.info(f"[MJPEG] Stream started for session {browser_session_id[:8]}...")

    while True:
        # SESSION ISOLATION FIX: look up only THIS user's camera
        with user_sessions_lock:
            state = user_sessions.get(browser_session_id, {})
            cam_sys = state.get('camera_system')

        frame = cam_sys.get_frame() if cam_sys is not None else None

        if frame is None:
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Camera Not Started", (150, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            frame = placeholder
        else:
            frame_count += 1
            if frame_count % 30 == 0:
                logger.info(f"[MJPEG] session={browser_session_id[:8]} frame={frame_count}")

        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            logger.warning("[MJPEG] ⚠️ Failed to encode frame")
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        time.sleep(0.033)  # ~30 FPS


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    return send_from_directory('frontend', 'index_integrated.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)


@app.route('/api/video_feed')
def video_feed():
    """
    SESSION ISOLATION FIX: capture session_id at request time and pass it
    into the generator so each user streams only their own camera feed.
    """
    browser_session_id = get_session_id()
    return Response(generate_frames(browser_session_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/camera/start', methods=['POST'])
@app.route('/camera/start', methods=['POST'])
def start_camera():
    """Start a client-side webcam session (per-user, already isolated)."""
    try:
        browser_session_id = (request.headers.get('X-Session-ID') or
                              request.headers.get('X-Browser-Session'))

        logger.info("=" * 60)
        logger.info("🎥 Starting new client-side webcam session...")
        if browser_session_id:
            logger.info(f"🆔 Browser Session ID: {browser_session_id}")
        logger.info("=" * 60)

        if browser_session_id:
            new_session_id = f"webcam_{browser_session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            new_session_id = generate_session_id("webcam")

        processor = get_or_create_session_processor(new_session_id)
        cleanup_inactive_sessions(max_age_seconds=3600)

        # MODE FIX: mark this browser as being in live-webcam mode so
        # /api/camera/status does not return stale video-file progress.
        user_state = get_user_state()
        user_state['mode'] = 'camera'
        # WEBCAM ANALYTICS FIX: record session dir so Analyze Classroom works after Stop Camera.
        # We set this now (not on stop) because the processor is deleted on stop and the dir
        # path would be lost.
        user_state['analytics_dir'] = processor.session_dir
        logger.info(f"# WEBCAM ANALYTICS FIX: camera session created: {processor.session_dir}")

        logger.info(f"✅ Client-side session created: {new_session_id}")
        logger.info(f"👥 Active webcam sessions: {len(session_processors)}")
        logger.info("=" * 60)

        return jsonify({
            'success': True,
            'message': 'Session created for client-side webcam',
            'session_id': new_session_id,
            'session_dir': processor.session_dir,
            'source_type': 'webcam_client',
            'browser_session_id': browser_session_id
        })

    except Exception as e:
        logger.error(f"Start camera error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/process_frame', methods=['POST'])
@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Process a single webcam frame (stateless per session)."""
    try:
        browser_session_id = (request.headers.get('X-Session-ID') or
                              request.headers.get('X-Browser-Session'))

        if 'frame' not in request.files:
            return jsonify({'success': False, 'message': 'No frame provided'}), 400

        frame_file = request.files['frame']
        session_id = request.form.get('session_id')

        if not session_id:
            return jsonify({'success': False, 'message': 'No session_id provided'}), 400

        nparr = np.frombuffer(frame_file.read(), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({'success': False, 'message': 'Failed to decode frame'}), 400

        processor = get_or_create_session_processor(session_id)

        if processor.frame_count % 30 == 0:
            logger.info(
                f"📸 Processing frame for session {session_id[:20]}... "
                f"(browser: {browser_session_id[:8] if browser_session_id else 'none'})"
            )

        detections = processor.process_frame(frame)

        return jsonify({
            'success': True,
            'detections': detections,
            'session_id': session_id,
            'frame_count': processor.frame_count
        })

    except Exception as e:
        logger.error(f"Process frame error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/video/upload', methods=['POST'])
def upload_video():
    """
    Upload a video file.
    SESSION ISOLATION FIX: saved to sessions/<browser_session_id>/uploads/
    so each user's uploads are stored in their own directory.
    """
    try:
        logger.info("=" * 60)
        logger.info("📤 Video upload request received")
        logger.info("=" * 60)

        if 'video' not in request.files:
            return jsonify({'success': False, 'error': 'No video file provided'}), 400

        file = request.files['video']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"

        # SESSION ISOLATION FIX: per-user upload directory
        user_upload_dir = get_session_base_dir() / 'uploads'
        user_upload_dir.mkdir(parents=True, exist_ok=True)

        filepath = str((user_upload_dir / filename).resolve())
        upload_dir_abs = str(user_upload_dir.resolve())

        # Security: prevent path traversal
        if not filepath.startswith(upload_dir_abs):
            return jsonify({'success': False, 'error': 'Invalid file path'}), 400

        file.save(filepath)

        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'Failed to save file'}), 500

        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)

        if file_size > MAX_UPLOAD_SIZE:
            os.remove(filepath)
            return jsonify({
                'success': False,
                'error': f'File too large: {file_size_mb:.2f} MB (max: {MAX_UPLOAD_SIZE/(1024*1024)} MB)'
            }), 400

        try:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                cap.release()
                os.remove(filepath)
                return jsonify({'success': False, 'error': 'File is not a valid video'}), 400
            cap.release()
        except Exception:
            os.remove(filepath)
            return jsonify({'success': False, 'error': 'Invalid video file'}), 400

        logger.info(f"✅ Video uploaded: {filename} ({file_size_mb:.2f} MB) → {filepath}")

        return jsonify({
            'success': True,
            'message': 'Video uploaded successfully',
            'filename': filename,
            'filepath': filepath,
            'size_mb': round(file_size_mb, 2)
        })

    except Exception as e:
        logger.error(f"❌ Video upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/video/process', methods=['POST'])
def process_video():
    """
    Start processing an uploaded video.
    SESSION ISOLATION FIX: camera_system stored in per-user state so User B
    starting a video never overwrites User A's camera_system global.
    """
    try:
        logger.info("=" * 60)
        logger.info("🎬 VIDEO PROCESSING REQUEST RECEIVED")
        logger.info("=" * 60)

        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

        if 'filepath' not in data:
            return jsonify({'success': False, 'error': 'No filepath provided'}), 400

        filepath = data['filepath']

        if not filepath or not isinstance(filepath, str) or not filepath.strip():
            return jsonify({'success': False, 'error': 'Invalid filepath'}), 400

        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': f'Video file not found: {filepath}'}), 404

        if not os.path.isfile(filepath):
            return jsonify({'success': False, 'error': f'Path is not a file: {filepath}'}), 400

        logger.info(f"✅ File validated: {filepath} ({os.path.getsize(filepath)/(1024*1024):.2f} MB)")

        # SESSION ISOLATION FIX: touch only THIS user's state
        user_state = get_user_state()

        existing_cam = user_state.get('camera_system')
        if existing_cam and existing_cam.running:
            logger.info("🛑 Stopping this user's previous session...")
            existing_cam.stop()
            time.sleep(0.5)

        new_session_id = generate_session_id("video")
        user_state['current_session_id'] = new_session_id
        user_state['video_processing_active'] = True
        # MODE FIX: mark as video mode before starting so status endpoint
        # immediately returns the correct shape on the next poll.
        user_state['mode'] = 'video'

        logger.info(f"🆕 New video session for user: {new_session_id}")

        cam = CameraSystem(video_source=filepath, session_id=new_session_id, is_video_file=True)
        user_state['camera_system'] = cam
        # WEBCAM ANALYTICS FIX: record session dir immediately so it is available even if
        # the user stops the video before calling Analyze Classroom.
        user_state['analytics_dir'] = cam.session_dir
        logger.info(f"# WEBCAM ANALYTICS FIX: video session dir: {cam.session_dir}")

        success = cam.start()

        if success:
            logger.info(f"✅ Video processing started: {cam.session_id}")
            return jsonify({
                'success': True,
                'message': 'Video processing started',
                'session_id': cam.session_id,
                'session_dir': cam.session_dir,
                'total_frames': cam.total_frames,
                'source_type': 'video',
                'video_path': filepath
            })
        else:
            error_msg = cam.processing_error or 'Failed to start video processing'
            logger.error(f"❌ Failed to start: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500

    except Exception as e:
        logger.error(f"❌ Video processing error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/video/stop', methods=['POST'])
@app.route('/video/stop', methods=['POST'])
def stop_video():
    """
    Stop video processing.
    SESSION ISOLATION FIX: stops only this user's camera.
    """
    try:
        user_state = get_user_state()
        cam = user_state.get('camera_system')

        if cam is None:
            return jsonify({'success': True, 'message': 'No video processing active'})

        cam.stop()
        user_state['video_processing_active'] = False
        # MODE FIX: return to idle so the progress bar hides immediately
        user_state['mode'] = 'idle'

        return jsonify({'success': True, 'message': 'Video processing stopped'})

    except Exception as e:
        logger.error(f"Stop video error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/camera/stop', methods=['POST'])
@app.route('/camera/stop', methods=['POST'])
def stop_camera():
    """
    Stop camera processing.
    SESSION ISOLATION FIX: handles webcam session_id (from body) and the
    per-user video camera independently.
    """
    try:
        data = request.get_json() or {}
        webcam_session_id = data.get('session_id')

        if webcam_session_id:
            saved_session_dir = None
            with session_lock:
                if webcam_session_id in session_processors:
                    logger.info(f"🛑 Stopping webcam session: {webcam_session_id}")
                    # WEBCAM ANALYTICS FIX: capture the session dir before deleting the
                    # processor so Analyze Classroom can find the face crops afterwards.
                    saved_session_dir = session_processors[webcam_session_id].session_dir
                    del session_processors[webcam_session_id]
            # WEBCAM ANALYTICS FIX: persist analytics_dir in user_state (outside the lock
            # so we don't hold session_lock while touching user_sessions_lock).
            u_state = get_user_state()
            if saved_session_dir:
                u_state['analytics_dir'] = saved_session_dir
                logger.info(f"# WEBCAM ANALYTICS FIX: camera stopped, analytics_dir retained: {saved_session_dir}")
            u_state['mode'] = 'idle'
            return jsonify({
                'success': True,
                'message': f'Session {webcam_session_id} stopped and cleaned up'
            })

        # SESSION ISOLATION FIX: fallback to this user's video camera
        user_state = get_user_state()
        cam = user_state.get('camera_system')
        if cam is not None:
            cam.stop()
            # MODE FIX: reset mode so /api/camera/status returns idle shape
            user_state['mode'] = 'idle'
            return jsonify({'success': True, 'message': 'Camera stopped'})

        # Reset mode even if there was nothing to stop (e.g. webcam-only session)
        user_state = get_user_state()
        user_state['mode'] = 'idle'
        return jsonify({'success': True, 'message': 'No active session to stop'})

    except Exception as e:
        logger.error(f"Stop camera error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/camera/status', methods=['GET'])
def camera_status():
    """
    Get camera status.
    SESSION ISOLATION FIX: returns only this user's camera state.
    MODE FIX: returns separate response shapes for 'camera', 'video', and 'idle'
    so the frontend can show/hide the progress bar correctly.
    """
    try:
        user_state = get_user_state()
        mode = user_state.get('mode', 'idle')

        if mode == 'camera':
            # WEBCAM RECOGNITION FIX: aggregate live stats from all active
            # SessionProcessors that belong to this browser session.
            # (A browser can only have one active webcam session at a time.)
            total_students = 0
            total_images = 0
            total_faces = 0
            with session_lock:
                for proc in session_processors.values():
                    sp_stats = proc.get_stats()
                    total_students += sp_stats.get('students_count', 0)
                    total_images   += sp_stats.get('images_saved', 0)
                    total_faces    += sp_stats.get('detection_count', 0)

            return jsonify({
                'success': True,
                'status': {
                    'mode': 'camera',
                    'camera_active': True,
                    'fps': 0,
                    'faces': total_faces,
                    'students': total_students,
                    'images_saved': total_images,
                }
            })

        if mode == 'video':
            cam = user_state.get('camera_system')
            if cam is None:
                # Shouldn't normally happen; treat as idle
                return jsonify({
                    'success': True,
                    'status': {'mode': 'idle', 'camera_active': False}
                })
            raw = cam.get_stats()
            return jsonify({
                'success': True,
                'status': {
                    'mode': 'video',
                    'is_processing': raw['running'],
                    'current_frame': raw['frame_number'],
                    'total_frames': raw['total_frames'],
                    'progress': raw['progress_percent'],
                    'fps': raw['fps'],
                    'active_tracks': raw['active_tracks'],
                    'total_students': raw.get('total_students', 0),
                    'total_images': raw.get('total_images', 0),
                    'processing_complete': raw['processing_complete'],
                    'processing_error': raw['processing_error'],
                }
            })

        # idle (or unknown)
        return jsonify({
            'success': True,
            'status': {
                'mode': 'idle',
                'camera_active': False,
                'fps': 0,
                'faces': 0,
                'students': 0,
                'images_saved': 0,
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """
    List available sessions.
    SESSION ISOLATION FIX: current_session reflects this user's session only.
    """
    try:
        # SESSION ISOLATION FIX: use this user's current_session_id
        user_state = get_user_state()
        current_session_id = user_state.get('current_session_id')

        sessions_dir = 'sessions'

        if not os.path.exists(sessions_dir):
            return jsonify({'success': True, 'sessions': [], 'current_session': current_session_id})

        sessions = []
        for session_folder in sorted(os.listdir(sessions_dir)):
            session_path = os.path.join(sessions_dir, session_folder)
            if os.path.isdir(session_path) and session_folder.startswith('session_'):
                student_folders = [
                    d for d in os.listdir(session_path)
                    if os.path.isdir(os.path.join(session_path, d)) and d.startswith('student_')
                ]
                total_images = sum(
                    len([f for f in os.listdir(os.path.join(session_path, folder))
                         if f.endswith(('.jpg', '.jpeg', '.png'))])
                    for folder in student_folders
                )
                sessions.append({
                    'session_id': session_folder,
                    'students': len(student_folders),
                    'images': total_images,
                    'is_current': session_folder == current_session_id
                })

        return jsonify({
            'success': True,
            'sessions': sessions,
            'current_session': current_session_id
        })

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_classroom():
    """
    Analyze all students.
    SESSION ISOLATION FIX: analytics engine is scoped to this user's data.
    """
    try:
        logger.info("=" * 60)
        logger.info("🔍 Starting classroom analysis...")
        logger.info("=" * 60)

        # SESSION ISOLATION FIX: per-user analytics engine
        user_state = get_user_state()

        # WEBCAM ANALYTICS FIX: validate that a session with face data exists before
        # running analysis.  Without this check the engine silently returns 0 students.
        analytics_dir = user_state.get('analytics_dir')
        if not analytics_dir or not os.path.exists(analytics_dir):
            return jsonify({
                'success': False,
                'error': 'No session data available for analytics. Please run the camera or upload a video first.'
            }), 400
        student_folders = [
            d for d in os.listdir(analytics_dir)
            if os.path.isdir(os.path.join(analytics_dir, d)) and d.startswith('student_')
        ]
        if not student_folders:
            return jsonify({
                'success': False,
                'error': 'No student data found in the session. No recognized faces were captured.'
            }), 400

        engine = get_analytics_engine(user_state)

        all_analytics = engine.analyze_all_students()
        logger.info(f"✅ Analyzed {len(all_analytics)} students")

        summary = engine.compute_classroom_summary(all_analytics)

        return jsonify({
            'success': True,
            'summary': summary,
            'students': all_analytics,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/student/<student_id>', methods=['GET'])
def get_student_details(student_id):
    """Get specific student details."""
    try:
        user_state = get_user_state()
        engine = get_analytics_engine(user_state)
        student_folder = os.path.join(engine.students_dir, student_id)

        if not os.path.exists(student_folder):
            return jsonify({'success': False, 'error': f'Student {student_id} not found'}), 404

        analytics = engine.analyze_student_folder(student_folder)

        if analytics is None:
            return jsonify({'success': False, 'error': f'No valid data for {student_id}'}), 404

        return jsonify({'success': True, 'student': analytics})

    except Exception as e:
        logger.error(f"Failed to get student details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    """Serve student images."""
    try:
        safe_path = os.path.normpath(filename)
        if '..' in safe_path:
            return jsonify({'error': 'Invalid path'}), 400

        if safe_path.startswith('sessions/'):
            directory = os.path.dirname(safe_path)
            filename = os.path.basename(safe_path)
        else:
            directory = os.path.dirname(os.path.join('students', safe_path))
            filename = os.path.basename(safe_path)

        return send_from_directory(directory, filename)

    except Exception as e:
        logger.error(f"Failed to serve image: {e}")
        return jsonify({'error': str(e)}), 404


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get statistics from current session.
    SESSION ISOLATION FIX: reads this user's session data only.
    """
    try:
        user_state = get_user_state()
        cam = user_state.get('camera_system')
        current_session_id = user_state.get('current_session_id')

        students_dir = (get_session_dir(current_session_id)
                        if (cam and current_session_id) else 'students')

        if not os.path.exists(students_dir):
            return jsonify({
                'success': True,
                'total_students': 0,
                'total_images': 0,
                'session_id': current_session_id
            })

        student_folders = [
            d for d in os.listdir(students_dir)
            if os.path.isdir(os.path.join(students_dir, d)) and d.startswith('student_')
        ]

        total_images = sum(
            len([f for f in os.listdir(os.path.join(students_dir, folder))
                 if f.endswith(('.jpg', '.jpeg', '.png'))])
            for folder in student_folders
        )

        return jsonify({
            'success': True,
            'total_students': len(student_folders),
            'total_images': total_images,
            'session_id': current_session_id
        })

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# STUDENT REGISTRATION ENDPOINTS
# ============================================================================

@app.route('/api/students/register', methods=['POST'])
def register_student():
    """Register a new student with face images."""
    try:
        data = request.get_json()
        student_name = data.get('student_name')
        student_id = data.get('student_id')
        face_images_b64 = data.get('face_images', [])

        logger.info(f"📝 Registration request: {student_name} ({student_id}), images: {len(face_images_b64)}")

        face_images = []
        for idx, img_b64 in enumerate(face_images_b64):
            try:
                import base64
                if ',' in img_b64:
                    img_b64 = img_b64.split(',')[1]
                img_data = base64.b64decode(img_b64)
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    face_images.append(img)
                    logger.info(f"   ✅ Image {idx+1} decoded: {img.shape}")
                else:
                    logger.warning(f"   ⚠️  Image {idx+1} decode failed")
            except Exception as e:
                logger.error(f"   ❌ Image {idx+1} error: {e}")

        if not face_images:
            return jsonify({'success': False, 'error': 'No valid images provided'}), 400

        result = student_registry.register_student(student_name, student_id, face_images)
        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/students/list', methods=['GET'])
def list_students():
    try:
        students = student_registry.get_all_students()
        return jsonify({'success': True, 'students': students, 'count': len(students)})
    except Exception as e:
        logger.error(f"❌ List students error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/students/delete/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        result = student_registry.delete_student(student_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"❌ Delete student error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/students/capture', methods=['POST'])
def capture_faces_from_camera():
    """
    Capture face images from the current camera feed.
    SESSION ISOLATION FIX: uses this user's camera system.
    """
    try:
        # SESSION ISOLATION FIX: use this user's camera
        user_state = get_user_state()
        cam = user_state.get('camera_system')

        if not cam or not cam.running:
            return jsonify({
                'success': False,
                'error': 'Camera not running. Please start camera first.'
            }), 400

        num_captures = (request.json.get('num_captures', 10) if request.json else 10)
        captured_images = []

        logger.info(f"📸 Capturing {num_captures} face images from camera...")

        for i in range(num_captures):
            frame = cam.get_frame()
            if frame is not None:
                detections = cam.detector.detect_faces(frame)
                if detections:
                    x1, y1, x2, y2, conf = detections[0]
                    face_crop = cam.image_manager.crop_face(frame, (x1, y1, x2, y2))
                    if face_crop is not None:
                        import base64
                        _, buffer = cv2.imencode('.jpg', face_crop)
                        img_b64 = base64.b64encode(buffer).decode('utf-8')
                        captured_images.append(f"data:image/jpeg;base64,{img_b64}")
                        logger.info(f"   ✅ Captured image {i+1}/{num_captures}")
            time.sleep(0.5)

        logger.info(f"✅ Captured {len(captured_images)} images")
        return jsonify({'success': True, 'images': captured_images, 'count': len(captured_images)})

    except Exception as e:
        logger.error(f"❌ Capture error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def main():
    import argparse

    parser = argparse.ArgumentParser(description="EduSence AI - Integrated Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=8080, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Debug mode')

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("🎓 EduSence AI - Integrated Server")
    logger.info("=" * 60)
    logger.info(f"🌐 Server: http://{args.host}:{args.port}")
    logger.info(f"📹 Video Stream: http://{args.host}:{args.port}/api/video_feed")
    logger.info("=" * 60)

    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == '__main__':
    main()
