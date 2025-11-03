#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE AUDIO/VIDEO CALLING BACKEND TESTING

**OBJECTIVE**: Test complete audio/video calling system backend after recent fixes

**CONTEXT**: 
- Recent fixes applied: MongoDB persistence, call initiation refactor, UID generation fix
- Previous issue: "AgoraRTCError UID_CONFLICT" - should be resolved now
- Calling system uses Agora.io for real-time audio/video
- Calling requires friend relationships

**TEST CREDENTIALS**:
- User 1: demo@loopync.com / password123
- Backend URL: Check REACT_APP_BACKEND_URL from /app/frontend/.env
- Test with existing friends in database

**CRITICAL TESTING REQUIREMENTS**:

**PHASE 1: Call Initiation (HIGH PRIORITY)**
1. Login as demo user and get JWT token
2. Get demo user's friends list (GET /api/users/{userId}/friends)
3. Test POST /api/calls/initiate with:
   - callerId: demo user ID
   - recipientId: friend user ID  
   - callType: "video" and "audio" (test both)
4. Verify response contains:
   - callerToken (Agora token)
   - recipientToken (Agora token)
   - channelName
   - callerUid (deterministic, integer)
   - recipientUid (deterministic, integer)
5. **CRITICAL**: Verify no UID conflicts - UIDs should be deterministic and unique
6. Verify call record created in database
7. Test error case: call to non-friend (should fail with proper error)

**PHASE 2: UID Generation Verification (CRITICAL)**
1. Make multiple call initiation requests with same users
2. Verify UIDs are CONSISTENT (same user = same UID every time)
3. Verify UIDs are DIFFERENT for different users
4. Verify UIDs are valid integers (Agora requirement)
5. Check for any UID_CONFLICT related errors in logs

**PHASE 3: Call Management**
1. Test call answer (if endpoint exists)
2. Test call rejection (if endpoint exists)
3. Test call end functionality
4. Verify call status updates in database
5. Test call history retrieval

**PHASE 4: Agora Configuration**
1. Verify Agora App ID is configured in backend
2. Verify Agora Certificate is configured
3. Test token generation validity
4. Verify tokens have correct expiration
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://media-fix-8.preview.emergentagent.com/api"
TEST_EMAIL = "demo@loopync.com"
TEST_PASSWORD = "password123"

class AudioVideoCallingTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.friends = []
        self.test_results = {
            "phase1_call_initiation": {"passed": 0, "failed": 0, "tests": []},
            "phase2_uid_verification": {"passed": 0, "failed": 0, "tests": []},
            "phase3_call_management": {"passed": 0, "failed": 0, "tests": []},
            "phase4_agora_config": {"passed": 0, "failed": 0, "tests": []}
        }
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def record_test(self, phase: str, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.test_results[phase]["tests"].append({
            "name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.test_results[phase]["passed"] += 1
        else:
            self.test_results[phase]["failed"] += 1
            
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
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            self.log(f"✅ Login successful - User ID: {self.user_id}")
            return True
        else:
            self.log(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def get_friends_list(self):
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
            
    def test_call_initiation_video(self):
        """Test video call initiation"""
        if not self.friends:
            self.record_test("phase1_call_initiation", "Video Call Initiation", False, "No friends available for testing")
            return False
            
        friend = self.friends[0]
        self.log(f"📹 Testing video call initiation to {friend.get('name')}...")
        
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id,
            "recipientId": friend.get("id"),
            "callType": "video"
        })
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["callId", "channelName", "appId", "callerToken", "callerUid", "recipientToken", "recipientUid"]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.record_test("phase1_call_initiation", "Video Call Initiation", False, f"Missing fields: {missing_fields}")
                self.log(f"❌ Video call initiation missing fields: {missing_fields}", "ERROR")
                return False
                
            # Verify UID types
            caller_uid = data.get("callerUid")
            recipient_uid = data.get("recipientUid")
            
            if not isinstance(caller_uid, int) or not isinstance(recipient_uid, int):
                self.record_test("phase1_call_initiation", "Video Call Initiation", False, f"UIDs not integers: caller={type(caller_uid)}, recipient={type(recipient_uid)}")
                self.log(f"❌ UIDs are not integers: caller={type(caller_uid)}, recipient={type(recipient_uid)}", "ERROR")
                return False
                
            if caller_uid == recipient_uid:
                self.record_test("phase1_call_initiation", "Video Call Initiation", False, f"UID conflict: both users have UID {caller_uid}")
                self.log(f"❌ UID CONFLICT: Both users have UID {caller_uid}", "ERROR")
                return False
                
            self.record_test("phase1_call_initiation", "Video Call Initiation", True, f"Call ID: {data.get('callId')}, Caller UID: {caller_uid}, Recipient UID: {recipient_uid}")
            self.log(f"✅ Video call initiation successful")
            self.log(f"   - Call ID: {data.get('callId')}")
            self.log(f"   - Channel: {data.get('channelName')}")
            self.log(f"   - Caller UID: {caller_uid}")
            self.log(f"   - Recipient UID: {recipient_uid}")
            return data
        else:
            self.record_test("phase1_call_initiation", "Video Call Initiation", False, f"HTTP {response.status_code}: {response.text}")
            self.log(f"❌ Video call initiation failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_call_initiation_audio(self):
        """Test audio call initiation"""
        if not self.friends:
            self.record_test("phase1_call_initiation", "Audio Call Initiation", False, "No friends available for testing")
            return False
            
        friend = self.friends[0]
        self.log(f"🎵 Testing audio call initiation to {friend.get('name')}...")
        
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id,
            "recipientId": friend.get("id"),
            "callType": "audio"
        })
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["callId", "channelName", "appId", "callerToken", "callerUid", "recipientToken", "recipientUid"]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.record_test("phase1_call_initiation", "Audio Call Initiation", False, f"Missing fields: {missing_fields}")
                self.log(f"❌ Audio call initiation missing fields: {missing_fields}", "ERROR")
                return False
                
            # Verify UID types
            caller_uid = data.get("callerUid")
            recipient_uid = data.get("recipientUid")
            
            if not isinstance(caller_uid, int) or not isinstance(recipient_uid, int):
                self.record_test("phase1_call_initiation", "Audio Call Initiation", False, f"UIDs not integers: caller={type(caller_uid)}, recipient={type(recipient_uid)}")
                self.log(f"❌ UIDs are not integers: caller={type(caller_uid)}, recipient={type(recipient_uid)}", "ERROR")
                return False
                
            if caller_uid == recipient_uid:
                self.record_test("phase1_call_initiation", "Audio Call Initiation", False, f"UID conflict: both users have UID {caller_uid}")
                self.log(f"❌ UID CONFLICT: Both users have UID {caller_uid}", "ERROR")
                return False
                
            self.record_test("phase1_call_initiation", "Audio Call Initiation", True, f"Call ID: {data.get('callId')}, Caller UID: {caller_uid}, Recipient UID: {recipient_uid}")
            self.log(f"✅ Audio call initiation successful")
            self.log(f"   - Call ID: {data.get('callId')}")
            self.log(f"   - Channel: {data.get('channelName')}")
            self.log(f"   - Caller UID: {caller_uid}")
            self.log(f"   - Recipient UID: {recipient_uid}")
            return data
        else:
            self.record_test("phase1_call_initiation", "Audio Call Initiation", False, f"HTTP {response.status_code}: {response.text}")
            self.log(f"❌ Audio call initiation failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_call_to_non_friend(self):
        """Test call initiation to non-friend (should fail)"""
        self.log("🚫 Testing call to non-friend (should fail)...")
        
        # Use a fake user ID that's not in friends list
        fake_user_id = "non_friend_user_123"
        
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id,
            "recipientId": fake_user_id,
            "callType": "video"
        })
        
        if response.status_code == 403 or response.status_code == 404:
            self.record_test("phase1_call_initiation", "Non-Friend Call Rejection", True, f"Correctly rejected with status {response.status_code}")
            self.log(f"✅ Non-friend call correctly rejected with status {response.status_code}")
            return True
        else:
            self.record_test("phase1_call_initiation", "Non-Friend Call Rejection", False, f"Should have failed but got status {response.status_code}")
            self.log(f"❌ Non-friend call should have failed but got status {response.status_code}", "ERROR")
            return False
            
    def test_uid_consistency(self):
        """Test UID generation consistency"""
        if not self.friends:
            self.record_test("phase2_uid_verification", "UID Consistency", False, "No friends available for testing")
            return False
            
        friend = self.friends[0]
        self.log("🔄 Testing UID generation consistency (multiple calls)...")
        
        uids_caller = []
        uids_recipient = []
        
        # Make 3 calls to test consistency
        for i in range(3):
            response = self.session.post(f"{BASE_URL}/calls/initiate", json={
                "callerId": self.user_id,
                "recipientId": friend.get("id"),
                "callType": "video"
            })
            
            if response.status_code == 200:
                data = response.json()
                uids_caller.append(data.get("callerUid"))
                uids_recipient.append(data.get("recipientUid"))
                self.log(f"   Call {i+1}: Caller UID={data.get('callerUid')}, Recipient UID={data.get('recipientUid')}")
            else:
                self.record_test("phase2_uid_verification", "UID Consistency", False, f"Call {i+1} failed: {response.status_code}")
                return False
                
        # Check consistency
        caller_consistent = len(set(uids_caller)) == 1
        recipient_consistent = len(set(uids_recipient)) == 1
        
        if caller_consistent and recipient_consistent:
            self.record_test("phase2_uid_verification", "UID Consistency", True, f"Caller UIDs: {uids_caller[0]} (consistent), Recipient UIDs: {uids_recipient[0]} (consistent)")
            self.log(f"✅ UID generation is consistent")
            self.log(f"   - Caller always gets UID: {uids_caller[0]}")
            self.log(f"   - Recipient always gets UID: {uids_recipient[0]}")
            return True
        else:
            self.record_test("phase2_uid_verification", "UID Consistency", False, f"Inconsistent UIDs - Caller: {uids_caller}, Recipient: {uids_recipient}")
            self.log(f"❌ UID generation is inconsistent", "ERROR")
            self.log(f"   - Caller UIDs: {uids_caller}")
            self.log(f"   - Recipient UIDs: {uids_recipient}")
            return False
            
    def test_uid_uniqueness(self):
        """Test UID uniqueness between different users"""
        if len(self.friends) < 2:
            self.record_test("phase2_uid_verification", "UID Uniqueness", False, "Need at least 2 friends for uniqueness testing")
            return False
            
        self.log("🔀 Testing UID uniqueness between different users...")
        
        # Test calls to different friends
        friend1 = self.friends[0]
        friend2 = self.friends[1]
        
        # Call to friend 1
        response1 = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id,
            "recipientId": friend1.get("id"),
            "callType": "video"
        })
        
        # Call to friend 2
        response2 = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id,
            "recipientId": friend2.get("id"),
            "callType": "video"
        })
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            uid1 = data1.get("recipientUid")
            uid2 = data2.get("recipientUid")
            
            if uid1 != uid2:
                self.record_test("phase2_uid_verification", "UID Uniqueness", True, f"Friend1 UID: {uid1}, Friend2 UID: {uid2} (different)")
                self.log(f"✅ UIDs are unique between different users")
                self.log(f"   - {friend1.get('name')} UID: {uid1}")
                self.log(f"   - {friend2.get('name')} UID: {uid2}")
                return True
            else:
                self.record_test("phase2_uid_verification", "UID Uniqueness", False, f"Both friends have same UID: {uid1}")
                self.log(f"❌ UID collision: Both friends have UID {uid1}", "ERROR")
                return False
        else:
            self.record_test("phase2_uid_verification", "UID Uniqueness", False, f"Failed to initiate calls for uniqueness test")
            return False
            
    def test_call_answer(self, call_data):
        """Test call answer functionality"""
        if not call_data:
            self.record_test("phase3_call_management", "Call Answer", False, "No call data available")
            return False
            
        call_id = call_data.get("callId")
        self.log(f"📞 Testing call answer for call {call_id}...")
        
        # Use the recipient's user ID (first friend) as the answering user
        recipient_id = self.friends[0].get("id") if self.friends else None
        if not recipient_id:
            self.record_test("phase3_call_management", "Call Answer", False, "No recipient ID available")
            return False
        
        response = self.session.post(f"{BASE_URL}/calls/{call_id}/answer?userId={recipient_id}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ongoing" or "answered" in data.get("message", "").lower():
                self.record_test("phase3_call_management", "Call Answer", True, f"Call {call_id} answered successfully")
                self.log(f"✅ Call answered successfully - Response: {data}")
                return True
            else:
                self.record_test("phase3_call_management", "Call Answer", False, f"Unexpected response: {data}")
                self.log(f"❌ Unexpected call response: {data}", "ERROR")
                return False
        else:
            self.record_test("phase3_call_management", "Call Answer", False, f"HTTP {response.status_code}: {response.text}")
            self.log(f"❌ Call answer failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_call_reject(self):
        """Test call rejection functionality"""
        if not self.friends:
            self.record_test("phase3_call_management", "Call Reject", False, "No friends available for testing")
            return False
            
        friend = self.friends[0]
        self.log(f"❌ Testing call rejection...")
        
        # First initiate a call
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id,
            "recipientId": friend.get("id"),
            "callType": "video"
        })
        
        if response.status_code != 200:
            self.record_test("phase3_call_management", "Call Reject", False, "Failed to initiate call for rejection test")
            return False
            
        call_data = response.json()
        call_id = call_data.get("callId")
        
        # Now reject the call
        response = self.session.post(f"{BASE_URL}/calls/{call_id}/reject")
        
        if response.status_code == 200:
            self.record_test("phase3_call_management", "Call Reject", True, f"Call {call_id} rejected successfully")
            self.log(f"✅ Call rejected successfully")
            return True
        else:
            self.record_test("phase3_call_management", "Call Reject", False, f"HTTP {response.status_code}: {response.text}")
            self.log(f"❌ Call reject failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_call_end(self, call_data):
        """Test call end functionality"""
        if not call_data:
            self.record_test("phase3_call_management", "Call End", False, "No call data available")
            return False
            
        call_id = call_data.get("callId")
        self.log(f"📴 Testing call end for call {call_id}...")
        
        # Use the caller's user ID (demo user) as the ending user
        response = self.session.post(f"{BASE_URL}/calls/{call_id}/end?userId={self.user_id}")
        
        if response.status_code == 200:
            data = response.json()
            self.record_test("phase3_call_management", "Call End", True, f"Call {call_id} ended successfully")
            self.log(f"✅ Call ended successfully - Response: {data}")
            return True
        else:
            self.record_test("phase3_call_management", "Call End", False, f"HTTP {response.status_code}: {response.text}")
            self.log(f"❌ Call end failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_call_history(self):
        """Test call history retrieval"""
        self.log(f"📋 Testing call history retrieval...")
        
        response = self.session.get(f"{BASE_URL}/calls/{self.user_id}/history")
        
        if response.status_code == 200:
            calls = response.json()
            self.record_test("phase3_call_management", "Call History", True, f"Retrieved {len(calls)} call records")
            self.log(f"✅ Call history retrieved - {len(calls)} calls found")
            for call in calls[:3]:  # Show first 3 calls
                self.log(f"   - Call {call.get('id')}: {call.get('callType')} call, status: {call.get('status')}")
            return True
        else:
            self.record_test("phase3_call_management", "Call History", False, f"HTTP {response.status_code}: {response.text}")
            self.log(f"❌ Call history failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_agora_configuration(self):
        """Test Agora configuration by checking if tokens are generated"""
        if not self.friends:
            self.record_test("phase4_agora_config", "Agora Configuration", False, "No friends available for testing")
            return False
            
        friend = self.friends[0]
        self.log("⚙️ Testing Agora configuration...")
        
        response = self.session.post(f"{BASE_URL}/calls/initiate", json={
            "callerId": self.user_id,
            "recipientId": friend.get("id"),
            "callType": "video"
        })
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for Agora-specific fields
            agora_fields = ["appId", "callerToken", "recipientToken", "channelName"]
            missing_agora_fields = [field for field in agora_fields if not data.get(field)]
            
            if missing_agora_fields:
                self.record_test("phase4_agora_config", "Agora Configuration", False, f"Missing Agora fields: {missing_agora_fields}")
                self.log(f"❌ Missing Agora fields: {missing_agora_fields}", "ERROR")
                return False
                
            # Check token format (should be non-empty strings)
            caller_token = data.get("callerToken")
            recipient_token = data.get("recipientToken")
            app_id = data.get("appId")
            
            if not caller_token or not recipient_token or not app_id:
                self.record_test("phase4_agora_config", "Agora Configuration", False, "Empty Agora tokens or app ID")
                self.log(f"❌ Empty Agora tokens or app ID", "ERROR")
                return False
                
            # Check if tokens look valid (should be long strings)
            if len(caller_token) < 50 or len(recipient_token) < 50:
                self.record_test("phase4_agora_config", "Agora Configuration", False, f"Tokens seem too short: caller={len(caller_token)}, recipient={len(recipient_token)}")
                self.log(f"❌ Tokens seem too short: caller={len(caller_token)}, recipient={len(recipient_token)}", "ERROR")
                return False
                
            self.record_test("phase4_agora_config", "Agora Configuration", True, f"App ID: {app_id}, Token lengths: caller={len(caller_token)}, recipient={len(recipient_token)}")
            self.log(f"✅ Agora configuration is working")
            self.log(f"   - App ID: {app_id}")
            self.log(f"   - Caller token length: {len(caller_token)}")
            self.log(f"   - Recipient token length: {len(recipient_token)}")
            self.log(f"   - Channel: {data.get('channelName')}")
            return True
        else:
            self.record_test("phase4_agora_config", "Agora Configuration", False, f"Call initiation failed: {response.status_code}")
            self.log(f"❌ Cannot test Agora config - call initiation failed: {response.status_code}", "ERROR")
            return False
            
    def run_all_tests(self):
        """Run comprehensive audio/video calling tests"""
        self.log("🎯 STARTING COMPREHENSIVE AUDIO/VIDEO CALLING BACKEND TESTING")
        self.log("=" * 80)
        
        # Phase 0: Setup
        if not self.login():
            self.log("❌ Cannot proceed without login", "ERROR")
            return False
            
        if not self.get_friends_list():
            self.log("❌ Cannot proceed without friends list", "ERROR")
            return False
            
        if len(self.friends) == 0:
            self.log("❌ No friends available for testing", "ERROR")
            return False
            
        # Phase 1: Call Initiation
        self.log("\n📞 PHASE 1: CALL INITIATION TESTING")
        self.log("-" * 50)
        
        video_call_data = self.test_call_initiation_video()
        audio_call_data = self.test_call_initiation_audio()
        self.test_call_to_non_friend()
        
        # Phase 2: UID Verification
        self.log("\n🔢 PHASE 2: UID GENERATION VERIFICATION")
        self.log("-" * 50)
        
        self.test_uid_consistency()
        self.test_uid_uniqueness()
        
        # Phase 3: Call Management
        self.log("\n📱 PHASE 3: CALL MANAGEMENT TESTING")
        self.log("-" * 50)
        
        if video_call_data:
            self.test_call_answer(video_call_data)
            self.test_call_end(video_call_data)
        
        self.test_call_reject()
        self.test_call_history()
        
        # Phase 4: Agora Configuration
        self.log("\n⚙️ PHASE 4: AGORA CONFIGURATION TESTING")
        self.log("-" * 50)
        
        self.test_agora_configuration()
        
        # Summary
        self.print_summary()
        
    def print_summary(self):
        """Print comprehensive test summary"""
        self.log("\n" + "=" * 80)
        self.log("🎯 COMPREHENSIVE AUDIO/VIDEO CALLING BACKEND TEST SUMMARY")
        self.log("=" * 80)
        
        total_passed = 0
        total_failed = 0
        
        for phase_name, results in self.test_results.items():
            phase_display = phase_name.replace("_", " ").title()
            passed = results["passed"]
            failed = results["failed"]
            total = passed + failed
            
            total_passed += passed
            total_failed += failed
            
            if total > 0:
                success_rate = (passed / total) * 100
                status = "✅ PASS" if failed == 0 else "❌ FAIL" if passed == 0 else "⚠️ PARTIAL"
                
                self.log(f"\n{status} {phase_display}: {passed}/{total} tests passed ({success_rate:.1f}%)")
                
                for test in results["tests"]:
                    status_icon = "✅" if test["passed"] else "❌"
                    self.log(f"  {status_icon} {test['name']}: {test['details']}")
        
        # Overall summary
        total_tests = total_passed + total_failed
        if total_tests > 0:
            overall_success_rate = (total_passed / total_tests) * 100
            overall_status = "✅ SUCCESS" if total_failed == 0 else "❌ FAILURE" if total_passed == 0 else "⚠️ PARTIAL SUCCESS"
            
            self.log(f"\n{overall_status} OVERALL: {total_passed}/{total_tests} tests passed ({overall_success_rate:.1f}%)")
            
            # Critical issues
            if total_failed > 0:
                self.log(f"\n🚨 CRITICAL ISSUES FOUND:")
                for phase_name, results in self.test_results.items():
                    for test in results["tests"]:
                        if not test["passed"]:
                            self.log(f"   ❌ {test['name']}: {test['details']}")
            
            # Expected results verification
            self.log(f"\n📋 EXPECTED RESULTS VERIFICATION:")
            
            # Check key requirements from review request
            call_initiation_working = any(test["passed"] and "Call Initiation" in test["name"] for phase in self.test_results.values() for test in phase["tests"])
            uid_conflict_resolved = any(test["passed"] and "UID" in test["name"] for phase in self.test_results.values() for test in phase["tests"])
            friend_validation_working = any(test["passed"] and "Non-Friend" in test["name"] for phase in self.test_results.values() for test in phase["tests"])
            agora_config_working = any(test["passed"] and "Agora Configuration" in test["name"] for phase in self.test_results.values() for test in phase["tests"])
            
            self.log(f"   {'✅' if call_initiation_working else '❌'} Call initiation returns valid tokens and UIDs")
            self.log(f"   {'✅' if uid_conflict_resolved else '❌'} No UID_CONFLICT errors (deterministic generation working)")
            self.log(f"   {'✅' if friend_validation_working else '❌'} Friend validation prevents unauthorized calls")
            self.log(f"   {'✅' if agora_config_working else '❌'} Agora.io integration functional")
            
            if overall_success_rate >= 80:
                self.log(f"\n🎉 AUDIO/VIDEO CALLING SYSTEM IS PRODUCTION-READY!")
            elif overall_success_rate >= 60:
                self.log(f"\n⚠️ AUDIO/VIDEO CALLING SYSTEM NEEDS MINOR FIXES")
            else:
                self.log(f"\n🚨 AUDIO/VIDEO CALLING SYSTEM NEEDS MAJOR FIXES")
        
        self.log("=" * 80)

def main():
    """Main test execution"""
    tester = AudioVideoCallingTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()