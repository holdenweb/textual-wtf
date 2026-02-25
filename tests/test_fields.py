"""Tests for textual_wtf.fields."""

import pytest

from textual_wtf.exceptions import FieldError, ValidationError
from textual_wtf.fields import (
    BooleanField,
    ChoiceField,
    Field,
    IntegerField,
    StringField,
    TextField,
)
from textual_wtf.validators import FunctionValidator, MaxLength, MaxValue, MinLength, MinValue
from textual_wtf.widgets import FormCheckbox, FormInput, FormSelect, FormTextArea


class TestFieldBase:
    def test_default_attributes(self):
        f = Field("Name")
        assert f.label == "Name"
        assert f.initial is None
        assert f.required is False
        assert f.disabled is False
        assert f.validators == []
        assert f.help_text == ""
        assert f.label_style == "above"
        assert f.help_style == "below"

    def test_custom_attributes(self):
        f = Field(
            "Email",
            initial="test@test.com",
            required=True,
            disabled=True,
            help_text="Enter email",
            label_style="beside",
            help_style="tooltip",
        )
        assert f.initial == "test@test.com"
        assert f.required is True
        assert f.disabled is True
        assert f.help_text == "Enter email"
        assert f.label_style == "beside"
        assert f.help_style == "tooltip"

    def test_widget_kwargs_captured(self):
        f = Field("Name", classes="custom", id="my-field")
        assert f.widget_kwargs == {"classes": "custom", "id": "my-field"}

    def test_validators_stored_as_list(self):
        v = MinLength(3)
        f = Field("Name", validators=[v])
        assert f.validators == [v]

    def test_callable_normalised_to_function_validator(self):
        fn = lambda v: None  # noqa: E731
        f = Field("Name", validators=[fn])
        assert len(f.validators) == 1
        assert isinstance(f.validators[0], FunctionValidator)

    def test_empty_validators_default(self):
        f = Field("Name")
        assert f.validators == []
        assert isinstance(f.validators, list)

    def test_to_python_passthrough(self):
        f = Field("Name")
        assert f.to_python("hello") == "hello"
        assert f.to_python(42) == 42
        assert f.to_python(None) is None

    def test_label_style_explicit_tracking(self):
        f1 = Field("A")
        assert f1._label_style_explicit is False
        f2 = Field("B", label_style="beside")
        assert f2._label_style_explicit is True

    def test_help_style_explicit_tracking(self):
        f1 = Field("A")
        assert f1._help_style_explicit is False
        f2 = Field("B", help_style="tooltip")
        assert f2._help_style_explicit is True


class TestStringField:
    def test_default_widget_class(self):
        assert StringField("Name").widget_class is FormInput

    def test_to_python_passthrough(self):
        f = StringField("Name")
        assert f.to_python("hello") == "hello"
        assert f.to_python(None) is None

    def test_min_length_adds_validator(self):
        f = StringField("Name", min_length=3)
        assert any(isinstance(v, MinLength) for v in f.validators)

    def test_max_length_adds_validator(self):
        f = StringField("Name", max_length=100)
        assert any(isinstance(v, MaxLength) for v in f.validators)

    def test_no_length_kwargs_no_extra_validators(self):
        assert StringField("Name").validators == []


class TestIntegerField:
    def test_default_widget_class(self):
        assert IntegerField("Age").widget_class is FormInput

    def test_restrict_in_widget_kwargs(self):
        assert "restrict" in IntegerField("Age").widget_kwargs

    def test_to_python_valid_int(self):
        assert IntegerField("Age").to_python("42") == 42

    def test_to_python_none(self):
        assert IntegerField("Age").to_python(None) is None

    def test_to_python_empty_string(self):
        assert IntegerField("Age").to_python("") is None

    def test_to_python_whitespace(self):
        assert IntegerField("Age").to_python("  ") is None

    def test_to_python_invalid_raises(self):
        with pytest.raises(ValidationError, match="whole number"):
            IntegerField("Age").to_python("abc")

    def test_minimum_adds_validator(self):
        f = IntegerField("Age", minimum=0)
        assert any(isinstance(v, MinValue) for v in f.validators)

    def test_maximum_adds_validator(self):
        f = IntegerField("Age", maximum=150)
        assert any(isinstance(v, MaxValue) for v in f.validators)

    def test_both_bounds(self):
        f = IntegerField("Age", minimum=0, maximum=150)
        assert any(isinstance(v, MinValue) for v in f.validators)
        assert any(isinstance(v, MaxValue) for v in f.validators)

    def test_to_python_negative(self):
        assert IntegerField("Temp").to_python("-5") == -5


class TestBooleanField:
    def test_default_widget_class(self):
        assert BooleanField("Active").widget_class is FormCheckbox

    def test_default_initial_false(self):
        assert BooleanField("Active").initial is False

    def test_custom_initial(self):
        assert BooleanField("Active", initial=True).initial is True

    def test_to_python_passthrough(self):
        f = BooleanField("Active")
        assert f.to_python(True) is True
        assert f.to_python(False) is False


class TestChoiceField:
    def test_choices_stored(self):
        choices = [("Red", "r"), ("Green", "g"), ("Blue", "b")]
        f = ChoiceField("Color", choices=choices)
        assert f.choices == choices

    def test_default_widget_class(self):
        assert ChoiceField("C", choices=[("A", "a")]).widget_class is FormSelect

    def test_empty_choices_raises(self):
        with pytest.raises(FieldError, match="non-empty"):
            ChoiceField("Color", choices=[])

    def test_to_python_passthrough(self):
        f = ChoiceField("C", choices=[("A", "a")])
        assert f.to_python("a") == "a"


class TestTextField:
    def test_default_widget_class(self):
        assert TextField("Notes").widget_class is FormTextArea

    def test_to_python_passthrough(self):
        f = TextField("Notes")
        assert f.to_python("hello") == "hello"
        assert f.to_python(None) is None

    def test_min_length_adds_validator(self):
        f = TextField("Notes", min_length=10)
        assert any(isinstance(v, MinLength) for v in f.validators)

    def test_max_length_adds_validator(self):
        f = TextField("Notes", max_length=500)
        assert any(isinstance(v, MaxLength) for v in f.validators)
