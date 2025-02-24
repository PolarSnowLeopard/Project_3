# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装中文字体和其他工具
RUN apt-get update && \
    apt-get install -y \
    fonts-wqy-microhei \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 创建日志目录
RUN mkdir -p /app/logs /app/output

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV LOG_PATH=/app/logs/app.log

# 复制项目文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 确保日志文件存在并设置权限
RUN touch /app/logs/app.log && \
    chmod 666 /app/logs/app.log

# 启动服务（使用tee同时输出到控制台和文件）
CMD python app.py 2>&1 | tee -a /app/logs/app.log