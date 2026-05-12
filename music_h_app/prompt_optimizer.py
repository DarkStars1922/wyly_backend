"""
提示词优化器：将用户简单冥想描述 → 专业 Minimax 音乐提示词

双策略：
  1. LLM 优化（Minimax abab6.5s-chat）— 质量高，需网络
  2. 模板后备 — LLM 不可用时自动降级
"""

import json
import logging
import os

import requests

from .prompt_templates import (
    FIVE_TONE_MAP,
    SYSTEM_PROMPT,
    TEMPLATE_PROMPTS,
    DEFAULT_TEMPLATE,
    USER_GROUP_TONE_MAP,
    EMOTION_TONE_MAP,
)

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """将用户的中文冥想描述优化为专业英文音乐生成提示词"""

    TEXT_API_URL = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
    LLM_MODEL = "abab6.5s-chat"
    LLM_TIMEOUT = 25
    LLM_MAX_TOKENS = 600

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.enabled = os.getenv("ENABLE_PROMPT_OPTIMIZATION", "true").lower() == "true"

    # ------------------------------------------------------------------
    def optimize(self, user_input, tone=None, user_group=None, emotion=None, duration=None):
        """
        转换用户输入为专业音乐提示词。

        Args:
            user_input: 用户原始描述（中文）
            tone: 可选，五音之一: gong/shang/jue/zhi/yu
            user_group: 可选，用户群体
            emotion: 可选，情绪状态
            duration: 可选，期望时长（秒）

        Returns:
            dict: {
                'optimized_prompt': str,   # 优化后的提示词
                'negative_prompt': str,    # 负面约束
                'original_input': str,     # 原始输入
                'was_optimized': bool,     # 是否进行过优化
                'optimization_method': str, # 'llm' / 'template' / 'none'
            }
        """
        if not self.enabled:
            return self._passthrough(user_input)

        # 解析五音信息
        if tone is None and user_group:
            tone = USER_GROUP_TONE_MAP.get(user_group)
        if tone is None and emotion:
            tone = EMOTION_TONE_MAP.get(emotion)

        tone_info = FIVE_TONE_MAP.get(tone, {}) if tone else {}

        # 尝试 LLM 优化
        try:
            return self._llm_optimize(user_input, tone_info, user_group, emotion, duration)
        except Exception as e:
            logger.warning(f"LLM optimization failed: {e}, falling back to template")

        # 后备：模板优化
        return self._template_optimize(user_input, tone, user_group, emotion, duration)

    # ------------------------------------------------------------------
    def _build_context(self, user_input, tone_info, user_group, emotion):
        """构建传给 LLM 的上下文字段"""
        instruments = tone_info.get("instruments", ["guqin", "xun", "bamboo flute"])
        bpm_min, bpm_max = tone_info.get("bpm_range", (55, 72))
        mood = tone_info.get("mood", "meditative, tranquil, healing")
        key_mode = tone_info.get("key", "Chinese pentatonic mode")

        return {
            "user_input": user_input,
            "instruments": instruments,
            "bpm_min": bpm_min,
            "bpm_max": bpm_max,
            "key": key_mode,
            "mood": mood,
            "user_group": user_group or "通用",
            "emotion": emotion or "通用",
        }

    # ------------------------------------------------------------------
    def _llm_optimize(self, user_input, tone_info, user_group, emotion, duration=None):
        """调用 Minimax 文本模型优化提示词"""
        ctx = self._build_context(user_input, tone_info, user_group, emotion)

        dur_hint = ""
        if duration:
            if duration <= 60:
                dur_hint = f"期望时长约{duration}秒，短小精炼的乐段\n"
            elif duration <= 180:
                dur_hint = f"期望时长约{duration}秒，适中篇幅的冥想音乐\n"
            else:
                dur_hint = f"期望时长约{duration}秒，绵长舒展的长篇冥想音乐\n"

        user_message = (
            f"请将以下冥想音乐描述优化为一段优美的中文意境描述：\n\n"
            f"用户输入：{ctx['user_input']}\n"
            f"情绪基调：{ctx['mood']}\n"
            f"{dur_hint}"
        )

        payload = {
            "model": self.LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.6,
            "max_tokens": self.LLM_MAX_TOKENS,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        resp = requests.post(
            self.TEXT_API_URL,
            json=payload,
            headers=headers,
            timeout=self.LLM_TIMEOUT,
        )
        data = resp.json()

        # 检查 LLM 响应的错误
        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code", 0) != 0:
            raise RuntimeError(f"LLM error: {base_resp.get('status_msg', 'unknown')}")

        raw = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        if not raw or len(raw) < 20:
            raise RuntimeError("LLM returned empty or too-short response")

        negative = tone_info.get("negative_prompt", "")

        logger.info(f"LLM optimization success: '{user_input[:40]}...' -> '{raw[:60]}...'")
        return {
            "optimized_prompt": raw,
            "negative_prompt": negative,
            "original_input": user_input,
            "was_optimized": True,
            "optimization_method": "llm",
        }

    # ------------------------------------------------------------------
    def _template_optimize(self, user_input, tone, user_group, emotion, duration=None):
        """模板后备：用预设模板作为优化结果"""
        key = (tone, emotion) if tone and emotion else None
        template = None
        if key:
            template = TEMPLATE_PROMPTS.get(key)

        if not template:
            template = TEMPLATE_PROMPTS.get((tone, "anxiety")) if tone else None

        if not template:
            template = DEFAULT_TEMPLATE

        tone_info = FIVE_TONE_MAP.get(tone, {}) if tone else {}
        negative = tone_info.get(
            "negative_prompt",
            "vocals, rap, lyrics, strong drums, fast tempo, aggressive, electronic",
        )

        if duration and duration > 180:
            combined = f"{template}，绵长舒展，余韵悠远"
        else:
            combined = template

        logger.info(f"Template optimization used: key={key}")
        return {
            "optimized_prompt": combined,
            "negative_prompt": negative,
            "original_input": user_input,
            "was_optimized": True,
            "optimization_method": "template",
        }

    # ------------------------------------------------------------------
    def _passthrough(self, user_input):
        """未启用优化时的直通模式"""
        return {
            "optimized_prompt": user_input,
            "negative_prompt": None,
            "original_input": user_input,
            "was_optimized": False,
            "optimization_method": "none",
        }
