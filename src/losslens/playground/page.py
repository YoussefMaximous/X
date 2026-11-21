"""Assemble the one self-contained Playground page."""

from __future__ import annotations

from .page_body import PAGE_BODY
from .page_script import SCRIPT


def render_page(payload: str) -> str:
    """Return the page with the JSON data and the inline script in place."""
    page = PAGE_BODY.replace("__TICK_DATA__", payload, 1)
    return page.replace("__SCRIPT__", SCRIPT, 1)
