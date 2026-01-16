.PHONY: help setup install clean test run-pipeline run-server lint format

# Default target
help:
	@echo "Electric Vehicle Analytics - Makefile Commands"
	@echo "=============================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Run complete setup (venv, install, directories)"
	@echo "  make install        - Install dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make run-pipeline   - Run ETL pipeline"
	@echo "  make run-server     - Start FastAPI server"
	@echo ""

	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-api       - Run API tests only"
	@echo "  make test-pipeline  - Run pipeline tests only"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run linting checks"
	@echo "  make format         - Format code with black"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove cache files and logs"
	@echo "  make clean-all      - Remove cache, logs, and venv"

# Setup
setup:
	@echo "Running setup script..."
	@chmod +x setup.sh
	@./setup.sh

install:
	@echo "Installing dependencies..."
	@pip install -r requirements.txt

# Running
run-pipeline:
	@echo "Running ETL pipeline..."
	@python scripts/run_pipeline.py

run-server:
	@echo "Starting FastAPI server..."
	@python scripts/run_server.py



docker-logs:
	@docker-compose logs -f

docker-restart:
	@echo "Restarting Docker services..."
	@docker-compose restart

# MongoDB
mongodb-start:
	@echo "Starting MongoDB with Docker..."
	@docker run -d --name ev_mongodb -p 27017:27017 -v mongodb_data:/data/db mongo:latest
	@echo "MongoDB started on port 27017"

mongodb-stop:
	@docker stop ev_mongodb
	@docker rm ev_mongodb

mongodb-shell:
	@docker exec -it ev_mongodb mongosh

# Testing
test:
	@echo "Running all tests..."
	@pytest -v

test-api:
	@echo "Running API tests..."
	@pytest tests/test_api.py -v

test-pipeline:
	@echo "Running pipeline tests..."
	@pytest tests/test_pipeline.py -v

test-coverage:
	@echo "Running tests with coverage..."
	@pytest --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

# Code Quality
lint:
	@echo "Running linting checks..."
	@flake8 app tests --max-line-length=100 --ignore=E501,W503 || true
	@pylint app tests --max-line-length=100 || true

format:
	@echo "Formatting code with black..."
	@black app tests scripts --line-length=100

# Cleanup
clean:
	@echo "Cleaning cache files and logs..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@rm -rf htmlcov .coverage
	@rm -rf logs/*.log
	@echo "Cleanup complete!"

clean-all: clean
	@echo "Removing virtual environment..."
	@rm -rf venv
	@echo "Full cleanup complete!"

# Development
dev-setup: setup
	@echo "Installing development dependencies..."
	@pip install black flake8 pylint pytest-cov

dev-server:
	@echo "Starting development server with auto-reload..."
	@uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database
db-reset:
	@echo "Resetting database..."
	@python -c "from app.database import db_manager; db_manager.connect(); db_manager.drop_collection('vehicles')"
	@echo "Database reset complete!"

# Frontend
frontend:
	@echo "Opening frontend dashboard..."
	@open frontend/index.html || xdg-open frontend/index.html

# Logs
logs:
	@echo "Showing application logs..."
	@tail -f logs/*.log

logs-clear:
	@echo "Clearing logs..."
	@rm -rf logs/*.log
	@echo "Logs cleared!"

# Environment
env:
	@echo "Current environment variables:"
	@cat .env 2>/dev/null || echo ".env file not found. Run 'make setup' first."

# Status
status:
	@echo "System Status:"
	@echo "=============="
	@echo -n "Python: "
	@python3 --version 2>/dev/null || echo "Not found"
	@echo -n "MongoDB: "
	@pgrep mongod >/dev/null && echo "Running" || echo "Not running"
	@echo -n "Docker: "
	@docker ps >/dev/null 2>&1 && echo "Running" || echo "Not available"
	@echo -n "Virtual Environment: "
	@[ -d "venv" ] && echo "Exists" || echo "Not created"
	@echo -n "CSV File: "
	@[ -f "data/raw/Electric_Vehicle_Population_Data.csv" ] && echo "Found" || echo "Not found"
