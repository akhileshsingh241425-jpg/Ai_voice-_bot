from flask import Flask
from flask_cors import CORS
from app.models.models import db
import os

# Core Routes - Only what's being used
from app.routes.main import main_bp
from app.routes.stt import stt_bp
from app.routes.eval import eval_bp
from app.routes.llm import llm_bp
from app.routes.training import training_bp
from app.routes.qa_bank_new import qa_bank_new_bp
from app.routes.viva_session import viva_session_bp
from app.routes.chat_viva import chat_viva_bp
from app.routes.viva_records import viva_records_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Get allowed origins from environment or use defaults
    allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
    
    # Enable CORS for frontend integration
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Register blueprints - Core only
    app.register_blueprint(main_bp)      # Health check, basic routes
    app.register_blueprint(stt_bp)       # Speech-to-Text (Whisper)
    app.register_blueprint(eval_bp)      # Basic evaluation
    app.register_blueprint(llm_bp)       # LLM evaluation (Ollama)
    app.register_blueprint(training_bp)  # Departments, Topics, Employees
    app.register_blueprint(qa_bank_new_bp)  # Q&A Bank per topic
    app.register_blueprint(viva_session_bp)  # Viva sessions
    app.register_blueprint(chat_viva_bp)  # Conversational Voice Interview
    app.register_blueprint(viva_records_bp)  # Viva records with video

    db.init_app(app)
    
    # Preload Whisper STT model in background
    try:
        from app.routes.stt import get_whisper_stt
        import threading

        def _background_preload():
            try:
                import os
                model_size = os.environ.get('WHISPER_MODEL_SIZE') or 'small'
                print(f"Background: starting Whisper preload (model={model_size})...")
                get_whisper_stt(model_size=model_size)
                print("Background: Whisper preload complete")
            except Exception as e:
                print(f"Background: Whisper preload failed: {e}")

        t = threading.Thread(target=_background_preload, daemon=True)
        t.start()
    except Exception as e:
        print(f"Warning: could not spawn background preload thread: {e}")

    return app
