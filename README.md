# 图片处理工具

一个用于处理博客图片的 Windows 工具，支持生成缩略图和转换为 avif/webp 格式。

> 本项目所有代码均由 [Cursor](https://cursor.sh) 生成，包括 README 文档。

## 功能特性

- 生成缩略图
  - 支持 PNG、JPG、JPEG 格式
  - 自动跳过 webp 和 avif 格式
  - 自动跳过 index 和 banner 文件
  - 自动跳过以 _proc 结尾的文件

- 转换为 avif/webp 格式
  - 支持 PNG、JPG、JPEG 格式
  - 自动跳过 webp 和 avif 格式

## 环境要求

- Windows 操作系统
- Python 3.11 或更高版本
- ffmpeg（用于生成缩略图）
- optimizt（用于转换为 avif/webp 格式）

## 安装依赖

1. 安装 ffmpeg
   - 从 [ffmpeg 官网](https://ffmpeg.org/download.html) 下载
   - 将 ffmpeg 添加到系统环境变量

2. 安装 optimizt
   ```bash
   npm install -g optimizt
   ```

## 使用方法

1. 运行程序
   ```bash
   python run.py
   ```

2. 选择处理模式
   - 点击"生成缩略图"按钮处理图片生成缩略图
   - 点击"生成avif/webp"按钮处理图片转换为 avif/webp 格式

3. 选择文件
   - 在弹出的文件选择对话框中选择要处理的图片文件
   - 支持多选文件

4. 等待处理完成
   - 处理过程中会显示进度信息
   - 可以随时点击"停止"按钮终止处理

## 输出说明

- 缩略图：在原文件名后添加 _proc 后缀
- avif/webp：在原文件名后添加 .avif 和 .webp 后缀

## 注意事项

- 程序会自动跳过不需要处理的文件
- 处理过程中请勿关闭程序
- 建议在处理大量文件前先测试少量文件

## 许可证

MIT License