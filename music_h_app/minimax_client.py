"""
MiniMax Music Generation API Client (music-2.6)
从 .env 读取 API_KEY，和 Mureka 结构完全一致
"""

import json
import logging
import os
from binascii import unhexlify, Error as BinasciiError

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
ERROR_MESSAGES = {
    1000: "服务异常，请稍后重试",
    1001: "音乐生成超时，请稍后重试",
    1002: "请求频率过高，请稍后重试",
    1003: "服务暂时不可用，请稍后重试",
    1004: "API 认证失败，请检查密钥配置",
    1008: "账户余额不足，请联系管理员",
    1024: "服务内部错误，请稍后重试",
    1026: "输入内容包含不适当信息，请修改描述后重试",
    1027: "生成内容未通过审核，请调整提示词后重试",
    1033: "下游服务错误，请稍后重试",
    1039: "Token 超限，请缩短输入内容",
    2013: "请求参数错误，请检查输入内容",
    2049: "无效的 API 密钥，请检查配置",
}

HTTP_ERROR_MESSAGES = {
    400: "请求参数有误",
    401: "API 密钥无效",
    403: "无权限访问",
    429: "请求过于频繁",
    500: "服务内部错误",
}

class MinimaxError(Exception):
    def __init__(self, code, message, user_message):
        self.code = code
        self.message = message
        self.user_message = user_message
        super().__init__(user_message)

class MinimaxMusicClient:
    """和 Mureka 结构完全统一"""
    API_URL = "https://api.minimaxi.com/v1/music_generation"
    DEFAULT_MODEL = "music-2.6"
    MAX_TIMEOUT = 300

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise MinimaxError(1004, "Missing API key", "MINIMAX_API_KEY 未配置")
        
        self.model = model or os.getenv("MINIMAX_MUSIC_MODEL", self.DEFAULT_MODEL)
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def build_payload(self, prompt, audio_format="mp3"):
        # 🔥 完全使用你刚刚跑通的正确格式
        return {
            "model": self.model,
            "prompt": prompt[:2000],       # 正确字段
            "lyrics": "[Inst]",   # 纯音乐专用，不影响结构
            "is_instrumental": True,      # 官方纯音乐开关
            "output_format": "hex",
            "audio_setting": {
                "sample_rate": 44100,
                "bitrate": 256000,
                "format": audio_format
            },
        }

    def generate(self, prompt, audio_format="mp3", task_id=None):
        payload = self.build_payload(prompt, audio_format)
        try:
            response = requests.post(
                self.API_URL, json=payload, headers=self._headers, timeout=self.MAX_TIMEOUT
            )
        except requests.Timeout:
            raise MinimaxError(1001, "Timeout", "请求超时")
        
        data = response.json()
        self._check_error(data)
        return self._parse_success_response(data)

    def _check_error(self, data):
        # 修复官方错误返回格式
        if "base_resp" in data:
            base = data["base_resp"]
            code = base.get("status_code", 2013)
            msg = base.get("status_msg", "未知错误")
            user_msg = ERROR_MESSAGES.get(code, msg)
            raise MinimaxError(code, msg, user_msg)

        if data.get("success") is False:
            base = data.get("base", {})
            code = base.get("status_code", 2013)
            msg = base.get("status_msg", "未知错误")
            user_msg = ERROR_MESSAGES.get(code, msg)
            raise MinimaxError(code, msg, user_msg)

    def _parse_success_response(self, data):
        audio_hex = data["data"]["audio"]
        audio_bytes = unhexlify(audio_hex)
        duration_sec = data["data"].get("duration", 0)
        
        return {
            "audio_bytes": audio_bytes,
            "metadata": {
                "music_duration_ms": duration_sec * 1000,
                "sample_rate": 44100,
                "music_size": len(audio_bytes),
            },
        }

# ---------------------------------------------------------------------------
# main 测试（和 Mureka 写法完全一样）
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        client = MinimaxMusicClient()

        # 古风高质量 prompt
        prompt = "古风纯音乐，江南烟雨意境，轻柔舒缓，古筝与笛子为主奏，静谧清雅，唯美空灵中国风"

        print("⏳ 生成中...30-60秒")
        result = client.generate(prompt)

        with open("ancient_music.mp3", "wb") as f:
            f.write(result["audio_bytes"])

        print("✅ 生成成功：ancient_music.mp3")
        print(f"⏱ 时长：{result['metadata']['music_duration_ms'] // 1000} 秒")

    except MinimaxError as e:
        print(f"❌ 错误：{e.user_message}")