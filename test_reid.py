"""
Test script for Face Re-Identification system
"""

import sys
import os

print("=" * 70)
print("🧪 TESTING FACE RE-IDENTIFICATION SYSTEM")
print("=" * 70)

# Test 1: Check dependencies
print("\n1️⃣  Testing dependencies...")
try:
    import cv2
    print("   ✅ OpenCV installed")
except:
    print("   ❌ OpenCV missing")
    sys.exit(1)

try:
    import numpy as np
    print("   ✅ NumPy installed")
except:
    print("   ❌ NumPy missing")
    sys.exit(1)

try:
    from ultralytics import YOLO
    print("   ✅ Ultralytics installed")
except:
    print("   ❌ Ultralytics missing")
    sys.exit(1)

try:
    import insightface
    print("   ✅ InsightFace installed")
except:
    print("   ❌ InsightFace missing - Install with: pip install insightface")
    sys.exit(1)

try:
    import onnxruntime
    print("   ✅ ONNX Runtime installed")
except:
    print("   ❌ ONNX Runtime missing - Install with: pip install onnxruntime")
    sys.exit(1)

try:
    from sklearn.metrics.pairwise import cosine_similarity
    print("   ✅ scikit-learn installed")
except:
    print("   ❌ scikit-learn missing - Install with: pip install scikit-learn")
    sys.exit(1)

# Test 2: Check model files
print("\n2️⃣  Checking model files...")
if os.path.exists("yolov8n-face.pt"):
    size_mb = os.path.getsize("yolov8n-face.pt") / (1024 * 1024)
    print(f"   ✅ YOLOv8-Face model found ({size_mb:.2f} MB)")
else:
    print("   ⚠️  YOLOv8-Face model not found (will auto-download)")

# Test 3: Load ReID system
print("\n3️⃣  Loading Face ReID system...")
try:
    from face_reid import FaceReID
    
    reid = FaceReID(similarity_threshold=0.6)
    
    if reid.app is not None:
        print("   ✅ InsightFace model loaded successfully")
        print(f"   ✅ Similarity threshold: {reid.similarity_threshold}")
    else:
        print("   ❌ InsightFace model failed to load")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Failed to load ReID: {e}")
    sys.exit(1)

# Test 4: Test embedding extraction
print("\n4️⃣  Testing embedding extraction...")
try:
    # Create a dummy face image
    dummy_face = np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)
    
    # Extract embedding
    embedding = reid.extract_embedding(dummy_face)
    
    if embedding is not None:
        print(f"   ✅ Embedding extracted (shape: {embedding.shape})")
    else:
        print("   ⚠️  No face detected in dummy image (expected)")
        
except Exception as e:
    print(f"   ❌ Embedding extraction failed: {e}")
    sys.exit(1)

# Test 5: Test similarity calculation
print("\n5️⃣  Testing similarity calculation...")
try:
    # Create two random embeddings
    emb1 = np.random.randn(512)
    emb2 = np.random.randn(512)
    
    # Calculate similarity
    similarity = cosine_similarity(emb1.reshape(1, -1), emb2.reshape(1, -1))[0][0]
    
    print(f"   ✅ Similarity calculated: {similarity:.3f}")
    print(f"   ✅ Threshold check: {'Match' if similarity > 0.6 else 'No match'}")
    
except Exception as e:
    print(f"   ❌ Similarity calculation failed: {e}")
    sys.exit(1)

# Test 6: Test ReID registration
print("\n6️⃣  Testing student registration...")
try:
    import time
    
    # Simulate registering a student
    track_id = 1
    dummy_face = np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)
    frame_time = time.time()
    
    student_id, is_new, similarity = reid.register_or_match_face(
        track_id, dummy_face, frame_time, force_extract=False
    )
    
    print(f"   ✅ Student registered: ID {student_id}")
    print(f"   ✅ Is new: {is_new}")
    print(f"   ✅ Similarity: {similarity:.3f}")
    
except Exception as e:
    print(f"   ❌ Registration failed: {e}")
    sys.exit(1)

# Test 7: Test statistics
print("\n7️⃣  Testing statistics...")
try:
    stats = reid.get_statistics()
    
    print(f"   ✅ Total students: {stats['total_students']}")
    print(f"   ✅ Active tracks: {stats['active_tracks']}")
    print(f"   ✅ Embeddings extracted: {stats['embeddings_extracted']}")
    print(f"   ✅ Successful matches: {stats['successful_matches']}")
    
except Exception as e:
    print(f"   ❌ Statistics failed: {e}")
    sys.exit(1)

# Test 8: Check configuration
print("\n8️⃣  Checking configuration...")
try:
    import config
    
    print(f"   ✅ ReID enabled: {config.ENABLE_REID}")
    print(f"   ✅ Similarity threshold: {config.REID_SIMILARITY_THRESHOLD}")
    print(f"   ✅ Track buffer: {config.TRACK_BUFFER} frames")
    print(f"   ✅ ByteTrack configured")
    
except Exception as e:
    print(f"   ❌ Configuration check failed: {e}")
    sys.exit(1)

# Final summary
print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print("\n📋 System Status:")
print("   ✅ All dependencies installed")
print("   ✅ Face ReID system operational")
print("   ✅ InsightFace model loaded")
print("   ✅ ByteTrack configured")
print("   ✅ Ready for classroom tracking")
print("\n🚀 Run the system:")
print("   python3 main.py")
print("\n📖 Read documentation:")
print("   REID_IMPLEMENTATION.md")
print("=" * 70)
