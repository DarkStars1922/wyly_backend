from django.http import JsonResponse
from django.views import View


GRADUATION_WALL_COPY = {
    "year": "2026",
    "title": "有你真好",
    "subtitle": "2 0 2 6 毕 业 回 忆 墙",
    "kicker": "CLASS OF 2026",
    "homepage_title": "毕业季限定照片墙",
    "homepage_description": "把合照、教室、操场和没说完的话放进同一片星河，生成一段可互动、可保存的毕业回忆。",
    "poster_school_placeholder": "如：第一中学 · 高三(7)班",
    "poster_blessing": "愿此去前程似锦，再相逢依旧如故。",
    "poster_signature": "致敬 2026 · 致敬每一颗相遇的珍珠",
}

GRADUATION_WALL_SECTIONS = [
    "那些普通却闪光的日子",
    "我们一起走过的走廊和操场",
    "那些没说出口的谢谢",
    "后来才知道，那就是青春",
    "风一来，回忆就都醒了",
    "愿我们都被这个世界温柔以待",
]

GRADUATION_WALL_CAPTIONS = [
    "原来那天的笑，我们一直都记得。",
    "这一刻，被时间好好收藏了起来。",
    "风把那年的声音，又吹了回来。",
    "有些瞬间，后来才懂它的重量。",
    "我们都在这张照片里，刚刚好。",
    "那天没说完的话，就让它留在这张照片里吧。",
]


def build_graduation_wall_config():
    return {
        "copy": GRADUATION_WALL_COPY,
        "sections": GRADUATION_WALL_SECTIONS,
        "captions": GRADUATION_WALL_CAPTIONS,
        "default_photos": [],
        "photo_count": 0,
        "upload_enabled": True,
        "poster_enabled": True,
    }


class GraduationWallConfigAPIView(View):
    def get(self, request):
        return JsonResponse(build_graduation_wall_config())
