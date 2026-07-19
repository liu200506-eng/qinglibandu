FROM python:3.11-slim

WORKDIR /app

# 设置时区与编码
ENV PYTHONIOENCODING=utf-8 \
    TZ=Asia/Shanghai \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 数据库目录（与 docker-compose volume 对应）
RUN mkdir -p /app/database

EXPOSE 8001

# 启动时若数据库为空，则从 JSON 重建
CMD ["sh", "-c", "python manage_knowledge.py rebuild computer_network || true; uvicorn main:app --host 0.0.0.0 --port 8001"]
