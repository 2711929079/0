import uuid
from typing import Dict, Optional, Tuple
from modules.llm_interface import LLMInterface
from modules.memory_manager import MemoryManager
from modules.user_auth import user_auth
import logging

class SessionManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 会话存储：session_id -> (llm_instance, username, memory_manager, role)
        self.sessions: Dict[str, Tuple[LLMInterface, Optional[str], MemoryManager, str]] = {}
        # 用户名到会话ID的映射：username -> session_id
        self.username_to_session: Dict[str, str] = {}
    
    def create_session(self, username: Optional[str] = None, role: str = "ying") -> str:
        """创建新会话或返回现有会话
        
        Args:
            username: 用户名，可选
            role: 角色标识，可选，默认值为"ying"（荧）
            
        Returns:
            会话ID
        """
        # 如果提供了用户名，检查是否已有会话
        if username and username in self.username_to_session:
            session_id = self.username_to_session[username]
            # 检查会话是否仍然存在
            if session_id in self.sessions:
                _, existing_username, _, existing_role = self.sessions[session_id]
                # 如果角色不同，更新会话的角色
                if existing_role != role:
                    memory_manager = MemoryManager(username=username, role=role)
                    llm_instance = LLMInterface(memory_manager=memory_manager, role=role)
                    self.sessions[session_id] = (llm_instance, username, memory_manager, role)
                    self.logger.info(f"更新会话角色: {session_id}, 用户: {username}, 新角色: {role}")
                self.logger.info(f"用户已有会话，返回现有会话: {session_id}, 用户: {username}")
                return session_id
        
        # 创建新会话
        session_id = str(uuid.uuid4())
        memory_manager = MemoryManager(username=username, role=role)
        llm_instance = LLMInterface(memory_manager=memory_manager, role=role)
        self.sessions[session_id] = (llm_instance, username, memory_manager, role)
        
        # 如果提供了用户名，建立用户名到会话ID的映射
        if username:
            self.username_to_session[username] = session_id
        
        self.logger.info(f"创建新会话: {session_id}, 用户: {username}, 角色: {role}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Tuple[LLMInterface, Optional[str], MemoryManager, str]]:
        """获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            (LLMInterface实例, 用户名, MemoryManager实例, 角色)，如果会话不存在则返回None
        """
        return self.sessions.get(session_id)
    
    def get_username_from_session(self, session_id: str) -> Optional[str]:
        """从会话中获取用户名
        
        Args:
            session_id: 会话ID
            
        Returns:
            用户名，如果会话不存在则返回None
        """
        session = self.get_session(session_id)
        if session:
            return session[1]  # 返回用户名（元组的第二个元素）
        return None
    
    def ensure_session(self, session_id: Optional[str] = None, password: Optional[str] = None, role: str = "ying") -> Tuple[str, Optional[str]]:
        """确保会话存在
        
        Args:
            session_id: 可选的会话ID
            password: 用户口令，可选
            role: 角色标识，可选，默认值为"ying"（荧）
            
        Returns:
            (会话ID, 用户名)
        """
        username = None
        
        # 如果提供了口令，进行用户认证
        if password:
            username = user_auth.authenticate_user(password)
            if not username:
                # 认证失败，尝试注册新用户
                if user_auth.register_user(password):
                    username = user_auth.get_user_by_password(password)
        
        # 如果会话ID存在且有效，返回现有会话
        if session_id and session_id in self.sessions:
            _, existing_username, _, existing_role = self.sessions[session_id]
            # 如果提供了口令但会话属于其他用户，创建新会话
            # 如果角色不同，也创建新会话
            if password and existing_username != username or existing_role != role:
                return self.create_session(username, role), username
            return session_id, existing_username
        else:
            # 创建新会话
            new_session_id = self.create_session(username, role)
            return new_session_id, username
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        if session_id in self.sessions:
            # 获取用户名，用于删除映射
            _, username, _, _ = self.sessions[session_id]
            # 删除会话
            del self.sessions[session_id]
            # 如果有用户名，删除用户名到会话ID的映射
            if username and username in self.username_to_session:
                del self.username_to_session[username]
            self.logger.info(f"删除会话: {session_id}, 用户: {username}")
            return True
        return False
    
    def get_session_count(self) -> int:
        """获取会话数量
        
        Returns:
            会话数量
        """
        return len(self.sessions)
    
    def clear_all_sessions(self):
        """清空所有会话"""
        self.sessions.clear()
        self.username_to_session.clear()
        self.logger.info("清空所有会话")

# 创建全局会话管理器实例
session_manager = SessionManager()
