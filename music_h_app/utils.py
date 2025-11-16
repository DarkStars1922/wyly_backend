import datetime
import uuid
import torch
import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import numpy as np
import io
import os
import time
from dotenv import load_dotenv
from music_h import settings
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
import threading
import requests
from requests.exceptions import RequestException
import base64

load_dotenv()

#os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 加载预训练模型
MODEL_NAME = os.getenv('AUDIOCRAFT_MODEL', 'facebook/musicgen-small')
MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', './model_cache')


class ProgressTracker:
    """进度跟踪器，用于跟踪音乐生成进度"""
    
    def __init__(self):
        self.progress = {}
        self.lock = threading.Lock()
    
    def create_task(self, task_id):
        """创建新任务"""
        with self.lock:
            self.progress[task_id] = {
                'status': 'initializing',
                'progress': 0,
                'message': '初始化...',
                'start_time': time.time()
            }
    
    def update(self, task_id, progress, message, status='processing'):
        """更新任务进度"""
        with self.lock:
            if task_id in self.progress:
                self.progress[task_id].update({
                    'status': status,
                    'progress': progress,
                    'message': message
                })
    
    def complete(self, task_id, file_path):
        """标记任务完成"""
        with self.lock:
            if task_id in self.progress:
                self.progress[task_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': '生成完成',
                    'file_path': file_path
                })
    
    def error(self, task_id, error_message):
        """标记任务错误"""
        with self.lock:
            if task_id in self.progress:
                self.progress[task_id].update({
                    'status': 'error',
                    'message': error_message
                })
    
    def get_progress(self, task_id):
        """获取任务进度"""
        with self.lock:
            return self.progress.get(task_id, None)
    
    def cleanup(self, task_id):
        """清理任务记录"""
        with self.lock:
            if task_id in self.progress:
                del self.progress[task_id]


# 全局进度跟踪器
progress_tracker = ProgressTracker()


class TranslationService:
    """翻译服务类，用于检测语言并翻译中文到英文"""
    
    # 默认启用翻译（可以通过环境变量控制）
    ENABLE_TRANSLATION = os.getenv('ENABLE_TRANSLATION', 'true').lower() == 'true'
    
    # 常用音乐术语中英文映射（快速翻译）
    MUSIC_TERMS = {
        # 情绪/风格
        '欢快': 'cheerful', '快乐': 'happy', '愉悦': 'joyful',
        '浪漫': 'romantic', '温柔': 'gentle', '柔和': 'soft',
        '激昂': 'passionate', '激情': 'passionate', '热情': 'enthusiastic',
        '宁静': 'peaceful', '安静': 'quiet', '平静': 'calm',
        '悲伤': 'sad', '忧郁': 'melancholic', '哀伤': 'sorrowful',
        '神秘': 'mysterious', '梦幻': 'dreamy', '空灵': 'ethereal',
        '史诗': 'epic', '宏大': 'grand', '壮丽': 'magnificent',
        '轻松': 'relaxing', '舒缓': 'soothing', '放松': 'relaxed',
        '活泼': 'lively', '欢乐': 'cheerful', '明快': 'bright',
        '电子': 'electronic', '古典': 'classical', '现代': 'modern',
        
        # 乐器
        '钢琴': 'piano', '吉他': 'guitar', '小提琴': 'violin',
        '大提琴': 'cello', '鼓': 'drums', '贝斯': 'bass',
        '长笛': 'flute', '萨克斯': 'saxophone', '小号': 'trumpet',
        '管弦乐': 'orchestral', '交响乐': 'symphonic', '弦乐': 'strings',
        '打击乐': 'percussion', '合成器': 'synthesizer', '电子琴': 'keyboard',
        
        # 风格/类型
        '爵士': 'jazz', '摇滚': 'rock', '流行': 'pop',
        '古典': 'classical', '民谣': 'folk', '蓝调': 'blues',
        '嘻哈': 'hip-hop', '说唱': 'rap', '雷鬼': 'reggae',
        '舞曲': 'dance', '电音': 'electronic', '环境': 'ambient',
        '冥想': 'meditation', '新世纪': 'new age',
        
        # 其他描述
        '旋律': 'melody', '节奏': 'rhythm', '和声': 'harmony',
        '独奏': 'solo', '伴奏': 'accompaniment', '背景': 'background',
        '强烈': 'strong', '轻柔': 'soft', '缓慢': 'slow',
        '快速': 'fast', '中等': 'moderate', '优美': 'beautiful',
        '音乐': 'music', '曲子': 'music', '歌曲': 'song',
    }
    
    @staticmethod
    def detect_language(text):
        """检测文本语言"""
        try:
            # 简单检测：如果包含中文字符，认为是中文
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                return 'zh'
            return 'en'
        except Exception:
            return 'en'
    
    @staticmethod
    def quick_translate(text):
        """快速翻译：使用词典映射"""
        words = []
        i = 0
        text_len = len(text)
        
        while i < text_len:
            # 尝试匹配最长的词组（从4个字符开始）
            matched = False
            for length in range(4, 0, -1):
                if i + length <= text_len:
                    word = text[i:i+length]
                    if word in TranslationService.MUSIC_TERMS:
                        words.append(TranslationService.MUSIC_TERMS[word])
                        i += length
                        matched = True
                        break
            
            if not matched:
                # 如果是中文标点或空格，跳过
                if text[i] in '，。、！？；：""''（）《》的地得了着':
                    i += 1
                # 如果是英文或数字，保留
                elif text[i].isascii():
                    words.append(text[i])
                    i += 1
                else:
                    i += 1
        
        # 组合翻译结果
        result = ' '.join(words).strip()
        return result if result else text
    
    @staticmethod
    def translate_to_english(text, timeout=30):
        """将文本翻译为英文，优先使用在线翻译，超时后使用快速翻译"""
        
        # 如果禁用翻译，直接返回原文
        if not TranslationService.ENABLE_TRANSLATION:
            print(f"ℹ️  翻译功能已禁用，使用原文: {text}")
            return text, False
        
        try:
            # 快速语言检测
            lang = TranslationService.detect_language(text)
            
            # 如果是英文，直接返回
            if lang == 'en':
                print(f"✓ 检测到英文，无需翻译")
                return text, False
            
            print(f"🌐 检测到中文: {text}")
            
            # 方案1: 在线翻译（优先，质量高）
            print(f"   尝试在线翻译（{timeout}秒超时）...")
            try:
                from deep_translator import GoogleTranslator
                import threading
                
                result_container = {'result': None, 'error': None}
                
                def translate_worker():
                    try:
                        translator = GoogleTranslator(source='auto', target='en')
                        result_container['result'] = translator.translate(text)
                    except Exception as e:
                        result_container['error'] = e
                
                thread = threading.Thread(target=translate_worker)
                thread.daemon = True
                thread.start()
                thread.join(timeout=timeout)
                
                # 检查在线翻译结果
                if not thread.is_alive() and result_container['result']:
                    translated_text = result_container['result']
                    print(f"✅ 在线翻译成功: {translated_text}")
                    return translated_text, True
                
                # 在线翻译失败或超时，使用快速翻译
                if thread.is_alive():
                    print(f"⏱️  在线翻译超时（{timeout}秒）")
                elif result_container['error']:
                    print(f"⚠️  在线翻译出错: {str(result_container['error'])[:50]}")
                else:
                    print(f"⚠️  在线翻译返回空结果")
                
            except Exception as e:
                print(f"⚠️  在线翻译异常: {str(e)[:50]}")
            
            # 方案2: 快速翻译（备选，秒级响应）
            print(f"   使用快速翻译（词典映射）...")
            quick_result = TranslationService.quick_translate(text)
            
            if quick_result and quick_result != text and len(quick_result) > 2:
                print(f"✅ 快速翻译结果: {quick_result}")
                return quick_result, True
            else:
                print(f"⚠️  快速翻译无法完整翻译，使用原文")
                return text, False
                
        except Exception as e:
            print(f"⚠️  翻译失败: {str(e)[:100]}")
            print(f"ℹ️  使用原文: {text}")
            return text, False


class MusicGenerator:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MusicGenerator, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance
    
    def _initialize_model(self):
        print(f"Loading {MODEL_NAME} model...")
        start_time = time.time()

        self.model = MusicGen.get_pretrained(
            MODEL_NAME, 
            device='cuda' if torch.cuda.is_available() else 'cpu',
        )
        
        # 设置生成参数
        self.model.set_generation_params(
            use_sampling=True,
            top_k=250,
            top_p=0.0,
            temperature=1.0,
            duration=30,  # 默认时长
            cfg_coef=3.0
        )
        
        print(f"Model loaded in {time.time() - start_time:.2f} seconds")
    
    def get_audio_save_path(subfolder="generated_music", extension="wav"):
        """生成唯一的音频文件保存路径"""
        # 创建按日期组织的目录结构
        today = datetime.datetime.now().strftime("%Y/%m/%d")
        save_dir = os.path.join(settings.MEDIA_ROOT, subfolder, today)
    
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)
    
        # 生成唯一文件名
        filename = f"musicgen_{uuid.uuid4().hex[:8]}.{extension}"
    
        # 返回完整路径
        return os.path.join(save_dir, filename)

    def _extend_audio_to_minutes(self, audio_tensor, sample_rate, requested_duration_seconds):
        """将生成的短音频扩展为指定分钟数的音频"""
        # 目标时长（秒）= 请求秒数 * 60
        target_duration_seconds = max(requested_duration_seconds * 60, requested_duration_seconds)
        target_samples = int(sample_rate * target_duration_seconds)

        if audio_tensor.dim() == 1:
            audio_tensor = audio_tensor.unsqueeze(0)  # [1, samples]

        channels, original_samples = audio_tensor.shape

        if target_samples <= original_samples:
            return audio_tensor[:, :target_samples]

        repeats = target_samples // original_samples
        remainder = target_samples % original_samples

        repeated = audio_tensor.repeat(1, repeats)
        if remainder > 0:
            repeated = torch.cat([repeated, audio_tensor[:, :remainder]], dim=1)

        return repeated[:, :target_samples]

    def generate_music(self, prompt, duration=30, format='mp3', task_id=None):
        try:
            print(f"\n{'='*60}")
            print(f"🎵 MusicGenerator.generate_music() 开始")
            print(f"{'='*60}")
            print(f"📝 提示词: {prompt}")
            print(f"⏱️  请求时长: {duration}秒 (将扩展为 {duration} 分钟音频)")
            print(f"🎼 格式: {format}")
            print(f"🆔 任务ID: {task_id}")
            
            # 更新进度：开始翻译
            if task_id:
                progress_tracker.update(task_id, 5, '准备生成参数...')
            
            # 生成音乐
            start_time = time.time()
            print(f"\n🔧 设置生成参数...")
            self.model.set_generation_params(duration=duration)
            
            if task_id:
                progress_tracker.update(task_id, 10, '模型准备就绪，开始生成音频...')
            
            print(f"🚀 开始生成音频...")
            print(f"⚙️  使用设备: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
            
            # 生成音频（这是最耗时的部分）
            if task_id:
                progress_tracker.update(task_id, 15, '正在生成音乐（这可能需要一些时间）...')
            
            wav = self.model.generate([prompt], progress=True)
            
            if task_id:
                progress_tracker.update(task_id, 80, '音频生成完成，正在保存文件...')
            
            print(f"✅ 音频生成完成")
            
            # 创建按日期组织的目录结构
            today = datetime.datetime.now().strftime("%Y/%m/%d")
            subfolder="generated_music"
            save_dir = os.path.join(settings.MEDIA_ROOT, subfolder, today)
            
            # 确保目录存在
            print(f"\n📁 创建目录: {save_dir}")
            os.makedirs(save_dir, exist_ok=True)
            
            if task_id:
                progress_tracker.update(task_id, 85, '准备保存音频文件...')
            
            # 生成唯一文件名
            extension="wav"
            unique_id = uuid.uuid4().hex[:8]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"musicgen_{timestamp}_{unique_id}"
            save_path = os.path.join(save_dir, filename)
            
            print(f"📝 文件名: {filename}")
            print(f"💾 保存路径: {save_path}")
            
            # 转换为字节流
            sample_rate = self.model.sample_rate
            print(f"🎵 采样率: {sample_rate}Hz")

            print(f"\n🧩 扩展音频至 {duration} 分钟...")
            extended_audio = self._extend_audio_to_minutes(wav[0].cpu(), sample_rate, duration)
            final_duration_seconds = extended_audio.shape[-1] / sample_rate
            print(f"🕒 最终音频时长: {final_duration_seconds/60:.2f} 分钟")
            
            print(f"\n💾 开始保存音频文件...")
            
            if task_id:
                progress_tracker.update(task_id, 90, f'正在保存 {format.upper()} 文件...')
            
            if format == 'wav':
                print(f"📄 格式: WAV")
                audio_write(save_path, extended_audio, sample_rate, format='wav')
                file_path = save_path + ".wav"
                filename += '.wav'
                content_type = 'audio/wav'
                print(f"✅ WAV 文件保存成功")
            else:
                print(f"📄 格式: MP3")
                audio_write(
                    save_path, 
                    extended_audio, 
                    sample_rate, 
                    format='mp3',
                )
                file_path = save_path + ".mp3"
                filename += '.mp3'
                content_type = 'audio/mpeg'
                print(f"✅ MP3 文件保存成功")

            if task_id:
                progress_tracker.update(task_id, 95, '文件保存完成，最后处理...')
            
            generation_time = time.time() - start_time
            print(f"\n⏱️  总耗时: {generation_time:.2f}秒")
            print(f"📊 生成速度: {duration/generation_time:.2f}x 实时")
            print(f"✅ 完整路径: {file_path}")
            
            audio_data = extended_audio.float()
            
            if task_id:
                progress_tracker.complete(task_id, file_path)
            
            print(f"{'='*60}")
            print(f"✅ MusicGenerator.generate_music() 完成")
            print(f"{'='*60}\n")
            
            return file_path, filename, content_type, audio_data, sample_rate
        except Exception as e:
            print(f"\n❌ MusicGenerator 错误: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            
            if task_id:
                progress_tracker.error(task_id, str(e))
            
            raise


class VideoGenerationError(Exception):
    """Raised when video generation fails."""


class VideoGenerator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VideoGenerator, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance

    def _initialize_client(self):
        self.model_id = os.getenv('VIDEO_GENERATOR_MODEL', 'damo-vilab/text-to-video-ms-1.7b')
        api_override = os.getenv('VIDEO_GENERATOR_API_URL')
        self.api_url = api_override or f"https://api-inference.huggingface.co/models/{self.model_id}"
        self.api_token = os.getenv('HUGGINGFACE_API_TOKEN')
        try:
            self.timeout = int(os.getenv('VIDEO_GENERATION_TIMEOUT', '180'))
        except ValueError:
            self.timeout = 180
        try:
            self.max_attempts = int(os.getenv('VIDEO_GENERATION_MAX_ATTEMPTS', '5'))
        except ValueError:
            self.max_attempts = 5
        try:
            self.max_frames = int(os.getenv('VIDEO_GENERATOR_MAX_FRAMES', '48'))
        except ValueError:
            self.max_frames = 48
        try:
            self.default_fps = int(os.getenv('VIDEO_GENERATOR_DEFAULT_FPS', '8'))
        except ValueError:
            self.default_fps = 8

    def _get_headers(self):
        if not self.api_token:
            raise VideoGenerationError('HUGGINGFACE_API_TOKEN 环境变量未配置，无法调用 HuggingFace 接口')
        return {
            'Authorization': f'Bearer {self.api_token}'
        }

    def _resolve_resolution(self, resolution):
        if isinstance(resolution, (list, tuple)) and len(resolution) == 2:
            return int(resolution[0]), int(resolution[1])
        if isinstance(resolution, str) and 'x' in resolution:
            width, height = resolution.lower().split('x', 1)
            return int(width), int(height)
        return 512, 512

    def _save_video_file(self, video_bytes, extension='mp4'):
        today = datetime.datetime.now().strftime('%Y/%m/%d')
        subfolder = 'generated_videos'
        save_dir = os.path.join(settings.MEDIA_ROOT, subfolder, today)
        os.makedirs(save_dir, exist_ok=True)

        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'videogen_{timestamp}_{unique_id}.{extension}'
        file_path = os.path.join(save_dir, filename)

        with open(file_path, 'wb') as video_file:
            video_file.write(video_bytes)

        content_type = 'video/mp4'
        if extension == 'gif':
            content_type = 'image/gif'
        elif extension == 'webm':
            content_type = 'video/webm'

        return file_path, filename, content_type

    def _decode_payload(self, response, content_type):
        if 'application/json' in content_type.lower():
            data = response.json()
            error_message = data.get('error') if isinstance(data, dict) else None
            if error_message:
                raise VideoGenerationError(error_message)
            video_payload = data.get('video') or data.get('generated_video')
            if video_payload:
                try:
                    return base64.b64decode(video_payload)
                except (ValueError, TypeError) as exc:
                    raise VideoGenerationError('无法解析 HuggingFace 返回的视频数据') from exc
            raise VideoGenerationError('未从 HuggingFace 返回中获取到视频数据')
        return response.content

    def generate_video(self, prompt, duration=4, fps=None, resolution='512x512', task_id=None):
        if task_id:
            progress_tracker.update(task_id, 5, '正在调用视频生成模型...')

        fps = fps or self.default_fps
        fps = max(4, min(fps, 12))

        num_frames = fps * max(duration, 1)
        num_frames = max(8, min(num_frames, self.max_frames))

        width, height = self._resolve_resolution(resolution)

        payload = {
            'inputs': prompt,
            'parameters': {
                'num_frames': int(num_frames),
                'fps': int(fps),
                'width': int(width),
                'height': int(height)
            }
        }

        attempts = 0
        wait_time = 5

        while attempts < self.max_attempts:
            attempts += 1

            try:
                response = requests.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout
                )
            except RequestException as exc:
                if attempts >= self.max_attempts:
                    raise VideoGenerationError(f'视频生成请求失败: {exc}') from exc
                time.sleep(wait_time)
                continue

            content_type = response.headers.get('content-type', '')

            if response.status_code == 200:
                video_bytes = self._decode_payload(response, content_type or '')
                extension = 'mp4'
                if 'gif' in content_type.lower():
                    extension = 'gif'
                elif 'webm' in content_type.lower():
                    extension = 'webm'

                file_path, filename, final_content_type = self._save_video_file(video_bytes, extension)

                if task_id:
                    progress_tracker.complete(task_id, file_path)

                return file_path, filename, final_content_type

            if response.status_code == 503:
                try:
                    data = response.json()
                    wait_time = max(5, min(30, int(data.get('estimated_time', wait_time))))
                except ValueError:
                    wait_time = min(wait_time * 2, 30)

                if task_id:
                    progress_tracker.update(task_id, 10, '模型加载中，请稍候...')

                time.sleep(wait_time)
                continue

            try:
                error_payload = response.json()
                error_message = error_payload.get('error') if isinstance(error_payload, dict) else response.text
            except ValueError:
                error_message = response.text or f'HTTP {response.status_code}'

            raise VideoGenerationError(f'视频生成失败: {error_message}')

        raise VideoGenerationError('多次重试后仍未生成视频，请稍后再试')