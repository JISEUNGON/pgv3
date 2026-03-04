# pgv3 - Container Management System V3 (FastAPI)
# Python 3.12 + Poetry
FROM python:3.12-slim

# 시스템 패키지 (필요 시 추가)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
ENV PATH="${POETRY_HOME}/bin:${PATH}"
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

# 의존성만 먼저 복사 후 설치 (레이어 캐시 활용)
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-root

# 애플리케이션 코드 및 설정
COPY main.py ./
COPY application.yaml ./
COPY src ./src

# 설정은 application.yaml 기준 (컨테이너 실행 시 볼륨/환경변수로 오버라이드 가능)
ENV PYTHONUNBUFFERED=1