"""
Test script for mask logic toggle API
"""
import requests
import json

BASE_URL = "http://localhost:5000"

# Admin credentials
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"

def login():
    """Login as admin and get token"""
    response = requests.post(
        f"{BASE_URL}/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful")
        return data["access_token"]
    else:
        print(f"❌ Login failed: {response.json()}")
        return None

def get_mask_logic(token):
    """Get current mask logic state"""
    response = requests.get(
        f"{BASE_URL}/admin/mask-logic",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Current Mask Logic:")
        print(f"   Inverted: {data['inverted']}")
        print(f"   Description: {data['description']}")
        return data
    else:
        print(f"❌ Failed to get mask logic: {response.json()}")
        return None

def toggle_mask_logic(token):
    """Toggle mask logic"""
    response = requests.post(
        f"{BASE_URL}/admin/mask-logic/toggle",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"\n🔄 Mask Logic Toggled:")
        print(f"   Success: {data['success']}")
        print(f"   New State: {data['inverted']}")
        print(f"   Message: {data['message']}")
        return data
    else:
        print(f"❌ Failed to toggle mask logic: {response.json()}")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Mask Logic Toggle API")
    print("=" * 50)
    
    # Login
    token = login()
    if not token:
        print("Cannot proceed without token")
        exit(1)
    
    # Get current state
    print("\n1. Getting current mask logic state...")
    initial_state = get_mask_logic(token)
    
    # Toggle
    print("\n2. Toggling mask logic...")
    toggle_mask_logic(token)
    
    # Get new state
    print("\n3. Getting new mask logic state...")
    new_state = get_mask_logic(token)
    
    # Verify toggle worked
    if initial_state and new_state:
        if initial_state["inverted"] != new_state["inverted"]:
            print("\n✅ Toggle successful! State changed.")
        else:
            print("\n❌ Toggle failed! State unchanged.")
    
    # Toggle back
    print("\n4. Toggling back to original state...")
    toggle_mask_logic(token)
    
    # Verify
    print("\n5. Verifying original state restored...")
    final_state = get_mask_logic(token)
    
    if initial_state and final_state:
        if initial_state["inverted"] == final_state["inverted"]:
            print("\n✅ All tests passed! Toggle works correctly.")
        else:
            print("\n❌ State not restored correctly.")
    
    print("\n" + "=" * 50)
    print("Test Complete")
    print("=" * 50)
