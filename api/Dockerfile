# RootCause AI — API adapter image
#
# Contains the unmodified backend modules plus the adapter. The adapter copies the
# backend's *.py files into a per-job workspace at runtime, so the image is
# read-only at the filesystem root and writable only where it needs to be.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# `contree` needs no compilers, but keep the image lean and non-root.
RUN useradd --create-home --uid 10001 rcai

WORKDIR /app

COPY api/requirements-api.txt /app/api/requirements-api.txt
COPY requirements.txt /app/backend-requirements.txt

# Backend deps (Streamlit is not needed by the adapter; install only what the
# investigation path imports) + adapter deps + the Nebius sandbox CLI.
RUN pip install --no-cache-dir \
        openai \
        python-dotenv \
        contree-cli \
    && pip install --no-cache-dir -r /app/api/requirements-api.txt

# The repository as-is: backend modules for the per-job copy, plus the adapter.
COPY --chown=rcai:rcai . /app/backend
COPY --chown=rcai:rcai api /app/backend/api

# Writable locations only.
RUN mkdir -p /data/state /data/work \
    && chown -R rcai:rcai /data

ENV RC_STATE_DIR=/data/state \
    RC_WORKSPACE_ROOT=/data/work \
    RC_BACKEND_DIR=/app/backend \
    RC_TRUST_PROXY=true \
    HOME=/home/rcai

USER rcai
WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
