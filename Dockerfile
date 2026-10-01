FROM node:22-bookworm-slim AS web-build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY frontend ./frontend
RUN npm run build

FROM node:22-bookworm-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=10000 \
    AI_SERVICE_URL=http://127.0.0.1:8001 \
    PATH=/opt/venv/bin:$PATH

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements-images.txt ./
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu -r requirements-images.txt

COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY backend ./backend
COPY ml ./ml
COPY scripts/start_production.py ./scripts/start_production.py
COPY data/directory.json data/model_metrics.json data/image_metrics.json data/image_pipeline_metrics.json data/training_complaints.csv ./data/
COPY --from=web-build /app/dist ./dist

EXPOSE 10000
CMD ["python", "scripts/start_production.py"]
