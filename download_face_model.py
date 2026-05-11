"""
Helper script to download YOLOv8 face detection models
"""

import os
import sys
import urllib.request
from pathlib import Path


def download_file(url, filename):
    """
    Download a file with progress bar
    
    Args:
        url: URL to download from
        filename: Local filename to save to
    """
    def progress_hook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write(f"\r  Downloading: {percent}% [{count * block_size}/{total_size} bytes]")
        sys.stdout.flush()
    
    print(f"📥 Downloading {filename}...")
    urllib.request.urlretrieve(url, filename, progress_hook)
    print(f"\n✅ Downloaded: {filename}")


def main():
    """
    Download YOLOv8 face detection models
    """
    print("=" * 60)
    print("🎓 YOLOv8 Face Detection Model Downloader")
    print("=" * 60)
    print()
    
    # Model URLs (GitHub releases or Hugging Face)
    models = {
        'yolov8n-face.pt': {
            'url': 'https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8n-face.pt',
            'description': 'YOLOv8 Nano Face (fastest, good for real-time)',
            'size': '~6 MB'
        },
        'yolov8s-face.pt': {
            'url': 'https://github.com/akanametov/yolov8-face/releases/download/v0.0.0/yolov8s-face.pt',
            'description': 'YOLOv8 Small Face (better accuracy, still fast)',
            'size': '~22 MB'
        }
    }
    
    print("Available models:")
    print()
    for i, (model_name, info) in enumerate(models.items(), 1):
        print(f"{i}. {model_name}")
        print(f"   {info['description']}")
        print(f"   Size: {info['size']}")
        print()
    
    print("Which model would you like to download?")
    print("1 - yolov8n-face.pt (recommended for most users)")
    print("2 - yolov8s-face.pt (better accuracy)")
    print("3 - Both models")
    print("0 - Exit")
    print()
    
    try:
        choice = input("Enter your choice (0-3): ").strip()
        
        if choice == '0':
            print("Exiting...")
            return
        
        models_list = list(models.items())
        
        if choice == '1':
            to_download = [models_list[0]]
        elif choice == '2':
            to_download = [models_list[1]]
        elif choice == '3':
            to_download = models_list
        else:
            print("❌ Invalid choice")
            return
        
        print()
        print("=" * 60)
        
        for model_name, info in to_download:
            if Path(model_name).exists():
                print(f"⚠️  {model_name} already exists, skipping...")
                continue
            
            try:
                download_file(info['url'], model_name)
            except Exception as e:
                print(f"\n❌ Failed to download {model_name}: {str(e)}")
                print(f"   Please download manually from:")
                print(f"   {info['url']}")
        
        print()
        print("=" * 60)
        print("✅ Download complete!")
        print()
        print("Next steps:")
        print("1. Update config.py to use your preferred model:")
        print("   YOLO_MODEL = 'yolov8n-face.pt'  # or 'yolov8s-face.pt'")
        print("2. Run the system: python main.py")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Download cancelled")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
