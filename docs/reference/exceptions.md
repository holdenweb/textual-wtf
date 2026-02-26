# Exceptions

textual-wtf defines four exception classes, all importable directly from `textual_wtf`.

## ValidationError

::: textual_wtf.exceptions.ValidationError
    options:
      show_root_heading: true
      show_source: false

Raised when a validator or `clean()` rejects a value.

```python
from textual_wtf import ValidationError
```

### Attributes

`message: str`
:   The human-readable error message passed to the constructor.

### When it is raised

- Inside a `FunctionValidator` callable to signal a failed validation check.
- By `IntegerField.to_python()` when the input cannot be converted to `int`.
- By custom validators that call `raise ValidationError(...)`.

### Example

```python
from textual_wtf import ValidationError

def must_be_even(value: int | None) -> None:
    if value is not None and value % 2 != 0:
        raise ValidationError(f"{value} is not an even number.")
```

---

## FieldError

::: textual_wtf.exceptions.FieldError
    options:
      show_root_heading: true
      show_source: false

Raised when a field is configured incorrectly at class definition time.

```python
from textual_wtf import FieldError
```

### When it is raised

- `ChoiceField` is defined with an empty `choices` list.
- A custom `Field` subclass detects an invalid configuration.

### Example

```python
from textual_wtf import ChoiceField

# Raises FieldError immediately at class definition time:
class BadForm(Form):
    size = ChoiceField("Size", choices=[])  # FieldError: non-empty list required
```

---

## FormError

::: textual_wtf.exceptions.FormError
    options:
      show_root_heading: true
      show_source: false

Raised for form definition or rendering errors.

```python
from textual_wtf import FormError
```

### When it is raised

- Embedding produces a field name that conflicts with an existing field.
- `add_error()` is called with a field name that does not exist on the form.
- A `BoundField` is rendered a second time (double-yield guard).

### Example

```python
from textual_wtf import Form, StringField

class BadForm(Form):
    billing_city = StringField("Billing city")
    billing = AddressForm()  # would create billing_city → FormError
```

---

## AmbiguousFieldError

::: textual_wtf.exceptions.AmbiguousFieldError
    options:
      show_root_heading: true
      show_source: false

Raised when unqualified attribute access on a form matches more than one embedded field.

```python
from textual_wtf import AmbiguousFieldError
```

### Attributes

`name: str`
:   The unqualified name that was looked up.

`candidates: list[str]`
:   The fully-qualified field names that all match the suffix.

### When it is raised

```python
form = OrderForm()  # has billing_city and shipping_city

try:
    form.city   # ambiguous — matches both billing_city and shipping_city
except AmbiguousFieldError as e:
    print(e.name)       # "city"
    print(e.candidates) # ["billing_city", "shipping_city"]
```

### Resolution

Use the fully-qualified name:

```python
billing_city  = form.billing_city
shipping_city = form.shipping_city
```
