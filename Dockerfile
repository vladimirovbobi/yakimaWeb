# Multi-stage: node frontend build → python runtime
ARG PYTHON_VERSION=3.12-slim

# ─── Stage 1: build static assets ────────────────────────────────────────
FROM node:26-alpine AS frontend
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

# ─── Stage 3: img-worker runtime (Playwright Chromium + Claude CLI) ──────
# Used by the img-worker compose service ONLY. The api/celery/beat services
# stick with the leaner `runtime` stage above.
FROM runtime AS img-runtime

# Node.js 20 — needed for the Claude Code CLI (npm-distributed).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Claude Code CLI (prototype-only flyer-generator backend; see ADR-0005 +
# the flyer-generator plan in .planning/).
RUN npm install -g @anthropic-ai/claude-code \
    && claude --version

# Playwright + Chromium for HTML→PDF rendering of generated flyers.
# `--with-deps` pulls the system libs Chromium needs at runtime.
RUN playwright install --with-deps chromium
