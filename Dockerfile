# Frontend build stage
FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /frontend
COPY frontend_v2/package*.json ./
RUN npm ci
COPY frontend_v2/ ./
RUN npm run build

# Use official Playwright image (includes Python & Browsers)
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

ARG ENABLE_CN_MIRRORS=false

WORKDIR /app

# ---------------------------------------------------------
# Set domestic mirrors (Ubuntu/PyPI) for China network
# ---------------------------------------------------------

# Enable mirrors only when explicitly requested by the build environment.
RUN if [ "$ENABLE_CN_MIRRORS" = "true" ]; then \
      sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
      sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
      sed -i 's/ports.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
      pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/; \
    fi

# ---------------------------------------------------------
# Install Dependencies
# ---------------------------------------------------------

# Install additonal system dependencies if needed (Playwright image has most)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN PIP_DEFAULT_TIMEOUT=120 pip install --no-cache-dir --retries 5 -r requirements.txt

# (No need to run playwright install, browsers are pre-installed)

# ---------------------------------------------------------
# Application Setup
# ---------------------------------------------------------

COPY . .
COPY --from=frontend-builder /frontend/dist /app/frontend_v2_dist

ENV PYTHONUNBUFFERED=1

CMD ["python", "batch_generator.py"]
