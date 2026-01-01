"""
Central Database Configuration
All routes should import get_db() from here
"""
import os
import pymysql

def get_db():
    """Get database connection using environment variables"""
    return pymysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', 'root'),
        database=os.environ.get('MYSQL_DATABASE', 'ai_voice_bot_new'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )
