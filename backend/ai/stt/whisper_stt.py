"""
Whisper STT Module - Using faster-whisper for 4x speed improvement
"""
import warnings
warnings.filterwarnings("ignore")

# Try faster-whisper first, fall back to regular whisper
try:
    from faster_whisper import WhisperModel
    USING_FASTER_WHISPER = True
    print("[WhisperSTT] Using faster-whisper (4x faster)")
except ImportError:
    import whisper
    USING_FASTER_WHISPER = False
    print("[WhisperSTT] Using standard whisper")


class WhisperSTT:
    def __init__(self, model_size='small'):
        """
        Initialize Whisper model.
        Models: tiny, base, small, medium, large
        For Hindi: 'small' is good balance of speed and accuracy
        """
        print(f"[WhisperSTT] Loading model: {model_size}")
        
        if USING_FASTER_WHISPER:
            # faster-whisper uses CPU by default, can use CUDA if available
            # compute_type: int8 is fastest, float16 for GPU, float32 for accuracy
            self.model = WhisperModel(
                model_size, 
                device="cpu",  # Change to "cuda" if you have NVIDIA GPU
                compute_type="int8"  # Fastest on CPU
            )
        else:
            self.model = whisper.load_model(model_size)
        
        print(f"[WhisperSTT] Model loaded successfully")

    def transcribe(self, file_path, language=None):
        """
        Transcribe audio file to text.
        If language is None, auto-detect.
        """
        print(f"[WhisperSTT] Transcribing: {file_path}, language: {language}")
        
        if USING_FASTER_WHISPER:
            # faster-whisper returns segments generator
            segments, info = self.model.transcribe(
                file_path,
                language=language,
                beam_size=5,
                best_of=5,
                temperature=0,
                condition_on_previous_text=False,
                vad_filter=True,  # Voice Activity Detection - removes silence
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Collect all segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)
            
            text = " ".join(text_parts).strip()
            detected_lang = info.language
            
            print(f"[WhisperSTT] Detected language: {detected_lang}")
            print(f"[WhisperSTT] Transcription: '{text}'")
            return text
        else:
            # Standard whisper
            result = self.model.transcribe(
                file_path,
                language=language,
                task='transcribe',
                verbose=False,
                temperature=0,
                beam_size=5,
                best_of=5,
                condition_on_previous_text=False
            )
            
            text = result['text'].strip()
            detected_lang = result.get('language', 'unknown')
            
            print(f"[WhisperSTT] Detected language: {detected_lang}")
            print(f"[WhisperSTT] Transcription: '{text}'")
            return text
