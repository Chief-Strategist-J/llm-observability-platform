#!/bin/bash
set -e

echo "🧹 Cleaning Knowledge Graph Service..."

# Stop services
docker compose down -v

# Remove data
read -p "Remove all data (Neo4j database)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing data..."
    rm -rf data/neo4j/data/*
    rm -rf data/neo4j/logs/*
    rm -rf logs/*
    echo "✅ Data cleaned"
fi

echo "✅ Cleanup complete"
