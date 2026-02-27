# Runtime objects

These objects are created automatically during form instantiation and rendering. You
interact with them at render time (configuring how a field is displayed) and at
validation time (reading values and errors).

---

## BoundField

::: textual_wtf.bound.BoundField
    options:
      members:
        - __init__
        - field
        - form
        - name
        - label
        - default
        - required
        - help_text
        - label_style
        - help_style
        - validators
        - value
        - is_dirty
        - errors
        - has_error
        - error_messages
        - __call__
        - simple_layout
        - validate
      show_root_heading: true
      show_source: false

---

## FieldController

::: textual_wtf.controller.FieldController
    options:
      show_root_heading: true
      show_source: false
      filters:
        - "!^_"

---

## FieldWidget

::: textual_wtf.field_widget.FieldWidget
    options:
      show_root_heading: true
      show_source: false
      filters:
        - "!^_"
