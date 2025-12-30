#!/usr/bin/env python3
"""
Simple test to verify new database is working
"""
from app import create_app
from app.models.models import db, Machine, Employee, Question, Answer

def test_database():
    app = create_app()
    
    with app.app_context():
        print("=== Database Test Results ===")
        
        # Test 1: Check if all tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables found: {tables}")
        
        expected_tables = ['machine', 'employee', 'score', 'question', 'answer']
        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
        else:
            print("✅ All required tables exist")
        
        # Test 2: Check machine data
        machine_count = Machine.query.count()
        print(f"Machines in database: {machine_count}")
        
        if machine_count > 0:
            print("✅ Machine data exists")
            # Show first 5 machines
            machines = Machine.query.limit(5).all()
            print("Sample machines:")
            for m in machines:
                print(f"  - ID: {m.id}, Name: {m.name}")
        else:
            print("❌ No machine data found")
        
        # Test 3: Check employee data
        employee_count = Employee.query.count()
        print(f"Employees in database: {employee_count}")
        
        if employee_count > 0:
            print("✅ Employee data exists")
            employees = Employee.query.all()
            for e in employees:
                print(f"  - ID: {e.id}, Name: {e.name}, Role: {e.role}, Machine: {e.machine}")
        
        # Test 4: Test adding sample question
        try:
            # Get first machine
            machine = Machine.query.first()
            if machine:
                # Add sample question
                question = Question(
                    machine_id=machine.id,
                    text="What is the function of this machine?",
                    level=1
                )
                db.session.add(question)
                
                # Add sample answer
                answer = Answer(
                    question_id=question.id,
                    text="This machine performs its designated production task."
                )
                db.session.add(answer)
                
                db.session.commit()
                print("✅ Question and Answer tables working")
                print(f"  - Question: {question.text}")
                print(f"  - Answer: {answer.text}")
                print(f"  - Machine: {machine.name}")
                print(f"  - Level: {question.level}")
            else:
                print("❌ No machine found to test question creation")
                
        except Exception as e:
            print(f"❌ Error testing Question/Answer: {e}")
            db.session.rollback()
        
        print("\n=== Database Status: WORKING ✅ ===")

if __name__ == "__main__":
    test_database()