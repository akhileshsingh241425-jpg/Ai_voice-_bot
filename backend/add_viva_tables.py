#!/usr/bin/env python3
"""
Add viva session tables to existing database
"""
from app import create_app
from app.models.models import db
from app.models.viva_models import VivaSession, VivaQuestion, VivaLevel

def add_viva_tables():
    """Add viva session tables to existing database"""
    print("Adding Viva Session tables...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Create only the new viva tables
            VivaSession.__table__.create(db.engine, checkfirst=True)
            VivaQuestion.__table__.create(db.engine, checkfirst=True)
            VivaLevel.__table__.create(db.engine, checkfirst=True)
            
            print("✅ Viva session tables created successfully!")
            
            # Verify tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            viva_tables = ['viva_session', 'viva_question', 'viva_level']
            existing_viva_tables = [t for t in viva_tables if t in tables]
            
            print(f"✅ Viva tables found: {existing_viva_tables}")
            
            if len(existing_viva_tables) == len(viva_tables):
                print("🎉 All viva session tables are ready!")
                return True
            else:
                missing = [t for t in viva_tables if t not in existing_viva_tables]
                print(f"❌ Missing tables: {missing}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating viva tables: {e}")
            return False

if __name__ == "__main__":
    print("=== Adding Viva Session Tables ===")
    if add_viva_tables():
        print("\n✅ Database ready for viva session management!")
    else:
        print("\n❌ Failed to add viva tables")