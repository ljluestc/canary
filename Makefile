# Makefile for Comprehensive System Management

.PHONY: help install test test-coverage lint format security-scan build deploy clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install         - Install all dependencies"
	@echo "  test            - Run all tests"
	@echo "  test-coverage   - Run tests with coverage"
	@echo "  lint            - Run linting on all code"
	@echo "  format          - Format all code"
	@echo "  security-scan   - Run security scans"
	@echo "  build           - Build all Docker images"
	@echo "  deploy          - Deploy to Kubernetes"
	@echo "  clean           - Clean up temporary files"

# Variables
PYTHON := python3
PIP := pip3
DOCKER := docker
KUBECTL := kubectl
TERRAFORM := terraform

# System directories
SYSTEMS := task-manager task-master systems/tinyurl systems/newsfeed systems/google-docs

# Install dependencies
install:
	@echo "Installing system dependencies..."
	sudo apt-get update
	sudo apt-get install -y python3 python3-pip python3-venv sqlite3 redis-server curl
	@echo "Installing Python dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install pytest pytest-cov coverage flake8 black bandit safety
	@echo "Installing system-specific dependencies..."
	@for system in $(SYSTEMS); do \
		if [ -f $$system/requirements.txt ]; then \
			echo "Installing dependencies for $$system..."; \
			$(PIP) install -r $$system/requirements.txt; \
		fi; \
	done

# Run all tests
test:
	@echo "Running comprehensive tests..."
	$(PYTHON) run_comprehensive_tests.py

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage..."
	@for system in $(SYSTEMS); do \
		if [ -d $$system ]; then \
			echo "Testing $$system..."; \
			cd $$system && $(PYTHON) -m pytest test_*.py -v --cov=. --cov-report=html --cov-report=xml; \
			cd ..; \
		fi; \
	done

# Run linting
lint:
	@echo "Running linting..."
	@for system in $(SYSTEMS); do \
		if [ -d $$system ]; then \
			echo "Linting $$system..."; \
			cd $$system && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; \
			cd ..; \
		fi; \
	done

# Format code
format:
	@echo "Formatting code..."
	@for system in $(SYSTEMS); do \
		if [ -d $$system ]; then \
			echo "Formatting $$system..."; \
			cd $$system && black .; \
			cd ..; \
		fi; \
	done

# Security scan
security-scan:
	@echo "Running security scans..."
	bandit -r . -f json -o bandit-report.json
	safety check --json --output safety-report.json
	@echo "Security scan completed. Check bandit-report.json and safety-report.json"

# Build Docker images
build:
	@echo "Building Docker images..."
	@for system in systems/*; do \
		if [ -f $$system/Dockerfile ]; then \
			echo "Building $$system..."; \
			$(DOCKER) build -t $$(basename $$system)-service:latest $$system/; \
		fi; \
	done

# Deploy to Kubernetes
deploy:
	@echo "Deploying to Kubernetes..."
	$(KUBECTL) apply -f k8s/
	@echo "Waiting for deployments to be ready..."
	$(KUBECTL) wait --for=condition=available --timeout=300s deployment/tinyurl-service
	$(KUBECTL) wait --for=condition=available --timeout=300s deployment/newsfeed-service
	$(KUBECTL) wait --for=condition=available --timeout=300s deployment/google-docs-service
	@echo "Deployment completed!"

# Setup infrastructure
setup-infrastructure:
	@echo "Setting up infrastructure..."
	cd terraform && $(TERRAFORM) init
	cd terraform && $(TERRAFORM) plan
	cd terraform && $(TERRAFORM) apply -auto-approve
	@echo "Infrastructure setup completed!"

# Start services locally
start-services:
	@echo "Starting services locally..."
	@echo "Starting Redis..."
	sudo systemctl start redis-server
	@echo "Starting TinyURL service on port 5000..."
	cd systems/tinyurl && $(PYTHON) tinyurl_service.py &
	@echo "Starting Newsfeed service on port 5001..."
	cd systems/newsfeed && $(PYTHON) newsfeed_service.py &
	@echo "Starting Google Docs service on port 5002..."
	cd systems/google-docs && $(PYTHON) google_docs_service.py &
	@echo "All services started!"

# Stop services
stop-services:
	@echo "Stopping services..."
	pkill -f tinyurl_service.py || true
	pkill -f newsfeed_service.py || true
	pkill -f google_docs_service.py || true
	sudo systemctl stop redis-server || true
	@echo "All services stopped!"

# Run integration tests
integration-test:
	@echo "Running integration tests..."
	$(PYTHON) -m pytest integration_tests/ -v

# Performance test
performance-test:
	@echo "Running performance tests..."
	$(PYTHON) run_comprehensive_tests.py --performance-only

# Generate documentation
docs:
	@echo "Generating documentation..."
	@for system in $(SYSTEMS); do \
		if [ -d $$system ]; then \
			echo "Generating docs for $$system..."; \
			cd $$system && $(PYTHON) -m pydoc -w .; \
			cd ..; \
		fi; \
	done

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	find . -type f -name "*.db" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} + || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + || true
	@echo "Cleanup completed!"

# Full CI pipeline
ci: install lint test-coverage security-scan build
	@echo "CI pipeline completed!"

# Full CD pipeline
cd: build deploy
	@echo "CD pipeline completed!"

# Development setup
dev-setup: install start-services
	@echo "Development environment ready!"
	@echo "Services available at:"
	@echo "  TinyURL: http://localhost:5000"
	@echo "  Newsfeed: http://localhost:5001"
	@echo "  Google Docs: http://localhost:5002"

# Production deployment
prod-deploy: ci cd
	@echo "Production deployment completed!"

# Health check
health-check:
	@echo "Checking service health..."
	@echo "TinyURL service:"
	curl -f http://localhost:5000/ || echo "TinyURL service not responding"
	@echo "Newsfeed service:"
	curl -f http://localhost:5001/ || echo "Newsfeed service not responding"
	@echo "Google Docs service:"
	curl -f http://localhost:5002/ || echo "Google Docs service not responding"

# Backup data
backup:
	@echo "Backing up data..."
	mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	@for system in $(SYSTEMS); do \
		if [ -f $$system/*.db ]; then \
			cp $$system/*.db backups/$(shell date +%Y%m%d_%H%M%S)/; \
		fi; \
	done
	@echo "Backup completed!"

# Restore data
restore:
	@echo "Available backups:"
	ls -la backups/
	@echo "Usage: make restore BACKUP_DIR=backups/YYYYMMDD_HHMMSS"

# Monitor logs
logs:
	@echo "Monitoring service logs..."
	tail -f systems/tinyurl/*.log systems/newsfeed/*.log systems/google-docs/*.log 2>/dev/null || echo "No log files found"

# Scale services
scale:
	@echo "Scaling services..."
	$(KUBECTL) scale deployment tinyurl-service --replicas=5
	$(KUBECTL) scale deployment newsfeed-service --replicas=3
	$(KUBECTL) scale deployment google-docs-service --replicas=2
	@echo "Scaling completed!"

# Rollback deployment
rollback:
	@echo "Rolling back deployment..."
	$(KUBECTL) rollout undo deployment/tinyurl-service
	$(KUBECTL) rollout undo deployment/newsfeed-service
	$(KUBECTL) rollout undo deployment/google-docs-service
	@echo "Rollback completed!"