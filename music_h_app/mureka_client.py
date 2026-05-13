"""
Mureka Instrumental Music Generation API Client

异步纯音乐生成接口封装：
- 提交: POST https://api.mureka.cn/v1/instrumental/generate
- 轮询: GET  https://api.mureka.cn/v1/instrumental/query/{task_id}
- 下载: 从返回的 choices[0] 下载音频字节
"""

import json
import logging
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
ERROR_MESSAGES = {
    9008: "请求频率过高，请稍后重试",
    6323: "并发任务已达上限，请等待其他任务完成",
}

HTTP_ERROR_MESSAGES = {
    400: "请求参数有误",
    401: "API 密钥无效，请检查配置",
    403: "无权限访问该接口",
    429: "请求过于频繁或配额已用完",
    500: "Mureka 服务内部错误，请稍后重试",
    503: "生成引擎过载，请稍后重试",
}


class MurekaError(Exception):
    """Mureka API 异常"""

    def __init__(self, code, message, user_message):
        self.code = code
        self.message = message
        self.user_message = user_message
        super().__init__(user_message)


class MurekaMusicClient:
    """Mureka Instrumental Music Generation 客户端"""

    GENERATE_URL = "https://api.mureka.cn/v1/instrumental/generate"
    QUERY_URL = "https://api.mureka.cn/v1/instrumental/query/{}"
    DEFAULT_MODEL = "auto"
    POLL_INTERVAL = 3
    MAX_POLL_TIME = 120
    SUBMIT_TIMEOUT = 30
    DOWNLOAD_TIMEOUT = 60

    # Mureka 返回的终止状态
    TERMINAL_STATUSES = {"succeeded", "failed", "timeouted", "cancelled"}

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("MUREKA_API_KEY")
        if not self.api_key:
            raise MurekaError(401, "Missing API key", "Mureka API 密钥未配置")
        self.model = model or os.getenv("MUREKA_MODEL", self.DEFAULT_MODEL)
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt, progress_callback=None):
        """
        完整异步生成流程：提交 → 轮询 → 下载。

        Args:
            prompt: 优化后的音乐描述文本
            progress_callback: callable(pct, message) 用于更新进度

        Returns:
            dict: {'audio_bytes': bytes, 'metadata': dict}

        Raises:
            MurekaError: 所有可恢复的错误
        """
        # Step 1: 提交任务
        if progress_callback:
            progress_callback(10, "正在提交音乐生成任务...")
        task_id = self._submit_task(prompt)
        logger.info("Mureka task submitted: id=%s, model=%s", task_id, self.model)

        if progress_callback:
            progress_callback(20, f"任务已提交 ({task_id[:8]}...)，等待生成...")

        # Step 2: 轮询等待完成
        result_data = self._poll_until_complete(task_id, progress_callback)

        if progress_callback:
            progress_callback(85, "正在下载音频文件...")

        # Step 3: 下载音频
        audio_bytes = self._download_audio(result_data)

        if progress_callback:
            progress_callback(95, "音频下载完成")

        return {
            "audio_bytes": audio_bytes,
            "metadata": {
                "music_duration_ms": result_data.get("duration", 0) * 1000,
                "model": result_data.get("model", self.model),
                "task_id": task_id,
            },
        }

    def _submit_task(self, prompt):
        """提交生成任务，返回 task_id"""
        payload = {
            "model": "auto",
            "n": 1,
            "prompt": prompt[:1024],
            "stream": False
        }

        try:
            resp = requests.post(
                self.GENERATE_URL,
                json=payload,
                headers=self._headers,
                timeout=self.SUBMIT_TIMEOUT,
            )
        except requests.Timeout:
            raise MurekaError(-1, "Submit timed out", "提交任务超时，请稍后重试")
        except requests.RequestException as e:
            logger.error("Mureka submit network error: %s", e)
            raise MurekaError(-1, str(e), f"网络请求失败: {e}")

        if resp.status_code != 200:
            self._check_http_error(resp)

        try:
            data = resp.json()
        except (ValueError, json.JSONDecodeError):
            snippet = resp.text[:300] if resp.text else "(empty)"
            logger.error("Mureka non-JSON submit response: %s", snippet)
            raise MurekaError(-1, snippet, "API 返回数据格式异常")

        self._check_error(data)

        task_id = data.get("id")
        if not task_id:
            raise MurekaError(-1, "Missing task id", "未获取到任务 ID")

        return str(task_id)

    def _poll_until_complete(self, task_id, progress_callback):
        """轮询直到任务完成或失败"""
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            if elapsed > self.MAX_POLL_TIME:
                raise MurekaError(-1, "Polling timeout", "音乐生成超时，请稍后重试")

            try:
                resp = requests.get(
                    self.QUERY_URL.format(task_id),
                    headers=self._headers,
                    timeout=15,
                )
            except requests.RequestException as e:
                logger.warning("Mureka poll network error (will retry): %s", e)
                time.sleep(self.POLL_INTERVAL)
                continue

            if resp.status_code != 200:
                self._check_http_error(resp)

            try:
                data = resp.json()
            except (ValueError, json.JSONDecodeError):
                time.sleep(self.POLL_INTERVAL)
                continue

            self._check_error(data)

            status = data.get("status", "")

            if status == "succeeded":
                logger.info("Mureka task succeeded: id=%s", task_id)
                return data

            if status in ("failed", "timeouted", "cancelled"):
                reason = data.get("failed_reason", "") or data.get("error", {}).get("message", "未知错误")
                raise MurekaError(-1, reason, f"音乐生成失败 ({status}): {reason}")

            # 更新进度 (25% - 80%)
            if progress_callback:
                progress_pct = 25 + int((elapsed / self.MAX_POLL_TIME) * 55)
                progress_pct = min(80, max(25, progress_pct))
                progress_callback(progress_pct, f"音乐生成中... ({int(elapsed)}秒)")

            time.sleep(self.POLL_INTERVAL)

    def _download_audio(self, result_data):
        """从完成结果中提取音频 URL 并下载"""
        audio_url = None

        # choices[0] 是主要的返回格式
        choices = result_data.get("choices")
        if choices and isinstance(choices, list) and len(choices) > 0:
            choice = choices[0]
            audio_url = choice.get("audio_url") or choice.get("url")
        if not audio_url:
            audio_urls = result_data.get("audio_urls")
            if audio_urls and isinstance(audio_urls, list) and len(audio_urls) > 0:
                audio_url = audio_urls[0]
        if not audio_url:
            audio_url = result_data.get("audio_url")

        if not audio_url:
            raise MurekaError(-1, "No audio URL", "API 未返回音频下载地址")

        logger.info("Downloading audio from: %s", audio_url[:120])

        try:
            resp = requests.get(audio_url, timeout=self.DOWNLOAD_TIMEOUT)
            resp.raise_for_status()
        except requests.Timeout:
            raise MurekaError(-1, "Download timed out", "音频下载超时，请重试")
        except requests.RequestException as e:
            logger.error("Audio download failed: %s", e)
            raise MurekaError(-1, str(e), "音频下载失败，请重试")

        if not resp.content:
            raise MurekaError(-1, "Empty audio", "下载的音频文件为空")

        return resp.content

    def _check_error(self, data):
        """检查业务错误"""
        error = data.get("error")
        if not error:
            return

        if isinstance(error, dict):
            message = error.get("message", "")
            code = error.get("code", -1)
        elif isinstance(error, str):
            message = error
            code = -1
        else:
            return

        user_msg = ERROR_MESSAGES.get(code, f"生成失败: {message}")
        logger.error("Mureka API error: code=%s, msg=%s", code, message)
        raise MurekaError(code, message, user_msg)

    def _check_http_error(self, response):
        """检查 HTTP 层错误"""
        status_code = response.status_code
        user_msg = HTTP_ERROR_MESSAGES.get(
            status_code, f"HTTP {status_code}: 请求失败"
        )
        try:
            body = response.json()
            api_msg = body.get("error", {}).get("message", "") if isinstance(body.get("error"), dict) else str(body.get("error", ""))
        except (ValueError, json.JSONDecodeError):
            api_msg = response.text[:200]

        logger.error("Mureka HTTP %s: %s", status_code, api_msg)
        raise MurekaError(status_code, api_msg, user_msg)
