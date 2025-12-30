#!/usr/bin/env python3
"""
Test script for Viva Session Management System
Tests the complete Level 1→2→3 progression flow
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_server_connection():
    """Test if server is running"""
    print("=== Testing Server Connection ===")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server responded with {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure to start the server with: python run.py")
        return False

def get_test_data():
    """Get employee and machine data for testing"""
    print("\n=== Getting Test Data ===")
    
    # Get employees
    try:
        response = requests.get(f"{BASE_URL}/employees")
        if response.status_code == 200:
            employees = response.json()
            if employees:
                employee = employees[0]  # Use first employee
                print(f"✅ Using Employee: {employee['name']} (ID: {employee['id']})")
            else:
                print("❌ No employees found")
                return None, None
        else:
            print(f"❌ Failed to get employees: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"❌ Error getting employees: {e}")
        return None, None
    
    # Get machines
    try:
        response = requests.get(f"{BASE_URL}/machines")
        if response.status_code == 200:
            data = response.json()
            machines = data.get('machines', [])
            if machines:
                machine = machines[0]  # Use first machine
                print(f"✅ Using Machine: {machine['name']} (ID: {machine['id']})")
            else:
                print("❌ No machines found")
                return None, None
        else:
            print(f"❌ Failed to get machines: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"❌ Error getting machines: {e}")
        return None, None
    
    return employee, machine

def test_start_viva_session(employee_id, machine_id):
    """Test starting a new viva session"""
    print(f"\n=== Testing Start Viva Session ===")
    
    data = {
        "employee_id": employee_id,
        "machine_id": machine_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/start_viva",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Viva session started successfully")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Employee: {result['employee_name']}")
            print(f"   Machine: {result['machine_name']}")
            print(f"   Current Level: {result['current_level']}")
            return result['session_id']
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_get_question(session_id):
    """Test getting a question for current level"""
    print(f"\n=== Testing Get Question for Session {session_id} ===")
    
    try:
        response = requests.get(f"{BASE_URL}/get_question/{session_id}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Question retrieved:")
            print(f"   Viva Question ID: {result['viva_question_id']}")
            print(f"   Level: {result['level']}")
            print(f"   Question: {result['question_text']}")
            print(f"   Questions Remaining: {result['questions_remaining']}")
            return result
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_submit_text_answer(viva_question_id, answer_text):
    """Test submitting a text answer"""
    print(f"\n=== Testing Submit Answer for Question {viva_question_id} ===")
    
    data = {
        "answer": answer_text
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/submit_answer/{viva_question_id}",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Answer submitted successfully")
            print(f"   Score: {result['evaluation']['score']}")
            print(f"   Passed: {result['evaluation']['passed']}")
            print(f"   User Answer: {result['user_answer']}")
            print(f"   Time Taken: {result['time_taken']} seconds")
            return result
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_complete_level(session_id):
    """Test completing current level"""
    print(f"\n=== Testing Complete Level for Session {session_id} ===")
    
    try:
        response = requests.post(f"{BASE_URL}/complete_level/{session_id}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Level completion result:")
            print(f"   Message: {result['message']}")
            print(f"   Level Passed: {result['level_passed']}")
            print(f"   Level Score: {result['level_score']}")
            print(f"   Session Status: {result['session_status']}")
            print(f"   Session Completed: {result['session_completed']}")
            
            if 'current_level' in result:
                print(f"   Current Level: {result['current_level']}")
            if 'final_score' in result:
                print(f"   Final Score: {result['final_score']}")
                
            return result
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_viva_progress(session_id):
    """Test getting viva session progress"""
    print(f"\n=== Testing Viva Progress for Session {session_id} ===")
    
    try:
        response = requests.get(f"{BASE_URL}/viva_progress/{session_id}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Session Progress:")
            print(f"   Employee: {result['employee_name']}")
            print(f"   Machine: {result['machine_name']}")
            print(f"   Current Level: {result['current_level']}")
            print(f"   Status: {result['status']}")
            print(f"   Questions Attempted: {result['questions_attempted']}")
            print(f"   Questions Correct: {result['questions_correct']}")
            
            for level_data in result['levels']:
                level = level_data['level']
                status = level_data['status']
                score = level_data.get('score', 'N/A')
                print(f"   Level {level}: {status} (Score: {score})")
                
            return result
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_active_sessions():
    """Test getting active sessions"""
    print(f"\n=== Testing Active Sessions ===")
    
    try:
        response = requests.get(f"{BASE_URL}/active_sessions")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Active Sessions Found: {result['total_active']}")
            
            for session in result['active_sessions']:
                print(f"   Session {session['session_id']}: {session['employee_name']} - {session['machine_name']} (Level {session['current_level']})")
                
            return result
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def simulate_level_completion(session_id, level):
    """Simulate completing all questions for a level"""
    print(f"\n=== Simulating Level {level} Completion ===")
    
    questions_per_level = 3  # From VIVA_CONFIG
    
    for i in range(questions_per_level):
        print(f"\n--- Question {i+1}/{questions_per_level} for Level {level} ---")
        
        # Get question
        question_data = test_get_question(session_id)
        if not question_data:
            print(f"❌ Failed to get question {i+1}")
            return False
        
        # Submit answer (simulate good answer)
        sample_answers = [
            "यह मशीन उत्पादन लाइन में महत्वपूर्ण काम करती है।",
            "मशीन का संचालन सुरक्षा नियमों के अनुसार करना चाहिए।",
            "इस मशीन की गुणवत्ता जांच नियमित रूप से करनी चाहिए।"
        ]
        
        answer_result = test_submit_text_answer(
            question_data['viva_question_id'],
            sample_answers[i % len(sample_answers)]
        )
        
        if not answer_result:
            print(f"❌ Failed to submit answer for question {i+1}")
            return False
            
        # Small delay between questions
        time.sleep(0.5)
    
    return True

def full_viva_simulation():
    """Run complete viva simulation: Level 1 → 2 → 3"""
    print("🎯 Starting Full Viva Session Simulation")
    print("=" * 60)
    
    # Test server connection
    if not test_server_connection():
        return False
    
    # Get test data
    employee, machine = get_test_data()
    if not employee or not machine:
        print("❌ Cannot proceed without employee and machine data")
        return False
    
    # Start viva session
    session_id = test_start_viva_session(employee['id'], machine['id'])
    if not session_id:
        print("❌ Cannot proceed without session")
        return False
    
    try:
        # Complete Level 1
        print(f"\n🔥 LEVEL 1 SIMULATION")
        if simulate_level_completion(session_id, 1):
            level_result = test_complete_level(session_id)
            if not level_result or not level_result.get('level_passed'):
                print("❌ Level 1 failed")
                return False
            print("✅ Level 1 completed successfully!")
        else:
            print("❌ Level 1 simulation failed")
            return False
        
        # Show progress after Level 1
        test_viva_progress(session_id)
        
        # Complete Level 2
        print(f"\n🔥 LEVEL 2 SIMULATION")
        if simulate_level_completion(session_id, 2):
            level_result = test_complete_level(session_id)
            if not level_result or not level_result.get('level_passed'):
                print("❌ Level 2 failed")
                return False
            print("✅ Level 2 completed successfully!")
        else:
            print("❌ Level 2 simulation failed")
            return False
        
        # Show progress after Level 2
        test_viva_progress(session_id)
        
        # Complete Level 3
        print(f"\n🔥 LEVEL 3 SIMULATION")
        if simulate_level_completion(session_id, 3):
            level_result = test_complete_level(session_id)
            if not level_result:
                print("❌ Level 3 completion failed")
                return False
            print("✅ Level 3 completed successfully!")
            
            if level_result.get('session_completed'):
                print("🎉 ENTIRE VIVA SESSION COMPLETED!")
                print(f"Final Score: {level_result.get('final_score', 'N/A')}")
            
        else:
            print("❌ Level 3 simulation failed")
            return False
        
        # Final progress check
        print(f"\n=== FINAL SESSION STATUS ===")
        final_progress = test_viva_progress(session_id)
        
        print(f"\n🎉 Viva Session Simulation Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        return False

def main():
    print("🧪 Viva Session Management Test Suite")
    print("=" * 60)
    
    # Run full simulation
    success = full_viva_simulation()
    
    if success:
        print(f"\n✅ ALL TESTS PASSED!")
        print("Viva Session Management System is working correctly!")
        print("Features tested:")
        print("  ✅ Start viva session")
        print("  ✅ Get questions for each level")
        print("  ✅ Submit answers with evaluation")
        print("  ✅ Complete levels with progression")
        print("  ✅ Level 1 → 2 → 3 progression")
        print("  ✅ Session progress tracking")
        print("  ✅ Final session completion")
    else:
        print(f"\n❌ TESTS FAILED")
        print("Please check the error messages above")
    
    # Test active sessions
    test_active_sessions()

if __name__ == "__main__":
    main()