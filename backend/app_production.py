"""
Production Server - Frontend + Backend on single port (9000)
Serves React static files + Flask API together
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os

# Import all blueprints
from app.routes.main import main_bp
from app.routes.stt import stt_bp
from app.routes.eval import eval_bp
from app.routes.llm import llm_bp
from app.routes.training import training_bp
from app.routes.qa_bank_new import qa_bank_new_bp
from app.routes.viva_session import viva_session_bp
from app.routes.chat_viva import chat_viva_bp
from app.routes.viva_records import viva_records_bp

# Create Flask app
app = Flask(__name__, static_folder='../frontend_build', static_url_path='')
CORS(app)

# Register all API blueprints - NO PREFIX (routes already have their paths)
app.register_blueprint(main_bp, url_prefix='/api')  # main_bp has "/" route
app.register_blueprint(stt_bp)       # routes: /stt/*
app.register_blueprint(eval_bp)      # routes: /eval/*
app.register_blueprint(llm_bp)       # routes: /llm/*
app.register_blueprint(training_bp)  # routes: /training/*
app.register_blueprint(qa_bank_new_bp)  # routes: /qa/*
app.register_blueprint(viva_session_bp) # routes: /viva/*
app.register_blueprint(chat_viva_bp)    # routes: /chat-viva/*
app.register_blueprint(viva_records_bp) # routes: /viva-records/*

# Serve React App - this MUST come after blueprint registration
@app.route('/')
def serve_react():
    """Serve React frontend"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # If file exists, serve it
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    # Otherwise serve index.html (for React Router)
    return send_from_directory(app.static_folder, 'index.html')

# Health check
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': 'AI Training Voice Bot Running'})

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 9000))
    print(f"🚀 Starting AI Training Voice Bot on port {PORT}")
    print(f"📁 Serving frontend from: {app.static_folder}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
