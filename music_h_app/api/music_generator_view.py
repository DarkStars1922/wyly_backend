import os
from django.http import FileResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from rest_framework import status
from ..utils import MusicGenerator
from ..serializers import MusicGenerationSerializer
import logging

logger = logging.getLogger(__name__)

class GenerateMusicView(APIView):
    generator = MusicGenerator()
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/music_generator.html'

    def get(self,request):
        return render(request,'music_h_app/music_generator.html')

    def post(self, request):
        serializer = MusicGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        prompt = data['prompt']
        duration = min(data.get('duration', 30), 120)  # 限制最大120秒
        format = data.get('format', 'mp3')
        
        try:
            audio_path,filename,content_type ,audio_data,sample_rate= self.generator.generate_music(
                prompt, 
                duration=duration,
                format=format
            )
            
            # 构建响应
            if not os.path.exists(audio_path):
                return Response({"error": "Audio file not found"}, status=404)
            audio_byte = open(audio_path, 'rb')

            # 返回文件流响应
            response = FileResponse(
                audio_byte,
                content_type=content_type
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Audio-Duration'] = str(duration)
            return response
            
        except Exception as e:
            logger.error(f"Music generation error: {str(e)}")
            return Response(
                {"error": "Music generation failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )