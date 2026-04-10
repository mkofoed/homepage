# Pull official base image
FROM python:3.14-slim@sha256:71b358f8bff55413f4a6b95af80acb07ab97b5636cd3b869f35c3680d31d1650

# Set work directory
# Create non-root user
RUN addgroup --system app && adduser --system --group app

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Install dependencies
COPY ./pyproject.toml .
RUN uv pip install --system -e .[dev]

# Copy project
COPY . .

# Change ownership to non-root user
RUN chown -R app:app /app
USER app
