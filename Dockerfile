# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装中文字体
RUN apt-get update && \
    apt-get install -y fonts-wqy-microhei && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .

# 创建输出目录
RUN mkdir output

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 5000

# 启动服务
CMD ["python", "app.py"]