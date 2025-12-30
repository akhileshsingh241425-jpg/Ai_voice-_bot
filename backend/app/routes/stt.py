
from flask import Blueprint, request, jsonify
from ai.stt.whisper_stt import WhisperSTT
import os

stt_bp = Blueprint('stt', __name__)

# Lazy loading - initialize only when first request comes
whisper_stt = None

def get_whisper_stt(model_size=None):
    """
    Return a singleton WhisperSTT instance. If model_size is provided it will
    be used for loading; otherwise the WHISPER_MODEL_SIZE env var or 'small'
    will be used. 'small' is a good balance of speed and accuracy for Hindi.
    """
    global whisper_stt
    if whisper_stt is None:
        import os
        # Use 'small' by default - good balance of speed and accuracy for Hindi
        # medium/large are more accurate but slower
        chosen = model_size or os.environ.get('WHISPER_MODEL_SIZE', 'small')
        print(f"Loading Whisper model (this may take a moment)... model_size={chosen}")
        whisper_stt = WhisperSTT(model_size=chosen)
        print("Whisper model loaded successfully!")
    return whisper_stt

@stt_bp.route('/stt', methods=['POST'])
def speech_to_text():
    print("[STT] Received STT request")
    if 'audio' not in request.files:
        print("[STT] Error: No audio file in request")
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    print(f"[STT] Audio file received: {audio_file.filename}, size: {audio_file.content_length}")
    
    # Get language from form data (default to Hindi)
    language = request.form.get('language', 'hi')
    print(f"[STT] Language: {language}")
    
    temp_path = os.path.join('temp_audio', audio_file.filename)
    os.makedirs('temp_audio', exist_ok=True)
    audio_file.save(temp_path)
    
    # Check file size
    file_size = os.path.getsize(temp_path)
    print(f"[STT] Saved audio file size: {file_size} bytes")
    
    try:
        print("[STT] Starting transcription with faster-whisper...")
        import time
        start_time = time.time()
        
        stt_model = get_whisper_stt()
        text = stt_model.transcribe(temp_path, language=language)
        
        elapsed = time.time() - start_time
        print(f"[STT] Transcription completed in {elapsed:.2f} seconds")
        print(f"[STT] Result: '{text}'")
    except Exception as e:
        print(f"[STT] Error during transcription: {str(e)}")
        import traceback
        traceback.print_exc()
        os.remove(temp_path)
        return jsonify({'error': str(e)}), 500
    
    os.remove(temp_path)
    print("[STT] Request completed successfully")
    return jsonify({'text': text, 'language': language})
