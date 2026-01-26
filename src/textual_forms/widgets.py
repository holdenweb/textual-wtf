"""Form widgets with validation support"""
from typing import List, Optional, TYPE_CHECKING, Tuple
from textual.widgets import Input, Checkbox, Select, TextArea, Static
from textual.containers import Center
from textual.validation import ValidationResult, Validator

if TYPE_CHECKING:
    from .fields import Field


def widget_id_gen():
    """Generate unique widget IDs"""
    count = 0
    while True:
        count += 1
        yield f"field-widget-{count}"


_id_gen = widget_id_gen()


class FormWidgetMixin:
    """Mixin to add validation error display to widgets"""
    
    async def on_input_changed(self, event):
        """Handle input changes and display validation errors"""
        if not hasattr(self, 'parent') or self.parent is None:
            return
        
        container = self.parent
        
        # ALWAYS clear previous errors first
        await container.remove_children(".form-error")
        
        if hasattr(event, 'validation_result') and event.validation_result is not None:
            vr = event.validation_result
            if not vr.is_valid:
                # Show all errors from this validation
                for msg in vr.failure_descriptions:
                    container.mount(Center(Static(msg), classes="form-error"))


class FormInput(Input, FormWidgetMixin):
    """Text input widget for forms"""
    
    def __init__(self, *, field: Optional['Field'] = None, valid_empty: bool = True,
                 validators: Optional[List[Validator]] = None, **kwargs):
        kwargs.setdefault('id', next(_id_gen))
        kwargs['validators'] = validators or []
        super().__init__(**kwargs)
        self.field = field
        self.valid_empty = valid_empty


class FormIntegerInput(Input, FormWidgetMixin):
    """Integer input widget for forms"""
    
    def __init__(self, *, field: Optional['Field'] = None, valid_empty: bool = True,
                 validators: Optional[List[Validator]] = None, **kwargs):
        kwargs.setdefault('id', next(_id_gen))
        kwargs['type'] = 'integer'
        kwargs['validators'] = validators or []
        super().__init__(**kwargs)
        self.field = field
        self.valid_empty = valid_empty


class FormTextArea(TextArea, FormWidgetMixin):
    """Multi-line text area widget for forms"""
    
    def __init__(self, *, field: Optional['Field'] = None, text: str = "", **kwargs):
        kwargs.setdefault('id', next(_id_gen))
        super().__init__(text=text, **kwargs)
        self.field = field
    
    @property
    def value(self):
        """Get text area value"""
        return self.text
    
    @value.setter
    def value(self, v):
        """Set text area value"""
        self.text = v if v is not None else ""
    
    def validate(self, value):
        """Validate text area value"""
        return ValidationResult()


class FormCheckbox(Checkbox):
    """Checkbox widget for forms"""
    
    def __init__(self, *, field: Optional['Field'] = None, label: str = "", **kwargs):
        kwargs.setdefault('id', next(_id_gen))
        super().__init__(value=False, **kwargs)
        self.field = field
        if label:
            self.label = label
    
    def validate(self, value):
        """Validate checkbox value"""
        return ValidationResult()


class AlwaysValid(Validator):
    """Validator that always passes"""
    
    def validate(self, value):
        return self.success()


class FormSelect(Select):
    """Select dropdown widget for forms"""
    
    def __init__(self, *, field: Optional['Field'] = None, 
                 choices: List[Tuple[str, str]], allow_blank: bool = False,
                 prompt: str = "Select an option", **kwargs):
        kwargs.setdefault('id', next(_id_gen))
        kwargs.setdefault('prompt', prompt)
        
        # Convert tuples to Select.Option objects
        options = [(label, value) for value, label in choices]
        
        super().__init__(options=options, **kwargs)
        self.field = field
        self.allow_blank = allow_blank
    
    def validate(self, value):
        """Validate select value"""
        if value != Select.BLANK or self.allow_blank:
            return AlwaysValid().success()
        return AlwaysValid().failure("Please select a value")


class WidgetRegistry:
    """Registry for custom widgets"""
    
    _widgets = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register a widget"""
        def decorator(widget_class):
            cls._widgets[name] = widget_class
            return widget_class
        return decorator
    
    @classmethod
    def get(cls, name: str):
        """Get a widget by name"""
        return cls._widgets.get(name)
    
    @classmethod
    def list_widgets(cls):
        """List all registered widgets"""
        return list(cls._widgets.keys())


# Register built-in widgets
WidgetRegistry.register("input")(FormInput)
WidgetRegistry.register("integer_input")(FormIntegerInput)
WidgetRegistry.register("textarea")(FormTextArea)
WidgetRegistry.register("checkbox")(FormCheckbox)
WidgetRegistry.register("select")(FormSelect)
