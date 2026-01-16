.PHONY: help dev-up dev-down dev-logs dev-build dev-restart dev-clean \
        prod-up prod-down prod-logs prod-build prod-restart prod-clean \
        dev-shell-api dev-shell-frontend dev-shell-db \
        prod-shell-api prod-shell-frontend prod-shell-db \
        clean-all docker-prune fix-build

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ Development Environment

dev-up: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(NC)"
	@echo "$(YELLOW)Backend API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/docs$(NC)"

dev-down: ## Stop development environment
	@echo "$(BLUE)Stopping development environment...$(NC)"
	docker-compose down
	@echo "$(GREEN)Development environment stopped!$(NC)"

dev-logs: ## View development environment logs (use LOGS=service to view specific service)
	@if [ -z "$(LOGS)" ]; then \
		docker-compose logs -f; \
	else \
		docker-compose logs -f $(LOGS); \
	fi

dev-build: ## Build development environment images
	@echo "$(BLUE)Building development environment images...$(NC)"
	docker-compose build
	@echo "$(GREEN)Development images built!$(NC)"

dev-restart: ## Restart development environment
	@echo "$(BLUE)Restarting development environment...$(NC)"
	docker-compose restart
	@echo "$(GREEN)Development environment restarted!$(NC)"

dev-clean: ## Stop and remove development containers, networks, and volumes
	@echo "$(YELLOW)WARNING: This will delete all development data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "$(GREEN)Development environment cleaned!$(NC)"; \
	else \
		echo "$(RED)Cancelled.$(NC)"; \
	fi

dev-shell-api: ## Open shell in development API container
	docker-compose exec api bash

dev-shell-frontend: ## Open shell in development frontend container
	docker-compose exec frontend sh

dev-shell-db: ## Open PostgreSQL shell in development database
	docker-compose exec postgres psql -U postgres -d yuyang_db

dev-ps: ## Show development environment container status
	docker-compose ps

##@ Production Environment

prod-up: ## Start production environment
	@echo "$(BLUE)Starting production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)Production environment started!$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:80$(NC)"
	@echo "$(YELLOW)Backend API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/docs$(NC)"

prod-down: ## Stop production environment
	@echo "$(BLUE)Stopping production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml down
	@echo "$(GREEN)Production environment stopped!$(NC)"

prod-logs: ## View production environment logs (use LOGS=service to view specific service)
	@if [ -z "$(LOGS)" ]; then \
		docker-compose -f docker-compose.prod.yml logs -f; \
	else \
		docker-compose -f docker-compose.prod.yml logs -f $(LOGS); \
	fi

prod-build: ## Build production environment images
	@echo "$(BLUE)Building production environment images...$(NC)"
	docker-compose -f docker-compose.prod.yml build
	@echo "$(GREEN)Production images built!$(NC)"

prod-restart: ## Restart production environment
	@echo "$(BLUE)Restarting production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml restart
	@echo "$(GREEN)Production environment restarted!$(NC)"

prod-clean: ## Stop and remove production containers, networks, and volumes
	@echo "$(YELLOW)WARNING: This will delete all production data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f docker-compose.prod.yml down -v; \
		echo "$(GREEN)Production environment cleaned!$(NC)"; \
	else \
		echo "$(RED)Cancelled.$(NC)"; \
	fi

prod-shell-api: ## Open shell in production API container
	docker-compose -f docker-compose.prod.yml exec api bash

prod-shell-frontend: ## Open shell in production frontend container
	docker-compose -f docker-compose.prod.yml exec frontend sh

prod-shell-db: ## Open PostgreSQL shell in production database
	docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d yuyang_db

prod-ps: ## Show production environment container status
	docker-compose -f docker-compose.prod.yml ps

##@ Common Operations

help: ## Display this help message
	@echo "$(BLUE)Available commands:$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(BLUE)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)Examples:$(NC)"
	@echo "  make dev-up              # Start development environment"
	@echo "  make dev-logs LOGS=api  # View API logs in development"
	@echo "  make prod-up            # Start production environment"
	@echo "  make fix-build          # Fix Docker build cache issues"
	@echo "  make clean-all          # Clean everything"

clean-all: ## Stop and remove all containers, networks, and volumes (both dev and prod)
	@echo "$(RED)WARNING: This will delete ALL data from both environments!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v 2>/dev/null || true; \
		docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true; \
		echo "$(GREEN)All environments cleaned!$(NC)"; \
	else \
		echo "$(RED)Cancelled.$(NC)"; \
	fi

status: ## Show status of all environments
	@echo "$(BLUE)Development Environment:$(NC)"
	@docker-compose ps 2>/dev/null || echo "$(YELLOW)Not running$(NC)"
	@echo ""
	@echo "$(BLUE)Production Environment:$(NC)"
	@docker-compose -f docker-compose.prod.yml ps 2>/dev/null || echo "$(YELLOW)Not running$(NC)"

rebuild-dev: ## Rebuild and restart development environment
	@echo "$(BLUE)Rebuilding development environment...$(NC)"
	docker-compose down
	docker-compose build --no-cache --pull
	docker-compose up -d
	@echo "$(GREEN)Development environment rebuilt and started!$(NC)"

rebuild-prod: ## Rebuild and restart production environment
	@echo "$(BLUE)Rebuilding production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml down
	docker-compose -f docker-compose.prod.yml build --no-cache --pull
	docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)Production environment rebuilt and started!$(NC)"
