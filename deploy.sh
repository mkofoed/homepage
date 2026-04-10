#!/bin/bash

# Stop script on error
set -e

echo "🚀 Starting deployment..."

# Pull latest changes
echo "⬇️ Pulling latest changes..."
git reset --hard HEAD
git clean -fd -e data/
git pull origin main
docker system prune -f

# Pull latest images
echo "🐳 Pulling latest images..."
docker compose -f docker-compose.prod.yml pull

# Start database first (web depends on it)
echo "🗄️ Starting database..."
docker compose -f docker-compose.prod.yml up -d db

# Wait for db to be ready
echo "⏳ Waiting for database to be ready..."
timeout 60 bash -c 'until docker compose -f docker-compose.prod.yml exec -T db pg_isready -U ${SQL_USER:-postgres}; do sleep 2; done'

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

echo "✅ Deployment completed successfully!"
