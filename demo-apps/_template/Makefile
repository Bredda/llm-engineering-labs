.PHONY: install dev dev-api dev-ui build clean

# ── Setup ──────────────────────────────────────────────────────────────────────
install:
	@echo "→ Installing api dependencies..."
	cd api && uv venv .venv && uv sync
	@echo "→ Installing ui dependencies..."
	cd ui && pnpm install
	@echo "✓ Done. Copy api/.env.example to api/.env and add your OPENAI_API_KEY"

# ── Dev (runs both in parallel) ────────────────────────────────────────────────
dev:
	@make -j2 dev-api dev-ui

dev-api:
	cd api && uv run uvicorn template_api.main:app --reload --port 8000 2>&1 \
		| while IFS= read -r line; do printf '\033[34m[api]\033[0m %s\n' "$$line"; done

dev-ui:
	cd ui && npm run dev 2>&1 \
		| while IFS= read -r line; do printf '\033[32m[ui] \033[0m %s\n' "$$line"; done

# ── Docker build ───────────────────────────────────────────────────────────────
build:
	docker build -t $(shell basename $(CURDIR)) .
	@echo "✓ Image built: $(shell basename $(CURDIR))"
	@echo "  Run: docker run -e OPENAI_API_KEY=sk-... -p 8000:8000 $(shell basename $(CURDIR))"

# ── Cleanup ────────────────────────────────────────────────────────────────────
clean:
	rm -f api/checkpoints.sqlite
	@echo "✓ SQLite checkpoint cleared"