# syntax=docker/dockerfile:1.7

# Pull official base image
FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6

# Set work directory
# Create non-root user
RUN addgroup --system app && adduser --system --group app

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev python3-dev nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Install the exact locked development dependency set before copying application code.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --extra dev --no-install-project

# Copy project
COPY . .

# Build Tailwind CSS
RUN npm ci --include=dev && npm run build:css

# Change ownership to non-root user
RUN chown -R app:app /app
USER app
