.PHONY: all rsync deploy test clean

# Default target
all:
	@echo "A2IA Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make rsync    - Sync code to amazingland.live server"
	@echo "  make deploy   - Rsync and restart server"
	@echo "  make test     - Run test suite locally"
	@echo "  make clean    - Clean local workspace and caches"

# Rsync to production server
rsync:
	@echo "Syncing code to amazingland.live..."
	rsync -avz --delete \
		--exclude='.venv/' \
		--exclude='__pycache__/' \
		--exclude='*.pyc' \
		--exclude='.pytest_cache/' \
		--exclude='workspace/' \
		--exclude='workspaces/' \
		--exclude='.git/' \
		--exclude='*.egg-info/' \
		--exclude='.ruff_cache/' \
		--exclude='.mypy_cache/' \
		./ aaron@amazingland.live:~/a2ia/
	@echo "✅ Sync complete!"

# Deploy: rsync + restart (you'll need to restart manually for now)
deploy: rsync
	@echo "Code synced. Restart A2IA on the server:"
	@echo "  ssh aaron@amazingland.live"
	@echo "  cd ~/a2ia && .venv/bin/python -m a2ia.server --mode http --host 127.0.0.1 --port 8000"

# Run tests locally
test:
	pytest --quiet

# Clean local development artifacts
clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf workspace workspaces
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	@echo "✅ Cleaned!"
