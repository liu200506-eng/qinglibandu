from utils.tts_client import synthesize_speech
from utils.stt_client import transcribe_audio


def text_to_speech(text: str, voice: str = "default") -> bytes | None:
    return synthesize_speech(text, voice)


def speech_to_text(audio_data: bytes) -> str | None:
    return transcribe_audio(audio_data)


def voice_chat(student_id: str, audio_data: bytes) -> dict:
    text = transcribe_audio(audio_data)
    if not text:
        return {"status": "error", "message": "语音识别失败"}

    from services.tutoring_service import chat
    chat_result = chat(student_id, text)

    if chat_result["response"]:
        synthesize_speech(chat_result["response"])

    return {
        "status": "success",
        "recognized_text": text,
        "response": chat_result["response"],
        "emotional_feedback": chat_result.get("emotional_feedback", "")
    }