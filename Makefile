.PHONY: help build up down restart logs clean test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker containers
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-db: ## Show database logs
	docker-compose logs -f db

clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all

setup: ## Initial setup - create .env file
	@if [ ! -f backend/.env ]; then \
		echo "Creating backend/.env file..."; \
		echo "OPENAI_API_KEY=your_openai_api_key_here" > backend/.env; \
		echo "DATABASE_URL=postgresql://invoice_user:invoice_pass@db:5432/invoice_db" >> backend/.env; \
		echo "Please edit backend/.env and add your OpenAI API key"; \
	else \
		echo "backend/.env already exists"; \
	fi

test: ## Run tests (placeholder for future test suite)
	@echo "Tests not yet implemented"

db-shell: ## Access PostgreSQL shell
	docker-compose exec db psql -U invoice_user -d invoice_db

db-reset: ## Reset database (WARNING: deletes all data)
	docker-compose down -v
	docker-compose up -d db
	sleep 5
	docker-compose up -d backend frontend

