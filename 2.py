import os
import ctypes
import sys
from tkinter import Text, messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import subprocess
import json

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def set_dpi_awareness():
    """设置 DPI 感知"""
    try:
        # Windows 8.1 及以上版本
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except AttributeError:
        try:
            # Windows 8.0 及以下版本
            ctypes.windll.user32.SetProcessDPIAware()
        except AttributeError:
            pass

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("图片处理工具")
        
        # 获取 DPI 缩放因子
        try:
            self.scaling_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
        except:
            self.scaling_factor = 1
        
        # 初始化最小窗口大小（考虑 DPI 缩放）
        self.min_width = int(450 * self.scaling_factor)
        self.min_height = int(450 * self.scaling_factor)
        self.root.minsize(self.min_width, self.min_height)
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_configure)
        
        # 设置窗口图标
        self.icon_path = get_resource_path("2.ico")
        if os.path.exists(self.icon_path):
            self.root.iconbitmap(self.icon_path)
            self.root.tk.call('wm', 'iconbitmap', self.root._w, self.icon_path)

        # 设置窗口背景色
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("Label.TLabel", background="#f0f0f0", padding=5)
        self.root.configure(background="#f0f0f0")

        # 创建主Frame
        self.main_frame = ttk.Frame(self.root)
        
        # 创建主界面
        self.create_main_interface()
        
        # 创建信息显示区域
        self.create_info_display()
        
        # 显示主界面
        self.show_main_interface()

        # 添加处理状态标志
        self.thumbnail_processing = False
        self.avif_webp_processing = False
        self.stop_processing = False

    def create_main_interface(self):
        """创建主界面布局"""
        # 创建一个主容器，使用grid布局以便更好地控制居中
        main_container = ttk.Frame(self.main_frame)
        main_container.pack(expand=True)
        
        # 创建左右两个空白列来实现居中效果
        ttk.Frame(main_container, width=20).grid(row=0, column=0)  # 左侧空白
        
        # 创建一个内部容器来包含所有元素
        inner_container = ttk.Frame(main_container)
        inner_container.grid(row=0, column=1, padx=20)
        
        # 设置样式
        style = ttk.Style()
        style.configure("Mode.TRadiobutton", 
                       background="#f0f0f0",  # 匹配软件背景色
                       font=("微软雅黑", 9))
        style.configure("Mode.TLabelframe", 
                       background="#f0f0f0")  # 设置LabelFrame背景色
        style.configure("Mode.TLabelframe.Label", 
                       background="#f0f0f0")  # 设置LabelFrame标题背景色
        
        # 创建一个LabelFrame来包含模式选择
        mode_frame = ttk.LabelFrame(
            inner_container, 
            text="处理模式", 
            padding=(10, 5),
            style="Mode.TLabelframe"  # 应用新样式
        )
        mode_frame.pack(fill="x", pady=(0, 15))
        
        # 创建模式选择变量
        self.process_mode = ttk.StringVar(value="folder")  # 默认为文件夹模式
        
        # 创建单选按钮容器
        radio_container = ttk.Frame(mode_frame, style="Mode.TFrame")
        radio_container.pack(fill="x")
        
        # 创建单选按钮
        ttk.Radiobutton(
            radio_container,
            text="文件夹模式",
            value="folder",
            variable=self.process_mode,
            style="Mode.TRadiobutton"
        ).pack(side="left", padx=(25, 0))  # 左边距20
        
        ttk.Radiobutton(
            radio_container,
            text="单文件模式",
            value="single",
            variable=self.process_mode,
            style="Mode.TRadiobutton"
        ).pack(side="left", padx=(70, 0))  # 增加左边距到80
        
        # 创建按钮和状态容器
        buttons_frame = ttk.Frame(inner_container)
        buttons_frame.pack(fill="x", pady=5)
        
        # 第一列：缩略图相关
        left_column = ttk.Frame(buttons_frame)
        left_column.pack(side="left", padx=20)
        
        # 生成缩略图按钮
        self.thumbnail_button = ttk.Button(
            left_column, 
            text="生成缩略图", 
            command=self.toggle_thumbnail, 
            width=10, 
            style="primary.TButton"
        )
        self.thumbnail_button.pack(pady=(0, 5))
        
        # ffmpeg状态标签
        self.ffmpeg_status = ttk.Label(
            left_column,
            text="ffmpeg: 检查中...",
            style="Label.TLabel"
        )
        self.ffmpeg_status.pack()
        
        # 第二列：avif/webp相关
        right_column = ttk.Frame(buttons_frame)
        right_column.pack(side="left", padx=20)
        
        # 生成avif/webp按钮
        self.avif_webp_button = ttk.Button(
            right_column, 
            text="生成avif/webp", 
            command=self.toggle_avif_webp, 
            width=14,
            style="info.TButton"
        )
        self.avif_webp_button.pack(pady=(0, 5))
        
        # optimizt状态标签
        self.optimizt_status = ttk.Label(
            right_column,
            text="optimizt: 检查中...",
            style="Label.TLabel"
        )
        self.optimizt_status.pack()
        
        # 右侧空白列
        ttk.Frame(main_container, width=20).grid(row=0, column=2)
        
        # 配置grid列权重以保持居中
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=0)
        main_container.grid_columnconfigure(2, weight=1)
        
        # 启动状态检查
        self.check_environment()

    def show_main_interface(self):
        """显示主界面"""
        self.main_frame.pack(pady=35)
        self.info_display.pack(pady=(5, 5))

    def create_info_display(self):
        """创建信息显示区域"""
        self.info_display = Text(self.root, height=15, width=48)
        self.progress_line = None
        self.last_progress = None

    def toggle_thumbnail(self):
        """切换缩略图处理状态"""
        if self.thumbnail_processing:
            self.stop_processing = True
            self.thumbnail_button.configure(state="disabled")
        else:
            self.generate_thumbnail()

    def toggle_avif_webp(self):
        """切换avif/webp处理状态"""
        if self.avif_webp_processing:
            self.stop_processing = True
            self.avif_webp_button.configure(state="disabled")
        else:
            self.generate_avif_webp()

    def generate_thumbnail(self):
        """生成缩略图"""
        # 先检查 ffmpeg 是否已安装
        if not self.check_command("ffmpeg"):
            self.show_custom_messagebox(
                "showerror",
                "错误",
                "未检测到 ffmpeg，请先安装 ffmpeg 后再使用此功能。\n\n" +
                "可以访问 https://ffmpeg.org/download.html 下载安装。"
            )
            return
        
        # 创建一个顶层窗口作为对话框的父窗口
        dialog_parent = ttk.Toplevel(self.root)
        dialog_parent.withdraw()
        dialog_parent.transient(self.root)
        
        if self.process_mode.get() == "single":  # 单文件模式
            file_path = filedialog.askopenfilename(
                parent=dialog_parent,
                title="选择需要处理的图片",
                filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")]
            )
            if file_path:
                self.thumbnail_processing = True
                self.stop_processing = False
                self.thumbnail_button.configure(text="停止", style="danger.TButton")
                threading.Thread(target=self.process_single_thumbnail, args=(file_path,), daemon=True).start()
        else:  # 文件夹模式
            folder_path = filedialog.askdirectory(
                parent=dialog_parent,
                title="选择需要处理的文件夹"
            )
            if folder_path:
                self.thumbnail_processing = True
                self.stop_processing = False
                self.thumbnail_button.configure(text="停止", style="danger.TButton")
                threading.Thread(target=self.process_thumbnails, args=(folder_path,), daemon=True).start()
        
        dialog_parent.destroy()

    def process_single_thumbnail(self, image_file):
        """处理单个图片（缩略图）"""
        try:
            self.display_info(f"开始处理文件: {os.path.basename(image_file)}")
            
            # 创建 startupinfo 对象来隐藏命令行窗口
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            if self.should_process_file(image_file):
                try:
                    # 构建输出文件路径
                    filename = os.path.splitext(os.path.basename(image_file))[0]
                    output_file = os.path.join(os.path.dirname(image_file), f"{filename}_proc.jpg")
                    
                    # 构建 ffmpeg 命令
                    cmd = [
                        "ffmpeg",
                        "-i", image_file,
                        "-vf", "scale=17:-1",
                        "-q:v", "2",
                        "-compression_level", "50",
                        output_file,
                        "-y"
                    ]
                    
                    # 执行 ffmpeg 命令
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        startupinfo=startupinfo
                    )
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        self.display_info(f"处理完成: {os.path.basename(image_file)} -> {os.path.basename(output_file)}")
                    else:
                        self.display_info(f"处理失败: {os.path.basename(image_file)}")
                
                except Exception as e:
                    self.display_info(f"处理出错: {os.path.basename(image_file)}\n错误信息: {str(e)}")
            else:
                self.display_info(f"跳过: {os.path.basename(image_file)} (已存在或不需要处理)")
            
        except Exception as e:
            self.display_info(f"处理过程出错: {str(e)}")
        finally:
            self.thumbnail_processing = False
            self.stop_processing = False
            self.root.after(0, lambda: self.thumbnail_button.configure(
                text="生成缩略图",
                style="primary.TButton",
                state="normal"
            ))

    def process_thumbnails(self, root_folder):
        """处理指定文件夹及其子文件夹中的所有图"""
        try:
            folder_name = os.path.basename(root_folder)
            self.display_info(f"开始处理文件夹: {folder_name}")
            self._process_thumbnails_folder(root_folder, root_folder)
            if not self.stop_processing:
                self.display_info("所有文件处理完成！")
            else:
                self.display_info("处理已终止！")
        except Exception as e:
            self.display_info(f"处理过程出错: {str(e)}")
        finally:
            self.thumbnail_processing = False
            self.stop_processing = False
            self.root.after(0, lambda: self.thumbnail_button.configure(
                text="生成缩略图",
                style="primary.TButton",
                state="normal"
            ))

    def _process_thumbnails_folder(self, folder, root_folder):
        """处理单个文件夹中的图片（缩略图）"""
        import glob
        
        # 创建 startupinfo 对象来隐藏命令行窗口
        startupinfo = None
        if os.name == 'nt':  # Windows系统
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        if self.stop_processing:
            return
            
        # 获取所有 PNG 和 JPG 文件
        image_files = []
        image_files.extend(glob.glob(os.path.join(folder, "*.png")))
        image_files.extend(glob.glob(os.path.join(folder, "*.jpg")))
        image_files.extend(glob.glob(os.path.join(folder, "*.jpeg")))
        
        for image_file in image_files:
            if self.stop_processing:
                return
            
            if not self.should_process_file(image_file):
                rel_path = os.path.relpath(image_file, root_folder)
                self.display_info(f"跳过: {rel_path}")
                continue
            
            try:
                # 构建输出文件路径
                filename = os.path.splitext(os.path.basename(image_file))[0]
                output_file = os.path.join(os.path.dirname(image_file), f"{filename}_proc.jpg")
                
                # 构建 ffmpeg 命令
                cmd = [
                    "ffmpeg",
                    "-i", image_file,
                    "-vf", "scale=17:-1",
                    "-q:v", "2",
                    "-compression_level", "50",
                    output_file,
                    "-y"
                ]
                
                # 执行 ffmpeg 命令，使用 subprocess.DEVNULL 忽略输出
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    startupinfo=startupinfo  # 添加这个参数
                )
                
                # 等待处理完成
                process.wait()
                
                if process.returncode == 0:
                    rel_input = os.path.relpath(image_file, root_folder)
                    rel_output = os.path.relpath(output_file, root_folder)
                    self.display_info(f"处理完成: {rel_input} -> {rel_output}")
                else:
                    rel_path = os.path.relpath(image_file, root_folder)
                    self.display_info(f"处理失败: {rel_path}")
            
            except Exception as e:
                rel_path = os.path.relpath(image_file, root_folder)
                self.display_info(f"处理出错: {rel_path}\n错误信息: {str(e)}")
        
        # 递归处理子文件夹
        for item in os.listdir(folder):
            if self.stop_processing:
                return
            item_path = os.path.join(folder, item)
            if os.path.isdir(item_path):
                self._process_thumbnails_folder(item_path, root_folder)

    def generate_avif_webp(self):
        """生成 avif/webp 格式图片"""
        # 先检查 optimizt 是否已安装
        if not self.check_command("optimizt"):
            self.show_custom_messagebox(
                "showerror",
                "错误",
                "未检测到 optimizt，请先安装 optimizt 后再使用此功能。\n\n" +
                "可以使用以下命令安装：\n" +
                "npm install -g optimizt"
            )
            return
        
        # 创建一个顶层窗口作为对话框的父窗口
        dialog_parent = ttk.Toplevel(self.root)
        dialog_parent.withdraw()
        dialog_parent.transient(self.root)
        
        if self.process_mode.get() == "single":  # 单文件模式
            file_path = filedialog.askopenfilename(
                parent=dialog_parent,
                title="选择需要处理的图片",
                filetypes=[("所有图片文件", "*.*")]  # 允许所有文件格式
            )
            if file_path:
                self.avif_webp_processing = True
                self.stop_processing = False
                self.avif_webp_button.configure(text="停止", style="danger.TButton")
                threading.Thread(target=self.process_single_avif_webp, args=(file_path,), daemon=True).start()
        else:  # 文件夹模式
            folder_path = filedialog.askdirectory(
                parent=dialog_parent,
                title="选择需要处理的文件夹"
            )
            if folder_path:
                self.avif_webp_processing = True
                self.stop_processing = False
                self.avif_webp_button.configure(text="停止", style="danger.TButton")
                threading.Thread(target=self.process_avif_webp, args=(folder_path,), daemon=True).start()
        
        dialog_parent.destroy()

    def process_single_avif_webp(self, image_file):
        """处理单个图片（avif/webp）"""
        try:
            self.display_info(f"开始处理文件: {os.path.basename(image_file)}")
            
            # 创建 startupinfo 对象来隐藏命令行窗口
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            try:
                filename_without_ext = os.path.splitext(image_file)[0]
                webp_file = f"{filename_without_ext}.webp"
                avif_file = f"{filename_without_ext}.avif"
                
                # 获取 optimizt 命令路径
                npm_path = os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Roaming', 'npm')
                optimizt_cmd = os.path.join(npm_path, 'optimizt.cmd')
                if not os.path.exists(optimizt_cmd):
                    optimizt_cmd = "optimizt"
                
                # 构建基础命令
                base_cmd = [optimizt_cmd, "--force"]
                
                # 检查是否需要生成 webp 和 avif
                need_webp = not os.path.exists(webp_file)
                need_avif = not os.path.exists(avif_file)
                
                if not need_webp and not need_avif:
                    self.display_info(f"跳过: {os.path.basename(image_file)} (已存在 webp 和 avif)")
                    return
                
                # 添加需要的格式参数
                if need_webp:
                    base_cmd.append("--webp")
                if need_avif:
                    base_cmd.append("--avif")
                
                # 添加输入文件
                base_cmd.append(image_file)
                
                # 执行命令
                process = subprocess.Popen(
                    base_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    startupinfo=startupinfo
                )
                
                process.wait()
                
                if process.returncode == 0:
                    formats = []
                    if need_webp:
                        formats.append("webp")
                    if need_avif:
                        formats.append("avif")
                    self.display_info(f"处理完成: {os.path.basename(image_file)} -> {', '.join(formats)}")
                else:
                    self.display_info(f"处理失败: {os.path.basename(image_file)}")
            
            except Exception as e:
                self.display_info(f"处理出错: {os.path.basename(image_file)}\n错误信息: {str(e)}")
            
        except Exception as e:
            self.display_info(f"处理过程出错: {str(e)}")
        finally:
            self.avif_webp_processing = False
            self.stop_processing = False
            self.root.after(0, lambda: self.avif_webp_button.configure(
                text="生成avif/webp",
                style="info.TButton",
                state="normal"
            ))

    def process_avif_webp(self, root_folder):
        """处理指定文件夹及其子文件夹中的所有图片，生成 avif 和 webp 格式"""
        try:
            folder_name = os.path.basename(root_folder)
            self.display_info(f"开始处理文件夹: {folder_name}")
            self._process_avif_webp_folder(root_folder, root_folder)
            if not self.stop_processing:
                self.display_info("所有文件处理完成！")
            else:
                self.display_info("处理已终止！")
        except Exception as e:
            self.display_info(f"处理过程出错: {str(e)}")
        finally:
            self.avif_webp_processing = False
            self.stop_processing = False
            self.root.after(0, lambda: self.avif_webp_button.configure(
                text="生成avif/webp",
                style="info.TButton",
                state="normal"
            ))

    def _process_avif_webp_folder(self, folder, root_folder):
        """处理单个文件夹中的图片（avif/webp）"""
        import glob
        
        # 创建 startupinfo 对象来隐藏命令行窗口
        startupinfo = None
        if os.name == 'nt':  # Windows系统
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # 获取 optimizt 命令路径
        npm_path = os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Roaming', 'npm')
        optimizt_cmd = os.path.join(npm_path, 'optimizt.cmd')
        if not os.path.exists(optimizt_cmd):
            optimizt_cmd = "optimizt"  # 如果找不到 .cmd 文件，使用命令名
        
        if self.stop_processing:
            return
            
        # 获取所有 PNG 和 JPG 文件
        image_files = []
        image_files.extend(glob.glob(os.path.join(folder, "*.png")))
        image_files.extend(glob.glob(os.path.join(folder, "*.jpg")))
        image_files.extend(glob.glob(os.path.join(folder, "*.jpeg")))
        
        for image_file in image_files:
            if self.stop_processing:
                return
            
            try:
                filename_without_ext = os.path.splitext(image_file)[0]
                webp_file = f"{filename_without_ext}.webp"
                avif_file = f"{filename_without_ext}.avif"
                
                # 构建基础命令
                base_cmd = [optimizt_cmd, "--force"]
                
                # 检查是否需要生成 webp
                need_webp = not os.path.exists(webp_file)
                # 检查是否需要生成 avif
                need_avif = not os.path.exists(avif_file)
                
                if not need_webp and not need_avif:
                    rel_path = os.path.relpath(image_file, root_folder)
                    self.display_info(f"跳过: {rel_path} (已存在 webp 和 avif)")
                    continue
                
                # 添加需要的格式参数
                if need_webp:
                    base_cmd.append("--webp")
                if need_avif:
                    base_cmd.append("--avif")
                
                # 添加输入文件
                base_cmd.append(image_file)
                
                # 执行命令
                process = subprocess.Popen(
                    base_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    startupinfo=startupinfo  # 添加这个参数
                )
                
                # 等待处理完成
                process.wait()
                
                if process.returncode == 0:
                    formats = []
                    if need_webp:
                        formats.append("webp")
                    if need_avif:
                        formats.append("avif")
                    rel_path = os.path.relpath(image_file, root_folder)
                    self.display_info(f"处理完成: {rel_path} -> {', '.join(formats)}")
                else:
                    rel_path = os.path.relpath(image_file, root_folder)
                    self.display_info(f"处理失败: {rel_path}")
            
            except Exception as e:
                rel_path = os.path.relpath(image_file, root_folder)
                self.display_info(f"处理出错: {rel_path}\n错误信息: {str(e)}")
        
        # 递归处理子文件夹
        for item in os.listdir(folder):
            if self.stop_processing:
                return
            item_path = os.path.join(folder, item)
            if os.path.isdir(item_path):
                self._process_avif_webp_folder(item_path, root_folder)

    def should_process_file(self, filepath):
        """检查文件是否需要处理"""
        # 检查文件名是否包含需要跳过的关键词
        filename = os.path.basename(filepath).lower()
        skip_keywords = ["banner", "index", "proc"]
        if any(keyword in filename for keyword in skip_keywords):
            return False
        
        # 检查是否已存在对应的处理后文件
        filename_without_ext = os.path.splitext(filepath)[0]
        processed_file = f"{filename_without_ext}_proc.jpg"
        
        # 如果已经存在处理后的文件，则跳过
        if os.path.exists(processed_file):
            return False
        
        return True

    def display_info(self, message):
        """显示信息"""
        self.info_display.insert("end", message + "\n")
        self.info_display.see("end")

    def show_custom_messagebox(self, type_, title, message, **kwargs):
        """显示自定义消息框"""
        dialog = ttk.Toplevel(self.root)
        dialog.withdraw()  # 隐藏对话框
        dialog.transient(self.root)  # 设置为主窗口的临时窗口
        
        if hasattr(self, 'icon_path') and self.icon_path:
            dialog.iconbitmap(self.icon_path)
        
        if type_ == "showinfo":
            result = messagebox.showinfo(title, message, parent=dialog, **kwargs)
        elif type_ == "showwarning":
            result = messagebox.showwarning(title, message, parent=dialog, **kwargs)
        elif type_ == "showerror":
            result = messagebox.showerror(title, message, parent=dialog, **kwargs)
        elif type_ == "askyesno":
            result = messagebox.askyesno(title, message, parent=dialog, **kwargs)
        
        dialog.destroy()
        return result

    def on_window_configure(self, event):
        """处理窗口大小变化事件"""
        if event.widget == self.root:
            required_width = self.calculate_required_width()
            if event.width < required_width:
                new_width = max(required_width, self.min_width)
                self.root.geometry(f"{new_width}x{event.height}")

    def calculate_required_width(self):
        """计算界面所需的最小宽度（考虑 DPI 缩放）"""
        if hasattr(self, 'main_frame') and self.main_frame.winfo_ismapped():
            # 计算主界面所需宽度
            left_padding = int(45 * self.scaling_factor)  # 左侧偏移
            first_button_width = 10  # 第一个按钮宽度（字符数）
            second_button_width = 14  # 第二个按钮宽度（字符数）
            char_width = int(8 * self.scaling_factor)     # 每个字符的平均像素宽度
            button_padding = int((5 + 15 + 5) * self.scaling_factor)  # 按钮之间的间距
            
            # 计算总宽度
            total_width = (
                left_padding +                                    # 左侧偏移
                (first_button_width * char_width) +              # 第一个按钮的宽度
                (second_button_width * char_width) +             # 第二个按钮的宽度
                button_padding +                                 # 按钮之间的间距
                int(40 * self.scaling_factor)                    # 额外边距
            )
            
            return total_width
        
        return self.min_width

    def check_environment(self):
        """检查环境中是否存在所需的命令行工具"""
        # 检查 ffmpeg
        if self.check_command("ffmpeg"):
            self.ffmpeg_status.configure(
                text="ffmpeg: 已安装 ✓",
                foreground="green"
            )
        else:
            self.ffmpeg_status.configure(
                text="ffmpeg: 未安装 ✗",
                foreground="red"
            )
        
        # 检查 optimizt
        if self.check_command("optimizt"):
            self.optimizt_status.configure(
                text="optimizt: 已安装 ✓",
                foreground="green"
            )
        else:
            self.optimizt_status.configure(
                text="optimizt: 未安装 ✗",
                foreground="red"
            )

    def check_command(self, command):
        """检查命令是否可用"""
        # 创建 startupinfo 对象来隐藏命令行窗口
        startupinfo = None
        if os.name == 'nt':  # Windows系统
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            # 首先尝试直接运行命令
            subprocess.run(
                [command, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo  # 添加这个参数
            )
            return True
        except FileNotFoundError:
            # 如果直接运行失败，检查 npm 全局安装路径
            if command == "optimizt":
                npm_path = os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Roaming', 'npm')
                command_path = os.path.join(npm_path, command + '.cmd')
                
                if os.path.exists(command_path):
                    try:
                        subprocess.run(
                            [command_path, "--version"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            startupinfo=startupinfo  # 添加这个参数
                        )
                        return True
                    except:
                        pass
            return False

if __name__ == "__main__":
    # 在创建窗口之前设置 DPI 感知
    set_dpi_awareness()
    
    root = ttk.Window(themename="cosmo")
    root.withdraw()
    
    # 获取当前屏幕的 DPI 缩放因子
    try:
        scaling_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    except:
        scaling_factor = 1
    
    # 调整窗口大小和位置
    window_width = int(450 * scaling_factor)
    window_height = int(450 * scaling_factor)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # 设置窗口图标
    icon_path = get_resource_path("2.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    
    # 创建应用实例
    app = App(root)
    
    # 显示窗口
    root.deiconify()
    
    # 开始主循环
    root.mainloop() 