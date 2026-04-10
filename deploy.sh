#!/bin/bash

set -euo pipefail

if [ -f .env ]; then
    # Export only the vars we need, safely handling special characters
    export POSTGRES_USER=$(grep -E '^POSTGRES_USER=' .env | head -1 | cut -d'=' -f2-)
    export POSTGRES_DB=$(grep -E '^POSTGRES_DB=' .env | head -1 | cut -d'=' -f2-)
    export REDIS_PASSWORD=$(grep -E '^REDIS_PASSWORD=' .env | head -1 | cut -d'=' -f2-)
fi

IMAGE_TAG="${IMAGE_TAG:-${1:-latest}}"
export IMAGE_TAG

PREVIOUS_TAG_FILE="$HOME/.homepage_previous_tag"

# Logging helper
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1"
}

log "🚀 Starting deployment..."

log "📦 Ensuring database and Redis are running..."
docker compose -f docker-compose.prod.yml up -d db redis

log "⏳ Waiting for database to be ready..."
for i in $(seq 1 30); do
  if docker compose -f docker-compose.prod.yml exec -T db pg_isready -U ${POSTGRES_USER:-homepage_app} -d ${POSTGRES_DB:-homepage} > /dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 30 ]; then
    log "❌ Database not ready after 60s"
    exit 1
  fi
  sleep 2
done

log "🔧 Ensuring TimescaleDB extension exists..."
docker compose -f docker-compose.prod.yml exec -T db psql -U ${POSTGRES_USER:-homepage_app} -d ${POSTGRES_DB:-homepage} -c "CREATE EXTENSION IF NOT EXISTS timescaledb;" || true

# Save the current tag for rollback
PREVIOUS_TAG=$(docker compose -f docker-compose.prod.yml ps --format '{{.Image}}' | grep web | sed 's/.*://')
if [ -n "$PREVIOUS_TAG" ]; then
    echo "$PREVIOUS_TAG" > "$PREVIOUS_TAG_FILE"
    log "🔖 Previous tag saved: $PREVIOUS_TAG"
else
    log "⚠️  No previous tag found. This could be the first deployment."
fi

log "🐋 Pulling new image: $IMAGE_TAG"
docker compose -f docker-compose.prod.yml pull web

log "📂 Running migrations..."
if ! docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate; then
    log "❌ Migration failed. Aborting deployment to avoid downtime."
    exit 1
fi

log "🎨 Collecting static files..."
docker compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput

log "🚀 Deploying containers..."
docker compose -f docker-compose.prod.yml up -d

log "⏳ Waiting for containers to pass health check..."
for i in $(seq 1 30); do
    if curl -sf http://localhost/health/ > /dev/null 2>&1; then
        log "✅ Health check passed. Deployment successful!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        log "❌ Health check failed after 60s. Rolling back..."
        bash "$(dirname "$0")/rollback.sh"
        exit 1
    fi
    sleep 2
done

log "🧹 Cleaning up unused Docker images..."
docker image prune -f --filter "until=168h"

log "✅ Deployment completed successfully!"
