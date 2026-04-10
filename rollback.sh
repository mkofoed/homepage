#!/bin/bash

set -euo pipefail

PREVIOUS_TAG_FILE="$HOME/.homepage_previous_tag"

if [ ! -f "$PREVIOUS_TAG_FILE" ]; then
    echo "❌ No previous deployment tag found. Manual intervention required."
    exit 1
fi

PREVIOUS_TAG=$(cat "$PREVIOUS_TAG_FILE")
echo "⏪ Rolling back to image tag: $PREVIOUS_TAG"

export IMAGE_TAG="$PREVIOUS_TAG"
cd "$(dirname "$0")"

docker compose -f docker-compose.prod.yml pull web
docker compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for rollback health check..."
for i in $(seq 1 30); do
  if curl -sf http://localhost/health/ > /dev/null 2>&1; then
    echo "✅ Rollback successful. Running tag: $PREVIOUS_TAG"
    exit 0
  fi
  sleep 2
done

echo "❌ Rollback health check failed! Manual intervention required."
exit 1
