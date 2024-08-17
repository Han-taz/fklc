FROM ubuntu:latest
LABEL authors="kevin"

# Poetry 기반 Python 3.10 이미지를 사용
FROM python:3.10.12

# 작업 디렉터리 설정
WORKDIR /app

# 시스템 패키지 설치 (옵션)
RUN apt-get update && apt-get install -y curl

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 -

# Poetry 환경 변수 설정
ENV PATH="/root/.local/bin:$PATH"

# 프로젝트 파일을 복사
COPY pyproject.toml poetry.lock /app/

# Poetry를 사용하여 의존성 설치
RUN poetry config virtualenvs.create false && poetry install --no-root --no-dev

# 애플리케이션 소스 코드를 복사
COPY ./app /app

# FastAPI 애플리케이션 실행 (gunicorn + uvicorn)
CMD ["poetry", "run", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
