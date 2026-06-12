# 使用官方轻量级 Python 镜像
FROM python:3.10-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 替换为清华大学 Debian 镜像源，加速 apt-get update 和 install
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖（FFmpeg 是音频隐写核心依赖）
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavcodec-extra \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码到容器中
COPY . /app/

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 创建媒体文件挂载点
RUN mkdir -p /app/media/videos /app/media/watermarked /app/media/settings

# 暴露端口
EXPOSE 8000

# 启动 Gunicorn 服务器 (因为音频处理可能耗时较长，增加 timeout 设置)
CMD ["gunicorn", "video_system.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "300"]
