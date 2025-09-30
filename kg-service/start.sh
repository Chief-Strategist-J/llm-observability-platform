#!/bin/bash
set -e

echo "🚀 Starting Knowledge Graph Service..."
# docker stop $(docker ps -aq) 2>/dev/null || true && \
# docker system prune -af --volumes
# Stop any existing containers
docker compose down 2>/dev/null || true

# Create necessary directories
mkdir -p data/neo4j/data data/neo4j/logs logs

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
fi

# Build and start services
echo "🔨 Building containers..."
docker compose build

echo "🚢 Starting services..."
docker compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Wait for Neo4j
echo "Waiting for Neo4j..."
for i in {1..30}; do
    if docker compose exec -T neo4j cypher-shell -u neo4j -p changeme123 "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Wait for API
echo "Waiting for API..."
for i in {1..30}; do
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo ""
echo "✅ Knowledge Graph Service is running!"
echo ""
echo "📊 Neo4j Browser: http://localhost:7474"
echo "   Username: neo4j"
echo "   Password: changeme123"
echo ""
echo "📡 API Documentation: http://localhost:8002/docs"
echo "🏥 Health Check: http://localhost:8002/health"
echo ""
echo "📋 View logs: docker compose logs -f kg-api"
echo "🛑 Stop services: ./stop.sh"
