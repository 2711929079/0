import redis
import json
import logging
import hashlib
import time
from typing import List, Dict, Optional, Any

class CacheManager:
    """缓存管理器 - 实现Redis缓存和内存缓存双重保障"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.memory_cache = {}
        # 尝试连接Redis，如果失败则使用内存缓存
        self.enabled = False
        self._init_redis()
        
        # 缓存统计信息
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'total_requests': 0,
            'start_time': time.time()
        }
        
        # 内存缓存大小限制（1000条记录）
        self.MAX_MEMORY_CACHE_SIZE = 1000
        
        # 缓存类型统计
        self.type_stats = {
            'session': {'hits': 0, 'misses': 0, 'sets': 0},
            'rag': {'hits': 0, 'misses': 0, 'sets': 0},
            'embedding': {'hits': 0, 'misses': 0, 'sets': 0}
        }
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=5)
            # 测试连接
            self.redis_client.ping()
            self.enabled = True
            self.logger.info("Redis连接成功")
        except Exception as e:
            self.enabled = False
            self.logger.warning(f"Redis连接失败，使用内存缓存: {e}")
    
    def get_session_context(self, user_id: str) -> List[Dict[str, Any]]:
        """获取会话上下文（短期记忆）"""
        key = f"user:{user_id}:session"
        self.cache_stats['total_requests'] += 1
        
        try:
            if self.enabled:
                data = self.redis_client.get(key)
                if data:
                    self.cache_stats['hits'] += 1
                    self.type_stats['session']['hits'] += 1
                    return json.loads(data)
            else:
                if key in self.memory_cache:
                    self.cache_stats['hits'] += 1
                    self.type_stats['session']['hits'] += 1
                    return self.memory_cache[key]
                
            self.cache_stats['misses'] += 1
            self.type_stats['session']['misses'] += 1
            return []
            
        except Exception as e:
            self.logger.error(f"获取会话上下文失败: {e}")
            self.cache_stats['misses'] += 1
            self.type_stats['session']['misses'] += 1
            return self.memory_cache.get(key, [])
    
    def set_session_context(self, user_id: str, context: List[Dict[str, Any]], max_length: int = 20):
        """保存会话上下文（短期记忆）"""
        key = f"user:{user_id}:session"
        # 限制长度，保留最近的对话
        if len(context) > max_length:
            context = context[-max_length:]
        
        try:
            if self.enabled:
                # 1周过期时间（避免上下文频繁丢失）
                self.redis_client.setex(key, 604800, json.dumps(context, ensure_ascii=False))
                self.cache_stats['sets'] += 1
                self.type_stats['session']['sets'] += 1
            else:
                # 内存缓存大小管理
                if len(self.memory_cache) >= self.MAX_MEMORY_CACHE_SIZE:
                    # 移除最旧的缓存项（FIFO）
                    oldest_key = next(iter(self.memory_cache))
                    del self.memory_cache[oldest_key]
                    self.cache_stats['evictions'] += 1
                
                self.memory_cache[key] = context
                self.cache_stats['sets'] += 1
                self.type_stats['session']['sets'] += 1
                
        except Exception as e:
            self.logger.error(f"保存会话上下文失败: {e}")
    
    def get_rag_result(self, query: str) -> Optional[List[str]]:
        """获取RAG检索结果缓存"""
        key = f"rag:{self._get_query_hash(query)}"
        self.cache_stats['total_requests'] += 1
        
        try:
            if self.enabled:
                data = self.redis_client.get(key)
                if data:
                    self.cache_stats['hits'] += 1
                    self.type_stats['rag']['hits'] += 1
                    return json.loads(data)
            else:
                if key in self.memory_cache:
                    self.cache_stats['hits'] += 1
                    self.type_stats['rag']['hits'] += 1
                    return self.memory_cache[key]
                
            self.cache_stats['misses'] += 1
            self.type_stats['rag']['misses'] += 1
            return None
            
        except Exception as e:
            self.logger.error(f"获取RAG结果缓存失败: {e}")
            self.cache_stats['misses'] += 1
            self.type_stats['rag']['misses'] += 1
            return None
    
    def set_rag_result(self, query: str, result: List[str]):
        """保存RAG检索结果缓存"""
        key = f"rag:{self._get_query_hash(query)}"
        
        try:
            if self.enabled:
                # 5分钟过期时间
                self.redis_client.setex(key, 300, json.dumps(result, ensure_ascii=False))
                self.cache_stats['sets'] += 1
                self.type_stats['rag']['sets'] += 1
            else:
                # 内存缓存大小管理
                if len(self.memory_cache) >= self.MAX_MEMORY_CACHE_SIZE:
                    # 移除最旧的缓存项（FIFO）
                    oldest_key = next(iter(self.memory_cache))
                    del self.memory_cache[oldest_key]
                    self.cache_stats['evictions'] += 1
                
                self.memory_cache[key] = result
                self.cache_stats['sets'] += 1
                self.type_stats['rag']['sets'] += 1
                
        except Exception as e:
            self.logger.error(f"保存RAG结果缓存失败: {e}")
    
    def get_embedding_cache(self, text: str) -> Optional[List[float]]:
        """获取Embedding向量缓存"""
        key = f"embedding:{self._get_query_hash(text)}"
        self.cache_stats['total_requests'] += 1
        
        try:
            if self.enabled:
                data = self.redis_client.get(key)
                if data:
                    self.cache_stats['hits'] += 1
                    self.type_stats['embedding']['hits'] += 1
                    return json.loads(data)
            else:
                if key in self.memory_cache:
                    self.cache_stats['hits'] += 1
                    self.type_stats['embedding']['hits'] += 1
                    return self.memory_cache[key]
                
            self.cache_stats['misses'] += 1
            self.type_stats['embedding']['misses'] += 1
            return None
            
        except Exception as e:
            self.logger.error(f"获取Embedding缓存失败: {e}")
            self.cache_stats['misses'] += 1
            self.type_stats['embedding']['misses'] += 1
            return None
    
    def set_embedding_cache(self, text: str, embedding: List[float]):
        """保存Embedding向量缓存"""
        key = f"embedding:{self._get_query_hash(text)}"
        
        try:
            if self.enabled:
                # 24小时过期时间
                self.redis_client.setex(key, 86400, json.dumps(embedding))
                self.cache_stats['sets'] += 1
                self.type_stats['embedding']['sets'] += 1
            else:
                # 内存缓存大小管理
                if len(self.memory_cache) >= self.MAX_MEMORY_CACHE_SIZE:
                    # 移除最旧的缓存项（FIFO）
                    oldest_key = next(iter(self.memory_cache))
                    del self.memory_cache[oldest_key]
                    self.cache_stats['evictions'] += 1
                
                self.memory_cache[key] = embedding
                self.cache_stats['sets'] += 1
                self.type_stats['embedding']['sets'] += 1
                
        except Exception as e:
            self.logger.error(f"保存Embedding缓存失败: {e}")
    
    def _get_query_hash(self, query: str) -> str:
        """生成查询的哈希值作为缓存键"""
        return hashlib.md5(query.encode('utf-8')).hexdigest()
    
    def clear_user_cache(self, user_id: str):
        """清除指定用户的所有缓存"""
        try:
            if self.enabled:
                # 使用SCAN命令查找所有相关键
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor=cursor, match=f"user:{user_id}:*")
                    if keys:
                        self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            else:
                # 清除内存缓存
                keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"user:{user_id}:")]
                for key in keys_to_delete:
                    del self.memory_cache[key]
        except Exception as e:
            self.logger.error(f"清除用户缓存失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        # 计算命中率
        total_requests = self.cache_stats['total_requests']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # 计算运行时间
        uptime = time.time() - self.cache_stats['start_time']
        
        stats = {
            'redis_enabled': self.enabled,
            'memory_cache_size': len(self.memory_cache),
            'total_requests': total_requests,
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets'],
            'evictions': self.cache_stats['evictions'],
            'hit_rate': f"{hit_rate:.2f}%",
            'uptime_seconds': int(uptime),
            'type_stats': self.type_stats
        }
        
        if self.enabled:
            try:
                info = self.redis_client.info('memory')
                stats['redis_used_memory'] = info.get('used_memory_human', 'N/A')
                stats['redis_keys_count'] = self.redis_client.dbsize()
                
                # 获取Redis缓存命中率（近似值）
                redis_info = self.redis_client.info()
                stats['redis_keyspace_hits'] = redis_info.get('keyspace_hits', 0)
                stats['redis_keyspace_misses'] = redis_info.get('keyspace_misses', 0)
                
            except Exception as e:
                self.logger.error(f"获取Redis统计信息失败: {e}")
        
        return stats
    
    def reset_stats(self):
        """重置缓存统计信息"""
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'total_requests': 0,
            'start_time': time.time()
        }
        
        self.type_stats = {
            'session': {'hits': 0, 'misses': 0, 'sets': 0},
            'rag': {'hits': 0, 'misses': 0, 'sets': 0},
            'embedding': {'hits': 0, 'misses': 0, 'sets': 0}
        }
    
    def get_cache_summary(self) -> str:
        """获取缓存统计摘要（用于日志记录）"""
        stats = self.get_cache_stats()
        return (f"缓存统计: 总请求={stats['total_requests']}, "
                f"命中={stats['hits']}, 未命中={stats['misses']}, "
                f"命中率={stats['hit_rate']}, 驱逐={stats['evictions']}, "
                f"内存缓存大小={stats['memory_cache_size']}")

# 创建全局缓存管理器实例
cache_manager = CacheManager()
