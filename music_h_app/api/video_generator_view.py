import os
import uuid

from django.http import FileResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status

from ..serializers import VideoGenerationSerializer
from ..utils import (
    VideoGenerator,
    VideoGenerationError,
    TranslationService,
    progress_tracker,
)


class GenerateVideoView(APIView):
    generator = VideoGenerator()
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/video_creation.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        serializer = VideoGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        prompt = data['prompt']
        duration = data.get('duration', 4)
        fps = data.get('fps', 8)
        resolution = data.get('resolution', '512x512')

        task_id = str(uuid.uuid4())
        progress_tracker.create_task(task_id)
        progress_tracker.update(task_id, 2, '正在准备生成参数...')

        try:
            translated_prompt, was_translated = TranslationService.translate_to_english(prompt)
            progress_tracker.update(task_id, 15, '正在生成视频，请稍候...')

            video_path, filename, content_type = self.generator.generate_video(
                translated_prompt,
                duration=duration,
                fps=fps,
                resolution=resolution,
                task_id=task_id
            )

            if not os.path.exists(video_path):
                progress_tracker.error(task_id, '生成的视频文件缺失')
                return Response({'error': 'Video file not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            response = FileResponse(open(video_path, 'rb'), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Task-Id'] = task_id
            response['X-Original-Prompt'] = prompt
            response['X-Translated-Prompt'] = translated_prompt
            response['X-Was-Translated'] = str(was_translated).lower()
            response['X-Video-Duration'] = str(duration)
            response['X-Video-Fps'] = str(fps)
            response['X-Video-Resolution'] = resolution

            progress_tracker.complete(task_id, video_path)
            return response

        except VideoGenerationError as exc:
            progress_tracker.error(task_id, str(exc))
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as exc:
            progress_tracker.error(task_id, str(exc))
            return Response(
                {'error': 'Video generation failed', 'details': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            progress_tracker.cleanup(task_id)
