import json
import os
import logging
from typing import List, Dict, Optional, Any
import datetime
import uuid
import sqlite3
import asyncio
from contextlib import contextmanager
from modules.cache_manager import cache_manager

class MemoryManager:
    """记忆管理器 - 实现三层记忆架构
    
    1. 短期记忆：内存存储，用于对话上下文
    2. 长期记忆：SQLite数据库存储，用于用户画像和长期习惯
    3. 向量记忆：语义存储，用于知识关联和语义检索
    """
    
    def __init__(self, username: Optional[str] = None, role: str = "ying"):
        self.logger = logging.getLogger(__name__)
        self.username = username
        self.user_id = username or "anonymous"
        self.role = role  # 角色标识：ying（荧）或 paimon（派蒙）
        
        # 1. 短期记忆：内存存储（结构化记忆）
        self.short_term_memory: List[Dict[str, Any]] = []
        self.MAX_SHORT_TERM_MEMORY = 50  # 最多保存50条对话
        
        # 从缓存加载短期记忆
        self._load_short_term_memory_from_cache()
        
        # 2. 长期记忆：SQLite数据库存储
        self.db_path = 'data/memory_database.db'
        # 连接池配置
        self._connection_pool = []
        self._max_connections = 5
        self._connection_lock = asyncio.Lock()
        self.long_term_memory: List[Dict[str, Any]] = []
        
        # 先初始化数据库表结构
        self._init_database()
        
        # 然后加载长期记忆
        self._load_long_term_memory()
        
        # 3. 向量记忆：语义存储（通过Chroma向量数据库实现）
        self.vector_memory_enabled = False
        self.chroma_collection = None
        self._init_vector_memory()
        
    def _get_connection(self):
        """获取数据库连接（线程安全）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    @contextmanager
    def get_db_connection(self):
        """上下文管理器：获取数据库连接"""
        conn = None
        try:
            conn = self._get_connection()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def _get_connection_async(self):
        """异步获取数据库连接（使用连接池）"""
        async with self._connection_lock:
            if self._connection_pool:
                return self._connection_pool.pop()
            
            # 创建新连接
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
    
    async def _release_connection_async(self, conn):
        """异步释放数据库连接到连接池"""
        async with self._connection_lock:
            if len(self._connection_pool) < self._max_connections:
                self._connection_pool.append(conn)
            else:
                conn.close()
    
    async def execute_query_async(self, query, params=None):
        """异步执行SQL查询"""
        conn = None
        try:
            conn = await self._get_connection_async()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            return cursor.fetchall()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"异步查询执行失败: {e}")
            raise
        finally:
            if conn:
                await self._release_connection_async(conn)
    
    def _init_database(self):
        """初始化SQLite数据库表结构"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 创建用户表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                )
                ''')
                
                # 创建长期记忆表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS long_term_memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    tags TEXT DEFAULT '[]',
                    type TEXT DEFAULT 'long_term',
                    access_count INTEGER DEFAULT 0,
                    timestamp TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    role TEXT DEFAULT "ying",
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_user_id ON long_term_memories(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_role ON long_term_memories(role)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_user_role ON long_term_memories(user_id, role)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON long_term_memories(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_importance ON long_term_memories(importance)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_access_count ON long_term_memories(access_count)')
                
                # 创建聊天记录表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_histories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                ''')
                
                # 创建聊天记录索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_user_role ON chat_histories(user_id, role)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_histories(timestamp)')
                
                # 确保用户存在
                cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (self.user_id,))
                if not cursor.fetchone():
                    cursor.execute(
                        'INSERT INTO users (user_id, created_at) VALUES (?, ?)',
                        (self.user_id, datetime.datetime.now().isoformat())
                    )
                
                self.logger.info(f"SQLite数据库初始化成功: {self.db_path}")
                
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {e}")
            raise
    
    def _load_long_term_memory(self):
        """从SQLite数据库加载长期记忆数据"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT id, content, importance, tags, type, access_count, timestamp, last_accessed
                FROM long_term_memories
                WHERE user_id = ? AND role = ?
                ORDER BY timestamp DESC
                ''', (self.user_id, self.role))
                
                rows = cursor.fetchall()
                self.long_term_memory = []
                
                for row in rows:
                    memory = {
                        'id': row['id'],
                        'content': row['content'],
                        'importance': row['importance'],
                        'tags': json.loads(row['tags']),
                        'type': row['type'],
                        'access_count': row['access_count'],
                        'timestamp': row['timestamp'],
                        'last_accessed': row['last_accessed']
                    }
                    self.long_term_memory.append(memory)
                
                self.logger.info(f"已从数据库加载 {len(self.long_term_memory)} 条长期记忆")
                
        except Exception as e:
            self.logger.error(f"加载长期记忆失败: {e}")
    
    async def _load_long_term_memory_async(self):
        """异步从SQLite数据库加载长期记忆数据"""
        try:
            rows = await self.execute_query_async('''
            SELECT id, content, importance, tags, type, access_count, timestamp, last_accessed
            FROM long_term_memories
            WHERE user_id = ? AND role = ?
            ORDER BY timestamp DESC
            ''', (self.user_id, self.role))
            
            self.long_term_memory = []
            for row in rows:
                memory = {
                    'id': row['id'],
                    'content': row['content'],
                    'importance': row['importance'],
                    'tags': json.loads(row['tags']),
                    'type': row['type'],
                    'access_count': row['access_count'],
                    'timestamp': row['timestamp'],
                    'last_accessed': row['last_accessed']
                }
                self.long_term_memory.append(memory)
            
            self.logger.info(f"异步从数据库加载 {len(self.long_term_memory)} 条长期记忆")
            return self.long_term_memory
            
        except Exception as e:
            self.logger.error(f"异步加载长期记忆失败: {e}")
            return []
    
    def _save_long_term_memory(self):
        """保存长期记忆数据到SQLite数据库"""
        # 这个方法在SQLite版本中不再需要，因为每条记忆都会立即保存
        pass
    
    def _init_vector_memory(self):
        """初始化向量记忆（Chroma数据库）"""
        try:
            import chromadb
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
            except ImportError:
                from langchain.embeddings import HuggingFaceEmbeddings
            
            # 创建Chroma客户端
            chroma_client = chromadb.PersistentClient(path="./data/chroma_db")
            
            # 创建或获取用户和角色专用的集合
            collection_name = f"user_memory_{self.user_id}_{self.role}"
            self.chroma_collection = chroma_client.get_or_create_collection(name=collection_name)
            
            self.vector_memory_enabled = True
            self.logger.info(f"向量记忆初始化成功，集合: {collection_name}")
            
        except ImportError:
            self.logger.warning("chromadb未安装，向量记忆功能不可用")
        except Exception as e:
            self.logger.error(f"初始化向量记忆失败: {e}")
    
    def add_short_term_memory(self, user_input: str, assistant_response: str):
        """添加短期记忆（对话上下文）
        
        适用于实时状态、当前偏好、对话上下文等高频访问数据
        """
        memory_item = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.datetime.now().isoformat(),
            'user_input': user_input,
            'assistant_response': assistant_response,
            'type': 'short_term'
        }
        self.short_term_memory.append(memory_item)
        
        # 限制短期记忆数量，保持内存高效
        if len(self.short_term_memory) > self.MAX_SHORT_TERM_MEMORY:
            self.short_term_memory = self.short_term_memory[-self.MAX_SHORT_TERM_MEMORY:]
        
        # 保存到缓存
        self._save_short_term_memory_to_cache()
    
    def _load_short_term_memory_from_cache(self):
        """从缓存加载短期记忆"""
        try:
            cached_memory = cache_manager.get_session_context(self.user_id)
            if cached_memory:
                self.short_term_memory = cached_memory
                self.logger.info(f"从缓存加载了 {len(cached_memory)} 条短期记忆")
        except Exception as e:
            self.logger.error(f"从缓存加载短期记忆失败: {e}")
    
    def _save_short_term_memory_to_cache(self):
        """保存短期记忆到缓存"""
        try:
            cache_manager.set_session_context(self.user_id, self.short_term_memory, max_length=20)
        except Exception as e:
            self.logger.error(f"保存短期记忆到缓存失败: {e}")
    
    def add_long_term_memory(self, content: str, importance: float = 0.5, tags: List[str] = None):
        """添加长期记忆（用户画像与长期习惯）
        
        Args:
            content: 记忆内容
            importance: 重要性评分 (0-1)
            tags: 标签列表
        """
        if tags is None:
            tags = []
        
        memory_item = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.datetime.now().isoformat(),
            'content': content,
            'importance': importance,
            'tags': tags,
            'type': 'long_term',
            'access_count': 0,
            'last_accessed': datetime.datetime.now().isoformat()
        }
        
        # 添加到内存
        self.long_term_memory.append(memory_item)
        
        # 保存到SQLite数据库
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO long_term_memories (
                    id, user_id, role, content, importance, tags, type, 
                    access_count, timestamp, last_accessed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    memory_item['id'],
                    self.user_id,
                    self.role,
                    memory_item['content'],
                    memory_item['importance'],
                    json.dumps(memory_item['tags']),
                    memory_item['type'],
                    memory_item['access_count'],
                    memory_item['timestamp'],
                    memory_item['last_accessed']
                ))
                
        except Exception as e:
            self.logger.error(f"保存长期记忆到数据库失败: {e}")
        
        # 同时添加到向量记忆
        if self.vector_memory_enabled:
            self._add_to_vector_memory(content, tags)
        
        self.logger.info(f"添加长期记忆: {content[:50]}... (重要性: {importance})")
    
    async def add_long_term_memory_async(self, content: str, importance: float = 0.5, tags: List[str] = None):
        """异步添加长期记忆"""
        if tags is None:
            tags = []
        
        memory_item = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.datetime.now().isoformat(),
            'content': content,
            'importance': importance,
            'tags': tags,
            'type': 'long_term',
            'access_count': 0,
            'last_accessed': datetime.datetime.now().isoformat()
        }
        
        # 添加到内存
        self.long_term_memory.append(memory_item)
        
        # 保存到SQLite数据库
        try:
            await self.execute_query_async('''
            INSERT INTO long_term_memories (
                id, user_id, role, content, importance, tags, type, 
                access_count, timestamp, last_accessed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_item['id'],
                self.user_id,
                self.role,
                memory_item['content'],
                memory_item['importance'],
                json.dumps(memory_item['tags']),
                memory_item['type'],
                memory_item['access_count'],
                memory_item['timestamp'],
                memory_item['last_accessed']
            ))
            
        except Exception as e:
            self.logger.error(f"异步保存长期记忆到数据库失败: {e}")
        
        # 同时添加到向量记忆
        if self.vector_memory_enabled:
            self._add_to_vector_memory(content, tags)
        
        self.logger.info(f"异步添加长期记忆: {content[:50]}... (重要性: {importance})")
    
    def _add_to_vector_memory(self, content: str, tags: List[str]):
        """将记忆添加到向量数据库"""
        try:
            doc_id = str(uuid.uuid4())
            metadata = {
                'type': 'memory',
                'tags': tags,
                'timestamp': datetime.datetime.now().isoformat(),
                'user_id': self.user_id
            }
            self.chroma_collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            self.logger.debug(f"已添加到向量记忆: {doc_id}")
        except Exception as e:
            self.logger.error(f"添加向量记忆失败: {e}")
    
    def search_memory(self, query: str, max_results: int = 5, include_vector_search: bool = True) -> List[Dict[str, Any]]:
        """搜索记忆
        
        Args:
            query: 查询文本
            max_results: 返回结果数量
            include_vector_search: 是否包含向量搜索
            
        Returns:
            匹配的记忆列表
        """
        results = []
        
        # 处理特殊查询："你还记得我吗"、"你认识我吗"等
        recognition_keywords = ['记得我', '认识我', '知道我', '我是谁']
        is_recognition_query = any(keyword in query for keyword in recognition_keywords)
        
        # 对于身份查询，优先搜索长期记忆中的身份信息，再搜索短期记忆
        if is_recognition_query:
            # 优先搜索长期记忆中的身份记忆
            identity_memories = []
            for memory in reversed(self.long_term_memory):
                if memory['content'].startswith('用户身份'):
                    identity_memories.append(memory)
            
            # 添加身份记忆到结果
            results.extend(identity_memories)
            
            # 如果还有剩余空间，添加短期记忆
            if len(results) < max_results:
                for memory in reversed(self.short_term_memory):
                    results.append(memory)
                    if len(results) >= max_results:
                        break
        else:
            # 1. 搜索短期记忆（普通查询）
            for memory in reversed(self.short_term_memory):
                if query in memory['user_input'] or query in memory['assistant_response']:
                    results.append(memory)
                    if len(results) >= max_results:
                        break
        
        # 2. 搜索长期记忆（普通查询）
        if not is_recognition_query:
            # 普通查询的搜索逻辑
            for memory in reversed(self.long_term_memory):
                if query in memory['content'] or any(query in tag for tag in memory['tags']):
                    memory['access_count'] += 1
                    memory['last_accessed'] = datetime.datetime.now().isoformat()
                    results.append(memory)
                    if len(results) >= max_results:
                        break
        
        # 更新数据库中的访问记录
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for memory in results:
                if memory.get('type') == 'long_term' or memory.get('type') is None:
                    try:
                        cursor.execute('''
                        UPDATE long_term_memories
                        SET access_count = ?, last_accessed = ?
                        WHERE id = ?
                        ''', (memory['access_count'], memory['last_accessed'], memory['id']))
                    except Exception as e:
                        self.logger.error(f"更新记忆访问记录失败: {e}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"批量更新记忆访问记录失败: {e}")
        
        # 3. 向量搜索（语义搜索）
        if include_vector_search and self.vector_memory_enabled and not is_recognition_query:
            try:
                vector_results = self.chroma_collection.query(
                    query_texts=[query],
                    n_results=min(max_results, 3)  # 限制向量搜索结果数量
                )
                
                for i, doc in enumerate(vector_results['documents'][0]):
                    vector_memory = {
                        'id': vector_results['ids'][0][i],
                        'content': doc,
                        'type': 'vector',
                        'similarity': vector_results.get('distances', [[0.0]])[0][i]
                    }
                    results.append(vector_memory)
            except Exception as e:
                self.logger.error(f"向量搜索失败: {e}")
        
        # 根据重要性、身份标识、访问次数和相似度排序
        # 对于身份记忆给予最高优先级，表格格式的旧记忆降低优先级
        results.sort(key=lambda x: (
            x.get('importance', 0.5) * 10 + (10 if x.get('content', '').startswith('用户身份') else 0),
            -30 if any(pattern in x.get('content', '') for pattern in ['| 角色 |', '|------|', '角色列表', '角色 |', '火元素安柏', '风元素琴', '冰元素凯亚', '雷元素丽莎', '水元素芭芭拉']) else 0,  # 表格格式和元素分类的旧记忆降低优先级
            x.get('access_count', 0),
            1.0 - x.get('similarity', 1.0)  # 相似度越高，值越大
        ), reverse=True)
        
        return results[:max_results]
    
    def extract_important_info(self, user_input: str, assistant_response: str) -> List[str]:
        """从对话中提取重要信息
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            
        Returns:
            提取的重要信息列表
        """
        important_info = []
        
        # 提取用户身份信息
        identity_keywords = ['我叫', '我的名字是', '我是', '我来自']
        for keyword in identity_keywords:
            if keyword in user_input:
                sentences = user_input.split('。')
                for sentence in sentences:
                    if keyword in sentence:
                        important_info.append("用户身份：" + sentence.strip() + "。")
        
        # 提取角色相关信息
        character_keywords = [
            '鹿野院平藏','珊瑚宫心海','罗莎莉亚','枫原万叶','艾尔海森','那维莱特','克洛琳德','阿蕾奇诺',
            '哥伦比娅','斯卡什哈','普契涅拉','达达利亚','雷电将军','神里绫华','神里绫人','八重神子',
            '荒泷一斗','九条裟罗','旅行者','迪卢克','芭芭拉','班尼特','诺艾尔','菲谢尔',
            '迪奥娜','阿贝多','提纳里','纳西妲','莱依拉','流浪者','珐露珊','坎蒂丝',
            '迪希雅','琳妮特','菲米尼','娜维娅','夏洛蒂','芙宁娜','希诺宁','玛薇卡',
            '基尼奇','桑多涅','久岐忍','埃洛伊','安柏','丽莎','凯亚','温迪',
            '可莉','砂糖','莫娜','甘雨','优菈','早柚','柯莱','多莉',
            '赛诺','妮露','白术','林尼','丑角','博士','散兵','女士',
            '钟离','刻晴','凝光','香菱','北斗','行秋','重云','七七',
            '胡桃','烟绯','云堇','夜兰','宵宫','五郎','托马','琴',
            '魈'
        ]
        for keyword in character_keywords:
            if keyword in user_input or keyword in assistant_response:
                full_text = user_input + " " + assistant_response
                sentences = full_text.split('。')
                for sentence in sentences:
                    if keyword in sentence:
                        important_info.append(sentence.strip() + "。")
                        break
        
        # 提取用户偏好信息
        preference_keywords = ['喜欢', '讨厌', '想要', '希望', '偏好', '喜欢用', '更喜欢']
        for keyword in preference_keywords:
            if keyword in user_input:
                sentences = user_input.split('。')
                for sentence in sentences:
                    if keyword in sentence:
                        important_info.append("用户偏好：" + sentence.strip() + "。")
        
        # 提取重要事件和活动
        event_keywords = ['任务', '活动', '更新', '版本', '新角色', '新武器', '活动', '副本']
        for keyword in event_keywords:
            if keyword in user_input or keyword in assistant_response:
                full_text = user_input + " " + assistant_response
                sentences = full_text.split('。')
                for sentence in sentences:
                    if keyword in sentence:
                        important_info.append("事件：" + sentence.strip() + "。")
        
        # 提取学习和游戏习惯
        habit_keywords = ['每天', '每周', '经常', '总是', '通常', '习惯']
        for keyword in habit_keywords:
            if keyword in user_input:
                sentences = user_input.split('。')
                for sentence in sentences:
                    if keyword in sentence:
                        important_info.append("用户习惯：" + sentence.strip() + "。")
        
        return important_info
    
    def process_dialogue(self, user_input: str, assistant_response: str):
        """处理对话，更新记忆
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
        """
        # 1. 添加短期记忆（对话上下文）
        self.add_short_term_memory(user_input, assistant_response)
        
        # 2. 提取重要信息并添加到长期记忆
        important_info = self.extract_important_info(user_input, assistant_response)
        for info in important_info:
            # 检查是否已经存在相似记忆
            exists = False
            for memory in self.long_term_memory:
                if info in memory['content'] or memory['content'] in info:
                    exists = True
                    break
            
            if not exists:
                # 确定重要性
                importance = 0.8 if '用户身份' in info else 0.7 if '用户偏好' in info else 0.5
                # 提取标签
                tags = self._extract_tags(info)
                self.add_long_term_memory(info, importance=importance, tags=tags)
    
    def _extract_tags(self, content: str) -> List[str]:
        """从内容中提取标签
        
        Args:
            content: 记忆内容
            
        Returns:
            标签列表
        """
        tags = []
        
        # 角色标签
        character_keywords = [
            '鹿野院平藏','珊瑚宫心海','罗莎莉亚','枫原万叶','艾尔海森','那维莱特','克洛琳德','阿蕾奇诺',
            '哥伦比娅','斯卡什哈','普契涅拉','达达利亚','雷电将军','神里绫华','神里绫人','八重神子',
            '荒泷一斗','九条裟罗','旅行者','迪卢克','芭芭拉','班尼特','诺艾尔','菲谢尔',
            '迪奥娜','阿贝多','提纳里','纳西妲','莱依拉','流浪者','珐露珊','坎蒂丝',
            '迪希雅','琳妮特','菲米尼','娜维娅','夏洛蒂','芙宁娜','希诺宁','玛薇卡',
            '基尼奇','桑多涅','久岐忍','埃洛伊','安柏','丽莎','凯亚','温迪',
            '可莉','砂糖','莫娜','甘雨','优菈','早柚','柯莱','多莉',
            '赛诺','妮露','白术','林尼','丑角','博士','散兵','女士',
            '钟离','刻晴','凝光','香菱','北斗','行秋','重云','七七',
            '胡桃','烟绯','云堇','夜兰','宵宫','五郎','托马','琴',
            '魈'
        ]
        for keyword in character_keywords:
            if keyword in content:
                tags.append(keyword)
        
        # 主题标签
        theme_keywords = {
            '用户身份': '身份',
            '用户偏好': '偏好',
            '喜欢': '偏好',
            '讨厌': '偏好',
            '任务': '任务',
            '活动': '活动',
            '更新': '版本',
            '新角色': '角色',
            '武器': '武器',
            '元素': '元素',
            '地区': '地区',
            '习惯': '习惯'
        }
        for keyword, tag in theme_keywords.items():
            if keyword in content:
                tags.append(tag)
        
        return tags
    
    def save_chat_history(self, role: str, content: str) -> bool:
        """保存聊天记录到数据库
        
        Args:
            role: 角色标识
            content: 聊天记录HTML内容
            
        Returns:
            是否保存成功
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 检查是否已存在该角色的聊天记录
                cursor.execute('''
                    SELECT id FROM chat_histories 
                    WHERE user_id = ? AND role = ?
                ''', (self.user_id, role))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有记录
                    cursor.execute('''
                        UPDATE chat_histories 
                        SET content = ?, timestamp = ?
                        WHERE id = ?
                    ''', (content, datetime.datetime.now().isoformat(), existing[0]))
                else:
                    # 创建新记录
                    history_id = str(uuid.uuid4())
                    cursor.execute('''
                        INSERT INTO chat_histories (id, user_id, role, content, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (history_id, self.user_id, role, content, datetime.datetime.now().isoformat()))
                
                self.logger.info(f"成功保存{role}角色的聊天记录")
                return True
                
        except Exception as e:
            self.logger.error(f"保存聊天记录失败: {e}")
            return False
    
    async def save_chat_history_async(self, role: str, content: str) -> bool:
        """异步保存聊天记录到数据库"""
        try:
            # 检查是否已存在该角色的聊天记录
            rows = await self.execute_query_async('''
                SELECT id FROM chat_histories 
                WHERE user_id = ? AND role = ?
            ''', (self.user_id, role))
            
            if rows:
                # 更新现有记录
                await self.execute_query_async('''
                    UPDATE chat_histories 
                    SET content = ?, timestamp = ?
                    WHERE id = ?
                ''', (content, datetime.datetime.now().isoformat(), rows[0]['id']))
            else:
                # 创建新记录
                history_id = str(uuid.uuid4())
                await self.execute_query_async('''
                    INSERT INTO chat_histories (id, user_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (history_id, self.user_id, role, content, datetime.datetime.now().isoformat()))
            
            self.logger.info(f"异步保存{role}角色的聊天记录成功")
            return True
            
        except Exception as e:
            self.logger.error(f"异步保存聊天记录失败: {e}")
            return False
    
    def load_chat_history(self, role: str) -> Optional[str]:
        """从数据库加载聊天记录
        
        Args:
            role: 角色标识
            
        Returns:
            聊天记录HTML内容，如果不存在返回None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT content FROM chat_histories 
                WHERE user_id = ? AND role = ?
            ''', (self.user_id, role))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                self.logger.info(f"成功加载{role}角色的聊天记录")
                return result[0]
            else:
                self.logger.info(f"{role}角色的聊天记录不存在")
                return None
                
        except Exception as e:
            self.logger.error(f"加载聊天记录失败: {e}")
            return None
    
    def get_recent_memory(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取最近的记忆
        
        Args:
            days: 天数
            
        Returns:
            最近的记忆列表
        """
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
        recent_memory = []
        
        for memory in self.long_term_memory:
            memory_time = datetime.datetime.fromisoformat(memory['timestamp'])
            if memory_time >= cutoff_time:
                recent_memory.append(memory)
        
        return recent_memory
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要
        
        Returns:
            记忆统计信息
        """
        return {
            'short_term_memory_count': len(self.short_term_memory),
            'long_term_memory_count': len(self.long_term_memory),
            'vector_memory_enabled': self.vector_memory_enabled,
            'most_accessed_memory': max(self.long_term_memory, 
                                     key=lambda x: x.get('access_count', 0), 
                                     default=None),
            'recent_memory_count': len(self.get_recent_memory()),
            'user_id': self.user_id
        }
    
    def clear_short_term_memory(self):
        """清空短期记忆"""
        self.short_term_memory = []
        # 清除缓存中的短期记忆
        cache_manager.clear_user_cache(self.user_id)
        self.logger.info("短期记忆已清空")
    
    def clear_long_term_memory(self):
        """清空长期记忆"""
        self.long_term_memory = []
        
        # 从SQLite数据库中删除
        try:
            self.cursor.execute('DELETE FROM long_term_memories WHERE user_id = ?', (self.user_id,))
            self.conn.commit()
            self.logger.info("数据库中的长期记忆已清空")
        except Exception as e:
            self.logger.error(f"清空数据库中的长期记忆失败: {e}")
        
        # 同时清空向量记忆
        if self.vector_memory_enabled:
            try:
                self.chroma_collection.delete(where={'user_id': self.user_id})
                self.logger.info("向量记忆已清空")
            except Exception as e:
                self.logger.error(f"清空向量记忆失败: {e}")
        
        self.logger.info("长期记忆已清空")
    
    def update_memory_importance(self, memory_id: str, importance: float):
        """更新记忆的重要性
        
        Args:
            memory_id: 记忆ID
            importance: 新的重要性评分 (0-1)
        """
        for memory in self.long_term_memory:
            if memory['id'] == memory_id:
                memory['importance'] = importance
                
                # 更新数据库
                try:
                    self.cursor.execute('''
                    UPDATE long_term_memories
                    SET importance = ?
                    WHERE id = ?
                    ''', (importance, memory_id))
                    self.conn.commit()
                    self.logger.info(f"更新记忆重要性: {memory_id} -> {importance}")
                except Exception as e:
                    self.logger.error(f"更新数据库中的记忆重要性失败: {e}")
                return
        self.logger.warning(f"记忆ID不存在: {memory_id}")
    
    def get_user_profile(self) -> Dict[str, Any]:
        """获取用户画像摘要
        
        Returns:
            用户画像信息
        """
        profile = {
            'user_id': self.user_id,
            'identity': [],
            'preferences': [],
            'habits': [],
            'interests': []
        }
        
        for memory in self.long_term_memory:
            content = memory['content']
            if '用户身份' in content:
                profile['identity'].append(content)
            elif '用户偏好' in content:
                profile['preferences'].append(content)
            elif '用户习惯' in content:
                profile['habits'].append(content)
            elif any(keyword in content for keyword in ['喜欢', '感兴趣', '想了解']):
                profile['interests'].append(content)
        
        return profile
    
    def __del__(self):
        """析构函数，关闭数据库连接"""
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
                self.logger.info("数据库连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭数据库连接时出错: {e}")
