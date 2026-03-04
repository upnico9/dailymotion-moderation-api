#!/bin/bash
set -e

echo "=== Building and starting services ==="
docker-compose up --build -d

echo ""
echo "=== Waiting for services to be ready ==="
echo "Waiting for postgres..."
docker-compose exec -T postgres sh -c 'until pg_isready -U moderation -d moderation_db; do sleep 1; done'

echo "Waiting for moderation_queue..."
until docker-compose exec -T moderation_queue python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" 2>/dev/null; do
  sleep 1
done
echo "moderation_queue is ready"

echo "Waiting for dailymotion_proxy..."
until docker-compose exec -T dailymotion_proxy python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" 2>/dev/null; do
  sleep 1
done
echo "dailymotion_proxy is ready"

echo ""
echo "=== Running moderation_queue tests ==="
docker-compose exec -T moderation_queue pytest tests/ -v

echo ""
echo "=== Running dailymotion_proxy tests ==="
docker-compose exec -T dailymotion_proxy pytest tests/ -v

echo ""
echo "=== All tests passed ==="
