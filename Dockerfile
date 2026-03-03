FROM python:3.10-slim

WORKDIR /app

# 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# 代码
COPY src/ ./src/
COPY api/ ./api/

# 端口
EXPOSE 8000

# 运行
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
