# Stage 1 — build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
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

ENV NODE_ENV=production PYTHONUNBUFFERED=1

# Python deps
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Node scan-worker: install deps and Playwright Chromium, then copy source
WORKDIR /app/scan-worker
COPY scan-worker/package*.json ./
RUN npm install
RUN npx playwright install --with-deps chromium
COPY scan-worker/ ./

# Copy backend source and built frontend
WORKDIR /app/backend
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist ./public

EXPOSE 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
