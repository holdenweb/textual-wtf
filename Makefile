# Makefile for textual-wtf documentation and development tasks.
# Uses uv for environment management.

UV      := uv
MKDOCS  := $(UV) run mkdocs

.PHONY: help docs-install docs-serve docs-build docs-deploy docs-clean \
        test lint clean

# ── Help ────────────────────────────────────────────────────────────────────

help:  ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} \
	     /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ── Documentation ────────────────────────────────────────────────────────────

docs-install:  ## Install documentation dependencies into the uv environment
	$(UV) add --group docs \
		mkdocs-material \
		"mkdocstrings[python]" \
		mkdocs-autorefs

docs-serve:  ## Serve documentation locally with live reload (http://127.0.0.1:8000)
	$(MKDOCS) serve

docs-build:  ## Build documentation to site/
	$(MKDOCS) build --strict

docs-deploy:  ## Deploy documentation to GitHub Pages
	$(MKDOCS) gh-deploy --force

docs-clean:  ## Remove the built docs site/
	rm -rf site/

# ── Development ──────────────────────────────────────────────────────────────

test:  ## Run the test suite
	$(UV) run pytest -v

lint:  ## Run ruff linter
	$(UV) run ruff check src/ tests/

# ── Housekeeping ─────────────────────────────────────────────────────────────

clean: docs-clean  ## Remove all build artefacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ dist/ build/
