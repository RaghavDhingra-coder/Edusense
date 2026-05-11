# 🚀 Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Test Installation

```bash
python test_system.py
```

This will verify:
- ✅ All packages installed correctly
- ✅ GPU/CUDA availability
- ✅ Webcam access
- ✅ YOLOv8 model loading
- ✅ All files present

## Step 3: Run the System

### Option A: Use Webcam (Live Detection)

```bash
python main.py
```

### Option B: Use Video File

```bash
python main.py --source path/to/your/video.mp4
```

## Step 4: Interact

While running:
- **Press `q`** to quit
- **Press `s`** to show statistics

## Step 5: Check Results

Your student face images will be saved in:

```
students/
├── student_1/
│   ├── 2026-05-11_10-30-15.jpg
│   ├── 2026-05-11_10-30-16.jpg
│   └── ...
├── student_2/
└── student_3/
```

## Common Issues

### "CUDA not available"
- System will use CPU automatically
- For GPU: Install CUDA toolkit and PyTorch with CUDA

### "Failed to open video source"
- Check webcam is connected
- Try: `python main.py --source 1` (different camera)
- Verify video file path

### Low FPS
- Use GPU: `python main.py --device cuda:0`
- Or increase confidence: `python main.py --confidence 0.6`

## Next Steps

1. ✅ Test with your classroom video
2. ✅ Adjust settings in `config.py`
3. ✅ Review saved face crops in `students/` folder
4. ✅ Ready for Phase 2: Attention classification!

## Need Help?

Check the full README.md for:
- Detailed configuration options
- Troubleshooting guide
- Architecture overview
- Future expansion plans

---

**That's it! You're ready to track classroom faces! 🎓**
