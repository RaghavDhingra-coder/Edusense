# 📚 Usage Examples & Command Reference

## Quick Start Examples

### 1. Basic Webcam Usage
```bash
python main.py
```
**What it does**: Opens webcam, detects faces, saves crops to `students/` folder

**Expected output**:
```
🎓 CLASSROOM FACE DETECTION AND TRACKING SYSTEM
═══════════════════════════════════════════════════════════
📦 Initializing components...
🔄 Loading YOLOv8 Face Detection model: yolov8n-face.pt
✅ Loaded face detection model: yolov8n-face.pt
✅ Model initialized on cuda:0
   Inference size: 1280x1280
   Confidence threshold: 0.6
   Min face size: 40x40
🎥 Opening video source: 0
✅ Webcam opened successfully
🚀 Starting face detection and tracking...
💾 Saved face image for Student ID 1 (conf: 0.87)
💾 Saved face image for Student ID 2 (conf: 0.92)
```

---

### 2. Process Video File
```bash
python main.py --source classroom_lecture.mp4
```
**What it does**: Processes recorded classroom video

**Use case**: Analyze recorded lectures, offline processing

---

### 3. Custom Output Directory
```bash
python main.py --source classroom.mp4 --output session_2024_05_11
```
**What it does**: Saves student images to `session_2024_05_11/` instead of `students/`

**Use case**: Organize by date, session, or class

**Result**:
```
session_2024_05_11/
├── student_1/
├── student_2/
└── student_3/
```

---

### 4. Adjust Detection Sensitivity
```bash
# More sensitive (detect more faces, may include false positives)
python main.py --confidence 0.5

# Less sensitive (fewer false positives, may miss some faces)
python main.py --confidence 0.7

# Balanced (default)
python main.py --confidence 0.6
```

---

### 5. Force CPU Usage
```bash
python main.py --device cpu
```
**When to use**: 
- No GPU available
- GPU memory issues
- Testing on different hardware

**Note**: Expect 3-5 FPS instead of 15-20 FPS

---

### 6. Force GPU Usage
```bash
python main.py --device cuda:0
```
**When to use**:
- Ensure GPU is being used
- Multiple GPUs available (use cuda:1, cuda:2, etc.)

---

## Real-World Scenarios

### Scenario 1: Small Classroom (15-20 students)
```bash
python main.py --source 0 --confidence 0.7
```
**Why**: Close-up faces, high confidence works well

**Expected**: 15-20 FPS, accurate detection

---

### Scenario 2: Large Lecture Hall (50+ students)
```bash
python main.py --source lecture_hall.mp4 --confidence 0.5
```
**Why**: Distant faces need lower confidence threshold

**Tip**: Consider using `yolov8s-face.pt` for better accuracy:
```python
# Edit config.py
YOLO_MODEL = "yolov8s-face.pt"
```

---

### Scenario 3: Poor Lighting Conditions
```bash
python main.py --source dim_classroom.mp4 --confidence 0.5
```
**Why**: Lower confidence helps in poor lighting

**Additional tip**: Edit `config.py`:
```python
USE_HALF_PRECISION = False  # More stable in difficult conditions
```

---

### Scenario 4: Multiple Sessions Same Day
```bash
# Morning session
python main.py --source morning.mp4 --output morning_session

# Afternoon session
python main.py --source afternoon.mp4 --output afternoon_session

# Evening session
python main.py --source evening.mp4 --output evening_session
```

**Result**:
```
morning_session/
├── student_1/
└── student_2/

afternoon_session/
├── student_1/
└── student_3/

evening_session/
├── student_1/
└── student_4/
```

---

### Scenario 5: High-Quality Offline Processing
```bash
# Edit config.py first:
# YOLO_MODEL = "yolov8s-face.pt"
# INFERENCE_SIZE = 1920
# CONFIDENCE_THRESHOLD = 0.5

python main.py --source recorded_lecture.mp4 --device cuda:0
```
**Why**: Best quality for offline analysis, not real-time

---

## Interactive Commands

### While System is Running:

**Press `q`**: Quit the application
```
🛑 Stopping system...
🧹 Cleaning up...
📊 STATISTICS
═══════════════════════════════════════════════════════════
Total Students Tracked: 12
Total Images Saved: 487
Current FPS: 16.3
```

**Press `s`**: Show current statistics
```
═══════════════════════════════════════════════════════════
📊 STATISTICS
═══════════════════════════════════════════════════════════
Total Students Tracked: 8
Total Images Saved: 234
Current FPS: 17.2

Per-Student Image Count:
  Student 1: 45 images
  Student 2: 38 images
  Student 3: 42 images
  Student 4: 31 images
  Student 5: 28 images
  Student 6: 19 images
  Student 7: 16 images
  Student 8: 15 images
═══════════════════════════════════════════════════════════
```

---

## Configuration Examples

### Example 1: Maximum Accuracy (Slow)
```python
# config.py
YOLO_MODEL = "yolov8m-face.pt"
INFERENCE_SIZE = 1920
CONFIDENCE_THRESHOLD = 0.5
MIN_FACE_WIDTH = 25
MIN_FACE_HEIGHT = 25
USE_HALF_PRECISION = False
```

**Use case**: Offline processing, research, maximum quality

**Expected FPS**: 5-10 FPS on GPU

---

### Example 2: Maximum Speed (Lower Accuracy)
```python
# config.py
YOLO_MODEL = "yolov8n-face.pt"
INFERENCE_SIZE = 640
CONFIDENCE_THRESHOLD = 0.7
MIN_FACE_WIDTH = 50
MIN_FACE_HEIGHT = 50
USE_HALF_PRECISION = True
```

**Use case**: Real-time monitoring, fast processing

**Expected FPS**: 25-30 FPS on GPU

---

### Example 3: Balanced (Default)
```python
# config.py
YOLO_MODEL = "yolov8n-face.pt"
INFERENCE_SIZE = 1280
CONFIDENCE_THRESHOLD = 0.6
MIN_FACE_WIDTH = 40
MIN_FACE_HEIGHT = 40
USE_HALF_PRECISION = True
```

**Use case**: Most classroom scenarios

**Expected FPS**: 15-20 FPS on GPU

---

### Example 4: Distant Face Optimization
```python
# config.py
YOLO_MODEL = "yolov8s-face.pt"
INFERENCE_SIZE = 1920
CONFIDENCE_THRESHOLD = 0.45
MIN_FACE_WIDTH = 25
MIN_FACE_HEIGHT = 25
CROP_PADDING = 20
```

**Use case**: Large lecture halls, back-row students

---

### Example 5: Tight Face Crops
```python
# config.py
CROP_PADDING = 10
MIN_CROP_SIZE = 40
```

**Use case**: Minimal background, face-only crops

---

## Testing & Validation

### Test 1: Verify Installation
```bash
python test_system.py
```

**Expected output**:
```
🧪 Testing Package Imports
✅ OpenCV: OK
✅ NumPy: OK
✅ Pillow: OK
✅ Ultralytics: OK

🔥 Testing CUDA/GPU Support
✅ CUDA Available: Yes
   GPU Device: NVIDIA GeForce RTX 3080

📹 Testing Webcam Access
✅ Webcam: OK
   Resolution: 1920x1080

🤖 Testing YOLOv8 Model
✅ YOLOv8 Model: OK

📁 Testing File Structure
✅ main.py: Present
✅ face_detector.py: Present
✅ image_manager.py: Present
✅ video_processor.py: Present
✅ config.py: Present
✅ requirements.txt: Present

✅ SYSTEM READY
```

---

### Test 2: Quick Webcam Test (10 seconds)
```bash
# Run for 10 seconds then press 'q'
python main.py

# Check results
ls students/
ls students/student_1/
```

**Expected**: 
- Folders created for each detected person
- ~10 images per person (1 per second)

---

### Test 3: Video File Test
```bash
# Process first 100 frames
python main.py --source test_video.mp4

# Press 'q' after a few seconds
# Check output
ls -R students/
```

---

### Test 4: Performance Benchmark
```bash
# GPU test
python main.py --source test_video.mp4 --device cuda:0

# CPU test
python main.py --source test_video.mp4 --device cpu

# Compare FPS shown on screen
```

---

## Common Workflows

### Workflow 1: Daily Classroom Monitoring
```bash
#!/bin/bash
# daily_monitor.sh

DATE=$(date +%Y-%m-%d)
TIME=$(date +%H-%M-%S)
OUTPUT="sessions/${DATE}_${TIME}"

python main.py --source 0 --output "$OUTPUT" --confidence 0.6

echo "Session saved to: $OUTPUT"
```

**Usage**:
```bash
chmod +x daily_monitor.sh
./daily_monitor.sh
```

---

### Workflow 2: Batch Video Processing
```bash
#!/bin/bash
# batch_process.sh

for video in videos/*.mp4; do
    filename=$(basename "$video" .mp4)
    echo "Processing: $filename"
    python main.py --source "$video" --output "processed/$filename"
done

echo "All videos processed!"
```

---

### Workflow 3: Weekly Analysis
```bash
#!/bin/bash
# weekly_analysis.sh

# Process all week's videos
for day in monday tuesday wednesday thursday friday; do
    python main.py \
        --source "recordings/${day}.mp4" \
        --output "week_analysis/${day}" \
        --confidence 0.6
done

# Generate statistics
python analyze_week.py
```

---

## Output Structure Examples

### Example 1: Single Session
```
students/
├── student_1/
│   ├── 2026-05-11_10-30-15.jpg
│   ├── 2026-05-11_10-30-16.jpg
│   ├── 2026-05-11_10-30-17.jpg
│   └── ... (45 images)
├── student_2/
│   ├── 2026-05-11_10-30-15.jpg
│   └── ... (38 images)
└── student_3/
    └── ... (42 images)
```

---

### Example 2: Multiple Sessions
```
sessions/
├── 2026-05-11_morning/
│   ├── student_1/
│   ├── student_2/
│   └── student_3/
├── 2026-05-11_afternoon/
│   ├── student_1/
│   ├── student_4/
│   └── student_5/
└── 2026-05-12_morning/
    ├── student_1/
    └── student_2/
```

---

### Example 3: Class-Based Organization
```
classes/
├── math_101/
│   ├── 2026-05-11/
│   │   ├── student_1/
│   │   └── student_2/
│   └── 2026-05-12/
│       ├── student_1/
│       └── student_3/
└── physics_201/
    └── 2026-05-11/
        ├── student_1/
        └── student_4/
```

---

## Performance Tuning Examples

### For Low-End Hardware (CPU Only)
```python
# config.py
YOLO_MODEL = "yolov8n-face.pt"
INFERENCE_SIZE = 640
CONFIDENCE_THRESHOLD = 0.7
TARGET_FPS = 5
DEVICE = "cpu"
USE_HALF_PRECISION = False
```

```bash
python main.py --source 0 --device cpu
```

**Expected**: 3-5 FPS, good accuracy

---

### For High-End Hardware (RTX 3080+)
```python
# config.py
YOLO_MODEL = "yolov8s-face.pt"
INFERENCE_SIZE = 1920
CONFIDENCE_THRESHOLD = 0.5
TARGET_FPS = 30
DEVICE = "cuda:0"
USE_HALF_PRECISION = True
```

```bash
python main.py --source 0 --device cuda:0
```

**Expected**: 20-30 FPS, excellent accuracy

---

### For Multiple Cameras
```bash
# Terminal 1 - Front camera
python main.py --source 0 --output front_view

# Terminal 2 - Back camera
python main.py --source 1 --output back_view

# Terminal 3 - Side camera
python main.py --source 2 --output side_view
```

---

## Troubleshooting Examples

### Issue: Low FPS
```bash
# Check current performance
python main.py --source test.mp4

# If FPS < 10, try:
# 1. Reduce inference size
# Edit config.py: INFERENCE_SIZE = 640

# 2. Use smaller model
# Edit config.py: YOLO_MODEL = "yolov8n-face.pt"

# 3. Increase confidence
python main.py --source test.mp4 --confidence 0.7
```

---

### Issue: Missing Faces
```bash
# Lower confidence threshold
python main.py --source classroom.mp4 --confidence 0.5

# Or edit config.py:
# CONFIDENCE_THRESHOLD = 0.5
# MIN_FACE_WIDTH = 30
# MIN_FACE_HEIGHT = 30
```

---

### Issue: Too Many False Positives
```bash
# Increase confidence threshold
python main.py --source classroom.mp4 --confidence 0.7

# Or edit config.py:
# CONFIDENCE_THRESHOLD = 0.7
# MIN_FACE_WIDTH = 50
# MIN_FACE_HEIGHT = 50
```

---

### Issue: Poor Crop Quality
```bash
# Adjust padding in config.py:
CROP_PADDING = 20  # More context
# or
CROP_PADDING = 10  # Tighter crops

# Then run:
python main.py --source classroom.mp4
```

---

## Advanced Examples

### Example 1: Custom Processing Script
```python
# custom_process.py
from main import ClassroomTrackingSystem
import config

# Override config
config.CONFIDENCE_THRESHOLD = 0.55
config.INFERENCE_SIZE = 1280

# Create system
system = ClassroomTrackingSystem(
    video_source="classroom.mp4",
    output_dir="custom_output"
)

# Run
system.run()
```

---

### Example 2: Integration with Database
```python
# db_integration.py
from main import ClassroomTrackingSystem
import sqlite3

# Setup database
conn = sqlite3.connect('classroom.db')
cursor = conn.cursor()

# Create system
system = ClassroomTrackingSystem(video_source=0)

# Custom processing with DB logging
# (Extend system.process_frame() to log to DB)
```

---

### Example 3: Real-Time Dashboard
```python
# dashboard.py
from main import ClassroomTrackingSystem
import threading
import flask

app = flask.Flask(__name__)

@app.route('/stats')
def get_stats():
    stats = system.image_manager.get_statistics()
    return flask.jsonify(stats)

# Run system in thread
system = ClassroomTrackingSystem(video_source=0)
threading.Thread(target=system.run).start()

# Run dashboard
app.run(port=5000)
```

---

## Quick Reference Card

### Essential Commands:
```bash
# Basic usage
python main.py

# Video file
python main.py --source video.mp4

# Custom output
python main.py --output my_folder

# Adjust sensitivity
python main.py --confidence 0.6

# Force CPU
python main.py --device cpu

# Test system
python test_system.py
```

### Keyboard Controls:
- **q** - Quit
- **s** - Show statistics

### Important Files:
- `config.py` - All settings
- `main.py` - Run system
- `students/` - Output folder
- `test_system.py` - Test installation

### Key Settings (config.py):
```python
YOLO_MODEL = "yolov8n-face.pt"
CONFIDENCE_THRESHOLD = 0.6
INFERENCE_SIZE = 1280
MIN_FACE_WIDTH = 40
MIN_FACE_HEIGHT = 40
CROP_PADDING = 15
```

---

**Ready to use!** Start with `python main.py` and adjust settings as needed.
