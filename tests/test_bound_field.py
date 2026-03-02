"""Tests for textual_wtf.bound — BoundField properties, validation, __call__."""

import pytest

from textual.widget import Widget

from textual_wtf.bound import BoundField
from textual_wtf.controller import FieldController
from textual_wtf.exceptions import FormError, ValidationError
from textual_wtf.fields import (
    BooleanField,
    ChoiceField,
    IntegerField,
    StringField,
    TextField,
)
from textual_wtf.forms import Form
from textual_wtf.validators import FunctionValidator, MinLength, Required


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
        # required=True prepends Required; MinLength follows
        validators = ContactForm().name.validators
        assert len(validators) >= 2
        assert any(isinstance(v, Required) for v in validators)
        assert any(isinstance(v, MinLength) for v in validators)

    def test_label_style_default(self):
        assert ContactForm().name.label_style == "above"

    def test_help_style_default(self):
        assert ContactForm().name.help_style == "below"

    def test_has_controller(self):
        form = ContactForm()
        assert isinstance(form.name.controller, FieldController)


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
        assert form.age.value == 25

    def test_integer_to_python_runs(self):
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
        # Required is prepended; FunctionValidator wraps no_spaces
        assert any(isinstance(v, FunctionValidator) for v in form.code.validators)

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


# ── __call__ — returns raw inner widget ─────────────────────────


class TestBoundFieldCall:
    def test_returns_widget(self):
        """__call__ returns the raw inner Textual widget (not self)."""
        form = ContactForm()
        result = form.name()
        assert isinstance(result, Widget)
        assert result is not form.name

    def test_stamps_field_controller(self):
        form = ContactForm()
        widget = form.name()
        assert hasattr(widget, "_field_controller")
        assert widget._field_controller is form.name.controller

    def test_marks_rendered(self):
        form = ContactForm()
        form.name()
        assert form.name.controller._consumed is True

    def test_duplicate_raises(self):
        form = ContactForm()
        form.name()
        with pytest.raises(FormError, match="already been rendered"):
            form.name()

    def test_override_disabled_produces_disabled_widget(self):
        """disabled=True passed to __call__ is forwarded to the raw widget."""
        form = ContactForm()
        widget = form.name(disabled=True)
        assert widget.disabled is True

    def test_no_overrides_keeps_bind_time_defaults(self):
        """BoundField.label_style / help_style reflect bind-time cascade, not call-site."""
        form = ContactForm()
        form.name()
        assert form.name.label_style == "above"
        assert form.name.help_style == "below"

    def test_extra_widget_kwargs_accepted(self):
        """Extra kwargs are forwarded to the widget without raising."""
        form = ContactForm()
        widget = form.name(placeholder="Enter name")
        assert widget is not None


# ── simple_layout — returns FieldWidget ─────────────────────────


class TestSimpleLayout:
    def test_returns_field_widget(self):
        from textual_wtf.field_widget import FieldWidget

        form = ContactForm()
        result = form.email.simple_layout()
        assert isinstance(result, FieldWidget)

    def test_marks_rendered(self):
        form = ContactForm()
        form.email.simple_layout()
        assert form.email.controller._consumed is True

    def test_duplicate_raises(self):
        form = ContactForm()
        form.email.simple_layout()
        with pytest.raises(FormError, match="already been rendered"):
            form.email.simple_layout()

    def test_call_then_simple_layout_raises(self):
        """Calling __call__ then simple_layout (or vice versa) also raises."""
        form = ContactForm()
        form.age()
        with pytest.raises(FormError):
            form.age.simple_layout()

    def test_overrides_reach_field_widget(self):
        """Call-site label_style / help_style / disabled are forwarded to FieldWidget."""
        from textual_wtf.field_widget import FieldWidget

        form = ContactForm()
        fw = form.email.simple_layout(label_style="beside", help_style="tooltip", disabled=True)
        assert isinstance(fw, FieldWidget)
        assert fw._label_style == "beside"
        assert fw._help_style == "tooltip"
        assert fw._disabled is True


# ── validate_for — event-scoped validation ──────────────────────


class TestValidateFor:
    def test_change_does_not_trigger_required(self):
        class F(Form):
            name = StringField("Name", required=True)

        form = F()
        form.name.value = ""
        assert form.name.controller.validate_for("change") is True
        assert form.name.has_error is False

    def test_blur_triggers_required(self):
        class F(Form):
            name = StringField("Name", required=True)

        form = F()
        form.name.value = ""
        assert form.name.controller.validate_for("blur") is False
        assert form.name.has_error is True
        assert any("required" in e.lower() for e in form.name.errors)

    def test_change_triggers_max_length(self):
        class F(Form):
            tag = StringField("Tag", max_length=5)

        form = F(data={"tag": "toolongstring"})
        assert form.tag.controller.validate_for("change") is False
        assert form.tag.has_error is True

    def test_change_does_not_trigger_min_length(self):
        class F(Form):
            name = StringField("Name", min_length=5)

        form = F(data={"name": "ab"})
        assert form.name.controller.validate_for("change") is True
        assert form.name.has_error is False

    def test_blur_triggers_min_length(self):
        class F(Form):
            name = StringField("Name", min_length=5)

        form = F(data={"name": "ab"})
        assert form.name.controller.validate_for("blur") is False
        assert form.name.has_error is True
        assert any("at least 5" in e for e in form.name.errors)

    def test_submit_triggers_min_length(self):
        class F(Form):
            name = StringField("Name", required=True, min_length=5)

        form = F(data={"name": "ab"})
        assert form.name.controller.validate_for("change") is True
        assert form.name.validate() is False
        assert any("at least 5" in e for e in form.name.errors)

    def test_validate_delegates_to_validate_for_submit(self):
        class F(Form):
            code = StringField("Code", min_length=4)

        form1 = F(data={"code": "ab"})
        form2 = F(data={"code": "ab"})
        result_via_validate = form1.code.validate()
        result_via_event = form2.code.controller.validate_for("submit")
        assert result_via_validate == result_via_event
        assert form1.code.errors == form2.code.errors

    def test_validate_for_clears_errors_when_valid(self):
        class F(Form):
            tag = StringField("Tag", max_length=5)

        form = F(data={"tag": "toolong"})
        form.tag.controller.validate_for("change")
        assert form.tag.has_error is True

        form.tag.value = "ok"
        assert form.tag.controller.validate_for("change") is True
        assert form.tag.has_error is False
        assert form.tag.errors == []

    def test_empty_optional_field_passes_blur(self):
        class F(Form):
            tag = StringField("Tag", min_length=3)

        form = F()
        assert form.tag.controller.validate_for("blur") is True
        assert form.tag.has_error is False

    def test_blur_collects_errors_from_multiple_validators(self):
        def no_digits(v):
            if any(c.isdigit() for c in v):
                raise ValidationError("No digits allowed")

        class F(Form):
            code = StringField("Code", min_length=4, validators=[no_digits])

        form = F(data={"code": "ab1"})
        assert form.code.controller.validate_for("blur") is False
        assert len(form.code.errors) >= 2


# ── to_python delegation ───────────────────────────────────────


class TestBoundFieldToPython:
    def test_integer_field_delegates(self):
        form = ContactForm()
        assert form.age.field.to_python("42") == 42

    def test_string_field_passthrough(self):
        form = ContactForm()
        assert form.name.field.to_python("hello") == "hello"
