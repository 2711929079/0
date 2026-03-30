@echo off
echo ================================================
echo 数字人"荧"远程访问启动脚本
echo ================================================
echo.
echo 请先下载 cloudflared.exe 并放在当前目录
echo 下载地址: https://github.com/cloudflare/cloudflareflared/releases/latest/download/cloudflared-windows-amd64.exe
echo.
pause

echo.
echo 正在启动Web服务器...
start "" python web_server.py

echo.
echo 等待服务器启动...
timeout /t 10 /nobreak >nul

echo.
echo 正在启动Cloudflare Tunnel...
echo 请在弹出的新窗口中复制生成的URL
echo.
start "" cloudflared.exe tunnel --url http://localhost:5000

echo.
echo 启动完成！
echo 请在新窗口中获取远程访问链接
echo 按任意键退出...
pause >nul