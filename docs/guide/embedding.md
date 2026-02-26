# Embedded Forms

Embedding allows you to reuse a form's field definitions inside another form, with the embedded fields namespaced under a prefix. This is the primary mechanism for building composite forms such as a shipping form that contains two independent address sub-forms.

## Instance embedding (recommended)

Assign a `Form` **instance** as a class attribute. The metaclass detects it, reads all of its field definitions, and registers each one in the parent form with the variable name as a prefix:

```python title="order_form.py"
from textual_wtf import Form, StringField

class AddressForm(Form):
    street   = StringField("Street", help_text="House number and street name.")
    city     = StringField("City")
    postcode = StringField("Postcode")


class OrderForm(Form):
    name     = StringField("Customer name", required=True)
    billing  = AddressForm()              # → billing_street, billing_city, billing_postcode
    shipping = AddressForm(required=False) # → shipping_street, shipping_city, shipping_postcode
```

After instantiation, `OrderForm()` has these fields (in this order):

- `name`
- `billing_street`
- `billing_city`
- `billing_postcode`
- `shipping_street`
- `shipping_city`
- `shipping_postcode`

!!! info "Why instance embedding?"
    Instance embedding lets you pass constructor arguments — particularly `required=` — independently to each embedding. Class embedding (assigning the class itself rather than an instance) works but cannot carry per-embedding configuration. Prefer instances.

## Accessing embedded fields

### Qualified access

Always works. Use the full prefixed name:

```python
form = OrderForm()

billing_city = form.bound_fields["billing_city"]
# or
billing_city = form.billing_city
```

### Unqualified access

If only one embedded field ends with `_<name>`, attribute access without the prefix resolves automatically:

```python
form = OrderForm()

# "name" is unambiguous — there is exactly one field called "name"
print(form.name.label)   # "Customer name"
```

If the same suffix appears in multiple embeddings, unqualified access raises `AmbiguousFieldError`:

```python
try:
    form.city             # ambiguous: billing_city, shipping_city
except AmbiguousFieldError as e:
    print(e.name)         # "city"
    print(e.candidates)   # ["billing_city", "shipping_city"]
    # Use the qualified name instead:
    form.billing_city
    form.shipping_city
```

### Iterating all fields

```python
form = OrderForm()
for name, bf in form.bound_fields.items():
    print(f"{name}: required={bf.required}")
# name: required=False
# billing_street: required=True
# billing_city: required=True
# billing_postcode: required=True
# shipping_street: required=False
# shipping_city: required=False
# shipping_postcode: required=False
```

## The required= cascade for embedded forms

When you embed a form instance, the `required=` kwarg on that instance cascades to every field in the embedded form — **except** fields that have `required` set explicitly at the field level (pinned fields).

```python title="required_cascade.py"
from textual_wtf import Form, StringField

class AddressForm(Form):
    required = True                          # class-level default

    street   = StringField("Street")        # not pinned → cascade applies
    city     = StringField("City")          # not pinned → cascade applies
    postcode = StringField("Postcode", required=True)  # pinned → always required


class OrderForm(Form):
    # billing = AddressForm()
    # → uses AddressForm.required = True → all three fields required
    billing = AddressForm()

    # shipping = AddressForm(required=False)
    # → overrides to False → street and city become optional
    #   postcode stays required because it is pinned at the field level
    shipping = AddressForm(required=False)
```

The complete cascade for embedded fields:

| Priority | Setting | Notes |
|---|---|---|
| Lowest | Class attribute `required = True` on the embedded form | Applied when no instance kwarg is provided |
| Middle | `AddressForm(required=False)` at the embedding site | Overrides the class attribute |
| Pinned | `StringField("X", required=True)` on the field itself | Cannot be overridden by any cascade level |
| Highest | `bf.simple_layout(required=True)` at render time | Overrides everything, including pinned fields |

## get_data() with embedded fields

`get_data()` returns a flat dictionary where each key is the fully-qualified field name:

```python
form = OrderForm(data={
    "name": "Alice",
    "billing_street": "123 Main St",
    "billing_city": "Springfield",
    "billing_postcode": "SP1 2AB",
    "shipping_street": "456 Oak Ave",
    "shipping_city": "Shelbyville",
    "shipping_postcode": "SH3 4CD",
})

data = form.get_data()
# {
#     "name": "Alice",
#     "billing_street": "123 Main St",
#     "billing_city": "Springfield",
#     ...
# }
```

## Rendering embedded fields manually

You can render embedded fields exactly like any other field — use their fully-qualified names:

```python title="embedded_layout.py"
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static
from textual_wtf import ControllerAwareLayout

class OrderLayout(ControllerAwareLayout):
    def compose(self) -> ComposeResult:
        bf = self.form.bound_fields

        yield bf["name"].simple_layout()

        with Horizontal():
            with Vertical():
                yield Static("Billing address", classes="section-title")
                yield bf["billing_street"].simple_layout()
                yield bf["billing_city"].simple_layout()
                yield bf["billing_postcode"].simple_layout()

            with Vertical():
                yield Static("Shipping address", classes="section-title")
                yield bf["shipping_street"].simple_layout()
                yield bf["shipping_city"].simple_layout()
                yield bf["shipping_postcode"].simple_layout()

        with Horizontal(id="buttons"):
            yield Button("Submit", id="submit", variant="primary")
            yield Button("Cancel", id="cancel")
```

## Naming conflicts

The metaclass raises `FormError` at class definition time if a prefixed embedded field name conflicts with an existing field:

```python
class BadForm(Form):
    billing_city = StringField("Billing city")  # explicit field
    billing      = AddressForm()                # would produce billing_city → conflict!
    # FormError: Embedded field 'billing_city' conflicts with existing field.
```

Always choose embedding prefixes that do not clash with other field names on the form.
