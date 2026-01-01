"""
Production Server - Frontend + Backend on single port (9000)
Serves React static files + Flask API together
"""

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

# Register all API blueprints
app.register_blueprint(main_bp)
app.register_blueprint(stt_bp, url_prefix='/stt')
app.register_blueprint(eval_bp, url_prefix='/eval')
app.register_blueprint(llm_bp, url_prefix='/llm')
app.register_blueprint(training_bp, url_prefix='/training')
app.register_blueprint(qa_bank_new_bp, url_prefix='/qa')
app.register_blueprint(viva_session_bp, url_prefix='/viva')
app.register_blueprint(chat_viva_bp, url_prefix='/chat-viva')
app.register_blueprint(viva_records_bp, url_prefix='/viva-records')

# Serve React App - catch all routes
@app.route('/')
def serve_react():
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
