# Stage 1: Build stage using official Python 12 image
FROM python:3.12-slim AS builder

WORKDIR /app

# Install Astral UV package manager in builder stage
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy virtual environment lockfiles and package manifests
COPY pyproject.toml uv.lock ./

# Compile virtual environment dependencies cleanly
RUN uv venv .venv && uv pip install --no-cache -r pyproject.toml

# Stage 2: Final lightweight runtime stage
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy compiled python virtual environment packages
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application layers, configurations, and assets
COPY app/ ./app/
COPY policies/ ./policies/
COPY public/ ./public/
COPY server.py ./server.py

# Expose port and configure web-server environments
ENV PORT=8000
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Bootstrap application on port 8000
CMD ["python", "server.py"]
