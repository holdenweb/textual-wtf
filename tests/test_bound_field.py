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
from textual_wtf.validators import FunctionValidator, MinLength


class ContactForm(Form):
    name = StringField("Name", required=True, validators=[MinLength(2)])
    email = StringField("Email", help_text="Your email address")
    age = IntegerField("Age", minimum=0, maximum=150)
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

    def test_integer_coerced_at_init(self):
        """String '25' from the data dict is coerced to int at init time."""
        form = ContactForm(data={"name": "Alice", "age": 25})
        assert form.age.value == 25  # already an int before validate()

    def test_integer_to_python_runs(self):
        """validate() passes and the value remains a correctly-typed int."""
        form = ContactForm(data={"name": "Alice", "age": 25})
        assert form.age.validate() is True
        assert form.age.value == 25

    def test_integer_out_of_range(self):
        form = ContactForm(data={"name": "Alice", "age": 200})
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

    def test_callable_normalised_to_function_validator(self):
        """A plain callable in validators= is wrapped in FunctionValidator."""

        def no_spaces(value):
            if " " in value:
                raise ValidationError("No spaces allowed")

        class StrictForm(Form):
            code = StringField("Code", required=True, validators=[no_spaces])

        form = StrictForm()
        assert isinstance(form.code.validators[0], FunctionValidator)

    def test_callable_validator(self):
        """FunctionValidator wrapping raises ValidationError on bad input."""

        def no_spaces(value):
            if " " in value:
                raise ValidationError("No spaces allowed")

        class StrictForm(Form):
            code = StringField("Code", required=True, validators=[no_spaces])

        form = StrictForm(data={"code": "has space"})
        assert form.code.validate() is False
        assert "No spaces" in form.code.errors[0]

    def test_callable_validator_passes(self):
        """FunctionValidator wrapping returns success for valid input."""

        def no_spaces(value):
            if " " in value:
                raise ValidationError("No spaces allowed")

        class StrictForm(Form):
            code = StringField("Code", required=True, validators=[no_spaces])

        form = StrictForm(data={"code": "nospace"})
        assert form.code.validate() is True


# ── Convenience keyword validators ──────────────────────────────


class TestConvenienceKwargs:
    def test_string_field_min_length(self):
        class F(Form):
            name = StringField("Name", required=True, min_length=3)

        assert F(data={"name": "Al"}).name.validate() is False
        assert F(data={"name": "Alice"}).name.validate() is True

    def test_string_field_max_length(self):
        class F(Form):
            name = StringField("Name", max_length=5)

        assert F(data={"name": "Toolong"}).name.validate() is False
        assert F(data={"name": "Hi"}).name.validate() is True

    def test_integer_field_minimum(self):
        class F(Form):
            age = IntegerField("Age", minimum=0)

        assert F(data={"age": -1}).age.validate() is False
        assert F(data={"age": 0}).age.validate() is True

    def test_integer_field_maximum(self):
        class F(Form):
            age = IntegerField("Age", maximum=150)

        assert F(data={"age": 200}).age.validate() is False
        assert F(data={"age": 100}).age.validate() is True

    def test_integer_field_minimum_maximum_both(self):
        class F(Form):
            age = IntegerField("Age", minimum=18, maximum=65)

        assert F(data={"age": 17}).age.validate() is False
        assert F(data={"age": 66}).age.validate() is False
        assert F(data={"age": 30}).age.validate() is True

    def test_text_field_max_length(self):
        class F(Form):
            bio = TextField("Bio", max_length=10)

        assert F(data={"bio": "Way too long text"}).bio.validate() is False
        assert F(data={"bio": "Short"}).bio.validate() is True


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


# ── _validate_for — event-scoped validation ─────────────────────


class TestValidateFor:
    """BoundField._validate_for(event) only fires validators whose
    validate_on includes *event*.  validate() always runs everything."""

    def test_change_does_not_trigger_required(self):
        """Required field with empty value: change should not flag it as an error."""

        class F(Form):
            name = StringField("Name", required=True)

        form = F()
        form.name.value = ""
        assert form.name._validate_for("change") is True
        assert form.name.has_error is False

    def test_blur_triggers_required(self):
        """Required field with empty value: blur should fail."""

        class F(Form):
            name = StringField("Name", required=True)

        form = F()
        form.name.value = ""
        assert form.name._validate_for("blur") is False
        assert form.name.has_error is True
        assert any("required" in e.lower() for e in form.name.errors)

    def test_change_triggers_max_length(self):
        """MaxLength fires on change, so an over-length value is caught immediately."""

        class F(Form):
            tag = StringField("Tag", max_length=5)

        form = F(data={"tag": "toolongstring"})
        assert form.tag._validate_for("change") is False
        assert form.tag.has_error is True

    def test_change_does_not_trigger_min_length(self):
        """MinLength does NOT fire on change — short values are tolerated while typing."""

        class F(Form):
            name = StringField("Name", min_length=5)

        form = F(data={"name": "ab"})
        assert form.name._validate_for("change") is True
        assert form.name.has_error is False

    def test_blur_triggers_min_length(self):
        """MinLength fires on blur — too-short value is caught when leaving the field."""

        class F(Form):
            name = StringField("Name", min_length=5)

        form = F(data={"name": "ab"})
        assert form.name._validate_for("blur") is False
        assert form.name.has_error is True
        assert any("at least 5" in e for e in form.name.errors)

    def test_validate_runs_all_validators_regardless_of_validate_on(self):
        """validate() (submit path) runs every validator regardless of validate_on."""

        class F(Form):
            name = StringField("Name", required=True, min_length=5)

        form = F(data={"name": "ab"})
        # _validate_for("change") would pass (min_length not in change validators)
        assert form.name._validate_for("change") is True
        # validate() must still catch the min_length violation
        assert form.name.validate() is False
        assert any("at least 5" in e for e in form.name.errors)

    def test_validate_for_clears_errors_when_valid(self):
        """_validate_for clears has_error and errors when the value is now valid."""

        class F(Form):
            tag = StringField("Tag", max_length=5)

        form = F(data={"tag": "toolong"})
        form.tag._validate_for("change")
        assert form.tag.has_error is True

        form.tag.value = "ok"
        assert form.tag._validate_for("change") is True
        assert form.tag.has_error is False
        assert form.tag.errors == []

    def test_empty_optional_field_passes_blur(self):
        """An optional empty field should always pass _validate_for("blur")."""

        class F(Form):
            tag = StringField("Tag", min_length=3)

        form = F()
        assert form.tag._validate_for("blur") is True
        assert form.tag.has_error is False

    def test_blur_collects_errors_from_multiple_validators(self):
        """Both MinLength and a custom callable validator fire on blur."""

        def no_digits(v):
            if any(c.isdigit() for c in v):
                raise ValidationError("No digits allowed")

        class F(Form):
            code = StringField("Code", min_length=4, validators=[no_digits])

        form = F(data={"code": "ab1"})
        # blur: min_length fires (too short) AND no_digits fires (has digit)
        assert form.code._validate_for("blur") is False
        assert len(form.code.errors) >= 2


# ── to_python delegation ───────────────────────────────────────


class TestBoundFieldToPython:
    def test_integer_field_delegates(self):
        form = ContactForm()
        # Directly test the delegation
        assert form.age.field.to_python("42") == 42

    def test_string_field_passthrough(self):
        form = ContactForm()
        assert form.name.field.to_python("hello") == "hello"
