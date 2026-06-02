import logging

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import status

from .graduation_wall_view import build_graduation_wall_config
from ..prompt_optimizer import PromptOptimizer

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class OptimizePromptView(APIView):
    """AI 提示词优化 API — 供前端按钮独立调用"""
    renderer_classes = [JSONRenderer]

    def post(self, request):
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response({"error": "请输入音乐描述"}, status=status.HTTP_400_BAD_REQUEST)

        tone = request.data.get("tone")
        user_group = request.data.get("user_group")
        emotion = request.data.get("emotion")

        logger.info("Prompt optimization request: prompt='%s'..., tone=%s, group=%s, emotion=%s",
                     prompt[:50], tone, user_group, emotion)

        try:
            optimizer = PromptOptimizer()
            result = optimizer.optimize(
                user_input=prompt,
                tone=tone,
                user_group=user_group,
                emotion=emotion,
            )
        except Exception as e:
            logger.exception("Prompt optimization failed")
            return Response(
                {"error": "提示词优化失败，请重试", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            "optimized_prompt": result["optimized_prompt"],
            "negative_prompt": result.get("negative_prompt"),
            "original_input": result["original_input"],
            "was_optimized": result["was_optimized"],
            "optimization_method": result["optimization_method"],
        })


class HomeAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/index.html'

    def get(self, request):
        return render(
            request,
            self.template_name,
            {'graduation_wall_config': build_graduation_wall_config()},
        )
    
class LyricAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/lyric_creator.html'

    def get(self, request):
        return render(request, self.template_name)
        

class MusicCreationView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/music_generator.html'

    def get(self, request):
        return render(request, self.template_name)


class MeditationMusicView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/meditation_music.html'

    def get(self, request):
        return render(request, self.template_name)


class ShowcaseView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/showcase_page.html'

    def get(self, request):
        return render(request, self.template_name)

