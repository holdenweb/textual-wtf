# Installation and Setup Guide

## Prerequisites

- Python 3.10 or higher
- uv package manager (recommended) or pip

## Installation

### Option 1: Using uv (Recommended)

```bash
# Install the package in development mode
uv pip install -e ".[dev]"

# Or install from PyPI (when published)
uv pip install textual-forms
```

### Option 2: Using pip

```bash
# Install in development mode
pip install -e ".[dev]"

# Or from PyPI (when published)
pip install textual-forms
```

## Quick Start

After installation, you can run the examples:

```bash
# Basic form example
python examples/basic_form.py

# Advanced form with validation
python examples/advanced_form.py

# User registration form
python examples/user_registration.py
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_fields.py -v

# Run specific test
pytest tests/test_fields.py::TestStringField::test_creation -v
```

## Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd textual-forms

# Create virtual environment
uv venv

# Activate virtual environment (optional with uv)
source .venv/bin/activate

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Check coverage
pytest --cov --cov-report=html
open htmlcov/index.html
```

## Package Structure

```
textual-forms/
├── src/textual_forms/     # Main package
│   ├── __init__.py        # Public API
│   ├── exceptions.py      # Custom exceptions
│   ├── validators.py      # Validation classes  
│   ├── fields.py          # Field implementations
│   ├── widgets.py         # Widget implementations
│   └── forms.py           # Form metaclass and base
├── tests/                 # Test suite
├── examples/              # Example applications
├── pyproject.toml         # Package configuration
├── README.md              # Overview
├── LICENSE                # MIT License
└── REFACTORING_GUIDE.md   # Architecture documentation
```

## Troubleshooting

### Import Error: No module named 'textual'

```bash
# Install textual
uv pip install textual
```

### Import Error: No module named 'textual_forms'

Make sure you've installed the package:
```bash
uv pip install -e .
```

### Tests failing

Ensure you have dev dependencies installed:
```bash
uv pip install -e ".[dev]"
```

## Next Steps

1. Read the [README.md](README.md) for usage examples
2. Check [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) for architecture details
3. Explore the examples in the `examples/` directory
4. Read the API documentation (coming soon)
