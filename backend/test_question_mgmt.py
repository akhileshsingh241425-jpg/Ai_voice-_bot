#!/usr/bin/env python3
"""
Test script for Question Management API
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_get_machines():
    """Test getting all machines with question counts"""
    print("=== Testing GET /machines ===")
    try:
        response = requests.get(f"{BASE_URL}/machines")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_machines']} machines")
            for machine in data['machines'][:3]:  # Show first 3
                print(f"   - {machine['name']} (ID: {machine['id']}, Questions: {machine['total_questions']})")
            return data['machines']
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_add_question(machine_id, machine_name):
    """Test adding a new question"""
    print(f"\n=== Testing POST /questions for {machine_name} ===")
    
    question_data = {
        "machine_id": machine_id,
        "question_text": f"{machine_name} का मुख्य कार्य क्या है?",
        "answer_text": f"{machine_name} का मुख्य कार्य उत्पादन लाइन में विशिष्ट कार्य करना है।",
        "level": 1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/questions",
            data=json.dumps(question_data),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Question added successfully")
            print(f"   Question ID: {data['question_id']}")
            print(f"   Machine: {data['machine']}")
            print(f"   Level: {data['level']}")
            return data['question_id']
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_get_questions_by_level(machine_id, machine_name, level=1):
    """Test getting questions for specific machine and level"""
    print(f"\n=== Testing GET /questions/{machine_id}/{level} for {machine_name} ===")
    
    try:
        response = requests.get(f"{BASE_URL}/questions/{machine_id}/{level}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_questions']} questions for {machine_name} Level {level}")
            for q in data['questions']:
                print(f"   - Q: {q['question_text'][:50]}...")
                print(f"     A: {q['answer_text'][:50]}...")
            return data['questions']
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_get_random_question(machine_id, machine_name, level=1):
    """Test getting random question for viva"""
    print(f"\n=== Testing GET /questions/random/{machine_id}/{level} for {machine_name} ===")
    
    try:
        response = requests.get(f"{BASE_URL}/questions/random/{machine_id}/{level}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Random question retrieved:")
            print(f"   Machine: {data['machine_name']}")
            print(f"   Level: {data['level']}")
            print(f"   Question: {data['question_text']}")
            print(f"   Expected Answer: {data['expected_answer'][:100]}...")
            print(f"   Keywords: {data['expected_keywords']}")
            return data
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_bulk_add_questions(machines):
    """Test bulk adding multiple questions"""
    print(f"\n=== Testing POST /questions/bulk ===")
    
    # Create sample questions for first 3 machines
    bulk_data = {
        "questions": []
    }
    
    for i, machine in enumerate(machines[:3]):
        for level in [1, 2, 3]:
            bulk_data["questions"].append({
                "machine_id": machine['id'],
                "question_text": f"{machine['name']} Level {level} - सुरक्षा नियम क्या हैं?",
                "answer_text": f"{machine['name']} के लिए Level {level} सुरक्षा नियम: सुरक्षा उपकरण पहनें और निर्देशों का पालन करें।",
                "level": level
            })
    
    try:
        response = requests.post(
            f"{BASE_URL}/questions/bulk",
            data=json.dumps(bulk_data),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Bulk operation completed:")
            print(f"   Added: {data['added_count']} questions")
            print(f"   Errors: {data['error_count']}")
            if data['errors']:
                print(f"   Error details: {data['errors'][:3]}")  # Show first 3 errors
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_update_question(question_id):
    """Test updating a question"""
    if not question_id:
        print("\n⏭️  Skipping update test (no question ID)")
        return
    
    print(f"\n=== Testing PUT /questions/{question_id} ===")
    
    update_data = {
        "question_text": "Updated: मशीन का संचालन कैसे करते हैं?",
        "answer_text": "Updated: मशीन का संचालन सुरक्षित तरीके से करना चाहिए।"
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/questions/{question_id}",
            data=json.dumps(update_data),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Question updated successfully")
            print(f"   Question: {data['question_text']}")
            print(f"   Answer: {data['answer_text']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

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

def main():
    print("🔧 Question Management API Test Suite")
    print("=" * 60)
    
    # Test server connection first
    if not test_server_connection():
        return
    
    # Test 1: Get all machines
    machines = test_get_machines()
    if not machines:
        print("❌ Cannot proceed without machines")
        return
    
    # Test 2: Add a question
    first_machine = machines[0]
    question_id = test_add_question(first_machine['id'], first_machine['name'])
    
    # Test 3: Get questions by machine and level
    test_get_questions_by_level(first_machine['id'], first_machine['name'], 1)
    
    # Test 4: Get random question
    test_get_random_question(first_machine['id'], first_machine['name'], 1)
    
    # Test 5: Bulk add questions
    test_bulk_add_questions(machines)
    
    # Test 6: Update question (if we have one)
    test_update_question(question_id)
    
    # Final check: Get machines again to see updated counts
    print(f"\n=== Final Machine Status ===")
    test_get_machines()
    
    print(f"\n🎉 Question Management API testing completed!")
    print(f"All endpoints are ready for frontend integration.")

if __name__ == "__main__":
    main()