// 检查登录按钮可用性的JavaScript脚本
console.log('=== 登录按钮可用性检查 ===');

// 检查DOM是否完全加载
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM已加载');
    
    // 检查登录按钮
    const loginButton = document.getElementById('loginButton');
    console.log('登录按钮:', loginButton);
    
    if (loginButton) {
        console.log('登录按钮存在');
        
        // 检查按钮的CSS属性
        const computedStyle = window.getComputedStyle(loginButton);
        console.log('按钮样式:', {
            display: computedStyle.display,
            visibility: computedStyle.visibility,
            opacity: computedStyle.opacity,
            pointerEvents: computedStyle.pointerEvents,
            cursor: computedStyle.cursor,
            zIndex: computedStyle.zIndex,
            position: computedStyle.position
        });
        
        // 检查是否有元素覆盖
        const rect = loginButton.getBoundingClientRect();
        console.log('按钮位置:', {
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height
        });
        
        // 检查是否有事件监听器
        console.log('按钮事件监听器:', getEventListeners(loginButton));
        
        // 手动触发点击事件
        loginButton.addEventListener('click', function() {
            console.log('登录按钮被点击！');
        });
        
        console.log('手动点击测试：');
        loginButton.click();
    } else {
        console.error('登录按钮不存在');
    }
});
