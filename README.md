# Textual Forms

A declarative, extensible forms library for [Textual](https://textual.textualize.io/) TUI applications.

## Features/Goals

- **Declarative Syntax**: Define forms using class-based field declarations
- **Flexible Widget Assignment**: Use different widgets for the same field type
- **Easy to Extend**: Add custom field types and widgets with clear patterns
- **Built-in Validation**: Uses standard textual validators
- **Simple Integration**: Drop forms into existing Textual apps with minimal code

## Installation

The package will be released to PyPI at release 0.8, at the time of writing in early alpha.
Until then, install from this repository as follows.

```bash
python -m pip install textual_forms@git+https://github.com/holdenweb/textual-forms.git
```

`uv` users can use

```bash
uv add textual_forms@git+https://github.com/holdenweb/textual-forms.git
```

## Quick Start

Here's the most basic example.

    """Basic form example with results display"""
    from textual.app import App, ComposeResult
    from textual.containers import Container, Vertical, Center
    from textual.widgets import Static, Button
    from textual_forms import Form, StringField, IntegerField, BooleanField
    from results_screen import ResultsDisplayScreen

    class UserForm(Form):
        """Simple user registration form"""
        name = StringField(label="Name", required=True)
        age = IntegerField(label="Age", min_value=0, max_value=130)
        active = BooleanField(label="Active User")


    class ResultScreen(ResultsDisplayScreen):
        """Utility Screen to display form results"""

        def compose(self) -> ComposeResult:
            with Container(id="results-container"):
                yield Static(self.result_title, id="results-title")

                yield from self.show_data()

                with Center(id="buttons"):
                    yield Button("New Form", variant="primary", id="new")
                    yield Button("Exit", id="exit")


    class BasicFormApp(App):
        """Demo app for basic form"""

        CSS_PATH = "basic_form.tcss"

        def compose(self) -> ComposeResult:
            self.form = UserForm(title="User Registration")
            yield self.form.render()

        def on_form_submitted(self, event: Form.Submitted):
            """Handle form submission"""
            data = event.form.get_data()
            # Show results screen
            def check_reset(should_reset):
                if should_reset:
                    self.reset_form()

            self.push_screen(ResultScreen("Form Submitted Successfully!", data), check_reset)

        def on_form_cancelled(self, event: Form.Cancelled):
            """Handle form cancellation"""
            # Show cancellation screen
            def check_reset(should_reset):
                if should_reset:
                    self.reset_form()

            self.push_screen(ResultScreen("Form Cancelled", None), check_reset)

        def reset_form(self):
            """Clear form and create fresh one"""
            # Remove old form
            old_form = self.query_one("RenderedForm")
            old_form.remove()

            # Create and mount new form
            self.form = UserForm(title="User Registration")
            self.mount(self.form.render())

        def on_click(self):
            self.app.log(self.css_tree)
            self.app.log(self.tree)


    if __name__ == "__main__":
        BasicFormApp().run()


## Current Field Types

- `StringField` - Text input (single line)
- `TextField` - Text input (multi-line)
- `IntegerField` - Integer input with validation
- `BooleanField` - Checkbox
- `ChoiceField` - Select dropdown

## Running Examples

If you have `uv` installed you can run the examples from the repository using the command

`uvx --from git+https://github.com/holdenweb/textual-forms.git python examples/<name>`

where `<name>` is taken from the following table.

| name                                | Description                                      |
|:------------------------------------|:-------------------------------------------------|
| `basic_form.py`                     | A simple form with basic fields                  |
| `advanced_form.py`                  | A more complex form with validations             |
| `user_registration.py`              | Form integrated with other components            |
| `nested_once_form.py`               | Simple nested form demonstration                 |
| `nested_twice_form.py`              | Demonstrating form component re-use              |

From within a clone of the repository the command `uv run examples/<name>` will suffice

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

## Older versions

The prehistory of the project is preserved in the `prototype` branch, which
represented a somewhat chaotic mishmash of code but proved the basic ideas
to be usable in practice.
