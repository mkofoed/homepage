# Personal Homepage

[![Deploy to VM](https://github.com/mkofoed/homepage/actions/workflows/deploy.yml/badge.svg)](https://github.com/mkofoed/homepage/actions/workflows/deploy.yml)

A personal homepage and web application built with Django.

## Tech Stack

- **Backend**: Django 6.0, Python 3.14
- **Database**: PostgreSQL 18 + TimescaleDB
- **Task Queue**: Celery + Redis
- **Frontend**: Django templates + HTMX
- **API**: Django REST Framework
- **Web Server**: Gunicorn + Nginx (jonasal/nginx-certbot)
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
docker compose up
```

## Production Deployment

Push to `main` triggers automatic deployment via GitHub Actions:

1. Build Docker image → push to GHCR (tagged by commit SHA)
2. SCP deployment files to server (no git on server)
3. Run `deploy.sh`: safe migrations → deploy → health check → auto-rollback on failure

### Manual Rollback

```bash
ssh <server>
cd ~/homepage
./rollback.sh
```

### Services (docker-compose.prod.yml)

| Service | Image | Purpose |
|---------|-------|---------|
| web | ghcr.io/mkofoed/homepage-web | Django + Gunicorn |
| db | timescale/timescaledb:latest-pg18 | PostgreSQL + TimescaleDB |
| redis | redis:7-alpine | Cache + Celery broker |
| celery_worker | homepage-web | Background task worker |
| celery_beat | homepage-web | Periodic task scheduler |
| nginx | jonasal/nginx-certbot:5-alpine | Reverse proxy + SSL |

### Environment Variables

See `.env.example` for required variables.

## Code Quality

```bash
uv run ruff check --fix .
uv run ruff format .
uv run mypy .
```