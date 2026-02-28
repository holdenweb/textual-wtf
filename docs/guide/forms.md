# Defining Forms

A form is a Python class that inherits from [`Form`][textual_wtf.Form]. Fields are declared as class-level attributes. The metaclass collects them, preserves declaration order, and attaches the runtime machinery needed for validation and rendering.

## Class declaration

```python title="my_forms.py"
from textual_wtf import Form, StringField, IntegerField, BooleanField, ChoiceField

class UserForm(Form):
    username = StringField("Username", required=True, max_length=30)
    email    = StringField("Email", required=True)
    age      = IntegerField("Age", minimum=0, maximum=120)
    role     = ChoiceField(
        "Role",
        choices=[("Admin", "admin"), ("Editor", "editor"), ("Viewer", "viewer")],
    )
    active   = BooleanField("Active account")
```

!!! note "No `__init__` needed"
    You never write `__init__` on a form class. The `Form` base class handles everything. Add class attributes (`title`, `label_style`, etc.) and field declarations — nothing else is required.

### Field ordering

Fields appear in the layout in the exact order they are declared in the class body. This is guaranteed by the metaclass, which uses an `OrderedDict` internally.

When you access `form.bound_fields` you get back an `OrderedDict[str, BoundField]` with the same order.

### Inheritance

Fields are inherited from base classes. Subclass fields appear after the parent's fields:

```python
class BaseProfileForm(Form):
    name  = StringField("Name", required=True)
    email = StringField("Email", required=True)

class ExtendedProfileForm(BaseProfileForm):
    bio  = TextField("Bio")        # appears after name and email
    role = ChoiceField("Role", choices=[("Admin", "admin"), ("User", "user")])
```

!!! warning "Name conflicts"
    Declaring a field with the same name as an inherited field raises `FormError` at class definition time, not at runtime.

## Class attributes

Form behaviour is configured through class attributes. Each can be overridden per-instance in the constructor.

`title: str = ""`
:   Text rendered as a bold heading above the fields when using `DefaultFormLayout`. Has no effect on the validation or data pipeline. Also used as the tab label in `TabbedForm`.

`label_style: LabelStyle = "above"`
:   Default label style for every field that does not set its own. One of `"above"`, `"beside"`, or `"placeholder"`. See the [Layout guide](layout.md#label-styles) for details.

`help_style: HelpStyle = "below"`
:   Default help-text style for every field that does not set its own. Either `"below"` (shown below the input) or `"tooltip"` (shown on hover). See [Layout guide](layout.md#help-style).

`required: bool | None = None`
:   Form-level default for the `required` flag. `None` means "do not override field-level defaults". See the [required cascade](#the-required-cascade) below.

`layout_class: type[FormLayout] | None = None`
:   Override the layout class used by `layout()`. When `None` (the default), `DefaultFormLayout` is used.

```python title="my_forms.py"
from textual_wtf import Form, StringField, TextField

class SupportTicketForm(Form):
    title        = "Submit a Support Ticket"
    label_style  = "beside"
    help_style   = "tooltip"
    required     = True          # all fields required by default

    subject = StringField("Subject", max_length=100)
    body    = TextField("Description", help_text="Describe the issue in detail.")
```

## The required cascade

The `required` flag can be set at four levels. Lower levels are overridden by higher levels. Field-level explicit settings are the exception — they are pinned and cannot be changed by any higher level.

| Level | Where | Priority | Example |
|---|---|---|---|
| 1 — Field explicit | `StringField("X", required=True)` | Pinned — never overridden | Always required, regardless of form settings |
| 2 — Class attribute | `class MyForm(Form): required = True` | Second | Default for all non-explicit fields on this class |
| 3 — Instance kwarg | `MyForm(required=False)` | Third | Overrides class attribute for this instance |
| 4 — Render time | `bf.simple_layout(required=True)` | Highest — render wins | Overrides everything for this one rendering call |

!!! info "Pinned fields"
    A field that sets `required=True` or `required=False` explicitly is **pinned**. Embedding that form with `required=False` will not make a pinned field optional. This lets you protect critical fields (such as an account number) from being accidentally made optional.

```python title="cascade_example.py"
from textual_wtf import Form, StringField

class AddressForm(Form):
    required = True                # class-level default: all fields required

    street   = StringField("Street")               # inherits required=True
    city     = StringField("City")                 # inherits required=True
    postcode = StringField("Postcode", required=True)  # pinned: always required


class OrderForm(Form):
    # billing: inherits class-level required=True from AddressForm
    billing  = AddressForm()

    # shipping: instance kwarg overrides class attr → all shipping fields optional
    # (except postcode, which is pinned at the field level)
    shipping = AddressForm(required=False)
```

## Creating form instances

Instantiate a form anywhere you need one — typically at the start of `compose()`:

```python
form = UserForm()
```

Pass `data=` to pre-populate fields:

```python
record = {"username": "alice", "age": 28, "active": True}
form = UserForm(data=record)
```

Override class attributes per-instance:

```python
form = UserForm(
    label_style="beside",
    help_style="tooltip",
    required=False,
    title="Edit Profile",
)
```

[`BaseForm.__init__`][textual_wtf.BaseForm] accepts:

`data: dict[str, Any] | None = None`
:   Initial field values. Keys should match field names.

`label_style: LabelStyle | None = None`
:   Override the form-wide label style.

`help_style: HelpStyle | None = None`
:   Override the form-wide help style.

`required: bool | None = None`
:   Override the form-wide required default.

`title: str | None = None`
:   Override the form title.

## Accessing fields

After instantiation, each field is available as a [`BoundField`][textual_wtf.BoundField] attribute:

```python
form = UserForm()

bf = form.username        # BoundField for the username field
print(bf.label)           # "Username"
print(bf.required)        # True
print(bf.value)           # None (no data supplied)
```

`form.bound_fields` returns the full `OrderedDict[str, BoundField]`:

```python
for name, bf in form.bound_fields.items():
    print(f"{name}: label={bf.label!r}, required={bf.required}")
```

## Getting and setting data

`get_data()` returns a snapshot of all current field values as a plain dictionary:

```python
data = form.get_data()
# {"username": "alice", "age": 28, "role": "editor", "active": True}
```

`set_data()` updates named fields without touching the others:

```python
form.set_data({"username": "bob", "age": 35})
```

!!! tip "After validation"
    Always call `form.clean()` or `form.validate()` before calling `get_data()` if you want to be sure the data is valid. `get_data()` returns the current values regardless of error state.

## Render lifecycle

A form instance is single-use per layout. Once `layout()` has been called (or a `BoundField` has been rendered via `simple_layout()` or `bf()`), that field is marked as rendered and cannot be composed a second time. To display the same form data again (for example, after a navigation event), create a new form instance:

```python
old_data = form.get_data()
form = UserForm(data=old_data)
yield from form.layout()
```
