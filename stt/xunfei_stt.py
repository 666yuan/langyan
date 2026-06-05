import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

import websockets
from dotenv import load_dotenv

load_dotenv()

RTASR_URL = "wss://rtasr.xfyun.cn/v1/ws"
CHUNK_SIZE = 1280       # 1280 bytes = 40ms of 16kHz 16-bit mono PCM
CHUNK_INTERVAL = 0.04   # 40ms between chunks


class STTError(Exception):
    pass


def _build_auth_url() -> str:
    appid = os.getenv("XUNFEI_APPID", "")
    api_key = os.getenv("XUNFEI_API_KEY", "")

    if not appid or not api_key:
        raise STTError(
            "[CONFIG ERROR] 请在 .env 文件中配置 XUNFEI_APPID / XUNFEI_API_KEY / XUNFEI_API_SECRET"
        )

    ts = str(int(time.time()))

    # signa = Base64( HmacSHA1( MD5(appid + ts), api_key ) )
    md5_str = hashlib.md5((appid + ts).encode("utf-8")).hexdigest()
    h = hmac.new(api_key.encode("utf-8"), md5_str.encode("utf-8"), hashlib.sha1)
    signa = base64.b64encode(h.digest()).decode("utf-8")

    params = urlencode({"appid": appid, "ts": ts, "signa": signa})
    return f"{RTASR_URL}?{params}"


def _extract_text(data_str: str) -> tuple[str, bool]:
    """从讯飞返回的 data 字段提取文字。返回 (text, is_final)。"""
    try:
        data = json.loads(data_str)
        st = data.get("cn", {}).get("st", {})
        is_final = st.get("type") == "0"
        words = [
            cw.get("w", "")
            for rt in st.get("rt", [])
            for ws_item in rt.get("ws", [])
            for cw in ws_item.get("cw", [])
        ]
        return "".join(words), is_final
    except Exception:
        return "", False


async def transcribe(audio_bytes: bytes) -> str:
    """
    将 PCM 音频字节发送到讯飞实时语音转写，返回最终识别文字。

    音频要求：16kHz 采样率，16-bit，单声道，原始 PCM（无 WAV 头）。
    """
    url = _build_auth_url()
    final_text_parts: list[str] = []

    try:
        async with websockets.connect(url, ping_interval=None, open_timeout=10) as ws:

            async def _send():
                for i in range(0, len(audio_bytes), CHUNK_SIZE):
                    chunk = audio_bytes[i : i + CHUNK_SIZE]
                    await ws.send(chunk)
                    await asyncio.sleep(CHUNK_INTERVAL)
                # 发送空帧，通知服务端音频结束
                await ws.send(b"")

            async def _recv():
                async for raw in ws:
                    if isinstance(raw, bytes):
                        continue
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    action = msg.get("action", "")

                    if action == "error":
                        raise STTError(
                            f"[STT ERROR] 讯飞返回错误: {msg.get('desc', msg)}"
                        )

                    if action == "result" and msg.get("code") == "0":
                        text, is_final = _extract_text(msg.get("data", "{}"))
                        if is_final and text:
                            final_text_parts.append(text)

                    if action == "session_end":
                        break

            await asyncio.gather(_send(), _recv())

    except OSError as e:
        raise STTError(
            f"[STT ERROR] 无法连接讯飞语音服务，请检查 APPID/APIKey\n{e}"
        )
    except websockets.exceptions.WebSocketException as e:
        raise STTError(f"[STT ERROR] WebSocket 异常: {e}")

    return "".join(final_text_parts).strip()


def strip_wav_header(wav_bytes: bytes) -> bytes:
    """剥离 WAV 文件头（44 字节），返回原始 PCM 数据。"""
    if wav_bytes[:4] == b"RIFF":
        return wav_bytes[44:]
    return wav_bytes


if __name__ == "__main__":
    import sys

    async def _test():
        test_file = os.path.join(
            os.path.dirname(__file__), "..", "tests", "fixtures", "hello_en.wav"
        )
        if not os.path.exists(test_file):
            print(f"[ERROR] 测试文件不存在: {test_file}")
            print("请在 tests/fixtures/ 放一段英文录音 hello_en.wav（16kHz / 16-bit / 单声道）")
            sys.exit(1)

        with open(test_file, "rb") as f:
            raw_audio = strip_wav_header(f.read())

        print(f"[TEST] 发送 {len(raw_audio)} 字节音频...")
        try:
            result = await transcribe(raw_audio)
            print(f"[RESULT] {result!r}")
        except STTError as e:
            print(str(e))
            sys.exit(1)

    asyncio.run(_test())
