import tkinter as tk
from tkinter import ttk, PhotoImage
from typing import Optional
import logging
import os
import sys
from config import config

# 添加PMX-VMD-Scripting-Tools到Python路径
sys.path.append(r"C:\Users\27119\PycharmProjects\pythonProject3\PMX-VMD-Scripting-Tools-master")

try:
    from mmd_scripting.core.nuthouse01_pmx_parser import read_pmx
    PMX_SUPPORT = True
except ImportError as e:
    logging.warning(f"PMX解析库导入失败: {e}")
    PMX_SUPPORT = False

class AvatarRenderer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.window = None
        self.canvas = None
        self.text_area = None
        self.is_running = False
        
    def create_window(self):
        try:
            self.window = tk.Tk()
            self.window.title(f"{config.AVATAR_NAME} - AI数字人")
            self.window.geometry("800x600")
            self.window.configure(bg=config.AVATAR_BACKGROUND_COLOR)
            
            main_frame = ttk.Frame(self.window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            avatar_frame = ttk.Frame(main_frame)
            avatar_frame.pack(fill=tk.X, pady=(0, 20))
            
            self.canvas = tk.Canvas(avatar_frame, width=200, height=200, bg="white", relief="solid", bd=1)
            self.canvas.pack(pady=20)
            self._draw_avatar()
            
            self.text_area = tk.Text(main_frame, height=10, wrap=tk.WORD, font=("微软雅黑", 12))
            self.text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
            self.text_area.config(state=tk.DISABLED)
            
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X)
            
            start_btn = ttk.Button(button_frame, text="开始对话", command=self._start_conversation)
            start_btn.pack(side=tk.LEFT, padx=5)
            
            stop_btn = ttk.Button(button_frame, text="停止对话", command=self._stop_conversation)
            stop_btn.pack(side=tk.LEFT, padx=5)
            
            clear_btn = ttk.Button(button_frame, text="清空对话", command=self._clear_conversation)
            clear_btn.pack(side=tk.LEFT, padx=5)
            
            self.is_running = True
            self.window.update()
            self.window.update_idletasks()
            self.window.lift()
            self.window.attributes('-topmost', True)
            self.window.attributes('-topmost', False)
            self.logger.info("数字人渲染窗口创建成功")
            
        except Exception as e:
            self.logger.error(f"创建窗口失败: {e}")
    
    def _draw_avatar(self):
        self.canvas.delete("all")
        
        # 优先使用配置文件中的纹理路径（2D图片）
        texture_path = config.AVATAR_TEXTURE_PATH
        
        if os.path.exists(texture_path):
            try:
                # 加载纹理图片作为数字人形象
                self.avatar_image = PhotoImage(file=texture_path)
                
                # 调整图片大小以适应画布（200x200）
                width = self.avatar_image.width()
                height = self.avatar_image.height()
                
                # 计算缩放比例，保持图片比例
                if width > height:
                    scale_factor = 200 / width
                else:
                    scale_factor = 200 / height
                
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                # 缩放图片
                self.avatar_image = self.avatar_image.subsample(int(1/scale_factor), int(1/scale_factor))
                
                # 在画布上显示图片
                self.canvas.create_image(100, 100, image=self.avatar_image)
                
                self.logger.info(f"成功加载数字人形象: {texture_path}")
                self.logger.info(f"图片原始大小: {width}x{height}, 缩放后: {new_width}x{new_height}")
                
            except Exception as e:
                self.logger.error(f"加载数字人形象失败: {e}")
                # 如果加载失败，绘制简单的卡通形象作为备用
                self._draw_fallback_avatar()
        else:
            self.logger.warning(f"纹理文件不存在: {texture_path}")
            # 如果配置文件中的纹理不存在，尝试使用PMX模型
            if PMX_SUPPORT:
                pmx_path = r"C:\Users\27119\Downloads\【女主角_荧】_by_原神_39fd8673fd145a6c65858227788cb173\荧.pmx"
                
                if os.path.exists(pmx_path):
                    try:
                        # 解析PMX模型
                        pmx_data = read_pmx(pmx_path)
                        self.logger.info(f"成功解析PMX模型: {pmx_data.header.name_jp}")
                        
                        # 获取模型目录路径
                        model_dir = os.path.dirname(pmx_path)
                        
                        # 加载主要纹理图片（按照材质顺序）
                        textures_to_load = []
                        
                        # 按照材质顺序加载纹理（皮肤、面部、头发、衣服等）
                        for material in pmx_data.materials:
                            if material.tex_path:
                                texture_full_path = os.path.join(model_dir, material.tex_path)
                                if os.path.exists(texture_full_path):
                                    textures_to_load.append(texture_full_path)
                        
                        # 显示完整的数字人形象
                        # 先创建背景
                        self.canvas.create_rectangle(0, 0, 200, 200, fill="white", tag="background")
                        
                        # 尝试显示所有找到的纹理
                        self.logger.info(f"找到的纹理数量: {len(textures_to_load)}")
                        
                        # 按顺序显示纹理
                        for i, tex_path in enumerate(textures_to_load[:3]):  # 最多显示3个纹理
                            try:
                                texture_name = os.path.basename(tex_path)
                                self.logger.info(f"加载纹理 {i+1}: {texture_name}")
                                
                                # 加载纹理
                                image = PhotoImage(file=tex_path)
                                # 使用固定的缩放比例
                                image = image.subsample(6, 6)
                                
                                # 显示纹理
                                self.canvas.create_image(100, 100, image=image, tag=f"texture_{i}")
                                self.logger.info(f"成功显示纹理 {texture_name}")
                                
                            except Exception as e:
                                self.logger.error(f"加载纹理 {tex_path} 失败: {e}")
                        
                        return
                        
                    except Exception as e:
                        self.logger.error(f"解析PMX模型失败: {e}")
            
            # 如果都失败了，绘制简单的卡通形象作为备用
            self._draw_fallback_avatar()
    
    def _draw_fallback_avatar(self):
        # 绘制完整的卡通形象
        # 先画头发（底层）
        self.canvas.create_oval(40, 40, 160, 140, fill="#FFD700", outline="#FFA500", width=2)
        
        # 再画头部
        self.canvas.create_oval(50, 50, 150, 150, fill="#FFE4E1", outline="#FFB6C1", width=2)
        
        # 眼睛
        self.canvas.create_oval(75, 80, 95, 100, fill="white", outline="black", width=1)
        self.canvas.create_oval(105, 80, 125, 100, fill="white", outline="black", width=1)
        self.canvas.create_oval(80, 85, 90, 95, fill="black")
        self.canvas.create_oval(110, 85, 120, 95, fill="black")
        
        # 眉毛
        self.canvas.create_line(70, 75, 100, 75, width=2, fill="black")
        self.canvas.create_line(100, 75, 130, 75, width=2, fill="black")
        
        # 嘴巴
        self.canvas.create_arc(80, 110, 120, 130, start=0, extent=180, style=tk.ARC, fill="pink", width=2)
        
        # 耳朵（在头部后面）
        self.canvas.create_oval(40, 80, 60, 100, fill="#FFE4E1", outline="#FFB6C1", width=1)
        self.canvas.create_oval(140, 80, 160, 100, fill="#FFE4E1", outline="#FFB6C1", width=1)
    
    def update_text(self, text: str, is_user: bool = False):
        if not self.text_area:
            return
            
        self.text_area.config(state=tk.NORMAL)
        
        if is_user:
            self.text_area.insert(tk.END, f"您: {text}\n\n", "user")
        else:
            self.text_area.insert(tk.END, f"{config.AVATAR_NAME}: {text}\n\n", "assistant")
        
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)
    
    def clear_assistant_text(self):
        """清空最后一行的助手文本（用于流式输出）"""
        if not self.text_area:
            return
            
        self.text_area.config(state=tk.NORMAL)
        
        # 获取文本内容
        content = self.text_area.get("1.0", tk.END)
        
        # 找到最后一个助手消息的位置
        lines = content.split('\n')
        last_assistant_line = None
        
        for i in range(len(lines)-1, -1, -1):
            if lines[i].startswith(f"{config.AVATAR_NAME}:"):
                last_assistant_line = i
                break
        
        if last_assistant_line is not None:
            # 计算要删除的范围
            start_line = last_assistant_line + 1
            # 删除从助手消息开始到末尾的内容
            self.text_area.delete(f"{start_line}.0", tk.END)
        
        self.text_area.config(state=tk.DISABLED)
    
    def append_text(self, text: str, is_user: bool = False):
        """追加文本（用于流式输出）"""
        if not self.text_area:
            return
            
        self.text_area.config(state=tk.NORMAL)
        
        if is_user:
            # 用户输入不使用流式输出
            self.text_area.insert(tk.END, text)
        else:
            # 助手回复使用流式输出
            self.text_area.insert(tk.END, text)
        
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)
    
    def _start_conversation(self):
        self.logger.info("开始对话")
    
    def _stop_conversation(self):
        self.logger.info("停止对话")
    
    def _clear_conversation(self):
        if self.text_area:
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete(1.0, tk.END)
            self.text_area.config(state=tk.DISABLED)
            self.logger.info("对话已清空")
    
    def run(self):
        if not self.window:
            self.create_window()
            
        if self.window:
            self.window.mainloop()
    
    def close(self):
        if self.window:
            self.window.destroy()
            self.is_running = False
            self.logger.info("数字人渲染窗口已关闭")