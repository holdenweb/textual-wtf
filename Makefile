test:
	uv run pytest -v

clean:
	find . -name __pycache__ -exec rm -rf {} \; -prune
