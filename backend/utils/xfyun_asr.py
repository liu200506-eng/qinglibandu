import json
import time
import hashlib
import base64
import asyncio
import threading
from urllib.parse import urlparse
from config import settings
import logging

logger = logging.getLogger(__name__)


def _generate_asr_auth_url(app_id: str, api_key: str, api_secret: str):
    base_url = settings.ASR_BASE_URL
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


def _transcribe_cloud(audio_bytes: bytes) -> str | None:
    try:
        import websockets
    except ImportError:
        logger.error("websockets未安装，请运行 pip install websockets")
        return None

    app_id = settings.ASR_APP_ID
    api_key = settings.ASR_API_KEY
    api_secret = settings.ASR_API_SECRET

    if not app_id or not api_key or not api_secret:
        logger.warning("ASR配置未完成")
        return None

    auth_url, app_id = _generate_asr_auth_url(app_id, api_key, api_secret)

    final_result = [""]

    async def _recognize():
        async with websockets.connect(auth_url) as ws:
            payload = {
                "common": {"app_id": app_id},
                "business": {
                    "language": "zh_cn",
                    "domain": "iat",
                    "accent": "mandarin",
                    "vinfo": 1,
                    "vad_eos": 10000,
                    "dwa": "wpgs",
                },
                "data": {
                    "status": 0,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": base64.b64encode(audio_bytes).decode(),
                },
            }

            await ws.send(json.dumps(payload))

            while True:
                response = await ws.recv()
                data = json.loads(response)

                if data["code"] != 0:
                    logger.error(f"ASR错误: {data['code']} - {data['message']}")
                    return

                result_data = data.get("data", {})
                status = result_data.get("status")

                if result_data.get("result"):
                    ws_result = result_data["result"]
                    if ws_result.get("ws"):
                        for ws_item in ws_result["ws"]:
                            if ws_item.get("cw"):
                                for cw_item in ws_item["cw"]:
                                    final_result[0] += cw_item.get("w", "")

                if status == 2:
                    break

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_recognize())
        return final_result[0]
    except Exception as e:
        logger.error(f"ASR调用失败: {e}")
        return None


def cloud_transcribe_audio_bytes(audio_bytes: bytes) -> str | None:
    result = [None]

    def target():
        result[0] = _transcribe_cloud(audio_bytes)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=60)

    if thread.is_alive():
        logger.error("ASR超时")
        return None

    return result[0]


def is_cloud_asr_available() -> bool:
    return bool(settings.ASR_APP_ID and settings.ASR_API_KEY and settings.ASR_API_SECRET)
