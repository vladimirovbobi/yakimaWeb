# Multi-stage: node frontend build → python runtime
ARG PYTHON_VERSION=3.12-slim

# ─── Stage 1: build static assets ────────────────────────────────────────
FROM node:22-alpine AS frontend
WORKDIR /build
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund || true
COPY tailwind.config.js postcss.config.js vite.config.js ./
COPY static/src ./static/src
COPY templates ./templates
COPY apps ./apps
RUN npm run build

# ─── Stage 2: python runtime ─────────────────────────────────────────────
FROM python:${PYTHON_VERSION} AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# uv for fast dep install
RUN pip install --no-cache-dir uv

# Copy source FIRST (because pyproject lists explicit packages we need to exist)
COPY . .
COPY --from=frontend /build/static/dist ./static/dist

RUN uv pip install --system --no-cache . --group dev

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
