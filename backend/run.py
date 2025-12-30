import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Disable the auto reloader/watchdog to avoid repeated restarts while
    # heavy ML libraries (transformers/whisper/torch) touch site-packages.
    # This prevents transient "Network error" on the frontend during model
    # initialization. If you still want the reloader, set FLASK_USE_RELOADER=1
    use_reloader = False
    if os.environ.get('FLASK_USE_RELOADER') == '1':
        use_reloader = True
    app.run(debug=True, use_reloader=use_reloader)
