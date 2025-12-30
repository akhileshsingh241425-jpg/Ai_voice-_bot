import whisper
import soundfile as sf
import os

class WhisperSTT:
    def __init__(self, model_size="base"):
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path, language="hi"):
        # Whisper expects audio in wav format
        data, samplerate = sf.read(audio_path)
        temp_wav = audio_path + ".wav"
        sf.write(temp_wav, data, samplerate)
        result = self.model.transcribe(temp_wav, language=language)
        os.remove(temp_wav)
        return result["text"]
