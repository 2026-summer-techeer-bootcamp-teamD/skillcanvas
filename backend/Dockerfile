FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 배포용 기본 실행 (개발 시엔 docker-compose가 --reload 로 덮어씀)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
