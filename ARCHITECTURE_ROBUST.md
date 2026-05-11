# Robust System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         VIDEO SOURCE                             │
│                    (Webcam / Video File)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRAME PREPROCESSING                           │
│  • Skip frames (configurable: 1, 2, 3)                          │
│  • Resize if needed                                              │
│  • Frame rate control                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  YOLOV8-FACE DETECTION                           │
│  Module: face_detector.py                                        │
│  • Model: yolov8n-face.pt                                        │
│  • Confidence threshold: 0.45                                    │
│  • Inference size: 640x640                                       │
│  • Filters: size, confidence, aspect ratio                       │
│  Output: [(x1,y1,x2,y2,confidence), ...]                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BYTETRACK TRACKING                            │
│  Module: face_detector.py (track_faces)                         │
│  • Track buffer: 90 frames                                       │
│  • High threshold: 0.6                                           │
│  • Low threshold: 0.2                                            │
│  • Maintains track IDs across frames                             │
│  Output: [(x1,y1,x2,y2,track_id,conf,age), ...]                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION LAYER                              │
│  Module: face_detector.py (is_valid_face_detection)             │
│  • Size check: >= 35x35 pixels                                  │
│  • Confidence check: >= 0.45                                     │
│  • Aspect ratio: 0.5 - 1.5                                       │
│  Rejects: tiny, low-conf, extreme angles                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FACE CROPPING                                 │
│  Module: image_manager.py (crop_face)                           │
│  • Tight padding: 10 pixels                                      │
│  • Boundary checks                                               │
│  • Minimum crop size: 40x40                                      │
│  Output: face_crop (BGR image)                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  QUALITY ASSESSMENT                              │
│  Module: face_reid_robust.py (assess_face_quality)              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Size Quality (0-30 points)                                │  │
│  │  • Larger faces = higher score                            │  │
│  │  • Formula: min(30, (min(w,h)/160) * 30)                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Confidence Quality (0-30 points)                          │  │
│  │  • Detection confidence * 30                              │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Sharpness Quality (0-25 points)                           │  │
│  │  • Laplacian variance (blur detection)                    │  │
│  │  • Formula: min(25, (laplacian_var/500) * 25)             │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Aspect Ratio Quality (0-15 points)                        │  │
│  │  • 0.7-1.3: 15 points (ideal)                             │  │
│  │  • 0.5-1.5: 10 points (acceptable)                        │  │
│  │  • Other: 5 points (poor)                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│  Total: 0-100 points, Threshold: 30                             │
│  Rejects: blurry, tiny, extreme angles, low confidence          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EMBEDDING EXTRACTION                            │
│  Module: face_reid_robust.py (extract_embedding)                │
│  • Model: InsightFace 'buffalo_s'                                │
│  • Resize to 160x160 for speed                                   │
│  • Output: 512-dimensional vector                                │
│  • Cached for 5 seconds                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRACK ASSIGNMENT CHECK                        │
│  Module: face_reid_robust.py                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Is track already assigned?                                │  │
│  │  YES → Return existing student_id                         │  │
│  │  NO  → Continue to matching                               │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Is this a recently lost track?                            │  │
│  │  YES + within 5s → Recover student_id                     │  │
│  │  NO → Continue to matching                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID MATCHING                               │
│  Module: face_reid_robust.py (hybrid_matching_score)            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. EMBEDDING SIMILARITY (50% weight)                      │  │
│  │    • Compare with average embedding of each student       │  │
│  │    • Cosine similarity                                    │  │
│  │    • emb_score = cosine_sim(emb1, avg_emb2)               │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 2. SPATIAL PROXIMITY (30% weight)                         │  │
│  │    • Compare current bbox with last known position        │  │
│  │    • Euclidean distance between centers                   │  │
│  │    • Normalized by frame diagonal                         │  │
│  │    • spatial_score = 1 - normalized_distance              │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 3. TEMPORAL CONTINUITY (20% weight)                       │  │
│  │    • Time since student last seen                         │  │
│  │    • Exponential decay: e^(-time/5.0)                     │  │
│  │    • Recently seen = higher score                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ COMBINED SCORE                                            │  │
│  │  score = emb_score*0.5 + spatial*0.3 + temporal*0.2      │  │
│  │  Threshold: 0.55                                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│  Output: (best_student_id, score, details) or (None, 0, {})     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION LOGIC                                │
│  Module: face_reid_robust.py (register_or_match_face)           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Match found (score >= 0.55)?                              │  │
│  │  YES → Assign existing student_id                         │  │
│  │       → Update embeddings (with outlier rejection)        │  │
│  │       → Update last_seen, last_bbox                       │  │
│  │       → Return (student_id, False, details)               │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ No match found                                            │  │
│  │  → Check cooldown (3 seconds since last new student)      │  │
│  │     Cooldown active? → Use track_id temporarily           │  │
│  │     Cooldown passed? → Create new student_id              │  │
│  │                       → Initialize embeddings             │  │
│  │                       → Return (new_id, True, details)    │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EMBEDDING SMOOTHING                             │
│  Module: face_reid_robust.py (update_student_embeddings)        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Outlier Detection                                         │  │
│  │  • Compare new embedding with average                     │  │
│  │  • If similarity < 0.4 → REJECT                           │  │
│  │  • Prevents bad embeddings from corrupting profile        │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Rolling Window                                            │  │
│  │  • Store up to 10 embeddings per student                  │  │
│  │  • FIFO queue (oldest removed when full)                  │  │
│  │  • Calculate average for matching                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    IMAGE SAVING                                  │
│  Module: image_manager.py (save_face_image)                     │
│  • Interval: 1.5 seconds per student                             │
│  • Quality filter: confidence >= 0.5                             │
│  • Minimum size: 50x50 pixels                                    │
│  • Format: JPEG (quality 95)                                     │
│  • Path: students/student_X/timestamp.jpg                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRACK MANAGEMENT                              │
│  Module: face_reid_robust.py                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Active Tracks                                             │  │
│  │  • track_to_student: {track_id: student_id}               │  │
│  │  • Updated every frame                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Lost Tracks (Grace Period)                                │  │
│  │  • lost_tracks: {track_id: (student_id, lost_time)}       │  │
│  │  • Timeout: 5 seconds                                     │  │
│  │  • Recoverable if track reappears                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Periodic Cleanup (every 100 frames)                       │  │
│  │  • Remove expired lost tracks                             │  │
│  │  • Clear old cache entries                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DISPLAY RENDERING                             │
│  Module: video_processor.py                                     │
│  • Draw bounding boxes (green, 2px)                              │
│  • Draw student IDs                                              │
│  • Draw FPS counter                                              │
│  • Draw statistics (students, images)                            │
│  • Draw debug overlay (optional)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT DISPLAY                                │
│  • OpenCV window with annotated frame                            │
│  • Keyboard controls (q, s, r)                                   │
│  • Real-time statistics                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Post-Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    STUDENT FOLDERS                               │
│  students/student_1/, student_2/, ..., student_N/                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              EMBEDDING EXTRACTION (BATCH)                        │
│  Module: folder_cleanup.py (get_folder_embeddings)              │
│  • Sample up to 20 images per folder                             │
│  • Extract embeddings for each image                             │
│  • Calculate average embedding per folder                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              DUPLICATE FOLDER DETECTION                          │
│  Module: folder_cleanup.py (detect_duplicate_folders)           │
│  • Compare all folder pairs                                      │
│  • Cosine similarity between average embeddings                  │
│  • Threshold: 0.65                                               │
│  • Group similar folders                                         │
│  Output: [[folder1, folder2], [folder3, folder4], ...]          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              MIXED-IDENTITY DETECTION                            │
│  Module: folder_cleanup.py (detect_mixed_identity_folders)      │
│  • Extract all embeddings from folder                            │
│  • DBSCAN clustering:                                            │
│    - eps = 0.6 (max distance)                                    │
│    - min_samples = 2                                             │
│    - metric = 'cosine'                                           │
│  • If multiple clusters → mixed identity                         │
│  Output: {folder_name: num_clusters}                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              FOLDER MERGING                                      │
│  Module: folder_cleanup.py (merge_duplicate_folders)            │
│  • Choose primary folder (most images)                           │
│  • Copy images from duplicates to primary                        │
│  • Rename copied images to avoid conflicts                       │
│  • Remove duplicate folders                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              FOLDER SPLITTING                                    │
│  Module: folder_cleanup.py (split_mixed_folder)                 │
│  • Cluster embeddings (DBSCAN)                                   │
│  • Create new folder for each cluster                            │
│  • Move images to respective folders                             │
│  • Remove original mixed folder                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              LOW-QUALITY REMOVAL                                 │
│  Module: folder_cleanup.py (remove_low_quality_folders)         │
│  • Count images per folder                                       │
│  • Remove folders with < 3 images                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              CLEANUP REPORT                                      │
│  Module: folder_cleanup.py (generate_cleanup_report)            │
│  • JSON report with:                                             │
│    - Total folders                                               │
│    - Duplicate groups                                            │
│    - Mixed-identity folders                                      │
│    - Low-quality folders                                         │
│    - Recommendations                                             │
│  Output: cleanup_report.json                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow

### Student Data Structure

```python
# In face_reid_robust.py

student_embeddings = {
    1: deque([emb1, emb2, ..., emb10]),  # Max 10 embeddings
    2: deque([emb1, emb2, ...]),
    ...
}

student_avg_embeddings = {
    1: avg_emb_1,  # Average of all embeddings
    2: avg_emb_2,
    ...
}

student_last_seen = {
    1: 1620000000.0,  # Unix timestamp
    2: 1620000005.0,
    ...
}

student_last_bbox = {
    1: (100, 150, 200, 250),  # (x1, y1, x2, y2)
    2: (300, 180, 400, 280),
    ...
}

track_to_student = {
    5: 1,  # Track 5 → Student 1
    7: 1,  # Track 7 → Student 1 (same student, new track)
    9: 2,  # Track 9 → Student 2
    ...
}

lost_tracks = {
    3: (2, 1620000010.0),  # Track 3 was Student 2, lost at time X
    ...
}
```

---

## 🔀 Decision Tree

```
New Detection
    │
    ├─ Quality Check
    │   ├─ Quality < 30 → REJECT
    │   └─ Quality >= 30 → Continue
    │
    ├─ Track Already Assigned?
    │   ├─ YES → Return existing student_id
    │   └─ NO → Continue
    │
    ├─ Recently Lost Track?
    │   ├─ YES + within 5s → RECOVER student_id
    │   └─ NO → Continue
    │
    ├─ Extract Embedding
    │   ├─ Failed → Use track_id temporarily
    │   └─ Success → Continue
    │
    ├─ Hybrid Matching
    │   ├─ Match found (score >= 0.55)
    │   │   ├─ Check Outlier (sim < 0.4)
    │   │   │   ├─ YES → Reject embedding
    │   │   │   └─ NO → Add to embeddings
    │   │   └─ Return existing student_id
    │   │
    │   └─ No match
    │       ├─ Cooldown Active (< 3s since last new)
    │       │   └─ Use track_id temporarily
    │       │
    │       └─ Cooldown Passed
    │           └─ Create NEW student_id
```

---

## 🎯 Key Algorithms

### 1. Hybrid Matching Score

```python
def hybrid_matching_score(embedding, bbox, time, student_id):
    # Embedding similarity
    avg_emb = student_avg_embeddings[student_id]
    emb_sim = cosine_similarity(embedding, avg_emb)
    
    # Spatial proximity
    last_bbox = student_last_bbox[student_id]
    distance = euclidean_distance(bbox_center, last_bbox_center)
    spatial_sim = 1 - (distance / frame_diagonal)
    
    # Temporal continuity
    last_seen = student_last_seen[student_id]
    time_diff = time - last_seen
    temporal_score = exp(-time_diff / 5.0)
    
    # Weighted combination
    combined = (
        emb_sim * 0.5 +
        spatial_sim * 0.3 +
        temporal_score * 0.2
    )
    
    return combined
```

### 2. Quality Assessment

```python
def assess_quality(face_crop, bbox, confidence):
    # Size quality
    size_score = min(30, (min(w, h) / 160) * 30)
    
    # Confidence quality
    conf_score = confidence * 30
    
    # Sharpness quality (Laplacian variance)
    gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    sharpness_score = min(25, (laplacian_var / 500) * 25)
    
    # Aspect ratio quality
    aspect_ratio = w / h
    if 0.7 <= aspect_ratio <= 1.3:
        aspect_score = 15
    elif 0.5 <= aspect_ratio <= 1.5:
        aspect_score = 10
    else:
        aspect_score = 5
    
    total = size_score + conf_score + sharpness_score + aspect_score
    return total  # 0-100
```

### 3. DBSCAN Clustering (Mixed Identity Detection)

```python
from sklearn.cluster import DBSCAN

def detect_mixed_identity(embeddings):
    # Cluster embeddings
    clustering = DBSCAN(
        eps=0.6,              # Max distance between samples
        min_samples=2,        # Min samples in cluster
        metric='cosine'       # Cosine distance
    ).fit(embeddings)
    
    labels = clustering.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    
    # Multiple clusters = mixed identity
    return n_clusters > 1
```

---

## 🔧 Configuration Hierarchy

```
config_robust.py
    │
    ├─ Detection Config
    │   ├─ CONFIDENCE_THRESHOLD
    │   ├─ MIN_FACE_SIZE
    │   └─ INFERENCE_SIZE
    │
    ├─ Tracking Config
    │   ├─ TRACK_BUFFER
    │   ├─ TRACK_HIGH_THRESH
    │   └─ TRACK_LOW_THRESH
    │
    ├─ ReID Config
    │   ├─ Matching
    │   │   ├─ REID_SIMILARITY_THRESHOLD
    │   │   ├─ REID_EMBEDDING_WEIGHT
    │   │   ├─ REID_SPATIAL_WEIGHT
    │   │   └─ REID_TEMPORAL_WEIGHT
    │   │
    │   ├─ Temporal
    │   │   ├─ REID_COOLDOWN_PERIOD
    │   │   ├─ REID_LOST_TRACK_TIMEOUT
    │   │   └─ REID_TEMPORAL_TAU
    │   │
    │   ├─ Quality
    │   │   ├─ REID_QUALITY_THRESHOLD
    │   │   └─ REID_OUTLIER_THRESHOLD
    │   │
    │   └─ Embeddings
    │       ├─ REID_MAX_EMBEDDINGS_PER_STUDENT
    │       └─ REID_EMBEDDING_CACHE_DURATION
    │
    ├─ Saving Config
    │   ├─ SAVE_INTERVAL
    │   ├─ SAVE_MIN_CONFIDENCE
    │   └─ IMAGE_QUALITY
    │
    └─ Presets
        ├─ fast
        ├─ balanced
        ├─ accurate
        └─ hackathon
```

---

This architecture provides a complete, production-ready system for robust student tracking in classroom environments.
