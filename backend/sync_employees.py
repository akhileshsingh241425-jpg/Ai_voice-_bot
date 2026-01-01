import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from flask import Flask
from app.models.models import db, Employee

# Update this URI to your actual DB URI if needed
DB_URI = 'mysql+pymysql://root:root@localhost/ai_voice_bot_new'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

API_URL = "https://hrm.umanerp.com/api/users/getEmployee"

FIELD_MAP = {
    'employeeId': 'employee_id',
    'fullName': 'full_name',
    'fatherName': 'father_name',
    'companyName': 'company_name',
    'department': 'department',
    'designation': 'designation',
    'status': 'status',
    'userImg': 'user_img',
    'lineUnit': 'line_unit',
    'dateOfJoining': 'date_of_joining',
    'mobileNumber': 'mobile_number',
    'reportingHead': 'reporting_head',
}




def fetch_active_employees():
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    employees = data.get("employees", [])
    return [emp for emp in employees if emp.get("status") == "Approved"]




def sync_employees():
    with app.app_context():
        active_employees = fetch_active_employees()
        for emp in active_employees:
            db_emp = Employee.query.filter_by(employee_id=emp['employeeId']).first()
            if not db_emp:
                db_emp = Employee(
                    employee_id=emp['employeeId'],
                    name=emp.get('fullName', 'Unknown'),
                    role=emp.get('designation', 'Unknown'),
                    machine='General'
                )
                db.session.add(db_emp)
            for api_field, model_field in FIELD_MAP.items():
                setattr(db_emp, model_field, emp.get(api_field, None))
            # Also update legacy fields
            db_emp.name = emp.get('fullName', db_emp.name)
        db.session.commit()
        print(f"Synced {len(active_employees)} active employees to database.")



if __name__ == "__main__":
    sync_employees()
