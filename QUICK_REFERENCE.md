# Quick Reference Card - Robust Tracking System

## ⚡ Quick Start

```bash
# Run with default settings
python3 main_robust.py

# Run with video file
python3 main_robust.py --source classroom.mp4

# Fast mode (real-time)
python3 main_robust.py --preset fast

# Accurate mode (best quality)
python3 main_robust.py --preset accurate
```

---

## 🎮 Keyboard Controls

| Key | Action |
|-----|--------|
| `q` | Quit |
| `s` | Show statistics |
| `r` | Reset statistics |

---

## 🔧 Common Adjustments

### Too Many Duplicate IDs?

```python
# In config_robust.py
REID_SIMILARITY_THRESHOLD = 0.50  # Lower (was 0.55)
REID_COOLDOWN_PERIOD = 5.0        # Increase (was 3.0)
REID_SPATIAL_WEIGHT = 0.4         # Increase (was 0.3)
REID_EMBEDDING_WEIGHT = 0.4       # Decrease (was 0.5)
```

### Different Students Merged?

```python
# In config_robust.py
REID_SIMILARITY_THRESHOLD = 0.60  # Raise (was 0.55)
REID_QUALITY_THRESHOLD = 40.0     # Raise (was 30.0)
REID_OUTLIER_THRESHOLD = 0.5      # Raise (was 0.4)
```

### Too Slow?

```bash
# Use fast preset
python3 main_robust.py --preset fast
```

Or adjust:
```python
SKIP_FRAMES = 3              # Process every 3rd frame
INFERENCE_SIZE = 416         # Smaller (was 640)
REID_MAX_EMBEDDINGS = 5      # Fewer (was 10)
```

### Too Many Low-Quality Images?

```python
SAVE_MIN_CONFIDENCE = 0.6    # Raise (was 0.5)
REID_QUALITY_THRESHOLD = 40.0  # Raise (was 30.0)
```

---

## 🧹 Post-Processing

```bash
# 1. Generate report
python3 folder_cleanup.py --action report

# 2. Review report
cat cleanup_report.json

# 3. Merge duplicates (dry run first!)
python3 folder_cleanup.py --action merge --dry-run
python3 folder_cleanup.py --action merge

# 4. Split mixed folders
python3 folder_cleanup.py --action split --dry-run
python3 folder_cleanup.py --action split

# 5. Remove low-quality folders
python3 folder_cleanup.py --action clean --dry-run
python3 folder_cleanup.py --action clean
```

---

## 📊 Key Parameters

### Hybrid Matching Weights (must sum to 1.0)

```python
REID_EMBEDDING_WEIGHT = 0.5   # Face similarity
REID_SPATIAL_WEIGHT = 0.3     # Location proximity
REID_TEMPORAL_WEIGHT = 0.2    # Recently seen bonus
```

### Thresholds

```python
REID_SIMILARITY_THRESHOLD = 0.55    # Match threshold
REID_QUALITY_THRESHOLD = 30.0       # Min quality (0-100)
CONFIDENCE_THRESHOLD = 0.45         # Detection confidence
```

### Timing

```python
REID_COOLDOWN_PERIOD = 3.0          # Seconds before new ID
REID_LOST_TRACK_TIMEOUT = 5.0       # Grace period
SAVE_INTERVAL = 1.5                 # Seconds between saves
```

---

## 🎯 Presets

| Preset | FPS | Accuracy | Use Case |
|--------|-----|----------|----------|
| `fast` | ~20 | Medium | Real-time demos |
| `balanced` | ~15 | High | General use (default) |
| `accurate` | ~10 | Very High | Post-processing |
| `hackathon` | ~15 | High | Quick demos |

---

## 🐛 Debug Mode

```python
# In config_robust.py
SHOW_DEBUG_OVERLAY = True
DEBUG_OVERLAY_DURATION = 100  # First 100 frames
```

Shows:
- Detections count
- Valid detections
- New students
- Matched students
- Quality rejections
- Processing time

---

## 📈 Statistics

Press `s` during runtime to see:
- Total students
- Total images saved
- Frames processed
- Current FPS
- Per-student image counts
- ReID statistics
- Quality rejections
- Cooldown preventions

---

## 🔍 Console Logs

```
✨ New: Student 1 (Track 5, Q:45.2)
   → New student created with quality score 45.2

🔄 Match: Track 7 → Student 1 (score:0.72, emb:0.68)
   → Track matched to existing student

⏳ Cooldown active, delaying new student creation
   → Waiting before creating new ID

⚠️  Track 3 lost (Student 2) - grace period active
   → Track lost, keeping in memory

🔄 Track 3 recovered → Student 2
   → Lost track recovered

⚠️  Outlier embedding rejected (sim: 0.35)
   → Bad embedding filtered out
```

---

## 📁 File Structure

```
EduSence-ai/
├── main_robust.py           ← RUN THIS
├── face_reid_robust.py      ← Robust ReID
├── config_robust.py         ← Configuration
├── folder_cleanup.py        ← Post-processing
├── students/                ← Output
│   ├── student_1/
│   ├── student_2/
│   └── ...
└── cleanup_report.json      ← Generated report
```

---

## 🚨 Troubleshooting

### No faces detected
- Check lighting
- Lower `CONFIDENCE_THRESHOLD` to 0.3
- Check camera is working

### IDs keep changing
- Increase `REID_COOLDOWN_PERIOD` to 5.0
- Lower `REID_SIMILARITY_THRESHOLD` to 0.50
- Increase `REID_LOST_TRACK_TIMEOUT` to 10.0

### System too slow
- Use `--preset fast`
- Increase `SKIP_FRAMES` to 3
- Lower `INFERENCE_SIZE` to 416

### Too many folders
- Run `python3 folder_cleanup.py --action merge`
- Lower `REID_SIMILARITY_THRESHOLD`
- Increase `REID_COOLDOWN_PERIOD`

---

## 💡 Pro Tips

1. **Always run post-processing** after recording
2. **Use dry-run first** before cleanup actions
3. **Backup students folder** before cleanup
4. **Start with balanced preset** then tune
5. **Monitor statistics** with 's' key
6. **Good lighting** = better quality scores
7. **Stable camera** = better spatial matching

---

## 📞 Quick Help

**Problem:** Same student, multiple folders
**Solution:** `python3 folder_cleanup.py --action merge`

**Problem:** Multiple students, one folder
**Solution:** `python3 folder_cleanup.py --action split`

**Problem:** Too slow
**Solution:** `python3 main_robust.py --preset fast`

**Problem:** Poor accuracy
**Solution:** `python3 main_robust.py --preset accurate`

---

## 🎓 Remember

✅ Robust system = `main_robust.py`
✅ Old system = `main.py` (not recommended)
✅ Always use presets for quick setup
✅ Post-processing fixes remaining issues
✅ Tune parameters for your specific scenario

---

**Start here:** `python3 main_robust.py`
**Then:** `python3 folder_cleanup.py --action report`
**Finally:** Tune parameters as needed
