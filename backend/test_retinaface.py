import cv2
import numpy as np
from retinaface import RetinaFace

# Test RetinaFace installation
print("Testing RetinaFace...")
print(f"RetinaFace version: {RetinaFace.__version__ if hasattr(RetinaFace, '__version__') else 'Unknown'}")

# Create a simple test image
test_img = np.zeros((480, 640, 3), dtype=np.uint8)
test_img[:] = (128, 128, 128)  # Gray background

print("\nTest 1: Empty image")
try:
    result = RetinaFace.detect_faces(test_img, threshold=0.3)
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")

print("\nTest 2: Load a real image from uploads folder")
import os
upload_folder = "uploads"
if os.path.exists(upload_folder):
    files = [f for f in os.listdir(upload_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
    if files:
        test_file = os.path.join(upload_folder, files[0])
        print(f"Testing with: {test_file}")
        
        img = cv2.imread(test_file)
        if img is not None:
            print(f"Image shape: {img.shape}")
            print(f"Image dtype: {img.dtype}")
            print(f"Image range: {img.min()} - {img.max()}")
            
            # Convert to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Try detection
            try:
                result = RetinaFace.detect_faces(img_rgb, threshold=0.3)
                print(f"Detection result type: {type(result)}")
                print(f"Detection result: {result}")
                
                if isinstance(result, dict):
                    print(f"Number of faces: {len(result)}")
                    for key, face in result.items():
                        print(f"  {key}: {face}")
            except Exception as e:
                print(f"Detection error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("Failed to read image")
    else:
        print("No image files in uploads folder")
else:
    print("Uploads folder doesn't exist")

print("\nTest complete!")
