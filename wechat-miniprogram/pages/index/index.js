Page({
  data: {
    messages: [],
    inputValue: '',
    scrollIntoView: '',
    currentRole: 'ying', // 当前角色：ying 或 paimon
    audioContext: null
  },
  
  onLoad: function () {
    console.log('页面加载')
    this.setData({
      audioContext: wx.createInnerAudioContext()
    })
    this.loadChatHistory()
  },
  
  // 加载聊天记录
  loadChatHistory: function() {
    wx.request({
      url: 'https://tutu12138.top/api/chat-messages',
      method: 'GET',
      data: {
        role: this.data.currentRole,
        limit: 50,
        offset: 0
      },
      success: (res) => {
        console.log('加载聊天记录成功:', res.data)
        if (res.data && res.data.messages) {
          const messages = res.data.messages.map(msg => ({
            id: msg.id || Date.now(),
            role: msg.role === 'user' ? 'user' : msg.role,
            content: msg.content,
            audio_url: msg.audio_url
          }))
          this.setData({
            messages: messages
          })
          this.scrollToBottom()
        }
      },
      fail: (err) => {
        console.error('加载聊天记录失败:', err)
      }
    })
  },
  
  // 切换角色
  switchRole: function(e) {
    const newRole = e.currentTarget.dataset.role
    this.setData({
      currentRole: newRole
    })
    this.loadChatHistory()
  },
  
  // 输入框变化
  onInputChange: function(e) {
    this.setData({
      inputValue: e.detail.value
    })
  },
  
  // 发送消息（使用流式API）
  sendMessage: function() {
    const message = this.data.inputValue.trim()
    if (!message) return
    
    // 添加用户消息到界面
    const newMessageId = Date.now()
    const userMessage = {
      id: newMessageId,
      role: 'user',
      content: message
    }
    
    // 添加AI消息占位符
    const aiMessageId = Date.now() + 1
    const aiMessage = {
      id: aiMessageId,
      role: this.data.currentRole,
      content: '',
      audio_url: null
    }
    
    this.setData({
      messages: [...this.data.messages, userMessage, aiMessage],
      inputValue: ''
    })
    
    this.scrollToBottom()
    
    // 调用流式API发送消息
    wx.request({
      url: 'https://tutu12138.top/api/stream-chat',
      method: 'POST',
      data: {
        message: message,
        role: this.data.currentRole
      },
      responseType: 'text',
      success: (res) => {
        console.log('流式响应:', res.data)
        // 解析流式响应
        const lines = res.data.split('\n')
        let fullContent = ''
        let audioUrl = null
        
        lines.forEach(line => {
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.substring(5).trim())
              if (data.type === 'init') {
                audioUrl = data.audio_url
              } else if (data.type === 'content') {
                fullContent += data.content
              }
            } catch (e) {
              console.error('解析流式数据失败:', e)
            }
          }
        })
        
        if (fullContent) {
          const updatedMessages = this.data.messages.map(msg => {
            if (msg.id === aiMessageId) {
              return {
                ...msg,
                content: fullContent,
                audio_url: audioUrl
              }
            }
            return msg
          })
          
          this.setData({
            messages: updatedMessages
          })
          this.scrollToBottom()
        }
      },
      fail: (err) => {
        console.error('发送消息失败:', err)
        // 更新错误消息
        const updatedMessages = this.data.messages.map(msg => {
          if (msg.id === aiMessageId) {
            return {
              ...msg,
              content: '发送失败，请重试'
            }
          }
          return msg
        })
        
        this.setData({
          messages: updatedMessages
        })
        this.scrollToBottom()
      }
    })
  },
  
  // 播放语音
  playAudio: function(e) {
    const audioUrl = e.currentTarget.dataset.url
    if (!audioUrl) return
    
    const audioContext = this.data.audioContext
    audioContext.src = 'https://tutu12138.top' + audioUrl
    audioContext.play()
  },
  
  // 滚动到底部
  scrollToBottom: function() {
    setTimeout(() => {
      this.setData({
        scrollIntoView: 'msg-' + Date.now()
      })
    }, 100)
  }
})