"""Tests for Field classes (pure Python — no Textual runtime needed)."""
import pytest
from textual_wtf import (
    BooleanField,
    ChoiceField,
    FieldError,
    Form,
    IntegerField,
    MinLength,
    Required,
    StringField,
    TextField,
    ValidationError,
)
from textual_wtf.fields import _UNSET


# ── Field base class ──────────────────────────────────────────────────────────

class TestFieldConstruction:
    def test_label_stored(self):
        f = StringField(label="Name")
        assert f.label == "Name"

    def test_defaults(self):
        f = StringField(label="X")
        assert f.initial is None
        assert f.required is False
        assert f.disabled is False
        assert f.validators == []
        assert f.help_text == ""
        assert f.label_style == "above"   # resolved from _UNSET
        assert f.help_style == "below"

    def test_explicit_label_style(self):
        f = StringField(label="X", label_style="beside")
        assert f.label_style == "beside"
        assert f._label_style == "beside"  # not _UNSET

    def test_unset_label_style(self):
        f = StringField(label="X")
        assert f._label_style is _UNSET

    def test_invalid_label_style_raises(self):
        with pytest.raises(FieldError):
            StringField(label="X", label_style="wrong")

    def test_invalid_help_style_raises(self):
        with pytest.raises(FieldError):
            StringField(label="X", help_style="hover")

    def test_validators_stored(self):
        v = Required()
        f = StringField(label="X", validators=[v])
        assert v in f.validators

    def test_widget_kwargs_forwarded(self):
        f = StringField(label="X", placeholder="Type here")
        assert f.widget_kwargs["placeholder"] == "Type here"


# ── StringField ───────────────────────────────────────────────────────────────

class TestStringField:
    def test_to_python_string(self):
        f = StringField(label="X")
        assert f.to_python("hello") == "hello"

    def test_to_python_none(self):
        f = StringField(label="X")
        assert f.to_python(None) is None

    def test_to_python_empty(self):
        f = StringField(label="X")
        assert f.to_python("") is None

    def test_to_widget(self):
        f = StringField(label="X")
        assert f.to_widget("hello") == "hello"
        assert f.to_widget(None) == ""

    def test_clean_required_raises(self):
        f = StringField(label="X", required=True)
        with pytest.raises(ValidationError, match="required"):
            f.clean("")

    def test_clean_required_passes(self):
        f = StringField(label="X", required=True)
        assert f.clean("hello") == "hello"

    def test_clean_optional_empty(self):
        f = StringField(label="X")
        assert f.clean("") is None

    def test_clean_runs_validators(self):
        f = StringField(label="X", validators=[MinLength(5)])
        with pytest.raises(ValidationError):
            f.clean("hi")

    def test_default_widget_class(self):
        from textual_wtf.widgets import FormInput
        assert StringField(label="X").widget_class is FormInput


# ── IntegerField ──────────────────────────────────────────────────────────────

class TestIntegerField:
    def test_to_python_integer(self):
        f = IntegerField(label="X")
        assert f.to_python("42") == 42
        assert f.to_python(42) == 42

    def test_to_python_empty(self):
        f = IntegerField(label="X")
        assert f.to_python("") is None
        assert f.to_python(None) is None

    def test_to_python_partial_minus(self):
        """Mid-typing leniency: '-' alone is not an error."""
        f = IntegerField(label="X")
        assert f.to_python("-") is None

    def test_to_python_non_integer(self):
        """Non-convertible string → None (not exception) during mid-typing."""
        f = IntegerField(label="X")
        assert f.to_python("abc") is None

    def test_clean_valid(self):
        f = IntegerField(label="X")
        assert f.clean("7") == 7

    def test_clean_non_integer_raises(self):
        f = IntegerField(label="X")
        with pytest.raises(ValidationError, match="valid integer"):
            f.clean("abc")

    def test_clean_required_empty_raises(self):
        f = IntegerField(label="X", required=True)
        with pytest.raises(ValidationError, match="required"):
            f.clean("")

    def test_min_value_validator_added(self):
        f = IntegerField(label="X", min_value=0)
        with pytest.raises(ValidationError):
            f.clean("-5")

    def test_max_value_validator_added(self):
        f = IntegerField(label="X", max_value=100)
        with pytest.raises(ValidationError):
            f.clean("200")

    def test_type_kwarg_in_widget_kwargs(self):
        f = IntegerField(label="X")
        assert f.widget_kwargs.get("type") == "integer"

    def test_default_widget_class(self):
        from textual_wtf.widgets import FormInput
        assert IntegerField(label="X").widget_class is FormInput


# ── BooleanField ──────────────────────────────────────────────────────────────

class TestBooleanField:
    def test_to_python_true(self):
        f = BooleanField(label="X")
        assert f.to_python(True) is True

    def test_to_python_false(self):
        f = BooleanField(label="X")
        assert f.to_python(False) is False

    def test_to_python_string_true(self):
        f = BooleanField(label="X")
        assert f.to_python("true") is True

    def test_to_python_string_false(self):
        f = BooleanField(label="X")
        assert f.to_python("false") is False

    def test_default_widget_class(self):
        from textual_wtf.widgets import FormCheckbox
        assert BooleanField(label="X").widget_class is FormCheckbox


# ── ChoiceField ───────────────────────────────────────────────────────────────

class TestChoiceField:
    CHOICES = [("Red", "red"), ("Green", "green")]

    def test_to_python_valid(self):
        f = ChoiceField(label="X", choices=self.CHOICES)
        assert f.to_python("red") == "red"

    def test_to_python_none(self):
        f = ChoiceField(label="X", choices=self.CHOICES)
        assert f.to_python(None) is None

    def test_clean_invalid_choice_raises(self):
        f = ChoiceField(label="X", choices=self.CHOICES, required=True)
        with pytest.raises(ValidationError):
            f.clean("yellow")

    def test_clean_valid_choice(self):
        f = ChoiceField(label="X", choices=self.CHOICES)
        assert f.clean("red") == "red"

    def test_choices_in_widget_kwargs(self):
        f = ChoiceField(label="X", choices=self.CHOICES)
        assert f.widget_kwargs["choices"] == self.CHOICES

    def test_default_widget_class(self):
        from textual_wtf.widgets import FormSelect
        assert ChoiceField(label="X", choices=self.CHOICES).widget_class is FormSelect


# ── TextField ─────────────────────────────────────────────────────────────────

class TestTextField:
    def test_default_widget_class(self):
        from textual_wtf.widgets import FormTextArea
        assert TextField(label="X").widget_class is FormTextArea

    def test_to_python_string(self):
        f = TextField(label="X")
        assert f.to_python("multi\nline") == "multi\nline"

    def test_to_python_empty(self):
        f = TextField(label="X")
        assert f.to_python("") is None


# ── Field.bind ────────────────────────────────────────────────────────────────

class TestFieldBind:
    def test_bind_returns_bound_field(self):
        from textual_wtf import BoundField

        class SimpleForm(Form):
            name = StringField(label="Name")

        form = SimpleForm()
        assert isinstance(form.name, BoundField)

    def test_bound_field_references_field(self):
        class SimpleForm(Form):
            name = StringField(label="Name")

        form = SimpleForm()
        assert form.name.field is SimpleForm._base_fields["name"]

    def test_bound_field_references_form(self):
        class SimpleForm(Form):
            name = StringField(label="Name")

        form = SimpleForm()
        assert form.name.form is form

    def test_initial_value_passed_through(self):
        class SimpleForm(Form):
            name = StringField(label="Name", initial="default")

        form = SimpleForm()
        assert form.name._initial_value == "default"

    def test_data_overrides_initial(self):
        class SimpleForm(Form):
            name = StringField(label="Name", initial="default")

        form = SimpleForm(data={"name": "override"})
        assert form.name._initial_value == "override"
