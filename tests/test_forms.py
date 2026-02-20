"""Tests for Form metaclass, field access, composition, and data methods."""
import pytest
from textual_wtf import (
    AmbiguousFieldError,
    BoundField,
    Form,
    FormError,
    IntegerField,
    StringField,
    TextField,
    ValidationError,
)


# ── Metaclass / class structure ───────────────────────────────────────────────

class TestFormMetaclass:
    def test_base_fields_collected(self):
        class MyForm(Form):
            name = StringField(label="Name")
            age  = IntegerField(label="Age")

        assert "name" in MyForm._base_fields
        assert "age" in MyForm._base_fields

    def test_base_fields_ordered(self):
        class MyForm(Form):
            first  = StringField(label="A")
            second = StringField(label="B")
            third  = StringField(label="C")

        assert list(MyForm._base_fields) == ["first", "second", "third"]

    def test_field_descriptors_removed_from_class(self):
        """Field instances must not remain as class attributes."""
        class MyForm(Form):
            name = StringField(label="Name")

        assert not isinstance(MyForm.__dict__.get("name"), StringField)

    def test_inheritance(self):
        class BaseF(Form):
            name = StringField(label="Name")

        class ChildF(BaseF):
            email = StringField(label="Email")

        assert "name" in ChildF._base_fields
        assert "email" in ChildF._base_fields

    def test_name_collision_in_composition_raises(self):
        class Addr(Form):
            street = StringField(label="Street")

        with pytest.raises(FormError, match="collision"):
            class OrderForm(Form):
                billing  = Addr.compose(prefix="billing")
                billing_street = StringField(label="Oops")  # collision!


# ── Field access on instances ─────────────────────────────────────────────────

class TestFieldAccess:
    def setup_method(self):
        class MyForm(Form):
            name = StringField(label="Name")
            age  = IntegerField(label="Age")

        self.MyForm = MyForm
        self.form = MyForm()

    def test_attribute_access_returns_bound_field(self):
        assert isinstance(self.form.name, BoundField)

    def test_attribute_access_is_correct_field(self):
        assert self.form.name.field is self.MyForm._base_fields["name"]

    def test_get_field_equivalent(self):
        assert self.form.get_field("name") is self.form.name

    def test_unknown_field_raises_attribute_error(self):
        with pytest.raises(AttributeError):
            _ = self.form.nonexistent

    def test_bound_fields_dict(self):
        assert set(self.form.bound_fields) == {"name", "age"}

    def test_fields_alias(self):
        assert self.form.fields is self.form.bound_fields


# ── Data methods ──────────────────────────────────────────────────────────────

class TestDataMethods:
    def setup_method(self):
        class MyForm(Form):
            name = StringField(label="Name")
            age  = IntegerField(label="Age")

        self.form = MyForm()

    def test_get_data_empty_form(self):
        data = self.form.get_data()
        assert data == {"name": None, "age": None}

    def test_set_data_and_get_data(self):
        self.form.set_data({"name": "Alice", "age": 30})
        data = self.form.get_data()
        assert data["name"] == "Alice"
        assert data["age"] == 30

    def test_set_data_ignores_unknown_keys(self):
        self.form.set_data({"name": "Bob", "unknown": "x"})
        assert self.form.name.value == "Bob"

    def test_initial_data_via_constructor(self):
        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm(data={"name": "Pre-filled"})
        assert form.name._initial_value == "Pre-filled"

    def test_bound_field_value_settable(self):
        self.form.name.value = "Charlie"
        assert self.form.get_data()["name"] == "Charlie"


# ── Validation ────────────────────────────────────────────────────────────────

class TestFormValidation:
    def test_is_valid_all_pass(self):
        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm()
        form.name.value = "Alice"
        assert form.is_valid()

    def test_is_valid_required_fails(self):
        class MyForm(Form):
            name = StringField(label="Name", required=True)

        form = MyForm()
        assert not form.is_valid()
        assert form.name.errors

    def test_validate_populates_errors_on_bound_field(self):
        class MyForm(Form):
            name = StringField(label="Name", required=True)

        form = MyForm()
        form.validate()
        assert form.name.has_error
        assert form.name.error_message

    def test_validate_clears_errors_after_fix(self):
        class MyForm(Form):
            name = StringField(label="Name", required=True)

        form = MyForm()
        form.validate()
        assert form.name.has_error

        form.name.value = "Fixed"
        form.validate()
        assert not form.name.has_error


# ── Form composition ──────────────────────────────────────────────────────────

class TestComposition:
    def setup_method(self):
        class AddressForm(Form):
            street = StringField(label="Street")
            city   = StringField(label="City")

        class OrderForm(Form):
            billing  = AddressForm.compose(prefix="billing")
            shipping = AddressForm.compose(prefix="shipping")
            notes    = TextField(label="Notes")

        self.OrderForm = OrderForm
        self.form = OrderForm()

    def test_prefixed_fields_exist(self):
        fields = set(self.form.bound_fields)
        assert "billing_street" in fields
        assert "billing_city" in fields
        assert "shipping_street" in fields
        assert "shipping_city" in fields
        assert "notes" in fields

    def test_qualified_access(self):
        assert isinstance(self.form.billing_street, BoundField)

    def test_unqualified_access_unique(self):
        """'notes' is unique across the form — unqualified access works."""
        assert isinstance(self.form.notes, BoundField)

    def test_unqualified_access_ambiguous_raises(self):
        """'street' matches both billing_street and shipping_street."""
        with pytest.raises(AmbiguousFieldError) as exc_info:
            _ = self.form.street
        assert "billing_street" in exc_info.value.candidates

    def test_data_is_flat(self):
        data = self.form.get_data()
        assert "billing_street" in data
        assert "shipping_street" in data

    def test_set_prefixed_field_value(self):
        self.form.billing_street.value = "123 Main St"
        assert self.form.get_data()["billing_street"] == "123 Main St"

    def test_nested_composition(self):
        class NameForm(Form):
            first = StringField(label="First")
            last  = StringField(label="Last")

        class PersonForm(Form):
            contact = NameForm.compose(prefix="contact")
            age     = IntegerField(label="Age")

        class RegisterForm(Form):
            primary = PersonForm.compose(prefix="primary")

        form = RegisterForm()
        assert "primary_contact_first" in form.bound_fields
        assert "primary_contact_last" in form.bound_fields
        assert "primary_age" in form.bound_fields


# ── Form.render ────────────────────────────────────────────────────────────────

class TestFormRender:
    def test_render_returns_layout(self):
        from textual_wtf import DefaultFormLayout

        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm()
        layout = form.render()
        assert isinstance(layout, DefaultFormLayout)
        assert layout.form is form

    def test_render_with_custom_layout_class(self):
        from textual_wtf import DefaultFormLayout, FormLayout

        class CustomLayout(FormLayout):
            def compose_form(self):
                yield from ()

        class MyForm(Form):
            layout_class = CustomLayout
            name = StringField(label="Name")

        form = MyForm()
        layout = form.render()
        assert isinstance(layout, CustomLayout)

    def test_render_layout_class_override_in_constructor(self):
        from textual_wtf import FormLayout

        class CustomLayout(FormLayout):
            def compose_form(self):
                yield from ()

        class MyForm(Form):
            name = StringField(label="Name")

        form = MyForm(layout_class=CustomLayout)
        assert isinstance(form.render(), CustomLayout)


# ── BoundField.disabled ────────────────────────────────────────────────────────

class TestBoundFieldDisabled:
    def test_disabled_initialised_from_field(self):
        class MyForm(Form):
            name = StringField(label="Name", disabled=True)

        form = MyForm()
        assert form.name.disabled is True

    def test_disabled_independent_per_instance(self):
        class MyForm(Form):
            name = StringField(label="Name", disabled=False)

        form1 = MyForm()
        form2 = MyForm()
        form1.name.disabled = True
        assert form2.name.disabled is False


# ── label_style / help_style precedence ──────────────────────────────────────

class TestStylePrecedence:
    def test_form_level_default_applied(self):
        class MyForm(Form):
            label_style = "beside"
            name = StringField(label="Name")

        form = MyForm()
        assert form.name._effective_label_style() == "beside"

    def test_field_level_overrides_form_default(self):
        class MyForm(Form):
            label_style = "beside"
            name = StringField(label="Name", label_style="placeholder")

        form = MyForm()
        assert form.name._effective_label_style() == "placeholder"

    def test_call_site_overrides_field_level(self):
        class MyForm(Form):
            label_style = "beside"
            name = StringField(label="Name", label_style="placeholder")

        form = MyForm()
        form.name(label_style="above")
        assert form.name._effective_label_style() == "above"
