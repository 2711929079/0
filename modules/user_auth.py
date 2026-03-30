import json
import hashlib
import os
import logging
from typing import Optional, Dict, Any

class UserAuth:
    def __init__(self, auth_file: str = "user_auth.json"):
        self.logger = logging.getLogger(__name__)
        self.auth_file = auth_file
        self.users: Dict[str, str] = {}
        self.load_users()
    
    def load_users(self):
        """加载用户信息"""
        try:
            if os.path.exists(self.auth_file):
                with open(self.auth_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                self.logger.info(f"加载了 {len(self.users)} 个用户")
            else:
                self.logger.info("用户文件不存在，创建新文件")
                self.save_users()
        except Exception as e:
            self.logger.error(f"加载用户信息失败: {e}")
    
    def save_users(self):
        """保存用户信息"""
        try:
            with open(self.auth_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            self.logger.info(f"保存了 {len(self.users)} 个用户")
        except Exception as e:
            self.logger.error(f"保存用户信息失败: {e}")
    
    def hash_password(self, password: str) -> str:
        """对密码进行哈希处理"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def register_user(self, password: str) -> bool:
        """注册新用户
        
        Args:
            password: 用户口令
            
        Returns:
            是否注册成功
        """
        if not password or len(password) < 4:
            self.logger.warning("口令太短，至少需要4个字符")
            return False
        
        hashed_pw = self.hash_password(password)
        
        if hashed_pw in self.users.values():
            self.logger.warning("该口令已被使用")
            return False
        
        # 使用哈希值作为用户名（简单实现）
        username = hashed_pw[:8]
        self.users[username] = hashed_pw
        self.save_users()
        self.logger.info(f"新用户注册成功: {username}")
        return True
    
    def authenticate_user(self, password: str) -> Optional[str]:
        """验证用户
        
        Args:
            password: 用户口令
            
        Returns:
            用户名，如果验证失败则返回None
        """
        hashed_pw = self.hash_password(password)
        
        for username, stored_hash in self.users.items():
            if stored_hash == hashed_pw:
                self.logger.info(f"用户验证成功: {username}")
                return username
        
        self.logger.warning("用户验证失败")
        return None
    
    def get_user_by_password(self, password: str) -> Optional[str]:
        """通过口令获取用户名
        
        Args:
            password: 用户口令
            
        Returns:
            用户名，如果不存在则返回None
        """
        hashed_pw = self.hash_password(password)
        
        for username, stored_hash in self.users.items():
            if stored_hash == hashed_pw:
                return username
        
        return None
    
    def delete_user(self, password: str) -> bool:
        """删除用户
        
        Args:
            password: 用户口令
            
        Returns:
            是否删除成功
        """
        username = self.get_user_by_password(password)
        if username:
            del self.users[username]
            self.save_users()
            self.logger.info(f"用户删除成功: {username}")
            return True
        return False
    
    def get_user_count(self) -> int:
        """获取用户数量"""
        return len(self.users)

# 创建全局用户认证实例
user_auth = UserAuth()
