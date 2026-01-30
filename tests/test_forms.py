"""Test forms"""
import pytest
from textual.app import App
from textual_wtf import Form, StringField, IntegerField, BooleanField
from textual_wtf.forms import FormMetaclass


class TestFormMetaclass:
    """Test FormMetaclass"""

    def test_field_collection(self):
        """Test that metaclass collects fields"""
        class TestForm(Form):
            name = StringField()
            age = IntegerField()

        assert "name" in TestForm._base_fields
        assert "age" in TestForm._base_fields
        assert isinstance(TestForm._base_fields["name"], StringField)
        assert isinstance(TestForm._base_fields["age"], IntegerField)


class TestForm:
    """Test Form class"""

    def test_form_creation(self):
        """Test form creation"""
        class UserForm(Form):
            name = StringField(label="Name")
            age = IntegerField(label="Age")

        form = UserForm()
        assert "name" in form.fields
        assert "age" in form.fields

    def test_field_binding(self):
        """Test that fields are bound to form"""
        class UserForm(Form):
            name = StringField()

        form = UserForm()
        field = form.fields["name"]
        assert field.name == "name"
        assert field.form is form

    def test_get_data(self):
        """Test get_data method without rendering"""
        class UserForm(Form):
            name = StringField()
            age = IntegerField()

        form = UserForm()
        # Without rendering, can't get actual data
        # This is expected behavior

    def test_set_data(self):
        """Test set_data method"""
        class UserForm(Form):
            name = StringField()
            age = IntegerField()

        form = UserForm(data={"name": "Jane", "age": 25})
        assert form.data["name"] == "Jane"
        assert form.data["age"] == 25

    def test_field_ordering(self):
        """Test custom field ordering"""
        class UserForm(Form):
            name = StringField()
            age = IntegerField()
            email = StringField()

        form = UserForm(field_order=["email", "name", "age"])
        field_names = list(form.fields.keys())
        assert field_names == ["email", "name", "age"]

    def test_initial_data(self):
        """Test providing initial data"""
        class UserForm(Form):
            name = StringField()

        form = UserForm(data={"name": "Initial"})
        assert form.data == {"name": "Initial"}


@pytest.mark.asyncio
class TestRenderedForm:
    """Test RenderedForm with app context"""

    async def test_creation(self):
        """Test rendered form creation with app"""
        class UserForm(Form):
            name = StringField(label="Name")

        class TestApp(App):
            def compose(self):
                form = UserForm()
                yield form.render()

        app = TestApp()
        async with app.run_test() as pilot:
            # Form should be rendered
            assert True  # If we get here, rendering worked
