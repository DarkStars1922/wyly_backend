import datetime
import uuid
import io
import os
import time
import json
from dotenv import load_dotenv
from django.conf import settings
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
import threading
import requests
from requests.exceptions import RequestException
import base64
import logging

logger = logging.getLogger(__name__)

load_dotenv()


class ProgressTracker:
    def __init__(self):
        self.progress = {}
        self.lock = threading.Lock()
        default_dir = os.path.join(str(settings.BASE_DIR), 'tmp', 'progress')
        self.progress_dir = os.getenv('PROGRESS_TRACKER_DIR', default_dir)
        os.makedirs(self.progress_dir, exist_ok=True)

    def _task_path(self, task_id):
        safe_task_id = ''.join(
            c for c in str(task_id) if c.isalnum() or c in ('-', '_')
        )[:128]
        if not safe_task_id:
            safe_task_id = 'invalid'
        return os.path.join(self.progress_dir, f'{safe_task_id}.json')

    def _save(self, task_id, data):
        path = self._task_path(task_id)
        tmp_path = f'{path}.{os.getpid()}.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp_path, path)

    def _load(self, task_id):
        path = self._task_path(task_id)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None

    def _cleanup_old_files(self, max_age=86400):
        now = time.time()
        try:
            for name in os.listdir(self.progress_dir):
                if not name.endswith('.json'):
                    continue
                path = os.path.join(self.progress_dir, name)
                if now - os.path.getmtime(path) > max_age:
                    os.remove(path)
        except OSError:
            logger.warning('Failed to cleanup progress files', exc_info=True)
    
    def create_task(self, task_id):
        data = {
            'status': 'initializing',
            'progress': 0,
            'message': '初始化...',
            'start_time': time.time()
        }
        with self.lock:
            self.progress[task_id] = data
            self._save(task_id, data)
        self._cleanup_old_files()
    
    def update(self, task_id, progress, message, status='processing'):
        with self.lock:
            data = self.progress.get(task_id) or self._load(task_id)
            if data is None:
                return

            try:
                next_progress = int(float(progress))
            except (TypeError, ValueError):
                next_progress = int(data.get('progress') or 0)
            next_progress = max(0, min(100, next_progress))

            current_progress = int(data.get('progress') or 0)
            current_status = data.get('status') or 'processing'
            if status == current_status == 'processing' and next_progress < current_progress:
                # Multiple workers/callbacks can report slightly older stages; never move the UI backwards.
                next_progress = current_progress
                message = data.get('message') or message

            data.update({
                'status': status,
                'progress': next_progress,
                'message': message
            })
            self.progress[task_id] = data
            self._save(task_id, data)
    
    def complete(self, task_id, file_path, file_url=None, **extra):
        with self.lock:
            data = self.progress.get(task_id) or self._load(task_id)
            if data is None:
                return
            entry = {
                'status': 'completed',
                'progress': 100,
                'message': '生成完成',
                'file_path': file_path,
            }
            if file_url:
                entry['file_url'] = file_url
            entry.update(extra)
            data.update(entry)
            self.progress[task_id] = data
            self._save(task_id, data)
    
    def error(self, task_id, error_message):
        with self.lock:
            data = self.progress.get(task_id) or self._load(task_id)
            if data is None:
                data = {'start_time': time.time()}
            data.update({
                'status': 'error',
                'progress': data.get('progress', 0),
                'message': error_message
            })
            self.progress[task_id] = data
            self._save(task_id, data)
    
    def get_progress(self, task_id):
        with self.lock:
            data = self.progress.get(task_id) or self._load(task_id)
            if data is not None:
                self.progress[task_id] = data
            return data

    def cleanup(self, task_id):
        with self.lock:
            self.progress.pop(task_id, None)
            try:
                os.remove(self._task_path(task_id))
            except FileNotFoundError:
                pass
            except OSError:
                logger.warning('Failed to remove progress file for task %s', task_id, exc_info=True)


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


class MusicGenerationService:
    """
    音乐生成编排器：提示词优化 → Mureka API 调用 → 音频保存
    """

    def __init__(self):
        from .prompt_optimizer import PromptOptimizer

        self.prompt_optimizer = PromptOptimizer()
        self._music_client = None

    @property
    def music_client(self):
        if self._music_client is None:
            from .mureka_client import MurekaMusicClient

            self._music_client = MurekaMusicClient()
        return self._music_client

    def generate(
        self,
        prompt,
        duration=30,
        format="mp3",
        task_id=None,
        tone=None,
        user_group=None,
        emotion=None,
        optimized_prompt=None,
    ):
        """
        完整音乐生成流水线。

        Args:
            prompt: 用户原始描述
            duration: 期望时长（秒），用于提示词优化参考
            format: 'mp3' 或 'wav'
            task_id: 进度跟踪 ID
            tone: 可选五音选择
            user_group: 可选用户群体
            emotion: 可选情绪状态
            optimized_prompt: 前端已优化好的提示词（提供后跳过服务端二次优化）

        Returns:
            tuple: (file_path, filename, content_type, audio_bytes, metadata, file_url)
        """
        if optimized_prompt:
            # 前端已优化，直接使用
            opt_result = {
                "optimized_prompt": optimized_prompt,
                "negative_prompt": "",
                "original_input": prompt,
                "was_optimized": True,
                "optimization_method": "pre-optimized",
            }
            if task_id:
                progress_tracker.update(task_id, 10, "使用前端优化提示词...")
            logger.info("Using pre-optimized prompt from frontend")
        else:
            if task_id:
                progress_tracker.update(task_id, 5, "正在优化提示词...")

            # Step 1: 提示词优化
            opt_result = self.prompt_optimizer.optimize(
                user_input=prompt,
                tone=tone,
                user_group=user_group,
                emotion=emotion,
                duration=duration,
            )
            logger.info(
                "Prompt optimized (method=%s): '%s...' -> '%s...'",
                opt_result["optimization_method"],
                prompt[:60],
                opt_result["optimized_prompt"][:60],
            )

        optimized_prompt_text = opt_result["optimized_prompt"]

        # Mureka 支持中文提示词，直接使用无需翻译
        music_prompt = optimized_prompt_text

        if task_id:
            progress_tracker.update(task_id, 15, "正在提交音乐生成任务...")

        # Step 2: 调用 Mureka API（异步：提交→轮询→下载，在客户端内部完成）
        from .mureka_client import MurekaError

        def _on_progress(pct, msg):
            if task_id:
                progress_tracker.update(task_id, pct, msg)

        try:
            result = self.music_client.generate(
                prompt=music_prompt,
                progress_callback=_on_progress,
            )
        except MurekaError:
            raise
        except Exception as e:
            logger.error("Music generation error: %s", e)
            if task_id:
                progress_tracker.error(task_id, str(e))
            raise

        if task_id:
            progress_tracker.update(task_id, 90, "正在保存音频文件...")

        audio_bytes = result["audio_bytes"]

        if not audio_bytes:
            if task_id:
                progress_tracker.error(task_id, "API 未返回音频数据")
            raise MurekaError(-1, "No audio data", "API 未返回音频数据，请重试")

        # Step 4: 保存到文件
        file_path, filename, content_type, file_url = self._save_audio(audio_bytes, format)

        if task_id:
            progress_tracker.complete(task_id, file_path, file_url)

        metadata = {
            **result["metadata"],
            "optimized_prompt": optimized_prompt_text,
            "original_prompt": prompt,
            "was_optimized": opt_result["was_optimized"],
            "optimization_method": opt_result["optimization_method"],
        }

        return file_path, filename, content_type, audio_bytes, metadata, file_url

    def _save_audio(self, audio_bytes, fmt):
        """保存音频字节到文件，并返回网页可访问的 file_url。"""
        today = datetime.datetime.now().strftime("%Y/%m/%d")
        save_dir = os.path.join(settings.MEDIA_ROOT, "generated_music", today)
        os.makedirs(save_dir, exist_ok=True)

        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = "mp3" if fmt == "mp3" else "wav"
        filename = f"meditation_{timestamp}_{unique_id}.{extension}"
        file_path = os.path.join(save_dir, filename)

        with open(file_path, "wb") as f:
            f.write(audio_bytes)

        file_url = f"{settings.MEDIA_URL}generated_music/{today}/{filename}"

        content_type = "audio/mpeg" if fmt == "mp3" else "audio/wav"
        return file_path, filename, content_type, file_url


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
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
