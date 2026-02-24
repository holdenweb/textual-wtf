"""Tests for textual_wtf.forms — metaclass, binding, embed, validate, clean."""

import pytest

from textual_wtf.exceptions import AmbiguousFieldError, FormError, ValidationError
from textual_wtf.fields import IntegerField, StringField, TextField
from textual_wtf.forms import BaseForm, EmbeddedForm, Form


# ── Test forms ──────────────────────────────────────────────────


class SimpleForm(Form):
    name = StringField("Name", required=True)
    age = IntegerField("Age", min_value=0, max_value=150)


class AddressForm(Form):
    street = StringField("Street")
    city = StringField("City")
    postcode = StringField("Postcode")


class OrderForm(Form):
    billing = AddressForm.embed(prefix="billing")
    shipping = AddressForm.embed(prefix="shipping")
    notes = TextField("Notes")


class TitledForm(Form):
    title = "My Form"
    name = StringField("Name")


# ── Metaclass ───────────────────────────────────────────────────


class TestFormMetaclass:
    def test_fields_extracted(self):
        defs = SimpleForm._field_definitions
        assert "name" in defs
        assert "age" in defs
        assert len(defs) == 2

    def test_field_order_preserved(self):
        assert list(SimpleForm._field_definitions.keys()) == ["name", "age"]

    def test_fields_not_left_as_class_attrs(self):
        assert not isinstance(getattr(SimpleForm, "name", None), StringField)

    def test_embedded_expansion(self):
        defs = OrderForm._field_definitions
        assert "billing_street" in defs
        assert "billing_city" in defs
        assert "billing_postcode" in defs
        assert "shipping_street" in defs
        assert "shipping_city" in defs
        assert "shipping_postcode" in defs
        assert "notes" in defs
        assert len(defs) == 7

    def test_embedded_name_collision_raises(self):
        with pytest.raises(FormError, match="conflicts"):

            class BadForm(Form):
                billing_street = StringField("Street")
                billing = AddressForm.embed(prefix="billing")

    def test_embed_returns_embedded_form(self):
        marker = AddressForm.embed(prefix="test")
        assert isinstance(marker, EmbeddedForm)
        assert marker.form_class is AddressForm
        assert marker.prefix == "test"

    def test_embed_title(self):
        marker = AddressForm.embed(prefix="test", title="Test Addr")
        assert marker.title == "Test Addr"


# ── Form instance ──────────────────────────────────────────────


class TestFormInstance:
    def test_bound_fields_created(self):
        form = SimpleForm()
        assert len(form.bound_fields) == 2
        assert "name" in form.bound_fields
        assert "age" in form.bound_fields

    def test_fields_alias(self):
        form = SimpleForm()
        assert form.fields is form.bound_fields

    def test_attribute_access(self):
        bf = SimpleForm().name
        assert bf.name == "name"
        assert bf.label == "Name"

    def test_get_field(self):
        assert SimpleForm().get_field("name").name == "name"

    def test_unknown_field_raises(self):
        with pytest.raises(AttributeError, match="no field"):
            _ = SimpleForm().nonexistent

    def test_get_field_unknown_raises(self):
        with pytest.raises(AttributeError, match="no field"):
            SimpleForm().get_field("nonexistent")

    def test_initial_data(self):
        form = SimpleForm(data={"name": "Alice", "age": "30"})
        assert form.name.value == "Alice"
        assert form.age.value == "30"

    def test_missing_data_uses_defaults(self):
        form = SimpleForm(data={"name": "Alice"})
        assert form.age.value is None


# ── Data access ─────────────────────────────────────────────────


class TestFormDataAccess:
    def test_get_data(self):
        form = SimpleForm(data={"name": "Alice", "age": "30"})
        data = form.get_data()
        assert data["name"] == "Alice"
        assert data["age"] == "30"

    def test_set_data(self):
        form = SimpleForm()
        form.set_data({"name": "Bob", "age": "25"})
        assert form.name.value == "Bob"
        assert form.age.value == "25"

    def test_set_data_ignores_unknown(self):
        form = SimpleForm()
        form.set_data({"name": "Bob", "unknown": "val"})
        assert form.name.value == "Bob"


# ── Validation ──────────────────────────────────────────────────


class TestFormValidation:
    def test_all_valid(self):
        form = SimpleForm(data={"name": "Alice", "age": "30"})
        assert form.validate() is True

    def test_required_missing_fails(self):
        form = SimpleForm()
        assert form.validate() is False
        assert len(form.name.errors) > 0

    def test_integer_out_of_range_fails(self):
        form = SimpleForm(data={"name": "Alice", "age": "200"})
        assert form.validate() is False
        assert len(form.age.errors) > 0

    def test_is_valid_alias(self):
        form = SimpleForm(data={"name": "Alice"})
        # Both should produce the same result
        assert form.is_valid() is True

    def test_populates_errors(self):
        form = SimpleForm()
        form.validate()
        assert form.name.has_error is True
        assert len(form.name.error_messages) > 0

    def test_clears_errors_on_pass(self):
        form = SimpleForm(data={"name": "Alice"})
        form.validate()
        assert form.name.has_error is False
        assert form.name.errors == []


# ── Clean ───────────────────────────────────────────────────────


class TestFormClean:
    def test_clean_calls_validate(self):
        form = SimpleForm(data={"name": "Alice"})
        assert form.clean() is True

    def test_clean_fails_when_validate_fails(self):
        form = SimpleForm()  # name required but missing
        assert form.clean() is False

    def test_clean_form_hook_called_on_success(self):
        """clean_form() is called after validate() passes."""
        called = []

        class HookForm(Form):
            name = StringField("Name", required=True)

            def clean_form(self):
                called.append(True)
                return True

        form = HookForm(data={"name": "Alice"})
        form.clean()
        assert called == [True]

    def test_clean_form_hook_not_called_on_failure(self):
        """clean_form() is NOT called when validate() fails."""
        called = []

        class HookForm(Form):
            name = StringField("Name", required=True)

            def clean_form(self):
                called.append(True)
                return True

        form = HookForm()
        form.clean()
        assert called == []

    def test_clean_form_can_reject(self):
        """clean_form() returning False means clean() returns False."""

        class CrossFieldForm(Form):
            password = StringField("Password", required=True)
            confirm = StringField("Confirm", required=True)

            def clean_form(self):
                if self.password.value != self.confirm.value:
                    self.confirm.errors = ["Passwords do not match"]
                    self.confirm.has_error = True
                    self.confirm.error_messages = ["Passwords do not match"]
                    return False
                return True

        form = CrossFieldForm(data={"password": "abc", "confirm": "xyz"})
        assert form.clean() is False
        assert "Passwords do not match" in form.confirm.errors

    def test_clean_form_cross_field_pass(self):
        class CrossFieldForm(Form):
            password = StringField("Password", required=True)
            confirm = StringField("Confirm", required=True)

            def clean_form(self):
                if self.password.value != self.confirm.value:
                    return False
                return True

        form = CrossFieldForm(data={"password": "abc", "confirm": "abc"})
        assert form.clean() is True


# ── Embedded form access ────────────────────────────────────────


class TestEmbeddedFormAccess:
    def test_qualified_access(self):
        bf = OrderForm().billing_street
        assert bf.name == "billing_street"

    def test_unqualified_unambiguous(self):
        assert OrderForm().notes.name == "notes"

    def test_unqualified_ambiguous_raises(self):
        with pytest.raises(AmbiguousFieldError) as exc_info:
            _ = OrderForm().street
        assert "street" in exc_info.value.name
        assert len(exc_info.value.candidates) == 2

    def test_embedded_get_data(self):
        form = OrderForm(data={"billing_street": "123 Main", "shipping_city": "London"})
        data = form.get_data()
        assert data["billing_street"] == "123 Main"
        assert data["shipping_city"] == "London"

    def test_embedded_set_data(self):
        form = OrderForm()
        form.set_data({"billing_street": "456 Oak"})
        assert form.billing_street.value == "456 Oak"


# ── Inheritance ─────────────────────────────────────────────────


class TestFormInheritance:
    def test_subclass_inherits_fields(self):

        class ExtendedForm(SimpleForm):
            email = StringField("Email")

        defs = ExtendedForm._field_definitions
        assert "name" in defs
        assert "age" in defs
        assert "email" in defs
        assert len(defs) == 3

    def test_subclass_field_order(self):

        class ExtendedForm(SimpleForm):
            email = StringField("Email")

        assert list(ExtendedForm._field_definitions.keys()) == [
            "name",
            "age",
            "email",
        ]


# ── Title and layout class ─────────────────────────────────────


class TestFormTitle:
    def test_title(self):
        assert TitledForm().title == "My Form"

    def test_no_title(self):
        assert SimpleForm().title == ""


class TestFormLayoutClass:
    def test_default_none(self):
        assert SimpleForm.layout_class is None

    def test_custom(self):
        from textual_wtf.layouts import FormLayout

        class CustomForm(Form):
            layout_class = FormLayout
            name = StringField("Name")

        assert CustomForm.layout_class is FormLayout

    def test_instance_override(self):
        from textual_wtf.layouts import FormLayout

        form = SimpleForm(layout_class=FormLayout)
        assert form._layout_class is FormLayout


# ── Label style cascade ────────────────────────────────────────


class TestLabelStyleCascade:
    def test_form_level_propagates(self):

        class BesideForm(Form):
            label_style = "beside"
            name = StringField("Name")
            email = StringField("Email")

        form = BesideForm()
        assert form.name.label_style == "beside"
        assert form.email.label_style == "beside"

    def test_field_level_overrides_form_level(self):

        class MixedForm(Form):
            label_style = "beside"
            name = StringField("Name", label_style="placeholder")
            email = StringField("Email")

        form = MixedForm()
        assert form.name.label_style == "placeholder"
        assert form.email.label_style == "beside"

    def test_instance_label_style_override(self):
        form = SimpleForm(label_style="beside")
        assert form.name.label_style == "beside"
