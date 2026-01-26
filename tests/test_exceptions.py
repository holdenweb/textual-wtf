"""Test exceptions"""
import pytest
from textual_forms.exceptions import ValidationError, FieldError, FormError


def test_validation_error():
    """Test ValidationError creation and attributes"""
    err = ValidationError("Test error", "test_code")
    assert err.message == "Test error"
    assert err.code == "test_code"
    assert str(err) == "Test error"


def test_validation_error_no_code():
    """Test ValidationError without code"""
    err = ValidationError("Test error")
    assert err.message == "Test error"
    assert err.code is None


def test_field_error():
    """Test FieldError"""
    err = FieldError("Field configuration error")
    assert str(err) == "Field configuration error"


def test_form_error():
    """Test FormError"""
    err = FormError("Form configuration error")
    assert str(err) == "Form configuration error"
