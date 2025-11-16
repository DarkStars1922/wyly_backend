import os
import uuid
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from rest_framework import status
from ..utils import MusicGenerator, TranslationService, progress_tracker
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
        print("="*80)
        print("🎵 音乐生成请求开始")
        print("="*80)
        
        serializer = MusicGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            print(f"❌ 验证失败: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        original_prompt = data['prompt']
        duration = min(data.get('duration', 30), 120)  # 限制最大120秒
        format = data.get('format', 'mp3')
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        print(f"🆔 任务ID: {task_id}")
        print(f"📝 原始提示词: {original_prompt}")
        print(f"⏱️  时长: {duration}秒")
        print(f"🎼 格式: {format}")
        
        try:
            # 创建进度跟踪
            progress_tracker.create_task(task_id)
            progress_tracker.update(task_id, 2, '正在翻译提示词...')
            
            # 翻译提示词为英文
            print("\n🌐 开始翻译...")
            translated_prompt, was_translated = TranslationService.translate_to_english(original_prompt)
            
            if was_translated:
                print(f"✅ 翻译成功: {original_prompt} -> {translated_prompt}")
                logger.info(f"Translated prompt from '{original_prompt}' to '{translated_prompt}'")
            else:
                print(f"ℹ️  无需翻译，直接使用: {translated_prompt}")
            
            # 使用翻译后的英文提示词生成音乐
            print("\n🎹 开始生成音乐...")
            print(f"🔊 使用提示词: {translated_prompt}")
            
            audio_path, filename, content_type, audio_data, sample_rate = self.generator.generate_music(
                translated_prompt,  # 使用翻译后的英文提示词
                duration=duration,
                format=format,
                task_id=task_id  # 传递任务ID以便跟踪进度
            )
            
            print(f"✅ 音乐生成成功!")
            print(f"📁 文件路径: {audio_path}")
            print(f"📄 文件名: {filename}")
            print(f"🎵 采样率: {sample_rate}Hz")
            
            # 构建响应
            if not os.path.exists(audio_path):
                print(f"❌ 错误: 音频文件不存在: {audio_path}")
                return Response({"error": "Audio file not found"}, status=404)
            
            audio_byte = open(audio_path, 'rb')
            print(f"✅ 文件已打开，准备返回")

            # 返回文件流响应
            response = FileResponse(
                audio_byte,
                content_type=content_type
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Task-Id'] = task_id
            response['X-Audio-Duration'] = str(duration * 60)
            # 添加翻译信息到响应头
            response['X-Original-Prompt'] = original_prompt
            response['X-Translated-Prompt'] = translated_prompt
            response['X-Was-Translated'] = str(was_translated).lower()
            
            print("="*80)
            print("✅ 请求处理完成，返回音频文件")
            print("="*80)
            
            # 清理进度记录
            progress_tracker.cleanup(task_id)
            
            return response
            
        except Exception as e:
            print(f"\n❌ 错误发生: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            import traceback
            print("错误堆栈:")
            traceback.print_exc()
            print("="*80)
            
            if 'task_id' in locals():
                progress_tracker.error(task_id, str(e))
            
            logger.error(f"Music generation error: {str(e)}")
            return Response(
                {"error": "Music generation failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProgressView(APIView):
    """查询音乐生成进度"""
    
    def get(self, request, task_id):
        """获取指定任务的进度"""
        progress = progress_tracker.get_progress(task_id)
        
        if progress is None:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(progress)