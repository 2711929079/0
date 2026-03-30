import redis
import time
import logging
from typing import Dict, Optional
from functools import wraps
from flask import request, abort, jsonify

class RateLimiter:
    """请求速率限制器 - 防止DOS攻击和滥用"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.enabled = False
        self._init_redis()
        
        # 速率限制配置
        self.rate_limits = {
            'api_chat': {'limit': 60, 'window': 60},  # 每分钟60次请求
            'api_login': {'limit': 5, 'window': 60},   # 每分钟5次登录尝试
            'api_speech': {'limit': 30, 'window': 60}, # 每分钟30次语音请求
            'api_audio': {'limit': 20, 'window': 60},  # 每分钟20次音频合成
        }
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=5)
            # 测试连接
            self.redis_client.ping()
            self.enabled = True
            self.logger.info("Redis连接成功，速率限制器已启用")
        except Exception as e:
            self.enabled = False
            self.logger.warning(f"Redis连接失败，速率限制器已禁用: {e}")
    
    def _get_client_ip(self) -> str:
        """获取客户端IP地址"""
        # 获取真实IP地址（考虑代理）
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.remote_addr
    
    def _get_key(self, endpoint: str, identifier: str) -> str:
        """生成速率限制的Redis键"""
        return f"rate_limit:{endpoint}:{identifier}"
    
    def is_allowed(self, endpoint: str, identifier: str) -> bool:
        """检查请求是否允许（基于速率限制）"""
        if not self.enabled:
            return True
        
        config = self.rate_limits.get(endpoint, {'limit': 100, 'window': 60})
        limit = config['limit']
        window = config['window']
        
        key = self._get_key(endpoint, identifier)
        
        try:
            # 使用Redis的INCR命令增加计数器
            current = self.redis_client.incr(key)
            
            # 如果是第一次请求，设置过期时间
            if current == 1:
                self.redis_client.expire(key, window)
            
            # 检查是否超过限制
            if current > limit:
                self.logger.warning(f"速率限制触发: {endpoint}, IP: {identifier}, 计数: {current}/{limit}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"速率限制检查失败: {e}")
            # 失败时允许请求（安全第一）
            return True
    
    def get_remaining(self, endpoint: str, identifier: str) -> Dict[str, int]:
        """获取剩余请求次数和重置时间"""
        if not self.enabled:
            return {'remaining': 999, 'reset_in': 0}
        
        config = self.rate_limits.get(endpoint, {'limit': 100, 'window': 60})
        limit = config['limit']
        window = config['window']
        
        key = self._get_key(endpoint, identifier)
        
        try:
            current = self.redis_client.get(key)
            if current:
                remaining = max(0, limit - int(current))
                ttl = self.redis_client.ttl(key)
                if ttl == -1:
                    ttl = window
                return {'remaining': remaining, 'reset_in': ttl}
            else:
                return {'remaining': limit, 'reset_in': window}
                
        except Exception as e:
            self.logger.error(f"获取剩余请求次数失败: {e}")
            return {'remaining': limit, 'reset_in': window}
    
    def rate_limit(self, endpoint: str):
        """装饰器：应用速率限制"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not self.enabled:
                    return f(*args, **kwargs)
                
                # 获取客户端标识符（优先使用用户ID，否则使用IP）
                identifier = request.remote_addr
                
                # 检查速率限制
                if not self.is_allowed(endpoint, identifier):
                    remaining_info = self.get_remaining(endpoint, identifier)
                    abort(429, description={
                        'error': '请求过于频繁，请稍后再试',
                        'remaining': remaining_info['remaining'],
                        'reset_in': remaining_info['reset_in']
                    })
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# 创建全局速率限制器实例
rate_limiter = RateLimiter()