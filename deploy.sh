#!/bin/bash

# Stop script on error
set -e

echo "🚀 Starting deployment..."

# Pull latest changes
echo "⬇️ Pulling latest changes..."
git pull origin main
docker system prune -f

# Build and start containers
echo "🐳 Building and starting containers..."
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations
echo "🗄️ Running migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Collect static files
echo "🎨 Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo "✅ Deployment completed successfully!"
