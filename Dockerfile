# Stage 1 — build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2 — runtime: Python 3.12 + Node 20 + Playwright Chromium
FROM python:3.12-slim AS runtime

# System libs: Node 20, Playwright/Chromium deps, libgomp1 for ONNX (fastembed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gnupg libgomp1 && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Chromium lives in a shared, world-readable path (NOT /root/.cache) so the
# non-root runtime user can read it. Set before `playwright install`.
ENV NODE_ENV=production \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Python deps
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Node scan-worker: install deps and Playwright Chromium, then copy source
WORKDIR /app/scan-worker
COPY scan-worker/package*.json ./
RUN npm ci
RUN npx playwright install --with-deps chromium
COPY scan-worker/ ./

# Copy backend source and built frontend
WORKDIR /app/backend
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist ./public

# Non-root user. Chromium + its cache must be readable/executable by this user.
RUN useradd --create-home --uid 10001 appuser && \
    chmod -R a+rX /ms-playwright && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Probe nginx-less uvicorn on the app port. python3 is guaranteed present
# (the base image is Python); curl is NOT in python:3.12-slim.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python3 -c "import os,urllib.request,sys; \
url='http://127.0.0.1:'+os.environ.get('PORT','8000')+'/api/health'; \
sys.exit(0 if urllib.request.urlopen(url, timeout=4).status==200 else 1)" || exit 1

# `exec` so uvicorn replaces the shell and receives SIGTERM directly
# (graceful shutdown). Shell form kept for ${PORT} expansion.
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
