"""Validators for form fields"""
import re
from abc import ABC, abstractmethod
from typing import Any, Optional
from textual.validation import Validator as TextualValidator, ValidationResult


SIMPLE_EMAIL_PAT = re.compile(r".+\@.+\..+")


class Validator(ABC):
    """Base validator class for field validation"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message
    
    @abstractmethod
    def __call__(self, value: Any) -> None:
        """Validate the value. Raise ValidationError if invalid."""
        pass
    
    def get_message(self) -> str:
        """Get the validation error message"""
        return self.message or "Validation failed"


class RequiredValidator(Validator):
    """Validates that a value is not empty"""
    
    def __init__(self, message: str = "This field is required"):
        super().__init__(message)
    
    def __call__(self, value: Any) -> None:
        if value is None or (isinstance(value, str) and not value.strip()):
            from .exceptions import ValidationError
            raise ValidationError(self.get_message())


class MinLengthValidator(Validator):
    """Validates minimum string length"""
    
    def __init__(self, min_length: int, message: Optional[str] = None):
        self.min_length = min_length
        super().__init__(message or f"Must be at least {min_length} characters")
    
    def __call__(self, value: Any) -> None:
        if value is not None and len(str(value)) < self.min_length:
            from .exceptions import ValidationError
            raise ValidationError(self.get_message())


class MaxLengthValidator(Validator):
    """Validates maximum string length"""
    
    def __init__(self, max_length: int, message: Optional[str] = None):
        self.max_length = max_length
        super().__init__(message or f"Must be at most {max_length} characters")
    
    def __call__(self, value: Any) -> None:
        if value is not None and len(str(value)) > self.max_length:
            from .exceptions import ValidationError
            raise ValidationError(self.get_message())


class MinValueValidator(Validator):
    """Validates minimum numeric value"""
    
    def __init__(self, min_value: float, message: Optional[str] = None):
        self.min_value = min_value
        super().__init__(message or f"Must be at least {min_value}")
    
    def __call__(self, value: Any) -> None:
        if value is not None and float(value) < self.min_value:
            from .exceptions import ValidationError
            raise ValidationError(self.get_message())


class MaxValueValidator(Validator):
    """Validates maximum numeric value"""
    
    def __init__(self, max_value: float, message: Optional[str] = None):
        self.max_value = max_value
        super().__init__(message or f"Must be at most {max_value}")
    
    def __call__(self, value: Any) -> None:
        if value is not None and float(value) > self.max_value:
            from .exceptions import ValidationError
            raise ValidationError(self.get_message())


class EvenInteger(TextualValidator):
    """Example custom validator - validates even integers"""
    
    def validate(self, value: str) -> ValidationResult:
        try:
            int_value = int(value)
        except ValueError:
            return self.success()
        
        if int_value % 2 != 0:
            return self.failure("Must be an even number")
        return self.success()


class Palindromic(TextualValidator):
    """Example custom validator - validates palindromes"""
    
    def validate(self, value: str) -> ValidationResult:
        if value == value[::-1]:
            return self.success()
        return self.failure("Must be a palindrome")


class EmailValidator(TextualValidator):
    """Simple email validator - rejects addresses like 'user@name' without TLD"""
    
    def validate(self, value: str) -> ValidationResult:
        if not value or not SIMPLE_EMAIL_PAT.match(value):
            return self.failure("Must be a valid email address")
        return self.success()
