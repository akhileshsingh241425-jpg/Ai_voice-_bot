import requests

url = "http://localhost:5000/sstp"

audio_path = "test_hindi.wav"  # Your recorded Hindi audio file
expected_answer = "स्ट्रिंगर मशीन का कार्य तारों को जोड़ना है।"
expected_keywords = ["स्ट्रिंगर", "तारों", "जोड़ना"]

with open(audio_path, "rb") as audio_file:
    files = {"audio": audio_file}
    data = {
        "expected_answer": expected_answer,
        "expected_keywords": expected_keywords
    }
    response = requests.post(url, files=files, data=data)
    print("Response:", response.json())
