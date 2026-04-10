#!/bin/bash

# Stop script on error
set -e

echo "🚀 Starting deployment..."

# Pull latest changes
echo "⬇️ Pulling latest changes..."
git reset --hard HEAD
git clean -fd -e data/ -e .env
git pull origin main

# Pull latest images
echo "🐳 Pulling latest images..."
docker compose -f docker-compose.prod.yml pull

# Start database first (web depends on it)
echo "🗄️ Starting database..."
docker compose -f docker-compose.prod.yml up -d db redis

# Wait for db to be ready
echo "⏳ Waiting for database to be ready..."
timeout 60 bash -c 'until docker compose -f docker-compose.prod.yml exec -T db pg_isready -U ${SQL_USER:-postgres}; do sleep 2; done'

# Extra wait for TimescaleDB extension initialization
echo "⏳ Waiting for TimescaleDB to finish initializing..."
sleep 10

# Stop old web/celery before migrations to avoid schema conflicts
echo "🛑 Stopping old web containers..."
docker compose -f docker-compose.prod.yml stop web celery_worker celery_beat || true

# Run migrations and collect static files BEFORE starting web
echo "🗄️ Running migrations..."
docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate

echo "🗄️ Backfilling Historical Spot Prices (first deploy only)..."
docker compose -f docker-compose.prod.yml run --rm web python manage.py backfill_spot_prices --limit 5000 || echo "⚠️  Backfill skipped (already populated or failed)"

echo "🎨 Collecting static files..."
docker compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput

# Now start all containers (web will have static files ready)
echo "🚀 Starting all containers..."
docker compose -f docker-compose.prod.yml up -d

# Smoke test
echo "🔍 Running smoke test..."
sleep 8
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/ || echo "000")
if [ "$HTTP_STATUS" != "200" ]; then
    echo "❌ Smoke test failed! HTTP status: $HTTP_STATUS"
    echo "📋 Web container logs:"
    docker compose -f docker-compose.prod.yml logs web --tail 20
    exit 1
fi
echo "✅ Smoke test passed (HTTP $HTTP_STATUS)"

# Clean up old images after successful deploy
echo "🧹 Cleaning up old images..."
docker system prune -f

echo "✅ Deployment completed successfully!"
