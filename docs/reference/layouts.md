# Layouts

Layout classes are Textual `Widget` subclasses (specifically `VerticalScroll` subclasses) that render a form's fields and handle submit/cancel interactions.

## FormLayout

::: textual_wtf.layouts.FormLayout
    options:
      members:
        - BINDINGS
        - __init__
        - on_button_pressed
        - action_submit
        - action_cancel
      show_root_heading: true
      show_source: false

`FormLayout` is the base class for all form layouts. It provides:

- `self.form` — the `BaseForm` instance passed at construction
- `Enter` keybinding → `action_submit()` → posts `Form.Submitted` (after successful `clean()`)
- `Escape` keybinding → `action_cancel()` → posts `Form.Cancelled`
- `on_button_pressed` handler that routes button IDs `"submit"` and `"cancel"`

Subclass `FormLayout` directly only if you also need to handle widget events yourself. Otherwise subclass `ControllerAwareLayout`.

### Bindings

| Key | Action | Description |
|---|---|---|
| `enter` | `submit` | Validate and submit the form |
| `escape` | `cancel` | Cancel without submitting |

### Constructor

```python
def __init__(self, form: BaseForm, id: str | None = None, **kwargs: Any) -> None
```

`form`
:   The `BaseForm` instance to render. All field data and validation logic lives on this object.

`id`
:   Optional Textual widget ID.

---

## ControllerAwareLayout

::: textual_wtf.layouts.ControllerAwareLayout
    options:
      show_root_heading: true
      show_source: false

`ControllerAwareLayout` extends `FormLayout` by routing Textual widget events to `FieldController` objects. This is the class you should subclass when building custom layouts that use `bf.__call__()` to place raw widgets.

### How event routing works

When you call `bf()` to get a raw widget, the `BoundField` stamps `._field_controller` on the returned widget. `ControllerAwareLayout` listens for `Input.Changed`, `Checkbox.Changed`, `Select.Changed`, `TextArea.Changed`, and `on_descendant_blur` events. For each event, it looks up the controller and calls the appropriate method (`handle_widget_input` or `validate_for`).

Events originating from within a `FieldWidget` (the composite widget produced by `bf.simple_layout()`) are ignored here — the `FieldWidget` handles them internally.

### When to use ControllerAwareLayout

Use `ControllerAwareLayout` (or its subclass `DefaultFormLayout`) as your layout base class whenever you use `bf()` to render raw widgets. If you use only `bf.simple_layout()`, the `FieldWidget` handles its own events and you could technically use bare `FormLayout` — but `ControllerAwareLayout` handles both cases gracefully, so it is always safe to use.

---

## DefaultFormLayout

::: textual_wtf.layouts.DefaultFormLayout
    options:
      members:
        - compose
      show_root_heading: true
      show_source: false

`DefaultFormLayout` is the layout returned by `form.layout()` when no custom `layout_class` is set. It renders:

1. A bold title label (if `form.title` is non-empty)
2. Each unrendered field via `bf.simple_layout()`
3. A row of Submit (primary) and Cancel buttons

### Default CSS

```css
DefaultFormLayout {
    height: auto;
    max-height: 100%;
    padding: 1 2;
}
DefaultFormLayout .form-title {
    text-style: bold;
    margin-bottom: 1;
}
DefaultFormLayout #buttons {
    height: auto;
    margin-top: 1;
}
```

Override these styles in your app's CSS to resize or reposition the layout:

```css
DefaultFormLayout {
    width: 60;
    max-height: 80%;
    border: solid $primary;
}
```

### Unrendered guard

`DefaultFormLayout.compose()` skips any field that has already been rendered (`bf.controller.is_consumed` is `True`). This lets you render some fields manually in a custom section before calling `form.layout()`, though mixing the two approaches in the same form is unusual.
