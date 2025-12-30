"""
Create QA Bank and Viva Result tables
"""
import pymysql

connection = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='ai_voice_bot_new',
    port=3306
)

try:
    with connection.cursor() as cursor:
        # Create QA Bank table
        print("Creating QA Bank table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_bank (
                id INT AUTO_INCREMENT PRIMARY KEY,
                machine_id INT NOT NULL,
                question TEXT NOT NULL,
                expected_answer TEXT NOT NULL,
                level INT DEFAULT 1,
                category VARCHAR(100) DEFAULT 'General',
                keywords VARCHAR(500) DEFAULT '',
                language VARCHAR(20) DEFAULT 'Hindi',
                is_active BOOLEAN DEFAULT TRUE,
                times_asked INT DEFAULT 0,
                times_correct INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machine(id)
            )
        """)
        print("✅ QA Bank table created!")
        
        # Create Viva Result table
        print("Creating Viva Result table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS viva_result (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(50) NOT NULL UNIQUE,
                machine_id INT NOT NULL,
                user_name VARCHAR(100) DEFAULT 'Anonymous',
                total_questions INT DEFAULT 0,
                correct_answers INT DEFAULT 0,
                partial_answers INT DEFAULT 0,
                wrong_answers INT DEFAULT 0,
                total_score FLOAT DEFAULT 0.0,
                detailed_results TEXT,
                level1_score FLOAT DEFAULT 0.0,
                level2_score FLOAT DEFAULT 0.0,
                level3_score FLOAT DEFAULT 0.0,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME,
                duration_seconds INT DEFAULT 0,
                status VARCHAR(20) DEFAULT 'in_progress',
                FOREIGN KEY (machine_id) REFERENCES machine(id)
            )
        """)
        print("✅ Viva Result table created!")
        
        connection.commit()
        print("\n✅ All tables ready!")
        
finally:
    connection.close()
