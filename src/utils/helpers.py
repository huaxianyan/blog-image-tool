import os
import sys
from typing import Optional

def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def is_windows() -> bool:
    """检查是否在Windows系统上运行"""
    return sys.platform == "win32"

def get_npm_global_path() -> Optional[str]:
    """获取npm全局安装路径"""
    if is_windows():
        return os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Roaming', 'npm')
    return None

def format_file_size(size_in_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB" 