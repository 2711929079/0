import requests
import logging
import io
import base64
from typing import Optional
from config import config

class SiliconFlowASR:
    """使用硅基流动的TeleSpeechASR模型进行语音识别"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = config.SILICONFLOW_API_KEY
        self.api_url = "https://api.siliconflow.cn/v1/audio/transcriptions"
        self.model = "TeleAI/TeleSpeechASR"
    
    def recognize_from_audio_data(self, audio_data: bytes, file_extension: str = "wav") -> Optional[str]:
        """从音频数据识别文本
        
        Args:
            audio_data: 音频数据（bytes）
            file_extension: 文件扩展名，默认为wav
            
        Returns:
            识别的文本，失败返回None
        """
        try:
            self.logger.info("开始使用硅基流动ASR进行语音识别")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "multipart/form-data"
            }
            
            # 根据文件扩展名设置MIME类型
            mime_types = {
                "wav": "audio/wav",
                "webm": "audio/webm",
                "ogg": "audio/ogg",
                "mp4": "audio/mp4"
            }
            
            mime_type = mime_types.get(file_extension.lower(), "audio/wav")
            
            files = {
                "file": (f"audio.{file_extension}", audio_data, mime_type),
                "model": (None, self.model),
                "response_format": (None, "json"),
                "language": (None, "zh")
            }
            
            self.logger.info(f"调用硅基流动ASR API，模型: {self.model}，格式: {mime_type}")
            
            response = requests.post(self.api_url, headers=headers, files=files, timeout=30)
            
            self.logger.info(f"API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"ASR识别结果: {result}")
                
                if 'text' in result:
                    return result['text']
                elif 'transcription' in result:
                    return result['transcription']
                else:
                    self.logger.error("ASR响应格式不正确")
                    return None
            else:
                self.logger.error(f"硅基流动ASR API调用失败: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"硅基流动ASR网络请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"语音识别过程中发生错误: {e}")
            return None
    
    def recognize_from_audio_file(self, file_path: str) -> Optional[str]:
        """从音频文件识别文本
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            识别的文本，失败返回None
        """
        try:
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            return self.recognize_from_audio_data(audio_data)
        except Exception as e:
            self.logger.error(f"读取音频文件失败: {e}")
            return None
