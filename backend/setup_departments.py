"""
Setup Department Structure for Solar Panel Manufacturing
Run this to create the proper hierarchy:
- Production (Pre-Lam, Post-Lam)
- Quality (IPQC, IQC, FQC)  
- Maintenance (Machine Maintenance, Utility)
- FG Area (Important Stages)
"""

import pymysql
from datetime import datetime

# Database connection
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='ai_voice_bot_new',
    port=3306
)

def setup_structure():
    try:
        with connection.cursor() as cursor:
            # Create Department table
            print("Creating Department table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS department (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    code VARCHAR(20) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create SubDepartment table
            print("Creating SubDepartment table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sub_department (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    department_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    code VARCHAR(20),
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (department_id) REFERENCES department(id)
                )
            """)
            
            # Add columns to Machine table if not exist
            print("Updating Machine table...")
            try:
                cursor.execute("ALTER TABLE machine ADD COLUMN sub_department_id INT")
            except:
                pass  # Column might already exist
            
            try:
                cursor.execute("ALTER TABLE machine ADD COLUMN category VARCHAR(50) DEFAULT 'General'")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE machine ADD COLUMN code VARCHAR(20)")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE machine ADD COLUMN description TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE machine ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            except:
                pass
            
            connection.commit()
            
            # Insert Departments
            print("\nInserting Departments...")
            departments = [
                ('Production', 'PROD', 'Solar Panel Production - Pre-Lam & Post-Lam'),
                ('Quality', 'QC', 'Quality Control - IPQC, IQC, FQC'),
                ('Maintenance', 'MAINT', 'Machine Maintenance & Utility'),
                ('FG Area', 'FG', 'Finished Goods - Important Stages')
            ]
            
            for name, code, desc in departments:
                cursor.execute("SELECT id FROM department WHERE code = %s", (code,))
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO department (name, code, description) VALUES (%s, %s, %s)",
                        (name, code, desc)
                    )
                    print(f"  ✅ Added: {name}")
                else:
                    print(f"  ⏭️ Exists: {name}")
            
            connection.commit()
            
            # Get department IDs
            cursor.execute("SELECT id, code FROM department")
            dept_ids = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Insert Sub-Departments
            print("\nInserting Sub-Departments...")
            sub_depts = [
                # Production
                (dept_ids['PROD'], 'Pre-Lam', 'PRELAM', 'Pre-Lamination Process'),
                (dept_ids['PROD'], 'Post-Lam', 'POSTLAM', 'Post-Lamination Process'),
                
                # Quality
                (dept_ids['QC'], 'IPQC', 'IPQC', 'In-Process Quality Control'),
                (dept_ids['QC'], 'IQC', 'IQC', 'Incoming Quality Control'),
                (dept_ids['QC'], 'FQC', 'FQC', 'Final Quality Control'),
                
                # Maintenance
                (dept_ids['MAINT'], 'Machine Maintenance', 'MACHMAINT', 'Machine Maintenance'),
                (dept_ids['MAINT'], 'Utility', 'UTIL', 'Utility Maintenance'),
                
                # FG Area
                (dept_ids['FG'], 'FG Stages', 'FGSTAGE', 'Finished Goods Important Stages'),
            ]
            
            for dept_id, name, code, desc in sub_depts:
                cursor.execute("SELECT id FROM sub_department WHERE code = %s", (code,))
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO sub_department (department_id, name, code, description) VALUES (%s, %s, %s, %s)",
                        (dept_id, name, code, desc)
                    )
                    print(f"  ✅ Added: {name}")
                else:
                    print(f"  ⏭️ Exists: {name}")
            
            connection.commit()
            
            # Get sub-department IDs
            cursor.execute("SELECT id, code FROM sub_department")
            subdept_ids = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Insert/Update Machines
            print("\nSetting up Machines...")
            machines = [
                # Pre-Lam Machines
                (subdept_ids['PRELAM'], 'Stringer', 'STR', 'Pre-Lam', 'Cell Stringing Machine'),
                (subdept_ids['PRELAM'], 'Pre EL', 'PREEL', 'Pre-Lam', 'Pre-Lamination EL Testing'),
                (subdept_ids['PRELAM'], 'Layup', 'LAYUP', 'Pre-Lam', 'Module Layup Station'),
                (subdept_ids['PRELAM'], 'Cell Tester', 'CELLTEST', 'Pre-Lam', 'Cell Testing Machine'),
                (subdept_ids['PRELAM'], 'Tabber', 'TAB', 'Pre-Lam', 'Tabbing Machine'),
                
                # Post-Lam Machines
                (subdept_ids['POSTLAM'], 'Laminator', 'LAM', 'Post-Lam', 'Lamination Machine'),
                (subdept_ids['POSTLAM'], 'Post EL', 'POSTEL', 'Post-Lam', 'Post-Lamination EL Testing'),
                (subdept_ids['POSTLAM'], 'Sun Simulator', 'SUNSIM', 'Post-Lam', 'Sun Simulator/Flash Tester'),
                (subdept_ids['POSTLAM'], 'Framing', 'FRAME', 'Post-Lam', 'Frame Fitting Machine'),
                (subdept_ids['POSTLAM'], 'Junction Box', 'JB', 'Post-Lam', 'Junction Box Attachment'),
                (subdept_ids['POSTLAM'], 'Hi-Pot Tester', 'HIPOT', 'Post-Lam', 'High Potential Tester'),
                
                # IPQC
                (subdept_ids['IPQC'], 'IPQC Station', 'IPQC1', 'IPQC', 'In-Process Quality Check Point'),
                (subdept_ids['IPQC'], 'Visual Inspection', 'VISINSP', 'IPQC', 'Visual Inspection Station'),
                
                # IQC
                (subdept_ids['IQC'], 'IQC Lab', 'IQC1', 'IQC', 'Incoming Material Testing'),
                (subdept_ids['IQC'], 'Cell Inspection', 'CELLINSP', 'IQC', 'Incoming Cell Inspection'),
                
                # FQC
                (subdept_ids['FQC'], 'FQC Station', 'FQC1', 'FQC', 'Final Quality Check'),
                (subdept_ids['FQC'], 'Packing Inspection', 'PACKINSP', 'FQC', 'Packing Quality Check'),
                
                # Maintenance
                (subdept_ids['MACHMAINT'], 'Machine Maintenance', 'MMAINT', 'Maintenance', 'Machine Preventive Maintenance'),
                (subdept_ids['UTIL'], 'Utility Systems', 'UTILITY', 'Maintenance', 'Utility Systems Maintenance'),
                
                # FG Area
                (subdept_ids['FGSTAGE'], 'Stringer FG', 'STRFG', 'FG Area', 'Stringer Stage for FG'),
                (subdept_ids['FGSTAGE'], 'Pre EL FG', 'PREELFG', 'FG Area', 'Pre EL Stage for FG'),
                (subdept_ids['FGSTAGE'], 'Post EL FG', 'POSTELFG', 'FG Area', 'Post EL Stage for FG'),
                (subdept_ids['FGSTAGE'], 'Laminator FG', 'LAMFG', 'FG Area', 'Laminator Stage for FG'),
                (subdept_ids['FGSTAGE'], 'Sun Simulator FG', 'SUNSIMFG', 'FG Area', 'Sun Simulator Stage for FG'),
            ]
            
            for subdept_id, name, code, category, desc in machines:
                cursor.execute("SELECT id FROM machine WHERE name = %s", (name,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing machine
                    cursor.execute("""
                        UPDATE machine 
                        SET sub_department_id = %s, code = %s, category = %s, description = %s, is_active = TRUE
                        WHERE id = %s
                    """, (subdept_id, code, category, desc, existing[0]))
                    print(f"  🔄 Updated: {name}")
                else:
                    # Insert new machine
                    cursor.execute("""
                        INSERT INTO machine (name, code, sub_department_id, category, description, is_active)
                        VALUES (%s, %s, %s, %s, %s, TRUE)
                    """, (name, code, subdept_id, category, desc))
                    print(f"  ✅ Added: {name}")
            
            connection.commit()
            
            # Show summary
            print("\n" + "="*50)
            print("📊 STRUCTURE SUMMARY")
            print("="*50)
            
            cursor.execute("""
                SELECT d.name as dept, sd.name as subdept, m.name as machine, m.category
                FROM department d
                LEFT JOIN sub_department sd ON sd.department_id = d.id
                LEFT JOIN machine m ON m.sub_department_id = sd.id
                ORDER BY d.id, sd.id, m.id
            """)
            
            current_dept = None
            current_subdept = None
            
            for row in cursor.fetchall():
                dept, subdept, machine, category = row
                
                if dept != current_dept:
                    print(f"\n📁 {dept}")
                    current_dept = dept
                    current_subdept = None
                
                if subdept != current_subdept and subdept:
                    print(f"   ├── {subdept}")
                    current_subdept = subdept
                
                if machine:
                    print(f"   │   ├── {machine}")
            
            print("\n✅ Setup complete!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        connection.close()


if __name__ == '__main__':
    setup_structure()
