# Frontend build stage
FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /frontend
COPY frontend_next/package*.json ./
RUN npm ci
COPY frontend_next/ ./
RUN npm run build

# Main stage
# Playwright Python image: Chromium + Firefox + WebKit browsers pre-installed
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

ARG ENABLE_CN_MIRRORS=false

WORKDIR /app

# System dependencies + PostgreSQL client
RUN apt-get update && apt-get install -y \
    build-essential curl git libxml2-dev libxslt-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# CN mirrors (optional, set ENABLE_CN_MIRRORS=true to use)
RUN if [ "$ENABLE_CN_MIRRORS" = "true" ]; then \
      sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
      sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
      pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/; \
    fi

# Python dependencies
COPY requirements.txt .
RUN PIP_DEFAULT_TIMEOUT=120 pip install --no-cache-dir --retries 5 -r requirements.txt

# Pre-download CloakBrowser Chromium binary (~140MB)
# This runs at BUILD time so containers start instantly without downloading
COPY scripts/docker_init.py /tmp/docker_init.py
RUN python3 /tmp/docker_init.py && rm /tmp/docker_init.py

# Application
COPY . .
COPY --from=frontend-builder /frontend/.next /app/frontend_dist

ENV PYTHONUNBUFFERED=1
ENV GEO_FRONTEND_DIST_DIR=/app/frontend_dist

CMD ["python", "batch_generator.py"]
