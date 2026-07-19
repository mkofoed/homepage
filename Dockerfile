# syntax=docker/dockerfile:1.7

# Pull official base image
FROM python:3.14-slim@sha256:71b358f8bff55413f4a6b95af80acb07ab97b5636cd3b869f35c3680d31d1650

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
