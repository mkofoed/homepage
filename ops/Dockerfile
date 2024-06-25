# Use python:3.12-alpine as the base image for the builder stage
FROM python:3.12-alpine AS builder

# Upgrade pip and install poetry
RUN pip install --upgrade pip \
    && pip install "poetry==1.8.3"

WORKDIR /homepage
COPY poetry.lock pyproject.toml /homepage/ops/

# Install the Python dependencies
RUN poetry config virtualenvs.create false \
    && cd ./ops \
    && poetry install $(test "$ENVIRONMENT" == production && echo "--no-dev") --no-interaction --no-ansi \
    && rm -rf ~/.cache/pip

# Use python:3.12-alpine as the base image for the final stage
FROM python:3.12-alpine

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

WORKDIR /homepage
COPY . /homepage/
