# Guide

The guide covers all aspects of textual-wtf in depth. Work through it in order, or jump to the section that interests you most.

## Sections

<div class="grid cards" markdown>

-   **[Defining Forms](forms.md)**

    ---

    Learn how to declare form classes, set class-level defaults such as `label_style` and `required`, and use `get_data()` / `set_data()` to move data in and out of a form instance.

-   **[Fields & Validators](fields.md)**

    ---

    Every built-in field type explained with examples. Then the full set of built-in validators, how to write an inline `FunctionValidator`, and how to subclass `Validator` for reusable logic.

-   **[Layout & Rendering](layout.md)**

    ---

    Three rendering modes — `layout()`, `simple_layout()`, and the raw `bf()` call. All three `label_style` options and both `help_style` options. Custom layouts by subclassing `FormLayout`.

-   **[Embedded Forms](embedding.md)**

    ---

    Assign a `Form` instance as a class attribute to embed its fields with a name prefix. Control `required` state independently for each embedding.

-   **[Validation](validation.md)**

    ---

    When validators fire, how to run validation manually, and how to add cross-field errors with `clean_form()` and `add_error()`.

-   **[Tabbed Forms](tabbed_forms.md)**

    ---

    `TabbedForm` renders multiple forms as tabs. Tab labels turn red when a field in that tab has an error.

</div>
