"""Tests for textual_wtf.bound — BoundField properties, validation, __call__."""

import pytest

from textual_wtf.bound import BoundField
from textual_wtf.exceptions import FormError, ValidationError
from textual_wtf.fields import (
    BooleanField,
    ChoiceField,
    IntegerField,
    StringField,
    TextField,
)
from textual_wtf.forms import Form
from textual_wtf.validators import MinLength


class ContactForm(Form):
    name = StringField("Name", required=True, validators=[MinLength(2)])
    email = StringField("Email", help_text="Your email address")
    age = IntegerField("Age", min_value=0, max_value=150)
    active = BooleanField("Active")
    notes = TextField("Notes")
    role = ChoiceField(
        "Role",
        choices=[("Admin", "admin"), ("User", "user"), ("Guest", "guest")],
    )


# ── Property delegation ────────────────────────────────────────


class TestBoundFieldProperties:
    def test_label(self):
        assert ContactForm().name.label == "Name"

    def test_default(self):
        form = ContactForm()
        assert form.name.default is None
        assert form.active.default is False

    def test_required(self):
        form = ContactForm()
        assert form.name.required is True
        assert form.email.required is False

    def test_help_text(self):
        assert ContactForm().email.help_text == "Your email address"
        assert ContactForm().name.help_text == ""

    def test_field_reference(self):
        form = ContactForm()
        assert form.name.field is ContactForm._field_definitions["name"]

    def test_form_reference(self):
        form = ContactForm()
        assert form.name.form is form

    def test_name_attribute(self):
        form = ContactForm()
        assert form.name.name == "name"
        assert form.email.name == "email"

    def test_validators_list(self):
        assert len(ContactForm().name.validators) >= 1

    def test_label_style_default(self):
        assert ContactForm().name.label_style == "above"

    def test_help_style_default(self):
        assert ContactForm().name.help_style == "below"


# ── Initial values ──────────────────────────────────────────────


class TestBoundFieldInitialValues:
    def test_value_from_data(self):
        form = ContactForm(data={"name": "Alice"})
        assert form.name.value == "Alice"

    def test_value_from_field_default(self):
        assert ContactForm().active.value is False

    def test_value_none_when_no_default_or_data(self):
        assert ContactForm().name.value is None

    def test_is_dirty_initially_false(self):
        assert ContactForm().name.is_dirty is False

    def test_disabled_from_field(self):
        class DisabledForm(Form):
            name = StringField("Name", disabled=True)

        assert DisabledForm().name.disabled is True


# ── Validation ──────────────────────────────────────────────────


class TestBoundFieldValidation:
    def test_valid_passes(self):
        form = ContactForm(data={"name": "Alice"})
        assert form.name.validate() is True

    def test_required_empty_fails(self):
        form = ContactForm()
        assert form.name.validate() is False
        assert form.name.has_error is True
        assert len(form.name.errors) > 0

    def test_min_length_fails(self):
        form = ContactForm(data={"name": "A"})
        assert form.name.validate() is False
        assert "at least 2" in form.name.errors[0]

    def test_clears_previous_errors(self):
        form = ContactForm()
        form.name.validate()
        assert form.name.has_error is True
        form.name.value = "Alice"
        form.name.validate()
        assert form.name.has_error is False
        assert form.name.errors == []

    def test_integer_to_python_runs(self):
        """validate() should coerce '25' to int via to_python."""
        form = ContactForm(data={"name": "Alice", "age": "25"})
        assert form.age.validate() is True
        assert form.age.value == 25  # coerced to int

    def test_integer_out_of_range(self):
        form = ContactForm(data={"name": "Alice", "age": "200"})
        assert form.age.validate() is False

    def test_integer_non_numeric(self):
        form = ContactForm(data={"name": "Alice", "age": "abc"})
        assert form.age.validate() is False
        assert form.age.has_error is True

    def test_optional_empty_passes(self):
        form = ContactForm(data={"name": "Alice"})
        assert form.email.validate() is True
        assert form.notes.validate() is True

    def test_error_messages_matches_errors(self):
        form = ContactForm()
        form.name.validate()
        assert form.name.error_messages == form.name.errors
        assert len(form.name.error_messages) > 0

    def test_callable_validator(self):
        def no_spaces(value):
            if " " in value:
                raise ValidationError("No spaces allowed")

        class StrictForm(Form):
            code = StringField("Code", required=True, validators=[no_spaces])

        form = StrictForm(data={"code": "has space"})
        assert form.code.validate() is False
        assert "No spaces" in form.code.errors[0]

    def test_callable_validator_passes(self):
        def no_spaces(value):
            if " " in value:
                raise ValidationError("No spaces allowed")

        class StrictForm(Form):
            code = StringField("Code", required=True, validators=[no_spaces])

        form = StrictForm(data={"code": "nospace"})
        assert form.code.validate() is True


# ── __call__ ────────────────────────────────────────────────────


class TestBoundFieldCall:
    def test_returns_self(self):
        form = ContactForm()
        result = form.name()
        assert result is form.name

    def test_marks_rendered(self):
        form = ContactForm()
        form.name()
        assert form.name._rendered is True

    def test_duplicate_raises(self):
        form = ContactForm()
        form.name()
        with pytest.raises(FormError, match="already been yielded"):
            form.name()

    def test_overrides_label_style(self):
        form = ContactForm()
        form.name(label_style="beside")
        assert form.name.label_style == "beside"

    def test_overrides_help_style(self):
        form = ContactForm()
        form.email(help_style="tooltip")
        assert form.email.help_style == "tooltip"

    def test_overrides_disabled(self):
        form = ContactForm()
        form.name(disabled=True)
        assert form.name.disabled is True

    def test_no_overrides_keeps_defaults(self):
        form = ContactForm()
        form.name()
        assert form.name.label_style == "above"
        assert form.name.help_style == "below"

    def test_merges_widget_kwargs(self):
        form = ContactForm()
        form.name(classes="custom-class")
        assert "classes" in form.name._widget_kwargs


# ── to_python delegation ───────────────────────────────────────


class TestBoundFieldToPython:
    def test_integer_field_delegates(self):
        form = ContactForm()
        # Directly test the delegation
        assert form.age.field.to_python("42") == 42

    def test_string_field_passthrough(self):
        form = ContactForm()
        assert form.name.field.to_python("hello") == "hello"
