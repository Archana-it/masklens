"""
Improved prediction function with better face and mask detection
Copy this function to replace the one in app.py if needed
"""

def predict_emotion_from_path_improved(image_path):
    """
    Improved version with better logging and detection
    """
    print("\n" + "="*60)
    print("=== PREDICTION STARTED ===")
    print("="*60)
    
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print("❌ ERROR: Could not read image")
        return None, "Image read error"
    
    print(f"✅ Image loaded: {img.shape}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # ========================================
    # FACE DETECTION - Multiple Strategies
    # ========================================
    print("\n🔍 FACE DETECTION:")
    faces = []
    strategy_used = None
    
    strategies = [
        {
            "name": "Standard",
            "cascade": face_cascade,
            "image": gray,
            "params": {"scaleFactor": 1.1, "minNeighbors": 4, "minSize": (30, 30)}
        },
        {
            "name": "Aggressive",
            "cascade": face_cascade,
            "image": gray,
            "params": {"scaleFactor": 1.05, "minNeighbors": 3, "minSize": (20, 20)}
        },
        {
            "name": "Very Aggressive",
            "cascade": face_cascade,
            "image": gray,
            "params": {"scaleFactor": 1.03, "minNeighbors": 2, "minSize": (15, 15)}
        },
        {
            "name": "Equalized",
            "cascade": face_cascade,
            "image": cv2.equalizeHist(gray),
            "params": {"scaleFactor": 1.1, "minNeighbors": 3, "minSize": (25, 25)}
        },
        {
            "name": "Alternative Cascade",
            "cascade": face_cascade_alt,
            "image": gray,
            "params": {"scaleFactor": 1.1, "minNeighbors": 3, "minSize": (25, 25)}
        },
        {
            "name": "Alt + Equalized",
            "cascade": face_cascade_alt,
            "image": cv2.equalizeHist(gray),
            "params": {"scaleFactor": 1.05, "minNeighbors": 2, "minSize": (20, 20)}
        },
        {
            "name": "CLAHE Enhanced",
            "cascade": face_cascade,
            "image": cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(gray),
            "params": {"scaleFactor": 1.1, "minNeighbors": 3, "minSize": (25, 25)}
        },
    ]
    
    for strategy in strategies:
        detected = strategy["cascade"].detectMultiScale(
            strategy["image"],
            **strategy["params"]
        )
        print(f"   Strategy '{strategy['name']}': {len(detected)} face(s)")
        
        if len(detected) > 0:
            faces = detected
            strategy_used = strategy["name"]
            print(f"   ✅ Using strategy: {strategy_used}")
            break
    
    # Check if face was detected
    if len(faces) == 0:
        print("❌ NO FACE DETECTED with any strategy")
        print("   Suggestions:")
        print("   - Ensure face is clearly visible")
        print("   - Improve lighting")
        print("   - Face camera directly")
        print("   - Move closer to camera")
        return None, "No face detected. Please ensure your face is clearly visible and well-lit."
    
    # Get largest face
    faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    (x, y, w, h) = faces_sorted[0]
    face = img[y:y+h, x:x+w]
    
    print(f"✅ Face extracted: {w}x{h} pixels at position ({x}, {y})")
    
    if face.size == 0:
        print("❌ ERROR: Invalid face region")
        return None, "Invalid face region"
    
    # ========================================
    # MASK DETECTION
    # ========================================
    print("\n🎭 MASK DETECTION:")
    try:
        # Prepare face for mask detection (128x128 RGB)
        mask_face = cv2.resize(face, (128, 128))
        mask_face = mask_face.astype("float32") / 255.0
        mask_face = np.expand_dims(mask_face, axis=0)
        
        # Predict mask
        mask_pred = mask_model.predict(mask_face, verbose=0)[0][0]
        print(f"   Raw prediction value: {mask_pred:.4f}")
        print(f"   Invert logic: {INVERT_MASK_PREDICTION}")
        
        # Interpret prediction
        if INVERT_MASK_PREDICTION:
            # High value = NO MASK, Low value = MASK
            mask_detected = mask_pred < 0.5
            print(f"   Logic: value < 0.5 = MASK, value > 0.5 = NO MASK")
        else:
            # High value = MASK, Low value = NO MASK
            mask_detected = mask_pred > 0.5
            print(f"   Logic: value > 0.5 = MASK, value < 0.5 = NO MASK")
        
        mask_status = "MASK" if mask_detected else "NO MASK"
        print(f"   ✅ Result: {mask_status}")
        
        # Select appropriate emotion model
        if mask_detected:
            selected_model = emotion_masked
            input_size = 128
            labels = masked_labels
            print(f"   📊 Using MASKED emotion model (128x128)")
        else:
            selected_model = emotion_regular
            input_size = 48
            labels = regular_labels
            print(f"   📊 Using REGULAR emotion model (48x48)")
        
    except Exception as e:
        print(f"❌ ERROR in mask detection: {str(e)}")
        return None, f"Mask detection error: {str(e)}"
    
    # ========================================
    # EMOTION DETECTION
    # ========================================
    print("\n😊 EMOTION DETECTION:")
    try:
        # Prepare face for emotion detection (grayscale)
        emo_face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        emo_face = cv2.resize(emo_face, (input_size, input_size))
        emo_face = emo_face.astype("float32") / 255.0
        emo_face = np.expand_dims(emo_face, axis=-1)
        emo_face = np.expand_dims(emo_face, axis=0)
        
        # Predict emotion
        emotion_pred = selected_model.predict(emo_face, verbose=0)
        print(f"   Raw predictions: {emotion_pred[0]}")
        print(f"   Labels: {labels}")
        
        emotion_idx = np.argmax(emotion_pred[0])
        emotion_label = labels[emotion_idx]
        confidence = emotion_pred[0][emotion_idx]
        
        print(f"   ✅ Predicted: {emotion_label} (confidence: {confidence:.2%})")
        
    except Exception as e:
        print(f"❌ ERROR in emotion detection: {str(e)}")
        return None, f"Emotion detection error: {str(e)}"
    
    # ========================================
    # FINAL RESULT
    # ========================================
    print("\n" + "="*60)
    print(f"FINAL RESULT: {mask_status} + {emotion_label} ({confidence:.2%})")
    print("="*60 + "\n")
    
    return {
        "mask_status": mask_status,
        "emotion": emotion_label,
        "confidence": float(confidence),
        "face_detection_strategy": strategy_used,
        "mask_prediction_raw": float(mask_pred)
    }, None
