# Personal Homepage

[![CI](https://github.com/mkofoed/homepage/actions/workflows/ci.yml/badge.svg)](https://github.com/mkofoed/homepage/actions/workflows/ci.yml)
[![Deploy to VM](https://github.com/mkofoed/homepage/actions/workflows/deploy.yml/badge.svg)](https://github.com/mkofoed/homepage/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A personal homepage and web application built with Django.

## Tech Stack

- **Backend**: Django 6.0, Python 3.14
- **Database**: PostgreSQL 18 + TimescaleDB
- **Task Queue**: Celery + Redis
- **Frontend**: Django templates + HTMX
- **API**: Django REST Framework
- **Web Server**: Uvicorn (ASGI) + Nginx (jonasal/nginx-certbot)
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions → GHCR → Hetzner VPS
- **Dependencies**: uv

## Architecture

- **Service layer pattern**: views handle HTTP, services handle business logic
- **Docker networks**: frontend (nginx + web) / backend (web + db + redis + celery)
- **Container registry**: ghcr.io/mkofoed/homepage-web

## Local Development

```bash
cp .env.example .env
docker compose up            # http://localhost:8000
```

Optional, but it catches most CI failures before they reach a pull request:

```bash
uv sync --locked --extra dev
uv run pre-commit install
```

**Python 3.14 is a hard requirement**, not just the tested version: parts of the
codebase use PEP 758 syntax (`except ValueError, AttributeError:`), which does
not parse on 3.13 or earlier.

## CI

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `ci.yml` | pull request to `main` | Ruff, djLint, Mypy, Django checks, tests with coverage, stale-Tailwind check, production Compose validation |
| `deploy.yml` | push to `main` | Ruff, Mypy, Django checks, tests with coverage, stale-Tailwind check (no djLint or Compose validation -- see AGENTS.md), then build → push to GHCR → deploy |

`main` deploys on push, so open a pull request and let `ci.yml` go green first.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the equivalent commands to run
locally.

## Production Deployment

Push to `main` triggers automatic deployment via GitHub Actions:

1. Run Ruff, Mypy, Django deployment checks, and the automated test suite
2. Build Docker image → push to GHCR (tagged by commit SHA)
3. SCP deployment files to server (no git on server)
4. Run `deploy.sh`: safe migrations → deploy → health check → auto-rollback on failure

### Manual Rollback

```bash
ssh <server>
cd ~/homepage
./rollback.sh
```

### Services (docker-compose.prod.yml)

| Service | Image | Purpose |
|---------|-------|---------|
| web | ghcr.io/mkofoed/homepage-web | Django ASGI application + Uvicorn |
| db | timescale/timescaledb:latest-pg18 | PostgreSQL + TimescaleDB |
| redis | redis:7-alpine | Cache + Celery broker |
| celery_worker | homepage-web | Background task worker |
| celery_beat | homepage-web | Periodic task scheduler |
| nginx | jonasal/nginx-certbot:5-alpine | Reverse proxy + SSL |

### Environment Variables

See `.env.example` for required variables.

## Code Quality

Ruff (lint and format), djLint (templates), and Mypy, with pre-commit hooks
mirroring the CI gate. Inside the running container:

```bash
alias dcw='docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run'

dcw ruff check --fix .
dcw ruff format .
dcw djlint core/templates blog/templates dashboard/templates --lint
dcw mypy .
dcw python manage.py test --settings=config.settings.test
```

The full gate, and what the test settings do and do not cover, is documented in
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)