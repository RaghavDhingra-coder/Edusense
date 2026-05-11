# Quick Debug Reference

## 🚨 Current Issue
**No bounding boxes displayed** (but detection works - images are being saved)

---

## ⚡ Quick Test (30 seconds)

```bash
# Test if drawing works at all
python3 test_drawing.py
```
**Expected**: Window with 3 green boxes

**If this works**: Drawing function is fine
**If this fails**: OpenCV display issue

---

## ⚡ Quick Test 2 (1 minute)

```bash
# Test if YOLO detection works
python3 test_detection_visual.py
```
**Expected**: Webcam with green boxes around faces

**If this works**: YOLO + drawing works, issue is in main pipeline
**If this fails**: YOLO or webcam issue

---

## ⚡ Quick Fix 1: Disable ReID

**File**: `config.py`
```python
ENABLE_REID = False  # Change from True
```

**Then run**: `python3 main.py`

**Purpose**: Rule out ReID as the cause

---

## ⚡ Quick Fix 2: Make Boxes More Visible

**File**: `config.py`
```python
BBOX_COLOR = (0, 0, 255)  # Red instead of green
BBOX_THICKNESS = 5         # Thicker lines
```

**Then run**: `python3 main.py`

**Purpose**: Make boxes impossible to miss

---

## ⚡ Quick Fix 3: Lower Confidence

**File**: `config.py`
```python
CONFIDENCE_THRESHOLD = 0.25  # Very low
```

**Then run**: `python3 main.py`

**Purpose**: Catch more detections

---

## 🔍 What to Look For

When running `python3 main.py`, watch for:

### ✅ Good Signs
```
✨ New student: Student 1 (Track 1)
💾 Saved: Student 1 (Track 1, conf: 0.67)
✅ Added to display list: Student 1, Track 1, bbox:(100,150,200,250), conf:0.67
🔍 DEBUG: Drawing 1 detections on frame
```

### ❌ Bad Signs
```
🔍 DEBUG: Raw YOLO detections: 0
   ❌ Validation failed for Track 1
   ❌ Crop failed for Track 1
🔍 DEBUG: Final detections for display: 0
```

---

## 📋 Checklist

- [ ] Run `test_drawing.py` - Does it show boxes?
- [ ] Run `test_detection_visual.py` - Does it detect faces?
- [ ] Run `main.py` - Check console for "Added to display list"
- [ ] Try disabling ReID - Does it help?
- [ ] Try red/thick boxes - Are they visible?
- [ ] Check `students/` folder - Are images being saved?

---

## 🎯 Most Likely Causes

1. **Detections filtered out** - Check validation/crop failures in console
2. **Drawing not called** - Check if "Drawing N detections" shows N > 0
3. **Boxes drawn but not visible** - Try red color and thick lines
4. **ReID interfering** - Try disabling ReID

---

## 📞 Full Guide

See **TESTING_GUIDE.md** for complete troubleshooting steps

---

**Quick Start**: Run `python3 test_drawing.py` then `python3 test_detection_visual.py`
