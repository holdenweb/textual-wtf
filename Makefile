.PHONY = test coverage release

test:
	uv run pytest -v
coverage:
	uv run pytest --cov src/textual_forms

