import requests
import json

def fetch_active_employees():
    url = "https://hrm.umanerp.com/api/users/getEmployee"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    employees = data.get("employees", [])
    active_employees = [emp for emp in employees if emp.get("status") == "Approved"]
    return active_employees

if __name__ == "__main__":
    active = fetch_active_employees()
    print(f"Total active employees: {len(active)}")
    print(json.dumps(active[:5], indent=2, ensure_ascii=False))  # Show first 5 as sample
