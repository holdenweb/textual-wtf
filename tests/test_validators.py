"""Tests for textual_wtf.validators."""

import pytest

from textual_wtf.exceptions import ValidationError
from textual_wtf.validators import (
    EmailValidator,
    FunctionValidator,
    MaxLength,
    MaxValue,
    MinLength,
    MinValue,
    Required,
    Validator,
)


class TestRequired:
    def test_none_fails(self):
        assert not Required().validate(None).is_valid

    def test_empty_string_fails(self):
        assert not Required().validate("").is_valid

    def test_whitespace_only_fails(self):
        assert not Required().validate("   ").is_valid

    def test_empty_list_fails(self):
        assert not Required().validate([]).is_valid

    def test_nonempty_string_passes(self):
        assert Required().validate("hello").is_valid

    def test_zero_passes(self):
        assert Required().validate(0).is_valid

    def test_false_passes(self):
        assert Required().validate(False).is_valid

    def test_failure_description_present(self):
        result = Required().validate(None)
        assert len(result.failure_descriptions) > 0
        assert "required" in result.failure_descriptions[0].lower()


class TestMinLength:
    def test_below_minimum_fails(self):
        assert not MinLength(3).validate("ab").is_valid

    def test_at_minimum_passes(self):
        assert MinLength(3).validate("abc").is_valid

    def test_above_minimum_passes(self):
        assert MinLength(3).validate("abcd").is_valid

    def test_none_passes(self):
        assert MinLength(3).validate(None).is_valid


class TestMaxLength:
    def test_above_maximum_fails(self):
        assert not MaxLength(5).validate("abcdef").is_valid

    def test_at_maximum_passes(self):
        assert MaxLength(5).validate("abcde").is_valid

    def test_below_maximum_passes(self):
        assert MaxLength(5).validate("abc").is_valid


class TestMinValue:
    def test_below_minimum_fails(self):
        assert not MinValue(10).validate(5).is_valid

    def test_at_minimum_passes(self):
        assert MinValue(10).validate(10).is_valid

    def test_above_minimum_passes(self):
        assert MinValue(10).validate(15).is_valid

    def test_float_boundary(self):
        assert not MinValue(3.14).validate(3.0).is_valid
        assert MinValue(3.14).validate(3.14).is_valid

    def test_none_passes(self):
        assert MinValue(10).validate(None).is_valid


class TestMaxValue:
    def test_above_maximum_fails(self):
        assert not MaxValue(100).validate(101).is_valid

    def test_at_maximum_passes(self):
        assert MaxValue(100).validate(100).is_valid

    def test_below_maximum_passes(self):
        assert MaxValue(100).validate(50).is_valid


class TestEmailValidator:
    def test_valid_email(self):
        assert EmailValidator().validate("user@example.com").is_valid

    def test_valid_with_dots(self):
        assert EmailValidator().validate("first.last@example.co.uk").is_valid

    def test_missing_at_sign(self):
        assert not EmailValidator().validate("userexample.com").is_valid

    def test_missing_domain(self):
        assert not EmailValidator().validate("user@").is_valid

    def test_missing_tld(self):
        assert not EmailValidator().validate("user@example").is_valid

    def test_empty_string_passes(self):
        assert EmailValidator().validate("").is_valid

    def test_none_passes(self):
        assert EmailValidator().validate(None).is_valid


class TestValidatorBase:
    def test_base_succeeds(self):
        assert Validator().validate("anything").is_valid


class TestFunctionValidator:
    def test_success_when_callable_returns_normally(self):
        v = FunctionValidator(lambda val: None)
        assert v.validate("anything").is_valid

    def test_failure_when_callable_raises_validation_error(self):
        def reject_all(val):
            raise ValidationError("Always fails.")

        result = FunctionValidator(reject_all).validate("x")
        assert not result.is_valid
        assert "Always fails." in result.failure_descriptions[0]

    def test_failure_description_preserved(self):
        def check(val):
            if len(val) < 3:
                raise ValidationError("Too short.")

        result = FunctionValidator(check).validate("ab")
        assert not result.is_valid
        assert "Too short." in result.failure_descriptions[0]

    def test_passes_value_to_callable(self):
        seen = []

        def capture(val):
            seen.append(val)

        FunctionValidator(capture).validate("hello")
        assert seen == ["hello"]
