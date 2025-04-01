import os
import ctypes
import asyncio
import tkinter as tk
from tkinter import Text, messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Optional, Callable
from functools import partial
import threading
from queue import Queue

from src.core.image_processor import ImageProcessor, ProcessType, ProcessMode, ProcessResult

class MainWindow:
    def __init__(self, root: ttk.Window):
        self.root = root
        self.root.title("图片处理工具")
        
        # 初始化图片处理器
        self.image_processor = ImageProcessor()
        
        # 处理状态
        self.processing = False
        self.stop_requested = False
        
        # 创建消息队列和事件循环
        self.message_queue = Queue()
        self.loop = None
        self.thread = None
        
        # 设置DPI感知
        self._setup_dpi_awareness()
        
        # 创建UI组件
        self._create_ui()
        
        # 设置窗口图标
        self._setup_icon()
        
        # 检查环境
        self._check_environment()
        
        # 启动事件循环线程
        self._start_event_loop()
        
        # 设置定期检查消息队列
        self._setup_message_check()
        
    def _setup_dpi_awareness(self):
        """设置DPI感知"""
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except AttributeError:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except AttributeError:
                pass
                
        # 获取DPI缩放因子
        try:
            self.scaling_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
        except:
            self.scaling_factor = 1
            
        # 设置最小窗口大小
        self.min_width = int(450 * self.scaling_factor)
        self.min_height = int(450 * self.scaling_factor)
        self.root.minsize(self.min_width, self.min_height)
        
    def _create_ui(self):
        """创建UI组件"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(expand=True, fill="both")
        
        # 创建按钮区域
        self._create_buttons()
        
        # 创建信息显示区域
        self._create_info_display()
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self._on_window_configure)
        
    def _create_buttons(self):
        """创建按钮区域"""
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.pack(fill="x", pady=5)
        
        # 创建一个容器来居中按钮
        center_container = ttk.Frame(buttons_frame)
        center_container.pack(expand=True)
        
        # 缩略图按钮
        left_column = ttk.Frame(center_container)
        left_column.pack(side="left", padx=20)
        
        self.thumbnail_button = ttk.Button(
            left_column,
            text="生成缩略图",
            command=self._process_thumbnail,
            width=10,
            style="primary.TButton"
        )
        self.thumbnail_button.pack(pady=(0, 5))
        
        self.ffmpeg_status = ttk.Label(
            left_column,
            text="ffmpeg: 检查中...",
            style="Label.TLabel"
        )
        self.ffmpeg_status.pack()
        
        # avif/webp按钮
        right_column = ttk.Frame(center_container)
        right_column.pack(side="left", padx=20)
        
        self.avif_webp_button = ttk.Button(
            right_column,
            text="生成avif/webp",
            command=self._process_avif_webp,
            width=14,
            style="info.TButton"
        )
        self.avif_webp_button.pack(pady=(0, 5))
        
        self.optimizt_status = ttk.Label(
            right_column,
            text="optimizt: 检查中...",
            style="Label.TLabel"
        )
        self.optimizt_status.pack()
        
    def _create_info_display(self):
        """创建信息显示区域"""
        # 创建一个Frame来包含两列
        info_frame = ttk.Frame(self.main_frame)
        info_frame.pack(expand=True, fill="both", pady=(10, 0))
        
        # 创建左右两列
        left_frame = ttk.Frame(info_frame)
        left_frame.pack(side="left", expand=True, fill="both", padx=(0, 5))
        
        right_frame = ttk.Frame(info_frame)
        right_frame.pack(side="right", expand=True, fill="both", padx=(5, 0))
        
        # 创建左侧标签
        left_label = ttk.Label(
            left_frame,
            text="待处理队列",
            style="Label.TLabel"
        )
        left_label.pack(pady=(0, 5))
        
        # 创建右侧标签
        right_label = ttk.Label(
            right_frame,
            text="处理信息",
            style="Label.TLabel"
        )
        right_label.pack(pady=(0, 5))
        
        # 创建左侧Text组件和滚动条（待处理队列）
        self.queue_display = Text(
            left_frame,
            height=15,
            width=24,
            wrap="word",
            font=("Consolas", 9)
        )
        left_scrollbar = ttk.Scrollbar(
            left_frame,
            orient="vertical",
            command=self.queue_display.yview
        )
        self.queue_display.configure(yscrollcommand=left_scrollbar.set)
        
        # 创建右侧Text组件和滚动条（处理信息）
        self.info_display = Text(
            right_frame,
            height=15,
            width=24,
            wrap="word",
            font=("Consolas", 9)
        )
        right_scrollbar = ttk.Scrollbar(
            right_frame,
            orient="vertical",
            command=self.info_display.yview
        )
        self.info_display.configure(yscrollcommand=right_scrollbar.set)
        
        # 放置组件
        left_scrollbar.pack(side="right", fill="y")
        self.queue_display.pack(side="left", expand=True, fill="both")
        
        right_scrollbar.pack(side="right", fill="y")
        self.info_display.pack(side="left", expand=True, fill="both")
        
        # 禁用编辑
        self.queue_display.configure(state="disabled")
        self.info_display.configure(state="disabled")
        
    def _setup_icon(self):
        """设置窗口图标"""
        icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "2.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
            
    def _check_environment(self):
        """检查环境配置"""
        if self.image_processor._ffmpeg_path:
            self.ffmpeg_status.configure(
                text="ffmpeg: 已安装 ✓",
                foreground="green"
            )
        else:
            self.ffmpeg_status.configure(
                text="ffmpeg: 未安装 ✗",
                foreground="red"
            )
            
        if self.image_processor._optimizt_path:
            self.optimizt_status.configure(
                text="optimizt: 已安装 ✓",
                foreground="green"
            )
        else:
            self.optimizt_status.configure(
                text="optimizt: 未安装 ✗",
                foreground="red"
            )
            
    def _start_event_loop(self):
        """在新线程中启动事件循环"""
        def run_event_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.loop = loop
            loop.run_forever()
            
        self.thread = threading.Thread(target=run_event_loop, daemon=True)
        self.thread.start()
        
    def _setup_message_check(self):
        """设置定期检查消息队列"""
        def check_messages():
            while not self.message_queue.empty():
                callback = self.message_queue.get_nowait()
                callback()
            self.root.after(100, check_messages)
            
        self.root.after(100, check_messages)

    def run_async(self, coro):
        """在事件循环中运行协程"""
        if not self.loop or not self.loop.is_running():
            self._display_info("错误: 事件循环未运行")
            return
            
        async def wrapped():
            try:
                await coro
            except Exception as e:
                error_msg = str(e)  # 在异常处理时捕获错误信息
                self.message_queue.put(
                    lambda msg=error_msg: self._display_info(f"错误: {msg}")  # 使用默认参数传递错误信息
                )
                
        future = asyncio.run_coroutine_threadsafe(wrapped(), self.loop)
        
        def check_future(fut):
            try:
                exc = fut.exception()
                if exc:
                    error_msg = str(exc)
                    self.message_queue.put(
                        lambda msg=error_msg: self._display_info(f"错误: {msg}")
                    )
            except asyncio.CancelledError:
                self._display_info("操作已取消")
                
        future.add_done_callback(check_future)

    def _cleanup(self):
        """清理资源"""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def _process_thumbnail(self):
        """处理缩略图"""
        if not self.image_processor._ffmpeg_path:
            self._show_error("未检测到ffmpeg", "请先安装ffmpeg后再使用此功能。")
            return
            
        if self.processing:
            self.stop_requested = True
            self.thumbnail_button.configure(state="disabled")
            return
            
        # 选择文件或文件夹
        paths = self._select_files_or_folder("选择要处理的图片或文件夹", ProcessType.THUMBNAIL)
        if not paths:
            return
            
        self.processing = True
        self.stop_requested = False
        self.thumbnail_button.configure(text="停止", style="danger.TButton")
        
        # 启动处理
        self.run_async(self._process_paths(paths, ProcessType.THUMBNAIL))
            
    def _process_avif_webp(self):
        """处理avif/webp格式"""
        if not self.image_processor._optimizt_path:
            self._show_error("未检测到optimizt", "请先安装optimizt后再使用此功能。")
            return
            
        if self.processing:
            self.stop_requested = True
            self.avif_webp_button.configure(state="disabled")
            return
            
        # 选择文件或文件夹
        paths = self._select_files_or_folder("选择要处理的图片或文件夹", ProcessType.AVIF_WEBP)
        if not paths:
            return
            
        self.processing = True
        self.stop_requested = False
        self.avif_webp_button.configure(text="停止", style="danger.TButton")
        
        # 启动处理
        self.run_async(self._process_paths(paths, ProcessType.AVIF_WEBP))

    def _select_files_or_folder(self, title: str, process_type: ProcessType) -> list:
        """选择文件"""
        files = filedialog.askopenfilenames(
            parent=self.root,
            title=title,
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")],
        )
        
        # 过滤文件
        filtered_files = []
        for file in files:
            # 获取文件名（不含扩展名）和扩展名
            filename = os.path.splitext(os.path.basename(file))[0]
            ext = os.path.splitext(file)[1].lower()
            
            # 根据处理类型应用不同的排除规则
            if process_type == ProcessType.THUMBNAIL:
                # 缩略图处理的排除规则
                # 1. 跳过webp和avif格式
                if ext in ['.webp', '.avif']:
                    continue
                    
                # 2. 跳过index和banner文件（精确匹配）
                if filename in ['index', 'banner']:
                    continue
                    
                # 3. 跳过以_proc结尾的文件
                if filename.endswith('_proc'):
                    continue
            else:
                # avif/webp处理的排除规则
                # 只跳过webp和avif格式
                if ext in ['.webp', '.avif']:
                    continue
                
            filtered_files.append(file)
            
        # 更新待处理队列显示
        if filtered_files:
            self._update_queue_display(filtered_files)
            
        return filtered_files

    async def _process_paths(self, paths: list, process_type: ProcessType):
        """处理文件列表"""
        try:
            if not paths:
                return
                
            # 获取第一个文件的目录作为基准目录
            base_dir = os.path.dirname(paths[0])
            self._display_info(f"开始处理目录: {os.path.basename(base_dir)}")
            
            for path in paths:
                if self.stop_requested:
                    break
                    
                # 处理单个文件
                self._display_info(f"处理文件: {os.path.basename(path)}")
                if process_type == ProcessType.THUMBNAIL:
                    result = await self.image_processor.process_thumbnail(path)
                else:
                    result = await self.image_processor.process_avif_webp(path)
                self._display_result(result)
                    
            if not self.stop_requested:
                self._display_info("所有文件处理完成！")
            else:
                self._display_info("处理已终止！")
                
        except Exception as e:
            self._display_info(f"处理过程出错: {str(e)}")
        finally:
            self._reset_processing_state()

    def _display_info(self, message: str):
        """显示处理信息"""
        def update():
            self.info_display.configure(state="normal")
            self.info_display.insert("end", message + "\n")
            self.info_display.see("end")
            self.info_display.configure(state="disabled")
            
        if threading.current_thread() is threading.main_thread():
            update()
        else:
            self.message_queue.put(update)

    def _update_queue_display(self, files: list):
        """更新待处理队列显示"""
        def update():
            self.queue_display.configure(state="normal")
            self.queue_display.delete("1.0", "end")
            for file in files:
                self.queue_display.insert("end", os.path.basename(file) + "\n")
            self.queue_display.see("end")
            self.queue_display.configure(state="disabled")
            
        if threading.current_thread() is threading.main_thread():
            update()
        else:
            self.message_queue.put(update)

    def _display_result(self, result: ProcessResult):
        """显示处理结果"""
        def update():
            rel_path = os.path.basename(result.input_path)
            if result.success:
                self._display_info(f"处理完成: {rel_path}")
                if result.output_paths:
                    for output_path in result.output_paths:
                        self._display_info(f"  └─ 输出: {os.path.basename(output_path)}")
            else:
                self._display_info(f"处理失败: {rel_path} - {result.message}")
                
        if threading.current_thread() is threading.main_thread():
            update()
        else:
            self.message_queue.put(update)
        
    def _reset_processing_state(self):
        """重置处理状态"""
        self.processing = False
        self.stop_requested = False
        
        def update():
            self.thumbnail_button.configure(
                text="生成缩略图",
                style="primary.TButton",
                state="normal"
            )
            self.avif_webp_button.configure(
                text="生成avif/webp",
                style="info.TButton",
                state="normal"
            )
            
        self.message_queue.put(update)
        
    def _show_error(self, title: str, message: str):
        """显示错误消息"""
        self.message_queue.put(lambda: messagebox.showerror(title, message))
        
    def _on_window_configure(self, event):
        """处理窗口大小变化事件"""
        if event.widget == self.root:
            required_width = self._calculate_required_width()
            if event.width < required_width:
                new_width = max(required_width, self.min_width)
                self.root.geometry(f"{new_width}x{event.height}")
                
    def _calculate_required_width(self) -> int:
        """计算界面所需的最小宽度"""
        if hasattr(self, 'main_frame') and self.main_frame.winfo_ismapped():
            left_padding = int(45 * self.scaling_factor)
            first_button_width = 10
            second_button_width = 14
            char_width = int(8 * self.scaling_factor)
            button_padding = int((5 + 15 + 5) * self.scaling_factor)
            
            total_width = (
                left_padding +
                (first_button_width * char_width) +
                (second_button_width * char_width) +
                button_padding +
                int(40 * self.scaling_factor)
            )
            
            return total_width
            
        return self.min_width 