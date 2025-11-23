#!/usr/bin/env python3
"""
Check if admin user exists and verify database setup
"""

import sqlite3
from werkzeug.security import check_password_hash

DB_PATH = "database.db"

def check_admin_user():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Check if admin user exists
    cur.execute("SELECT * FROM users WHERE email = 'admin@gmail.com'")
    admin_user = cur.fetchone()
    
    if admin_user:
        print("✅ Admin user found:")
        print(f"   ID: {admin_user['id']}")
        print(f"   Name: {admin_user['fullname']}")
        print(f"   Email: {admin_user['email']}")
        print(f"   Role: {admin_user['role']}")
        print(f"   Created: {admin_user['created_at']}")
        
        # Test password
        if check_password_hash(admin_user['password_hash'], 'admin123'):
            print("✅ Password 'admin123' is correct")
        else:
            print("❌ Password 'admin123' is incorrect")
    else:
        print("❌ Admin user not found!")
        
        # Show all users
        cur.execute("SELECT id, fullname, email, role FROM users")
        all_users = cur.fetchall()
        print(f"\nAll users in database ({len(all_users)}):")
        for user in all_users:
            print(f"   {user['id']}: {user['fullname']} ({user['email']}) - Role: {user['role']}")
    
    conn.close()

if __name__ == "__main__":
    print("🔍 Checking admin user setup...")
    check_admin_user()