from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.templatetags.static import static
from django.views import View


DEFAULT_PHOTO_DIR = Path("graduation_wall/defaults")
DEFAULT_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

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


def _default_photo_names():
    candidates = []
    for root in getattr(settings, "STATICFILES_DIRS", []):
        candidates.append(Path(root) / DEFAULT_PHOTO_DIR)
    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        candidates.append(Path(static_root) / DEFAULT_PHOTO_DIR)

    names = []
    seen = set()
    for directory in candidates:
        if not directory.exists():
            continue
        for photo in sorted(directory.iterdir()):
            if not photo.is_file() or photo.suffix.lower() not in DEFAULT_PHOTO_EXTENSIONS:
                continue
            if photo.name in seen:
                continue
            seen.add(photo.name)
            names.append(photo.name)
    return names


def build_graduation_wall_config():
    default_photos = [
        static(f"{DEFAULT_PHOTO_DIR.as_posix()}/{name}")
        for name in _default_photo_names()
    ]
    return {
        "copy": GRADUATION_WALL_COPY,
        "sections": GRADUATION_WALL_SECTIONS,
        "captions": GRADUATION_WALL_CAPTIONS,
        "default_photos": default_photos,
        "photo_count": len(default_photos),
        "upload_enabled": True,
        "poster_enabled": True,
    }


class GraduationWallConfigAPIView(View):
    def get(self, request):
        return JsonResponse(build_graduation_wall_config())
