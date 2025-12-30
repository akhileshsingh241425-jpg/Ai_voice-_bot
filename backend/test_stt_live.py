"""
STT Live Test Script
Records audio from microphone and tests Whisper transcription
"""
import os
import sys
import wave
import tempfile

# Check if pyaudio is available
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    print("PyAudio not installed. Installing...")
    os.system(f'{sys.executable} -m pip install pyaudio')
    try:
        import pyaudio
        HAS_PYAUDIO = True
    except:
        print("Could not install PyAudio. Using file-based test instead.")

def record_audio(duration=5, filename="test_recording.wav"):
    """Record audio from microphone"""
    if not HAS_PYAUDIO:
        return None
    
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    
    print(f"\n🎤 Recording for {duration} seconds... SPEAK NOW!")
    print("=" * 40)
    
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    frames = []
    for i in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)
        # Show progress
        progress = int((i / (RATE / CHUNK * duration)) * 40)
        print(f"\r[{'=' * progress}{' ' * (40-progress)}] {int((i / (RATE / CHUNK * duration)) * 100)}%", end='')
    
    print("\n✅ Recording complete!")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save to file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return filename

def test_whisper(audio_file, model_size='small'):
    """Test Whisper transcription"""
    print(f"\n🔄 Loading Whisper model ({model_size})...")
    
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from ai.stt.whisper_stt import WhisperSTT
    
    stt = WhisperSTT(model_size=model_size)
    
    print(f"\n🎯 Transcribing audio file: {audio_file}")
    print("=" * 40)
    
    # Test with auto-detect
    print("\n📝 Test 1: Auto-detect language")
    result_auto = stt.transcribe(audio_file, language=None)
    print(f"Result: {result_auto}")
    
    # Test with Hindi
    print("\n📝 Test 2: Force Hindi (hi)")
    result_hi = stt.transcribe(audio_file, language='hi')
    print(f"Result: {result_hi}")
    
    # Test with English
    print("\n📝 Test 3: Force English (en)")
    result_en = stt.transcribe(audio_file, language='en')
    print(f"Result: {result_en}")
    
    return result_auto, result_hi, result_en

def main():
    print("=" * 50)
    print("🎤 STT (Speech-to-Text) Test Tool")
    print("=" * 50)
    
    # Choose test mode
    print("\nSelect test mode:")
    print("1. Record from microphone (live test)")
    print("2. Use existing audio file")
    print("3. Quick test with sample text generation")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    audio_file = None
    
    if choice == '1':
        if not HAS_PYAUDIO:
            print("❌ PyAudio not available for recording")
            return
        
        duration = input("Recording duration in seconds (default 5): ").strip()
        duration = int(duration) if duration else 5
        
        audio_file = record_audio(duration)
        
    elif choice == '2':
        audio_file = input("Enter path to audio file: ").strip()
        if not os.path.exists(audio_file):
            print(f"❌ File not found: {audio_file}")
            return
    
    elif choice == '3':
        # Create a simple test
        print("\n🔄 Running quick Whisper test...")
        import whisper
        model = whisper.load_model("small")
        print("✅ Whisper model loaded successfully!")
        print(f"   Model type: {type(model)}")
        print(f"   Available models: tiny, base, small, medium, large")
        return
    
    else:
        print("Invalid choice")
        return
    
    if audio_file:
        # Select model size
        print("\nSelect Whisper model:")
        print("1. tiny (fastest, least accurate)")
        print("2. base (fast, low accuracy)")
        print("3. small (balanced) [RECOMMENDED]")
        print("4. medium (slower, better accuracy)")
        print("5. large (slowest, best accuracy)")
        
        model_choice = input("Enter choice (1-5, default 3): ").strip()
        model_map = {'1': 'tiny', '2': 'base', '3': 'small', '4': 'medium', '5': 'large'}
        model_size = model_map.get(model_choice, 'small')
        
        results = test_whisper(audio_file, model_size)
        
        print("\n" + "=" * 50)
        print("📊 RESULTS SUMMARY")
        print("=" * 50)
        print(f"Auto-detect: {results[0]}")
        print(f"Hindi mode:  {results[1]}")
        print(f"English mode: {results[2]}")
        print("=" * 50)
        
        # Cleanup
        if choice == '1' and os.path.exists(audio_file):
            cleanup = input("\nDelete test recording? (y/n): ").strip().lower()
            if cleanup == 'y':
                os.remove(audio_file)
                print("✅ Recording deleted")

if __name__ == "__main__":
    main()
