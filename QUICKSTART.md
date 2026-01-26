# Quick Start Guide

Get up and running with Textual Forms in 5 minutes!

## Installation

```bash
# Using uv (recommended)
uv pip install textual-forms

# Or using pip
pip install textual-forms
```

## Your First Form

Create a file `my_form.py`:

```python
from textual.app import App
from textual_forms import Form, StringField, IntegerField

# 1. Define your form
class UserForm(Form):
    name = StringField(label="Name", required=True)
    age = IntegerField(label="Age", min_value=0, max_value=130)

# 2. Create your app
class MyApp(App):
    def compose(self):
        yield UserForm(title="User Info").render()
    
    def on_form_submitted(self, event: Form.Submitted):
        data = event.form.get_data()
        self.notify(f"Hello, {data['name']}!")
        self.exit(data)
    
    def on_form_cancelled(self, event: Form.Cancelled):
        self.exit()

# 3. Run it!
if __name__ == "__main__":
    app = MyApp()
    result = app.run()
    print(f"You entered: {result}")
```

Run it:
```bash
python my_form.py
```

## Common Patterns

### Pre-populate a Form

```python
initial_data = {"name": "John", "age": 30}
yield UserForm(data=initial_data).render()
```

### Add Validation

```python
from textual_forms.validators import EmailValidator

class ContactForm(Form):
    email = StringField(
        label="Email",
        validators=[EmailValidator()]
    )
```

### Multi-line Text

```python
class ArticleForm(Form):
    body = TextField(label="Article Body")  # Multi-line automatically
```

### Dropdown Selection

```python
from textual_forms import ChoiceField

class PreferencesForm(Form):
    country = ChoiceField(
        label="Country",
        choices=[
            ("us", "United States"),
            ("uk", "United Kingdom"),
            ("ca", "Canada"),
        ]
    )
```

### Checkboxes

```python
from textual_forms import BooleanField

class SignupForm(Form):
    agree_terms = BooleanField(label="I agree to terms")
```

## Next Steps

- Check out the [examples/](examples/) directory for more examples
- Read the [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) for architecture details
- See [README.md](README.md) for complete documentation

## Need Help?

- Open an issue on GitHub
- Check the documentation
- Look at the example applications in `examples/`
