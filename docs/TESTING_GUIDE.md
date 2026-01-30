# Testing Guide - Using Textual's run_test()

## Overview

Textual provides `run_test()` for headless testing of TUI applications. This allows you to test widget creation, rendering, and interaction without a terminal.

## Two Types of Tests

### 1. Tests Without App Context (Fast)

Test field logic, validators, and form structure without creating widgets:

```python
def test_field_configuration():
    """Test without app context"""
    form = UserForm()

    # Inspect structure
    assert "email" in form.get_field_names()

    # Check configuration
    field = form.get_field("email")
    assert field.required is True

    # Test field logic
    assert field.to_python("  test@example.com  ") == "test@example.com"
```

### 2. Tests With App Context (Complete)

Test rendering and widget behavior using `run_test()`:

```python
@pytest.mark.asyncio
async def test_form_rendering():
    """Test with app context using run_test()"""

    class TestApp(App):
        def compose(self):
            yield UserForm().render()

    app = TestApp()
    async with app.run_test() as pilot:
        # Now you have full app context
        # Widgets are created and mounted
        assert app.screen is not None
```

## Complete Examples

### Testing Widget Creation

```python
import pytest
from textual.app import App
from textual_wtf.widgets import FormInput

@pytest.mark.asyncio
async def test_widget_creation():
    """Test widget with app context"""

    class TestApp(App):
        def compose(self):
            yield FormInput()

    app = TestApp()
    async with app.run_test() as pilot:
        # Widget created successfully
        assert True
```

### Testing Form Rendering

```python
@pytest.mark.asyncio
async def test_form_with_data():
    """Test form with initial data"""

    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.form = None

        def compose(self):
            self.form = UserForm(data={"name": "John", "age": 30})
            yield self.form.render()

    app = TestApp()
    async with app.run_test() as pilot:
        # Check form data
        data = app.form.get_data()
        assert data["name"] == "John"
        assert data["age"] == 30
```

### Testing User Interaction

```python
@pytest.mark.asyncio
async def test_user_input():
    """Test simulating user input"""

    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.form = None

        def compose(self):
            self.form = UserForm()
            yield self.form.render()

    app = TestApp()
    async with app.run_test() as pilot:
        # Simulate user typing into input
        # (Textual's pilot provides methods for this)
        # See Textual docs for full pilot API
        pass
```

## Required Setup

### Install pytest-asyncio

```bash
uv pip install -e ".[dev]"
```

### Configure pytest

In `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## Running Tests

```bash
# Run all tests
pytest

# Run only async tests
pytest -k "asyncio"

# Run only non-async tests
pytest -k "not asyncio"

# Verbose output
pytest -v

# With coverage
pytest --cov
```

## Best Practices

### ✓ DO:
- Use `run_test()` for widget/rendering tests
- Test field logic without app context (faster)
- Mark async tests with `@pytest.mark.asyncio`
- Create minimal test apps
- Store form reference in app for access

### ✗ DON'T:
- Try to create widgets outside `run_test()`
- Mix sync and async in same test
- Make test apps too complex
- Forget to mark async tests

## Common Patterns

### Pattern 1: Test Form Structure (No App)

```python
def test_form_structure():
    form = UserForm()
    assert len(form.get_field_names()) == 3
    assert form.get_field("email").required is True
```

### Pattern 2: Test Widget Creation (With App)

```python
@pytest.mark.asyncio
async def test_widgets():
    class TestApp(App):
        def compose(self):
            yield UserForm().render()

    async with TestApp().run_test():
        pass  # Widgets created successfully
```

### Pattern 3: Test Data Flow (With App)

```python
@pytest.mark.asyncio
async def test_data():
    class TestApp(App):
        def __init__(self):
            super().__init__()
            self.form = UserForm(data={"name": "Test"})

        def compose(self):
            yield self.form.render()

    app = TestApp()
    async with app.run_test():
        assert app.form.get_data()["name"] == "Test"
```

## Troubleshooting

### Error: "Unknown pytest.mark.asyncio"

Install pytest-asyncio:
```bash
uv pip install pytest-asyncio
```

### Error: "NoActiveAppError"

You're trying to create widgets outside `run_test()`. Wrap in test app:

```python
# Wrong
def test():
    widget = FormInput()  # Error!

# Right
@pytest.mark.asyncio
async def test():
    class TestApp(App):
        def compose(self):
            yield FormInput()

    async with TestApp().run_test():
        pass
```

### Error: "async def functions are not natively supported"

Add `asyncio_mode = "auto"` to pytest config in `pyproject.toml`.

## Summary

- **Fast tests**: Test fields/validators without app context
- **Complete tests**: Use `run_test()` for rendering and widgets
- **Mark async tests**: Use `@pytest.mark.asyncio`
- **Access form**: Store reference in app instance
- **Run headless**: `run_test()` doesn't need a terminal

See test files for complete examples!
