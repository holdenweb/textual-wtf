"""Tests for built-in validators."""
import pytest
from textual_wtf import (
    EmailValidator,
    MaxLength,
    MaxValue,
    MinLength,
    MinValue,
    Required,
    ValidationError,
    Validator,
)


def test_validator_is_abstract():
    """Cannot instantiate Validator directly."""
    with pytest.raises(TypeError):
        Validator()


# ── Required ──────────────────────────────────────────────────────────────────

class TestRequired:
    def test_passes_non_empty_string(self):
        Required().validate("hello")

    def test_passes_zero(self):
        Required().validate(0)

    def test_passes_false(self):
        Required().validate(False)

    def test_fails_none(self):
        with pytest.raises(ValidationError):
            Required().validate(None)

    def test_fails_empty_string(self):
        with pytest.raises(ValidationError):
            Required().validate("")

    def test_fails_empty_list(self):
        with pytest.raises(ValidationError):
            Required().validate([])

    def test_custom_message(self):
        v = Required(message="Fill this in.")
        with pytest.raises(ValidationError) as exc_info:
            v.validate(None)
        assert exc_info.value.message == "Fill this in."


# ── MinLength / MaxLength ─────────────────────────────────────────────────────

class TestMinLength:
    def test_passes_equal(self):
        MinLength(3).validate("abc")

    def test_passes_longer(self):
        MinLength(3).validate("abcde")

    def test_fails_shorter(self):
        with pytest.raises(ValidationError):
            MinLength(3).validate("ab")

    def test_skips_none(self):
        MinLength(3).validate(None)  # no error — Required handles None


class TestMaxLength:
    def test_passes_equal(self):
        MaxLength(5).validate("hello")

    def test_passes_shorter(self):
        MaxLength(5).validate("hi")

    def test_fails_longer(self):
        with pytest.raises(ValidationError):
            MaxLength(5).validate("toolongstring")

    def test_skips_none(self):
        MaxLength(5).validate(None)


# ── MinValue / MaxValue ───────────────────────────────────────────────────────

class TestMinValue:
    def test_passes_equal(self):
        MinValue(0).validate(0)

    def test_passes_greater(self):
        MinValue(0).validate(42)

    def test_fails_less(self):
        with pytest.raises(ValidationError):
            MinValue(0).validate(-1)

    def test_skips_none(self):
        MinValue(0).validate(None)


class TestMaxValue:
    def test_passes_equal(self):
        MaxValue(100).validate(100)

    def test_passes_less(self):
        MaxValue(100).validate(50)

    def test_fails_greater(self):
        with pytest.raises(ValidationError):
            MaxValue(100).validate(101)

    def test_skips_none(self):
        MaxValue(100).validate(None)


# ── EmailValidator ────────────────────────────────────────────────────────────

class TestEmailValidator:
    def test_passes_valid(self):
        EmailValidator().validate("user@example.com")

    def test_passes_subdomain(self):
        EmailValidator().validate("user@mail.example.co.uk")

    def test_fails_no_at(self):
        with pytest.raises(ValidationError):
            EmailValidator().validate("userexample.com")

    def test_fails_no_dot_after_at(self):
        with pytest.raises(ValidationError):
            EmailValidator().validate("user@nodot")

    def test_passes_none(self):
        # None means "empty" — Required handles the empty case.
        EmailValidator().validate(None)

    def test_passes_empty_string(self):
        EmailValidator().validate("")


# ── Callable validators ───────────────────────────────────────────────────────

def test_callable_validator_passes():
    def must_be_even(value):
        if value % 2 != 0:
            raise ValidationError("Must be even.")

    must_be_even(4)  # no error


def test_callable_validator_raises():
    def must_be_even(value):
        if value % 2 != 0:
            raise ValidationError("Must be even.")

    with pytest.raises(ValidationError, match="Must be even"):
        must_be_even(3)
