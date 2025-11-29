import cv2
import numpy as np
import os

print("Testing OpenCV DNN Face Detector...")

# Load the model
DNN_MODEL_PATH = "res10_300x300_ssd_iter_140000.caffemodel"
DNN_CONFIG_PATH = "deploy.prototxt"

if not os.path.exists(DNN_MODEL_PATH):
    print(f"❌ Model file not found: {DNN_MODEL_PATH}")
    exit(1)

if not os.path.exists(DNN_CONFIG_PATH):
    print(f"❌ Config file not found: {DNN_CONFIG_PATH}")
    exit(1)

print("✅ Model files found")

try:
    face_net = cv2.dnn.readNetFromCaffe(DNN_CONFIG_PATH, DNN_MODEL_PATH)
    print("✅ DNN model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    exit(1)

# Test with an image from uploads
upload_folder = "uploads"
if os.path.exists(upload_folder):
    files = [f for f in os.listdir(upload_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
    if files:
        test_file = os.path.join(upload_folder, files[0])
        print(f"\nTesting with: {test_file}")
        
        img = cv2.imread(test_file)
        if img is not None:
            h, w = img.shape[:2]
            print(f"Image size: {w}x{h}")
            
            # Create blob
            blob = cv2.dnn.blobFromImage(
                img, 
                scalefactor=1.0, 
                size=(300, 300), 
                mean=(104.0, 177.0, 123.0),
                swapRB=False,
                crop=False
            )
            
            # Detect faces
            face_net.setInput(blob)
            detections = face_net.forward()
            
            print(f"\nDetections shape: {detections.shape}")
            print(f"Number of detections: {detections.shape[2]}")
            
            face_count = 0
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.5:
                    face_count += 1
                    x1 = int(detections[0, 0, i, 3] * w)
                    y1 = int(detections[0, 0, i, 4] * h)
                    x2 = int(detections[0, 0, i, 5] * w)
                    y2 = int(detections[0, 0, i, 6] * h)
                    print(f"  Face {face_count}: confidence={confidence:.3f}, bbox=({x1},{y1},{x2},{y2})")
            
            if face_count > 0:
                print(f"\n✅ SUCCESS: Detected {face_count} face(s)")
            else:
                print("\n⚠️ No faces detected with confidence > 0.5")
        else:
            print("❌ Failed to read image")
    else:
        print("No image files in uploads folder")
else:
    print("Uploads folder doesn't exist")

print("\n✅ Test complete!")
