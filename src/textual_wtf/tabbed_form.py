"""TabbedForm — Textual Widget that renders multiple Forms as TabbedContent."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from textual.css.query import NoMatches
from textual.widget import Widget
from textual.widgets import Tab, TabbedContent, TabPane

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from .forms import BaseForm


class TabbedForm(Widget):
    """Renders a sequence of :class:`~textual_wtf.BaseForm` instances as tabs.

    Each form occupies one :class:`~textual.widgets.TabPane`.  The tab label
    switches to the error colour whenever *any* field in that form currently
    has a validation error, giving the user a clear visual cue about which
    tab requires attention.

    The tab title is taken from ``form.title`` (a class attribute or instance
    kwarg on the form).  If no title is set the fallback is ``"Form N"`` where
    *N* is the 1-based position.

    Usage::

        class BillingForm(Form):
            title = "Billing"
            required = True
            street = StringField("Street")
            ...

        tf = TabbedForm(
            BillingForm(),
            ShippingForm(title="Shipping", required=False),
        )
        yield tf
    """

    DEFAULT_CSS = """
    TabbedForm {
        height: auto;
    }
    TabbedForm TabbedContent {
        height: auto;
    }
    TabbedForm TabbedContent > ContentSwitcher {
        height: auto;
    }
    TabbedForm TabPane {
        height: auto;
        padding: 0;
    }
    TabbedForm Tab.has-error {
        color: $error;
    }
    """

    def __init__(self, *forms: BaseForm, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._forms = forms

    def compose(self) -> ComposeResult:
        with TabbedContent():
            for i, form in enumerate(self._forms):
                tab_title = getattr(form, "title", "") or f"Form {i + 1}"
                pane_id = f"tabpane-{i}"
                with TabPane(tab_title, id=pane_id):
                    yield form.layout()

    def on_mount(self) -> None:
        """Register error listeners on all field controllers."""
        for i, form in enumerate(self._forms):
            for bf in form.bound_fields.values():
                bf.controller.add_error_listener(
                    lambda has_error, messages, _idx=i: self._refresh_tab_state(_idx)
                )

    def _refresh_tab_state(self, idx: int) -> None:
        """Sync the ``has-error`` CSS class on the tab for *form* at *idx*."""
        form = self._forms[idx]
        pane_id = f"tabpane-{idx}"
        has_any_error = any(
            bf.controller.has_error for bf in form.bound_fields.values()
        )
        try:
            tab = self.query_one(f"Tab#{pane_id}", Tab)
            if has_any_error:
                tab.add_class("has-error")
            else:
                tab.remove_class("has-error")
        except NoMatches:
            pass
