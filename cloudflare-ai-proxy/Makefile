.PHONY: help install dev build up down logs test clean

help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies locally"
	@echo "  dev        - Run development server"
	@echo "  build      - Build Docker image"
	@echo "  up         - Start Docker containers"
	@echo "  up-dev     - Start Docker containers in dev mode"
	@echo "  down       - Stop Docker containers"
	@echo "  logs       - View Docker logs"
	@echo "  test       - Run tests"
	@echo "  clean      - Clean up Docker resources"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

build:
	docker build -t cloudflare-ai-proxy:latest .

up:
	docker-compose up -d

up-dev:
	docker-compose -f docker-compose.dev.yml up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	@echo "Testing API endpoints..."
	@echo "Health check:"
	curl -s http://localhost:8080/health | python -m json.tool || echo "Service not running"
	@echo "\nGenerate test:"
	curl -s -X POST http://localhost:8080/v1/generate \
		-H "Content-Type: application/json" \
		-d '{"prompt": "Hello, how are you?", "max_tokens": 50}' | python -m json.tool || echo "Service not running"

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f
