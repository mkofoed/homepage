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
sleep 5

# Run migrations and collect static files BEFORE starting web
echo "🗄️ Running migrations..."
docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate

echo "🗄️ Backfilling Historical Spot Prices..."
docker compose -f docker-compose.prod.yml run --rm web python manage.py backfill_spot_prices --limit 5000

echo "🎨 Collecting static files..."
docker compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput

# Now start all containers (web will have static files ready)
echo "🚀 Starting all containers..."
docker compose -f docker-compose.prod.yml up -d

echo "✅ Deployment completed successfully!"
