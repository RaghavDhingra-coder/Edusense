"""
Quick test to verify YOLOv8-Face model loading with PyTorch 2.6+ fix
"""

import torch
import os

print("=" * 60)
print("Testing YOLOv8-Face Model Loading")
print("=" * 60)

# Step 1: Check if model file exists
print("\n1. Checking model file...")
if os.path.exists("yolov8n-face.pt"):
    size_mb = os.path.getsize("yolov8n-face.pt") / (1024 * 1024)
    print(f"   ✅ Model file exists: {size_mb:.2f} MB")
else:
    print("   ❌ Model file not found")
    print("   Run: python3 main.py (it will auto-download)")
    exit(1)

# Step 2: Apply PyTorch 2.6+ fix
print("\n2. Applying PyTorch 2.6+ compatibility fix...")
try:
    import torch.serialization
    from ultralytics.nn.tasks import DetectionModel
    from torch.nn.modules.container import Sequential
    from torch.nn import Module
    
    torch.serialization.add_safe_globals([
        DetectionModel,
        Sequential,
        Module,
    ])
    print("   ✅ Safe globals added")
except Exception as e:
    print(f"   ⚠️  Warning: {e}")

# Step 3: Load model with weights_only=False
print("\n3. Loading YOLOv8-Face model...")
try:
    from ultralytics import YOLO
    
    # Monkey-patch torch.load to use weights_only=False
    original_load = torch.load
    
    def safe_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    
    torch.load = safe_load
    
    model = YOLO("yolov8n-face.pt")
    
    torch.load = original_load
    
    print("   ✅ Model loaded successfully!")
    
except Exception as e:
    print(f"   ❌ Failed to load model: {e}")
    exit(1)

# Step 4: Test inference
print("\n4. Testing inference...")
try:
    import numpy as np
    
    # Create a dummy image
    dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
    
    # Run inference
    results = model(dummy_image, verbose=False)
    
    print("   ✅ Inference works!")
    
except Exception as e:
    print(f"   ❌ Inference failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nYour system is ready to use!")
print("Run: python3 main.py")
print("=" * 60)
