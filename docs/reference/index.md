# API Reference

Complete API documentation for every public class, method, and attribute in textual-wtf.

## Sections

| Page | Contents |
|---|---|
| [Forms](forms.md) | `BaseForm`, `Form` — form declaration, validation, data access |
| [Fields](fields.md) | `Field`, `StringField`, `IntegerField`, `BooleanField`, `ChoiceField`, `TextField` |
| [Validators](validators.md) | `Validator`, `Required`, `MinLength`, `MaxLength`, `MinValue`, `MaxValue`, `EmailValidator`, `FunctionValidator` |
| [Layouts](layouts.md) | `FormLayout`, `ControllerAwareLayout`, `DefaultFormLayout` |
| [TabbedForm](tabbed_form.md) | `TabbedForm` |
| [Exceptions](exceptions.md) | `ValidationError`, `FieldError`, `FormError`, `AmbiguousFieldError` |

## Quick import reference

Everything public is available from the top-level `textual_wtf` package:

```python
from textual_wtf import (
    # Forms
    Form,
    BaseForm,
    TabbedForm,

    # Fields
    StringField,
    IntegerField,
    BooleanField,
    ChoiceField,
    TextField,

    # Validators
    Validator,
    Required,
    MinLength,
    MaxLength,
    MinValue,
    MaxValue,
    EmailValidator,
    FunctionValidator,

    # Layouts
    FormLayout,
    ControllerAwareLayout,
    DefaultFormLayout,

    # Runtime types
    BoundField,
    FieldController,
    FieldWidget,

    # Exceptions
    ValidationError,
    FieldError,
    FormError,
    AmbiguousFieldError,
)
```
