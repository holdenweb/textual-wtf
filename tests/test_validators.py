"""Test validators"""
import pytest
from textual_forms.validators import (
    RequiredValidator, MinLengthValidator, MaxLengthValidator,
    MinValueValidator, MaxValueValidator, EvenInteger, Palindromic,
    EmailValidator
)
from textual_forms.exceptions import ValidationError


class TestRequiredValidator:
    """Test RequiredValidator"""
    
    def test_valid_value(self):
        """Test with valid value"""
        validator = RequiredValidator()
        validator("test")  # Should not raise
    
    def test_none_value(self):
        """Test with None"""
        validator = RequiredValidator()
        with pytest.raises(ValidationError):
            validator(None)
    
    def test_empty_string(self):
        """Test with empty string"""
        validator = RequiredValidator()
        with pytest.raises(ValidationError):
            validator("")
    
    def test_whitespace_string(self):
        """Test with whitespace"""
        validator = RequiredValidator()
        with pytest.raises(ValidationError):
            validator("   ")


class TestMinLengthValidator:
    """Test MinLengthValidator"""
    
    def test_valid_length(self):
        """Test with valid length"""
        validator = MinLengthValidator(5)
        validator("hello")  # Should not raise
    
    def test_too_short(self):
        """Test with too short value"""
        validator = MinLengthValidator(5)
        with pytest.raises(ValidationError):
            validator("hi")
    
    def test_none_value(self):
        """Test with None"""
        validator = MinLengthValidator(5)
        validator(None)  # Should not raise


class TestMaxLengthValidator:
    """Test MaxLengthValidator"""
    
    def test_valid_length(self):
        """Test with valid length"""
        validator = MaxLengthValidator(10)
        validator("hello")  # Should not raise
    
    def test_too_long(self):
        """Test with too long value"""
        validator = MaxLengthValidator(5)
        with pytest.raises(ValidationError):
            validator("toolong")


class TestMinValueValidator:
    """Test MinValueValidator"""
    
    def test_valid_value(self):
        """Test with valid value"""
        validator = MinValueValidator(10)
        validator(15)  # Should not raise
    
    def test_too_small(self):
        """Test with too small value"""
        validator = MinValueValidator(10)
        with pytest.raises(ValidationError):
            validator(5)


class TestMaxValueValidator:
    """Test MaxValueValidator"""
    
    def test_valid_value(self):
        """Test with valid value"""
        validator = MaxValueValidator(100)
        validator(50)  # Should not raise
    
    def test_too_large(self):
        """Test with too large value"""
        validator = MaxValueValidator(100)
        with pytest.raises(ValidationError):
            validator(150)


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
    
    def test_invalid_email(self):
        """Test with invalid email"""
        validator = EmailValidator()
        result = validator.validate("notanemail")
        assert not result.is_valid
