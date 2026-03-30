import openai
from typing import List, Dict, Optional
import logging
from config import config
from modules.memory_manager import MemoryManager

class LLMInterface:
    def __init__(self, memory_manager=None, role: str = "ying"):
        self.logger = logging.getLogger(__name__)
        self.conversation_history: List[Dict[str, str]] = []
        self.memory_manager = memory_manager if memory_manager else MemoryManager()
        self.role = role  # 角色标识：ying（荧）或 paimon（派蒙）
        self._init_client()
        
    def _init_client(self):
        if config.API_KEY:
            self.client = openai.OpenAI(
                api_key=config.API_KEY,
                base_url=config.BASE_URL
            )
        else:
            self.logger.warning("硅基流动API密钥未配置")
    
    def add_message(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        
        if len(self.conversation_history) > config.MAX_HISTORY_LENGTH:
            self.conversation_history = self.conversation_history[-config.MAX_HISTORY_LENGTH:]
    
    def generate_response(self, user_input: str) -> Optional[str]:
        """生成完整回复（非流式）"""
        try:
            # 检查是否是角色查询
            is_character_query = any(keyword in user_input for keyword in ['角色', '人物', '有哪些', '谁', '哪些'])
            
            # 搜索相关记忆（角色查询不使用记忆）
            memory_results = [] if is_character_query else self.memory_manager.search_memory(user_input)
            
            # 构建记忆上下文（角色查询不添加记忆）
            memory_context = ""
            if memory_results and not is_character_query:
                memory_context = "【记忆信息】\n"
                for i, memory in enumerate(memory_results[:3], 1):
                    if memory['type'] == 'long_term':
                        memory_context += f"- {memory['content']}\n"
                    elif memory['type'] == 'short_term':
                        memory_context += f"- 用户: {memory['user_input']}\n  我: {memory['assistant_response']}\n"
            
            # 添加用户消息
            self.add_message("user", user_input)
            
            # 构建系统提示词（包含记忆信息）
            system_prompt = config.SYSTEM_PROMPTS.get(self.role, config.SYSTEM_PROMPTS["ying"])
            if memory_context:
                system_prompt += f"\n\n{memory_context}"
            
            messages = [
                {"role": "system", "content": system_prompt}
            ] + self.conversation_history
            
            self.logger.info(f"调用LLM模型: {config.MODEL_NAME}")
            self.logger.info(f"消息数量: {len(messages)}")
            self.logger.info(f"记忆信息长度: {len(memory_context)}")
            
            response = self.client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=messages,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                stream=False
            )
            
            self.logger.info(f"LLM响应状态: {response}")
            
            assistant_response = response.choices[0].message.content.strip()
            self.logger.info(f"AI回复内容: '{assistant_response}'")
            
            self.add_message("assistant", assistant_response)
            
            # 更新记忆
            self.memory_manager.process_dialogue(user_input, assistant_response)
            
            self.logger.info(f"AI回复: {assistant_response}")
            return assistant_response
            
        except Exception as e:
            self.logger.error(f"生成回复失败: {e}")
            return "抱歉，我现在无法生成回复，请稍后再试。"
    
    def generate_stream_response(self, user_input: str):
        """生成流式回复"""
        try:
            # 搜索相关记忆
            memory_results = self.memory_manager.search_memory(user_input)
            
            # 构建记忆上下文
            memory_context = ""
            if memory_results:
                memory_context = "【记忆信息】\n"
                for i, memory in enumerate(memory_results[:3], 1):
                    if memory['type'] == 'long_term':
                        memory_context += f"- {memory['content']}\n"
                    elif memory['type'] == 'short_term':
                        memory_context += f"- 用户: {memory['user_input']}\n  我: {memory['assistant_response']}\n"
            
            # 添加用户消息
            self.add_message("user", user_input)
            
            # 构建系统提示词（包含记忆信息）
            system_prompt = config.SYSTEM_PROMPTS.get(self.role, config.SYSTEM_PROMPTS["ying"])
            if memory_context:
                system_prompt += f"\n\n{memory_context}"
            
            messages = [
                {"role": "system", "content": system_prompt}
            ] + self.conversation_history
            
            response = self.client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=messages,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                stream=True
            )
            
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            self.add_message("assistant", full_response)
            
            # 更新记忆
            self.memory_manager.process_dialogue(user_input, full_response)
            
            self.logger.info(f"AI流式回复: {full_response}")
            
        except Exception as e:
            self.logger.error(f"生成流式回复失败: {e}")
            yield f"生成回复失败: {e}"
    
    def clear_history(self):
        self.conversation_history = []
        self.logger.info("对话历史已清空")
    
    def get_history(self) -> List[Dict[str, str]]:
        return self.conversation_history.copy()
    
    def set_system_prompt(self, prompt: str):
        self.logger.info("系统提示词已更新")