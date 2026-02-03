"""Form metaclass and base classes"""
import copy
from typing import Dict, Any, Optional, List
from textual.message import Message
from textual.containers import Center
from textual.widgets import Static
from .fields import Field
from .exceptions import FieldError, AmbiguousFieldError, ValidationError


class ComposedForm:
    """Marker for composed form inclusion"""
    def __init__(self, form_class: type, prefix: str = '', title: Optional[str] = None):
        self.form_class = form_class
        self.prefix = prefix
        # If no title provided but prefix exists, capitalize prefix as title
        if title is None and prefix:
            self.title = prefix.capitalize()
        else:
            self.title = title


class FormMetaclass(type):
    """Metaclass that collects Field declarations and expands composed forms"""

    def __new__(mcs, name, bases, attrs):
        # Collect fields and composed forms in declaration order
        items_in_order = []

        for key, value in list(attrs.items()):
            if isinstance(value, Field):
                items_in_order.append(('field', key, value))
                attrs.pop(key)  # Remove from class attrs
            elif isinstance(value, ComposedForm):
                items_in_order.append(('composed', key, value))
                attrs.pop(key)  # Remove from class attrs

        # Process items in order, expanding composed forms
        all_fields = []
        declared_fields = []
        composition_metadata = {}

        for item_type, attr_name, item in items_in_order:
            if item_type == 'field':
                # Regular field - add directly
                all_fields.append((attr_name, item))
                declared_fields.append((attr_name, item))

            elif item_type == 'composed':
                # Composed form - expand it
                composed = item

                if not hasattr(composed.form_class, '_base_fields'):
                    raise FieldError(
                        f"Cannot compose {composed.form_class.__name__}: "
                        f"it doesn't appear to be a Form class"
                    )

                composed_fields = composed.form_class._base_fields
                prefix = composed.prefix

                # Expand fields with prefix
                for field_name, field in composed_fields.items():
                    # Generate new field name
                    if prefix:
                        new_name = f"{prefix}_{field_name}"
                    else:
                        new_name = field_name

                    # Deep copy the field
                    new_field = copy.deepcopy(field)
                    all_fields.append((new_name, new_field))

                    # Track composition metadata
                    if prefix or composed.title:
                        composition_metadata[new_name] = {
                            'composed_from': attr_name,
                            'prefix': prefix,
                            'original_name': field_name,
                            'title': composed.title
                        }

        # Check for name collisions
        field_names = {}
        for field_name, field in all_fields:
            if field_name in field_names:
                raise FieldError(
                    f"Field name collision: '{field_name}' is defined multiple times. "
                    f"Use different prefixes to avoid collisions."
                )
            field_names[field_name] = field

        # Store as _base_fields
        new_class = super().__new__(mcs, name, bases, attrs)
        new_class._base_fields = dict(all_fields)
        new_class._declared_fields = dict(declared_fields)
        new_class._composition_metadata = composition_metadata
        return new_class




class BaseForm:
    """Base form class without metaclass"""

    # Default layout class to use when rendering
    layout_class = None  # Will be set to DefaultFormLayout after import

    def __init__(self, *children, data: Optional[Dict[str, Any]] = None,
                 field_order: Optional[List[str]] = None,
                 title: Optional[str] = None,
                 layout_class=None,
                 **kwargs):
        """
        Initialize form

        Creates BoundField instances from class-level Field definitions.
        This is much faster than deep copying and enables thread-safe
        Form class reuse.

        Args:
            data: Initial data dict
            field_order: Custom field ordering
            title: Form title
            layout_class: Custom layout class (overrides class-level layout_class)
            **kwargs: Additional kwargs for layout
        """
        self.data = data
        self.children = children
        self.field_order = field_order
        self.title = title
        self.kwargs = kwargs

        # Layout configuration
        if layout_class is not None:
            self._layout_class = layout_class
        elif self.layout_class is not None:
            self._layout_class = self.layout_class
        else:
            # Will use DefaultFormLayout (imported at module level)
            from .layouts import DefaultFormLayout
            self._layout_class = DefaultFormLayout

        # Create BoundFields from class-level Field definitions
        # NO MORE DEEP COPY - just create lightweight BoundField wrappers
        self.bound_fields: Dict[str, 'BoundField'] = {}

        for name, field in self._base_fields.items():
            # Get initial value from data if provided
            initial = data.get(name) if data else None
            # Create BoundField (holds runtime state)
            bound_field = field.bind(self, name, initial)
            self.bound_fields[name] = bound_field

            # Set as attribute for direct access (form.fieldname)
            setattr(self, name, bound_field)

        # Apply custom field ordering if provided
        self.order_fields(self.field_order)

    @property
    def fields(self) -> Dict[str, 'BoundField']:
        """
        Backward compatibility: alias for bound_fields

        Returns bound_fields so existing code using form.fields continues to work.
        """
        return self.bound_fields

    def __getattr__(self, name: str) -> 'BoundField':
        """
        Allow dot-access to fields using the "SQL-style" resolution logic.
        This is called only if the attribute was not found by normal lookup.
        """
        # Try to resolve using get_field logic
        field = self.get_field(name)
        if field:
            return field

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @classmethod
    def compose(cls, prefix: str = '', title: Optional[str] = None) -> ComposedForm:
        """Create a composition marker for including this form in another"""
        return ComposedForm(cls, prefix=prefix, title=title)

    def get_data(self) -> Dict[str, Any]:
        """Get current values from all fields"""
        data: Dict[str, Any] = {}
        for name, field in self.fields.items():
            data[name] = field.value
        return data

    def set_data(self, data: Dict[str, Any]):
        """Set values for fields from dict"""
        for name, value in data.items():
            if name in self.fields:
                self.fields[name].value = value

    def order_fields(self, field_order):
        """Reorder fields according to field_order list"""
        if field_order is None:
            return

        # Work directly with bound_fields since fields is now a property
        ordered = {}
        # First add fields in specified order
        for key in field_order:
            if key in self.bound_fields:
                ordered[key] = self.bound_fields.pop(key)

        # Then add any remaining fields
        for k in list(self.bound_fields):
            ordered[k] = self.bound_fields.pop(k)

        self.bound_fields = ordered

    def get_fields_dict(self) -> Dict[str, 'BoundField']:
        """Get fields dictionary without rendering"""
        return self.bound_fields

    def get_field_names(self) -> List[str]:
        """Get list of field names in order"""
        return list(self.bound_fields.keys())

    def get_field(self, name: str) -> Optional['BoundField']:
        """
        Get a specific field by name with SQL-style resolution
        """
        # Try exact match first
        if name in self.fields:
            return self.fields[name]

        # Try unqualified match (fields ending with _<name>)
        candidates = [
            field_name for field_name in self.fields
            if field_name == name or field_name.endswith('_' + name)
        ]

        if len(candidates) == 0:
            return None  # Not found
        elif len(candidates) == 1:
            return self.fields[candidates[0]]  # Unambiguous
        else:
            from .exceptions import AmbiguousFieldError
            raise AmbiguousFieldError(
                f"Field '{name}' is ambiguous. Could be: {', '.join(sorted(candidates))}. "
                f"Use the full qualified name to disambiguate."
            )

    def render(self, id=None):
        """
        Render the form as a Textual widget

        Creates a layout instance using the configured layout_class.
        During rendering, sets self._current_layout so that field()
        calls can track which fields have been rendered.

        Returns:
            Layout instance (e.g., DefaultFormLayout or custom layout)
        """
        # Create layout instance
        layout = self._layout_class(self, id=id, **self.kwargs)

        # Store layout reference so BoundField.__call__ can track rendering
        self._current_layout = layout

        return layout

    async def validate(self):
        """Validate all form fields"""
        result = True

        for name, field in self.fields.items():
            widget = field.widget
            container = widget.parent

            # Clear previous errors
            await container.remove_children(".form-error")

            # Widget-level validation (validators passed to widget)
            vr = widget.validate(widget.value)
            if vr is not None and not vr.is_valid:
                result = False
                # Display errors
                for msg in vr.failure_descriptions:
                    container.mount(Center(Static(msg), classes="form-error"))

            # Field-level validation (required, custom Field validators)
            try:
                field.clean(field.value)
            except ValidationError as e:
                result = False
                container.mount(Center(Static(str(e)), classes="form-error"))

        return result


class Form(BaseForm, metaclass=FormMetaclass):
    """
    Form with declarative field syntax
    """

    class Submitted(Message):
        """Posted when form is submitted successfully"""
        def __init__(self, layout):
            """
            Args:
                layout: The FormLayout instance that submitted the form
            """
            super().__init__()
            self.layout = layout
            # Provide backward compatibility
            self.form = layout

    class Cancelled(Message):
        """Posted when form is cancelled"""
        def __init__(self, layout):
            """
            Args:
                layout: The FormLayout instance that cancelled the form
            """
            super().__init__()
            self.layout = layout
            # Provide backward compatibility
            self.form = layout
