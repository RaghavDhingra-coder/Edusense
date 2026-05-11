# 🤖 YOLOv8 Face Detection Model Setup

## Overview

This system uses **YOLOv8 Face Detection** models specifically trained for face detection. These are NOT the standard YOLOv8 object detection models.

## Model Options

### Option 1: YOLOv8n-face (Recommended for Most Cases)
- **Size**: ~6 MB
- **Speed**: Very fast (~15-20 FPS on GPU)
- **Accuracy**: Good for most classroom scenarios
- **Use Case**: Real-time processing, standard classrooms

### Option 2: YOLOv8s-face (Better Accuracy)
- **Size**: ~22 MB
- **Speed**: Fast (~10-15 FPS on GPU)
- **Accuracy**: Better for distant/small faces
- **Use Case**: Large classrooms, lecture halls

### Option 3: YOLOv8m-face (High Accuracy)
- **Size**: ~52 MB
- **Speed**: Moderate (~5-10 FPS on GPU)
- **Accuracy**: Best accuracy
- **Use Case**: Offline processing, quality priority

---

## Automatic Download (Easiest)

The system will attempt to download the model automatically on first run:

```bash
python main.py
```

If successful, you'll see:
```
🔄 Loading YOLOv8 Face Detection model: yolov8n-face.pt
✅ Loaded face detection model: yolov8n-face.pt
```

---

## Manual Download (Recommended)

If automatic download fails, download manually:

### Method 1: Direct Download

**YOLOv8n-face**:
```bash
wget https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8n-face.pt
```

**YOLOv8s-face**:
```bash
wget https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8s-face.pt
```

**YOLOv8m-face**:
```bash
wget https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8m-face.pt
```

### Method 2: Using curl (macOS/Linux)

```bash
curl -L -o yolov8n-face.pt https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8n-face.pt
```

### Method 3: Browser Download

1. Visit: https://github.com/akanametov/yolov8-face/releases
2. Download `yolov8n-face.pt` or `yolov8s-face.pt`
3. Place in your project directory

---

## Model Placement

Place the downloaded model file in your project directory:

```
classroom-tracking/
├── main.py
├── face_detector.py
├── config.py
├── yolov8n-face.pt    ← Place model here
└── ...
```

Or specify a custom path in `config.py`:

```python
YOLO_MODEL = "/path/to/your/yolov8n-face.pt"
```

---

## Switching Models

### To use YOLOv8s-face (better accuracy):

**Option 1: Edit config.py**
```python
YOLO_MODEL = "yolov8s-face.pt"
```

**Option 2: Command line**
```bash
# Not directly supported, edit config.py
```

### To use YOLOv8m-face (best accuracy):

```python
# In config.py
YOLO_MODEL = "yolov8m-face.pt"
```

---

## Model Comparison

| Model | Size | Speed (GPU) | Speed (CPU) | Accuracy | Best For |
|-------|------|-------------|-------------|----------|----------|
| yolov8n-face | 6 MB | 15-20 FPS | 3-5 FPS | Good | Real-time, standard rooms |
| yolov8s-face | 22 MB | 10-15 FPS | 1-3 FPS | Better | Large classrooms |
| yolov8m-face | 52 MB | 5-10 FPS | <1 FPS | Best | Offline processing |

---

## Verification

### Test if model is loaded correctly:

```bash
python test_system.py
```

Expected output:
```
🤖 Testing YOLOv8 Model
═══════════════════════════════════════════════════════════
🔄 Loading YOLOv8n model (this may take a moment)...
✅ YOLOv8 Model: OK
   Model will be downloaded on first run if not present
```

### Test face detection:

```bash
python main.py --source 0  # Webcam test
```

You should see:
```
🔄 Loading YOLOv8 Face Detection model: yolov8n-face.pt
✅ Loaded face detection model: yolov8n-face.pt
✅ Model initialized on cuda:0
   Inference size: 1280x1280
   Confidence threshold: 0.6
   Min face size: 40x40
```

---

## Troubleshooting

### Error: "Failed to load face detection model"

**Solution 1**: Download manually
```bash
wget https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8n-face.pt
```

**Solution 2**: Check internet connection
```bash
ping github.com
```

**Solution 3**: Use alternative source
- Download from Google Drive or other mirrors
- Search for "yolov8-face pretrained models"

### Error: "Model file not found"

**Check file location**:
```bash
ls -la *.pt
```

**Verify path in config.py**:
```python
import os
print(os.path.exists("yolov8n-face.pt"))  # Should print True
```

### Error: "CUDA out of memory"

**Solution**: Use smaller model or CPU
```python
# In config.py
YOLO_MODEL = "yolov8n-face.pt"  # Smallest model
DEVICE = "cpu"  # Use CPU instead
```

### Warning: "Could not load yolov8n-face.pt"

The system will try alternative models automatically:
1. First tries: `yolov8n-face.pt`
2. Then tries: `yolov8s-face.pt`
3. Falls back to: Standard YOLOv8n (not recommended)

**Recommended**: Download face model manually

---

## Alternative Face Detection Models

If you cannot access the above models, alternatives include:

### 1. YOLO-Face (Different Implementation)
```bash
# Clone repository
git clone https://github.com/derronqi/yolov8-face
cd yolov8-face
# Follow their setup instructions
```

### 2. RetinaFace (Alternative Architecture)
- More accurate but slower
- Requires different integration
- Not plug-and-play with current system

### 3. MTCNN (Lightweight Alternative)
- Lighter weight
- Good for CPU
- Requires code modifications

---

## Model Training (Advanced)

To train your own face detection model on classroom data:

### 1. Collect Data
- Record classroom videos
- Extract frames
- Annotate faces with bounding boxes

### 2. Prepare Dataset
```
dataset/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

### 3. Train Model
```python
from ultralytics import YOLO

# Load pretrained face model
model = YOLO('yolov8n-face.pt')

# Train on your data
model.train(
    data='classroom_faces.yaml',
    epochs=100,
    imgsz=1280,
    batch=16
)
```

### 4. Use Custom Model
```python
# In config.py
YOLO_MODEL = "runs/detect/train/weights/best.pt"
```

---

## Performance Optimization

### For GPU:
```python
# In config.py
DEVICE = "cuda:0"
USE_HALF_PRECISION = True  # FP16 for 2x speed
INFERENCE_SIZE = 1280
```

### For CPU:
```python
# In config.py
DEVICE = "cpu"
USE_HALF_PRECISION = False
INFERENCE_SIZE = 640  # Smaller for speed
YOLO_MODEL = "yolov8n-face.pt"  # Smallest model
```

### For Multiple GPUs:
```python
# Use specific GPU
DEVICE = "cuda:0"  # First GPU
DEVICE = "cuda:1"  # Second GPU
```

---

## Model Storage

### Recommended Structure:
```
project/
├── models/
│   ├── yolov8n-face.pt
│   ├── yolov8s-face.pt
│   └── custom_classroom_face.pt
├── main.py
└── config.py
```

### Update config.py:
```python
YOLO_MODEL = "models/yolov8n-face.pt"
```

---

## License & Attribution

**YOLOv8-Face Models**:
- Source: https://github.com/akanametov/yolov8-face
- Based on: Ultralytics YOLOv8
- License: AGPL-3.0

**Ultralytics YOLOv8**:
- Source: https://github.com/ultralytics/ultralytics
- License: AGPL-3.0

**Usage**: Free for research and educational purposes. For commercial use, check license terms.

---

## Quick Reference

### Download Command:
```bash
wget https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8n-face.pt
```

### Verify Download:
```bash
ls -lh yolov8n-face.pt
# Should show ~6MB file
```

### Test Model:
```bash
python main.py --source 0
```

### Switch Model:
```python
# Edit config.py
YOLO_MODEL = "yolov8s-face.pt"  # or yolov8m-face.pt
```

---

## Support

If you encounter issues:

1. ✅ Check model file exists: `ls *.pt`
2. ✅ Verify file size: `ls -lh yolov8n-face.pt` (~6MB)
3. ✅ Test with test_system.py
4. ✅ Check GitHub releases for latest models
5. ✅ Try alternative download methods

---

**Model Status**: ✅ **READY FOR CLASSROOM FACE DETECTION**
