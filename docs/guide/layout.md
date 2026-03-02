# Layout & Rendering

textual-wtf offers three rendering modes with different tradeoffs between convenience and control.

## layout() — automatic rendering

`form.layout()` is the zero-configuration path. It returns a `DefaultFormLayout` widget that renders every unrendered field in declaration order, preceded by the form title (if set) and followed by Submit and Cancel buttons. Use it with `yield` in your `compose()` method, just like any other Textual widget.

```python title="auto_layout.py"
from textual.app import App, ComposeResult, on
from textual_wtf import Form, StringField, IntegerField

class ProfileForm(Form):
    title = "Edit Profile"

    name = StringField("Name", required=True)
    age  = IntegerField("Age", minimum=0, maximum=120)


class ProfileApp(App):
    def compose(self) -> ComposeResult:
        self.form = ProfileForm()
        yield self.form.layout()

    @on(ProfileForm.Submitted)
    def submitted(self, event: ProfileForm.Submitted) -> None:
        self.notify(str(event.form.get_data()))
```

`layout()` accepts an optional `id` parameter if you need to query the layout later:

```python
yield self.form.layout(id="profile-layout")
```

!!! tip "Layout class override"
    Set `layout_class` on the form class to swap in a custom layout:

    ```python
    class ProfileForm(Form):
        layout_class = MyTwoColumnLayout
        ...
    ```

---

## BoundField.simple_layout() — per-field chrome

`simple_layout()` gives you control over which fields appear where, while still rendering the full chrome (label, input, help text, error message) for each field. Use it when you need a custom arrangement — a two-column grid, fields inside a `TabPane`, or interleaved with other widgets.

```python title="manual_layout.py"
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button
from textual_wtf import Form, StringField, ControllerAwareLayout

class AddressForm(Form):
    street   = StringField("Street", required=True)
    city     = StringField("City", required=True)
    postcode = StringField("Postcode", required=True)


class AddressLayout(ControllerAwareLayout):
    def compose(self) -> ComposeResult:
        bf = self.form.bound_fields

        yield bf["street"].simple_layout()

        with Horizontal():
            yield bf["city"].simple_layout()
            yield bf["postcode"].simple_layout()

        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
```

`simple_layout()` returns a `FieldWidget` — a self-contained `Container` that owns the label, the input widget, and the error/help labels. You can yield it anywhere in a `compose()` method.

### simple_layout() parameters

`label_style: LabelStyle | None = None`
:   Override the label style for this one field rendering.

`help_style: HelpStyle | None = None`
:   Override the help style for this one field rendering.

`disabled: bool | None = None`
:   Force the widget enabled or disabled.

`required: bool | None = None`
:   Override the required flag at render time (highest priority in the cascade).

`renderer: Callable[[BoundField], ComposeResult] | None = None`
:   Pass a callable that receives the `BoundField` and returns a `ComposeResult`. The callable replaces the entire inner layout of the `FieldWidget`.

`**widget_kwargs`
:   Additional keyword arguments forwarded to the underlying Textual widget.

---

## BoundField.__call__() — raw widget

Calling a `BoundField` directly (`bf()` or `bf.__call__()`) returns just the inner Textual widget (`Input`, `Checkbox`, `Select`, or `TextArea`) with no surrounding chrome. Use this when you want total layout freedom and will provide your own labels and error display.

```python title="raw_widget.py"
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Label
from textual_wtf import Form, StringField, ControllerAwareLayout

class SearchForm(Form):
    query = StringField("Search query", required=True)


class SearchBar(ControllerAwareLayout):
    def compose(self) -> ComposeResult:
        bf = self.form.bound_fields

        with Horizontal():
            yield Label("Search:")
            yield bf["query"]()      # raw Input widget
            yield Button("Go", id="submit", variant="primary")
```

!!! warning "ControllerAwareLayout required"
    Raw widgets produced by `bf()` do not live inside a `FieldWidget`, so they have no parent that can route widget events (change, blur) back to the `FieldController`. You **must** use `ControllerAwareLayout` (or a subclass) as the parent layout, otherwise validation will not fire.

    `DefaultFormLayout` already extends `ControllerAwareLayout`, so this requirement only applies when you subclass `FormLayout` directly.

### __call__() parameters

`label_style: LabelStyle | None = None`
:   Has no effect for raw widgets (no label container). Accepted for API symmetry with `simple_layout()`.

`help_style: HelpStyle | None = None`
:   Has no effect for raw widgets. Accepted for API symmetry with `simple_layout()`.

`disabled: bool | None = None`
:   Force the widget enabled or disabled.

`required: bool | None = None`
:   Override the required flag at render time (highest priority in the cascade).

`**widget_kwargs`
:   Additional keyword arguments forwarded to the underlying Textual widget.

---

## FieldErrors — error display for raw widgets

When you use `bf()` to get a raw widget, there is no surrounding `FieldWidget` to display validation errors. Place a `FieldErrors` widget next to the raw widget to get the same error display that `simple_layout()` provides automatically:

```python title="raw_with_errors.py"
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label
from textual_wtf import Form, StringField, ControllerAwareLayout, FieldErrors

class SearchForm(Form):
    query = StringField("Search query", required=True)


class SearchBar(ControllerAwareLayout):
    def compose(self) -> ComposeResult:
        bf = self.form.bound_fields

        with Horizontal():
            yield Label("Search:")
            with Vertical():
                yield bf["query"]()
                yield FieldErrors(bf["query"].controller)
            yield Button("Go", id="submit", variant="primary")
```

`FieldErrors` registers itself with the controller on mount and deregisters on unmount. It hides itself automatically when the field is valid and becomes visible (in the theme's error colour) when validation fails.

!!! note "Same mechanism as FieldWidget"
    `FieldWidget` uses `FieldErrors` internally, so both code paths share exactly the same error display logic.

---

## Label styles

The `label_style` setting controls where the field label appears relative to the input widget.

=== "above (default)"

    The label sits on its own line above the input. This is the most readable style and handles long labels well.

    ```
    Username
    ┌────────────────────────────────┐
    │ alice                          │
    └────────────────────────────────┘
    ```

    ```python
    class MyForm(Form):
        label_style = "above"   # also the default if unset

        username = StringField("Username")
    ```

=== "beside"

    The label sits to the left of the input on the same line. Efficient for forms with many short fields.

    ```
    Username  ┌───────────────────────┐
              │ alice                 │
              └───────────────────────┘
    ```

    ```python
    class MyForm(Form):
        label_style = "beside"

        username = StringField("Username")
    ```

=== "placeholder"

    No visible label — the label text is used as the input placeholder. Compact but less accessible for longer forms.

    ```
    ┌────────────────────────────────┐
    │ Username                       │
    └────────────────────────────────┘
    ```

    ```python
    class MyForm(Form):
        label_style = "placeholder"

        username = StringField("Username")
    ```

!!! info "Per-field override"
    You can mix styles in the same form by setting `label_style=` on individual fields:

    ```python
    class MyForm(Form):
        label_style = "above"          # default for all fields

        name  = StringField("Name")                          # above
        email = StringField("Email", label_style="beside")  # beside only
    ```

---

## Help style

`help_style` controls how the `help_text` of a field is presented.

`"below"` (default)
:   Help text appears as a muted line below the input widget. Always visible.

`"tooltip"`
:   Help text appears in a tooltip when the user hovers over the input (or when it receives focus, depending on terminal). Saves vertical space.

```python
class MyForm(Form):
    help_style = "tooltip"  # form-wide default

    name  = StringField("Name", help_text="Your full name.")
    email = StringField("Email", help_text="We'll never share this.",
                        help_style="below")  # override for this field
```

---

## Custom layouts

To create a custom layout, subclass `ControllerAwareLayout` and implement `compose()`. The form is available as `self.form`.

```python title="custom_layout.py"
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Label
from textual_wtf import ControllerAwareLayout

class TwoColumnLayout(ControllerAwareLayout):
    """Renders fields in two columns."""

    DEFAULT_CSS = """
    TwoColumnLayout {
        height: auto;
        padding: 1 2;
    }
    TwoColumnLayout .col {
        width: 1fr;
        height: auto;
    }
    TwoColumnLayout #buttons {
        height: auto;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        fields = list(self.form.bound_fields.values())
        left  = fields[::2]   # even-indexed fields
        right = fields[1::2]  # odd-indexed fields

        with Horizontal():
            with self.app.__class__():  # placeholder — see how-to for real example
                for bf in left:
                    yield bf.simple_layout()
            with self.app.__class__():
                for bf in right:
                    yield bf.simple_layout()

        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
```

!!! tip "Full how-to"
    See [How-to: Custom Layout](../how-to/custom_layout.md) for a complete, working two-column custom layout.

### Using a custom layout

Pass it directly to `layout()` at call time:

```python
self.form = MyForm()
yield self.form.layout(TwoColumnLayout)
```

Or set `layout_class` on the form class to make it the default for every call:

```python
class MyForm(Form):
    layout_class = TwoColumnLayout

    first_name = StringField("First name", required=True)
    last_name  = StringField("Last name", required=True)
    email      = StringField("Email", required=True)
    phone      = StringField("Phone")
```

Then `layout()` with no argument will use `TwoColumnLayout` automatically.

### Callable layouts

`layout()` also accepts a plain callable instead of a `FormLayout` subclass. The callable receives the form instance and must return a `Widget`. This is useful for lightweight, one-off arrangements that don't need a full class:

```python
from textual.widget import Widget
from textual_wtf import ControllerAwareLayout

def compact_layout(form) -> Widget:
    """Two fields side by side, no buttons."""
    class _Layout(ControllerAwareLayout):
        def compose(self):
            bf = self.form.bound_fields
            with Horizontal():
                yield bf["first_name"].simple_layout()
                yield bf["last_name"].simple_layout()
    return _Layout(form=form)

self.form = MyForm()
yield self.form.layout(compact_layout)
```

### The renderer= callback

`simple_layout()` accepts a `renderer=` callback that replaces the entire inner content of a `FieldWidget`. The callback receives the `BoundField` and must return a `ComposeResult`:

```python title="custom_renderer.py"
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label
from textual_wtf import BoundField

def inline_renderer(bf: BoundField) -> ComposeResult:
    """Render label and input side-by-side inside a FieldWidget."""
    with Horizontal():
        yield Label(f"{bf.label}:", classes="inline-label")
        yield bf._build_inner_widget()


class MyLayout(ControllerAwareLayout):
    def compose(self) -> ComposeResult:
        for bf in self.form.bound_fields.values():
            yield bf.simple_layout(renderer=inline_renderer)
```
