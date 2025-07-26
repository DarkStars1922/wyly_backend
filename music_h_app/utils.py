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

load_dotenv()

#os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 加载预训练模型
MODEL_NAME = os.getenv('AUDIOCRAFT_MODEL', 'facebook/musicgen-small')
MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', './model_cache')

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

    def generate_music(self, prompt, duration=30, format='mp3'):
        try:
            # 生成音乐
            start_time = time.time()
            self.model.set_generation_params(duration=duration)
            wav = self.model.generate([prompt], progress=True)
            # 创建按日期组织的目录结构
            today = datetime.datetime.now().strftime("%Y/%m/%d")
            subfolder="generated_music"
            save_dir = os.path.join(settings.MEDIA_ROOT, subfolder, today)
            # 确保目录存在
            os.makedirs(save_dir, exist_ok=True)
            # 生成唯一文件名
            extension="wav"
            unique_id = uuid.uuid4().hex[:8]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"musicgen_{timestamp}_{unique_id}"
            save_path = os.path.join(save_dir, filename)
            # 转换为字节流
            sample_rate = self.model.sample_rate
            
            if format == 'wav':
                audio_write(save_path, wav[0].cpu(), sample_rate, format='wav')
                file_path = save_path + ".wav"
                filename += '.wav'
                content_type = 'audio/wav'
            else:
                # MP3格式需要额外处理
                audio_write(
                    save_path, 
                    wav[0].cpu(), 
                    sample_rate, 
                    format='mp3',
                )
                file_path = save_path + ".mp3"
                filename += '.mp3'
                content_type = 'audio/mpeg'

            generation_time = time.time() - start_time
            print(f"Generated {duration}s audio in {generation_time:.2f} seconds")
            audio_data = wav[0].cpu().float()
            return file_path,filename, content_type,audio_data,sample_rate
        except Exception as e:
            print(f"Generation failed: {str(e)}")
            raise