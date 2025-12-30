import requests

url = "http://127.0.0.1:5000/stt"
audio_file_path = "./test_hindi.wav"  # WAV file is in backend folder

with open(audio_file_path, "rb") as f:
    files = {"audio": f}  # Use 'audio' as key to match backend expectation
    response = requests.post(url, files=files)

print("Status Code:", response.status_code)
print("Response:", response.text)