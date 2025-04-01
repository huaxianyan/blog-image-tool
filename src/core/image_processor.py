import os
import asyncio
import subprocess
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ProcessMode(Enum):
    SINGLE = "single"
    FOLDER = "folder"

class ProcessType(Enum):
    THUMBNAIL = "thumbnail"
    AVIF_WEBP = "avif_webp"

@dataclass
class ProcessResult:
    success: bool
    message: str
    input_path: str
    output_paths: List[str]

class ImageProcessor:
    def __init__(self):
        self._ffmpeg_path = self._find_ffmpeg()
        self._optimizt_path = self._find_optimizt()
        
    def _check_environment(self):
        """检查环境配置"""
        # 检查ffmpeg
        ffmpeg_path = self._find_ffmpeg()
        if ffmpeg_path:
            self._ffmpeg_path = ffmpeg_path
        else:
            self._ffmpeg_path = None
            
        # 检查optimizt
        optimizt_path = self._find_optimizt()
        if optimizt_path:
            self._optimizt_path = optimizt_path
        else:
            self._optimizt_path = None
            
    def _find_ffmpeg(self) -> Optional[str]:
        """查找ffmpeg可执行文件路径"""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True)
            return "ffmpeg"
        except FileNotFoundError:
            return None
            
    def _find_optimizt(self) -> Optional[str]:
        """查找optimizt可执行文件路径"""
        try:
            subprocess.run(["optimizt", "--version"], capture_output=True)
            return "optimizt"
        except FileNotFoundError:
            npm_path = os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Roaming', 'npm')
            optimizt_cmd = os.path.join(npm_path, 'optimizt.cmd')
            if os.path.exists(optimizt_cmd):
                return optimizt_cmd
            return None
        
    def _check_command(self, command: str) -> bool:
        """检查命令是否可用"""
        try:
            result = subprocess.run(
                [command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
            
    def _run_command(self, command: list, cwd: Optional[str] = None) -> tuple:
        """运行命令"""
        try:
            # 检查是否需要管理员权限
            if self._needs_admin_permission(command[0]):
                # 尝试以管理员权限运行
                if not self._run_as_admin(command, cwd):
                    return False, "需要管理员权限但无法获取"
                    
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, str(e)
            
    def _needs_admin_permission(self, path: str) -> bool:
        """检查是否需要管理员权限"""
        try:
            # 检查文件是否存在
            if not os.path.exists(path):
                return False
                
            # 尝试以普通权限访问文件
            with open(path, 'rb') as f:
                f.read(1)
                f.seek(0)
            return False
        except PermissionError:
            return True
        except:
            return False
            
    def _run_as_admin(self, command: list, cwd: Optional[str] = None) -> bool:
        """以管理员权限运行命令"""
        try:
            # 使用 ShellExecuteW 以管理员权限运行命令
            if cwd:
                os.chdir(cwd)
                
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待进程完成
            stdout, stderr = process.communicate()
            return process.returncode == 0
        except:
            return False

    async def process_thumbnail(self, input_path: str) -> ProcessResult:
        """异步处理缩略图"""
        if not self._ffmpeg_path:
            return ProcessResult(
                success=False,
                message="ffmpeg未安装",
                input_path=input_path,
                output_paths=[]
            )

        try:
            output_path = f"{os.path.splitext(input_path)[0]}_proc.jpg"
            cmd = [
                self._ffmpeg_path,
                "-i", input_path,
                "-vf", "scale=17:-1",
                "-q:v", "2",
                "-compression_level", "50",
                output_path,
                "-y"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            await process.wait()
            
            if process.returncode == 0:
                return ProcessResult(
                    success=True,
                    message="处理成功",
                    input_path=input_path,
                    output_paths=[output_path]
                )
            else:
                return ProcessResult(
                    success=False,
                    message="处理失败",
                    input_path=input_path,
                    output_paths=[]
                )
        except Exception as e:
            return ProcessResult(
                success=False,
                message=f"处理出错: {str(e)}",
                input_path=input_path,
                output_paths=[]
            )

    async def process_avif_webp(self, input_path: str) -> ProcessResult:
        """异步处理avif/webp格式"""
        if not self._optimizt_path:
            return ProcessResult(
                success=False,
                message="optimizt未安装",
                input_path=input_path,
                output_paths=[]
            )

        try:
            base_path = os.path.splitext(input_path)[0]
            webp_path = f"{base_path}.webp"
            avif_path = f"{base_path}.avif"
            
            cmd = [self._optimizt_path, "--force"]
            
            # 检查是否需要生成webp和avif
            need_webp = not os.path.exists(webp_path)
            need_avif = not os.path.exists(avif_path)
            
            if not need_webp and not need_avif:
                return ProcessResult(
                    success=True,
                    message="文件已存在，跳过处理",
                    input_path=input_path,
                    output_paths=[webp_path, avif_path]
                )
            
            if need_webp:
                cmd.append("--webp")
            if need_avif:
                cmd.append("--avif")
            
            cmd.append(input_path)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            await process.wait()
            
            if process.returncode == 0:
                output_paths = []
                if need_webp and os.path.exists(webp_path):
                    output_paths.append(webp_path)
                if need_avif and os.path.exists(avif_path):
                    output_paths.append(avif_path)
                    
                return ProcessResult(
                    success=True,
                    message="处理成功",
                    input_path=input_path,
                    output_paths=output_paths
                )
            else:
                return ProcessResult(
                    success=False,
                    message="处理失败",
                    input_path=input_path,
                    output_paths=[]
                )
        except Exception as e:
            return ProcessResult(
                success=False,
                message=f"处理出错: {str(e)}",
                input_path=input_path,
                output_paths=[]
            )

    def should_process_file(self, filepath: str) -> bool:
        """检查文件是否需要处理"""
        filename = os.path.basename(filepath).lower()
        skip_keywords = ["banner", "index", "proc"]
        if any(keyword in filename for keyword in skip_keywords):
            return False
        
        filename_without_ext = os.path.splitext(filepath)[0]
        processed_file = f"{filename_without_ext}_proc.jpg"
        
        return not os.path.exists(processed_file)

    async def process_directory(
        self,
        directory: str,
        process_type: ProcessType,
        progress_callback=None
    ) -> List[ProcessResult]:
        """异步处理整个目录"""
        results = []
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        file_path = os.path.join(root, file)
                        if self.should_process_file(file_path):
                            try:
                                if process_type == ProcessType.THUMBNAIL:
                                    result = await self.process_thumbnail(file_path)
                                else:
                                    result = await self.process_avif_webp(file_path)
                                    
                                if result:  # 确保结果不为None
                                    results.append(result)
                                    if progress_callback:
                                        await progress_callback(result)
                            except Exception as e:
                                # 如果处理单个文件失败，创建一个失败的结果
                                error_result = ProcessResult(
                                    success=False,
                                    message=f"处理出错: {str(e)}",
                                    input_path=file_path,
                                    output_paths=[]
                                )
                                results.append(error_result)
                                if progress_callback:
                                    await progress_callback(error_result)
                                
        except Exception as e:
            # 如果整个目录处理过程出错，返回一个错误结果
            error_result = ProcessResult(
                success=False,
                message=f"目录处理出错: {str(e)}",
                input_path=directory,
                output_paths=[]
            )
            results.append(error_result)
            if progress_callback:
                await progress_callback(error_result)
                
        return results 