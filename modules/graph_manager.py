import json
import sqlite3
import logging
from typing import List, Dict, Any, Optional

class GraphManager:
    """知识图谱管理器
    
    管理知识图谱的查询和操作，支持节点查询、关系查询等功能。
    """
    
    def __init__(self, db_path='data/graph_database.db'):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库连接"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.logger.info(f"知识图谱数据库连接成功: {self.db_path}")
        except Exception as e:
            self.logger.error(f"初始化知识图谱数据库失败: {e}")
            raise
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点信息
        
        Args:
            node_id: 节点ID
            
        Returns:
            节点信息，不存在则返回None
        """
        try:
            self.cursor.execute('''
            SELECT id, label, type, properties FROM graph_nodes WHERE id = ?
            ''', (node_id,))
            
            row = self.cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'label': row[1],
                    'type': row[2],
                    'properties': json.loads(row[3])
                }
            return None
            
        except Exception as e:
            self.logger.error(f"获取节点失败: {e}")
            return None
    
    def search_nodes(self, keyword: str, node_type: Optional[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """搜索节点
        
        Args:
            keyword: 搜索关键词
            node_type: 节点类型过滤
            max_results: 返回结果数量
            
        Returns:
            匹配的节点列表
        """
        try:
            if node_type:
                self.cursor.execute('''
                SELECT id, label, type, properties FROM graph_nodes
                WHERE type = ? AND (id LIKE ? OR label LIKE ?)
                LIMIT ?
                ''', (node_type, f'%{keyword}%', f'%{keyword}%', max_results))
            else:
                self.cursor.execute('''
                SELECT id, label, type, properties FROM graph_nodes
                WHERE id LIKE ? OR label LIKE ?
                LIMIT ?
                ''', (f'%{keyword}%', f'%{keyword}%', max_results))
            
            rows = self.cursor.fetchall()
            nodes = []
            for row in rows:
                nodes.append({
                    'id': row[0],
                    'label': row[1],
                    'type': row[2],
                    'properties': json.loads(row[3])
                })
            return nodes
            
        except Exception as e:
            self.logger.error(f"搜索节点失败: {e}")
            return []
    
    def get_related_nodes(self, node_id: str, relation_type: Optional[str] = None, max_results: int = 20) -> List[Dict[str, Any]]:
        """获取与指定节点相关的节点
        
        Args:
            node_id: 节点ID
            relation_type: 关系类型过滤
            max_results: 返回结果数量
            
        Returns:
            相关节点列表，包含关系信息
        """
        try:
            if relation_type:
                self.cursor.execute('''
                SELECT e.source, e.target, e.type, e.properties, n.id, n.label, n.type, n.properties
                FROM graph_edges e
                JOIN graph_nodes n ON e.target = n.id
                WHERE e.source = ? AND e.type = ?
                LIMIT ?
                ''', (node_id, relation_type, max_results))
            else:
                self.cursor.execute('''
                SELECT e.source, e.target, e.type, e.properties, n.id, n.label, n.type, n.properties
                FROM graph_edges e
                JOIN graph_nodes n ON e.target = n.id
                WHERE e.source = ?
                LIMIT ?
                ''', (node_id, max_results))
            
            rows = self.cursor.fetchall()
            results = []
            for row in rows:
                results.append({
                    'edge': {
                        'source': row[0],
                        'target': row[1],
                        'type': row[2],
                        'properties': json.loads(row[3])
                    },
                    'node': {
                        'id': row[4],
                        'label': row[5],
                        'type': row[6],
                        'properties': json.loads(row[7])
                    }
                })
            return results
            
        except Exception as e:
            self.logger.error(f"获取相关节点失败: {e}")
            return []
    
    def search_relations(self, source_id: Optional[str] = None, target_id: Optional[str] = None, 
                        relation_type: Optional[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """搜索关系
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            relation_type: 关系类型
            max_results: 返回结果数量
            
        Returns:
            关系列表
        """
        try:
            query = '''
            SELECT e.source, e.target, e.type, e.properties, 
                   s.id, s.label, s.type, s.properties,
                   t.id, t.label, t.type, t.properties
            FROM graph_edges e
            JOIN graph_nodes s ON e.source = s.id
            JOIN graph_nodes t ON e.target = t.id
            WHERE 1=1
            '''
            params = []
            
            if source_id:
                query += ' AND e.source = ?'
                params.append(source_id)
            if target_id:
                query += ' AND e.target = ?'
                params.append(target_id)
            if relation_type:
                query += ' AND e.type = ?'
                params.append(relation_type)
                
            query += ' LIMIT ?'
            params.append(max_results)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'source': {
                        'id': row[4],
                        'label': row[5],
                        'type': row[6],
                        'properties': json.loads(row[7])
                    },
                    'target': {
                        'id': row[8],
                        'label': row[9],
                        'type': row[10],
                        'properties': json.loads(row[11])
                    },
                    'relation': {
                        'type': row[2],
                        'properties': json.loads(row[3])
                    }
                })
            return results
            
        except Exception as e:
            self.logger.error(f"搜索关系失败: {e}")
            return []
    
    def query_graph(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """查询知识图谱
        
        这是主要的查询方法，用于处理用户的自然语言查询。
        
        Args:
            query: 查询文本
            max_results: 返回结果数量
            
        Returns:
            查询结果列表
        """
        results = []
        
        # 1. 首先搜索节点
        nodes = self.search_nodes(query, max_results=max_results)
        for node in nodes:
            # 获取节点的详细信息和相关关系
            related_nodes = self.get_related_nodes(node['id'], max_results=5)
            
            result = {
                'type': 'node',
                'content': node,
                'related': related_nodes[:3]  # 只返回前3个相关节点
            }
            results.append(result)
            
            if len(results) >= max_results:
                break
        
        # 2. 如果节点搜索结果不足，搜索关系
        if len(results) < max_results:
            # 提取查询中的关键词，只搜索与关键词相关的关系
            keywords = self._extract_keywords(query)
            if keywords:
                relations = self._search_relations_by_keywords(keywords, max_results=max_results - len(results))
                for relation in relations:
                    result = {
                        'type': 'relation',
                        'content': relation
                    }
                    results.append(result)
        
        return results[:max_results]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取文本中的关键词
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表
        """
        import re
        # 提取中文词语和英文单词
        chinese_pattern = re.compile(r'[\u4e00-\u9fa5]+')
        english_pattern = re.compile(r'[a-zA-Z]+')
        
        chinese_words = chinese_pattern.findall(text)
        english_words = english_pattern.findall(text)
        
        return chinese_words + english_words
    
    def _search_relations_by_keywords(self, keywords: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """通过关键词搜索关系
        
        Args:
            keywords: 关键词列表
            max_results: 返回结果数量
            
        Returns:
            关系列表
        """
        try:
            # 构建搜索条件
            conditions = []
            params = []
            
            for keyword in keywords:
                conditions.append('(s.label LIKE ? OR t.label LIKE ?)')
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            
            if not conditions:
                return []
            
            query = f'''
            SELECT e.source, e.target, e.type, e.properties, 
                   s.id, s.label, s.type, s.properties,
                   t.id, t.label, t.type, t.properties
            FROM graph_edges e
            JOIN graph_nodes s ON e.source = s.id
            JOIN graph_nodes t ON e.target = t.id
            WHERE {' OR '.join(conditions)}
            LIMIT ?
            '''
            params.append(max_results)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'source': {
                        'id': row[4],
                        'label': row[5],
                        'type': row[6],
                        'properties': json.loads(row[7])
                    },
                    'target': {
                        'id': row[8],
                        'label': row[9],
                        'type': row[10],
                        'properties': json.loads(row[11])
                    },
                    'relation': {
                        'type': row[2],
                        'properties': json.loads(row[3])
                    }
                })
            return results
            
        except Exception as e:
            self.logger.error(f"通过关键词搜索关系失败: {e}")
            return []
    
    def get_graph_summary(self) -> Dict[str, Any]:
        """获取知识图谱摘要
        
        Returns:
            图谱统计信息
        """
        try:
            self.cursor.execute('SELECT COUNT(*) FROM graph_nodes')
            node_count = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM graph_edges')
            edge_count = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT DISTINCT type FROM graph_nodes')
            node_types = [row[0] for row in self.cursor.fetchall()]
            
            self.cursor.execute('SELECT DISTINCT type FROM graph_edges')
            edge_types = [row[0] for row in self.cursor.fetchall()]
            
            return {
                'node_count': node_count,
                'edge_count': edge_count,
                'node_types': node_types,
                'edge_types': edge_types
            }
            
        except Exception as e:
            self.logger.error(f"获取图谱摘要失败: {e}")
            return {}
    
    def __del__(self):
        """析构函数，关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.logger.info("知识图谱数据库连接已关闭")
