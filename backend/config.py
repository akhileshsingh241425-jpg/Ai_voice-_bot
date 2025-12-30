import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    # Example MySQL URI: 'mysql+pymysql://username:password@localhost/dbname'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost:3306/ai_voice_bot_new'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Add other config variables as needed
