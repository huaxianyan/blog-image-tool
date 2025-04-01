import os
import sys

# 获取可执行文件所在目录
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# 将可执行文件目录添加到 DLL 搜索路径
os.add_dll_directory(application_path)

# 将 Python 安装目录添加到 DLL 搜索路径
if hasattr(sys, '_MEIPASS'):
    os.add_dll_directory(sys._MEIPASS) 