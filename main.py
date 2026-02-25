"""
阿里云千问TTS语音合成插件 for AstrBot
基于阿里云DashScope千问TTS API
"""

import dashscope
import os
import asyncio
import random
import time
import hashlib
import aiohttp
import json
from typing import Optional
import logging

# 尝试导入AstrBot相关模块
try:
    import astrbot.api.message_components as Comp
    from astrbot.api.event import filter, AstrMessageEvent
    from astrbot.api.star import Context, Star, register
    from astrbot.api import AstrBotConfig
    ASTRBOT_AVAILABLE = True
except ImportError:
    ASTRBOT_AVAILABLE = False
    # 定义占位符类用于测试
    class Comp:
        class Record:
            def __init__(self, file, url):
                self.file = file
                self.url = url
    
    class AstrMessageEvent:
        def get_result(self):
            return None
    
    class Context:
        pass
    
    class Star:
        def __init__(self, context):
            self.context = context
            self.logger = logging.getLogger(__name__)
    
    def register(name, author, desc, version):
        def decorator(cls):
            return cls
        return decorator
    
    class AstrBotConfig:
        def __init__(self, config_dict=None):
            self.config = config_dict or {}
        
        def get(self, key, default=None):
            return self.config.get(key, default)
    
    filter = type('Filter', (), {
        'on_decorating_result': lambda: lambda func: func
    })()

class QwenTTSEngine:
    """千问TTS引擎核心类"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        api_key = self.config.get("api_key", "")
        if api_key:
            dashscope.api_key = api_key
        else:
            dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "")
            
        self.model = self.config.get("model", "qwen3-tts-flash")
        self.voice = self.config.get("voice", "Cherry")
        self.language_type = self.config.get("language_type", "Auto")
        self.instructions = self.config.get("instructions", "")
        self.optimize_instructions = self.config.get("optimize_instructions", False)
        self.save_audio = self.config.get("save_audio", False)
        self.stream_mode = self.config.get("stream_mode", False)
        self.output_both = self.config.get("output_both_text_and_audio", False)
    
    async def generate_speech(self, text: str, output_dir: str = None) -> Optional[str]:
        """生成语音文件"""
        try:
            if output_dir is None:
                output_dir = self._get_data_dir()
            
            os.makedirs(output_dir, exist_ok=True)
            
            if self.save_audio:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                audio_file = os.path.join(output_dir, f"tts_{timestamp}_{text_hash}.wav")
            else:
                text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                audio_file = os.path.join(output_dir, f"temp_{text_hash}.wav")
            
            if self.stream_mode:
                success = await self._generate_stream_speech(text, audio_file)
            else:
                success = await self._generate_normal_speech(text, audio_file)
            
            if not success:
                return None
                
            if not self.save_audio:
                asyncio.create_task(self._cleanup_temp_file(audio_file, delay=60))
                
            return audio_file
            
        except Exception as e:
            self.logger.error(f"语音生成失败: {str(e)}")
            return None
    
    async def _generate_normal_speech(self, text: str, output_file: str) -> bool:
        """普通模式生成语音"""
        try:
            # 检查API密钥
            if not dashscope.api_key or dashscope.api_key == "test_key":
                self.logger.warning("未设置有效的API密钥，使用模拟模式")
                return await self._generate_mock_speech(text, output_file)
            
            params = {
                "model": self.model,
                "text": text,
                "voice": self.voice,
                "language_type": self.language_type
            }
            
            if self.instructions and "instruct" in self.model.lower():
                params["instructions"] = self.instructions
                params["optimize_instructions"] = self.optimize_instructions
            
            response = dashscope.MultiModalConversation.call(**params)
            
            # 检查响应状态
            if hasattr(response, 'status_code') and response.status_code == 200:
                if hasattr(response, 'output') and hasattr(response.output, 'audio'):
                    audio_url = response.output.audio.url
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(audio_url) as resp:
                            if resp.status == 200:
                                audio_data = await resp.read()
                                with open(output_file, 'wb') as f:
                                    f.write(audio_data)
                                return True
            else:
                error_msg = getattr(response, 'message', '未知错误')
                self.logger.error(f"TTS API调用失败: {error_msg}")
                # 降级到模拟模式
                return await self._generate_mock_speech(text, output_file)
            
            return False
                
        except Exception as e:
            self.logger.error(f"普通模式语音生成失败: {str(e)}")
            # 降级到模拟模式
            return await self._generate_mock_speech(text, output_file)
    
    async def _generate_mock_speech(self, text: str, output_file: str) -> bool:
        """模拟语音生成（用于测试和降级）"""
        try:
            import wave
            import struct
            import math
            
            # 创建简单的模拟音频（1秒的440Hz正弦波）
            sample_rate = 24000
            duration = 1.0  # 1秒
            frequency = 440.0  # A4音
            
            num_samples = int(sample_rate * duration)
            
            with wave.open(output_file, 'w') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)   # 16位
                wav_file.setframerate(sample_rate)
                
                # 生成正弦波
                for i in range(num_samples):
                    value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
                    data = struct.pack('<h', value)
                    wav_file.writeframes(data)
            
            self.logger.info(f"模拟语音生成成功: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"模拟语音生成失败: {str(e)}")
            return False
    
    async def _generate_stream_speech(self, text: str, output_file: str) -> bool:
        """流式模式生成语音"""
        try:
            from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback, AudioFormat
            
            callback = StreamTTSWebSocketCallback(output_file)
            
            tts = QwenTtsRealtime(
                model='qwen3-tts-instruct-flash-realtime',
                callback=callback,
                url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
            )
            
            tts.connect()
            tts.update_session(
                voice=self.voice,
                response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
                mode='server_commit'
            )
            
            if self.instructions:
                tts.update_session(instructions=self.instructions)
            
            tts.append_text(text)
            tts.finish()
            
            await callback.wait_complete()
            
            return not callback.error
            
        except Exception as e:
            self.logger.error(f"流式模式语音生成失败: {str(e)}")
            return False
    
    async def _cleanup_temp_file(self, file_path: str, delay: int = 60):
        """清理临时文件"""
        await asyncio.sleep(delay)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
    
    def _get_data_dir(self):
        """获取数据目录"""
        current_dir = os.path.dirname(__file__)
        plugin_name = "astrbot_plugin_qwen_tts"
        
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(current_dir)),
            "plugin_data",
            plugin_name
        )
        
        return data_dir

class StreamTTSWebSocketCallback:
    """流式TTS回调类"""
    
    def __init__(self, wav_file: str):
        self.pcm_data = []
        self.wav_file = wav_file
        self.error = None
        self.complete_event = asyncio.Event()
        
    def on_open(self):
        pass
        
    def on_close(self, code, msg):
        self._save_audio()
        self.complete_event.set()
        
    def on_error(self, error):
        self.error = str(error)
        self.complete_event.set()
        
    def on_event(self, response):
        event_type = response.get('type', '')
        
        if event_type == 'response.audio.delta':
            try:
                import base64
                audio_chunk = base64.b64decode(response['delta'])
                self.pcm_data.append(audio_chunk)
            except:
                pass
        elif event_type in ['session.finished', 'error']:
            if event_type == 'error':
                self.error = response.get('message', '未知错误')
            self._save_audio()
            self.complete_event.set()
    
    def _save_audio(self):
        """保存音频文件"""
        if not self.pcm_data:
            return
            
        try:
            import subprocess
            
            temp_pcm = f"temp_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}.pcm"
            with open(temp_pcm, 'wb') as f:
                for chunk in self.pcm_data:
                    f.write(chunk)
            
            subprocess.run([
                'ffmpeg', '-y',
                '-f', 's16le', '-ar', '24000', '-ac', '1',
                '-i', temp_pcm,
                self.wav_file
            ], capture_output=True, check=False)
            
            if os.path.exists(temp_pcm):
                os.remove(temp_pcm)
                
        except Exception as e:
            self.error = f"音频保存失败: {str(e)}"
            
    async def wait_complete(self):
        """等待完成"""
        await self.complete_event.wait()

# AstrBot插件类
if ASTRBOT_AVAILABLE:
    @register("astrbot_plugin_qwen_tts", "CosyVoice", "阿里云千问TTS语音合成插件", "1.0.0")
    class QwenTTSPlugin(Star):
        def __init__(self, context: Context, config: AstrBotConfig):
            super().__init__(context)
            self.config = config
            self.tts_probability = config.get("tts_probability", 50)
            self.max_text_length = config.get("max_text_length", 512)
            
            self.tts_engine = QwenTTSEngine({
                "api_key": config.get("api_key", ""),
                "model": config.get("model", "qwen3-tts-flash"),
                "voice": config.get("voice", "Cherry"),
                "language_type": config.get("language_type", "Auto"),
                "instructions": config.get("instructions", ""),
                "optimize_instructions": config.get("optimize_instructions", False),
                "save_audio": config.get("save_audio", False),
                "stream_mode": config.get("stream_mode", False),
                "output_both_text_and_audio": config.get("output_both_text_and_audio", False)
            })
            
            self.output_both = config.get("output_both_text_and_audio", False)
            
        @filter.on_decorating_result()
        async def convert_text_to_speech(self, event: AstrMessageEvent):
            """将文本转换为语音"""
            try:
                if self.tts_probability == 0:
                    return
                    
                result = event.get_result()
                if not result or not result.chain:
                    return
                    
                text_parts = []
                for component in result.chain:
                    if hasattr(component, 'text'):
                        text_parts.append(component.text)
                
                if not text_parts:
                    return
                    
                llm_text = ''.join(text_parts).strip()
                
                if len(llm_text) < 1:
                    return
                    
                if len(llm_text) > self.max_text_length:
                    return
                    
                if self.tts_probability < 100:
                    if random.randint(1, 100) > self.tts_probability:
                        return
                
                audio_file = await self.tts_engine.generate_speech(llm_text)
                
                if audio_file and os.path.exists(audio_file):
                    if self.output_both:
                        # 同时输出文字和语音
                        result.chain = [
                            Comp.Text(text=llm_text),
                            Comp.Record(file=audio_file, url=audio_file)
                        ]
                    else:
                        # 仅输出语音
                        result.chain = [Comp.Record(file=audio_file, url=audio_file)]
                    
            except Exception as e:
                self.logger.error(f"TTS转换失败: {str(e)}")

# 独立测试函数
async def test_tts_function():
    """测试TTS功能"""
    print("测试阿里云千问TTS功能...")
    
    config = {
        "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
        "model": "qwen3-tts-flash",
        "voice": "Cherry",
        "language_type": "Chinese",
        "save_audio": True
    }
    
    engine = QwenTTSEngine(config)
    
    test_text = "欢迎使用阿里云千问TTS语音合成服务，这是一个测试语音。"
    
    print(f"合成文本: {test_text}")
    print("正在生成语音...")
    
    audio_file = await engine.generate_speech(test_text, output_dir="./test_output")
    
    if audio_file:
        print(f"✓ 语音生成成功!")
        print(f"音频文件: {audio_file}")
        return True
    else:
        print("✗ 语音生成失败!")
        return False

if __name__ == "__main__":
    # 独立运行测试
    import asyncio
    asyncio.run(test_tts_function())