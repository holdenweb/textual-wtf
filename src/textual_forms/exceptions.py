"""Exceptions for textual-forms"""


class ValidationError(Exception):
    """Raised when field validation fails"""
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class FieldError(Exception):
    """Raised when there's an error with field configuration"""
    pass


class FormError(Exception):
    """Raised when there's an error with form configuration"""
    pass


class AmbiguousFieldError(FieldError):
    """Raised when an unqualified field name matches multiple fields"""
    pass
