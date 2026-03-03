"""
Password change form demonstrating cross-field validation via clean_form().

Per-field validators (Required, MinLength) fire on blur and on submit.
``clean_form()`` runs *after* all per-field validators pass, so by the time
it is called you know that every field has a non-empty value meeting its
individual constraints.  ``add_error(field_name, message)`` attaches the
cross-field error to a specific field; it appears in that field's error
display alongside any per-field errors already shown.

Two cross-field rules enforced here:
  1. The new password must differ from the current password.
  2. The confirm field must exactly match the new password.

The ``password=True`` kwarg is forwarded through ``StringField``'s
``widget_kwargs`` to the underlying ``FormInput`` (a thin ``Input`` wrapper),
masking all three fields with bullet characters.

Note: this demo does not validate the current password against any stored
credential.  In a real application, ``clean_form()`` would also verify it.

Run with: python -m examples  (select "Password Change")
"""

from __future__ import annotations

from textual.app import ComposeResult, on
from textual.containers import Vertical

from textual_wtf import Form, StringField

from .example_screen import ExampleScreen


# ── Form definition ───────────────────────────────────────────────────────────


class PasswordChangeForm(Form):
    """Password change form with per-field and cross-field validation.

    Per-field: Required (via required=True) and MinLength(8) on new_password.
    Cross-field: new ≠ current, and confirm == new — both checked in clean_form().
    """

    title = "Change Password"
    label_style = "above"
    help_style = "below"

    current_password = StringField(
        "Current password",
        required=True,
        help_text="Your existing password",
        password=True,
    )
    new_password = StringField(
        "New password",
        required=True,
        min_length=8,
        help_text="At least 8 characters",
        password=True,
    )
    confirm_password = StringField(
        "Confirm new password",
        required=True,
        help_text="Re-enter the new password exactly",
        password=True,
    )

    def clean_form(self) -> bool:
        """Cross-field validation: ensure passwords are self-consistent.

        Called by ``clean()`` only after all per-field validators have passed,
        so ``current_password.value``, ``new_password.value``, and
        ``confirm_password.value`` are all guaranteed non-empty here.

        ``add_error()`` attaches an error message to the named field and
        causes ``clean()`` to return ``False`` even if this method returns
        ``True``.
        """
        current = self.current_password.value or ""
        new_pw = self.new_password.value or ""
        confirm = self.confirm_password.value or ""

        ok = True

        if new_pw and current and new_pw == current:
            self.add_error(
                "new_password",
                "New password must differ from your current password.",
            )
            ok = False

        if new_pw and confirm and new_pw != confirm:
            self.add_error(
                "confirm_password",
                "The two passwords do not match.",
            )
            ok = False

        return ok


# ── Demo screen ───────────────────────────────────────────────────────────────


class PasswordChangeDemoScreen(ExampleScreen):
    """Centred password-change form; resets itself after a successful submit."""

    CSS = """
    PasswordChangeDemoScreen { align: center middle; }

    #form-container {
        width: 60;
        max-height: 80%;
    }

    DefaultFormLayout {
        border: double $primary;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        self.form = PasswordChangeForm()
        with Vertical(id="form-container"):
            yield self.form.layout()

    @on(Form.Submitted)
    def form_submitted(self, event: Form.Submitted) -> None:
        self.notify(
            "Password changed successfully.",
            severity="information",
            timeout=5,
        )
        # Reset the form so the demo can be tried again without restarting.
        self.form = PasswordChangeForm()
        container = self.query_one("#form-container")
        container.remove_children()
        container.mount(self.form.layout())

    @on(Form.Cancelled)
    def form_cancelled(self, event: Form.Cancelled) -> None:
        self.notify("Cancelled", severity="warning")
        self.action_back()
