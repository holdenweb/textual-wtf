"""Form layout classes for rendering forms"""
from typing import Optional, Set, TYPE_CHECKING
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Center, Horizontal, VerticalScroll
from textual.widgets import Button, Static, Label
from textual.message import Message

from .exceptions import FormError

if TYPE_CHECKING:
    from .forms import Form


class FormLayout(VerticalScroll):
    """
    Base class for form layouts

    Handles the visual presentation of a form. Subclass this to create
    custom form layouts with different visual arrangements of fields.

    The layout tracks which fields have been rendered to prevent duplicate
    rendering (which would create multiple widgets for the same field).
    """

    DEFAULT_CSS = """
    FormLayout {
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

    def __init__(self, form: 'Form', id: Optional[str] = None, **kwargs):
        """
        Initialize form layout

        Args:
            form: The Form instance to render
            id: Optional widget ID
            **kwargs: Additional kwargs for VerticalScroll
        """
        super().__init__(id=id, **kwargs)
        self.form = form
        self._rendered_fields: Set[str] = set()

    def _track_field_render(self, field_name: str) -> None:
        """
        Track that a field has been rendered

        Raises FormError if field already rendered (prevents duplicate widgets).

        Args:
            field_name: Name of the field being rendered
        """
        if field_name in self._rendered_fields:
            raise FormError(
                f"Field '{field_name}' has already been rendered. "
                f"Each field can only be rendered once per form."
            )
        self._rendered_fields.add(field_name)

    def compose(self):
        """
        Compose the layout

        Calls compose_form() to build the form UI. Subclasses should
        override compose_form(), not this method.
        """
        yield from self.compose_form()

    def compose_form(self):
        """
        Compose the form UI

        Override this method in subclasses to create custom layouts.
        Use form.fieldname() to render each field.

        Example:
            def compose_form(self):
                yield Label("My Custom Form")
                yield self.form.name()
                yield self.form.email()
                yield Button("Submit", id="submit")
        """
        raise NotImplementedError("FormLayout subclasses must implement compose_form()")

    def get_data(self):
        """Get current form data"""
        return self.form.get_data()

    def set_data(self, data):
        """Set form data"""
        return self.form.set_data(data)

    async def validate(self):
        """Validate all form fields"""
        return await self.form.validate()

    @on(Button.Pressed, "#submit")
    async def submit_pressed(self, event: Button.Pressed) -> None:
        """Handle submit button press"""
        # Import here to avoid circular import
        from .forms import Form

        if await self.validate():
            self.post_message(Form.Submitted(self))
        else:
            self.app.notify("Please fix the errors before submitting", severity="error")

    @on(Button.Pressed, "#cancel")
    async def cancel_pressed(self, event: Button.Pressed) -> None:
        """Handle cancel button press"""
        # Import here to avoid circular import
        from .forms import Form

        self.post_message(Form.Cancelled(self))

class DefaultFormLayout(FormLayout):
    """
    Default form layout

    Renders forms in the traditional vertical style:
    - Optional title
    - Subform titles for composed forms
    - Each field with label and widget
    - Submit/Cancel buttons
    """

    def compose_form(self) -> ComposeResult:
        """Compose the form in default vertical layout"""
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
                # Call the field to get its widget
                yield field()

        # Submit/Cancel buttons
        yield Vertical(
            Horizontal(
                Button("Cancel", id="cancel"),
                Button("Submit", id="submit", variant="primary"),
                id="buttons"
            ),
            id="outer-buttons"
        )

