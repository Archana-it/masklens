"""
Detection Configuration File
Adjust these settings to fix face and mask detection issues
"""

# ========================================
# MASK DETECTION CONFIGURATION
# ========================================

# Toggle this if mask detection is backwards
# False = Model outputs high value (>0.5) for MASK
# True = Model outputs high value (>0.5) for NO MASK
INVERT_MASK_PREDICTION = False

# Mask detection threshold (0.0 to 1.0)
MASK_THRESHOLD = 0.5

# ========================================
# FACE DETECTION CONFIGURATION
# ========================================

# Standard detection parameters (good for clear, well-lit faces)
FACE_DETECTION_STANDARD = {
    "scaleFactor": 1.1,    # 1.1 = standard, lower = more sensitive
    "minNeighbors": 4,     # 4 = standard, lower = more detections
    "minSize": (30, 30),   # Minimum face size in pixels
    "maxSize": (500, 500)  # Maximum face size in pixels
}

# Aggressive detection parameters (for masked faces or poor lighting)
FACE_DETECTION_AGGRESSIVE = {
    "scaleFactor": 1.05,   # More sensitive
    "minNeighbors": 2,     # Less filtering
    "minSize": (20, 20),   # Smaller minimum
    "maxSize": (500, 500)
}

# Very aggressive detection (last resort)
FACE_DETECTION_VERY_AGGRESSIVE = {
    "scaleFactor": 1.03,   # Very sensitive
    "minNeighbors": 1,     # Minimal filtering
    "minSize": (15, 15),   # Very small minimum
    "maxSize": (500, 500)
}

# Enable/disable detection strategies
ENABLE_HISTOGRAM_EQUALIZATION = True  # Improves detection in poor lighting
ENABLE_CLAHE_ENHANCEMENT = True       # Contrast enhancement
ENABLE_ALTERNATIVE_CASCADE = True     # Use alternative face detector
ENABLE_DENOISING = False              # Slower but may help with noisy images

# ========================================
# EMOTION DETECTION CONFIGURATION
# ========================================

# Swap these if emotion predictions are backwards
EMOTION_LABELS_REGULAR = ["Happy", "Sad"]  # For faces without mask
EMOTION_LABELS_MASKED = ["Happy", "Sad"]   # For faces with mask

# Minimum confidence threshold (0.0 to 1.0)
# Predictions below this will be marked as uncertain
EMOTION_CONFIDENCE_THRESHOLD = 0.5

# ========================================
# DEBUGGING OPTIONS
# ========================================

# Enable verbose logging
VERBOSE_LOGGING = True

# Save detected faces for debugging
SAVE_DETECTED_FACES = False
DETECTED_FACES_DIR = "debug_faces"

# Print raw prediction values
PRINT_RAW_PREDICTIONS = True

# ========================================
# USAGE INSTRUCTIONS
# ========================================
"""
HOW TO FIX COMMON ISSUES:

1. FACE NOT DETECTED:
   - Lower scaleFactor (try 1.05 or 1.03)
   - Lower minNeighbors (try 2 or 1)
   - Lower minSize (try (20, 20) or (15, 15))
   - Enable ENABLE_HISTOGRAM_EQUALIZATION
   - Enable ENABLE_CLAHE_ENHANCEMENT

2. MASK DETECTION BACKWARDS:
   - Toggle INVERT_MASK_PREDICTION
   - Run test_detection.py to see raw values
   - If NO MASK gives high value (>0.5), set to True
   - If MASK gives high value (>0.5), set to False

3. EMOTION DETECTION BACKWARDS:
   - Swap EMOTION_LABELS_REGULAR
   - Change ["Happy", "Sad"] to ["Sad", "Happy"]
   - Do the same for EMOTION_LABELS_MASKED

4. TOO MANY FALSE DETECTIONS:
   - Increase scaleFactor (try 1.2 or 1.3)
   - Increase minNeighbors (try 5 or 6)
   - Increase minSize (try (40, 40) or (50, 50))

5. TESTING:
   Run: python test_detection.py
   - Press 'c' to capture and test
   - Press 't' to toggle mask logic
   - Press 'q' to quit
"""

# ========================================
# HELPER FUNCTIONS
# ========================================

def get_face_detection_params(strategy="standard"):
    """Get face detection parameters for a specific strategy"""
    if strategy == "standard":
        return FACE_DETECTION_STANDARD
    elif strategy == "aggressive":
        return FACE_DETECTION_AGGRESSIVE
    elif strategy == "very_aggressive":
        return FACE_DETECTION_VERY_AGGRESSIVE
    else:
        return FACE_DETECTION_STANDARD

def interpret_mask_prediction(raw_value):
    """Interpret raw mask prediction value"""
    if INVERT_MASK_PREDICTION:
        # High value = NO MASK
        is_mask = raw_value < MASK_THRESHOLD
    else:
        # High value = MASK
        is_mask = raw_value > MASK_THRESHOLD
    
    return "MASK" if is_mask else "NO MASK"

def get_emotion_labels(has_mask):
    """Get emotion labels based on mask status"""
    if has_mask:
        return EMOTION_LABELS_MASKED
    else:
        return EMOTION_LABELS_REGULAR

def log_detection(message, level="INFO"):
    """Log detection messages if verbose logging is enabled"""
    if VERBOSE_LOGGING:
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }.get(level, "ℹ️")
        print(f"{prefix} {message}")
