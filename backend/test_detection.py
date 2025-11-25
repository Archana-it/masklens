"""
Test script to diagnose face and mask detection issues
"""
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import sys

print("=" * 60)
print("MASKLENS DETECTION TEST SCRIPT")
print("=" * 60)

# Load models
print("\n1. Loading models...")
try:
    mask_model = load_model("mask_detection_model.h5")
    emotion_regular = load_model("emotion_model_regular.h5")
    emotion_masked = load_model("emotion_model_masked.h5")
    print("✅ All models loaded successfully")
    print(f"   - Mask model input shape: {mask_model.input_shape}")
    print(f"   - Regular emotion model input shape: {emotion_regular.input_shape}")
    print(f"   - Masked emotion model input shape: {emotion_masked.input_shape}")
except Exception as e:
    print(f"❌ Error loading models: {e}")
    sys.exit(1)

# Load face cascades
print("\n2. Loading face detection cascades...")
try:
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    face_cascade_alt = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_alt.xml"
    )
    print("✅ Face cascades loaded")
except Exception as e:
    print(f"❌ Error loading cascades: {e}")
    sys.exit(1)

# Test with webcam
print("\n3. Testing with webcam...")
print("   Press 'c' to capture and test")
print("   Press 'q' to quit")
print("   Press 't' to toggle mask prediction logic")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cannot open webcam")
    sys.exit(1)

INVERT_MASK_PREDICTION = False

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Cannot read frame")
        break
    
    # Convert to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
    
    # Draw rectangles around faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f"Face {w}x{h}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Display info
    cv2.putText(frame, f"Faces detected: {len(faces)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Invert mask logic: {INVERT_MASK_PREDICTION}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, "Press 'c' to test, 't' to toggle, 'q' to quit", (10, frame.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.imshow('MaskLens Detection Test', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord('t'):
        INVERT_MASK_PREDICTION = not INVERT_MASK_PREDICTION
        print(f"\n🔄 Toggled mask prediction logic to: {INVERT_MASK_PREDICTION}")
    elif key == ord('c'):
        print("\n" + "=" * 60)
        print("TESTING CURRENT FRAME")
        print("=" * 60)
        
        # Test face detection
        print(f"\n📸 Frame size: {frame.shape}")
        print(f"🔍 Faces detected: {len(faces)}")
        
        if len(faces) == 0:
            print("❌ No face detected - trying alternative strategies...")
            
            # Try different strategies
            strategies = [
                ("Aggressive", {"scaleFactor": 1.05, "minNeighbors": 3, "minSize": (20, 20)}),
                ("Very Aggressive", {"scaleFactor": 1.03, "minNeighbors": 2, "minSize": (15, 15)}),
                ("Equalized", {"scaleFactor": 1.1, "minNeighbors": 4, "minSize": (30, 30)}),
            ]
            
            for name, params in strategies:
                if name == "Equalized":
                    test_gray = cv2.equalizeHist(gray)
                else:
                    test_gray = gray
                
                test_faces = face_cascade.detectMultiScale(test_gray, **params)
                print(f"   Strategy '{name}': {len(test_faces)} faces")
                
                if len(test_faces) > 0:
                    faces = test_faces
                    print(f"   ✅ Using strategy '{name}'")
                    break
        
        if len(faces) > 0:
            # Get largest face
            faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            (x, y, w, h) = faces_sorted[0]
            face = frame[y:y+h, x:x+w]
            
            print(f"\n✅ Face extracted: {face.shape}")
            
            # Test mask detection
            print("\n🎭 Testing mask detection...")
            mask_face = cv2.resize(face, (128, 128))
            mask_face = mask_face.astype("float32") / 255.0
            mask_face = np.expand_dims(mask_face, axis=0)
            
            mask_pred = mask_model.predict(mask_face, verbose=0)[0][0]
            print(f"   Raw mask prediction: {mask_pred:.4f}")
            print(f"   Invert logic: {INVERT_MASK_PREDICTION}")
            
            if INVERT_MASK_PREDICTION:
                mask_detected = mask_pred < 0.5
                print(f"   Logic: pred < 0.5 = MASK")
            else:
                mask_detected = mask_pred > 0.5
                print(f"   Logic: pred > 0.5 = MASK")
            
            mask_status = "MASK" if mask_detected else "NO MASK"
            print(f"   ✅ Result: {mask_status}")
            
            # Test emotion detection
            print(f"\n😊 Testing emotion detection...")
            if mask_detected:
                print("   Using MASKED emotion model (128x128)")
                selected_model = emotion_masked
                input_size = 128
            else:
                print("   Using REGULAR emotion model (48x48)")
                selected_model = emotion_regular
                input_size = 48
            
            emo_face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
            emo_face = cv2.resize(emo_face, (input_size, input_size))
            emo_face = emo_face.astype("float32") / 255.0
            emo_face = np.expand_dims(emo_face, axis=-1)
            emo_face = np.expand_dims(emo_face, axis=0)
            
            emotion_pred = selected_model.predict(emo_face, verbose=0)
            emotion_idx = np.argmax(emotion_pred[0])
            emotion_label = ["Happy", "Sad"][emotion_idx]
            confidence = emotion_pred[0][emotion_idx]
            
            print(f"   Raw predictions: {emotion_pred[0]}")
            print(f"   ✅ Emotion: {emotion_label} (confidence: {confidence:.2%})")
            
            print("\n" + "=" * 60)
            print(f"FINAL RESULT: {mask_status} + {emotion_label}")
            print("=" * 60)
        else:
            print("❌ Could not detect face with any strategy")

cap.release()
cv2.destroyAllWindows()
print("\n✅ Test completed")
