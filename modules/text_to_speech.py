import asyncio
import edge_tts
import requests
from typing import Optional, List
import logging
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import re
from config import config

class TextToSpeech:
    def __init__(self, role: str = "ying"):
        self.logger = logging.getLogger(__name__)
        self.role = role  # 角色标识：ying（荧）或 paimon（派蒙）
        self.voice_name = config.TTS_VOICE_NAME
        self.use_siliconflow = self.voice_name.startswith("speech:")
        # 检查是否使用自定义语音
        self.use_custom_voice = hasattr(config, 'CUSTOM_VOICE_TYPE') and config.CUSTOM_VOICE_TYPE in ['file', 'tts']
        
        # 情绪关键词库
        self.emotion_keywords = {
            # 积极情绪
            'happy': ['开心', '快乐', '高兴', '喜悦', '欢乐', '兴奋', '欣喜', '愉悦', '欢快', '喜笑颜开', '哈哈大笑'],
            'excited': ['激动', '兴奋', '热血', '激情', '澎湃', '振奋', '激昂', '亢奋', '狂热', '热情'],
            'friendly': ['友好', '亲切', '温馨', '温暖', '体贴', '温柔', '和善', '和蔼', '亲切', '友善'],
            
            # 消极情绪
            'sad': ['难过', '悲伤', '伤心', '悲哀', '悲痛', '忧伤', '忧郁', '沮丧', '失落', '低落'],
            'angry': ['愤怒', '生气', '气愤', '暴怒', '恼火', '烦躁', '暴躁', '恼火', '愤愤不平'],
            'fearful': ['害怕', '恐惧', '恐惧', '惊慌', '惊恐', '紧张', '焦虑', '担忧', '忧虑'],
            
            # 中性情绪
            'calm': ['平静', '冷静', '平和', '安宁', '安详', '沉稳', '镇定', '从容', '淡定'],
            'serious': ['严肃', '认真', '庄重', '郑重', '严谨', '庄重', '严肃认真'],
            'curious': ['好奇', '奇怪', '疑惑', '疑问', '纳闷', '费解', '困惑', '不解']
        }
        
        # 语气词和标点符号
        self.exclamation_pattern = r'[!！]+'
        self.question_pattern = r'[?？]+'
        self.laugh_pattern = r'[哈]{2,}|[呵]{2,}|[嘿]{2,}|[嘻]{2,}'
    
    def _filter_special_chars(self, text: str) -> str:
        """过滤特殊符号，只保留中文、英文、数字和基本标点"""
        # 保留中文、英文、数字和基本标点
        filtered_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；：、"\']', '', text)
        return filtered_text
    
    def _analyze_emotion(self, text: str) -> dict:
        """分析文本情绪，返回情绪参数"""
        # 快速情绪分析：优先检查标点符号和语气词，这些最容易识别
        if re.search(self.exclamation_pattern, text):
            return {
                'emotion': 'excited',
                'speed': 1.1,
                'pitch': 1.05
            }
        
        if re.search(self.laugh_pattern, text):
            return {
                'emotion': 'happy',
                'speed': 1.1,
                'pitch': 1.05
            }
        
        if re.search(self.question_pattern, text):
            return {
                'emotion': 'curious',
                'speed': 0.95,
                'pitch': 1.02
            }
        
        # 快速关键词匹配
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    if emotion in ['happy', 'excited']:
                        return {
                            'emotion': emotion,
                            'speed': 1.1,
                            'pitch': 1.05
                        }
                    elif emotion in ['sad', 'fearful']:
                        return {
                            'emotion': emotion,
                            'speed': 0.8,
                            'pitch': 0.95
                        }
                    elif emotion == 'angry':
                        return {
                            'emotion': 'angry',
                            'speed': 1.05,
                            'pitch': 1.1
                        }
                    elif emotion == 'calm':
                        return {
                            'emotion': 'calm',
                            'speed': 0.9,
                            'pitch': 1.0
                        }
        
        # 默认中性情绪
        return {
            'emotion': 'neutral',
            'speed': 1.0,
            'pitch': 1.0
        }
        
    def _split_long_text(self, text: str, max_length: int = 120) -> List[str]:
        """将长文本分割成多个短文本片段，优先在标点符号处断句"""
        self.logger.info(f"开始分割文本，长度: {len(text)}")
        
        segments = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # 计算当前片段的结束位置
            end = min(start + max_length, text_length)
            
            # 如果没有达到文本末尾，尝试在标点符号处断句
            if end < text_length:
                # 优先在句号、问号、感叹号处断句（向后搜索30个字符）
                found_punctuation = False
                for i in range(end, max(start, end - 30), -1):
                    if text[i] in '。！？.!?':
                        end = i + 1
                        found_punctuation = True
                        self.logger.info(f"在位置 {i} 找到断句标点: {text[i]}")
                        break
                
                # 如果没有找到句号等标点，尝试在逗号处断句
                if not found_punctuation:
                    for i in range(end, max(start, end - 30), -1):
                        if text[i] in '，,':
                            end = i + 1
                            found_punctuation = True
                            self.logger.info(f"在位置 {i} 找到逗号断句")
                            break
                
                # 如果还是没找到标点，尝试在分号处断句
                if not found_punctuation:
                    for i in range(end, max(start, end - 30), -1):
                        if text[i] in '；;':
                            end = i + 1
                            found_punctuation = True
                            self.logger.info(f"在位置 {i} 找到分号断句")
                            break
                
                # 如果还是没找到标点，就按原长度分割
                if not found_punctuation:
                    end = min(start + max_length, text_length)
                    self.logger.warning(f"未找到合适标点，强制分割在位置 {end}")
            
            segment = text[start:end]
            if segment.strip():
                segments.append(segment)
                self.logger.info(f"添加片段: '{segment[:30]}...' (长度: {len(segment)})")
            start = end
            
        self.logger.info(f"文本分割完成，共 {len(segments)} 个片段")
        return segments
    
    async def _speak_async(self, text: str) -> bool:
        try:
            self.logger.info(f"正在播放语音: {text[:50]}...")
            
            # 将长文本分割成多个短片段
            text_segments = self._split_long_text(text, max_length=80)
            self.logger.info(f"文本已分割成 {len(text_segments)} 个片段")
            
            # 分析文本情绪
            emotion_params = self._analyze_emotion(text)
            self.logger.info(f"分析到情绪: {emotion_params['emotion']}, 语速: {emotion_params['speed']}, 音调: {emotion_params['pitch']}")
            
            # 确定使用的语音配置
            use_siliconflow = self.use_siliconflow
            voice_name = self.voice_name
            
            # 如果启用自定义语音
            if self.use_custom_voice:
                if config.CUSTOM_VOICE_TYPE == 'tts':
                    # 根据角色选择自定义TTS音色
                    if self.role == 'paimon' and hasattr(config, 'PAIMON_VOICE_ID'):
                        voice_name = config.PAIMON_VOICE_ID
                        self.logger.info(f"使用派蒙自定义TTS音色: {voice_name}")
                    else:
                        voice_name = config.CUSTOM_VOICE_ID
                        self.logger.info(f"使用荧自定义TTS音色: {voice_name}")
                    use_siliconflow = True
                elif config.CUSTOM_VOICE_TYPE == 'file':
                    # 播放固定音频文件
                    self.logger.info(f"使用自定义语音文件: {config.CUSTOM_VOICE_FILE}")
                    try:
                        data, fs = sf.read(config.CUSTOM_VOICE_FILE, dtype='float32')
                        sd.play(data, fs)
                        sd.wait()
                        return True
                    except Exception as e:
                        self.logger.error(f"播放自定义语音文件失败: {e}")
                        # 如果自定义语音失败，回退到默认语音
            
            # 逐个片段合成并播放
            for i, segment in enumerate(text_segments):
                self.logger.info(f"处理第 {i+1}/{len(text_segments)} 个片段: {segment[:30]}...")
                
                # 使用唯一的临时文件名，避免缓存冲突
                import uuid
                temp_file = f"temp_tts_{uuid.uuid4().hex}.wav"
                
                try:
                    if use_siliconflow:
                        # 使用硅基流动API（支持自定义音色和情绪）
                        # 过滤特殊符号，避免合成错误
                        filtered_text = self._filter_special_chars(segment)
                        if filtered_text != segment:
                            self.logger.info(f"原始文本包含特殊符号，已过滤: {segment[:30]}... -> {filtered_text[:30]}...")
                        
                        url = "https://api.siliconflow.cn/v1/audio/speech"
                        headers = {
                            "Authorization": f"Bearer {config.SILICONFLOW_API_KEY}",
                            "Content-Type": "application/json"
                        }
                        data = {
                            "model": "FunAudioLLM/CosyVoice2-0.5B",
                            "input": filtered_text,
                            "voice": voice_name
                        }
                        
                        self.logger.info(f"调用硅基流动语音合成API，使用音色: {voice_name}")
                        self.logger.info(f"请求数据: {data}")
                        
                        # 暂时不使用情绪参数，避免API问题
                        # if emotion_params['emotion'] != 'neutral':
                        #     data['emotion'] = emotion_params['emotion']
                        
                        response = requests.post(url, headers=headers, json=data, timeout=30)
                        self.logger.info(f"API响应状态码: {response.status_code}")
                        
                        if response.status_code == 200:
                            self.logger.info(f"API调用成功，响应内容大小: {len(response.content)} 字节")
                            with open(temp_file, 'wb') as f:
                                f.write(response.content)
                        else:
                            self.logger.error(f"硅基流动API调用失败: {response.status_code} - {response.text}")
                            return False
                    else:
                        # 使用edge-tts（标准语音）
                        communicate = edge_tts.Communicate(segment, self.voice_name)
                        await communicate.save(temp_file)
                    
                    if os.path.exists(temp_file):
                        self.logger.info(f"开始播放音频文件: {temp_file}")
                        data, fs = sf.read(temp_file, dtype='float32')
                        self.logger.info(f"音频数据加载成功，采样率: {fs} Hz, 数据长度: {len(data)}")
                        
                        # 在音频末尾添加静音，确保最后一个字完整播放
                        silence_duration = 0.3  # 秒
                        silence_samples = int(silence_duration * fs)
                        silence = np.zeros(silence_samples, dtype='float32')
                        extended_data = np.concatenate([data, silence])
                        self.logger.info(f"添加 {silence_duration} 秒静音，扩展后数据长度: {len(extended_data)}")
                        
                        sd.play(extended_data, fs)
                        self.logger.info("音频播放中...")
                        sd.wait()
                        self.logger.info(f"第 {i+1} 个音频片段播放完成")
                    else:
                        self.logger.error(f"音频文件不存在: {temp_file}")
                        return False
                finally:
                    if os.path.exists(temp_file):
                        self.logger.info(f"删除临时音频文件: {temp_file}")
                        os.remove(temp_file)
            
            return True
                    
        except Exception as e:
            self.logger.error(f"语音播放失败: {e}")
            return False
    
    def speak(self, text: str) -> bool:
        try:
            return asyncio.run(self._speak_async(text))
        except Exception as e:
            self.logger.error(f"语音播放失败: {e}")
            return False
    
    def _split_text(self, text: str, max_length: int = 80) -> list:
        """将长文本分割成多个短文本片段，优先在标点符号处断句"""
        segments = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # 计算当前片段的结束位置
            end = min(start + max_length, text_length)
            
            # 如果没有达到文本末尾，尝试在标点符号处断句
            if end < text_length:
                # 优先在句号、问号、感叹号处断句
                for i in range(end, max(start, end - 10), -1):
                    if text[i] in '。！？.!?':
                        end = i + 1
                        break
                else:
                    # 如果没有找到合适的标点，在逗号处断句
                    for i in range(end, max(start, end - 10), -1):
                        if text[i] in '，,':
                            end = i + 1
                            break
            
            segment = text[start:end]
            if segment.strip():
                segments.append(segment)
            start = end
        
        self.logger.info(f"文本分割完成，共 {len(segments)} 个片段")
        return segments
    
    async def save_to_file_async(self, text: str, file_path: str) -> bool:
        try:
            self.logger.info(f"保存语音到文件: {file_path}")
            
            # 分析文本情绪
            emotion_params = self._analyze_emotion(text)
            self.logger.info(f"分析到情绪: {emotion_params['emotion']}, 语速: {emotion_params['speed']}, 音调: {emotion_params['pitch']}")
            
            # 关闭分段设置，文本一次性合成
            text_segments = self._split_text(text, max_length=2000)
            self.logger.info(f"文本长度: {len(text)}, 分割为 {len(text_segments)} 个片段")
            
            # 确定使用的语音配置
            use_siliconflow = self.use_siliconflow
            voice_name = self.voice_name
            
            # 如果启用自定义语音
            if self.use_custom_voice:
                if config.CUSTOM_VOICE_TYPE == 'tts':
                    # 根据角色选择自定义TTS音色
                    if self.role == 'paimon' and hasattr(config, 'PAIMON_VOICE_ID'):
                        voice_name = config.PAIMON_VOICE_ID
                        self.logger.info(f"使用派蒙自定义TTS音色: {voice_name}")
                    else:
                        voice_name = config.CUSTOM_VOICE_ID
                        self.logger.info(f"使用荧自定义TTS音色: {voice_name}")
                    use_siliconflow = True
            
            if use_siliconflow:
                # 使用硅基流动API，逐段合成
                import soundfile as sf
                import numpy as np
                all_audio_data = []
                
                for i, segment in enumerate(text_segments):
                    self.logger.info(f"合成第 {i+1}/{len(text_segments)} 段文本: {segment[:50]}...")
                    
                    url = "https://api.siliconflow.cn/v1/audio/speech"
                    headers = {
                        "Authorization": f"Bearer {config.SILICONFLOW_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": "FunAudioLLM/CosyVoice2-0.5B",
                        "input": segment,
                        "voice": voice_name
                    }
                    
                    try:
                        response = requests.post(url, headers=headers, json=data, timeout=30)
                        
                        if response.status_code == 200:
                            # 保存临时文件并读取音频数据
                            temp_file = f"temp_segment_{i}.wav"
                            with open(temp_file, 'wb') as f:
                                f.write(response.content)
                            
                            # 读取音频数据
                            data, fs = sf.read(temp_file, dtype='float32')
                            all_audio_data.append(data)
                            
                            # 删除临时文件
                            os.remove(temp_file)
                            self.logger.info(f"第 {i+1} 段合成成功")
                        else:
                            self.logger.error(f"硅基流动API调用失败: {response.status_code} - {response.text}")
                            return False
                    except requests.exceptions.RequestException as e:
                        self.logger.error(f"硅基流动API网络请求失败: {e}")
                        return False
                
                # 合并所有音频片段
                if all_audio_data:
                    # 添加静音间隔（减少间隔时间，让语音更流畅）
                    silence_duration = 0.05  # 秒
                    fs = 24000  # 假设采样率为24000Hz
                    silence_samples = int(silence_duration * fs)
                    silence = np.zeros(silence_samples, dtype='float32')
                    
                    merged_data = all_audio_data[0]
                    for i in range(1, len(all_audio_data)):
                        merged_data = np.concatenate([merged_data, silence, all_audio_data[i]])
                    
                    # 保存合并后的音频
                    sf.write(file_path, merged_data, fs)
                    self.logger.info(f"音频片段合并完成，总长度: {len(merged_data)} 样本")
                else:
                    self.logger.error("没有成功合成的音频片段")
                    return False
            else:
                # 使用edge-tts，逐段合成
                import soundfile as sf
                import numpy as np
                all_audio_data = []
                
                for i, segment in enumerate(text_segments):
                    self.logger.info(f"合成第 {i+1}/{len(text_segments)} 段文本: {segment[:50]}...")
                    
                    temp_file = f"temp_segment_{i}.wav"
                    communicate = edge_tts.Communicate(segment, voice_name)
                    await communicate.save(temp_file)
                    
                    # 读取音频数据
                    data, fs = sf.read(temp_file, dtype='float32')
                    all_audio_data.append(data)
                    
                    # 删除临时文件
                    os.remove(temp_file)
                
                # 合并所有音频片段
                if all_audio_data:
                    # 添加静音间隔
                    silence_duration = 0.1  # 秒
                    silence_samples = int(silence_duration * fs)
                    silence = np.zeros(silence_samples, dtype='float32')
                    
                    merged_data = all_audio_data[0]
                    for i in range(1, len(all_audio_data)):
                        merged_data = np.concatenate([merged_data, silence, all_audio_data[i]])
                    
                    # 保存合并后的音频
                    sf.write(file_path, merged_data, fs)
            
            return True
        except Exception as e:
            self.logger.error(f"保存语音文件失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return False
    
    def save_to_file(self, text: str, file_path: str) -> bool:
        """同步版本的save_to_file，用于非异步环境"""
        try:
            asyncio.run(self.save_to_file_async(text, file_path))
            return True
        except Exception as e:
            self.logger.error(f"同步保存语音文件失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return False
    
    def generate_audio_data(self, text: str) -> Optional[bytes]:
        try:
            temp_file = "temp_audio.wav"
            
            # 分析文本情绪
            emotion_params = self._analyze_emotion(text)
            self.logger.info(f"分析到情绪: {emotion_params['emotion']}, 语速: {emotion_params['speed']}, 音调: {emotion_params['pitch']}")
            
            async def generate():
                if self.use_siliconflow:
                    # 使用硅基流动API
                    url = "https://api.siliconflow.cn/v1/audio/speech"
                    headers = {
                        "Authorization": f"Bearer {config.SILICONFLOW_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": "FunAudioLLM/CosyVoice2-0.5B",
                        "input": text,
                        "voice": self.voice_name
                    }
                    
                    # 根据情绪添加参数
                    if emotion_params['emotion'] != 'neutral':
                        data['emotion'] = emotion_params['emotion']
                    
                    response = requests.post(url, headers=headers, json=data)
                    
                    if response.status_code == 200:
                        with open(temp_file, 'wb') as f:
                            f.write(response.content)
                    else:
                        self.logger.error(f"硅基流动API调用失败: {response.status_code} - {response.text}")
                        return False
                else:
                    # 使用edge-tts
                    communicate = edge_tts.Communicate(text, self.voice_name)
                    await communicate.save(temp_file)
            
            asyncio.run(generate())
            
            try:
                with open(temp_file, 'rb') as f:
                    return f.read()
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as e:
            self.logger.error(f"生成音频数据失败: {e}")
            return None
    
    def set_voice(self, voice_name: str):
        if voice_name == "custom":
            # 切换到自定义语音
            self.use_custom_voice = hasattr(config, 'CUSTOM_VOICE_TYPE') and config.CUSTOM_VOICE_TYPE in ['file', 'tts']
            if self.use_custom_voice:
                if config.CUSTOM_VOICE_TYPE == 'tts':
                    self.logger.info(f"已切换到自定义TTS音色: {config.CUSTOM_VOICE_ID}")
                else:
                    self.logger.info(f"已切换到自定义语音文件: {config.CUSTOM_VOICE_FILE}")
        else:
            # 切换到标准语音
            self.voice_name = voice_name
            self.use_siliconflow = voice_name.startswith("speech:")
            self.use_custom_voice = False
            self.logger.info(f"已切换语音: {voice_name}")
        return True