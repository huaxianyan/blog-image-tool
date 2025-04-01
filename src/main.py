import os
import sys
import asyncio
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.ui.main_window import MainWindow

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def main():
    """主函数"""
    # 创建主窗口
    root = ttk.Window(
        title="图片处理工具",
        themename="cosmo",
        size=(450, 450),
        position=(100, 100),
        minsize=(450, 450)
    )
    root.withdraw()
    
    # 设置样式
    style = ttk.Style()
    style.configure('TFrame', background='white')
    style.configure('TLabelframe', background='white')
    style.configure('TLabelframe.Label', background='white')
    style.configure('TRadiobutton', background='white')
    
    # 获取DPI缩放因子
    try:
        scaling_factor = root.winfo_fpixels('1i') / 72.0
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
    
    # 创建应用实例
    app = MainWindow(root)
    
    # 设置窗口关闭处理
    def on_closing():
        app._cleanup()  # 清理资源
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 显示窗口
    root.deiconify()
    
    # 开始主循环
    root.mainloop()

if __name__ == "__main__":
    main() 