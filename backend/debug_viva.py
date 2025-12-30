import pymysql
import requests

# Check database
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='ai_voice_bot_new',
    port=3306
)
cursor = conn.cursor(pymysql.cursors.DictCursor)

print("=" * 50)
print("EMPLOYEES IN DATABASE:")
print("=" * 50)
cursor.execute("""
    SELECT e.id, e.emp_id, e.name, e.department_id, d.name as dept_name 
    FROM employee_new e 
    JOIN department_new d ON e.department_id = d.id
""")
for r in cursor.fetchall():
    print(f"  ID: {r['id']} | {r['emp_id']} | {r['name']} | {r['dept_name']}")

print("\n" + "=" * 50)
print("TOPICS WITH QUESTIONS:")
print("=" * 50)
cursor.execute("""
    SELECT t.id, t.name, COUNT(q.id) as cnt 
    FROM training_topic t 
    LEFT JOIN qa_bank_new q ON q.topic_id = t.id AND q.is_active = TRUE 
    GROUP BY t.id 
    HAVING cnt >= 5
""")
for r in cursor.fetchall():
    print(f"  ID: {r['id']} | {r['name']} ({r['cnt']} Q)")

conn.close()

# Check APIs
print("\n" + "=" * 50)
print("API CHECKS:")
print("=" * 50)
try:
    r = requests.get('http://localhost:5000/employees')
    data = r.json()
    print(f"Employees API: {len(data.get('employees', []))} employees")
except Exception as e:
    print(f"Employees API Error: {e}")

try:
    r = requests.get('http://localhost:5000/qa/topics-stats')
    data = r.json()
    topics = [t for t in data.get('topics', []) if t.get('total_questions', 0) >= 5]
    print(f"Topics API: {len(topics)} topics with 5+ questions")
    for t in topics[:5]:
        print(f"  - {t['name']}: {t['total_questions']} Q")
except Exception as e:
    print(f"Topics API Error: {e}")
