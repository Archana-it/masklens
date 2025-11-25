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
# Use absolute paths to avoid duplicate files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print(f"Database path: {DB_PATH}")
print(f"Upload folder: {UPLOAD_FOLDER}")

# ====== Model Configuration ======
INVERT_MASK_PREDICTION = False  # Model outputs high value for MASK

# ====== Password Validation ======
import re

def validate_password(password):
    """
    Validate password requirements:
    - Minimum 8 characters
    - Maximum 16 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 16:
        return False, "Password must not exceed 16 characters"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    
    return True, "Password is valid"

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
    print("Loading mask + emotion models...")
    mask_model = load_model("mask_detection_model.h5")
    emotion_regular = load_model("emotion_model_regular.h5")
    emotion_masked = load_model("emotion_model_masked.h5")

    regular_labels = ["Happy", "Sad"]
    masked_labels  = ["Happy", "Sad"]

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    
    face_cascade_alt = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_alt.xml"
    )

    print("Models and face cascade loaded successfully!")
    
except Exception as e:
    print(f"ERROR loading model: {e}")
    mask_model = None
    emotion_regular = None
    emotion_masked = None

def predict_emotion_from_path(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None, "Image read error"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Enhanced face detection - multiple strategies
    # Note: More conservative to avoid false positives (like detecting paper as face)
    faces = []
    
    # Strategy 1: Standard detection (good balance)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    print(f"Strategy 1 (Standard): Found {len(faces)} faces")
    
    # Strategy 2: Moderate sensitivity (for masked faces)
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(35, 35))
        print(f"Strategy 2 (Moderate): Found {len(faces)} faces")
    
    # Strategy 3: More aggressive (for difficult lighting)
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
        print(f"Strategy 3 (Aggressive): Found {len(faces)} faces")
    
    # Strategy 4: With histogram equalization (for poor lighting)
    if len(faces) == 0:
        equalized = cv2.equalizeHist(gray)
        faces = face_cascade.detectMultiScale(equalized, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))
        print(f"Strategy 4 (Equalized): Found {len(faces)} faces")
    
    # Strategy 5: Alternative cascade (different detection algorithm)
    if len(faces) == 0:
        faces = face_cascade_alt.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))
        print(f"Strategy 5 (Alt Cascade): Found {len(faces)} faces")
    
    # Strategy 6: CLAHE enhancement (for contrast issues)
    if len(faces) == 0:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        faces = face_cascade.detectMultiScale(enhanced, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))
        print(f"Strategy 6 (CLAHE): Found {len(faces)} faces")

    # NO FALLBACK: Return error if no face detected
    if len(faces) == 0:
        print("❌ NO FACE DETECTED - All detection strategies failed")
        print("   Please ensure:")
        print("   - Your face is clearly visible")
        print("   - Good lighting conditions")
        print("   - Face the camera directly")
        print("   - Remove any obstructions")
        return None, "No face detected. Please ensure your face is clearly visible and well-lit."
    
    # Face detected - extract it
    print(f"✅ Face detected: {len(faces)} face(s)")
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    (x, y, w, h) = faces[0]
    face = img[y:y+h, x:x+w]
    
    if face.size == 0:
        print("❌ ERROR: Invalid face region")
        return None, "Invalid face region"

    # Mask Detection
    try:
        mask_face = cv2.resize(face, (128, 128))
        mask_face = mask_face.astype("float32") / 255.0
        mask_face = np.expand_dims(mask_face, axis=0)

        mask_pred = mask_model.predict(mask_face, verbose=0)[0][0]
        print(f"Mask prediction: {mask_pred:.4f}")
        
        # INVERT_MASK_PREDICTION = True: high value = NO MASK, low value = MASK
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

        print(f"Mask status: {mask_status}")

        # Emotion Prediction
        emo_face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        emo_face = cv2.resize(emo_face, (input_size, input_size))
        emo_face = emo_face.astype("float32") / 255.0
        emo_face = np.expand_dims(emo_face, axis=-1)
        emo_face = np.expand_dims(emo_face, axis=0)

        emotion_pred = selected_model.predict(emo_face, verbose=0)
        emotion_idx = np.argmax(emotion_pred[0])
        emotion_label = labels[emotion_idx]
        confidence = emotion_pred[0][emotion_idx]
        
        print(f"Emotion: {emotion_label} ({confidence:.2f})")

        return {
            "mask_status": mask_status,
            "emotion": emotion_label,
            "confidence": float(confidence)
        }, None
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
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

    # Validate password
    is_valid, message = validate_password(password)
    if not is_valid:
        return jsonify({"error": message}), 400

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
@jwt_required()
def predict():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        if mask_model is None or emotion_regular is None or emotion_masked is None:
            return jsonify({"error": "Models not loaded"}), 500
            
        result, error = predict_emotion_from_path(file_path)
        if error:
            return jsonify({"error": error}), 400
        
        user_id = int(get_jwt_identity())
        save_emotion(user_id, file.filename, result["emotion"])

        return jsonify({
            "prediction": result["emotion"],
            "mask_status": result["mask_status"],
            "emotion": result["emotion"]
        }), 200
    
    except Exception as e:
        print(f"Prediction error: {str(e)}")
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

@app.route("/admin/dashboard", methods=["GET"])
@jwt_required()
def admin_dashboard():
    user_id = int(get_jwt_identity())
    role = get_user_role(user_id)
    if role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    
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
@jwt_required()
def admin_get_users():
    user_id = int(get_jwt_identity())
    if get_user_role(user_id) != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    conn = get_db_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, fullname, email, role, created_at FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({"users": users})

@app.route("/admin/users/create", methods=["POST"])
@jwt_required()
def admin_create_user():
    user_id = int(get_jwt_identity())
    if get_user_role(user_id) != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    data = request.get_json(force=True)
    fullname = data.get("fullname")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")  # Default to 'user' if not specified

    if not fullname or not email or not password:
        return jsonify({"error": "fullname, email and password are required"}), 400

    # Validate password
    is_valid, message = validate_password(password)
    if not is_valid:
        return jsonify({"error": message}), 400

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
@jwt_required()
def admin_delete_user(user_id):
    admin_id = int(get_jwt_identity())
    if get_user_role(admin_id) != 'admin':
        return jsonify({"error": "Admin access required"}), 403
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
@jwt_required()
def admin_get_emotions():
    user_id = int(get_jwt_identity())
    if get_user_role(user_id) != 'admin':
        return jsonify({"error": "Admin access required"}), 403
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
@jwt_required()
def admin_delete_emotion(emotion_id):
    user_id = int(get_jwt_identity())
    if get_user_role(user_id) != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM emotions WHERE id = ?", (emotion_id,))
    
    if cur.rowcount == 0:
        conn.close()
        return jsonify({"error": "Emotion record not found"}), 404
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Emotion record deleted successfully"})



@app.route("/admin/stats", methods=["GET"])
@jwt_required()
def admin_stats():
    user_id = int(get_jwt_identity())
    if get_user_role(user_id) != 'admin':
        return jsonify({"error": "Admin access required"}), 403
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
