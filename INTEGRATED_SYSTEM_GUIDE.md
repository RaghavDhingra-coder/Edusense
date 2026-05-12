# 🎓 EduSence AI - Integrated System Guide

## Overview

The integrated system combines camera streaming, face detection, tracking, and analytics into **ONE unified web dashboard**.

### Key Features

✅ **Single Command Launch** - Run everything with `python3 integrated_server.py`  
✅ **Web-Based Interface** - No separate OpenCV windows  
✅ **Live Video Stream** - See processed frames in browser  
✅ **Real-Time Stats** - FPS, faces detected, students tracked  
✅ **Preserved Logic** - ALL existing detection/tracking/analytics logic intact  
✅ **Same Accuracy** - No reduction in detection or pose estimation quality  

---

## 🚀 Quick Start

### 1. Start the Integrated Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start integrated server (port 8080)
python3 integrated_server.py

# Or specify custom port
python3 integrated_server.py --port 8081
```

### 2. Open Dashboard

Open your browser and navigate to:
```
http://localhost:8080
```

### 3. Start Camera

1. Click **"Start Camera"** button in the dashboard
2. Allow camera access if prompted
3. See live processed video feed with:
   - Face detection bounding boxes
   - Student IDs
   - Real-time FPS counter
   - Active face count
   - Total students tracked

### 4. Analyze Engagement

1. Let the camera run to collect student face data
2. Click **"Analyze Classroom"** button
3. View engagement analytics:
   - Overall classroom statistics
   - Individual student cards
   - Head pose data (yaw, pitch, roll)
   - Focus/distraction status

### 5. Stop Camera

Click **"Stop Camera"** when done

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│         INTEGRATED WEB DASHBOARD (Port 8080)            │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Live Video Feed (MJPEG Stream)                   │  │
│  │  • Processed frames with bounding boxes           │  │
│  │  • Student IDs overlaid                           │  │
│  │  • Real-time FPS and stats                        │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Camera Controls                                   │  │
│  │  • Start Camera                                    │  │
│  │  • Stop Camera                                     │  │
│  │  • Analyze Classroom                               │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Analytics Dashboard                               │  │
│  │  • Summary cards                                   │  │
│  │  • Engagement distribution                         │  │
│  │  • Individual student cards                        │  │
│  │  • Head pose debugging info                        │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│         FLASK SERVER (integrated_server.py)             │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Camera Processing Thread                          │ │
│  │  • Runs in background                              │ │
│  │  • Preserves ALL existing logic from main.py      │ │
│  │  • YOLOv8 face detection                           │ │
│  │  • ByteTrack tracking                              │ │
│  │  • InsightFace ReID                                │ │
│  │  • Image saving                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Analytics Engine                                  │ │
│  │  • HybridAttentivenessAnalyzer                     │ │
│  │  • Head pose estimation (MediaPipe)                │ │
│  │  • Attentiveness classification                    │ │
│  │  • Identity merger                                 │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  API Endpoints                                     │ │
│  │  • /api/video_feed - MJPEG stream                  │ │
│  │  • /api/camera/start - Start camera                │ │
│  │  • /api/camera/stop - Stop camera                  │ │
│  │  • /api/camera/status - Get stats                  │ │
│  │  • /api/analyze - Run analytics                    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Details

### Preserved Components

The integrated system **PRESERVES ALL EXISTING LOGIC**:

1. **Face Detection** - Exact same YOLOv8 detection from `face_detector.py`
2. **Tracking** - Same ByteTrack implementation
3. **ReID** - Same InsightFace embedding matching from `face_reid.py`
4. **Image Saving** - Same quality filtering and saving logic
5. **Analytics** - Same `HybridAttentivenessAnalyzer` with head pose
6. **Thresholds** - All detection/tracking/pose thresholds unchanged

### What Changed

Only the **delivery mechanism** changed:

- **Before**: OpenCV window (`cv2.imshow`)
- **After**: Web browser (MJPEG stream)

The processing pipeline is **IDENTICAL**.

### Threading Architecture

```python
Main Thread (Flask)
├── Handles HTTP requests
├── Serves web dashboard
└── Manages API endpoints

Background Thread (Camera Processing)
├── Reads camera frames
├── Runs detection (YOLOv8)
├── Runs tracking (ByteTrack)
├── Runs ReID (InsightFace)
├── Saves images
├── Draws annotations
└── Updates latest frame for streaming
```

**Thread Safety:**
- Frame access protected by `threading.Lock()`
- Camera start/stop protected by `camera_lock`
- No race conditions or deadlocks

---

## 📡 API Endpoints

### Camera Control

#### Start Camera
```http
POST /api/camera/start
```

**Response:**
```json
{
  "success": true,
  "message": "Camera started successfully"
}
```

#### Stop Camera
```http
POST /api/camera/stop
```

**Response:**
```json
{
  "success": true,
  "message": "Camera stopped"
}
```

#### Camera Status
```http
GET /api/camera/status
```

**Response:**
```json
{
  "success": true,
  "status": {
    "running": true,
    "fps": 28.5,
    "frame_number": 1234,
    "active_tracks": 5,
    "total_students": 8,
    "total_images": 456
  }
}
```

### Video Streaming

#### Video Feed
```http
GET /api/video_feed
```

Returns MJPEG stream of processed frames.

### Analytics

#### Analyze Classroom
```http
POST /api/analyze
```

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_students": 10,
    "focused_students": 7,
    "unfocused_students": 3,
    "average_engagement": 72.5
  },
  "students": [...]
}
```

---

## 🎯 Usage Workflow

### Typical Session

1. **Launch Server**
   ```bash
   python3 integrated_server.py
   ```

2. **Open Dashboard**
   - Browser: `http://localhost:8080`

3. **Start Camera**
   - Click "Start Camera"
   - See live video feed
   - Watch students being detected and tracked
   - Student IDs assigned automatically

4. **Collect Data**
   - Let camera run for 2-5 minutes
   - System saves face crops automatically
   - Monitor stats: FPS, faces, students, images

5. **Analyze Engagement**
   - Click "Analyze Classroom"
   - Wait for processing (~10-30 seconds)
   - View results:
     - Overall engagement percentage
     - Focused vs. unfocused students
     - Individual student cards
     - Head pose data

6. **Stop Camera**
   - Click "Stop Camera" when done

---

## 🔍 Debugging

### Check Logs

The server logs show:
- Camera start/stop events
- Frame processing
- Detection counts
- ReID matches
- Analytics progress

```bash
# Run with verbose logging
python3 integrated_server.py

# Watch logs
tail -f logs/integrated_server.log
```

### Common Issues

#### Camera Won't Start

**Problem:** "Failed to open camera"

**Solutions:**
- Check camera is not in use by another app
- Try different camera index: modify `video_source=0` to `video_source=1`
- Check camera permissions

#### Video Feed Not Loading

**Problem:** Black screen or "Camera Not Started"

**Solutions:**
- Click "Start Camera" button
- Check browser console for errors
- Verify URL: `http://localhost:8080/api/video_feed`
- Try refreshing page

#### Low FPS

**Problem:** FPS < 10

**Solutions:**
- Close other applications
- Use GPU: ensure CUDA is available
- Reduce camera resolution in code
- Check CPU usage

#### No Students Detected

**Problem:** "No student folders found"

**Solutions:**
- Start camera first to collect data
- Let camera run for at least 1-2 minutes
- Check `students/` folder exists
- Verify faces are being detected (check video feed)

---

## ⚙️ Configuration

### Camera Settings

Edit `integrated_server.py`:

```python
# Camera resolution
self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Camera FPS
self.cap.set(cv2.CAP_PROP_FPS, 30)
```

### Detection Thresholds

Edit `config.py` (same as before):

```python
# Face detection
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45

# ReID
REID_SIMILARITY_THRESHOLD = 0.55
REID_QUALITY_THRESHOLD = 30.0
```

### Analytics Thresholds

Edit `integrated_server.py` in `get_analytics_engine()`:

```python
analytics_engine = HybridAttentivenessAnalyzer(
    students_dir='students',
    focus_threshold=0.65,      # 65% focused = "Focused"
    yaw_threshold=30.0,        # ±30° sideways
    pitch_threshold=30.0,      # ±30° up/down
    roll_threshold=35.0,       # ±35° head tilt
    consecutive_distraction_threshold=2
)
```

### Server Port

```bash
# Default port 8080
python3 integrated_server.py

# Custom port
python3 integrated_server.py --port 5000
```

---

## 📊 Performance

### Expected Performance

| Metric | Value |
|--------|-------|
| FPS (CPU) | 15-25 |
| FPS (GPU) | 25-35 |
| Latency | < 100ms |
| Memory | ~500MB |
| CPU Usage | 30-50% |

### Optimization Tips

1. **Use GPU**
   - Ensure CUDA is available
   - Check: `torch.cuda.is_available()`

2. **Reduce Resolution**
   - Lower camera resolution
   - Faster processing, lower quality

3. **Adjust Frame Skip**
   - Process every Nth frame
   - Add in `_process_loop()`

4. **Close Other Apps**
   - Free up CPU/GPU resources

---

## 🆚 Comparison: Standalone vs Integrated

| Feature | Standalone (main.py) | Integrated (integrated_server.py) |
|---------|---------------------|-----------------------------------|
| **Launch** | `python3 main.py` | `python3 integrated_server.py` |
| **Interface** | OpenCV window | Web browser |
| **Terminals** | 2 (tracking + analytics) | 1 (unified) |
| **Video Display** | cv2.imshow() | MJPEG stream |
| **Analytics** | Separate command | Same dashboard |
| **Detection Logic** | ✅ Preserved | ✅ Preserved |
| **Tracking Logic** | ✅ Preserved | ✅ Preserved |
| **ReID Logic** | ✅ Preserved | ✅ Preserved |
| **Analytics Logic** | ✅ Preserved | ✅ Preserved |
| **Accuracy** | ✅ Same | ✅ Same |
| **Demo-Friendly** | ❌ Separate windows | ✅ Single dashboard |

---

## 🎓 Use Cases

### 1. Live Classroom Monitoring

```bash
# Start server
python3 integrated_server.py

# Open on projector/screen
# URL: http://localhost:8080

# Start camera
# Monitor live feed
# Analyze periodically
```

### 2. Demo/Presentation

```bash
# Start server
python3 integrated_server.py

# Open in browser
# Share screen
# Show live detection
# Show analytics
```

### 3. Research Data Collection

```bash
# Start server
python3 integrated_server.py

# Start camera
# Let run for session duration
# Stop camera
# Analyze results
# Export data
```

---

## 🔐 Security Notes

### Local Network Only

By default, server binds to `0.0.0.0:8080` (all interfaces).

**For production:**
```bash
# Bind to localhost only
python3 integrated_server.py --host 127.0.0.1
```

### Camera Access

- Browser will request camera permission
- Grant access for video feed to work
- Camera is accessed via OpenCV, not browser API

### Data Privacy

- All processing is local
- No cloud upload
- Student images saved to `students/` folder
- Secure folder permissions recommended

---

## 🚀 Next Steps

### Enhancements

Possible future improvements:

1. **Recording** - Save video with annotations
2. **Alerts** - Real-time distraction alerts
3. **Export** - CSV/PDF reports
4. **Multi-Camera** - Support multiple cameras
5. **Authentication** - Login system
6. **Database** - Store analytics history

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## ❓ FAQ

**Q: Does this replace main.py?**  
A: No, both work. Use `main.py` for standalone, `integrated_server.py` for web dashboard.

**Q: Is the accuracy the same?**  
A: Yes, 100%. All detection/tracking/analytics logic is preserved.

**Q: Can I use a video file instead of webcam?**  
A: Yes, modify `video_source=0` to `video_source='video.mp4'` in `CameraSystem.__init__()`.

**Q: Why port 8080?**  
A: Matches existing frontend configuration. Can be changed with `--port`.

**Q: Can I run on a server?**  
A: Yes, but ensure camera is accessible. May need X11 forwarding or virtual display.

---

**Built for seamless classroom monitoring. One command. One dashboard. Full functionality.**

🚀 **Get started:** `python3 integrated_server.py`
