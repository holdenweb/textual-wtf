"""Field implementations for forms"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, List, TYPE_CHECKING
from textual.widget import Widget
from textual.validation import Validator as TextualValidator

from .exceptions import ValidationError, FieldError

if TYPE_CHECKING:
    from .forms import Form


class Field(ABC):
    """Base field class - defines interface for all field types"""
    
    default_widget: Optional[Type[Widget]] = None
    
    def __init__(self, *, widget: Optional[Type[Widget]] = None, 
                 validators: Optional[List[TextualValidator]] = None,
                 required: bool = False, initial: Any = None, 
                 label: Optional[str] = None, help_text: Optional[str] = None, 
                 disabled: bool = False, **widget_kwargs):
        """Initialize field"""
        self.widget_class = widget or self.default_widget
        self.validators = validators or []
        self.required = required
        self.initial = initial
        self.label = label
        self.help_text = help_text
        self.disabled = disabled
        self.widget_kwargs = widget_kwargs
        
        # Set by Form metaclass
        self.name: Optional[str] = None
        self.form: Optional['Form'] = None
        
        # Runtime state
        self._widget_instance: Optional[Widget] = None
        self._errors: List[str] = []
    
    @abstractmethod
    def to_python(self, value: Any) -> Any:
        """Convert widget value to Python value"""
        pass
    
    @abstractmethod
    def to_widget(self, value: Any) -> Any:
        """Convert Python value to widget value"""
        pass
    
    def create_widget(self) -> Widget:
        """Factory method to create configured widget"""
        if not self.widget_class:
            raise FieldError(
                f"{self.__class__.__name__} must define default_widget "
                f"or pass widget parameter"
            )
        
        kwargs = self.widget_kwargs.copy()
        
        # Pass validators to widget if it supports them
        if hasattr(self.widget_class, '__init__'):
            init_params = self.widget_class.__init__.__code__.co_varnames
            if 'validators' in init_params:
                kwargs.setdefault('validators', self.validators)
        
        widget = self.widget_class(**kwargs)
        widget.field = self
        return widget
    
    def validate(self, value: Any) -> None:
        """Validate Python value - override to add custom validation"""
        self._errors = []
        if self.required and value is None:
            raise ValidationError(f"{self.label or self.name} is required")
    
    def clean(self, value: Any) -> Any:
        """Convert and validate value"""
        python_value = self.to_python(value)
        self.validate(python_value)
        return python_value
    
    @property
    def value(self) -> Any:
        """Get current field value"""
        if self._widget_instance is None:
            return self.initial
        return self.to_python(self._widget_instance.value)
    
    @value.setter
    def value(self, value: Any) -> None:
        """Set field value"""
        if self._widget_instance is not None:
            self._widget_instance.value = self.to_widget(value)
    
    @property
    def widget(self) -> Optional[Widget]:
        """Get widget instance"""
        return self._widget_instance
    
    @widget.setter
    def widget(self, widget: Widget) -> None:
        """Set widget instance"""
        self._widget_instance = widget
    
    @property
    def errors(self) -> List[str]:
        """Get validation errors"""
        return self._errors


class StringField(Field):
    """Text field (single or multi-line)"""
    
    def __init__(self, *, max_length: Optional[int] = None, 
                 min_length: Optional[int] = None, multiline: bool = False, **kwargs):
        # Choose widget based on multiline flag
        if multiline and 'widget' not in kwargs:
            from .widgets import FormTextArea
            kwargs['widget'] = FormTextArea
        else:
            from .widgets import FormInput
            if 'widget' not in kwargs:
                kwargs['widget'] = FormInput
        
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length
    
    def to_python(self, value: Any) -> Optional[str]:
        """Convert to Python string"""
        if value in (None, ''):
            return None
        return str(value).strip()
    
    def to_widget(self, value: Any) -> str:
        """Convert to widget string"""
        return value if value is not None else ''


class IntegerField(Field):
    """Integer field"""
    
    def __init__(self, *, min_value: Optional[int] = None, 
                 max_value: Optional[int] = None, **kwargs):
        from .widgets import FormIntegerInput
        if 'widget' not in kwargs:
            kwargs['widget'] = FormIntegerInput
        
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def to_python(self, value: Any) -> Optional[int]:
        """Convert to Python int"""
        if value in (None, ''):
            return None
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid integer: {value}") from e
    
    def to_widget(self, value: Any) -> str:
        """Convert to widget string"""
        return str(value) if value is not None else ''
    
    def validate(self, value: Any) -> None:
        """Validate integer constraints"""
        super().validate(value)
        if value is not None:
            if self.min_value is not None and value < self.min_value:
                raise ValidationError(f"Must be at least {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                raise ValidationError(f"Must be at most {self.max_value}")


class BooleanField(Field):
    """Boolean/checkbox field"""
    
    def __init__(self, **kwargs):
        from .widgets import FormCheckbox
        if 'widget' not in kwargs:
            kwargs['widget'] = FormCheckbox
        super().__init__(**kwargs)
    
    def to_python(self, value: Any) -> bool:
        """Convert to Python bool"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'on')
        return bool(value)
    
    def to_widget(self, value: Any) -> bool:
        """Convert to widget bool"""
        return self.to_python(value)


class ChoiceField(Field):
    """Select/dropdown field"""
    
    def __init__(self, *, choices: List[tuple[str, str]], **kwargs):
        from .widgets import FormSelect
        if 'widget' not in kwargs:
            kwargs['widget'] = FormSelect
        
        super().__init__(**kwargs)
        self.choices = choices
        self.widget_kwargs['choices'] = choices
        self.widget_kwargs['allow_blank'] = not kwargs.get('required', False)
    
    def to_python(self, value: Any) -> Optional[str]:
        """Convert to Python string"""
        if value in (None, ''):
            return None
        return str(value)
    
    def to_widget(self, value: Any) -> str:
        """Convert to widget string"""
        return value if value is not None else ''


class TextField(StringField):
    """Multi-line text field (alias for StringField with multiline=True)"""
    
    def __init__(self, **kwargs):
        kwargs['multiline'] = True
        super().__init__(**kwargs)
