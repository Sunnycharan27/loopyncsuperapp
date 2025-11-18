#!/usr/bin/env python3
"""
UID VERIFICATION TEST - Verify deterministic UID generation across multiple sessions
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://profile-avatar-2.preview.emergentagent.com/api"
TEST_EMAIL = "demo@loopync.com"
TEST_PASSWORD = "password123"

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def login():
    """Login and get JWT token"""
    session = requests.Session()
    
    response = session.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        user_id = data.get("user", {}).get("id")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session, user_id
    return None, None

def test_uid_determinism():
    """Test that UIDs are deterministic across multiple sessions"""
    log("🔢 Testing UID determinism across multiple sessions...")
    
    # Test with multiple sessions
    uid_results = {}
    
    for session_num in range(3):
        log(f"   Session {session_num + 1}:")
        
        session, user_id = login()
        if not session or not user_id:
            log(f"   ❌ Failed to login in session {session_num + 1}")
            continue
            
        # Get friends
        friends_response = session.get(f"{BASE_URL}/users/{user_id}/friends")
        if friends_response.status_code != 200:
            log(f"   ❌ Failed to get friends in session {session_num + 1}")
            continue
            
        friends = friends_response.json()
        if not friends:
            log(f"   ❌ No friends found in session {session_num + 1}")
            continue
            
        # Test call initiation to first friend
        friend = friends[0]
        call_response = session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": user_id,
            "recipientId": friend.get("id"),
            "callType": "video"
        })
        
        if call_response.status_code == 200:
            data = call_response.json()
            caller_uid = data.get("callerUid")
            recipient_uid = data.get("recipientUid")
            
            log(f"     Caller UID: {caller_uid}")
            log(f"     Recipient UID: {recipient_uid}")
            
            # Store results
            if user_id not in uid_results:
                uid_results[user_id] = []
            if friend.get("id") not in uid_results:
                uid_results[friend.get("id")] = []
                
            uid_results[user_id].append(caller_uid)
            uid_results[friend.get("id")].append(recipient_uid)
        else:
            log(f"   ❌ Call initiation failed in session {session_num + 1}: {call_response.status_code}")
    
    # Verify consistency
    log("\n🔍 UID Consistency Analysis:")
    all_consistent = True
    
    for user_id, uids in uid_results.items():
        unique_uids = set(uids)
        if len(unique_uids) == 1:
            log(f"   ✅ User {user_id[:8]}... always gets UID: {list(unique_uids)[0]}")
        else:
            log(f"   ❌ User {user_id[:8]}... has inconsistent UIDs: {list(unique_uids)}")
            all_consistent = False
    
    if all_consistent:
        log("\n🎉 UID GENERATION IS FULLY DETERMINISTIC!")
    else:
        log("\n❌ UID GENERATION HAS CONSISTENCY ISSUES!")
    
    return all_consistent

if __name__ == "__main__":
    test_uid_determinism()