# AI Agent Documentation

This document provides a comprehensive overview of the `homepage` project to help AI assistants and agents quickly understand the architecture, tech stack, and coding conventions used in this codebase.

## Project Overview
This project is a personal homepage and web application. It serves as both a public-facing website and an active demonstration of modern backend development practices using Django.

## Tech Stack
- **Framework**: Django 6.0
- **Language**: Python 3.14
- **Package Management**: `uv` (Configurations in `pyproject.toml`)
- **Database**: PostgreSQL 18 (using TimescaleDB docker image locally)
- **Frontend Integration**: HTMX (managed via `django-htmx`)
- **API Framework**: Django REST Framework (DRF)
- **API Documentation**: `drf-spectacular` (Swagger UI available at `/api/docs/`)
- **Containerization**: Docker & Docker Compose
- **Linting & Formatting**: Ruff
- **Type Checking**: Mypy (`django-stubs`, `djangorestframework-stubs`)

## Deployment Details
### Deployment Workflow
- Images are hosted on GitHub Container Registry (GHCR) at `ghcr.io/mkofoed/homepage-web`.
- CI/CD with GitHub Actions handles automated builds and deployment.
- Key steps include:
  - Docker images are built and pushed to GHCR.
  - Server setup transfers files like `docker-compose.prod.yml`, `deploy.sh`, `rollback.sh`, and `nginx/` via SCP.
  - The server does not use `git` for deployment files.

### Service Setup
- **Nginx**: Included in the Docker Compose stack using the image `jonasal/nginx-certbot:5-alpine`.
- **Networks**: 
  - `frontend` (nginx + web)
  - `backend` (web + db + redis + celery).
- **Environment**: Relies on `.env` for secrets like `REDIS_PASSWORD`, `POSTGRES_USER`, etc.

### Database and Redis
- PostgreSQL 18 is used with the `homepage_app` user.
- Redis requires authentication and uses a read-only file system for security.

### Deployment Scripts
- `deploy.sh` ensures safe migrations, health checks, and rollback support.
- Health checks use `docker exec` to run lightweight service checks inside containers.

---

## Agent Guidelines & Conventions
When modifying or extending this codebase, adhere to the following rules:

### 1. Strictly use the Service Layer Pattern
- **Views (`views.py`)**: Must only handle HTTP request parsing, basic validation, delegation to a service function, and returning the proper HTTP Response/Template.
- **Services (`services/*.py`)**: Must contain all business logic, complex database queries, external API calls, and algorithmic computations. Services should be independent of Django's `Request` object whenever possible.

### 2. Frontend / HTMX
- We rely on `django-htmx` middleware.
- When writing views that respond to HTMX triggers, use `if getattr(request, "htmx", False):` to determine if you should return a partial HTML snippet or a fully extended base template.

### 3. Dependency Management (`uv`)
- Dependencies are managed exclusively via `uv` in the `pyproject.toml` file.
- Do not generate `requirements.txt` or `Pipfile`.
- When updating dependencies in the Docker container, utilize `uv pip install --system -e .` or `uv sync`.

### 4. Code Quality & Typing
- **Type Hints**: All new functions, variables, and class methods must have explicit Python 3.14 type hints.
- **Ruff**: Ensure your code conforms to the Ruff formatting rules defined in `pyproject.toml`. Run `uv run ruff check --fix .` and `uv run ruff format .` on modifications.
- **Mypy**: Ensure strict type compliance by running `uv run mypy .`.

### 5. Dockerized Environment
- The project is designed to be run via `docker-compose up`.
- The `web` service mounts the root directory directly into `/app`.
- PostgreSQL database volumes are persistent (`postgres_data`). Local database configurations are mocked via the `.env` file (copied from `.env.example`).