# ── Stage 1: build ui ─────────────────────────────────────────────────────────
FROM node:20-alpine AS ui-builder
RUN corepack enable pnpm
WORKDIR /app/ui
COPY ui/package.json ui/pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile
COPY ui/ ./
RUN pnpm build
# Output: /app/ui/dist

# ── Stage 2: api + static files ───────────────────────────────────────────────
FROM python:3.12-slim
WORKDIR /app

# uv for fast installs — no pip cache needed in Docker
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY api/pyproject.toml api/uv.lock* ./
RUN uv sync --frozen --no-dev

COPY api/ ./
COPY --from=ui-builder /app/ui/dist ./static

# SQLite checkpoint — persist via a named volume
# docker run -v <demo>-data:/app/data -e OPENAI_API_KEY=sk-... <image>
ENV CHECKPOINT_PATH=/app/data/checkpoints.sqlite
ENV SERVE_STATIC=true

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "template_api.main:app", "--host", "0.0.0.0", "--port", "8000"]