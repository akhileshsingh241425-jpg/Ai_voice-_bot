import sounddevice as sd
import soundfile as sf

# Settings
filename = "test_hindi.wav"  # Output file name
samplerate = 16000  # Sample rate (Hz)
duration = 20       # Duration in seconds
channels = 1        # Mono

print(f"Recording for {duration} seconds. Please speak Hindi...")
recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=channels, dtype='int16')
sd.wait()  # Wait until recording is finished
sf.write(filename, recording, samplerate)
print(f"Recording saved as {filename}")
