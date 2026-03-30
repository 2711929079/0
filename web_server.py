from flask import Flask, request, jsonify, render_template_string, send_file, Response
import logging
import threading
import os
import uuid
import re
import time
import json
from modules.llm_interface import LLMInterface
from modules.text_to_speech import TextToSpeech
from modules.langchain_integration import LangChainIntegration
from modules.session_manager import session_manager
from modules.memory_manager import MemoryManager
from modules.siliconflow_asr import SiliconFlowASR
from modules.graph_manager import GraphManager
from modules.prompt_hook import prompt_hook
from modules.rate_limiter import rate_limiter
from modules.input_validator import input_validator
from config import config

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 创建音频文件保存目录
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)



# 初始化Flask应用
app = Flask(__name__, static_folder='static', static_url_path='/static')



# 初始化数字人组件
llm = LLMInterface()
tts = TextToSpeech()
langchain = LangChainIntegration(role='ying')

# 加载知识库（仅在首次启动或数据库不存在时加载）
if hasattr(config, 'KNOWLEDGE_BASE_URLS') and config.KNOWLEDGE_BASE_URLS:
    langchain.load_knowledge_base(config.KNOWLEDGE_BASE_URLS, force_reload=False)

# 设置自定义语音
if hasattr(config, 'CUSTOM_VOICE_TYPE') and config.CUSTOM_VOICE_TYPE == 'tts':
    tts.set_voice("custom")
    logger.info("已启用自定义语音")

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>旅行者-荧 - v{{version}}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            background-color: #fff;
            border-radius: 10px 10px 0 0;
        }
        .header-left {
            flex: 1;
        }
        .header-left h1 {
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin: 0;
        }
        .subtitle {
            font-size: 12px;
            color: #666;
            margin: 4px 0 0 0;
        }
        .header-right {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        .chat-container {
            height: 400px;
            overflow-y: auto;
            padding: 15px;
            margin-bottom: 20px;
            background-color: #f8f9fa;
        }
        .message {
            display: flex;
            margin-bottom: 20px;
            max-width: 80%;
        }
        .user-message {
            margin-left: auto;
            flex-direction: row-reverse;
        }
        .ai-message {
            margin-right: auto;
        }
        .message-avatar {
            margin-right: 10px;
            flex-shrink: 0;
        }
        .user-message .message-avatar {
            margin-right: 0;
            margin-left: 10px;
        }
        .avatar-small {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 2px solid #3498db;
            object-fit: cover;
        }
        .message-content-wrapper {
            flex: 1;
        }
        .message-author {
            font-weight: bold;
            margin-bottom: 5px;
            color: #2c3e50;
            font-size: 14px;
        }
        .message-content {
            padding: 12px 16px;
            border-radius: 18px;
            line-height: 1.5;
            color: #333;
            word-wrap: break-word;
        }
        .ai-message .message-content {
            background-color: #fff;
            border-top-left-radius: 4px;
        }
        .user-message .message-content {
            background-color: #3498db;
            color: white;
            border-top-right-radius: 4px;
        }
        .voice-support-tip {
            text-align: center;
            font-size: 12px;
            color: #999;
            margin-top: 8px;
            font-style: italic;
        }
        .loading {
            color: #666;
            font-style: italic;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .loading::after {
            content: '';
            width: 16px;
            height: 16px;
            border: 2px solid #3498db;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        /* 语音控制工具栏 */
        .voice-controls {
            display: flex;
            justify-content: center;
            gap: 16px;
            padding: 10px;
            background-color: #f8f9fa;
            border-top: 1px solid #e9ecef;
            border-bottom: 1px solid #e9ecef;
        }

        .input-area {
            display: flex;
            gap: 12px;
            align-items: center;
            padding: 10px;
        }
        .input-area input {
            flex: 1;
            padding: 15px 20px;
            border: 1px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        .input-area input:focus {
            border-color: #3498db;
        }
        .input-area button {
            padding: 15px 20px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: background-color 0.3s;
            width: 80px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .input-area button:hover {
            background-color: #2980b9;
        }
        .voice-toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background-color: white;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid #e9ecef;
            font-size: 14px;
            font-weight: 500;
        }
        .voice-toggle:hover {
            background-color: #f8f9fa;
            transform: translateY(-1px);
        }
        .voice-toggle.active {
            background-color: #e3f2fd;
            border-color: #3498db;
            color: #3498db;
        }
        .voice-toggle input[type="checkbox"] {
            display: none;
        }
        .voice-toggle-icon {
            font-size: 18px;
            color: #666;
            transition: color 0.3s;
        }
        .voice-toggle.active .voice-toggle-icon {
            color: #3498db;
        }
        .stream-toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background-color: white;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid #e9ecef;
            font-size: 14px;
            font-weight: 500;
        }
        .stream-toggle:hover {
            background-color: #f8f9fa;
            transform: translateY(-1px);
        }
        .stream-toggle.active {
            background-color: #e8f5e9;
            border-color: #4caf50;
            color: #4caf50;
        }
        .stream-toggle input[type="checkbox"] {
            display: none;
        }
        .stream-toggle-icon {
            font-size: 18px;
            color: #666;
            transition: color 0.3s;
        }
        .stream-toggle.active .stream-toggle-icon {
            color: #4caf50;
        }
        .voice-input-btn {
            padding: 16px;
            background-color: #fff;
            border: 2px solid #3498db;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            width: 64px;
            height: 64px;
            box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
        }
        .voice-input-btn:hover {
            background-color: #f0f8ff;
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(52, 152, 219, 0.3);
        }
        .voice-input-btn:active {
            transform: scale(0.95);
        }
        .voice-input-btn.active {
            background-color: #3498db;
            color: white;
            border-color: #3498db;
            box-shadow: 0 0 20px rgba(52, 152, 219, 0.5);
            animation: pulse 1.5s infinite;
        }
        .voice-input-btn i {
            font-size: 24px;
            color: #3498db;
            transition: all 0.3s;
        }
        .voice-input-btn.active i {
            color: white;
        }
        
        .role-avatars {
            display: flex;
            gap: 12px;
            align-items: center;
            margin-left: 15px;
        }
        
        .role-avatar {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 3px solid transparent;
        }
        
        .role-avatar:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(155, 89, 182, 0.4);
            border-color: #9b59b6;
        }
        
        .role-avatar:active {
            transform: scale(0.95);
        }
        
        .role-avatar.active {
            border-color: #e74c3c;
            box-shadow: 0 0 0 4px rgba(231, 76, 60, 0.2);
        }
        
        .role-avatar-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(52, 152, 219, 0.7);
            }
            70% {
                box-shadow: 0 0 0 15px rgba(52, 152, 219, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(52, 152, 219, 0);
            }
        }
        .login-container {
            display: flex !important;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.95);
            z-index: 9999 !important;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .login-container.hidden {
            display: none !important;
        }
        .chat-container {
            display: block !important;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
            width: 400px;
            max-width: 90%;
        }
        .login-title {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .login-subtitle {
            font-size: 14px;
            color: #666;
            margin-bottom: 30px;
        }
        .login-input {
            padding: 15px 20px;
            width: 280px;
            max-width: 100%;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 16px;
            margin-bottom: 20px;
            outline: none;
            transition: border-color 0.3s;
        }
        .login-input:focus {
            border-color: #3498db;
        }
        .login-button {
            padding: 15px 40px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: background-color 0.3s;
            width: 280px;
            max-width: 100%;
        }
        .login-button:hover {
            background-color: #2980b9;
        }
        .login-status {
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }
        .login-status.error {
            color: #e74c3c;
        }
        .login-status.success {
            color: #27ae60;
        }
    </style>
</head>
<body>
    <!-- 登录界面 -->
    <div class="login-container" id="loginContainer">
        <div class="login-box">
            <div class="login-title">旅行者-荧</div>
            <div class="login-subtitle">请输入访问口令</div>
            <input type="password" class="login-input" id="passwordInput" placeholder="输入口令..." autocomplete="off">
            <button class="login-button" id="loginButton">登录</button>
            <div class="login-status" id="loginStatus"></div>
        </div>
    </div>
    
    <div class="container">
        <!-- 顶部标题栏 -->
        <div class="header">
            <div class="header-left">
                <h1 id="avatarName">旅行者-荧</h1>
                <p class="subtitle" id="avatarDescription">来自异世界的旅行者</p>
            </div>
            <div class="header-right">
                <label class="voice-toggle" id="voiceToggleLabel">
                    <input type="checkbox" id="voiceToggle" checked>
                    <i class="fas fa-volume-up voice-toggle-icon"></i>
                    <span>语音回复</span>
                </label>
                <label class="stream-toggle" id="streamToggleLabel">
                    <input type="checkbox" id="streamToggle">
                    <i class="fas fa-stream stream-toggle-icon"></i>
                    <span>流式输出</span>
                </label>
                <div class="role-avatars">
                    <div class="role-avatar" id="yingAvatar" title="切换到荧" data-role="ying">
                        <img src="/static/ying.png" alt="荧" class="role-avatar-img">
                    </div>
                    <div class="role-avatar" id="paimonAvatar" title="切换到派蒙" data-role="paimon">
                        <img src="/static/paimon.jpg" alt="派蒙" class="role-avatar-img">
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 聊天界面 -->
        <div class="chat-container" id="chatContainer">
            <div class="message ai-message">
                <div class="message-avatar">
                    <img src="/static/ying.png" alt="荧" class="avatar-small" id="avatarImage">
                </div>
                <div class="message-content-wrapper">
                    <div class="message-author" id="messageAuthor">荧</div>
                    <div class="message-content">{{ welcome_message }}</div>
                </div>
            </div>
        </div>

        <div class="input-area" id="inputArea">
            <input type="text" id="userInput" placeholder="输入您的问题..." autocomplete="off">
            <button id="sendButton">发送</button>
        </div>
        

    </div>
    
    <script>
        // 版本号：{{version}}
        console.log('=== 页面版本:', '{{version}}', '===');
        console.log('=== 最新修改：滚动位置独立保存功能 ===');
        
        // 全局变量
        var sessionId = null;
        var currentPassword = null;
        
        // 角色管理
        var currentRole = 'ying'; // 当前角色：ying（荧）或 paimon（派蒙）
        var roleConfig = {
            ying: {
                name: '旅行者-荧',
                description: '来自异世界的旅行者',
                avatar: '/static/ying.png',
                author: '荧',
                voiceId: 'speech:ying:8ccoy7xf2n:gdwndqcpxtpaiqkeatqc'
            },
            paimon: {
                name: '应急食品-派蒙',
                description: '旅行者最好的伙伴',
                avatar: '/static/paimon.jpg',
                author: '派蒙',
                voiceId: 'speech:paimon:8ccoy7xf2n:gdwndqcpxtpaiqkeatqc'
            }
        };
        
        // 音频队列管理
        var globalAudioQueue = [];
        var isGlobalPlaying = false;
        var activeAudios = [];
        var pendingAudioRequests = [];
        var isProcessingQueue = false;
        var currentAudioRequest = null;
        
        // 简化的登录处理
        function handleLoginClick() {
            console.log('=== 登录按钮被点击 ===');
            var password = document.getElementById('passwordInput').value.trim();
            console.log('输入的密码:', password ? '已提供' : '空');
            
            if (!password) {
                document.getElementById('loginStatus').textContent = '请输入口令';
                document.getElementById('loginStatus').className = 'login-status error';
                return;
            }
            
            document.getElementById('loginStatus').textContent = '登录中...';
            document.getElementById('loginStatus').className = 'login-status success';
            
            // 发送登录请求
            fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: password })
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                console.log('登录响应:', data);
                if (data.success) {
                    document.getElementById('loginStatus').textContent = '登录成功！';
                    document.getElementById('loginStatus').className = 'login-status success';
                    document.getElementById('loginContainer').classList.add('hidden');
                    currentPassword = password;
                    localStorage.setItem('savedPassword', password);
                    
                    // 保存会话ID
                    if (data.session_id) {
                        sessionId = data.session_id;
                        localStorage.setItem('sessionId', sessionId);
                        console.log('保存会话ID:', sessionId);
                    }
                    
                    // 登录成功后加载聊天记录
                    console.log('开始加载聊天记录，当前角色:', currentRole);
                    console.log('当前会话ID:', sessionId);
                    loadChatHistory(currentRole);
                } else {
                    document.getElementById('loginStatus').textContent = data.error || '登录失败';
                    document.getElementById('loginStatus').className = 'login-status error';
                }
            })
            .catch(function(error) {
                console.error('登录失败:', error);
                document.getElementById('loginStatus').textContent = '网络错误';
                document.getElementById('loginStatus').className = 'login-status error';
            });
        }
        
        // 加载聊天记录函数

        
        function addMessage(message, isUser) {
            var chatContainer = document.getElementById('chatContainer');
            var messageDiv = document.createElement('div');
            messageDiv.className = isUser ? 'message user-message' : 'message ai-message';
            
            // 创建内容包装器
            var contentWrapper = document.createElement('div');
            contentWrapper.className = 'message-content-wrapper';
            
            var authorDiv = document.createElement('div');
            authorDiv.className = 'message-author';
            authorDiv.textContent = isUser ? '您' : roleConfig[currentRole].author;
            
            var contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = message;
            
            contentWrapper.appendChild(authorDiv);
            contentWrapper.appendChild(contentDiv);
            
            if (!isUser) {
                // AI消息添加头像
                var avatarDiv = document.createElement('div');
                avatarDiv.className = 'message-avatar';
                avatarDiv.id = 'avatar-' + Date.now();
                
                var avatarImg = document.createElement('img');
                avatarImg.src = roleConfig[currentRole].avatar;
                avatarImg.alt = roleConfig[currentRole].author;
                avatarImg.className = 'avatar-small';
                
                avatarDiv.appendChild(avatarImg);
                messageDiv.appendChild(avatarDiv);
            }
            
            messageDiv.appendChild(contentWrapper);
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            // 保存聊天记录
            saveChatHistory();
        }
        
        // 登录函数
        function login(password) {
            console.log('开始登录函数');
            console.log('登录请求:', { password: password ? '已提供' : '空' });
            console.log('fetch API调用开始');
            return fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ password: password })
            })
            .then(function(response) {
                console.log('fetch API调用完成，响应状态:', response.status);
                return response.json();
            })
            .then(function(data) {
                console.log('登录响应:', data);
                if (data.success) {
                    currentPassword = password;
                    // 保存口令到本地存储
                    localStorage.setItem('savedPassword', password);
                    console.log('登录成功，currentPassword已设置:', currentPassword);
                    
                    // 保存会话ID
                    if (data.session_id) {
                        sessionId = data.session_id;
                        localStorage.setItem('sessionId', sessionId);
                        console.log('保存会话ID:', sessionId);
                        
                        // 登录成功后加载聊天记录
                        console.log('开始加载聊天记录，当前角色:', currentRole);
                        console.log('当前会话ID:', sessionId);
                        loadChatHistory(currentRole);
                    }
                    
                    document.getElementById('loginStatus').textContent = '登录成功！';
                    document.getElementById('loginStatus').className = 'login-status success';
                    document.getElementById('loginContainer').classList.add('hidden');
                    return true;
                } else {
                    console.log('登录失败:', data.error || '未知错误');
                    document.getElementById('loginStatus').textContent = data.error || '登录失败，请重试';
                    document.getElementById('loginStatus').className = 'login-status error';
                    return false;
                }
            })
            .catch(function(error) {
                console.error('登录失败:', error);
                document.getElementById('loginStatus').textContent = '网络错误，请重试';
                document.getElementById('loginStatus').className = 'login-status error';
                return false;
            });
        }
        
        // 发送消息函数
        function sendMessage() {
            var userInput = document.getElementById('userInput');
            var chatContainer = document.getElementById('chatContainer');
            var voiceToggle = document.getElementById('voiceToggle');
            var streamToggle = document.getElementById('streamToggle');
            
            var message = userInput.value.trim();
            if (!message) return;
            
            if (!currentPassword) {
                alert('请先登录');
                return;
            }
            
            // 停止上一个问题的回复语音
            stopAllAudio();
            
            addMessage(message, true);
            userInput.value = '';
            
            var loadingDiv = document.createElement('div');
            loadingDiv.className = 'message ai-message';
            loadingDiv.innerHTML = '<div class="message-author">' + roleConfig[currentRole].author + '</div><div class="message-content loading">正在思考...</div>';
            chatContainer.appendChild(loadingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            var requestData = { 
                message: message,
                enable_audio: voiceToggle.checked,
                stream: streamToggle.checked,
                password: currentPassword,
                role: currentRole
            };
            if (sessionId) {
                requestData.session_id = sessionId;
            }
            
            if (streamToggle.checked) {
                // 流式输出
                // 先发送POST请求获取会话ID和初始数据
                console.log('开始发送流式请求，请求数据:', requestData);
                fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                })
                .then(function(response) {
                    console.log('收到响应，状态码:', response.status);
                    console.log('响应头:', response.headers);
                    chatContainer.removeChild(loadingDiv);
                    if (!response.ok) {
                        console.error('响应状态错误:', response.status);
                        throw new Error('Network response was not ok');
                    }
                    
                    // 检查响应类型
                    var contentType = response.headers.get('content-type');
                    console.log('响应内容类型:', contentType);
                    if (contentType && contentType.includes('text/event-stream')) {
                        // 流式响应
                        console.log('开始处理流式响应');
                        var messageDiv = document.createElement('div');
                        messageDiv.className = 'message ai-message';
                        
                        // 创建内容包装器
                        var contentWrapper = document.createElement('div');
                        contentWrapper.className = 'message-content-wrapper';
                        
                        // 创建作者和内容
                        var authorDiv = document.createElement('div');
                        authorDiv.className = 'message-author';
                        authorDiv.textContent = roleConfig[currentRole].author;
                        
                        var contentDiv = document.createElement('div');
                        contentDiv.className = 'message-content';
                        
                        contentWrapper.appendChild(authorDiv);
                        contentWrapper.appendChild(contentDiv);
                        
                        // 创建头像
                        var avatarDiv = document.createElement('div');
                        avatarDiv.className = 'message-avatar';
                        
                        var avatarImg = document.createElement('img');
                        avatarImg.src = roleConfig[currentRole].avatar;
                        avatarImg.alt = roleConfig[currentRole].author;
                        avatarImg.className = 'avatar-small';
                        
                        avatarDiv.appendChild(avatarImg);
                        messageDiv.appendChild(avatarDiv);
                        messageDiv.appendChild(contentWrapper);
                        
                        chatContainer.appendChild(messageDiv);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                        
                        var contentDiv = messageDiv.querySelector('.message-content');
                        var audioUrl = null;
                        var audioQueue = [];
                        var isPlaying = false;
                        var accumulatedText = '';
                        // 将fullAudioUrl定义为消息级别的变量，确保每个消息有自己的音频URL
                        var messageFullAudioUrl = null;
                        
                        var reader = response.body.getReader();
                        var decoder = new TextDecoder();
                        
                        function processChunk() {
                            reader.read().then(function(result) {
                                if (result.done) {
                                    console.log('Stream completed');
                                    return;
                                }
                                
                                var chunk = decoder.decode(result.value, { stream: true });
                                var lines = chunk.split('\\n');
                                
                                lines.forEach(function(line) {
                                    if (line.startsWith('data: ')) {
                                        try {
                                            var dataStr = line.substring(6);
                                            var data = JSON.parse(dataStr);
                                            
                                            if (data.type === 'init') {
                                                console.log('收到init数据:', data);
                                                if (data.session_id) {
                                                    sessionId = data.session_id;
                                                    localStorage.setItem('sessionId', sessionId);
                                                }
                                                // 保存完整音频URL
                                                console.log('收到的audio_url:', data.audio_url);
                                                if (data.audio_url) {
                                                    messageFullAudioUrl = window.location.origin + data.audio_url;
                                                    console.log('设置messageFullAudioUrl:', messageFullAudioUrl);
                                                } else {
                                                    console.warn('audio_url为空');
                                                }
                                            } else if (data.type === 'text') {
                                                contentDiv.textContent += data.content;
                                                chatContainer.scrollTop = chatContainer.scrollHeight;
                                                accumulatedText += data.content;
                                                
                                                // 如果启用了语音回复，实时合成音频（优化版本）
                                                var voiceToggle = document.getElementById('voiceToggle');
                                                if (voiceToggle.checked) {
                                                    // 只有当累计文本长度达到一定阈值时才进行处理，减少频繁调用
                                                    if (accumulatedText.length > 50) {
                                                        // 检测句子边界（标点符号）
                                                        var sentences = accumulatedText.split(/([。！？.!?])/);
                                                        if (sentences.length > 2) {
                                                            // 提取完整句子
                                                            var completeSentence = sentences.slice(0, -2).join('');
                                                            var lastChar = sentences[sentences.length - 2];
                                                            var remaining = sentences[sentences.length - 1];
                                                            
                                                            if (completeSentence.length > 20) {
                                                                // 合成完整句子的音频，不停止其他音频（流式输出时按顺序播放）
                                                                synthesizeAudio(completeSentence + lastChar, messageDiv, false);
                                                                accumulatedText = remaining;
                                                            }
                                                        }
                                                    }
                                                }
                                            } else if (data.type === 'finish') {
                                                console.log('Stream finished');
                                                
                                                // 处理剩余的文本
                                                var voiceToggle = document.getElementById('voiceToggle');
                                                if (voiceToggle.checked && accumulatedText.length > 0) {
                                                    // 合成剩余文本的音频，不停止其他音频（流式输出时按顺序播放）
                                                    synthesizeAudio(accumulatedText, messageDiv, false);
                                                }
                                                
                                                // 等待流式音频队列播放完成后再创建重播按钮
                                                function createReplayButtonWhenQueueEmpty() {
                                                    if (globalAudioQueue.length === 0 && !isGlobalPlaying) {
                                                        console.log('创建重播按钮，messageFullAudioUrl:', messageFullAudioUrl);
                                                        if (messageFullAudioUrl) {
                                                    var replayButton = document.createElement('button');
                                                    replayButton.className = 'play-audio-btn';
                                                    replayButton.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5v14l11-7z" fill="#4A90E2"></path></svg>';
                                                    replayButton.title = '重播';
                                                    // 使用完整音频URL的路径部分作为data-audio-url
                                                    replayButton.setAttribute('data-audio-url', messageFullAudioUrl.replace(window.location.origin, ''));
                                                    replayButton.style.marginTop = '8px';
                                                    replayButton.style.padding = '8px';
                                                    replayButton.style.border = '2px solid #4A90E2';
                                                    replayButton.style.borderRadius = '50%';
                                                    replayButton.style.backgroundColor = '#ffffff';
                                                    replayButton.style.cursor = 'pointer';
                                                    replayButton.style.width = '40px';
                                                    replayButton.style.height = '40px';
                                                    replayButton.style.display = 'flex';
                                                    replayButton.style.alignItems = 'center';
                                                    replayButton.style.justifyContent = 'center';
                                                    replayButton.style.opacity = '0.8';
                                                    replayButton.style.transition = 'all 0.3s ease';
                                                    replayButton.style.zIndex = '10';
                                                    replayButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                                    replayButton.style.userSelect = 'none';
                                                    replayButton.style.outline = 'none';
                                                    
                                                    replayButton.addEventListener('mouseenter', function() {
                                                        replayButton.style.backgroundColor = '#4A90E2';
                                                        replayButton.style.borderColor = '#357ABD';
                                                        replayButton.style.opacity = '1';
                                                        replayButton.style.transform = 'scale(1.1)';
                                                        replayButton.style.boxShadow = '0 4px 8px rgba(74, 144, 226, 0.3)';
                                                    });
                                                    
                                                    replayButton.addEventListener('mouseleave', function() {
                                                        replayButton.style.backgroundColor = '#ffffff';
                                                        replayButton.style.borderColor = '#4A90E2';
                                                        replayButton.style.opacity = '0.8';
                                                        replayButton.style.transform = 'scale(1)';
                                                        replayButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                                    });
                                                    
                                                    replayButton.addEventListener('mousedown', function() {
                                                        replayButton.style.transform = 'scale(0.95)';
                                                    });
                                                    
                                                    replayButton.addEventListener('mouseup', function() {
                                                        replayButton.style.transform = 'scale(1)';
                                                    });
                                                    
                                                    replayButton.onclick = function() {
                                                        console.log('重播按钮被点击');
                                                        // 停止当前播放
                                                        stopAllAudio();
                                                        // 添加短暂延迟，确保旧的音频完全停止
                                                        setTimeout(function() {
                                                            // 播放完整音频
                                                            var fullAudio = new Audio(messageFullAudioUrl);
                                                            // 将音频添加到活动列表
                                                            activeAudios.push(fullAudio);
                                                            fullAudio.play().catch(function(err) {
                                                                console.error('重播失败:', err);
                                                                // 从活动列表中移除
                                                                var index = activeAudios.indexOf(fullAudio);
                                                                if (index > -1) {
                                                                    activeAudios.splice(index, 1);
                                                                }
                                                            });
                                                            // 监听播放结束事件
                                                            fullAudio.addEventListener('ended', function() {
                                                                // 从活动列表中移除
                                                                var index = activeAudios.indexOf(fullAudio);
                                                                if (index > -1) {
                                                                    activeAudios.splice(index, 1);
                                                                }
                                                            });
                                                        }, 100); // 100毫秒延迟
                                                    };
                                                    
                                                    // 将按钮添加到头像内部（下方）
                                                    var avatarDiv = messageDiv.querySelector('.message-avatar');
                                                            if (avatarDiv) {
                                                                // 将按钮插入到头像内部的底部
                                                                avatarDiv.appendChild(replayButton);
                                                            } else {
                                                                messageDiv.appendChild(replayButton);
                                                            }
                                                            // 重播按钮添加完成后，重新保存聊天记录
                                                            console.log('重播按钮添加完成，重新保存聊天记录');
                                                            saveChatHistory();
                                                        }
                                                    } else {
                                                        // 如果队列还没有播放完成，等待100毫秒后再次检查
                                                        setTimeout(createReplayButtonWhenQueueEmpty, 100);
                                                    }
                                                }
                                                
                                                // 开始等待队列播放完成后创建重播按钮
                                                createReplayButtonWhenQueueEmpty();
                                            }
                                        } catch (e) {
                                            console.error('解析SSE数据失败:', e);
                                        }
                                    }
                                });
                                
                                processChunk();
                            }).catch(function(error) {
                                console.error('读取流失败:', error);
                                contentDiv.textContent = '抱歉，发生了错误，请稍后再试';
                            });
                        }
                        
                        processChunk();
                    } else {
                        // 非流式响应，解析JSON
                        return response.json();
                    }
                })
                .then(function(data) {
                    if (data) {
                        addMessage(data.response, false);
                        
                        if (data.session_id) {
                            sessionId = data.session_id;
                            localStorage.setItem('sessionId', sessionId);
                        }
                        
                        if (data.audio_url) {
                            var audioUrl = window.location.origin + data.audio_url;
                            var audio = new Audio(audioUrl);
                            
                            var messageDiv = chatContainer.lastElementChild;
                            var avatarDiv = messageDiv.querySelector('.message-avatar');
                            
                            if (avatarDiv) {
                                var playButton = document.createElement('button');
                                playButton.className = 'play-audio-btn';
                                playButton.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5v14l11-7z" fill="#4A90E2"></path></svg>';
                                playButton.title = '播放';
                                playButton.setAttribute('data-audio-url', data.audio_url);
                                playButton.style.marginTop = '8px';
                                playButton.style.padding = '8px';
                                playButton.style.border = '2px solid #4A90E2';
                                playButton.style.borderRadius = '50%';
                                playButton.style.backgroundColor = '#ffffff';
                                playButton.style.cursor = 'pointer';
                                playButton.style.width = '40px';
                                playButton.style.height = '40px';
                                playButton.style.display = 'flex';
                                playButton.style.alignItems = 'center';
                                playButton.style.justifyContent = 'center';
                                playButton.style.opacity = '0.8';
                                playButton.style.transition = 'all 0.3s ease';
                                playButton.style.zIndex = '10';
                                playButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                playButton.style.userSelect = 'none';
                                playButton.style.outline = 'none';
                                
                                playButton.addEventListener('mouseenter', function() {
                                    playButton.style.backgroundColor = '#4A90E2';
                                    playButton.style.borderColor = '#357ABD';
                                    playButton.style.opacity = '1';
                                    playButton.style.transform = 'scale(1.1)';
                                    playButton.style.boxShadow = '0 4px 8px rgba(74, 144, 226, 0.3)';
                                });
                                
                                playButton.addEventListener('mouseleave', function() {
                                    playButton.style.backgroundColor = '#ffffff';
                                    playButton.style.borderColor = '#4A90E2';
                                    playButton.style.opacity = '0.8';
                                    playButton.style.transform = 'scale(1)';
                                    playButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                });
                                
                                playButton.addEventListener('mousedown', function() {
                                    playButton.style.transform = 'scale(0.95)';
                                });
                                
                                playButton.addEventListener('mouseup', function() {
                                    playButton.style.transform = 'scale(1)';
                                });
                                
                                // 为音频对象添加事件监听器（只添加一次）
                                audio.addEventListener('ended', function() {
                                    playButton.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5v14l11-7z" fill="#4A90E2"></path></svg>';
                                    // 从活动列表中移除
                                    var index = activeAudios.indexOf(audio);
                                    if (index > -1) {
                                        activeAudios.splice(index, 1);
                                    }
                                });
                                
                                audio.addEventListener('pause', function() {
                                    playButton.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5v14l11-7z" fill="#4A90E2"></path></svg>';
                                    // 从活动列表中移除
                                    var index = activeAudios.indexOf(audio);
                                    if (index > -1) {
                                        activeAudios.splice(index, 1);
                                    }
                                });
                                
                                playButton.addEventListener('click', function() {
                                    // 停止当前播放
                                    stopAllAudio();
                                    // 将音频添加到活动列表
                                    activeAudios.push(audio);
                                    audio.play().then(function() {
                                        playButton.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>';
                                    }).catch(function(err) {
                                        console.error('音频播放失败:', err);
                                        playButton.innerHTML = '❌';
                                        window.open(audioUrl, '_blank');
                                        // 从活动列表中移除
                                        var index = activeAudios.indexOf(audio);
                                        if (index > -1) {
                                            activeAudios.splice(index, 1);
                                        }
                                    });
                                });
                                
                                avatarDiv.appendChild(playButton);
                                // 停止当前播放的音频
                                stopAllAudio();
                                // 将音频添加到活动列表
                                activeAudios.push(audio);
                                audio.play().catch(function(err) {
                                    console.error('自动播放失败:', err);
                                    // 从活动列表中移除
                                    var index = activeAudios.indexOf(audio);
                                    if (index > -1) {
                                        activeAudios.splice(index, 1);
                                    }
                                });
                                
                                // 添加事件监听器，确保音频播放结束后从活动列表中移除
                                audio.addEventListener('ended', function() {
                                    var index = activeAudios.indexOf(audio);
                                    if (index > -1) {
                                        activeAudios.splice(index, 1);
                                    }
                                });
                                
                                audio.addEventListener('pause', function() {
                                    var index = activeAudios.indexOf(audio);
                                    if (index > -1) {
                                        activeAudios.splice(index, 1);
                                    }
                                });
                                
                                // 播放按钮添加完成后，重新保存聊天记录
                                console.log('播放按钮添加完成，重新保存聊天记录');
                                saveChatHistory();
                            }
                        }
                    }
                })
                .catch(function(error) {
                    chatContainer.removeChild(loadingDiv);
                    addMessage('抱歉，发生了错误，请稍后再试', false);
                    console.error('Error:', error);
                });
            } else {
            // 非流式输出
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            })
            .then(function(response) {
                chatContainer.removeChild(loadingDiv);
                return response.json();
            })
            .then(function(data) {
                addMessage(data.response, false);
                
                if (data.session_id) {
                    sessionId = data.session_id;
                    localStorage.setItem('sessionId', sessionId);
                }
                
                // 确保同时输出文字和语音
                var voiceToggle = document.getElementById('voiceToggle');
                if (voiceToggle.checked) {
                    if (data.audio_url) {
                        var audioUrl = window.location.origin + data.audio_url;
                        var audio = new Audio(audioUrl);
                        
                        var messageDiv = chatContainer.lastElementChild;
                        var avatarDiv = messageDiv.querySelector('.message-avatar');
                        
                        if (avatarDiv) {
                            var playButton = document.createElement('button');
                            playButton.className = 'play-audio-btn';
                            playButton.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5v14l11-7z" fill="#4A90E2"></path></svg>';
                            playButton.title = '播放';
                            playButton.setAttribute('data-audio-url', data.audio_url);
                            playButton.style.marginTop = '8px';
                            playButton.style.padding = '8px';
                            playButton.style.border = '2px solid #4A90E2';
                            playButton.style.borderRadius = '50%';
                            playButton.style.backgroundColor = '#ffffff';
                            playButton.style.cursor = 'pointer';
                            playButton.style.width = '40px';
                            playButton.style.height = '40px';
                            playButton.style.display = 'flex';
                            playButton.style.alignItems = 'center';
                            playButton.style.justifyContent = 'center';
                            playButton.style.opacity = '0.8';
                            playButton.style.transition = 'all 0.3s ease';
                            playButton.style.zIndex = '10';
                            playButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                            playButton.style.userSelect = 'none';
                            playButton.style.outline = 'none';
                            
                            playButton.addEventListener('mouseenter', function() {
                                playButton.style.backgroundColor = '#4A90E2';
                                playButton.style.borderColor = '#357ABD';
                                playButton.style.opacity = '1';
                                playButton.style.transform = 'scale(1.1)';
                                playButton.style.boxShadow = '0 4px 8px rgba(74, 144, 226, 0.3)';
                            });
                            
                            playButton.addEventListener('mouseleave', function() {
                                playButton.style.backgroundColor = '#ffffff';
                                playButton.style.borderColor = '#4A90E2';
                                playButton.style.opacity = '0.8';
                                playButton.style.transform = 'scale(1)';
                                playButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                            });
                            
                            playButton.addEventListener('mousedown', function() {
                                playButton.style.transform = 'scale(0.95)';
                            });
                            
                            playButton.addEventListener('mouseup', function() {
                                playButton.style.transform = 'scale(1)';
                            });
                            
                            // 为音频对象添加事件监听器（只添加一次）
                            audio.addEventListener('ended', function() {
                                playButton.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5v14l11-7z" fill="#4A90E2"></path></svg>';
                                // 从活动列表中移除
                                var index = activeAudios.indexOf(audio);
                                if (index > -1) {
                                    activeAudios.splice(index, 1);
                                }
                            });
                            
                            audio.addEventListener('pause', function() {
                                playButton.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5v14l11-7z" fill="#4A90E2"></path></svg>';
                                // 从活动列表中移除
                                var index = activeAudios.indexOf(audio);
                                if (index > -1) {
                                    activeAudios.splice(index, 1);
                                }
                            });
                            
                            playButton.addEventListener('click', function() {
                                // 停止当前播放
                                stopAllAudio();
                                // 将音频添加到活动列表
                                activeAudios.push(audio);
                                audio.play().then(function() {
                                    playButton.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>';
                                }).catch(function(err) {
                                    console.error('音频播放失败:', err);
                                    playButton.innerHTML = '❌';
                                    window.open(audioUrl, '_blank');
                                    // 从活动列表中移除
                                    var index = activeAudios.indexOf(audio);
                                    if (index > -1) {
                                        activeAudios.splice(index, 1);
                                    }
                                });
                            });
                            
                            avatarDiv.appendChild(playButton);
                            // 播放按钮添加完成后，重新保存聊天记录
                            console.log('播放按钮添加完成，重新保存聊天记录');
                            saveChatHistory();
                            // 停止当前播放的音频
                            stopAllAudio();
                            // 将音频添加到活动列表
                            activeAudios.push(audio);
                            audio.play().catch(function(err) {
                                console.error('自动播放失败:', err);
                                // 从活动列表中移除
                                var index = activeAudios.indexOf(audio);
                                if (index > -1) {
                                    activeAudios.splice(index, 1);
                                }
                            });
                            
                            // 添加事件监听器，确保音频播放结束后从活动列表中移除
                            audio.addEventListener('ended', function() {
                                var index = activeAudios.indexOf(audio);
                                if (index > -1) {
                                    activeAudios.splice(index, 1);
                                }
                            });
                            
                            audio.addEventListener('pause', function() {
                                var index = activeAudios.indexOf(audio);
                                if (index > -1) {
                                    activeAudios.splice(index, 1);
                                }
                            });
                        }
                    } else {
                        // 如果没有音频URL，使用实时音频合成
                        var messageDiv = chatContainer.lastElementChild;
                        synthesizeAudio(data.response, messageDiv);
                    }
                }
            })
            .catch(function(error) {
                chatContainer.removeChild(loadingDiv);
                addMessage('抱歉，发生了错误，请稍后再试', false);
                console.error('Error:', error);
            });
        }
        }
        
        // 更新语音开关样式
        function updateVoiceToggleStyle() {
            var voiceToggle = document.getElementById('voiceToggle');
            var voiceToggleLabel = document.getElementById('voiceToggleLabel');
            
            if (voiceToggle.checked) {
                voiceToggleLabel.classList.add('active');
            } else {
                voiceToggleLabel.classList.remove('active');
            }
        }
        
        // 更新流式输出开关样式
        function updateStreamToggleStyle() {
            var streamToggle = document.getElementById('streamToggle');
            var streamToggleLabel = document.getElementById('streamToggleLabel');
            
            if (streamToggle.checked) {
                streamToggleLabel.classList.add('active');
            } else {
                streamToggleLabel.classList.remove('active');
            }
        }
        
        // 实时音频合成函数
        function stopAllAudio() {
            // 停止所有正在播放的音频
            activeAudios.forEach(function(audio) {
                audio.pause();
                audio.currentTime = 0;
                // 移除所有事件监听器，防止音频继续播放
                audio.removeEventListener('canplaythrough', audio._canplaythroughListener);
                audio.removeEventListener('ended', audio._endedListener);
                audio.removeEventListener('error', audio._errorListener);
            });
            activeAudios = [];
            
            // 清空队列
            globalAudioQueue = [];
            pendingAudioRequests = [];
            isGlobalPlaying = false;
            isProcessingQueue = false;
            
            // 取消所有正在进行的音频合成请求
            if (currentAudioRequest) {
                currentAudioRequest.abort();
                currentAudioRequest = null;
            }
            
            console.log('已停止所有音频播放和合成');
        }
        
        function playNextAudio() {
            if (globalAudioQueue.length === 0) {
                isGlobalPlaying = false;
                return;
            }
            
            isGlobalPlaying = true;
            var audioUrl = globalAudioQueue.shift();
            var audio = new Audio(audioUrl);
            
            // 将音频添加到活动列表
            activeAudios.push(audio);
            
            // 预加载音频
            audio.preload = 'auto';
            
            // 定义事件监听器函数，以便可以移除
            audio._canplaythroughListener = function() {
                // 只有当没有被停止时才播放
                if (activeAudios.indexOf(audio) > -1) {
                    audio.play().catch(function(err) {
                        console.error('音频播放失败:', err);
                        // 从活动列表中移除
                        var index = activeAudios.indexOf(audio);
                        if (index > -1) {
                            activeAudios.splice(index, 1);
                        }
                        // 播放失败时继续播放下一个
                        playNextAudio();
                    });
                }
            };
            
            audio._endedListener = function() {
                // 从活动音频列表中移除
                var index = activeAudios.indexOf(audio);
                if (index > -1) {
                    activeAudios.splice(index, 1);
                }
                // 播放下一个音频
                playNextAudio();
            };
            
            audio._errorListener = function(err) {
                console.error('音频加载失败:', err);
                // 从活动列表中移除
                var index = activeAudios.indexOf(audio);
                if (index > -1) {
                    activeAudios.splice(index, 1);
                }
                // 加载失败时继续播放下一个
                playNextAudio();
            };
            
            // 添加事件监听器
            audio.addEventListener('canplaythrough', audio._canplaythroughListener);
            audio.addEventListener('ended', audio._endedListener);
            audio.addEventListener('error', audio._errorListener);
        }
        
        function processAudioQueue() {
            if (isProcessingQueue || pendingAudioRequests.length === 0) {
                return;
            }
            
            isProcessingQueue = true;
            var request = pendingAudioRequests.shift();
            var text = request.text;
            var messageDiv = request.messageDiv;
            
            // 创建AbortController来控制请求
            var controller = new AbortController();
            currentAudioRequest = controller;
            
            fetch('/api/synthesize_audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    password: currentPassword,
                    role: currentRole
                }),
                signal: controller.signal
            })
            .then(function(response) {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('HTTP error ' + response.status);
                }
            })
            .then(function(data) {
                if (data.success && data.audio_url) {
                    var audioUrl = window.location.origin + data.audio_url;
                    
                    // 将音频添加到队列末尾（确保按顺序播放）
                    globalAudioQueue.push(audioUrl);
                    
                    // 如果当前没有播放，开始播放队列
                    if (!isGlobalPlaying) {
                        playNextAudio();
                    }
                }
            })
            .catch(function(error) {
                if (error.name !== 'AbortError') {
                    console.error('音频合成失败:', error);
                }
            })
            .finally(function() {
                // 如果当前请求还在进行中，清除currentAudioRequest
                if (currentAudioRequest === controller) {
                    currentAudioRequest = null;
                }
                isProcessingQueue = false;
                // 继续处理下一个请求
                processAudioQueue();
            });
        }
        
        function synthesizeAudio(text, messageDiv, stopOthers = true) {
            if (!currentPassword) return;
            
            // 如果需要停止其他音频（例如新消息或按钮点击时）
            if (stopOthers) {
                stopAllAudio();
            }
            
            // 将请求添加到队列
            pendingAudioRequests.push({
                text: text,
                messageDiv: messageDiv
            });
            
            // 开始处理队列
            processAudioQueue();
        }
        
        function initVoiceRecognition() {
            var voiceInputBtn = document.getElementById('voiceInputBtn');
            
            // 检查浏览器支持
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                console.warn('浏览器不支持媒体设备API');
                voiceInputBtn.disabled = true;
                voiceInputBtn.style.opacity = '0.5';
                // 添加提示信息到欢迎语下方
                var welcomeMessage = document.querySelector('.message-content');
                if (welcomeMessage) {
                    var tipDiv = document.createElement('div');
                    tipDiv.className = 'voice-support-tip';
                    tipDiv.textContent = '您的浏览器不支持语音输入功能';
                    welcomeMessage.parentNode.appendChild(tipDiv);
                }
                return;
            }
            
            // 绑定语音输入按钮点击事件
            voiceInputBtn.addEventListener('click', function() {
                if (isListening) {
                    // 停止录音
                    stopRecording();
                } else {
                    // 开始录音
                    startRecording();
                }
            });
        }
        

        
        // 获取浏览器支持的音频格式（带编解码器）
        function getSupportedAudioFormat() {
            var formats = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/ogg;codecs=vorbis',
                'audio/ogg',
                'audio/wav',
                'audio/mp4'
            ];
            
            for (var i = 0; i < formats.length; i++) {
                var format = formats[i];
                if (MediaRecorder.isTypeSupported(format)) {
                    return format;
                }
            }
            
            // 如果没有支持的格式，使用默认格式
            return 'audio/webm';
        }
        
        // 开始录音（实时转写）
        function startRecording() {
            navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                var voiceInputBtn = document.getElementById('voiceInputBtn');
                
                // 获取浏览器支持的音频格式
                var mimeType = getSupportedAudioFormat();
                mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });
                
                audioChunks = [];
                var transcript = '';
                
                // 每500ms发送一次音频片段进行实时识别
                var recognitionInterval = setInterval(function() {
                    if (mediaRecorder && mediaRecorder.state === 'recording' && audioChunks.length > 0) {
                        var currentChunks = audioChunks.slice();
                        audioChunks = [];
                        var audioBlob = new Blob(currentChunks, { type: mimeType });
                        sendAudioForRealTimeRecognition(audioBlob, mimeType, function(result) {
                            if (result.success) {
                                transcript += result.transcript + ' ';
                                document.getElementById('userInput').value = transcript;
                            }
                        });
                    }
                }, 500);
                
                mediaRecorder.ondataavailable = function(event) {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = function() {
                    isListening = false;
                    clearInterval(recognitionInterval);
                    voiceInputBtn.classList.remove('active');
                    voiceInputBtn.innerHTML = '<i class="fas fa-phone-alt"></i>';
                    
                    // 发送最后一段音频进行识别
                    if (audioChunks.length > 0) {
                        var audioBlob = new Blob(audioChunks, { type: mimeType });
                        sendAudioForRecognition(audioBlob, mimeType);
                    }
                    
                    // 停止所有音频轨道
                    stream.getTracks().forEach(function(track) {
                        track.stop();
                    });
                };
                
                mediaRecorder.start(100); // 每100ms获取一次数据
                isListening = true;
                voiceInputBtn.classList.add('active');
                voiceInputBtn.innerHTML = '<i class="fas fa-phone-slash"></i>';
                addMessage('正在录音并实时转写，请说话...', false);
            })
            .catch(function(error) {
                console.error('获取麦克风权限失败:', error);
                addMessage('错误: ' + error.message, false);
            });
        }
        
        // 停止录音
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
            }
        }
        
        // 发送音频到服务器进行实时识别（不显示消息）
        function sendAudioForRealTimeRecognition(audioBlob, mimeType, callback) {
            // 根据MIME类型获取文件扩展名
            var extension = mimeType.split('/')[1].split(';')[0];
            
            var formData = new FormData();
            formData.append('audio', audioBlob, 'recording.' + extension);
            
            fetch('/api/speech_recognition', {
                method: 'POST',
                body: formData
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(result) {
                console.log('实时语音识别结果:', result);
                if (callback) {
                    callback(result);
                }
            })
            .catch(function(error) {
                console.error('实时语音识别失败:', error);
                if (callback) {
                    callback({ success: false, error: '识别失败' });
                }
            });
        }
        
        // 发送音频到服务器进行最终识别
        function sendAudioForRecognition(audioBlob, mimeType) {
            addMessage('正在识别语音...', false);
            
            // 根据MIME类型获取文件扩展名
            var extension = mimeType.split('/')[1].split(';')[0];
            
            var formData = new FormData();
            formData.append('audio', audioBlob, 'recording.' + extension);
            
            fetch('/api/speech_recognition', {
                method: 'POST',
                body: formData
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(result) {
                console.log('语音识别结果:', result);
                
                if (result.success) {
                    var transcript = result.transcript;
                    document.getElementById('userInput').value = transcript;
                    addMessage('语音识别成功: ' + transcript, false);
                    setTimeout(sendMessage, 500);
                } else {
                    addMessage('错误: ' + result.error, false);
                }
            })
            .catch(function(error) {
                console.error('发送音频到服务器失败:', error);
                addMessage('错误: 语音识别请求失败', false);
            });
        }
        
        // 绑定播放按钮事件
        function bindPlayButtonEvents() {
            var playButtons = document.querySelectorAll('.play-audio-btn');
            playButtons.forEach(function(button) {
                // 只绑定一次事件
                if (button.dataset.bound) return;
                
                button.addEventListener('click', function() {
                    var audioUrl = window.location.origin + this.dataset.audioUrl;
                    var audio = new Audio(audioUrl);
                    
                    // 停止当前播放
                    stopAllAudio();
                    // 将音频添加到活动列表
                    activeAudios.push(audio);
                    
                    // 添加加载错误处理
                    audio.addEventListener('error', function() {
                        console.error('音频加载失败:', audioUrl);
                        button.innerHTML = '❌';
                        // 尝试使用本地地址重试
                        var localAudioUrl = 'http://localhost:5000' + button.dataset.audioUrl;
                        console.log('尝试使用本地地址重试:', localAudioUrl);
                        var localAudio = new Audio(localAudioUrl);
                        localAudio.play().then(function() {
                            button.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>';
                        }).catch(function(err) {
                            console.error('本地地址重试也失败:', err);
                            window.open(audioUrl, '_blank');
                        });
                        // 从活动列表中移除
                        var index = activeAudios.indexOf(audio);
                        if (index > -1) {
                            activeAudios.splice(index, 1);
                        }
                    });
                    
                    audio.play().then(function() {
                        button.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>';
                    }).catch(function(err) {
                        console.error('音频播放失败:', err);
                        button.innerHTML = '❌';
                        window.open(audioUrl, '_blank');
                        // 从活动列表中移除
                        var index = activeAudios.indexOf(audio);
                        if (index > -1) {
                            activeAudios.splice(index, 1);
                        }
                    });
                    
                    // 为音频对象添加事件监听器
                    audio.addEventListener('ended', function() {
                        button.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5v14l11-7z" fill="#4A90E2"></path></svg>';
                        // 从活动列表中移除
                        var index = activeAudios.indexOf(audio);
                        if (index > -1) {
                            activeAudios.splice(index, 1);
                        }
                    });
                    
                    audio.addEventListener('pause', function() {
                        button.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 5v14l11-7z" fill="#4A90E2"></path></svg>';
                        // 从活动列表中移除
                        var index = activeAudios.indexOf(audio);
                        if (index > -1) {
                            activeAudios.splice(index, 1);
                        }
                    });
                });
                
                // 添加鼠标悬停效果
                button.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#4A90E2';
                    this.style.borderColor = '#357ABD';
                    this.style.opacity = '1';
                    this.style.transform = 'scale(1.1)';
                    this.style.boxShadow = '0 4px 8px rgba(74, 144, 226, 0.3)';
                });
                
                button.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = '#ffffff';
                    this.style.borderColor = '#4A90E2';
                    this.style.opacity = '0.8';
                    this.style.transform = 'scale(1)';
                    this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                });
                
                button.addEventListener('mousedown', function() {
                    this.style.transform = 'scale(0.95)';
                });
                
                button.addEventListener('mouseup', function() {
                    this.style.transform = 'scale(1)';
                });
                
                button.dataset.bound = 'true';
            });
        }

        // 加载聊天记录函数
        function loadChatHistory(role) {
            console.log('loadChatHistory调用，角色:', role, '会话ID:', sessionId);
            if (!sessionId) {
                console.error('会话ID为空，无法加载聊天记录');
                return;
            }
            
            // 从服务器加载聊天记录
            console.log('发送聊天记录请求:', `/api/chat-history?session_id=${sessionId}&role=${role}`);
            fetch(`/api/chat-history?session_id=${sessionId}&role=${role}`)
            .then(response => response.json())
            .then(data => {
                console.log('聊天记录响应:', data);
                var chatContainer = document.getElementById('chatContainer');
                
                if (data.success && data.chat_history) {
                    console.log('聊天记录内容长度:', data.chat_history.length);
                    chatContainer.innerHTML = data.chat_history;
                    console.log('聊天记录加载成功');
                    // 绑定播放按钮事件
                    bindPlayButtonEvents();
                } else {
                    console.log('没有找到聊天记录，尝试从本地存储加载备份');
                    // 尝试从本地存储加载备份
                    var backupHistory = localStorage.getItem(`chat_history_${sessionId}_${role}`);
                    if (backupHistory) {
                        console.log('从本地存储加载聊天记录备份成功');
                        chatContainer.innerHTML = backupHistory;
                        // 绑定播放按钮事件
                        bindPlayButtonEvents();
                    } else {
                        console.log('本地存储也没有备份，显示欢迎消息');
                        // 如果没有保存的记录，显示欢迎消息
                        var config = roleConfig[role];
                        var welcomeMessages = {
                            "ying": [
                                "旅途虽远，幸得相逢。我是荧，愿陪你走过每一段时光。",
                                "欢迎来到我的世界，我是旅行者荧。累了就停下来，我听你说。",
                                "跨越山海遇见你，真好。我是荧，愿与你分享旅途的温柔。",
                                "新的冒险即将启程，我是荧。准备好了吗？我们一起出发！",
                                "无论前路是光明还是深渊，我都会前行。我是荧，愿与你并肩。",
                                "为了重逢，我从未停下脚步。我是荧，欢迎加入我的旅程。",
                                "星海为途，信念为灯。我是荧，在此等候与你相遇。",
                                "风带来远方的消息，我是荧。愿与你共赏提瓦特的风景。",
                                "穿越时空而来，只为遇见。我是荧，欢迎来到我的世界。"
                            ],
                            "paimon": [
                                "哈喽～我是派蒙，旅行者最好的伙伴！有什么想聊的都可以告诉我哦！",
                                "哇，你来了！我是派蒙，会一直陪在你身边的应急食品！",
                                "嗨嗨～我是派蒙，今天也要一起冒险吗？"
                            ]
                        };
                        
                        var messages = welcomeMessages[role];
                        var welcomeMessage = messages[Math.floor(Math.random() * messages.length)];
                        console.log('显示欢迎消息:', welcomeMessage);
                        
                        chatContainer.innerHTML = `
                            <div class="message ai-message">
                                <div class="message-avatar">
                                    <img src="${config.avatar}" alt="${config.author}" class="avatar-small" id="avatarImage">
                                </div>
                                <div class="message-content-wrapper">
                                    <div class="message-author" id="messageAuthor">${config.author}</div>
                                    <div class="message-content">${welcomeMessage}</div>
                                </div>
                            </div>
                        `;
                    }
                }
                
                // 检查是否是初次加载
                var isFirstLoad = localStorage.getItem(`first_load_${sessionId}_${role}`);
                
                setTimeout(function() {
                    console.log(`=== ${role} 角色加载完成，开始处理滚动位置 ===`);
                    console.log(`isFirstLoad:`, isFirstLoad);
                    
                    if (!isFirstLoad) {
                        // 初次加载，滚动到最底部
                        console.log(`初次加载${role}，滚动到最底部`);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                        console.log(`滚动后的位置:`, chatContainer.scrollTop);
                        // 标记为已加载过
                        localStorage.setItem(`first_load_${sessionId}_${role}`, 'false');
                        console.log(`已标记${role}为非初次加载`);
                    } else {
                        // 恢复上次的滚动位置
                        var savedScrollTop = localStorage.getItem(`scroll_position_${sessionId}_${role}`);
                        console.log(`从localStorage读取${role}的滚动位置:`, savedScrollTop);
                        if (savedScrollTop) {
                            var scrollValue = parseInt(savedScrollTop);
                            chatContainer.scrollTop = scrollValue;
                            console.log(`恢复${role}的滚动位置为:`, scrollValue);
                            console.log(`实际滚动位置:`, chatContainer.scrollTop);
                        } else {
                            console.log(`没有保存的滚动位置，滚动到最新对话位置`);
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                            console.log(`滚动后的位置:`, chatContainer.scrollTop);
                        }
                    }
                }, 100);
            }).catch(error => {
                console.error('加载聊天记录时发生错误:', error);
            });
        }

        // 角色切换函数
        // 保存当前角色的聊天记录到数据库
        let isSavingHistory = false;
        
        function saveChatHistory() {
            if (!sessionId) return;
            
            var chatContainer = document.getElementById('chatContainer');
            var chatHistory = chatContainer.innerHTML;
            
            // 保存到本地存储作为备份
            localStorage.setItem(`chat_history_${sessionId}_${currentRole}`, chatHistory);
            console.log('聊天记录已保存到本地存储');
            
            // 如果正在保存中，跳过
            if (isSavingHistory) {
                console.log('聊天记录正在保存中，跳过本次保存');
                return;
            }
            
            isSavingHistory = true;
            
            // 发送到服务器保存
            fetch('/api/chat-history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    role: currentRole,
                    content: chatHistory
                })
            }).then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('聊天记录保存成功');
                } else {
                    console.error('聊天记录保存失败:', data.error);
                }
            }).catch(error => {
                console.error('保存聊天记录时发生错误:', error);
            }).finally(() => {
                isSavingHistory = false;
            });
        }
        
        // 页面关闭前保存聊天记录
        window.addEventListener('beforeunload', function(event) {
            if (sessionId) {
                var chatContainer = document.getElementById('chatContainer');
                var chatHistory = chatContainer.innerHTML;
                // 保存到本地存储作为备份
                localStorage.setItem(`chat_history_${sessionId}_${currentRole}`, chatHistory);
                console.log('页面关闭前已保存聊天记录到本地存储');
            }
        });
        
        // 从数据库加载指定角色的聊天记录
        // 切换角色函数
        function switchToRole(role) {
            if (role === currentRole) return;
            
            // 保存当前角色的聊天记录和滚动位置
            saveChatHistory();
            var chatContainer = document.getElementById('chatContainer');
            if (sessionId && currentRole) {
                localStorage.setItem(`scroll_position_${sessionId}_${currentRole}`, chatContainer.scrollTop);
                console.log(`保存${currentRole}的滚动位置:`, chatContainer.scrollTop);
            }
            
            // 切换角色
            currentRole = role;
            var config = roleConfig[currentRole];
            
            // 更新界面显示
            document.getElementById('avatarName').textContent = config.name;
            document.getElementById('avatarDescription').textContent = config.description;
            document.getElementById('avatarImage').src = config.avatar;
            document.getElementById('avatarImage').alt = config.author;
            document.getElementById('messageAuthor').textContent = config.author;
            
            // 加载新角色的聊天记录
            loadChatHistory(currentRole);
            
            console.log('角色已切换到:', config.name);
        }


        


        // 页面加载完成后初始化
        window.addEventListener('load', function() {
            var voiceToggle = document.getElementById('voiceToggle');
            var voiceToggleLabel = document.getElementById('voiceToggleLabel');
            var streamToggle = document.getElementById('streamToggle');
            var streamToggleLabel = document.getElementById('streamToggleLabel');
            var sendButton = document.getElementById('sendButton');
            var userInput = document.getElementById('userInput');
            var loginButton = document.getElementById('loginButton');
            var passwordInput = document.getElementById('passwordInput');
            
            // 恢复保存的状态
            var savedVoiceState = localStorage.getItem('voiceEnabled');
            if (savedVoiceState !== null) {
                voiceToggle.checked = savedVoiceState === 'true';
            }
            updateVoiceToggleStyle();
            
            // 恢复流式输出开关状态
            var savedStreamState = localStorage.getItem('streamEnabled');
            if (savedStreamState !== null) {
                streamToggle.checked = savedStreamState === 'true';
            }
            updateStreamToggleStyle();
            
            // 恢复会话ID
            sessionId = localStorage.getItem('sessionId');
            console.log('恢复会话ID:', sessionId);
            
            // 如果有会话ID，验证会话是否仍然有效
            if (sessionId) {
                fetch(`/api/chat-history?session_id=${sessionId}&role=${currentRole}`)
                .then(response => {
                    if (response.status === 401) {
                        // 会话无效，清除旧会话ID
                        console.log('会话已过期，清除旧会话ID');
                        sessionId = null;
                        localStorage.removeItem('sessionId');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success && data.chat_history) {
                        // 会话有效，加载聊天记录
                        var chatContainer = document.getElementById('chatContainer');
                        chatContainer.innerHTML = data.chat_history;
                        console.log('聊天记录加载成功');
                        
                        // 检查是否是初次加载
                        var isFirstLoad = localStorage.getItem(`first_load_${sessionId}_${currentRole}`);
                        
                        setTimeout(function() {
                            console.log(`=== 页面加载完成，开始处理滚动位置 ===`);
                            console.log(`当前角色:`, currentRole);
                            console.log(`isFirstLoad:`, isFirstLoad);
                            
                            if (!isFirstLoad) {
                                // 初次加载，滚动到最底部
                                console.log(`初次加载${currentRole}，滚动到最底部`);
                                chatContainer.scrollTop = chatContainer.scrollHeight;
                                console.log(`滚动后的位置:`, chatContainer.scrollTop);
                                // 标记为已加载过
                                localStorage.setItem(`first_load_${sessionId}_${currentRole}`, 'false');
                                console.log(`已标记${currentRole}为非初次加载`);
                            } else {
                                // 恢复上次的滚动位置
                                var savedScrollTop = localStorage.getItem(`scroll_position_${sessionId}_${currentRole}`);
                                console.log(`从localStorage读取${currentRole}的滚动位置:`, savedScrollTop);
                                if (savedScrollTop) {
                                    var scrollValue = parseInt(savedScrollTop);
                                    chatContainer.scrollTop = scrollValue;
                                    console.log(`恢复${currentRole}的滚动位置为:`, scrollValue);
                                    console.log(`实际滚动位置:`, chatContainer.scrollTop);
                                } else {
                                    console.log(`没有保存的滚动位置，滚动到最新对话位置`);
                                    chatContainer.scrollTop = chatContainer.scrollHeight;
                                    console.log(`滚动后的位置:`, chatContainer.scrollTop);
                                }
                            }
                        }, 100);
                    } else {
                        // 会话无效或没有聊天记录，显示欢迎消息
                        var config = roleConfig[currentRole];
                        var welcomeMessages = {
                            "ying": [
                                "旅途虽远，幸得相逢。我是荧，愿陪你走过每一段时光。",
                                "欢迎来到我的世界，我是旅行者荧。累了就停下来，我听你说。",
                                "跨越山海遇见你，真好。我是荧，愿与你分享旅途的温柔。",
                                "新的冒险即将启程，我是荧。准备好了吗？我们一起出发！",
                                "无论前路是光明还是深渊，我都会前行。我是荧，愿与你并肩。",
                                "为了重逢，我从未停下脚步。我是荧，欢迎加入我的旅程。",
                                "星海为途，信念为灯。我是荧，在此等候与你相遇。",
                                "风带来远方的消息，我是荧。愿与你共赏提瓦特的风景。",
                                "穿越时空而来，只为遇见。我是荧，欢迎来到我的世界。"
                            ],
                            "paimon": [
                                "哈喽～我是派蒙，旅行者最好的伙伴！有什么想聊的都可以告诉我哦！",
                                "哇，你来了！我是派蒙，会一直陪在你身边的应急食品！",
                                "嗨嗨～我是派蒙，今天也要一起冒险吗？"
                            ]
                        };
                        
                        var messages = welcomeMessages[currentRole];
                        var welcomeMessage = messages[Math.floor(Math.random() * messages.length)];
                        
                        var chatContainer = document.getElementById('chatContainer');
                        chatContainer.innerHTML = `
                            <div class="message ai-message">
                                <div class="message-avatar">
                                    <img src="${config.avatar}" alt="${config.author}" class="avatar-small" id="avatarImage">
                                </div>
                                <div class="message-content-wrapper">
                                    <div class="message-author" id="messageAuthor">${config.author}</div>
                                    <div class="message-content">${welcomeMessage}</div>
                                </div>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('验证会话时发生错误:', error);
                    sessionId = null;
                    localStorage.removeItem('sessionId');
                    
                    // 显示欢迎消息
                    var config = roleConfig[currentRole];
                    var welcomeMessages = {
                        "ying": [
                            "旅途虽远，幸得相逢。我是荧，愿陪你走过每一段时光。",
                            "欢迎来到我的世界，我是旅行者荧。累了就停下来，我听你说。",
                            "跨越山海遇见你，真好。我是荧，愿与你分享旅途的温柔。",
                            "新的冒险即将启程，我是荧。准备好了吗？我们一起出发！",
                            "无论前路是光明还是深渊，我都会前行。我是荧，愿与你并肩。",
                            "为了重逢，我从未停下脚步。我是荧，欢迎加入我的旅程。",
                            "星海为途，信念为灯。我是荧，在此等候与你相遇。",
                            "风带来远方的消息，我是荧。愿与你共赏提瓦特的风景。",
                            "穿越时空而来，只为遇见。我是荧，欢迎来到我的世界。"
                        ],
                        "paimon": [
                            "哈喽～我是派蒙，旅行者最好的伙伴！有什么想聊的都可以告诉我哦！",
                            "哇，你来了！我是派蒙，会一直陪在你身边的应急食品！",
                            "嗨嗨～我是派蒙，今天也要一起冒险吗？"
                        ]
                    };
                    
                    var messages = welcomeMessages[currentRole];
                    var welcomeMessage = messages[Math.floor(Math.random() * messages.length)];
                    
                    var chatContainer = document.getElementById('chatContainer');
                    chatContainer.innerHTML = `
                        <div class="message ai-message">
                            <div class="message-avatar">
                                <img src="${config.avatar}" alt="${config.author}" class="avatar-small" id="avatarImage">
                            </div>
                            <div class="message-content-wrapper">
                                <div class="message-author" id="messageAuthor">${config.author}</div>
                                <div class="message-content">${welcomeMessage}</div>
                            </div>
                        </div>
                    `;
                });
            } else {
                // 没有会话ID，显示欢迎消息
                loadChatHistory(currentRole);
            }
            
            // 绑定语音开关事件
            voiceToggle.addEventListener('change', function() {
                localStorage.setItem('voiceEnabled', this.checked);
                updateVoiceToggleStyle();
            });
            
            // 绑定流式输出开关事件
            streamToggle.addEventListener('change', function() {
                localStorage.setItem('streamEnabled', this.checked);
                updateStreamToggleStyle();
            });
            
            // 绑定发送按钮事件
            sendButton.addEventListener('click', sendMessage);
            userInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            // 绑定登录按钮点击事件
            console.log('=== 开始绑定登录按钮点击事件 ===');
            if (loginButton) {
                console.log('登录按钮存在，开始绑定点击事件');
                loginButton.addEventListener('click', handleLoginClick);
                console.log('登录按钮点击事件绑定完成');
            } else {
                console.error('登录按钮不存在，无法绑定点击事件');
            }
            
            // 绑定角色头像点击事件
            var yingAvatar = document.getElementById('yingAvatar');
            var paimonAvatar = document.getElementById('paimonAvatar');
            
            if (yingAvatar) {
                yingAvatar.addEventListener('click', function() {
                    switchToRole('ying');
                });
            }
            
            if (paimonAvatar) {
                paimonAvatar.addEventListener('click', function() {
                    switchToRole('paimon');
                });
            }
            
            // 登录输入框回车事件
            if (passwordInput) {
                passwordInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        handleLoginClick();
                    }
                });
            }
            
            // 添加滚动事件监听器，保存每个角色的滚动位置
            var chatContainer = document.getElementById('chatContainer');
            chatContainer.addEventListener('scroll', function() {
                if (sessionId && currentRole) {
                    localStorage.setItem(`scroll_position_${sessionId}_${currentRole}`, chatContainer.scrollTop);
                    console.log(`滚动事件触发，保存${currentRole}的滚动位置:`, chatContainer.scrollTop);
                }
            });
            
            // 检查localStorage是否可用
            function isLocalStorageAvailable() {
                try {
                    var testKey = '__test__';
                    localStorage.setItem(testKey, testKey);
                    localStorage.removeItem(testKey);
                    return true;
                } catch (e) {
                    return false;
                }
            }
            
            // 尝试自动登录
            setTimeout(function() {
                var storageAvailable = isLocalStorageAvailable();
                console.log('存储检查:', { localStorageAvailable: storageAvailable });
                
                if (!storageAvailable) {
                    console.log('localStorage不可用，无法自动登录');
                    return;
                }
                
                var savedPassword = localStorage.getItem('savedPassword');
                console.log('自动登录检查:', { 
                    savedPassword: savedPassword ? '存在' : '不存在',
                    passwordLength: savedPassword ? savedPassword.length : 0
                });
                
                if (savedPassword && savedPassword.length > 0) {
                    console.log('开始自动登录...');
                    login(savedPassword).then(function(success) {
                        console.log('自动登录结果:', success ? '成功' : '失败');
                    });
                } else {
                    console.log('没有保存的口令或口令为空，显示登录界面');
                }
            }, 1000); // 延迟1秒，确保页面完全加载
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """主页"""
    logger.info("收到根路由请求")
    try:
        import random
        import time
        
        logger.info("测试1: 导入成功")
        
        # 测试config模块
        logger.info(f"config模块存在: {config is not None}")
        
        # 测试WELCOME_MESSAGES
        logger.info(f"WELCOME_MESSAGES存在: {'WELCOME_MESSAGES' in dir(config)}")
        if 'WELCOME_MESSAGES' in dir(config):
            logger.info(f"WELCOME_MESSAGES类型: {type(config.WELCOME_MESSAGES)}")
            logger.info(f"WELCOME_MESSAGES包含ying: {'ying' in config.WELCOME_MESSAGES}")
            
        logger.info("测试2: config访问成功")
        
        # 使用默认角色（荧）的欢迎语
        welcome_message = random.choice(config.WELCOME_MESSAGES["ying"])
        logger.info(f"欢迎语: {welcome_message}")
        
        # 添加版本号，强制浏览器刷新
        version = int(time.time())
        logger.info(f"版本号: {version}")
        
        logger.info("测试3: 变量准备完成")
        
        logger.info("开始渲染模板")
        html_content = render_template_string(HTML_TEMPLATE, welcome_message=welcome_message, version=version)
        logger.info("模板渲染成功")
        
        # 创建Response对象并设置缓存控制头
        response = Response(html_content)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        logger.info("缓存控制头添加成功")
        return response
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}", exc_info=True)
        return f"服务器内部错误: {str(e)}", 500

@app.route('/test')
def test():
    """测试端点"""
    logger.info("收到测试端点请求")
    return "测试成功"

@app.route('/test-login')
def test_login():
    """测试登录页面"""
    with open('test_login_button.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/simple-test')
def simple_test():
    """简单测试页面"""
    with open('simple_test.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/minimal-test')
def minimal_test():
    """极简测试页面"""
    with open('minimal_test.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/console-test')
def console_test():
    """控制台测试页面"""
    with open('test_login_console.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/direct-test')
def direct_test():
    """直接测试页面"""
    with open('test_login_direct.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/minimal-login')
def minimal_login():
    """极简登录测试页面"""
    with open('test_minimal_login.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/login-debug')
def login_debug():
    """登录按钮调试页面"""
    with open('test_login_debug.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/button-test')
def button_test():
    """按钮点击测试页面"""
    with open('test_button_click.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/test')
def test_page():
    """测试页面"""
    with open('test_page.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/test_voice')
def test_voice_page():
    """语音测试页面"""
    with open('test_voice.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/test_mediarecorder')
def test_mediarecorder_page():
    """MediaRecorder API测试页面"""
    with open('test_mediarecorder.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/audio/<filename>')
def serve_audio(filename):
    """提供音频文件下载"""
    try:
        audio_path = os.path.join(AUDIO_DIR, filename)
        if os.path.exists(audio_path):
            return send_file(audio_path, mimetype='audio/wav')
        else:
            return jsonify({'error': '音频文件不存在'}), 404
    except Exception as e:
        logger.error(f"提供音频文件失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/speech_recognition', methods=['POST'])
@rate_limiter.rate_limit('api_speech')
def speech_recognition():
    """语音识别API端点"""
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '没有提供音频文件'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'success': False, 'error': '文件名不能为空'}), 400
        
        # 获取文件扩展名
        filename = audio_file.filename
        file_extension = filename.split('.')[-1] if '.' in filename else 'wav'
        
        # 读取音频数据
        audio_data = audio_file.read()
        
        # 使用硅基流动ASR进行识别
        asr = SiliconFlowASR()
        transcript = asr.recognize_from_audio_data(audio_data, file_extension)
        
        if transcript:
            logger.info(f"语音识别成功: {transcript}")
            return jsonify({'success': True, 'transcript': transcript})
        else:
            logger.warning("语音识别失败")
            return jsonify({'success': False, 'error': '语音识别失败，请重试'})
            
    except Exception as e:
        logger.error(f"语音识别处理失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
@rate_limiter.rate_limit('api_login')
def login():
    """登录API端点"""
    try:
        data = request.get_json(force=True)
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': '口令不能为空'}), 400
        
        # 输入验证：检测SQL注入和XSS攻击
        is_sql_safe, sql_error = input_validator.validate_sql_injection(password)
        if not is_sql_safe:
            return jsonify({'error': sql_error}), 400
        
        is_xss_safe, xss_error = input_validator.validate_xss_attack(password)
        if not is_xss_safe:
            return jsonify({'error': xss_error}), 400
        
        # 清理输入数据
        password = input_validator.sanitize_input(password)
        
        # 验证或注册用户
        from modules.user_auth import user_auth
        username = user_auth.authenticate_user(password)
        
        if not username:
            # 注册新用户
            if user_auth.register_user(password):
                username = user_auth.get_user_by_password(password)
                logger.info(f"新用户注册成功: {username}")
                # 创建会话ID
                session_id = session_manager.create_session(username)
                return jsonify({
                    'success': True,
                    'message': '注册成功',
                    'username': username,
                    'session_id': session_id
                })
            else:
                return jsonify({'error': '注册失败，口令可能已被使用'}), 400
        else:
            logger.info(f"用户登录成功: {username}")
            # 创建或获取会话ID
            session_id = session_manager.create_session(username)
            return jsonify({
                'success': True,
                'message': '登录成功',
                'username': username,
                'session_id': session_id
            })
            
    except Exception as e:
        logger.error(f"登录处理失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat-history', methods=['GET'])
def get_chat_history():
    """获取聊天记录API端点"""
    try:
        session_id = request.args.get('session_id')
        role = request.args.get('role', 'ying')
        
        if not session_id:
            return jsonify({"error": "会话ID不能为空"}), 400
        
        # 获取用户信息
        username = session_manager.get_username_from_session(session_id)
        if not username:
            return jsonify({"error": "无效的会话ID"}), 401
        
        # 创建记忆管理器
        memory_manager = MemoryManager(username=username, role=role)
        
        # 加载聊天记录
        chat_history = memory_manager.load_chat_history(role)
        
        return jsonify({
            "success": True,
            "chat_history": chat_history
        })
        
    except Exception as e:
        logger.error(f"获取聊天记录失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat-history', methods=['POST'])
def save_chat_history():
    """保存聊天记录API端点"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        role = data.get('role', 'ying')
        content = data.get('content')
        
        if not session_id:
            return jsonify({"error": "会话ID不能为空"}), 400
        if not content:
            return jsonify({"error": "聊天内容不能为空"}), 400
        
        # 获取用户信息
        username = session_manager.get_username_from_session(session_id)
        if not username:
            return jsonify({"error": "无效的会话ID"}), 401
        
        # 创建记忆管理器
        memory_manager = MemoryManager(username=username, role=role)
        
        # 保存聊天记录
        success = memory_manager.save_chat_history(role, content)
        
        return jsonify({
            "success": success
        })
        
    except Exception as e:
        logger.error(f"保存聊天记录失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@rate_limiter.rate_limit('api_chat')
def chat():
    """聊天API端点"""
    try:
        logger.info("收到/api/chat请求")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"请求头: {dict(request.headers)}")
        
        # 处理编码问题
        try:
            data = request.get_json(force=True)
            logger.info(f"请求数据: {data}")
        except Exception as e:
            logger.error(f"解析JSON失败: {e}")
            logger.error(f"请求体: {request.get_data(as_text=True)}")
            return jsonify({'error': '无效的JSON格式'}), 400
        
        message = data.get('message', '')
        session_id = data.get('session_id', None)
        password = data.get('password', None)
        enable_audio = data.get('enable_audio', False)
        stream = data.get('stream', False)
        role = data.get('role', 'ying')  # 默认角色为荧
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 确保消息是字符串类型
        message = str(message)
        
        # 输入验证：检测SQL注入和XSS攻击
        is_sql_safe, sql_error = input_validator.validate_sql_injection(message)
        if not is_sql_safe:
            return jsonify({'error': sql_error}), 400
        
        is_xss_safe, xss_error = input_validator.validate_xss_attack(message)
        if not is_xss_safe:
            return jsonify({'error': xss_error}), 400
        
        # 清理输入数据
        message = input_validator.sanitize_input(message)
        
        # 确保会话存在（支持用户认证和角色切换）
        session_id, username = session_manager.ensure_session(session_id, password, role)
        session_data = session_manager.get_session(session_id)
        
        if not session_data:
            return jsonify({'error': '会话不存在'}), 400
        
        llm_instance, _, memory_manager, _ = session_data
        
        logger.info(f"收到消息: {message}")
        logger.info(f"消息长度: {len(message)}")
        logger.info(f"消息类型: {type(message)}")
        logger.info(f"消息编码: {message.encode('utf-8')}")
        logger.info(f"会话ID: {session_id}, 用户: {username}")
        logger.info(f"流式输出: {stream}")
        
        # 提示词预处理 - 防止提示词失效和注入攻击
        processed_message, is_malicious = prompt_hook.preprocess_prompt(message)
        if is_malicious:
            return jsonify({
                'error': processed_message,
                'session_id': session_id
            }), 400
        message = processed_message
        
        # 将用户消息添加到对话历史，以便指代解析
        llm_instance.add_message("user", message)
        
        # 根据角色创建LangChainIntegration实例
        role_langchain = LangChainIntegration(role=role)
        
        # 使用LangChain处理查询（需要修改langchain以支持传入LLM实例）
        logger.info(f"开始调用langchain.run_agent，角色: {role}")
        response = role_langchain.run_agent(message, llm_instance)
        logger.info(f"langchain.run_agent返回: {response}")
        
        if not response:
            # 回退到普通LLM
            response = llm_instance.generate_response(message)
        
        if not response:
            response = "我现在不想对话，一会再来吧"
        
        logger.info(f"生成回复: {response}")
        
        # 将AI回复添加到对话历史
        llm_instance.add_message("assistant", response)
        
        # 更新记忆
        logger.info("更新记忆")
        memory_manager.process_dialogue(message, response)
        
        # 过滤回复内容，清理特殊符号、表情符号和机械化回复
        def filter_response(text):
            if not text:
                return text
                
            # 移除表情符号（使用更可靠的方法）
            import emoji
            text = emoji.replace_emoji(text, replace='')
            
            # 移除特殊符号（保留常用标点符号，包括中文冒号）
            special_chars = r'[`~!@#$%^&*()_\-+=<>?{}|\\/;"\[·！@#￥%……&*（）——=+{}|‘“”《》【】]'
            text = re.sub(f'[{re.escape(special_chars)}]', '', text)
            
            # 移除重复的标点符号
            text = re.sub(r'([，。！？；:])\1+', r'\1', text)
            
            # 先移除多余的空格
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 检测两句话之间只有空格的情况，添加句号
            # 模式：中文字符 + 空格 + 中文字符
            text = re.sub(r'([\u4e00-\u9fa5]+)\s+([\u4e00-\u9fa5]+)', r'\1。\2', text)
            
            # 清理中文标点符号后面的空格（删除所有标点符号后的空格）
            text = re.sub(r'([，。！？；：])\s+', r'\1', text)
            
            # 清理中文标点符号前面的空格
            text = re.sub(r'\s+([，。！？；：])', r'\1', text)
            
            # 检查并替换机械化回复
            robotic_patterns = [
                ('根据提供的信息', '根据我所知道的'),
                ('在《原神》中', '在提瓦特大陆'),
                ('旅行者「荧」', '我'),
                ('我是《原神》中的', '我是'),
                ('来自《原神》', ''),
                ('作为《原神》角色', '')
            ]
            
            for pattern, replacement in robotic_patterns:
                text = text.replace(pattern, replacement)
                
            # 如果文本为空，返回默认回复
            if not text or len(text.strip()) == 0:
                text = "抱歉，我不太理解你的意思，可以换个方式问我吗？"
                
            return text
        
        response = filter_response(response)
        logger.info(f"过滤后回复: {response}")
        
        # 总是生成音频（用于重播功能）
        audio_url = None
        # 生成音频文件
        audio_filename = f"response_{uuid.uuid4().hex}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        
        logger.info(f"开始生成音频文件: {audio_filename}")
        logger.info(f"音频文件路径: {audio_path}")
        logger.info(f"回复内容长度: {len(response)}")
        
        # 使用TTS保存音频文件（异步版本）
        try:
            logger.info("开始调用tts.save_to_file_async...")
            # 根据角色创建TextToSpeech实例
            role_tts = TextToSpeech(role=role)
            success = role_tts.save_to_file(response, audio_path)
            logger.info(f"TTS调用返回结果: {success}")
            
            if success:
                audio_url = f"/audio/{audio_filename}"
                logger.info(f"音频文件生成成功: {audio_filename}, URL: {audio_url}")
            else:
                logger.error("音频文件生成失败: TTS返回False")
        except Exception as e:
            logger.error(f"音频文件生成异常: {e}")
            import traceback
            logger.error(f"异常详情: {traceback.format_exc()}")
        
        if stream:
            # 流式输出
            def generate_stream():
                # 先发送初始数据（不含文本内容）
                yield f'data: {json.dumps({
                    "type": "init",
                    "session_id": session_id,
                    "username": username,
                    "audio_url": audio_url
                })}\n\n'
                
                # 逐字发送响应内容
                for char in response:
                    yield f'data: {json.dumps({
                        "type": "text",
                        "content": char
                    })}\n\n'
                    time.sleep(0.02)  # 控制发送速度
                
                # 发送结束标志
                yield f'data: {json.dumps({
                    "type": "finish"
                })}\n\n'
            
            return Response(generate_stream(), mimetype='text/event-stream')
        else:
            # 非流式输出
            return jsonify({
                'response': response,
                'audio_url': audio_url,
                'session_id': session_id,
                'username': username
            })
        
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/synthesize_audio', methods=['POST'])
@rate_limiter.rate_limit('api_audio')
def synthesize_audio():
    """实时音频合成API"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        password = data.get('password', '')
        role = data.get('role', 'ying')  # 默认角色为荧
        
        # 验证密码
        from modules.user_auth import user_auth
        username = user_auth.authenticate_user(password)
        if not password or not username:
            return jsonify({'success': False, 'error': '密码验证失败'}), 401
        
        if not text:
            return jsonify({'success': False, 'error': '文本内容不能为空'}), 400
        
        # 生成音频文件
        audio_filename = f"synthesize_{uuid.uuid4().hex}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        
        # 根据角色创建TextToSpeech实例
        role_tts = TextToSpeech(role=role)
        
        # 使用TTS保存音频文件
        success = role_tts.save_to_file(text, audio_path)
        
        if success:
            audio_url = f"/audio/{audio_filename}"
            logger.info(f"实时音频合成成功: {audio_filename}")
            return jsonify({
                'success': True,
                'audio_url': audio_url
            })
        else:
            logger.warning("实时音频合成失败")
            return jsonify({
                'success': False,
                'error': '音频合成失败'
            })
            
    except Exception as e:
        logger.error(f"实时音频合成失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health')
def health():
    """健康检查端点"""
    return jsonify({'status': 'ok', 'message': '服务运行正常'})

if __name__ == '__main__':
    logger.info("启动Web服务器...")
    
    # 根据配置决定是否启用HTTPS
    if config.ENABLE_HTTPS:
        # 检查SSL证书文件是否存在
        if os.path.exists(config.SSL_CERT_FILE) and os.path.exists(config.SSL_KEY_FILE):
            logger.info(f"启用HTTPS，端口: {config.HTTPS_PORT}")
            app.run(
                host='0.0.0.0', 
                port=config.HTTPS_PORT, 
                ssl_context=(config.SSL_CERT_FILE, config.SSL_KEY_FILE),
                debug=False  # HTTPS模式下禁用debug
            )
        else:
            logger.error("SSL证书文件不存在，回退到HTTP模式")
            logger.info(f"启动HTTP服务器，端口: {config.PORT}")
            app.run(host='0.0.0.0', port=config.PORT, debug=True)
    else:
        # HTTP模式
        logger.info(f"启动HTTP服务器，端口: {config.PORT}")
        app.run(host='0.0.0.0', port=config.PORT, debug=True)
