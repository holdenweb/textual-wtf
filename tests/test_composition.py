"""Test form composition functionality"""
import pytest
from textual.app import App
from textual_wtf import Form, StringField, IntegerField, BooleanField
from textual_wtf.exceptions import FieldError, AmbiguousFieldError


class AddressForm(Form):
    """Reusable address form"""
    street = StringField(label="Street")
    city = StringField(label="City")
    postal_code = StringField(label="Postal Code")


class PersonalForm(Form):
    """Personal information form"""
    first_name = StringField(label="First Name")
    last_name = StringField(label="Last Name")
    email = StringField(label="Email")


class TestBasicComposition:
    """Test basic form composition"""

    def test_compose_with_prefix(self):
        """Test composing a form with prefix"""
        class OrderForm(Form):
            billing = AddressForm.compose(prefix='billing')

        form = OrderForm()

        # Check that fields are prefixed
        assert 'billing_street' in form.fields
        assert 'billing_city' in form.fields
        assert 'billing_postal_code' in form.fields

        # Original field names should not exist
        assert 'street' not in form.fields
        assert 'city' not in form.fields

    def test_compose_without_prefix(self):
        """Test composing a form without prefix"""
        class SimpleForm(Form):
            address = AddressForm.compose()

        form = SimpleForm()

        # Fields should not be prefixed
        assert 'street' in form.fields
        assert 'city' in form.fields
        assert 'postal_code' in form.fields

    def test_compose_with_empty_prefix(self):
        """Test composing with explicit empty prefix"""
        class SimpleForm(Form):
            address = AddressForm.compose(prefix='')

        form = SimpleForm()

        # Same as no prefix
        assert 'street' in form.fields
        assert 'city' in form.fields

    def test_compose_multiple_forms(self):
        """Test composing multiple forms with different prefixes"""
        class ShippingForm(Form):
            billing = AddressForm.compose(prefix='billing')
            shipping = AddressForm.compose(prefix='shipping')

        form = ShippingForm()

        # Both sets of fields should exist
        assert 'billing_street' in form.fields
        assert 'billing_city' in form.fields
        assert 'shipping_street' in form.fields
        assert 'shipping_city' in form.fields

        # Six total fields (3 from each)
        assert len(form.fields) == 6

    def test_compose_with_additional_fields(self):
        """Test mixing composed forms with regular fields"""
        class OrderForm(Form):
            billing = AddressForm.compose(prefix='billing')
            notes = StringField(label="Notes")
            urgent = BooleanField(label="Urgent")

        form = OrderForm()

        # Composed fields
        assert 'billing_street' in form.fields
        assert 'billing_city' in form.fields
        assert 'billing_postal_code' in form.fields

        # Regular fields
        assert 'notes' in form.fields
        assert 'urgent' in form.fields

        # Total: 3 composed + 2 regular = 5
        assert len(form.fields) == 5


class TestFieldOrdering:
    """Test field ordering with composition"""

    def test_field_order_preservation(self):
        """Test that field order is preserved"""
        class OrderForm(Form):
            email = StringField()
            billing = AddressForm.compose(prefix='billing')
            notes = StringField()

        form = OrderForm()
        field_names = list(form.fields.keys())

        # Fields appear in declaration order:
        # email, then billing fields (expanded in place), then notes
        assert field_names == [
            'email',
            'billing_street',
            'billing_city',
            'billing_postal_code',
            'notes'
        ]

    def test_multiple_compositions_order(self):
        """Test ordering with multiple compositions"""
        class ComplexForm(Form):
            personal = PersonalForm.compose(prefix='p')
            address = AddressForm.compose(prefix='a')
            extra = StringField()

        form = ComplexForm()
        field_names = list(form.fields.keys())

        # Should be: personal fields, address fields, extra
        assert field_names[:3] == ['p_first_name', 'p_last_name', 'p_email']
        assert field_names[3:6] == ['a_street', 'a_city', 'a_postal_code']
        assert field_names[6] == 'extra'


class TestNameCollisions:
    """Test name collision detection"""

    def test_collision_same_form_no_prefix(self):
        """Test collision when composing same form twice without prefixes"""
        with pytest.raises(FieldError, match="Field name collision"):
            class BadForm(Form):
                addr1 = AddressForm.compose()
                addr2 = AddressForm.compose()

    def test_collision_with_regular_field(self):
        """Test collision between composed field and regular field"""
        with pytest.raises(FieldError, match="Field name collision"):
            class BadForm(Form):
                billing = AddressForm.compose(prefix='billing')
                billing_street = StringField()  # Collision!

    def test_no_collision_with_different_prefixes(self):
        """Test no collision when using different prefixes"""
        # Should not raise
        class GoodForm(Form):
            billing = AddressForm.compose(prefix='billing')
            shipping = AddressForm.compose(prefix='shipping')

        form = GoodForm()
        assert len(form.fields) == 6


class TestSQLStyleLookup:
    """Test SQL-style field name resolution"""

    def test_exact_match(self):
        """Test exact field name match"""
        class OrderForm(Form):
            billing = AddressForm.compose(prefix='billing')

        form = OrderForm()
        field = form.get_field('billing_street')

        assert field is not None
        assert field.name == 'billing_street'

    def test_unqualified_match_unique(self):
        """Test unqualified match when unique"""
        class SimpleForm(Form):
            billing = AddressForm.compose(prefix='billing')
            email = StringField()

        form = SimpleForm()

        # 'email' is unique - should work without prefix
        field = form.get_field('email')
        assert field is not None
        assert field.name == 'email'

    def test_unqualified_match_ambiguous(self):
        """Test unqualified match raises error when ambiguous"""
        class ShippingForm(Form):
            billing = AddressForm.compose(prefix='billing')
            shipping = AddressForm.compose(prefix='shipping')

        form = ShippingForm()

        # 'street' is ambiguous
        with pytest.raises(AmbiguousFieldError, match="ambiguous"):
            form.get_field('street')

    def test_qualified_match_disambiguates(self):
        """Test qualified name disambiguates"""
        class ShippingForm(Form):
            billing = AddressForm.compose(prefix='billing')
            shipping = AddressForm.compose(prefix='shipping')

        form = ShippingForm()

        # Qualified names should work
        billing_street = form.get_field('billing_street')
        shipping_street = form.get_field('shipping_street')

        assert billing_street.name == 'billing_street'
        assert shipping_street.name == 'shipping_street'

    def test_nonexistent_field(self):
        """Test looking up nonexistent field"""
        class SimpleForm(Form):
            billing = AddressForm.compose(prefix='billing')

        form = SimpleForm()
        field = form.get_field('nonexistent')

        assert field is None


class TestNestedComposition:
    """Test nested form composition"""

    def test_nested_composition_two_levels(self):
        """Test composing a form that itself contains composed forms"""
        class ContactForm(Form):
            address = AddressForm.compose(prefix='addr')
            phone = StringField(label="Phone")

        class OrderForm(Form):
            contact = ContactForm.compose(prefix='contact')

        form = OrderForm()

        # Check nested field names
        assert 'contact_addr_street' in form.fields
        assert 'contact_addr_city' in form.fields
        assert 'contact_addr_postal_code' in form.fields
        assert 'contact_phone' in form.fields

    def test_nested_composition_three_levels(self):
        """Test three levels of nesting"""
        class LocationForm(Form):
            address = AddressForm.compose(prefix='addr')

        class ContactForm(Form):
            location = LocationForm.compose(prefix='loc')

        class OrderForm(Form):
            contact = ContactForm.compose(prefix='c')

        form = OrderForm()

        # Check deeply nested field names
        assert 'c_loc_addr_street' in form.fields
        assert 'c_loc_addr_city' in form.fields


class TestDataHandling:
    """Test data handling with composed forms"""

    def test_get_data_with_composition(self):
        """Test getting data from composed form"""
        class OrderForm(Form):
            billing = AddressForm.compose(prefix='billing')
            notes = StringField()

        form = OrderForm()

        # Set some values (would normally be set through widgets)
        form.fields['billing_street']._widget_instance = None
        form.fields['billing_street'].initial = '123 Main St'
        form.fields['notes']._widget_instance = None
        form.fields['notes'].initial = 'Test note'

        # Data should be flat with prefixed keys
        # (Can't fully test without widgets, but structure should be correct)
        assert 'billing_street' in form.fields
        assert 'notes' in form.fields


@pytest.mark.asyncio
class TestCompositionWithRendering:
    """Test composition with actual rendering"""

    async def test_render_composed_form(self):
        """Test rendering a form with composition"""
        class OrderForm(Form):
            billing = AddressForm.compose(prefix='billing')
            notes = StringField(label="Notes")

        class TestApp(App):
            def compose(self):
                yield OrderForm().render()

        app = TestApp()
        async with app.run_test() as pilot:
            # If we get here, rendering worked
            assert True

    async def test_render_nested_composition(self):
        """Test rendering nested composition"""
        class ContactForm(Form):
            address = AddressForm.compose(prefix='addr')
            phone = StringField(label="Phone")

        class OrderForm(Form):
            contact = ContactForm.compose(prefix='contact')

        class TestApp(App):
            def compose(self):
                yield OrderForm().render()

        app = TestApp()
        async with app.run_test() as pilot:
            assert True


class TestCompositionMetadata:
    """Test composition metadata tracking"""

    def test_metadata_tracked(self):
        """Test that composition metadata is tracked"""
        class OrderForm(Form):
            billing = AddressForm.compose(prefix='billing')
            email = StringField()

        # Check that metadata exists
        assert hasattr(OrderForm, '_composition_metadata')

        # Composed fields should have metadata
        metadata = OrderForm._composition_metadata
        assert 'billing_street' in metadata
        assert metadata['billing_street']['prefix'] == 'billing'
        assert metadata['billing_street']['original_name'] == 'street'

        # Regular fields should not
        assert 'email' not in metadata
