"""Validators for form fields"""
import re
from abc import ABC, abstractmethod
from typing import Any, Optional
from textual.validation import Validator, ValidationResult


SIMPLE_EMAIL_PAT = re.compile(r".+\@.+\..+")


class EvenInteger(Validator):
    """Example custom validator - validates even integers"""

    def validate(self, value: str) -> ValidationResult:
        try:
            int_value = int(value)
        except ValueError:
            return self.success()

        if int_value % 2 != 0:
            return self.failure("Must be an even number")
        return self.success()


class Palindromic(Validator):
    """Example custom validator - validates palindromes"""

    def validate(self, value: str) -> ValidationResult:
        if value == value[::-1]:
            return self.success()
        return self.failure("Must be a palindrome")


class EmailValidator(Validator):
    """Simple email validator - rejects addresses like 'user@name' without TLD"""

    def validate(self, value: str) -> ValidationResult:
        if not value or not SIMPLE_EMAIL_PAT.match(value):
            return self.failure("Must be a valid email address")
        return self.success()
