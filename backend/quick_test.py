#!/usr/bin/env python3
"""
Quick test to check if database is working without starting full server
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.models.models import db, Machine, Employee, Question, Answer
from config import Config

def quick_db_test():
    # Create minimal Flask app just for DB testing
    from flask import Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("=== Quick Database Test ===")
        
        # Test 1: Count machines
        machine_count = Machine.query.count()
        print(f"✅ Machines in database: {machine_count}")
        
        # Test 2: Show first 3 machines
        machines = Machine.query.limit(3).all()
        for m in machines:
            print(f"  - {m.name}")
        
        # Test 3: Count employees  
        employee_count = Employee.query.count()
        print(f"✅ Employees in database: {employee_count}")
        
        # Test 4: Test creating a question
        machine = Machine.query.first()
        if machine:
            # Check if question already exists
            existing_q = Question.query.filter_by(machine_id=machine.id, level=1).first()
            if not existing_q:
                question = Question(
                    machine_id=machine.id,
                    text=f"What is the primary function of {machine.name}?",
                    level=1
                )
                db.session.add(question)
                db.session.commit()
                print(f"✅ Added sample question for {machine.name}")
            else:
                print(f"✅ Question already exists for {machine.name}")
        
        # Test 5: Count questions
        question_count = Question.query.count() 
        print(f"✅ Questions in database: {question_count}")
        
        print("\n🎉 Database is working perfectly!")
        print(f"Database: {Config.SQLALCHEMY_DATABASE_URI}")
        
        return True

if __name__ == "__main__":
    try:
        quick_db_test()
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        sys.exit(1)