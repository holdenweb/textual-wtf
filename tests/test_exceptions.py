"""Tests for exception classes."""
from textual_wtf import (
    AmbiguousFieldError,
    FieldError,
    FormError,
    ValidationError,
)


def test_validation_error_message():
    exc = ValidationError("bad value")
    assert exc.message == "bad value"
    assert str(exc) == "bad value"
    assert isinstance(exc, Exception)


def test_field_error_is_exception():
    exc = FieldError("bad config")
    assert isinstance(exc, Exception)
    assert str(exc) == "bad config"


def test_form_error_is_exception():
    exc = FormError("collision")
    assert isinstance(exc, Exception)


def test_ambiguous_field_error():
    exc = AmbiguousFieldError("street", ["billing_street", "shipping_street"])
    assert exc.name == "street"
    assert exc.candidates == ["billing_street", "shipping_street"]
    assert "street" in str(exc)
    assert "billing_street" in str(exc)


def test_exception_hierarchy():
    # All are plain Exception subclasses (not each other).
    assert issubclass(ValidationError, Exception)
    assert issubclass(FieldError, Exception)
    assert issubclass(FormError, Exception)
    assert issubclass(AmbiguousFieldError, Exception)
