from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..utils import MusicGenerator
from ..serializers import MusicGenerationSerializer
import logging

logger = logging.getLogger(__name__)

class GenerateMusicView(APIView):
    generator = MusicGenerator()
    
    def post(self, request):
        serializer = MusicGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        prompt = data['prompt']
        duration = min(data.get('duration', 30), 120)  # 限制最大120秒
        format = data.get('format', 'mp3')
        
        try:
            audio_path, content_type = self.generator.generate_music(
                prompt, 
                duration=duration,
                format=format
            )
            
            # 构建响应
            filename = f"generated_music_{hash(prompt)}.{format}"
            
            return Response({
                "file_path":audio_path,
                }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Music generation error: {str(e)}")
            return Response(
                {"error": "Music generation failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )