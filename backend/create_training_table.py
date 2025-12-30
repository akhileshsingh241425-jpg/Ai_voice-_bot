"""
Create MachineTraining table if it doesn't exist
"""
import pymysql

# Database connection
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='ai_voice_bot_new',
    port=3306
)

try:
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'machine_training'")
        result = cursor.fetchone()
        
        if result:
            print("✅ machine_training table already exists")
        else:
            print("Creating machine_training table...")
            
            # Create the table
            create_sql = """
            CREATE TABLE machine_training (
                id INT AUTO_INCREMENT PRIMARY KEY,
                machine_id INT NOT NULL,
                good_examples TEXT,
                bad_examples TEXT,
                instructions TEXT,
                question_style VARCHAR(50) DEFAULT 'technical',
                preferred_language VARCHAR(20) DEFAULT 'Hindi',
                difficulty_focus VARCHAR(20) DEFAULT 'mixed',
                total_corrections INT DEFAULT 0,
                last_trained_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machine(id)
            )
            """
            cursor.execute(create_sql)
            connection.commit()
            print("✅ machine_training table created successfully!")
        
        # Show table structure
        cursor.execute("DESCRIBE machine_training")
        columns = cursor.fetchall()
        print("\nTable structure:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
            
finally:
    connection.close()
