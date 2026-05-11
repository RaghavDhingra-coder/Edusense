"""
Robust Configuration for Classroom Face Detection and Tracking System
Optimized for real-world classroom conditions
"""

# ============================================================================
# DETECTION CONFIGURATION
# ============================================================================

# Face Detection Thresholds
CONFIDENCE_THRESHOLD = 0.45  # Balanced for classroom (not too strict)
MIN_FACE_SIZE = 35  # Minimum face size in pixels
MIN_FACE_WIDTH = 35
MIN_FACE_HEIGHT = 35
IOU_THRESHOLD = 0.45  # IoU threshold for NMS
INFERENCE_SIZE = 640  # Standard size for real-time performance

# ============================================================================
# TRACKING CONFIGURATION - ByteTrack
# ============================================================================

TRACKER_TYPE = "bytetrack"
TRACK_HIGH_THRESH = 0.6     # High confidence threshold
TRACK_LOW_THRESH = 0.2      # Low threshold (keeps tracks alive longer)
TRACK_BUFFER = 90           # Frames to keep lost tracks (3 seconds at 30fps)
MATCH_THRESH = 0.8          # Matching threshold
MAX_AGE = 90                # Maximum frames without detection
MIN_HITS = 3                # Minimum hits before confirmed

# ============================================================================
# ROBUST REID CONFIGURATION
# ============================================================================

ENABLE_REID = True

# Matching Thresholds
REID_SIMILARITY_THRESHOLD = 0.55  # Lowered for better matching (was 0.6)
REID_MERGE_THRESHOLD = 0.65       # For post-processing folder merging
REID_SPLIT_THRESHOLD = 0.45       # For detecting mixed identities

# Hybrid Matching Weights (must sum to 1.0)
REID_EMBEDDING_WEIGHT = 0.5   # Weight for embedding similarity
REID_SPATIAL_WEIGHT = 0.3     # Weight for spatial proximity
REID_TEMPORAL_WEIGHT = 0.2    # Weight for temporal continuity

# Embedding Management
REID_MAX_EMBEDDINGS_PER_STUDENT = 10  # Rolling average with this many embeddings
REID_EMBEDDING_CACHE_DURATION = 5.0   # Cache duration in seconds
REID_EXTRACT_INTERVAL = 30            # Extract every N frames for existing tracks

# Temporal Consistency
REID_COOLDOWN_PERIOD = 3.0            # Seconds before creating new student ID
REID_LOST_TRACK_TIMEOUT = 5.0         # Grace period for lost tracks
REID_TEMPORAL_TAU = 5.0               # Time constant for temporal decay

# Quality Filtering
REID_QUALITY_THRESHOLD = 30.0         # Minimum quality score (0-100)
REID_MIN_SHARPNESS = 100.0            # Minimum Laplacian variance
REID_OUTLIER_THRESHOLD = 0.4          # Reject embeddings below this similarity

# ============================================================================
# VIDEO PROCESSING CONFIGURATION
# ============================================================================

TARGET_FPS = 15  # Process at this FPS for performance
DISPLAY_SCALE = 1.0
SKIP_FRAMES = 2  # Process every Nth frame (1 = all frames, 2 = every other)

# ============================================================================
# IMAGE SAVING CONFIGURATION
# ============================================================================

SAVE_INTERVAL = 1.5  # Save one image per 1.5 seconds per student
CROP_PADDING = 10    # Tight padding for face crops
OUTPUT_DIR = "students"
IMAGE_FORMAT = "jpg"
IMAGE_QUALITY = 95
MIN_CROP_SIZE = 40   # Minimum crop dimension

# Quality Filters for Saving
SAVE_MIN_CONFIDENCE = 0.5    # Only save high-confidence detections
SAVE_MIN_FACE_SIZE = 50      # Larger minimum for saved images
SAVE_MAX_BLUR_THRESHOLD = 150.0  # Maximum blur (Laplacian variance)

# ============================================================================
# DISPLAY CONFIGURATION
# ============================================================================

BBOX_COLOR = (0, 255, 0)  # Green
BBOX_THICKNESS = 2
TEXT_COLOR = (0, 255, 0)
TEXT_THICKNESS = 2
TEXT_FONT = 0  # cv2.FONT_HERSHEY_SIMPLEX
TEXT_SCALE = 0.7
FPS_COLOR = (0, 0, 255)

# Debug Display
SHOW_DEBUG_OVERLAY = True
DEBUG_OVERLAY_DURATION = 100  # Show debug for first N frames

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

YOLO_MODEL = "yolov8n-face.pt"
DEVICE = "cpu"  # "cuda:0" for GPU
USE_HALF_PRECISION = False  # FP16 for GPU

# InsightFace Model
INSIGHTFACE_MODEL = "buffalo_s"  # Lightweight model
INSIGHTFACE_DET_SIZE = (160, 160)

# ============================================================================
# POST-PROCESSING CONFIGURATION
# ============================================================================

# Folder Cleanup
CLEANUP_MIN_IMAGES = 3        # Minimum images to keep folder
CLEANUP_MERGE_THRESHOLD = 0.65  # Similarity for merging folders
CLEANUP_SPLIT_THRESHOLD = 0.45  # Threshold for splitting mixed folders
CLEANUP_MAX_IMAGES_SAMPLE = 20  # Max images to sample per folder

# DBSCAN Clustering (for mixed identity detection)
DBSCAN_EPS = 0.6              # Maximum distance between samples
DBSCAN_MIN_SAMPLES = 2        # Minimum samples in cluster

# ============================================================================
# PERFORMANCE OPTIMIZATION
# ============================================================================

# Memory Management
MAX_TRACK_HISTORY = 30        # Keep last N positions per track
CLEANUP_INTERVAL = 100        # Clean up old data every N frames

# Batch Processing
BATCH_EMBEDDING_EXTRACTION = False  # Extract embeddings in batches
BATCH_SIZE = 4

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_NEW_STUDENTS = True
LOG_REID_MATCHES = True
LOG_TRACK_LOSSES = True
LOG_QUALITY_REJECTIONS = False  # Can be verbose

# ============================================================================
# EXPERIMENTAL FEATURES
# ============================================================================

# Advanced Features (set to False if causing issues)
USE_MOTION_PREDICTION = False  # Predict next position based on velocity
USE_APPEARANCE_HISTORY = True  # Track appearance changes over time
USE_ADAPTIVE_THRESHOLDS = False  # Adjust thresholds based on scene

# ============================================================================
# PRESETS
# ============================================================================

def apply_preset(preset_name):
    """
    Apply configuration preset
    
    Presets:
    - 'fast': Optimized for speed (lower quality)
    - 'balanced': Balance between speed and accuracy (default)
    - 'accurate': Optimized for accuracy (slower)
    - 'hackathon': Quick demo mode
    """
    global CONFIDENCE_THRESHOLD, INFERENCE_SIZE, TARGET_FPS
    global REID_SIMILARITY_THRESHOLD, REID_MAX_EMBEDDINGS_PER_STUDENT
    global SKIP_FRAMES, SAVE_INTERVAL
    
    if preset_name == 'fast':
        CONFIDENCE_THRESHOLD = 0.5
        INFERENCE_SIZE = 416
        TARGET_FPS = 20
        SKIP_FRAMES = 3
        REID_MAX_EMBEDDINGS_PER_STUDENT = 5
        SAVE_INTERVAL = 2.0
        print("⚡ Applied 'fast' preset")
    
    elif preset_name == 'accurate':
        CONFIDENCE_THRESHOLD = 0.4
        INFERENCE_SIZE = 640
        TARGET_FPS = 10
        SKIP_FRAMES = 1
        REID_MAX_EMBEDDINGS_PER_STUDENT = 15
        SAVE_INTERVAL = 1.0
        REID_SIMILARITY_THRESHOLD = 0.6
        print("🎯 Applied 'accurate' preset")
    
    elif preset_name == 'hackathon':
        CONFIDENCE_THRESHOLD = 0.45
        INFERENCE_SIZE = 640
        TARGET_FPS = 15
        SKIP_FRAMES = 2
        REID_COOLDOWN_PERIOD = 2.0
        SAVE_INTERVAL = 1.0
        print("🚀 Applied 'hackathon' preset")
    
    elif preset_name == 'balanced':
        # Already set as defaults
        print("⚖️  Applied 'balanced' preset (default)")
    
    else:
        print(f"⚠️  Unknown preset: {preset_name}")


# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration parameters"""
    errors = []
    
    # Check weights sum to 1.0
    weight_sum = REID_EMBEDDING_WEIGHT + REID_SPATIAL_WEIGHT + REID_TEMPORAL_WEIGHT
    if abs(weight_sum - 1.0) > 0.01:
        errors.append(f"ReID weights must sum to 1.0 (current: {weight_sum})")
    
    # Check thresholds are in valid range
    if not 0 <= REID_SIMILARITY_THRESHOLD <= 1:
        errors.append("REID_SIMILARITY_THRESHOLD must be between 0 and 1")
    
    if not 0 <= CONFIDENCE_THRESHOLD <= 1:
        errors.append("CONFIDENCE_THRESHOLD must be between 0 and 1")
    
    # Check positive values
    if REID_COOLDOWN_PERIOD < 0:
        errors.append("REID_COOLDOWN_PERIOD must be positive")
    
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ Configuration validated")
    return True


# Validate on import
if __name__ != "__main__":
    validate_config()
