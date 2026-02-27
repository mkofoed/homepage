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

## Application Architecture

The project is structured into modular Django applications. We strictly enforce a **Service Layer** pattern to prevent "Fat Views" and keep business logic decoupled from HTTP request handling.

### 1. `core` App
Handles project-wide infrastructure, base templates, and system metrics.
- **Views**: `/health/`, `/metrics/`, dashboard, and static pages (`home`, `about`, `architecture`).
- **Services (`core/services/`)**: Contains pure Python modules for system interactions, such as `system_metrics.py` which abstracts database ping tests and OS resource checks via `psutil`.

### 2. `blog` App
A blogging engine demonstrating standard Django ORM and template usage.
- **Frontend**: Utilizes **HTMX** for seamless, partial-page reloads. Pagination is handled by checking the `request.htmx` attribute (provided by `django-htmx` middleware) to return partial HTML chunks instead of full page renders.

### 3. `showcase` App
An API playground demonstrating RESTful endpoint design.
- **Views**: Exposes endpoints (`/api/showcase/*`) handling request parsing, parameter validation, and DRF `Response` formatting.
- **Services (`showcase/services/`)**: Contains the raw business logic. `algorithms.py` handles calculations, sequences, and text parsing. `content.py` manages static data generation.

### 4. `config` Directory
Contains the project-wide settings and URL routing.
- Settings are environment-aware and decoupled via `python-decouple`, split into `base.py`, `development.py`, and `production.py`.

*Note: There is an initialized `messenger_book` app directory, but its implementation was discarded and it is currently inactive.*

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
