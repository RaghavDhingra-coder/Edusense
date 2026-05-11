# Testing Guide: Debug Face Detection Display Issue

## Quick Start

Run these tests in order to isolate the issue:

### Test 1: Verify Drawing Function Works
```bash
python3 test_drawing.py
```

**Expected**: Window shows 3 green boxes with labels on a gray background

**If this fails**: OpenCV display issue (unlikely)
**If this works**: Drawing function is fine, issue is elsewhere

---

### Test 2: Verify YOLO Detection Works
```bash
python3 test_detection_visual.py
```

**Expected**: 
- Webcam opens
- Green boxes appear around faces
- Confidence scores shown
- Frame counter in top-left

**If this fails**: YOLO model or webcam issue
**If this works**: Basic detection + drawing works, issue is in main pipeline

---

### Test 3: Test on Video File
```bash
python3 test_video_detection.py
```

**Expected**:
- Video plays with face detection
- Console shows detection counts
- Summary statistics at end

**If this fails**: Same as Test 2
**If this works**: Confirms detection works on recorded video

---

### Test 4: Run Main System with Debug
```bash
python3 main.py
```

**Watch for**:
- "Raw YOLO detections: N" (should be > 0 after a few frames)
- "Added to display list: Student X" (confirms detection added)
- "Drawing N detections on frame" (confirms drawing called)

**Expected**: Boxes should appear if all above messages show N > 0

---

## Detailed Troubleshooting

### Scenario A: Test 1 Fails
**Problem**: OpenCV display not working
**Solution**: 
- Check OpenCV installation: `pip3 install --upgrade opencv-python`
- Try different display backend
- Check if running in headless environment

### Scenario B: Test 2 Fails
**Problem**: YOLO detection or webcam issue
**Solutions**:
1. Check webcam access: `ls /dev/video*` (Linux) or System Preferences (Mac)
2. Try different camera: `python3 test_detection_visual.py` and modify source
3. Check model file: `ls -lh yolov8n-face.pt` (should be ~6MB)
4. Lower confidence: Edit test script, change `conf=0.3` to `conf=0.1`

### Scenario C: Test 2 Works, Test 4 Fails
**Problem**: Integration issue in main pipeline
**Debugging steps**:

1. **Check if detections reach display list**:
   Look for this in console:
   ```
   ✅ Added to display list: Student X, Track Y, bbox:(x1,y1,x2,y2), conf:0.XX
   ```
   
   - **If you see this**: Detections are added, issue is in drawing
   - **If you don't see this**: Detections are filtered out before display

2. **If detections are added but not drawn**:
   - Check `video_processor.py` `draw_detections()` method
   - Verify coordinates are valid
   - Try changing box color to red: `BBOX_COLOR = (0, 0, 255)` in config.py
   - Increase thickness: `BBOX_THICKNESS = 5` in config.py

3. **If detections are NOT added**:
   - Check validation failures: Look for "Validation failed: N"
   - Check crop failures: Look for "Crop failed: N"
   - Temporarily disable ReID: Set `ENABLE_REID = False` in config.py
   - Lower thresholds further: `CONFIDENCE_THRESHOLD = 0.25` in config.py

---

## Quick Fixes to Try

### Fix 1: Disable ReID Temporarily
**File**: `config.py`
```python
ENABLE_REID = False  # Was True
```
**Purpose**: Rule out ReID as the cause

### Fix 2: Change Box Color to Red
**File**: `config.py`
```python
BBOX_COLOR = (0, 0, 255)  # Was (0, 255, 0)
```
**Purpose**: Rule out color visibility issue

### Fix 3: Make Boxes Thicker
**File**: `config.py`
```python
BBOX_THICKNESS = 5  # Was 2
```
**Purpose**: Make boxes more visible

### Fix 4: Lower Confidence Threshold
**File**: `config.py`
```python
CONFIDENCE_THRESHOLD = 0.25  # Was 0.4
```
**Purpose**: Catch more detections

### Fix 5: Simplify Validation
**File**: `face_detector.py`, method `is_valid_face_detection()`

Temporarily return `True` to bypass all validation:
```python
def is_valid_face_detection(self, bbox, confidence):
    return True  # Bypass validation for testing
```
**Purpose**: Rule out validation as the cause

---

## Debug Output Reference

### Normal Output (Working)
```
🔍 DEBUG FRAME 10
🔍 DEBUG: Raw YOLO detections: 2
   ✅ Passed: Track 1, bbox:(100,150,200,250), conf:0.85
   ✅ Passed: Track 2, bbox:(300,180,400,280), conf:0.72
🔍 DEBUG: Tracker output: 2 detections (filtered: 0)
🔍 DEBUG: Detections from tracker: 2
   ✅ Added to display list: Student 1, Track 1, bbox:(100,150,200,250), conf:0.85
   ✅ Added to display list: Student 2, Track 2, bbox:(300,180,400,280), conf:0.72
🔍 DEBUG: Final detections for display: 2
   Validation failed: 0
   Crop failed: 0
🔍 DEBUG: Drawing 2 detections on frame
```

### Problem Output (No Detections)
```
🔍 DEBUG FRAME 10
🔍 DEBUG: Raw YOLO detections: 0
🔍 DEBUG: Tracker output: 0 detections (filtered: 0)
🔍 DEBUG: Detections from tracker: 0
🔍 DEBUG: Final detections for display: 0
   Validation failed: 0
   Crop failed: 0
🔍 DEBUG: Drawing 0 detections on frame
```
**Diagnosis**: No faces detected by YOLO (normal for first few frames)

### Problem Output (Detections Filtered)
```
🔍 DEBUG FRAME 10
🔍 DEBUG: Raw YOLO detections: 3
   ❌ Filtered: Track 1, size:False, conf:True, aspect:True
   ❌ Filtered: Track 2, size:True, conf:False, aspect:True
   ✅ Passed: Track 3, bbox:(300,180,400,280), conf:0.72
🔍 DEBUG: Tracker output: 1 detections (filtered: 2)
🔍 DEBUG: Detections from tracker: 1
   ✅ Added to display list: Student 1, Track 3, bbox:(300,180,400,280), conf:0.72
🔍 DEBUG: Final detections for display: 1
   Validation failed: 0
   Crop failed: 0
🔍 DEBUG: Drawing 1 detections on frame
```
**Diagnosis**: Some detections filtered by size/confidence, but 1 should be visible

### Problem Output (Validation Fails)
```
🔍 DEBUG FRAME 10
🔍 DEBUG: Raw YOLO detections: 2
   ✅ Passed: Track 1, bbox:(100,150,200,250), conf:0.85
   ✅ Passed: Track 2, bbox:(300,180,400,280), conf:0.72
🔍 DEBUG: Tracker output: 2 detections (filtered: 0)
🔍 DEBUG: Detections from tracker: 2
   ❌ Validation failed for Track 1
   ❌ Validation failed for Track 2
🔍 DEBUG: Final detections for display: 0
   Validation failed: 2
   Crop failed: 0
🔍 DEBUG: Drawing 0 detections on frame
```
**Diagnosis**: Detections pass tracker but fail validation (check `is_valid_face_detection()`)

---

## Success Criteria

✅ **Test 1**: Green boxes visible on gray background
✅ **Test 2**: Green boxes track your face in webcam
✅ **Test 3**: Faces detected in video file
✅ **Test 4**: Main system shows boxes AND saves images

---

## Next Steps After Testing

1. **Run all 4 tests** in order
2. **Note which tests pass/fail**
3. **Check debug output** from Test 4
4. **Try quick fixes** based on results
5. **Report findings** with specific test results

---

## Common Issues and Solutions

### Issue: "No module named 'ultralytics'"
**Solution**: `pip3 install ultralytics`

### Issue: "No module named 'insightface'"
**Solution**: `pip3 install insightface onnxruntime`

### Issue: Webcam permission denied (Mac)
**Solution**: System Preferences → Security & Privacy → Camera → Enable for Terminal

### Issue: "Failed to open video source: 0"
**Solution**: 
- Try different camera index: `python3 main.py --source 1`
- Check if another app is using camera
- Restart Terminal/IDE

### Issue: Very low FPS
**Solution**:
- Lower `INFERENCE_SIZE` in config.py (try 320 or 416)
- Disable ReID: `ENABLE_REID = False`
- Use GPU if available: `DEVICE = "cuda:0"` in config.py

---

**Last Updated**: After implementing extended debug output
**Status**: Ready for systematic testing
