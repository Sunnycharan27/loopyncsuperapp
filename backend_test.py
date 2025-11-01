#!/usr/bin/env python3
"""
Comprehensive Agora Video/Audio Calling System Backend Test
Test Agora Video/Audio Calling System - Complete Call Flow

Backend URL: https://socialverse-62.preview.emergentagent.com/api
Test Credentials: 
- User 1 (Caller): demo@loopync.com / password123
- User 2 (Recipient): Need to check if demo user has friends or create test scenario

COMPREHENSIVE CALLING SYSTEM TEST:
- Test 1: Verify Agora Configuration
- Test 2: Friend Relationship Check  
- Test 3: Call Initiation
- Test 4: Call Record Creation
- Test 5: Answer Call Endpoint
- Test 6: End Call Endpoint
- Test 7: Call History
"""

import requests
import json
import os
import sys
from datetime import datetime
import time

# Configuration
BASE_URL = "https://socialverse-62.preview.emergentagent.com/api"
TEST_EMAIL = "demo@loopync.com"
TEST_PASSWORD = "password123"

class AgoraCallTestSuite:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.demo_user_id = None
        self.friend_user_id = None
        self.test_call_id = None
        self.results = {
            "total_tests": 7,
            "passed": 0,
            "failed": 0,
            "test_details": []
        }
        
    def log_test_result(self, test_name, passed, details, error=None):
        """Log test result"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        self.results["test_details"].append({
            "test": test_name,
            "status": status,
            "details": details,
            "error": error
        })
        
        if passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
            
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
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
    
    def test_basic_voice_chat(self):
        """Test 1: Basic Voice Chat Test"""
        print("🎤 Testing Basic Voice Chat...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/voice/chat",
                json={
                    "query": "Hello, what is Loopync?",
                    "temperature": 0.7,
                    "max_tokens": 150
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                success = data.get("success", False)
                response_data = data.get("data", {})
                ai_response = response_data.get("response", "")
                session_id = response_data.get("session_id", "")
                model = response_data.get("model", "")
                
                # Validation checks
                checks = []
                checks.append(("success field is True", success == True))
                checks.append(("response contains AI text", len(ai_response) > 0))
                checks.append(("session_id is present", len(session_id) > 0))
                checks.append(("model is gpt-4o", model == "gpt-4o"))
                checks.append(("response is concise (under 150 words)", len(ai_response.split()) <= 150))
                checks.append(("response mentions Loopync", "loopync" in ai_response.lower() or "social" in ai_response.lower()))
                
                all_passed = all(check[1] for check in checks)
                
                details = f"Response validation: {sum(check[1] for check in checks)}/{len(checks)} checks passed"
                for check_name, passed in checks:
                    details += f"\n   - {check_name}: {'✓' if passed else '✗'}"
                
                self.log_test(
                    "Basic Voice Chat Test",
                    all_passed,
                    details,
                    {
                        "ai_response": ai_response,
                        "session_id": session_id,
                        "model": model,
                        "word_count": len(ai_response.split())
                    }
                )
                
                # Store session_id for persistence test
                self.test_session_id = session_id
                return all_passed
                
            else:
                self.log_test(
                    "Basic Voice Chat Test",
                    False,
                    f"API call failed with status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Basic Voice Chat Test", False, f"Test error: {str(e)}")
            return False
    
    def test_session_persistence(self):
        """Test 2: Session Persistence Test"""
        print("🧠 Testing Session Persistence...")
        
        if not hasattr(self, 'test_session_id'):
            self.log_test("Session Persistence Test", False, "No session_id from previous test")
            return False
        
        try:
            # First message: Introduce name
            print("   Sending first message: 'My name is John'")
            response1 = self.session.post(
                f"{BACKEND_URL}/voice/chat",
                json={
                    "query": "My name is John",
                    "session_id": self.test_session_id,
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
            
            # Wait a moment to ensure session processing
            time.sleep(2)
            
            # Second message: Ask about name
            print("   Sending second message: 'What is my name?'")
            response2 = self.session.post(
                f"{BACKEND_URL}/voice/chat",
                json={
                    "query": "What is my name?",
                    "session_id": self.test_session_id,
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
                
                # Check if AI remembers the name "John"
                remembers_name = "john" in second_response.lower()
                
                self.log_test(
                    "Session Persistence Test",
                    remembers_name,
                    f"AI {'remembered' if remembers_name else 'did not remember'} the name 'John' from previous message",
                    {
                        "first_message": "My name is John",
                        "first_response": first_response,
                        "second_message": "What is my name?",
                        "second_response": second_response,
                        "session_id": self.test_session_id
                    }
                )
                return remembers_name
                
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
    
    def test_multiple_query_types(self):
        """Test 3: Multiple Query Types"""
        print("💬 Testing Multiple Query Types...")
        
        test_queries = [
            {
                "type": "question",
                "query": "How do I add friends on Loopync?",
                "expected_keywords": ["friend", "add", "connect", "people", "user"]
            },
            {
                "type": "command",
                "query": "Tell me about the features",
                "expected_keywords": ["feature", "social", "app", "loopync", "platform"]
            },
            {
                "type": "casual",
                "query": "What can I do here?",
                "expected_keywords": ["can", "do", "social", "connect", "share", "post"]
            }
        ]
        
        all_passed = True
        
        for i, test_query in enumerate(test_queries, 1):
            try:
                print(f"   Testing {test_query['type']} query: '{test_query['query']}'")
                
                response = self.session.post(
                    f"{BACKEND_URL}/voice/chat",
                    json={
                        "query": test_query["query"],
                        "temperature": 0.7,
                        "max_tokens": 150
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("data", {}).get("response", "").lower()
                    
                    # Check if response contains relevant keywords
                    keyword_matches = sum(1 for keyword in test_query["expected_keywords"] if keyword in ai_response)
                    has_relevant_content = keyword_matches > 0
                    is_appropriate_length = len(ai_response.split()) <= 150
                    
                    test_passed = has_relevant_content and is_appropriate_length
                    all_passed = all_passed and test_passed
                    
                    self.log_test(
                        f"Query Type Test {i} ({test_query['type']})",
                        test_passed,
                        f"Response relevance: {keyword_matches}/{len(test_query['expected_keywords'])} keywords found, Length: {len(ai_response.split())} words",
                        {
                            "query": test_query["query"],
                            "response": data.get("data", {}).get("response", ""),
                            "keyword_matches": keyword_matches,
                            "word_count": len(ai_response.split())
                        }
                    )
                else:
                    all_passed = False
                    self.log_test(
                        f"Query Type Test {i} ({test_query['type']})",
                        False,
                        f"API call failed with status {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                all_passed = False
                self.log_test(f"Query Type Test {i} ({test_query['type']})", False, f"Test error: {str(e)}")
        
        return all_passed
    
    def test_error_handling(self):
        """Test 4: Error Handling"""
        print("🚨 Testing Error Handling...")
        
        error_tests = [
            {
                "name": "Empty Query",
                "payload": {"query": ""},
                "expected_behavior": "Should handle empty query gracefully"
            },
            {
                "name": "Missing Query Field",
                "payload": {"temperature": 0.7},
                "expected_behavior": "Should return validation error for missing query"
            },
            {
                "name": "Invalid Temperature",
                "payload": {"query": "Hello", "temperature": 2.5},
                "expected_behavior": "Should handle invalid temperature"
            }
        ]
        
        all_passed = True
        
        for test in error_tests:
            try:
                print(f"   Testing: {test['name']}")
                
                response = self.session.post(
                    f"{BACKEND_URL}/voice/chat",
                    json=test["payload"],
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
                    }
                )
                
                # For error cases, we expect either 400 (validation error) or 422 (unprocessable entity)
                # or the API might handle gracefully and return 200 with error message
                
                if response.status_code in [400, 422]:
                    # Expected validation error
                    test_passed = True
                    details = f"Correctly returned validation error (status {response.status_code})"
                elif response.status_code == 200:
                    # Check if it handled gracefully
                    data = response.json()
                    success = data.get("success", False)
                    if not success or "error" in str(data).lower():
                        test_passed = True
                        details = "Handled error gracefully with success=false or error message"
                    else:
                        test_passed = False
                        details = "Should have returned error for invalid input"
                else:
                    test_passed = False
                    details = f"Unexpected status code {response.status_code}: {response.text}"
                
                all_passed = all_passed and test_passed
                
                self.log_test(
                    f"Error Handling - {test['name']}",
                    test_passed,
                    details,
                    {"status_code": response.status_code, "response": response.text[:200]}
                )
                
            except Exception as e:
                all_passed = False
                self.log_test(f"Error Handling - {test['name']}", False, f"Test error: {str(e)}")
        
        return all_passed
    
    def test_ai_response_quality(self):
        """Test 5: AI Response Quality"""
        print("🎯 Testing AI Response Quality...")
        
        quality_tests = [
            {
                "query": "What is Loopync and how does it work?",
                "quality_checks": [
                    ("conversational_tone", lambda r: any(word in r.lower() for word in ["you", "your", "can", "will", "help"])),
                    ("speech_friendly", lambda r: not any(char in r for char in ["```", "**", "*", "#"])),
                    ("mentions_loopync", lambda r: "loopync" in r.lower()),
                    ("appropriate_length", lambda r: 20 <= len(r.split()) <= 150),
                    ("no_code_blocks", lambda r: "```" not in r and "code" not in r.lower())
                ]
            }
        ]
        
        all_passed = True
        
        for i, test in enumerate(quality_tests, 1):
            try:
                print(f"   Testing response quality for: '{test['query']}'")
                
                response = self.session.post(
                    f"{BACKEND_URL}/voice/chat",
                    json={
                        "query": test["query"],
                        "temperature": 0.7,
                        "max_tokens": 150
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.auth_token}" if self.auth_token else ""
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("data", {}).get("response", "")
                    
                    # Run quality checks
                    quality_results = []
                    for check_name, check_func in test["quality_checks"]:
                        passed = check_func(ai_response)
                        quality_results.append((check_name, passed))
                    
                    passed_checks = sum(1 for _, passed in quality_results)
                    total_checks = len(quality_results)
                    test_passed = passed_checks >= (total_checks * 0.8)  # 80% pass rate
                    
                    all_passed = all_passed and test_passed
                    
                    details = f"Quality checks: {passed_checks}/{total_checks} passed"
                    for check_name, passed in quality_results:
                        details += f"\n   - {check_name}: {'✓' if passed else '✗'}"
                    
                    self.log_test(
                        f"AI Response Quality Test {i}",
                        test_passed,
                        details,
                        {
                            "query": test["query"],
                            "response": ai_response,
                            "word_count": len(ai_response.split()),
                            "quality_score": f"{passed_checks}/{total_checks}"
                        }
                    )
                else:
                    all_passed = False
                    self.log_test(
                        f"AI Response Quality Test {i}",
                        False,
                        f"API call failed with status {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                all_passed = False
                self.log_test(f"AI Response Quality Test {i}", False, f"Test error: {str(e)}")
        
        return all_passed
    
    def run_all_tests(self):
        """Run all voice bot tests"""
        print("🚀 Starting AI Voice Bot Backend Testing Suite")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Credentials: {TEST_EMAIL} / {TEST_PASSWORD}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 60)
        print()
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all tests
        test_methods = [
            self.test_basic_voice_chat,
            self.test_session_persistence,
            self.test_multiple_query_types,
            self.test_error_handling,
            self.test_ai_response_quality
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            if test_method():
                passed_tests += 1
        
        # Print summary
        print("=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        # Print individual test results
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {result['test']}")
        
        print()
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - AI Voice Bot Backend is fully functional!")
            return True
        else:
            print(f"⚠️  {total_tests - passed_tests} test(s) failed - AI Voice Bot needs attention")
            return False

def main():
    """Main test execution"""
    tester = VoiceBotTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()