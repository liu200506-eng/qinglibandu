import asyncio
import io
import sys
import threading

_edge_tts_voice_map = {
    "default": "zh-CN-XiaoxiaoNeural",
    "female": "zh-CN-XiaoxiaoNeural",
    "male": "zh-CN-YunxiNeural",
    "young": "zh-CN-XiaoyiNeural",
    "professional": "zh-CN-YunjianNeural",
}


def _generate_in_thread(text: str, voice_name: str) -> bytes | None:
    try:
        import edge_tts
    except ImportError:
        return None

    audio_buffer = io.BytesIO()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _generate():
        communicate = edge_tts.Communicate(text, voice_name)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
        return audio_buffer.getvalue()

    try:
        return loop.run_until_complete(_generate())
    finally:
        loop.close()


def synthesize_speech(text: str, voice: str = "default") -> bytes | None:
    voice_name = _edge_tts_voice_map.get(voice, _edge_tts_voice_map["default"])

    try:
        import edge_tts
    except ImportError:
        print("[TTS] edge_tts not installed, falling back to text")
        return text.encode("utf-8")

    try:
        result = [None]

        def target():
            result[0] = _generate_in_thread(text, voice_name)

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout=60)

        if thread.is_alive():
            print("[TTS] Timeout")
            return None

        return result[0]

    except Exception as e:
        print(f"TTS error: {e}")
        return None
