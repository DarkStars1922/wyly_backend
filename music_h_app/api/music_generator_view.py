import os
import uuid
import logging
import threading

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import MusicGenerationSerializer
from ..utils import MusicGenerationService, progress_tracker
from ..mureka_client import MurekaError

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class GenerateMusicView(APIView):
    _service = None

    @property
    def service(self):
        if GenerateMusicView._service is None:
            GenerateMusicView._service = MusicGenerationService()
        return GenerateMusicView._service

    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "music_h_app/music_generator.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        serializer = MusicGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        original_prompt = data["prompt"]
        duration = min(data.get("duration", 30), 120)
        audio_format = data.get("format", "mp3")
        tone = data.get("tone")
        user_group = data.get("user_group")
        emotion = data.get("emotion")
        optimized_prompt = data.get("optimized_prompt")
        client_task_id = data.get("client_task_id")

        task_id = client_task_id or str(uuid.uuid4())
        progress_tracker.create_task(task_id)
        progress_tracker.update(task_id, 2, "任务已创建，正在排队生成...")

        logger.info(
            "Music generation request queued: prompt='%s', duration=%s, format=%s, "
            "tone=%s, group=%s, emotion=%s, pre_optimized=%s, task=%s",
            original_prompt[:80],
            duration,
            audio_format,
            tone,
            user_group,
            emotion,
            bool(optimized_prompt),
            task_id,
        )

        worker = threading.Thread(
            target=self._run_generation,
            name=f"music-generation-{task_id[:8]}",
            kwargs={
                "task_id": task_id,
                "original_prompt": original_prompt,
                "duration": duration,
                "audio_format": audio_format,
                "tone": tone,
                "user_group": user_group,
                "emotion": emotion,
                "optimized_prompt": optimized_prompt,
            },
            daemon=True,
        )
        worker.start()

        return Response(
            {
                "status": "processing",
                "task_id": task_id,
                "message": "音乐生成任务已开始，请通过进度接口查询结果",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    def _run_generation(
        self,
        task_id,
        original_prompt,
        duration,
        audio_format,
        tone=None,
        user_group=None,
        emotion=None,
        optimized_prompt=None,
    ):
        try:
            file_path, filename, content_type, audio_bytes, metadata, file_url = (
                self.service.generate(
                    prompt=original_prompt,
                    duration=duration,
                    format=audio_format,
                    task_id=task_id,
                    tone=tone,
                    user_group=user_group,
                    emotion=emotion,
                    optimized_prompt=optimized_prompt,
                )
            )

            if not os.path.exists(file_path):
                progress_tracker.error(task_id, "音频文件未找到")
                logger.error("Generated music file missing: task=%s file=%s", task_id, file_path)
                return

            logger.info("Music generation success: task=%s, file=%s", task_id, filename)
            progress_tracker.complete(
                task_id,
                file_path,
                file_url,
                audio_url=file_url,
                filename=filename,
                content_type=content_type,
                original_prompt=original_prompt,
                optimized_prompt=metadata.get("optimized_prompt", ""),
                was_optimized=metadata.get("was_optimized", False),
                optimization_method=metadata.get("optimization_method", "none"),
                music_duration_ms=metadata.get("music_duration_ms", 0),
            )

        except MurekaError as e:
            logger.error("Mureka API error [%s]: %s", e.code, e.message)
            progress_tracker.error(task_id, e.user_message)

        except Exception as e:
            logger.exception("Music generation failed")
            progress_tracker.error(task_id, str(e))


class ProgressView(APIView):
    """查询音乐生成进度"""

    def get(self, request, task_id):
        progress = progress_tracker.get_progress(task_id)
        if progress is None:
            return Response({
                "status": "initializing",
                "progress": 0,
                "message": "任务正在排队或初始化...",
            })
        return Response(progress)
