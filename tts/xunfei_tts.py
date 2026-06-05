import asyncio
import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode

import websockets
from dotenv import load_dotenv

load_dotenv()

TTS_HOST = "tts-api.xfyun.cn"
TTS_PATH = "/v2/tts"
TTS_URL  = f"wss://{TTS_HOST}{TTS_PATH}"

# 英文发音人，可通过环境变量覆盖
# 参考：https://www.xfyun.cn/services/online_tts （平台体验中心查看可用发音人）
DEFAULT_VCN = os.getenv("XUNFEI_TTS_VCN", "x4_EnUs_laura")


class TTSError(Exception):
    pass


def _build_auth_url() -> str:
    appid      = os.getenv("XUNFEI_APPID", "")
    api_key    = os.getenv("XUNFEI_API_KEY", "")
    api_secret = os.getenv("XUNFEI_API_SECRET", "")

    if not appid or not api_key or not api_secret:
        raise TTSError(
            "[CONFIG ERROR] 请在 .env 文件中配置 XUNFEI_APPID / XUNFEI_API_KEY / XUNFEI_API_SECRET"
        )

    # RFC1123 格式时间戳（UTC）
    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    # 签名原文：host + date + request-line
    signature_origin = f"host: {TTS_HOST}\ndate: {date}\nGET {TTS_PATH} HTTP/1.1"

    # HMAC-SHA256 → Base64
    signature = base64.b64encode(
        hmac.new(
            api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")

    authorization_origin = (
        f'api_key="{api_key}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

    params = urlencode({"authorization": authorization, "date": date, "host": TTS_HOST})
    return f"{TTS_URL}?{params}"


def _build_request(text: str, vcn: str) -> str:
    appid = os.getenv("XUNFEI_APPID", "")
    payload = {
        "common": {"app_id": appid},
        "business": {
            "aue": "lame",               # MP3 格式
            "auf": "audio/L16;rate=16000",
            "vcn": vcn,
            "speed": 50,                 # 语速 0-100
            "volume": 50,                # 音量 0-100
            "pitch": 50,                 # 音调 0-100
            "tte": "UTF8",
        },
        "data": {
            "status": 2,                 # 一次性发送全部文本
            "text": base64.b64encode(text.encode("utf-8")).decode("utf-8"),
        },
    }
    return json.dumps(payload)


async def synthesize(text: str, vcn: str = DEFAULT_VCN) -> bytes:
    """
    将英文文本合成为 MP3 音频字节。

    Args:
        text: 需要合成的英文文本。
        vcn:  发音人，默认 x4_EnUs_laura（美式英语女声）。

    Returns:
        完整的 MP3 音频字节。
    """
    url = _build_auth_url()
    request_json = _build_request(text, vcn)
    audio_chunks: list[bytes] = []

    try:
        async with websockets.connect(url, ping_interval=None, open_timeout=10) as ws:
            await ws.send(request_json)

            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                code = msg.get("code", -1)
                if code != 0:
                    raise TTSError(
                        f"[TTS ERROR] 讯飞返回错误 code={code}: {msg.get('message', msg)}"
                    )

                data = msg.get("data", {})
                audio_b64 = data.get("audio", "")
                if audio_b64:
                    audio_chunks.append(base64.b64decode(audio_b64))

                # status=2 表示合成完毕
                if data.get("status") == 2:
                    break

    except OSError as e:
        raise TTSError(
            f"[TTS ERROR] 无法连接讯飞语音服务，请检查 APPID/APIKey/APISecret\n{e}"
        )
    except websockets.exceptions.WebSocketException as e:
        raise TTSError(f"[TTS ERROR] WebSocket 异常: {e}")

    if not audio_chunks:
        raise TTSError("[TTS ERROR] 未收到任何音频数据，请检查文本内容或发音人参数")

    return b"".join(audio_chunks)


if __name__ == "__main__":
    import sys

    async def _test():
        test_text = "Hello, welcome to your interview. Please tell me about yourself."
        out_path = os.path.join(
            os.path.dirname(__file__), "..", "tests", "fixtures", "tts_test.mp3"
        )

        print(f"[TEST] 合成文本: {test_text!r}")
        try:
            audio = await synthesize(test_text)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(audio)
            print(f"[OK] 已保存到 {out_path}，大小 {len(audio)} 字节")
        except TTSError as e:
            print(str(e))
            sys.exit(1)

    asyncio.run(_test())
