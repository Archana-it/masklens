"""
Test script to verify that non-face images are properly rejected
"""
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import sys

print("=" * 70)
print("TESTING: Non-Face Rejection")
print("=" * 70)

# Load models
print("\nLoading models...")
try:
    mask_model = load_model("mask_detection_model.h5")
    emotion_regular = load_model("emotion_model_regular.h5")
    emotion_masked = load_model("emotion_model_masked.h5")
    print("✅ Models loaded\n")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Load face cascades
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
face_cascade_alt = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt.xml")

print("Opening webcam...")
print("\nInstructions:")
print("1. First, show your FACE - press SPACE to test")
print("2. Then, hold PAPER/OBJECT - press SPACE to test")
print("3. Press 'q' to quit\n")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cannot open webcam")
    sys.exit(1)

test_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces with current settings
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    
    # Draw rectangles
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, "FACE DETECTED", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Display status
    if len(faces) > 0:
        cv2.putText(frame, f"Status: FACE DETECTED ({len(faces)})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "Status: NO FACE DETECTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.putText(frame, "Press SPACE to test, 'q' to quit", (10, frame.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.imshow('Non-Face Rejection Test', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord(' '):
        test_count += 1
        print("\n" + "=" * 70)
        print(f"TEST #{test_count}")
        print("=" * 70)
        
        # Run all detection strategies
        print("\nRunning detection strategies:")
        
        strategies = [
            ("Standard", {"scaleFactor": 1.1, "minNeighbors": 5, "minSize": (40, 40)}),
            ("Moderate", {"scaleFactor": 1.08, "minNeighbors": 4, "minSize": (35, 35)}),
            ("Aggressive", {"scaleFactor": 1.05, "minNeighbors": 3, "minSize": (30, 30)}),
        ]
        
        all_faces = []
        for name, params in strategies:
            detected = face_cascade.detectMultiScale(gray, **params)
            print(f"   Strategy '{name}': {len(detected)} face(s)")
            if len(detected) > 0 and len(all_faces) == 0:
                all_faces = detected
        
        # Try equalization
        if len(all_faces) == 0:
            equalized = cv2.equalizeHist(gray)
            detected = face_cascade.detectMultiScale(equalized, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))
            print(f"   Strategy 'Equalized': {len(detected)} face(s)")
            if len(detected) > 0:
                all_faces = detected
        
        # Try alternative cascade
        if len(all_faces) == 0:
            detected = face_cascade_alt.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))
            print(f"   Strategy 'Alt Cascade': {len(detected)} face(s)")
            if len(detected) > 0:
                all_faces = detected
        
        # Try CLAHE
        if len(all_faces) == 0:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            detected = face_cascade.detectMultiScale(enhanced, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))
            print(f"   Strategy 'CLAHE': {len(detected)} face(s)")
            if len(detected) > 0:
                all_faces = detected
        
        print("\n" + "-" * 70)
        
        if len(all_faces) == 0:
            print("❌ RESULT: NO FACE DETECTED")
            print("✅ System correctly rejected non-face image")
            print("\nThis is CORRECT behavior for:")
            print("   - Paper/objects")
            print("   - Covered faces")
            print("   - No person in frame")
            print("\nPrediction would be: ERROR - No face detected")
        else:
            print(f"✅ RESULT: FACE DETECTED ({len(all_faces)} face(s))")
            print("✅ System would proceed with emotion prediction")
            
            # Get largest face
            faces_sorted = sorted(all_faces, key=lambda f: f[2] * f[3], reverse=True)
            (x, y, w, h) = faces_sorted[0]
            print(f"\nFace region: {w}x{h} pixels at position ({x}, {y})")
            print("Prediction would proceed normally")
        
        print("=" * 70)

cap.release()
cv2.destroyAllWindows()

print("\n✅ Test completed")
print(f"Total tests run: {test_count}")
