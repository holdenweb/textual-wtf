"""
Textual Forms - A declarative forms library for Textual TUI applications

Example:
    from textual_forms import Form, StringField, IntegerField
    
    class UserForm(Form):
        name = StringField(label="Name", required=True)
        age = IntegerField(label="Age", min_value=0, max_value=130)
"""

from .exceptions import ValidationError, FieldError, FormError, AmbiguousFieldError
from .fields import (
    Field,
    StringField,
    IntegerField,
    BooleanField,
    ChoiceField,
    TextField,
)
from .forms import Form
from .validators import (
    Validator,
    RequiredValidator,
    MinLengthValidator,
    MaxLengthValidator,
    MinValueValidator,
    MaxValueValidator,
    EvenInteger,
    Palindromic,
    EmailValidator,
)
from .widgets import (
    FormInput,
    FormIntegerInput,
    FormTextArea,
    FormCheckbox,
    FormSelect,
    WidgetRegistry,
)

__version__ = "0.3.0"

__all__ = [
    # Exceptions
    "ValidationError",
    "FieldError",
    "FormError",
    "AmbiguousFieldError",
    # Fields
    "Field",
    "StringField",
    "IntegerField",
    "BooleanField",
    "ChoiceField",
    "TextField",
    # Forms
    "Form",
    # Validators
    "Validator",
    "RequiredValidator",
    "MinLengthValidator",
    "MaxLengthValidator",
    "MinValueValidator",
    "MaxValueValidator",
    "EvenInteger",
    "Palindromic",
    "EmailValidator",
    # Widgets
    "FormInput",
    "FormIntegerInput",
    "FormTextArea",
    "FormCheckbox",
    "FormSelect",
    "WidgetRegistry",
]
