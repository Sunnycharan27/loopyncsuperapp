#!/usr/bin/env python3
"""
Focused AI Voice Bot Testing - Session Persistence & Error Handling
Retest ONLY the session persistence and error handling for the AI Voice Bot

This is a FOCUSED retest of only the 2 failing features from the previous test:
1. Session Persistence Test (was FAILING before)
2. Error Handling Test (was FAILING before)

Backend URL: https://profile-avatar-2.preview.emergentagent.com/api
Test Credentials: demo@loopync.com / password123
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://profile-avatar-2.preview.emergentagent.com/api"
TEST_EMAIL = "demo@loopync.com"
TEST_PASSWORD = "password123"

class FocusedVoiceBotTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details, response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        print(f"   Details: {details}")
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()
        
    def authenticate(self):
        """Authenticate with demo credentials"""
        print("🔐 Authenticating with demo credentials...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                user_data = data.get("user", {})
                
                self.log_test(
                    "Authentication", 
                    True, 
                    f"Successfully authenticated as {user_data.get('name', 'Unknown')} ({user_data.get('email', 'Unknown')})",
                    {"user_id": user_data.get('id'), "email": user_data.get('email')}
                )
                return True
            else:
                self.log_test(
                    "Authentication", 
                    False, 
                    f"Login failed with status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_session_persistence_fix(self):
        """FOCUSED TEST 1: Session Persistence Fix Verification"""
        print("🧠 Testing Session Persistence Fix...")
        
        try:
            # Generate a new session_id for this test
            session_id = f"test_session_{int(time.time())}"
            
            # First message: "My name is John"
            print("   Step 1: Sending first message: 'My name is John'")
            response1 = self.session.post(
                f"{BACKEND_URL}/voice/chat",
                json={
                    "query": "My name is John",
                    "session_id": session_id,
                    "temperature": 0.7,
                    "max_tokens": 100
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
                }
            )
            
            if response1.status_code != 200:
                self.log_test(
                    "Session Persistence Test",
                    False,
                    f"First message failed with status {response1.status_code}: {response1.text}"
                )
                return False
            
            data1 = response1.json()
            first_response = data1.get("data", {}).get("response", "")
            returned_session_id = data1.get("data", {}).get("session_id", "")
            
            print(f"   First response: {first_response}")
            print(f"   Session ID: {returned_session_id}")
            
            # Wait a moment to ensure session processing
            time.sleep(2)
            
            # Second message: "What is my name?" with SAME session_id
            print("   Step 2: Sending second message: 'What is my name?' with SAME session_id")
            response2 = self.session.post(
                f"{BACKEND_URL}/voice/chat",
                json={
                    "query": "What is my name?",
                    "session_id": session_id,  # Use the SAME session_id
                    "temperature": 0.7,
                    "max_tokens": 100
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
                }
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                second_response = data2.get("data", {}).get("response", "")
                
                print(f"   Second response: {second_response}")
                
                # VERIFY: AI should remember and say "John" or reference the name
                remembers_name = "john" in second_response.lower()
                
                # Additional checks for session context maintenance
                session_maintained = (
                    returned_session_id == session_id or  # Session ID consistency
                    any(word in second_response.lower() for word in ["john", "your name is", "you told me", "you said"])
                )
                
                test_passed = remembers_name and session_maintained
                
                details = f"Session persistence verification:"
                details += f"\n   - AI remembered name 'John': {'✓' if remembers_name else '✗'}"
                details += f"\n   - Session context maintained: {'✓' if session_maintained else '✗'}"
                details += f"\n   - Session ID consistency: {session_id} -> {returned_session_id}"
                
                self.log_test(
                    "Session Persistence Test",
                    test_passed,
                    details,
                    {
                        "session_id": session_id,
                        "first_message": "My name is John",
                        "first_response": first_response,
                        "second_message": "What is my name?",
                        "second_response": second_response,
                        "remembers_name": remembers_name,
                        "session_maintained": session_maintained
                    }
                )
                return test_passed
                
            else:
                self.log_test(
                    "Session Persistence Test",
                    False,
                    f"Second message failed with status {response2.status_code}: {response2.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Session Persistence Test", False, f"Test error: {str(e)}")
            return False

    def test_multi_turn_conversation(self):
        """FOCUSED TEST 2: Multi-Turn Conversation Test"""
        print("💬 Testing Multi-Turn Conversation...")
        
        try:
            # Generate a new session_id for this conversation
            session_id = f"conversation_session_{int(time.time())}"
            
            # Message 1: "I like pizza"
            print("   Message 1: 'I like pizza'")
            response1 = self.session.post(
                f"{BACKEND_URL}/voice/chat",
                json={
                    "query": "I like pizza",
                    "session_id": session_id,
                    "temperature": 0.7,
                    "max_tokens": 100
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
                }
            )
            
            if response1.status_code != 200:
                self.log_test(
                    "Multi-Turn Conversation Test",
                    False,
                    f"Message 1 failed with status {response1.status_code}: {response1.text}"
                )
                return False
            
            data1 = response1.json()
            response1_text = data1.get("data", {}).get("response", "")
            print(f"   Response 1: {response1_text}")
            
            time.sleep(1)
            
            # Message 2: "What food do I like?" (same session)
            print("   Message 2: 'What food do I like?' (same session)")
            response2 = self.session.post(
                f"{BACKEND_URL}/voice/chat",
                json={
                    "query": "What food do I like?",
                    "session_id": session_id,
                    "temperature": 0.7,
                    "max_tokens": 100
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
                }
            )
            
            if response2.status_code != 200:
                self.log_test(
                    "Multi-Turn Conversation Test",
                    False,
                    f"Message 2 failed with status {response2.status_code}: {response2.text}"
                )
                return False
            
            data2 = response2.json()
            response2_text = data2.get("data", {}).get("response", "")
            print(f"   Response 2: {response2_text}")
            
            # VERIFY: AI remembers "pizza"
            remembers_pizza = "pizza" in response2_text.lower()
            
            time.sleep(1)
            
            # Message 3: "Do I prefer Italian food?" (same session)
            print("   Message 3: 'Do I prefer Italian food?' (same session)")
            response3 = self.session.post(
                f"{BACKEND_URL}/voice/chat",
                json={
                    "query": "Do I prefer Italian food?",
                    "session_id": session_id,
                    "temperature": 0.7,
                    "max_tokens": 100
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
                }
            )
            
            if response3.status_code != 200:
                self.log_test(
                    "Multi-Turn Conversation Test",
                    False,
                    f"Message 3 failed with status {response3.status_code}: {response3.text}"
                )
                return False
            
            data3 = response3.json()
            response3_text = data3.get("data", {}).get("response", "")
            print(f"   Response 3: {response3_text}")
            
            # VERIFY: AI can make connection to pizza/Italian
            makes_connection = any(word in response3_text.lower() for word in ["pizza", "italian", "yes", "like"])
            
            test_passed = remembers_pizza and makes_connection
            
            details = f"Multi-turn conversation verification:"
            details += f"\n   - AI remembered 'pizza': {'✓' if remembers_pizza else '✗'}"
            details += f"\n   - AI made pizza/Italian connection: {'✓' if makes_connection else '✗'}"
            
            self.log_test(
                "Multi-Turn Conversation Test",
                test_passed,
                details,
                {
                    "session_id": session_id,
                    "conversation": [
                        {"message": "I like pizza", "response": response1_text},
                        {"message": "What food do I like?", "response": response2_text},
                        {"message": "Do I prefer Italian food?", "response": response3_text}
                    ],
                    "remembers_pizza": remembers_pizza,
                    "makes_connection": makes_connection
                }
            )
            return test_passed
                
        except Exception as e:
            self.log_test("Multi-Turn Conversation Test", False, f"Test error: {str(e)}")
            return False

    def test_error_handling_fix(self):
        """FOCUSED TEST 3: Error Handling Fix Verification"""
        print("🚨 Testing Error Handling Fix...")
        
        error_tests = [
            {
                "name": "Empty Query",
                "payload": {"query": ""},
                "expected_status": [400, 422],  # Should return validation error
                "description": "Empty query should return 400 error (not 200 success)"
            },
            {
                "name": "Whitespace Only Query",
                "payload": {"query": "   "},
                "expected_status": [400, 422],  # Should return validation error
                "description": "Whitespace only query should return 400 error"
            },
            {
                "name": "Invalid Temperature",
                "payload": {"query": "Hello", "temperature": 2.5},
                "expected_status": [422],  # Should return validation error
                "description": "Invalid temperature (2.5) should return 422 validation error"
            }
        ]
        
        all_passed = True
        
        for test in error_tests:
            try:
                print(f"   Testing: {test['name']}")
                print(f"   Expected: {test['description']}")
                
                response = self.session.post(
                    f"{BACKEND_URL}/voice/chat",
                    json=test["payload"],
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
                    }
                )
                
                # VERIFY: Returns proper error status (not 200 success)
                status_correct = response.status_code in test["expected_status"]
                
                if status_correct:
                    test_passed = True
                    details = f"✓ Correctly returned error status {response.status_code} (expected {test['expected_status']})"
                else:
                    test_passed = False
                    if response.status_code == 200:
                        # This was the previous bug - returning 200 success for invalid input
                        details = f"✗ BUG: Still returning 200 success for invalid input (should be {test['expected_status']})"
                        try:
                            data = response.json()
                            details += f"\n   Response data: {json.dumps(data, indent=2)}"
                        except:
                            details += f"\n   Response text: {response.text}"
                    else:
                        details = f"✗ Unexpected status {response.status_code} (expected {test['expected_status']})"
                
                all_passed = all_passed and test_passed
                
                self.log_test(
                    f"Error Handling - {test['name']}",
                    test_passed,
                    details,
                    {
                        "payload": test["payload"],
                        "status_code": response.status_code,
                        "expected_status": test["expected_status"],
                        "response_preview": response.text[:200]
                    }
                )
                
            except Exception as e:
                all_passed = False
                self.log_test(f"Error Handling - {test['name']}", False, f"Test error: {str(e)}")
        
        return all_passed
    
    def run_focused_tests(self):
        """Run focused tests for session persistence and error handling"""
        print("🎯 Starting FOCUSED AI Voice Bot Testing - Session Persistence & Error Handling")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Credentials: {TEST_EMAIL} / {TEST_PASSWORD}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        print("FOCUSED TESTING - Session Persistence Fix Verification:")
        print("1. Session Persistence Test (This was FAILING before)")
        print("2. Multi-Turn Conversation Test")
        print("3. Error Handling Test (This was FAILING before)")
        print("=" * 80)
        print()
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run focused tests
        test_methods = [
            ("Session Persistence Fix", self.test_session_persistence_fix),
            ("Multi-Turn Conversation", self.test_multi_turn_conversation),
            ("Error Handling Fix", self.test_error_handling_fix)
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_name, test_method in test_methods:
            print(f"🔍 Running {test_name}...")
            if test_method():
                passed_tests += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
            print()
        
        # Print summary
        print("=" * 80)
        print("🏁 FOCUSED TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        # Print individual test results
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {result['test']}")
        
        print()
        
        if passed_tests == total_tests:
            print("🎉 ALL FOCUSED TESTS PASSED!")
            print("✅ Session persistence should now work (conversation context maintained)")
            print("✅ Error handling should properly reject empty/invalid queries")
            print("✅ All tests should PASS")
            return True
        else:
            failed_count = total_tests - passed_tests
            print(f"⚠️  {failed_count} focused test(s) still failing")
            print("❌ Session persistence and/or error handling still need fixes")
            
            # Show which specific tests failed
            failed_tests = [result['test'] for result in self.test_results if not result['success']]
            if failed_tests:
                print(f"Failed tests: {', '.join(failed_tests)}")
            
            return False

def main():
    """Main test execution"""
    tester = FocusedVoiceBotTester()
    success = tester.run_focused_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()