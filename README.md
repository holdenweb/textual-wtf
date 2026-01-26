# Textual Forms

A declarative, extensible forms library for [Textual](https://textual.textualize.io/) TUI applications.

## Features

- **Declarative Syntax**: Define forms using class-based field declarations
- **Flexible Widget Assignment**: Use different widgets for the same field type
- **Easy to Extend**: Add custom field types and widgets with clear patterns
- **Built-in Validation**: Comprehensive validation with helpful error messages
- **Simple Integration**: Drop forms into existing Textual apps with minimal code

## Installation

```bash
uv pip install -e .
```

## Quick Start

```python
from textual.app import App
from textual_forms import Form, StringField, IntegerField

class UserForm(Form):
    name = StringField(label="Name", required=True)
    age = IntegerField(label="Age", min_value=0, max_value=130)

class MyApp(App):
    def compose(self):
        yield UserForm().render()
    
    def on_form_submitted(self, event: Form.Submitted):
        data = event.form.get_data()
        self.notify(f"Hello, {data['name']}!")

if __name__ == "__main__":
    MyApp().run()
```

## Field Types

- `StringField` - Text input (single line)
- `TextField` - Text input (multi-line)
- `IntegerField` - Integer input with validation
- `BooleanField` - Checkbox
- `ChoiceField` - Select dropdown

## Running Examples

```bash
# Basic example
uv run python examples/basic_form.py

# Advanced example with custom fields
uv run python examples/advanced_form.py

# User registration form
uv run python examples/user_registration.py
```

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run specific test
uv run pytest tests/test_fields.py -v
```

## Architecture

The library uses a three-layer architecture:

1. **Fields** - Handle data conversion and validation logic
2. **Widgets** - Handle UI rendering and user interaction  
3. **Forms** - Coordinate fields and widgets into complete forms

See `REFACTORING_GUIDE.md` for detailed architecture documentation.

## License

MIT License - see LICENSE file for details.

## Choice Field Format

When using `ChoiceField`, provide choices as a list of `(value, label)` tuples:

```python
country = ChoiceField(
    label="Country",
    choices=[
        ("us", "United States"),  # value, label
        ("uk", "United Kingdom"),
        ("ca", "Canada"),
    ]
)
```

- The **value** (first element) is what gets stored in the form data
- The **label** (second element) is what the user sees in the dropdown

When the form is submitted, `form.get_data()['country']` will contain the value (e.g., `"us"`), not the label.

## Testing Your Forms

Textual widgets require an active application context to render. The library provides utility methods to test forms without rendering:

```python
# Test form structure without app context
form = UserForm()

# Get all fields
fields = form.get_fields_dict()

# Get field names in order
names = form.get_field_names()

# Get specific field
email_field = form.get_field("email")
assert email_field.required is True

# Create widgets without rendering (for basic testing)
widgets = form.create_widgets()

# Test data handling
form.set_data({"name": "John", "age": 30})
data = form.get_data()
```

For full integration tests with rendering, use Textual's testing utilities:

```python
@pytest.mark.asyncio
async def test_form():
    class TestApp(App):
        def compose(self):
            yield UserForm().render()
    
    app = TestApp()
    # Use app.run_test() for full testing
```

See `docs/TESTING_GUIDE.md` for complete testing documentation.
