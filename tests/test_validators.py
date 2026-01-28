"""Test validators"""
import pytest
from textual_forms.validators import (
    EvenInteger,
    Palindromic,
    EmailValidator,
)
from textual_forms.exceptions import ValidationError


class TestEvenInteger:
    """Test EvenInteger validator"""

    def test_even_number(self):
        """Test with even number"""
        validator = EvenInteger()
        result = validator.validate("42")
        assert result.is_valid

    def test_odd_number(self):
        """Test with odd number"""
        validator = EvenInteger()
        result = validator.validate("43")
        assert not result.is_valid


class TestPalindromic:
    """Test Palindromic validator"""

    def test_palindrome(self):
        """Test with palindrome"""
        validator = Palindromic()
        result = validator.validate("racecar")
        assert result.is_valid

    def test_not_palindrome(self):
        """Test with non-palindrome"""
        validator = Palindromic()
        result = validator.validate("hello")
        assert not result.is_valid


class TestEmailValidator:
    """Test EmailValidator"""

    def test_valid_email(self):
        """Test with valid email"""
        validator = EmailValidator()
        result = validator.validate("test@example.com")
        assert result.is_valid

    @pytest.mark.parametrize("address", ["notanemail", "not@anemail", "not.anemail", "not.an@email"])
    def test_invalid_email(self, address):
        """Test with invalid email"""
        validator = EmailValidator()
        result = validator.validate(address)
        assert not result.is_valid
