from flask_cors import CORS
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import numpy as np
import cv2
import os
import sqlite3
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)

# ====== Admin-only decorator ======
def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        # Check if JWT identity has a role
        if isinstance(identity, dict):
            role = identity.get("role", "user")
        else:
            role = "user"
        if role != "admin":
            return jsonify({"error": "Admin access only"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__  # Required for Flask routes
    return wrapper

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ====== JWT CONFIG ======
app.config["JWT_SECRET_KEY"] = "your-very-secret-key"  # change this to a strong secret in prod
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)  # adjust as needed
jwt = JWTManager(app)

# Handle JWT errors
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print("JWT ERROR: Token has expired")
    return jsonify({"error": "Token has expired", "msg": "Token has expired"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"JWT ERROR: Invalid token - {str(error)}")
    return jsonify({"error": "Invalid token", "msg": str(error)}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"JWT ERROR: Missing token - {str(error)}")
    return jsonify({"error": "Authorization token is missing", "msg": str(error)}), 401

# ====== Paths & DB ======
DB_PATH = "database.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ====== Model Configuration ======
# If mask detection is inverted, change this to True
INVERT_MASK_PREDICTION = False  # Set to True if mask detection is backwards

# ====== Initialize DB (users + emotions) ======
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT
        )
    """)

    # Check if role column exists, if not add it
    cur.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'role' not in columns:
        print("Adding role column to users table...")
        cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        print("Role column added successfully!")

    # Create default admin (only if not exists)
    cur.execute("SELECT * FROM users WHERE email = 'admin@gmail.com'")
    admin_exists = cur.fetchone()

    if not admin_exists:
        admin_pass = generate_password_hash("admin123")
        cur.execute(
            "INSERT INTO users (fullname, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Admin", "admin@gmail.com", admin_pass, "admin", datetime.now().isoformat())
        )
        print("Default admin user created!")

    # Emotions table (linked to user)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            emotion TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ====== Helper DB functions ======
def get_db_conn():
    return sqlite3.connect(DB_PATH)

def save_emotion(user_id, filename, emotion):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO emotions (user_id, filename, emotion, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, filename, emotion, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def create_user(fullname, email, password):
    pwd_hash = generate_password_hash(password)
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (fullname, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (fullname, email, pwd_hash, datetime.now().isoformat())
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id

def find_user_by_email(email):
    conn = get_db_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row

# ====== Existing prediction code (unchanged behavior) ======
try:
    # =======================
# LOAD MODELS (NEW LOGIC)
# =======================

    print("Loading mask + emotion models...")

    mask_model = load_model("mask_detection_model.h5")
    emotion_regular = load_model("emotion_model_regular.h5")
    emotion_masked = load_model("emotion_model_masked.h5")

    regular_labels = ["Happy", "Sad"]
    masked_labels  = ["Happy", "Sad"]

    # Load multiple face detection cascades for better mask detection
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    
    # Alternative cascade that might work better with masks
    try:
        face_cascade_alt = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_alt.xml"
        )
        print("Alternative face cascade loaded")
    except:
        face_cascade_alt = None
        print("Alternative face cascade not available")

    print("Models and face cascade loaded successfully!")

    # print("Loading emotion model...")
    # # Try the regular model first
    # model = load_model("emotion_model_regular.h5")
    # print("Regular model loaded successfully!")
    # print("Model input shape:", model.input_shape)
    # print("Model summary:")
    # model.summary()
    # class_names = ["Happy", "Sad"]
    
except Exception as e:
    print(f"ERROR loading model: {e}")
    # try:                                                 i changed here! Load Models
    #     print("Trying masked model...")
    #     model = load_model("emotion_model_masked.h5")
    #     print("Masked model loaded successfully!")
    #     print("Model input shape:", model.input_shape)
    #     print("Model summary:")
    #     model.summary()
    #     class_names = ["Happy", "Sad"]
    # except Exception as e2:
    #     print(f"ERROR loading masked model: {e2}")
    #     model = None

# face_cascade = cv2.CascadeClassifier(
#     cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
# )
# print(f"Face cascade loaded: {not face_cascade.empty()}")

# def predict_emotion_from_path(image_path):                         Function changes
#     img = cv2.imread(image_path)
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#     faces = face_cascade.detectMultiScale(gray, 1.3, 5)
#     if len(faces) == 0:
#         return None

#     x, y, w, h = faces[0]
#     face = gray[y:y+h, x:x+w]
    
#     # Try different preprocessing approaches
#     try:
#         # Method 1: 48x48 with channel dimension
#         face_48 = cv2.resize(face, (48, 48))
#         face_48 = face_48.astype("float32") / 255.0
#         face_48 = np.expand_dims(face_48, axis=0)
#         face_48 = np.expand_dims(face_48, axis=-1)
        
#         pred = model.predict(face_48)
#         emotion = class_names[int(np.argmax(pred))]
#         return emotion
        
#     except Exception as e1:
#         print(f"Method 1 failed: {e1}")
#         try:
#             # Method 2: Flattened 48x48
#             face_flat = cv2.resize(face, (48, 48))
#             face_flat = face_flat.astype("float32") / 255.0
#             face_flat = face_flat.flatten()
#             face_flat = np.expand_dims(face_flat, axis=0)
            
#             pred = model.predict(face_flat)
#             emotion = class_names[int(np.argmax(pred))]
#             return emotion
            
#         except Exception as e2:
#             print(f"Method 2 failed: {e2}")
#             try:
#                 # Method 3: Different size (224x224 flattened = 50176, close to 25088)
#                 face_224 = cv2.resize(face, (158, 158))  # 158*158 = 24964 ≈ 25088
#                 face_224 = face_224.astype("float32") / 255.0
#                 face_224 = face_224.flatten()
#                 face_224 = np.expand_dims(face_224, axis=0)
                
#                 pred = model.predict(face_224)
#                 emotion = class_names[int(np.argmax(pred))]
#                 return emotion
                
#             except Exception as e3:
#                 print(f"Method 3 failed: {e3}")
#                 print("All preprocessing methods failed")
#                 return None

def predict_emotion_from_path(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None, "Image read error"

    orig = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Try multiple face detection strategies for better mask detection
    faces = []
    
    # Strategy 1: Standard parameters
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    print(f"Strategy 1: Found {len(faces)} faces")
    
    # Strategy 2: More sensitive parameters for masked faces
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, 1.1, 3, minSize=(30, 30))
        print(f"Strategy 2: Found {len(faces)} faces")
    
    # Strategy 3: Even more lenient parameters
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, 1.05, 2, minSize=(20, 20))
        print(f"Strategy 3: Found {len(faces)} faces")
    
    # Strategy 4: Try with histogram equalization (better for poor lighting)
    if len(faces) == 0:
        equalized = cv2.equalizeHist(gray)
        faces = face_cascade.detectMultiScale(equalized, 1.2, 4, minSize=(30, 30))
        print(f"Strategy 4 (equalized): Found {len(faces)} faces")
    
    # Strategy 5: Try with different scale factors
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, 1.4, 3, minSize=(25, 25), maxSize=(300, 300))
        print(f"Strategy 5: Found {len(faces)} faces")
    
    # Strategy 6: Try alternative cascade if available
    if len(faces) == 0 and face_cascade_alt is not None:
        faces = face_cascade_alt.detectMultiScale(gray, 1.2, 4, minSize=(30, 30))
        print(f"Strategy 6 (alt cascade): Found {len(faces)} faces")
    
    # Strategy 7: Very aggressive detection for masks
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, 1.02, 1, minSize=(15, 15), maxSize=(500, 500))
        print(f"Strategy 7 (aggressive): Found {len(faces)} faces")

    if len(faces) == 0:
        print("Face detection failed with all strategies")
        print("Using fallback: analyzing entire image")
        # Fallback: use center portion of the image
        h, w = img.shape[:2]
        # Use center 70% of the image as face region
        margin_h, margin_w = int(h * 0.15), int(w * 0.15)
        face = img[margin_h:h-margin_h, margin_w:w-margin_w]
        print(f"Fallback face region size: {face.shape}")
    else:
        print(f"Face detected with {len(faces)} face(s) found")
        # Sort faces by area (largest first) to get the most prominent face
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        (x, y, w, h) = faces[0]  # Use the largest face
        face = img[y:y+h, x:x+w]
        
        print(f"Face region: {x}, {y}, {w}, {h}")
        print(f"Face size: {face.shape}")
    
    # Ensure face region is valid
    if face.size == 0:
        return None, "Invalid face region detected"

    # -------------------------
    # 1. MASK PREDICTION (128x128x3)
    # -------------------------
    try:
        mask_face = cv2.resize(face, (128, 128))
        mask_face = mask_face.astype("float32") / 255.0
        mask_face = np.expand_dims(mask_face, axis=0)

        print(f"Mask prediction input shape: {mask_face.shape}")
        mask_pred = mask_model.predict(mask_face)[0][0]
        print(f"Mask prediction raw value: {mask_pred}")
        
        # Try both interpretations of the mask model
        # Some models output 0 for mask, 1 for no mask
        # Others output 1 for mask, 0 for no mask
        
        # Let's test both thresholds and see which makes more sense
        interpretation_1 = "MASK" if mask_pred < 0.5 else "NO MASK"
        interpretation_2 = "MASK" if mask_pred > 0.5 else "NO MASK"
        
        print(f"Interpretation 1 (< 0.5 = MASK): {interpretation_1}")
        print(f"Interpretation 2 (> 0.5 = MASK): {interpretation_2}")
        
        # Apply mask detection logic (configurable in case model is inverted)
        if INVERT_MASK_PREDICTION:
            mask_detected = mask_pred < 0.5
        else:
            mask_detected = mask_pred > 0.5
            
        if mask_detected:
            mask_status = "MASK"
            selected_model = emotion_masked
            input_size = 128
            labels = masked_labels
        else:
            mask_status = "NO MASK"
            selected_model = emotion_regular
            input_size = 48
            labels = regular_labels

        print(f"Final detected mask status: {mask_status}")
        print(f"Using model for: {mask_status}")
        print(f"Selected input size: {input_size}")

        # -------------------------
        # 2. EMOTION PREDICTION
        # -------------------------
        emo_face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        emo_face = cv2.resize(emo_face, (input_size, input_size))
        emo_face = emo_face.astype("float32") / 255.0
        emo_face = np.expand_dims(emo_face, axis=-1)
        emo_face = np.expand_dims(emo_face, axis=0)

        print(f"Emotion prediction input shape: {emo_face.shape}")
        emotion_pred = selected_model.predict(emo_face)
        emotion_label = labels[np.argmax(emotion_pred)]
        print(f"Emotion prediction: {emotion_label}")

        return {
            "mask_status": mask_status,
            "emotion": emotion_label
        }, None
        
    except Exception as e:
        print(f"Error in prediction pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, f"Prediction error: {str(e)}"

# ====== Auth routes ======
@app.route("/register", methods=["POST"])
def register():
    """
    JSON body: { "fullname": "...", "email": "...", "password": "..." }
    """
    data = request.get_json(force=True)
    fullname = data.get("fullname")
    email = data.get("email")
    password = data.get("password")

    if not fullname or not email or not password:
        return jsonify({"error": "fullname, email and password are required"}), 400

    # Check if user exists
    if find_user_by_email(email) is not None:
        return jsonify({"error": "Email already registered"}), 400

    user_id = create_user(fullname, email, password)
    return jsonify({"message": "User created", "user_id": user_id}), 201

@app.route("/login", methods=["POST"])
def login():
    """
    JSON body: { "email": "...", "password": "..." }
    Returns: { access_token: "...", role: "...", fullname: "..." }
    """
    data = request.get_json(force=True)
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    user = find_user_by_email(email)
    if user is None:
        return jsonify({"error": "Invalid credentials"}), 401

    # Re-fetch user details including role
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash, role, fullname FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "Invalid credentials"}), 401

    user_id = row[0]
    password_hash = row[1]
    role = row[2] if len(row) > 2 else "user"
    fullname = row[3] if len(row) > 3 else "User"

    if not check_password_hash(password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Create access token with identity = user_id (must be string)
    access_token = create_access_token(identity=str(user_id))
    print(f"LOGIN SUCCESS: Created token for user_id {user_id}, role: {role}")
    print(f"Token created: {access_token[:50]}...")

    return jsonify({
        "access_token": access_token,
        "role": role,
        "fullname": fullname
    }), 200

# ====== Protected prediction endpoint ======
@app.route("/predict", methods=["POST"])
@jwt_required()  # require JWT for prediction
def predict():
    """
    Protected endpoint. Use Authorization: Bearer <access_token>
    Body: multipart/form-data with `image` file
    """
    print("=== PREDICT ENDPOINT CALLED ===")
    print(f"Request files: {request.files}")
    print(f"Request form: {request.form}")
    
    if "image" not in request.files:
        print("ERROR: No image in request.files")
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    print(f"File received: {file.filename}, size: {file.content_length}")
    
    # sanitize filename if you want (not included here)
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    print(f"File saved to: {file_path}")

    try:
        # Check if models are loaded
        if mask_model is None or emotion_regular is None or emotion_masked is None:
            print("ERROR: Models not loaded")
            return jsonify({"error": "Models not loaded. Check server logs."}), 500
            
        result, error = predict_emotion_from_path(file_path)
        if error:
            return jsonify({"error": error}), 400
         # Get user ID from JWT
        user_id = int(get_jwt_identity())
        print(f"User ID from JWT: {user_id}")

        # Save emotion only (DB stores emotion only)
        save_emotion(user_id, file.filename, result["emotion"])
        print(f"Emotion saved to database")

        return jsonify({
            "mask_status": result["mask_status"],
            "emotion": result["emotion"]
        }), 200
        #print(f"Emotion predicted: {emotion}")
        
        # if emotion is None:
        #     print("ERROR: No face detected in image")
        #     return jsonify({"error": "No face detected"}), 400

        # get current user id from JWT (convert back to int)
        # user_id = int(get_jwt_identity())
        # print(f"User ID from JWT: {user_id}")

        # save record linked to user
        # save_emotion(user_id, file.filename, emotion)
        # print(f"Emotion saved to database")

        # print(f"Returning prediction: {emotion}")
        # return jsonify({"prediction": emotion}), 200
    
    except Exception as e:
        print(f"ERROR in prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@app.route("/weekly_summary", methods=["GET"])
@jwt_required()
def weekly_summary():
    user_id = int(get_jwt_identity())

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch last 7 days of user emotion data
    cur.execute("""
        SELECT emotion, timestamp 
        FROM emotions
        WHERE user_id = ? 
          AND timestamp >= datetime('now', '-7 days')
        ORDER BY timestamp ASC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return jsonify({"message": "No data for weekly summary"}), 200

    # Count emotions
    emotion_count = {}
    daily_data = {}  # For graphing

    for row in rows:
        emotion = row["emotion"]
        date_only = row["timestamp"].split("T")[0]

        # Daily grouping
        if date_only not in daily_data:
            daily_data[date_only] = {"Happy": 0, "Sad": 0}

        daily_data[date_only][emotion] += 1

        # Weekly overall count
        if emotion not in emotion_count:
            emotion_count[emotion] = 0
        emotion_count[emotion] += 1

    # Most predicted emotion
    most_frequent = max(emotion_count, key=emotion_count.get)

    # Quotes based on emotion
    quotes = {
        "Sad": [
            "It's okay to feel sad. You are stronger than you think.",
            "Every day may not be good, but there’s something good in every day.",
            "Keep going — brighter days are coming."
        ],
        "Happy": [
            "Keep smiling! Happiness looks great on you!",
            "Your positive energy is contagious!",
            "Stay awesome! You're doing great!"
        ]
    }

    import random
    quote = random.choice(quotes[most_frequent])

    return jsonify({
        "most_frequent": most_frequent,
        "daily_graph": daily_data,
        "quote": quote
    })

# ====== Optional: route to get current user's predictions ======
@app.route("/my_emotions", methods=["GET"])
@jwt_required()
def my_emotions():
    user_id = int(get_jwt_identity())
    conn = get_db_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, filename, emotion, timestamp FROM emotions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    results = [dict(r) for r in rows]
    return jsonify({"emotions": results})

# ====== Admin Routes ======
def get_user_role(user_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def admin_required(f):
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = int(get_jwt_identity())
        print(f"Admin check - User ID: {user_id}")
        role = get_user_role(user_id)
        print(f"Admin check - User role: {role}")
        if role != 'admin':
            print(f"Access denied - Role '{role}' is not 'admin'")
            return jsonify({"error": "Admin access required"}), 403
        print("Admin access granted")
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route("/admin/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    print("=== ADMIN DASHBOARD ENDPOINT CALLED ===")
    user_id = int(get_jwt_identity())
    print(f"User ID from JWT: {user_id}")
    
    conn = get_db_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get total users
    cur.execute("SELECT COUNT(*) as total FROM users WHERE role = 'user'")
    total_users = cur.fetchone()['total']
    
    # Get total emotions
    cur.execute("SELECT COUNT(*) as total FROM emotions")
    total_emotions = cur.fetchone()['total']
    
    # Get emotions by type
    cur.execute("SELECT emotion, COUNT(*) as count FROM emotions GROUP BY emotion")
    emotion_stats = [dict(row) for row in cur.fetchall()]
    
    # Get recent users (last 10)
    cur.execute("SELECT id, fullname, email, created_at FROM users WHERE role = 'user' ORDER BY created_at DESC LIMIT 10")
    recent_users = [dict(row) for row in cur.fetchall()]
    
    # Get daily emotion counts for last 30 days
    cur.execute("""
        SELECT DATE(timestamp) as date, emotion, COUNT(*) as count 
        FROM emotions 
        WHERE timestamp >= datetime('now', '-30 days')
        GROUP BY DATE(timestamp), emotion
        ORDER BY date DESC
    """)
    daily_emotions = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return jsonify({
        "total_users": total_users,
        "total_emotions": total_emotions,
        "emotion_stats": emotion_stats,
        "recent_users": recent_users,
        "daily_emotions": daily_emotions
    })

@app.route("/admin/users", methods=["GET"])
@admin_required
def admin_get_users():
    conn = get_db_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, fullname, email, role, created_at FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({"users": users})

@app.route("/admin/users/create", methods=["POST"])
@admin_required
def admin_create_user():
    """
    Admin endpoint to create new users with specific roles
    JSON body: { "fullname": "...", "email": "...", "password": "...", "role": "user" or "admin" }
    """
    data = request.get_json(force=True)
    fullname = data.get("fullname")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")  # Default to 'user' if not specified

    if not fullname or not email or not password:
        return jsonify({"error": "fullname, email and password are required"}), 400

    # Validate role
    if role not in ["user", "admin"]:
        return jsonify({"error": "Role must be 'user' or 'admin'"}), 400

    # Check if user exists
    if find_user_by_email(email) is not None:
        return jsonify({"error": "Email already registered"}), 400

    # Create user with specified role
    pwd_hash = generate_password_hash(password)
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (fullname, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (fullname, email, pwd_hash, role, datetime.now().isoformat())
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()

    return jsonify({
        "message": "User created successfully",
        "user_id": user_id,
        "role": role
    }), 201

@app.route("/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def admin_delete_user(user_id):
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Delete user's emotions first
    cur.execute("DELETE FROM emotions WHERE user_id = ?", (user_id,))
    
    # Delete user
    cur.execute("DELETE FROM users WHERE id = ? AND role = 'user'", (user_id,))
    
    if cur.rowcount == 0:
        conn.close()
        return jsonify({"error": "User not found or cannot delete admin"}), 404
    
    conn.commit()
    conn.close()
    return jsonify({"message": "User deleted successfully"})

@app.route("/admin/emotions", methods=["GET"])
@admin_required
def admin_get_emotions():
    conn = get_db_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id, e.filename, e.emotion, e.timestamp, u.fullname, u.email
        FROM emotions e
        JOIN users u ON e.user_id = u.id
        ORDER BY e.timestamp DESC
        LIMIT 100
    """)
    emotions = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({"emotions": emotions})

@app.route("/admin/emotions/<int:emotion_id>", methods=["DELETE"])
@admin_required
def admin_delete_emotion(emotion_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM emotions WHERE id = ?", (emotion_id,))
    
    if cur.rowcount == 0:
        conn.close()
        return jsonify({"error": "Emotion record not found"}), 404
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Emotion record deleted successfully"})

@app.route("/admin/toggle_mask_logic", methods=["POST"])
@admin_required
def toggle_mask_logic():
    """
    Admin endpoint to toggle mask detection logic if it's inverted
    """
    global INVERT_MASK_PREDICTION
    INVERT_MASK_PREDICTION = not INVERT_MASK_PREDICTION
    
    return jsonify({
        "message": "Mask detection logic toggled",
        "invert_mask_prediction": INVERT_MASK_PREDICTION,
        "current_logic": "< 0.5 = MASK" if INVERT_MASK_PREDICTION else "> 0.5 = MASK"
    }), 200

@app.route("/debug/mask_detection", methods=["POST"])
@jwt_required()
def debug_mask_detection():
    """
    Debug endpoint to test mask detection specifically
    """
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    file_path = os.path.join(UPLOAD_FOLDER, f"mask_debug_{file.filename}")
    file.save(file_path)
    
    try:
        img = cv2.imread(file_path)
        if img is None:
            return jsonify({"error": "Could not read image"}), 400
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Try to detect face
        faces = face_cascade.detectMultiScale(gray, 1.1, 3, minSize=(30, 30))
        
        if len(faces) == 0:
            # Use center region as fallback
            h, w = img.shape[:2]
            margin_h, margin_w = int(h * 0.15), int(w * 0.15)
            face = img[margin_h:h-margin_h, margin_w:w-margin_w]
            face_method = "fallback_center"
        else:
            (x, y, w, h) = faces[0]
            face = img[y:y+h, x:x+w]
            face_method = "face_detection"
        
        # Test mask prediction
        mask_face = cv2.resize(face, (128, 128))
        mask_face = mask_face.astype("float32") / 255.0
        mask_face = np.expand_dims(mask_face, axis=0)
        
        mask_pred = mask_model.predict(mask_face)[0][0]
        
        results = {
            "face_detection_method": face_method,
            "face_region_size": f"{face.shape[1]}x{face.shape[0]}",
            "mask_prediction_raw": float(mask_pred),
            "interpretation_1_lt_05": "MASK" if mask_pred < 0.5 else "NO MASK",
            "interpretation_2_gt_05": "MASK" if mask_pred > 0.5 else "NO MASK",
            "current_logic_result": "MASK" if mask_pred > 0.5 else "NO MASK",
            "confidence": float(abs(mask_pred - 0.5) * 2)  # Distance from 0.5, scaled to 0-1
        }
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({"error": f"Mask debug failed: {str(e)}"}), 500

@app.route("/debug/face_detection", methods=["POST"])
@jwt_required()
def debug_face_detection():
    """
    Debug endpoint to test face detection without full prediction
    """
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    file_path = os.path.join(UPLOAD_FOLDER, f"debug_{file.filename}")
    file.save(file_path)
    
    try:
        img = cv2.imread(file_path)
        if img is None:
            return jsonify({"error": "Could not read image"}), 400
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Test all face detection strategies
        results = {}
        
        # Strategy 1
        faces1 = face_cascade.detectMultiScale(gray, 1.3, 5)
        results["strategy_1_standard"] = len(faces1)
        
        # Strategy 2
        faces2 = face_cascade.detectMultiScale(gray, 1.1, 3, minSize=(30, 30))
        results["strategy_2_sensitive"] = len(faces2)
        
        # Strategy 3
        faces3 = face_cascade.detectMultiScale(gray, 1.05, 2, minSize=(20, 20))
        results["strategy_3_lenient"] = len(faces3)
        
        # Strategy 4
        equalized = cv2.equalizeHist(gray)
        faces4 = face_cascade.detectMultiScale(equalized, 1.2, 4, minSize=(30, 30))
        results["strategy_4_equalized"] = len(faces4)
        
        # Strategy 5
        faces5 = face_cascade.detectMultiScale(gray, 1.4, 3, minSize=(25, 25), maxSize=(300, 300))
        results["strategy_5_scaled"] = len(faces5)
        
        # Strategy 7
        faces7 = face_cascade.detectMultiScale(gray, 1.02, 1, minSize=(15, 15), maxSize=(500, 500))
        results["strategy_7_aggressive"] = len(faces7)
        
        results["image_size"] = f"{img.shape[1]}x{img.shape[0]}"
        results["total_strategies_with_faces"] = sum(1 for count in results.values() if isinstance(count, int) and count > 0)
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({"error": f"Debug failed: {str(e)}"}), 500

@app.route("/admin/stats", methods=["GET"])
@admin_required
def admin_stats():
    conn = get_db_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Users registered per month
    cur.execute("""
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
        FROM users 
        WHERE role = 'user'
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY month DESC
        LIMIT 12
    """)
    monthly_users = [dict(row) for row in cur.fetchall()]
    
    # Emotions per day (last 30 days)
    cur.execute("""
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM emotions
        WHERE timestamp >= datetime('now', '-30 days')
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    """)
    daily_activity = [dict(row) for row in cur.fetchall()]
    
    # Top active users
    cur.execute("""
        SELECT u.fullname, u.email, COUNT(e.id) as emotion_count
        FROM users u
        LEFT JOIN emotions e ON u.id = e.user_id
        WHERE u.role = 'user'
        GROUP BY u.id
        ORDER BY emotion_count DESC
        LIMIT 10
    """)
    top_users = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return jsonify({
        "monthly_users": monthly_users,
        "daily_activity": daily_activity,
        "top_users": top_users
    })



if __name__ == "__main__":
    app.run(debug=True)
