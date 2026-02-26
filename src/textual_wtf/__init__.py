"""textual-wtf — Declarative forms library for Textual TUI applications."""

from .bound import BoundField
from .controller import FieldController
from .exceptions import (
    AmbiguousFieldError,
    FieldError,
    FormError,
    ValidationError,
)
from .field_widget import FieldWidget
from .fields import (
    BooleanField,
    ChoiceField,
    Field,
    IntegerField,
    StringField,
    TextField,
)
from .forms import BaseForm, Form
from .layouts import ControllerAwareLayout, DefaultFormLayout, FormLayout
from .tabbed_form import TabbedForm
from .types import HelpStyle, LabelStyle
from .validators import (
    EmailValidator,
    MaxLength,
    MaxValue,
    MinLength,
    MinValue,
    Required,
    Validator,
)
from .widgets import FormCheckbox, FormInput, FormSelect, FormTextArea

__all__ = [
    # Field declarations
    "Field",
    "StringField",
    "IntegerField",
    "BooleanField",
    "ChoiceField",
    "TextField",
    # Runtime
    "BoundField",
    "FieldController",
    "FieldWidget",
    # Forms
    "BaseForm",
    "Form",
    "TabbedForm",
    # Layouts
    "FormLayout",
    "ControllerAwareLayout",
    "DefaultFormLayout",
    # Validators
    "Validator",
    "Required",
    "MinLength",
    "MaxLength",
    "MinValue",
    "MaxValue",
    "EmailValidator",
    # Widgets
    "FormInput",
    "FormCheckbox",
    "FormSelect",
    "FormTextArea",
    # Exceptions
    "ValidationError",
    "FieldError",
    "FormError",
    "AmbiguousFieldError",
    # Types
    "LabelStyle",
    "HelpStyle",
]
