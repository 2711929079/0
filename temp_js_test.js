// 全局变量
var sessionId = null;
var currentPassword = null;
var mediaRecorder = null;
var audioChunks = [];
var isListening = false;

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

function addMessage(message, isUser) {
    var chatContainer = document.getElementById('chatContainer');
    var messageDiv = document.createElement('div');
    messageDiv.className = isUser ? 'message user-message' : 'message ai-message';
    
    // 创建内容包装器
    var contentWrapper = document.createElement('div');
    contentWrapper.className = 'message-content-wrapper';
    
    var authorDiv = document.createElement('div');
    authorDiv.className = 'message-author';
    authorDiv.textContent = isUser ? '您' : '荧';
    
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
        avatarImg.src = '/static/ying.png';
        avatarImg.alt = '荧';
        avatarImg.className = 'avatar-small';
        
        avatarDiv.appendChild(avatarImg);
        messageDiv.appendChild(avatarDiv);
    }
    
    messageDiv.appendChild(contentWrapper);
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
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
    
    addMessage(message, true);
    userInput.value = '';
    
    var loadingDiv = document.createElement('div');
    loadingDiv.className = 'message ai-message';
    loadingDiv.innerHTML = '<div class="message-author">荧</div><div class="message-content loading">正在思考...</div>';
    chatContainer.appendChild(loadingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    var requestData = { 
        message: message,
        enable_audio: voiceToggle.checked,
        stream: streamToggle.checked,
        password: currentPassword
    };
    if (sessionId) {
        requestData.session_id = sessionId;
    }
    
    if (streamToggle.checked) {
        // 流式输出
        // 先发送POST请求获取会话ID和初始数据
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(function(response) {
            chatContainer.removeChild(loadingDiv);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // 检查响应类型
            var contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('text/event-stream')) {
                // 流式响应
                var messageDiv = document.createElement('div');
                messageDiv.className = 'message ai-message';
                messageDiv.innerHTML = '<div class="message-author">荧</div><div class="message-content"></div>';
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                
                var contentDiv = messageDiv.querySelector('.message-content');
                var audioUrl = null;
                
                var reader = response.body.getReader();
                var decoder = new TextDecoder();
                
                function processChunk() {
                    reader.read().then(function(result) {
                        if (result.done) {
                            console.log('Stream completed');
                            return;
                        }
                        
                        var chunk = decoder.decode(result.value, { stream: true });
                        var lines = chunk.split('
');
                        
                        lines.forEach(function(line) {
                            if (line.startsWith('data: ')) {
                                try {
                                    var dataStr = line.substring(6);
                                    var data = JSON.parse(dataStr);
                                    
                                    if (data.type === 'init') {
                                        if (data.session_id) {
                                            sessionId = data.session_id;
                                            localStorage.setItem('sessionId', sessionId);
                                        }
                                        audioUrl = data.audio_url;
                                    } else if (data.type === 'text') {
                                        contentDiv.textContent += data.content;
                                        chatContainer.scrollTop = chatContainer.scrollHeight;
                                    } else if (data.type === 'finish') {
                                        console.log('Stream finished');
                                        if (audioUrl) {
                                            var fullAudioUrl = window.location.origin + audioUrl;
                                            var audio = new Audio(fullAudioUrl);
                                            
                                            var avatarDiv = messageDiv.querySelector('.message-avatar');
                                            if (avatarDiv) {
                                                var playButton = document.createElement('button');
                                                playButton.className = 'play-audio-btn';
                                                playButton.innerHTML = '🔊';
                                                playButton.style.marginTop = '5px';
                                                playButton.style.padding = '4px';
                                                playButton.style.border = 'none';
                                                playButton.style.borderRadius = '50%';
                                                playButton.style.backgroundColor = '#f0f0f0';
                                                playButton.style.cursor = 'pointer';
                                                playButton.style.fontSize = '14px';
                                                playButton.style.width = '30px';
                                                playButton.style.height = '30px';
                                                playButton.style.display = 'flex';
                                                playButton.style.alignItems = 'center';
                                                playButton.style.justifyContent = 'center';
                                                playButton.style.opacity = '0.7';
                                                playButton.style.transition = 'opacity 0.3s';
                                                
                                                playButton.addEventListener('mouseenter', function() {
                                                    playButton.style.opacity = '1';
                                                });
                                                
                                                playButton.addEventListener('mouseleave', function() {
                                                    playButton.style.opacity = '0.7';
                                                });
                                                
                                                playButton.addEventListener('click', function() {
                                                    audio.play().then(function() {
                                                        playButton.innerHTML = '⏸️';
                                                        audio.addEventListener('ended', function() {
                                                            playButton.innerHTML = '🔊';
                                                        });
                                                        audio.addEventListener('pause', function() {
                                                            playButton.innerHTML = '🔊';
                                                        });
                                                    }).catch(function(err) {
                                                        console.error('音频播放失败:', err);
                                                        playButton.innerHTML = '❌';
                                                        window.open(fullAudioUrl, '_blank');
                                                    });
                                                });
                                                
                                                avatarDiv.appendChild(playButton);
                                                audio.play().catch(function(err) {
                                                    console.error('自动播放失败:', err);
                                                });
                                            }
                                        }
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
                        playButton.innerHTML = '🔊';
                        playButton.style.marginTop = '5px';
                        playButton.style.padding = '4px';
                        playButton.style.border = 'none';
                        playButton.style.borderRadius = '50%';
                        playButton.style.backgroundColor = '#f0f0f0';
                        playButton.style.cursor = 'pointer';
                        playButton.style.fontSize = '14px';
                        playButton.style.width = '30px';
                        playButton.style.height = '30px';
                        playButton.style.display = 'flex';
                        playButton.style.alignItems = 'center';
                        playButton.style.justifyContent = 'center';
                        playButton.style.opacity = '0.7';
                        playButton.style.transition = 'opacity 0.3s';
                        
                        playButton.addEventListener('mouseenter', function() {
                            playButton.style.opacity = '1';
                        });
                        
                        playButton.addEventListener('mouseleave', function() {
                            playButton.style.opacity = '0.7';
                        });
                        
                        playButton.addEventListener('click', function() {
                            audio.play().then(function() {
                                playButton.innerHTML = '⏸️';
                                audio.addEventListener('ended', function() {
                                    playButton.innerHTML = '🔊';
                                });
                                audio.addEventListener('pause', function() {
                                    playButton.innerHTML = '🔊';
                                });
                            }).catch(function(err) {
                                console.error('音频播放失败:', err);
                                playButton.innerHTML = '❌';
                                window.open(audioUrl, '_blank');
                            });
                        });
                        
                        avatarDiv.appendChild(playButton);
                        audio.play().catch(function(err) {
                            console.error('自动播放失败:', err);
                        });
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
            
            if (data.audio_url) {
                var audioUrl = window.location.origin + data.audio_url;
                var audio = new Audio(audioUrl);
                
                var messageDiv = chatContainer.lastElementChild;
                var avatarDiv = messageDiv.querySelector('.message-avatar');
                
                if (avatarDiv) {
                    var playButton = document.createElement('button');
                    playButton.className = 'play-audio-btn';
                    playButton.innerHTML = '🔊';
                    playButton.style.marginTop = '5px';
                    playButton.style.padding = '4px';
                    playButton.style.border = 'none';
                    playButton.style.borderRadius = '50%';
                    playButton.style.backgroundColor = '#f0f0f0';
                    playButton.style.cursor = 'pointer';
                    playButton.style.fontSize = '14px';
                    playButton.style.width = '30px';
                    playButton.style.height = '30px';
                    playButton.style.display = 'flex';
                    playButton.style.alignItems = 'center';
                    playButton.style.justifyContent = 'center';
                    playButton.style.opacity = '0.7';
                    playButton.style.transition = 'opacity 0.3s';
                    
                    playButton.addEventListener('mouseenter', function() {
                        playButton.style.opacity = '1';
                    });
                    
                    playButton.addEventListener('mouseleave', function() {
                        playButton.style.opacity = '0.7';
                    });
                    
                    playButton.addEventListener('click', function() {
                        audio.play().then(function() {
                            playButton.innerHTML = '⏸️';
                            audio.addEventListener('ended', function() {
                                playButton.innerHTML = '🔊';
                            });
                            audio.addEventListener('pause', function() {
                                playButton.innerHTML = '🔊';
                            });
                        }).catch(function(err) {
                            console.error('音频播放失败:', err);
                            playButton.innerHTML = '❌';
                            window.open(audioUrl, '_blank');
                        });
                    });
                    
                    avatarDiv.appendChild(playButton);
                    audio.play().catch(function(err) {
                        console.error('自动播放失败:', err);
                    });
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

function initVoiceRecognition() {
    var voiceInputBtn = document.getElementById('voiceInputBtn');
    
    // 检查浏览器支持
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn('浏览器不支持媒体设备API');
        voiceInputBtn.disabled = true;
        voiceInputBtn.style.opacity = '0.5';
        addMessage('您的浏览器不支持语音输入功能', false);
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

// 开始录音
function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
    .then(function(stream) {
        var voiceInputBtn = document.getElementById('voiceInputBtn');
        
        // 获取浏览器支持的音频格式
        var mimeType = getSupportedAudioFormat();
        mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });
        
        audioChunks = [];
        
        mediaRecorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = function() {
            isListening = false;
            voiceInputBtn.classList.remove('active');
            voiceInputBtn.innerHTML = '<i class="fas fa-phone-alt"></i>';
            
            var audioBlob = new Blob(audioChunks, { type: mimeType });
            sendAudioForRecognition(audioBlob, mimeType);
            
            // 停止所有音频轨道
            stream.getTracks().forEach(function(track) {
                track.stop();
            });
        };
        
        mediaRecorder.start();
        isListening = true;
        voiceInputBtn.classList.add('active');
        voiceInputBtn.innerHTML = '<i class="fas fa-phone-slash"></i>';
        addMessage('正在录音，请说话...', false);
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

// 发送音频到服务器进行识别
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
    
    // 登录输入框回车事件
    if (passwordInput) {
        passwordInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleLoginClick();
            }
        });
    }
    
    // 初始化语音识别
    initVoiceRecognition();
    
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
