import requests
import json

url = "http://localhost:5000/generate_questions"

# Example data
payload = {
    "department": "quality",
    "filename": "quality_manual.pdf",  # Change to your uploaded manual filename
    "num_questions": 5,
    "qtype": "factual"  # Options: factual, conceptual, scenario
}

response = requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
print("Questions:")
for q in response.json().get('questions', []):
    print(q)
