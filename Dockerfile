FROM python:3.11-slim-bullseye

WORKDIR /app

COPY . /app

RUN set -ex \
    && apt-get update \
    && apt install -y \
    fonts-dejavu fonts-liberation fonts-noto fonts-roboto fonts-open-sans \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]