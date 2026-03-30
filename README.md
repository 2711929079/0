# 原神数字人系统

一个基于大语言模型的原神游戏数字人系统，具备记忆管理、知识检索、语音交互等功能。

## ✨ 功能特性

- **三层记忆架构**：短期记忆、中期记忆、长期记忆
- **知识图谱**：基于游戏角色关系构建的知识网络
- **向量检索**：高效的语义搜索和文档检索
- **语音交互**：支持语音输入和语音合成
- **安全防护**：输入验证、速率限制、HTTPS支持
- **性能优化**：连接池、异步操作、缓存策略

## 🛠️ 技术栈

- **后端**：Python + Flask
- **数据库**：SQLite + ChromaDB
- **AI**：OpenAI API + LangChain
- **语音**：SiliconFlow ASR + TTS
- **部署**：Cloudflare Tunnel

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/genshin-digital-human.git
cd genshin-digital-human
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0

# SiliconFlow API配置
SILICONFLOW_API_KEY=your_siliconflow_api_key
```

### 4. 启动服务

```bash
python web_server.py
```

服务将在 http://localhost:8000 启动

## 📚 项目结构

```
genshin-digital-human/
├── modules/               # 核心功能模块
│   ├── memory_manager.py     # 记忆管理系统
│   ├── cache_manager.py      # 缓存管理
│   ├── graph_manager.py      # 知识图谱管理
│   ├── llm_interface.py      # LLM接口
│   └── ...
├── data/                  # 数据存储
│   ├── chroma_db/            # 向量数据库
│   ├── memory_database.db    # 记忆数据库
│   └── graph_database.db     # 图谱数据库
├── docs/                  # 文档
├── web/                   # Web前端
├── audio_files/           # 音频文件
├── config.py              # 配置文件
├── web_server.py          # 主服务器
└── requirements.txt       # 依赖管理
```

## 🚀 API 端点

### 聊天接口

```
POST /api/chat
Content-Type: application/json

{
  "message": "你好，能介绍一下原神吗？",
  "user_id": "anonymous"
}
```

### 语音合成

```
POST /api/synthesize
Content-Type: application/json

{
  "text": "这是一段测试文本",
  "role": "ying"
}
```

## 📖 使用说明

1. **聊天功能**：通过 `/api/chat` 接口进行对话
2. **语音交互**：支持语音输入和语音回复
3. **记忆管理**：系统会自动保存对话历史和用户偏好
4. **知识检索**：基于游戏知识库提供准确的回答

## 🔒 安全说明

- 所有用户输入都会经过严格验证
- API请求受到速率限制保护
- 支持HTTPS加密传输
- 敏感信息使用环境变量管理

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- 原神游戏官方
- OpenAI
- LangChain
- SiliconFlow