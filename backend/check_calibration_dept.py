import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='ai_voice_bot_new',
    port=3306
)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# Check Calibration topic department
print("=" * 50)
print("CALIBRATION TOPIC DEPARTMENT MAPPING:")
print("=" * 50)
cursor.execute("""
    SELECT t.id, t.name as topic, d.name as dept 
    FROM training_topic t 
    JOIN department_topic_mapping dtm ON t.id = dtm.topic_id 
    JOIN department_new d ON d.id = dtm.department_id 
    WHERE t.name LIKE '%Calibration%'
""")
rows = cursor.fetchall()
for r in rows:
    print(f"Topic: {r['topic']}")
    print(f"Department: {r['dept']}")
    print(f"Topic ID: {r['id']}")

# Check Q&A count
print("\n" + "=" * 50)
print("CALIBRATION QUESTIONS COUNT:")
print("=" * 50)
cursor.execute("""
    SELECT COUNT(*) as cnt FROM qa_bank_new q 
    JOIN training_topic t ON q.topic_id = t.id 
    WHERE t.name LIKE '%Calibration%' AND q.is_active = TRUE
""")
cnt = cursor.fetchone()['cnt']
print(f"Total Questions: {cnt}")

# Show all departments
print("\n" + "=" * 50)
print("ALL DEPARTMENTS:")
print("=" * 50)
cursor.execute("SELECT * FROM department_new")
for d in cursor.fetchall():
    print(f"  {d['id']}: {d['name']}")

conn.close()
