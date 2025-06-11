# Python 이미지 사용
FROM python:3.10-slim

ENV TZ=Asia/Seoul

RUN apt-get update && apt-get install -y tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    apt-get clean

# 작업 디렉터리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 기본 명령(Compose에서 덮어씀)
CMD ["python", "main_alert.py"]
