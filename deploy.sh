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

# Start containers
echo "🚀 Starting containers..."
docker compose -f docker-compose.prod.yml up -d

# Run migrations
echo "🗄️ Running migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Collect static files
echo "🎨 Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo "✅ Deployment completed successfully!"
