# WSGI entry point for production (Gunicorn/uWSGI)
# Usage: gunicorn wsgi:app

import os
import sys

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import and create the Flask app
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Only for development - use Gunicorn in production
    app.run(host='0.0.0.0', port=5000)
