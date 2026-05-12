import requests
import binascii

# 配置
API_KEY = "sk-cp-lCswKiE82hqQ4U0NdAuZiDvP0_tzK37rfjfFLI47jWKBHVQgYPiHXFTD1kllIaIK2JOKAgxh5Hvo67pLOXLK7PI62zYPYY-UHEqc78UFG7V5hYQzvY-Zuoo"
API_URL = "https://api.minimaxi.com/v1/music_generation"

# ===================== 配置 =====================
PROMPT = "古风，宁静的流水，唯美空灵，中国风纯音乐，古筝，笛子，安静舒缓,60s左右"
LYRICS = "[Inst]"  # 纯音乐标记，不影响曲风
OUTPUT_FILE = "pure_music_final.mp3"
# ==================================================

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 🔥 只有官方文档里的字段，一个多余都没有
data = {
    "model": "music-2.6",
    "prompt": PROMPT,
    "lyrics": LYRICS,
    "is_instrumental": True,  # 纯音乐
    "output_format": "hex",
    "audio_setting": {
        "sample_rate": 44100,
        "bitrate": 256000,
        "format": "mp3"
    }
}

print("正在生成古风纯音乐... 请等待 1~2分钟")

try:
    # 超时设为 180 秒，防止超时
    resp = requests.post(API_URL, headers=headers, json=data, timeout=180)
    result = resp.json()

    if result.get("data") and result["data"].get("audio"):
        audio_hex = result["data"]["audio"]
        music_bytes = binascii.unhexlify(audio_hex)
        
        with open(OUTPUT_FILE, "wb") as f:
            f.write(music_bytes)
            
        print(f"✅ 生成成功！文件：{OUTPUT_FILE}")
        print(f"⏱ 音频时长：{result['data'].get('duration', 0)} 秒")
    else:
        print("❌ API 返回错误：", result)

except Exception as e:
    print("❌ 报错：", e)