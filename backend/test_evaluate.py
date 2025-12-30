import requests
import json

url = "http://localhost:5000/evaluate"
data = {
    "answer": "स्ट्रिंगर मशीन तारों को जोड़ने का काम करती है।",
    "expected_answer": "स्ट्रिंगर मशीन का कार्य तारों को जोड़ना है।",
    "expected_keywords": ["स्ट्रिंगर", "तारों", "जोड़ना"]
}

response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
print("Response:", response.json())
