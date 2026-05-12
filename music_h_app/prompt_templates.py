"""
五音疗愈冥想音乐 — 提示词模板与约束配置

FIVE_TONE_MAP: 宫商角徵羽 → 乐器/节奏/情绪/负面约束映射
SYSTEM_PROMPT: PromptOptimizer 调用 LLM 时的系统提示词（中文输出）
TEMPLATE_PROMPTS: LLM 不可用时的模板化后备提示词（中文）
"""

# ---------------------------------------------------------------------------
# 五音映射：宫商角徵羽 → 五行/五脏/乐器/BPM/情绪/负面约束
# ---------------------------------------------------------------------------
FIVE_TONE_MAP = {
    "gong": {  # 宫 — 土 — 脾
        "element": "土",
        "organ": "脾",
        "instruments": ["guqin", "xun", "bass drum"],
        "bpm_range": (50, 65),
        "key": "C gong mode",
        "mood": "沉稳厚重，安定滋养，如大地怀抱般温暖包容",
        "negative_prompt": (
            "vocals, rap, lyrics, strong drums, fast tempo, aggressive, "
            "electronic beats, heavy bass, distorted sounds, dissonant, "
            "chaotic percussion, metal, rock, dance, hip-hop"
        ),
    },
    "shang": {  # 商 — 金 — 肺
        "element": "金",
        "organ": "肺",
        "instruments": ["guzheng", "bamboo flute", "chime bells"],
        "bpm_range": (55, 70),
        "key": "D shang mode",
        "mood": "清冽纯净，明净澄澈，如秋风穿过竹林般清爽通透",
        "negative_prompt": (
            "vocals, rap, lyrics, strong drums, fast tempo, aggressive, "
            "electronic beats, heavy bass, distorted sounds, dissonant, "
            "chaotic percussion, metal, rock, dance, hip-hop, harsh timbres"
        ),
    },
    "jue": {  # 角 — 木 — 肝
        "element": "木",
        "organ": "肝",
        "instruments": ["bamboo flute", "xiao", "erhu"],
        "bpm_range": (60, 75),
        "key": "E jue mode",
        "mood": "生发舒展，轻盈向上，如春风拂过新芽般充满生机",
        "negative_prompt": (
            "vocals, rap, lyrics, strong drums, fast tempo, aggressive, "
            "electronic beats, heavy bass, distorted sounds, dissonant, "
            "chaotic percussion, metal, rock, dance, hip-hop, stagnant sounds"
        ),
    },
    "zhi": {  # 徵 — 火 — 心
        "element": "火",
        "organ": "心",
        "instruments": ["guzheng", "pipa", "bamboo flute"],
        "bpm_range": (65, 80),
        "key": "G zhi mode",
        "mood": "温暖明亮，喜悦祥和，如烛光般柔和温暖照亮内心",
        "negative_prompt": (
            "vocals, rap, lyrics, strong drums, fast tempo, aggressive, "
            "electronic beats, heavy bass, distorted sounds, dissonant, "
            "chaotic percussion, metal, rock, dance, hip-hop, cold mechanical sounds"
        ),
    },
    "yu": {  # 羽 — 水 — 肾
        "element": "水",
        "organ": "肾",
        "instruments": ["xun", "xiao", "guqin"],
        "bpm_range": (50, 60),
        "key": "A yu mode",
        "mood": "深邃静谧，如水般流动，月光映在深潭般的宁静致远",
        "negative_prompt": (
            "vocals, rap, lyrics, strong drums, fast tempo, aggressive, "
            "electronic beats, heavy bass, distorted sounds, dissonant, "
            "chaotic percussion, metal, rock, dance, hip-hop, bright piercing sounds"
        ),
    },
}

# ---------------------------------------------------------------------------
# 人群/情绪 → 五音推荐映射
# ---------------------------------------------------------------------------
USER_GROUP_TONE_MAP = {
    "insomnia": "yu",
    "anxiety": "gong",
    "depression": "jue",
    "stress": "shang",
    "autism": "gong",
    "cognitive": "jue",
    "pregnancy": "zhi",
    "elderly": "yu",
}

EMOTION_TONE_MAP = {
    "anger": "shang",
    "anxiety": "gong",
    "depression": "jue",
    "sadness": "yu",
    "stress": "shang",
    "fatigue": "zhi",
    "excitement": "yu",
    "restlessness": "gong",
}

# ---------------------------------------------------------------------------
# LLM 系统提示词（中文，输出中文专业提示词）
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """你是一位擅长用文字描绘音乐意境的诗人。用户会描述他想要什么感觉的音乐，你需要把这段话优化成一段优美的中文意境描述。

## 规则
- 输入是一段大白话，输出是一段优美的意境描述
- 不分条、不列点、不提 BPM/拍子/调式等技术术语
- 融入中国传统乐器（古琴、古筝、埙、竹笛、箫）和自然意象
- 营造禅意、空灵、静谧的冥想氛围
- 60-120 字，像散文诗一样流畅
- 纯器乐方向，不涉及人声歌词

## 示例
输入："最近压力大，想要放松的音乐"
输出：空山新雨后，古琴声如泉水漫过青石，箫音在竹林深处若隐若现，每一次拨弦都像在轻抚紧绷的心弦，让思绪随山风飘远。

只输出优化后的一段话，不要加说明和前缀。"""

# ---------------------------------------------------------------------------
# 模板后备提示词（中文，按五音 + 情绪组合）
# ---------------------------------------------------------------------------
TEMPLATE_PROMPTS = {
    ("gong", "anxiety"): (
        "古琴与埙的声音如大地般沉稳厚重，温暖包容地环绕周身，"
        "每一个悠长的音符都在安抚不安的心神，让人渐渐沉入安定的怀抱"
    ),
    ("gong", "restlessness"): (
        "古琴独奏如大地低语，深沉而安宁，在传统禅堂的空灵氛围中，"
        "乐音缓慢消散，将躁动一一抚平"
    ),
    ("gong", "insomnia"): (
        "古琴配埙的轻柔低吟，摇篮曲般温柔，仿佛被温暖的手托起，"
        "在深夜静谧中失重漂浮，乐句间自然的留白引人入眠"
    ),
    ("shang", "stress"): (
        "古筝与竹笛清冽纯净，如秋日晴空般通透，流水般的旋律洗涤心灵的尘埃，"
        "每一次呼吸都变得轻盈自在"
    ),
    ("shang", "anger"): (
        "古筝配编钟的远响澄澈冷静，清越的音色缓缓消解紧绷的情绪，"
        "柔和混响如清风吹散心头积郁"
    ),
    ("jue", "depression"): (
        "竹笛与二胡如春风拂过新芽，轻盈向上的旋律充满生机，"
        "明亮的音符如晨光穿透阴霾，唤醒心底的希望"
    ),
    ("jue", "fatigue"): (
        "箫与竹笛交叠如翠绿竹林中的清风，清新灵动，攀升式的旋律"
        "如草木向阳而生，为身心注入自然的活力"
    ),
    ("zhi", "sadness"): (
        "古筝与琵琶温暖如烛光，柔和的光晕照亮内心，"
        "祥和的旋律如波浪般轻轻涌动，抚慰每一寸忧伤"
    ),
    ("zhi", "excitement"): (
        "竹笛配轻柔古筝，平静而温暖的音符让心归于安宁，"
        "柔和的乐句缓缓降落，将躁动的喜悦沉淀为内心的宁静"
    ),
    ("yu", "depression"): (
        "埙独奏配箫的回声深邃静谧，如月光洒在幽深的湖面上，"
        "音符从静默中缓缓浮现，带来深沉的安详与慰藉"
    ),
    ("yu", "insomnia"): (
        "古琴与埙如梦似幻，在深水的静止中失重漂浮，"
        "若有若无的旋律以静默为主，引领意识滑入温柔的梦境"
    ),
    ("yu", "anxiety"): (
        "箫声描绘流水意象，连绵不断如清泉涤荡，"
        "洗去紧张与焦虑，留下一片深蓝色的宁静"
    ),
}

# 通用后备提示词（未匹配到具体组合时使用）
DEFAULT_TEMPLATE = (
    "古琴独奏，中国五声音阶营造禅意冥想氛围，"
    "缓慢空灵的乐句在自然混响中延展，空间感的留白让人沉入宁静"
)
