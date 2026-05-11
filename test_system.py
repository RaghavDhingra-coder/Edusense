"""
Test script to verify system installation and basic functionality
"""

import sys
import cv2
import torch
from pathlib import Path


def test_imports():
    """Test if all required packages are installed"""
    print("=" * 60)
    print("🧪 Testing Package Imports")
    print("=" * 60)
    
    packages = {
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'PIL': 'Pillow',
        'ultralytics': 'Ultralytics'
    }
    
    all_passed = True
    
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: FAILED - {str(e)}")
            all_passed = False
    
    return all_passed


def test_cuda():
    """Test CUDA availability"""
    print("\n" + "=" * 60)
    print("🔥 Testing CUDA/GPU Support")
    print("=" * 60)
    
    cuda_available = torch.cuda.is_available()
    
    if cuda_available:
        print(f"✅ CUDA Available: Yes")
        print(f"   GPU Device: {torch.cuda.get_device_name(0)}")
        print(f"   CUDA Version: {torch.version.cuda}")
    else:
        print("⚠️  CUDA Available: No (will use CPU)")
        print("   For GPU acceleration, install CUDA and PyTorch with CUDA support")
    
    return True


def test_webcam():
    """Test webcam access"""
    print("\n" + "=" * 60)
    print("📹 Testing Webcam Access")
    print("=" * 60)
    
    cap = cv2.VideoCapture(0)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✅ Webcam: OK")
            print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
            cap.release()
            return True
        else:
            print("⚠️  Webcam opened but failed to read frame")
            cap.release()
            return False
    else:
        print("⚠️  Webcam: Not accessible")
        print("   The system can still process video files")
        return False


def test_yolo_model():
    """Test YOLOv8 model loading"""
    print("\n" + "=" * 60)
    print("🤖 Testing YOLOv8 Model")
    print("=" * 60)
    
    try:
        from ultralytics import YOLO
        
        print("🔄 Loading YOLOv8n model (this may take a moment)...")
        model = YOLO('yolov8n.pt')
        print("✅ YOLOv8 Model: OK")
        print("   Model will be downloaded on first run if not present")
        return True
    except Exception as e:
        print(f"❌ YOLOv8 Model: FAILED - {str(e)}")
        return False


def test_file_structure():
    """Test if all required files are present"""
    print("\n" + "=" * 60)
    print("📁 Testing File Structure")
    print("=" * 60)
    
    required_files = [
        'main.py',
        'face_detector.py',
        'image_manager.py',
        'video_processor.py',
        'config.py',
        'requirements.txt'
    ]
    
    all_present = True
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}: Present")
        else:
            print(f"❌ {file}: Missing")
            all_present = False
    
    return all_present


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🎓 CLASSROOM TRACKING SYSTEM - INSTALLATION TEST")
    print("=" * 60 + "\n")
    
    results = {
        'Imports': test_imports(),
        'CUDA': test_cuda(),
        'Webcam': test_webcam(),
        'YOLOv8': test_yolo_model(),
        'Files': test_file_structure()
    }
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Overall result
    critical_tests = ['Imports', 'YOLOv8', 'Files']
    critical_passed = all(results[test] for test in critical_tests)
    
    print("\n" + "=" * 60)
    if critical_passed:
        print("✅ SYSTEM READY")
        print("=" * 60)
        print("\nYou can now run the system:")
        print("  python main.py                    # Use webcam")
        print("  python main.py --source video.mp4 # Use video file")
    else:
        print("❌ SYSTEM NOT READY")
        print("=" * 60)
        print("\nPlease fix the failed tests above.")
        print("Run: pip install -r requirements.txt")
    
    print()


if __name__ == "__main__":
    main()
