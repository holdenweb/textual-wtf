"""Tests for textual_wtf.exceptions."""

import pytest

from textual_wtf.exceptions import (
    AmbiguousFieldError,
    FieldError,
    FormError,
    ValidationError,
)


class TestValidationError:
    def test_message_attribute(self):
        err = ValidationError("bad value")
        assert err.message == "bad value"

    def test_is_exception(self):
        with pytest.raises(ValidationError, match="bad value"):
            raise ValidationError("bad value")


class TestFieldError:
    def test_message_attribute(self):
        err = FieldError("bad config")
        assert err.message == "bad config"

    def test_is_exception(self):
        with pytest.raises(FieldError):
            raise FieldError("bad config")


class TestFormError:
    def test_message_attribute(self):
        err = FormError("duplicate")
        assert err.message == "duplicate"


class TestAmbiguousFieldError:
    def test_attributes(self):
        err = AmbiguousFieldError("street", ["billing_street", "shipping_street"])
        assert err.name == "street"
        assert err.candidates == ["billing_street", "shipping_street"]

    def test_message_includes_details(self):
        err = AmbiguousFieldError("street", ["billing_street", "shipping_street"])
        assert "street" in str(err)
        assert "billing_street" in str(err)
