#!/usr/bin/env python3
"""
CRITICAL CALL FUNCTIONALITY TESTING - Audio & Video Call Initiation Fix Verification

🎯 **TESTING SCOPE**: Test call initiation after backend Pydantic model fix

**USER ISSUE**: 
- React error when initiating calls: "Objects are not valid as a React child"
- Call initiation failing for both audio and video calls

**FIXES APPLIED**:
1. Backend: Changed call initiation endpoint to use Pydantic model (CallInitiateRequest)
2. Frontend: Enhanced error handling to properly extract error messages as strings

**BACKEND URL**: https://profile-avatar-2.preview.emergentagent.com/api
**TEST CREDENTIALS**: demo@loopync.com / password123
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://profile-avatar-2.preview.emergentagent.com/api"
TEST_EMAIL = "demo@loopync.com"
TEST_PASSWORD = "password123"

class CallTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.friends = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def login(self):
        """Login and get JWT token"""
        self.log("🔐 Logging in with demo credentials...")
        
        response = self.session.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.user_id = data.get("user", {}).get("id")
            self.log(f"✅ Login successful! User ID: {self.user_id}")
            
            # Set authorization header for future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            })
            return True
        else:
            self.log(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
            return False
    
    def get_friends(self):
        """Get user's friends list"""
        self.log("👥 Getting friends list...")
        
        response = self.session.get(f"{BASE_URL}/users/{self.user_id}/friends")
        
        if response.status_code == 200:
            self.friends = response.json()
            self.log(f"✅ Found {len(self.friends)} friends")
            for friend in self.friends:
                self.log(f"   - {friend.get('name')} (ID: {friend.get('id')})")
            return True
        else:
            self.log(f"❌ Failed to get friends: {response.status_code} - {response.text}", "ERROR")
            return False
    
    def test_audio_call_initiation(self):
        """Test Priority 1: Audio Call Initiation"""
        self.log("\n📞 TEST 1: Audio Call Initiation")
        
        if not self.friends:
            self.log("❌ No friends available for testing", "ERROR")
            return False
            
        friend = self.friends[0]  # Use first friend
        friend_id = friend.get('id')
        friend_name = friend.get('name')
        
        self.log(f"   Initiating audio call to {friend_name} (ID: {friend_id})")
        
        request_body = {
            "callerId": self.user_id,
            "recipientId": friend_id,
            "callType": "audio"
        }
        
        self.log(f"   Request body: {json.dumps(request_body, indent=2)}")
        
        response = self.session.post(f"{BASE_URL}/calls/initiate", json=request_body)
        
        self.log(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.log("✅ Audio call initiation successful!")
            
            # Verify response structure
            required_fields = ["callId", "channelName", "appId", "callerToken", "callerUid", "recipientToken", "recipientUid", "expiresIn"]
            missing_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                else:
                    self.log(f"   ✅ {field}: {str(data[field])[:50]}{'...' if len(str(data[field])) > 50 else ''}")
            
            if missing_fields:
                self.log(f"❌ Missing required fields: {missing_fields}", "ERROR")
                return False
            
            # Verify no Pydantic errors
            if isinstance(data.get('detail'), dict):
                self.log("❌ Response contains object in detail field (Pydantic error)", "ERROR")
                return False
                
            self.log("✅ All required fields present and properly formatted")
            return True
        else:
            self.log(f"❌ Audio call initiation failed: {response.text}", "ERROR")
            return False
    
    def test_video_call_initiation(self):
        """Test Priority 1: Video Call Initiation"""
        self.log("\n📹 TEST 2: Video Call Initiation")
        
        if not self.friends:
            self.log("❌ No friends available for testing", "ERROR")
            return False
            
        friend = self.friends[0]  # Use first friend
        friend_id = friend.get('id')
        friend_name = friend.get('name')
        
        self.log(f"   Initiating video call to {friend_name} (ID: {friend_id})")
        
        request_body = {
            "callerId": self.user_id,
            "recipientId": friend_id,
            "callType": "video"
        }
        
        response = self.session.post(f"{BASE_URL}/calls/initiate", json=request_body)
        
        self.log(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.log("✅ Video call initiation successful!")
            
            # Verify response structure
            required_fields = ["callId", "channelName", "appId", "callerToken", "callerUid", "recipientToken", "recipientUid", "expiresIn"]
            missing_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                else:
                    self.log(f"   ✅ {field}: {str(data[field])[:50]}{'...' if len(str(data[field])) > 50 else ''}")
            
            if missing_fields:
                self.log(f"❌ Missing required fields: {missing_fields}", "ERROR")
                return False
            
            # Verify no Pydantic errors
            if isinstance(data.get('detail'), dict):
                self.log("❌ Response contains object in detail field (Pydantic error)", "ERROR")
                return False
                
            self.log("✅ All required fields present and properly formatted")
            return True
        else:
            self.log(f"❌ Video call initiation failed: {response.text}", "ERROR")
            return False
    
    def test_error_scenarios(self):
        """Test Priority 1: Error Scenarios"""
        self.log("\n🚨 TEST 3: Error Scenarios")
        
        # Test 3a: Non-existent caller
        self.log("   3a: Testing non-existent caller")
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": "non_existent_user",
            "recipientId": self.friends[0].get('id') if self.friends else "test_user_1",
            "callType": "audio"
        })
        
        if response.status_code == 404:
            data = response.json()
            if data.get('detail') == "Caller not found":
                self.log("   ✅ Non-existent caller properly rejected with 404")
            else:
                self.log(f"   ❌ Wrong error message: {data.get('detail')}", "ERROR")
                return False
        else:
            self.log(f"   ❌ Expected 404, got {response.status_code}", "ERROR")
            return False
        
        # Test 3b: Non-friend recipient (if we have friends, test with a non-friend)
        self.log("   3b: Testing non-friend recipient")
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id,
            "recipientId": "non_friend_user",
            "callType": "audio"
        })
        
        if response.status_code == 403:
            data = response.json()
            if data.get('detail') == "You can only call friends":
                self.log("   ✅ Non-friend recipient properly rejected with 403")
            else:
                self.log(f"   ❌ Wrong error message: {data.get('detail')}", "ERROR")
                return False
        else:
            self.log(f"   ❌ Expected 403, got {response.status_code}", "ERROR")
            return False
        
        # Test 3c: Invalid request format (missing fields)
        self.log("   3c: Testing invalid request format")
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id
            # Missing recipientId and callType
        })
        
        if response.status_code == 422:
            data = response.json()
            if isinstance(data.get('detail'), list):
                self.log("   ✅ Invalid request format properly rejected with 422 validation error")
            else:
                self.log(f"   ❌ Expected validation error list, got: {data.get('detail')}", "ERROR")
                return False
        else:
            self.log(f"   ❌ Expected 422, got {response.status_code}", "ERROR")
            return False
        
        # Test 3d: Empty request body
        self.log("   3d: Testing empty request body")
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={})
        
        if response.status_code == 422:
            self.log("   ✅ Empty request body properly rejected with 422")
        else:
            self.log(f"   ❌ Expected 422, got {response.status_code}", "ERROR")
            return False
        
        self.log("✅ All error scenarios working correctly")
        return True
    
    def test_agora_token_generation(self):
        """Test Priority 1: Agora Token Generation"""
        self.log("\n🎮 TEST 4: Agora Token Generation Verification")
        
        if not self.friends:
            self.log("❌ No friends available for testing", "ERROR")
            return False
        
        # Initiate a call to get tokens
        friend = self.friends[0]
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id,
            "recipientId": friend.get('id'),
            "callType": "audio"
        })
        
        if response.status_code != 200:
            self.log(f"❌ Failed to initiate call for token testing: {response.text}", "ERROR")
            return False
        
        data = response.json()
        
        # Verify Agora token structure
        self.log("   Verifying Agora token generation...")
        
        # Check callId (UUID format)
        call_id = data.get('callId')
        if call_id and len(call_id) == 36 and call_id.count('-') == 4:
            self.log(f"   ✅ callId: Valid UUID format ({call_id})")
        else:
            self.log(f"   ❌ callId: Invalid format ({call_id})", "ERROR")
            return False
        
        # Check channelName
        channel_name = data.get('channelName')
        if channel_name and channel_name.startswith('call-'):
            self.log(f"   ✅ channelName: Valid format ({channel_name})")
        else:
            self.log(f"   ❌ channelName: Invalid format ({channel_name})", "ERROR")
            return False
        
        # Check appId (Agora app ID)
        app_id = data.get('appId')
        if app_id and len(app_id) == 32:  # Agora app IDs are typically 32 characters
            self.log(f"   ✅ appId: Valid format ({app_id})")
        else:
            self.log(f"   ❌ appId: Invalid format ({app_id})", "ERROR")
            return False
        
        # Check tokens (JWT-like strings)
        caller_token = data.get('callerToken')
        recipient_token = data.get('recipientToken')
        
        if caller_token and len(caller_token) > 100:  # Agora tokens are long
            self.log(f"   ✅ callerToken: Valid JWT-like string ({len(caller_token)} chars)")
        else:
            self.log(f"   ❌ callerToken: Invalid format", "ERROR")
            return False
        
        if recipient_token and len(recipient_token) > 100:
            self.log(f"   ✅ recipientToken: Valid JWT-like string ({len(recipient_token)} chars)")
        else:
            self.log(f"   ❌ recipientToken: Invalid format", "ERROR")
            return False
        
        # Check UIDs (integers)
        caller_uid = data.get('callerUid')
        recipient_uid = data.get('recipientUid')
        
        if isinstance(caller_uid, int) and caller_uid > 0:
            self.log(f"   ✅ callerUid: Valid integer ({caller_uid})")
        else:
            self.log(f"   ❌ callerUid: Invalid format ({caller_uid})", "ERROR")
            return False
        
        if isinstance(recipient_uid, int) and recipient_uid > 0:
            self.log(f"   ✅ recipientUid: Valid integer ({recipient_uid})")
        else:
            self.log(f"   ❌ recipientUid: Invalid format ({recipient_uid})", "ERROR")
            return False
        
        # Check expiration
        expires_in = data.get('expiresIn')
        if expires_in == 3600:
            self.log(f"   ✅ expiresIn: Correct value (3600 seconds)")
        else:
            self.log(f"   ❌ expiresIn: Wrong value ({expires_in})", "ERROR")
            return False
        
        self.log("✅ Agora token generation working correctly")
        return True
    
    def test_call_management(self):
        """Test Priority 2: Call Management"""
        self.log("\n📱 TEST 5: Call Management (Answer/End)")
        
        if not self.friends:
            self.log("❌ No friends available for testing", "ERROR")
            return False
        
        # First, initiate a call
        friend = self.friends[0]
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id,
            "recipientId": friend.get('id'),
            "callType": "audio"
        })
        
        if response.status_code != 200:
            self.log(f"❌ Failed to initiate call: {response.text}", "ERROR")
            return False
        
        call_data = response.json()
        call_id = call_data.get('callId')
        
        # Test answering the call (using recipient's perspective)
        recipient_id = friend.get('id')
        self.log(f"   Testing answer call (ID: {call_id}) as recipient ({recipient_id})")
        response = self.session.post(f"{BASE_URL}/calls/{call_id}/answer", params={"userId": recipient_id})
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ongoing':
                self.log("   ✅ Call answered successfully, status changed to 'ongoing'")
            else:
                self.log(f"   ❌ Call status not updated correctly: {data.get('status')}", "ERROR")
                return False
        else:
            self.log(f"   ❌ Failed to answer call: {response.text}", "ERROR")
            return False
        
        # Test ending the call (caller can end it)
        self.log(f"   Testing end call (ID: {call_id}) as caller ({self.user_id})")
        response = self.session.post(f"{BASE_URL}/calls/{call_id}/end", params={"userId": self.user_id})
        
        if response.status_code == 200:
            data = response.json()
            if data.get('message') == 'Call ended':
                self.log(f"   ✅ Call ended successfully, duration: {data.get('duration')} seconds")
            else:
                self.log(f"   ❌ Call end response invalid: {data}", "ERROR")
                return False
        else:
            self.log(f"   ❌ Failed to end call: {response.text}", "ERROR")
            return False
        
        self.log("✅ Call management working correctly")
        return True
    
    def test_call_history(self):
        """Test Priority 3: Call History"""
        self.log("\n📋 TEST 6: Call History")
        
        response = self.session.get(f"{BASE_URL}/calls/history/{self.user_id}")
        
        if response.status_code == 200:
            calls = response.json()
            self.log(f"   ✅ Retrieved {len(calls)} calls from history")
            
            if calls:
                # Verify call structure
                call = calls[0]
                required_fields = ["id", "callerId", "recipientId", "callType", "status", "startedAt"]
                
                for field in required_fields:
                    if field in call:
                        self.log(f"   ✅ {field}: {call[field]}")
                    else:
                        self.log(f"   ❌ Missing field: {field}", "ERROR")
                        return False
                
                # Check if caller and recipient data is enriched
                if 'caller' in call and 'recipient' in call:
                    self.log("   ✅ Call history includes enriched user data")
                else:
                    self.log("   ❌ Call history missing user data enrichment", "ERROR")
                    return False
            
            self.log("✅ Call history working correctly")
            return True
        else:
            self.log(f"❌ Failed to get call history: {response.text}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all call functionality tests"""
        self.log("🚀 Starting CRITICAL CALL FUNCTIONALITY TESTING")
        self.log("=" * 80)
        
        # Login first
        if not self.login():
            return False
        
        # Get friends list
        if not self.get_friends():
            return False
        
        # Run all tests
        tests = [
            ("Audio Call Initiation", self.test_audio_call_initiation),
            ("Video Call Initiation", self.test_video_call_initiation),
            ("Error Scenarios", self.test_error_scenarios),
            ("Agora Token Generation", self.test_agora_token_generation),
            ("Call Management", self.test_call_management),
            ("Call History", self.test_call_history)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED", "ERROR")
            except Exception as e:
                self.log(f"❌ {test_name}: EXCEPTION - {str(e)}", "ERROR")
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log(f"🎯 CALL FUNCTIONALITY TEST RESULTS")
        self.log(f"   Tests Passed: {passed}/{total}")
        self.log(f"   Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED - CALL FUNCTIONALITY IS WORKING!")
            return True
        else:
            self.log("⚠️  SOME TESTS FAILED - CALL FUNCTIONALITY NEEDS FIXES")
            return False

if __name__ == "__main__":
    tester = CallTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)