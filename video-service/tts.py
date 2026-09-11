import asyncio
import wave
from pathlib import Path


def _write_silent_wav(text, output_path):
    """Last-resort audio so video creation still works without espeak."""
    duration = max(2.0, min(120.0, len(text or "") / 12.0))
    sample_rate = 22050
    frames = int(duration * sample_rate)
    silence = b"\x00\x00" * frames

    with wave.open(str(output_path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(silence)

def _generate(text, output_path, voice_hint=None, rate=165):
    output = Path(output_path)
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        if voice_hint:
            hint = voice_hint.lower()
            for voice in engine.getProperty("voices"):
                blob = f"{voice.id} {voice.name}".lower()
                if hint in blob:
                    engine.setProperty("voice", voice.id)
                    break
        engine.save_to_file(text, str(output))
        engine.runAndWait()
        engine.stop()

        if not output.exists() or output.stat().st_size == 0:
            raise RuntimeError("The text-to-speech engine did not create audio.")
    except Exception:
        _write_silent_wav(text, output)

async def generate_audio(text, output_path, voice="default"):
    await asyncio.to_thread(_generate, text, output_path, voice)
