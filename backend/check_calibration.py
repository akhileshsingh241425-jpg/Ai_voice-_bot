import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='ai_voice_bot_new',
    port=3306
)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# Check Calibration topic questions
cursor.execute("""
    SELECT t.name as topic, COUNT(q.id) as cnt 
    FROM training_topic t
    LEFT JOIN qa_bank_new q ON q.topic_id = t.id AND q.is_active = TRUE
    WHERE t.name LIKE '%Calibration%'
    GROUP BY t.id, t.name
""")
rows = cursor.fetchall()
print("=" * 50)
print("CALIBRATION TOPIC STATUS:")
print("=" * 50)
for r in rows:
    print(f"Topic: {r['topic']}")
    print(f"Questions: {r['cnt']}")

# Get actual questions
cursor.execute("""
    SELECT q.question, q.expected_answer, q.language, q.level
    FROM qa_bank_new q 
    JOIN training_topic t ON q.topic_id = t.id 
    WHERE t.name LIKE '%Calibration%' AND q.is_active = TRUE
    LIMIT 20
""")
qs = cursor.fetchall()

if qs:
    print(f"\n✅ Found {len(qs)} questions:")
    for i, q in enumerate(qs, 1):
        print(f"\n{i}. [{q['language']}] Level {q['level']}")
        print(f"   Q: {q['question'][:80]}")
        print(f"   A: {q['expected_answer'][:80]}")
else:
    print("\n❌ No Calibration questions found in database!")
    print("Please upload Excel file again.")

conn.close()
