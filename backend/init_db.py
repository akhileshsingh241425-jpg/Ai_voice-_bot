#!/usr/bin/env python3
"""
Fixed init_db.py - Creates tables without heavy operations
Use create_fresh_db.py for full database setup with data
"""

from app import create_app
from app.services.db_init import init_db

def main():
    try:
        print("=== Database Initialization ===")
        
        # Create Flask app
        app = create_app()
        print("✅ Flask app created")
        
        # Initialize database tables
        init_db(app)
        print("✅ Database tables created")
        
        # Check if we already have data
        from app.models.models import db, Machine
        with app.app_context():
            machine_count = Machine.query.count()
            if machine_count > 0:
                print(f"✅ Found {machine_count} machines already in database")
            else:
                print("ℹ️  No machines found. Run create_fresh_db.py to add data")
        
        print("\n🎉 Database initialization completed successfully!")
        print("Note: Use create_fresh_db.py to populate with production machines")
        
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
