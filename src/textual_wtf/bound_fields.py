"""BoundField - runtime state for fields in form instances"""
from typing import Any, Optional, List, TYPE_CHECKING
from textual.widget import Widget
from textual.validation import Validator

from .exceptions import ValidationError

if TYPE_CHECKING:
    from .fields import Field
    from .forms import Form


class BoundField:
    """
    Holds runtime state for a field in a form instance.
    
    Separates mutable state (_widget, _errors, _value) from immutable
    configuration (stored in the Field instance). This allows Field
    instances to be safely shared across multiple form instances.
    
    CRITICAL INVARIANT: _value must always contain the current Python value,
    regardless of whether a widget exists. This ensures data is never lost
    and provides a canonical source of truth.
    
    Attributes:
        field: Reference to the Field configuration (shared, immutable)
        form: Parent form instance
        name: Field name in the form
        _widget_instance: The actual Textual widget (or None)
        _errors: Current validation errors
        _value: Current Python value (ALWAYS KEPT IN SYNC)
    """
    
    def __init__(self, field: 'Field', form: 'Form', name: str, initial: Any = None):
        """
        Initialize BoundField with runtime state
        
        Args:
            field: Field configuration (shared across instances)
            form: Parent form instance
            name: Field name
            initial: Initial value (overrides field.initial if provided)
        """
        # Reference to configuration
        self.field = field
        self.form = form
        self.name = name
        
        # Runtime state (mutable, instance-specific)
        self._widget_instance: Optional[Widget] = None
        self._errors: List[str] = []
        self._value = initial if initial is not None else field.initial
    
    # ========================================================================
    # Properties - Delegate configuration to Field
    # ========================================================================
    
    @property
    def label(self) -> Optional[str]:
        """Field label (delegated to Field config)"""
        return self.field.label
    
    @property
    def help_text(self) -> Optional[str]:
        """Field help text (delegated to Field config)"""
        return self.field.help_text
    
    @property
    def required(self) -> bool:
        """Whether field is required (delegated to Field config)"""
        return self.field.required
    
    @property
    def disabled(self) -> bool:
        """Whether field is disabled (delegated to Field config)"""
        return self.field.disabled
    
    @property
    def validators(self) -> List[Validator]:
        """Field validators (delegated to Field config)"""
        return self.field.validators
    
    @property
    def initial(self) -> Any:
        """Initial value (delegated to Field config)"""
        return self.field.initial
    
    # ========================================================================
    # Properties - Runtime state
    # ========================================================================
    
    @property
    def widget(self) -> Optional[Widget]:
        """Get widget instance"""
        return self._widget_instance
    
    @widget.setter
    def widget(self, widget: Widget) -> None:
        """Set widget instance"""
        self._widget_instance = widget
        if widget:
            # Create back-reference so widget can access bound field
            widget.bound_field = self
    
    @property
    def errors(self) -> List[str]:
        """Get validation errors"""
        return self._errors
    
    @errors.setter
    def errors(self, errors: List[str]) -> None:
        """Set validation errors"""
        self._errors = errors
    
    @property
    def value(self) -> Any:
        """
        Get current field value
        
        CRITICAL: If widget exists, reads from widget and SYNCS to _value.
        This ensures _value is always current, even when user types in widget.
        
        Returns:
            Current Python value (from widget if exists, otherwise from _value)
        """
        if self._widget_instance is not None:
            # Read from widget and keep _value in sync
            python_value = self.field.to_python(self._widget_instance.value)
            self._value = python_value  # CRITICAL: Always sync
            return python_value
        return self._value
    
    @value.setter
    def value(self, value: Any) -> None:
        """
        Set field value
        
        CRITICAL: Always updates _value (canonical storage) and syncs to
        widget if it exists. This ensures both storage locations stay in sync.
        
        Args:
            value: Python value to set
        """
        self._value = value  # CRITICAL: Always update canonical storage
        if self._widget_instance is not None:
            # Also sync to widget if it exists
            self._widget_instance.value = self.field.to_widget(value)
    
    # ========================================================================
    # Methods - Delegate to Field for logic
    # ========================================================================
    
    def create_widget(self) -> Widget:
        """
        Create widget using field configuration
        
        Returns:
            Widget instance configured from Field
        """
        widget = self.field.create_widget()
        self._widget_instance = widget
        # Set back-reference
        widget.bound_field = self
        # Also set field reference for backward compatibility
        widget.field = self
        return widget
    
    def to_python(self, value: Any) -> Any:
        """Convert widget value to Python value (delegated to Field)"""
        return self.field.to_python(value)
    
    def to_widget(self, value: Any) -> Any:
        """Convert Python value to widget value (delegated to Field)"""
        return self.field.to_widget(value)
    
    def validate(self, value: Any) -> None:
        """
        Validate value using field configuration
        
        Clears existing errors and validates the value.
        Stores validation errors in _errors list.
        
        Args:
            value: Value to validate
        """
        self._errors = []
        try:
            self.field.validate(value)
        except ValidationError as e:
            self._errors.append(str(e))
    
    def clean(self, value: Any) -> Any:
        """
        Convert and validate value
        
        Args:
            value: Raw value to clean
            
        Returns:
            Cleaned Python value
            
        Raises:
            ValidationError: If validation fails
        """
        python_value = self.field.to_python(value)
        self.validate(python_value)
        if self._errors:
            raise ValidationError(self._errors[0])
        return python_value
    
    # ========================================================================
    # Additional properties for compatibility with code that accesses
    # field-specific attributes (e.g., IntegerField.min_value)
    # ========================================================================
    
    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to Field for any attributes not found on BoundField
        
        This allows access to field-specific configuration like:
        - IntegerField.min_value, max_value
        - ChoiceField.choices
        - etc.
        """
        # Avoid infinite recursion for special attributes
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        # Try to get attribute from Field
        try:
            return getattr(self.field, name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' and '{type(self.field).__name__}' "
                f"have no attribute '{name}'"
            )
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<BoundField: {self.name} ({self.field.__class__.__name__})>"
