"""Integration tests using Textual's run_test for headless testing"""
import pytest
from textual.app import App
from textual_forms import Form, StringField, IntegerField, BooleanField, ChoiceField


class SimpleForm(Form):
    """Simple form for testing"""
    name = StringField(label="Name", required=True)
    age = IntegerField(label="Age", min_value=0, max_value=130)
    active = BooleanField(label="Active")


class ChoiceForm(Form):
    """Form with choices for testing"""
    country = ChoiceField(
        label="Country",
        choices=[
            ("us", "United States"),
            ("uk", "United Kingdom"),
            ("ca", "Canada"),
        ],
        required=True
    )


class TestFormWithoutAppContext:
    """Test form functionality that doesn't require app context"""
    
    def test_form_creation(self):
        """Test form can be created without app"""
        form = SimpleForm()
        assert form is not None
        assert "name" in form.fields
        assert "age" in form.fields
        assert "active" in form.fields
    
    def test_get_fields_dict(self):
        """Test get_fields_dict utility method"""
        form = SimpleForm()
        fields = form.get_fields_dict()
        assert isinstance(fields, dict)
        assert "name" in fields
        assert "age" in fields
        assert "active" in fields
    
    def test_get_field_names(self):
        """Test get_field_names utility method"""
        form = SimpleForm()
        names = form.get_field_names()
        assert names == ["name", "age", "active"]
    
    def test_get_field(self):
        """Test get_field utility method"""
        form = SimpleForm()
        
        name_field = form.get_field("name")
        assert name_field is not None
        assert name_field.label == "Name"
        assert name_field.required is True
        
        nonexistent = form.get_field("nonexistent")
        assert nonexistent is None
    
    def test_field_configuration(self):
        """Test field configuration without rendering"""
        form = SimpleForm()
        
        age_field = form.get_field("age")
        assert age_field.min_value == 0
        assert age_field.max_value == 130
        
        active_field = form.get_field("active")
        assert active_field.to_python(True) is True
    
    def test_choice_field_configuration(self):
        """Test choice field without rendering"""
        form = ChoiceForm()
        country_field = form.get_field("country")
        
        assert country_field.choices == [
            ("us", "United States"),
            ("uk", "United Kingdom"),
            ("ca", "Canada"),
        ]
        assert country_field.required is True


@pytest.mark.asyncio
class TestFormWithAppContext:
    """Test form functionality using Textual's run_test for headless testing"""
    
    async def test_form_rendering(self):
        """Test that form renders with app context"""
        
        class TestApp(App):
            def compose(self):
                yield SimpleForm(title="Test Form").render()
        
        app = TestApp()
        async with app.run_test() as pilot:
            # Form should be rendered
            assert app.screen is not None
    
    async def test_widget_creation_in_app(self):
        """Test widget creation within app context"""
        
        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.form = None
            
            def compose(self):
                self.form = SimpleForm()
                yield self.form.render()
        
        app = TestApp()
        async with app.run_test() as pilot:
            # Widgets should be created
            assert app.form is not None
            assert "name" in app.form.fields
            
            # Fields should have widgets
            name_field = app.form.get_field("name")
            assert name_field.widget is not None
    
    async def test_form_data_in_app(self):
        """Test form data handling within app"""
        
        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.form = None
            
            def compose(self):
                initial_data = {
                    "name": "John Doe",
                    "age": 30,
                    "active": True
                }
                self.form = SimpleForm(data=initial_data)
                yield self.form.render()
        
        app = TestApp()
        async with app.run_test() as pilot:
            # Get data from form
            data = app.form.get_data()
            assert data["name"] == "John Doe"
            assert data["age"] == 30
            assert data["active"] is True


class TestFormUtilityMethods:
    """Test the utility methods"""
    
    def test_field_introspection(self):
        """Test inspecting form structure"""
        form = SimpleForm()
        
        # Get all field names
        names = form.get_field_names()
        assert len(names) == 3
        
        # Get specific field
        name_field = form.get_field("name")
        assert name_field.label == "Name"
        
        # Get all fields
        fields = form.get_fields_dict()
        assert len(fields) == 3
        for name, field in fields.items():
            assert field.name == name
            assert field.form is form
    
    def test_field_order(self):
        """Test custom field ordering"""
        form = SimpleForm(field_order=["active", "name", "age"])
        names = form.get_field_names()
        assert names == ["active", "name", "age"]
    
    def test_initial_data(self):
        """Test form with initial data"""
        initial = {
            "name": "Jane Smith",
            "age": 25,
            "active": False
        }
        form = SimpleForm(data=initial)
        
        # Data should be stored
        assert form.data == initial


class TestDocumentedPatterns:
    """Test documented usage patterns"""
    
    def test_pattern_inspect_without_render(self):
        """Test inspecting form structure without rendering"""
        form = SimpleForm()
        
        # Pattern 1: Get field information
        for field_name in form.get_field_names():
            field = form.get_field(field_name)
            assert field.label is not None
        
        assert len(form.get_field_names()) == 3
    
    def test_pattern_test_field_logic(self):
        """Test field conversion logic without rendering"""
        form = SimpleForm()
        
        # Pattern 2: Test field logic directly
        name_field = form.get_field("name")
        assert name_field.to_python("  Test  ") == "Test"
        assert name_field.to_python("") is None
        
        age_field = form.get_field("age")
        assert age_field.to_python("42") == 42
        assert age_field.to_python("") is None
    
    def test_pattern_validate_configuration(self):
        """Test validating form configuration"""
        form = ChoiceForm()
        
        # Pattern 3: Validate form is configured correctly
        country = form.get_field("country")
        assert len(country.choices) == 3
        assert country.required is True
        
        # Verify choices are correct
        values = [choice[0] for choice in country.choices]
        labels = [choice[1] for choice in country.choices]
        assert "us" in values
        assert "United States" in labels
