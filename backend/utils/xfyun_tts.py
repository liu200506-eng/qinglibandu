import json
import time
import hashlib
import base64
import asyncio
import threading
import io
from urllib.parse import urlparse
from config import settings
import logging

logger = logging.getLogger(__name__)

_voice_map = {
    "default": "xiaoyan",
    "female": "xiaoyan",
    "male": "aisjiuxu",
    "young": "aisbabyxu",
    "professional": "aisxping",
}


def _generate_tts_auth_url(app_id: str, api_key: str, api_secret: str):
    base_url = settings.TTS_BASE_URL
    parsed = urlparse(base_url)
    host = parsed.netloc
    path = parsed.path

    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
    signature_sha = hashlib.sha256(signature_origin.encode()).digest()
    signature_sha = base64.b64encode(signature_sha).decode()

    authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
    authorization = base64.b64encode(authorization_origin.encode()).decode()

    params = {
        "authorization": authorization,
        "date": date,
        "host": host,
    }

    return f"{base_url}?{urllib.parse.urlencode(params)}", app_id


def _generate_tts(text: str, voice: str) -> bytes | None:
    try:
        import websockets
    except ImportError:
        logger.error("websockets未安装，请运行 pip install websockets")
        return None

    app_id = settings.TTS_APP_ID
    api_key = settings.TTS_API_KEY
    api_secret = settings.TTS_API_SECRET

    if not app_id or not api_key or not api_secret:
        logger.warning("TTS配置未完成，使用edge_tts回退")
        return None

    voice_name = _voice_map.get(voice, _voice_map["default"])
    auth_url, app_id = _generate_tts_auth_url(app_id, api_key, api_secret)

    audio_buffer = io.BytesIO()

    async def _synthesize():
        async with websockets.connect(auth_url) as ws:
            payload = {
                "common": {"app_id": app_id},
                "business": {
                    "aue": "lame",
                    "sfl": 1,
                    "auf": f"audio/L16;rate={settings.TTS_SAMPLE_RATE}",
                    "vcn": voice_name,
                    "tte": "UTF8",
                    "speed": 50,
                    "volume": 50,
                    "pitch": 50,
                },
                "data": {
                    "status": 2,
                    "text": base64.b64encode(text.encode("utf-8")).decode(),
                },
            }

            await ws.send(json.dumps(payload))

            while True:
                response = await ws.recv()
                data = json.loads(response)

                if data["code"] != 0:
                    logger.error(f"TTS错误: {data['code']} - {data['message']}")
                    return None

                audio_data = data.get("data", {}).get("audio")
                status = data.get("data", {}).get("status")

                if audio_data:
                    audio_buffer.write(base64.b64decode(audio_data))

                if status == 2:
                    break

        return audio_buffer.getvalue()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_synthesize())
    except Exception as e:
        logger.error(f"TTS调用失败: {e}")
        return None


def cloud_synthesize_speech(text: str, voice: str = "default") -> bytes | None:
    result = [None]

    def target():
        result[0] = _generate_tts(text, voice)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=60)

    if thread.is_alive():
        logger.error("TTS超时")
        return None

    return result[0]
