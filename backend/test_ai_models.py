#!/usr/bin/env python3
"""
Test script to verify real AI models are working
"""
import requests
import json

def test_stt_endpoint():
    """Test Speech-to-Text endpoint"""
    print("=== Testing STT Endpoint ===")
    url = "http://127.0.0.1:5000/stt"
    
    # Check if test audio file exists
    audio_file = "test_hindi.wav"
    try:
        with open(audio_file, "rb") as f:
            files = {"audio": f}
            response = requests.post(url, files=files, timeout=30)
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ STT Success: {result['text']}")
            return result['text']
        else:
            print(f"❌ STT Failed: {response.status_code} - {response.text}")
            return None
            
    except FileNotFoundError:
        print(f"❌ Audio file '{audio_file}' not found")
        return None
    except Exception as e:
        print(f"❌ STT Error: {e}")
        return None

def test_evaluation_endpoint():
    """Test Answer Evaluation endpoint"""
    print("\n=== Testing Evaluation Endpoint ===")
    url = "http://127.0.0.1:5000/evaluate"
    
    data = {
        "answer": "स्ट्रिंगर मशीन तारों को जोड़ने का काम करती है।",
        "expected_answer": "स्ट्रिंगर मशीन का कार्य तारों को जोड़ना है।", 
        "expected_keywords": ["स्ट्रिंगर", "तारों", "जोड़ना"]
    }
    
    try:
        response = requests.post(url, 
                               data=json.dumps(data), 
                               headers={"Content-Type": "application/json"},
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Evaluation Success:")
            print(f"   Score: {result.get('score', 'N/A')}")
            print(f"   Passed: {result.get('passed', 'N/A')}")
            print(f"   Similarity: {result.get('similarity', 'N/A')}")
            return result
        else:
            print(f"❌ Evaluation Failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Evaluation Error: {e}")
        return None

def test_sstp_pipeline():
    """Test complete STT + Evaluation pipeline"""
    print("\n=== Testing SSTP Pipeline ===")
    url = "http://127.0.0.1:5000/sstp"
    
    audio_file = "test_hindi.wav"
    try:
        with open(audio_file, "rb") as f:
            files = {"audio": f}
            data = {
                "expected_answer": "स्ट्रिंगर मशीन का कार्य तारों को जोड़ना है।",
                "expected_keywords": ["स्ट्रिंगर", "तारों", "जोड़ना"]
            }
            response = requests.post(url, files=files, data=data, timeout=60)
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SSTP Pipeline Success:")
            print(f"   Transcribed: {result.get('transcribed_text', 'N/A')}")
            evaluation = result.get('evaluation', {})
            print(f"   Score: {evaluation.get('score', 'N/A')}")
            print(f"   Passed: {evaluation.get('passed', 'N/A')}")
            return result
        else:
            print(f"❌ SSTP Failed: {response.status_code} - {response.text}")
            return None
            
    except FileNotFoundError:
        print(f"❌ Audio file '{audio_file}' not found")
        return None
    except Exception as e:
        print(f"❌ SSTP Error: {e}")
        return None

def test_server_connection():
    """Test if server is running"""
    print("=== Testing Server Connection ===")
    try:
        response = requests.get("http://127.0.0.1:5000/", timeout=5)
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
    print("🤖 AI Models Test Suite")
    print("=" * 50)
    
    # Test server connection first
    if not test_server_connection():
        return
    
    # Test individual endpoints
    test_evaluation_endpoint()  # This loads sentence-transformers
    test_stt_endpoint()         # This loads Whisper (may take time)
    test_sstp_pipeline()        # This uses both models
    
    print("\n🎉 AI Models testing completed!")
    print("Note: First STT request may be slow due to Whisper model loading")

if __name__ == "__main__":
    main()