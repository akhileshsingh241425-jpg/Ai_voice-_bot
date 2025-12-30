"""
Fix Department-Topic Mapping as per User's Original List
"""
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root', 
    password='root',
    database='ai_voice_bot_new',
    port=3306
)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# First, clear existing data (in correct order due to foreign keys)
print("Clearing existing data...")
cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
cursor.execute("DELETE FROM viva_result_new")
cursor.execute("DELETE FROM viva_session_new")
cursor.execute("DELETE FROM training_record")
cursor.execute("DELETE FROM qa_bank_new")
cursor.execute("DELETE FROM department_topic_mapping")
cursor.execute("DELETE FROM training_topic")
cursor.execute("DELETE FROM training_category")
cursor.execute("DELETE FROM employee_new")
cursor.execute("DELETE FROM department_new")
cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
conn.commit()

# ==================== DEPARTMENTS ====================
print("\nCreating Departments...")
departments = [
    (1, 'Production', 'PROD'),
    (2, 'Quality (IQC/IPQC/FQC)', 'QC'),
    (3, 'Maintenance & Utility', 'MAINT')
]
for d in departments:
    cursor.execute("INSERT INTO department_new (id, name, code) VALUES (%s, %s, %s)", d)
print(f"✅ {len(departments)} Departments created")

# ==================== CATEGORIES ====================
print("\nCreating Categories...")
categories = [
    (1, 'Process/Technical Training', 'PROCESS'),
    (2, 'Awareness/System Training', 'AWARENESS'),
    (3, 'Quality & Inspection Training', 'QUALITY'),
    (4, 'Quality Systems Training', 'QMS'),
    (5, 'Safety Specific Training', 'SAFETY'),
    (6, 'Common Training (★)', 'COMMON')
]
for c in categories:
    cursor.execute("INSERT INTO training_category (id, name, code) VALUES (%s, %s, %s)", c)
print(f"✅ {len(categories)} Categories created")

conn.commit()

# ==================== TRAINING TOPICS ====================
# Format: (id, name, category_id, is_common, [department_ids])

topics = []
topic_id = 1

# ========== PRODUCTION DEPARTMENT TOPICS ==========
print("\n📦 Creating Production Topics...")

# Process/Technical Training - Production
prod_process = [
    "Solar Panel Manufacturing Process (Cutting, Stringing, Layup, Lamination, Framing, Testing)",
    "Machine Operation SOP (Standard Operating Procedures)",
    "Product Specifications & Quality Standards",
    "Process Control Parameters",
    "Defect Identification & Prevention",
    "Material Handling Procedures",
    "Work Instructions Compliance"
]
for name in prod_process:
    topics.append((topic_id, name, 1, False, [1]))  # Category 1, Dept 1 (Production)
    topic_id += 1

# Awareness/System Training - Production
prod_awareness = [
    "5S Implementation",
    "Lean Manufacturing Basics",
    "Kaizen Participation"
]
for name in prod_awareness:
    topics.append((topic_id, name, 2, False, [1]))
    topic_id += 1

# Quality & Inspection - Production
prod_quality = [
    "In-process Inspection Points"
]
for name in prod_quality:
    topics.append((topic_id, name, 3, False, [1]))
    topic_id += 1

# ========== QUALITY DEPARTMENT TOPICS (IQC/IPQC/FQC) ==========
print("🔍 Creating Quality Topics...")

# Quality & Inspection Training - Quality
qc_quality = [
    "Incoming Quality Inspection (IQC)",
    "In-Process Quality Control (IPQC)",
    "Final Quality Control (FQC)",
    "Sampling Techniques (AQL)",
    "Testing Equipment Operation (EL Tester, Flash Tester, Hi-Pot Tester)",
    "Non-Conformance Handling",
    "Calibration Awareness"
]
for name in qc_quality:
    topics.append((topic_id, name, 3, False, [2]))  # Category 3, Dept 2 (Quality)
    topic_id += 1

# Quality Systems Training - Quality
qc_systems = [
    "ISO 9001 Awareness",
    "Document Control System",
    "Internal Audit Basics"
]
for name in qc_systems:
    topics.append((topic_id, name, 4, False, [2]))
    topic_id += 1

# ========== MAINTENANCE & UTILITY DEPARTMENT TOPICS ==========
print("🔧 Creating Maintenance Topics...")

# Process/Technical Training - Maintenance
maint_process = [
    "Equipment Maintenance SOPs",
    "Preventive Maintenance Schedules",
    "Breakdown Troubleshooting",
    "Spare Parts Management",
    "Electrical Safety & Maintenance",
    "Pneumatic & Hydraulic Systems",
    "PLC Basics (if applicable)"
]
for name in maint_process:
    topics.append((topic_id, name, 1, False, [3]))  # Category 1, Dept 3 (Maintenance)
    topic_id += 1

# Safety Specific Training - Maintenance
maint_safety = [
    "Lockout/Tagout (LOTO) Procedures",
    "Working at Heights",
    "Confined Space Entry",
    "Hot Work Permit System"
]
for name in maint_safety:
    topics.append((topic_id, name, 5, False, [3]))
    topic_id += 1

# Awareness/System Training - Maintenance
maint_awareness = [
    "Energy Conservation",
    "Utility Systems (Compressed Air, Nitrogen, Cooling Water)"
]
for name in maint_awareness:
    topics.append((topic_id, name, 2, False, [3]))
    topic_id += 1

# ========== COMMON TRAINING (★ All Departments) ==========
print("⭐ Creating Common Topics (All Departments)...")

common_topics = [
    "EHS (Environment, Health & Safety) Induction",
    "Fire Safety & Emergency Evacuation",
    "First Aid Basics",
    "PPE Usage",
    "Waste Segregation & Environmental Awareness",
    "Anti-Harassment Policy (POSH)",
    "Company Policies & Code of Conduct",
    "Workplace Ethics",
    "Basic Computer Skills (if applicable)"
]
for name in common_topics:
    topics.append((topic_id, name, 6, True, [1, 2, 3]))  # All 3 departments
    topic_id += 1

# Insert all topics
print("\nInserting topics...")
for t in topics:
    tid, name, cat_id, is_common, dept_ids = t
    cursor.execute(
        "INSERT INTO training_topic (id, name, category_id, is_common) VALUES (%s, %s, %s, %s)",
        (tid, name, cat_id, is_common)
    )
    # Add department mappings
    for dept_id in dept_ids:
        cursor.execute(
            "INSERT INTO department_topic_mapping (department_id, topic_id) VALUES (%s, %s)",
            (dept_id, tid)
        )

conn.commit()

# ==================== ONLY ONE TEST EMPLOYEE ====================
print("\n👷 Creating Test Employee...")
employees = [
    ('TEST001', 'Test Employee', 1, 'Test'),  # Only 1 test employee
]
for emp in employees:
    cursor.execute(
        "INSERT INTO employee_new (emp_id, name, department_id, designation) VALUES (%s, %s, %s, %s)",
        emp
    )
print(f"✅ {len(employees)} Test Employee created")

conn.commit()

# ==================== SUMMARY ====================
print("\n" + "="*60)
print("✅ DATABASE FIXED SUCCESSFULLY!")
print("="*60)

# Count by department
cursor.execute("""
    SELECT d.name, COUNT(*) as cnt 
    FROM department_topic_mapping dtm 
    JOIN department_new d ON dtm.department_id = d.id 
    GROUP BY d.id, d.name
""")
dept_counts = cursor.fetchall()
print("\n📊 Topics per Department:")
for dc in dept_counts:
    print(f"   {dc['name']}: {dc['cnt']} topics")

# Count by category
cursor.execute("""
    SELECT c.name, COUNT(*) as cnt 
    FROM training_topic t 
    JOIN training_category c ON t.category_id = c.id 
    GROUP BY c.id, c.name
""")
cat_counts = cursor.fetchall()
print("\n📚 Topics per Category:")
for cc in cat_counts:
    print(f"   {cc['name']}: {cc['cnt']} topics")

# Total
cursor.execute("SELECT COUNT(*) as cnt FROM training_topic")
total = cursor.fetchone()['cnt']
print(f"\n📌 Total Training Topics: {total}")

conn.close()
print("\n✅ Done! Restart frontend to see changes.")
