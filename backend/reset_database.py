#!/usr/bin/env python3
"""
Database Reset Script for MaskLens
This script will delete the existing database and recreate it with proper schema.
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

DB_PATH = "database.db"

def reset_database():
    """Delete existing database and create fresh one with admin user"""
    
    # Remove existing database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"✅ Deleted existing database: {DB_PATH}")
    
    # Create new database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Create users table with role column
    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TEXT
        )
    """)
    print("✅ Created users table with role column")
    
    # Create emotions table
    cur.execute("""
        CREATE TABLE emotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            emotion TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    print("✅ Created emotions table")
    
    # Create default admin user
    admin_pass = generate_password_hash("admin123")
    cur.execute(
        "INSERT INTO users (fullname, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
        ("Admin", "admin@gmail.com", admin_pass, "admin", datetime.now().isoformat())
    )
    print("✅ Created default admin user")
    print("   📧 Email: admin@gmail.com")
    print("   🔑 Password: admin123")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Database reset complete!")
    print("You can now start the backend with: python app.py")

if __name__ == "__main__":
    print("🔄 Resetting MaskLens Database...")
    print("⚠️  This will delete all existing data!")
    
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        reset_database()
    else:
        print("❌ Database reset cancelled")