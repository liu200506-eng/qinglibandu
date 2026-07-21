from fastapi import APIRouter, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from utils.tts_client import synthesize_speech as edge_synthesize
from utils.stt_client import transcribe_audio_bytes as google_transcribe, is_asr_available as is_google_asr_available
from utils.xfyun_tts import cloud_synthesize_speech
from utils.xfyun_asr import cloud_transcribe_audio_bytes, is_cloud_asr_available
from config import settings
import io

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/voices")
async def get_voices():
    return {
        "voices": [
            {"id": "default", "name": "默认女声", "description": "标准女声"},
            {"id": "female", "name": "女声", "description": "标准女声"},
            {"id": "male", "name": "男声", "description": "标准男声"},
            {"id": "young", "name": "青年音", "description": "青年音色"},
            {"id": "professional", "name": "播音腔", "description": "播音腔"},
        ],
        "provider": "云端语音服务" if settings.TTS_APP_ID else "Edge TTS",
    }


@router.get("/status")
async def get_voice_status():
    return {
        "tts_available": True,
        "asr_available": is_cloud_asr_available() or is_google_asr_available(),
        "cloud_tts_available": bool(settings.TTS_APP_ID),
        "cloud_asr_available": is_cloud_asr_available(),
        "provider": "云端语音服务" if settings.TTS_APP_ID else "Edge TTS",
    }


@router.post("/synthesize")
async def text_to_speech(text: str = Body(...), voice: str = "default"):
    audio_data = None

    if settings.TTS_APP_ID:
        audio_data = cloud_synthesize_speech(text, voice)

    if audio_data is None:
        audio_data = edge_synthesize(text, voice)

    if audio_data:
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mp3",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
    return {"status": "error", "message": "语音合成失败"}


@router.post("/transcribe")
async def speech_to_text(audio_file: UploadFile = File(...)):
    audio_data = await audio_file.read()
    text = None

    if is_cloud_asr_available():
        text = cloud_transcribe_audio_bytes(audio_data)

    if text is None:
        if is_google_asr_available():
            text = google_transcribe(audio_data)

    if text:
        return {"status": "success", "text": text}
    return {"status": "error", "message": "语音识别失败"}


@router.post("/chat")
async def voice_chat(student_id: str = Body(...), audio_file: UploadFile = File(...)):
    audio_data = await audio_file.read()
    text = None

    if is_cloud_asr_available():
        text = cloud_transcribe_audio_bytes(audio_data)

    if text is None:
        if is_google_asr_available():
            text = google_transcribe(audio_data)

    if not text:
        return {"status": "error", "message": "语音识别失败"}

    from api.tutoring_routes import chat
    chat_result = await chat(student_id, text)

    return {
        "status": "success",
        "recognized_text": text,
        "response": chat_result["response"],
        "emotional_feedback": chat_result.get("emotional_feedback", ""),
        "provider": "云端语音服务" if is_cloud_asr_available() else "Google Speech",
    }
