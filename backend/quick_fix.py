"""
Quick Fix Script for Face and Mask Detection Issues
This script helps you find the right settings for your system
"""

import cv2
import numpy as np
from tensorflow.keras.models import load_model
import sys
import os

print("=" * 70)
print("MASKLENS DETECTION QUICK FIX")
print("=" * 70)
print("\nThis script will help you fix face and mask detection issues.")
print("Follow the prompts to test and adjust settings.\n")

# Load models
print("Loading models...")
try:
    mask_model = load_model("mask_detection_model.h5")
    emotion_regular = load_model("emotion_model_regular.h5")
    emotion_masked = load_model("emotion_model_masked.h5")
    print("✅ Models loaded\n")
except Exception as e:
    print(f"❌ Error loading models: {e}")
    sys.exit(1)

# Load face cascades
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
face_cascade_alt = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt.xml")

# Configuration
config = {
    "invert_mask": False,
    "scale_factor": 1.1,
    "min_neighbors": 4,
    "min_size": 30
}

def test_face_detection(frame, gray):
    """Test face detection with current settings"""
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=config["scale_factor"],
        minNeighbors=config["min_neighbors"],
        minSize=(config["min_size"], config["min_size"])
    )
    return faces

def test_mask_detection(face_img):
    """Test mask detection"""
    mask_face = cv2.resize(face_img, (128, 128))
    mask_face = mask_face.astype("float32") / 255.0
    mask_face = np.expand_dims(mask_face, axis=0)
    
    mask_pred = mask_model.predict(mask_face, verbose=0)[0][0]
    
    if config["invert_mask"]:
        mask_detected = mask_pred < 0.5
    else:
        mask_detected = mask_pred > 0.5
    
    return mask_pred, "MASK" if mask_detected else "NO MASK"

def test_emotion_detection(face_img, is_mask):
    """Test emotion detection"""
    if is_mask:
        model = emotion_masked
        size = 128
    else:
        model = emotion_regular
        size = 48
    
    emo_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    emo_face = cv2.resize(emo_face, (size, size))
    emo_face = emo_face.astype("float32") / 255.0
    emo_face = np.expand_dims(emo_face, axis=-1)
    emo_face = np.expand_dims(emo_face, axis=0)
    
    emotion_pred = model.predict(emo_face, verbose=0)
    emotion_idx = np.argmax(emotion_pred[0])
    emotion_label = ["Happy", "Sad"][emotion_idx]
    confidence = emotion_pred[0][emotion_idx]
    
    return emotion_label, confidence, emotion_pred[0]

# Main testing loop
print("Opening webcam...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Cannot open webcam")
    sys.exit(1)

print("\n" + "=" * 70)
print("CONTROLS:")
print("=" * 70)
print("SPACE    - Capture and test current frame")
print("i        - Toggle mask inversion logic")
print("s        - Decrease scale factor (more sensitive)")
print("S        - Increase scale factor (less sensitive)")
print("n        - Decrease min neighbors (more detections)")
print("N        - Increase min neighbors (fewer detections)")
print("m        - Decrease min size (detect smaller faces)")
print("M        - Increase min size (detect larger faces)")
print("r        - Reset to default settings")
print("q        - Quit")
print("=" * 70 + "\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = test_face_detection(frame, gray)
    
    # Draw faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    # Display settings
    y_pos = 30
    cv2.putText(frame, f"Faces: {len(faces)}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    y_pos += 30
    cv2.putText(frame, f"Scale: {config['scale_factor']:.2f}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    y_pos += 25
    cv2.putText(frame, f"Neighbors: {config['min_neighbors']}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    y_pos += 25
    cv2.putText(frame, f"MinSize: {config['min_size']}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    y_pos += 25
    cv2.putText(frame, f"Invert: {config['invert_mask']}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    cv2.imshow('Quick Fix - Press SPACE to test', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord(' '):  # Space bar
        print("\n" + "=" * 70)
        print("TESTING CURRENT FRAME")
        print("=" * 70)
        
        if len(faces) == 0:
            print("❌ No face detected")
            print("\nSuggestions:")
            print("  - Press 's' to make detection more sensitive")
            print("  - Press 'n' to reduce filtering")
            print("  - Press 'm' to detect smaller faces")
            print("  - Ensure good lighting and face camera directly")
        else:
            # Get largest face
            faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            (x, y, w, h) = faces_sorted[0]
            face = frame[y:y+h, x:x+w]
            
            print(f"✅ Face detected: {w}x{h} pixels")
            
            # Test mask detection
            mask_pred, mask_status = test_mask_detection(face)
            print(f"\n🎭 Mask Detection:")
            print(f"   Raw value: {mask_pred:.4f}")
            print(f"   Invert logic: {config['invert_mask']}")
            print(f"   Result: {mask_status}")
            
            if mask_status == "MASK":
                print("   ℹ️  If you're NOT wearing a mask, press 'i' to toggle")
            else:
                print("   ℹ️  If you ARE wearing a mask, press 'i' to toggle")
            
            # Test emotion detection
            is_mask = mask_status == "MASK"
            emotion, confidence, raw_pred = test_emotion_detection(face, is_mask)
            print(f"\n😊 Emotion Detection:")
            print(f"   Model: {'Masked' if is_mask else 'Regular'}")
            print(f"   Raw predictions: Happy={raw_pred[0]:.4f}, Sad={raw_pred[1]:.4f}")
            print(f"   Result: {emotion} ({confidence:.2%})")
            
            print("\n" + "=" * 70)
            print(f"FINAL: {mask_status} + {emotion}")
            print("=" * 70)
    
    elif key == ord('i'):
        config["invert_mask"] = not config["invert_mask"]
        print(f"\n🔄 Mask inversion: {config['invert_mask']}")
    
    elif key == ord('s'):
        config["scale_factor"] = max(1.01, config["scale_factor"] - 0.02)
        print(f"\n📉 Scale factor: {config['scale_factor']:.2f} (more sensitive)")
    
    elif key == ord('S'):
        config["scale_factor"] = min(1.5, config["scale_factor"] + 0.02)
        print(f"\n📈 Scale factor: {config['scale_factor']:.2f} (less sensitive)")
    
    elif key == ord('n'):
        config["min_neighbors"] = max(1, config["min_neighbors"] - 1)
        print(f"\n📉 Min neighbors: {config['min_neighbors']} (more detections)")
    
    elif key == ord('N'):
        config["min_neighbors"] = min(10, config["min_neighbors"] + 1)
        print(f"\n📈 Min neighbors: {config['min_neighbors']} (fewer detections)")
    
    elif key == ord('m'):
        config["min_size"] = max(10, config["min_size"] - 5)
        print(f"\n📉 Min size: {config['min_size']} (smaller faces)")
    
    elif key == ord('M'):
        config["min_size"] = min(100, config["min_size"] + 5)
        print(f"\n📈 Min size: {config['min_size']} (larger faces)")
    
    elif key == ord('r'):
        config = {
            "invert_mask": False,
            "scale_factor": 1.1,
            "min_neighbors": 4,
            "min_size": 30
        }
        print("\n🔄 Reset to default settings")

cap.release()
cv2.destroyAllWindows()

# Save configuration
print("\n" + "=" * 70)
print("FINAL CONFIGURATION")
print("=" * 70)
print(f"INVERT_MASK_PREDICTION = {config['invert_mask']}")
print(f"scaleFactor = {config['scale_factor']:.2f}")
print(f"minNeighbors = {config['min_neighbors']}")
print(f"minSize = ({config['min_size']}, {config['min_size']})")
print("\nUpdate these values in backend/app.py:")
print(f"  Line 45: INVERT_MASK_PREDICTION = {config['invert_mask']}")
print(f"  Line ~200: scaleFactor={config['scale_factor']:.2f}, minNeighbors={config['min_neighbors']}, minSize=({config['min_size']}, {config['min_size']})")
print("=" * 70)
