"""Form metaclass and base classes"""
import copy
from typing import Dict, Any, Optional, List
from textual import on
from textual.containers import Vertical, Center, Horizontal, VerticalScroll
from textual.widgets import Button, Static, Label
from textual.message import Message

from .fields import Field
from .exceptions import FieldError


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


class RenderedForm(VerticalScroll):
    """Rendered form widget that displays fields and buttons"""

    DEFAULT_CSS = """
    RenderedForm {
        keyline: thin green;
    }

    Vertical {
        margin: 1;
    }

    #form-title {
        background: blue;
        height: auto;
        margin: 1;
    }

    .subform-title {
        background: white;
        color: black;
        height: auto;
        padding: 0 1;
        margin: 1 0 0 0;
    }

    .form-field {
        height: auto;
    }

    .form-error {
        color: red;
        width: 1fr;
    }

    #buttons {
        height: auto;
        align: center middle;
        margin: 0;
    }

    #outer-buttons {
        height: auto;
    }

    Input {
        height: auto;
    }

    TextArea {
        height: 6;
    }
    """


    def __init__(self, form, data: Optional[Dict[str, Any]] = None,
                 field_order: Optional[List[str]] = None, id=None):
        """
        Initialize rendered form

        Args:
            form: The Form instance
            data: Initial data dict
            field_order: Custom field ordering
            id: Widget ID
        """
        super().__init__(id=id, **form.kwargs)
        self.form = form
        self.fields = form.fields
        self.data = data
        self.field_order = field_order

        if data is not None:
            self.set_data(data)

    def compose(self):
        """Compose the form UI"""
        # Optional title
        if self.form.title is not None:
            yield Vertical(
                Center(Static(f"---- {self.form.title} ----")),
                id="form-title"
            )

        # Track which subforms we've already rendered headers for
        rendered_subforms = set()
        
        # Render each field
        for name, field in self.form.fields.items():
            # Check if this field is part of a composed subform with a title
            metadata = self.form._composition_metadata.get(name)
            if metadata and metadata.get('title'):
                subform_id = metadata['composed_from']
                
                # Render subform title once per subform
                if subform_id not in rendered_subforms:
                    yield Static(metadata['title'], classes="subform-title")
                    rendered_subforms.add(subform_id)
            
            with Vertical(classes="form-field"):
                if field.label:
                    yield Label(field.label)
                yield field.widget

                # Set initial data if provided
                if self.data and name in self.data:
                    field.value = self.data[name]

        # Submit/Cancel buttons
        yield Vertical(
            Horizontal(
                Button("Cancel", id="cancel"),
                Button("Submit", id="submit", variant="primary"),
                id="buttons"
            ),
            id="outer-buttons"
        )

    def get_data(self) -> Dict[str, Any]:
        """Get current form data"""
        return self.form.get_data()

    def set_data(self, data: Dict[str, Any]):
        """Set form data"""
        return self.form.set_data(data)

    async def validate(self):
        """Validate all form fields"""
        return await self.form.validate()

    @on(Button.Pressed, "#submit")
    async def submit_pressed(self, event: Button.Pressed) -> None:
        """Handle submit button press"""
        if await self.validate():
            self.post_message(Form.Submitted(self))
        else:
            self.app.notify("Please fix the errors before submitting", severity="error")

    @on(Button.Pressed, "#cancel")
    async def cancel_pressed(self, event: Button.Pressed) -> None:
        """Handle cancel button press"""
        self.post_message(Form.Cancelled(self))


class BaseForm:
    """Base form class without metaclass"""

    def __init__(self, *children, data: Optional[Dict[str, Any]] = None,
                 field_order: Optional[List[str]] = None,
                 title: Optional[str] = None, render_type=RenderedForm, **kwargs):
        """
        Initialize form

        Args:
            data: Initial data dict
            field_order: Custom field ordering
            title: Form title
            render_type: Custom renderer class
            **kwargs: Additional kwargs for renderer
        """
        self.data = data
        self.children = children
        self.field_order = field_order
        self.title = title
        self.kwargs = kwargs
        self.render_type = render_type

        # Deep copy fields from _base_fields
        self.fields: Dict[str, Field] = copy.deepcopy(self._base_fields)

        # Apply custom field ordering if provided
        self.order_fields(self.field_order)

        # Bind fields to this form
        for name, field in self.fields.items():
            field.name = name
            field.form = self

    @classmethod
    def compose(cls, prefix: str = '', title: Optional[str] = None) -> ComposedForm:
        """
        Create a composition marker for including this form in another

        Args:
            prefix: Optional prefix for field names (e.g., 'billing' creates 'billing_street')
                   Empty string or no prefix means fields are added without prefixing
            title: Optional title for the subform section. If not provided and prefix exists,
                   the prefix will be capitalized and used as the title

        Returns:
            ComposedForm marker for use in form class definition

        Example:
            class AddressForm(Form):
                street = StringField()
                city = StringField()

            class OrderForm(Form):
                billing = AddressForm.compose(prefix='billing')   # Creates billing_street, billing_city with "Billing" title
                shipping = AddressForm.compose(prefix='shipping', title='Ship To') # Custom title
                notes = StringField()
        """
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

        fields = {}
        # First add fields in specified order
        for key in field_order:
            if key in self.fields:
                fields[key] = self.fields.pop(key)

        # Then add any remaining fields
        for k in list(self.fields):
            fields[k] = self.fields.pop(k)

        self.fields = fields


    def get_fields_dict(self) -> Dict[str, Field]:
        """
        Get fields dictionary without rendering

        Useful for:
        - Testing field configuration
        - Inspecting form structure
        - Validating field setup

        Returns:
            Dictionary of field name -> Field instance
        """
        return self.fields

    def get_field_names(self) -> List[str]:
        """
        Get list of field names in order

        Returns:
            List of field names
        """
        return list(self.fields.keys())

    def get_field(self, name: str) -> Optional[Field]:
        """
        Get a specific field by name with SQL-style resolution

        Supports:
        - Exact match: get_field('billing_street')
        - Unqualified match: get_field('street') if unambiguous
        - Raises AmbiguousFieldError if multiple fields match

        Args:
            name: Field name (qualified or unqualified)

        Returns:
            Field instance or None if not found

        Raises:
            AmbiguousFieldError: If unqualified name matches multiple fields
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

    def render(self, id=None) -> RenderedForm:
        """
        Render the form as a Textual widget

        Args:
            id: Optional ID for the rendered form

        Returns:
            RenderedForm widget ready to be mounted
        """
        # Create widgets for all fields
        for name, field in self.fields.items():
            field.widget = field.create_widget()
            field._widget_instance = field.widget

        # Create and return rendered form
        self.rform = self.render_type(
            self,
            id=id,
            data=self.data,
            field_order=self.field_order
        )
        return self.rform

    async def validate(self):
        """
        Validate all form fields

        Returns:
            True if all fields are valid, False otherwise
        """
        result = True

        for name, field in self.fields.items():
            widget = field.widget
            container = widget.parent

            # Clear previous errors
            await container.remove_children(".form-error")

            # Validate widget
            vr = widget.validate(widget.value)
            if vr is not None and not vr.is_valid:
                result = False
                # Display errors
                for msg in vr.failure_descriptions:
                    container.mount(Center(Static(msg, classes="form-error")))

        return result


class Form(BaseForm, metaclass=FormMetaclass):
    """
    Form with declarative field syntax

    Example:
        class UserForm(Form):
            name = StringField(label="Name", required=True)
            age = IntegerField(label="Age", min_value=0)
    """

    class Submitted(Message):
        """Posted when form is submitted successfully"""

        def __init__(self, r_form: RenderedForm):
            super().__init__()
            self.form = r_form

    class Cancelled(Message):
        """Posted when form is cancelled"""

        def __init__(self, r_form: RenderedForm):
            super().__init__()
            self.form = r_form
