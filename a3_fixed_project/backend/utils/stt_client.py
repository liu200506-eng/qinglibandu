import os
import tempfile

_recognizer = None


def _ensure_recognizer():
    global _recognizer
    if _recognizer is None:
        try:
            import speech_recognition as sr
            _recognizer = sr.Recognizer()
        except ImportError:
            print("[ASR] speech_recognition not installed")
            return None
    return _recognizer


def transcribe_audio(audio_path: str) -> str | None:
    try:
        import speech_recognition as sr
    except ImportError:
        print("[ASR] speech_recognition not installed")
        return None

    recognizer = _ensure_recognizer()
    if not recognizer:
        return None

    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)

        try:
            return recognizer.recognize_google(audio, language='zh-CN')
        except sr.UnknownValueError:
            print("[ASR] Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"[ASR] Could not request results from Google Speech Recognition service; {e}")
            return None

    except Exception as e:
        print(f"[ASR] Error: {e}")
        return None


def transcribe_audio_bytes(audio_bytes: bytes) -> str | None:
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    try:
        return transcribe_audio(temp_path)
    finally:
        os.unlink(temp_path)


def is_asr_available() -> bool:
    try:
        import speech_recognition
        return True
    except ImportError:
        return False
