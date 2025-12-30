#!/usr/bin/env python3
"""
Fresh database creation script that drops and recreates everything
"""

from app import create_app
from app.models.models import db, Machine, Question, Answer, Employee, Score
import pymysql

# Database configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'ai_voice_bot_new'

def create_fresh_database():
    """Drop old database and create fresh one"""
    print("Creating fresh database...")
    
    # Connect to MySQL server (without database)
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # Drop database if exists
            cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
            print(f"Dropped database {DB_NAME} if it existed")
            
            # Create new database
            cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"Created new database {DB_NAME}")
            
        connection.commit()
        print("Database operations completed successfully")
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
    finally:
        connection.close()
    
    return True

def create_tables_and_data():
    """Create tables and insert sample data"""
    print("Creating Flask app and tables...")
    
    # Update config to use new database
    import config
    config.Config.SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/{DB_NAME}'
    
    app = create_app()
    
    with app.app_context():
        # Create all tables
        print("Creating tables...")
        db.create_all()
        print("Tables created successfully!")
        
        # Insert machines
        print("Inserting machines...")
        machines = [
            "Glass Loader C-1",
            "Glass Loader C-2", 
            "Front EPE Machine C1",
            "EPE Soldering Machine C1",
            "ATW Stringer",
            "Auto Layup & Bussing",
            "Auto Tapping C-1",
            "Auto Barcode Machine C-1",
            "Back EVA Machine C-1",
            "TPT Machine C-1",
            "Lead flattening Machine C-1",
            "EL",
            "Edge Sealing Machine C-1",
            "Laminaor",
            "Auto Tape Removal Machine C-1",
            "Trimming machine",
            "In-line Visual inspection C-1",
            "Auto Framing",
            "JB Glue Dispenser",
            "JB Soldering Machine",
            "Auto Potting C-1",
            "Frame & JB Inspection C-2",
            "Curing Line",
            "Corner Buffing Machine C-1",
            "Sun-Simulator",
            "Hi-POT",
            "Post-EL",
            "Auto-labelling Machine C-1",
            "Corner Cap Machine C-1",
            "Auto Sorter"
        ]
        
        # Insert machines in batches
        for i, machine_name in enumerate(machines, 1):
            machine = Machine(name=machine_name)
            db.session.add(machine)
            print(f"Added machine {i}/30: {machine_name}")
            
            # Commit every 10 machines to avoid memory issues
            if i % 10 == 0:
                db.session.commit()
                print(f"Committed batch of {i} machines")
        
        # Final commit
        db.session.commit()
        print(f"All {len(machines)} machines inserted successfully!")
        
        # Insert sample employee
        sample_employee = Employee(
            name="Test Employee",
            role="Operator", 
            machine="ATW Stringer"
        )
        db.session.add(sample_employee)
        db.session.commit()
        print("Sample employee added")
        
        # Verify tables exist
        tables = db.engine.table_names()
        print(f"\nCreated tables: {tables}")
        
        # Verify machine count
        machine_count = Machine.query.count()
        print(f"Total machines in database: {machine_count}")
        
    print("\nDatabase setup completed successfully!")
    return True

if __name__ == "__main__":
    print("=== Fresh Database Creation ===")
    
    # Step 1: Create fresh database
    if create_fresh_database():
        print("\nStep 1: Database created ✅")
    else:
        print("\nStep 1: Database creation failed ❌")
        exit(1)
    
    # Step 2: Create tables and insert data  
    if create_tables_and_data():
        print("\nStep 2: Tables and data created ✅")
        print("\n🎉 Fresh database setup complete!")
        print(f"\nNew database: {DB_NAME}")
        print("Update your config.py to use the new database name.")
    else:
        print("\nStep 2: Table creation failed ❌")
        exit(1)