# 1. 使用官方的 Python 基础镜像
FROM python:3.11-slim-bullseye

# 2. 设置工作目录
WORKDIR /app

# 3. 复制依赖文件
COPY requirements.txt .

# 4. 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 5. 复制应用代码
COPY . .

# 6. 暴露新的端口
EXPOSE 11435

# 7. 启动命令，使用新的端口
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11435"]