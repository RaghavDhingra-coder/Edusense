# ✅ Deployment Checklist

## Pre-Deployment Checklist

### 1. System Requirements
- [ ] Python 3.8+ installed
- [ ] pip package manager available
- [ ] (Optional) NVIDIA GPU with CUDA for better performance
- [ ] Webcam connected OR video files ready
- [ ] Sufficient disk space (1GB+ recommended)

### 2. Installation
- [ ] All project files downloaded
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Face detection model downloaded (yolov8n-face.pt or yolov8s-face.pt)
- [ ] Installation tested: `python test_system.py`

### 3. Configuration
- [ ] Reviewed `config.py` settings
- [ ] Adjusted `CONFIDENCE_THRESHOLD` for your environment
- [ ] Set appropriate `INFERENCE_SIZE` based on hardware
- [ ] Configured `OUTPUT_DIR` for your needs
- [ ] Selected correct `DEVICE` (cuda:0 or cpu)

### 4. Testing
- [ ] Ran `python test_system.py` successfully
- [ ] Tested with webcam: `python main.py`
- [ ] Tested with video file: `python main.py --source test.mp4`
- [ ] Verified face detection accuracy
- [ ] Checked crop quality in `students/` folder
- [ ] Confirmed FPS is acceptable (≥10 FPS)

---

## Deployment Scenarios

### Scenario A: Live Classroom Monitoring

**Hardware Setup:**
- [ ] Camera positioned to capture all students
- [ ] Camera connected and tested
- [ ] Computer with GPU (recommended)
- [ ] Stable power supply

**Software Setup:**
- [ ] System installed and tested
- [ ] Configuration optimized for classroom size
- [ ] Output directory configured
- [ ] Backup storage available

**Configuration:**
```python
# config.py for live monitoring
YOLO_MODEL = "yolov8n-face.pt"
INFERENCE_SIZE = 1280
CONFIDENCE_THRESHOLD = 0.6
DEVICE = "cuda:0"
USE_HALF_PRECISION = True
```

**Run Command:**
```bash
python main.py --source 0 --output live_session_$(date +%Y%m%d_%H%M%S)
```

**Checklist:**
- [ ] Camera angle covers all students
- [ ] Lighting is adequate
- [ ] System runs at ≥15 FPS
- [ ] All students are detected
- [ ] Crops are high quality

---

### Scenario B: Recorded Video Processing

**Hardware Setup:**
- [ ] Video files available
- [ ] Sufficient storage for output
- [ ] Computer with GPU (optional but recommended)

**Software Setup:**
- [ ] System installed and tested
- [ ] Batch processing script ready (if needed)
- [ ] Output organization planned

**Configuration:**
```python
# config.py for offline processing
YOLO_MODEL = "yolov8s-face.pt"  # Better accuracy
INFERENCE_SIZE = 1920           # Higher quality
CONFIDENCE_THRESHOLD = 0.5
DEVICE = "cuda:0"
USE_HALF_PRECISION = True
```

**Run Command:**
```bash
python main.py --source classroom_lecture.mp4 --output session_2024_05_11
```

**Checklist:**
- [ ] Video quality is good
- [ ] All videos are accessible
- [ ] Output directory has space
- [ ] Processing time is acceptable
- [ ] Results are reviewed

---

### Scenario C: Large Lecture Hall

**Special Considerations:**
- [ ] Many students (50+)
- [ ] Distant faces (back rows)
- [ ] Wide camera angle

**Configuration:**
```python
# config.py for large lecture hall
YOLO_MODEL = "yolov8s-face.pt"  # Better for distant faces
INFERENCE_SIZE = 1920           # Larger for small faces
CONFIDENCE_THRESHOLD = 0.5      # Lower for distant faces
MIN_FACE_WIDTH = 30             # Smaller minimum
MIN_FACE_HEIGHT = 30
DEVICE = "cuda:0"
USE_HALF_PRECISION = True
```

**Checklist:**
- [ ] Camera has wide angle lens
- [ ] Resolution is high (1080p+)
- [ ] Back-row students are visible
- [ ] System detects distant faces
- [ ] FPS is acceptable (≥10)

---

### Scenario D: Small Classroom

**Special Considerations:**
- [ ] Few students (10-20)
- [ ] Close-up faces
- [ ] High accuracy needed

**Configuration:**
```python
# config.py for small classroom
YOLO_MODEL = "yolov8n-face.pt"  # Fast enough
INFERENCE_SIZE = 1280
CONFIDENCE_THRESHOLD = 0.7      # Higher for accuracy
MIN_FACE_WIDTH = 50             # Larger minimum
MIN_FACE_HEIGHT = 50
DEVICE = "cuda:0"
USE_HALF_PRECISION = True
```

**Checklist:**
- [ ] All students clearly visible
- [ ] High detection accuracy (95%+)
- [ ] Minimal false positives
- [ ] High-quality crops
- [ ] Real-time performance (≥15 FPS)

---

## Performance Optimization Checklist

### GPU Optimization
- [ ] CUDA installed and working
- [ ] GPU detected: Check with `python test_system.py`
- [ ] FP16 enabled: `USE_HALF_PRECISION = True`
- [ ] Appropriate inference size for GPU memory
- [ ] Monitoring GPU usage (nvidia-smi)

### CPU Optimization
- [ ] Smaller model: `yolov8n-face.pt`
- [ ] Smaller inference: `INFERENCE_SIZE = 640`
- [ ] FP16 disabled: `USE_HALF_PRECISION = False`
- [ ] Higher confidence: `CONFIDENCE_THRESHOLD = 0.7`
- [ ] Realistic FPS expectations (3-5 FPS)

### Storage Optimization
- [ ] Sufficient disk space
- [ ] Fast storage (SSD recommended)
- [ ] Regular cleanup of old sessions
- [ ] Backup strategy in place
- [ ] Monitoring disk usage

---

## Quality Assurance Checklist

### Detection Quality
- [ ] All visible students detected
- [ ] No false positives (objects detected as faces)
- [ ] Back-row students detected (if applicable)
- [ ] Stable tracking IDs (no frequent switching)
- [ ] Confidence scores are reasonable (≥0.6)

### Crop Quality
- [ ] Crops contain only face region
- [ ] Minimal background in crops
- [ ] Consistent crop sizes
- [ ] Valid aspect ratios
- [ ] No empty or corrupted crops

### System Performance
- [ ] FPS is acceptable for use case
- [ ] No memory leaks (long-term stability)
- [ ] CPU/GPU usage is reasonable
- [ ] No crashes or errors
- [ ] Graceful handling of edge cases

---

## Troubleshooting Checklist

### If Detection is Poor:
- [ ] Check lighting conditions
- [ ] Verify camera angle and position
- [ ] Lower confidence threshold
- [ ] Use larger model (yolov8s-face.pt)
- [ ] Increase inference size
- [ ] Check video quality

### If FPS is Low:
- [ ] Use GPU if available
- [ ] Enable FP16: `USE_HALF_PRECISION = True`
- [ ] Reduce inference size
- [ ] Use smaller model (yolov8n-face.pt)
- [ ] Increase confidence threshold
- [ ] Close other applications

### If Crops are Poor:
- [ ] Adjust `CROP_PADDING` in config.py
- [ ] Check `MIN_CROP_SIZE` setting
- [ ] Verify detection quality first
- [ ] Review aspect ratio filters
- [ ] Check camera resolution

### If False Positives:
- [ ] Increase `CONFIDENCE_THRESHOLD`
- [ ] Increase `MIN_FACE_WIDTH` and `MIN_FACE_HEIGHT`
- [ ] Verify using face-specific model (not yolov8n.pt)
- [ ] Check aspect ratio filters
- [ ] Review detection logs

---

## Production Deployment Checklist

### Before Going Live:
- [ ] Full system test completed
- [ ] Configuration optimized
- [ ] Backup system in place
- [ ] Monitoring setup (FPS, disk space)
- [ ] Error handling tested
- [ ] Documentation reviewed
- [ ] Team trained on system

### During Deployment:
- [ ] System started successfully
- [ ] Initial detection verified
- [ ] FPS is acceptable
- [ ] Crops are being saved
- [ ] No errors in console
- [ ] Monitoring active

### After Deployment:
- [ ] Review saved images
- [ ] Check statistics (press 's')
- [ ] Verify all students detected
- [ ] Confirm crop quality
- [ ] Document any issues
- [ ] Plan improvements

---

## Maintenance Checklist

### Daily:
- [ ] Check system is running
- [ ] Monitor FPS and performance
- [ ] Verify disk space
- [ ] Review any errors

### Weekly:
- [ ] Review detection quality
- [ ] Check crop quality samples
- [ ] Clean up old sessions (if needed)
- [ ] Update configuration if needed
- [ ] Backup important data

### Monthly:
- [ ] Full system review
- [ ] Performance optimization
- [ ] Update dependencies if needed
- [ ] Review and update documentation
- [ ] Plan for Phase 2 features

---

## Phase 2 Preparation Checklist

### Data Collection:
- [ ] Sufficient face crops collected
- [ ] Crops are high quality
- [ ] Multiple students tracked
- [ ] Diverse conditions captured
- [ ] Data organized by student

### System Readiness:
- [ ] Stable tracking IDs maintained
- [ ] Clean folder structure
- [ ] Consistent crop quality
- [ ] Good detection accuracy
- [ ] Performance is acceptable

### Next Steps:
- [ ] Plan attention classification model
- [ ] Design emotion detection system
- [ ] Plan analytics dashboard
- [ ] Design database schema
- [ ] Plan integration approach

---

## Final Verification

### System Status:
- [ ] All components working
- [ ] Configuration optimized
- [ ] Performance acceptable
- [ ] Quality verified
- [ ] Documentation complete

### Ready for:
- [ ] Live classroom monitoring
- [ ] Recorded video processing
- [ ] Long-term deployment
- [ ] Phase 2 integration
- [ ] Production use

---

## Sign-Off

**Deployment Date:** _______________

**Deployed By:** _______________

**Configuration:**
- Model: _______________
- Inference Size: _______________
- Device: _______________
- Confidence: _______________

**Performance:**
- FPS: _______________
- Detection Accuracy: _______________
- Crop Quality: _______________

**Status:** ✅ READY FOR PRODUCTION

---

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________
