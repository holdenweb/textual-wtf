# field.py
from typing import Any, Callable, List, Optional

from .widget import StringWidget, IntegerWidget, CheckboxWidget, SelectWidget, TextWidget

class Field:

    def __init__(
        self,
        label: str = "",
        required: bool = True,
        validators: Optional[List[Callable[[Any], List[str]]]] = None,
        help_text: str = "",
        disabled=False,
        widget=None,
        **kwargs,
    ):
        self.kwargs = kwargs
        self.label = label
        self.required = required
        self.validators = validators or []
        self.help_text = help_text
        self.name: str = ""
        self.form: Optional["Form"] = None
        self.disabled = disabled
        self.widget = widget

    @property
    def value(self):
        return self.widget.value if self.widget.value else None

    @value.setter
    def value(self, value):  # Only works with string-valued widgets
        self.widget.value = '' if value is None else str(value)

    def to_widget_value(self, value: Any) -> Any:
        return value

    def create_widget(self):
        if self.widget is None:
            raise NotImplementedError("Fields with no default widget must implement create_widget()")


class StringField(Field):
    def create_widget(self):
        return StringWidget(field=self, valid_empty=not self.required, validators=self.validators, **self.kwargs)

class IntegerField(Field):
    def create_widget(self):
        return IntegerWidget(field=self, valid_empty=not self.required, validators=self.validators, **self.kwargs)

    @property
    def value(self) -> Optional[int]:
        try:
            return int(self.widget.value)
        except ValueError:
            return None

    @value.setter
    def value(self, value):
        self.widget.value = str(value)

class TextField(Field):
    def create_widget(self):
        return TextWidget(field=self, **self.kwargs)


class BooleanField(Field):
    def create_widget(self):
        return CheckboxWidget(field=self, label=self.label, **self.kwargs)

    def to_python(self, value: bool) -> bool:
        return value

    @property
    def value(self):
        return self.widget.value

    @value.setter
    def value(self, value):
        self.widget.value = value

class ChoiceField(Field):

    def __init__(
        self,
        choices: List[tuple[str, str]],
        label: str = "",
        required: bool = True,
        validators: Optional[List[Callable[[Any], List[str]]]] = None,
        help_text: str = "",
        **kwargs,
    ):
        self.choices = choices
        self.kwargs = kwargs
        self.required = required
        super().__init__(label, required, validators, help_text, **kwargs)

    def create_widget(self):
        return SelectWidget(field=self, choices=self.choices, allow_blank=not self.required, **self.kwargs)

    def to_python(self, value: str) -> str:
        return value
