"""Test fields"""
import pytest
from textual_forms.fields import (
    StringField, IntegerField, BooleanField, ChoiceField, TextField
)
from textual_forms.exceptions import ValidationError, FieldError
from textual_forms.widgets import FormInput, FormIntegerInput, FormCheckbox


class TestStringField:
    """Test StringField"""
    
    def test_creation(self):
        """Test field creation"""
        field = StringField(label="Test", required=True)
        assert field.label == "Test"
        assert field.required is True
    
    def test_to_python(self):
        """Test to_python conversion"""
        field = StringField()
        assert field.to_python("hello") == "hello"
        assert field.to_python("  hello  ") == "hello"
        assert field.to_python("") is None
        assert field.to_python(None) is None
    
    def test_to_widget(self):
        """Test to_widget conversion"""
        field = StringField()
        assert field.to_widget("hello") == "hello"
        assert field.to_widget(None) == ""
    
    def test_multiline(self):
        """Test multiline option"""
        field = StringField(multiline=True)
        from textual_forms.widgets import FormTextArea
        assert field.widget_class == FormTextArea


class TestIntegerField:
    """Test IntegerField"""
    
    def test_to_python(self):
        """Test to_python conversion"""
        field = IntegerField()
        assert field.to_python("42") == 42
        assert field.to_python(42) == 42
        assert field.to_python("") is None
        assert field.to_python(None) is None
    
    def test_to_python_invalid(self):
        """Test to_python with invalid value"""
        field = IntegerField()
        with pytest.raises(ValidationError):
            field.to_python("not a number")
    
    def test_validate_min_value(self):
        """Test min_value validation"""
        field = IntegerField(min_value=10)
        field.validate(15)  # Should not raise
        with pytest.raises(ValidationError):
            field.validate(5)
    
    def test_validate_max_value(self):
        """Test max_value validation"""
        field = IntegerField(max_value=100)
        field.validate(50)  # Should not raise
        with pytest.raises(ValidationError):
            field.validate(150)


class TestBooleanField:
    """Test BooleanField"""
    
    def test_to_python(self):
        """Test to_python conversion"""
        field = BooleanField()
        assert field.to_python(True) is True
        assert field.to_python(False) is False
        assert field.to_python("true") is True
        assert field.to_python("yes") is True
        assert field.to_python("false") is False
        assert field.to_python(1) is True
        assert field.to_python(0) is False


class TestChoiceField:
    """Test ChoiceField"""
    
    def test_creation(self):
        """Test field creation"""
        choices = [("us", "United States"), ("uk", "United Kingdom")]
        field = ChoiceField(choices=choices)
        assert field.choices == choices
        # Widget will receive these choices and convert them for Select widget
        assert field.widget_kwargs['choices'] == choices
    
    def test_to_python(self):
        """Test to_python conversion"""
        choices = [("us", "United States")]
        field = ChoiceField(choices=choices)
        # The field stores and returns the value (first element of tuple)
        assert field.to_python("us") == "us"
        assert field.to_python("") is None


class TestTextField:
    """Test TextField"""
    
    def test_is_multiline(self):
        """Test that TextField is multiline"""
        field = TextField()
        from textual_forms.widgets import FormTextArea
        assert field.widget_class == FormTextArea
