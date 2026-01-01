import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key_change_in_production')
    
    # Database Configuration from Environment Variables
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'ai_voice_bot_new')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    
    # Build SQLAlchemy URI from environment variables
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask Environment
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # Upload Configuration
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'viva_videos')
