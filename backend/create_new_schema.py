"""
Complete Database Schema for Training-based Viva System
Based on Gautam Solar Training Structure

Structure:
- Department (Production, Quality, Maintenance & Utility)
- Training Category (Process/Technical, Awareness, Quality, Safety, System)
- Training Topic (All training topics mapped to department & category)
- QA Bank (Questions per training topic)
- Employee (With department)
- Training Record (Employee training completion)
- Viva Session (Viva details)
- Viva Result (Detailed results)
"""

import pymysql
from datetime import datetime

# Database connection
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='ai_voice_bot_new',
    port=3306
)
cursor = conn.cursor()

print("="*60)
print("🔧 CREATING NEW TRAINING-BASED SCHEMA")
print("="*60)

# ============================================
# DROP OLD TABLES (if needed)
# ============================================
print("\n📦 Dropping old tables...")
old_tables = [
    'viva_result', 'viva_session', 'training_record', 
    'qa_bank_new', 'training_topic', 'training_category',
    'employee_new', 'department_new'
]
for table in old_tables:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    except:
        pass
conn.commit()

# ============================================
# 1. DEPARTMENT TABLE
# ============================================
print("\n1️⃣ Creating department table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS department_new (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("   ✅ department_new created")

# ============================================
# 2. TRAINING CATEGORY TABLE
# ============================================
print("\n2️⃣ Creating training_category table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS training_category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("   ✅ training_category created")

# ============================================
# 3. TRAINING TOPIC TABLE
# ============================================
print("\n3️⃣ Creating training_topic table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS training_topic (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50),
    description TEXT,
    category_id INT,
    is_common BOOLEAN DEFAULT FALSE,
    duration_hours DECIMAL(4,1) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES training_category(id)
)
""")
print("   ✅ training_topic created")

# ============================================
# 4. DEPARTMENT-TOPIC MAPPING (Many-to-Many)
# ============================================
print("\n4️⃣ Creating department_topic_mapping table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS department_topic_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    topic_id INT NOT NULL,
    is_mandatory BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (department_id) REFERENCES department_new(id),
    FOREIGN KEY (topic_id) REFERENCES training_topic(id),
    UNIQUE KEY unique_mapping (department_id, topic_id)
)
""")
print("   ✅ department_topic_mapping created")

# ============================================
# 5. EMPLOYEE TABLE
# ============================================
print("\n5️⃣ Creating employee_new table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS employee_new (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    department_id INT,
    designation VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    join_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES department_new(id)
)
""")
print("   ✅ employee_new created")

# ============================================
# 6. QA BANK TABLE (Per Training Topic)
# ============================================
print("\n6️⃣ Creating qa_bank_new table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS qa_bank_new (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    question TEXT NOT NULL,
    expected_answer TEXT NOT NULL,
    level INT DEFAULT 1 COMMENT '1=Easy, 2=Medium, 3=Hard',
    language VARCHAR(20) DEFAULT 'Hindi',
    keywords TEXT,
    times_asked INT DEFAULT 0,
    times_correct INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES training_topic(id)
)
""")
print("   ✅ qa_bank_new created")

# ============================================
# 7. TRAINING RECORD (Employee Training Completion)
# ============================================
print("\n7️⃣ Creating training_record table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS training_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    topic_id INT NOT NULL,
    training_date DATE NOT NULL,
    trainer_name VARCHAR(100),
    training_type ENUM('New Joiner', 'Refresher', 'Upgrade') DEFAULT 'New Joiner',
    status ENUM('Completed', 'Pending Viva', 'Passed', 'Failed') DEFAULT 'Completed',
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employee_new(id),
    FOREIGN KEY (topic_id) REFERENCES training_topic(id)
)
""")
print("   ✅ training_record created")

# ============================================
# 8. VIVA SESSION TABLE
# ============================================
print("\n8️⃣ Creating viva_session_new table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS viva_session_new (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    employee_id INT NOT NULL,
    topic_id INT NOT NULL,
    training_record_id INT,
    total_questions INT DEFAULT 20,
    answered_questions INT DEFAULT 0,
    status ENUM('Active', 'Completed', 'Abandoned') DEFAULT 'Active',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (employee_id) REFERENCES employee_new(id),
    FOREIGN KEY (topic_id) REFERENCES training_topic(id),
    FOREIGN KEY (training_record_id) REFERENCES training_record(id)
)
""")
print("   ✅ viva_session_new created")

# ============================================
# 9. VIVA RESULT TABLE
# ============================================
print("\n9️⃣ Creating viva_result_new table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS viva_result_new (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    employee_id INT NOT NULL,
    topic_id INT NOT NULL,
    total_questions INT NOT NULL,
    correct_answers INT NOT NULL,
    total_score INT NOT NULL,
    percentage DECIMAL(5,2) NOT NULL,
    grade VARCHAR(5),
    passed BOOLEAN NOT NULL,
    detailed_results JSON,
    evaluated_by VARCHAR(100),
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employee_new(id),
    FOREIGN KEY (topic_id) REFERENCES training_topic(id)
)
""")
print("   ✅ viva_result_new created")

conn.commit()

print("\n" + "="*60)
print("✅ ALL TABLES CREATED SUCCESSFULLY!")
print("="*60)

# ============================================
# SEED DATA - DEPARTMENTS
# ============================================
print("\n📊 SEEDING DATA...")
print("\n1️⃣ Adding Departments...")

departments = [
    ('Production', 'PROD', 'Production Department - Solar Module Manufacturing'),
    ('Quality', 'QA', 'Quality Department - IQC, IPQC, FQC'),
    ('Maintenance & Utility', 'MAINT', 'Maintenance and Utility Department'),
]

for name, code, desc in departments:
    cursor.execute("""
        INSERT INTO department_new (name, code, description) 
        VALUES (%s, %s, %s)
    """, (name, code, desc))
print(f"   ✅ Added {len(departments)} departments")

# ============================================
# SEED DATA - TRAINING CATEGORIES
# ============================================
print("\n2️⃣ Adding Training Categories...")

categories = [
    ('Process / Technical', 'PROC', 'Process and Technical Training'),
    ('Awareness / System', 'AWARE', 'Awareness and System Training'),
    ('Quality & Inspection', 'QC', 'Quality Control and Inspection'),
    ('Quality Systems', 'QS', 'Quality Management Systems'),
    ('Safety Specific', 'SAFETY', 'Safety Related Training'),
    ('Common Training', 'COMMON', 'Common Training for All'),
]

for name, code, desc in categories:
    cursor.execute("""
        INSERT INTO training_category (name, code, description) 
        VALUES (%s, %s, %s)
    """, (name, code, desc))
print(f"   ✅ Added {len(categories)} categories")

conn.commit()

# Get category IDs
cursor.execute("SELECT id, code FROM training_category")
cat_map = {row[1]: row[0] for row in cursor.fetchall()}

# Get department IDs
cursor.execute("SELECT id, code FROM department_new")
dept_map = {row[1]: row[0] for row in cursor.fetchall()}

# ============================================
# SEED DATA - TRAINING TOPICS
# ============================================
print("\n3️⃣ Adding Training Topics...")

# Production - Process/Technical
production_process = [
    'Tabber & Stringer Process',
    'Autobussing Process',
    'Lamination Process',
    'JB & Framing Process',
    'Rework Process',
    'Raw Material Processing & Cutting',
    'Solar Module Manufacturing Process & Testing',
    'Sun Simulator Operation',
    'EL Process (Pre & Post)',
    'Proper Cleaning Process & Checking Criteria',
    'Dispatch & Packaging Process',
]

# Production - Awareness/System
production_awareness = [
    'Handling Practices of Solar Module',
    'SOP / WI Awareness',
    'Functional & Department Know-how',
]

# Quality - Quality & Inspection
quality_inspection = [
    'IQC Testing - Criteria, Process & Specifications',
    'IPQC Process & Checking Criteria',
    'FQC Process & Checking Criteria',
    'EL Process - Importance, Defects & Interpretation',
    'Hi-Pot Testing - Process, Validation & Safety',
    'Sun Simulator Operation & Acceptance Criteria',
]

# Quality - Quality Systems
quality_systems = [
    'Quality Tools Awareness',
    'ISO Awareness & Implementation (9001/14001/45001/50001)',
    'GSPL Quality Policy & QMS Awareness',
    'Document Control & SOP/WI Awareness',
]

# Maintenance - Technical
maintenance_technical = [
    'Preventive Maintenance & Breakdown Maintenance',
    'General Electrical Check-up',
    'Hi-Pot Safety Awareness',
    'Production Tools Awareness',
    'Utility Equipment Handling',
    'Computer Skills Upgradation',
]

# Maintenance - Safety Specific
maintenance_safety = [
    'Electrical Safety (General Work)',
    'Process Safety Management',
    'Fire Fighting',
    'First Aid',
    'Excavation Safety',
    'Environmental Safety',
    'Emergency Response Plan',
]

# Common Training (All Departments)
common_training = [
    'Gautam Solar Values, Vision & Mission',
    '5S Awareness',
    'Safety Awareness',
    'PPEs Types & Usage',
    'Risk Management & Incident Investigation',
    'GSPL HR Policies',
    'Motivational Training',
    'Soft Skill Development',
    'Legal Compliance Training',
]

# Insert all topics
topic_count = 0

# Production Process topics
for topic in production_process:
    cursor.execute("""
        INSERT INTO training_topic (name, category_id, is_common) 
        VALUES (%s, %s, FALSE)
    """, (topic, cat_map['PROC']))
    topic_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO department_topic_mapping (department_id, topic_id) 
        VALUES (%s, %s)
    """, (dept_map['PROD'], topic_id))
    topic_count += 1

# Production Awareness topics
for topic in production_awareness:
    cursor.execute("""
        INSERT INTO training_topic (name, category_id, is_common) 
        VALUES (%s, %s, FALSE)
    """, (topic, cat_map['AWARE']))
    topic_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO department_topic_mapping (department_id, topic_id) 
        VALUES (%s, %s)
    """, (dept_map['PROD'], topic_id))
    topic_count += 1

# Quality Inspection topics
for topic in quality_inspection:
    cursor.execute("""
        INSERT INTO training_topic (name, category_id, is_common) 
        VALUES (%s, %s, FALSE)
    """, (topic, cat_map['QC']))
    topic_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO department_topic_mapping (department_id, topic_id) 
        VALUES (%s, %s)
    """, (dept_map['QA'], topic_id))
    topic_count += 1

# Quality Systems topics
for topic in quality_systems:
    cursor.execute("""
        INSERT INTO training_topic (name, category_id, is_common) 
        VALUES (%s, %s, FALSE)
    """, (topic, cat_map['QS']))
    topic_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO department_topic_mapping (department_id, topic_id) 
        VALUES (%s, %s)
    """, (dept_map['QA'], topic_id))
    topic_count += 1

# Maintenance Technical topics
for topic in maintenance_technical:
    cursor.execute("""
        INSERT INTO training_topic (name, category_id, is_common) 
        VALUES (%s, %s, FALSE)
    """, (topic, cat_map['PROC']))
    topic_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO department_topic_mapping (department_id, topic_id) 
        VALUES (%s, %s)
    """, (dept_map['MAINT'], topic_id))
    topic_count += 1

# Maintenance Safety topics
for topic in maintenance_safety:
    cursor.execute("""
        INSERT INTO training_topic (name, category_id, is_common) 
        VALUES (%s, %s, FALSE)
    """, (topic, cat_map['SAFETY']))
    topic_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO department_topic_mapping (department_id, topic_id) 
        VALUES (%s, %s)
    """, (dept_map['MAINT'], topic_id))
    topic_count += 1

# Common Training (All Departments)
for topic in common_training:
    cursor.execute("""
        INSERT INTO training_topic (name, category_id, is_common) 
        VALUES (%s, %s, TRUE)
    """, (topic, cat_map['COMMON']))
    topic_id = cursor.lastrowid
    # Map to all departments
    for dept_code in ['PROD', 'QA', 'MAINT']:
        cursor.execute("""
            INSERT INTO department_topic_mapping (department_id, topic_id) 
            VALUES (%s, %s)
        """, (dept_map[dept_code], topic_id))
    topic_count += 1

conn.commit()
print(f"   ✅ Added {topic_count} training topics with department mappings")

# ============================================
# ADD SAMPLE EMPLOYEES
# ============================================
print("\n4️⃣ Adding Sample Employees...")

employees = [
    ('EMP001', 'Rajesh Kumar', dept_map['PROD'], 'Operator'),
    ('EMP002', 'Suresh Singh', dept_map['PROD'], 'Technician'),
    ('EMP003', 'Amit Sharma', dept_map['QA'], 'QC Inspector'),
    ('EMP004', 'Vikram Yadav', dept_map['QA'], 'IPQC Executive'),
    ('EMP005', 'Deepak Verma', dept_map['MAINT'], 'Maintenance Technician'),
    ('EMP006', 'Rahul Gupta', dept_map['MAINT'], 'Electrician'),
    ('EMP007', 'Sanjay Patel', dept_map['PROD'], 'Line Incharge'),
    ('EMP008', 'Mohan Das', dept_map['QA'], 'FQC Inspector'),
]

for emp_id, name, dept_id, designation in employees:
    cursor.execute("""
        INSERT INTO employee_new (emp_id, name, department_id, designation) 
        VALUES (%s, %s, %s, %s)
    """, (emp_id, name, dept_id, designation))

conn.commit()
print(f"   ✅ Added {len(employees)} sample employees")

# ============================================
# SUMMARY
# ============================================
print("\n" + "="*60)
print("📊 SCHEMA SUMMARY")
print("="*60)

cursor.execute("SELECT COUNT(*) FROM department_new")
print(f"   Departments: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM training_category")
print(f"   Training Categories: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM training_topic")
print(f"   Training Topics: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM department_topic_mapping")
print(f"   Department-Topic Mappings: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM employee_new")
print(f"   Employees: {cursor.fetchone()[0]}")

print("\n" + "="*60)
print("✅ DATABASE SETUP COMPLETE!")
print("="*60)

conn.close()
