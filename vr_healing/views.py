import copy
import hmac
import json
import math
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from .models import VRSession


GOALS = {"relax", "sleep", "focus", "energy"}
INSTRUMENTS = {"chinese", "western"}
TONES = {"gong", "shang", "jue", "zhi", "yu"}
SOUNDSCAPES = {"rain", "waves", "fire", "stream"}
SCENES = {"ocean", "forest", "aurora"}
COMPANIONS = {"xiaoxuan", "xiaoxing"}
STAI_REVERSE_INDEXES = {0, 1, 4, 7, 9, 10, 14, 15, 18, 19}

BASIC_FIELDS = (
    "heartRate",
    "respiration",
    "temperature",
    "oxygenSaturation",
    "skinConductance",
)
EEG_FIELDS = ("delta", "theta", "alpha", "beta", "gamma", "lowAlpha", "highAlpha")
EMOTION_FIELDS = (
    "polarity",
    "happy",
    "neutral",
    "sadness",
    "fear",
    "surprise",
    "disgust",
    "anger",
)
DEVICE_FIELDS = (
    "eyeX",
    "eyeY",
    "accelerationX",
    "accelerationY",
    "accelerationZ",
    "gyroscopeX",
    "gyroscopeY",
    "gyroscopeZ",
    "ambientTemperature",
    "humidity",
)
SERIES_FIELDS = BASIC_FIELDS + EEG_FIELDS
MAX_SERIES_ITEMS = 1000
MAX_JSON_BYTES = 1024 * 1024

DEFAULT_VIDEO_CATALOG = (
    {
        "videoId": "vr-video-2-27",
        "title": "晨雾海岸",
        "scene": "ocean",
        "localPath": "assets/video/library/2_27.mp4",
        "functionTag": "舒缓",
        "tags": ["relax", "sleep", "chinese"],
    },
    {
        "videoId": "vr-video-2-25",
        "title": "林间微光",
        "scene": "forest",
        "localPath": "assets/video/library/2_25.mp4",
        "functionTag": "安定",
        "tags": ["relax", "sleep", "focus", "western"],
    },
    {
        "videoId": "vr-video-2-10",
        "title": "极光来信",
        "scene": "aurora",
        "localPath": "assets/video/library/2_10.mp4",
        "functionTag": "清醒",
        "tags": ["focus", "energy", "western"],
    },
)

MUSIC_PATHS = {
    "piano": "assets/audio/西方轻音乐.mp3",
    "five-tone": "assets/music/tone-wood.m4a",
    "tone-gong": "assets/music/tone-earth.m4a",
    "tone-shang": "assets/music/tone-metal.m4a",
    "tone-jue": "assets/music/tone-wood.m4a",
    "tone-zhi": "assets/music/tone-fire.m4a",
    "tone-yu": "assets/music/tone-water.m4a",
}
SOUNDSCAPE_PATHS = {
    "rain": "assets/audio/soundscape/rain.mp3",
    "waves": "assets/audio/soundscape/waves.mp3",
    "fire": "assets/audio/soundscape/fire.mp3",
    "stream": "assets/audio/soundscape/stream.mp3",
}


def _configured(name, default=""):
    value = getattr(settings, name, None)
    if value not in (None, ""):
        return value
    return os.environ.get(name, default)


class ApiProblem(Exception):
    def __init__(self, message, status=400, code="invalid_request"):
        self.message = message
        self.status = status
        self.code = code


def _error(problem):
    if isinstance(problem, ApiProblem):
        return JsonResponse(
            {"error": {"code": problem.code, "message": problem.message}},
            status=problem.status,
        )
    return JsonResponse(
        {"error": {"code": "invalid_request", "message": str(problem)}}, status=400
    )


def _json_body(request):
    content_length = request.META.get("CONTENT_LENGTH")
    if content_length and int(content_length) > MAX_JSON_BYTES:
        raise ApiProblem("请求体过大。", code="payload_too_large", status=413)
    try:
        value = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ApiProblem("请求体必须是有效的 JSON。")
    if not isinstance(value, dict):
        raise ApiProblem("请求体必须是 JSON 对象。")
    return value


def _session_key(request, create=False):
    if create and not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _owned_session(request, session_id):
    key = _session_key(request)
    if not key:
        raise ApiProblem("找不到该体验会话。", status=404, code="not_found")
    try:
        return VRSession.objects.get(id=session_id, session_key=key)
    except (VRSession.DoesNotExist, ValueError):
        raise ApiProblem("找不到该体验会话。", status=404, code="not_found")


def _iso(value):
    return value.isoformat() if value else None


def _analysis_json(session):
    result = {"status": session.analysis_status}
    if session.analysis_text:
        result["text"] = session.analysis_text
    if session.analysis_model:
        result["model"] = session.analysis_model
    if session.analysis_generated_at:
        result["generatedAt"] = _iso(session.analysis_generated_at)
    return result


def _session_json(session):
    return {
        "id": str(session.id),
        "companion": session.companion,
        "consent": session.consent,
        "preferences": session.preferences,
        "before": session.before,
        "after": session.after,
        "plan": session.plan,
        "elapsedSeconds": session.elapsed_seconds,
        "durationSeconds": session.duration_seconds,
        "status": session.status,
        "analysis": _analysis_json(session),
    }


def _report_json(session):
    return {
        "id": str(session.id),
        "before": session.before,
        "after": session.after,
        "plan": session.plan,
        "elapsedSeconds": session.elapsed_seconds,
        "durationSeconds": session.duration_seconds,
        "status": session.status,
        "analysis": _analysis_json(session),
    }


def _invalidate_analysis(session):
    session.analysis_revision += 1
    session.analysis_status = "pending"
    session.analysis_text = None
    session.analysis_model = None
    session.analysis_generated_at = None


def _empty_measurement(fields):
    return {field: None for field in fields}


def _empty_assessment(stage, source="questionnaire"):
    return {
        "stage": stage,
        "basic": _empty_measurement(BASIC_FIELDS),
        "eeg": _empty_measurement(EEG_FIELDS),
        "emotion": _empty_measurement(EMOTION_FIELDS),
        "device": _empty_measurement(DEVICE_FIELDS),
        "series": {},
        "questionnaire": {
            "name": "STAI-S",
            "score": None,
            "responses": [],
            "totalItems": 20,
            "completedAt": None,
            "scoringVersion": "stai-s-v1",
        },
        "flags": {"highRisk": False},
        "source": source,
        "capturedAt": _iso(timezone.now()),
    }


def _score_stai(responses):
    if len(responses) != 20 or any(
        isinstance(value, bool) or not isinstance(value, int) or value not in (1, 2, 3, 4)
        for value in responses
    ):
        raise ApiProblem("responses 必须包含 20 个 1 到 4 的整数。", code="invalid_responses")
    return sum((5 - value if index in STAI_REVERSE_INDEXES else value) for index, value in enumerate(responses))


def _assessment_with_questionnaire(stage, responses, previous=None):
    assessment = _empty_assessment(stage)
    if isinstance(previous, dict) and previous.get("source") == "device-api":
        for group in ("basic", "eeg", "emotion", "device", "series"):
            if group in previous:
                assessment[group] = copy.deepcopy(previous[group])
    score = _score_stai(responses)
    now = _iso(timezone.now())
    assessment["questionnaire"] = {
        "name": "STAI-S",
        "score": score,
        "responses": responses,
        "totalItems": 20,
        "completedAt": now,
        "scoringVersion": "stai-s-v1",
    }
    assessment["capturedAt"] = now
    return assessment


def _field_value(value, field, maximum=1_000_000):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ApiProblem(f"{field} 必须是数字或 null。", code="invalid_measurement")
    if not math.isfinite(float(value)) or abs(float(value)) > maximum:
        raise ApiProblem(f"{field} 超出允许范围。", code="invalid_measurement")
    return value


def _normalize_group(data, fields, label):
    if data is None:
        return _empty_measurement(fields)
    if not isinstance(data, dict):
        raise ApiProblem(f"{label} 必须是对象。", code="invalid_measurement")
    return {field: _field_value(data.get(field), f"{label}.{field}") for field in fields}


def _normalize_series(data):
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ApiProblem("series 必须是对象。", code="invalid_measurement")
    result = {}
    for field in SERIES_FIELDS:
        values = data.get(field)
        if values is None:
            continue
        if not isinstance(values, list) or len(values) > MAX_SERIES_ITEMS:
            raise ApiProblem("series 数组长度或格式不正确。", code="invalid_measurement")
        result[field] = [_field_value(value, f"series.{field}") for value in values]
    return result


def _device_assessment(stage, payload, previous=None):
    assessment = copy.deepcopy(previous) if isinstance(previous, dict) else _empty_assessment(stage, "device-api")
    assessment["stage"] = stage
    for name, fields in (
        ("basic", BASIC_FIELDS),
        ("eeg", EEG_FIELDS),
        ("emotion", EMOTION_FIELDS),
        ("device", DEVICE_FIELDS),
    ):
        if name in payload:
            assessment[name] = _normalize_group(payload.get(name), fields, name)
    if "series" in payload:
        assessment["series"] = _normalize_series(payload.get("series"))
    if not assessment.get("questionnaire"):
        assessment["questionnaire"] = _empty_assessment(stage)["questionnaire"]
    assessment["flags"] = {"highRisk": False}
    assessment["source"] = "device-api"
    assessment["capturedAt"] = _iso(timezone.now())
    return assessment


def _asset_local_path(relative_path):
    if not isinstance(relative_path, str):
        return None
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if not normalized or ".." in Path(normalized).parts:
        return None
    return Path(settings.BASE_DIR) / "static" / "vr" / normalized


def _asset_url(relative_path, require_local=True):
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if ".." in Path(normalized).parts:
        return None
    base = _configured("VR_MEDIA_BASE_URL") or ""
    if base:
        return base.rstrip("/") + "/" + normalized
    path = _asset_local_path(normalized)
    if require_local and (path is None or not path.is_file()):
        return None
    return settings.STATIC_URL.rstrip("/") + "/vr/" + normalized


def _catalog_path():
    configured = _configured("VR_MEDIA_CATALOG_PATH") or ""
    if configured:
        return Path(configured)
    return Path(settings.BASE_DIR) / "static" / "vr" / "assets" / "data" / "recommendation-catalog-v2.json"


def _scene_from_video(item):
    text = " ".join(
        str(value)
        for value in (
            item.get("scene"),
            item.get("sceneCategory"),
            item.get("title"),
            *(item.get("contentKeywords") or []),
            *(item.get("tags") or []),
        )
    )
    if any(word in text.lower() for word in ("海", "水", "coast", "ocean", "water")):
        return "ocean"
    if any(word in text.lower() for word in ("极光", "aurora", "雪", "山", "cloud")):
        return "aurora"
    return item.get("scene") if item.get("scene") in SCENES else "forest"


def _catalog_values(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return value if isinstance(value, (list, tuple, set)) else []


def _catalog_number(value, default=0.0):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, value))


def _catalog_item(item):
    if not isinstance(item, dict):
        return None
    video_id = item.get("videoId") or item.get("video_id") or item.get("id")
    relative = item.get("localPath") or item.get("path") or item.get("file")
    raw_url = item.get("url")
    if not relative and isinstance(raw_url, str) and not raw_url.startswith(("http://", "https://", "/")):
        relative = raw_url
    if isinstance(raw_url, str) and raw_url.startswith(("http://", "https://")):
        url = raw_url
    elif relative:
        url = _asset_url(relative)
    else:
        url = None
    if not video_id or not url:
        return None
    tags = (
        _catalog_values(item.get("tags"))
        + _catalog_values(item.get("contentKeywords"))
        + _catalog_values(item.get("moodKeywords"))
        + _catalog_values(item.get("functionTag"))
        + _catalog_values(item.get("sceneCategory"))
    )
    vector = item.get("vector") if isinstance(item.get("vector"), dict) else {}
    safety = item.get("safetyFlags") if isinstance(item.get("safetyFlags"), dict) else {}
    normalized_relative = str(relative).replace("\\", "/").lstrip("/") if relative else ""
    return {
        "videoId": str(video_id),
        "title": str(item.get("title") or item.get("name") or video_id),
        "scene": _scene_from_video(item),
        "url": url,
        "mediaKey": normalized_relative.lower() or str(raw_url or url).lower(),
        "sceneCategory": str(item.get("sceneCategory") or item.get("scene") or ""),
        "functionTag": str(item.get("functionTag") or item.get("function_tag") or "慢节奏"),
        "tags": [str(tag).lower() for tag in tags if tag],
        "moodKeywords": [str(tag).lower() for tag in _catalog_values(item.get("moodKeywords")) if tag],
        "vector": {str(key): _catalog_number(value) for key, value in vector.items()},
        "safetyFlags": {str(key): bool(value) for key, value in safety.items()},
    }


def _video_catalog():
    candidates = []
    path = _catalog_path()
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            values = raw.get("videos", []) if isinstance(raw, dict) else raw
            if isinstance(values, list):
                candidates.extend(values)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            candidates = []
    candidates.extend(DEFAULT_VIDEO_CATALOG)
    result = []
    seen = set()
    for item in candidates:
        normalized = _catalog_item(item)
        if normalized and normalized["mediaKey"] not in seen:
            seen.add(normalized["mediaKey"])
            result.append(normalized)
    return result


def _media_config():
    videos = {}
    for scene in SCENES:
        videos[scene] = None
    for video in _video_catalog():
        videos.setdefault(video["scene"], video["url"])
        if videos.get(video["scene"]) is None:
            videos[video["scene"]] = video["url"]
    # Keep a stable key for each scene even when a future catalog has no matching tag.
    for fallback in DEFAULT_VIDEO_CATALOG:
        if not videos.get(fallback["scene"]):
            videos[fallback["scene"]] = _asset_url(fallback["localPath"])
    music = {key: _asset_url(path) for key, path in MUSIC_PATHS.items()}
    soundscape = {key: _asset_url(path) for key, path in SOUNDSCAPE_PATHS.items()}
    return {"video": videos, "music": music, "soundscape": soundscape}


def _validate_choice(payload, field, allowed, default=None):
    value = payload.get(field, default)
    if value not in allowed:
        raise ApiProblem(f"{field} 不是有效选项。", code=f"invalid_{field}")
    return value


def _preferred_scene(goal, score):
    if goal == "sleep":
        return "forest"
    if goal == "focus":
        return "aurora"
    if goal == "energy":
        return "aurora"
    return "ocean" if score >= 45 else "forest"


def _make_plan(session, payload):
    if not session.before or session.before.get("questionnaire", {}).get("score") is None:
        raise ApiProblem("请先完成前测问卷。", code="before_assessment_required")
    preferences = session.preferences or {}
    goal = _validate_choice(payload, "goal", GOALS, preferences.get("goal", "relax"))
    instrument = _validate_choice(payload, "instrument", INSTRUMENTS, preferences.get("instrument", "chinese"))
    tone = _validate_choice(payload, "tone", TONES, preferences.get("tone", "jue"))
    soundscape = _validate_choice(payload, "soundscape", SOUNDSCAPES, preferences.get("soundscape", "rain"))
    scene = payload.get("scene")
    if scene is not None and scene not in SCENES:
        raise ApiProblem("scene 不是有效选项。", code="invalid_scene")
    score = int(session.before["questionnaire"]["score"])
    target_scene = scene
    videos = _video_catalog()
    if not videos:
        raise ApiProblem("当前没有可播放的 VR 视频素材。", status=503, code="media_unavailable")

    stress = max(0.0, min(1.0, (score - 20) / 60))
    goal_profile = {
        "relax": {"valence": 0.66, "relaxation": 0.84, "arousal": 0.18, "safety": 0.92, "rhythm": 0.16, "function": 0.12},
        "sleep": {"valence": 0.55, "relaxation": 0.94, "arousal": 0.10, "safety": 0.96, "rhythm": 0.10, "function": 0.08},
        "focus": {"valence": 0.56, "relaxation": 0.58, "arousal": 0.38, "safety": 0.84, "rhythm": 0.28, "function": 0.52},
        "energy": {"valence": 0.78, "relaxation": 0.42, "arousal": 0.58, "safety": 0.80, "rhythm": 0.38, "function": 0.72},
    }[goal].copy()
    goal_profile["relaxation"] = min(1.0, goal_profile["relaxation"] + stress * 0.08)
    goal_profile["arousal"] = max(0.05, goal_profile["arousal"] - stress * 0.10)
    goal_profile["safety"] = min(1.0, goal_profile["safety"] + stress * 0.06)
    function_targets = {
        "relax": {"安抚", "舒缓", "放松"},
        "sleep": {"安抚", "舒缓", "助眠"},
        "focus": {"正念", "专注"},
        "energy": {"提振", "活跃", "正念"},
    }[goal]
    tone_preferences = {
        "gong": (0.50, {"山", "云", "开阔"}),
        "shang": (0.38, {"天空", "雪", "专注", "清冷"}),
        "jue": (0.20, {"自然", "荷", "青山", "云雾", "生机"}),
        "zhi": (0.62, {"日出", "日落", "明亮", "温暖", "希望"}),
        "yu": (0.12, {"海", "水", "荷塘", "湿地", "柔和"}),
    }
    tone_arousal, tone_keywords = tone_preferences[tone]
    soundscape_keywords = {
        "rain": {"云雾", "荷塘", "柔和", "静谧", "舒缓"},
        "waves": {"海岸", "湿地", "开阔", "水"},
        "fire": {"温暖", "日落", "山峦", "晚霞"},
        "stream": {"荷", "自然", "清新", "云", "水"},
    }[soundscape]

    def rank(video):
        vector = video["vector"]
        value = (
            0.18 * (1 - abs(vector.get("dim1_valence", 0.5) - goal_profile["valence"]))
            + 0.22 * (1 - abs(vector.get("dim2_relaxation_inducibility", 0.5) - goal_profile["relaxation"]))
            + 0.16 * (1 - abs(vector.get("dim3_arousal", 0.5) - goal_profile["arousal"]))
            + 0.18 * (1 - abs(vector.get("dim4_safety", 0.5) - goal_profile["safety"]))
            + 0.10 * (1 - abs(vector.get("dim5_visual_rhythm", 0.5) - goal_profile["rhythm"]))
            + 0.10 * (1 - abs(vector.get("dim6_function", 0.5) - goal_profile["function"]))
        )
        tags = set(video["tags"]) | set(video["moodKeywords"])
        function_match = 1.0 if video["functionTag"] in function_targets else 0.0
        tone_match = len(tags & {keyword.lower() for keyword in tone_keywords}) / max(1, len(tone_keywords))
        tone_arousal_match = 1 - abs(vector.get("dim3_arousal", 0.5) - tone_arousal)
        soundscape_match = len(tags & {keyword.lower() for keyword in soundscape_keywords}) / max(1, len(soundscape_keywords))
        # The catalog has no audio metadata, so instrument only nudges the visual style.
        instrument_match = 1.0 if (instrument == "chinese" and video["sceneCategory"] not in {"城市建设"}) else 0.0
        scene_match = 1.0 if target_scene and video["scene"] == target_scene else 0.0
        safety = video["safetyFlags"]
        safety_penalty = 0.35 if any(safety.get(key) for key in ("contains_flashing", "contains_dark_threatening_elements", "contains_people")) else 0.0
        transition_penalty = 0.10 if safety.get("contains_sudden_transition") and goal in {"sleep", "relax"} else 0.0
        return (
            value
            + 0.12 * function_match
            + 0.08 * tone_match
            + 0.08 * tone_arousal_match
            + 0.10 * soundscape_match
            + 0.02 * instrument_match
            + 0.12 * scene_match
            - safety_penalty
            - transition_penalty
        )

    video = max(videos, key=lambda item: (rank(item), item["videoId"]))
    recommendation_score = round(max(0.0, min(1.0, rank(video))), 3)
    music = "five-tone" if instrument == "chinese" else "piano"
    goal_label = {"relax": "减压", "sleep": "助眠", "focus": "专注", "energy": "提振"}[goal]
    reason = (
        f"围绕“{goal_label}”和你选择的{('中国乐器' if instrument == 'chinese' else '西洋乐器')}，"
        f"从{video['title']}的连续自然节律开始。"
    )
    reasons = [
        f"目标偏好匹配：{goal_label}。",
        f"素材特征匹配：{video['functionTag']}、{video['sceneCategory']}。",
        f"已按当前 STAI-S 分数 {score}、五音和声音场景完成排序。",
    ]
    plan = {
        "goal": goal,
        "scene": video["scene"],
        "instrument": instrument,
        "tone": tone,
        "music": music,
        "soundscape": soundscape,
        "title": video["title"],
        "reason": reason,
        "reasons": reasons,
        "videoId": video["videoId"],
        "videoUrl": video["url"],
        "sourceType": "questionnaire",
        "algorithm": "stai-catalog-vector-v2",
        "recommendationScore": recommendation_score,
        "functionTag": video["functionTag"],
    }
    session.preferences = {
        "goal": goal,
        "instrument": instrument,
        "tone": tone,
        "soundscape": soundscape,
        "scene": video["scene"],
    }
    session.plan = plan
    _invalidate_analysis(session)
    session.save()
    return plan


def _ai_endpoint():
    configured = _configured("VR_AI_BASE_URL") or "https://api.deepseek.com/chat/completions"
    endpoint = configured.strip().rstrip("/")
    if endpoint.endswith("/chat/completions"):
        return endpoint
    if endpoint.endswith("/v1"):
        return endpoint + "/chat/completions"
    return endpoint + "/chat/completions"


def _ai_key():
    return _configured("VR_AI_API_KEY")


def _analysis_prompt(session):
    before = session.before or {}
    after = session.after or {}

    def present(values):
        return {
            key: value
            for key, value in (values or {}).items()
            if value is not None
        }

    data = {
        "beforeQuestionnaireScore": before.get("questionnaire", {}).get("score"),
        "afterQuestionnaireScore": after.get("questionnaire", {}).get("score"),
        "beforeBasic": present(before.get("basic")),
        "afterBasic": present(after.get("basic")),
        "goal": (session.plan or {}).get("goal"),
        "instrument": (session.plan or {}).get("instrument"),
        "tone": (session.plan or {}).get("tone"),
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _strip_thinking(text):
    text = re.sub(r"<think(?:ing)?\b[^>]*>.*?</think(?:ing)?>", "", text, flags=re.I | re.S)
    return text.strip()[:4000]


def _call_ai(session):
    revision = session.analysis_revision

    def save_result(**values):
        updated = VRSession.objects.filter(
            pk=session.pk,
            analysis_revision=revision,
        ).update(**values)
        session.refresh_from_db()
        return updated

    key = _ai_key()
    model = _configured("VR_AI_MODEL") or "deepseek-chat"
    if not key:
        save_result(
            analysis_status="unavailable",
            analysis_text=None,
            analysis_model=None,
            analysis_generated_at=None,
        )
        return
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是 VR 放松体验的记录助手。用简洁、事实性的中文回答，最多 120 字。"
                    "这是非医疗体验记录，不做诊断、不做风险分级，不把问卷分数解释成疾病。"
                    "只描述提供的数据和体验前后是否存在可见的变化；没有提供的设备指标不要提及，也不要补写或推断。"
                    "重点给出简洁、温和、适合展示的体验反馈。不要输出思考过程或 XML 标签。"
                ),
            },
            {"role": "user", "content": _analysis_prompt(session)},
        ],
        "max_tokens": 300,
        "temperature": 0.2,
    }
    try:
        response = requests.post(
            _ai_endpoint(),
            json=payload,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=45,
        )
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError("upstream status")
        body = response.json()
        base_resp = body.get("base_resp") if isinstance(body, dict) else None
        if isinstance(base_resp, dict) and str(base_resp.get("status_code", "0")) not in {"0", "200"}:
            raise RuntimeError("upstream response")
        choices = body.get("choices") if isinstance(body, dict) else None
        content = choices[0].get("message", {}).get("content") if choices else None
        content = _strip_thinking(content) if isinstance(content, str) else ""
        if not content:
            raise RuntimeError("empty upstream response")
    except Exception:
        save_result(
            analysis_status="failed",
            analysis_text=None,
            analysis_model=None,
            analysis_generated_at=None,
        )
        return
    save_result(
        analysis_status="ready",
        analysis_text=content,
        analysis_model=model,
        analysis_generated_at=timezone.now(),
    )



@require_GET
@ensure_csrf_cookie
def config(request):
    return JsonResponse(
        {
            "csrfToken": get_token(request),
            "media": _media_config(),
            "aiConfigured": bool(_ai_key()),
            "deviceConfigured": False,
        }
    )


def vr_index(request):
    index = Path(settings.BASE_DIR) / "static" / "vr" / "index.html"
    if not index.is_file():
        return HttpResponse("VR frontend is unavailable.", status=404)
    return HttpResponse(index.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")


@require_http_methods(["GET", "POST"])
@csrf_protect
def sessions(request):
    if request.method == "GET":
        key = _session_key(request)
        if not key:
            return JsonResponse({"sessions": []})
        rows = VRSession.objects.filter(session_key=key).order_by("-created_at")[:20]
        return JsonResponse({"sessions": [_session_json(row) for row in rows]})
    try:
        body = _json_body(request)
        if body.get("consent") is not True:
            raise ApiProblem("consent 必须为 true。", code="consent_required")
        companion = body.get("companion")
        if companion not in COMPANIONS:
            raise ApiProblem("companion 不是有效选项。", code="invalid_companion")
        key = _session_key(request, create=True)
        session = VRSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=key,
            consent=True,
            companion=companion,
        )
        return JsonResponse(_session_json(session), status=201)
    except ApiProblem as problem:
        return _error(problem)


@require_GET
def session_detail(request, session_id):
    try:
        return JsonResponse(_session_json(_owned_session(request, session_id)))
    except ApiProblem as problem:
        return _error(problem)


@require_http_methods(["POST"])
@csrf_protect
def assessment(request, session_id):
    try:
        session = _owned_session(request, session_id)
        body = _json_body(request)
        stage = body.get("stage")
        if stage not in {"before", "after"}:
            raise ApiProblem("stage 必须是 before 或 after。", code="invalid_stage")
        responses = body.get("responses")
        if not isinstance(responses, list):
            raise ApiProblem("responses 必须是数组。", code="invalid_responses")
        previous = session.before if stage == "before" else session.after
        value = _assessment_with_questionnaire(stage, responses, previous)
        if stage == "before":
            session.before = value
        else:
            session.after = value
        _invalidate_analysis(session)
        session.save()
        return JsonResponse(value)
    except ApiProblem as problem:
        return _error(problem)


@require_http_methods(["POST"])
@csrf_protect
def recommendation(request, session_id):
    try:
        session = _owned_session(request, session_id)
        plan = _make_plan(session, _json_body(request))
        return JsonResponse(plan)
    except ApiProblem as problem:
        return _error(problem)


@require_http_methods(["POST"])
@csrf_protect
def experience(request, session_id):
    try:
        session = _owned_session(request, session_id)
        body = _json_body(request)
        event = body.get("event")
        if event not in {"start", "complete", "abandon"}:
            raise ApiProblem("event 不是有效选项。", code="invalid_event")
        if not session.before or not session.plan:
            raise ApiProblem("体验必须在前测和推荐之后开始。", code="plan_required")
        plan = session.plan
        for field in ("goal", "instrument", "tone", "soundscape", "videoId"):
            if field in body and body[field] != plan.get(field):
                raise ApiProblem(f"{field} 与已保存的推荐不一致。", code="plan_mismatch")
        duration = body.get("duration", session.duration_seconds or 120)
        elapsed = body.get("elapsedSeconds", session.elapsed_seconds)
        if (
            isinstance(duration, bool)
            or not isinstance(duration, int)
            or duration < 30
            or duration > 3600
            or isinstance(elapsed, bool)
            or not isinstance(elapsed, int)
            or elapsed < 0
            or elapsed > duration
        ):
            raise ApiProblem("体验时长不在允许范围内。", code="invalid_duration")
        if session.duration_seconds is not None and duration != session.duration_seconds:
            raise ApiProblem("体验时长不能在同一会话中改变。", code="duration_mismatch")
        session.duration_seconds = duration
        session.elapsed_seconds = max(session.elapsed_seconds, elapsed)
        now = timezone.now()
        if event == "start":
            if session.status in {"completed", "abandoned"}:
                raise ApiProblem("该体验会话已经结束。", code="session_closed")
            session.status = "started"
            session.started_at = session.started_at or now
        elif event == "complete":
            if not session.started_at and session.status != "completed":
                raise ApiProblem("体验尚未开始。", code="experience_not_started")
            session.status = "completed"
            session.completed_at = session.completed_at or now
        elif event == "abandon":
            if session.status == "completed":
                raise ApiProblem("已完成的体验不能放弃。", code="session_closed")
            session.status = "abandoned"
        session.save()
        return JsonResponse(_session_json(session))
    except ApiProblem as problem:
        return _error(problem)


@require_GET
def report(request, session_id):
    try:
        return JsonResponse(_report_json(_owned_session(request, session_id)))
    except ApiProblem as problem:
        return _error(problem)


@require_http_methods(["POST"])
@csrf_protect
def analysis(request, session_id):
    try:
        session = _owned_session(request, session_id)
        if not session.before or not session.after:
            raise ApiProblem("前测和后测都完成后才能生成报告。", code="assessments_required")
        body = _json_body(request)
        if body.get("retry") is True and session.analysis_status in {"failed", "unavailable"}:
            _invalidate_analysis(session)
            session.save(update_fields=(
                "analysis_revision",
                "analysis_status",
                "analysis_text",
                "analysis_model",
                "analysis_generated_at",
                "updated_at",
            ))
            session.refresh_from_db()
        if session.analysis_status == "pending":
            _call_ai(session)
        return JsonResponse(_report_json(session))
    except ApiProblem as problem:
        return _error(problem)


def _device_authorized(request):
    configured = _configured("VR_DEVICE_API_KEY") or ""
    if not configured:
        raise ApiProblem("设备接口未配置。", status=503, code="device_unavailable")
    header = request.headers.get("Authorization", "")
    supplied = header[7:] if header.startswith("Bearer ") else ""
    if not supplied or not hmac.compare_digest(supplied, configured):
        raise ApiProblem("设备接口认证失败。", status=401, code="device_unauthorized")


@csrf_exempt
@require_http_methods(["POST"])
def device_assessment(request):
    try:
        _device_authorized(request)
        body = _json_body(request)
        session_id = body.get("sessionId")
        stage = body.get("stage")
        if stage not in {"before", "after"}:
            raise ApiProblem("stage 必须是 before 或 after。", code="invalid_stage")
        try:
            session = VRSession.objects.get(id=session_id)
        except (VRSession.DoesNotExist, ValueError, TypeError):
            raise ApiProblem("找不到该体验会话。", status=404, code="not_found")
        previous = session.before if stage == "before" else session.after
        value = _device_assessment(stage, body, previous)
        if stage == "before":
            session.before = value
        else:
            session.after = value
        _invalidate_analysis(session)
        session.save()
        return JsonResponse({"id": str(session.id), "stage": stage, "assessment": value})
    except ApiProblem as problem:
        return _error(problem)
