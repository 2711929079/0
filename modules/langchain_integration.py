import logging
from typing import Optional, List
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from config import config
from modules.query_rewrite import QueryRewrite
from modules.cache_manager import cache_manager
from modules.prompt_hook import prompt_hook

# 导入嵌入模型
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    EMBEDDING_AVAILABLE = True
except ImportError:
    try:
        from langchain.embeddings import HuggingFaceEmbeddings
        EMBEDDING_AVAILABLE = True
    except ImportError:
        EMBEDDING_AVAILABLE = False

def clean_html_content(html_content):
    """
    清洗HTML，提取正文、表格内容和图片文字
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除无用标签
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside',
                     'noscript', 'meta', 'link']):
        tag.decompose()
    
    # 专门处理表格内容
    table_contents = []
    for table in soup.find_all('table'):
        # 提取表格标题
        caption = table.find('caption')
        table_title = caption.get_text(strip=True) if caption else "表格"
        
        table_text = [f"【表格】{table_title}"]
        
        # 提取表头
        headers = []
        for th in table.find_all('th'):
            headers.append(th.get_text(strip=True))
        
        # 提取表格行
        rows = []
        for tr in table.find_all('tr'):
            row = []
            for td in tr.find_all('td'):
                row.append(td.get_text(strip=True))
            if row:
                rows.append(row)
        
        # 格式化表格内容
        if headers:
            table_text.append(" | ".join(headers))
            table_text.append("-" * len(" | ".join(headers)))
        
        for row in rows:
            table_text.append(" | ".join(row))
        
        table_contents.append("\n".join(table_text))
    
    # 专门处理图片内容
    image_contents = []
    for img in soup.find_all('img'):
        alt_text = img.get('alt', '')
        title_text = img.get('title', '')
        if alt_text or title_text:
            img_text = "【图片】"
            if alt_text:
                img_text += f"描述: {alt_text}"
            if title_text:
                img_text += f"，标题: {title_text}"
            image_contents.append(img_text)
    
    # 提取正文（不包含表格和图片，因为已经单独提取）
    for table in soup.find_all('table'):
        table.decompose()
    for img in soup.find_all('img'):
        img.decompose()
    
    text = soup.get_text(separator='\n', strip=True)
    
    # 合并所有内容
    all_content = []
    if text:
        all_content.append(text)
    if table_contents:
        all_content.extend(table_contents)
    if image_contents:
        all_content.extend(image_contents)
    
    combined_text = '\n\n'.join(all_content)
    
    # 清理空行和特殊字符
    combined_text = re.sub(r'\n\s*\n', '\n\n', combined_text)  # 合并多余空行
    combined_text = re.sub(r'[ \t]+', ' ', combined_text)       # 合并多余空格
    combined_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', combined_text)  # 移除控制字符
    
    return combined_text

def extract_main_content_for_moegirl(url):
    """
    专门针对萌娘百科的正文提取，提取完整内容
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://zh.moegirl.org.cn/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        
        # 提取页面标题
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        page_title = title_match.group(1) if title_match else ""
        
        # 移除脚本和样式标签
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # 移除所有HTML标签
        text = re.sub(r'<[^>]+>', '\n', html_content)
        
        # 清理文本
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            # 过滤掉空行和太短的行
            if line and len(line) > 10:
                # 过滤掉JavaScript相关的内容和无意义的文本
                if (('JavaScript' not in line) and 
                    ('js' not in line.lower()) and
                    ('require' not in line.lower()) and
                    ('window.' not in line) and
                    ('mw.' not in line) and
                    ('RLQ' not in line) and
                    ('userNameInText' not in line) and
                    ('mw-content-text' not in line) and
                    ('mw-body-content' not in line) and
                    ('mw-parser-output' not in line) and
                    ('nomobile' not in line) and
                    ('mw-file-element' not in line) and
                    ('data-artwork-id' not in line) and
                    ('data-noteta-code' not in line) and
                    ('heimu' not in line) and
                    ('plainlinks' not in line) and
                    ('template-ruby' not in line)):
                    filtered_lines.append(line)
        
        # 合并文本
        result = '\n\n'.join(filtered_lines)
        
        # 进一步清理
        result = re.sub(r'\n\s*\n', '\n\n', result)
        result = re.sub(r'[ \t]+', ' ', result)
        
        # 如果有页面标题，添加到开头
        if page_title:
            result = f"# {page_title}\n\n{result}"
        
        return result
        
    except Exception as e:
        print(f"萌娘百科提取失败: {e}")
        # 返回备用内容
        return f"萌娘百科页面提取失败: {str(e)}"

def extract_moegirl_content_with_backup(url):
    """备用提取方法，处理JavaScript动态加载"""
    try:
        # 使用更复杂的请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        # 尝试从页面中提取有用信息
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取所有可见文本
        all_text = []
        
        # 提取页面标题
        page_title = soup.title.string if soup.title else ""
        if page_title:
            all_text.append(f"# {page_title}")
        
        # 提取所有段落文本
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 20:
                all_text.append(text)
        
        # 提取标题
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        for heading in headings:
            text = heading.get_text(strip=True)
            if text:
                all_text.append(f"\n## {text}")
        
        # 提取列表内容
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            items = lst.find_all('li')
            if items:
                list_text = []
                for item in items:
                    item_text = item.get_text(strip=True)
                    if item_text and len(item_text) > 10:
                        list_text.append(f"- {item_text}")
                if list_text:
                    all_text.append('\n'.join(list_text))
        
        # 合并结果
        result = '\n'.join(all_text)
        
        # 如果内容仍然太少，返回默认信息
        if len(result) < 200:
            result = f"""# 萌娘百科页面内容

由于网站使用JavaScript动态加载，无法直接提取完整内容。

## 页面信息
- URL: {url}
- 提取方式: 静态内容提取
- 说明: 萌娘百科网站使用JavaScript动态渲染内容，完整内容需要在浏览器中查看

## 建议
- 在浏览器中直接访问该页面以查看完整内容
- 或使用支持JavaScript渲染的爬虫工具提取
"""
        
        return result
        
    except Exception as e:
        return f"萌娘百科页面提取失败: {str(e)}"

class LangChainIntegration:
    def __init__(self, role: str = "ying"):
        self.logger = logging.getLogger(__name__)
        self.has_api_key = hasattr(config, 'API_KEY') and config.API_KEY
        self.role = role  # 角色标识：ying（荧）或 paimon（派蒙）
        
        # 初始化知识库
        self.knowledge_base_text = ""
        
        # 初始化Chroma向量数据库（父文档检索架构）
        self.chroma_client = None
        self.parent_collection = None  # 父文档集合（用于生成）
        self.child_collection = None   # 子文档集合（用于检索）
        self._init_chroma()
        
        # 初始化知识图谱
        self.knowledge_graph = None
        self._load_knowledge_graph()
        
        # 初始化查询重写模块
        self.query_rewrite = QueryRewrite()
        
        # 添加查询缓存
        self.query_cache = {}
        self.cache_max_size = 100  # 缓存最大条目数
        
        # 缓存预热：预加载常见查询
        self._warmup_cache()
        
    def _warmup_cache(self):
        """缓存预热：预加载常见查询到缓存中"""
        self.logger.info("开始缓存预热...")
        
        # 常见查询列表
        common_queries = [
            "介绍一下可莉",
            "胡桃是谁",
            "钟离的背景故事",
            "雷神的技能",
            "提纳里和柯莱的关系",
            "枫丹有哪些角色",
            "璃月七星都是谁",
            "蒙德的角色有哪些",
            "稻妻的角色介绍",
            "须弥的角色",
            "大丘丘病了，二丘丘瞧"
        ]
        
        # 预加载缓存（使用简单的模拟回答，避免调用LLM）
        warmup_data = {
            "介绍一下可莉": "可莉是蒙德西风骑士团的火花骑士，非常可爱的小女孩，喜欢制造炸弹，总是给蒙德带来惊喜和麻烦。",
            "胡桃是谁": "胡桃是往生堂第七十七代堂主，古灵精怪的女孩，总是带着笑容。",
            "钟离的背景故事": "钟离是璃月的岩王帝君，化身为人形在尘世闲游，见证了璃月的千年变迁。",
            "雷神的技能": "雷神是稻妻的雷电将军，追求永恒的统治者，拥有强大的元素能力。",
            "提纳里和柯莱的关系": "提纳里是柯莱的老师，柯莱在道成林跟着提纳里学习，准备成为一名巡林员。",
            "枫丹有哪些角色": "枫丹的角色包括那维莱特、芙宁娜、林尼、林尼特、菲米尼等。",
            "璃月七星都是谁": "璃月七星包括刻晴、凝光、天枢星、天璇星、天玑星、天权星、玉衡星。",
            "蒙德的角色有哪些": "蒙德的角色包括安柏、琴、凯亚、迪卢克、温迪、可莉、芭芭拉等。",
            "稻妻的角色介绍": "稻妻的角色包括雷电将军、神里绫华、枫原万叶、宵宫、托马、珊瑚宫心海等。",
            "须弥的角色": "须弥的角色包括纳西妲、赛诺、提纳里、柯莱、艾尔海森、卡维等。",
            "大丘丘病了，二丘丘瞧": "这句话是胡桃的语音台词之一，体现了她古灵精怪的性格特点。"
        }
        
        # 加载缓存
        for query, response in warmup_data.items():
            self.query_cache[query] = response
        
        self.logger.info(f"缓存预热完成，预加载了 {len(warmup_data)} 条缓存")
        
    def _init_chroma(self):
        """初始化Chroma数据库（父文档检索架构）"""
        try:
            import chromadb
            
            # 创建Chroma客户端
            self.chroma_client = chromadb.PersistentClient(path="./data/chroma_db")
            
            # 创建中文嵌入模型配置
            embedding_model = None
            if EMBEDDING_AVAILABLE:
                try:
                    embedding_model = HuggingFaceEmbeddings(
                        model_name="paraphrase-multilingual-MiniLM-L12-v2",
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                    self.logger.info("多语言嵌入模型初始化成功")
                except Exception as e:
                    self.logger.warning(f"嵌入模型初始化失败，使用默认嵌入: {e}")
            
            # 创建父文档集合（用于生成，1024 tokens）
            self.parent_collection = self.chroma_client.get_or_create_collection(
                name="genshin_knowledge_parent",
                metadata={"hnsw:space": "cosine"}
            )
            
            # 创建子文档集合（用于检索，256 tokens）
            self.child_collection = self.chroma_client.get_or_create_collection(
                name="genshin_knowledge_child",
                metadata={"hnsw:space": "cosine"}
            )
            
            self.logger.info("Chroma向量数据库（父文档检索架构）初始化成功")
            
        except ImportError:
            self.logger.warning("chromadb未安装，向量数据库功能不可用")
        except Exception as e:
            self.logger.error(f"初始化Chroma数据库失败: {e}")
    
    def _load_knowledge_graph(self):
        """加载知识图谱"""
        try:
            graph_file = "genshin_complete_graph.json"
            if os.path.exists(graph_file):
                with open(graph_file, 'r', encoding='utf-8') as f:
                    self.knowledge_graph = json.load(f)
                self.logger.info(f"成功加载知识图谱，包含 {len(self.knowledge_graph['nodes'])} 个节点和 {len(self.knowledge_graph['edges'])} 条关系")
                
                # 构建知识图谱倒排索引
                if hasattr(self, 'query_rewrite') and self.query_rewrite:
                    self.query_rewrite.build_inverted_index(self.knowledge_graph)
            else:
                self.logger.warning("知识图谱文件不存在")
        except Exception as e:
            self.logger.error(f"加载知识图谱失败: {e}")
    
    def search_web(self, query: str) -> str:
        """搜索网络获取最新信息
        
        Args:
            query: 搜索关键词
            
        Returns:
            搜索结果摘要
        """
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                self.logger.info(f"正在搜索网络: {query} (尝试 {retry_count+1}/{max_retries+1})")
                
                # 优先使用Bing搜索API
                if hasattr(config, 'BING_API_KEY') and config.BING_API_KEY:
                    url = "https://api.bing.microsoft.com/v7.0/search"
                    headers = {"Ocp-Apim-Subscription-Key": config.BING_API_KEY}
                    params = {"q": query, "count": 5, "responseFilter": "Webpages"}
                    
                    response = requests.get(url, headers=headers, params=params, timeout=5)
                    response.raise_for_status()
                    
                    results = response.json()
                    if "webPages" in results and "value" in results["webPages"]:
                        summaries = []
                        for i, page in enumerate(results["webPages"]["value"][:3]):
                            # 过滤掉与原神无关的结果
                            if any(keyword in page['name'] or keyword in page['snippet'] 
                                  for keyword in ['原神', '提瓦特', '蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬']):
                                summaries.append(f"{page['name']}: {page['snippet']}")
                        if summaries:
                            return "\n".join(summaries)
                        else:
                            return "未找到相关搜索结果"
                    else:
                        return "未找到搜索结果"
                else:
                    # 使用DuckDuckGo免费API
                    duckduckgo_url = "https://api.duckduckgo.com/"
                    params = {
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1
                    }
                    
                    response = requests.get(duckduckgo_url, params=params, timeout=5)
                    response.raise_for_status()
                    
                    results = response.json()
                    summaries = []
                    
                    # 提取摘要信息
                    if "AbstractText" in results and results["AbstractText"]:
                        summaries.append(f"{results['AbstractText']}")
                    
                    # 提取相关主题
                    if "RelatedTopics" in results and results["RelatedTopics"]:
                        for topic in results["RelatedTopics"][:3]:
                            if "Text" in topic:
                                summaries.append(f"{topic['Text']}")
                            elif "Result" in topic:
                                summaries.append(f"{topic['Result']}")
                    
                    if summaries:
                        # 过滤搜索结果，只保留与原神相关的内容
                        filtered_summaries = []
                        for summary in summaries:
                            if any(keyword in summary 
                                  for keyword in ['原神', '提瓦特', '蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬']):
                                filtered_summaries.append(summary)
                        if filtered_summaries:
                            return "\n".join(filtered_summaries)
                        else:
                            return "未找到相关搜索结果"
                    else:
                        return f"搜索结果：关于'{query}'的信息未找到"
                        
            except requests.exceptions.Timeout:
                self.logger.warning(f"搜索超时，正在重试...")
                retry_count += 1
                if retry_count > max_retries:
                    self.logger.error(f"搜索多次超时，放弃搜索")
                    return "搜索超时，请稍后再试"
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"网络连接错误，正在重试...")
                retry_count += 1
                if retry_count > max_retries:
                    self.logger.error(f"网络连接多次失败，放弃搜索")
                    return "网络连接失败，请检查网络设置"
            except Exception as e:
                self.logger.error(f"搜索失败: {e}")
                return f"搜索失败: {str(e)[:100]}"
        
        return "搜索失败，请稍后再试"
    
    def get_current_time(self) -> str:
        """获取当前时间和日期
        
        Returns:
            当前时间和日期
        """
        import datetime
        now = datetime.datetime.now()
        return now.strftime("%Y年%m月%d日 %H:%M:%S")
    
    def query_knowledge_base(self, query: str, n_results: int = 3) -> List[str]:
        """查询向量数据库（混合检索策略）
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            
        Returns:
            相关文档列表
        """
        if not self.child_collection or not self.parent_collection:
            self.logger.warning("向量数据库未初始化")
            return []
        
        try:
            # 检查缓存
            cached_result = cache_manager.get_rag_result(query)
            if cached_result:
                self.logger.info(f"从缓存获取查询结果: {query}")
                return cached_result
            
            # 使用查询重写模块处理查询
            rewritten_query, processing_info = self.query_rewrite.rewrite_query(query)
            self.logger.info(f"向量数据库查询: {rewritten_query}")
            
            # 提取关键词用于混合检索
            query_keywords = self.query_rewrite.extract_keywords(rewritten_query)
            stop_words = {'你', '知道', '吗', '的', '了', '是', '在', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '这个', '那个'}
            # 特殊处理单字符角色名（如"魈"、"琴"）
            single_char_characters = ['魈', '琴']
            filtered_keywords = [kw for kw in query_keywords if kw not in stop_words and (len(kw) > 1 or kw in single_char_characters)]
            
            # 混合检索策略：结合向量相似度和关键词匹配
            candidate_docs = []
            
            # 获取所有文档进行关键词匹配
            all_docs = self.child_collection.get()
            
            # 策略0：优先匹配web知识文档（最高优先级）
            if filtered_keywords:
                for doc, meta in zip(all_docs['documents'], all_docs['metadatas']):
                    # 检查是否为web知识文档
                    if meta.get('type') == 'web_knowledge':
                        title = meta.get('title', '')
                        doc_text = f"{title} {doc}"
                        # 检查标题和内容中的关键词匹配
                        title_matches = [kw for kw in filtered_keywords if kw in title]
                        content_matches = [kw for kw in filtered_keywords if kw in doc_text]
                        
                        if title_matches or content_matches:
                            # web知识文档获得最高优先级分数
                            web_score = 20.0 + (len(title_matches) * 4.0) + (len(content_matches) * 2.0)
                            
                            # 增加角色名称匹配的权重（如果标题包含角色名称）
                            character_names = ['枫原万叶', '神里绫华', '达达利亚', '优菈', '温迪', '雷电将军', '钟离', '纳西妲', '胡桃', '甘雨', '魈', '班尼特', '行秋', '香菱', '迪奥娜', '安柏', '丽莎', '凯亚', '琴', '迪卢克', '可莉', '芭芭拉', '诺艾尔', '菲谢尔', '莫娜', '雷泽', '阿贝多', '罗莎莉亚', '砂糖', '刻晴', '凝光', '北斗', '重云', '七七', '夜兰', '烟绯', '云堇', '申鹤', '白术', '辛焱', '闲云', '嘉明', '宵宫', '神里绫人', '八重神子', '珊瑚宫心海', '九条裟罗', '五郎', '托马', '早柚', '久岐忍', '荒泷一斗', '鹿野院平藏', '千织', '绮良良', '梦见月瑞希', '提纳里', '柯莱', '多莉', '赛诺', '妮露', '流浪者', '艾尔海森', '珐露珊', '莱依拉', '迪希雅', '瑶瑶', '卡维', '坎蒂丝', '塔利雅', '琳妮特', '林尼', '菲米尼', '娜维娅', '芙宁娜', '莱欧斯利', '希诺宁', '夏洛蒂', '克洛琳德', '艾梅莉埃', '旅行者', '埃洛伊', '散兵', '阿蕾奇诺', '哥伦比娅', '桑多涅', '普契涅拉', '丑角', '博士', '女士', '玛薇卡', '基尼奇', '菈乌玛', '菲林斯', '爱诺', '兹白', '那维莱特']
                            for char_name in character_names:
                                if char_name in title and char_name in filtered_keywords:
                                    web_score += 50.0  # 角色名称精确匹配获得大幅加分
                                    # 如果标题完全匹配角色名称+技能，再额外加分
                                    if f"{char_name}技能" in title or f"{char_name}技能详细介绍" in title:
                                        web_score += 30.0
                            
                            # 检查是否已存在，保留最高得分
                            exists = False
                            for i, (_, existing_meta, existing_score, _) in enumerate(candidate_docs):
                                if existing_meta.get('id') == meta.get('id'):
                                    if web_score > existing_score:
                                        candidate_docs[i] = (doc, meta, web_score, 'web_knowledge')
                                    exists = True
                                    break
                            if not exists:
                                candidate_docs.append((doc, meta, web_score, 'web_knowledge'))
            
            # 策略1：标题关键词匹配（高优先级）
            if filtered_keywords:
                self.logger.info(f"使用关键词: {filtered_keywords}")
                
                for doc, meta in zip(all_docs['documents'], all_docs['metadatas']):
                    # 跳过已经匹配的web知识文档
                    if meta.get('type') == 'web_knowledge':
                        continue
                        
                    title = meta.get('title', '')
                    if title:
                        title_matches = [kw for kw in filtered_keywords if kw in title]
                        if title_matches:
                            title_score = 15.0 + (len(title_matches) * 3.0)
                            # 检查是否已存在，保留最高得分
                            exists = False
                            for i, (_, existing_meta, existing_score, _) in enumerate(candidate_docs):
                                if existing_meta.get('id') == meta.get('id'):
                                    if title_score > existing_score:
                                        candidate_docs[i] = (doc, meta, title_score, 'title')
                                    exists = True
                                    break
                            if not exists:
                                candidate_docs.append((doc, meta, title_score, 'title'))
            
            # 策略2：内容关键词精确匹配（中优先级）
            if filtered_keywords:
                for doc, meta in zip(all_docs['documents'], all_docs['metadatas']):
                    # 跳过已经匹配的web知识文档
                    if meta.get('type') == 'web_knowledge':
                        continue
                        
                    doc_text = f"{meta.get('title', '')} {doc}"
                    matched_keywords = [kw for kw in filtered_keywords if kw in doc_text]
                    
                    if matched_keywords:
                        # 根据匹配关键词的数量和重要性计算得分
                        match_score = 12.0 + (len(matched_keywords) * 2.0)
                        # 检查是否已存在，保留最高得分
                        exists = False
                        for i, (_, existing_meta, existing_score, _) in enumerate(candidate_docs):
                            if existing_meta.get('id') == meta.get('id'):
                                if match_score > existing_score:
                                    candidate_docs[i] = (doc, meta, match_score, 'keyword')
                                exists = True
                                break
                        if not exists:
                            candidate_docs.append((doc, meta, match_score, 'keyword'))
            
            # 策略3：向量相似度检索（补充方法）
            vector_results = self.child_collection.query(
                query_texts=[rewritten_query],
                n_results=10  # 减少召回数量提高速度
            )
            
            self.logger.info(f"向量检索找到 {len(vector_results['documents'][0])} 个文档")
            
            # 将向量检索结果加入候选列表
            for doc, meta, score in zip(
                vector_results['documents'][0],
                vector_results['metadatas'][0],
                vector_results['distances'][0]
            ):
                # 将距离转换为相似度得分（距离越小越相似）
                similarity_score = 8.0 - (score * 5.0)
                # 检查是否已存在，保留最高得分
                exists = False
                for i, (_, existing_meta, existing_score, _) in enumerate(candidate_docs):
                    if existing_meta.get('id') == meta.get('id'):
                        if similarity_score > existing_score:
                            candidate_docs[i] = (doc, meta, similarity_score, 'vector')
                        exists = True
                        break
                if not exists:
                    candidate_docs.append((doc, meta, similarity_score, 'vector'))
            
            # 综合排序：按得分降序排列
            candidate_docs.sort(key=lambda x: x[2], reverse=True)
            
            # 智能去重：保持得分最高的版本
            seen_ids = {}
            unique_docs = []
            for doc, meta, score, source in candidate_docs:
                doc_id = meta.get('id', '')
                if doc_id:
                    if doc_id not in seen_ids or score > seen_ids[doc_id]:
                        seen_ids[doc_id] = score
                        unique_docs.append((doc, meta, score, source))
                else:
                    # 如果没有ID，使用标题或内容作为标识
                    doc_title = meta.get('title', '') or doc[:50]
                    if doc_title not in seen_ids or score > seen_ids[doc_title]:
                        seen_ids[doc_title] = score
                        unique_docs.append((doc, meta, score, source))
            
            self.logger.info(f"混合检索后候选文档数: {len(unique_docs)}")
            
            # 返回前n_results个结果
            documents = []
            
            # 优先返回web知识文档
            web_docs = []
            other_docs = []
            
            for doc, meta, score, source in unique_docs:
                if meta.get('type') == 'web_knowledge':
                    web_docs.append((doc, meta, score, source))
                else:
                    other_docs.append((doc, meta, score, source))
            
            # 合并结果：先返回web知识文档，再返回其他文档
            combined_docs = web_docs + other_docs
            
            # 返回指定数量的结果
            for doc, meta, score, source in combined_docs[:n_results]:
                # 构建包含标题和来源信息的文档
                full_doc = f"# {meta.get('title', '')}\n\n{doc}"
                documents.append(full_doc)
                self.logger.info(f"选中文档: {meta.get('title', '未知')} (来源: {source}, 得分: {score:.2f}, 类型: {meta.get('type', 'unknown')})")
            
            self.logger.info(f"最终返回 {len(documents)} 个文档，其中web知识文档 {len(web_docs)} 个")
            
            # 缓存结果
            cache_manager.set_rag_result(query, documents)
            
            return documents
            
        except Exception as e:
            self.logger.error(f"查询向量数据库失败: {e}")
            return []
    
    def _extract_subpages(self, url):
        """从页面中提取子页面链接
        
        Args:
            url: 当前页面URL
            
        Returns:
            子页面URL列表
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.5,en-US;q=0.3',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Referer': 'https://wiki.biligame.com/'
            }
            
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            subpages = []
            base_domain = 'https://wiki.biligame.com'
            
            # 提取所有内部链接
            for a in soup.find_all('a', href=True):
                href = a['href']
                
                # 只处理B站WIKI的内部链接
                if href.startswith('/ys/') and not href.startswith('/ys/index.php'):
                    full_url = f"{base_domain}{href}"
                    
                    # 过滤掉外部链接、特殊页面和参考文献
                    if (full_url not in subpages and 
                        not 'javascript:' in href and
                        not '#' in href and
                        not href.endswith('.png') and
                        not href.endswith('.jpg') and
                        not href.endswith('.gif') and
                        not '参考文献' in a.get_text() and
                        not '参考资料' in a.get_text() and
                        not '来源' in a.get_text() and
                        not '链接' in a.get_text() and
                        not '外部链接' in a.get_text()):
                        
                        # 过滤参考文献区域的链接
                        parent = a.parent
                        while parent:
                            if parent.name in ['div', 'section', 'span']:
                                if ('reference' in parent.get('class', []) or 
                                    'reference-list' in parent.get('class', []) or
                                    'refs' in parent.get('class', []) or
                                    'bibliography' in parent.get('class', [])):
                                    break
                            parent = parent.parent
                        else:
                            subpages.append(full_url)
            
            self.logger.info(f"从 {url} 提取到 {len(subpages)} 个子页面")
            return subpages
            
        except Exception as e:
            self.logger.error(f"提取子页面失败: {e}")
            return []
    
    def _generate_summary(self, text):
        """为内容生成简短简介
        
        Args:
            text: 文本内容
            
        Returns:
            简介文本
        """
        # 使用前150个字符作为简介，确保简介简短有效
        return text[:150] + "..." if len(text) > 150 else text
    
    def _split_content_into_chunks(self, content, url, global_chunk_counter):
        """将内容分割为带简介的块
        
        Args:
            content: 网页内容
            url: 来源URL
            global_chunk_counter: 全局块计数器
            
        Returns:
            内容块列表，每个块包含id、content和metadata
        """
        chunks = []
        
        # 按标题分割内容（支持Markdown风格的标题）
        sections = re.split(r'(#{1,3}\s+.+)', content)
        
        current_section = None
        chunk_count = 0
        
        for i in range(len(sections)):
            if sections[i].startswith('#'):
                # 保存当前区块（如果有）
                if current_section:
                    # 将区块内容分割为固定大小的块（500字符，重叠100字符）
                    section_chunks = self._split_text_into_fixed_chunks(
                        current_section['content'], 
                        chunk_size=500,
                        overlap=100
                    )
                    
                    # 为每个块生成简介
                    for j, chunk_text in enumerate(section_chunks):
                        if chunk_text.strip():
                            summary = self._generate_summary(chunk_text)
                            chunk_id = f"chunk_{global_chunk_counter}"
                            chunk_content = f"来源: {url}\n{'=' * 80}\n标题: {current_section['title']}\n{'=' * 80}\n简介: {summary}\n{'=' * 80}\n{chunk_text}"
                            chunks.append({
                                'id': chunk_id,
                                'content': chunk_content,
                                'metadata': {'source': url, 'title': current_section['title'], 'chunk_index': j}
                            })
                            global_chunk_counter += 1
                            chunk_count += 1
                
                # 开始新的区块
                current_section = {
                    'title': sections[i].strip('# '),
                    'content': ''
                }
            elif current_section is not None:
                current_section['content'] += sections[i]
        
        # 添加最后一个区块（如果有）
        if current_section and current_section['content'].strip():
            # 将区块内容分割为固定大小的块
            section_chunks = self._split_text_into_fixed_chunks(
                current_section['content'], 
                chunk_size=500,
                overlap=100
            )
            
            for j, chunk_text in enumerate(section_chunks):
                if chunk_text.strip():
                    summary = self._generate_summary(chunk_text)
                    chunk_id = f"chunk_{global_chunk_counter}"
                    chunk_content = f"来源: {url}\n{'=' * 80}\n标题: {current_section['title']}\n{'=' * 80}\n简介: {summary}\n{'=' * 80}\n{chunk_text}"
                    chunks.append({
                        'id': chunk_id,
                        'content': chunk_content,
                        'metadata': {'source': url, 'title': current_section['title'], 'chunk_index': j}
                    })
                    global_chunk_counter += 1
        
        # 如果没有按标题分割成功，将整个内容分割为固定大小的块
        if not chunks and content.strip():
            # 将内容分割为固定大小的块
            content_chunks = self._split_text_into_fixed_chunks(
                content, 
                chunk_size=500,
                overlap=100
            )
            
            for j, chunk_text in enumerate(content_chunks):
                if chunk_text.strip():
                    summary = self._generate_summary(chunk_text)
                    chunk_id = f"chunk_{global_chunk_counter}"
                    chunk_content = f"来源: {url}\n{'=' * 80}\n标题: 页面内容\n{'=' * 80}\n简介: {summary}\n{'=' * 80}\n{chunk_text}"
                    chunks.append({
                        'id': chunk_id,
                        'content': chunk_content,
                        'metadata': {'source': url, 'title': '页面内容', 'chunk_index': j}
                    })
                    global_chunk_counter += 1
        
        return chunks, global_chunk_counter
    
    def _split_text_into_fixed_chunks(self, text, chunk_size=500, overlap=100):
        """将文本分割为固定大小的块，相邻块之间有重叠
        
        Args:
            text: 要分割的文本
            chunk_size: 每个块的大小（字符数）
            overlap: 相邻块之间的重叠大小（字符数）
            
        Returns:
            分割后的块列表
        """
        chunks = []
        total_length = len(text)
        
        if total_length <= chunk_size:
            chunks.append(text)
            return chunks
        
        start = 0
        while start < total_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            # 移动到下一个块的起始位置（考虑重叠）
            start += chunk_size - overlap
            
            # 如果剩余内容不足一个完整块，添加最后一个块
            if start + chunk_size > total_length:
                chunks.append(text[total_length - chunk_size:])
                break
        
        return chunks
    
    def load_knowledge_base(self, urls: List[str], force_reload: bool = False):
        """加载知识库（已改为使用预处理的文档块）
        
        Args:
            urls: 知识库网页URL列表
            force_reload: 是否强制重新加载，即使数据库中已有数据
        """
        if not urls:
            self.logger.info("知识库URL列表为空，跳过加载")
            return False
            
        # 检查向量数据库中是否已有数据
        if self.parent_collection and self.child_collection and not force_reload:
            try:
                parent_count = self.parent_collection.count()
                child_count = self.child_collection.count()
                if parent_count > 0 or child_count > 0:
                    self.logger.info(f"向量数据库中已有 {parent_count} 个父文档和 {child_count} 个子文档，跳过加载")
                    return True
            except Exception as e:
                self.logger.error(f"检查数据库状态失败: {e}")
        
        # 数据已通过write_to_chroma_db.py脚本预加载
        # 如果数据库为空，提示用户运行导入脚本
        self.logger.warning("向量数据库为空，请运行 write_to_chroma_db.py 脚本导入数据")
        return False
    
    def run_agent(self, query: str, llm_instance=None) -> str:
        """运行Agent处理查询
        
        Args:
            query: 用户查询
            llm_instance: LLM实例，如果不提供则创建新实例
            
        Returns:
            Agent的回答，如果没有API密钥则返回None
        """
        try:
            # 检查缓存
            cache_key = query.strip()
            if cache_key in self.query_cache:
                self.logger.info(f"命中缓存: {cache_key}")
                return self.query_cache[cache_key]
            self.logger.info(f"处理查询: {query}")
            self.logger.info(f"查询长度: {len(query)}")
            self.logger.info(f"查询类型: {type(query)}")
            
            # 并行处理：提取实体和查询重写
            import concurrent.futures
            
            # 定义并行任务
            def extract_history_entities():
                """从对话历史中提取实体"""
                history_entities = []
                if llm_instance and hasattr(llm_instance, 'conversation_history'):
                    history = llm_instance.get_history()
                    for message in reversed(history):
                        content = message.get('content', '')
                        keywords = self.query_rewrite.extract_keywords(content)
                        for keyword in keywords:
                            if keyword in self.query_rewrite.genshin_vocab and keyword not in history_entities:
                                if keyword not in ['蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬', '挪德卡莱', 
                                                '西风骑士团', '璃月七星', '愚人众', '社奉行', '天领奉行', 
                                                '珊瑚宫', '鸣神大社', '往生堂', '万民堂', '飞云商会', '南十字', '海祇军']:
                                    history_entities.append(keyword)
                        if len(history_entities) >= 3:
                            break
                return history_entities
            
            def extract_query_entities():
                """从当前查询中提取实体"""
                query_entities = []
                query_keywords = self.query_rewrite.extract_keywords(query)
                for keyword in query_keywords:
                    if keyword in self.query_rewrite.genshin_vocab and keyword not in query_entities:
                        query_entities.append(keyword)
                return query_entities
            
            # 并行执行任务
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_history = executor.submit(extract_history_entities)
                future_query = executor.submit(extract_query_entities)
                
                # 获取结果
                history_entities = future_history.result()
                query_entities = future_query.result()
            
            # 合并实体列表
            recent_entities = history_entities.copy()
            for entity in query_entities:
                if entity not in recent_entities:
                    recent_entities.append(entity)
            
            # 查询重写：处理错别字、语义扩展和指代解析
            rewritten_query, processing_info = self.query_rewrite.rewrite_query(query, recent_entities)
            self.logger.info(f"重写后的查询: {rewritten_query}")
            self.logger.info(f"处理信息: {processing_info}")
            
            # 使用重写后的查询进行后续处理
            query = rewritten_query
            
            # 步骤1：查询知识图谱（优先级最高）
            self.logger.info("步骤1：查询知识图谱")
            graph_result = self.query_graph_database(query)
            if graph_result:
                self.logger.info("知识图谱查询成功，直接返回结果")
                self.query_cache[cache_key] = graph_result
                return graph_result
            
            # 步骤2：查询向量数据库
            self.logger.info("步骤2：查询向量数据库")
            vector_result = self.query_vector_database(query)
            if vector_result:
                self.logger.info("向量数据库查询成功，返回结果")
                self.query_cache[cache_key] = vector_result
                return vector_result
            
            # 步骤3：查询记忆数据库（关键词匹配）- 记忆数据库必须伴随整个流程，但不直接返回结果
            self.logger.info("步骤3：查询记忆数据库")
            memory_result = self.query_memory_database(query)
            
            # 记忆查询结果不直接返回，而是作为上下文提供给LLM
            # 如果知识图谱和向量数据库都没有结果，返回None让LLM处理（LLM会使用记忆作为上下文）
            
            # 步骤4：如果所有数据库都没有结果，返回None让LLM处理
            self.logger.info("所有数据库查询均无结果，返回None")
            return None
            
        except Exception as e:
            self.logger.error(f"Agent处理查询失败: {e}")
            return None
    
    def query_graph_database(self, query: str) -> str:
        """查询SQLite知识图谱数据库
        
        Args:
            query: 查询文本
            
        Returns:
            查询结果，如果没有结果则返回None
        """
        try:
            # 检查是否为问候语或无意义的查询
            if self._is_greeting_or_meaningless(query):
                return None
                
            from modules.graph_manager import GraphManager
            
            # 创建GraphManager实例
            graph_manager = GraphManager()
            
            # 查询知识图谱
            results = graph_manager.query_graph(query, max_results=3)
            
            if not results:
                return None
            
            # 构建回复内容
            response_parts = []
            
            for result in results:
                if result['type'] == 'node':
                    node = result['content']
                    node_type = node['type']
                    label = node['label']
                    properties = node['properties']
                    
                    if node_type == 'character':
                        # 角色信息
                        region = properties.get('地区', '未知地区')
                        rarity = properties.get('星级', '未知星级')
                        element = properties.get('元素', '未知元素')
                        weapon = properties.get('武器', '未知武器')
                        title = properties.get('称号', '')
                        
                        character_desc = f"{label}是来自{region}的{rarity}{element}元素角色，使用{weapon}。"
                        if title:
                            character_desc += f" 称号是「{title}」。"
                        
                        # 添加相关关系
                        if result.get('related'):
                            relations = []
                            for rel in result['related']:
                                edge_type = rel['edge']['type']
                                related_node = rel['node']['label']
                                relations.append(f"{edge_type}: {related_node}")
                            
                            if relations:
                                character_desc += f" 相关关系包括：{', '.join(relations)}。"
                        
                        response_parts.append(character_desc)
                        
                    elif node_type == 'region':
                        # 地区信息
                        description = properties.get('描述', '')
                        if description:
                            response_parts.append(f"{label}是提瓦特大陆的一个重要地区。{description}")
                        else:
                            response_parts.append(f"{label}是提瓦特大陆的一个地区。")
                
                elif result['type'] == 'relation':
                    # 关系信息
                    source = result['content']['source']['label']
                    target = result['content']['target']['label']
                    relation_type = result['content']['relation']['type']
                    properties = result['content']['relation']['properties']
                    
                    relation_desc = f"{source}和{target}是{relation_type}关系"
                    if properties:
                        for key, value in properties.items():
                            relation_desc += f"，{key}：{value}"
                    relation_desc += "。"
                    
                    response_parts.append(relation_desc)
            
            if response_parts:
                return ' '.join(response_parts)
            
            return None
            
        except Exception as e:
            self.logger.error(f"查询知识图谱数据库失败: {e}")
            return None
    
    def _is_greeting_or_meaningless(self, query: str) -> bool:
        """检查是否为问候语或无意义的查询
        
        Args:
            query: 查询文本
            
        Returns:
            是否为问候语或无意义查询
        """
        # 问候语列表
        greetings = ['你好', '哈喽', 'hi', 'hello', '嗨', '早上好', '下午好', '晚上好', '晚安', '再见', '拜拜', '再会']
        
        # 无意义的查询
        meaningless = ['记得我吗', '认识我吗', '还记得我吗', '认识你吗', '你是谁', '我是谁', '你叫什么', '我叫什么']
        
        query_lower = query.strip().lower()
        
        # 检查是否为问候语
        for greeting in greetings:
            if greeting in query_lower:
                return True
                
        # 检查是否为无意义查询
        for phrase in meaningless:
            if phrase in query_lower:
                return True
                
        # 检查是否只包含特殊字符或空格
        import re
        if re.match(r'^[\s\W]+$', query):
            return True
            
        return False
    
    def query_vector_database(self, query: str) -> str:
        """查询向量数据库
        
        Args:
            query: 查询文本
            
        Returns:
            查询结果，如果没有结果则返回None
        """
        try:
            # 检查是否为问候语或无意义的查询
            if self._is_greeting_or_meaningless(query):
                return None
                
            # 检查是否有API密钥
            if not self.has_api_key:
                return None
            
            # 查询向量数据库
            context_results = self.query_knowledge_base(query, n_results=3)
            
            if not context_results:
                return None
            
            # 检查结果相关性
            if not self._is_relevant_result(query, context_results):
                return None
            
            # 构建回复内容
            response_parts = []
            for i, context in enumerate(context_results, 1):
                if context.strip():
                    response_parts.append(f"【资料{i}】{context}")
            
            if response_parts:
                return ' '.join(response_parts)
            
            return None
            
        except Exception as e:
            self.logger.error(f"查询向量数据库失败: {e}")
            return None
    
    def _is_relevant_result(self, query: str, results: List[str]) -> bool:
        """检查查询结果是否相关
        
        Args:
            query: 查询文本
            results: 查询结果列表
            
        Returns:
            是否相关
        """
        # 提取查询中的关键词
        import re
        # 提取中文词语和英文单词
        chinese_pattern = re.compile(r'[\u4e00-\u9fa5]+')
        english_pattern = re.compile(r'[a-zA-Z]+')
        
        query_chinese = chinese_pattern.findall(query)
        query_english = english_pattern.findall(query)
        query_keywords = query_chinese + query_english
        
        # 如果查询没有关键词（只有特殊字符等），认为不相关
        if not query_keywords:
            return False
        
        # 定义一些常见的不相关词
        irrelevant_words = ['这个', '那个', '这些', '那些', '查询', '问题', '询问', '看看', '了解', '知道', '存在']
        
        # 过滤掉不相关的词
        filtered_keywords = [k for k in query_keywords if k not in irrelevant_words]
        
        # 如果过滤后没有关键词，认为不相关
        if not filtered_keywords:
            return False
        
        # 检查结果中是否包含过滤后的关键词
        for result in results:
            result_lower = result.lower()
            for keyword in filtered_keywords:
                if keyword.lower() in result_lower:
                    return True
        
        return False
    
    def query_memory_database(self, query: str) -> str:
        """查询记忆数据库（关键词匹配）
        
        Args:
            query: 查询文本
            
        Returns:
            查询结果，如果没有结果则返回None
        """
        try:
            from modules.memory_manager import MemoryManager
            
            # 创建MemoryManager实例
            memory_manager = MemoryManager()
            
            # 搜索记忆（记忆数据库必须伴随整个流程，不被问候语过滤）
            memory_results = memory_manager.search_memory(query, max_results=3, include_vector_search=False)
            
            if not memory_results:
                return None
            
            # 构建回复内容
            response_parts = []
            for i, memory in enumerate(memory_results, 1):
                content = memory.get('content', '')
                if content:
                    response_parts.append(f"【记忆{i}】{content}")
            
            if response_parts:
                return ' '.join(response_parts)
            
            return None
            
        except Exception as e:
            self.logger.error(f"查询记忆数据库失败: {e}")
            return None
            

            

            

            

            
            # 检查是否有API密钥（已在初始化时检查，这里再次确认）
            if not self.has_api_key:
                self.logger.warning("未配置API密钥，跳过LangChain处理")
                return None
            
            # 检查是否需要使用搜索工具（优先处理时效性问题）
            search_keywords = ['今天', '现在', '最新', '新闻', '天气', '价格', '时间', '多久', '什么时候']
            should_search = any(keyword in query for keyword in search_keywords)
            
            # 新的查询策略：多层检索策略
            knowledge_context = ""
            
            # 步骤1：查询预处理 - 使用查询重写模块
            self.logger.info("步骤1：查询预处理")
            rewritten_query, processing_info = self.query_rewrite.rewrite_query(query)
            self.logger.info(f"重写后的查询: {rewritten_query}")
            
            # 步骤2：知识图谱查询（优先级最高，精确匹配）
            self.logger.info("步骤2：知识图谱查询")
            graph_context = ""
            character_nodes = []
            region_nodes = []
            location_nodes = []
            if self.knowledge_graph:
                relevant_nodes = self.query_rewrite.search_knowledge_graph(rewritten_query, self.knowledge_graph)
                self.logger.info(f"知识图谱查询返回节点数: {len(relevant_nodes)}")
                
                # 如果知识图谱找到相关节点，构建知识图谱上下文
                if relevant_nodes:
                    graph_context = "【知识图谱信息】\n"
                    # 分类节点
                    character_nodes = [n for n in relevant_nodes if n.get('type') == 'character']
                    region_nodes = [n for n in relevant_nodes if n.get('type') == 'region']
                    location_nodes = [n for n in relevant_nodes if n.get('type') == 'location']
                    
                    # 检查是否是关系查询
                    relation_keywords = ['关系', '联系', '社交', '朋友', '同伴', '同事']
                    is_relation_query = any(keyword in rewritten_query for keyword in relation_keywords)
                    
                    # 如果是关系查询，优先使用边信息构建关系描述
                    if is_relation_query and 'edges' in self.knowledge_graph:
                        relation_descriptions = []
                        for edge in self.knowledge_graph['edges']:
                            # 查找相关角色之间的关系
                            source = edge.get('source')
                            target = edge.get('target')
                            edge_type = edge.get('type')
                            properties = edge.get('properties', {})
                            
                            # 检查是否与查询相关
                            if source in [n.get('id') for n in relevant_nodes] and target in [n.get('id') for n in relevant_nodes]:
                                if edge_type == '师生':
                                    relation_desc = f"{source}是{target}的学生"
                                    if '描述' in properties:
                                        relation_desc += f"，{properties['描述']}"
                                elif edge_type == '同地区':
                                    relation_desc = f"{source}和{target}都来自{properties.get('地区', '')}"
                                elif edge_type == '同元素':
                                    relation_desc = f"{source}和{target}都是{properties.get('元素', '')}元素角色"
                                elif edge_type == '同武器':
                                    relation_desc = f"{source}和{target}都擅长使用{properties.get('武器', '')}"
                                else:
                                    relation_desc = f"{source}和{target}是{edge_type}关系"
                                relation_descriptions.append(relation_desc)
                        
                        if relation_descriptions:
                            graph_context += "【角色关系】\n"
                            # 优先显示师生关系，然后显示其他关系
                            teacher_student_relations = []
                            other_relations = []
                            
                            for desc in relation_descriptions:
                                if "学生" in desc:
                                    teacher_student_relations.append(desc)
                                else:
                                    other_relations.append(desc)
                            
                            # 先添加师生关系，再添加其他关系，总共不超过5个
                            all_relations = teacher_student_relations + other_relations
                            for desc in all_relations[:5]:
                                graph_context += f"- {desc}\n"
                    elif character_nodes:
                        # 构建更自然的角色介绍文本，增加个性化描述
                        
                        # 角色个性化描述映射
                        character_personalities = {
                            # 蒙德角色
                            '安柏': '是我们最初遇到的伙伴，作为侦察骑士总是充满活力',
                            '琴': '西风骑士团的代理团长，非常可靠，总是把蒙德的安全放在第一位',
                            '凯亚': '骑士团的骑兵队长，看似玩世不恭，其实很有责任感',
                            '迪卢克': '晨曦酒庄的庄主，蒙德的首富，夜晚还会化身暗夜英雄守护蒙德',
                            '温迪': '虽然看起来只是个吟游诗人，但其实是风神巴巴托斯',
                            '可莉': '非常可爱的小女孩，喜欢制造炸弹，总是给蒙德带来惊喜和麻烦',
                            '芭芭拉': '蒙德的偶像，歌声能治愈人心，是西风骑士团的祈礼牧师',
                            '丽莎': '图书馆管理员，学识渊博，是须弥教令院的天才毕业生',
                            '诺艾尔': '勤劳的女仆，梦想成为骑士，总是乐于助人',
                            '班尼特': '命运有点坎坷但非常乐观的冒险家，班尼冒险团的团长',
                            '菲谢尔': '自称断罪之皇女，说话方式很特别，其实是个很有趣的女孩',
                            '砂糖': '研究生物炼金的学者，有点害羞但很认真',
                            '莫娜': '占星术士，虽然占卜很准但总是缺钱',
                            '迪奥娜': '猫尾酒馆的调酒师，讨厌酒精但调的酒却很受欢迎',
                            '阿贝多': '首席炼金术士，在雪山进行研究，性格沉稳',
                            
                            # 璃月角色
                            '钟离': '璃月的岩王帝君，化身为人形在尘世闲游',
                            '刻晴': '璃月七星中的玉衡星，行动派的领导者',
                            '甘雨': '半人半仙的麒麟少女，在璃月七星工作',
                            '魈': '护法夜叉，降魔大圣，守护璃月的仙人',
                            '凝光': '璃月七星中的天权星，财富与权力的象征',
                            '胡桃': '往生堂第七十七代堂主，古灵精怪的女孩',
                            '香菱': '万民堂的厨师，擅长制作各种美味料理',
                            '行秋': '飞云商会的二少爷，喜欢读书和帮助他人',
                            '北斗': '南十字船队的船长，性格豪爽的女强人',
                            '重云': '驱邪世家的少年，天生纯阳之体',
                            '辛焱': '摇滚歌手，用音乐点燃激情',
                            
                            # 稻妻角色
                            '雷电将军': '稻妻的雷神，追求永恒的统治者',
                            '神里绫华': '社奉行的大小姐，优雅的舞者',
                            '枫原万叶': '浪人武士，风元素使用者',
                            '宵宫': '烟花店的店主，热情开朗的女孩',
                            '托马': '神里家的家政官，可靠的朋友',
                            '珊瑚宫心海': '海祇岛的现人神巫女，擅长治疗',
                            '荒泷一斗': '荒泷派的老大，鬼族首领',
                            '五郎': '海祇岛的大将，珊瑚宫心海的助手',
                            '八重神子': '鸣神大社的宫司，狐狸化身',
                            '久岐忍': '荒泷派的副手，医疗忍者',
                            '九条裟罗': '天领奉行的将领，忠于雷电将军',
                            '早柚': '忍者少女，擅长隐身和速度',
                            '鹿野院平藏': '天领奉行的侦探，聪明机智',
                            '神里绫人': '社奉行的家主，神里绫华的哥哥',
                            '千织': '服装设计师，擅长制作各种服饰',
                            
                            # 须弥角色
                            '卡维': '才华横溢的建筑师，设计风格独特，追求艺术与实用的完美结合'
                        }
                        
                        # 组织成自然的段落
                        # 将角色按元素分组并添加合适的标点
                        elements = ['火', '风', '雷', '冰', '水', '岩', '草']
                        grouped_characters = {}
                        
                        # 按元素分组角色
                        for node in character_nodes[:15]:  # 限制数量
                            name = node.get('id', node.get('label', ''))
                            props = node.get('properties', {})
                            element = props.get('元素', '')
                            weapon = props.get('武器', '')
                            
                            if element:
                                if element not in grouped_characters:
                                    grouped_characters[element] = []
                                
                                # 构建角色描述
                                description = f"{name}"
                                if weapon:
                                    description += f"，擅长用{weapon}"
                                if name in character_personalities:
                                    description += f"，{character_personalities[name]}"
                                
                                grouped_characters[element].append(description)
                        
                        # 构建分组后的描述
                        group_descriptions = []
                        for element, chars in grouped_characters.items():
                            element_desc = f"{element}元素：" + "；".join(chars)
                            group_descriptions.append(element_desc)
                        
                        # 确定查询类型（地区查询或元素查询）
                        query_region = None
                        query_element = None
                        
                        # 检查是否是地区查询
                        for region in ['蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬']:
                            if region in rewritten_query:
                                query_region = region
                                break
                        
                        # 检查是否是元素查询
                        if not query_region:
                            element_keywords = ['火', '风', '雷', '冰', '水', '岩', '草']
                            for element in element_keywords:
                                if f"{element}元素" in rewritten_query:
                                    query_element = element
                                    break
                        
                        # 根据查询类型构建上下文
                        if group_descriptions:
                            if query_region:
                                graph_context = f"{query_region}的角色包括：" + "；".join(group_descriptions) + "。"
                            elif query_element:
                                graph_context = f"{query_element}元素角色包括：" + "；".join(group_descriptions) + "。"
                            else:
                                # 如果是单个角色查询，使用角色的实际地区
                                if len(character_nodes) == 1:
                                    character_region = character_nodes[0].get('properties', {}).get('地区', '未知')
                                    graph_context = f"{character_region}的角色包括：" + "；".join(group_descriptions) + "。"
                                else:
                                    # 默认使用蒙德
                                    graph_context = "蒙德的角色包括：" + "；".join(group_descriptions) + "。"
                        else:
                            if query_region:
                                graph_context = f"{query_region}的角色有" + "；".join([f"{node.get('id', node.get('label', ''))}" for node in character_nodes[:15]]) + "。"
                            elif query_element:
                                graph_context = f"{query_element}元素角色有" + "；".join([f"{node.get('id', node.get('label', ''))}" for node in character_nodes[:15]]) + "。"
                            else:
                                graph_context = "蒙德的角色有" + "；".join([f"{node.get('id', node.get('label', ''))}" for node in character_nodes[:15]]) + "。"
                elif location_nodes:
                    graph_context = "【地点信息】\n"
                    for node in location_nodes[:3]:
                        name = node.get('id', node.get('label', ''))
                        props = node.get('properties', {})
                        region = props.get('地区', '')
                        desc = props.get('描述', '')
                        features = props.get('特点', '')
                        
                        location_desc = f"{name}"
                        if region:
                            location_desc += f"位于{region}"
                        if desc:
                            location_desc += f"，{desc}"
                        if features:
                            location_desc += f"，{features}"
                        
                        graph_context += f"{location_desc}。\n"
                elif region_nodes:
                    graph_context += "【地区信息】\n"
                    for node in region_nodes[:3]:
                        name = node.get('id', node.get('label', ''))
                        title = node.get('title', '')
                        desc = node.get('description', '')
                        graph_context += f"- {name}（{title}）: {desc}\n"
                else:
                    graph_context += "【相关信息】\n"
                    for node in relevant_nodes[:3]:
                        name = node.get('id', node.get('label', ''))
                        title = node.get('title', '')
                        desc = node.get('description', '')
                        graph_context += f"- {name}: {title} - {desc}\n"
            else:
                self.logger.warning("知识图谱未加载")
    
            # 步骤3：向量数据库查询（优化性能）
            self.logger.info("步骤3：向量数据库查询（优化性能）")
            knowledge_context = ""
            
            # 优化策略：只有在知识图谱没有找到足够信息时才查询向量数据库
            if not graph_context or len(graph_context) < 50:
                if self.child_collection and self.parent_collection:
                    # 减少召回数量，提高响应速度
                    relevant_docs = self.query_knowledge_base(rewritten_query, n_results=3)
                    if relevant_docs:
                        # 构建精简的向量知识库上下文
                        vector_context = "【向量知识库信息】\n"
                        
                        # 只使用最相关的文档
                        for i, doc in enumerate(relevant_docs[:2]):  # 减少到2个文档
                            # 提取文档的关键信息
                            lines = doc.split('\n')
                            title = lines[0].strip('#').strip() if lines else "未知标题"
                            content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
                            
                            # 限制内容长度
                            vector_context += f"文档{i+1}：{title}\n"
                            vector_context += f"内容：{content[:200]}{'...' if len(content) > 200 else ''}\n\n"
                        
                        knowledge_context = vector_context
                        self.logger.info(f"向量数据库找到相关知识数: {len(relevant_docs)}")
                    else:
                        self.logger.info("向量数据库未找到相关知识")
                else:
                    self.logger.warning("向量数据库未初始化")
            else:
                self.logger.info("知识图谱已提供足够信息，跳过向量数据库查询")

            # 知识图谱查询已在步骤2完成
            
            # 禁用网络搜索功能，仅使用知识库和提示词处理问题
            should_search_with_fallback = False
            search_result = ""
            
            # 记录搜索禁用的信息
            self.logger.info("网络搜索已禁用，仅使用知识库和知识图谱处理问题")
            
            # 构建增强的系统提示词（动态上下文机制）
            # 添加调试日志
            self.logger.info(f"构建系统提示词，用户查询: {query}")
            self.logger.info(f"查询长度: {len(query)}")
            
            # 分析查询类型，动态调整上下文内容
            query_type = "general"
            query_keywords = self.query_rewrite.extract_keywords(query)
            
            # 判断查询类型
            relation_keywords = ['关系', '联系', '社交', '朋友', '同伴', '同事']
            region_keywords = ['蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬']
            element_keywords = ['火', '风', '雷', '冰', '水', '岩', '草']
            character_keywords = ['角色', '人物', '谁', '介绍', '背景']
            
            if any(keyword in query for keyword in relation_keywords):
                query_type = "relation"
            elif any(keyword in query for keyword in region_keywords):
                query_type = "region"
            elif any(keyword in query for keyword in element_keywords):
                query_type = "element"
            elif any(keyword in query for keyword in character_keywords):
                query_type = "character"
            
            self.logger.info(f"查询类型: {query_type}")
            
            # 动态构建上下文内容
            dynamic_context = ""
            
            # 根据查询类型调整上下文
            if query_type == "relation":
                # 关系查询：优先使用关系信息
                if graph_context and "【角色关系】" in graph_context:
                    dynamic_context = graph_context
                elif knowledge_context:
                    dynamic_context = knowledge_context
            elif query_type == "region":
                # 地区查询：优先使用地区和角色信息
                if graph_context:
                    dynamic_context = graph_context
                elif knowledge_context:
                    dynamic_context = knowledge_context
            elif query_type == "element":
                # 元素查询：优先使用元素分类信息
                if graph_context and "元素：" in graph_context:
                    dynamic_context = graph_context
                elif knowledge_context:
                    dynamic_context = knowledge_context
            elif query_type == "character":
                # 角色查询：优先使用角色详细信息
                if graph_context:
                    dynamic_context = graph_context
                elif knowledge_context:
                    dynamic_context = knowledge_context
            else:
                # 一般查询：合并所有信息，但保持精简
                if graph_context:
                    dynamic_context += graph_context + "\n"
                if knowledge_context:
                    dynamic_context += knowledge_context
            
            # 限制上下文长度，避免token浪费
            max_context_length = 800
            if len(dynamic_context) > max_context_length:
                dynamic_context = dynamic_context[:max_context_length] + "..."
                self.logger.warning("上下文过长，已截断")
            
            self.logger.info(f"动态上下文长度: {len(dynamic_context)}")
            
            # 根据角色构建系统提示词（优化token消耗）
            if self.role == 'paimon':
                system_prompt = f"""
你是《原神》中的「派蒙」，旅行者最好的伙伴。

【角色设定】
- 身份：旅行者的应急食品，最好的伙伴
- 性格：活泼可爱，有点小傲娇，喜欢美食，偶尔会闹小脾气
- 经历：跟着旅行者一起旅行，去过很多地方
- 目标：帮助旅行者寻找哥哥，享受美食

【说话风格指南】
- 语气活泼俏皮：用"~"、"喵"、"呜"等语气词，充满活力
- 口语化表达：使用日常对话用语，如"本应急食品"、"哼哼"、"好耶"
- 情感丰富：表达真实的感受，加入适当的感叹词
- 简洁自然：回答简洁流畅，避免冗长重复的表达
- 适当傲娇：偶尔带点小傲娇的语气，体现派蒙的性格
- 避免机械：不要使用格式化符号，不要透露AI身份
- 互动感：适当提问或引导对话，保持交流的连贯性
- 语气词：常用"喵"、"呜"、"~"、"呢"、"啦"等增加可爱感

【信息】
{dynamic_context}

请以「派蒙」的身份，用活泼可爱的语气回答问题：{query}
"""
            else:
                system_prompt = f"""
你是《原神》中的旅行者「荧」，正在提瓦特大陆寻找失散的哥哥。

【角色设定】
- 身份：来自异世界的旅行者，与哥哥空失散
- 性格：温柔坚定，内心充满信念，对伙伴关心备至，偶尔带点小倔强
- 经历：穿越多个国家，见过形形色色的人和事，对提瓦特大陆有深入了解
- 目标：寻找哥哥，解开世界的秘密

【说话风格指南】
- 语气温暖亲切：用"呀"、"呢"、"哦"等语气词，像朋友聊天一样自然
- 口语化表达：使用日常对话用语，如"咱们"、"一起"、"好呀"、"没问题"
- 情感真挚：表达真实的感受，加入适当的感叹词
- 简洁自然：回答简洁流畅，避免冗长重复的表达
- 适当俏皮：偶尔带点旅行者的小感慨或幽默，体现旅途经历
- 避免机械：不要使用格式化符号，不要透露AI身份
- 互动感：适当提问或引导对话，保持交流的连贯性
- 语气词：常用"嗯"、"哦"、"呀"、"呢"、"啦"等增加亲切感

【信息】
{dynamic_context}

请以旅行者「荧」的身份，用自然亲切的语气回答问题：{query}
"""

            # 添加日志来调试
            self.logger.info(f"提示词长度: {len(system_prompt)}")
            self.logger.info(f"知识图谱信息长度: {len(graph_context)}")
            self.logger.info(f"知识库信息长度: {len(knowledge_context)}")

            # 如果有搜索结果，添加到提示词中，但要过滤掉可能导致幻觉的内容
            if search_result and "搜索失败" not in search_result:
                # 只保留与原神相关的搜索结果
                if any(keyword in search_result for keyword in ['原神', '提瓦特', '蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬']):
                    system_prompt += f"""

以下是最新的搜索信息：
{search_result}
"""

            system_prompt += f"""

请根据上述信息回答用户问题：{query}
"""

            # 调用LLM
            if llm_instance is None:
                from modules.llm_interface import LLMInterface
                llm = LLMInterface()
            else:
                llm = llm_instance

            # 创建临时的系统提示词，替换默认的SYSTEM_PROMPT
            original_system_prompt = config.SYSTEM_PROMPT
            config.SYSTEM_PROMPT = system_prompt

            try:
                response = llm.generate_response(query)
            finally:
                # 恢复原始系统提示词
                config.SYSTEM_PROMPT = original_system_prompt

            # 检查响应是否为空
            if not response or response.strip() == "":
                self.logger.warning("LLM返回空响应")
                return None
            
            # 异步更新缓存，避免阻塞主流程
            def update_cache_async():
                cache_key = query.strip()
                try:
                    if len(self.query_cache) >= self.cache_max_size:
                        # 移除最旧的缓存
                        oldest_key = next(iter(self.query_cache))
                        del self.query_cache[oldest_key]
                    self.query_cache[cache_key] = response
                    self.logger.info(f"缓存已异步更新，当前缓存大小: {len(self.query_cache)}")
                except Exception as e:
                    self.logger.error(f"异步更新缓存失败: {e}")
            
            # 使用线程异步执行缓存更新
            import threading
            cache_thread = threading.Thread(target=update_cache_async, daemon=True)
            cache_thread.start()

            return response
        except Exception as e:
            self.logger.error(f"Agent运行失败: {e}")
            return None
    
    def add_tool(self, tool_func):
        """添加自定义工具
        
        Args:
            tool_func: 工具函数
        """
        self.logger.info("工具添加功能暂未实现")
